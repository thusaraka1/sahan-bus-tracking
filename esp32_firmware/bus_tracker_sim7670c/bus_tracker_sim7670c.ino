/*
 * ============================================================================
 *  LEE BUS PROJECT — ESP32 Sensor Hub Firmware (Research & Production)
 * ============================================================================
 *  
 *  Reads sensor data from:
 *    1. MPU6050  (Gyro/Accel/Temp) — I2C   (SDA=GPIO 21, SCL=GPIO 22)
 *    2. NEO-6M   (GPS / GNSS)      — UART2 (TX->GPIO 16, RX->GPIO 17)
 *    3. HW-484   (Microphone/Sound)— ADC1  (AO=GPIO 34)
 *
 *  Publishes JSON via:
 *    4. SIM7670C (4G LTE Modem)    — UART1 (TX->GPIO 27, RX->GPIO 14)
 *       → HiveMQ Cloud MQTT (TLS port 8883, SNI Enabled)
 *
 *  Wiring Reference (Verified for your hardware build):
 *  ┌────────────┬────────────┬────────────────────────────────────────────────┐
 *  │ Module     │ Module Pin │ ESP32 Pin / Power                              │
 *  ├────────────┼────────────┼────────────────────────────────────────────────┤
 *  │ SIM7670C   │ VCC        │ External 5V (2A Peak Recommended)              │
 *  │ (4G LTE)   │ GND        │ Common GND with ESP32                          │
 *  │            │ TX         │ GPIO 27 (ESP32 UART1 RX - receives from SIM TX)│
 *  │            │ RX         │ GPIO 14 (ESP32 UART1 TX - transmits to SIM RX) │
 *  ├────────────┼────────────┼────────────────────────────────────────────────┤
 *  │ NEO-6M GPS │ VCC        │ 3.3V (or 5V depending on breakout module)       │
 *  │            │ GND        │ Common GND                                     │
 *  │            │ TX         │ GPIO 16 (ESP32 UART2 RX - receives from GPS TX)│
 *  │            │ RX         │ GPIO 17 (ESP32 UART2 TX - transmits to GPS RX) │
 *  ├────────────┼────────────┼────────────────────────────────────────────────┤
 *  │ MPU6050    │ VCC        │ 3.3V                                           │
 *  │ (Gyro/Acc) │ GND        │ Common GND                                     │
 *  │            │ SCL        │ GPIO 22 (I2C SCL)                              │
 *  │            │ SDA        │ GPIO 21 (I2C SDA)                              │
 *  ├────────────┼────────────┼────────────────────────────────────────────────┤
 *  │ HW-484     │ VCC        │ 3.3V                                           │
 *  │ (Sound)    │ GND        │ Common GND                                     │
 *  │            │ AO         │ GPIO 34 (ADC1 Channel 6)                       │
 *  │            │ DO         │ Not Connected                                  │
 *  └────────────┴────────────┴────────────────────────────────────────────────┘
 *
 *  Board in Arduino IDE: "ESP32 Dev Module"
 *  Required Libraries:
 *    - Wire.h (ESP32 built-in)
 *    - HardwareSerial.h (ESP32 built-in)
 *    - TinyGPSPlus (Install via Arduino Library Manager -> search "TinyGPSPlus")
 * ============================================================================
 */

#include <Wire.h>
#include <HardwareSerial.h>
#include <TinyGPSPlus.h>

// ========================== PIN DEFINITIONS ==========================
// SIM7670C LTE Module (UART1)
// SIM7670C TX pin -> ESP32 GPIO 27
// SIM7670C RX pin -> ESP32 GPIO 14
#define SIM_RX_PIN    27   // ESP32 receives from SIM TX
#define SIM_TX_PIN    14   // ESP32 transmits to SIM RX

// NEO-6M GPS Module (UART2)
// NEO-6M TX pin -> ESP32 GPIO 16
// NEO-6M RX pin -> ESP32 GPIO 17
#define GPS_RX_PIN    16   // ESP32 receives from GPS TX
#define GPS_TX_PIN    17   // ESP32 transmits to GPS RX

// MPU6050 (I2C default pins)
#define MPU_SDA_PIN   21
#define MPU_SCL_PIN   22
#define MPU6050_ADDR  0x68

// HW-484 Microphone (ADC1)
#define MIC_PIN       34

