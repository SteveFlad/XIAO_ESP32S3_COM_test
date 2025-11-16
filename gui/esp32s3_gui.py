"""
XIAO ESP32S3 Communication GUI
A Python GUI application for communicating with the XIAO ESP32S3 via USB Serial and BLE.

Features:
- USB Serial communication
- BLE device scanning and connection
- Real-time message display
- Command sending interface
- Connection status monitoring
- Device information display

Requirements:
- Python 3.7+
- tkinter (usually included with Python)
- pyserial
- bleak (for BLE communication)

Author: GitHub Copilot
Date: November 2025
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import serial
import serial.tools.list_ports
import asyncio
import threading
import time
from datetime import datetime
import json
import os
import concurrent.futures

try:
    from bleak import BleakClient, BleakScanner
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False
    print("Warning: bleak not installed. BLE functionality will be disabled.")
    print("Install with: pip install bleak")

class AsyncioManager:
    """Manages asyncio operations in a separate thread to avoid conflicts with tkinter"""
    
    def __init__(self):
        self.loop = None
        self.thread = None
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._start_event_loop()
    
    def _start_event_loop(self):
        """Start the asyncio event loop in a separate thread"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()
        
        # Wait for loop to be ready
        while self.loop is None:
            time.sleep(0.01)
    
    def run_async(self, coro):
        """Run an async coroutine and return a future"""
        if self.loop and not self.loop.is_closed():
            return asyncio.run_coroutine_threadsafe(coro, self.loop)
        else:
            raise RuntimeError("Event loop is not running")
    
    def shutdown(self):
        """Shutdown the event loop"""
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.executor.shutdown(wait=False)

