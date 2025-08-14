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
import paho.mqtt.client as mqtt
import logging

# Configure logging
log_level = os.environ.get("LOG_LEVEL", 'INFO').upper()
numeric_level = getattr(logging, log_level, None)
if not isinstance(numeric_level, int):
  print(f"Invalid log level: {log_level}, defaulting to INFO")
  numeric_level = logging.INFO
logging.basicConfig(level=numeric_level, format='%(asctime)s - %(levelname)s - %(message)s')

RETRY_COUNTER = 0
DISCOVER_PORT = 20054
BROADCAST_ADDRESS = "255.255.255.255"
UDP_TIMEOUT = 1.0
UDP_RETRIES = 5
BUFFER_SIZE = 1024

# Read config from ENV VARS or Set manually
MQTT_BROKER = os.environ.get("MQTT_BROKER", '')
MQTT_PORT = int(os.environ.get("MQTT_PORT", '1883'))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", 'snapmaker/status')
MQTT_USER = os.environ.get("MQTT_USER", '')
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", '')
HA_TOKEN = os.environ.get("SUPERVISOR_TOKEN", '')  # Set your HomeAssistant API Token
if os.path.exists("/.dockerenv"):
  HA_WEBHOOK_ID = os.environ.get("HA_WEBHOOK_ID")  # HomeAssistant WebHook ID
  HA_WEBHOOK_URL = "http://supervisor/core/api/webhook/" + HA_WEBHOOK_ID
else:
  HA_WEBHOOK_URL = os.environ.get("HA_WEBHOOK_URL", '')  # Set your HomeAssistant WebHook URL
CONNECT_IP = os.environ.get("SM_IP", '')  # Set your SnapMaker IP or let it discover
CONNECT_PORT = os.environ.get("SM_PORT", '8080')  # Set your SnapMaker API Port (default is 8080)
if os.path.exists("/.dockerenv"):
  TOKEN_FILE = os.path.join("/data", "SMtoken.txt")  # inside Docker
else:
  TOKEN_FILE = os.path.join(os.getcwd(), "SMtoken.txt")  # not in Docker

def main():
  """Main program function."""
  global CONNECT_IP

  if not CONNECT_IP:
    logging.info("connectIP not set, will try to discover")
    CONNECT_IP = updDiscover()

  if not validate_ip_address(CONNECT_IP):
    logging.error(f"connectIP ({CONNECT_IP}) is not valid")
    sys.exit(1)

  retry_count = 0
  while retry_count < 5:
    if not is_reachable(CONNECT_IP, CONNECT_PORT):
      logging.warning(f"Set IP ({CONNECT_IP}) not reachable, retrying in {retry_count} minutes")
      postIt('{"status": "UNAVAILABLE"}')
      time.sleep(retry_count * 60)  # Wait for an increasing amount of time
      retry_count += 1
    else:
      break  # If reachable, exit the loop
  else:  # This else belongs to the while loop, executed if the loop finishes without a break
    logging.error(f"Set IP ({CONNECT_IP}) not reachable after multiple retries")
    postIt('{"status": "UNAVAILABLE"}')
    sys.exit(1)

  global SM_TOKEN
  SM_TOKEN = getSMToken(CONNECT_IP)

  logging.info(f"Connecting with Token: {SM_TOKEN}")
  sm_status = readStatus(SM_TOKEN)
  postIt(sm_status)


def getSMToken(connect_ip):
  """Gets the SnapMaker token, either from file or by generating a new one."""
  sm_url = f"http://{connect_ip}:{CONNECT_PORT}/api/v1/connect"

  try:
    with open(TOKEN_FILE, "r+") as file:
      sm_token = file.read().strip()
      if sm_token:
        # Connect to SnapMaker with saved token
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        form_data = {'token': sm_token}
        try:
          requests.post(sm_url, data=form_data, headers=headers)
          return sm_token
        except requests.exceptions.RequestException as e:
          logging.error(f"Error connecting to Snapmaker with saved token: {e}")
          return None  # Or handle the error as appropriate

      else:
        # Create token
        logging.info("smToken not set, will try to generate")
        while True:
          try:
            r = requests.post(sm_url)
            r.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            logging.info("Please authorize on Touchscreen.")
            time.sleep(10)

            if "Failed" in r.text:
              logging.error(r.text)
              logging.error("Binding failed, please restart script")
              sys.exit(1)

            sm_token = json.loads(r.text).get("token")
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            form_data = {'token': sm_token}
            r = requests.post(sm_url, data=form_data, headers=headers)
            r.raise_for_status()

            if json.loads(r.text).get("token") == sm_token:
              file.seek(0)
              file.write(sm_token)
              file.truncate()
              logging.info(f"Token received and saved to {TOKEN_FILE}.")
              return sm_token
          except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            time.sleep(20)  # Wait before retrying
          except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON: {e}")
            sys.exit(1)
  except FileNotFoundError:
    try:
      # Create file and retry
      open(TOKEN_FILE, "w+").close()  # Create the file and immediately close it
      return getSMToken(connect_ip)  # Recursive call after creating the file
    except OSError as e:
      logging.error(f"Unable to create token file: {e}")
      sys.exit(1)


