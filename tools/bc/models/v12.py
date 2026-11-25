"""v1.2.0 models: Wyvern Eggs, the tamed wyvern's animations, the kingdom soldiers (the Diamond Legionnaire, the Spade
Zealot, the Heart Guardian) and the new icons. All designs are original."""
from __future__ import annotations

import math

import numpy as np

from .. import tex
from ..geo import Geo
from ..tex import P, rgb
from .sea import SKIN, _face, _humanoid_bones, humanoid_animations
from .v11 import WYVERN_LOOK, _icon, _scale_pattern, wyvern_animations


def _r(*h):
    return tex.ramp(*h)


# ======================================================================================
# Wyvern Eggs
# ======================================================================================
def _speckles(color):
    c = np.array(rgb(color)[:3], np.float32)

    def fn(a, ctx):
        h, w = a.shape[:2]
        rng = np.random.default_rng(ctx.seed + 9)
        for _ in range(max(2, (h * w) // 30)):
            y, x = int(rng.integers(0, h)), int(rng.integers(0, w))
            a[y, x, :3] = c
        return a
    return fn


def egg_geo(kind):
    L = WYVERN_LOOK[kind]
    g = Geo('geometry.bc.wyvern_egg', res=4, atlas_width=64, visible=(1, 1, (0, 0.4, 0)), seed=1201)
    shell = tex.Painted(tex.Metal(L['scale'], sheen=0.35, noise=0.1), {'*': _speckles(L['glow'])})
    g.bone('root', pivot=(0, 0, 0))
    g.bone('egg', 'root', (0, 0, 0))
    for y, s in ((0, 4), (1, 6), (3, 7), (6, 7), (8.5, 6), (10.5, 4.4), (12, 2.6)):
        g.box('egg', (0, y + 1.25, 0), (s, 2.5, s), shell)
    g.box('egg', (0, 7, 0), (7.4, 0.6, 7.4), tex.Flat(L['glow']))
    return g


def egg_animations():
    return {'animation.bc.wyvern_egg.idle': {'loop': True, 'bones': {
        'egg': {'rotation': [0, 0, "math.sin(q.life_time * 400.0) * math.max(0.0, math.sin(q.life_time * 40.0) - 0.7) * 30.0"],
                'scale': ['1.0 + math.sin(q.life_time * 90.0) * 0.02'] * 3},
    }}}


# ======================================================================================
# the tamed wyvern: the wild wyvern's moves, scaled by its stage, and a seat for its rider
# ======================================================================================
def tamed_animations():
    a = {k.replace('animation.bc.wyvern.', 'animation.bc.tamed_wyvern.'): v for k, v in wyvern_animations().items()}
    a['animation.bc.tamed_wyvern.grow'] = {'loop': True, 'bones': {'root': {'scale': ["0.45 + q.property('bc:stage') * 0.33"] * 3}}}
    return a


# ======================================================================================
# the kingdom soldiers
# ======================================================================================
def _visor(color):
    c = np.array(rgb(color)[:3], np.float32)

    def fn(a, ctx):
        h, w = a.shape[:2]
        y = int(h * 0.42)
        a[y:y + max(1, h // 7), int(w * 0.15):int(w * 0.85), :3] = np.array(rgb('0a0a10')[:3])
        a[y:y + max(1, h // 7), int(w * 0.3):int(w * 0.42), :3] = c
        a[y:y + max(1, h // 7), int(w * 0.58):int(w * 0.7), :3] = c
        return a
    return fn


def legionnaire_geo():
    """The Diamond Legionnaire: crystal-studded plate, a crested helm, a crystal-headed spear."""
    g = Geo('geometry.bc.diamond_legionnaire', res=2, atlas_width=128, visible=(2, 3, (0, 1.2, 0)), seed=1202)
    _humanoid_bones(g)
    plate = tex.Metal(_r('3a4250', '545e70', '707c90', '909cb0', 'b4c0d4'), sheen=0.5)
    under = tex.Cloth(_r('101a2a', '182640', '223456', '2c446c'))
    crystal = tex.Crystal(_r('2a7a9a', '4ab0d0', '8ae0f8', 'd0f8ff'), alpha=255)
    helm = tex.PerFace(plate, north=tex.Painted(plate, {'north': _visor('8ae0f8')}))
    g.cube('head', (-4.2, 24, -4.2), (8.4, 8.4, 8.4), helm)
    for k, h in enumerate((3.4, 4.6, 3.4)):
        g.box('head', (0, 33.2 + h / 2 - 1, -2.4 + k * 2.4), (1.2, h, 1.8), crystal)   # crest of crystal
    g.cube('body', (-4, 12, -2), (8, 12, 4), under)
    g.cube('body', (-4.6, 14, -2.6), (9.2, 10.2, 5.2), plate)
    g.box('body', (0, 19.5, -2.9), (2.4, 3.4, 0.6), crystal, rotation=[0, 0, 45], pivot=(0, 19.5, -2.9))
    g.cube('body', (-4.8, 10.5, -2.8), (9.6, 4, 5.6), plate)                           # tassets
    for side, x0, sx in (('rightArm', -8, -1), ('leftArm', 4, 1)):
        g.cube(side, (x0, 12, -2), (4, 12, 4), under)
        g.cube(side, (x0 - 0.3, 19, -2.6), (4.6, 5.4, 5.2), plate)                     # pauldron
        g.box(side, (x0 + 2 + sx * 1.6, 25.4, 0), (1.4, 3.2, 1.4), crystal, rotation=[0, 0, sx * -25], pivot=(x0 + 2, 23.5, 0))
        g.cube(side, (x0 - 0.2, 12, -2.2), (4.4, 4, 4.4), plate)
    for side, x0 in (('rightLeg', -3.9), ('leftLeg', -0.1)):
        g.cube(side, (x0, 0, -2), (4, 12, 4), under)
        g.cube(side, (x0 - 0.2, 0, -2.3), (4.4, 6, 4.6), plate)
    # a crystal-headed spear
    g.cube('rightArm', (-6.6, -4, -0.6), (1.2, 26, 1.2), tex.Wood(P['wood']))
    g.box('rightArm', (-6, 23.5, 0), (1.6, 4.5, 1.6), crystal, rotation=[0, 45, 0], pivot=(-6, 23.5, 0))
    return g


def zealot_geo():
    """The Spade Zealot: a hooded black robe with violet trim, a bone mask and a staff crowned with a dark orb."""
    g = Geo('geometry.bc.spade_zealot', res=2, atlas_width=128, visible=(2, 3, (0, 1.2, 0)), seed=1203)
    _humanoid_bones(g)
    g.bone('orb', 'rightArm', (-6, 26, 0))
    robe = tex.Cloth(_r('08060c', '110c18', '1a1424', '241c32', '302640'), folds=0.24)
    trim = tex.Cloth(_r('2a0e3a', '3e1658', '561e78', '6e2a96'))
    mask = tex.Material(P['bone'], noise=0.08)
    orb = tex.Energy(_r('12021e', '2a0640', '4a1070', 'a040ff', 'e0b0ff'), alpha=255)

    def masked(a, ctx):
        h, w = a.shape[:2]
        a[int(h * 0.38):int(h * 0.5), int(w * 0.2):int(w * 0.38), :3] = rgb('a040ff')[:3]
        a[int(h * 0.38):int(h * 0.5), int(w * 0.62):int(w * 0.8), :3] = rgb('a040ff')[:3]
        return a
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.PerFace(robe, north=tex.Painted(mask, {'north': masked})))
    g.cube('head', (-4.6, 26, -4.4), (9.2, 7.4, 9.2), robe)                              # hood
    g.box('head', (0, 34.2, 2.5), (3, 3, 4), robe, rotation=[-30, 0, 0], pivot=(0, 33, 1))
    g.cube('body', (-4, 12, -2), (8, 12, 4), robe)
    g.cube('body', (-4.6, 1, -2.6), (9.2, 12, 5.2), robe)                                # robe skirt
    g.cube('body', (-4.7, 1, -2.7), (9.4, 1.2, 5.4), trim)
    g.cube('body', (-0.8, 12, -2.4), (1.6, 12, 0.4), trim)
    for side, x0 in (('rightArm', -8), ('leftArm', 4)):
        g.cube(side, (x0, 12, -2), (4, 12, 4), robe)
        g.cube(side, (x0 - 0.2, 12, -2.2), (4.4, 2, 4.4), trim)
    for side, x0 in (('rightLeg', -3.9), ('leftLeg', -0.1)):
        g.cube(side, (x0, 0, -2), (4, 12, 4), tex.Cloth(_r('08060c', '110c18', '1a1424')))
    g.cube('rightArm', (-6.6, -2, -0.6), (1.2, 26, 1.2), tex.Wood(_r('120c08', '1e1410', '2a1e16')))
    g.box('orb', (-6, 26, 0), (3, 3, 3), orb, rotation=[45, 45, 0], pivot=(-6, 26, 0))
    return g


def guardian_geo():
    """The Heart Guardian: a spirit warden in leaf-green and white, a crown of pink blossoms and a living staff."""
    g = Geo('geometry.bc.heart_guardian', res=2, atlas_width=128, visible=(2, 3, (0, 1.2, 0)), seed=1204)
    _humanoid_bones(g)
    skin = tex.Material(SKIN, noise=0.08, edge=0.85)
    robe = tex.Cloth(_r('b8c8b0', 'ccdcc4', 'e0eed8', 'f0f8ec', 'ffffff'), folds=0.2)
    leaf = tex.Material(_r('1e4a1c', '2a6428', '387e34', '4a9a44'), noise=0.25, cell=1.2)
    bloom = tex.Material(_r('c04a7a', 'e06a9a', 'f8a0c0', 'ffd0e0'), noise=0.15)
    wood = tex.Wood(_r('3a2414', '54341c', '6e4626'))
    glow = tex.Energy(_r('4a1030', '9a2a60', 'ff70b0', 'ffd0e8'), alpha=255)
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(skin, {'north': _face()}))
    g.cube('head', (-4.3, 30, -4.3), (8.6, 2.6, 8.6), leaf)
    for k in range(6):
        a = k / 6 * math.tau
        g.box('head', (math.cos(a) * 4.2, 32.6, math.sin(a) * 4.2), (1.8, 1.6, 1.8), bloom)
    g.cube('body', (-4, 12, -2), (8, 12, 4), robe)
    g.cube('body', (-4.6, 2, -2.6), (9.2, 11, 5.2), robe)
    g.cube('body', (-4.8, 18, -2.8), (9.6, 6, 5.6), leaf)                                # leaf mantle
    for side, x0 in (('rightArm', -8), ('leftArm', 4)):
        g.cube(side, (x0, 12, -2), (4, 12, 4), robe)
        g.cube(side, (x0 + 0.2, 12, -1.8), (3.6, 2, 3.6), skin)
    for side, x0 in (('rightLeg', -3.9), ('leftLeg', -0.1)):
        g.cube(side, (x0, 0, -2), (4, 12, 4), tex.Cloth(_r('6a7a62', '7e8e76', '92a28a')))
    g.cube('rightArm', (-6.6, -2, -0.6), (1.2, 25, 1.2), wood)
    g.box('rightArm', (-6, 23.8, 0), (2.4, 2.4, 2.4), glow, rotation=[45, 0, 45], pivot=(-6, 23.8, 0))
    for k in range(3):
        g.box('rightArm', (-6 + (k - 1) * 1.4, 22.5, 0.2), (0.8, 2.4, 0.8), leaf, rotation=[0, 0, (k - 1) * 30], pivot=(-6, 21.5, 0))
    return g


def soldier_animations(prefix):
    a = humanoid_animations(prefix)
    a[f'animation.bc.{prefix}.cast'] = {'animation_length': 0.8, 'bones': {
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.25': [-120, 10, 10], '0.55': [-90, 0, 0], '0.8': [0, 0, 0]}},
        'body': {'rotation': {'0.0': [0, 0, 0], '0.25': [0, -15, 0], '0.8': [0, 0, 0]}},
    }}
    if prefix == 'spade_zealot':
        a[f'animation.bc.{prefix}.idle']['bones']['orb'] = {'rotation': [0, 'q.life_time * 120.0', 0], 'position': [0, 'math.sin(q.life_time * 120.0) * 0.6', 0]}
    return a


# ======================================================================================
# icons
# ======================================================================================
def v12_icons():
    def egg(col, spot):
        def fn(d, s):
            d.ellipse([8 * s, 4 * s, 24 * s, 29 * s], fill=col)
            d.ellipse([11 * s, 7 * s, 16 * s, 13 * s], fill=tuple(min(255, c + 60) for c in col[:3]) + (255,))
            for x, y in ((12, 18), (19, 12), (17, 23), (21, 19), (14, 25)):
                d.ellipse([(x - 1.2) * s, (y - 1.2) * s, (x + 1.2) * s, (y + 1.2) * s], fill=spot)
        return fn

    def whistle(d, s):
        d.polygon([(5 * s, 14 * s), (22 * s, 10 * s), (27 * s, 13 * s), (27 * s, 18 * s), (22 * s, 21 * s), (5 * s, 18 * s)], fill=(226, 216, 190, 255))
        d.ellipse([21 * s, 11 * s, 27 * s, 20 * s], fill=(200, 188, 160, 255))
        d.ellipse([10 * s, 13 * s, 13 * s, 16 * s], fill=(60, 40, 30, 255))
        d.line([(5 * s, 16 * s), (3 * s, 24 * s), (9 * s, 27 * s)], fill=(60, 140, 80, 255), width=int(1.4 * s))

    def saddle(d, s):
        d.polygon([(4 * s, 14 * s), (10 * s, 9 * s), (22 * s, 9 * s), (28 * s, 14 * s), (26 * s, 21 * s), (6 * s, 21 * s)], fill=(120, 72, 40, 255))
        d.rectangle([8 * s, 6 * s, 12 * s, 11 * s], fill=(96, 56, 30, 255))
        d.rectangle([21 * s, 6 * s, 25 * s, 11 * s], fill=(96, 56, 30, 255))
        d.rectangle([6 * s, 19 * s, 26 * s, 22 * s], fill=(170, 40, 40, 255))
        d.line([(9 * s, 21 * s), (9 * s, 28 * s)], fill=(170, 40, 40, 255), width=int(1.2 * s))
        d.rectangle([7 * s, 27 * s, 11 * s, 29 * s], fill=(214, 160, 40, 255))

    def shard(d, s):
        d.polygon([(16 * s, 2 * s), (24 * s, 14 * s), (19 * s, 29 * s), (11 * s, 27 * s), (8 * s, 12 * s)], fill=(74, 176, 208, 255))
        d.polygon([(16 * s, 4 * s), (20 * s, 14 * s), (16 * s, 26 * s)], fill=(200, 245, 255, 255))

    def sigil(d, s):
        # a spade-like sigil of black iron (a generic card-suit shape)
        d.ellipse([7 * s, 11 * s, 17 * s, 21 * s], fill=(40, 30, 54, 255))
        d.ellipse([15 * s, 11 * s, 25 * s, 21 * s], fill=(40, 30, 54, 255))
        d.polygon([(16 * s, 3 * s), (7 * s, 15 * s), (25 * s, 15 * s)], fill=(40, 30, 54, 255))
        d.polygon([(16 * s, 17 * s), (12 * s, 28 * s), (20 * s, 28 * s)], fill=(40, 30, 54, 255))
        d.ellipse([14 * s, 13 * s, 18 * s, 17 * s], fill=(160, 64, 255, 255))

    def bloom(d, s):
        for k in range(5):
            a = k / 5 * math.tau - math.pi / 2
            x, y = 16 + math.cos(a) * 7, 14 + math.sin(a) * 7
            d.ellipse([(x - 5) * s, (y - 5) * s, (x + 5) * s, (y + 5) * s], fill=(240, 120, 170, 255))
        d.ellipse([12 * s, 10 * s, 20 * s, 18 * s], fill=(255, 220, 120, 255))
        d.line([(16 * s, 20 * s), (16 * s, 30 * s)], fill=(60, 140, 60, 255), width=int(1.6 * s))

    def draught(d, s):
        d.ellipse([7 * s, 11 * s, 25 * s, 29 * s], fill=(240, 130, 180, 255))
        d.rectangle([13 * s, 4 * s, 19 * s, 12 * s], fill=(200, 230, 240, 255))
        d.rectangle([12 * s, 2 * s, 20 * s, 5 * s], fill=(150, 100, 50, 255))
        d.ellipse([11 * s, 15 * s, 16 * s, 20 * s], fill=(255, 220, 235, 255))

    def prism(d, s):
        d.polygon([(16 * s, 3 * s), (27 * s, 16 * s), (16 * s, 29 * s), (5 * s, 16 * s)], fill=(90, 190, 230, 255))
        d.polygon([(16 * s, 3 * s), (16 * s, 29 * s), (5 * s, 16 * s)], fill=(150, 225, 250, 255))
        d.line([(5 * s, 16 * s), (27 * s, 16 * s)], fill=(230, 250, 255, 255), width=int(1 * s))

    def brand(d, s):
        d.rectangle([14 * s, 14 * s, 18 * s, 30 * s], fill=(70, 50, 40, 255))
        d.ellipse([6 * s, 2 * s, 26 * s, 18 * s], fill=(40, 34, 48, 255))
        d.ellipse([10 * s, 6 * s, 22 * s, 14 * s], fill=(200, 80, 255, 255))

    def blossom(d, s):
        bloom(d, s)
        d.ellipse([3 * s, 3 * s, 8 * s, 8 * s], fill=(255, 240, 250, 255))
        d.ellipse([24 * s, 4 * s, 28 * s, 8 * s], fill=(255, 240, 250, 255))
    ember, frost, storm = (196, 70, 26, 255), (120, 176, 214, 255), (46, 58, 88, 255)
    return {'wyvern_egg_ember': _icon(egg(ember, (255, 170, 70, 255))), 'wyvern_egg_frost': _icon(egg(frost, (230, 250, 255, 255))),
            'wyvern_egg_storm': _icon(egg(storm, (255, 226, 60, 255))), 'wyvern_whistle': _icon(whistle), 'wyvern_saddle': _icon(saddle),
            'diamond_shard': _icon(shard), 'spade_sigil': _icon(sigil), 'heart_bloom': _icon(bloom), 'spirit_draught': _icon(draught),
            'relic_prism': _icon(prism), 'relic_brand': _icon(brand), 'relic_blossom': _icon(blossom)}
