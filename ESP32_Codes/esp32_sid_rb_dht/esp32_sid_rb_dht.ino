/* ECE304 Final Project
 * Rei Ballabani
 * Justin Culp
 * Akshat Pokharna
 * Bernard Morelos Jr.
 */
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT_U.h> // Adafruit Universal Sensor Library
#include <WebServer.h>
#include <Arduino_JSON.h>

#define SSID_STRING "Ripper"
#define SSID_PASSWORD_STRING "12345678"

#define CIRCUIT_ID "RB1"
#define DHT_SENSOR_ID 1
#define DHT_SENSOR_NAME "RB_DHT"
#define DHT_SENSOR_LOCATION "Bedroom 612"

// Define constants
const int DHTTYPE=DHT11;
const int dht_pin=21;
const int red_LED_pin = 19;
const int blue_LED_pin = 16;
const int freq = 5000; // LED PWM frequency
const int ledChannel = 0; // LED Channel
const int resolution = 8; // LED PWM resolution

// Create object for DHT
DHT dht(dht_pin, DHTTYPE); // DHT object

const char* ssid = SSID_STRING;  // Enter SSID here
const char* password = SSID_PASSWORD_STRING;  //Enter Password here

//Your Domain name with URL path or IP address with path
const char* serverName = "http://192.168.137.1:5000/dht11";

// the following variables are unsigned longs because the time, measured in
// milliseconds, will quickly become a bigger number than can be stored in an int.
unsigned long lastTime = 0;
// Set timer to 5 seconds (5000)
unsigned long timerDelay = 5000;

WebServer server(80); // Web Server open on port 80

void setup() {
  Serial.begin(115200);
  dht.begin();
  WiFi.begin(ssid, password);
  Serial.println("Connecting");

  // configure LED
  ledcSetup(ledChannel, freq, resolution);
  ledcAttachPin(blue_LED_pin, ledChannel);
  pinMode(red_LED_pin, OUTPUT);
  
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("Connected to WiFi network with IP Address: ");
  Serial.println(WiFi.localIP());
 
  Serial.println("Timer set to 5 seconds (timerDelay variable), it will take 5 seconds before publishing the first reading.");
   
  server.on("/led_set_post",HTTP_POST,led_set_post);
  server.onNotFound(handle_NotFound);
  server.begin();
  Serial.println("HTTP server started");
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
      doc["cid"] = CIRCUIT_ID;
      
      doc["dht"]["id"] = DHT_SENSOR_ID;
      doc["dht"]["name"] = DHT_SENSOR_NAME;
      doc["dht"]["location"] = DHT_SENSOR_LOCATION;
      doc["dht"]["temperature"] = dht.readTemperature();
      doc["dht"]["humidity"] = dht.readHumidity(); 

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

void led_set_post(){
  String body = server.arg("plain");
  JSONVar myObject = JSON.parse(body);
  digitalWrite(red_LED_pin, (int) myObject["redled"]);
  ledcWrite(ledChannel,(int) myObject["blueled"]); // Set LED brightness
  server.send(200,"application/json",JSON.stringify(myObject));
}

void handle_NotFound(){
  server.send(404, "text/plain", "Not found");
}
