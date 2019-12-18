#!/usr/bin/env python

"""Simple IP address display for Spectro."""

# Gets code to pass both pylint & pylint3:
# pylint: disable=superfluous-parens

import socket
import time
from PIL import Image, ImageDraw, ImageFont
from spectrobase import SpectroBase

class IPShow(SpectroBase):
    """Simple IP address display for Spectro."""

    def run(self):

        host_name = socket.gethostname() + ".local"
        ip_address = socket.gethostbyname(host_name)

        # Create offscreen buffer for graphics
        double_buffer = self.matrix.CreateFrameCanvas()

        # Create PIL image. Image object is 2X the matrix resolution
        # to provide nicer downsampling -- scrolling text looks better.
        image = Image.new(
            "RGB", (self.matrix.width * 2, self.matrix.height * 2))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(
            "fonts/FreeSansOblique.ttf", self.matrix.height)
        text_size = font.getsize(ip_address)  # Pixel dimensions of IP string
        y_position = (image.height - text_size[1]) / 2  # Center vertically

        while True:
            # Clear image
            draw.rectangle((0, 0, image.width-1, image.height-1), fill=0)

            # Text position is based on current time, NOT a pixel increment,
            # because the frame-to-frame interval is not consistent, may vary
            # due to garbage collections or other goings on.  Text may 'jump'
            # on some frames but the position is linear-time-constant, always
            # takes 4 seconds to cross display from start to finish.
            relative_time = time.time() / 4.0 % 1.0
            x_position = (
                image.size[0] - relative_time * (image.size[0] + text_size[0]))
            draw.text((x_position, y_position), ip_address, font=font)

            # Scale, copy PIL image to matrix buffer, swap buffers each frame
            double_buffer.SetImage(image.resize(
                (self.matrix.width, self.matrix.height),
                resample=Image.BILINEAR))
            double_buffer = self.matrix.SwapOnVSync(double_buffer)

if __name__ == "__main__":
    MY_APP = IPShow()  # Instantiate class, calls __init__() above
    MY_APP.process()   # SpectroBase startup, calls run() above
