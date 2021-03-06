#!/usr/bin/python
import json
import random
import signal
import subprocess
import sys
import time
from threading import Thread

from phue import Bridge

with open('config.json', 'r') as f:
    config = json.load(f)
dash_config = config['Dash']

# After party time, how many seconds before we allow ourselves to activate
# the lights again
DEBOUNCE_INTERVAL = config['Debounce']


class PartyTime(Thread):
    def __init__(self, *args, **kwargs):
        super(PartyTime, self).__init__(*args, **kwargs)
        self.daemon = True

        hue_config = config['Hue']
        self.bridge = Bridge(hue_config['bridge-ip'])
        self.bridge.connect()

        # Setup lights
        self.light_group = hue_config['light-group']
        self.group_name = hue_config['light-group-name']
        self.bridge.create_group(self.group_name, self.light_group)
        self.base_light_state = {
            'bri': 120,
            'sat': 0,
            'transitiontime': 10,
            'on': True,
        }

        self.enabled = False
        self.base_lights()
        self.start()

    def base_lights(self):
        self.bridge.set_group(self.group_name, self.base_light_state)
        time.sleep(1)

    def hue_point(self, color):
        """
        Splits the spectrum up by the number of lights in the light group to
        get an evenly spaced rainbow of colors
        """
        color = int(color % len(self.light_group))
        hue = 65535 / len(self.light_group)
        hue = hue * color
        return hue

    def party_on(self):
        """
        Sets a random light, the next step in the rainbow, defined using the
        hue_point method
        """
        random.shuffle(self.light_group)
        params = {'sat': 254, 'bri': 254, 'transitiontime': 1}
        i = 0
        while self.enabled:
            params['hue'] = self.hue_point(i)
            self.bridge.set_light(random.choice(self.light_group), params)
            time.sleep(0.05)
            i += 1

    def party_off(self):
        # reset to base state
        base = dict(self.base_light_state)
        base['transitiontime'] = 3
        for light in self.light_group:
            self.bridge.set_light(light, base)
            time.sleep(0.2)
        self.base_lights()

    def toggle(self):
        self.enabled = not self.enabled

    def run(self):
        while True:
            if self.enabled:
                self.party_on()
            else:
                self.party_off()
            time.sleep(0.1)


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

party_time = PartyTime()
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
                party_time.toggle()
