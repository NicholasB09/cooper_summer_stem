#include <Arduino.h>
#include <WiFi.h>
#include <Wire.h>
#include <VL53L0X_mod.h>
#include <U8g2lib.h>

// Include your custom header containing all bitmaps and frame arrays
#include "animation.h"

// --- Wi-Fi Access Point Credentials ---
const char* ssid = "ESP32_Ultrasonic";
const char* password = "password123";

// --- Display Object Setup ---
// Replace this driver line with your specific display model if different
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);

// --- State and Animation Tracker Variables ---
int counter = 0;
int currentState = -1; // 0 = too close, 1 = okay, 2 = too far
int distance = 0;

VL53L0X_mod sensor;
WiFiServer server(8080);

void handleStateAndAnimation(WiFiClient* client);

void setup() {
  Serial.begin(115200);

  // Initialize I2C and VL53L0X sensor
  Wire.begin();
  sensor.init();
  sensor.setTimeout(500);

  // Initialize U8g2 Display
  u8g2.begin();

  // Configure ESP32 Access Point
  Serial.println("\nSetting up Access Point...");
  WiFi.softAP(ssid, password);
  
  IPAddress IP = WiFi.softAPIP();
  Serial.print("AP IP address: ");
  Serial.println(IP);

  // Start TCP Server
  server.begin();
  Serial.println("Server started. Waiting for clients...");
}

void loop() {
  // Read distance from VL53L0X
  distance = sensor.readRangeSingleMillimeters();

  WiFiClient client = server.available();
  if (client) {
    Serial.println("New Client Connected.");
    
    while (client.connected()) {
      distance = sensor.readRangeSingleMillimeters();
      handleStateAndAnimation(&client);
      delay(30); 
    }

    client.stop();
    Serial.println("Client Disconnected.");
  }

  // Handle animation logic when no Wi-Fi client is connected
  handleStateAndAnimation(NULL);
  delay(30);
}

void handleStateAndAnimation(WiFiClient* client) {
  int newState;

  // 1. Evaluate distance ranges and output Wi-Fi status string
  if (distance < 50) {
    newState = 0; // "too close"
    if (client && client->connected()) client->println("too close");
  } else if (distance < 150) {
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