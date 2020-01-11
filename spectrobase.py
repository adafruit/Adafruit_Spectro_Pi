#!/usr/bin/env python

"""
This file is adapted from the Python binding examples from hzeller's
rpi-rgb-led-matrix project: https://github.com/hzeller/rpi-rgb-led-matrix
It contains code common to several matrix-using Python scripts, such as
handling command-line settings. Some parts have been pared down from the
original (e.g. various print statements removed, no usleep), others
reformatted to appease pylint/pylint3.
"""

# Gets code to pass both pylint & pylint3:
# pylint: disable=bad-option-value, useless-object-inheritance, superfluous-parens, no-self-use, unused-argument

import sys
import signal
import argparse
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw

class SpectroBase(object):
    """A base class for Adafruit Spectro projects, adapted from the
       hzeller Python examples."""
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.args = None
        self.matrix = None

        self.parser.add_argument(
            "-r", "--led-rows", action="store", help="Display rows. "
            "16 for 16x32, 32 for 32x32. Default: 32", default=32, type=int)
        self.parser.add_argument(
            "--led-cols", action="store", help="Panel columns. Typically "
            "32 or 64. (Default: 32)", default=32, type=int)
        self.parser.add_argument(
            "-c", "--led-chain", action="store", help="Daisy-chained boards. "
            "Default: 1.", default=1, type=int)
        self.parser.add_argument(
            "-P", "--led-parallel", action="store", help="For Plus-models "
            "or RPi2: parallel chains. 1..3. Default: 1", default=1, type=int)
        self.parser.add_argument(
            "-p", "--led-pwm-bits", action="store", help="Bits used for PWM. "
            "Something between 1..11. Default: 11", default=11, type=int)
        self.parser.add_argument(
            "-b", "--led-brightness", action="store", help="Sets brightness "
            "level. Default: 100. Range: 1..100", default=100, type=int)
        self.parser.add_argument(
            "-m", "--led-gpio-mapping", help="Hardware Mapping: regular, "
            "adafruit-hat, adafruit-hat-pwm",
            choices=['regular', 'adafruit-hat', 'adafruit-hat-pwm'], type=str)
        self.parser.add_argument(
            "--led-scan-mode", action="store", help="Progressive or "
            "interlaced scan. 0 Progressive, 1 Interlaced (default)",
            default=1, choices=range(2), type=int)
        self.parser.add_argument(
            "--led-pwm-lsb-nanoseconds", action="store", help="Base "
            "time-unit for the on-time in the lowest significant bit in "
            "nanoseconds. Default: 130", default=130, type=int)
        self.parser.add_argument(
            "--led-show-refresh", action="store_true", help="Shows the "
            "current refresh rate of the LED panel")
        self.parser.add_argument(
            "--led-slowdown-gpio", action="store", help="Slow down writing "
            "to GPIO. Range: 0..4. Default: 1", default=1, type=int)
        self.parser.add_argument(
            "--led-no-hardware-pulse", action="store",
            help="Don't use hardware pin-pulse generation")
        self.parser.add_argument(
            "--led-rgb-sequence", action="store", help="Switch if your "
            "matrix has led colors swapped. Default: RGB",
            default="RGB", type=str)
        self.parser.add_argument(
            "--led-pixel-mapper", action="store", help="Apply pixel mappers. "
            "e.g \"Rotate:90\"", default="", type=str)
        self.parser.add_argument(
            "--led-row-addr-type", action="store", help="0 = default; "
            "1=AB-addressed panels;2=row direct",
            default=0, type=int, choices=[0, 1, 2])
        self.parser.add_argument(
            "--led-multiplexing", action="store", help="Multiplexing type: "
            "0=direct; 1=strip; 2=checker; 3=spiral; 4=ZStripe; "
            "5=ZnMirrorZStripe; 6=coreman; 7=Kaler2Scan; 8=ZStripeUneven "
            "(Default: 0)", default=0, type=int)

    def run(self):
        """Placeholder. Override this in subclass."""

    def signal_handler(self, signum, frame):
        """Signal handler calls just invokes exit() which clears matrix."""
        exit(0)

    def process(self):
        """Process command-line input and initiate the RGB matrix with
           those options before calling the subclass code."""
        self.args = self.parser.parse_args()

        options = RGBMatrixOptions()

        if self.args.led_gpio_mapping is not None:
            options.hardware_mapping = self.args.led_gpio_mapping
        options.rows = self.args.led_rows
        options.cols = self.args.led_cols
        options.chain_length = self.args.led_chain
        options.parallel = self.args.led_parallel
        options.row_address_type = self.args.led_row_addr_type
        options.multiplexing = self.args.led_multiplexing
        options.pwm_bits = self.args.led_pwm_bits
        options.brightness = self.args.led_brightness
        options.pwm_lsb_nanoseconds = self.args.led_pwm_lsb_nanoseconds
        options.led_rgb_sequence = self.args.led_rgb_sequence
        options.pixel_mapper_config = self.args.led_pixel_mapper
        if self.args.led_show_refresh:
            options.show_refresh_rate = 1

        if self.args.led_slowdown_gpio is not None:
            options.gpio_slowdown = self.args.led_slowdown_gpio
        if self.args.led_no_hardware_pulse:
            options.disable_hardware_pulsing = True

        # Don't drop root status; lets us maintain I2C access, etc.
        # For some reason this isn't working from command line.
        options.drop_privileges = False

        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

        self.matrix = RGBMatrix(options=options)

        try:
            self.run()
        except KeyboardInterrupt:
            sys.exit(0)

        return True

    def halve(self, image_in):
        """PIL's image.resize() with BILINEAR sampling doesn't quite produce
           the expected 2x2 pixel averaging when scaling an image exactly 1:2.
           This function handles it manually, returning an image half the size
           of the original with 2x2 averaging. Being all Python, it's not as
           fast as PIL, so not the best for quick animation. This is
           specifically for PIL images, NOT an RGBMatrix canvas."""
        width = image_in.size[0] / 2
        height = image_in.size[1] / 2
        image_out = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(image_out)
        for row in range(height):
            for col in range(width):
                pixel_0 = image_in.getpixel((col * 2, row * 2))
                pixel_1 = image_in.getpixel((col * 2 + 1, row * 2))
                pixel_2 = image_in.getpixel((col * 2, row * 2 + 1))
                pixel_3 = image_in.getpixel((col * 2 + 1, row * 2 + 1))
                draw.point((col, row), fill=(
                    (pixel_0[0] + pixel_1[0] + pixel_2[0] + pixel_3[0]) // 4,
                    (pixel_0[1] + pixel_1[1] + pixel_2[1] + pixel_3[1]) // 4,
                    (pixel_0[2] + pixel_1[2] + pixel_2[2] + pixel_3[2]) // 4))
        return image_out
