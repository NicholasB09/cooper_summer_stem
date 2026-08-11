#include <WiFi.h>

// Wi-Fi Access Point Credentials
const char* ssid = "ESP32_Ultrasonic";
const char* password = "password123"; // Must be at least 8 characters

int distance;

#include <Wire.h>
#include <VL53L0X_mod.h>

VL53L0X_mod sensor;

// Create a TCP server on port 8080
WiFiServer server(8080);

void setup() {
  Serial.begin(115200);

  Serial.print("laser test init");
  Wire.begin();  // use default SDA (21), SCL (22)
  sensor.init();
  sensor.setTimeout(500);

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
  // Check if a client has connected
  WiFiClient client = server.available();

  if (client) {
    Serial.println("New Client Connected.");
    
    // While the client remains connected, send sensor data
    while (client.connected()) {
      // Send the data over Wi-Fi as a string followed by a newline
      if (distance < 50) {
        client.println("too close");
      }
      else if (distance < 150) {
        client.println("okay");
      }
      else {
        client.println("too far");
      }

      distance = sensor.readRangeSingleMillimeters();
      Serial.print("Distance: ");
      Serial.print(distance);
      Serial.println(" mm");
      // Wait 100 milliseconds before sending the next reading
      delay(100); 
    }

    // Disconnect the client
    client.stop();
    Serial.println("Client Disconnected.");
  }

  distance = sensor.readRangeSingleMillimeters();
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" mm");
  
      
  // client.println("too far");
  delay(200);
}