#!/usr/bin/env python

"""
Audio spectrum display for Adafruit Spectro. This is designed to be fun to
look at, not a Serious Audio Tool(tm). Requires USB microphone & ALSA config.
Prerequisite libraries include PyAudio and NumPy:
sudo apt-get install python3-pyaudio python3-numpy
See the following for ALSA config (use Stretch directions):
learn.adafruit.com/usb-audio-cards-with-a-raspberry-pi/updating-alsa-config
"""

# Gets code to pass both pylint & pylint3:
# pylint: disable=superfluous-parens, no-self-use, too-many-locals, too-many-branches, too-many-statements, import-error


import numpy as np
from PIL import Image
from PIL import ImageDraw
from spectrobase import SpectroBase
import pyaudio

FORMAT = pyaudio.paInt16  # Data format from audio device (16-bit int)
CHANNELS = 1              # Mono's fine for what we're doing
RATE = 32000              # Balance audio quality & frame rate
CHUNK = 512               # Audio samples to read per frame
NOISE = 2                 # Subtraced from FFT output to avoid sparkles
LEAST = 50                # Lowest bin of FFT output to use for graph
MOST = 300                # Highest bin (0 to CHUNK-1). Bit above C7-ish
EXPONENT = 2.5            # Column-to-FFT-bin nonlinear mapping

class AudioSpectrum(SpectroBase):
    """Audio spectrum display for Adafruit Spectro."""

