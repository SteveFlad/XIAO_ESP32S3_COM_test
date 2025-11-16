#!/usr/bin/env python3
"""
Simple BLE Scanner for ESP32S3 Device Detection

This script scans for BLE devices and specifically looks for your XIAO ESP32S3.
It will show all discovered devices and highlight your ESP32S3 if found.

Usage:
    python ble_scanner.py

Requirements:
    pip install bleak
"""

import asyncio
import sys
from bleak import BleakScanner

# Your ESP32S3 device identifiers
TARGET_NAME = "XIAO-ESP32S3-Test"
TARGET_SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"

async def scan_for_devices():
    """Scan for BLE devices and look for the ESP32S3"""
    print("🔍 Scanning for BLE devices...")
    print("📱 Looking specifically for:", TARGET_NAME)
    print("🆔 Target Service UUID:", TARGET_SERVICE_UUID)
    print("-" * 60)
    
    devices = await BleakScanner.discover(timeout=10.0)
    
    if not devices:
        print("❌ No BLE devices found!")
        print("\nTroubleshooting tips:")
        print("1. Make sure Bluetooth is enabled on this computer")
        print("2. Ensure your ESP32S3 is powered on and running")
        print("3. Try moving closer to the ESP32S3")
        print("4. Check if the ESP32S3 is advertising (look for periodic updates in serial monitor)")
        return False
    
    print(f"✅ Found {len(devices)} BLE device(s):")
    print()
    
    esp32_found = False
    
    for i, device in enumerate(devices, 1):
        name = device.name or "Unknown Device"
        address = device.address
        rssi = device.rssi if hasattr(device, 'rssi') else "Unknown"
        
        # Check if this is our ESP32S3
        is_target = (TARGET_NAME.lower() in name.lower()) or ("esp32" in name.lower())
        
        if is_target:
            print(f"🎯 FOUND TARGET DEVICE #{i}:")
            print(f"   📛 Name: {name}")
            print(f"   📍 Address: {address}")
            print(f"   📶 RSSI: {rssi} dBm")
            esp32_found = True
        else:
            print(f"📱 Device #{i}:")
            print(f"   📛 Name: {name}")
            print(f"   📍 Address: {address}")
            print(f"   📶 RSSI: {rssi} dBm")
        
        # Try to get service UUIDs if available
        if hasattr(device, 'metadata') and device.metadata:
            uuids = device.metadata.get('uuids', [])
            if uuids:
                print(f"   🆔 Services: {', '.join(uuids)}")
                if TARGET_SERVICE_UUID in uuids:
                    print("   ✅ FOUND TARGET SERVICE UUID!")
        
        print()
    
    if esp32_found:
        print("🎉 ESP32S3 device found and is advertising!")
    else:
        print("⚠️  ESP32S3 device not found in scan results")
        print("\nPossible issues:")
        print("1. Device might not be advertising - check serial monitor output")
        print("2. BLE might not be properly initialized on ESP32S3")
        print("3. Device might be using a different name")
        print("4. Signal might be too weak - move closer")
    
    return esp32_found

async def continuous_scan():
    """Continuously scan for devices every 5 seconds"""
    print("🔄 Starting continuous BLE scanning...")
    print("Press Ctrl+C to stop\n")
    
    scan_count = 0
    while True:
        try:
            scan_count += 1
            print(f"📡 Scan #{scan_count} - {asyncio.get_event_loop().time():.1f}s")
            
            found = await scan_for_devices()
            
            if found:
                print("✅ Target device is consistently advertising!")
            
            print(f"\n⏳ Waiting 5 seconds before next scan...")
            print("=" * 60)
            await asyncio.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n👋 Scanning stopped by user")
            break
        except Exception as e:
            print(f"❌ Error during scan: {e}")
            await asyncio.sleep(2)

def main():
    """Main function to run the scanner"""
    print("🔵 BLE Scanner for XIAO ESP32S3")
    print("=" * 40)
    
    try:
        # Check if bleak is available
        import bleak
        print("📦 Bleak BLE library loaded successfully")
    except ImportError:
        print("❌ Error: bleak not installed!")
        print("Install with: pip install bleak")
        sys.exit(1)
    
    print("\nChoose scanning mode:")
    print("1. Single scan (default)")
    print("2. Continuous scanning")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "2":
            asyncio.run(continuous_scan())
        else:
            asyncio.run(scan_for_devices())
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()