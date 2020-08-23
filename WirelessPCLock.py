#!/usr/bin/env python3

# WirelessPCLock.py
# Copyright (C) 2020  Zack Didcott

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse, logging, sys, _thread, time, webbrowser
from select import select

## GTK ##
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import Gtk, AppIndicator3

from utils import *

class WPCL():
	def __init__(self, args):
		## Configuration ##
		self.ABOUT_URL="https://github.com/Zedeldi/WPCL"
		self.RECEIVER_NAME=args.device
		self.TIMEOUT=args.timeout

		self.device=getDevice(self.RECEIVER_NAME) # Get device to watch. Returns an evdev.InputDevice
		if self.device == None: sys.exit(1)
		self.main()

	def main(self):
		self.indicator = AppIndicator3.Indicator.new("WirelessPCLock", "lock.svg", AppIndicator3.IndicatorCategory.SYSTEM_SERVICES) # GTK applet
		self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
		self.indicator.set_menu(self.buildMenu())
		self.listener=_thread.start_new_thread(self.listen, ()) # Listen for data in a separate thread, to prevent main loop blocking

	def buildMenu(self):
		menu = Gtk.Menu()
		self.enabled = Gtk.CheckMenuItem.new_with_label('Enabled')
		self.enabled.set_active(True)
		self.enabled.connect('toggled', self.toggleListen)
		menu.append(self.enabled)
		itemAbout = Gtk.MenuItem.new_with_label('About')
		itemAbout.connect('activate', self.about)
		menu.append(itemAbout)
		itemSeparator = Gtk.SeparatorMenuItem()
		menu.append(itemSeparator)
		itemQuit = Gtk.MenuItem.new_with_label('Quit')
		itemQuit.connect('activate', self.quit)
		menu.append(itemQuit)
		menu.show_all()
		return menu

	def listen(self):
		try:
			while True:
				while self.enabled.get_active():
					r,w,x=select([self.device],[],[], self.TIMEOUT) # Blocks until data or timeout is reached
					if not self.enabled.get_active(): break # In case user disabled during wait
					if len(r) == 0: # Device inactive, lock
						logging.debug("Timed out.")
						if not getLockState(): lock() # Do not lock twice
					else: # Device is active, unlock
						logging.debug("Data received.")
						if getLockState(): unlock()
						while self.device.read_one(): logging.debug("Flushing device buffer...") # Flush device buffer
				time.sleep(1)
		except OSError as e: # I/O failed
			logging.error("Lost communication with receiver ({0})".format(e))
			if not getLockState(): lock()
			_thread.interrupt_main() # Sends SIGINT to main thread

	def toggleListen(self, caller):
		if self.enabled.get_active():
			self.indicator.set_icon_full("lock.svg", "Locking enabled.")
			logging.info("Enabled.")
		else:
			self.indicator.set_icon_full("unlock.svg", "Locking disabled.")
			logging.info("Disabled.")

	def about(self, caller): webbrowser.open(self.ABOUT_URL, new=2, autoraise=True)

	def quit(self, caller):
		logging.info("Goodbye :)")
		Gtk.main_quit()
		time.sleep(1) # Give time for evdev to close device before Python dies

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Wireless PC Lock - Copyright (C) 2020 Zack Didcott")
	parser.add_argument('-d', '--device', type=str, default="HID 13b7:7417", help="specify a device name (default: HID 13b7:7417)")
	parser.add_argument('-t', '--timeout', type=int, default=5, help="timeout before locking, in seconds; should be longer than the interval between communications (default: 5)")
	parser.add_argument('-l', '--log', type=str, default=None, help="output log into a file")
	group = parser.add_mutually_exclusive_group()
	group.add_argument('-q', '--quiet', action='store_const', const=-1, default=0, dest='verbosity', help="only display errors")
	group.add_argument('-v', '--verbose', action='store_const', const=1, default=0, dest='verbosity', help="display debugging information (default: INFO)") # See also: action='count'

	args = parser.parse_args()
	
	## Logging ##
	loglevel = 20 - (args.verbosity * 10)
	logging.basicConfig(
		level=loglevel, # Possible values: CRITICAL = 50, ERROR = 40, WARNING = 30, INFO = 20, DEBUG = 10
		filename=args.log,
		format='%(asctime)s | [%(levelname)s] %(message)s',
		datefmt='%H:%M:%S'
	)
	
	logging.info(parser.description)
	logging.debug("== Configuration ==")
	for arg, value in sorted(vars(args).items()):
		logging.debug("{0}: {1}".format(arg.title(), value))
	logging.debug("===================")
	
	app=WPCL(args)
	try: Gtk.main()
	except KeyboardInterrupt: sys.exit(1)