// ========================== HIVEMQ CLOUD CONFIG ==========================
// Switch between your HiveMQ Cloud clusters if needed:
// Profile 1: Lee Bus Project Cluster (9ce9a991c31542a49529dd4db804495d - Tested Working)
// Profile 2: Sahan Bus Track Cluster (b5ad82f71b0d40d6bcf02b00ce1cd933)
#define HIVEMQ_PROFILE 1

#if HIVEMQ_PROFILE == 1
  const char* MQTT_BROKER   = "9ce9a991c31542a49529dd4db804495d.s1.eu.hivemq.cloud";
  const int   MQTT_PORT     = 8883;  // TLS port
  const char* MQTT_USER     = "lee_project";
  const char* MQTT_PASS     = "Lee_project@123";
  const char* MQTT_CLIENT   = "lee_bus_esp32_001";
  const char* MQTT_TOPIC    = "lee_bus/sensors";
  const char* BUS_ROUTE_ID  = "ROUTE_04";
  const char* BUS_NAME      = "Route 04: Colombo - Chilaw (IoT Hub)";
#else
  const char* MQTT_BROKER   = "b5ad82f71b0d40d6bcf02b00ce1cd933.s1.eu.hivemq.cloud";
  const int   MQTT_PORT     = 8883;  // TLS port
  const char* MQTT_USER     = "Bus_track";
  const char* MQTT_PASS     = "Bus@12345";
  const char* MQTT_CLIENT   = "BUS_001";
  const char* MQTT_TOPIC    = "bus/BUS_001/location";
  const char* BUS_ROUTE_ID  = "ROUTE_A";
  const char* BUS_NAME      = "Colombo - Kandy Express (IoT Hub)";
#endif

// ========================== TIMING CONFIG ==========================
#define PUBLISH_INTERVAL_MS   5000   // Telemetry published every 5 seconds
#define GPS_READ_TIMEOUT_MS   1000
#define AT_RESPONSE_TIMEOUT   10000  // 10s for general AT commands
#define AT_MQTT_TIMEOUT       30000  // 30s for MQTT TLS handshake
#define MIC_SAMPLE_COUNT      64     // ADC sample averaging

// ========================== SERIAL PORTS ==========================
HardwareSerial simSerial(1);   // UART1 for SIM7670C
HardwareSerial gpsSerial(2);   // UART2 for NEO-6M

// ========================== OBJECTS ==========================
TinyGPSPlus gps;

// ========================== SENSOR DATA ==========================
struct SensorData {
  // MPU6050
  float accelX, accelY, accelZ;
  float gyroX, gyroY, gyroZ;
  float temperature;
  
  // GPS
  double latitude;
  double longitude;
  double altitude;
  double speed;       // km/h
  double course;      // degrees
  int    satellites;
  bool   gpsValid;
  char   gpsTime[20]; // HH:MM:SS
  char   gpsDate[12]; // YYYY-MM-DD
  
  // Microphone
  int    micRaw;
  float  micVoltage;
  float  micDB;       // dB estimate
};

SensorData data;
unsigned long lastPublish = 0;
bool mqttConnected = false;

// Function prototypes
void initMPU6050();
void readMPU6050();
void readGPS();
void readMicrophone();
void initSIM7670C();
void connectMQTT();
void publishSensorData();
void printSensorData();
String sendAT(String command, String expectedResponse, unsigned long timeout);
bool sendATok(String command, unsigned long timeout);

