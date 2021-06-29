"""Collection of functions to handle locking and evdev."""

import evdev
import logging
import os
import psutil


def lock() -> None:
    """Lock the system."""
    logging.info("Locking...")
    os.system("i3lock")


def unlock() -> None:
    """Unlock the system."""
    logging.info("Unlocking...")
    os.system("pkill i3lock")


def get_lock_state() -> bool:
    """Return current lock state."""
    return "i3lock" in (p.name() for p in psutil.process_iter())


def get_device(receiver_name: str) -> evdev.InputDevice:
    """Return device with provided name."""
    # Get list of devices
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if device.name == receiver_name:  # Found receiver
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
