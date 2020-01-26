#!/usr/bin/env python

"""
Arcade clock for Spectro.
"""

# Gets code to pass both pylint & pylint3:
# pylint: disable=bad-option-value, useless-object-inheritance

import time
from PIL import Image, ImageDraw
from spectrobase import SpectroBase

TWELVE_HOUR = True
EURO_DATE = False

# Each item in this list is a 4-tuple containing X, Y, width and height of
# sprite data within the sprite sheet image. Some of the sprite elements
# might overlap or get recycled (e.g. the dot image is just one pixel of the
# colon image) because this was adapted from an Arduino project and the
# space constraints there were insane.
SPRITE_COORDS = [
    (0, 16, 3, 5), (3, 16, 3, 5), (6, 16, 3, 5), (9, 16, 3, 5), # Digits 0-3
    (12, 16, 3, 5), (15, 16, 3, 5), (18, 16, 3, 5),             # Digits 4-6
    (21, 16, 3, 5), (24, 16, 3, 5), (27, 16, 3, 5),             # Digits 7-9
    (30, 17, 1, 3),                                 # Colon (between HH:MM:SS)
    (30, 17, 1, 1),                                 # Dot (between MM.DD.YY)
    (0, 38, 9, 9), (8, 46, 9, 9), (8, 54, 9, 9),    # Outline for mouth
    (8, 62, 9, 9), (8, 54, 9, 9), (8, 46, 9, 9),    # moving right (6 frames)
    (0, 38, 9, 9), (0, 29, 9, 9), (8, 29, 9, 9),    # Outline for mouth
    (16, 29, 9, 9), (8, 29, 9, 9), (0, 29, 9, 9),   # moving down (6 frames)
    (0, 38, 9, 9), (0, 46, 9, 9), (0, 54, 9, 9),    # Outline for mouth
    (0, 62, 9, 9), (0, 54, 9, 9), (0, 46, 9, 9),    # moving left (6 frames)
    (0, 38, 9, 9), (0, 21, 9, 9), (8, 21, 9, 9),    # Outline for mouth
    (16, 21, 9, 9), (8, 21, 9, 9), (0, 21, 9, 9),   # moving up (6 frames)
    (17, 40, 7, 7), (23, 46, 7, 7), (23, 52, 7, 7), # Mouth moving right
    (23, 59, 7, 7), (23, 52, 7, 7), (23, 46, 7, 7), # (6 frames)
    (17, 40, 7, 7), (0, 77, 7, 7), (6, 77, 7, 7),   # Mouth moving down
    (13, 77, 7, 7), (6, 77, 7, 7), (0, 77, 7, 7),   # (6 frames)
    (17, 40, 7, 7), (17, 46, 7, 7), (17, 52, 7, 7), # Mouth moving left
    (17, 59, 7, 9), (17, 52, 7, 7), (17, 46, 7, 7), # (6 frames)
    (17, 40, 7, 7), (0, 71, 7, 7), (6, 71, 7, 7),   # Mouth moving up
    (13, 71, 7, 7), (6, 71, 7, 7), (0, 71, 7, 7),   # (6 frames)
    (23, 66, 9, 9), (23, 75, 9, 9),                 # Ghost outline (2 frames)
    (25, 21, 7, 7), (25, 28, 7, 7),                 # Ghost (2 frames)
    (26, 38, 5, 3), (26, 42, 5, 3),                 # Ghost eyes (right, down)
    (26, 36, 5, 3), (26, 41, 5, 3),                 # Ghost eyes (left, up)
    (0, 0, 32, 16),                                 # Playfield
]

def orient(frac):
    """Given a fractional value (0.0 to 1.0), determine the corresponding
       pixel index around the perimeter of the maze (there are 68 distinct
       viable pixel positions around the 32x16 image)."""
    pixel = int(frac * 68)
    if pixel < 25:
        x_pos = pixel
        y_pos = 0
        direction = 0 # Right
    elif pixel < 34:
        x_pos = 25
        y_pos = pixel - 25
        direction = 1 # Down
    elif pixel < 59:
        x_pos = 59 - pixel
        y_pos = 9
        direction = 2 # Left
    else:
        x_pos = 0
        y_pos = 68 - pixel
        direction = 3 # Up
    return x_pos, y_pos, direction

