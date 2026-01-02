#include <mega32a.h>
#include <delay.h>
#include <stdio.h>

#define F_CPU 11059200UL

// FUNCTION PROTOTYPES
void UART_init(unsigned long USART_BAUDRATE);
void UART_TxChar(char ch);
void UART_SendString(char *str);
unsigned int read_adc_multiple_samples(unsigned char adc_input, unsigned char num_samples);
unsigned int average_multiple_readings(unsigned char ic_pin_number);
void set_mux_channel(unsigned char primary_mux, unsigned char secondary_mux);
void scan_all_64_channels(void);
void monitor_selected_channel(void);

// Global variables
unsigned int adc_val = 0;
float analog = 0.0;
char buffer[100];

// Dual MUX tracking
unsigned char selected_primary_mux = 0;  // PB3/4/5 - Best channel (0-7)
unsigned char selected_secondary_mux = 0; // PB0/1/2 - Will cycle (0-7)
unsigned int min_reading = 0xFFFF;
unsigned int channel_readings[8][8]; // [primary][secondary]

// UART Initialization
void UART_init(unsigned long USART_BAUDRATE)
{
    unsigned int BAUD_PRESCALE;
    BAUD_PRESCALE = (unsigned int)((F_CPU / (USART_BAUDRATE * 16UL)) - 1);

    UCSRB |= (1 << RXEN) | (1 << TXEN);
    UCSRC |= (1 << URSEL) | (1 << UCSZ0) | (1 << UCSZ1);
    UBRRL = BAUD_PRESCALE;
    UBRRH = (BAUD_PRESCALE >> 8);
}

// UART Transmit Character
void UART_TxChar(char ch)
{
    while (!(UCSRA & (1<<UDRE)));
    UDR = ch;
}

// UART Send String
void UART_SendString(char *str)
{
    while (*str)
    {
        UART_TxChar(*str++);
    }
}

// Voltage Reference: AREF pin
#define ADC_VREF_TYPE ((0<<REFS1) | (0<<REFS0) | (0<<ADLAR))

// Set both multiplexers
void set_mux_channel(unsigned char primary_mux, unsigned char secondary_mux)
{
    // PB0/1/2 = secondary (lower 3 bits)
    // PB3/4/5 = primary (upper 3 bits shifted)
    PORTB = (secondary_mux & 0x07) | ((primary_mux & 0x07) << 3);
}

// Enhanced ADC reading with averaging
unsigned int read_adc_multiple_samples(unsigned char adc_input, unsigned char num_samples)
{
    unsigned int readings[16];
    unsigned long sum = 0;
    unsigned char i, j;
    unsigned int temp;
    unsigned char discard_count;
    unsigned char start_index, end_index;

    ADMUX = adc_input | ADC_VREF_TYPE;
    delay_ms(2); // Wait for MUX to stabilize

    // Flush old readings
    for(i = 0; i < 3; i++)
    {
        ADCSRA |= (1<<ADSC);
        while ((ADCSRA & (1<<ADIF)) == 0);
        ADCSRA |= (1<<ADIF);
    }

    // Take samples
    for(i = 0; i < num_samples; i++)
    {
        ADCSRA |= (1<<ADSC);
        while ((ADCSRA & (1<<ADIF)) == 0);
        ADCSRA |= (1<<ADIF);
        readings[i] = ADCW;
        delay_ms(1);
    }

    // Bubble sort
    for(i = 0; i < num_samples-1; i++)
    {
        for(j = i+1; j < num_samples; j++)
        {
            if(readings[j] < readings[i])
            {
                temp = readings[i];
                readings[i] = readings[j];
                readings[j] = temp;
            }
        }
    }

    // Discard top and bottom 25%
    discard_count = num_samples / 4;
    start_index = discard_count;
    end_index = num_samples - discard_count;

    sum = 0;
    for(i = start_index; i < end_index; i++)
        sum += readings[i];

    return (unsigned int)(sum / (end_index - start_index));
}

// Average multiple readings
unsigned int average_multiple_readings(unsigned char ic_pin_number)
{
    unsigned int i, reading;
    unsigned long sum = 0;
    unsigned int readings[10];
    unsigned int min_val, max_val;

    // Take 10 readings
    for(i = 0; i < 10; i++)
    {
        reading = read_adc_multiple_samples(3, 8);
        readings[i] = reading;
        delay_ms(5); // Reduced delay
    }

    // Find min/max
    min_val = readings[0];
    max_val = readings[0];
    sum = 0;

    for(i = 0; i < 10; i++)
    {
        sum += readings[i];
        if(readings[i] < min_val) min_val = readings[i];
        if(readings[i] > max_val) max_val = readings[i];
    }

    // Remove extremes from average
    sum = sum - min_val - max_val;

    return (unsigned int)(sum / 8); // 10 - 2 outliers
}

// Scan all 64 channels and find the cycle with lowest average (SILENT MODE)
void scan_all_64_channels(void)
{
    unsigned char primary, secondary;
    unsigned int reading;
    unsigned long cycle_sum;
    unsigned int cycle_average;
    unsigned int min_cycle_average = 0xFFFF;

    for(primary = 0; primary < 8; primary++)
    {
        cycle_sum = 0;

        for(secondary = 0; secondary < 8; secondary++)
        {
            // Set both muxes
            set_mux_channel(primary, secondary);

            // Wait for settling
            delay_ms(400);

            // Take reading
            reading = average_multiple_readings(secondary);
            channel_readings[primary][secondary] = reading;
            cycle_sum += reading;
        }

        // Calculate average for this cycle
        cycle_average = (unsigned int)(cycle_sum / 8);

        // Check if this cycle has the lowest average
        if(cycle_average < min_cycle_average)
        {
            min_cycle_average = cycle_average;
            selected_primary_mux = primary;
        }
    }

    // Store the minimum reading
    min_reading = min_cycle_average;
}

// Monitor the selected primary channel, cycling through secondary
void monitor_selected_channel(void)
{
    unsigned char secondary;
    unsigned int reading;

    for(secondary = 0; secondary < 8; secondary++)
    {
        // Set muxes
        set_mux_channel(selected_primary_mux, secondary);

        // Wait for settling
        delay_ms(400);

        // Take reading
        reading = average_multiple_readings(secondary);
        analog = (float)reading * 5.0 / 1024.0;

        // Send only the voltage value as number (Pin 1-8)
        sprintf(buffer, "%1.3f\r\n", analog);
        UART_SendString(buffer);
    }
}

void main(void)
{
    unsigned int cycle = 0;

    // Configure PORTB as output (all 8 bits for dual MUX)
    DDRB = 0xFF;
    PORTB = 0x00;

    // Configure ADC input
    DDRC &= ~(1 << 3);
    PORTC &= ~(1 << 3);

    UART_init(9600);

    // ADC Setup: Prescaler 128 for maximum accuracy
    ADCSRA = (1 << ADEN) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);

    delay_ms(500);

    // Silent scan to find lowest average cycle
    scan_all_64_channels();

    delay_ms(1000);

    // Main loop: Monitor the selected primary channel
    while (1)
    {
        monitor_selected_channel();
        delay_ms(500);
        cycle++;

        // Rescan every 20 cycles to check if minimum has changed
        if(cycle % 20 == 0)
        {
            scan_all_64_channels();
            delay_ms(1000);
        }
    }
}