class ESP32S3_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("XIAO ESP32S3 Communication Interface")
        self.root.geometry("1000x700")
        
        # Communication variables
        self.serial_connection = None
        self.ble_client = None
        self.is_connected_serial = False
        self.is_connected_ble = False
        self.message_count = 0
        
        # BLE UUIDs (matching your ESP32S3 code)
        self.SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"
        self.CHARACTERISTIC_UUID = "87654321-4321-4321-4321-cba987654321"
        
        # Threading
        self.serial_thread = None
        self.ble_thread = None
        self.stop_threads = False
        
        # Asyncio manager for BLE operations
        self.asyncio_manager = AsyncioManager() if BLEAK_AVAILABLE else None
        
        # Setup GUI
        self.setup_gui()
        self.refresh_serial_ports()
        
        # Auto-scan for BLE devices if bleak is available (disabled to prevent asyncio issues)
        # if BLEAK_AVAILABLE:
        #     self.scan_ble_devices()
    
    def setup_gui(self):
        """Setup the main GUI layout"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # USB Serial Tab
        self.setup_serial_tab()
        
        # BLE Tab
        if BLEAK_AVAILABLE:
            self.setup_ble_tab()
        
        # Settings Tab
        self.setup_settings_tab()
        
        # Status bar
        self.setup_status_bar()
    
    def setup_serial_tab(self):
        """Setup USB Serial communication tab"""
        serial_frame = ttk.Frame(self.notebook)
        self.notebook.add(serial_frame, text="USB Serial")
        
        # Connection frame
        conn_frame = ttk.LabelFrame(serial_frame, text="Serial Connection", padding=10)
        conn_frame.pack(fill='x', padx=5, pady=5)
        
        # Port selection
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=0, sticky='w', padx=(0,5))
        self.serial_port_var = tk.StringVar(value="COM9")
        self.serial_port_combo = ttk.Combobox(conn_frame, textvariable=self.serial_port_var, width=10)
        self.serial_port_combo.grid(row=0, column=1, padx=(0,5))
        
        # Baud rate
        ttk.Label(conn_frame, text="Baud:").grid(row=0, column=2, sticky='w', padx=(10,5))
        self.baud_var = tk.StringVar(value="115200")
        baud_combo = ttk.Combobox(conn_frame, textvariable=self.baud_var, width=10,
                                 values=["9600", "19200", "38400", "57600", "115200", "230400"])
        baud_combo.grid(row=0, column=3, padx=(0,5))
        
        # Buttons
        self.refresh_btn = ttk.Button(conn_frame, text="Refresh Ports", command=self.refresh_serial_ports)
        self.refresh_btn.grid(row=0, column=4, padx=(10,5))
        
        self.serial_connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_serial_connection)
        self.serial_connect_btn.grid(row=0, column=5, padx=(5,0))
        
        # Message display frame
        msg_frame = ttk.LabelFrame(serial_frame, text="Messages", padding=10)
        msg_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Message display area
        self.serial_messages = scrolledtext.ScrolledText(msg_frame, height=15, wrap=tk.WORD)
        self.serial_messages.pack(fill='both', expand=True)
        
        # Command frame
        cmd_frame = ttk.LabelFrame(serial_frame, text="Send Command", padding=10)
        cmd_frame.pack(fill='x', padx=5, pady=5)
        
        # Command input
        self.serial_command_var = tk.StringVar()
        command_entry = ttk.Entry(cmd_frame, textvariable=self.serial_command_var)
        command_entry.pack(side='left', fill='x', expand=True, padx=(0,5))
        command_entry.bind('<Return>', self.send_serial_command)
        
        # Quick command buttons
        quick_frame = ttk.Frame(cmd_frame)
        quick_frame.pack(side='right')
        
        ttk.Button(quick_frame, text="Status (s)", command=lambda: self.send_serial_command_direct("s")).pack(side='left', padx=2)
        ttk.Button(quick_frame, text="Help (h)", command=lambda: self.send_serial_command_direct("h")).pack(side='left', padx=2)
        ttk.Button(quick_frame, text="Test (t)", command=lambda: self.send_serial_command_direct("t")).pack(side='left', padx=2)
        ttk.Button(quick_frame, text="Memory (m)", command=lambda: self.send_serial_command_direct("m")).pack(side='left', padx=2)
        ttk.Button(quick_frame, text="Send", command=self.send_serial_command).pack(side='left', padx=2)
    
    def setup_ble_tab(self):
        """Setup BLE communication tab"""
        ble_frame = ttk.Frame(self.notebook)
        self.notebook.add(ble_frame, text="BLE Communication")
        
        # Device scanning frame
        scan_frame = ttk.LabelFrame(ble_frame, text="BLE Device Scanner", padding=10)
        scan_frame.pack(fill='x', padx=5, pady=5)
        
        # Device list
        list_frame = ttk.Frame(scan_frame)
        list_frame.pack(fill='x')
        
        self.device_listbox = tk.Listbox(list_frame, height=4)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.device_listbox.yview)
        self.device_listbox.configure(yscrollcommand=scrollbar.set)
        self.device_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # BLE buttons
        ble_btn_frame = ttk.Frame(scan_frame)
        ble_btn_frame.pack(fill='x', pady=(5,0))
        
        ttk.Button(ble_btn_frame, text="Scan Devices", command=self.scan_ble_devices).pack(side='left', padx=(0,5))
        ttk.Button(ble_btn_frame, text="Inspect Device", command=self.inspect_ble_device).pack(side='left', padx=5)
        self.ble_connect_btn = ttk.Button(ble_btn_frame, text="Connect", command=self.toggle_ble_connection)
        self.ble_connect_btn.pack(side='left', padx=5)
        
        # BLE status
        self.ble_status_var = tk.StringVar(value="Not connected")
        ttk.Label(ble_btn_frame, textvariable=self.ble_status_var).pack(side='right')
        
        # BLE message display
        ble_msg_frame = ttk.LabelFrame(ble_frame, text="BLE Messages", padding=10)
        ble_msg_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.ble_messages = scrolledtext.ScrolledText(ble_msg_frame, height=10, wrap=tk.WORD)
        self.ble_messages.pack(fill='both', expand=True)
        
        # BLE command frame
        ble_cmd_frame = ttk.LabelFrame(ble_frame, text="Send BLE Message", padding=10)
        ble_cmd_frame.pack(fill='x', padx=5, pady=5)
        
        self.ble_command_var = tk.StringVar()
        ble_entry = ttk.Entry(ble_cmd_frame, textvariable=self.ble_command_var)
        ble_entry.pack(side='left', fill='x', expand=True, padx=(0,5))
        ble_entry.bind('<Return>', self.send_ble_message)
        
        ttk.Button(ble_cmd_frame, text="Send BLE", command=self.send_ble_message).pack(side='right')
    
    def setup_settings_tab(self):
        """Setup settings and information tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings & Info")
        
        # Device info frame
        info_frame = ttk.LabelFrame(settings_frame, text="Device Information", padding=10)
        info_frame.pack(fill='x', padx=5, pady=5)
        
        self.device_info = scrolledtext.ScrolledText(info_frame, height=8, wrap=tk.WORD)
        self.device_info.pack(fill='both', expand=True)
        self.device_info.insert('1.0', "XIAO ESP32S3 Communication Interface\n\n"
                                      "Features:\n"
                                      "• USB Serial communication (115200 baud)\n"
                                      "• BLE communication with GATT services\n"
                                      "• Real-time message monitoring\n"
                                      "• Interactive command interface\n\n"
                                      "BLE Service UUID: 12345678-1234-1234-1234-123456789abc\n"
                                      "BLE Characteristic UUID: 87654321-4321-4321-4321-cba987654321\n")
        
        # Settings frame
        settings_inner_frame = ttk.LabelFrame(settings_frame, text="Application Settings", padding=10)
        settings_inner_frame.pack(fill='x', padx=5, pady=5)
        
        # Auto-scroll option
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_inner_frame, text="Auto-scroll messages", variable=self.auto_scroll_var).pack(anchor='w')
        
        # Timestamp option
        self.timestamp_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_inner_frame, text="Show timestamps", variable=self.timestamp_var).pack(anchor='w')
        
        # Save/Load buttons
        btn_frame = ttk.Frame(settings_inner_frame)
        btn_frame.pack(fill='x', pady=(10,0))
        
        ttk.Button(btn_frame, text="Save Messages", command=self.save_messages).pack(side='left', padx=(0,5))
        ttk.Button(btn_frame, text="Clear All", command=self.clear_all_messages).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="About", command=self.show_about).pack(side='right')
    
    def setup_status_bar(self):
        """Setup status bar at bottom"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side='bottom', fill='x')
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var, relief='sunken').pack(side='left', fill='x', expand=True)
        
        self.connection_status_var = tk.StringVar(value="Disconnected")
        ttk.Label(status_frame, textvariable=self.connection_status_var, relief='sunken').pack(side='right')
    
    def refresh_serial_ports(self):
        """Refresh available serial ports"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.serial_port_combo['values'] = ports
        if ports and not self.serial_port_var.get() in ports:
            self.serial_port_combo.set(ports[0])
        self.update_status(f"Found {len(ports)} serial port(s)")
    
    def toggle_serial_connection(self):
        """Toggle serial connection"""
        if not self.is_connected_serial:
            self.connect_serial()
        else:
            self.disconnect_serial()
    
    def connect_serial(self):
        """Connect to serial port"""
        try:
            port = self.serial_port_var.get()
            baud = int(self.baud_var.get())
            
            self.serial_connection = serial.Serial(port, baud, timeout=1)
            self.is_connected_serial = True
            
            # Start reading thread
            self.stop_threads = False
            self.serial_thread = threading.Thread(target=self.read_serial_messages, daemon=True)
            self.serial_thread.start()
            
            # Update UI
            self.serial_connect_btn.config(text="Disconnect")
            self.update_status(f"Connected to {port} at {baud} baud")
            self.add_serial_message(f"[GUI] Connected to {port} at {baud} baud", "system")
            self.update_connection_status()
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to {port}:\n{str(e)}")
            self.update_status("Connection failed")
    
    def disconnect_serial(self):
        """Disconnect from serial port"""
        self.stop_threads = True
        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None
        
        self.is_connected_serial = False
        self.serial_connect_btn.config(text="Connect")
        self.update_status("Disconnected from serial")
        self.add_serial_message("[GUI] Disconnected from serial", "system")
        self.update_connection_status()
    
    def read_serial_messages(self):
        """Read messages from serial port in separate thread"""
        while not self.stop_threads and self.is_connected_serial:
            try:
                if self.serial_connection and self.serial_connection.in_waiting:
                    message = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                    if message:
                        self.root.after(0, lambda: self.add_serial_message(message, "received"))
                time.sleep(0.1)
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"Serial read error: {str(e)}"))
                break
    
    def send_serial_command(self, event=None):
        """Send command via serial"""
        command = self.serial_command_var.get().strip()
        if command:
            self.send_serial_command_direct(command)
            self.serial_command_var.set("")
    
    def send_serial_command_direct(self, command):
        """Send command directly via serial"""
        if not self.is_connected_serial:
            messagebox.showwarning("Not Connected", "Please connect to serial port first")
            return
        
        try:
            self.serial_connection.write(f"{command}\n".encode())
            self.add_serial_message(f"[GUI] Sent: {command}", "sent")
        except Exception as e:
            messagebox.showerror("Send Error", f"Failed to send command:\n{str(e)}")
    
    def scan_ble_devices(self):
        """Scan for BLE devices"""
        if not BLEAK_AVAILABLE:
            messagebox.showwarning("BLE Unavailable", "BLE functionality requires the 'bleak' package.\nInstall with: pip install bleak")
            return
        
        self.device_listbox.delete(0, tk.END)
        self.device_listbox.insert(0, "Scanning...")
        self.update_status("Scanning for BLE devices...")
        
        # Run scan in separate thread
        threading.Thread(target=self._scan_ble_async, daemon=True).start()
    
    def _scan_ble_async(self):
        """Async BLE scan wrapper using AsyncioManager"""
        if not self.asyncio_manager:
            self.root.after(0, lambda: self.update_status("BLE manager not available"))
            return
            
        try:
            # Use the dedicated asyncio manager
            future = self.asyncio_manager.run_async(self._scan_ble())
            devices = future.result(timeout=10)  # 10 second timeout
            self.root.after(0, lambda: self._update_device_list(devices))
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"BLE scan error: {str(e)}"))
    
    async def _scan_ble(self):
        """Scan for BLE devices"""
        devices = await BleakScanner.discover(timeout=5.0)
        return devices
    
    def _update_device_list(self, devices):
        """Update device listbox with scan results"""
        self.device_listbox.delete(0, tk.END)
        
        esp32_devices = []
        other_devices = []
        
        for device in devices:
            name = device.name or "Unknown"
            address = device.address
            display_text = f"{name} ({address})"
            
            if "XIAO" in name.upper() or "ESP32" in name.upper():
                esp32_devices.append((device, display_text))
            else:
                other_devices.append((device, display_text))
        
        # Create mapping from listbox index to actual device
        self.device_index_map = {}
        listbox_index = 0
        
        # Add ESP32 devices first with highlighting
        for device, display_text in esp32_devices:
            self.device_listbox.insert(tk.END, f"🎯 {display_text}")
            self.device_index_map[listbox_index] = device
            listbox_index += 1
        
        # Add separator if both types exist (don't map this to a device)
        if esp32_devices and other_devices:
            self.device_listbox.insert(tk.END, "--- Other Devices ---")
            listbox_index += 1  # Skip separator in mapping
        
        # Add other devices
        for device, display_text in other_devices:
            self.device_listbox.insert(tk.END, f"📱 {display_text}")
            self.device_index_map[listbox_index] = device
            listbox_index += 1
        
        self.ble_devices = devices
        self.update_status(f"Found {len(devices)} BLE device(s)")
    
    def inspect_ble_device(self):
        """Inspect selected BLE device to show its services and characteristics"""
        selection = self.device_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a BLE device first")
            return
        
        listbox_index = selection[0]
        
        # Check if we have a device mapping for this index
        if not hasattr(self, 'device_index_map') or listbox_index not in self.device_index_map:
            messagebox.showwarning("Invalid Selection", "Please select a valid BLE device (not a separator)")
            return
        
        device = self.device_index_map[listbox_index]
        threading.Thread(target=self._inspect_ble_async, args=(device,), daemon=True).start()
    
    def _inspect_ble_async(self, device):
        """Async BLE device inspection"""
        if not self.asyncio_manager:
            self.root.after(0, lambda: self.update_status("BLE manager not available"))
            return
            
        try:
            future = self.asyncio_manager.run_async(self._inspect_ble(device))
            services_info = future.result(timeout=10)
            self.root.after(0, lambda: self._show_device_info(device, services_info))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Inspection Error", f"Failed to inspect device:\n{str(e)}"))
    
    async def _inspect_ble(self, device):
        """Inspect BLE device services and characteristics"""
        client = BleakClient(device.address)
        try:
            await client.connect()
            services = client.services
            
            services_info = []
            target_service_found = False
            target_char_found = False
            
            for service in services:
                service_info = {
                    'uuid': service.uuid,
                    'description': service.description,
                    'characteristics': []
                }
                
                if service.uuid.lower() == self.SERVICE_UUID.lower():
                    target_service_found = True
                
                for char in service.characteristics:
                    char_info = {
                        'uuid': char.uuid,
                        'properties': char.properties,
                        'description': char.description or "Unknown"
                    }
                    
                    if char.uuid.lower() == self.CHARACTERISTIC_UUID.lower():
                        target_char_found = True
                        char_info['is_target'] = True
                    
                    service_info['characteristics'].append(char_info)
                
                if service.uuid.lower() == self.SERVICE_UUID.lower():
                    service_info['is_target'] = True
                
                services_info.append(service_info)
            
            return {
                'services': services_info,
                'target_service_found': target_service_found,
                'target_char_found': target_char_found
            }
        
        finally:
            if client.is_connected:
                await client.disconnect()
    
    def _show_device_info(self, device, services_info):
        """Show device inspection results"""
        info_window = tk.Toplevel(self.root)
        info_window.title(f"BLE Device Inspector - {device.name}")
        info_window.geometry("800x600")
        
        # Create scrolled text widget
        info_text = scrolledtext.ScrolledText(info_window, wrap=tk.WORD, font=('Consolas', 10))
        info_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Device header
        info_text.insert(tk.END, f"Device Information\n")
        info_text.insert(tk.END, f"=" * 50 + "\n")
        info_text.insert(tk.END, f"Name: {device.name or 'Unknown'}\n")
        info_text.insert(tk.END, f"Address: {device.address}\n")
        info_text.insert(tk.END, f"RSSI: {getattr(device, 'rssi', 'Unknown')} dBm\n\n")
        
        # Target service/characteristic status
        info_text.insert(tk.END, f"ESP32S3 Compatibility Check\n")
        info_text.insert(tk.END, f"-" * 30 + "\n")
        
        if services_info['target_service_found']:
            info_text.insert(tk.END, f"✅ Target Service Found: {self.SERVICE_UUID}\n")
        else:
            info_text.insert(tk.END, f"❌ Target Service Missing: {self.SERVICE_UUID}\n")
        
        if services_info['target_char_found']:
            info_text.insert(tk.END, f"✅ Target Characteristic Found: {self.CHARACTERISTIC_UUID}\n")
        else:
            info_text.insert(tk.END, f"❌ Target Characteristic Missing: {self.CHARACTERISTIC_UUID}\n")
        
        if services_info['target_service_found'] and services_info['target_char_found']:
            info_text.insert(tk.END, f"\n🎉 This device appears to be compatible with your ESP32S3!\n\n")
        else:
            info_text.insert(tk.END, f"\n⚠️  This device may not be your ESP32S3 or may be running different firmware.\n\n")
        
        # Services and characteristics
        info_text.insert(tk.END, f"Available Services and Characteristics\n")
        info_text.insert(tk.END, f"=" * 50 + "\n\n")
        
        for service in services_info['services']:
            is_target = service.get('is_target', False)
            prefix = "🎯 " if is_target else "📡 "
            
            info_text.insert(tk.END, f"{prefix}Service: {service['uuid']}\n")
            info_text.insert(tk.END, f"   Description: {service['description']}\n")
            
            for char in service['characteristics']:
                is_target_char = char.get('is_target', False)
                char_prefix = "  🎯 " if is_target_char else "  📝 "
                
                info_text.insert(tk.END, f"{char_prefix}Characteristic: {char['uuid']}\n")
                info_text.insert(tk.END, f"     Properties: {char['properties']}\n")
                info_text.insert(tk.END, f"     Description: {char['description']}\n")
            
            info_text.insert(tk.END, "\n")
        
        info_text.config(state='disabled')
    
    def toggle_ble_connection(self):
        """Toggle BLE connection"""
        if not self.is_connected_ble:
            self.connect_ble()
        else:
            self.disconnect_ble()
    
    def connect_ble(self):
        """Connect to selected BLE device"""
        selection = self.device_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a BLE device first")
            return
        
        listbox_index = selection[0]
        
        # Check if we have a device mapping for this index
        if not hasattr(self, 'device_index_map') or listbox_index not in self.device_index_map:
            messagebox.showwarning("Invalid Selection", "Please select a valid BLE device (not a separator)")
            return
        
        device = self.device_index_map[listbox_index]
        threading.Thread(target=self._connect_ble_async, args=(device,), daemon=True).start()
    
    def _connect_ble_async(self, device):
        """Async BLE connection wrapper using AsyncioManager"""
        if not self.asyncio_manager:
            self.root.after(0, lambda: self.update_status("BLE manager not available"))
            return
            
        try:
            # Use the dedicated asyncio manager
            future = self.asyncio_manager.run_async(self._connect_ble(device))
            future.result(timeout=10)  # 10 second timeout
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"BLE connection error: {str(e)}"))
    
    async def _connect_ble(self, device):
        """Connect to BLE device"""
        try:
            self.ble_client = BleakClient(device.address)
            await self.ble_client.connect()
            
            # Check if device has our custom service and characteristic
            services = self.ble_client.services
            service_found = False
            characteristic_found = False
            
            for service in services:
                if service.uuid.lower() == self.SERVICE_UUID.lower():
                    service_found = True
                    for char in service.characteristics:
                        if char.uuid.lower() == self.CHARACTERISTIC_UUID.lower():
                            characteristic_found = True
                            break
                    break
            
            if not service_found:
                await self.ble_client.disconnect()
                self.root.after(0, lambda: messagebox.showerror("BLE Error", 
                    f"Device '{device.name}' does not have the required service.\n\n"
                    f"Expected Service UUID: {self.SERVICE_UUID}\n\n"
                    f"This device may not be your XIAO ESP32S3. Please select the correct device."))
                return
            
            if not characteristic_found:
                await self.ble_client.disconnect()
                self.root.after(0, lambda: messagebox.showerror("BLE Error", 
                    f"Device '{device.name}' does not have the required characteristic.\n\n"
                    f"Expected Characteristic UUID: {self.CHARACTERISTIC_UUID}\n\n"
                    f"Make sure your ESP32S3 is running the correct firmware."))
                return
            
            # Subscribe to notifications
            await self.ble_client.start_notify(self.CHARACTERISTIC_UUID, self._ble_notification_handler)
            
            self.is_connected_ble = True
            self.root.after(0, lambda: self._ble_connected(device))
            
        except Exception as e:
            if self.ble_client:
                try:
                    await self.ble_client.disconnect()
                except:
                    pass
            self.root.after(0, lambda: messagebox.showerror("BLE Error", f"Failed to connect to '{device.name}':\n{str(e)}"))
    
    def _ble_connected(self, device):
        """Handle successful BLE connection"""
        self.ble_connect_btn.config(text="Disconnect")
        self.ble_status_var.set(f"Connected to {device.name}")
        self.update_status(f"Connected to BLE device: {device.name}")
        self.add_ble_message(f"[GUI] Connected to {device.name} ({device.address})", "system")
        self.update_connection_status()
    
    def disconnect_ble(self):
        """Disconnect from BLE device"""
        if self.ble_client:
            threading.Thread(target=self._disconnect_ble_async, daemon=True).start()
    
    def _disconnect_ble_async(self):
        """Async BLE disconnection wrapper"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            if self.ble_client:
                loop.run_until_complete(self.ble_client.disconnect())
        except Exception as e:
            print(f"BLE disconnect error: {e}")
        finally:
            loop.close()
            self.root.after(0, self._ble_disconnected)
    
    def _ble_disconnected(self):
        """Handle BLE disconnection"""
        self.ble_client = None
        self.is_connected_ble = False
        self.ble_connect_btn.config(text="Connect")
        self.ble_status_var.set("Not connected")
        self.update_status("Disconnected from BLE")
        self.add_ble_message("[GUI] Disconnected from BLE", "system")
        self.update_connection_status()
    
    def _ble_notification_handler(self, sender, data):
        """Handle BLE notifications"""
        try:
            message = data.decode('utf-8', errors='ignore').strip()
            self.root.after(0, lambda: self.add_ble_message(f"[BLE] {message}", "received"))
        except Exception as e:
            print(f"BLE notification error: {e}")
    
    def send_ble_message(self, event=None):
        """Send message via BLE"""
        if not self.is_connected_ble:
            messagebox.showwarning("Not Connected", "Please connect to BLE device first")
            return
        
        message = self.ble_command_var.get().strip()
        if message:
            threading.Thread(target=self._send_ble_async, args=(message,), daemon=True).start()
            self.ble_command_var.set("")
    
    def _send_ble_async(self, message):
        """Async BLE message sending wrapper using AsyncioManager"""
        if not self.asyncio_manager:
            self.root.after(0, lambda: messagebox.showerror("BLE Error", "BLE manager not available"))
            return
            
        try:
            # Use the dedicated asyncio manager
            future = self.asyncio_manager.run_async(self._send_ble(message))
            future.result(timeout=5)  # 5 second timeout
            self.root.after(0, lambda: self.add_ble_message(f"[GUI] Sent: {message}", "sent"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("BLE Send Error", f"Failed to send message:\n{str(e)}"))
    
    async def _send_ble(self, message):
        """Send message via BLE"""
        if self.ble_client:
            await self.ble_client.write_gatt_char(self.CHARACTERISTIC_UUID, message.encode())
    
    def add_serial_message(self, message, msg_type):
        """Add message to serial display"""
        timestamp = datetime.now().strftime("%H:%M:%S") if self.timestamp_var.get() else ""
        
        if msg_type == "sent":
            prefix = "→ "
        elif msg_type == "received":
            prefix = "← "
        else:
            prefix = "● "
        
        full_message = f"{timestamp} {prefix}{message}\n" if timestamp else f"{prefix}{message}\n"
        
        self.serial_messages.insert(tk.END, full_message)
        if self.auto_scroll_var.get():
            self.serial_messages.see(tk.END)
        
        self.message_count += 1
    
    def add_ble_message(self, message, msg_type):
        """Add message to BLE display"""
        timestamp = datetime.now().strftime("%H:%M:%S") if self.timestamp_var.get() else ""
        
        if msg_type == "sent":
            prefix = "→ "
        elif msg_type == "received":
            prefix = "← "
        else:
            prefix = "● "
        
        full_message = f"{timestamp} {prefix}{message}\n" if timestamp else f"{prefix}{message}\n"
        
        self.ble_messages.insert(tk.END, full_message)
        if self.auto_scroll_var.get():
            self.ble_messages.see(tk.END)
        
        self.message_count += 1
    
    def clear_all_messages(self):
        """Clear all message displays"""
        self.serial_messages.delete(1.0, tk.END)
        if hasattr(self, 'ble_messages'):
            self.ble_messages.delete(1.0, tk.END)
        self.message_count = 0
        self.update_status("All messages cleared")
    
    def save_messages(self):
        """Save messages to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("XIAO ESP32S3 Communication Log\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write("USB Serial Messages:\n")
                    f.write("-" * 20 + "\n")
                    f.write(self.serial_messages.get(1.0, tk.END))
                    
                    if hasattr(self, 'ble_messages'):
                        f.write("\nBLE Messages:\n")
                        f.write("-" * 20 + "\n")
                        f.write(self.ble_messages.get(1.0, tk.END))
                
                self.update_status(f"Messages saved to {filename}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save messages:\n{str(e)}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """XIAO ESP32S3 Communication Interface

A Python GUI application for communicating with the XIAO ESP32S3 
development board via USB Serial and Bluetooth Low Energy (BLE).

Features:
• USB Serial communication with configurable baud rates
• BLE device scanning and GATT communication
• Real-time message monitoring and logging
• Interactive command interface with quick buttons
• Message saving and timestamps
• Cross-platform compatibility

Requirements:
• Python 3.7 or newer
• pyserial library for USB Serial communication
• bleak library for BLE communication (optional)
• tkinter (included with most Python installations)

Created with GitHub Copilot
November 2025"""
        
        messagebox.showinfo("About", about_text)
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def update_connection_status(self):
        """Update connection status display"""
        status_parts = []
        if self.is_connected_serial:
            status_parts.append("Serial")
        if self.is_connected_ble:
            status_parts.append("BLE")
        
        if status_parts:
            self.connection_status_var.set(f"Connected: {', '.join(status_parts)}")
        else:
            self.connection_status_var.set("Disconnected")
    
    def on_closing(self):
        """Handle application closing"""
        self.stop_threads = True
        
        # Disconnect from devices
        if self.is_connected_serial:
            self.disconnect_serial()
        if self.is_connected_ble:
            self.disconnect_ble()
        
        # Shutdown asyncio manager
        if self.asyncio_manager:
            self.asyncio_manager.shutdown()
        
        # Wait a moment for cleanup
        time.sleep(0.5)
        self.root.destroy()

def main():
    """Main application entry point"""
    root = tk.Tk()
    app = ESP32S3_GUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.on_closing()

if __name__ == "__main__":
    main()