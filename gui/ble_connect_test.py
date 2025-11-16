#!/usr/bin/env python3
"""
Simple BLE Connection Test for XIAO ESP32S3

This script connects to your ESP32S3 and tests communication.
"""

import asyncio
from bleak import BleakClient

# Your ESP32S3 identifiers (found from the scanner)
ESP32_ADDRESS = "B8:F8:62:FB:87:6D"  # Your actual device address
SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"
CHARACTERISTIC_UUID = "87654321-4321-4321-4321-cba987654321"

async def test_esp32_connection():
    """Test connection and communication with ESP32S3"""
    print(f"🔗 Attempting to connect to ESP32S3...")
    print(f"📍 Address: {ESP32_ADDRESS}")
    print(f"🆔 Service: {SERVICE_UUID}")
    print(f"🎯 Characteristic: {CHARACTERISTIC_UUID}")
    print("-" * 50)
    
    try:
        async with BleakClient(ESP32_ADDRESS) as client:
            print(f"✅ Connected to {ESP32_ADDRESS}")
            
            # Check if we're connected
            if client.is_connected:
                print("🔌 Connection established successfully!")
                
                # Get device information
                try:
                    device_name = await client.read_gatt_char("00002a00-0000-1000-8000-00805f9b34fb")  # Device Name
                    print(f"📛 Device Name: {device_name.decode()}")
                except:
                    print("📛 Device Name: Could not read")
                
                # List all services
                print("\n🔍 Available Services:")
                for service in client.services:
                    print(f"   🆔 {service.uuid}: {service.description}")
                    for char in service.characteristics:
                        print(f"      📝 {char.uuid}: {char.properties}")
                
                # Try to read from our custom characteristic
                try:
                    print(f"\n📖 Reading from characteristic {CHARACTERISTIC_UUID}...")
                    value = await client.read_gatt_char(CHARACTERISTIC_UUID)
                    print(f"✅ Read value: {value.decode()}")
                except Exception as e:
                    print(f"❌ Could not read characteristic: {e}")
                
                # Try to write to our custom characteristic
                try:
                    message = "Hello from Python BLE client!"
                    print(f"\n📝 Writing message: '{message}'")
                    await client.write_gatt_char(CHARACTERISTIC_UUID, message.encode())
                    print("✅ Message sent successfully!")
                    
                    # Read back the response
                    await asyncio.sleep(1)  # Give time for ESP32 to process
                    response = await client.read_gatt_char(CHARACTERISTIC_UUID)
                    print(f"📨 Response: {response.decode()}")
                    
                except Exception as e:
                    print(f"❌ Could not write to characteristic: {e}")
                
                print("\n🎉 BLE communication test completed!")
                
            else:
                print("❌ Failed to establish connection")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure ESP32S3 is powered on and advertising")
        print("2. Try running the BLE scanner again to confirm device is visible")
        print("3. Check that no other device is connected to the ESP32S3")
        print("4. Try moving closer to the ESP32S3")

async def main():
    """Main function"""
    print("🔵 ESP32S3 BLE Connection Test")
    print("=" * 40)
    
    await test_esp32_connection()
    
    print("\n👋 Test completed!")

if __name__ == "__main__":
    asyncio.run(main())