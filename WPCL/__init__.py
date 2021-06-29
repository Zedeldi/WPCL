"""
WPCL - Copyright (C) 2020  Zack Didcott.

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

import logging
import os
import sys
import _thread
import time
import webbrowser
from select import select

# GTK #
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import Gtk, AppIndicator3

from WPCL.utils import lock, unlock, get_lock_state, get_device


class WPCL:
    """GTK applet to control WPCL."""

    def __init__(self, device: str, timeout: int) -> None:
        """Configure attributes and applet."""
        self.ABOUT_URL = "https://github.com/Zedeldi/WPCL"
        self.RECEIVER_NAME = device
        self.TIMEOUT = timeout

        res = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "resources"
        )
        self.icon_enabled = os.path.join(res, "lock.svg")
        self.icon_disabled = os.path.join(res, "unlock.svg")

        self.device = get_device(self.RECEIVER_NAME)  # Get device to watch
        if self.device is None:
            sys.exit(1)
        self.init_ui()

    def init_ui(self) -> None:
        """Create applet with menu."""
        self.indicator = AppIndicator3.Indicator.new(
            "WPCL",
            self.icon_enabled,
            AppIndicator3.IndicatorCategory.SYSTEM_SERVICES,
        )  # GTK applet
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())

    def build_menu(self) -> Gtk.Menu:
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

    def run(self) -> None:
        """Start GTK process and listen for data in a new thread."""
        # Listen for data in a separate thread, to prevent main loop blocking
        _thread.start_new_thread(self.listen, ())
        Gtk.main()

    def listen(self) -> None:
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

    def toggle_listen(self, caller: Gtk.CheckMenuItem) -> None:
        """Toggle the lock icon on state change."""
        if self.enabled.get_active():
            self.indicator.set_icon_full(self.icon_enabled, "Locking enabled.")
            logging.info("Enabled.")
        else:
            self.indicator.set_icon_full(
                self.icon_disabled, "Locking disabled."
            )
            logging.info("Disabled.")

    def about(self, caller: Gtk.MenuItem) -> None:
        """Open about URL in a browser."""
        webbrowser.open(self.ABOUT_URL, new=2, autoraise=True)

    def quit(self, caller: Gtk.MenuItem) -> None:
        """Close applet and handle process end."""
        logging.info("Goodbye :)")
        Gtk.main_quit()
        time.sleep(1)  # Give time for evdev to close device before Python dies
        sys.exit(0)
