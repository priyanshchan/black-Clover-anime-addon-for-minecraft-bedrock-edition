"""Mob models: Dark Disciple (hostile mage) and the Devil (boss)."""
from __future__ import annotations

import math

import numpy as np

from .. import tex
from ..geo import Geo
from ..tex import P, rgb


# ======================================================================================
# Dark Disciple
# ======================================================================================
def _hood_front(a, ctx):
    """Cut an opening in the hood's front so the mask shows through."""
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    cx = (w - 1) / 2
    open_ = (np.abs(xx - cx) < w * 0.36) & (yy > h * 0.22) & (yy < h * 0.95)
    a[open_, 3] = 0
    # shadowed rim
    rim = (np.abs(xx - cx) < w * 0.42) & (yy > h * 0.16) & ~open_
    a[rim, :3] *= 0.55
    return a


def _mask(a, ctx):
    h, w = a.shape[:2]
    # glowing eye slits + clover mark
    for ex in (int(w * 0.18), int(w * 0.6)):
        a[int(h * 0.35):int(h * 0.35) + 2, ex:ex + int(w * 0.22), :3] = rgb('d05cff')[:3]
        a[int(h * 0.35):int(h * 0.35) + 2, ex:ex + int(w * 0.22), 3] = 130
    a[int(h * 0.72):int(h * 0.78), int(w * 0.3):int(w * 0.7), :3] *= 0.5
    cx = w // 2
    a[int(h * 0.08):int(h * 0.22), cx - 1:cx + 1, :3] = rgb('8a1a1a')[:3]
    return a


def _robe_trim(a, ctx):
    h, w = a.shape[:2]
    a[-2:, :, :3] = rgb('8a46c8')[:3]
    a[-2:, :, 3] = 130
    if ctx.face == 'north':
        cx = w // 2
        a[:, cx - 1:cx + 1, :3] = rgb('8a46c8')[:3] * 0.6
    return a


def _belt(a, ctx):
    h, w = a.shape[:2]
    a[:, :, :3] = rgb('2a1a10')[:3]
    a[0, :, :3] = rgb('4a3020')[:3]
    if ctx.face == 'north':
        cx = w // 2
        a[:, cx - 2:cx + 2, :3] = rgb('b0b6c4')[:3]
    return a


