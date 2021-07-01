# raspi-bt-hd-audio-receiver

Connect your sound system to Bluetooth devices. Control your sound system to switch inputs when Bluetooth devices are connected and switch back after they disconnect (needs adjusting to fit to your sound system).

Tested with a Raspberry Pi 2 and an old Bluetooth 2.0 receiver; works very well and reliable even with that old hardware.

**Important notice:**

Using a newer Raspberry Pi is of course totally fine. But be aware that built in WiFi and Bluetooth are interferring so that you should either use the built in WiFi and an external Bluetooth dongle or use an ethernet connection to ensure a stutter free connection.

Basic explanations and terminal commands are following. Sometimes adjusting commands to your needs can be necessary. Feel also free to skips some steps.

## 1 Basic installation

- Install Raspberry Pi OS headless (tested with Buster) from https://www.raspberrypi.org/software/
- After flashing to the SD card, mount it and activate SSH with `touch ssh` in the boot partition
- Start the Raspberry Pi and connect via SSH with `ssh pi@raspberrypi`. Password is `raspberry`.


```
sudo apt update
sudo apt upgrade
sudo apt install git
git clone https://codeberg.org/epinez/raspi-bt-hd-audio-receiver.git ~/raspi-bt-hd-audio-receiver
cd ~/raspi-bt-hd-audio-receiver
git submodule init
git submodule update
sudo nano /etc/machine-info
PRETTY_HOSTNAME=<YOUR-DESIRED-BLUETOOTH-NAME>
sudo reboot
```

## 2 Bluealsa (former "bluez-alsa")

Bluealsa and its command line utilities are there for the Bluetooth connection and the Bluetooth audio playability. Outputting the sound to HDMI is default.

Helpful information: https://github.com/Arkq/bluez-alsa/wiki/Installation-from-source

In order to support some codecs (AAC and apt-X / HD) for license reasons you need to compile these dependencies from source, adjust some build parameters for bluealsa and compile that from source, too (See 2.2 and 2.3).

### 2.1 Dependencies from official repository

`sudo apt install automake build-essential libtool pkg-config python-docutils libasound2-dev libbluetooth-dev libdbus-1-dev libglib2.0-dev libsbc-dev cmake`

### 2.2 AAC codec with fdk-aac

```
cd ~/raspi-bt-hd-audio-receiver/fdk-aac/
./autogen.sh 
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
sudo cmake --install ./
```

### 2.3 APT-X and APT-X HD with libopenaptx

```
cd ~/raspi-bt-hd-audio-receiver/libopenaptx/
sudo make install
```

### 2.4 Bluealsa

```
cd ~/raspi-bt-hd-audio-receiver/bluez-alsa
autoreconf --install --force
mkdir build
cd build
../configure --enable-aac --enable-ofono --enable-debug --enable-aptx --enable-aptx-hd --with-libopenaptx
make
sudo make install
```

## 3 Bluetooth prerequisites

`sudo cp ~/raspi-bt-hd-audio-receiver/systemd-services/bluealsa.service /lib/systemd/system/bluealsa.service`

In order to start the service automatically after reboot and after the Bluetooth hardware is set up:

`sudo cp ~/raspi-bt-hd-audio-receiver/udev-rules/100-bluealsa.rules /etc/udev/rules.d/100-bluealsa.rules`

Give Bluetooth permission to the pi user: `sudo adduser pi bluetooth`

Get rid of some Bluetooth error: `sudo nano /lib/systemd/system/bluetooth.service`

Change the ExecStart line to: `ExecStart=/usr/lib/bluetooth/bluetoothd --noplugin=sap`

Reboot and see wether the services are up and running.

`sudo reboot`

Debugging commands (in case something does not work properly):

```
sudo systemctl status bluealsa.service
sudo systemctl status bluetooth.service
sudo systemctl restart bluealsa.service
sudo systemctl restart bluetooth.service
```

## 4 Bluetooth Pairing

```
bluetoothctl
power on
agent on
default-agent
scan on
// Wait for the pairing target and copy it's Bluetooth address
scan off
trust XX:XX:XX:XX:XX:XX
pair XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
```

Trusting ensures the device gets autoconnected to even after reboot.

Now enter the Bluetooth PIN and confirm. Enter the PIN on the target device (e.g. smartphone) and exit bluetoothctl with Ctrl + C. The connection stays established nevertheless.

## 5 Bluetooth Audio Playback

Test the audio device: `bluealsa-aplay 00:00:00:00:00:00`

Playing audio on the connected device should work now. Defaults to the Pi's HDMI output. You may now exit the player with Ctrl + C and automatically start the audio player after reboot by:

`sudo cp ~/raspi-bt-hd-audio-receiver/systemd-services/bluealsa-aplay.service /lib/systemd/system/bluealsa-aplay.service`

Activate the service:

```
sudo systemctl daemon-reload
sudo systemctl enable bluealsa-aplay.service
sudo systemctl start bluealsa-aplay.service
```

## 6 Manage connected sound system

In my case it makes life much easier to do some automation on the sound system side (AVR which has a REST-API) when a Bluetooth device connects and disconnects. Feel free to skip this step or alter the script to control your own sound system. Using HDMI-CEC with cec-client could also be an alternative.

**Current Features (as of 01.07.2021):**

- Make a simple sound on bluetooth connect / disconnect
- Switch on after connecting bluetooth device if currently in standby
- Switch to Raspberry Pi input after connecting bluetooth device
- Switch back to last input after disconnecting bluetooth device

```
chmod +x ~/raspi-bt-hd-audio-receiver/avr-manager.py
sudo apt install python3-pip libsdl2-2.0-0 libsdl2-mixer-2.0-0
pip3 install requests pyudev pygame
```

`sudo cp ~/raspi-bt-hd-audio-receiver/systemd-services/avr-manager.service /lib/systemd/system/avr-manager.service`

Activate the service:

```
sudo systemctl daemon-reload
sudo systemctl enable avr-manager.service
sudo systemctl start avr-manager.service
```

## 7 Deactivate Raspberry Pi LEDs

`sudo nano /boot/config.txt`

Add the following lines:

```
#disable ACT and PWR LEDs
dtparam=act_led_trigger=none
dtparam=pwr_led_trigger=none

#disable ethernet port LEDs
dtparam=eth0_led=4
dtparam=eth1_led=4
```

Deactivating ethernet LEDs does only work with Raspberry 3 and above like that. Older Raspberrys need a specific tool for that.

```
sudo apt install libusb-1.0-0-dev
cd ~/raspi-bt-hd-audio-receiver/lan951x-led-ctl
make
chmod +x lan951x-led-ctl
sudo ./lan951x-led-ctl --fdx=0 --lnk=0 --spd=0
```

The program has to be started after every reboot, you can autostart it with:

`sudo nano /etc/rc.local`

Add the following above `exit 0`:

`sudo /home/pi/raspi-bt-hd-audio-receiver/lan951x-led-ctl/lan951x-led-ctl --fdx=0 --lnk=0 --spd=0`

---

## Possible improvements

- LDAC codec support for higher quality audio
- Automate the steps above in a handy script with a few prompts
- Allow other devices (than the already trusted) to connect headless

AVR or other sound system related:

- Use Bluetooth hardware volume changes on connected device to trigger AVR volume via REST

## Contributing

Feel free to:

- file issues or correct the doc if some steps do not work as they are stated here
- improve or shorten steps
- suggest actions for an enhanced audio quality