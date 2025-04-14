#include <SPI.h>
#include <Wire.h>
#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <Adafruit_BMP085.h>
#include <DHT.h>

Adafruit_BMP085 bmp;


#define DHTPIN D4         // Pin connected to the DHT sensor
#define DHTTYPE DHT11     // DHT sensor type (DHT11 or DHT22)

DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "Bruh";
const char* password = "Akki@453";

const char* host = "script.google.com";  //https://script.google.com/
const int httpsPort = 443;

WiFiClientSecure client;
String Gas = "AKfycbzGKIz74GCG4Y8Fw7teRPyVBBwIlp46jUMcRDBMQyLfi9HFMtwhzoHIh1EBrJ9ASek";


const int solarPanelPin = A0;

void setup() {
  Serial.begin(9600);
  WiFi.begin(ssid, password);
  Serial.print("Connecting");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(250);
  }

  Serial.println("");
  Serial.print("Successfully connected to : ");
  Serial.println(ssid);
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.println();
  client.setInsecure();
  dht.begin();
  // if (!bmp.begin()) {
	// Serial.println("Could not find a valid BMP085 sensor, check wiring!");
	// while (1) {}
  // }
  bmp.begin();

}

void loop() {
  float temperature = dht.readTemperature();  // Read temperature in Celsius
  float humidity = dht.readHumidity();
  int sensorValue = analogRead(solarPanelPin);
  float voltage = sensorValue * (9 / 1023.0);
  float power = voltage * 0.82;
  Serial.print("Pressure = ");
    Serial.print(bmp.readPressure());
    Serial.println(" Pa");
    Serial.print("Power:- ");
    Serial.println(power);
    Serial.print("Altitude:- ");
    Serial.print(bmp.readAltitude());
    Serial.println(" meters");
    Serial.print("Temperature= ");
    Serial.println(temperature);
  if (!client.connect(host, httpsPort)) {
    Serial.println("connection failed");
    return;
  }
  String url = "/macros/s/" + Gas + "/exec?temperature=" + temperature + "&humidity=" + humidity + "&surface_pressure=" + bmp.readPressure() + "&altitude=" + bmp.readAltitude() + "&solar_power=" + power;
  client.print(String("GET ") + url + " HTTP/1.1\r\n" + "Host: " + host + "\r\n" + "User-Agent: BuildFailureDetectorESP8266\r\n" + "Connection: close\r\n\r\n");
  delay(300000);
  //delay(1000);
}