def disciple_geo(variant='disciple'):
    shade = variant == 'shade'
    ident = 'geometry.bc.shade_soldier' if shade else 'geometry.bc.dark_disciple'
    g = Geo(ident, res=2, atlas_width=128, visible=(2, 3, (0, 1.2, 0)))
    if shade:
        # living shadow: near-black body with a faint violet glow (alpha < 255 = emissive)
        robe = tex.Cloth(tex.ramp('050309', '0b0614', '120a20', '1a0f2e'), folds=0.3, alpha=235)
        robe_dark = tex.Cloth(tex.ramp('020104', '06030b', '0b0614', '120a20'), folds=0.25, alpha=235)
        skin = tex.Material(tex.ramp('0b0614', '160c28', '22123c'), noise=0.2, alpha=235)
        mask = tex.Painted(tex.Material(tex.ramp('050309', '0b0614', '120a20'), noise=0.1), {'north': _mask})
    else:
        robe = tex.Cloth(P['purple_cloth'], folds=0.22)
        robe_dark = tex.Cloth(tex.ramp('07040b', '0f0818', '170c24', '211232', '2c1842'), folds=0.2)
        skin = tex.Material(tex.ramp('5b5560', '75707c', '8f8a96', 'a7a3ae'), noise=0.08)
        mask = tex.Painted(tex.Material(P['bone'], noise=0.06, edge=0.8), {'north': _mask})

    g.bone('root', pivot=(0, 0, 0))
    g.bone('waist', 'root', (0, 12, 0))
    g.bone('body', 'waist', (0, 24, 0))
    g.bone('head', 'body', (0, 24, 0))
    g.bone('rightArm', 'body', (-5, 22, 0))
    g.bone('leftArm', 'body', (5, 22, 0))
    g.bone('rightLeg', 'root', (-1.9, 12, 0))
    g.bone('leftLeg', 'root', (1.9, 12, 0))
    g.bone('skirt', 'waist', (0, 12, 0))
    g.bone('grimoire', 'body', (-10, 20, 0))
    g.bone('cast_fx', 'body', (0, 18, -8), locators={'cast': [0, 18, -8]})

    g.cube('head', (-4, 24, -4), (8, 8, 8), skin)
    g.cube('head', (-3.6, 24.6, -4.35), (7.2, 6.4, 0.5), mask)
    g.cube('head', (-4.6, 23.6, -4.6), (9.2, 9.4, 9.2), tex.PerFace(robe_dark, north=tex.Painted(robe_dark, {'north': _hood_front})))
    g.cube('head', (-2.5, 27.5, 4.4), (5, 4.5, 2.4), robe_dark, rotation=[-25, 0, 0], pivot=(0, 29, 4.4))   # hood tail
    g.cube('body', (-4, 12, -2), (8, 12, 4), tex.Painted(robe, {'north': _robe_trim, 'south': _robe_trim}))
    g.cube('body', (-4.6, 19.5, -2.6), (9.2, 4.8, 5.2), robe_dark)                                         # mantle
    g.cube('body', (-4.2, 12.0, -2.2), (8.4, 1.4, 4.4), tex.PerFace(_belt))
    for side, x0, piv in (('rightArm', -8.4, -5), ('leftArm', 4.0, 5)):
        g.cube(side, (x0, 13, -2.2), (4.4, 11, 4.4), robe)
        g.cube(side, (x0 - 0.3, 11.2, -2.5), (5.0, 3.4, 5.0), tex.Painted(robe_dark, {'*': _robe_trim}))      # flared cuff
        g.cube(side, (x0 + 0.6, 10.0, -1.6), (3.2, 2.2, 3.2), skin)                                          # hand
    g.cube('rightLeg', (-3.9, 0, -2), (4, 12, 4), robe_dark)
    g.cube('leftLeg', (-0.1, 0, -2), (4, 12, 4), robe_dark)
    g.cube('skirt', (-4.4, 5.5, -2.4), (8.8, 6.6, 4.8), robe)
    g.cube('skirt', (-4.9, 0.2, -2.9), (9.8, 5.5, 5.8), tex.Painted(robe, {'*': _robe_trim}))
    # floating dark grimoire
    cover = tex.Material(P['dark'][:5], noise=0.15)
    g.cube('grimoire', (-12.5, 17, -2), (5, 6, 1.6), tex.Painted(cover, {'*': _book_face}))
    g.cube('grimoire', (-12.2, 17.3, -2.2), (4.6, 5.4, 2.0), tex.PerFace(lambda a, c: _pages(a, c)))
    return g


def _book_face(a, ctx):
    if ctx.face in ('north', 'south'):
        h, w = a.shape[:2]
        lay = tex.draw_layer(h, w, lambda d, s: tex.clover_shape(d, w * s / 2, h * s / 2, min(w, h) * s * 0.3, 3, (192, 140, 255, 255)), 4)
        m = lay[..., 3] > 90
        a[m, :3] = lay[m, :3]
        a[m, 3] = 130
    return a


def _pages(a, ctx):
    a[:] = rgb('cdb98d')
    a[::2, :, :3] *= 0.85
    return a


