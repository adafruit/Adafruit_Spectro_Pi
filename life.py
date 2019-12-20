#!/usr/bin/env python

"""
Conway's Game of Life for Adafruit Spectro.
"""

# Gets code to pass both pylint & pylint3:
# pylint: disable=superfluous-parens, unused-variable, too-many-locals

from copy import deepcopy
from math import sin, pi
from random import randrange
from time import time
from spectrobase import SpectroBase

class Life(SpectroBase):
    """Conway's Game of Life for Adafruit Spectro."""

    def __init__(self, *args, **kwargs):
        super(Life, self).__init__(*args, **kwargs)
        self.canvas = None   # LED drawing canvas is alloc'd in run()
        self.grid_prior = [] # Grid state from prior iteration
        self.grid_now = []   # Current grid state
        self.grid_next = []  # New grid state being computed
        self.repetitions = 0 # Count of prior-matches-next iterations

    def reset(self):
        """Allocate/clear grid state, randomly set ~25% of pixels"""
        # 'prior' grid is allocated all 0's
        self.grid_prior = [[0 for col in range(self.matrix.width)]
                           for row in range(self.matrix.height)]
        # 'next' grid copies size/state (all 0's) from 'prior':
        self.grid_next = deepcopy(self.grid_prior)
        # 'now' grid initially copies size/state from 'prior'...
        self.grid_now = deepcopy(self.grid_prior)
        # ...then set ~25% of pixels randomly (some may overlap, is OK):
        for count in range(self.matrix.width * self.matrix.height / 4):
            self.grid_now[randrange(self.matrix.height)][
                randrange(self.matrix.width)] = 1
        self.repetitions = 0  # Reset repetition counter

    def step(self):
        """Run one iteration of Conway's Game of Life, using self.grid_now
           as present playfield state, and self.grid_next as the destination
           next state; don't read/write in same buffer!"""
        self.canvas.Clear()  # Clear LED matrix
        angle = -time()      # RGB color is a time-constant function...
        red = (sin(angle) + 1.0) * 127.5
        green = (sin(angle + pi * 2 / 3) + 1.0) * 127.5
        blue = (sin(angle + pi * 4 / 3) + 1.0) * 127.5
        # Use references to individual rows of grid_now and grid_next,
        # avoids a number of MOD operations and 2D array accesses.
        row_current = self.grid_now[self.matrix.height - 1]
        row_next = self.grid_now[0]
        for row in range(self.matrix.height):
            row_prior = row_current
            row_current = row_next
            row_next = self.grid_now[(row + 1) % self.matrix.height]
            dest = self.grid_next[row]  # Destination row
            col_prior = self.matrix.width - 1
            for col in range(self.matrix.width):
                col_next = (col + 1) % self.matrix.width
                center = row_current[col]     # Center pixel
                neighbors = (                 # 8 neighboring pixels:
                    row_prior[col_prior] +    # (-1,-1)
                    row_prior[col] +          # ( 0,-1)
                    row_prior[col_next] +     # (+1,-1)
                    row_current[col_prior] +  # (-1, 0)
                    row_current[col_next] +   # (+1, 0)
                    row_next[col_prior] +     # (-1,+1)
                    row_next[col] +           # ( 0,+1)
                    row_next[col_next])       # (+1,+1)
                # Apply Life rules...
                if center and not (2 <= neighbors <= 3):
                    # Clear center pixel if set and <2 or >3 neighbors set
                    dest[col] = 0
                elif not center and neighbors == 3:
                    # Set center pixel if clear and 3 neighbors set
                    dest[col] = 1
                else:
                    # No change to pixel state
                    dest[col] = row_current[col]
                # Plot set pixels in the canvas
                if dest[col]:
                    self.canvas.SetPixel(col, row, red, green, blue)
                col_prior = col

    def run(self):
        # Create offscreen buffer for graphics
        self.canvas = self.matrix.CreateFrameCanvas()

        self.reset()

        while True:
            self.step()  # Run one iteration of life
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
            # If prior frame and next frame (2 frames apart) match,
            # it's probably stabilized on blocks and blinkers.
            if self.grid_next == self.grid_prior:
                # Keep running for a bit, but eventually start over
                self.repetitions += 1
                if self.repetitions >= 250:
                    self.reset()
                    continue
            else:
                self.repetitions = 0
            # Shuffle prior, present and next grids down by one.
            self.grid_prior, self.grid_now, self.grid_next = \
                self.grid_now, self.grid_next, self.grid_prior

if __name__ == "__main__":
    MY_APP = Life()  # Instantiate class, calls __init__() above
    MY_APP.process()   # SpectroBase startup, calls run() above
