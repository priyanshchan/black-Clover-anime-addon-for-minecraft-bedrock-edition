"""Block models: the Grimoire Altar."""
from __future__ import annotations

import math

import numpy as np

from .. import tex
from ..geo import Geo
from ..tex import P, rgb
from .items import _emblem_layer, page_decal


def _gold_rim(a, ctx):
    h, w = a.shape[:2]
    a[0, :, :3] = rgb('f0c24a')[:3]
    if h > 2:
        a[1, :, :3] = rgb('a8701c')[:3]
    return a


def _clover_panel(a, ctx):
    h, w = a.shape[:2]
    # recessed frame
    a[1, 1:-1, :3] *= 0.6
    a[-2, 1:-1, :3] *= 0.6
    a[1:-1, 1, :3] *= 0.6
    a[1:-1, -2, :3] *= 0.6
    lay = _emblem_layer(h, w, rgb('6fe0a0'), 4, scale=0.3)
    m = lay[..., 3] > 80
    a[m, :3] = lay[m, :3]
    a[m, 3] = 255
    return a


def altar_geo():
    g = Geo('geometry.bc.grimoire_altar', res=2, atlas_width=128, visible=(2, 2, (0, 0.5, 0)))
    g.bone('altar', pivot=(0, 0, 0))
    brick = tex.Stone(P['deepslate'], brick=4)
    stone = tex.Stone(P['stone'], brick=3)
    carved = tex.Painted(tex.Material(P['deepslate'], noise=0.1), {'north': _clover_panel, 'south': _clover_panel,
                                                                  'east': _clover_panel, 'west': _clover_panel})
    gold = tex.Metal(P['gold'])
    g.cube('altar', (-8, 0, -8), (16, 2, 16), tex.Painted(brick, {'north': _gold_rim, 'south': _gold_rim, 'east': _gold_rim, 'west': _gold_rim}))
    g.cube('altar', (-6.5, 2, -6.5), (13, 2, 13), stone)
    g.cube('altar', (-4, 4, -4), (8, 7, 8), carved)
    g.cube('altar', (-5, 11, -5), (10, 1.5, 10), tex.Painted(stone, {'north': _gold_rim, 'south': _gold_rim, 'east': _gold_rim, 'west': _gold_rim}))
    # slanted lectern top with an open grimoire
    g.bone('top', 'altar', (0, 12.5, 0), rotation=[-22.5, 0, 0])
    g.cube('top', (-5.5, 12.5, -4.5), (11, 1.2, 9), tex.Material(P['wood'], noise=0.1))
    cover = tex.Material(tex.ramp('0b2412', '133a1c', '1d5427', '2a7234'), noise=0.12)
    paper = tex.Material(P['paper'], noise=0.05, edge=0.9, highlight=False)
    g.cube('top', (-5.0, 13.7, -3.9), (10, 0.4, 7.8), cover)
    g.cube('top', (-4.7, 14.1, -3.6), (4.5, 0.6, 7.2), tex.PerFace(paper, up=tex.Painted(paper, {'up': page_decal('wind')})))
    g.cube('top', (0.2, 14.1, -3.6), (4.5, 0.6, 7.2), tex.PerFace(paper, up=tex.Painted(paper, {'up': page_decal('light')})))
    # mana crystal clusters on the corners
    crystal = tex.Crystal(tex.ramp('3a1a6e', '5a2ca6', '7c4ad8', 'a57cf0', 'd2bcff', 'f4ecff'), alpha=210)
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * 5.3, sz * 5.3
            g.box('altar', (x, 6.0, z), (1.8, 4.6, 1.8), crystal, rotation=[sz * 14, 45, -sx * 14], pivot=(x, 4, z), mi='crystal')
            g.box('altar', (x - sx * 1.1, 5.0, z + sz * 0.3), (1.2, 2.4, 1.2), crystal, rotation=[sz * 30, 20, -sx * 35], pivot=(x, 4, z), mi='crystal')
    # gold trims at the pillar corners
    for sx in (-1, 1):
        for sz in (-1, 1):
            g.box('altar', (sx * 4, 7.5, sz * 4), (1.0, 7, 1.0), gold)
    return g
