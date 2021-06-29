# raspi-bt-hd-audio-receiver

Connect your sound system to Bluetooth devices. Control your sound system to switch inputs when Bluetooth devices are connected and switch back after they disconnect (needs adjusting to fit to your sound system).

Tested with a Raspberry Pi 2 and an old Bluetooth 2.0 receiver; works very well and reliable even with that old hardware.

Important notice:

Using a newer Raspberry Pi is of course totally fine. But be aware that built in WiFi and Bluetooth are interferring so that you should either use the built in WiFi and an external Bluetooth dongle or use an ethernet connection to ensure a stutter free connection.

Basic explanations and terminal commands are following. Sometimes adjusting commands to your needs can be necessary. Feel also free to skips some steps.

## 1 Basic installation

- Install Raspberry Pi OS headless (tested with Buster) from https://www.raspberrypi.org/software/
- After flashing to the SD card, mount it and activate SSH with `touch ssh` in the boot partition
- Start the Raspberry Pi and connect via SSH with `ssh pi@raspberrypi`. Password is `raspberry`.


```
sudo apt update
sudo apt upgrade
sudo nano /etc/machine-info
PRETTY_HOSTNAME=<YOUR-DESIRED-BLUETOOTH-NAME>
sudo reboot
```

## 2 Bluealsa (former "bluez-alsa")

Bluealsa and its command line utilities are there for the Bluetooth connection and the Bluetooth audio playability. Outputting the sound to HDMI is default.

Helpful informationen: https://github.com/Arkq/bluez-alsa/wiki/Installation-from-source

In order to support some codecs (AAC and apt-X / HD) for license reasons you need to compile these dependencies from source, adjust some build parameters for bluealsa and compile that from source, too (See 2.2 and 2.3).

### 2.1 Dependencies from official repository

`sudo apt install git automake build-essential libtool pkg-config python-docutils libasound2-dev libbluetooth-dev libdbus-1-dev libglib2.0-dev libsbc-dev cmake`

### 2.2 AAC codec with fdk-aac

```
cd ~
git clone https://github.com/mstorsjo/fdk-aac.git
cd fdk-aac/
./autogen.sh 
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
sudo cmake --install ./
```

### 2.3 APT-X and APT-X HD with libopenaptx

```
cd ~
git clone https://github.com/pali/libopenaptx.git
cd libopenaptx/
sudo make install
```

### 2.4 Bluealsa

```
cd ~
git clone https://github.com/Arkq/bluez-alsa.git
cd bluez-alsa
autoreconf --install --force
mkdir build
cd build
../configure --enable-aac --enable-ofono --enable-debug --enable-aptx --enable-aptx-hd --with-libopenaptx
make
sudo make install
```

## 3 Bluetooth prerequisites

Copy the `systemd-services/bluealsa.service` file from this repo to `/lib/systemd/system/bluealsa.service`

In order to start the service automatically after reboot and after the Bluetooth hardware is set up:

```
cd /etc/udev/rules.d/
sudo nano 100-bluealsa.rules
```

Add the following line: `ACTION=="add", KERNEL=="hci0", ENV{SYSTEMD_WANTS}+="bluealsa.service"`

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

Start the audio device: `bluealsa-aplay 00:00:00:00:00:00`

Playing audio on the connected device should work now. Defaults to the Pi's HDMI output. You may now exit the player with Ctrl + C.

To automatically start the audio player after reboot copy the `systemd-services/bluealsa-aplay.service` file from this repo to `/lib/systemd/system/bluealsa-aplay.service`

Activate the service:

```
sudo systemctl daemon-reload
sudo systemctl enable bluealsa-aplay.service
sudo systemctl start bluealsa-aplay.service
```

## Automatic input change of sound system on device connect

In my case it makes life easier to automatically switch the input of the sound system (AVR which has a REST-API) when a Bluetooth device connects and switch back to the old input after it disconnected. Feel free to skip this step or alter it to control your own sound system. Using HDMI-CEC with cec-client could also be an alternative.

`cd ~`

Add the `switch-avr-input.py` file from this repo.

```
chmod +x switch-avr-input.py
sudo apt install python3-pip
pip3 install requests
pip3 install pyudev
sudo nano /lib/systemd/system/switch-avr-input.service
```

Copy the `systemd-services/switch-avr-input.service` file from this repo to `/lib/systemd/system/switch-avr-input.service`

Activate the service:

```
sudo systemctl daemon-reload
sudo systemctl enable switch-avr-input.service
sudo systemctl start switch-avr-input.service
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

---

## Possible improvements

- LDAC codec support for higher quality audio
- Automate the steps above in a handy script with a few prompts

AVR or other sound system related:

- Use Bluetooth hardware volume changes on connected device to trigger AVR volume via REST
- Switch on AVR after Bluetooth device connected if it was off before
- Allow other devices (than the already trusted) to connect headless

## Contributing

Feel free to:

- file issues or correct the doc if some steps do not work as they are stated here
- improve or shorten steps
- suggest actions for an enhanced audio quality