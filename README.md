# IC Tester with MongoDB Integration

A comprehensive integrated circuit (IC) testing system that uses Arduino/ATmega microcontrollers for data acquisition, MongoDB for cloud storage, and a Python GUI for visualization and analysis.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Database Schema](#database-schema)
- [Troubleshooting](#troubleshooting)
- [Team](#team)

## 🔍 Overview

This IC Tester system is designed to characterize and identify integrated circuits by measuring analog voltage readings across multiple pins using multiplexed ADC channels. The system compares measured values against a MongoDB database of known IC signatures to identify unknown chips.

**Key Components:**
- **Hardware Layer**: Arduino Uno or ATmega32A microcontroller with dual multiplexer configuration
- **Data Layer**: MongoDB Atlas for cloud-based IC signature storage
- **Interface Layer**: Python Tkinter GUI with real-time visualization

## ✨ Features

- **Automated IC Testing**: Sequential measurement of 8 channels per IC
- **Dual Multiplexer Support**: Scan up to 64 channels (8×8 configuration)
- **Real-time Data Visualization**: Live plotting of voltage readings
- **MongoDB Integration**: Cloud-based storage and retrieval of IC signatures
- **Pattern Matching**: SSE-based comparison algorithm to identify ICs
- **Photo Management**: Store and display IC photos alongside data
- **Database Management**: Add, view, update, and delete IC records
- **Statistical Analysis**: Multi-sample averaging with outlier rejection

## 🏗️ System Architecture

```
┌─────────────────┐
│   IC Under Test │
└────────┬────────┘
         │
    ┌────▼────────────────────────┐
    │  Multiplexer Circuit (8:1)  │
    │  Primary + Secondary MUX    │
    └────────┬────────────────────┘
             │
    ┌────────▼────────────────┐
    │  Arduino/ATmega32A      │
    │  - ADC Sampling         │
    │  - Serial Communication │
    └────────┬────────────────┘
             │ USB/UART
    ┌────────▼────────────────┐
    │  Python GUI Application │
    │  - Data Collection      │
    │  - Visualization        │
    │  - Pattern Matching     │
    └────────┬────────────────┘
             │ Internet
    ┌────────▼────────────────┐
    │  MongoDB Atlas Cloud    │
    │  - IC Signature Storage │
    │  - Photo Storage        │
    └─────────────────────────┘
```

## 🔧 Hardware Requirements

### Microcontroller Options

**Option 1: Arduino Uno**
- Arduino Uno board
- USB cable for programming and communication
- 3 digital output pins for multiplexer control (D1, D3, D4)
- 1 analog input pin (A0)

**Option 2: ATmega32A**
- ATmega32A microcontroller (11.0592 MHz crystal)
- UART-to-USB adapter
- Port B (PB0-PB5) for dual multiplexer control
- ADC Channel 3 (PC3) for voltage measurement

### Additional Components

- CD4051 or similar 8:1 analog multiplexer (1 or 2 units)
- IC test socket/fixture
- 5V power supply
- Connecting wires and breadboard
- Optional: ZIF socket for easy IC insertion

## 💻 Software Requirements

### Python Environment

```bash
Python 3.7+
```

### Required Python Packages

```bash
pip install tkinter
pip install pyserial
pip install matplotlib
pip install numpy
pip install pymongo
pip install Pillow
```

### Development Tools

- Arduino IDE (for Arduino Uno firmware)
- CodeVision AVR (for ATmega32A firmware)
- MongoDB Atlas account (free tier available)

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/faressspace/Ic-tester.git
cd Ic-tester
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Upload Firmware

**For Arduino Uno:**
```bash
# Open Arduino.c in Arduino IDE
# Select Board: Arduino Uno
# Select Port: [Your COM Port]
# Click Upload
```

**For ATmega32A:**
```bash
# Open ATmega.c in CodeVision AVR
# Compile and program using ISP programmer
```

### 4. Set Up MongoDB

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster
3. Create a database user with read/write permissions
4. Whitelist your IP address (or use 0.0.0.0/0 for testing)
5. Get your connection string

## ⚙️ Configuration

### MongoDB Connection

Update the GUI application with your MongoDB credentials:

```python
# In GUI.py or via the interface
mongodb_uri = "mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/"
database_name = "ic_tester"
collection_name = "ic_database"
```

### Serial Port Configuration

```python
# Default settings
serial_port = "COM4"  # Adjust based on your system
baud_rate = 9600
```

### Hardware Pin Configuration

**Arduino Uno (Arduino.c):**
```c
#define switch1 1   // Digital pin 1
#define switch2 3   // Digital pin 3
#define switch3 4   // Digital pin 4
// ADC input: A0
```

**ATmega32A (ATmega.c):**
```c
// Primary MUX: PB3, PB4, PB5
// Secondary MUX: PB0, PB1, PB2
// ADC input: PC3 (ADC Channel 3)
```

## 🚀 Usage

### Starting the Application

```bash
python GUI.py
```

### Testing an IC

1. **Insert IC**: Place the IC in the test fixture
2. **Connect**: Click "Reconnect MongoDB" to verify database connection
3. **Configure Serial**: Select the correct COM port and baud rate
4. **Start Collection**: Click "Start Collection" button
5. **Wait**: System will collect 5 message cycles (40 readings total)
6. **Compare**: Click "Compare with Database" to identify the IC
7. **Review Results**: Check the comparison results and similarity scores

### Adding New ICs to Database

**Method 1: From Measurement**
1. Test an IC using "Start Collection"
2. After comparison, click "Save to Database"
3. Enter a unique IC name
4. Optionally upload a photo

**Method 2: Manual Entry**
1. Click "Add New IC to Database"
2. Enter IC name
3. Input 8 comma-separated voltage readings
4. Optionally browse and select an IC photo
5. Click "Save IC"

### Viewing Database

1. Click "View Database" to see all stored ICs
2. Review IC names, readings, timestamps, and photo availability
3. Select an IC to delete it from the database

## 🗄️ Database Schema

### IC Document Structure

```javascript
{
  "_id": ObjectId("..."),
  "ic_name": "7404_HEX_INVERTER",
  "readings": [0.123, 4.567, 0.089, 4.923, 0.045, 4.878, 0.234, 4.765],
  "timestamp": ISODate("2025-01-03T10:30:00Z"),
  "photo": "base64_encoded_image_data...",
  "messages": [
    [0.120, 4.560, ...],
    [0.125, 4.570, ...],
    [0.124, 4.565, ...],
    [0.122, 4.568, ...],
    [0.123, 4.567, ...]
  ],
  "comparison_results": [
    {"name": "7404_ALT", "sse": 0.0023},
    {"name": "7405_VARIANT", "sse": 0.1234}
  ],
  "added_manually": false
}
```

### Indexes

```javascript
db.ic_database.createIndex({ "ic_name": 1 })
db.ic_database.createIndex({ "timestamp": -1 })
```

## 🔍 Pattern Matching Algorithm

The system uses Sum of Squared Errors (SSE) to compare measured readings with database entries:

```
SSE = Σ(measured[i] - reference[i])² for i = 0 to 7

Similarity = 100 / (1 + SSE) %
```

**Interpretation:**
- SSE < 0.01: Excellent match (>99% similarity)
- SSE < 0.1: Good match (>90% similarity)
- SSE < 1.0: Moderate match (>50% similarity)
- SSE > 1.0: Poor match

## 🛠️ Troubleshooting

### Serial Connection Issues

**Problem**: "Port COM4 not found"
- **Solution**: Check Device Manager for the correct COM port
- Try different USB ports
- Reinstall USB drivers

**Problem**: "No data received"
- **Solution**: Verify baud rate matches firmware (9600)
- Check USB cable connection
- Press Arduino reset button

### MongoDB Connection Issues

**Problem**: "Connection timeout"
- **Solution**: Check internet connection
- Verify IP address is whitelisted in MongoDB Atlas
- Check firewall settings

**Problem**: "Authentication failed"
- **Solution**: Verify username and password in connection string
- Ensure database user has proper permissions

### Measurement Issues

**Problem**: "Readings are unstable"
- **Solution**: Increase settling delays in firmware
- Check multiplexer connections
- Verify power supply stability
- Ensure proper IC insertion

**Problem**: "All readings are 0V or 5V"
- **Solution**: Check multiplexer control signals
- Verify ADC reference voltage
- Test with known working IC

### Code Issues in Firmware

**Arduino.c Issues:**
- Line 2: `#define switch1 3` redefines switch1 (should be `switch2`)
- Lines with `digitalWrite(switch1, ...)` - second parameter should be `switch2`
- Line with `Serial.println(pin1)` in section //1 second occurrence should print `pin2`

## 📊 GUI Features

### Tabs

1. **Real-time Data**: Shows current voltage readings for all 8 channels
2. **Log**: Displays timestamped system messages and status updates
3. **Comparison Results**: Ranked list of matching ICs with similarity scores
4. **Visualization**: Matplotlib plots showing measurement trends and comparisons

### Controls

- **Start Collection**: Begin data acquisition
- **Stop**: Halt ongoing collection
- **Compare with Database**: Run pattern matching
- **Save to Database**: Store current measurement
- **Add New IC**: Manual database entry
- **View Database**: Browse all stored ICs


## 👥 Team

- Faress Farrag
- Gasser Mohamed
- Ahmed Mahfouz
- Ahmed Hossam

**Supervisor**: Dr. Hossam El-Din Moustafa


## 📚️ content drive

https://drive.google.com/drive/u/1/folders/15dxTtdAfdbfrDmxfM95Eg7QcgDFA
