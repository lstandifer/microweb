import machine
import network
import socket
import uos
import ubinascii
import json
import time
from machine import Pin
from time import sleep
from picozero import pico_temp_sensor, pico_led

led = Pin(9, Pin.OUT)


config = {
    "default_ap_name" : "PicoW",
    "default_ap_password" : "tutswiki",
    "custom_ap_name" : "",
    "custom_ap_password" : "",
    "wifi_ssid" : "",
    "wifi_password": "",
    "timezone" : "Americas/Central",
    "language" : "english",
    "created_date" : "",
    "updated_date" : "",
    "topic" : "ap config file"
}

##########################################################################
### generate empty variables to be used later

ssid = ""
password = ""

##########################################################################
### generate random string

def randStr(length=20):
    source = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890'
    return ''.join([source[x] for x in [(uos.urandom(1)[0] % len(source)) for _ in range(length)]])

##########################################################################
### get local mac address without :

def getMacAddr():
    wlan_sta = network.WLAN(network.STA_IF)
    wlan_sta.active(True)
    wlan_mac = wlan_sta.config('mac')
    return ubinascii.hexlify(wlan_mac).decode()

##########################################################################
### get ap ssid needs decoded json config

def getSsid(config):
    if "custom_ap_name" in config and len(config["custom_ap_name"]) > 0:
        return config["custom_ap_name"]
    else:
        return config["default_ap_name"]
        

##########################################################################
### get access point name needs decoded json config

def getPassword(config):
    if "custom_ap_password" in config and len(config["custom_ap_password"]) > 0:
        return config["custom_ap_password"]
    else:
        return config["default_ap_password"]

##########################################################################
### check if a file is preset returns a boolean

def isFilePresent(file):
    try:
        f = open(file, "r")
        return True
    except OSError:  # open failed
        return False
    
##########################################################################
### initial setup of the app reads config file and sets ap password with random string

def initialSetup():
  try:
    present = isFilePresent("config.json")
    if not present:
          myJSON = json.dumps(config)
          with open("config.json", "w") as jsonfile:
             jsonfile.write(myJSON)
             print("Initial config successful. Restarting...")
             jsonfile.close()
             machine.reset()
  except OSError: # open failed
    machine.reset()

##########################################################################
### read config file

def readConfigFile():
  try:
      with open("config.json", "r") as jsonfile:
        data = json.load(jsonfile) # Reading the file
        print("Successfully read config file...")
        jsonfile.close()
        return data
  except:
      machine.reset()
      print("unable to load config file")

##########################################################################
### update an individual field in json

def updateJsonFileField(key, value, fileName):
    jsonFile = open(fileName, "r") # Open the JSON file for reading
    data = json.load(jsonFile) # Read the JSON into the buffer
    jsonFile.close() # Close the JSON file

    ## Working with buffered content
    tmp = data[key] 
    data[key] = value

    ## Save our changes to JSON file
    jsonFile = open(fileName, "w+")
    jsonFile.write(json.dumps(data))
    jsonFile.close()
    
##########################################################################
### Setup Access Point for user connection

def setupAccessPoint(ssid, password):

    ap = network.WLAN(network.AP_IF)

    ap.config(essid=ssid, password=password) 
    ap.active(True)

    while ap.active == False:
        pass

    print("")
    print("Access point active")
    print("")
    print("Wifi SSID:       " + ssid)
    print("Wifi Password:   " + password)
    print("Ap Ip Address:   " + ap.ifconfig()[0])
    print("Subnet:          " + ap.ifconfig()[1])
    print("Gateway:         " + ap.ifconfig()[2])
    print("DNS:             " + ap.ifconfig()[3])

##########################################################################
### Setup wifi credentials

def setupWifi(data, ssid, password):
    
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect(ssid, password)

    max_wait = 10
    while max_wait > 0:
        if wifi.status() < 0 or wifi.status() >= 3:
            break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)

    if wifi.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        status = wifi.ifconfig()
        print( 'ip = ' + status[0] )
        return status

##########################################################################
### connect to wifi
    
def connectWifi(ssid, password):
    #Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip


##########################################################################
### Start web server
    
def startWebServer(html):
#    try:
#        ip = connectWifi(ssid, password)
#    except KeyboardInterrupt:
#        machine.reset()

    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

    s = socket.socket()
    s.bind(addr)
    s.listen(1)

    print('listening on    ', addr[0])

    # Listen for connections
    while True:
        try:
            cl, addr = s.accept()
            print('client connected from', addr)
            request = cl.recv(1024)
            print(request)

            request = str(request)
            led_on = request.find('/light/on')
            led_off = request.find('/light/off')
            print( 'led on = ' + str(led_on))
            print( 'led off = ' + str(led_off))

            if led_on == 6:
                print("led on")
                led.value(1)
                stateis = "LED is ON"

            if led_off == 6:
                print("led off")
                led.value(0)
                stateis = "LED is OFF"

            response = html % stateis

            cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            cl.send(response)
            cl.close()

        except OSError as e:
            cl.close()
            print('connection closed')

##########################################################################
### html template for web page

mainHtml = """<!DOCTYPE html>
<html>
    <head> <title>Pico W</title> </head>
    <body> <h1>Pico W</h1>
        <p>%s</p>
    </body>
</html>
"""

##########################################################################
### html template for access point page

apHtml = """<!DOCTYPE html>
<html>
    <head> <title>Pico W</title> </head>
    <body> <h1>Pico W</h1>
        <p>%s</p>
    </body>
</html>
"""

##########################################################################
### run initial config file creation and read config file


initialSetup()
config = readConfigFile()

ssid = getSsid(config)
password = getPassword(config)
ip = ""

if not "wifi_ssid" in config or not "wifi_password" in config or len(config["wifi_ssid"]) == 0 or len(config["wifi_password"]) == 0:
    setupAccessPoint(ssid, password)
    startWebServer(apHtml)
else:
    startWebServer(apHtml, ssid, password)