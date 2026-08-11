#include <WiFi.h>

// Wi-Fi Access Point Credentials
const char* ssid = "ESP32_Ultrasonic";
const char* password = "password123"; // Must be at least 8 characters

int distance1;
int distance2;

// --- State and Animation Tracker Variables ---
int counter = 0;
int currentState = -1; // 0 = too close, 1 = okay, 2 = too far
int distance = 0;

#include <Wire.h>
#include <VL53L0X_mod.h>
#include <U8g2lib.h> // Library for SSD1309 OLED
#include "animation.h"

// Control pins for Sensor XSHUT
#define XSHUT_PIN_1 16
#define XSHUT_PIN_2 17

// Initialize SSD1309 128x64 display over I2C (Address 0x3C typically)
// Adjust driver constructor if your breakout uses a specific reset pin
U8G2_SSD1309_128X64_NONAME0_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);

// Create sensor objects
VL53L0X_mod sensor1;
VL53L0X_mod sensor2;

// VL53L0X_mod sensor;

// Create a TCP server on port 8080
WiFiServer server(8080);

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22); // ESP32 default I2C pins (SDA=21, SCL=22)
  Wire.setClock(100000); // 100kHz fast I2C mode

  // Configure XSHUT pins as outputs
  pinMode(XSHUT_PIN_1, OUTPUT);
  pinMode(XSHUT_PIN_2, OUTPUT);

  // Initialize SSD1309 Display
  u8g2.begin();

  // STEP 1: Keep both sensors in reset state (LOW)
  digitalWrite(XSHUT_PIN_1, LOW);
  digitalWrite(XSHUT_PIN_2, LOW);
  delay(10);

  // STEP 2: Power up Sensor 1
  digitalWrite(XSHUT_PIN_1, HIGH);
  delay(10);

  sensor1.setTimeout(500);
  if (!sensor1.init()) {
    Serial.println("Failed to detect Sensor 1!");
    while (1);
  }

  // Reassign Sensor 1 address from 0x29 (default) to 0x30
  sensor1.setAddress(0x30);
  Serial.println("Sensor 1 initialized at 0x30");

  // STEP 3: Power up Sensor 2
  digitalWrite(XSHUT_PIN_2, HIGH);
  delay(10);

  sensor2.setTimeout(500);
  if (!sensor2.init()) {
    Serial.println("Failed to detect Sensor 2!");
    while (1);
  }
  // Sensor 2 stays at default address 0x29
  Serial.println("Sensor 2 initialized at 0x29");

  // Note: continuous measurement start calls (startContinuous) are omitted for single-shot mode

  //old laser init
  // Serial.print("laser test init");
  // Wire.begin();  // use default SDA (21), SCL (22)
  // sensor.init();
  // sensor.setTimeout(500);

  // Set up the ESP32 as a Wi-Fi Access Point
  Serial.println("\nSetting up Access Point...");
  WiFi.softAP(ssid, password);
  
  IPAddress IP = WiFi.softAPIP();
  Serial.print("AP IP address: ");
  Serial.println(IP); // By default, this is usually 192.168.4.1

  // Start the TCP server
  server.begin();
  Serial.println("Server started. Waiting for clients...");
}

void loop() {
  // Read distance in millimeters using single-shot mode
  distance1 = sensor1.readRangeSingleMillimeters();
  distance2 = sensor2.readRangeSingleMillimeters();

  Serial.print("Sensor 1 (0x30): ");
  if (sensor1.timeoutOccurred()) {
    Serial.print("TIMEOUT ");
  } else {
    Serial.print(distance1);
    Serial.print(" mm");
  }

  Serial.print(" | Sensor 2 (0x29): ");
  if (sensor2.timeoutOccurred()) {
    Serial.print("TIMEOUT");
  } else {
    Serial.print(distance2);
    Serial.print(" mm");
  }

  Serial.println();
  // Check if a client has connected
  WiFiClient client = server.available();

  if (client) {
    Serial.println("New Client Connected.");
    
    // While the client remains connected, send sensor data
    while (client.connected()) {
      // Send the data over Wi-Fi as a string followed by a newline
      // if (distance1 < 50 && distance2 < 50) {
      //   client.println("too close");
      // }
      // else if (distance1 < 150 && distance2 < 150) {
      //   client.println("okay");
      // }
      // else {
      //   client.println("too far");
      // }
      distance1 = sensor1.readRangeSingleMillimeters();
      distance2 = sensor2.readRangeSingleMillimeters();

      handleStateAndAnimation(&client);
      delay(30); 

      Serial.print("Sensor 1 (0x30): ");
      if (sensor1.timeoutOccurred()) {
        Serial.print("TIMEOUT ");
      } else {
        Serial.print(distance1);
        Serial.print(" mm");
      }

      Serial.print(" | Sensor 2 (0x29): ");
      if (sensor2.timeoutOccurred()) {
        Serial.print("TIMEOUT");
      } else {
        Serial.print(distance2);
        Serial.print(" mm");
      }
      Serial.println();
      // distance = sensor.readRangeSingleMillimeters();
      // Serial.print("Distance: ");
      // Serial.print(distance);
      // Serial.println(" mm");
      // Wait 100 milliseconds before sending the next reading
      delay(100); 
    }

    // Disconnect the client
    client.stop();
    Serial.println("Client Disconnected.");
  }
  
  // distance = sensor.readRangeSingleMillimeters();
  // Serial.print("Distance: ");
  // Serial.print(distance);
  // Serial.println(" mm");
  
      
  // client.println("too far");
  handleStateAndAnimation(NULL);
  delay(200);
}

void handleStateAndAnimation(WiFiClient* client) {
  int newState;

  // 1. Evaluate distance ranges and output Wi-Fi status string
  if (distance1 < 50 && distance2 < 50) {
    newState = 0; // "too close"
    if (client && client->connected()) client->println("too close");
  } else if (distance1 < 150 && distance2 < 150) {
    newState = 1; // "okay"
    if (client && client->connected()) client->println("okay");
  } else {
    newState = 2; // "too far"
    if (client && client->connected()) client->println("too far");
  }

  // 2. Reset frame counter when entering a new zone
  if (newState != currentState) {
    currentState = newState;
    counter = 0; 
  }

  // 3. Render single-loop animation frame
  u8g2.clearBuffer();

  if (currentState == 0) {
    u8g2.drawXBMP(0, 0, 128, 50, (const unsigned char*)pgm_read_ptr(&(epd_bitmap_tooClose[counter]))); 
    if (counter < FRAMES_TOO_CLOSE - 1) counter++;

  } else if (currentState == 1) {
    u8g2.drawXBMP(0, 0, 128, 50, (const unsigned char*)pgm_read_ptr(&(epd_bitmap_okay[counter]))); 
    if (counter < FRAMES_OKAY - 1) counter++;

  } else if (currentState == 2) {
    u8g2.drawXBMP(0, 0, 128, 50, (const unsigned char*)pgm_read_ptr(&(epd_bitmap_tooFar[counter]))); 
    if (counter < FRAMES_TOO_FAR - 1) counter++;
  }

  u8g2.sendBuffer();
}