def disciple_animations():
    walk = 'math.cos(q.anim_time * 38.17 * 0.0 + q.modified_distance_moved * 38.17) * 40.0 * q.modified_move_speed'
    return {
        'animation.bc.dark_disciple.idle': {
            'loop': True,
            'bones': {
                'body': {'rotation': ['math.sin(q.life_time * 90.0) * 1.5', 0, 0]},
                'rightArm': {'rotation': ['-10.0 + math.sin(q.life_time * 90.0) * 3.0', 0, '6.0 + math.sin(q.life_time * 70.0) * 2.0']},
                'leftArm': {'rotation': ['-10.0 - math.sin(q.life_time * 90.0) * 3.0', 0, '-6.0 - math.sin(q.life_time * 70.0) * 2.0']},
                'skirt': {'rotation': ['math.sin(q.life_time * 120.0) * 2.0', 0, 0]},
                'grimoire': {'position': ['math.sin(q.life_time * 60.0) * 1.5', 'math.sin(q.life_time * 140.0) * 1.2', 'math.cos(q.life_time * 60.0) * 1.5'],
                             'rotation': [0, 'q.life_time * 40.0', 'math.sin(q.life_time * 100.0) * 8.0']},
            },
        },
        'animation.bc.dark_disciple.walk': {
            'loop': True,
            'bones': {
                'rightLeg': {'rotation': [walk, 0, 0]},
                'leftLeg': {'rotation': [f'-({walk})', 0, 0]},
                'rightArm': {'rotation': [f'-({walk}) * 0.6', 0, 0]},
                'leftArm': {'rotation': [f'({walk}) * 0.6', 0, 0]},
                'skirt': {'rotation': [f'math.abs({walk}) * 0.25', 0, 0]},
            },
        },
        'animation.bc.dark_disciple.look_at_target': {
            'loop': True,
            'bones': {'head': {'rotation': ['q.target_x_rotation', 'q.target_y_rotation', 0]}},
        },
        'animation.bc.dark_disciple.cast': {
            'animation_length': 0.9,
            'bones': {
                'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-120, -15, 0], '0.45': [-95, 10, 0], '0.9': [0, 0, 0]}},
                'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-120, 15, 0], '0.45': [-95, -10, 0], '0.9': [0, 0, 0]}},
                'body': {'rotation': {'0.0': [0, 0, 0], '0.2': [-8, 0, 0], '0.45': [6, 0, 0], '0.9': [0, 0, 0]}},
                'grimoire': {'position': {'0.0': [0, 0, 0], '0.3': [6, 4, -6], '0.9': [0, 0, 0]}},
            },
        },
    }


# ======================================================================================
# Devil (boss)
# ======================================================================================
def _devil_face(a, ctx):
    h, w = a.shape[:2]
    ey = int(h * 0.38)
    for ex in (int(w * 0.16), int(w * 0.6)):
        ew = max(2, int(w * 0.24))
        a[ey:ey + 3, ex:ex + ew, :3] = rgb('ff3a2a')[:3]
        a[ey:ey + 3, ex:ex + ew, 3] = 130
        a[ey + 1, ex + 1:ex + ew - 1, :3] = rgb('fff0a0')[:3]
        a[ey - 2:ey, ex - 1:ex + ew + 1, :3] *= 0.4   # heavy brow
    # cheek ridges
    a[int(h * 0.62):, int(w * 0.1):int(w * 0.12) + 1, :3] *= 0.5
    a[int(h * 0.62):, int(w * 0.88):int(w * 0.9) + 1, :3] *= 0.5
    return a


