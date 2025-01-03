#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2017 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function, unicode_literals

import copy
import json
import math, cmath
from collections import namedtuple

class KLEParseError(Exception):
    pass

def rotate_complex(radians):
    return cmath.exp(radians*1j)

Rect = namedtuple('Rect', 'x y w h')

class Point(namedtuple('Point', ('x', 'y'))):
    __slots__ = ()
    def __abs__(self):
        return type(self)(abs(self.x), abs(self.y))

    def __int__(self):
        return type(self)(int(self.x), int(self.y))

    def __add__(self, other):
        return type(self)(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return type(self)(self.x - other.x, self.y - other.y)

    def __neg__(self):
        return type(self)(-self.x, -self.y)

    def __mul__(self, other):
        return type(self)(self.x * other, self.y * other)

    def __rmul__(self, other):
        return type(self)(self.x * other, self.y * other)

    def __truediv__(self, other):
         return type(self)(self.x / other, self.y / other)

    def __rdiv__(self, other):
        return type(self)(self.x / other, self.y / other)

    def dot_product(self, other):
        return self.x * other.x + self.y * other.y

    def cross_product(self, other):
        return self.x * other.y - self.y * other.x

    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2)

    def distance_to(self, other):
        return math.hypot((self.x - other.x), (self.y - other.y))

    def normalize(self):
        if self.x == 0 and self.y == 0:
            return Point(self.x, self.y)
        else:
            return Point(self.x, self.y) / self.magnitude()


