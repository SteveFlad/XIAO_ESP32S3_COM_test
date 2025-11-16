# XIAO ESP32S3 Communication Test

A comprehensive communication interface for the XIAO ESP32S3 development board, featuring both USB Serial and Bluetooth Low Energy (BLE) communication capabilities.

## Features

### ESP32S3 Firmware
- **USB Serial Communication**: High-speed serial communication at 115200 baud
- **Bluetooth Low Energy (BLE)**: GATT server with custom service and characteristic
- **Interactive Commands**: Built-in command system for testing and diagnostics
- **Memory Management**: Real-time memory usage monitoring
- **Status Reporting**: Device status and capability reporting

### Python GUI Application
- **Dual Communication**: Support for both USB Serial and BLE communication
- **Device Scanner**: Automatic BLE device discovery with ESP32S3 identification
- **Device Inspector**: Detailed BLE service and characteristic inspection
- **Real-time Messaging**: Live message display with timestamps
- **Command Interface**: Interactive command sending with quick-access buttons
- **Message Logging**: Save communication logs to file
- **Cross-platform**: Works on Windows, macOS, and Linux

## Hardware Requirements

- **XIAO ESP32S3** development board by Seeed Studio
- **USB-C cable** for programming and serial communication
- **Computer** with Bluetooth Low Energy support (for BLE features)

## Software Requirements

### For ESP32S3 Firmware
- [PlatformIO](https://platformio.org/) or [Arduino IDE](https://www.arduino.cc/en/software)
- ESP32 Arduino Core

### For Python GUI
- **Python 3.7+**
- **Required packages**:
  ```bash
  pip install pyserial bleak
  ```

## Quick Start

### 1. Flash the ESP32S3 Firmware

#### Using PlatformIO (Recommended)
```bash
# Clone or download this repository
cd XIAO_ESP32S3_COM_test

# Build and upload
pio run --target upload

# Open serial monitor (optional)
pio device monitor
```

#### Using Arduino IDE
1. Install ESP32 board support
2. Select "XIAO_ESP32S3" as the board
3. Open `src/main.cpp`
4. Upload to your device

### 2. Run the Python GUI

```bash
# Navigate to the GUI directory
cd gui

# Install dependencies
pip install pyserial bleak

# Launch the GUI
python esp32s3_gui.py
```

## Usage

### USB Serial Communication
1. Connect your XIAO ESP32S3 via USB-C
2. Open the GUI and go to the "USB Serial" tab
3. Select the correct COM port (usually COM9 on Windows)
4. Click "Connect"
5. Use the command buttons or type custom commands

**Available Commands:**
- `s` - Show device status
- `h` - Display help information  
- `t` - Run communication test
- `m` - Show memory usage
- `r` - Restart device

### BLE Communication
1. Ensure your ESP32S3 is powered on
2. Go to the "BLE Communication" tab
3. Click "Scan Devices" - ESP32S3 devices will be marked with 🎯
4. Select "XIAO-ESP32S3-Test" from the list
5. Use "Inspect Device" to verify compatibility (optional)
6. Click "Connect"
7. Send messages through the BLE interface

### Device Inspector
The BLE Device Inspector helps identify compatible devices:
- ✅ **Compatible**: Shows green checkmarks for correct service/characteristic UUIDs
- ⚠️ **Incompatible**: Warns about missing services or characteristics
- 📡 **Service Details**: Lists all available BLE services and their properties

## Technical Specifications

### BLE Configuration
- **Service UUID**: `12345678-1234-1234-1234-123456789abc`
- **Characteristic UUID**: `87654321-4321-4321-4321-cba987654321`
- **Device Name**: `XIAO-ESP32S3-Test`
- **Properties**: Read, Write, Notify

### Serial Configuration
- **Baud Rate**: 115200 (configurable in GUI)
- **Data Bits**: 8
- **Parity**: None  
- **Stop Bits**: 1
- **Flow Control**: None

## Project Structure

```
XIAO_ESP32S3_COM_test/
├── platformio.ini          # PlatformIO configuration
├── src/
│   └── main.cpp            # ESP32S3 firmware source
├── gui/
│   ├── esp32s3_gui.py     # Main GUI application
│   ├── ble_scanner.py     # BLE diagnostic tool
│   └── ble_connect_test.py # BLE connection tester
├── include/               # Header files
├── lib/                   # Project libraries  
└── test/                  # Test files
```

## Troubleshooting

### Common Issues

**"Port not found" or "Access denied"**
- Ensure the ESP32S3 is connected via USB
- Check if another program is using the serial port
- Try a different USB cable or port
- On Windows, check Device Manager for the correct COM port

**"BLE device not found"**
- Verify the ESP32S3 firmware is running correctly
- Check that Bluetooth is enabled on your computer
- Ensure the device is within range (< 10 meters)
- Try restarting the ESP32S3

**"Characteristic not found" error**
- Use the "Inspect Device" feature to verify compatibility
- Ensure you're connecting to the correct ESP32S3 device
- Verify the firmware is using the correct UUIDs

**Python GUI crashes or freezes**
- Update to Python 3.7 or newer
- Reinstall the required packages: `pip install --upgrade pyserial bleak`
- Check for Windows Defender or antivirus blocking

### Debug Tools

The project includes diagnostic utilities:

- **`ble_scanner.py`**: Standalone BLE device scanner
- **`ble_connect_test.py`**: Direct BLE connection testing
- **Serial Monitor**: Use PlatformIO's built-in monitor for low-level debugging

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## License

This project is open source and available under the MIT License.

## Acknowledgments

- **Seeed Studio** for the XIAO ESP32S3 hardware
- **Espressif** for the ESP32 platform and libraries
- **GitHub Copilot** for development assistance
- **Community contributors** for testing and feedback

---

**Created with GitHub Copilot | November 2025**