def _teeth(a, ctx):
    h, w = a.shape[:2]
    if ctx.face == 'north':
        a[:max(2, h // 3), :, :3] = rgb('f3eedf')[:3]
        for x in range(0, w, 3):
            a[:max(2, h // 3), x, :3] = rgb('5b5244')[:3]
    return a


def _veins(alpha=130):
    def fn(a, ctx):
        h, w = a.shape[:2]
        rng = np.random.default_rng(ctx.seed)
        for _ in range(max(1, (h * w) // 700)):
            y, x = int(rng.integers(0, h)), int(rng.integers(0, w))
            for i in range(int(rng.integers(4, 10))):
                y = int(np.clip(y + rng.integers(-1, 2), 0, h - 1))
                x = int(np.clip(x + rng.integers(-1, 2), 0, w - 1))
                a[y, x, :3] = rgb('ff3a2a')[:3]
                a[y, x, 3] = alpha
        return a
    return fn


def _membrane(a, ctx):
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # scalloped trailing edge along the bottom
    period = max(6, w / 3)
    edge = h - (np.abs(np.sin(xx / period * math.pi)) * h * 0.28 + 1)
    a[yy > edge, 3] = 0
    a[(yy <= edge) & (yy > edge - 2), :3] *= 0.6
    # vein ribs
    for k in range(1, 4):
        x0 = int(w * k / 4)
        a[:, max(0, x0 - 1):x0, :3] *= 0.6
    return a


def devil_geo():
    g = Geo('geometry.bc.devil', res=2, atlas_width=256, visible=(5, 5, (0, 1.8, 0)))
    skin = tex.Material(P['devil_skin'], noise=0.16, edge=0.7)
    skin_v = tex.Painted(skin, {'*': _veins()})
    horn = tex.Material(tex.ramp('0a0806', '1c1610', '3a3024', '5a4a38', '7a6850', 'a08a6c'), noise=0.08, grad=0.3)
    bone_m = tex.Material(P['bone'], noise=0.06)
    cloth = tex.Cloth(tex.ramp('050506', '0d0d10', '17171c', '22222a'), folds=0.25)
    wing_bone = tex.Material(tex.ramp('08050a', '140a12', '22101c', '341826'), noise=0.1)
    membrane = tex.Painted(tex.Material(tex.ramp('12040a', '220812', '360c1c', '4a1226', '601a32'), noise=0.2, edge=0, highlight=False),
                           {'*': _membrane})

    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 22, 0))
    g.bone('chest', 'body', (0, 26, 0))
    g.bone('head', 'chest', (0, 38, -1), locators={'eyes': [0, 42, -6]})
    g.bone('jaw', 'head', (0, 38.5, -2))
    for side, sx in (('right', -1), ('left', 1)):
        g.bone(f'{side}Arm', 'chest', (sx * 8.5, 35, 0))
        g.bone(f'{side}Forearm', f'{side}Arm', (sx * 11, 26, 0))
        g.bone(f'{side}Hand', f'{side}Forearm', (sx * 11, 16, -0.5), locators={f'{side}_hand': [sx * 11, 14, -1]})
        g.bone(f'{side}Wing', 'chest', (sx * 3, 33, 4))
        g.bone(f'{side}WingTip', f'{side}Wing', (sx * 19, 34, 5))
        g.bone(f'{side}Leg', 'body', (sx * 3, 14, 0))
        g.bone(f'{side}Shin', f'{side}Leg', (sx * 3.2, 7.5, 0))
        g.bone(f'{side}HornA', 'head', (sx * 3.4, 47, -1.5), rotation=[-10, 0, sx * 48])
        g.bone(f'{side}HornB', f'{side}HornA', (sx * 3.4, 52, -1.5), rotation=[-25, 0, sx * -38])
        g.bone(f'{side}HornC', f'{side}HornB', (sx * 3.4, 56.2, -1.5), rotation=[-30, 0, sx * -28])
    g.bone('tail0', 'body', (0, 16, 3))
    for k in range(1, 5):
        g.bone(f'tail{k}', f'tail{k - 1}', (0, 16 - k * 0.2, 3 + k * 6.5))

    # torso
    g.cube('chest', (-7.5, 26, -4.5), (15, 12, 9), tex.Painted(skin_v, {'north': _abs_chest}))
    g.cube('body', (-5.5, 18, -3.5), (11, 8, 7), tex.Painted(skin_v, {'north': _abs}))
    g.cube('body', (-5.2, 14, -3.2), (10.4, 4.2, 6.4), cloth)
    g.cube('body', (-4.5, 6.5, -3.4), (9, 7.6, 0), cloth)   # loincloth front (plane)
    g.cube('body', (-4.5, 7.5, 3.3), (9, 6.6, 0), cloth)
    # spine spikes
    for k in range(4):
        g.box('chest', (0, 36 - k * 3, 4.8), (1.2, 2.4, 2.4), horn, rotation=[-35, 0, 0], pivot=(0, 36 - k * 3, 4.5))
    # head
    g.cube('head', (-4.5, 38.5, -6), (9, 9, 9), tex.Painted(skin, {'north': _devil_face}))
    g.cube('head', (-3.6, 39.6, -7.0), (7.2, 3.0, 1.2), skin)                        # snout ridge
    g.cube('jaw', (-3.8, 36.2, -7.0), (7.6, 2.6, 7.0), tex.Painted(skin, {'north': _teeth}))
    for side, sx in (('right', -1), ('left', 1)):
        # horns: three segments sweeping out, up and back
        g.cube(f'{side}HornA', (sx * 3.4 - 1.7, 46.0, -3.2), (3.4, 6.2, 3.4), horn)
        g.cube(f'{side}HornB', (sx * 3.4 - 1.25, 51.6, -2.75), (2.5, 5.0, 2.5), horn)
        g.cube(f'{side}HornC', (sx * 3.4 - 0.7, 55.9, -2.2), (1.4, 4.0, 1.4), horn)
        # arms
        ax0 = 7.5 if sx > 0 else -13.5
        g.cube(f'{side}Arm', (ax0, 26, -3.2), (6, 11, 6.4), skin_v)
        g.cube(f'{side}Arm', (ax0 - 0.4, 33, -3.6), (6.8, 4.6, 7.2), horn)        # shoulder plate
        g.box(f'{side}Arm', (sx * 11, 37.5, 0), (1.6, 3.6, 1.6), horn, rotation=[0, 0, sx * 25], pivot=(sx * 11, 36, 0))
        fx0 = 8 if sx > 0 else -14
        g.cube(f'{side}Forearm', (fx0, 16, -3.4), (6, 10.5, 6.8), skin_v)
        for k in range(3):
            g.box(f'{side}Forearm', (sx * 11 + sx * 3.2, 23 - k * 3, 0), (1.4, 2.2, 1.4), horn, rotation=[0, 0, sx * 60], pivot=(sx * 11 + sx * 3, 23 - k * 3, 0))
        hx0 = 8.5 if sx > 0 else -13.5
        g.cube(f'{side}Hand', (hx0, 12.5, -3.2), (5, 3.8, 5.8), skin)
        for k in range(4):
            cx = sx * 11 + (k - 1.5) * 1.25 * sx
            g.box(f'{side}Hand', (cx, 10.6, -2.6), (0.9, 3.6, 0.9), bone_m, rotation=[-25, 0, 0], pivot=(cx, 12.5, -2.6))
        # legs (digitigrade)
        lx0 = 0.6 if sx > 0 else -5.6
        g.cube(f'{side}Leg', (lx0, 7.5, -2.6), (5, 7, 5.2), skin_v)
        sx0 = 1.2 if sx > 0 else -5.2
        g.cube(f'{side}Shin', (sx0, 0.5, -1.5), (4, 7.4, 4), skin, rotation=[22, 0, 0], pivot=(sx * 3.2, 7.5, 0))
        g.cube(f'{side}Shin', (sx0 - 0.3, -0.5, -4.2), (4.6, 2.2, 4.8), horn)       # hoof
        # wings
        wx0 = 3 if sx > 0 else -19
        g.cube(f'{side}Wing', (wx0, 33, 4), (16, 2.2, 2.2), wing_bone)
        g.cube(f'{side}Wing', (wx0, 15.5, 5.0), (16, 18, 0), membrane)
        tx0 = 19 if sx > 0 else -33
        g.cube(f'{side}WingTip', (tx0, 33.3, 4.4), (14, 1.6, 1.6), wing_bone)
        g.cube(f'{side}WingTip', (tx0, 19.5, 5.1), (14, 14.5, 0), membrane)
        g.box(f'{side}WingTip', (sx * 33.5, 36, 5), (1.2, 4.5, 1.2), horn, rotation=[0, 0, sx * 25], pivot=(sx * 33, 34, 5))
    for k in range(5):
        s = 3.4 - k * 0.5
        z0 = 3 + k * 6.5
        y0 = 16 - k * 0.2 - s / 2
        g.cube(f'tail{k}' if k < 5 else 'tail4', (-s / 2, y0, z0), (s, s, 6.8), skin)
    g.box('tail4', (0, 15.2, 35.5), (4.2, 0.8, 4.2), horn, rotation=[0, 45, 0], pivot=(0, 15.2, 35.5))
    return g


def _abs_chest(a, ctx):
    h, w = a.shape[:2]
    cx = w // 2
    a[:, cx - 1:cx + 1, :3] *= 0.6
    a[int(h * 0.55):int(h * 0.55) + 1, 2:-2, :3] *= 0.6
    _veins(130)(a, ctx)
    # glowing contract sigil on the chest
    lay = tex.draw_layer(h, w, lambda d, s: tex.clover_shape(d, w * s / 2, h * s * 0.35, min(w, h) * s * 0.22, 5, (255, 60, 40, 255), devil=True), 4)
    m = lay[..., 3] > 90
    a[m, :3] = lay[m, :3]
    a[m, 3] = 130
    return a


def _abs(a, ctx):
    h, w = a.shape[:2]
    cx = w // 2
    a[:, cx - 1:cx + 1, :3] *= 0.6
    for y in range(h // 3, h, h // 3):
        a[y, 2:-2, :3] *= 0.6
    return a


def devil_animations():
    bones_idle = {
        'root': {'position': [0, '6.0 + math.sin(q.life_time * 90.0) * 1.6', 0]},
        'body': {'rotation': ['6.0 + math.sin(q.life_time * 90.0 + 40.0) * 2.0', 0, 0]},
        'rightArm': {'rotation': ['-8.0 + math.sin(q.life_time * 90.0) * 4.0', 0, '8.0']},
        'leftArm': {'rotation': ['-8.0 - math.sin(q.life_time * 90.0) * 4.0', 0, '-8.0']},
        'rightForearm': {'rotation': ['-20.0', 0, 0]},
        'leftForearm': {'rotation': ['-20.0', 0, 0]},
        'rightLeg': {'rotation': ['-18.0 + math.sin(q.life_time * 90.0) * 4.0', 0, 4]},
        'leftLeg': {'rotation': ['-10.0 - math.sin(q.life_time * 90.0) * 4.0', 0, -4]},
        'jaw': {'rotation': ['math.max(0.0, math.sin(q.life_time * 45.0)) * 6.0', 0, 0]},
    }
    for k in range(5):
        bones_idle[f'tail{k}'] = {'rotation': [f'{-6 + k * 4} + math.sin(q.life_time * 100.0 - {k * 45}) * 6.0',
                                               f'math.sin(q.life_time * 80.0 - {k * 50}) * 14.0', 0]}
    flap = 'math.sin(q.life_time * 220.0)'
    return {
        'animation.bc.devil.hover': {'loop': True, 'bones': bones_idle},
        'animation.bc.devil.wings': {
            'loop': True,
            'bones': {
                'rightWing': {'rotation': [0, f'-25.0 + {flap} * 30.0', f'10.0 + {flap} * 12.0']},
                'leftWing': {'rotation': [0, f'25.0 - {flap} * 30.0', f'-10.0 - {flap} * 12.0']},
                'rightWingTip': {'rotation': [0, f'-20.0 + {flap} * 25.0', 0]},
                'leftWingTip': {'rotation': [0, f'20.0 - {flap} * 25.0', 0]},
            },
        },
        'animation.bc.devil.look_at_target': {'loop': True, 'bones': {'head': {'rotation': ['q.target_x_rotation', 'q.target_y_rotation', 0]}}},
        'animation.bc.devil.attack': {
            'animation_length': 0.6,
            'bones': {
                'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.15': [-150, -20, 20], '0.32': [-30, 25, -10], '0.6': [0, 0, 0]}},
                'chest': {'rotation': {'0.0': [0, 0, 0], '0.15': [-10, 20, 0], '0.32': [12, -25, 0], '0.6': [0, 0, 0]}},
                'jaw': {'rotation': {'0.0': [0, 0, 0], '0.2': [22, 0, 0], '0.6': [0, 0, 0]}},
            },
        },
        'animation.bc.devil.cast': {
            'animation_length': 1.2,
            'bones': {
                'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.3': [-160, 0, 35], '0.9': [-150, 0, 30], '1.2': [0, 0, 0]}},
                'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.3': [-160, 0, -35], '0.9': [-150, 0, -30], '1.2': [0, 0, 0]}},
                'head': {'rotation': {'0.0': [0, 0, 0], '0.3': [-25, 0, 0], '0.9': [-20, 0, 0], '1.2': [0, 0, 0]}},
                'jaw': {'rotation': {'0.0': [0, 0, 0], '0.3': [28, 0, 0], '0.9': [25, 0, 0], '1.2': [0, 0, 0]}},
                'chest': {'rotation': {'0.0': [0, 0, 0], '0.3': [-14, 0, 0], '1.2': [0, 0, 0]}},
            },
        },
    }
