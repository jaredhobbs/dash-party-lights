#!/bin/bash

# The channel of that SSID that Dash will try to connect to
# You can either choose this at network creation time,
# or determine it afterwards via tcpdump
CHANNEL=$(jq -r '.Dash.Channel' config.json)

# The capability field of your WiFi dongle
# You can determine this via `iw phy`
CAP_FIELD="$(jq -r '.Dash.Capabilities' config.json)"

# cd to directory containing this script
cd $(dirname $(readlink -f $0))

# tcpdump or someone else eventually gives up
# and tears down our monitor interface. Loop to
# recreate it.
# The break allows us to control-C out of this loop.
while true; do
    sudo ./setup_monitor_interface.sh "$CHANNEL" "$CAP_FIELD" 2>&1
    sudo ./lights.py || break
done