# Not currently used (no args, no self.* variables)
#    def __init__(self, *args, **kwargs):
#        super(AudioSpectrum, self).__init__(*args, **kwargs)

    def weight(self, pos, center, width):
        """Used for 'weighting' values from the spectrum output into display
           columns. Given a position 'pos' along X axis of spectrum out,
           compute corresponding Y for cubic curve centered on 'center' with
           range +/- 'width'. Returns 0.0 (outside or at very edge of curve)
           to 1.0 (peak at center of curve)."""
        dist = abs(pos - center) / width  # Normalized distance from center
        if dist >= 1.0:                   # Not on curve
            return 0.0
        dist = 1.0 - dist                 # Invert dist so 1.0 is at center
        return ((3.0 - (dist * 2.0)) * dist) * dist

    def run(self):

        # Access USB mic via PyAudio
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            output=False,
            frames_per_buffer=CHUNK)

        # Create offscreen buffer for graphics
        double_buffer = self.matrix.CreateFrameCanvas()

        # Create PIL image and drawing context
        image = Image.new("RGB", (self.matrix.width, self.matrix.height))
        draw = ImageDraw.Draw(image)

        # Some tables associated with each column of the display.
        # Should probably make a class for this, but for now it's just
        # lots of messy variables...
        height = [0] * self.matrix.width        # Current column height
        peak = [0] * self.matrix.width          # Recent column peak
        dropv = [0.0] * self.matrix.width       # Current peak falling speed
        autolevel = [32.0] * self.matrix.width  # Per-column auto adjust

        # Precompute values for each display column...
        colors = []  # Again, if I make a per-column class as mentioned
        weights = [] # above, these values can go in there. Deadlines happen.
        sums = []
        for column in range(self.matrix.width):
            # Precompute hue. '300' is intentional...don't wrap all the
            # way around back to red (360). Purple (300) looks good.
            colors.append('hsl(%d, %d%%, %d%%)' %
                          (column * 300 / self.matrix.width, 100, 50))

            # Precompute FFT weightings. Each column of the display
            # represents the sum of several FFT bins, applying a cubic
            # weighting to each, with a slight overlap between columns.
            frac = column / float(self.matrix.width - 1) # 0.0 to 1.0
            center = LEAST + (MOST - LEAST) * (frac ** EXPONENT)
            # Overlap is a function of distance to the next column.
            if column > 0:
                dist_column = column - 1  # Use distance from prior column
            else:
                dist_column = column + 1  # 1st column; use distance to next
            frac = dist_column / float(self.matrix.width - 1) # 0.0 to 1.0
            dist_center = LEAST + (MOST - LEAST) * (frac ** EXPONENT)
            width = 0.75 + abs(center - dist_center)   # Cubic curve half-width
            column_weights = []                        # List of bin weights
            total = 0.0                                # Sum of weights
            left = max(0, int(center - width))            # Clip left
            right = min(int(center + width + 1), CHUNK-1) # Clip right
            # Compute each FFT bin's contribution to column
            for bucket in range(left, right): # ('bin' is a reserved keyword)
                weight = self.weight(bucket + 0.5, center, width)
                if weight > 0:
                    # Bin is in range, append as a 2-element list with the
                    # bin index and the bin's weighting toward the column.
                    column_weights.append([bucket, weight])
                    total += weight
            weights.append(column_weights)  # Weights for this column
            sums.append(total)              # Sum-of-weights for column
        # Now normalize all the column sums, apply an exponential
        # scaling function to tone down the lower-frequency bins.
        # No scientific reason for this, just looks better on the matrix.
        maxsum = max(sums)
        for column in range(self.matrix.width):
            # Scaling function was arrived at through experimentation;
            # no scientific reason to these values, just looked good.
            scale = (0.02 + 0.08 *
                     ((column / float(self.matrix.width - 1)) ** 1.8))
            scale *= maxsum / sums[column] # Boost 'weak' columns
            for weight in weights[column]: # List of bin weights for column
                weight[1] *= scale         # Scale each bin weight

        while True:

            # Read bytes from PyAudio stream, convert to int16,
            # process via NumPy's FFT function...
            data_8 = stream.read(CHUNK * 2, exception_on_overflow=False)
            data_16 = np.frombuffer(data_8, np.int16)
            fft_out = np.fft.fft(data_16, norm="ortho")
            # fft_out will have CHUNK * 2 elements, mirrored at center

            # Get spectrum of first half. Instead of square root for
            # magnitude, use something between square and cube root.
            # No scientific reason, just looked good.
            spec_y = [(c.real * c.real + c.imag * c.imag) ** 0.4
                      for c in fft_out[0:CHUNK]]

            # Process and render each column (here's where having
            # a Column class would make things a little tidier).
            for column in range(self.matrix.width):
                # Calculate weighted sum of FFT bins for this column
                total = -NOISE
                for bin_weight in weights[column]:
                    total += spec_y[bin_weight[0]] * bin_weight[1]

                # Auto-leveling is intended to make each column 'pop'.
                # When a particular column isn't getting a lot of input
                # from the FFT, gradually boost that column's sensitivity.
                if total > autolevel[column]:
                    # Make autolevel rise quickly if column total exceeds it
                    autolevel[column] = autolevel[column] * 0.25 + total * 0.75
                else:
                    # And fall slowly otherwise
                    autolevel[column] = autolevel[column] * 0.98 + total * 0.02
                # Minimum autolevel value is 1/8 matrix height
                if autolevel[column] < self.matrix.height / 8.0:
                    autolevel[column] = self.matrix.height / 8.0

                # Apply autoleveling to weighted input...
                # this is the preliminary column height before filtering
                total = total * (self.matrix.height / autolevel[column])

                # Filter the column height computed above
                if total > height[column]:
                    # If it's greater than this column's prior height,
                    # filter column's height quickly in that direction
                    height[column] = height[column] * 0.4 + total * 0.6
                else:
                    # If less, filter slowly down
                    height[column] = height[column] * 0.6 + total * 0.4

                # Compute "peak dots," which sort of show the recent
                # peak level for each column (mostly just neat to watch).
                if height[column] > peak[column]:
                    # If column exceeds old peak, move peak immediately
                    peak[column] = min(height[column], self.matrix.height)
                    dropv[column] = 0.0
                else:
                    # Otherwise, peak gradually accelerates down
                    dropv[column] += 0.15
                    peak[column] -= dropv[column]

                # Draw peak dot
                draw.point([column, 32-peak[column]], fill=(255, 255, 255))
                # Draw spectrum column (may occlude dot, is OK)
                draw.line([column, 32, column, 32-height[column]],
                          fill=colors[column])
                # Debug stuff for showing autolevel action
                #draw.point([column, 32-autolevel[column]], fill=(255, 0, 0))

            # Copy PIL image to matrix buffer, swap buffers each frame
            double_buffer.SetImage(image)
            double_buffer = self.matrix.SwapOnVSync(double_buffer)

            # Clear PIL image before next pass
            draw.rectangle([0, 0, self.matrix.width - 1,
                            self.matrix.height - 1], fill=0)

if __name__ == "__main__":
    MY_APP = AudioSpectrum()  # Instantiate class, calls __init__() above
    MY_APP.process()          # SpectroBase startup, calls run() above
