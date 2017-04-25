#!/usr/bin/python
import json
import random
import signal
import subprocess
import sys
import time

from phue import Bridge

with open('config.json', 'r') as f:
    config = json.load(f)
dash_config = config['Dash']
hue_config = config['Hue']
b = Bridge(hue_config['bridge-ip'])
b.connect()

# After party time, how many seconds before we allow ourselves to activate
# the lights again
DEBOUNCE_INTERVAL = config['Debounce']

# Setup lights
light_group = hue_config['light-group']
group_name = hue_config['light-group-name']
b.create_group(group_name, light_group)
base_light_state = {'bri': 120, 'sat': 0, 'transitiontime': 10, 'on': True}


def baseLights():
    b.set_group(group_name, base_light_state)
    time.sleep(1)


def huePoint(color):
    """Splits the spectrum up by the number of lights in the light group to get
    an evenly spaced rainbow of colors
    """
    color = int(color % len(light_group))
    hue = 65535 / len(light_group)
    hue = hue * color
    return hue


def partyLights(cycles):
    """Sets a random light, the next step in the rainbow,
    defined using the huePoint function
    """
    cycles = cycles * 16
    random.shuffle(light_group)
    params = {'sat': 254, 'bri': 254, 'transitiontime': 1}
    for i in range(cycles):
        params['hue'] = huePoint(i)
        b.set_light(random.choice(light_group), params)
        time.sleep(0.05)
    # reset to base state
    base = dict(base_light_state)
    base['transitiontime'] = 3
    for light in light_group:
        b.set_light(light, base)
        time.sleep(0.2)
    baseLights()


def partyTime():
    print "Button clicked"
    partyLights(10)

# Ignore SIGCHLD
# This will prevent zombies
signal.signal(signal.SIGCHLD, signal.SIG_IGN)

SSID_TOKENS = dash_config['SSIDs']
print "Number of tokens in list:", len(SSID_TOKENS)

print "SSID_TOKENS is/are:"
for token in SSID_TOKENS:
    print '  {}'.format(token)

cmd = 'tcpdump -l -K -q -i ButtonMonitor -n -s 256'
proc = subprocess.Popen(cmd.split(), close_fds=True,
                        bufsize=0, stdout=subprocess.PIPE)

baseLights()
last_played = 0
while True:
    line = proc.stdout.readline()
    if not line:
        print "tcpdump exited"
        sys.exit(1)
    for token in SSID_TOKENS:
        if token in line:
            now = time.time()
            if now - last_played > DEBOUNCE_INTERVAL:
                last_played = now
                sys.stdout.write(line)
                sys.stdout.flush()
                partyTime()
