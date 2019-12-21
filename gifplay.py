#!/usr/bin/env python

"""
GIF player for Adafruit Spectro.
"""

import os
import glob
import time
from PIL import Image, ImageSequence
from spectrobase import SpectroBase

DEFAULT_GIF_PATH = "/boot/gifs"
LOOP_TIME = 10
FILTER = Image.LANCZOS  # Slower Pis might want BICUBIC or BILINEAR here

class GIFplayer(SpectroBase):
    """GIF player for Adafruit Spectro."""

    def __init__(self, *args, **kwargs):
        super(GIFplayer, self).__init__(*args, **kwargs)

        self.gif_path = DEFAULT_GIF_PATH
        self.matrix_size = None
        self.double_buffer = None
        self.frame_start_time = 0
        self.frame_duration = 0

        self.parser.add_argument(
            "-d", "--dir", help="Directory containing GIFs",
            default=DEFAULT_GIF_PATH)

    def loop_gif(self, image):
        """Play one image for LOOP_TIME seconds or one complete pass,
           whichever is longer."""
        file_start_time = time.time()

        # Determine how to size and center image on the matrix,
        # maintaining the aspect ratio (approximately, due to resolution).
        matrix_aspect = float(self.matrix.width) / float(self.matrix.height)
        image_aspect = float(image.width) / float(image.height)
        if matrix_aspect > image_aspect:
            # Letterbox horizontally (vertical bars left/right)
            scaled_size = (int(self.matrix.height * image_aspect + 0.5),
                           self.matrix.height)
        elif matrix_aspect < image_aspect:
            # Letterbox vertically (horizontal bars top/bottom)
            scaled_size = (self.matrix.width,
                           int(self.matrix.width / image_aspect + 0.5))
        else:
            # No letterbox, maybe just scale
            scaled_size = self.matrix_size
        position = ((self.matrix.width - scaled_size[0]) // 2,
                    (self.matrix.height - scaled_size[1]) // 2)
        resize = (image.size != scaled_size)
        if scaled_size != self.matrix_size:
            back_image = Image.new("RGB", self.matrix_size)
        else:
            back_image = None

        # Repeat until >= 10 seconds elapsed or 1 full pass through file
        while (time.time() - file_start_time) <= LOOP_TIME:
            # File playback is NOT cut off at 10 sec; all frames will
            # play as long as the file STARTED before the 10 sec cutoff.
            for frame in ImageSequence.Iterator(image):
                # Save frame duration, gets lost in the convert/resize
                next_duration = frame.info.get('duration', 100) / 1000.0
                if resize:
                    # Frame must be converted to RGB and resized each time,
                    # can't just do that operation once on the input image,
                    # as the RGB conversion makes it lose its "GIF-ness."
                    frame = frame.convert('RGB')
                    frame = frame.resize(scaled_size, resample=FILTER)
                if back_image:
                    back_image.paste(frame, position)
                    self.double_buffer.SetImage(back_image)
                else:
                    self.double_buffer.SetImage(frame)
                # Pause before showing new frame if prior frame delay
                # has not yet fully elapsed.
                frame_delay = (self.frame_duration -
                               (time.time() - self.frame_start_time))
                if frame_delay > 0.0:
                    time.sleep(frame_delay)
                self.double_buffer = self.matrix.SwapOnVSync(self.double_buffer)
                self.frame_start_time = time.time()
                self.frame_duration = next_duration

    def run(self):
        # Handle script-specific command line argument(s):
        if self.args.dir is not None:
            self.gif_path = self.args.dir

        # Create offscreen buffer for graphics
        self.double_buffer = self.matrix.CreateFrameCanvas()

        self.matrix_size = (self.matrix.width, self.matrix.height)

        os.chdir(self.gif_path)
        while True:
            for filename in glob.glob("*.gif"):
                try:
                    image = Image.open(filename)
                    self.loop_gif(image)
                except IOError:
                    pass

if __name__ == "__main__":
    MY_APP = GIFplayer()  # Instantiate class, calls __init__() above
    MY_APP.process()      # SpectroBase startup, calls run() above
