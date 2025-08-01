# SnapMaker Monitor

Get SnapMaker 2.0 API Status into Home Assistant
The original [version](https://github.com/NiteCrwlr/playground/blob/main/SNStatus/SNStatusV2.py) from [NiteCrwlr](https://github.com/NiteCrwlr) did not work for me so I tried to debug it without a lot of python knowledge...

Turns out udp discovery did not work for me and still doesn't but it is now refactored and send all available data.

While creating a docker addon the script has moved to /snapmaker-monitor/rootfs/app/