// ============================================================================
//  SETUP
// ============================================================================
void setup() {
  // Debug serial
  Serial.begin(115200);
  delay(1000);
  
  Serial.println();
  Serial.println("╔══════════════════════════════════════════════════════════════╗");
  Serial.println("║   LEE BUS PROJECT — ESP32 + SIM7670C + NEO-6M SENSOR HUB     ║");
  Serial.println("║   TLS 8883 MQTT Telemetry Pipeline (Proven Working AT Stack)  ║");
  Serial.println("╚══════════════════════════════════════════════════════════════╝");
  Serial.println();

  // 1. Initialize I2C for MPU6050
  Wire.begin(MPU_SDA_PIN, MPU_SCL_PIN);
  initMPU6050();
  
  // 2. Initialize GPS UART2 (NEO-6M: TX->16, RX->17)
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
  Serial.printf("[GPS]  UART2 initialized on RX=%d, TX=%d (9600 baud)\n", GPS_RX_PIN, GPS_TX_PIN);
  
  // 3. Initialize Microphone ADC (HW-484 on GPIO 34)
  analogReadResolution(12);          // 12-bit (0-4095)
  analogSetAttenuation(ADC_11db);    // Full 0-3.3V range
  pinMode(MIC_PIN, INPUT);
  Serial.printf("[MIC]  ADC initialized on GPIO %d\n", MIC_PIN);
  
  // 4. Initialize SIM7670C LTE UART1 (SIM7670C: TX->27, RX->14)
  simSerial.begin(115200, SERIAL_8N1, SIM_RX_PIN, SIM_TX_PIN);
  Serial.printf("[SIM]  UART1 initialized on RX=%d, TX=%d (115200 baud)\n", SIM_RX_PIN, SIM_TX_PIN);
  Serial.println();
  
  // Boot up SIM module & connect to MQTT
  delay(3000);  // Allow SIM7670C to boot and stabilize
  initSIM7670C();
}

// ============================================================================
//  MAIN LOOP
// ============================================================================
void loop() {
  // Continuously feed GPS data
  readGPS();
  
  // Publish at interval
  if (millis() - lastPublish >= PUBLISH_INTERVAL_MS) {
    lastPublish = millis();
    
    // Read all sensors
    readMPU6050();
    readMicrophone();
    
    // Print to debug serial
    printSensorData();
    
    // Publish via MQTT
    if (mqttConnected) {
      publishSensorData();
    } else {
      Serial.println("[MQTT] Not connected — attempting reconnect...");
      connectMQTT();
    }
  }
  
  // Check for unsolicited SIM messages
  while (simSerial.available()) {
    String line = simSerial.readStringUntil('\n');
    line.trim();
    if (line.length() > 0) {
      Serial.println("[SIM<] " + line);
      // Detect disconnect
      if (line.indexOf("+CMQTTDISC") >= 0 || line.indexOf("ERROR") >= 0 || line.indexOf("CLOSED") >= 0) {
        mqttConnected = false;
      }
    }
  }
}

// ============================================================================
//  MPU6050 FUNCTIONS
// ============================================================================
void initMPU6050() {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x6B);  // PWR_MGMT_1 register
  Wire.write(0x00);  // Wake up
  byte error = Wire.endTransmission(true);
  
  if (error == 0) {
    Serial.println("[MPU]  MPU6050 initialized OK");
    
    // Set accelerometer to ±2g
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(0x1C);
    Wire.write(0x00);
    Wire.endTransmission(true);
    
    // Set gyroscope to ±250°/s
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(0x1B);
    Wire.write(0x00);
    Wire.endTransmission(true);
  } else {
    Serial.println("[MPU]  *** MPU6050 NOT FOUND! Check wiring (SDA=21, SCL=22). ***");
  }
}

void readMPU6050() {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x3B);  // Start at ACCEL_XOUT_H
  Wire.endTransmission(false);
  Wire.requestFrom((uint8_t)MPU6050_ADDR, (uint8_t)14, (uint8_t)true);
  
  if (Wire.available() >= 14) {
    int16_t rawAx = Wire.read() << 8 | Wire.read();
    int16_t rawAy = Wire.read() << 8 | Wire.read();
    int16_t rawAz = Wire.read() << 8 | Wire.read();
    int16_t rawT  = Wire.read() << 8 | Wire.read();
    int16_t rawGx = Wire.read() << 8 | Wire.read();
    int16_t rawGy = Wire.read() << 8 | Wire.read();
    int16_t rawGz = Wire.read() << 8 | Wire.read();
    
    // Convert to physical units
    data.accelX = rawAx / 16384.0;  // ±2g  → LSB/g = 16384
    data.accelY = rawAy / 16384.0;
    data.accelZ = rawAz / 16384.0;
    data.gyroX  = rawGx / 131.0;    // ±250°/s → LSB/(°/s) = 131
    data.gyroY  = rawGy / 131.0;
    data.gyroZ  = rawGz / 131.0;
    data.temperature = rawT / 340.0 + 36.53;
  }
}

