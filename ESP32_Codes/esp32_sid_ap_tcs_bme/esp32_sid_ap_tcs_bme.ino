/* ECE304 Final Project
 * Rei Ballabani
 * Justin Culp
 * Akshat Pokharna
 * Bernard Morelos Jr.
 */
// Import Libraries
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include "Adafruit_TCS34725.h"
#include <WiFi.h> // Wifi Library
#include <HTTPClient.h>
#include <WebServer.h>
#include <Arduino_JSON.h>

#define SSID_STRING "Ripper"
#define SSID_PASSWORD_STRING "12345678"

#define CIRCUIT_ID "AP2"
#define TCS_SENSOR_ID 8
#define TCS_SENSOR_NAME "AP_TCS"
#define TCS_SENSOR_LOCATION "Bedroom CLR"
#define BME_SENSOR_ID 9
#define BME_SENSOR_NAME "AP_BME"
#define BME_SENSOR_LOCATION "Bedroom LAB"

// BME definitions
#define BME_SCK 22
#define BME_MISO 12
#define BME_MOSI 21
#define BME_CS 10

#define SEALEVELPRESSURE_HPA (1013.25)

// TCS34725 definitions

// set to false if using a common cathode LED
#define commonAnode true

// TCS34725 Global Variables
// our RGB -> eye-recognized gamma color
byte gammatable[256];
Adafruit_TCS34725 tcs = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_50MS, TCS34725_GAIN_4X);

// BME Global Variables
unsigned long delayTime;
Adafruit_BME280 bme; // I2C

// Pick analog outputs, for the ESP32, it is available only on GPIO 0-15
const int red_LED_pin=13;
const int green_LED_pin=14;
const int blue_LED_pin=15;
const int red_led_channel = 1;
const int green_led_channel = 2;
const int blue_led_channel = 3;
const int led_resolution = 8;

// Pin Request Status
bool LED_request = LOW;
bool bme_request = LOW;
bool tcs_request = LOW;

typedef struct {
    float red;
    float green;
    float blue;
    float clr_temp;
    float lux;
    float temperature;
    float pressure;
    float altitude; 
    float humidity;
} sensor_readings_float_t;

/* Put your SSID & Password */
const char* ssid = SSID_STRING;  // Enter SSID here
const char* password = SSID_PASSWORD_STRING;  //Enter Password here

//Your Domain name with URL path or IP address with path
const char* serverName = "http://192.168.0.4:5000/inlab";

// the following variables are unsigned longs because the time, measured in
// milliseconds, will quickly become a bigger number than can be stored in an int.
unsigned long lastTime = 0;
// Set timer to 5 seconds (5000)
unsigned long timerDelay = 5000;

WebServer server(80); // Web Server open on port 80

void get_sensor_readings(sensor_readings_float_t* snsr);
void get_sensor_json(JSONVar* doc);
void set_ledc_write(int led_channel, int value);

void setup() {
  Serial.begin(115200);
  delay(100);
  
  ledcAttachPin(red_LED_pin, red_led_channel);
  ledcSetup(red_led_channel, 2000, led_resolution);
  ledcAttachPin(green_LED_pin, green_led_channel);
  ledcSetup(green_led_channel, 12000, led_resolution);
  ledcAttachPin(blue_LED_pin, blue_led_channel);
  ledcSetup(blue_led_channel, 12000, led_resolution);

  Serial.print("Connecting to ");
  Serial.println(ssid);

  //Connect to your local wifi network
  WiFi.begin(ssid, password);
  delay(100);

  //check wifi is connected to wifi network
  while (WiFi.status() != WL_CONNECTED){
    delay(1000);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected!");
  Serial.print("Got IP: ");
  Serial.println(WiFi.localIP());
  
  server.on("/", handle_OnConnect);
  server.on("/led_set_post",HTTP_POST,set_LED_value_post);
  server.onNotFound(handle_NotFound);
  
  server.begin();
  Serial.println("HTTP server started");

  Serial.println("Timer set to 5 seconds (timerDelay variable), it will take 5 seconds before publishing the first reading.");

  //Setup Sensors
  unsigned status;
  status = tcs.begin();
  if (!status) {
    Serial.println("TCS34725 Undetected");
    while (1);
  }

  status = bme.begin();
  if (!status) {
      Serial.println("Could not find a valid BME280 sensor, check wiring, address, sensor ID!");
      Serial.print("SensorID was: 0x"); Serial.println(bme.sensorID(),16);
      Serial.print("        ID of 0xFF probably means a bad address, a BMP 180 or BMP 085\n");
      Serial.print("   ID of 0x56-0x58 represents a BMP 280,\n");
      Serial.print("        ID of 0x60 represents a BME 280.\n");
      Serial.print("        ID of 0x61 represents a BME 680.\n");
      while (1);
  }

  delayTime = 1000;
  Serial.println();


  // gammatable to bring RGB sensor readings to
  // a number that makes sense to human eyes
  for (int i=0; i<256; i++) {
      float x = i;
      x /= 255;
      x = pow(x, 2.5);
      x *= 255;
  
      if (commonAnode) {
        gammatable[i] = 255 - x;
      } else {
        gammatable[i] = x;
      }
  }
}

void loop() {
  //Send an HTTP POST request every timerDelay milliseconds
  if ((millis() - lastTime) > timerDelay) {
    //Check WiFi connection status
    if(WiFi.status()== WL_CONNECTED){
      HTTPClient http;
      
      // Start the service
      http.begin(serverName);
      
      JSONVar doc;
      get_sensor_json(&doc);
      
      String JSON_string = JSON.stringify(doc);
      Serial.println(JSON_string);

      // Specify content-type header
      http.addHeader("Content-Type", "application/json");         
      // Send HTTP POST request
      int httpResponseCode = http.POST(JSON_string);
     
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);
        
      // Free resources
      http.end();
    }
    else {
      Serial.println("WiFi Disconnected");
    }
    lastTime = millis();
  }
  server.handleClient();
}

