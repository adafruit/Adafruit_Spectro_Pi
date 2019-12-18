#!/usr/bin/env python

"""
Minimal example for using the SpectroBase class.
New Spectro scripts can start with this & embellish as needed.
Adapted from hzeller's RGBMatrix Python binding examples.
"""

# Gets code to pass both pylint & pylint3:
# pylint: disable=superfluous-parens

from spectrobase import SpectroBase

class BoilerPlate(SpectroBase):
    """Example for SpectroBase, does nothing useful, just double-buffers
       a blank screen until cancelled. New Spectro projects can use this
       as a starting point and embellish as needed."""

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

        while True:
            # Swap buffers each frame
            double_buffer = self.matrix.SwapOnVSync(double_buffer)

if __name__ == "__main__":
    MY_APP = BoilerPlate()  # Instantiate class, calls __init__() above
    MY_APP.process()        # SpectroBase startup, calls run() above