// ============================================================================
//  GPS FUNCTIONS
// ============================================================================
void readGPS() {
  unsigned long start = millis();
  while (gpsSerial.available() > 0 && (millis() - start) < GPS_READ_TIMEOUT_MS) {
    char c = gpsSerial.read();
    gps.encode(c);
  }
  
  if (gps.location.isValid()) {
    data.latitude   = gps.location.lat();
    data.longitude  = gps.location.lng();
    data.gpsValid   = true;
  } else {
    data.gpsValid = false;
  }
  
  if (gps.altitude.isValid()) {
    data.altitude = gps.altitude.meters();
  }
  
  if (gps.speed.isValid()) {
    data.speed = gps.speed.kmph();
  }
  
  if (gps.course.isValid()) {
    data.course = gps.course.deg();
  }
  
  if (gps.satellites.isValid()) {
    data.satellites = gps.satellites.value();
  }
  
  if (gps.time.isValid()) {
    snprintf(data.gpsTime, sizeof(data.gpsTime), "%02d:%02d:%02d",
             gps.time.hour(), gps.time.minute(), gps.time.second());
  }
  
  if (gps.date.isValid()) {
    snprintf(data.gpsDate, sizeof(data.gpsDate), "%04d-%02d-%02d",
             gps.date.year(), gps.date.month(), gps.date.day());
  }
}

// ============================================================================
//  MICROPHONE FUNCTIONS
// ============================================================================
void readMicrophone() {
  long sum = 0;
  int  peak = 0;
  
  // Take multiple samples for better accuracy
  for (int i = 0; i < MIC_SAMPLE_COUNT; i++) {
    int sample = analogRead(MIC_PIN);
    sum += sample;
    if (sample > peak) peak = sample;
    delayMicroseconds(200);
  }
  
  data.micRaw     = sum / MIC_SAMPLE_COUNT;
  data.micVoltage = (data.micRaw / 4095.0) * 3.3;
  
  // Rough dB estimate (relative, not calibrated)
  // Using peak-to-average ratio for approximate loudness
  float peakVoltage = (peak / 4095.0) * 3.3;
  if (peakVoltage > 0.01) {
    data.micDB = 20.0 * log10(peakVoltage / 0.01);  // Reference: 10mV
  } else {
    data.micDB = 0.0;
  }
}

// ============================================================================
//  SIM7670C AT COMMAND FUNCTIONS
// ============================================================================

/**
 * Send AT command and wait for expected response
 */
String sendAT(String command, String expectedResponse, unsigned long timeout) {
  // Flush any pending data
  while (simSerial.available()) simSerial.read();
  
  Serial.println("[SIM>] " + command);
  simSerial.println(command);
  
  String response = "";
  unsigned long start = millis();
  bool found = false;
  
  while (millis() - start < timeout) {
    while (simSerial.available()) {
      char c = simSerial.read();
      response += c;
    }
    if (response.indexOf(expectedResponse) >= 0) {
      found = true;
      break;
    }
    if (response.indexOf("ERROR") >= 0) {
      break;
    }
    delay(10);
  }
  
  response.trim();
  Serial.println("[SIM<] " + response);
  
  if (!found && response.indexOf("ERROR") < 0) {
    Serial.println("[SIM]  *** TIMEOUT waiting for: " + expectedResponse + " ***");
  }
  
  return response;
}

/**
 * Send AT command — simplified version (just check for OK)
 */
bool sendATok(String command, unsigned long timeout) {
  String resp = sendAT(command, "OK", timeout);
  return (resp.indexOf("OK") >= 0);
}

/**
 * Initialize SIM7670C module, check network, enable GPRS
 */