/* Web Server Functions */
void handle_OnConnect() {
  Serial.println("Getting Temperature and Humidity");
  JSONVar doc;
  get_sensor_json(&doc);
  delay(2000);
  server.send(200, "application/json", JSON.stringify(doc));
}

void set_LED_value_post(){
  Serial.println("Setting Values of LEDs");
  Serial.println(server.hasArg("plain"));
  String body = server.arg("plain");
  Serial.println(body);
  JSONVar myObject = JSON.parse(body);

  if (myObject.hasOwnProperty("redled")){
    set_ledc_write(red_led_channel,(int) myObject["redled"]);
  }
    
  if (myObject.hasOwnProperty("greenled")){
    set_ledc_write(green_led_channel,(int) myObject["greenled"]);
  }

  if (myObject.hasOwnProperty("blueled")){
    set_ledc_write(blue_led_channel,(int) myObject["blueled"]);
  }
  delay(2000);
  server.send(200,"application/json",JSON.stringify(myObject));
}

void handle_NotFound(){
  server.send(404, "text/plain", "Not found");
}

/* Helper Functions */
void get_sensor_readings(sensor_readings_float_t* snsr) {
  tcs.setInterrupt(false);  // turn on LED
  delay(60);  // takes 50ms to read
  tcs.getRGB(&(snsr->red), &(snsr->green), &(snsr->blue));
  tcs.setInterrupt(true);  // turn off LED

  snsr->clr_temp = tcs.calculateColorTemperature(snsr->red, snsr->green, snsr->blue);
  snsr->lux = tcs.calculateLux(snsr->red, snsr->green, snsr->blue);
  
  snsr->temperature = bme.readTemperature();
  snsr->pressure = bme.readPressure() / 100.0F;
  snsr->altitude = bme.readAltitude(SEALEVELPRESSURE_HPA);
  snsr->humidity = bme.readHumidity();
}

void get_sensor_json(JSONVar* doc) {
  sensor_readings_float_t snsr;
  get_sensor_readings(&snsr);

  (*doc)["cid"] = CIRCUIT_ID;
  
  (*doc)["tcs"]["id"] = TCS_SENSOR_ID;
  (*doc)["tcs"]["name"] = TCS_SENSOR_NAME;
  (*doc)["tcs"]["location"]= TCS_SENSOR_LOCATION;
  (*doc)["tcs"]["red"] = snsr.red;
  (*doc)["tcs"]["green"] = snsr.green;
  (*doc)["tcs"]["blue"] = snsr.blue;
  (*doc)["tcs"]["clr_temp"] = snsr.clr_temp;
  (*doc)["tcs"]["lux"] = snsr.lux;
  
  (*doc)["bme"]["id"] = BME_SENSOR_ID;
  (*doc)["bme"]["name"] = BME_SENSOR_NAME;
  (*doc)["bme"]["location"] = BME_SENSOR_LOCATION;
  (*doc)["bme"]["temperature"] = snsr.temperature;
  (*doc)["bme"]["pressure"] = snsr.pressure;
  (*doc)["bme"]["altitude"] = snsr.altitude;
  (*doc)["bme"]["humidity"] = snsr.humidity;
}

void set_ledc_write(int led_channel, int led_value) {
  if (led_value >= 0 && led_value < 256) {
    ledcWrite(led_channel,led_value);
  }
}
