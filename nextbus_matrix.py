#!/usr/bin/env python

"""
NextBus scrolling marquee display for Adafruit Spectro (64x32).
"""

import math
import time
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
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
MIN_TIME = 2        # Drop predictions below this threshold (minutes)
SHORT_TIME = 6      # Times greater than this are displayed in MID_TIME_COLOR
MID_TIME = 12       # Times greater than this are displayed LONG_TIME_COLOR

ROUTE_COLOR = (255, 255, 255)   # Color for route labels (usu. numbers)
DESC_COLOR = (110, 110, 110)    # " for route direction/description
LONG_TIME_COLOR = (0, 255, 0)   # Ample arrival time = green
MID_TIME_COLOR = (255, 255, 0)  # Medium arrival time = yellow
SHORT_TIME_COLOR = (255, 0, 0)  # Short arrival time = red
MINUTES_COLOR = (110, 110, 110) # Commans and 'minutes' labels
NO_TIMES_COLOR = (0, 0, 255)    # No predictions = blue

# pylint: disable=bad-option-value, useless-object-inheritance, too-few-public-methods


class Tile(object):
    """Staggered rectangles that scroll across the matrix. Tiles
       are NOT permanently tied to a prediction, the predictions
       are reassigned to new tiles as they slip off the left side."""
    def __init__(self, x_pos, y_pos, predict):
        self.x_pos = x_pos     # Initial X position
        self.y_pos = y_pos     # Y position (does not change)
        self.predict = predict # Initial corresponding Predict object

    def draw(self, parent):
        """Draw tile at current position on screen. Parent object is
           passed in so we have access to its draw and font objects."""
        # Make local copies of position variables we
        # can alter without corrupting the originals
        x_pos = math.floor(self.x_pos)  # Always round X DOWN
        y_pos = self.y_pos + parent.font_y_offset

        label = self.predict.data[1] + ' ' # Route number or code
        parent.draw.text((x_pos, y_pos), label, font=parent.font,
                         fill=ROUTE_COLOR)
        x_pos += parent.font.getsize(label)[0]

        label = self.predict.data[3]       # Route direction/desc
        parent.draw.text((x_pos, y_pos), label, font=parent.font,
                         fill=DESC_COLOR)

        x_pos = math.floor(self.x_pos)     # Reset X position to start
        y_pos += 16                        # Advance Y by 1 line

        if self.predict.predictions == []: # No predictions to display
            parent.draw.text((x_pos, y_pos), 'No Predictions',
                             font=parent.font, fill=NO_TIMES_COLOR)
        else:
            is_first_shown = True
            count = 0 # DO NOT use enumerate; increments only in some cases
            for prediction in self.predict.predictions:
                seconds = prediction - (time.time() -
                                        self.predict.last_query_time)
                minutes = int(seconds / 60)
                if minutes <= MIN_TIME:
                    continue  # Skip prediction, count is NOT incremented
                elif minutes <= SHORT_TIME:
                    fill = SHORT_TIME_COLOR
                elif minutes <= MID_TIME:
                    fill = MID_TIME_COLOR
                else:
                    fill = LONG_TIME_COLOR
                if is_first_shown:
                    is_first_shown = False
                else:
                    label = ', '
                    # The comma between times needs to be drawn in a
                    # goofball position so it's not cropped off bottom.
                    parent.draw.text((x_pos + 1, y_pos - 4), label,
                                     font=parent.font, fill=MINUTES_COLOR)
                    x_pos += parent.font.getsize(label)[0]
                label = str(minutes)
                parent.draw.text((x_pos, y_pos), label, font=parent.font,
                                 fill=fill)
                x_pos += parent.font.getsize(label)[0]
                count += 1
                if count >= MAX_PREDICTIONS:
                    break  # Limit number of predictions shown
            if count > 0:
                parent.draw.text((x_pos, y_pos), ' minutes',
                                 font=parent.font, fill=MINUTES_COLOR)

class NextBus(SpectroBase):
    """NextBus scrolling marquee display for Adafruit Spectro."""

    def __init__(self, *args, **kwargs):
        super(NextBus, self).__init__(*args, **kwargs)
        self.draw = None
        self.font = None
        self.font_y_offset = -3  # Text offset so descenders aren't cropped
        self.prev_time = time.time()

    def run(self):

        # Create offscreen buffer for graphics
        double_buffer = self.matrix.CreateFrameCanvas()

        # Create PIL image. Image object is 2X the matrix resolution
        # to provide nicer downsampling -- scrolling text looks better.
        image = Image.new(
            "RGB", (self.matrix.width * 2, self.matrix.height * 2))
        self.draw = ImageDraw.Draw(image)
        self.font = ImageFont.truetype("fonts/FreeSansOblique.ttf", 18)

        # Populate a list of Predict objects (from nextbus_predict.py)
        # from STOPS[]. While at it, also determine the widest tile width --
        # the labels accompanying each prediction. As currently written,
        # they're all the same width, whatever maximum we figure here.
        tile_width = self.font.getsize(
            '88' *  MAX_PREDICTIONS      + # 2 digits for minutes
            ', ' * (MAX_PREDICTIONS - 1) + # comma+space between times
            ' minutes')[0]                 # 1 space + 'minutes' at end
        tile_width = max(tile_width, self.font.getsize('No Predictions')[0])
        predict_list = []
        for stop in STOPS:
            predict_list.append(Predict(stop))
            tile_width = max(tile_width,
                             self.font.getsize(stop[1] + ' ' + stop[3])[0])
        tile_width += 20 # Allow extra horizontal space between tiles

        # Allocate list of tile objects, enough to cover matrix w/scrolling
        tile_list = []
        if tile_width >= image.size[0]:
            tiles_across = 2
        else:
            tiles_across = int(math.ceil(image.size[0] / tile_width)) + 1
        next_prediction = 0  # Index of predict_list item to attach to tile
        for x_pos in range(tiles_across):
            for y_pos in range(int(image.size[1] / 32)):
                tile_list.append(
                    Tile(int(x_pos * tile_width + y_pos * tile_width / 2) & ~1,
                         y_pos * 32, predict_list[next_prediction]))
                next_prediction += 1
                if next_prediction >= len(predict_list):
                    next_prediction = 0

        while True:

            # Clear background
            self.draw.rectangle((0, 0, image.size[0] - 1, image.size[1] - 1),
                                fill=0)

            # Determine distance tiles will be moved this frame
            current_time = time.time()
            relative_pos = tile_width / 3.0 * (current_time - self.prev_time)
            self.prev_time = current_time

            # Move and draw tiles
            for tile in tile_list:
                tile.x_pos -= relative_pos
                # If tile has moved off the left edge, move it right
                # and assign it the next prediction in predict_list[]
                if tile.x_pos <= -tile_width:
                    tile.x_pos += tile_width * tiles_across
                    tile.predict = predict_list[next_prediction]
                    next_prediction += 1
                    if next_prediction >= len(predict_list):
                        next_prediction = 0
                if tile.x_pos < image.size[0]: # Draw tile if onscreen
                    tile.draw(self)

            # Scale image 1:2, bilinear interpolation for smoothiness
            # Copy scaled PIL image to matrix buffer, swap buffers each frame
            double_buffer.SetImage(image.resize(
                (self.matrix.width, self.matrix.height),
                resample=Image.BILINEAR))
            double_buffer = self.matrix.SwapOnVSync(double_buffer)

if __name__ == "__main__":
    MY_APP = NextBus()  # Instantiate class, calls __init__() above
    MY_APP.process()    # SpectroBase startup, calls run() above