void initSIM7670C() {
  Serial.println("────────────────────────────────────────");
  Serial.println("[SIM]  Initializing SIM7670C LTE Module");
  Serial.println("────────────────────────────────────────");
  
  // Basic AT handshake
  int retries = 5;
  bool simReady = false;
  while (retries-- > 0) {
    if (sendATok("AT", 2000)) {
      simReady = true;
      break;
    }
    delay(1000);
  }
  
  if (!simReady) {
    Serial.println("[SIM]  *** Module not responding! Check power & wiring (TX=27, RX=14). ***");
    return;
  }
  
  // Disable echo
  sendATok("ATE0", 2000);
  
  // Check SIM card
  sendAT("AT+CPIN?", "READY", 5000);
  
  // Check signal quality
  sendAT("AT+CSQ", "OK", 3000);
  
  // Check network registration
  Serial.println("[SIM]  Waiting for network registration...");
  retries = 20;
  while (retries-- > 0) {
    String resp = sendAT("AT+CREG?", "OK", 3000);
    // +CREG: 0,1 = registered (home) or +CREG: 0,5 = registered (roaming)
    if (resp.indexOf(",1") >= 0 || resp.indexOf(",5") >= 0) {
      Serial.println("[SIM]  ✓ Registered on network");
      break;
    }
    Serial.println("[SIM]  Not registered yet, retrying...");
    delay(2000);
  }
  
  // Check GPRS/data registration
  retries = 10;
  while (retries-- > 0) {
    String resp = sendAT("AT+CGREG?", "OK", 3000);
    if (resp.indexOf(",1") >= 0 || resp.indexOf(",5") >= 0) {
      Serial.println("[SIM]  ✓ Data service registered");
      break;
    }
    delay(2000);
  }
  
  // Activate PDP context (data connection)
  sendATok("AT+CGATT=1", 10000);         // Attach to GPRS
  sendATok("AT+CGDCONT=1,\"IP\",\"\"", 5000);  // Set PDP context (auto APN)
  sendATok("AT+CGACT=1,1", 10000);       // Activate PDP context
  
  // Check IP address
  sendAT("AT+CGPADDR=1", "OK", 5000);
  
  Serial.println("[SIM]  ✓ LTE data connection established");
  Serial.println();
  
  // Connect to MQTT
  connectMQTT();
}

/**
 * Connect to HiveMQ Cloud broker via MQTT over TLS 8883
 */
void connectMQTT() {
  Serial.println("────────────────────────────────────────");
  Serial.printf("[MQTT] Connecting to HiveMQ Cloud (%s:8883)...\n", MQTT_BROKER);
  Serial.println("────────────────────────────────────────");
  
  // Stop any existing MQTT session
  sendAT("AT+CMQTTDISC=0,60", "OK", 5000);
  delay(500);
  sendAT("AT+CMQTTREL=0", "OK", 3000);
  delay(500);
  sendAT("AT+CMQTTSTOP", "OK", 3000);
  delay(1000);
  
  // ─── Step 1: Start MQTT service ───
  if (!sendATok("AT+CMQTTSTART", 5000)) {
    // Might already be started — continue anyway
    Serial.println("[MQTT] MQTT service may already be running, continuing...");
  }
  delay(1000);
  
  // ─── Step 2: Configure SSL ───
  // Set SSL version (TLS 1.2)
  sendATok("AT+CSSLCFG=\"sslversion\",0,4", 3000);
  
  // Skip server certificate verification (for cloud brokers)
  // 0 = no auth, 1 = server auth, 2 = server+client auth
  sendATok("AT+CSSLCFG=\"authmode\",0,0", 3000);
  
  // Enable SNI (Server Name Indication) — required by HiveMQ Cloud
  sendATok("AT+CSSLCFG=\"enableSNI\",0,1", 3000);
  
  delay(500);
  
  // ─── Step 3: Acquire MQTT client (with SSL) ───
  // AT+CMQTTACCQ=<client_index>,<clientID>,<server_type>
  // server_type: 0=TCP, 1=TLS
  String accqCmd = "AT+CMQTTACCQ=0,\"" + String(MQTT_CLIENT) + "\",1";
  if (!sendATok(accqCmd, 5000)) {
    Serial.println("[MQTT] *** Failed to acquire client ***");
    return;
  }
  delay(500);
  
  // ─── Step 4: Link SSL config to MQTT client ───
  // AT+CMQTTSSLCFG=<client_index>,<ssl_ctx_index>
  sendATok("AT+CMQTTSSLCFG=0,0", 3000);
  delay(500);
  
  // ─── Step 5: Connect to broker ───
  // AT+CMQTTCONNECT=<client_index>,<server>,<keepalive>,<clean_session>,<username>,<password>
  String connectCmd = "AT+CMQTTCONNECT=0,\"tcp://" 
                      + String(MQTT_BROKER) + ":" + String(MQTT_PORT) 
                      + "\",60,1,\"" + String(MQTT_USER) + "\",\"" + String(MQTT_PASS) + "\"";
  
  String resp = sendAT(connectCmd, "+CMQTTCONNECT: 0,0", AT_MQTT_TIMEOUT);
  
  if (resp.indexOf("+CMQTTCONNECT: 0,0") >= 0) {
    mqttConnected = true;
    Serial.println();
    Serial.println("╔══════════════════════════════════════════════════════╗");
    Serial.println("║  ✓ MQTT CONNECTED TO HIVEMQ CLOUD (TLS 8883)!        ║");
    Serial.println("╚══════════════════════════════════════════════════════╝");
    Serial.println();
  } else {
    mqttConnected = false;
    Serial.println("[MQTT] *** Connection FAILED ***");
    Serial.println("[MQTT] Response: " + resp);
    
    // Parse error code if available
    int errIdx = resp.indexOf("+CMQTTCONNECT: 0,");
    if (errIdx >= 0) {
      String errCode = resp.substring(errIdx + 17);
      errCode.trim();
      Serial.println("[MQTT] Error code: " + errCode);
      Serial.println("[MQTT] Common errors:");
      Serial.println("       1 = Unacceptable protocol version");
      Serial.println("       2 = Identifier rejected");
      Serial.println("       3 = Server unavailable");
      Serial.println("       4 = Bad username/password");
      Serial.println("       5 = Not authorized");
    }
  }
}

