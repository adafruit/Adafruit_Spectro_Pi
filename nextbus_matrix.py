#!/usr/bin/env python

"""
NextBus scrolling marquee display for Adafruit Spectro (64x32).
"""

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import math
import os
import time
from nextbus_predict import Predict
from spectrobase import SpectroBase

# Configurable stuff ---------------------------------------------------------

# List of bus lines/stops to predict.  Use nextbus_routefinder.py to look
# up lines/stops for your location, copy & paste results here.  The 4th
# string on each line can then be edited for brevity if desired.
STOPS = [
    ('lametro', '79', '11086', 'Downtown LA'),
    ('lametro', '79', '2549', 'Arcadia Station'),
    ('lametro', '260', '11086', 'Altadena'),
    ('lametro', '260', '2549', 'Artesia Station')
]

MAX_PREDICTIONS = 3 # NextBus shows up to 5; limit to 3 for simpler display
MIN_TIME = 0        # Drop predictions below this threshold (minutes)
SHORT_TIME = 5      # Times greater than this are displayed in MID_TIME_COLOR
MID_TIME = 10       # Times greater than this are displayed LONG_TIME_COLOR

ROUTE_COLOR = (255, 255, 255)   # Color for route labels (usu. numbers)
DESC_COLOR = (110, 110, 110)    # " for route direction/description
LONG_TIME_COLOR = (0, 255, 0)   # Ample arrival time = green
MID_TIME_COLOR = (255, 255, 0)  # Medium arrival time = yellow
SHORT_TIME_COLOR = (255, 0, 0)  # Short arrival time = red
MINUTES_COLOR = (110, 110, 110) # Commans and 'minutes' labels
NO_TIMES_COLOR = (0, 0, 255)    # No predictions = blue

class Tile(object):
    def __init__(self, x_offset, y_offset, predict):
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.predict = predict  # Corresponding Predict object

    def draw(self, x_pos, y_pos, parent):
        label = self.predict.data[1] + ' ' # Route number or code
        parent.draw.text((x_pos, y_pos + parent.font_y_offset), label,
                         font=parent.font, fill=ROUTE_COLOR)

        label = self.predict.data[3]       # Route direction/desc
        parent.draw.text((x_pos + parent.font.getsize(label)[0],
                  y_pos + parent.font_y_offset), label, font=parent.font,
                  fill=DESC_COLOR)
        if self.predict.predictions == []: # No predictions to display
            parent.draw.text((x_pos, y_pos + parent.font_y_offset + 8),
                'No Predictions', font=parent.font, fill=NO_TIMES_COLOR)
        else:
            is_first_shown = True
            count = 0
            for p in self.predict.predictions:
                t = p - (time.time() - self.predict.last_query_time)
                m = int(t / 60)
                if m <= MIN_TIME:
                    continue
                elif m <= SHORT_TIME:
                    fill = SHORT_TIME_COLOR
                elif m <= MID_TIME:
                    fill = MID_TIME_COLOR
                else:
                    fill = LONG_TIME_COLOR
                if is_first_shown:
                    is_first_shown = False
                else:
                    label = ', '
                    # The comma between times needs to
                    # be drawn in a goofball position
                    # so it's not cropped off bottom.
                    parent.draw.text((x_pos + 1,
                        y_pos + parent.font_y_offset + 8 - 2),
                        label, font=parent.font, fill=MINUTES_COLOR)
                    x_pos += parent.font.getsize(label)[0]
                label = str(m)
                parent.draw.text((x_pos, y_pos + parent.font_y_offset + 8),
                  label, font=parent.font, fill=fill)
                x_pos += parent.font.getsize(label)[0]
                count += 1
                if count >= MAX_PREDICTIONS:
                    break
            if count > 0:
                parent.draw.text((x_pos, y_pos + parent.font_y_offset + 8),
                  ' minutes', font=parent.font, fill=MINUTES_COLOR)

