#include <ESP8266WiFi.h>

void sniffer_callback(uint8_t *buf, uint16_t len) {
  // We extract the Frame Control byte to identify packet type
  // Type 0x00 = Management, Subtype 0x0C = Deauthentication
  int type = buf[12]; 
  signed int rssi = buf[0]; // Signal strength

  // Send data to Laptop over USB
  Serial.print(type);
  Serial.print(",");
  Serial.println(rssi);
}

void setup() {
  Serial.begin(115200);
  WiFi.disconnect();
  WiFi.mode(WIFI_STA);
  
  // Enter Promiscuous Mode
  wifi_set_opmode(STATION_MODE);
  wifi_set_promiscuous_rx_cb(sniffer_callback);
  wifi_promiscuous_enable(1);
  
  Serial.println("SYSTEM_READY");
}

void loop() {
  // Hop between channels 1 to 13 to catch all traffic
  for (int i = 1; i <= 13; i++) {
    wifi_set_channel(i);
    delay(200); 
  }
}