/**
 * Build JSON payload and publish to MQTT topic
 * Includes both nested sensor hub and top-level fields for full compatibility
 */
void publishSensorData() {
  // Build JSON payload
  String json = "{";
  
  // Device & Bus Identification
  json += "\"device\":\"" + String(MQTT_CLIENT) + "\",";
  json += "\"bus_id\":\"" + String(MQTT_CLIENT) + "\",";
  json += "\"route_id\":\"" + String(BUS_ROUTE_ID) + "\",";
  json += "\"bus_name\":\"" + String(BUS_NAME) + "\",";
  json += "\"uptime\":" + String(millis() / 1000) + ",";
  
  // Top-level GPS coordinates for standard telemetry
  if (data.gpsValid) {
    json += "\"latitude\":" + String(data.latitude, 6) + ",";
    json += "\"longitude\":" + String(data.longitude, 6) + ",";
    json += "\"speed\":" + String(data.speed, 1) + ",";
    json += "\"heading\":" + String(data.course, 1) + ",";
    json += "\"altitude\":" + String(data.altitude, 1) + ",";
  }
  
  // MPU6050 data
  json += "\"mpu6050\":{";
  json += "\"accel\":{";
  json += "\"x\":" + String(data.accelX, 3) + ",";
  json += "\"y\":" + String(data.accelY, 3) + ",";
  json += "\"z\":" + String(data.accelZ, 3) + "},";
  json += "\"gyro\":{";
  json += "\"x\":" + String(data.gyroX, 2) + ",";
  json += "\"y\":" + String(data.gyroY, 2) + ",";
  json += "\"z\":" + String(data.gyroZ, 2) + "},";
  json += "\"temp\":" + String(data.temperature, 1) + "},";
  
  // GPS data
  json += "\"gps\":{";
  json += "\"valid\":" + String(data.gpsValid ? "true" : "false") + ",";
  if (data.gpsValid) {
    json += "\"lat\":" + String(data.latitude, 6) + ",";
    json += "\"lng\":" + String(data.longitude, 6) + ",";
    json += "\"alt\":" + String(data.altitude, 1) + ",";
    json += "\"speed\":" + String(data.speed, 1) + ",";
    json += "\"course\":" + String(data.course, 1) + ",";
  }
  json += "\"sats\":" + String(data.satellites) + ",";
  json += "\"time\":\"" + String(data.gpsTime) + "\",";
  json += "\"date\":\"" + String(data.gpsDate) + "\"},";
  
  // Microphone data
  json += "\"mic\":{";
  json += "\"raw\":" + String(data.micRaw) + ",";
  json += "\"voltage\":" + String(data.micVoltage, 3) + ",";
  json += "\"db\":" + String(data.micDB, 1) + "}";
  
  json += "}";
  
  int topicLen = strlen(MQTT_TOPIC);
  int payloadLen = json.length();
  
  Serial.println("[MQTT] Publishing " + String(payloadLen) + " bytes to: " + String(MQTT_TOPIC));
  
  // ─── Set topic ───
  // AT+CMQTTTOPIC=<client_index>,<topic_length>
  String topicCmd = "AT+CMQTTTOPIC=0," + String(topicLen);
  simSerial.println(topicCmd);
  Serial.println("[SIM>] " + topicCmd);
  delay(300);
  
  // Wait for '>' prompt then send topic
  unsigned long start = millis();
  bool gotPrompt = false;
  while (millis() - start < 3000) {
    if (simSerial.available()) {
      char c = simSerial.read();
      Serial.print(c);
      if (c == '>') {
        gotPrompt = true;
        break;
      }
    }
  }
  
  if (!gotPrompt) {
    Serial.println("[MQTT] *** No prompt for topic, aborting publish ***");
    mqttConnected = false;
    return;
  }
  
  simSerial.print(MQTT_TOPIC);
  delay(500);
  
  // Read response
  String topicResp = "";
  start = millis();
  while (millis() - start < 3000) {
    while (simSerial.available()) {
      topicResp += (char)simSerial.read();
    }
    if (topicResp.indexOf("OK") >= 0) break;
    delay(10);
  }
  Serial.println("[SIM<] " + topicResp);
  
  // ─── Set payload ───
  // AT+CMQTTPAYLOAD=<client_index>,<payload_length>
  String payloadCmd = "AT+CMQTTPAYLOAD=0," + String(payloadLen);
  simSerial.println(payloadCmd);
  Serial.println("[SIM>] " + payloadCmd);
  delay(300);
  
  // Wait for '>' prompt then send payload
  start = millis();
  gotPrompt = false;
  while (millis() - start < 3000) {
    if (simSerial.available()) {
      char c = simSerial.read();
      Serial.print(c);
      if (c == '>') {
        gotPrompt = true;
        break;
      }
    }
  }
  
  if (!gotPrompt) {
    Serial.println("[MQTT] *** No prompt for payload, aborting publish ***");
    mqttConnected = false;
    return;
  }
  
  simSerial.print(json);
  delay(500);
  
  // Read response
  String payloadResp = "";
  start = millis();
  while (millis() - start < 3000) {
    while (simSerial.available()) {
      payloadResp += (char)simSerial.read();
    }
    if (payloadResp.indexOf("OK") >= 0) break;
    delay(10);
  }
  Serial.println("[SIM<] " + payloadResp);
  
  // ─── Publish ───
  // AT+CMQTTPUB=<client_index>,<qos>,<pub_timeout>
  // QoS 1 for reliable delivery
  String resp = sendAT("AT+CMQTTPUB=0,1,60", "+CMQTTPUB: 0,0", 10000);
  
  if (resp.indexOf("+CMQTTPUB: 0,0") >= 0) {
    Serial.println("[MQTT] ✓ Published successfully!");
  } else {
    Serial.println("[MQTT] *** Publish FAILED ***");
    mqttConnected = false;
  }
}

