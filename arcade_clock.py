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

SPRITE_COORDS_LARGE = [
    (0, 33, 7, 11), (8, 33, 7, 11), (16, 33, 7, 11),   # Digits 0-2
    (24, 33, 7, 11), (32, 33, 7, 11), (40, 33, 7, 11), # Digits 3-5
    (48, 33, 7, 11), (56, 33, 7, 11), (64, 33, 7, 11), # Digits 6-8
    (72, 33, 7, 11),                                   # 9
    (48, 45, 2, 5),                                 # Colon (between HH:MM:SS)
    (48, 45, 2, 2),                                 # Dot (between MM.DD.YY)
    (78, 15, 15, 15), (32, 45, 15, 15), (16, 45, 15, 15), # Outline for mouth
    (0, 45, 15, 15), (16, 45, 15, 15), (32, 45, 15, 15),  # moving right (6)
    (78, 15, 15, 15), (32, 61, 15, 15), (16, 61, 15, 15), # Outline for mouth
    (0, 61, 15, 15), (16, 61, 15, 15), (32, 61, 15, 15),  # moving down (6)
    (78, 15, 15, 15), (32, 77, 15, 15), (16, 77, 15, 15), # Outline for mouth
    (0, 77, 15, 15), (16, 77, 15, 15), (32, 77, 15, 15),  # moving left (6)
    (78, 15, 15, 15), (32, 93, 15, 15), (16, 93, 15, 15), # Outline for mouth
    (0, 93, 15, 15), (16, 93, 15, 15), (32, 93, 15, 15),  # moving up (6)
    (80, 31, 13, 13), (80, 45, 13, 13), (66, 45, 13, 13), # Mouth moving right
    (52, 45, 13, 13), (66, 45, 13, 13), (80, 45, 13, 13), # (6 frames)
    (80, 31, 13, 13), (80, 59, 13, 13), (66, 59, 13, 13), # Mouth moving down
    (52, 59, 13, 13), (66, 59, 13, 13), (80, 59, 13, 13), # (6 frames)
    (80, 31, 13, 13), (80, 73, 13, 13), (66, 73, 13, 13), # Mouth moving left
    (52, 73, 13, 13), (66, 73, 13, 13), (80, 73, 13, 13), # (6 frames)
    (80, 31, 13, 13), (80, 87, 13, 13), (66, 87, 13, 13), # Mouth moving up
    (52, 87, 13, 13), (66, 87, 13, 13), (80, 87, 13, 13), # (6 frames)
    (62, 101, 15, 15), (78, 101, 15, 15),                 # Ghost outline (2)
    (66, 0, 13, 13), (80, 0, 13, 13),                     # Ghost (2 frames)
    (66, 14, 9, 5),                                       # Ghost eyes
    (67, 20, 7, 2),                                       # Ghost pupils
    (0, 0, 64, 32),                                       # Playfield = 66
]

def orient_small(frac):
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
        x_pos = 58 - pixel
        y_pos = 9
        direction = 2 # Left
    else:
        x_pos = 0
        y_pos = 67 - pixel
        direction = 3 # Up
    return x_pos, y_pos, direction

def orient_large(frac):
    """Given a fractional value (0.0 to 1.0), determine the corresponding
       pixel index around the perimeter of the maze (there are 136 distinct
       viable pixel positions around the 64x32 image)."""
