# XIAO ESP32S3 Communication GUI

A comprehensive Python GUI application for communicating with your XIAO ESP32S3 development board via USB Serial and Bluetooth Low Energy (BLE).

## Features

### 🔌 USB Serial Communication
- Auto-detection of available serial ports
- Configurable baud rates (9600 to 230400)
- Real-time message monitoring
- Interactive command interface with quick buttons
- Send custom commands or use predefined shortcuts

### 📱 Bluetooth Low Energy (BLE)
- BLE device scanning and discovery
- GATT service communication
- Real-time notifications from ESP32S3
- Send messages to BLE characteristics
- Auto-detection of ESP32/XIAO devices

### 🖥️ User Interface
- Tabbed interface for organized functionality
- Real-time message display with timestamps
- Auto-scrolling message windows
- Save message logs to file
- Connection status monitoring
- Cross-platform compatibility (Windows, macOS, Linux)

## Installation

### Option 1: Automatic Setup
1. Navigate to the `gui` folder
2. Run the setup script:
   ```bash
   python setup.py
   ```
   This will automatically install all required dependencies and offer to launch the GUI.

### Option 2: Manual Installation
1. Install Python 3.7 or newer
2. Install required packages:
   ```bash
   pip install pyserial bleak tkinter
   ```
3. Run the GUI:
   ```bash
   python esp32s3_gui.py
   ```

## Requirements

- **Python 3.7+** (with tkinter support)
- **pyserial** - For USB Serial communication
- **bleak** - For Bluetooth Low Energy communication (optional)
- **tkinter** - For GUI interface (usually included with Python)

## Usage

### Getting Started
1. Connect your XIAO ESP32S3 to your computer via USB
2. Launch the GUI application
3. The USB Serial tab should auto-detect your device on COM9

### USB Serial Communication
1. Select the correct COM port (usually COM9 for XIAO ESP32S3)
2. Set baud rate to 115200 (default for your ESP32S3 code)
3. Click "Connect"
4. Use the quick command buttons or type custom commands:
   - **Status (s)** - Get connection status
   - **Help (h)** - Show available commands
   - **Test (t)** - Send test message
   - **Memory (m)** - Show memory information

### BLE Communication
1. Click "Scan Devices" to discover nearby BLE devices
2. Look for "XIAO-ESP32S3-Test" in the device list
3. Select it and click "Connect"
4. Send messages through the BLE interface
5. Receive real-time notifications from the ESP32S3

### Message Management
- **Timestamps**: Toggle timestamp display in settings
- **Auto-scroll**: Automatically scroll to newest messages
- **Save Messages**: Export all communications to a text file
- **Clear All**: Remove all messages from display

## BLE Service Details

The GUI communicates with your ESP32S3 using these UUIDs:
- **Service UUID**: `12345678-1234-1234-1234-123456789abc`
- **Characteristic UUID**: `87654321-4321-4321-4321-cba987654321`

## Troubleshooting

### Serial Connection Issues
- **Port not found**: Try clicking "Refresh Ports" or check USB connection
- **Permission denied**: On Linux/macOS, you may need to add your user to the dialout group
- **Connection failed**: Ensure no other applications are using the serial port

### BLE Connection Issues
- **No BLE devices found**: Ensure Bluetooth is enabled on your computer
- **bleak not installed**: Install with `pip install bleak`
- **Connection timeout**: Try scanning again or restart the ESP32S3

### General Issues
- **GUI not launching**: Ensure Python 3.7+ is installed with tkinter support
- **Import errors**: Run `python setup.py` to install missing dependencies
- **Slow performance**: Try disabling timestamps or reducing message frequency

## File Structure

```
gui/
├── esp32s3_gui.py      # Main GUI application
├── setup.py            # Installation and setup script
├── requirements.txt    # Python package dependencies
└── README.md          # This documentation
```

## Supported Platforms

- **Windows** 10/11 (tested)
- **macOS** 10.14+ (should work)
- **Linux** Ubuntu 18.04+ (should work)

## ESP32S3 Commands

When connected via USB Serial, you can send these commands:
- `h` - Show help menu
- `s` - Show connection status
- `t` - Send test message to all connected devices
- `r` - Restart BLE advertising
- `c` - Show message counters
- `m` - Show memory information

## Development Notes

The GUI application is built with:
- **tkinter** for the user interface
- **pyserial** for serial communication
- **bleak** for cross-platform BLE support
- **threading** for non-blocking I/O operations
- **asyncio** for asynchronous BLE operations

## License

This project is part of the XIAO ESP32S3 communication test suite. Feel free to modify and distribute according to your needs.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Ensure all dependencies are correctly installed
3. Verify your ESP32S3 is running the compatible firmware
4. Check that the BLE UUIDs match between the GUI and ESP32S3 code