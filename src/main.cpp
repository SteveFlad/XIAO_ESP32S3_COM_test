/*
 * XIAO ESP32S3 Communication Test Program
 * Tests USB Serial (COM9) and BLE connections
 * 
 * Features:
 * - USB Serial communication test
 * - BLE (Bluetooth Low Energy) advertising and GATT server
 * - Interactive command interface
 * - Connection status monitoring
 * 
 * Note: ESP32-S3 primarily supports BLE, not Bluetooth Classic (SPP)
 */

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// BLE Configuration
#define SERVICE_UUID        "12345678-1234-1234-1234-123456789abc"
#define CHARACTERISTIC_UUID "87654321-4321-4321-4321-cba987654321"

BLEServer* pServer = nullptr;
BLECharacteristic* pCharacteristic = nullptr;
bool bleConnected = false;

// Test counters
unsigned long lastStatusUpdate = 0;
unsigned long testCounter = 0;
unsigned long usbMessageCount = 0;
unsigned long bleMessageCount = 0;

// BLE Server Callbacks
class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        bleConnected = true;
        Serial.println("[BLE] Client connected");
    };

    void onDisconnect(BLEServer* pServer) {
        bleConnected = false;
        Serial.println("[BLE] Client disconnected");
        // Restart advertising
        BLEDevice::startAdvertising();
    }
};

// Forward declarations
void processCommand(String input, bool isBLE);

// BLE Characteristic Callbacks
class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        std::string rxValue = pCharacteristic->getValue();
        bleMessageCount++;
        
        if (rxValue.length() > 0) {
            String input = String(rxValue.c_str());
            input.trim();
            
            Serial.print("[BLE] Received: ");
            Serial.println(input);
            
            // Process command and get response
            processCommand(input, true);
        }
    }
};



void setupBLE() {
    Serial.println("[Setup] Initializing BLE...");
    
    BLEDevice::init("XIAO-ESP32S3-Test");
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    BLEService *pService = pServer->createService(SERVICE_UUID);
    
    pCharacteristic = pService->createCharacteristic(
                        CHARACTERISTIC_UUID,
                        BLECharacteristic::PROPERTY_READ |
                        BLECharacteristic::PROPERTY_WRITE |
                        BLECharacteristic::PROPERTY_NOTIFY
                    );

    pCharacteristic->setCallbacks(new MyCallbacks());
    pCharacteristic->addDescriptor(new BLE2902());
    pCharacteristic->setValue("Hello from XIAO ESP32S3!");
    
    pService->start();
    
    // Start the BLE server
    pServer->getAdvertising()->start();
    
    // Configure advertising for better visibility
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06);  // Help with iPhone connections
    pAdvertising->setMaxPreferred(0x12);
    
    // Set device as connectable and discoverable
    BLEDevice::startAdvertising();
    
    Serial.println("[BLE] Server started, advertising as 'XIAO-ESP32S3-Test'");
    Serial.println("[BLE] Service UUID: " + String(SERVICE_UUID));
    Serial.println("[BLE] Device should now be discoverable!");
}



void printMenu() {
    Serial.println("\n=== XIAO ESP32S3 Communication Test ===");
    Serial.println("Commands:");
    Serial.println("  h - Show this help menu");
    Serial.println("  s - Show connection status");
    Serial.println("  t - Send test message to all connected devices");
    Serial.println("  r - Restart BLE advertising");
    Serial.println("  c - Show message counters");
    Serial.println("  m - Show memory info");
    Serial.println("  Any other text will be echoed back");
    Serial.println("=========================================\n");
}

void showStatus() {
    Serial.println("\n=== Connection Status ===");
    Serial.println("USB Serial: Connected (you're reading this!)");
    Serial.println("BLE: " + String(bleConnected ? "Connected" : "Advertising"));
    Serial.println("Uptime: " + String(millis() / 1000) + " seconds");
    Serial.println("Free heap: " + String(ESP.getFreeHeap()) + " bytes");
    Serial.println("========================\n");
}

void sendTestMessage() {
    testCounter++;
    String message = "Test message #" + String(testCounter) + " from XIAO ESP32S3";
    
    Serial.println("[USB] Sending: " + message);
    
    if (bleConnected && pCharacteristic) {
        String bleMessage = "[BLE] " + message;
        pCharacteristic->setValue(bleMessage.c_str());
        pCharacteristic->notify();
        Serial.println("[BLE] Message sent");
    } else {
        Serial.println("[BLE] No connection - message not sent");
    }
}

void showCounters() {
    Serial.println("\n=== Message Counters ===");
    Serial.println("USB messages received: " + String(usbMessageCount));
    Serial.println("BLE messages: " + String(bleMessageCount));
    Serial.println("Test messages sent: " + String(testCounter));
    Serial.println("========================\n");
}

void showMemoryInfo() {
    Serial.println("\n=== Memory Information ===");
    Serial.println("Free heap: " + String(ESP.getFreeHeap()) + " bytes");
    Serial.println("Largest free block: " + String(ESP.getMaxAllocHeap()) + " bytes");
    Serial.println("Total heap size: " + String(ESP.getHeapSize()) + " bytes");
    Serial.println("Free PSRAM: " + String(ESP.getFreePsram()) + " bytes");
    Serial.println("==========================\n");
}

void processCommand(String input, bool isBLE) {
    String response = "";
    
    if (input == "h") {
        printMenu();
        response = "Help menu sent to USB Serial";
    } else if (input == "s") {
        showStatus();
        response = "Status info sent to USB Serial";
    } else if (input == "t") {
        sendTestMessage();
        response = "Test message sent";
    } else if (input == "r") {
        BLEDevice::startAdvertising();
        Serial.println("[BLE] Advertising restarted");
        response = "BLE advertising restarted";
    } else if (input == "c") {
        showCounters();
        response = "Counters sent to USB Serial";
    } else if (input == "m") {
        showMemoryInfo();
        response = "Memory info sent to USB Serial";
    } else if (input.length() > 0) {
        response = "Echo: " + input;
        if (!isBLE) {
            Serial.println("[USB Echo] You sent: " + input);
        }
    }
    
    // Send response back via BLE if this was a BLE command
    if (isBLE && bleConnected && pCharacteristic && response.length() > 0) {
        pCharacteristic->setValue(response.c_str());
        pCharacteristic->notify();
    }
}

void setup() {
    // Initialize USB Serial
    Serial.begin(115200);
    delay(2000); // Give time for serial monitor to connect
    
    Serial.println("\n*** XIAO ESP32S3 Communication Test Starting ***");
    Serial.println("Board: Seeed XIAO ESP32S3");
    Serial.println("USB Port: COM9");
    Serial.println("Baud Rate: 115200");
    
    // Initialize BLE
    setupBLE();
    
    // Show initial status and menu
    showStatus();
    printMenu();
    
    lastStatusUpdate = millis();
    
    Serial.println("[Setup] All communication channels initialized!");
    Serial.println("[Setup] Ready for testing...");
}

void loop() {
    // Handle USB Serial input
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        input.trim();
        usbMessageCount++;
        
        processCommand(input, false);
    }
    

    
    // Periodic status update every 30 seconds
    if (millis() - lastStatusUpdate > 30000) {
        Serial.println("\n[Periodic Update] System running - " + String(millis() / 1000) + "s uptime");
        Serial.println("Connections: USB=Active, BLE=" + String(bleConnected ? "Connected" : "Advertising"));
        lastStatusUpdate = millis();
    }
    
    delay(100); // Small delay to prevent overwhelming the serial output
}