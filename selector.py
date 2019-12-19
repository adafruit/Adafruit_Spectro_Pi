#!/usr/bin/env python

"""
Selector program for Adafruit Spectro. Cycles among various programs/scripts
using the side button.
"""

# Gets code to pass both pylint & pylint3:
# pylint: disable=bad-option-value, useless-object-inheritance, no-member

import os
import subprocess
import time
import argparse
try:
    import RPi.GPIO as gpio
except ImportError:
    exit("This library requires the RPi.GPIO module\n"
         "Install with: sudo pip install RPi.GPIO")

# List of programs to cycle through. First item is launched on startup,
# will run for 15 seconds before automatically advancing to the next.
# All subsequent advancements will only occur with a manual button press
# (even when cycling back to the first program). For each item, there is
# a program name (if ending in ".py", it will be run via the Python
# interpreter, else standalone program) and a True/False argument
# indicating whether the framebuffer-to-matrix utility should be run
# concurrently with that program/script.
PROGRAMS = (
    ("ipaddr.py", False),
    ("bargraph.py", False))
# Python version to use with any .py scripts in above list, in case
# version 2 or 3 needs to be forced:
PYTHON = "python"
# Name of framebuffer-to-matrix utility:
FB_TO_MATRIX = "rpi-fb-matrix"
# Command-line flags passed to above program/scripts and the
# framebuffer-to-matrix utility:
FLAGS = ["--led-cols=64", "--led-rows=32", "--led-slowdown-gpio=4"]
# Additional commands not used here, but you might find useful:
# FLAGS = ["--led-rgb-sequence=rbg", "--led-brightness=50"]

class Selector(object):
    """Selector program for Spectro. Cycles among various programs/scripts
       using the side button."""

    def __init__(self):
        self.mode = 0
        self.process = []
        self.timeout = 10.0  # First-program timeout (then advances modes)
        self.time_start = time.time()
        self.gpio = 25
        self.parser = argparse.ArgumentParser()
        self.args = None
        self.parser.add_argument(
            "-g", "--gpio", action="store", help="GPIO # for mode selector "
            "button (to GND). Default: " + str(self.gpio), default=self.gpio,
            type=int)

    def launch(self):
        """Exit currently-running Spectro program (if any), launch the
           next one."""
        # Terminate existing process (if any) and wait for it to finish...
        for process in self.process:
            process.terminate()
            process.wait()
            # process.wait() seems to be a little flaky about this,
            # hence the extra while and sleep that follow...
            while process.returncode is None:
                pass
        time.sleep(0.5)
        self.process = []

        # Launch new process (from PROGRAMS list, based on self.mode)
        # Launch framebuffer-to-matrix util concurrently, if needed:
        if PROGRAMS[self.mode][1] is True:
            self.process.append(
                subprocess.Popen([FB_TO_MATRIX] + FLAGS))
        # Launch Python script or standalone program, passing FLAGS:
        if PROGRAMS[self.mode][0].endswith(".py"):
            self.process.append(
                subprocess.Popen([PYTHON, PROGRAMS[self.mode][0]] + FLAGS))
        else:
            self.process.append(
                subprocess.Popen([PROGRAMS[self.mode][0]] + FLAGS))


    def run(self):
        """Main loop of Selector program."""

        # Handle script-specific command line argument(s):
        self.args = self.parser.parse_args()
        if self.args.gpio is not None:
            self.gpio = self.args.gpio

        # GPIO init
        gpio.setwarnings(False)
        gpio.setmode(gpio.BCM)
        gpio.setup(self.gpio, gpio.IN, pull_up_down=gpio.PUD_UP)

        self.launch() # Run initial Spectro process (shows IP address)

        while True:
            if(gpio.input(self.gpio) == 0 or
               (self.timeout > 0 and
                time.time() - self.time_start > self.timeout)):
                time_pressed = time.time()
                self.mode += 1                 # Advance to next mode
                if self.mode >= len(PROGRAMS): # Wrap around to start
                    self.mode = 0
                self.timeout = -1  # Only do timeout case once, at startup
                time.sleep(0.1)                # Extra button debounce
                while gpio.input(self.gpio) == 0: # Wait for button release
                    if time.time() - time_pressed >= 3: # Held for a few sec?
                        for process in self.process:
                            process.terminate()         # Terminate process(es)
                        os.system("shutdown -h now")    # Halt system
                        while True:                     # Wait for it
                            pass
                self.launch()      # End current prog, start next
            time.sleep(0.1)

if __name__ == "__main__":
    SELECTOR = Selector()
    SELECTOR.run()
