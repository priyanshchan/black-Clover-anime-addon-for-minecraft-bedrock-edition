"""v1.0.0: the Mana Waygate block (a rune arch with a floating mana crystal) and its icon. Original design."""
from __future__ import annotations

import numpy as np

from .. import tex
from ..geo import Geo
from ..tex import P, rgb


def waygate_geo():
    g = Geo('geometry.bc.waygate', res=2, atlas_width=128, visible=(2, 3, (0, 1, 0)))
    g.bone('gate', pivot=(0, 0, 0))
    g.bone('crystal', 'gate', (0, 14, 0))
    stone = tex.Stone(P['stone'])
    dark = tex.Metal(P['deepslate'])
    rune = tex.Energy(P['water'], alpha=255)
    gold = tex.Metal(P['gold'])
    crystal = tex.Crystal(P['ice'], alpha=230)
    g.cube('gate', (-8, 0, -8), (16, 2, 16), stone)                  # plinth
    g.cube('gate', (-6, 2, -6), (12, 1, 12), dark)                   # step
    g.cube('gate', (-3.5, 3.0, -3.5), (7, 0.3, 7), rune)             # rune pad
    for x in (-7, 5):
        g.cube('gate', (x, 2, -1.5), (2, 24, 3), stone)              # pillars
        g.cube('gate', (x - 0.3, 26, -1.8), (2.6, 2, 3.6), gold)     # capitals
        g.cube('gate', (x + 0.6, 6, -1.7), (0.8, 16, 0.3), rune)     # glowing runes
    g.cube('gate', (-7.5, 28, -2), (15, 2, 4), stone)                # lintel
    g.cube('gate', (-1.5, 26.5, -2.2), (3, 2.5, 0.6), gold)          # keystone
    g.cube('crystal', (-1.4, 11.5, -1.4), (2.8, 5, 2.8), crystal, rotation=(0, 45, 0), pivot=(0, 14, 0))
    g.cube('crystal', (-0.9, 16.3, -0.9), (1.8, 1.6, 1.8), crystal, rotation=(0, 45, 0), pivot=(0, 17, 0))
    g.cube('crystal', (-0.9, 10.1, -0.9), (1.8, 1.6, 1.8), crystal, rotation=(0, 45, 0), pivot=(0, 11, 0))
    return g


def waygate_icon():
    def fn(d, s):
        d.rectangle([4 * s, 27 * s, 28 * s, 30 * s], fill=(97, 101, 111, 255))
        for x in (5, 23):
            d.rectangle([x * s, 6 * s, (x + 4) * s, 27 * s], fill=(119, 124, 135, 255))
            d.line([((x + 2) * s, 10 * s), ((x + 2) * s, 24 * s)], fill=(124, 200, 255, 255), width=int(1.2 * s))
        d.rectangle([4 * s, 3 * s, 28 * s, 7 * s], fill=(119, 124, 135, 255))
        d.rectangle([14 * s, 2 * s, 18 * s, 6 * s], fill=(240, 194, 74, 255))
        d.polygon([(16 * s, 11 * s), (19 * s, 16 * s), (16 * s, 22 * s), (13 * s, 16 * s)], fill=(160, 230, 255, 255))
    a = tex.draw_layer(32, 32, fn, 4)
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    tex.outline(a, rgb('0a0a0f'))
    return a