class KLEKey(object):
    """              ( x, y )
     0 top left      (-1, -1)
     1 bottom left   (-1,  1)
     2 top right     ( 1, -1)
     3 bottom right  ( 1,  1)
     4 front left    (-1,  2)
     5 front right   ( 1,  2)
     6 center left   (-1,  0)
     7 center right  ( 1,  0)
     8 top center    ( 0,  1)
     9 center        ( 0,  0)
    10 bottom center ( 0, -1)
    11 front center  ( 0,  2)
    """
    TOP_LEFT = 0
    BOT_LEFT = 1
    TOP_RIGHT = 2
    BOT_RIGHT = 3
    FRONT_LEFT = 4
    FRONT_RIGHT = 5
    CENTER_LEFT = 6
    CENTER_RIGHT = 7
    TOP_CENTER = 8
    CENTER = 9
    BOT_CENTER = 10
    FRONT_CENTER = 11

    LEGEND_MAP = {
        TOP_LEFT: (-1, -1),
        BOT_LEFT: (-1,  1),
        TOP_RIGHT: ( 1, -1),
        BOT_RIGHT: ( 1,  1),
        FRONT_LEFT: (-1,  2),
        FRONT_RIGHT: ( 1,  2),
        CENTER_LEFT: (-1,  0),
        CENTER_RIGHT: ( 1,  0),
        TOP_CENTER: ( 0,  -1),
        CENTER: ( 0,  0),
        BOT_CENTER: ( 0, 1),
        FRONT_CENTER: ( 0,  2),
    }

    def __init__(self, ux, uy, uw, uh, text="", properties=None, decal=False, spacing=19.0):
        """@todo: to be defined1. """
        # the coordinate system
        # the offset in the coordinate system
        self._u_x = ux * 1.0
        self._u_y = uy * 1.0
        self._u_w = uw * 1.0
        self._u_h = uh * 1.0
        self._spacing = spacing
        self.decal = decal
        if properties == None:
            self.properties = KbProperties()
        else:
            self.properties = copy.copy(properties)
        self._r = self.properties.r
        self._u_rx = self.properties.rx
        self._u_ry = self.properties.ry

        legends = text.split("\n")
        max_legends = len(KLEKey.LEGEND_MAP)
        if len(legends) > max_legends:
            raise Exception(KLEParseError("Too many legends for key. Got {}, max is {}"
                                          .format(len(legends), max_legends)))

        self._legends = {}

        for key in range(max_legends):
            if key < len(legends):
                self._legends[key] = legends[key]
            else:
                self._legends[key] = ""

        for key in self._legends.keys():
            if not key in self._legends:
                self._legends [key] = ''

    def get_legend(self, key):
        assert(key in KLEKey.LEGEND_MAP)
        return self._legends[key]

    def set_legend(self, key, value):
        assert(key in KLEKey.LEGEND_MAP)
        assert(type(value) == str)
        self._legends[key] = value

    def get_legend_list(self):
        result = []
        for key in range(len(KLEKey.LEGEND_MAP)):
            if self._legends[key] != "":
                result.append((KLEKey.LEGEND_MAP[key], self._legends[key]))
        return result

    def get_legend_str(self):
        result = ""
        print(self._legends)
        for key in range(len(KLEKey.LEGEND_MAP)):
            result += self._legends[key] + "\n"
        return result.strip("\n")

    @property
    def spacing(self):
        return self._spacing

    @property
    def x(self):
        return self._spacing * (self._u_x + self._u_rx)

    @property
    def y(self):
        return self._spacing * (self._u_y + self._u_ry)

    @property
    def w(self):
        return self._spacing * self._u_w

    @property
    def h(self):
        return self._spacing * self._u_h

    @property
    def r(self):
        return self._r

    @property
    def r_rad(self):
        return math.radians(self._r)

    @property
    def rx(self):
        return self._u_rx * self._spacing

    @property
    def ry(self):
        return self._u_ry * self._spacing

    def get_rect_points(self):
        pos = self.get_pos()
        pos = pos[0] + pos[1]*1j

        edge_w = (self.w + 0j         ) * rotate_complex(self.r_rad)
        edge_h = (0        + self.h*1j) * rotate_complex(self.r_rad)

        v0 = pos
        v1 = pos + edge_w
        v2 = pos + edge_w + edge_h
        v3 = pos + edge_h

        return [
            Point(v0.real, v0.imag),
            Point(v1.real, v1.imag),
            Point(v2.real, v2.imag),
            Point(v3.real, v3.imag),
        ]

    def get_center(self):
        pos = self.get_pos()
        pos = pos.x + pos.y*1j
        center = pos + 1/2 * (self.w + self.h*1j) * rotate_complex(self.r_rad)
        return Point(center.real, center.imag)

    def set_center(self, x, y):
        new_center = x + y*1j
        corner = new_center - 1/2 * (self.w + self.h*1j) * rotate_complex(self.r_rad)
        self.set_pos(corner.real, corner.imag)

    def bounding_box(self):
        points = self.get_rect_points()
        xmin = math.inf
        ymin = math.inf
        xmax = -math.inf
        ymax = -math.inf

        for point in points:
            xmin = min(xmin, point[0])
            ymin = min(ymin, point[1])
            xmax = max(xmax, point[0])
            ymax = max(ymax, point[1])

        return Rect(xmin, ymin, xmax-xmin, ymax-ymin)

    def bounding_box_points(self):
        (x, y, w, h) = self.bounding_box()
        return [
            Point(x    , y    ),
            Point(x + w, y    ),
            Point(x + w, y + h),
            Point(x    , y + h)
        ]

    @property
    def spacing(self):
        return self._spacing

    @spacing.setter
    def spacing(self, value):
        self._spacing = value

    def get_pos(self):
        rpos = (self._u_rx + self._u_ry*1j)
        pos = rpos + (self._u_x + self._u_y*1j) * rotate_complex(self.r_rad)
        pos *= self._spacing
        return Point(pos.real, pos.imag)

    def set_pos(self, x, y):
        u_pos = Point(x, y) / self._spacing # remove scaling
        u_pos -= Point(self._u_rx, self._u_ry) # remove translation offset
        u_pos = (u_pos.x + u_pos.y*1j) * rotate_complex(-self.r_rad) # remove rotation
        self._u_x = u_pos.real # left with unit positions
        self._u_y = u_pos.imag

    def set_angle(self, new_r):
        pos = self.get_center()
        self._r = new_r
        self.set_center(pos.x, pos.y)

    @property
    def u_x(self):
        return self._u_x + self._u_rx

    @property
    def u_y(self):
        return self._u_y + self._u_ry

    @property
    def u_w(self):
        return self._u_w

    @property
    def u_h(self):
        return self._u_h

    def get_u_pos(self):
        return Point(self._u_x, self._u_y)

    def set_u_pos(self, ux, uy, r=None, u_rx=None, u_ry=None):
        self._u_x = ux
        self._u_y = uy
        if r: self._r = r
        if u_rx: self._u_rx = u_rx
        if u_ry: self._u_ry = u_ry

    def __str__(self):
        return "KLEKey(legend={}, ux={}, uy={}, uw={}, uh={}, r={})".format(
            repr(self.get_legend_list()), self._u_x, self._u_y, self._u_w, self._u_h, self._r
        )

    def __repr__(self):
        return str(self)

    def get_properties(self):
        result = KeyProperties()
        result.x = self._u_x
        result.y = self._u_y
        result.w = self._u_w
        result.h = self._u_h
        result.rx = self._u_rx
        result.ry = self._u_ry
        return result


class KeyProperties(object):
    def __init__(self,
                 x=0, y=0,
                 w=1, h=1,
                 x2=None, y2=None,
                 w2=None, h2=None,
                 stepped=False,
                 homing=False,
                 decal=False):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.x2 = None
        self.y2 = None
        self.w2 = None
        self.h2 = None

        self.rx = None
        self.ry = None

        self.stepped = False
        self.homing = False
        self.decal = False

    @staticmethod
    def from_json(obj):
        props = KeyProperties()
        if 'x' in obj:
            props.x = float(obj['x'])
        if 'y' in obj:
            props.y = float(obj['y'])
        if 'w' in obj:
            props.w = float(obj['w'])
        if 'h' in obj:
            props.h = float(obj['h'])
        if 'x2' in obj:
            props.x2 = float(obj['x2'])
        if 'y2' in obj:
            props.y2 = float(obj['y2'])
        if 'w2' in obj:
            props.w2 = float(obj['w2'])
        if 'h2' in obj:
            props.h2 = float(obj['h2'])
        if 'd' in obj:
            props.decal = bool(obj['d'])
        if 'l' in obj:
            props.stepped = bool(obj['l'])
        if 'n' in obj:
            props.homing = bool(obj['n'])
        return props

    def to_json(self):
        result = {}
        for field in [
            'x', 'y', 'w', 'h', 'x2', 'y2', 'w2', 'h2',
            'rx', 'ry',
        ]:
            value = getattr(self, field)
            if value != None: result[field] = value
        return result


