#!/usr/bin/env python3

"""
WirelessPCLock.py - Copyright (C) 2020  Zack Didcott.

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

import argparse
import logging
import sys
import _thread
import time
import webbrowser
from select import select

# GTK #
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import Gtk, AppIndicator3  # noqa: E402

from utils import lock, unlock, get_lock_state, get_device  # noqa: E402


class WPCL:
    """GTK applet to control WPCL."""

    def __init__(self, args):
        """Configure attributes and start applet."""
        self.ABOUT_URL = "https://github.com/Zedeldi/WPCL"
        self.RECEIVER_NAME = args.device
        self.TIMEOUT = args.timeout

        self.device = get_device(self.RECEIVER_NAME)  # Get device to watch
        if self.device is None:
            sys.exit(1)
        self.main()

    def main(self):
        """Create applet and start listener thread."""
        self.indicator = AppIndicator3.Indicator.new(
            "WirelessPCLock",
            "lock.svg",
            AppIndicator3.IndicatorCategory.SYSTEM_SERVICES,
        )  # GTK applet
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())
        # Listen for data in a separate thread, to prevent main loop blocking
        self.listener = _thread.start_new_thread(self.listen, ())

    def build_menu(self):
        """Configure the GTK applet menu."""
        menu = Gtk.Menu()
        self.enabled = Gtk.CheckMenuItem.new_with_label("Enabled")
        self.enabled.set_active(True)
        self.enabled.connect("toggled", self.toggle_listen)
        menu.append(self.enabled)
        item_about = Gtk.MenuItem.new_with_label("About")
        item_about.connect("activate", self.about)
        menu.append(item_about)
        item_separator = Gtk.SeparatorMenuItem()
        menu.append(item_separator)
        item_quit = Gtk.MenuItem.new_with_label("Quit")
        item_quit.connect("activate", self.quit)
        menu.append(item_quit)
        menu.show_all()
        return menu

    def listen(self):
        """Listen for data on device and handle locking."""
        try:
            while True:
                while self.enabled.get_active():
                    # Blocks until data or timeout is reached
                    r, w, x = select([self.device], [], [], self.TIMEOUT)
                    if not self.enabled.get_active():
                        # In case user disabled during wait
                        break
                    if len(r) == 0:  # Device inactive, lock
                        logging.debug("Timed out.")
                        if not get_lock_state():  # Do not lock twice
                            lock()
                    else:  # Device is active, unlock
                        logging.debug("Data received.")
                        if get_lock_state():
                            unlock()
                        while self.device.read_one():
                            # Flush device buffer
                            logging.debug("Flushing device buffer...")
                time.sleep(1)
        except OSError as e:  # I/O failed
            logging.error(f"Lost communication with receiver ({e})")
            if not get_lock_state():
                lock()
            _thread.interrupt_main()  # Sends SIGINT to main thread

    def toggle_listen(self, caller):
        """Toggle the lock icon on state change."""
        if self.enabled.get_active():
            self.indicator.set_icon_full("lock.svg", "Locking enabled.")
            logging.info("Enabled.")
        else:
            self.indicator.set_icon_full("unlock.svg", "Locking disabled.")
            logging.info("Disabled.")

    def about(self, caller):
        """Open about URL in a browser."""
        webbrowser.open(self.ABOUT_URL, new=2, autoraise=True)

    def quit(self, caller):
        """Close applet and handle process end."""
        logging.info("Goodbye :)")
        Gtk.main_quit()
        time.sleep(1)  # Give time for evdev to close device before Python dies


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Wireless PC Lock - Copyright (C) 2020 Zack Didcott"
    )
    parser.add_argument(
        "-d",
        "--device",
        type=str,
        default="HID 13b7:7417",
        help="specify a device name (default: HID 13b7:7417)",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=5,
        help=(
            "timeout before locking, in seconds; should be longer than the "
            "interval between communications (default: 5)"
        ),
    )
    parser.add_argument(
        "-l", "--log", type=str, default=None, help="output log into a file"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const=-1,
        default=0,
        dest="verbosity",
        help="only display errors",
    )
    group.add_argument(
        "-v",
        "--verbose",
        action="store_const",  # See also: action="count"
        const=1,
        default=0,
        dest="verbosity",
        help="display debugging information (default: INFO)",
    )

    args = parser.parse_args()

    # Logging #
    loglevel = 20 - (args.verbosity * 10)
    logging.basicConfig(
        # Possible values:
        # CRITICAL	= 50
        # ERROR		= 40
        # WARNING	= 30
        # INFO		= 20
        # DEBUG		= 10
        level=loglevel,
        filename=args.log,
        format="%(asctime)s | [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    logging.info(parser.description)
    logging.debug("== Configuration ==")
    for arg, value in sorted(vars(args).items()):
        logging.debug(f"{arg.title()}: {value}")
    logging.debug("===================")

    app = WPCL(args)
    try:
        Gtk.main()
    except KeyboardInterrupt:
        sys.exit(1)
