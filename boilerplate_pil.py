#!/usr/bin/env python

"""
Minimal example for using the SpectroBase class plus Python Imaging Library.
New Spectro scripts can start with this & embellish as needed. PIL provides
more graphics primitives, raster operations, image loading and TrueType font
support...but some operations, especially scrolling TrueType text, might be
too much for single-core Pi A/B/Zero to handle well. For simple text
displays (e.g. clock, system stats, etc.), consider using the DrawText
function of RGBMatrix, which uses .bdf bitmap fonts -- less flexible, but
quicker and more legible at small sizes.
"""

# Gets code to pass both pylint & pylint3:
# pylint: disable=superfluous-parens

from PIL import Image
#from PIL import ImageDraw
#from PIL import ImageFont
from spectrobase import SpectroBase

class BoilerPlate(SpectroBase):
    """Example for SpectroBase using PIL, does nothing useful, just double-
       buffers a blank screen until cancelled. New Spectro projects can use
       this as a starting point and embellish as needed."""

    def __init__(self, *args, **kwargs):
        super(BoilerPlate, self).__init__(*args, **kwargs)

        # Example of an additional command line argument.
        # Second value here, "--foo", is both the command line switch and
        # the argument's name within self.args (i.e. self.args.foo).
        # If no 'default' is given, unassigned value is None.
        self.parser.add_argument(
            "-f", "--foo", help="Example of an additional "
            "command line argument.", default="Foo")

    def run(self):

        # Handle script-specific command line argument(s):
        if self.args.foo is not None:
            print(self.args.foo)

        # Create offscreen buffer for graphics
        double_buffer = self.matrix.CreateFrameCanvas()

        # Create PIL image
        image = Image.new("RGB", (self.matrix.width, self.matrix.height))
        # In some situations you might not want the PIL image the same
        # size as the RGBMatrix canvas. One case is declaring a fixed-size
        # 64x32 image, then calling resize() if (and only if) RGB matrix is
        # the smaller 32x16 size. A different case would be, regardless of
        # matrix size, declaring the PIL image 2X matrix.size.width & height
        # and always calling resize() to get smooth 2x2 downsampling.
        # (See also reference to the halve() function below)
        # image = Image.new(
        #     "RGB", (self.matrix.width * 2, self.matrix.height * 2))

        while True:
            # Copy PIL image to matrix buffer, swap buffers each frame
            double_buffer.SetImage(image)
            # See notes above re: scaling option
            # double_buffer.SetImage(image.resize(
            #     (self.matrix.width, self.matrix.height),
            #     resample=Image.BILINEAR))
            # There's also the halve() function in SpectroBase, providing
            # a more precise 1:2 downscaling, but it's not as quick.
            # double_buffer.SetImage(self.halve(self.image))
            double_buffer = self.matrix.SwapOnVSync(double_buffer)

if __name__ == "__main__":
    MY_APP = BoilerPlate()  # Instantiate class, calls __init__() above
    MY_APP.process()        # SpectroBase startup, calls run() above
