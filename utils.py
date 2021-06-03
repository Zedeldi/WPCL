"""
utils.py - Copyright (C) 2020  Zack Didcott.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import evdev
import logging
import os
import psutil


def lock():
    """Lock the system."""
    logging.info("Locking...")
    os.system("i3lock")


def unlock():
    """Unlock the system."""
    logging.info("Unlocking...")
    os.system("pkill i3lock")


def get_lock_state() -> bool:
    """Return current lock state."""
    return "i3lock" in (p.name() for p in psutil.process_iter())


def get_device(RECEIVER_NAME) -> evdev.InputDevice:
    """Return device with provided name."""
    # Get list of devices
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if device.name == RECEIVER_NAME:  # Found receiver
            try:
                device.grab()  # Try to get exclusive access
                logging.debug("Device grabbed.")
                return device
            except OSError as e:
                logging.error(f"Cannot grab device ({e})")
                return None
    else:
        logging.error("Wireless PC Lock not found.")
        return None
