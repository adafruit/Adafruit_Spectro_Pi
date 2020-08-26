#!/usr/bin/env python

"""Simple CPU load & temperature display for Spectro."""

# Gets code to pass both pylint & pylint3:
# pylint: disable=c-extension-no-member

import time
import psutil
from rgbmatrix import graphics
from spectrobase import SpectroBase

# Fonts used for 32x16 and 64x32 matrices, respectively.
# This requires that rpi-rgb-led-matrix is in an adjacent directory.
SMALL_FONT = "../rpi-rgb-led-matrix/fonts/tom-thumb.bdf"
LARGE_FONT = "../rpi-rgb-led-matrix/fonts/5x7.bdf"
IMPERIAL = False  # Set this True if you want degrees Fahrenheit

class CPULoad(SpectroBase):
    """Simple CPU load & temperature display for Spectro."""

    def run(self):

        # Create offscreen buffer for graphics
        double_buffer = self.matrix.CreateFrameCanvas()

        text_color = graphics.Color(255, 255, 255)
        font = graphics.Font()
        if self.matrix.width < 64:
            font.LoadFont(SMALL_FONT)
            load_format = "LOAD:{:5.1f}"   # Small screen = packed tight,
            temp_format = "TEMP:{:5.1f}"   # no percent or degree stuff.
            symbol = ""
        else:
            font.LoadFont(LARGE_FONT)
            load_format = "LOAD: {:5.1f}%" # A little more space
            temp_format = "TEMP: {:5.1f}"
            if IMPERIAL:
                symbol = u"\N{DEGREE SIGN}" + "F"
            else:
                symbol = u"\N{DEGREE SIGN}" + "C"

        psutil.cpu_percent(percpu=False)  # Read, discard initial CPU load

        while True:
            double_buffer.Clear()  # Clear image

            # Poll CPU load and temperature
            cpu_load = psutil.cpu_percent(percpu=False)
            temps = psutil.sensors_temperatures(fahrenheit=IMPERIAL)
            try:
                thermal = temps.get("cpu_thermal") # New hotness
                temperature = thermal[0].current
            except TypeError:
                thermal = temps.get("cpu-thermal") # Oldschool
                temperature = thermal[0].current

            # Format load and temperature
            load_string = load_format.format(cpu_load)
            temp_string = temp_format.format(temperature) + symbol

            # Draw load and temperature to the matrix
            graphics.DrawText(double_buffer, font, 0,
                              font.baseline, text_color, load_string)
            graphics.DrawText(double_buffer, font, 0,
                              font.height + font.baseline, text_color,
                              temp_string)

            # Swap buffers each frame
            double_buffer = self.matrix.SwapOnVSync(double_buffer)

            time.sleep(0.5)

if __name__ == "__main__":
    MY_APP = CPULoad()  # Instantiate class, calls __init__() above
    MY_APP.process()    # SpectroBase startup, calls run() above
