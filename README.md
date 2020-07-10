# WPCL

[![GitHub license](https://img.shields.io/github/license/Zedeldi/WPCL?style=flat-square)](https://github.com/Zedeldi/WPCL/blob/master/LICENSE) [![GitHub last commit](https://img.shields.io/github/last-commit/Zedeldi/WPCL?style=flat-square)](https://github.com/Zedeldi/WPCL/commits)

A small userspace program to get a USB Wireless PC Lock working on GNU/Linux.

## Context

I picked up this little 'Wireless PC Lock' from a charity shop, for about £2. While it seemed like a pretty neat concept all those years ago, much better implementations for remote locking exist now, e.g. Bluetooth proximity, NFC, etc. As it was just lying around, I figured I'd try to put something together to make it more useful.

For reference, a review can be found here: <https://www.dansdata.com/pclock.htm>

### Receiver

- USB ID: 13b7:7417
- Reportedly 315MHz (US), 434MHz (everywhere else)

 ![Receiver](images/receiver.png?raw=true)

- Uses generic HID drivers; recognised as a joystick

<details>
  <summary>Driver Information</summary>

  ![Devices](images/devices.png?raw=true)

  | ![HID](images/HID.png?raw=true)  | ![Controller](images/controller.png?raw=true) |
  | :------------------------------: | :-------------------------------------------: |
  |        Generic HID device        |                Game controller                |
</details>

### Software

- Originally designed for Windows 98 to XP
- Ugly & flawed, didn't use Windows' API for screen locking
- Featured poorly-written error messages

<details>
  <summary>Screenshots</summary>

  ![Default lockscreen](images/lockscreen.png?raw=true)

  ![Error message](images/error.png?raw=true)
</details>

## Installation

1. Clone this repo: `git clone https://github.com/Zedeldi/WPCL.git`
2. Install required Python modules: `pip3 install -r requirements.txt`
3. Run: `python3 WirelessPCLock.py`

## Configuration

Within utils.py, modify `lock()`, `unlock()`, and `getLockState()` to match your requirements. By default, it uses [i3lock](https://github.com/i3/i3lock) as the screen-locker.

## How it Works

Plainly, it checks for input from the receiver, and locks the screen accordingly; if data is waiting, the transmitter is in range and `unlock()` is executed. After each event, the device buffer is flushed, and the program waits for more input. If a timeout is reached instead, `lock()` is called.

Libraries:

- [evdev](https://pypi.org/project/evdev/) - device event interface
- [psutil](https://pypi.org/project/psutil/) - check running processes
- [PyGObject](https://pypi.org/project/PyGObject/) (GTK) - graphical tray applet

A very simplified bash version, which just watches for input from a character device:

```shell
#!/bin/bash
while true; do
	if `timeout 3 cat "/dev/input/by-id/usb-13b7_7417-event-joystick" | read -n 1`; then
		echo "Data received"
	else
		echo "Timed out"
	fi
done
```

## Caveats

As the receiver is recognised as a joystick, we have no interface to deal with RF stuff; we would need a specific driver for that. Therefore, there is no way - as far as I can tell - to differentiate between transmitters, unless the receiver emits different 'joystick events', depending on what it hears. Unfortunately, I have no other RF devices to test this.

*Do **not** use this software to protect government secrets.*

## License

WPCL is licensed under the GPL v3 for everyone to use, modify and share freely.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

[![GPL v3 Logo](https://www.gnu.org/graphics/gplv3-127x51.png)](https://www.gnu.org/licenses/gpl-3.0-standalone.html)

## Credits

Icons = <https://feathericons.com>

## Donate

If you found this project useful, please consider donating. Any amount is greatly appreciated! Thank you :smiley:

My bitcoin address is: [bc1q5aygkqypxuw7cjg062tnh56sd0mxt0zd5md536](bitcoin://bc1q5aygkqypxuw7cjg062tnh56sd0mxt0zd5md536)
