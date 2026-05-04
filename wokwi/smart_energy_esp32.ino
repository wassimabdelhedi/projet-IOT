/*
 * Smart Energy Monitoring — ESP32 (WokWi Node 2)
 * Branchement : Pot (Sim ACS712) sur Pin 34, LEDs sur 26 et 27.
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// --- CONFIGURATION ---
const char* ssid = "Wokwi-GUEST";
const char* password = "";
const char* mqtt_server = "broker.emqx.io";

// TOPICS DIFFÉRENTS POUR ÉVITER LES CONFLITS (NODE 2)
#define T_SENSOR  "sem/bat1/node2/sensors/power"
#define T_CMD     "sem/bat1/node2/cmd/relay"

// PINS
#define PIN_POT    34
#define PIN_RELAY  26  // LED ROUGE
#define PIN_LED    27  // LED VERTE

// CONSTANTES
#define SEUIL_W   300.0
#define VOLTAGE   230.0

WiFiClient espClient;
PubSubClient client(espClient);

bool relayON = true;
unsigned long lastMsg = 0;

void setup_wifi() {
  delay(10);
  Serial.print("Connexion au WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" OK");
}

void callback(char* topic, byte* payload, unsigned int length) {
  char cmd = (char)payload[0];
  Serial.print("[CMD] Reçu : ");
  Serial.println(cmd);

  if (cmd == '0') {
    relayON = false;
    digitalWrite(PIN_RELAY, LOW);
    digitalWrite(PIN_LED, LOW);
    Serial.println("Relais OUVERT");
  } else if (cmd == '1') {
    relayON = true;
    digitalWrite(PIN_RELAY, HIGH);
    digitalWrite(PIN_LED, HIGH);
    Serial.println("Relais FERMÉ");
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Connexion MQTT...");
    String clientId = "ESP32Client-Wokwi-";
    clientId += String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println(" OK");
      client.subscribe(T_CMD);
    } else {
      Serial.print(" Échec, rc=");
      Serial.print(client.state());
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_RELAY, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  
  // État initial
  digitalWrite(PIN_RELAY, HIGH);
  digitalWrite(PIN_LED, HIGH);

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > 5000) {
    lastMsg = now;

    // Lecture puissance simulée via Potentiomètre
    int raw = analogRead(PIN_POT);
    float current = (raw / 4095.0) * 5.0; // 0-5A
    float power = current * VOLTAGE;

    // Protection locale
    if (power > SEUIL_W && relayON) {
      relayON = false;
      digitalWrite(PIN_RELAY, LOW);
      digitalWrite(PIN_LED, LOW);
      Serial.println("[ALERTE] Seuil dépassé - Coupure locale");
    }

    // Publication JSON
    StaticJsonDocument<200> doc;
    doc["node_id"]   = "esp32-wokwi-node2";
    doc["power_W"]   = round(power * 10) / 10.0;
    doc["current_A"] = round(current * 100) / 100.0;
    doc["voltage_V"] = VOLTAGE;
    doc["relay"]     = relayON ? 1 : 0;
    doc["seuil_ok"]  = (power <= SEUIL_W) ? 1 : 0;

    char buffer[256];
    serializeJson(doc, buffer);
    client.publish(T_SENSOR, buffer);

    Serial.print("[PUB] P=");
    Serial.print(power);
    Serial.print("W | Relay=");
    Serial.println(relayON ? "ON" : "OFF");
  }
}
