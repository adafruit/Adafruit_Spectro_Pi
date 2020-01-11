#!/usr/bin/env python

"""
Accelerometer-based "LED sand" (or rain or whatever) demo for Adafruit
Spectro. Requires LIS3DH accelerometer on I2C pins (and enable I2C).
If accelerometer not detected, program will exit.

Install Blinka and LIS3DH support with:
sudo pip3 install adafruit-circuitpython-lis3dh
sudo pip3 install adafruit-circuitpython-busdevice
"""

# pylint: disable=import-error

import board
import busio
import adafruit_lis3dh
from spectrobase import SpectroBase
from pixeldust import PixelDust

class AccelSand(SpectroBase):
    """LIS3DH accelerometer-based "LED sand" for Adafruit Spectro."""

    def __init__(self, *args, **kwargs):
        super(AccelSand, self).__init__(*args, **kwargs)

        self.parser.add_argument(
            "-e", "--elasticity", help="Elasticity (bounce) 0.0 to 1.0",
            default=0.1)
        self.parser.add_argument(
            "-g", "--grains", help="Number of grains")

    def run(self):

        # Parse and clip optional arguments (or use defaults)
        if self.args.grains is not None:
            num_grains = min(abs(int(self.args.grains)),
                             self.matrix.width * self.matrix.height)
        else:
            num_grains = self.matrix.width * self.matrix.height // 6

        if self.args.elasticity is not None:
            elasticity = min(abs(float(self.args.elasticity)), 1.0)
        else:
            elasticity = 0.1

        i2c = busio.I2C(board.SCL, board.SDA)
        accelerometer = adafruit_lis3dh.LIS3DH_I2C(i2c, address=0x18)
        accelerometer.range = adafruit_lis3dh.RANGE_4_G
        acceleration = (0.0, 9.8, 0.0)

        # Create offscreen buffer for graphics
        double_buffer = self.matrix.CreateFrameCanvas()

        # Create pixeldust object
        dust = PixelDust(self.matrix.width, self.matrix.height, elasticity)

        # Initialize with random sand
        dust.randomize(num_grains)

        while True:
            try:
                acceleration = accelerometer.acceleration
            except OSError:
                # Keep last value
                pass
            dust.iterate(acceleration)

            # Render sand
            double_buffer.Clear()
            for i in range(num_grains):
                position_x, position_y = dust.get_position(i)
                double_buffer.SetPixel(position_x, position_y, 0, 150, 250)

            double_buffer = self.matrix.SwapOnVSync(double_buffer)

if __name__ == "__main__":
    MY_APP = AccelSand()  # Instantiate class, calls __init__() above
    MY_APP.process()      # SpectroBase startup, calls run() above