class KbProperties(object):
    """
    KbProperties apply to all subsequent keycaps
    """
    def __init__(self,
                 keycap_color='#ffffff',
                 text_color='#000000',
                 ghosted=False,
                 profile=None,
                 text_alignment=None,
                 font_primary=3,
                 font_secondary=3,
                 r = 0,
                 rx = 0,
                 ry = 0
                ):
        self.bg = keycap_color
        self.fg = text_color
        self.ghosted = False
        self.profile = None
        self.text_alignment = None
        self.font_primary = 3
        self.font_secondary = 3
        self.r = r
        self.rx = rx
        self.ry = ry

    def update(self, obj):
        if 'c' in obj:
            self.bg = str(obj['c'])
        if 't' in obj:
            self.fg = str(obj['t'])
        if 'g' in obj:
            self.ghosted = bool(obj['g'])
        if 'a' in obj:
            self.text_alignment = int(obj['a'])
        if 'f' in obj:
            self.font_primary = int(obj['f'])
        if 'f2' in obj:
            self.font_secondary = int(obj['f2'])
        if 'p' in obj:
            self.profile = str(obj['p'])
        if 'r' in obj:
            self.r = float(obj['r'])
        if 'rx' in obj:
            self.rx = float(obj['rx'])
        if 'ry' in obj:
            self.ry = float(obj['ry'])


class KLEKeyboard(object):
    """Docstring for Keyboard. """

    def __init__(self, spacing=19.0):
        """@todo: to be defined1. """
        self.keys = []
        self.col = 0
        self.row = -1
        self.global_props = KbProperties()
        self.cur_x = 0
        self.cur_y = 0
        self.spacing = spacing
        self.metadata = {}

    def get_keys(self):
        return iter(self.keys)

    def reset_pos(self, u_x, u_y):
        self.cur_x = u_x
        self.cur_y = u_y

    def add_row(self):
        self.cur_x = 0
        self.cur_y += 1
        self._col = 0
        self.row += 1

    def add_key(self, x=0, y=0, w=1, h=1, text="", decal=False):
        self.cur_x += x
        self.cur_y += y
        pos_x = self.cur_x
        pos_y = self.cur_y
        key = KLEKey(pos_x, pos_y, w, h, text=text, properties=self.global_props,
                  decal=decal, spacing=self.spacing)
        self.keys.append(key)
        self.cur_x += w
        self.col += 1

    def addFatKey(self, w=1, h=1, x=1, y=0, w2=1, h2=1, x2=1, y2=0):
        pass

    @staticmethod
    def from_file(file_name, spacing=19.0):
        with open(file_name) as json_file:
            json_layout = json.loads(json_file.read())
        return KLEKeyboard.from_json(json_layout, spacing=spacing)

    @staticmethod
    def from_json(json_layout, spacing=19.0):
        keyboard = KLEKeyboard(spacing=spacing)
        props = KeyProperties()
        pos = 0
        for row in json_layout:
            if isinstance(row, dict):
                # Copy all the fields to the metadata
                for key in row:
                    keyboard.metadata[key] = row[key]
                continue
            for key in row:
                if type(key) == str:
                    x = props.x
                    y = props.y
                    w = props.w
                    h = props.h
                    d = props.decal
                    key_text = key
                    keyboard.add_key(x, y, w, h, text=key_text, decal=d)
                    # reset properties for next key
                    props = KeyProperties()
                    pos += 1
                elif type(key) == dict:
                    props = KeyProperties.from_json(key)

                    keyboard.global_props.update(key)

                    if 'rx' in key:
                        keyboard.cur_x = 0
                    if 'ry' in key:
                        keyboard.cur_y = 0
            keyboard.add_row()
        return keyboard

    def to_json(self):
        result = []

        if self.metadata != {}:
            result.append(copy.copy(self.metadata))



        last_key = None
        for key in self.get_keys():
            # TODO: make output cleaner.
            # TODO: handle all fields correctly
            # if last_key:
            #     last_properties = key.get_properties()
            # last_key = key
            props = key.get_properties()
            row = [props.to_json(), key.get_legend_str()]
            result.append(row)

        return result

    def mirror(self, axis='x'):
        """
        Mirror the keys in the layout

        Args:
            axis: the axis on which to mirror, either 'x' or 'y'
        """
        if axis == 'x':
            mirror = Point(-1, 1)
        elif axis == 'y':
            mirror = Point(1, -1)
        # elif isinstance(axis, Point):
        #     mirror = axis

        for key in self.get_keys():
            old_center = key.get_center()
            key.set_center(mirror.x * old_center.x, mirror.y * old_center.y)
            key.set_angle(-key.r)
