#!/usr/bin/python3
# Requires: sudo pip3 install requests
# Original: https://github.com/NiteCrwlr/playground/blob/main/SNStatus/SNStatusV2.py
#

import os
import sys
import socket
import ipaddress
import requests
import json
import time
from datetime import timedelta

retryCounter = 0

haToken = "" # Set your HomeAssistant API Token
whUrl = '' # Set to your HomeAssistant WebHook URL
connectIP = '' # Set printer ip or let it discover
connectPort = '8080'
tokenFile = os.getcwd() + "/SMtoken.txt" # Set to writable location (default is script location)

# Read config from ENV VARS
if os.environ.get("HA_TOKEN"):
  haToken = os.environ.get("HA_TOKEN")
if os.environ.get("HA_WEBHOOK_URL"):
  whUrl = os.environ.get("HA_WEBHOOK_URL")
if os.environ.get("SM_IP"):
  connectIP = os.environ.get("SM_IP")
if os.environ.get("SM_PORT"):
  connectPort = os.environ.get("SM_PORT")
if os.environ.get("SM_TOKEN"):
  smToken = os.environ.get("SM_TOKEN")
if os.environ.get(""):
  smToken = os.environ.get("SM_TOKEN")

# Main Program
def main():
  global connectIP
  if not connectIP:
    print("connectIP not set will try to discover")
    connectIP = updDiscover()

  if not validate_ip_address(connectIP):
    print("connectIP is not valid")
    sys.exit(1)

  if not is_reachable(connectIP, connectPort):
    print("Set IP " + connectIP + " not reachable")
    postIt('{"status": "UNAVAILABLE"}')
    sys.exit(1)

  if smToken == "":
    smToken = getSMToken(connectIP)
  print("Connecting with Token:",smToken)
  smStatus = readStatus(smToken)
  postIt(smStatus)

def getSMToken(connectIP):
  # Create file if not exists
  try:
    file = open(tokenFile, "r+")
  except FileNotFoundError:
    file = open(tokenFile, "w+")

  smUrl = "http://" + connectIP + ":" + connectPort + "/api/v1/connect"
  smToken = file.read()
  if smToken == "":
    # Create token
    connected = False
    while not connected:
      r = requests.post(smUrl)
      print("Please authorize on Touchscreen.")
      time.sleep(10)
      if "Failed" in r.text:
        print(r.text)
        print("Binding failed, please restart script")
        sys.exit(1)
      smToken = (json.loads(r.text).get("token"))
      headers = {'Content-Type' : 'application/x-www-form-urlencoded'}
      formData = {'token' : smToken}
      r = requests.post(smUrl, data=formData, headers=headers)
      if json.loads(r.text).get("token") == smToken:
        file.write(smToken)
        print("Token received and saved.\n" + smToken + "\nIf you use docker set SM_TOKEN env var and restart the container.")
        connected = True
        return(smToken)

  else:
    file.close()
    # Connect to SnapMaker with saved token
    headers = {'Content-Type' : 'application/x-www-form-urlencoded'}
    formData = {'token' : smToken}
    r = requests.post(smUrl, data=formData, headers=headers)
    return(smToken)

def readStatus(smToken):
  print("Reading SnapMaker Status...")
  smApi = "http://" + connectIP + ":" + connectPort + "/api/v1/status?token="
  r = requests.get(smApi+smToken)
  smStatus = json.loads(r.text)
  #print(smStatus)

  smStatus['ip'] = connectIP
  # toolHeads:
  #   TOOLHEAD_3DPRINTING_1 (both single and dual head)
  #   TOOLHEAD_CNC_1
  #   TOOLHEAD_LASER_1
  if smStatus.get('toolHead') == "TOOLHEAD_3DPRINTING_1":
    if smStatus.get('nozzleTemperature') is None:
      print("Current Toolhead: Dual Extruder")
      smStatus['toolHead'] = 'Dual Extruder'
      smStatus['nozzleTemperature'] = smStatus.get('nozzleTemperature1')
      smStatus['nozzleTargetTemperature'] = smStatus.get('nozzleTargetTemperature1')
    else:
      smStatus['toolHead'] = "Extruder"
      print("Current Toolhead: Extruder")
  elif smStatus.get('toolHead') == "TOOLHEAD_CNC_1":
    smStatus['toolHead'] = 'CNC'
    print("Current Toolhead: CNC")
  elif smStatus.get('toolHead') == "TOOLHEAD_LASER_1":
    smStatus['toolHead'] = 'Laser'
    print("Current Toolhead: Laser")

  if smStatus.get("progress") is not None:
    smStatus['progress'] = ("{:0.1f}".format(smStatus.get("progress")*100))
  else:
    smStatus['progress'] = "0"

  if smStatus.get("estimatedTime") is not None:
    smStatus['estimatedTime'] = str(timedelta(seconds=smStatus.get("estimatedTime")))
  else:
    smStatus['estimatedTime'] = str(timedelta(seconds=0))

  if smStatus.get("elapsedTime") is not None:
    smStatus['elapsedTime'] = str(timedelta(seconds=smStatus.get("elapsedTime")))
  else:
    smStatus['elapsedTime'] = str(timedelta(seconds=0))

  if smStatus.get("remainingTime") is not None:
    smStatus['remainingTime'] = str(timedelta(seconds=smStatus.get("remainingTime")))
  else:
    smStatus['remainingTime'] = str(timedelta(seconds=0))

  return(smStatus)

# Check if IP is valid:
def validate_ip_address(ipString):
  try:
    ipaddress.ip_address(ipString)
    return True
  except ValueError:
    return False

# POST to HomeAssistant Webhook
def postIt(status):
  jsonStatus = json.dumps(status, default=str, sort_keys=False, indent=2)
  session = requests.Session()
  session.verify = False
  print("Sending State:", jsonStatus)
  try:
    requests.post(whUrl, json = jsonStatus)
  except requests.exceptions.ConnectionError:
    print("Could not connect to HomeAssistant on", whUrl)
    return

def is_reachable(ipAddress, apiPort):
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
      sock.settimeout(1)  # Timeout in seconds
      sock.connect((ipAddress, int(apiPort)))
      return True
  except Exception:
    return False

# Check status of Snapmaker 2.0 via UDP Discovery
# Possible replies:
#  'Snapmaker@X.X.X.X|model:Snapmaker 2 Model A350|status:IDLE'
#  'Snapmaker@X.X.X.X|model:Snapmaker 2 Model A350|status:RUNNING'
def updDiscover():
  global retryCounter
  bufferSize = 1024
  msg = b'discover'
  destPort = 20054
  sockTimeout = 1.0
  retries = 5
  UDPClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  UDPClientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
  UDPClientSocket.settimeout(sockTimeout)
  UDPClientSocket.sendto(msg, ("255.255.255.255", destPort))
  try:
    reply, serverAddress = UDPClientSocket.recvfrom(bufferSize)
    elements = str(reply).split('|')
    return((elements[0]).replace('\'',''))
  except socket.timeout:
    retryCounter += 1
    if (retryCounter==retries):
      print("UDP discover failed")
      sys.exit(1)
    else:
      updDiscover()

# Run Main Program
main()
