# define switch1 1
# define switch1 3
# define switch3 4



void setup() {
  Serial.begin(9600);
  pinMode(switch1 , OUTPUT);
  pinMode(switch1 , OUTPUT);
  pinMode(switch3 , OUTPUT);
  pinMode(A0 , INPUT);  //read pin data
  

  while (!Serial) {
    ; 
  }
  Serial.println("Arduino Ready");
}

void loop() {
  


/*
 
  static int elementNumber = 1;
  
  // Send one element at a time
  Serial.println(elementNumber);
  
  elementNumber++;
  if (elementNumber > 8) {
    elementNumber = 1; // Reset after 50
  }
  delay(50);
   // Send one element every second

*/


//1
  digitalWrite(switch1 ,0); digitalWrite(switch1,0); digitalWrite(switch3,0);    
  delay(50);
  
  
   int pin1 = analogRead(A0);
  Serial.println(pin1);
  delay(50);
//1
  digitalWrite(switch1 ,0); digitalWrite(switch1,0); digitalWrite(switch3,1);  delay(50);   int pin2 = analogRead(A0);
  Serial.println(pin1);
  delay(50);
//3
  digitalWrite(switch1 ,0); digitalWrite(switch1,1); digitalWrite(switch3,0); delay(50);    int pin3 = analogRead(A0);
  Serial.println(pin3);
  delay(50);
//4
  digitalWrite(switch1 ,0); digitalWrite(switch1,1); digitalWrite(switch3,1);  delay(50);   int pin4 = analogRead(A0);
  Serial.println(pin4);
  delay(50);
//5
  digitalWrite(switch1 ,1); digitalWrite(switch1,0); digitalWrite(switch3,0); delay(50);   int pin5 = analogRead(A0);
  Serial.println(pin5);
  delay(50);
//6
  digitalWrite(switch1 ,1); digitalWrite(switch1,0); digitalWrite(switch3,1);   delay(50);  int pin6 = analogRead(A0);
  Serial.println(pin6);
  delay(50);
//7
  digitalWrite(switch1 ,1); digitalWrite(switch1,1); digitalWrite(switch3,0);  delay(50);   int pin7 = analogRead(A0);
  Serial.println(pin7);
  delay(50);
//8
  digitalWrite(switch1 ,1); digitalWrite(switch1,1); digitalWrite(switch3,1);   delay(50);  int pin8 = analogRead(A0);
  Serial.println(pin8);
  delay(50);
  
}