# 50 across, 18 high
    pixel = int(frac * 136)
    if pixel < 50:
        x_pos = pixel + 1
        y_pos = 1
        direction = 0 # Right
    elif pixel < 68:
        x_pos = 50
        y_pos = pixel - 49
        direction = 1 # Down
    elif pixel < 118:
        x_pos = 118 - pixel
        y_pos = 18
        direction = 2 # Left
    else:
        x_pos = 1
        y_pos = 136 - pixel
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

        self.sprite_data = None
        self.sprite_list = None
        self.sprite_coords_list = None
        self.current_time = 0
        self.image = None
        self.draw = None

    def set_two_digits(self, first_sprite, value):
        """Set the image indices for two adjacent Sprites, used for
           assigning two-digit numbers (e.g. HH, MM, SS, etc.)."""
        self.sprite_list[first_sprite].image_index = value // 10
        self.sprite_list[first_sprite + 1].image_index = value % 10

    def draw_mouth_small(self):
        """Animate mouth around small (32x16) maze."""
        frac = (self.current_time % 3.5) / 3.5  # 3.5 seconds per lap
        x_pos, y_pos, direction = orient_small(frac)
        frame = int((self.current_time % 0.3) * 20.0)  # 0 to 5
        self.sprite_list[17].reframe(12 + direction * 6 + frame,
                                     x_pos - 1, y_pos - 1)
        self.sprite_list[19].reframe(36 + direction * 6 + frame,
                                     x_pos, y_pos)
        return frac, x_pos, y_pos

    def draw_mouth_large(self):
        """Animate mouth around large (64x32) maze."""
        frac = (self.current_time % 3.5) / 3.5  # 3.5 seconds per lap
        x_pos, y_pos, direction = orient_large(frac)
        frame = int((self.current_time % 0.3) * 20.0)  # 0 to 5
        self.sprite_list[17].reframe(12 + direction * 6 + frame,
                                     x_pos - 1, y_pos - 1)
        self.sprite_list[19].reframe(36 + direction * 6 + frame,
                                     x_pos, y_pos)
        return frac, x_pos, y_pos

    def draw_ghost_small(self, frac):
        """Animate ghost around small (32x16) maze."""
        # Make ghost follow mouth, slightly behind
        x_pos, y_pos, direction = orient_small((frac - 0.18) % 1.0)
        frame = int((self.current_time % 1.0) * 2.0)
        self.sprite_list[18].reframe(60 + frame, x_pos - 1, y_pos - 1)
        self.sprite_list[20].reframe(62 + frame, x_pos, y_pos)
        self.sprite_list[21].reframe(64 + direction, x_pos + 1, y_pos + 1)

    def draw_ghost_large(self, frac):
        """Animate ghost around large (64x32) maze."""
        # Make ghost follow mouth, slightly behind
        x_pos, y_pos, direction = orient_large((frac - 0.15) % 1.0)
        frame = int((self.current_time % 1.0) * 2.0)
        self.sprite_list[18].reframe(60 + frame, x_pos - 1, y_pos - 1)
        self.sprite_list[20].reframe(62 + frame, x_pos, y_pos)
        eye_offset = [(3, 3), (2, 4), (1, 3), (2, 2)]
        pupil_offset = [(5, 5), (3, 7), (1, 5), (3, 2)]
        self.sprite_list[21].reframe(64, x_pos + eye_offset[direction][0],
                                     y_pos + eye_offset[direction][1])
        self.sprite_list[22].reframe(65, x_pos + pupil_offset[direction][0],
                                     y_pos + pupil_offset[direction][1])

    def eat_digits(self, x_pos, y_pos, offset, dist):
        """Make the mouth "eat" clock digits."""
        # Making the mouth eat digits is pretty brute force...
        # position of sprite center is compared against mouth center.
        # if +/- 'dist' pixels, consider that sprite "eaten" (set its
        # brightness to 0). This is not foolproof...if the frame rate
        # is super chunky (e.g. Pi Zero under heavy load), it's
        # possible (though I don't know how probable) that some
        # digits may be skipped. This would be visually annoying but
        # is not actually destructive.
        x_pos += offset
        y_pos += offset
        dist *= dist  # Pixel distance squared (avoids a sqrt())
        for sprite in self.sprite_list[1:17]:
            idx = sprite.image_index
            delta_x = x_pos - (sprite.x_pos +
                               self.sprite_coords_list[idx][2] // 2)
            delta_y = y_pos - (sprite.y_pos +
                               self.sprite_coords_list[idx][3] // 2)
            if delta_x * delta_x + delta_y * delta_y <= dist:
                sprite.off_time = self.current_time
                sprite.brightness = 0.0
            else:
                sprite.brightness = min(
                    1.0, max(0.0, self.current_time - sprite.off_time - 1.0))

    def load_sprites(self, large):
        """Load sprite sheet and extract sprite rasters from it."""
        if large:
            filename = 'graphics/arcade-bitmasks-large.png'
            self.sprite_coords_list = SPRITE_COORDS_LARGE
        else:
            filename = 'graphics/arcade-bitmasks.png'
            self.sprite_coords_list = SPRITE_COORDS

        # Load sprite sheet and extract individual sprite rasters from it
        sprite_graphics = Image.open(filename)
        self.sprite_data = []
        for coords in self.sprite_coords_list:
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
        # This is a bit messy because the list has to be build in "stacking
        # order" -- as sprites will be rendered back-to-front.
        self.sprite_list = [
            Sprite(len(self.sprite_coords_list) - 1, 0, 0,
                   (33, 33, 255))                # Maze
        ]
        if large:
            self.sprite_list += [
                Sprite(0, 5, 2, (255, 183, 174)),    # H
                Sprite(0, 13, 2, (255, 183, 174)),    # H
                Sprite(10, 21, 5, (255, 183, 174)),  # :
                Sprite(0, 24, 2, (255, 183, 174)),   # M
                Sprite(0, 32, 2, (255, 183, 174)),   # M
                Sprite(10, 40, 5, (255, 183, 174)),  # :
                Sprite(0, 43, 2, (255, 183, 174)),   # S
                Sprite(0, 51, 2, (255, 183, 174)),   # S

                Sprite(0, 5, 19, (255, 183, 174)),   # M
                Sprite(0, 13, 19, (255, 183, 174)),   # M
                Sprite(11, 21, 23, (255, 183, 174)), # -
                Sprite(0, 24, 19, (255, 183, 174)),  # D
                Sprite(0, 32, 19, (255, 183, 174)),  # D
                Sprite(11, 40, 23, (255, 183, 174)), # -
                Sprite(0, 43, 19, (255, 183, 174)),  # Y
                Sprite(0, 51, 19, (255, 183, 174))]  # Y
        else:
            self.sprite_list += [
                Sprite(0, 2, 1, (255, 183, 174)),    # H
                Sprite(0, 6, 1, (255, 183, 174)),    # H
                Sprite(10, 10, 2, (255, 183, 174)),  # :
                Sprite(0, 12, 1, (255, 183, 174)),   # M
                Sprite(0, 16, 1, (255, 183, 174)),   # M
                Sprite(10, 20, 2, (255, 183, 174)),  # :
                Sprite(0, 22, 1, (255, 183, 174)),   # S
                Sprite(0, 26, 1, (255, 183, 174)),   # S
                Sprite(0, 2, 10, (255, 183, 174)),   # M
                Sprite(0, 6, 10, (255, 183, 174)),   # M
                Sprite(11, 10, 12, (255, 183, 174)), # -
                Sprite(0, 12, 10, (255, 183, 174)),  # D
                Sprite(0, 16, 10, (255, 183, 174)),  # D
                Sprite(11, 20, 12, (255, 183, 174)), # -
                Sprite(0, 22, 10, (255, 183, 174)),  # Y
                Sprite(0, 26, 10, (255, 183, 174))]  # Y
        self.sprite_list += [
            Sprite(0, 0, 0, (0, 0, 0)),          # Mouth outline
            Sprite(0, 0, 0, (0, 0, 0)),          # Ghost outline
            Sprite(0, 0, 0, (255, 255, 0)),      # Mouth
            Sprite(0, 0, 0, (255, 0, 0)),        # Ghost
            Sprite(64, 0, 0, (222, 222, 255))]   # Eyes
        if large:
            self.sprite_list += [Sprite(65, 0, 0, (0, 0, 222))] # Pupils


    def run(self):

        # Create offscreen buffer for graphics
        double_buffer = self.matrix.CreateFrameCanvas()

        # Create PIL image and drawing context
        self.image = Image.new("RGB", (self.matrix.width, self.matrix.height))
        self.draw = ImageDraw.Draw(self.image)

        self.load_sprites(self.matrix.width > 32)

        while True:

            self.current_time = time.time()

            localtime = time.localtime(self.current_time)
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
            if self.matrix.width > 32:
                frac, x_pos, y_pos = self.draw_mouth_large()
                self.eat_digits(x_pos, y_pos, 6, 2)
                self.draw_ghost_large(frac)
            else:
                frac, x_pos, y_pos = self.draw_mouth_small()
                self.eat_digits(x_pos, y_pos, 3, 2)
                self.draw_ghost_small(frac)

            # Clear image, draw sprites in back-to-front order:
            self.draw.rectangle((0, 0, self.matrix.width, self.matrix.height),
                                fill=0)
            for sprite in self.sprite_list:
                self.image.paste(
                    sprite.adjusted_brightness(),
                    (sprite.x_pos, sprite.y_pos,
                     sprite.x_pos + self.sprite_coords_list[
                         sprite.image_index][2],
                     sprite.y_pos + self.sprite_coords_list[
                         sprite.image_index][3]),
                    mask=self.sprite_data[sprite.image_index])

            # Copy PIL image to matrix buffer, swap buffers each frame
            double_buffer.SetImage(self.image)
            double_buffer = self.matrix.SwapOnVSync(double_buffer)

if __name__ == "__main__":
    MY_APP = ArcadeClock()  # Instantiate class, calls __init__() above
    MY_APP.process()        # SpectroBase startup, calls run() above
