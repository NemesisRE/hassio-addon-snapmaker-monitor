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
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RETRY_COUNTER = 0
TOKEN_FILE = os.path.join(os.getcwd(), "SMtoken.txt")  # Set to writable location (default is script location)
DISCOVER_PORT = 20054
BROADCAST_ADDRESS = "255.255.255.255"
UDP_TIMEOUT = 1.0
UDP_RETRIES = 5
BUFFER_SIZE = 1024

# Read config from ENV VARS or Set manually
HA_TOKEN = os.environ.get("HA_TOKEN", '')  # Set your HomeAssistant API Token
HA_WEBHOOK_URL = os.environ.get("HA_WEBHOOK_URL", '')  # Set your HomeAssistant WebHook URL
CONNECT_IP = os.environ.get("SM_IP", '')  # Set your SnapMaker IP or let it discover
CONNECT_PORT = os.environ.get("SM_PORT", '8080')  # Set your SnapMaker API Port (default is 8080)
SM_TOKEN = os.environ.get("SM_TOKEN", 'generate_token')  # Set your SnapMaker API Token or let it generate


def main():
  """Main program function."""
  global CONNECT_IP

  if not CONNECT_IP:
    logging.info("connectIP not set, will try to discover")
    CONNECT_IP = updDiscover()

  if not validate_ip_address(CONNECT_IP):
    logging.error(f"connectIP ({CONNECT_IP}) is not valid")
    sys.exit(1)

  if not is_reachable(CONNECT_IP, CONNECT_PORT):
    logging.error(f"Set IP ({CONNECT_IP}) not reachable")
    postIt('{"status": "UNAVAILABLE"}')
    sys.exit(1)

  global SM_TOKEN
  if not SM_TOKEN or SM_TOKEN == "generate_token":
    logging.info("smToken not set, will try to generate")
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
              logging.info(f"Token received and saved.\n{sm_token}\nIf you use docker set SM_TOKEN env var and restart the container.")
              return sm_token
          except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            time.sleep(10)  # Wait before retrying
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

  sm_status['ip'] = CONNECT_IP

  # Toolhead detection
  tool_head = sm_status.get('toolHead')
  if tool_head == "TOOLHEAD_3DPRINTING_1":
    if sm_status.get('nozzleTemperature') is None:
      logging.info("Current Toolhead: Dual Extruder")
      sm_status['toolHead'] = 'Dual Extruder'
      sm_status['nozzleTemperature'] = sm_status.get('nozzleTemperature1')
      sm_status['nozzleTargetTemperature'] = sm_status.get('nozzleTargetTemperature1')
    else:
      logging.info("Current Toolhead: Extruder")
      sm_status['toolHead'] = "Extruder"
  elif tool_head == "TOOLHEAD_CNC_1":
    logging.info("Current Toolhead: CNC")
    sm_status['toolHead'] = 'CNC'
  elif tool_head == "TOOLHEAD_LASER_1":
    logging.info("Current Toolhead: Laser")
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
  logging.info(f"Sending State: {json_status}")
  try:
    requests.post(HA_WEBHOOK_URL, json=json_status)
  except requests.exceptions.RequestException as e:
    logging.error(f"Could not connect to HomeAssistant on {HA_WEBHOOK_URL}: {e}")


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
  main()