class Sprite(object):
    """Movable graphics entities. These don't themselves contain bitmap data,
       but have an index into the main applications sprite_data[] array."""
    def __init__(self, image_index, x_pos, y_pos, color):
        self.image_index = image_index
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.color = color
        self.brightness = 1.0
        self.off_time = -100.0

    def reframe(self, idx, x_pos, y_pos):
        """Assign a new image index and (X,Y) position to a Sprite."""
        self.image_index = idx
        self.x_pos = x_pos
        self.y_pos = y_pos

    def adjusted_brightness(self):
        """Return a Sprite's color with its current brightness applied."""
        return (int(self.color[0] * self.brightness),
                int(self.color[1] * self.brightness),
                int(self.color[2] * self.brightness))

class ArcadeClock(SpectroBase):
    """Arcade clock for Spectro."""

    def __init__(self, *args, **kwargs):
        super(ArcadeClock, self).__init__(*args, **kwargs)

        # Create PIL image and drawing context
        self.image = Image.new("RGB", (64, 32))
        self.draw = ImageDraw.Draw(self.image)

        # Load sprite sheet and extract individual sprite rasters from it
        sprite_graphics = Image.open('graphics/arcade-bitmasks.png')
        self.sprite_data = []
        for coords in SPRITE_COORDS:
            self.sprite_data.append(
                sprite_graphics.crop((coords[0], coords[1],    # X0, Y0
                                      coords[0] + coords[2],   # X1
                                      coords[1] + coords[3]))) # Y1

        # Sprite objects in back-to-front render order. For each Sprite,
        # first element is an index to a sprite image (in sprite_data[]
        # array) -- many of these are assigned 0 to start, which is then
        # overridden in the logic loop. Second and third elements are X & Y
        # position on matrix (again many are initialized to 0 and changed
        # later), last element is sprite color (also sometimes initialized
        # 0 and changed later).
        self.sprite_list = [
            Sprite(len(SPRITE_COORDS) - 1, 0, 0, (0, 0, 255)), # Playfield
            Sprite(0, 2, 1, (255, 255, 255)),    # H
            Sprite(0, 6, 1, (255, 255, 255)),    # H
            Sprite(10, 10, 2, (255, 255, 255)),  # :
            Sprite(0, 12, 1, (255, 255, 255)),   # M
            Sprite(0, 16, 1, (255, 255, 255)),   # M
            Sprite(10, 20, 2, (255, 255, 255)),  # :
            Sprite(0, 22, 1, (255, 255, 255)),   # S
            Sprite(0, 26, 1, (255, 255, 255)),   # S
            Sprite(0, 2, 10, (255, 255, 255)),   # M
            Sprite(0, 6, 10, (255, 255, 255)),   # M
            Sprite(11, 10, 12, (255, 255, 255)), # -
            Sprite(0, 12, 10, (255, 255, 255)),  # D
            Sprite(0, 16, 10, (255, 255, 255)),  # D
            Sprite(11, 20, 12, (255, 255, 255)), # -
            Sprite(0, 22, 10, (255, 255, 255)),  # Y
            Sprite(0, 26, 10, (255, 255, 255)),  # Y
            Sprite(0, 0, 0, (0, 0, 0)),          # Mouth outline
            Sprite(0, 0, 0, (0, 0, 0)),          # Ghost outline
            Sprite(0, 0, 0, (255, 255, 0)),      # Mouth
            Sprite(0, 0, 0, (255, 0, 0)),        # Ghost
            Sprite(0, 0, 0, (255, 255, 255))     # Eyes
        ]

    def set_two_digits(self, first_sprite, value):
        """Set the image indices for two adjacent Sprites, used for
           assigning two-digit numbers (e.g. HH, MM, SS, etc.)."""
        self.sprite_list[first_sprite].image_index = value // 10
        self.sprite_list[first_sprite + 1].image_index = value % 10

    def run(self):

        # Create offscreen buffer for graphics
        double_buffer = self.matrix.CreateFrameCanvas()

        while True:

            current_time = time.time()

            localtime = time.localtime(current_time)
            if TWELVE_HOUR:
                hour = localtime.tm_hour % 12
                if hour == 0:
                    hour = 12
            else:
                hour = localtime.tm_hour

            # Configure time sprites (HH:MM:SS)
            self.set_two_digits(1, hour)
            self.set_two_digits(4, localtime.tm_min)
            self.set_two_digits(7, localtime.tm_sec)

            # Configure date sprites (MM.DD.YY) or (YY:MM:DD)
            if EURO_DATE:
                self.set_two_digits(9, localtime.tm_year % 100)
                self.set_two_digits(12, localtime.tm_mon)
                self.set_two_digits(15, localtime.tm_mday)
            else:
                self.set_two_digits(9, localtime.tm_mon)
                self.set_two_digits(12, localtime.tm_mday)
                self.set_two_digits(15, localtime.tm_year % 100)

            # Animate mouth around maze
            frac = (current_time % 3.5) / 3.5  # 3.5 seconds per lap
            x_pos, y_pos, direction = orient(frac)
            frame = int((current_time % 0.4) * 15.0)  # 0 to 5
            self.sprite_list[17].reframe(12 + direction * 6 + frame,
                                         x_pos - 1, y_pos - 1)
            self.sprite_list[19].reframe(36 + direction * 6 + frame,
                                         x_pos, y_pos)
            # Making the mouth "eat" digits is pretty brute force...
            # position of sprite center is compared against mouth center.
            # if +/- 2 pixels, consider that sprite "eaten" (set its
            # brightness to 0). This is not foolproof...if the frame rate
            # is super chunky (e.g. Pi Zero under heavy load), it's
            # possible (though I don't know how probable) that some
            # digits may be skipped. This would be visually annoying but
            # is not actually destructive.
            x_pos += 3
            y_pos += 3
            for sprite in self.sprite_list[1:17]:
                idx = sprite.image_index
                delta_x = x_pos - (sprite.x_pos + SPRITE_COORDS[idx][2] // 2)
                delta_y = y_pos - (sprite.y_pos + SPRITE_COORDS[idx][3] // 2)
                if delta_x * delta_x + delta_y * delta_y <= 4:
                    sprite.off_time = current_time
                    sprite.brightness = 0.0
                else:
                    sprite.brightness = min(
                        1.0, max(0.0, current_time - sprite.off_time - 1.0))

            # Make ghost follow mouth, slightly behind
            x_pos, y_pos, direction = orient((frac - 0.18) % 1.0)
            frame = int((current_time % 1.0) * 2.0)
            self.sprite_list[18].reframe(60 + frame, x_pos - 1, y_pos - 1)
            self.sprite_list[20].reframe(62 + frame, x_pos, y_pos)
            self.sprite_list[21].reframe(64 + direction, x_pos + 1, y_pos + 1)

            # Clear image, draw sprites in back-to-front order:
            self.draw.rectangle((0, 0, self.matrix.width, self.matrix.height),
                                fill=0)
            for sprite in self.sprite_list:
                self.image.paste(
                    sprite.adjusted_brightness(),
                    (sprite.x_pos, sprite.y_pos,
                     sprite.x_pos + SPRITE_COORDS[sprite.image_index][2],
                     sprite.y_pos + SPRITE_COORDS[sprite.image_index][3]),
                    mask=self.sprite_data[sprite.image_index])

            # Copy PIL image to matrix buffer, swap buffers each frame
            double_buffer.SetImage(self.image)
            double_buffer = self.matrix.SwapOnVSync(double_buffer)

if __name__ == "__main__":
    MY_APP = ArcadeClock()  # Instantiate class, calls __init__() above
    MY_APP.process()        # SpectroBase startup, calls run() above
