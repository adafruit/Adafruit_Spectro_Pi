#!/usr/bin/env python

"""
Framebuffer-to-matrix mirror program for Adafruit Spectro.
Based on notro's framebuffer insights.
https://github.com/notro/fbtft_test
PRO TIP: for best performance, set up framebuffer for
a small size (e.g. 320x240) in /boot/config.txt:

hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=320 240 60 1 0 0 0
"""

import os
import fcntl
import mmap
import struct
from PIL import Image, ImageOps
from spectrobase import SpectroBase

FILTER = Image.LANCZOS  # Slower Pis might want BICUBIC or BILINEAR here
FRAMEBUFFER_DEVICE = "/dev/fb0"

# Definitions from linux/fb.h
FBIOGET_VSCREENINFO = 0x4600
FBIOBLANK = 0x4611
FB_BLANK_UNBLANK = 0

class FB2Matrix(SpectroBase):
    """Framebuffer-to-matrix mirror program for Adafruit Spectro."""

    def __init__(self, *args, **kwargs):
        super(FB2Matrix, self).__init__(*args, **kwargs)

        self.framebuffer_file = os.open(FRAMEBUFFER_DEVICE, os.O_RDONLY)
        vinfo = struct.unpack("8I12I16I4I",
                              fcntl.ioctl(self.framebuffer_file,
                                          FBIOGET_VSCREENINFO,
                                          " "*((8+12+16+4)*4)))
        bytes_per_pixel = (vinfo[6] + 7) // 8
        self.framebuffer_bytes = vinfo[0] * vinfo[1] * bytes_per_pixel
        self.framebuffer_mapped = mmap.mmap(self.framebuffer_file,
                                            self.framebuffer_bytes,
                                            flags=mmap.MAP_SHARED,
                                            prot=mmap.PROT_READ)
        self.framebuffer_size = (vinfo[0], vinfo[1])

        self.double_buffer = None # Initialized in run()
        self.matrix_size = None   # Initialized in run()
        self.stretch = False

        self.parser.add_argument(
            "-s", "--stretch", help="Stretch rather than crop image",
            action="store_true")

    def run(self):
        if self.args.stretch is not None:
            self.stretch = self.args.stretch

        # Create offscreen buffer for matrix graphics
        self.double_buffer = self.matrix.CreateFrameCanvas()
        self.matrix_size = (self.matrix.width, self.matrix.height)

        # Turn off display blanking
        try:
            fcntl.ioctl(self.framebuffer_file, FBIOBLANK, FB_BLANK_UNBLANK)
        except IOError:
            pass

        while True:
            self.framebuffer_mapped.seek(0)
            framebuf_data = self.framebuffer_mapped.read(self.framebuffer_bytes)
            image = Image.frombytes("RGBA", self.framebuffer_size,
                                    framebuf_data)
            channels = image.split()  # [B,G,R,A]
            image = Image.merge("RGB", (channels[2], channels[1], channels[0]))

            if self.stretch:
                # Stretch framebuffer image to fill matrix
                # (Does not maintain aspect ratio - image may be distorted)
                image = image.resize(self.matrix_size, resample=FILTER)
            else:
                # Crop framebuffer image to fill matrix (default)
                # (Maintains aspect ratio - no distortion, but cuts image)
                image = ImageOps.fit(image, self.matrix_size, method=FILTER)

            self.double_buffer.SetImage(image)
            self.double_buffer = self.matrix.SwapOnVSync(self.double_buffer)

if __name__ == "__main__":
    MY_APP = FB2Matrix()  # Instantiate class, calls __init__() above
    MY_APP.process()      # SpectroBase startup, calls run() above
