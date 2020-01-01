#!/usr/bin/env python

"""
Simple IP address display for Spectro.
Displays hostname and numeric IP address.
"""

import socket
import time
from PIL import Image, ImageDraw, ImageFont
from spectrobase import SpectroBase

class IPShow(SpectroBase):
    """Simple IP address display for Spectro. Shows hostname & IP address."""

    def __init__(self, *args, **kwargs):
        super(IPShow, self).__init__(*args, **kwargs)
        self.draw = None
        self.font = None
        self.text_size = []
        self.double_string = ""

    def run(self):
        # Create offscreen buffer for graphics
        double_buffer = self.matrix.CreateFrameCanvas()

        # Create PIL image. Image object is 2X the matrix resolution
        # to provide nicer downsampling -- scrolling text looks better.
        image = Image.new(
            "RGB", (self.matrix.width * 2, self.matrix.height * 2))
        self.draw = ImageDraw.Draw(image)
        # Oblique fonts look nicer with horizontal scrolling;
        # it avoids flicker from vertical strokes.
        if self.matrix.height < 32:
            self.font = ImageFont.truetype(
                "fonts/FreeSansOblique.ttf", 24)
        else:
            self.font = ImageFont.truetype(
                "fonts/FreeSansOblique.ttf", 28)

        host_name = socket.gethostname() + ".local"
        ip_address = socket.gethostbyname(host_name)
        # Concatenate host name and IP (and some spaces) into one
        # string so we know how much to scroll across screen...
        single_string = host_name + "   " + ip_address + "   "
        self.text_size = self.font.getsize(single_string)
        # Maintain a doubled-up copy so we just have to draw
        # one instance as the string scrolls off the left side.
        self.double_string = single_string * 2

        while True:
            # Clear image
            self.draw.rectangle((0, 0, image.width-1, image.height-1), fill=0)

            # Call screen-drawing function as appropriate to matrix size:
            if self.matrix.height < 32:
                self.draw_small()
            else:
                self.draw_large()

            # Scale image 1:2, bilinear interpolation for smoothiness
            scaled = image.resize((self.matrix.width, self.matrix.height),
                                  resample=Image.BILINEAR)
            # Copy scaled PIL image to matrix buffer, swap buffers each frame
            double_buffer.SetImage(scaled)
            double_buffer = self.matrix.SwapOnVSync(double_buffer)

    def draw_small(self):
        """Draw hostname/address on a single line for small matrices."""
        # Text position is based on current time, NOT a pixel increment,
        # because the frame-to-frame interval is not consistent, may vary
        # due to garbage collections or other goings on.  Text may 'jump'
        # on some frames but the position is linear-time-constant, always
        # takes 6 seconds to cross display from start to finish.
        relative_time = (time.time() / 6.0) % 1.0
        position = (-self.text_size[0] * relative_time,
                    self.matrix.height - self.text_size[1] // 2)
        self.draw.text(position, self.double_string, font=self.font)

    def draw_large(self):
        """Draw hostname/address on two lines for larger matrices."""
        # Same principle as above, but there's two lines. They display
        # the exact same information, just the scrolling speed varies...
        # one for fast readers, one more leisurely...
        relative_time = (time.time() / 5.0) % 1.0
        position = (-self.text_size[0] * relative_time,
                    self.matrix.height // 2 - self.text_size[1] // 2)
        self.draw.text(position, self.double_string, font=self.font)
        relative_time = (time.time() / 10.0) % 1.0
        position = (-self.text_size[0] * relative_time,
                    (self.matrix.height * 3 - self.text_size[1]) // 2)
        self.draw.text(position, self.double_string, font=self.font)

if __name__ == "__main__":
    MY_APP = IPShow()  # Instantiate class, calls __init__() above
    MY_APP.process()   # SpectroBase startup, calls run() above
