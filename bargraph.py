#!/usr/bin/env python

"""
Bargraph clock for Spectro.
"""

# Gets code to pass both pylint & pylint3:
# pylint: disable=superfluous-parens

import time
from PIL import Image, ImageDraw
from spectrobase import SpectroBase

TWELVE_HOUR = True
BACKGROUND_COLOR = (0, 0, 0)
HOUR_FOREGROUND = (255, 0, 0)
MINUTE_FOREGROUND = (255, 255, 0)
SECOND_FOREGROUND = (0, 255, 0)
HOUR_BACKGROUND = tuple(i//8 for i in HOUR_FOREGROUND)
MINUTE_BACKGROUND = tuple(i//8 for i in MINUTE_FOREGROUND)
SECOND_BACKGROUND = tuple(i//8 for i in SECOND_FOREGROUND)

class BargraphClock(SpectroBase):
    """Bargraph clock for Spectro."""

    def __init__(self, *args, **kwargs):
        super(BargraphClock, self).__init__(*args, **kwargs)

        # Create PIL image
        self.image = Image.new("RGB", (64, 32))

        digits = Image.open('graphics/bargraph-digits.png')
        self.digit = []
        for i in range(10):
            self.digit.append(digits.crop((i*6, 0, i*6+6, 10)))

    def draw_digit(self, n, x, y):
        self.image.paste(self.digit[n], (x, y, x+6, y+10), mask=self.digit[n])

    def run(self):

        # Create offscreen buffer for graphics
        double_buffer = self.matrix.CreateFrameCanvas()

        draw = ImageDraw.Draw(self.image)

        while True:
            # Erase background
            draw.rectangle((0, 0, 64, 32), fill=BACKGROUND_COLOR)

            localtime = time.localtime(time.time())
            if TWELVE_HOUR == True:
                hour = localtime.tm_hour % 12
                width = 44 * (hour * 60 + localtime.tm_min) // 719
                if hour == 0:
                    hour = 12
            else:
                hour = localtime.tm_hour
                width = 44 * (hour * 60 + localtime.tm_min) // 1439

            self.draw_digit(hour // 10, 2, 2)
            self.draw_digit(hour % 10, 10, 2)
            self.draw_digit(localtime.tm_min // 10, 2, 14)
            self.draw_digit(localtime.tm_min % 10, 10, 14)

            if width > 0:
                draw.rectangle((18, 2, 17 + width, 11), fill=HOUR_FOREGROUND)
            if width < 44:
                draw.rectangle((18 + width, 2, 61, 11), fill=HOUR_BACKGROUND)

            width = 44 * localtime.tm_min // 59
            if width > 0:
                draw.rectangle((18, 14, 17 + width, 23), fill=MINUTE_FOREGROUND)
            if width < 44:
                draw.rectangle((18 + width, 14, 61, 23), fill=MINUTE_BACKGROUND)

            width = localtime.tm_sec
            draw.rectangle((2, 26, 2 + width, 29), fill=SECOND_FOREGROUND)
            if width < 59:
                draw.rectangle((3 + width, 26, 61, 29), fill=SECOND_BACKGROUND)

            # Copy PIL image to matrix buffer, swap buffers each frame
            if self.matrix.height >= 32:
                double_buffer.SetImage(self.image)
            else:
                double_buffer.SetImage(self.halve(self.image))
            double_buffer = self.matrix.SwapOnVSync(double_buffer)

if __name__ == "__main__":
    MY_APP = BargraphClock()  # Instantiate class, calls __init__() above
    MY_APP.process()        # SpectroBase startup, calls run() above