class NextBus(SpectroBase):
    """NextBus scrolling marquee display for Adafruit Spectro (64x32)."""

    def __init__(self, *args, **kwargs):
        super(NextBus, self).__init__(*args, **kwargs)
        self.draw = None
        self.font = None
        self.font_y_offset = -2  # Text offset so descenders aren't cropped

    def run(self):

        # Create offscreen buffer for graphics
        double_buffer = self.matrix.CreateFrameCanvas()

        # Create PIL image. Image object is 2X the matrix resolution
        # to provide nicer downsampling -- scrolling text looks better.
        image = Image.new(
            "RGB", (self.matrix.width * 2, self.matrix.height * 2))
        self.draw = ImageDraw.Draw(image)
        self.font = ImageFont.truetype(
            "fonts/FreeSansOblique.ttf", 28)

        # Populate a list of Predict objects (from nextbus_predict.py)
        # from STOPS[]. While at it, also determine the widest tile width --
        # the labels accompanying each prediction. As currently written,
        # they're all the same width, whatever maximum we figure here.
        tile_width = self.font.getsize(
          '88' *  MAX_PREDICTIONS      +          # 2 digits for minutes
          ', ' * (MAX_PREDICTIONS - 1) +          # comma+space between times
          ' minutes')[0]                          # 1 space + 'minutes' at end
        width = self.font.getsize('No Predictions')[0] # Label when no times
        tile_width = max(width, tile_width)
        predict_list = []
        for s in STOPS:
            predict_list.append(Predict(s))
            width = self.font.getsize(s[1] + ' ' + s[3])[0] # Route label
            tile_width = max(width, tile_width)
        tile_width += 6 # Allow extra space between tiles

        # Allocate list of tile objects, enough to cover matrix while scrolling
        self.tile_list = []
        if tile_width >= image.size[0]:
            tiles_across = 2
        else:
            tiles_across = int(math.ceil(image.size[0] / tile_width)) + 1

        nextPrediction = 0  # Index of predictList item to attach to tile
        for x in xrange(tiles_across):
            for y in xrange(0, 2):
                self.tile_list.append(Tile(x * tile_width +
                    y * tile_width / 2, 
                    y * 17, predict_list[nextPrediction]))
                nextPrediction += 1
                if nextPrediction >= len(predict_list):
                    nextPrediction = 0

        while True:

            # Clear background
            self.draw.rectangle((0, 0, image.size[0] - 1, image.size[1] - 1),
                           fill=0)

            relative_time = (time.time() / 6.0) % 1.0
# tiles_across
            relative_pos = -tile_width * relative_time

            for t in self.tile_list:
                tile_pos = relative_pos + t.x_offset
# if off left side, try advancing off right and re-check
                x_pos = t.x_offset
                y_pos = t.y_offset

                if t.x_offset < image.size[0]: # Draw tile if onscreen
                    t.draw(x_pos, y_pos, self)

# CHANGE ALL THIS
# Oh! This reassigns prediction-to-tile mapping
# Well this gets interesting.
#                t.x -= 1               # Move left 1 pixel
#                if(t.x <= -tile_width): # Off left edge?
#                    t.x += tile_width * tiles_across     # Move off right &
#                    t.p  = predictList[nextPrediction] # assign prediction
#                    nextPrediction += 1                # Cycle predictions
#                    if nextPrediction >= len(predictList):
#                        nextPrediction = 0

            # Scale image 1:2, bilinear interpolation for smoothiness
            scaled = image.resize((self.matrix.width, self.matrix.height),
                                  resample=Image.BILINEAR)
            # Copy scaled PIL image to matrix buffer, swap buffers each frame
            double_buffer.SetImage(scaled)
            double_buffer = self.matrix.SwapOnVSync(double_buffer)

if __name__ == "__main__":
    MY_APP = NextBus()  # Instantiate class, calls __init__() above
    MY_APP.process()    # SpectroBase startup, calls run() above
