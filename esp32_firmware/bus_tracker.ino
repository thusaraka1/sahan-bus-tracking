/*
 * AI-Powered IoT Bus Tracking System
 * ESP32 Firmware - GPS Data Collection & MQTT Publishing
 * 
 * Hardware:
 *   - ESP32 Dev Module
 *   - NEO-6M GPS Module (TX->GPIO16, RX->GPIO17)
 * 
 * Dependencies (Install via Arduino Library Manager):
 *   - TinyGPSPlus by Mikal Hart
 *   - PubSubClient by Nick O'Leary
 *   - WiFiClientSecure (built-in with ESP32 board package)
 * 
 * Setup:
 *   1. Install ESP32 board package in Arduino IDE
 *   2. Install the above libraries
 *   3. Update WiFi and HiveMQ credentials below
 *   4. Select board: "ESP32 Dev Module"
 *   5. Upload to ESP32
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <TinyGPSPlus.h>
#include <HardwareSerial.h>

// ============================================================
// CONFIGURATION - Update these values with your credentials
// ============================================================

// WiFi Configuration
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD  = "YOUR_WIFI_PASSWORD";

// HiveMQ Cloud Configuration
const char* MQTT_BROKER    = "b5ad82f71b0d40d6bcf02b00ce1cd933.s1.eu.hivemq.cloud";
const int   MQTT_PORT      = 8883;  // TLS port
const char* MQTT_USERNAME  = "Bus_track";
const char* MQTT_PASSWORD  = "Bus@12345";

// Bus Configuration
const char* BUS_ID         = "BUS_001";
const char* ROUTE_ID       = "ROUTE_A";
const char* BUS_NAME       = "Colombo - Kandy Express";

// MQTT Topic
// Format: bus/{bus_id}/location
char MQTT_TOPIC[64];

// GPS Module pins (Hardware Serial 2)
#define GPS_RX_PIN 16
#define GPS_TX_PIN 17
#define GPS_BAUD   9600

// Data transmission interval (milliseconds)
#define PUBLISH_INTERVAL 5000  // Send data every 5 seconds

// Status LED
#define LED_PIN 2  // Built-in LED on most ESP32 boards

// ============================================================
// GLOBAL OBJECTS
// ============================================================

TinyGPSPlus gps;
HardwareSerial gpsSerial(2);  // Use UART2
WiFiClientSecure espClient;
PubSubClient mqttClient(espClient);

unsigned long lastPublishTime = 0;
unsigned long lastGPSCheck = 0;
int satelliteCount = 0;
bool gpsFixed = false;

// ============================================================
// HiveMQ Cloud Root CA Certificate
// This is the ISRG Root X1 certificate used by Let's Encrypt
// (HiveMQ Cloud uses Let's Encrypt certificates)
// ============================================================
static const char* root_ca PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMTUwNjA0MTEwNDM4
WhcNMzUwNjA0MTEwNDM4WjBPMQswCQYDVQQGEwJVUzEpMCcGA1UEChMgSW50ZXJu
ZXQgU2VjdXJpdHkgUmVzZWFyY2ggR3JvdXAxFTATBgNVBAMTDElTUkcgUm9vdCBY
MTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAK3oJHP0FDfzm54rVygc
h77ct984kIxuPOZXoHj3dcKi/vVqbvYATyjb3miGbESTtrFj/RQSa78f0uoxmyF+
0TM8ukj13Xnfs7j/EvEhmkvBioZxaUpmZmyPfjxwv60pIgbz5MDmgK7iS4+3mX6U
A5/TR5d8mUgjU+g4rk8Kb4Mu0UlXjIB0ttov0DiNewNwIRt18jA8+o+u3dpjq+sW
T8KOEUt+zwvo/7V3LvSye0rgTBIlDHCNAymg4VMk7BPZ7hm/ELNKjD+Jo2FR3qyH
B5T0Y3HsLuJvW5iB4YlcNHlsdu87kGJ55tukmi8mxdAQ4Q7e2RCOFvu396j3x+UC
B5iPNgiV5+I3lg02dZ77DnKxHZu8A/lJBdiB3QW0KtZB6awBdpUKD9jf1b0SHzUv
KBds0pjBqAlkd25HN7rOrFleaJ1/ctaJxQZBKT5ZPt0m9STJEadao0xAH0ahmbWn
OlFuhjuefXKnEgV4We0+UXgVCwOPjdAvBbI+e0ocS3MFEvzG6uBQE3xDk3SzynTn
jh8BCNAw1FtxNrQHusEwMFxIt4I7mKZ9YIqioymCzLq9gwQbooMDQaHWBfEbwrbw
qHyGO0aoSCqI3Haadr8faqU9GY/rOPNk3sgrDQoo//fb4hVC1CLQJ13hef4Y53CI
rU7m2Ys6xt0nUW7/vGT1M0NPAgMBAAGjQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNV
HRMBAf8EBTADAQH/MB0GA1UdDgQWBBR5tFnme7bl5AFzgAiIyBpY9umbbjANBgkq
hkiG9w0BAQsFAAOCAgEAVR9YqbyyqFDQDLHYGmkgJykIrGF1XIpu+ILlaS/V9lZL
ubhzEFnTIZd+50xx+7LSYK05qAvqFyFWhfFQDlnrzuBZ6brJFe+GnY+EgPbk6ZGQ
3BebYhtF8GaV0nxvwuo77x/Py9auJ/GpsMiu/X1+mvoiBOv/2X/qkSsisRcOj/KK
NFtY2PwByVS5uCbMiogZiUwYkLFEh9J61TnqRpC9/5D+IW/ES2B0YfkEzMVOBpo8
bbCNdkYhiGNzwDBNvag4LoH0wnKNXn3EY9IYGME8uJFh7reaxaN0XCLeBnAS5iePA
j7pYflSBIyEGLCPj6reaxaN0Lp+4ebkFqsFMUkFABQ14cQofGGJEtRaTliPGP7Mmh
GJRBQCMaG+G3EPVRP4fJSbKG/5P7P4bFge2EoQkALWjE7LU2DUiDq8sedsIwQrqR
ag7mL05k7v0/5bt2ERFCbAcbz2VfN8uO1Rs8pkBVcWz9sCa9vLykqGDz1S8jlS9I
siv+A1M0rvbGl2DITEY6oFJPEcAPUHsLGGqGJ7/IQrFxfSH7x/XKSe26AOdA2rlV
5mGPMe2LDq0q23RmaOqN9m+eFHHkbL1Knlh/FP/sDkERKRIkLVtcXKKz8u0Dwz2x
pLCU7giM47xmB0P7ae0cHJf2fP+qhSqbF2TmJmc2ESIH0Gs3L8kRH6+0
-----END CERTIFICATE-----
)EOF";

// ============================================================
// SETUP
// ============================================================

void setup() {
  // Initialize serial for debugging
  Serial.begin(115200);
  Serial.println("\n====================================");
  Serial.println("  AI Bus Tracking System - ESP32");
  Serial.println("====================================\n");

  // Initialize LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // Build MQTT topic
  snprintf(MQTT_TOPIC, sizeof(MQTT_TOPIC), "bus/%s/location", BUS_ID);
  Serial.printf("MQTT Topic: %s\n", MQTT_TOPIC);

  // Initialize GPS serial
  gpsSerial.begin(GPS_BAUD, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
  Serial.println("[GPS] Serial initialized on UART2");

  // Connect to WiFi
  connectWiFi();

  // Configure MQTT
  espClient.setCACert(root_ca);
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setBufferSize(512);  // Increase buffer for JSON payload

  // Connect to MQTT
  connectMQTT();

  Serial.println("\n[SYSTEM] Setup complete. Starting main loop...\n");
}

// ============================================================
// MAIN LOOP
// ============================================================

void loop() {
  // Maintain MQTT connection
  if (!mqttClient.connected()) {
    connectMQTT();
  }
  mqttClient.loop();

  // Read GPS data
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }

  // Check GPS fix status periodically
  if (millis() - lastGPSCheck > 2000) {
    lastGPSCheck = millis();
    satelliteCount = gps.satellites.value();
    gpsFixed = gps.location.isValid() && gps.location.isUpdated();
    
    // Blink LED based on GPS status
    if (gpsFixed) {
      digitalWrite(LED_PIN, HIGH);  // Solid = GPS fix
    } else {
      digitalWrite(LED_PIN, !digitalRead(LED_PIN));  // Blink = searching
    }
  }

  // Publish location data at defined interval
  if (millis() - lastPublishTime >= PUBLISH_INTERVAL) {
    lastPublishTime = millis();
    publishLocationData();
  }
}

// ============================================================
// WiFi CONNECTION
// ============================================================

void connectWiFi() {
  Serial.printf("[WiFi] Connecting to %s", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n[WiFi] Connected! IP: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\n[WiFi] Connection FAILED! Restarting...");
    ESP.restart();
  }
}

// ============================================================
// MQTT CONNECTION
// ============================================================

void connectMQTT() {
  int attempts = 0;
  while (!mqttClient.connected() && attempts < 5) {
    Serial.printf("[MQTT] Connecting to %s:%d...\n", MQTT_BROKER, MQTT_PORT);
    
    String clientId = "ESP32_" + String(BUS_ID) + "_" + String(random(0xffff), HEX);
    
    if (mqttClient.connect(clientId.c_str(), MQTT_USERNAME, MQTT_PASSWORD)) {
      Serial.println("[MQTT] Connected successfully!");
      
      // Publish online status
      char statusTopic[64];
      snprintf(statusTopic, sizeof(statusTopic), "bus/%s/status", BUS_ID);
      mqttClient.publish(statusTopic, "{\"status\":\"online\"}", true);
      
    } else {
      Serial.printf("[MQTT] Failed, rc=%d. Retrying in 5 seconds...\n", mqttClient.state());
      delay(5000);
    }
    attempts++;
  }
}

// ============================================================
// PUBLISH LOCATION DATA
// ============================================================

void publishLocationData() {
  // Build JSON payload
  char payload[384];
  
  if (gps.location.isValid()) {
    float latitude  = gps.location.lat();
    float longitude = gps.location.lng();
    float speed     = gps.speed.kmph();
    float heading   = gps.course.deg();
    float altitude  = gps.altitude.meters();
    int   sats      = gps.satellites.value();

    // Get timestamp from GPS
    char timestamp[32];
    snprintf(timestamp, sizeof(timestamp), "%04d-%02d-%02dT%02d:%02d:%02dZ",
      gps.date.year(), gps.date.month(), gps.date.day(),
      gps.time.hour(), gps.time.minute(), gps.time.second());

    // Create JSON payload
    snprintf(payload, sizeof(payload),
      "{"
        "\"bus_id\":\"%s\","
        "\"route_id\":\"%s\","
        "\"bus_name\":\"%s\","
        "\"latitude\":%.6f,"
        "\"longitude\":%.6f,"
        "\"speed\":%.1f,"
        "\"heading\":%.1f,"
        "\"altitude\":%.1f,"
        "\"satellites\":%d,"
        "\"timestamp\":\"%s\""
      "}",
      BUS_ID, ROUTE_ID, BUS_NAME,
      latitude, longitude, speed, heading, altitude, sats, timestamp
    );

    Serial.printf("[GPS] Lat: %.6f, Lng: %.6f, Speed: %.1f km/h, Sats: %d\n",
      latitude, longitude, speed, sats);

  } else {
    // GPS not fixed yet - send status with no coordinates
    snprintf(payload, sizeof(payload),
      "{"
        "\"bus_id\":\"%s\","
        "\"route_id\":\"%s\","
        "\"bus_name\":\"%s\","
        "\"latitude\":0,"
        "\"longitude\":0,"
        "\"speed\":0,"
        "\"heading\":0,"
        "\"altitude\":0,"
        "\"satellites\":%d,"
        "\"timestamp\":\"awaiting_fix\","
        "\"gps_status\":\"searching\""
      "}",
      BUS_ID, ROUTE_ID, BUS_NAME, gps.satellites.value()
    );

    Serial.printf("[GPS] Searching for satellites... (found: %d)\n", gps.satellites.value());
  }

  // Publish to MQTT
  if (mqttClient.publish(MQTT_TOPIC, payload)) {
    Serial.println("[MQTT] Data published successfully");
  } else {
    Serial.println("[MQTT] Publish FAILED!");
  }
}
