"""Abyssal Seas expansion models: ship, raiders, captain, Leviathan, fruit auras, projectiles, bounty board.

All designs are original (no characters, ships or symbols from other works).
"""
from __future__ import annotations

import math

import numpy as np

from .. import tex
from ..data import FRUITS
from ..geo import Geo
from ..tex import P, rgb

DARK_WOOD = tex.ramp('1e130b', '2c1c10', '3b2716', '4c331d', '5e4026', '714d2f')
LIGHT_WOOD = tex.ramp('4a3420', '62462b', '7a5a37', '927044', 'a98651', 'bf9b61')
NAVY = tex.ramp('0a1022', '111a35', '19264a', '23345f', '2f4576')
SKIN = tex.ramp('6b4630', '86583c', 'a06c4a', 'b9825a', 'cf9a6e')
SEA_SCALE = tex.ramp('061a24', '0b2b3a', '114052', '18586b', '237386', '3592a3')
BELLY = tex.ramp('3d5a5a', '557575', '6f9090', '8aabaa', 'a6c6c2')
ROCK = tex.ramp('2c2925', '3d3933', '524c44', '676056', '7e766a', '968d7f')
IRON = tex.ramp('121316', '1d1f24', '2a2d33', '393d45', '4c515b', '636975')


class Planks(tex.Material):
    """Wood planks with seams and nail heads."""

    def __init__(self, r, plank=3, **kw):
        kw.setdefault('noise', 0.09)
        super().__init__(r, **kw)
        self.plank = plank

    def __call__(self, a, ctx):
        super().__call__(a, ctx)
        h, w = ctx.h, ctx.w
        step = max(2, self.plank * ctx.res)
        horizontal = w >= h
        rng = np.random.default_rng(ctx.seed)
        if horizontal:
            for y in range(step - 1, h, step):
                a[y, :, :3] *= 0.62
            for y in range(0, h, step):
                for x in range(int(rng.integers(1, 6)), w, int(rng.integers(8, 14)) * ctx.res // 2 + 4):
                    if y + 1 < h:
                        a[y + 1, x, :3] = rgb('9aa3b1')[:3] * 0.7
        else:
            for x in range(step - 1, w, step):
                a[:, x, :3] *= 0.62
        return a


def _portholes(a, ctx):
    h, w = a.shape[:2]
    if w < 20:
        return a
    cy = int(h * 0.45)
    for cx in range(int(w * 0.18), w - 4, int(w * 0.2)):
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                d = dx * dx + dy * dy
                y, x = cy + dy, cx + dx
                if 0 <= y < h and 0 <= x < w:
                    if d <= 4:
                        a[y, x, :3] = rgb('0d1218')[:3]
                    elif d <= 10:
                        a[y, x, :3] = rgb('c9a24a')[:3]
    return a


def _sail_emblem(a, ctx):
    """Original sail mark: a four-leaf clover over a crossed anchor."""
    h, w = a.shape[:2]

    def fn(d, s):
        cx, cy = w * s / 2, h * s * 0.48
        r = min(w, h) * s * 0.26
        col = (40, 32, 28, 255)
        # anchor
        d.line([(cx, cy - r * 0.9), (cx, cy + r * 1.1)], fill=col, width=int(max(1, r * 0.16)))
        d.arc([cx - r * 0.9, cy + r * 0.1, cx + r * 0.9, cy + r * 1.3], 20, 160, fill=col, width=int(max(1, r * 0.16)))
        d.line([(cx - r * 0.5, cy - r * 0.45), (cx + r * 0.5, cy - r * 0.45)], fill=col, width=int(max(1, r * 0.14)))
        tex.clover_shape(d, cx, cy - r * 0.55, r * 0.55, 4, (30, 110, 52, 255), stem=False)
    lay = tex.draw_layer(h, w, fn, 4)
    lay[..., 3] = np.where(lay[..., 3] > 100, 255, 0)
    tex.alpha_over(a, lay)
    # patch seams
    for x in range(0, w, max(4, w // 5)):
        a[:, x, :3] *= 0.9
    return a


def _flag(a, ctx):
    h, w = a.shape[:2]
    a[:] = rgb('101014')

    def fn(d, s):
        cx, cy = w * s / 2, h * s / 2
        r = min(w, h) * s * 0.32
        d.line([(cx - r * 1.2, cy + r), (cx + r * 1.2, cy - r)], fill=(230, 230, 220, 255), width=int(max(1, s * 1.2)))
        d.line([(cx - r * 1.2, cy - r), (cx + r * 1.2, cy + r)], fill=(230, 230, 220, 255), width=int(max(1, s * 1.2)))
        tex.clover_shape(d, cx, cy, r * 0.7, 4, (235, 235, 225, 255), stem=False)
    lay = tex.draw_layer(h, w, fn, 4)
    lay[..., 3] = np.where(lay[..., 3] > 100, 255, 0)
    tex.alpha_over(a, lay)
    a[..., 3] = 255
    return a


# ======================================================================================
# sailing ship
# ======================================================================================
def ship_geo():
    g = Geo('geometry.bc.sail_ship', res=2, atlas_width=512, visible=(8, 6, (0, 2, 0)))
    hull = tex.Painted(Planks(DARK_WOOD, plank=3), {'east': _portholes, 'west': _portholes})
    hull_plain = Planks(DARK_WOOD, plank=3)
    deck = Planks(LIGHT_WOOD, plank=2)
    trim = tex.Metal(P['gold'])
    iron = tex.Metal(IRON, sheen=0.3)
    cloth = tex.Cloth(P['white_cloth'], folds=0.12)
    sail = tex.Painted(cloth, {'north': _sail_emblem, 'south': _sail_emblem})
    rope = tex.Material(tex.ramp('5a4630', '7a6040', '977a52'), noise=0.1)
    lamp = tex.Flat('ffd36a', alpha=130)

    g.bone('root', pivot=(0, 0, 0), locators={'helm': [0, 18, 9], 'bow': [0, 12, -32]})
    g.bone('hull', 'root', (0, 0, 0))
    # keel & sides
    g.box('hull', (0, 1.5, 0), (14, 3, 38), hull_plain)
    for sx in (-1, 1):
        g.box('hull', (sx * 7.0, 5.0, 0), (2, 7, 38), hull)
        g.box('hull', (sx * 8.0, 10.0, -1), (2, 5, 40), hull_plain)
        g.box('hull', (sx * 8.0, 12.9, -1), (2.6, 0.8, 40.4), trim)                       # gold gunwale
        # bow boards angled toward the stem
        g.box('hull', (sx * 4.0, 7.5, -24.5), (2, 11, 12.1), hull_plain, rotation=[0, sx * 41.6, 0], pivot=(sx * 4.0, 7.5, -24.5))
        g.box('hull', (sx * 10.2, 8.5, -8), (3.6, 2.2, 2.2), iron)                        # cannons
        g.box('hull', (sx * 10.2, 8.5, 6), (3.6, 2.2, 2.2), iron)
    g.box('hull', (0, 3.5, -24), (10, 5, 9), hull_plain)
    g.box('hull', (0, 5.0, -28.5), (4, 6, 3), hull_plain)
    # stern & aft castle
    g.box('hull', (0, 8.5, 20), (18, 15, 2), tex.Painted(hull_plain, {'south': _portholes}))
    g.box('hull', (0, 14.8, 14.5), (17, 4.5, 9), hull_plain)
    g.box('hull', (0, 17.2, 14.5), (17.6, 0.6, 9.6), deck)
    # deck
    g.box('hull', (0, 11.6, -3), (14, 1, 34), deck)
    # railings
    for sx in (-1, 1):
        for z in range(-18, 10, 6):
            g.box('hull', (sx * 8.0, 14.5, z), (1, 2.6, 1), hull_plain)
        g.box('hull', (sx * 8.0, 16.0, -4.5), (1.2, 0.8, 28), trim)
        g.box('hull', (sx * 8.0, 19.0, 14.5), (1.2, 0.8, 9.6), trim)
    # lanterns
    for sx in (-1, 1):
        g.box('hull', (sx * 8.2, 20.5, 19), (1.8, 2.2, 1.8), lamp)
    # bowsprit + jib
    g.box('hull', (0, 13.5, -33), (1.6, 1.6, 15), hull_plain, rotation=[-18, 0, 0], pivot=(0, 12.5, -27))
    g.bone('jib', 'root', (0, 14, -34))
    g.cube('jib', (-0.25, 14, -34), (0.5, 29, 9), cloth, rotation=[-43, 0, 0], pivot=(0, 14, -34))
    # mast, yards, crow's nest
    g.bone('mast', 'root', (0, 12, -4))
    g.box('mast', (0, 36, -4), (2.4, 50, 2.4), hull_plain)
    g.box('mast', (0, 50, -4), (28, 1.2, 1.2), hull_plain)
    g.box('mast', (0, 30, -4), (26, 1.2, 1.2), hull_plain)
    g.box('mast', (0, 59.5, -4), (7, 3, 7), hull_plain)
    for sx in (-1, 1):                                                                     # rigging
        g.box('mast', (sx * 7, 32, 2), (0.4, 40, 0.4), rope, rotation=[0, 0, sx * 12], pivot=(sx * 7, 32, 2))
    # sails
    g.bone('sail', 'mast', (0, 50, -4))
    g.cube('sail', (-12.5, 30.6, -5.6), (25, 19, 1.4), sail)
    g.bone('topsail', 'mast', (0, 58, -4))
    g.cube('topsail', (-8, 51, -5.1), (16, 7, 1.0), cloth)
    # flag
    g.bone('flag', 'mast', (1.2, 64, -4))
    g.box('mast', (0, 63, -4), (0.8, 4, 0.8), hull_plain)
    g.cube('flag', (1.2, 60.5, -4.1), (9, 5.5, 0.2), tex.PerFace(_flag))
    # helm wheel
    g.box('hull', (0, 19.5, 11.2), (1.2, 3.5, 1.2), hull_plain)
    g.bone('wheel', 'root', (0, 21.5, 10.4))
    for ang in (0, 45, 90, 135):
        g.box('wheel', (0, 21.5, 10.4), (7, 0.6, 0.6), deck, rotation=[0, 0, ang], pivot=(0, 21.5, 10.4))
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        cx, cy = math.cos(a) * 3.0, 21.5 + math.sin(a) * 3.0
        g.box('wheel', (cx, cy, 10.4), (2.4, 0.8, 0.8), trim, rotation=[0, 0, k * 45 + 22.5 + 90], pivot=(cx, cy, 10.4))
    return g


def ship_animations():
    sway = 'math.sin(q.life_time * 70.0)'
    return {
        'animation.bc.sail_ship.sail': {
            'loop': True,
            'bones': {
                'hull': {'rotation': [f'math.sin(q.life_time * 55.0) * 1.2', 0, f'{sway} * 1.8']},
                'mast': {'rotation': [f'math.sin(q.life_time * 55.0) * 1.2', 0, f'{sway} * 1.8']},
                'jib': {'rotation': [f'math.sin(q.life_time * 55.0) * 1.2', 0, f'{sway} * 1.8']},
                'sail': {'rotation': [f'-math.clamp(q.modified_move_speed * 12.0, 0.0, 10.0) + math.sin(q.life_time * 90.0) * 1.5', 0, 0],
                         'scale': [1, 1, '1.0 + math.clamp(q.modified_move_speed * 2.5, 0.0, 1.6)']},
                'topsail': {'rotation': ['math.sin(q.life_time * 100.0) * 2.0', 0, 0]},
                'flag': {'rotation': [0, 'math.sin(q.life_time * 320.0) * 14.0', 0]},
                'wheel': {'rotation': [0, 0, 'math.sin(q.life_time * 40.0) * 30.0']},
            },
        },
    }


# ======================================================================================
# humanoid helpers
# ======================================================================================
def _humanoid_bones(g):
    g.bone('root', pivot=(0, 0, 0))
    g.bone('waist', 'root', (0, 12, 0))
    g.bone('body', 'waist', (0, 24, 0))
    g.bone('head', 'body', (0, 24, 0))
    g.bone('rightArm', 'body', (-5, 22, 0))
    g.bone('leftArm', 'body', (5, 22, 0))
    g.bone('rightLeg', 'root', (-1.9, 12, 0))
    g.bone('leftLeg', 'root', (1.9, 12, 0))


def _face(eyepatch=False, beard=False, scar=False):
    def fn(a, ctx):
        h, w = a.shape[:2]
        ey = int(h * 0.48)
        # eyes
        for ex in (int(w * 0.19), int(w * 0.62)):
            a[ey:ey + 2, ex:ex + int(w * 0.18), :3] = rgb('f0ece4')[:3]
            a[ey:ey + 2, ex + int(w * 0.09):ex + int(w * 0.18), :3] = rgb('2a1e14')[:3]
        a[ey - 2, int(w * 0.16):int(w * 0.4), :3] *= 0.55
        a[ey - 2, int(w * 0.6):int(w * 0.84), :3] *= 0.55
        if eyepatch:
            a[ey - 1:ey + 3, int(w * 0.14):int(w * 0.42), :3] = rgb('0c0c0e')[:3]
            for x in range(w):
                y = int(ey - 3 - (x - w * 0.28) * 0.35)
                if 0 <= y < h:
                    a[y, x, :3] = rgb('0c0c0e')[:3]
        a[int(h * 0.78), int(w * 0.35):int(w * 0.65), :3] = rgb('4a2a1e')[:3]
        if beard:
            a[int(h * 0.7):, :, :3] = tex.quantize(tex.ramp('2a1a0e', '3b2614', '4e331c'), np.full((h - int(h * 0.7), w), 0.5) + tex.white_noise(h - int(h * 0.7), w, 3) * 0.3)[..., :3]
            a[int(h * 0.78), int(w * 0.35):int(w * 0.65), :3] = rgb('1a0e08')[:3]
        else:
            rng = np.random.default_rng(ctx.seed)
            for _ in range(w):
                y, x = int(rng.integers(int(h * 0.7), h)), int(rng.integers(0, w))
                a[y, x, :3] *= 0.75
        if scar:
            for i in range(5):
                y, x = ey - 3 + i, int(w * 0.7) + i // 2
                if 0 <= y < h and 0 <= x < w:
                    a[y, x, :3] = rgb('8a3a30')[:3]
        return a
    return fn


def _stripes(a, ctx):
    h, w = a.shape[:2]
    band = max(2, ctx.res * 1)
    for y in range(h):
        if (y // band) % 2 == 0:
            a[y, :, :3] = a[y, :, :3] * 0.25 + rgb('1d2f5a')[:3] * 0.75
    return a


def _vest_front(a, ctx):
    h, w = a.shape[:2]
    cx = w // 2
    a[:, cx - max(2, w // 6):cx + max(2, w // 6), 3] = 0
    return a


def _dots(a, ctx):
    h, w = a.shape[:2]
    for y in range(1, h, 3):
        for x in range((y // 3) % 2 * 2 + 1, w, 4):
            a[y, x, :3] = rgb('f0e8dc')[:3]
    return a


def _coat_trim(a, ctx):
    h, w = a.shape[:2]
    a[-2:, :, :3] = rgb('d39a2c')[:3]
    if ctx.face == 'north':
        cx = w // 2
        a[:, cx - 1:cx + 1, :3] = rgb('d39a2c')[:3]
        for y in range(2, h - 2, max(3, h // 5)):
            a[y, cx - 3:cx - 1, :3] = rgb('f0c24a')[:3]
            a[y, cx + 1:cx + 3, :3] = rgb('f0c24a')[:3]
    return a


def _cutlass(g, bone):
    steel = tex.Metal(P['steel'], sheen=0.4)
    gold = tex.Metal(P['gold'])
    g.bone('sword', bone, (-6, 12.5, 0))
    g.box('sword', (-6, 12.0, 0.5), (1.4, 1.4, 3.2), tex.Material(P['leather']))
    g.box('sword', (-6, 12.0, -1.4), (1.6, 3.4, 0.8), gold)                         # guard
    g.cube('sword', (-6.35, 11.3, -12.5), (0.7, 1.6, 11), steel)                     # blade (points forward)
    g.cube('sword', (-6.35, 11.6, -14.2), (0.7, 1.1, 1.8), steel, rotation=[-25, 0, 0], pivot=(-6, 12, -12.5))


def raider_geo():
    g = Geo('geometry.bc.sea_raider', res=2, atlas_width=128, visible=(2, 3, (0, 1.1, 0)))
    _humanoid_bones(g)
    skin = tex.Material(SKIN, noise=0.08, edge=0.85)
    shirt = tex.Painted(tex.Cloth(P['white_cloth'], folds=0.1), {'*': _stripes})
    vest = tex.Painted(tex.Material(P['leather'], noise=0.12), {'north': _vest_front})
    sash = tex.Cloth(P['red_cloth'])
    pants = tex.Cloth(tex.ramp('1a1610', '262018', '332a20', '40362a'))
    boots = tex.Material(tex.ramp('120c08', '1e1510', '2a1e16', '382a1e'), noise=0.1)
    bandana = tex.Painted(tex.Cloth(P['red_cloth'], folds=0.05), {'*': _dots})
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(skin, {'north': _face(eyepatch=True)}))
    g.cube('head', (-4.35, 28.6, -4.35), (8.7, 3.8, 8.7), bandana)
    g.cube('head', (-1.2, 26.6, 4.2), (2.4, 2.8, 2.2), bandana, rotation=[-30, 0, 0], pivot=(0, 28, 4.2))
    g.cube('body', (-4, 12, -2), (8, 12, 4), shirt)
    g.cube('body', (-4.3, 15, -2.3), (8.6, 9.2, 4.6), vest)
    g.cube('body', (-4.45, 12, -2.45), (8.9, 2.4, 4.9), sash)
    g.cube('body', (-4.6, 11.0, -2.6), (2.2, 3.5, 1.0), sash, rotation=[0, 0, 15], pivot=(-3.5, 13, -2.4))
    for side, x0 in (('rightArm', -8), ('leftArm', 4)):
        g.cube(side, (x0, 18, -2), (4, 6, 4), shirt)
        g.cube(side, (x0, 12, -2), (4, 6, 4), skin)
    g.cube('rightLeg', (-3.9, 3, -2), (4, 9, 4), pants)
    g.cube('leftLeg', (-0.1, 3, -2), (4, 9, 4), pants)
    g.cube('rightLeg', (-4.1, 0, -2.3), (4.4, 3.4, 4.6), boots)
    g.cube('leftLeg', (-0.3, 0, -2.3), (4.4, 3.4, 4.6), boots)
    _cutlass(g, 'rightArm')
    return g


def captain_geo():
    g = Geo('geometry.bc.raider_captain', res=2, atlas_width=128, visible=(2, 3, (0, 1.2, 0)))
    _humanoid_bones(g)
    g.bone('coattails', 'body', (0, 13, 2))
    skin = tex.Material(SKIN, noise=0.08, edge=0.85)
    coat = tex.Painted(tex.Cloth(tex.ramp('2a0507', '470a10', '6a1018', '8f1a22', 'a52a28'), folds=0.15), {'north': _coat_trim, 'south': _coat_trim})
    shirt = tex.Cloth(P['white_cloth'], folds=0.08)
    hat = tex.Material(tex.ramp('08080a', '121216', '1c1c22', '26262e'), noise=0.08)
    gold = tex.Metal(P['gold'])
    pants = tex.Cloth(tex.ramp('0e0e14', '17171f', '20202b', '2a2a38'))
    boots = tex.Material(tex.ramp('0a0806', '15100c', '211812', '2e2219'), noise=0.1)
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(skin, {'north': _face(beard=True, scar=True)}))
    # tricorn hat: crown + three upturned brims
    g.cube('head', (-4.4, 31.2, -4.4), (8.8, 3.4, 8.8), hat)
    g.cube('head', (-6.5, 31.0, -6.5), (13, 0.8, 13), hat)
    for k, ang in enumerate((0, 120, 240)):
        r = math.radians(ang)
        cx, cz = math.sin(r) * 5.2, -math.cos(r) * 5.2
        g.box('head', (cx, 33.0, cz), (8.5, 3.2, 0.8), tex.Painted(hat, {'*': lambda a, c: _gold_edge(a)}), rotation=[0, -ang, 0], pivot=(cx, 33.0, cz))
    g.cube('head', (-1.2, 33.4, -6.0), (2.4, 2.4, 0.6), gold)                                 # hat badge
    g.cube('body', (-4, 12, -2), (8, 12, 4), shirt)
    g.cube('body', (-4.4, 11.5, -2.4), (8.8, 12.8, 4.8), coat)
    g.cube('body', (-2, 21.5, -2.7), (4, 2.5, 0.6), shirt)                                   # cravat
    g.cube('body', (-4.6, 12.6, -2.6), (9.2, 1.6, 5.2), tex.Material(P['leather']))           # belt
    g.cube('body', (-1, 12.4, -2.9), (2, 2, 0.4), gold)
    g.cube('coattails', (-4.4, 3.5, 1.5), (8.8, 9, 1.0), coat)
    for side, x0 in (('rightArm', -8), ('leftArm', 4)):
        g.cube(side, (x0 - 0.4, 14, -2.4), (4.8, 10, 4.8), coat)
        g.cube(side, (x0 - 0.6, 21.6, -2.6), (5.2, 1.6, 5.2), gold)                          # epaulette
        g.cube(side, (x0 - 0.5, 13.5, -2.5), (5.0, 1.5, 5.0), tex.Material(P['white_cloth']))
        g.cube(side, (x0, 12, -2), (4, 2, 4), skin)
    g.cube('rightLeg', (-3.9, 3, -2), (4, 9, 4), pants)
    g.cube('leftLeg', (-0.1, 3, -2), (4, 9, 4), pants)
    g.cube('rightLeg', (-4.1, 0, -2.3), (4.4, 5.5, 4.6), boots)
    g.cube('leftLeg', (-0.3, 0, -2.3), (4.4, 5.5, 4.6), boots)
    _cutlass(g, 'rightArm')
    return g


def _gold_edge(a):
    a[0, :, :3] = rgb('d39a2c')[:3]
    return a


def humanoid_animations(prefix):
    walk = 'math.cos(q.modified_distance_moved * 38.17) * 38.0 * q.modified_move_speed'
    anims = {
        f'animation.bc.{prefix}.idle': {'loop': True, 'bones': {
            'body': {'rotation': ['math.sin(q.life_time * 90.0) * 1.2', 0, 0]},
            'rightArm': {'rotation': ['-12.0 + math.sin(q.life_time * 90.0) * 2.0', 0, 4]},
            'leftArm': {'rotation': ['math.sin(q.life_time * 90.0) * -2.0', 0, -4]},
        }},
        f'animation.bc.{prefix}.walk': {'loop': True, 'bones': {
            'rightLeg': {'rotation': [walk, 0, 0]},
            'leftLeg': {'rotation': [f'-({walk})', 0, 0]},
            'leftArm': {'rotation': [f'({walk}) * 0.7', 0, 0]},
            'rightArm': {'rotation': [f'-({walk}) * 0.3', 0, 0]},
        }},
        f'animation.bc.{prefix}.look_at_target': {'loop': True, 'bones': {'head': {'rotation': ['q.target_x_rotation', 'q.target_y_rotation', 0]}}},
        f'animation.bc.{prefix}.attack': {'animation_length': 0.45, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.12': [-150, 20, 10], '0.26': [-40, -25, 0], '0.45': [0, 0, 0]}},
            'body': {'rotation': {'0.0': [0, 0, 0], '0.12': [0, 15, 0], '0.26': [0, -20, 0], '0.45': [0, 0, 0]}},
        }},
    }
    if prefix == 'raider_captain':
        anims[f'animation.bc.{prefix}.idle']['bones']['coattails'] = {'rotation': ['6.0 + math.sin(q.life_time * 120.0) * 3.0', 0, 0]}
        anims[f'animation.bc.{prefix}.walk']['bones']['coattails'] = {'rotation': ['math.abs(math.cos(q.modified_distance_moved * 38.17)) * 25.0 * q.modified_move_speed', 0, 0]}
        anims[f'animation.bc.{prefix}.cast'] = {'animation_length': 0.8, 'bones': {
            'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-110, -10, -10], '0.55': [-95, 0, 0], '0.8': [0, 0, 0]}},
            'body': {'rotation': {'0.0': [0, 0, 0], '0.2': [0, -15, 0], '0.8': [0, 0, 0]}},
        }}
    return anims


# ======================================================================================
# the Abyssal Leviathan
# ======================================================================================
def _scales(a, ctx):
    h, w = a.shape[:2]
    for y in range(0, h, 3):
        for x in range((y // 3) % 2 * 2, w, 4):
            if y + 1 < h:
                a[y, x:x + 2, :3] *= 0.7
            if y + 2 < h:
                a[y + 2, x:x + 2, :3] = np.minimum(a[y + 2, x:x + 2, :3] * 1.25, 255)
    return a


def _fin_edge(a, ctx):
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    edge = h - (np.abs(np.sin(xx / max(3, w / 4) * math.pi)) * h * 0.35 + 1)
    a[yy > edge, 3] = 0
    for x in range(0, w, max(3, w // 5)):
        a[:, x, :3] *= 0.7
    return a


def _lev_eyes(a, ctx):
    h, w = a.shape[:2]
    a[int(h * 0.25):int(h * 0.25) + 3, int(w * 0.7):int(w * 0.7) + 4, :3] = rgb('7affe8')[:3]
    a[int(h * 0.25):int(h * 0.25) + 3, int(w * 0.7):int(w * 0.7) + 4, 3] = 130
    return a


def leviathan_geo():
    g = Geo('geometry.bc.leviathan', res=1, atlas_width=256, visible=(12, 6, (0, 1.5, 0)))
    scale = tex.Painted(tex.Material(SEA_SCALE, noise=0.1, edge=0.75), {'*': _scales})
    belly = tex.Material(BELLY, noise=0.1)
    body_m = tex.PerFace(scale, down=belly)
    fin = tex.Painted(tex.Material(tex.ramp('0b3a44', '125463', '1b6e80', '2a8a9c', '3fa8b8'), noise=0.15, edge=0, highlight=False), {'*': _fin_edge})
    horn = tex.Material(P['bone'], noise=0.06, grad=0.3)
    teeth = tex.Flat('f0ece0')
    eyes_face = tex.Painted(scale, {'east': _lev_eyes, 'west': _lev_eyes})
    mouth = tex.Material(tex.ramp('2a0508', '470a10', '6a1018'), edge=0)

    g.bone('root', pivot=(0, 12, 0))
    g.bone('head', 'root', (0, 12, -8), locators={'mouth': [0, 10, -34]})
    g.bone('jaw', 'head', (0, 7, -10))
    g.box('head', (0, 14, -18), (16, 12, 22), eyes_face)
    g.box('head', (0, 12, -32), (11, 8, 10), scale)
    g.box('head', (0, 9.5, -27), (12, 1.6, 18), mouth)
    for x in range(-5, 6, 2):
        g.box('head', (x, 8.6, -35.5), (1, 2.2, 1), teeth)
    for sx in (-1, 1):
        g.box('head', (sx * 5.5, 22, -12), (2.6, 2.6, 16), horn, rotation=[24, sx * -10, 0], pivot=(sx * 5.5, 20, -16))
        g.box('head', (sx * 7.0, 18, -4), (1.8, 1.8, 10), horn, rotation=[12, sx * -24, 0], pivot=(sx * 7.0, 18, -8))
        g.cube('head', (sx * 8.1 - (0.05 if sx > 0 else -0.05), 6, -20), (0, 14, 12), fin, rotation=[0, sx * 25, 0], pivot=(sx * 8, 12, -20))
        g.box('head', (sx * 4.5, 13, -37.5), (1.2, 1.2, 8), horn, rotation=[0, sx * -40, 0], pivot=(sx * 3.5, 13, -36))   # whiskers
    g.box('jaw', (0, 5.5, -21), (13, 4, 22), tex.PerFace(scale, down=belly))
    for x in range(-5, 6, 2):
        g.box('jaw', (x, 8.2, -30.5), (1, 2, 1), teeth)
    parent = 'root'
    z = -6.0
    for k in range(10):
        s = 15 - k * 1.15
        name = f'seg{k}'
        g.bone(name, parent, (0, 12, z))
        g.cube(name, (-s / 2, 12 - s / 2, z), (s, s, 14.5), body_m)
        if k < 8:
            g.cube(name, (-0.2, 12 + s / 2, z + 2), (0.4, 7 - k * 0.5, 10), fin)
        if k in (1, 4):
            for sx in (-1, 1):
                g.cube(name, (sx * s / 2 - (0 if sx > 0 else 12), 12 - s / 2 + 1, z + 3), (12, 0, 8), fin)
        parent = name
        z += 14.0
    g.cube('seg9', (-0.3, 0, z - 2), (0.6, 24, 12), fin)
    return g


def leviathan_animations():
    bones = {
        'root': {'rotation': ['-q.target_x_rotation * 0.4', 0, 'math.sin(q.life_time * 60.0) * 3.0']},
        'head': {'rotation': ['math.sin(q.life_time * 80.0) * 4.0', 'math.sin(q.life_time * 50.0) * 8.0', 0]},
        'jaw': {'rotation': ['6.0 + math.max(0.0, math.sin(q.life_time * 70.0)) * 8.0', 0, 0]},
    }
    for k in range(10):
        bones[f'seg{k}'] = {'rotation': [f'math.sin(q.life_time * 140.0 - {k * 40}) * 5.0', f'math.sin(q.life_time * 110.0 - {k * 45}) * 11.0', 0]}
    return {
        'animation.bc.leviathan.swim': {'loop': True, 'bones': bones},
        'animation.bc.leviathan.bite': {'animation_length': 0.6, 'bones': {
            'jaw': {'rotation': {'0.0': [0, 0, 0], '0.2': [40, 0, 0], '0.35': [-4, 0, 0], '0.6': [0, 0, 0]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.2': [-15, 0, 0], '0.35': [12, 0, 0], '0.6': [0, 0, 0]}},
        }},
        'animation.bc.leviathan.roar': {'animation_length': 1.4, 'bones': {
            'jaw': {'rotation': {'0.0': [0, 0, 0], '0.3': [45, 0, 0], '1.1': [42, 0, 0], '1.4': [0, 0, 0]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.3': [-35, 0, 0], '1.1': [-30, 0, 0], '1.4': [0, 0, 0]}},
        }},
    }


# ======================================================================================
# projectiles
# ======================================================================================
def _rock(name, size, palette=ROCK, glow=None):
    g = Geo(f'geometry.bc.{name}', res=2, atlas_width=64, visible=(2, 2, (0, 0, 0)))
    g.bone('root', pivot=(0, 0, 0))
    g.bone('spin', 'root', (0, 0, 0))
    rock = tex.Stone(palette, brick=0)
    g.box('spin', (0, 0, 0), (size, size * 0.9, size), rock)
    g.box('spin', (0, 0, 0), (size * 1.1, size * 0.7, size * 0.7), rock, rotation=[35, 20, 0], pivot=(0, 0, 0))
    g.box('spin', (0, 0, 0), (size * 0.7, size * 1.05, size * 0.75), rock, rotation=[0, 40, 30], pivot=(0, 0, 0))
    if glow:
        lava = tex.Energy(P['flame'][2:], alpha=135)
        for ang in (0, 120, 240):
            r = math.radians(ang)
            g.box('spin', (math.cos(r) * size * 0.45, 0, math.sin(r) * size * 0.45), (size * 0.3, size * 0.9, size * 0.3), lava,
                  rotation=[ang, 0, 45], pivot=(0, 0, 0))
    anim = {f'animation.bc.{name}.fly': {'loop': True, 'bones': {
        'root': {'rotation': ['-q.target_x_rotation', '-q.target_y_rotation', 0]},
        'spin': {'rotation': ['q.life_time * 400.0', 'q.life_time * 250.0', 0]}}}}
    return g, anim


def boulder():
    return _rock('boulder', 7)


def meteor():
    return _rock('meteor', 12, glow=True)


def cannonball():
    g, anim = _rock('cannonball', 4, palette=IRON)
    return g, anim


def metal_blade():
    g = Geo('geometry.bc.metal_blade', res=2, atlas_width=64, visible=(2, 2, (0, 0, 0)))
    g.bone('root', pivot=(0, 0, 0))
    g.bone('spin', 'root', (0, 0, 0))
    silver = tex.Metal(tex.ramp('5d6370', '858c9a', 'aab1be', 'cfd5df', 'f1f4f8', 'ffffff'), sheen=0.6)
    g.cube('spin', (-1.4, -0.25, -7), (2.8, 0.5, 10), silver)
    g.box('spin', (0, 0, -7.6), (1.6, 0.5, 1.6), silver, rotation=[0, 45, 0], pivot=(0, 0, -7.6))
    for sx in (-1, 1):
        g.box('spin', (sx * 2.2, 0, 1.5), (2.4, 0.4, 4.0), silver, rotation=[0, sx * 35, 0], pivot=(sx * 1.4, 0, 3))
    anim = {'animation.bc.metal_blade.fly': {'loop': True, 'bones': {
        'root': {'rotation': ['-q.target_x_rotation', '-q.target_y_rotation', 0]},
        'spin': {'rotation': [0, 0, 'q.life_time * 900.0']}}}}
    return g, anim


# ======================================================================================
# fruit power auras (worn on the casting arm)
# ======================================================================================
def power_geo(fid):
    f = FRUITS[fid]
    g = Geo(f'geometry.bc.power_{fid}', res=2, atlas_width=128, visible=(3, 3, (0, 1, 0)))
    g.skeleton()
    g.bone('aura', 'rightArm', (-6, 14, 0))
    g.bone('orbit', 'aura', (-6, 14, 0))
    col = tex.ramp(*['%02x%02x%02x' % tuple(int(c * k) for c in bytes.fromhex(f['color'])) for k in (0.35, 0.55, 0.75, 0.95)] + ['ffffff'])
    glow = tex.Energy(col, alpha=135)
    hx, hz = -6.0, 0.0
    if fid == 'ember':
        g.box('aura', (hx, 13.5, hz), (5.0, 3.2, 5.0), tex.Energy(P['flame'][1:], alpha=140))
        for k in range(8):
            a = math.radians(k * 45)
            g.box('orbit', (hx + math.cos(a) * 3.2, 15 + (k % 3), hz + math.sin(a) * 3.2), (1.2, 4 + (k % 3) * 1.5, 1.2),
                  tex.Energy(P['flame'][2:], alpha=135), rotation=[0, -k * 45, 0], pivot=(hx, 14, hz))
    elif fid == 'stone':
        rock = tex.Stone(ROCK, brick=0)
        g.cube('aura', (-8.8, 11.0, -2.8), (5.6, 6.5, 5.6), rock)
        for x, y, z in ((-8.6, 11.6, -3.4), (-5.6, 11.2, -3.2), (-7.2, 10.4, -1.5), (-9.2, 14, 0.5)):
            g.box('aura', (x, y, z), (2, 2, 2), rock, rotation=[30, 20, 10], pivot=(x, y, z))
    elif fid == 'gravity':
        dark = tex.Material(tex.ramp('08040e', '140a24', '22103a'), edge=0, highlight=False)
        for k in range(3):
            a = math.radians(k * 120)
            g.box('orbit', (hx + math.cos(a) * 4.2, 13.5, hz + math.sin(a) * 4.2), (2.2, 2.2, 2.2), dark, rotation=[45, 45, 0],
                  pivot=(hx + math.cos(a) * 4.2, 13.5, hz + math.sin(a) * 4.2))
        for k in range(12):
            a = math.radians(k * 30)
            g.box('aura', (hx + math.cos(a) * 4.2, 13.5, hz + math.sin(a) * 4.2), (2.4, 0.4, 0.4), glow, rotation=[0, -k * 30 - 90, 0],
                  pivot=(hx + math.cos(a) * 4.2, 13.5, hz + math.sin(a) * 4.2))
    elif fid == 'shadow':
        shade = tex.Material(tex.ramp('020104', '07040c', '0e0818', '1a1028'), noise=0.25, edge=0, highlight=False)
        g.box('aura', (hx, 13.5, hz), (4.8, 3.4, 4.8), glow)
        for k in range(7):
            a = math.radians(k * 51)
            g.box('orbit', (hx + math.cos(a) * 2.8, 16 + k % 3, hz + math.sin(a) * 2.8), (1.1, 7 + (k % 3) * 2, 1.1), shade,
                  rotation=[math.sin(a) * 15, 0, math.cos(a) * 15], pivot=(hx, 13, hz))
    elif fid == 'bloom':
        vine = tex.Material(tex.ramp('0b2412', '133a1c', '1d5427', '2a7234', '3c9444'), noise=0.15)
        leaf = tex.Material(tex.ramp('1d5427', '2a7234', '3c9444', '5cb85a', '8fde7e'), noise=0.1)
        for k in range(10):
            a = math.radians(k * 72)
            y = 12 + k * 1.1
            g.box('aura', (hx + math.cos(a) * 2.4, y, hz + math.sin(a) * 2.4), (1.6, 0.9, 0.9), vine, rotation=[0, -k * 72, 25], pivot=(hx, y, hz))
        for k, (y, a) in enumerate(((17, 30), (14, 160), (20, 260))):
            r = math.radians(a)
            g.box('aura', (hx + math.cos(r) * 3, y, hz + math.sin(r) * 3), (3.2, 0.3, 2.0), leaf, rotation=[0, -a, 20], pivot=(hx + math.cos(r) * 2.4, y, hz + math.sin(r) * 2.4))
        g.box('aura', (hx, 11.0, hz - 0.5), (2.4, 2.4, 2.4), tex.Energy(tex.ramp('c84a7a', 'f07aa8', 'ffc8dc', 'ffffff'), alpha=140), rotation=[45, 45, 0], pivot=(hx, 11, hz - 0.5))
    elif fid == 'frost':
        ice = tex.Crystal(P['ice'], alpha=215)
        g.cube('aura', (-8.6, 11.2, -2.6), (5.2, 4.5, 5.2), ice)
        for k in range(6):
            a = math.radians(k * 60)
            g.box('orbit', (hx + math.cos(a) * 3.0, 13 + (k % 2) * 2, hz + math.sin(a) * 3.0), (1.2, 4.5, 1.2), ice,
                  rotation=[math.sin(a) * 30, 0, math.cos(a) * 30], pivot=(hx + math.cos(a) * 3.0, 12, hz + math.sin(a) * 3.0))
    elif fid == 'barrier':
        pane = tex.Energy(tex.ramp('a08a30', 'd8c060', 'f0e6a0', 'fffbe8'), alpha=140)
        for k in range(6):
            a = math.radians(k * 60)
            cx, cz = hx + math.cos(a) * 4.0, hz + math.sin(a) * 4.0
            g.box('orbit', (cx, 14, cz), (2.6, 3.4, 0.3), pane, rotation=[0, -k * 60 + 90, 0], pivot=(cx, 14, cz))
    elif fid == 'quicksilver':
        silver = tex.Metal(tex.ramp('5d6370', '858c9a', 'aab1be', 'cfd5df', 'f1f4f8', 'ffffff'), sheen=0.6)
        g.cube('aura', (-8.5, 11.2, -2.5), (5.0, 7, 5.0), silver)
        for sx in (-1.4, 0, 1.4):
            g.cube('aura', (hx + sx - 0.3, 11.6, -9.5), (0.6, 0.8, 7.2), silver)
    else:
        _generic_aura(g, fid, glow, hx, hz)
    return g


def _generic_aura(g, fid, glow, hx, hz):
    """Wave 4 fruits: a glowing fist with orbiting motes, shaped a little for each power."""
    solid = {
        'lava': tex.Stone(tex.ramp('1a0a06', '2e140c', '421e12', '5a2a18'), brick=0),
        'ash': tex.Material(tex.ramp('2a2a30', '3e3e46', '56565e', '707078'), noise=0.3, edge=0, highlight=False),
        'lodestone': tex.Metal(tex.ramp('3a1a16', '5a2a24', '7a3a32', 'a85048', 'd07060'), sheen=0.4),
        'ink': tex.Material(tex.ramp('06040c', '0e0a1a', '181230', '241a48'), noise=0.2, edge=0, highlight=False),
        'cloud': tex.Material(tex.ramp('9aa4c0', 'c0c8e0', 'dce2f4', 'f4f6ff', 'ffffff'), noise=0.15, edge=0, highlight=False),
    }.get(fid)
    g.box('aura', (hx, 13.5, hz), (4.6, 3.2, 4.6), glow)
    if fid == 'lava':
        g.cube('aura', (-8.6, 11.0, -2.6), (5.2, 4.2, 5.2), tex.Painted(solid, {'*': lambda a, c: (a.__setitem__((slice(1, None, 3), slice(None), slice(0, 3)), [255, 110, 30]), a)[1]}))
    elif fid in ('ash', 'cloud', 'ink'):
        for k in range(6):
            a = math.radians(k * 60)
            g.box('orbit', (hx + math.cos(a) * 3.0, 15 + (k % 3) * 1.6, hz + math.sin(a) * 3.0), (2.4, 2.4, 2.4), solid,
                  rotation=[k * 20, k * 35, 0], pivot=(hx + math.cos(a) * 3.0, 15, hz + math.sin(a) * 3.0))
    elif fid == 'lodestone':
        for k in range(10):
            a = math.radians(k * 36)
            g.box('orbit', (hx + math.cos(a) * 4.0, 13.5, hz + math.sin(a) * 4.0), (2.0, 0.8, 0.8), solid if k % 2 else glow,
                  rotation=[0, -k * 36 - 90, 0], pivot=(hx + math.cos(a) * 4.0, 13.5, hz + math.sin(a) * 4.0))
    elif fid == 'prism':
        crys = tex.Crystal(tex.ramp('5a2a7a', '8a4ac0', 'c08aff', 'f0d8ff', 'ffffff'), alpha=200)
        for k in range(5):
            a = math.radians(k * 72)
            g.box('orbit', (hx + math.cos(a) * 3.4, 14 + (k % 2) * 2, hz + math.sin(a) * 3.4), (1.2, 3.6, 1.2), crys,
                  rotation=[25, k * 72, 0], pivot=(hx + math.cos(a) * 3.4, 14, hz + math.sin(a) * 3.4))
    else:  # bounce / blast / acid: rings and motes
        for ring in range(2):
            for k in range(8):
                a = math.radians(k * 45 + ring * 22.5)
                r = 3.2 + ring * 1.2
                g.box('orbit', (hx + math.cos(a) * r, 12.5 + ring * 3, hz + math.sin(a) * r), (1.4, 0.6, 0.6), glow,
                      rotation=[0, -k * 45 - ring * 22.5 - 90, 0], pivot=(hx + math.cos(a) * r, 12.5 + ring * 3, hz + math.sin(a) * r))


def power_animations():
    return {'animation.bc.power.aura': {'loop': True, 'bones': {
        'orbit': {'rotation': [0, 'q.life_time * 120.0', 0]},
        'aura': {'scale': '1.0 + math.sin(q.life_time * 300.0) * 0.04'},
    }}}


# ======================================================================================
# bounty board block
# ======================================================================================
def _poster(kind):
    def fn(a, ctx):
        h, w = a.shape[:2]
        a[:] = tex.quantize(P['paper'], np.clip(0.55 + tex.white_noise(h, w, ctx.seed) * 0.1, 0, 1))

        def draw(d, s):
            cx = w * s / 2
            # silhouette
            d.ellipse([cx - w * s * 0.18, h * s * 0.16, cx + w * s * 0.18, h * s * 0.42], fill=(40, 28, 20, 255))
            d.rectangle([cx - w * s * 0.28, h * s * 0.4, cx + w * s * 0.28, h * s * 0.62], fill=(40, 28, 20, 255))
            if kind == 1:
                d.polygon([(cx - w * s * 0.34, h * s * 0.2), (cx + w * s * 0.34, h * s * 0.2), (cx, h * s * 0.06)], fill=(20, 16, 12, 255))
            d.rectangle([w * s * 0.15, h * s * 0.72, w * s * 0.85, h * s * 0.76], fill=(90, 50, 30, 255))
            d.ellipse([cx - w * s * 0.1, h * s * 0.8, cx + w * s * 0.1, h * s * 0.92], fill=(200, 150, 40, 255))
        lay = tex.draw_layer(h, w, draw, 4)
        lay[..., 3] = np.where(lay[..., 3] > 100, 255, 0)
        tex.alpha_over(a, lay)
        a[0, :, :3] *= 0.8
        a[:, 0, :3] *= 0.8
        a[..., 3] = 255
        return a
    return fn


def bounty_board_geo():
    g = Geo('geometry.bc.bounty_board', res=2, atlas_width=128, visible=(2, 2, (0, 0.5, 0)))
    g.bone('board', pivot=(0, 0, 0))
    wood = Planks(LIGHT_WOOD, plank=2)
    post = tex.Wood(DARK_WOOD)
    g.cube('board', (-7.5, 0, -1), (2, 16, 2), post)
    g.cube('board', (5.5, 0, -1), (2, 16, 2), post)
    g.cube('board', (-6, 4, -0.5), (12, 10, 1), wood)
    g.cube('board', (-8, 14.5, -2.5), (16, 1.5, 5), tex.Wood(DARK_WOOD))
    for k, (x, y) in enumerate(((-5.2, 8.6), (-1.6, 9.2), (2.0, 8.4))):
        g.cube('board', (x, y, -0.9), (3.2, 4.4, 0.4), tex.PerFace(_poster(k % 2), south=_poster(k % 2)))
    for k, x in enumerate((-4.6, -0.2, 3.6)):
        g.cube('board', (x, 4.8, -0.9), (2.4, 3.0, 0.4), tex.PerFace(_poster((k + 1) % 2)))
    g.box('board', (0, 5.2, -1.2), (2.6, 1.0, 1.0), tex.Metal(P['gold']))
    return g