// ============================================================================
//  DEBUG PRINT
// ============================================================================
void printSensorData() {
  Serial.println("┌──────────── SENSOR READINGS ────────────┐");
  
  // MPU6050
  Serial.println("│ MPU6050 Motion & Accel:");
  Serial.printf("│   Accel: X=%.3f  Y=%.3f  Z=%.3f g\n", 
                data.accelX, data.accelY, data.accelZ);
  Serial.printf("│   Gyro:  X=%.2f  Y=%.2f  Z=%.2f °/s\n", 
                data.gyroX, data.gyroY, data.gyroZ);
  Serial.printf("│   Cabin Temp: %.1f °C\n", data.temperature);
  
  // GPS
  Serial.println("│ NEO-6M GPS:");
  if (data.gpsValid) {
    Serial.printf("│   Lat: %.6f  Lng: %.6f (Fix Valid)\n", data.latitude, data.longitude);
    Serial.printf("│   Alt: %.1fm  Speed: %.1f km/h  Course: %.1f°\n", 
                  data.altitude, data.speed, data.course);
  } else {
    Serial.println("│   No fix yet (searching for satellites...)");
  }
  Serial.printf("│   Sats: %d  Time: %s  Date: %s\n", 
                data.satellites, data.gpsTime, data.gpsDate);
  
  // Microphone
  Serial.println("│ HW-484 Microphone:");
  Serial.printf("│   Raw: %d  Voltage: %.3fV  ~dB: %.1f\n", 
                data.micRaw, data.micVoltage, data.micDB);
  
  Serial.println("└──────────────────────────────────────────┘");
}
