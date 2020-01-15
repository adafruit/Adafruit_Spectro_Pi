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
    ("ip_address.py", False),
    ("cpu_load.py", False),
    ("bargraph.py", False),
    ("life.py", False),
    ("gifplay.py", False),
    ("audio.py", False),
    ("accel.py", False),
    ("idle.py", True)) # Nonsense idle script to test fb2matrix.py
# Python version to use with any .py scripts in above list, in case
# version 2 or 3 needs to be forced:
PYTHON = "python3"
# Name of framebuffer-to-matrix script:
FB_TO_MATRIX = "fb2matrix.py"
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
        self.timeout = 15.0  # First-program timeout (then advances modes)
        self.time_start = time.time()
        self.gpio = 25
        self.parser = argparse.ArgumentParser()
        self.args = None
        self.parser.add_argument(
            "-g", "--gpio", action="store", help="GPIO # for mode selector "
            "button (to GND). Default: " + str(self.gpio), default=self.gpio,
            type=int)

    def run_one(self):
        """Monitor last-launched subprocess until either it exits,
           the mode-change button is pressed or the subprocess timeout
           has elapsed. Also check for extended button hold and halt
           system if necessary."""
        while True:
            self.process[0].poll() # Sets returncode if process exited
            if(self.process[0].returncode or  # Signal or script error OR
               gpio.input(self.gpio) == 0 or  # Button press OR
               (self.timeout > 0 and          # Timeout
                time.time() - self.time_start > self.timeout)):
                time_pressed = time.time()
                # Try killing process(es), assuming it hasn't choked
                # on its own due to a signal or Python script error.
                for process in self.process:
                    try:
                        process.terminate()
                        process.wait()
                        # process.wait() seems a little flaky about
                        # this, hence the extra while and sleep:
                        while process.returncode is None:
                            time.sleep(0.25)
                    except OSError:
                        pass  # Process already exited (signal or error)
                time.sleep(0.1) # Extra button debounce a little
                while gpio.input(self.gpio) == 0: # Wait for button release
                    if time.time() - time_pressed >= 3: # Held a few sec?
                        os.system("shutdown -h now")    # Halt system
                        while True:                     # Wait for it
                            pass
                break
            time.sleep(0.1)

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

        while True:  # Cycle between programs indefinitely

            # Launch new process (from PROGRAMS list, based on self.mode).
            # Run as Python script or standalone program, passing FLAGS:
            if PROGRAMS[self.mode][0].endswith(".py"):
                self.process.append(
                    subprocess.Popen([PYTHON, PROGRAMS[self.mode][0]] + FLAGS))
            else:
                self.process.append(
                    subprocess.Popen([PROGRAMS[self.mode][0]] + FLAGS))
            # Optionally launch framebuffer-to-matrix util concurrently
            if PROGRAMS[self.mode][1] is True:
                self.process.append(
                    subprocess.Popen([PYTHON, FB_TO_MATRIX] + FLAGS))

            self.run_one()  # Until button press, timeout, etc.

            self.mode += 1                 # Advance to next mode
            if self.mode >= len(PROGRAMS): # Wrap around to start
                self.mode = 0
            self.timeout = -1  # Only do timeout case once, at startup
            self.process = []

if __name__ == "__main__":
    SELECTOR = Selector()
    SELECTOR.run()