def readStatus(sm_token):
  """Reads the status from the SnapMaker."""
  logging.info("Reading SnapMaker Status...")
  sm_api = f"http://{CONNECT_IP}:{CONNECT_PORT}/api/v1/status?token="
  try:
    r = requests.get(sm_api + sm_token)
    r.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    sm_status = json.loads(r.text)
  except requests.exceptions.RequestException as e:
    logging.error(f"Request failed: {e}")
    return {"status": "UNAVAILABLE", "error": str(e)}  # Return an error status
  except json.JSONDecodeError as e:
    logging.error(f"Failed to decode JSON: {e}")
    return {"status": "UNAVAILABLE", "error": str(e)}

  logging.debug(f"SnapMaker Status: {sm_status}")

  sm_status['ip'] = CONNECT_IP

  # Toolhead detection
  tool_head = sm_status.get('toolHead')
  if tool_head == "TOOLHEAD_3DPRINTING_1":
    if sm_status.get('nozzleTemperature') is None:
      logging.debug("Current Toolhead: Dual Extruder")
      sm_status['toolHead'] = 'Dual Extruder'
      sm_status['nozzleTemperature'] = sm_status.get('nozzleTemperature1')
      sm_status['nozzleTargetTemperature'] = sm_status.get('nozzleTargetTemperature1')
    else:
      logging.debug("Current Toolhead: Extruder")
      sm_status['toolHead'] = "Extruder"
  elif tool_head == "TOOLHEAD_CNC_1":
    logging.debug("Current Toolhead: CNC")
    sm_status['toolHead'] = 'CNC'
  elif tool_head == "TOOLHEAD_LASER_1":
    logging.debug("Current Toolhead: Laser")
    sm_status['toolHead'] = 'Laser'

  # Format progress and time fields
  sm_status['progress'] = "{:0.1f}".format(sm_status.get("progress", 0) * 100)
  sm_status['estimatedTime'] = str(timedelta(seconds=sm_status.get("estimatedTime", 0)))
  sm_status['elapsedTime'] = str(timedelta(seconds=sm_status.get("elapsedTime", 0)))
  sm_status['remainingTime'] = str(timedelta(seconds=sm_status.get("remainingTime", 0)))

  return sm_status


def validate_ip_address(ip_string):
  """Checks if the provided string is a valid IP address."""
  try:
    ipaddress.ip_address(ip_string)
    return True
  except ValueError:
    return False


def postIt(status):
  """Posts the status to the HomeAssistant webhook."""
  json_status = json.dumps(status, default=str, sort_keys=False, indent=2)
  session = requests.Session()
  session.verify = False  # Disable SSL verification
  logging.debug(f"Status: {json_status}")

  if HA_WEBHOOK_URL:
    # Check if HA_WEBHOOK_URL is a valid URL
    try:
      result = requests.compat.urlparse(HA_WEBHOOK_URL)
      if not all([result.scheme, result.netloc]):
        raise ValueError
    except ValueError:
      logging.error(f"HA_WEBHOOK_URL ({HA_WEBHOOK_URL}) is not a valid URL, cannot post status.")
      sys.exit(1)

    try:
      logging.info(f"Sending State...")
      requests.post(HA_WEBHOOK_URL, json=json_status)
      logging.info("State sent successfully to HomeAssistant webhook.")
    except requests.exceptions.RequestException as e:
      logging.error(f"Could not connect to HomeAssistant on {HA_WEBHOOK_URL}: {e}")

  elif MQTT_BROKER:
    try:
      client = mqtt.Client()
      if MQTT_USER:
        logging.info(f"Sending State...")
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.publish(MQTT_TOPIC, json_status)
        client.disconnect()
        logging.info(f"State sent successfully to MQTT topic.")
    except Exception as e:
      logging.error(f"Could not connect to MQTT broker {MQTT_BROKER}: {e}")


def is_reachable(ip_address, api_port):
  """Checks if the given IP address and port are reachable."""
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
      sock.settimeout(1)  # Timeout in seconds
      sock.connect((ip_address, int(api_port)))
      return True
  except Exception:
    return False


def updDiscover():
  """Check status of Snapmaker 2.0 via UDP Discovery."""
  global RETRY_COUNTER
  msg = b'discover'
  UDPClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  UDPClientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
  UDPClientSocket.settimeout(UDP_TIMEOUT)
  UDPClientSocket.sendto(msg, (BROADCAST_ADDRESS, DISCOVER_PORT))
  try:
    reply, serverAddress = UDPClientSocket.recvfrom(BUFFER_SIZE)
    elements = str(reply).split('|')
    return (elements[0]).replace('\'', '')
  except socket.timeout:
    RETRY_COUNTER += 1
    if (RETRY_COUNTER == UDP_RETRIES):
      logging.error("UDP discover failed")
      sys.exit(1)
    else:
      return updDiscover()


# Run Main Program
if __name__ == "__main__":
  # Check if running inside a Docker container
  if os.path.exists("/.dockerenv"):
    logging.debug("Running inside a Docker container")
    while True:
      try:
        main()
        time.sleep(60)
      except Exception as e:
        logging.error(f"An error occurred: {e}")
        time.sleep(60)
  else:
    logging.debug("Not running inside a Docker container")
    main()
    sys.exit(0)
