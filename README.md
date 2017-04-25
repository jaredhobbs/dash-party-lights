# Dash button party lights!

This code reacts to Amazon Dash buttons and is designed for the Raspberry Pi.
Pressing the Dash button will trigger a party light mode on connected Hue
lightbulbs. The Dash button code is based on
[One-Second-Dash](https://github.com/ridiculousfish/one-second-dash)
and the Hue code is based on this
[eShares blog post](https://blog.esharesinc.com/how-we-connect-our-office-lights-to-nps-twitter-and-slack/).

The code works by placing your WiFi interface in monitor mode and listening for
probe requests for a special SSID that does not exist (via tcpdump).

This method also has the advantage that your Dash buttons do not join your
network and need not be given its password.

## Usage

#### Dash button setup

1. Configure a router with a non-existant network SSID and make note of the
   channel.
2. Setup the Dash button through the Amazon app as usual, but exit the setup
   _before_ choosing a product to associate the button with.
3. You can destroy the network after setting up the button; it's no longer
   necessary.

#### Raspberry Pi Setup

This tutorial assumes you also want to have your RPi on your normal WiFi
network. This requires two dongles, since monitor mode displaces managed mode.
If you are happy using Ethernet, things are a little simpler.

1. Clone this repo on your RPi
2. Get a network dongle that supports monitor mode.
   Be careful with the chipset: RT5370 works, RTL8188CUS does not.
3. Install requirements:

        sudo apt-get update
		sudo apt-get install jq iw tcpdump python-pip
        pip install -r requirements.txt

4. If you are using two dongles, we need to be able to tell them apart.
   We do this by looking at the _capabilities_ according to `iw phy`.
   Run `iw phy` and look for a field like `Capabilities:`.
   Figure out which one corresponds to your monitor dongle and add that to the
   `config.json` file, for example, `Capabilities: 0x1862`
    
    One way to figure this out is to run `iw phy` with only one dongle
    attached. That tells you the capabilities for that dongle.
	
	If you are using Ethernet, you'll only get one Capabilities field.

5. `wpa_supplicant` is your nemesis. We want to disable it.
   Edit `/etc/network/interfaces`. If you plan to use Ethernet, make the WiFi
   section look like so:

        allow-hotplug wlan0
    
	If you plan to use two WiFi dongles, make it look like so
    (here wlan0 is the managed mode interface, that will connect to the real
    network, and wlan1 will be the monitor).

        allow-hotplug wlan0
        auto wlan0
        iface wlan0 inet dhcp
                wpa-ssid "YourWiFiSSID"
                wpa-psk c1c28a70e6f7180ca50300fbc9b451cc1d519c4b33df3c4d30
        
        allow-hotplug wlan1
	
    `YourWiFiSSID` is replaced with your network's SSID (the real one that your
    RPi connects to, not the fake one for the Dash). The wpa-psk value can be
    obtained via `wpa_passphrase YourWiFiSSID`
    (`sudo apt-get install wpasupplicant` if necessary)

6. Edit `config.json`:
   * Set `SSIDs` to the SSID you chose during Dash setup
   * Set `Channel` to the channel you identified in step 2 under
     "Dash button setup".
   * Set `Capabilities` to the capabilities field you identified in step 4

7. `sudo start.sh` and watch the output. Once you see the line starting with
   `listening on ButtonMonitor`, press your Dash button.
   You should see a line printed!

   Note: For the first run, you'll need to press the link button on the
   Hue bridge before running the `start.sh` command.
   The command should be run within 30 seconds of pressing the link button.

8. To make your Dash button do something else, modify the `partyTime()`
   function in `lights.py`.

##### Launch at boot

1. To make the party lights script run at boot, you can edit the
   `/etc/rc.local` file to invoke `start.sh` (before exit 0):

        sudo -u pi /home/pi/dash-party-lights/start.sh > /home/pi/dash.log &
