"""v1.1.0 models and animations: the three Mana Wyverns (Ember, Frost, Storm), the Spire Warden, the Mimic, the Mana Sprite,
the Will-o'-Wisp, the Rootwarden, the Hollow Knight and the Wanderer; relic and exploration icons; the Mana Spawner and the
Obelisk Core blocks. All designs are original."""
from __future__ import annotations

import math

import numpy as np

from .. import tex
from ..geo import Geo
from ..tex import P, rgb
from .sea import SKIN, _face, _humanoid_bones, humanoid_animations


def _r(*h):
    return tex.ramp(*h)


# ======================================================================================
# the Mana Wyverns
# ======================================================================================
WYVERN_LOOK = {
    'ember_wyvern': dict(scale=_r('2a0804', '45100a', '631a0e', '842a12', 'a83e18', 'c95a22'), belly=_r('6a3a10', '8a521a', 'a86c26', 'c48836', 'dca44a'),
                         membrane=_r('2a0606', '420c0a', '5e1610', '7a2214', '963018'), horn=P['obsidian'], glow='ffa040', vein='ff8a2a',
                         spine=_r('1a0a06', '2c120a', '3e1a0e', '52240f')),
    'frost_wyvern': dict(scale=_r('2c4a66', '3e6688', '5684aa', '74a4c8', '98c6e2', 'c4e6f6'), belly=_r('8aa6b8', 'a6c0d0', 'c2d8e4', 'dcecf4', 'f2fafe'),
                         membrane=_r('1a3a5a', '24507a', '30689a', '4282b8', '5aa0d4'), horn=P['white_cloth'], glow='8ae6ff', vein='c8f4ff',
                         spine=_r('4fb0d8', '8ad8f0', 'c6f0fb', 'f2fdff')),
    'storm_wyvern': dict(scale=_r('10141e', '1a2030', '242c44', '2e3a58', '3a4a6e', '4a5e86'), belly=_r('4a4e5a', '60646e', '787c86', '90949e', 'a8acb6'),
                         membrane=_r('140e2a', '1e1640', '2a2058', '362a70', '443688'), horn=P['blackiron'], glow='ffe03a', vein='ffe85a',
                         spine=_r('6b4a00', 'b58300', 'f2c200', 'ffe23d')),
}


def _scale_pattern(a, ctx):
    h, w = a.shape[:2]
    step = max(2, ctx.res * 2)
    for y in range(0, h, step):
        for x in range((y // step) % 2 * (step // 2), w, step):
            a[y, x:x + max(1, step // 2), :3] *= 0.72
            if y + 1 < h:
                a[y + 1, x:x + max(1, step // 2), :3] = np.minimum(a[y + 1, x:x + max(1, step // 2), :3] * 1.18, 255)
    return a


def _membrane(vein):
    v = np.array(rgb(vein)[:3], np.float32)

    def fn(a, ctx):
        h, w = a.shape[:2]
        if h < 2 or w < 2:
            return a
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        # ragged trailing edge (the far side in v), and a few veins fanning from the arm
        edge = h - 1 - (np.abs(np.sin(xx / max(3.0, w / 5.0) * math.pi)) * h * 0.22 + 1)
        a[yy > edge, 3] = 0
        for k in range(1, 5):
            x0 = int(w * k / 5)
            for y in range(h):
                x = int(x0 + (y / max(1, h)) * (w / 10.0) * (1 if k % 2 else -1))
                if 0 <= x < w and a[y, x, 3] > 0:
                    a[y, x, :3] = a[y, x, :3] * 0.4 + v * 0.6
        return a
    return fn


def _wyvern_eyes(glow):
    g = np.array(rgb(glow)[:3], np.float32)

    def fn(a, ctx):
        h, w = a.shape[:2]
        y = int(h * 0.35)
        a[y:y + max(1, h // 4), int(w * 0.55):int(w * 0.85), :3] = g
        return a
    return fn


def wyvern_geo(kind):
    """All three wyverns share one layout (one geometry), with their own textures."""
    L = WYVERN_LOOK[kind]
    g = Geo('geometry.bc.mana_wyvern', res=2, atlas_width=256, visible=(8, 6, (0, 2, 0)), seed=1101)
    scales = tex.Painted(tex.Metal(L['scale'], sheen=0.28, noise=0.1), {'*': _scale_pattern})
    belly = tex.Material(L['belly'], noise=0.08, edge=0.8)
    membrane = tex.Painted(tex.Material(L['membrane'], noise=0.18, edge=0, highlight=False), {'*': _membrane(L['vein'])})
    horn = tex.Material(L['horn'], noise=0.08, edge=0.75)
    spine = tex.Metal(L['spine'], sheen=0.4)
    glow = tex.Flat(L['glow'])
    claw = tex.Flat('ece4d4')
    head_mat = tex.PerFace(scales, east=tex.Painted(scales, {'east': _wyvern_eyes(L['glow'])}),
                           west=tex.Painted(scales, {'west': _wyvern_eyes(L['glow'])}))

    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 16, 0))
    g.bone('neck0', 'body', (0, 22, -9))
    g.bone('neck1', 'neck0', (0, 26, -15))
    g.bone('head', 'neck1', (0, 29, -20))
    g.bone('jaw', 'head', (0, 28, -24))
    for side, sx in (('right', -1), ('left', 1)):
        g.bone(f'{side}Wing', 'body', (sx * 5, 23, -5))
        g.bone(f'{side}WingTip', f'{side}Wing', (sx * 24, 23, -5))
        g.bone(f'{side}Thigh', 'body', (sx * 5, 15, 4))
        g.bone(f'{side}Shin', f'{side}Thigh', (sx * 5.5, 8, 3))
    prev = 'body'
    for k, (y, z) in enumerate(((18, 9), (17.5, 17), (17, 24), (16.5, 30))):
        g.bone(f'tail{k}', prev, (0, y, z))
        prev = f'tail{k}'

    # torso, chest and belly plates, a ridge of spines
    g.cube('body', (-5, 13, -9), (10, 10, 18), scales)
    g.cube('body', (-5.5, 14, -11), (11, 8.5, 5), scales)
    g.cube('body', (-4, 12.4, -8), (8, 1, 15), belly)
    for k in range(7):
        z = -9 + k * 3
        g.box('body', (0, 24.0, z), (1.0, 2.6 - abs(k - 3) * 0.3, 1.8), spine, rotation=[-35, 0, 0], pivot=(0, 23, z))
    # neck and head
    g.cube('neck0', (-2.6, 20, -16), (5.2, 5.2, 8), scales, rotation=[22, 0, 0], pivot=(0, 22, -9))
    g.cube('neck0', (-2, 19.6, -15), (4, 1, 6), belly, rotation=[22, 0, 0], pivot=(0, 22, -9))
    g.cube('neck1', (-2.3, 24.2, -21), (4.6, 4.6, 7), scales, rotation=[10, 0, 0], pivot=(0, 26, -15))
    for k in range(2):
        g.box('neck1', (0, 29.1, -16.5 - k * 2.6), (0.8, 1.8, 1.4), spine, rotation=[-35, 0, 0], pivot=(0, 28.6, -16.5 - k * 2.6))
    g.cube('head', (-3.5, 27, -28), (7, 5, 8), head_mat)
    g.cube('head', (-2.6, 27.2, -34), (5.2, 3.4, 6.5), scales)                     # snout
    g.cube('head', (-3.8, 31.2, -27), (7.6, 1.2, 4), scales)                      # brow ridge
    for sx in (-1, 1):
        g.box('head', (sx * 2.4, 34.0, -22.5), (1.3, 6.5, 1.3), horn, rotation=[-58, 0, sx * -14], pivot=(sx * 2.4, 31.5, -23.5))
        g.box('head', (sx * 3.7, 31.4, -24.2), (0.9, 3.6, 0.9), horn, rotation=[-42, 0, sx * -42], pivot=(sx * 3.5, 30.6, -24.5))
        g.box('head', (sx * 1.2, 30.4, -33.0), (0.6, 0.6, 0.8), tex.Flat('140a08'))   # nostrils
        for k in range(3):
            g.box('head', (sx * (1.6 + (k % 2) * 0.5), 26.8, -33.2 + k * 2.2), (0.5, 1.0, 0.5), claw)
    g.cube('jaw', (-2.3, 25.2, -33.5), (4.6, 1.8, 10), scales)
    g.cube('jaw', (-1.8, 25.0, -32.5), (3.6, 0.6, 8), belly)
    for sx in (-1, 1):
        for k in range(3):
            g.box('jaw', (sx * 1.7, 27.3, -32.8 + k * 2.3), (0.5, 0.9, 0.5), claw)
    # wings: arm struts with membranes trailing behind, and finger struts across the tips
    for side, sx in (('right', -1), ('left', 1)):
        x0 = -24 if sx < 0 else 5
        g.cube(f'{side}Wing', (x0, 22, -6), (19, 2.2, 2.2), scales)
        g.cube(f'{side}Wing', (x0, 22.6, -4), (19, 0, 15), membrane)
        g.box(f'{side}Wing', (sx * 6.5, 23.6, -5), (4, 3, 4), scales)              # shoulder
        tx0 = -42 if sx < 0 else 24
        g.cube(f'{side}WingTip', (tx0, 22.3, -5.6), (18, 1.6, 1.6), scales)
        g.cube(f'{side}WingTip', (tx0, 22.7, -4), (18, 0, 13), membrane)
        for k in range(3):
            fx = sx * (28 + k * 5)
            g.box(f'{side}WingTip', (fx, 22.9, 1.5), (0.8, 0.8, 11), horn, rotation=[0, sx * (10 + k * 12), 0], pivot=(fx, 22.9, -4.5))
        g.box(f'{side}WingTip', (sx * 42.6, 23.1, -5.2), (1.0, 1.0, 3.4), claw, rotation=[0, sx * 35, 0], pivot=(sx * 42, 23.1, -5))
        # hind legs
        lx = sx * 5
        g.cube(f'{side}Thigh', (lx - 2.5, 8, 0), (5, 8, 6.5), scales, rotation=[-12, 0, 0], pivot=(lx, 15, 4))
        g.cube(f'{side}Shin', (lx + sx * 0.5 - 1.5, 2, 2), (3, 7, 3), scales, rotation=[18, 0, 0], pivot=(lx + sx * 0.5, 8, 3))
        g.cube(f'{side}Shin', (lx + sx * 0.5 - 2, 0, -1.5), (4, 2, 5), scales)
        for k in (-1, 0, 1):
            g.box(f'{side}Shin', (lx + sx * 0.5 + k * 1.3, 0.6, -2.6), (0.6, 1.2, 1.6), claw, rotation=[25, 0, 0], pivot=(lx + sx * 0.5 + k * 1.3, 1, -1.8))
    # the tail, and its tip
    for k, (s, y, z) in enumerate(((7, 15, 9), (5, 15.5, 17), (3.4, 15.6, 24), (2, 15.8, 30))):
        g.cube(f'tail{k}', (-s / 2, y, z), (s, max(2.5, s * 0.85), 8 if k < 3 else 6.5), scales)
        if k < 3:
            g.box(f'tail{k}', (0, y + max(2.5, s * 0.85) + 0.6, z + 4), (0.8, 1.6, 1.4), spine, rotation=[-35, 0, 0], pivot=(0, y + max(2.5, s * 0.85), z + 4))
    g.box('tail3', (0, 17.0, 38.4), (4.6, 0.9, 4.6), glow, rotation=[0, 45, 0], pivot=(0, 17.0, 38.4))
    for sx in (-1, 1):
        g.box('tail3', (sx * 2.2, 17.0, 35.4), (0.8, 0.8, 3.6), spine, rotation=[0, sx * -40, 0], pivot=(sx * 1, 17.0, 34.4))
    return g


def wyvern_animations():
    flap = 'math.sin(q.life_time * 210.0)'
    sway = 'math.sin(q.life_time * 70.0)'
    a = {
        # in the air: wide wingbeats, legs tucked back, tail streaming
        'animation.bc.wyvern.fly': {'loop': True, 'bones': {
            'root': {'position': [0, f'2.0 + {flap} * -1.5', 0]},
            'rightWing': {'rotation': [0, 0, f'8.0 + {flap} * 38.0']},
            'leftWing': {'rotation': [0, 0, f'-8.0 - {flap} * 38.0']},
            'rightWingTip': {'rotation': [0, 0, f'{flap} * 24.0']},
            'leftWingTip': {'rotation': [0, 0, f'-{flap} * 24.0']},
            'rightThigh': {'rotation': [55, 0, 0]}, 'leftThigh': {'rotation': [55, 0, 0]},
            'rightShin': {'rotation': [30, 0, 0]}, 'leftShin': {'rotation': [30, 0, 0]},
            'neck0': {'rotation': ['-10.0 + math.sin(q.life_time * 105.0) * 3.0', 0, 0]},
            'tail0': {'rotation': [f'-4.0 + {flap} * 3.0', f'{sway} * 6.0', 0]},
            'tail1': {'rotation': [0, f'{sway} * 8.0', 0]},
            'tail2': {'rotation': [0, f'{sway} * 10.0', 0]},
            'tail3': {'rotation': [0, f'{sway} * 12.0', 0]},
        }},
        # on the ground: wings folded against the flanks, breathing, a lazy tail
        'animation.bc.wyvern.ground': {'loop': True, 'bones': {
            'body': {'rotation': ['-6.0 + math.sin(q.life_time * 60.0) * 1.0', 0, 0]},
            'rightWing': {'rotation': [0, -85, 15]}, 'leftWing': {'rotation': [0, 85, -15]},
            'rightWingTip': {'rotation': [0, 170, 0]}, 'leftWingTip': {'rotation': [0, -170, 0]},
            'tail0': {'rotation': [8, f'{sway} * 8.0', 0]}, 'tail1': {'rotation': [4, f'{sway} * 10.0', 0]},
            'tail2': {'rotation': [0, f'{sway} * 12.0', 0]}, 'tail3': {'rotation': [-6, f'{sway} * 14.0', 0]},
        }},
        'animation.bc.wyvern.walk': {'loop': True, 'bones': {
            'rightThigh': {'rotation': ['math.cos(q.modified_distance_moved * 30.0) * 30.0 * q.modified_move_speed', 0, 0]},
            'leftThigh': {'rotation': ['-math.cos(q.modified_distance_moved * 30.0) * 30.0 * q.modified_move_speed', 0, 0]},
            'body': {'position': [0, 'math.abs(math.cos(q.modified_distance_moved * 30.0)) * 1.2 * q.modified_move_speed', 0]},
        }},
        # asleep on the hoard: curled up, head down on the ground, slow breaths
        'animation.bc.wyvern.sleep': {'loop': True, 'bones': {
            'root': {'position': [0, -5, 0]},
            'body': {'rotation': [0, 0, 0], 'scale': [1, '1.0 + math.sin(q.life_time * 40.0) * 0.025', 1]},
            'neck0': {'rotation': [38, -32, 0]}, 'neck1': {'rotation': [30, -26, 0]}, 'head': {'rotation': [-18, -20, 8]},
            'rightWing': {'rotation': [0, -85, 22]}, 'leftWing': {'rotation': [0, 85, -22]},
            'rightWingTip': {'rotation': [0, 170, 0]}, 'leftWingTip': {'rotation': [0, -170, 0]},
            'rightThigh': {'rotation': [-60, 0, 0]}, 'leftThigh': {'rotation': [-60, 0, 0]},
            'rightShin': {'rotation': [60, 0, 0]}, 'leftShin': {'rotation': [60, 0, 0]},
            'tail0': {'rotation': [0, 30, 0]}, 'tail1': {'rotation': [0, 38, 0]}, 'tail2': {'rotation': [0, 40, 0]}, 'tail3': {'rotation': [0, 40, 0]},
        }},
        'animation.bc.wyvern.look': {'loop': True, 'bones': {
            'neck1': {'rotation': ['q.target_x_rotation * 0.4', 'q.target_y_rotation * 0.5', 0]},
            'head': {'rotation': ['q.target_x_rotation * 0.4', 'q.target_y_rotation * 0.5', 0]},
        }},
        # a breath: neck stretched, jaw wide, wings thrown back
        'animation.bc.wyvern.breath': {'animation_length': 1.6, 'bones': {
            'neck0': {'rotation': {'0.0': [0, 0, 0], '0.35': [-30, 0, 0], '0.5': [18, 0, 0], '1.3': [14, 0, 0], '1.6': [0, 0, 0]}},
            'neck1': {'rotation': {'0.0': [0, 0, 0], '0.35': [-15, 0, 0], '0.5': [10, 0, 0], '1.3': [8, 0, 0], '1.6': [0, 0, 0]}},
            'jaw': {'rotation': {'0.0': [0, 0, 0], '0.35': [12, 0, 0], '0.5': [38, 0, 0], '1.3': [36, 0, 0], '1.6': [0, 0, 0]}},
            'rightWing': {'rotation': {'0.0': [0, 0, 0], '0.4': [0, -25, 30], '1.6': [0, 0, 0]}},
            'leftWing': {'rotation': {'0.0': [0, 0, 0], '0.4': [0, 25, -30], '1.6': [0, 0, 0]}},
        }},
        'animation.bc.wyvern.bite': {'animation_length': 0.5, 'bones': {
            'neck0': {'rotation': {'0.0': [0, 0, 0], '0.15': [-25, 0, 0], '0.28': [30, 0, 0], '0.5': [0, 0, 0]}},
            'jaw': {'rotation': {'0.0': [0, 0, 0], '0.15': [40, 0, 0], '0.28': [0, 0, 0]}},
        }},
        'animation.bc.wyvern.roar': {'animation_length': 1.4, 'bones': {
            'neck0': {'rotation': {'0.0': [0, 0, 0], '0.3': [-38, 0, 0], '1.1': [-34, 0, 0], '1.4': [0, 0, 0]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.3': [-25, 0, 0], '1.1': [-20, 0, 0], '1.4': [0, 0, 0]}},
            'jaw': {'rotation': {'0.0': [0, 0, 0], '0.3': [42, 0, 0], '1.1': [40, 0, 0], '1.4': [0, 0, 0]}},
            'rightWing': {'rotation': {'0.0': [0, 0, 0], '0.35': [0, -10, 60], '1.1': [0, -10, 55], '1.4': [0, 0, 0]}},
            'leftWing': {'rotation': {'0.0': [0, 0, 0], '0.35': [0, 10, -60], '1.1': [0, 10, -55], '1.4': [0, 0, 0]}},
        }},
    }
    return a


# ======================================================================================
# the Spire Warden
# ======================================================================================
def _rune_face(color):
    c = np.array(rgb(color)[:3], np.float32)

    def fn(a, ctx):
        h, w = a.shape[:2]
        rng = np.random.default_rng(ctx.seed + 5)
        for _ in range(max(2, (h * w) // 60)):
            y, x = int(rng.integers(1, max(2, h - 2))), int(rng.integers(1, max(2, w - 3)))
            ln = int(rng.integers(2, 4))
            if rng.random() < 0.5:
                a[y, x:x + ln, :3] = c
            else:
                a[y:y + ln, x, :3] = c
        return a
    return fn


def _eye_slit(color):
    c = np.array(rgb(color)[:3], np.float32)

    def fn(a, ctx):
        h, w = a.shape[:2]
        y = int(h * 0.45)
        a[y:y + max(1, h // 6), int(w * 0.2):int(w * 0.8), :3] = c
        return a
    return fn


def warden_geo():
    g = Geo('geometry.bc.spire_warden', res=2, atlas_width=256, visible=(6, 5, (0, 2, 0)), seed=1102)
    stone = tex.Painted(tex.Stone(P['stone'], brick=3), {'*': _rune_face('60e0ff')})
    dark = tex.Metal(P['deepslate'], sheen=0.2)
    trim = tex.Metal(P['gold'], sheen=0.5)
    glow = tex.Energy(_r('1a5a6a', '2a8aa0', '60e0ff', 'b8f8ff', 'f0ffff'), alpha=255)
    head = tex.PerFace(stone, north=tex.Painted(tex.Stone(P['stone'], brick=3), {'north': _eye_slit('8af4ff')}))
    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 18, 0))
    g.bone('head', 'body', (0, 31, 0))
    g.bone('rightFist', 'body', (-14, 22, -1))
    g.bone('leftFist', 'body', (14, 22, -1))
    g.bone('ring', 'body', (0, 24, 0))
    g.bone('shard', 'root', (0, 3, 0))
    # torso: carved block, gold trim, a glowing core in the chest
    g.cube('body', (-7, 17, -5), (14, 14, 10), stone)
    g.cube('body', (-7.5, 29, -5.5), (15, 2, 11), trim)
    g.box('body', (0, 24, -5.3), (5, 5, 1.2), glow, rotation=[0, 0, 45], pivot=(0, 24, -5.3))
    for sx in (-1, 1):
        g.cube('body', (sx * 7 - (5 if sx < 0 else 0), 26, -5.5), (5, 6, 11), dark)          # pauldrons
        g.box('body', (sx * 9.5, 33.0, 0), (1.4, 4.5, 1.4), dark, rotation=[0, 0, sx * -20], pivot=(sx * 9.5, 31.5, 0))
    g.cube('body', (-5, 10, -4), (10, 7, 8), stone)                                           # tapering skirt
    g.cube('body', (-3, 5, -2.5), (6, 5, 5), dark)
    g.cube('shard', (-1.5, 0, -1.5), (3, 3, 3), glow, rotation=[45, 45, 0], pivot=(0, 1.5, 0))
    # head: a stone helm with one burning eye and a crown of spikes
    g.cube('head', (-3.5, 31, -4), (7, 6.5, 7), head)
    for k, x in enumerate((-2.5, 0, 2.5)):
        g.box('head', (x, 38.5 + (1 if k == 1 else 0), 0), (1.2, 3 + (1 if k == 1 else 0), 1.2), trim)
    # floating fists
    for side, sx in (('right', -1), ('left', 1)):
        cx = sx * 14
        g.cube(f'{side}Fist', (cx - 3.5, 16, -4.5), (7, 8, 7), stone)
        g.cube(f'{side}Fist', (cx - 3.8, 21, -4.8), (7.6, 1.4, 7.6), trim)
        g.box(f'{side}Fist', (cx, 18.5, -4.7), (2.5, 2.5, 0.6), glow)
    # a ring of twelve rune tablets
    for k in range(12):
        a = k / 12 * math.tau
        x, z = math.cos(a) * 15, math.sin(a) * 15
        g.box('ring', (x, 24, z), (2.4, 3.2, 0.6), glow, rotation=[0, -math.degrees(a) + 90, 0], pivot=(x, 24, z))
    return g


def warden_animations():
    bob = 'math.sin(q.life_time * 90.0)'
    return {
        'animation.bc.spire_warden.idle': {'loop': True, 'bones': {
            'root': {'position': [0, f'3.0 + {bob} * 1.5', 0]},
            'rightFist': {'position': [0, f'math.sin(q.life_time * 90.0 + 90.0) * 1.6', 0]},
            'leftFist': {'position': [0, f'math.sin(q.life_time * 90.0 - 90.0) * 1.6', 0]},
            'ring': {'rotation': [0, 'q.life_time * 40.0', 0]},
            'shard': {'rotation': [0, 'q.life_time * -120.0', 0], 'position': [0, f'{bob} * -1.0', 0]},
        }},
        'animation.bc.spire_warden.look': {'loop': True, 'bones': {'head': {'rotation': ['q.target_x_rotation', 'q.target_y_rotation', 0]}}},
        'animation.bc.spire_warden.slam': {'animation_length': 1.0, 'bones': {
            'rightFist': {'position': {'0.0': [0, 0, 0], '0.4': [4, 14, -2], '0.6': [6, -14, -8], '1.0': [0, 0, 0]}},
            'leftFist': {'position': {'0.0': [0, 0, 0], '0.4': [-4, 14, -2], '0.6': [-6, -14, -8], '1.0': [0, 0, 0]}},
            'body': {'rotation': {'0.0': [0, 0, 0], '0.4': [-14, 0, 0], '0.6': [16, 0, 0], '1.0': [0, 0, 0]}},
        }},
        'animation.bc.spire_warden.cast': {'animation_length': 1.2, 'bones': {
            'rightFist': {'position': {'0.0': [0, 0, 0], '0.3': [-6, 8, 0], '0.9': [-6, 8, 0], '1.2': [0, 0, 0]}},
            'leftFist': {'position': {'0.0': [0, 0, 0], '0.3': [6, 8, 0], '0.9': [6, 8, 0], '1.2': [0, 0, 0]}},
            'ring': {'scale': {'0.0': [1, 1, 1], '0.3': [1.35, 1, 1.35], '0.9': [1.35, 1, 1.35], '1.2': [1, 1, 1]}},
        }},
    }


# ======================================================================================
# the Mimic
# ======================================================================================
def mimic_geo():
    g = Geo('geometry.bc.mimic', res=2, atlas_width=128, visible=(2, 2, (0, 0.5, 0)), seed=1103)
    wood = tex.Wood(P['wood'])
    band = tex.Metal(P['blackiron'], sheen=0.4)
    lock = tex.Metal(P['gold'], sheen=0.5)
    tooth = tex.Material(_r('a8a090', 'cfc8b4', 'ece6d6', 'fbf8ee'), noise=0.05, edge=0.85)
    tongue = tex.Material(_r('5a0a1a', '7e1428', '9e2236', 'be3a4a'), noise=0.12, edge=0.8)
    maw = tex.Flat('1a0508')
    eye = tex.Flat('ffd040')
    g.bone('root', pivot=(0, 0, 0))
    g.bone('base', 'root', (0, 0, 0))
    g.bone('lid', 'base', (0, 10, 7))
    g.bone('tongue', 'base', (0, 9, 4))
    g.cube('base', (-7, 1, -7), (14, 9, 14), wood)
    g.cube('base', (-6.5, 9.0, -6.5), (13, 0.6, 13), maw)
    for x in (-7.3, 5.9):
        g.cube('base', (x, 1, -7.3), (1.4, 9, 14.6), band)
    for k in range(6):
        x = -5.5 + k * 2.2
        g.box('base', (x, 10.6, -6.4), (1.2, 1.6, 0.8), tooth, rotation=[0, 0, 45], pivot=(x, 10.6, -6.4))
    for sx in (-1, 1):
        for k in range(3):
            g.box('base', (sx * 6.4, 10.5, -3.5 + k * 3.5), (0.8, 1.4, 1.1), tooth)
    for cx, cz in ((-5.5, -5.5), (5.5, -5.5), (-5.5, 5.5), (5.5, 5.5)):
        g.cube('base', (cx - 1, 0, cz - 1), (2, 1.2, 2), band)
    g.cube('lid', (-7, 10, -7), (14, 5, 14), wood)
    g.cube('lid', (-7.3, 10, -7.3), (1.4, 5.2, 14.6), band)
    g.cube('lid', (5.9, 10, -7.3), (1.4, 5.2, 14.6), band)
    g.cube('lid', (-1.5, 9.0, -7.6), (3, 3, 1), lock)
    g.cube('lid', (-6.5, 10.0, -6.5), (13, 0.4, 13), maw)
    for k in range(6):
        x = -4.4 + k * 2.2
        g.box('lid', (x, 9.6, -6.4), (1.2, 1.6, 0.8), tooth, rotation=[0, 0, 45], pivot=(x, 9.6, -6.4))
    for sx in (-1, 1):
        g.box('lid', (sx * 3, 10.0, -3.5), (1.6, 0.4, 1.6), eye)
    g.cube('tongue', (-2.5, 8.6, -8), (5, 1, 12), tongue)
    return g


def mimic_animations():
    return {
        'animation.bc.mimic.idle': {'loop': True, 'bones': {
            'lid': {'rotation': ['-8.0 - math.abs(math.sin(q.life_time * 120.0)) * 10.0', 0, 0]},
            'tongue': {'rotation': ['math.sin(q.life_time * 200.0) * 6.0', 'math.sin(q.life_time * 140.0) * 10.0', 0]},
        }},
        'animation.bc.mimic.hop': {'loop': True, 'bones': {
            'root': {'position': [0, 'math.abs(math.sin(q.modified_distance_moved * 40.0)) * 3.0 * q.modified_move_speed * 2.0', 0]},
            'lid': {'rotation': ['-20.0 - math.abs(math.sin(q.modified_distance_moved * 40.0)) * 25.0', 0, 0]},
        }},
        'animation.bc.mimic.attack': {'animation_length': 0.45, 'bones': {
            'lid': {'rotation': {'0.0': [0, 0, 0], '0.15': [-75, 0, 0], '0.3': [5, 0, 0], '0.45': [-10, 0, 0]}},
            'root': {'position': {'0.0': [0, 0, 0], '0.15': [0, 2, -2], '0.3': [0, 0, -1], '0.45': [0, 0, 0]}},
        }},
    }


# ======================================================================================
# the Mana Sprite and the Will-o'-Wisp
# ======================================================================================
def sprite_geo():
    g = Geo('geometry.bc.mana_sprite', res=4, atlas_width=64, visible=(1, 1, (0, 0.4, 0)), seed=1104)
    skin = tex.Material(_r('3a8a5a', '58b07a', '7ad49a', 'a8f0c0', 'd8fff0'), noise=0.06, edge=0.85)
    dress = tex.Material(_r('1a5a3a', '24764c', '30925e', '40ae72'), noise=0.08)
    hair = tex.Material(_r('a0ffe0', 'c8fff0', 'f0fffa'), noise=0.08)
    wing = tex.Flat('b8fff0', alpha=255)
    eye = tex.Flat('1a1a3a')
    glow = tex.Flat('f0fff8')
    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 3, 0))
    g.bone('head', 'body', (0, 6, 0))
    for side, sx in (('R', -1), ('L', 1)):
        g.bone(f'wing{side}1', 'body', (sx * 0.8, 5.2, 0.8))
        g.bone(f'wing{side}2', 'body', (sx * 0.8, 4.2, 0.8))
    g.cube('body', (-1, 2, -0.8), (2, 4, 1.6), dress)
    g.cube('body', (-1.4, 2, -1.1), (2.8, 1.4, 2.2), dress)
    g.cube('head', (-1.6, 6, -1.6), (3.2, 3.2, 3.2), tex.PerFace(skin, north=tex.Painted(skin, {'north': lambda a, c: (a.__setitem__(
        (slice(int(a.shape[0] * 0.45), int(a.shape[0] * 0.7)), slice(int(a.shape[1] * 0.15), int(a.shape[1] * 0.4)), slice(0, 3)), rgb('1a1a3a')[:3]),
        a.__setitem__((slice(int(a.shape[0] * 0.45), int(a.shape[0] * 0.7)), slice(int(a.shape[1] * 0.6), int(a.shape[1] * 0.85)), slice(0, 3)), rgb('1a1a3a')[:3]), a)[2]})))
    g.cube('head', (-1.8, 8.4, -1.8), (3.6, 1.2, 3.6), hair)
    for sx in (-1, 1):
        g.box('head', (sx * 0.9, 10.4, -0.4), (0.3, 2.2, 0.3), eye, rotation=[-20, 0, sx * -20], pivot=(sx * 0.6, 9.4, 0))
        g.box('head', (sx * 1.3, 11.5, -0.8), (0.6, 0.6, 0.6), glow)
    for side, sx in (('R', -1), ('L', 1)):
        g.cube(f'wing{side}1', (sx * 0.8 - (4.2 if sx < 0 else 0), 5.2, 0.8), (4.2, 3.2, 0), wing)
        g.cube(f'wing{side}2', (sx * 0.8 - (3.2 if sx < 0 else 0), 2.4, 0.8), (3.2, 1.8, 0), wing)
    return g


def sprite_animations():
    buzz = 'math.sin(q.life_time * 2400.0)'
    return {'animation.bc.mana_sprite.fly': {'loop': True, 'bones': {
        'root': {'position': [0, '2.0 + math.sin(q.life_time * 160.0) * 1.0', 0]},
        'wingR1': {'rotation': [0, f'20.0 + {buzz} * 40.0', 0]}, 'wingL1': {'rotation': [0, f'-20.0 - {buzz} * 40.0', 0]},
        'wingR2': {'rotation': [0, f'10.0 - {buzz} * 30.0', 0]}, 'wingL2': {'rotation': [0, f'-10.0 + {buzz} * 30.0', 0]},
        'head': {'rotation': [0, 'math.sin(q.life_time * 60.0) * 15.0', 0]},
    }}}


def wisp_geo():
    g = Geo('geometry.bc.wisp', res=4, atlas_width=64, visible=(1, 1, (0, 0.5, 0)), seed=1105)
    core = tex.Flat('f0fbff')
    mid = tex.Energy(_r('2a6aa0', '4a9ad0', '8acaff', 'd0f0ff'), alpha=255)
    g.bone('root', pivot=(0, 0, 0))
    g.bone('orb', 'root', (0, 8, 0))
    g.bone('tail', 'orb', (0, 8, 0))
    g.box('orb', (0, 8, 0), (2, 2, 2), core, rotation=[45, 45, 0], pivot=(0, 8, 0))
    g.box('orb', (0, 8, 0), (3.4, 3.4, 3.4), mid, rotation=[0, 45, 45], pivot=(0, 8, 0))
    for k in range(3):
        s = 1.4 - k * 0.35
        g.box('tail', (0, 8 - k * 0.6, 2.4 + k * 1.8), (s, s, s), mid, rotation=[45, 45, 0], pivot=(0, 8 - k * 0.6, 2.4 + k * 1.8))
    return g


def wisp_animations():
    return {'animation.bc.wisp.float': {'loop': True, 'bones': {
        'orb': {'rotation': ['q.life_time * 90.0', 'q.life_time * 140.0', 0], 'scale': ['1.0 + math.sin(q.life_time * 300.0) * 0.15'] * 3,
                'position': [0, 'math.sin(q.life_time * 120.0) * 1.5', 0]},
        'tail': {'rotation': [0, 'math.sin(q.life_time * 90.0) * 20.0', 0]},
    }}}


# ======================================================================================
# the Rootwarden
# ======================================================================================
def _bark_face(a, ctx):
    h, w = a.shape[:2]
    a[int(h * 0.3):int(h * 0.42), int(w * 0.2):int(w * 0.4), :3] = rgb('9cff6a')[:3]
    a[int(h * 0.3):int(h * 0.42), int(w * 0.6):int(w * 0.8), :3] = rgb('9cff6a')[:3]
    a[int(h * 0.55):int(h * 0.75), int(w * 0.3):int(w * 0.7), :3] = rgb('120a06')[:3]
    return a


def rootwarden_geo():
    g = Geo('geometry.bc.rootwarden', res=2, atlas_width=128, visible=(4, 4, (0, 1.5, 0)), seed=1106)
    bark = tex.Wood(_r('1e140c', '2c1e12', '3c2a18', '4e3820', '62472a'))
    moss = tex.Material(_r('1a3a14', '24501c', '326a26', '428432'), noise=0.25, cell=1.2)
    leaves = tex.Material(_r('12300e', '1a4614', '24601c', '307a26', '3e9432'), noise=0.3, cell=1.0, edge=0.6)
    shroom = tex.Material(_r('6a0e0e', '9a1a16', 'c8302a', 'e8544a'), noise=0.1)
    face = tex.PerFace(bark, north=tex.Painted(bark, {'north': _bark_face}))
    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 14, 0))
    g.bone('head', 'body', (0, 30, 0))
    g.bone('rightArm', 'body', (-8, 27, 0))
    g.bone('leftArm', 'body', (8, 27, 0))
    g.bone('rightLeg', 'root', (-4, 14, 0))
    g.bone('leftLeg', 'root', (4, 14, 0))
    g.cube('body', (-7, 14, -5), (14, 16, 10), bark)
    g.cube('body', (-7.4, 22, -5.4), (6, 5, 10.8), moss)
    g.cube('head', (-5, 30, -5), (10, 9, 9), face)
    g.cube('head', (-7, 37, -6), (14, 6, 12), leaves)
    g.cube('head', (-5, 42, -4), (10, 4, 8), leaves)
    for sx in (-1, 1):
        g.box('head', (sx * 5.5, 44, 0), (1.4, 6, 1.4), bark, rotation=[0, 0, sx * -30], pivot=(sx * 4, 41, 0))
    g.box('body', (7.5, 30.5, 1), (2, 1.6, 2), shroom)
    g.box('body', (8.5, 29.4, -1.5), (1.4, 1.2, 1.4), shroom)
    for side, sx in (('right', -1), ('left', 1)):
        ax = sx * 8
        g.cube(f'{side}Arm', (ax - 2.5 if sx > 0 else ax - 2.5, 10, -2.5), (5, 18, 5), bark)
        for k in range(3):
            g.box(f'{side}Arm', (ax + (k - 1) * 1.6, 8.5, -1.5 + (k % 2)), (0.9, 4, 0.9), bark, rotation=[(k - 1) * 18, 0, (k - 1) * 14], pivot=(ax + (k - 1) * 1.2, 10, 0))
        g.cube(f'{side}Arm', (ax - 3, 22, -3), (6, 4, 6), leaves)
        lx = sx * 4
        g.cube(f'{side}Leg', (lx - 3, 0, -3), (6, 14, 6), bark)
        for k in range(3):
            a = (k - 1) * 40
            g.box(f'{side}Leg', (lx + math.sin(math.radians(a)) * 3.5, 0.8, -math.cos(math.radians(a)) * 3.5), (1.6, 1.6, 4), bark,
                  rotation=[0, -a, 0], pivot=(lx, 0.8, 0))
    return g


def rootwarden_animations():
    walk = 'math.cos(q.modified_distance_moved * 25.0) * 26.0 * q.modified_move_speed'
    return {
        'animation.bc.rootwarden.idle': {'loop': True, 'bones': {
            'body': {'rotation': ['math.sin(q.life_time * 40.0) * 2.0', 0, 'math.sin(q.life_time * 30.0) * 1.5']},
            'rightArm': {'rotation': ['math.sin(q.life_time * 40.0) * 4.0', 0, 6]},
            'leftArm': {'rotation': ['-math.sin(q.life_time * 40.0) * 4.0', 0, -6]},
            'head': {'rotation': [0, 'math.sin(q.life_time * 25.0) * 6.0', 0]},
        }},
        'animation.bc.rootwarden.walk': {'loop': True, 'bones': {
            'rightLeg': {'rotation': [walk, 0, 0]}, 'leftLeg': {'rotation': [f'-({walk})', 0, 0]},
            'rightArm': {'rotation': [f'-({walk}) * 0.6', 0, 0]}, 'leftArm': {'rotation': [f'({walk}) * 0.6', 0, 0]},
        }},
        'animation.bc.rootwarden.attack': {'animation_length': 0.9, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.35': [-160, 0, 15], '0.55': [-20, 0, 0], '0.9': [0, 0, 0]}},
            'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.35': [-160, 0, -15], '0.55': [-20, 0, 0], '0.9': [0, 0, 0]}},
            'body': {'rotation': {'0.0': [0, 0, 0], '0.35': [-10, 0, 0], '0.55': [18, 0, 0], '0.9': [0, 0, 0]}},
        }},
    }


# ======================================================================================
# the Hollow Knight
# ======================================================================================
def _hollow_visor(a, ctx):
    h, w = a.shape[:2]
    y = int(h * 0.42)
    a[y:y + max(1, h // 8), int(w * 0.15):int(w * 0.85), :3] = rgb('06060a')[:3]
    for ex in (int(w * 0.25), int(w * 0.62)):
        a[y:y + max(1, h // 8), ex:ex + max(1, w // 7), :3] = rgb('7ad0ff')[:3]
    for k in range(3):
        x = int(w * (0.3 + k * 0.17))
        a[int(h * 0.1):int(h * 0.35), x, :3] *= 0.5
    return a


def hollow_knight_geo():
    g = Geo('geometry.bc.hollow_knight', res=2, atlas_width=128, visible=(2, 3, (0, 1.2, 0)), seed=1107)
    _humanoid_bones(g)
    g.bone('grimoire', 'body', (8, 18, -4))
    robe = tex.Cloth(_r('0e0c12', '17141e', '211c2a', '2c2638', '3a3248'), folds=0.22)
    rust = tex.Metal(_r('1e1410', '2e1e16', '40281c', '54342a', '6a4636'), sheen=0.25, noise=0.14)
    iron = tex.Metal(P['blackiron'], sheen=0.3, noise=0.12)
    bone = tex.Material(P['bone'], noise=0.1)
    page = tex.Energy(_r('1a4a6a', '3a7aa0', '7ad0ff', 'c8f0ff'), alpha=255)
    cover = tex.Material(_r('140c08', '22160e', '342216'), noise=0.15)
    helm = tex.PerFace(iron, north=tex.Painted(iron, {'north': _hollow_visor}))
    g.cube('head', (-4, 24, -4), (8, 8, 8), helm)
    g.cube('head', (-4.4, 30.0, -4.4), (8.8, 2.4, 8.8), rust)
    g.box('head', (0, 33.6, 0.6), (1.2, 3.0, 6), tex.Cloth(P['red_cloth']), rotation=[-12, 0, 0], pivot=(0, 32, 0))    # a faded plume
    g.cube('body', (-4, 12, -2), (8, 12, 4), robe)
    g.cube('body', (-4.5, 16, -2.5), (9, 8, 5), rust)
    g.cube('body', (-4.6, 4, -2.6), (9.2, 9, 5.2), robe)                                # tattered robe skirt
    for sx in (-1, 1):
        g.cube('body', (sx * 4 - (3 if sx < 0 else 0), 21, -3), (3, 3.5, 6), rust)        # pauldrons
    for side, x0 in (('rightArm', -8), ('leftArm', 4)):
        g.cube(side, (x0, 12, -2), (4, 12, 4), robe)
        g.cube(side, (x0 - 0.2, 12, -2.2), (4.4, 4, 4.4), iron)
    for side, x0 in (('rightLeg', -3.9), ('leftLeg', -0.1)):
        g.cube(side, (x0, 0, -2), (4, 12, 4), tex.Cloth(_r('0a0a0e', '121218', '1c1c24')))
        g.cube(side, (x0 - 0.2, 0, -2.3), (4.4, 4.5, 4.6), iron)
    # a notched sword in the right hand
    g.cube('rightArm', (-6.5, 9.5, -0.6), (1.2, 3, 1.2), tex.Material(P['leather']))
    g.cube('rightArm', (-7.4, 12.2, -1.0), (3.0, 0.8, 2.0), rust)
    g.cube('rightArm', (-6.4, 13.0, -0.4), (1.0, 13, 0.8), tex.Metal(_r('3a3a40', '55555c', '72727a', '8e8e96'), sheen=0.4))
    # a cracked grimoire floating at its side
    g.box('grimoire', (8, 18, -4), (5, 6, 1.4), cover, rotation=[0, -20, 0], pivot=(8, 18, -4))
    g.box('grimoire', (8.1, 18, -4.8), (4.4, 5.4, 0.4), page, rotation=[0, -20, 0], pivot=(8, 18, -4))
    g.box('grimoire', (6.4, 17.6, -4.2), (0.6, 2.4, 1.6), bone, rotation=[0, -20, 0], pivot=(8, 18, -4))
    return g


def hollow_knight_animations():
    a = humanoid_animations('hollow_knight')
    a['animation.bc.hollow_knight.idle']['bones']['grimoire'] = {
        'position': [0, 'math.sin(q.life_time * 120.0) * 1.2', 0], 'rotation': [0, 'math.sin(q.life_time * 50.0) * 12.0', 0]}
    a['animation.bc.hollow_knight.idle']['bones']['head'] = {'rotation': [8, 'math.sin(q.life_time * 20.0) * 4.0', 'math.sin(q.life_time * 33.0) * 5.0']}
    a['animation.bc.hollow_knight.cast'] = {'animation_length': 0.9, 'bones': {
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.25': [-105, -10, -15], '0.6': [-95, 0, -5], '0.9': [0, 0, 0]}},
        'grimoire': {'position': {'0.0': [0, 0, 0], '0.25': [-2, 4, -3], '0.6': [-2, 4, -3], '0.9': [0, 0, 0]},
                     'rotation': {'0.0': [0, 0, 0], '0.25': [0, 70, 0], '0.6': [0, 70, 0], '0.9': [0, 0, 0]}},
    }}
    return a


# ======================================================================================
# the Wanderer (one shape, six looks)
# ======================================================================================
WANDERER_LOOKS = [
    # (cloak, hat, pack, trim)
    ('pilgrim', _r('5a5a60', '7a7a82', '9a9aa2', 'bcbcc4', 'dedee4'), _r('3a2a1a', '4e3a24', '644a30'), P['leather'], P['silver']),
    ('cartographer', _r('12301e', '1a4228', '245634', '2e6c42', '3a8452'), _r('3a2414', '54341c', '6e4626'), P['leather'], P['gold']),
    ('peddler', _r('3a1a0e', '5a2814', '7a3a1c', '9a5028', 'b86a36'), _r('2a2a2a', '3c3c3c', '505050'), _r('4a2a10', '643a18', '7e4c22'), P['gold']),
    ('hermit', _r('140a24', '22103a', '321850', '442268', '582e82'), _r('140a24', '22103a', '321850'), P['leather'], P['gold']),
    ('bard', _r('3a0a0e', '5e1016', '82181e', 'a6242a', 'c8383a'), _r('5a3a08', '7a520e', '9c6c18'), P['leather'], P['gold']),
    ('lost_knight', _r('070b1a', '0d1430', '142048', '1d2d62', '283c7c'), _r('2d313a', '434955', '5c6370'), P['leather'], P['silver']),
]


def wanderer_geo(idx):
    _, cloak_r, hat_r, pack_r, trim_r = WANDERER_LOOKS[idx]
    g = Geo('geometry.bc.wanderer', res=2, atlas_width=128, visible=(2, 3, (0, 1.2, 0)), seed=1108)
    _humanoid_bones(g)
    g.bone('staff', 'rightArm', (-6, 12, 0))
    skin = tex.Material(SKIN, noise=0.08, edge=0.85)
    cloak = tex.Cloth(cloak_r, folds=0.2)
    hat = tex.Material(hat_r, noise=0.12)
    pack = tex.Material(pack_r, noise=0.12)
    trim = tex.Metal(trim_r, sheen=0.5)
    wood = tex.Wood(P['wood'])
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(skin, {'north': _face(beard=idx in (0, 3))}))
    g.cube('head', (-6.5, 31, -6.5), (13, 0.8, 13), hat)                              # wide brim
    g.cube('head', (-4.2, 31.6, -4.2), (8.4, 4, 8.4), hat)
    g.cube('head', (-4.3, 31.8, -4.3), (8.6, 0.8, 8.6), trim)
    g.cube('body', (-4, 12, -2), (8, 12, 4), cloak)
    g.cube('body', (-4.5, 5, -2.5), (9, 19.2, 5), cloak)                              # long travelling coat
    g.cube('body', (-4.6, 13.5, -2.7), (9.2, 1.4, 5.4), tex.Material(P['leather']))
    g.box('body', (0, 14.2, -2.9), (1.6, 1.4, 0.6), trim)
    g.cube('body', (-3.5, 13, 2.5), (7, 9, 4), pack)                                  # backpack and bedroll
    g.cube('body', (-4.5, 22, 2.8), (9, 2.6, 3), tex.Cloth(_r('5a1a10', '7a2a18', '9a3a22')))
    for side, x0 in (('rightArm', -8), ('leftArm', 4)):
        g.cube(side, (x0, 12, -2), (4, 12, 4), cloak)
        g.cube(side, (x0 + 0.2, 12, -1.8), (3.6, 2, 3.6), skin)
    for side, x0 in (('rightLeg', -3.9), ('leftLeg', -0.1)):
        g.cube(side, (x0, 0, -2), (4, 12, 4), tex.Cloth(_r('1a1610', '262018', '332a20', '40362a')))
        g.cube(side, (x0 - 0.2, 0, -2.3), (4.4, 4, 4.6), tex.Material(_r('120c08', '1e1510', '2a1e16')))
    # a walking staff with a lantern hanging from its crook
    g.cube('staff', (-6.6, -2, -0.6), (1.2, 26, 1.2), wood)
    g.box('staff', (-5.0, 23.6, -0.0), (3.4, 1.2, 1.2), wood)
    g.cube('staff', (-4.2, 19.4, -1.1), (2.2, 3, 2.2), trim)
    g.cube('staff', (-3.9, 19.8, -0.8), (1.6, 2.2, 1.6), tex.Flat('ffd070'))
    return g


def wanderer_animations():
    a = humanoid_animations('wanderer')
    a['animation.bc.wanderer.idle']['bones']['rightArm'] = {'rotation': ['-18.0 + math.sin(q.life_time * 90.0) * 2.0', 0, 6]}
    a['animation.bc.wanderer.wave'] = {'animation_length': 1.2, 'bones': {
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-160, 0, -20], '0.45': [-160, 0, 10], '0.7': [-160, 0, -20], '0.95': [-160, 0, 10], '1.2': [0, 0, 0]}},
    }}
    return a


# ======================================================================================
# icons
# ======================================================================================
def _icon(fn, outline='0a0a0f'):
    a = tex.draw_layer(32, 32, fn, 4)
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    tex.outline(a, rgb(outline))
    return a


def v11_icons():
    def ring(d, s):
        d.ellipse([7 * s, 9 * s, 25 * s, 27 * s], outline=(214, 160, 40, 255), width=int(3.4 * s))
        d.ellipse([11 * s, 3 * s, 21 * s, 13 * s], fill=(60, 120, 230, 255))
        d.ellipse([13.5 * s, 5 * s, 17 * s, 8.5 * s], fill=(190, 225, 255, 255))
        d.arc([7 * s, 9 * s, 25 * s, 27 * s], 100, 170, fill=(255, 236, 150, 255), width=int(1.2 * s))

    def talisman(d, s):
        d.rounded_rectangle([8 * s, 5 * s, 24 * s, 28 * s], radius=3 * s, fill=(110, 116, 128, 255))
        d.rounded_rectangle([10 * s, 7 * s, 22 * s, 26 * s], radius=2 * s, fill=(84, 90, 102, 255))
        d.line([(16 * s, 9 * s), (16 * s, 23 * s)], fill=(96, 224, 255, 255), width=int(1.6 * s))
        d.line([(12 * s, 13 * s), (20 * s, 19 * s)], fill=(96, 224, 255, 255), width=int(1.6 * s))
        d.line([(20 * s, 13 * s), (12 * s, 19 * s)], fill=(96, 224, 255, 255), width=int(1.6 * s))
        d.line([(16 * s, 1 * s), (16 * s, 5 * s)], fill=(120, 80, 50, 255), width=int(1.2 * s))

    def idol(d, s):
        bone_c = (226, 216, 190, 255)
        d.ellipse([11 * s, 3 * s, 21 * s, 12 * s], fill=bone_c)
        d.polygon([(10 * s, 12 * s), (22 * s, 12 * s), (24 * s, 28 * s), (8 * s, 28 * s)], fill=bone_c)
        d.ellipse([13 * s, 6 * s, 15.5 * s, 8.5 * s], fill=(200, 40, 40, 255))
        d.ellipse([16.5 * s, 6 * s, 19 * s, 8.5 * s], fill=(200, 40, 40, 255))
        d.line([(10 * s, 18 * s), (22 * s, 18 * s)], fill=(150, 130, 100, 255), width=int(1.2 * s))
        d.line([(9 * s, 23 * s), (23 * s, 23 * s)], fill=(150, 130, 100, 255), width=int(1.2 * s))

    def eye(d, s):
        d.polygon([(16 * s, 3 * s), (27 * s, 16 * s), (16 * s, 29 * s), (5 * s, 16 * s)], fill=(60, 200, 190, 255))
        d.polygon([(16 * s, 5 * s), (23 * s, 16 * s), (16 * s, 13 * s)], fill=(160, 255, 236, 255))
        d.ellipse([11 * s, 11 * s, 21 * s, 21 * s], fill=(230, 250, 255, 255))
        d.ellipse([14 * s, 12 * s, 18 * s, 20 * s], fill=(20, 30, 50, 255))

    def fang(d, s):
        d.polygon([(9 * s, 4 * s), (21 * s, 4 * s), (19 * s, 14 * s), (13 * s, 29 * s), (11 * s, 16 * s)], fill=(236, 228, 210, 255))
        d.line([(12 * s, 6 * s), (13 * s, 26 * s)], fill=(255, 255, 250, 255), width=int(1.0 * s))
        d.rectangle([8 * s, 3 * s, 22 * s, 7 * s], fill=(150, 40, 30, 255))
        d.line([(8 * s, 5 * s), (22 * s, 5 * s)], fill=(214, 160, 40, 255), width=int(1.0 * s))

    def feather(d, s):
        d.polygon([(24 * s, 3 * s), (28 * s, 6 * s), (14 * s, 24 * s), (8 * s, 26 * s), (10 * s, 20 * s)], fill=(184, 240, 255, 255))
        d.polygon([(24 * s, 3 * s), (20 * s, 4 * s), (8 * s, 20 * s), (10 * s, 20 * s)], fill=(130, 210, 240, 255))
        d.line([(26 * s, 4 * s), (5 * s, 29 * s)], fill=(250, 255, 255, 255), width=int(1.2 * s))

    def explorer_map(d, s):
        d.polygon([(4 * s, 7 * s), (12 * s, 5 * s), (20 * s, 8 * s), (28 * s, 5 * s), (28 * s, 26 * s), (20 * s, 29 * s), (12 * s, 26 * s), (4 * s, 28 * s)],
                  fill=(226, 206, 156, 255))
        d.line([(12 * s, 5 * s), (12 * s, 26 * s)], fill=(180, 156, 110, 255), width=int(1 * s))
        d.line([(20 * s, 8 * s), (20 * s, 29 * s)], fill=(180, 156, 110, 255), width=int(1 * s))
        d.line([(7 * s, 22 * s), (11 * s, 17 * s), (16 * s, 19 * s), (21 * s, 13 * s)], fill=(120, 80, 50, 255), width=int(1.2 * s))
        d.rectangle([21 * s, 9 * s, 25 * s, 15 * s], fill=(70, 80, 100, 255))
        d.polygon([(20 * s, 9 * s), (23 * s, 6 * s), (26 * s, 9 * s)], fill=(60, 140, 220, 255))

    def journal(d, s):
        d.polygon([(6 * s, 3 * s), (26 * s, 4 * s), (25 * s, 27 * s), (21 * s, 25 * s), (18 * s, 29 * s), (14 * s, 26 * s), (7 * s, 29 * s)], fill=(236, 226, 196, 255))
        for k in range(6):
            d.line([(9 * s, (8 + k * 3) * s), (23 * s, (8 + k * 3) * s)], fill=(110, 90, 70, 255), width=int(0.8 * s))
        d.ellipse([18 * s, 18 * s, 23 * s, 23 * s], fill=(150, 50, 40, 255))

    def star(d, s):
        pts = []
        for k in range(10):
            r = (13 if k % 2 == 0 else 5.5) * s
            a = k / 10 * math.tau - math.pi / 2
            pts.append((16 * s + math.cos(a) * r, 16 * s + math.sin(a) * r))
        d.polygon(pts, fill=(255, 226, 90, 255))
        d.ellipse([12 * s, 12 * s, 20 * s, 20 * s], fill=(255, 250, 220, 255))

    def dust(d, s):
        d.polygon([(9 * s, 14 * s), (23 * s, 14 * s), (26 * s, 28 * s), (6 * s, 28 * s)], fill=(120, 80, 50, 255))
        d.rectangle([11 * s, 10 * s, 21 * s, 14 * s], fill=(170, 130, 80, 255))
        for x, y, r in ((10, 5, 2), (17, 3, 1.6), (23, 7, 1.8), (14, 19, 1.4), (20, 22, 1.4), (8, 9, 1.0)):
            d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s], fill=(160, 255, 200, 255))

    def tooth(d, s):
        d.polygon([(7 * s, 5 * s), (25 * s, 5 * s), (21 * s, 12 * s), (16 * s, 29 * s), (11 * s, 12 * s)], fill=(240, 232, 214, 255))
        d.polygon([(7 * s, 5 * s), (25 * s, 5 * s), (24 * s, 8 * s), (8 * s, 8 * s)], fill=(160, 40, 50, 255))
        d.line([(13 * s, 10 * s), (16 * s, 25 * s)], fill=(255, 255, 255, 255), width=int(1 * s))

    def ember(d, s):
        d.ellipse([8 * s, 14 * s, 24 * s, 28 * s], fill=(30, 26, 34, 255))
        d.polygon([(16 * s, 2 * s), (22 * s, 14 * s), (19 * s, 20 * s), (13 * s, 20 * s), (10 * s, 14 * s)], fill=(90, 170, 255, 255))
        d.polygon([(16 * s, 8 * s), (19 * s, 15 * s), (16 * s, 19 * s), (13 * s, 15 * s)], fill=(200, 240, 255, 255))
        d.line([(11 * s, 22 * s), (20 * s, 25 * s)], fill=(60, 120, 200, 255), width=int(1 * s))

    def core(d, s):
        d.polygon([(16 * s, 2 * s), (24 * s, 12 * s), (16 * s, 28 * s), (8 * s, 12 * s)], fill=(96, 224, 255, 255))
        d.polygon([(16 * s, 4 * s), (20 * s, 12 * s), (16 * s, 22 * s)], fill=(200, 250, 255, 255))
        d.rectangle([7 * s, 20 * s, 25 * s, 25 * s], fill=(110, 116, 128, 255))
        d.rectangle([7 * s, 20 * s, 25 * s, 21.5 * s], fill=(214, 160, 40, 255))
    return {'relic_ring': _icon(ring), 'relic_talisman': _icon(talisman), 'relic_idol': _icon(idol), 'relic_eye': _icon(eye),
            'relic_fang': _icon(fang), 'relic_feather': _icon(feather), 'explorer_map': _icon(explorer_map), 'journal_page': _icon(journal),
            'star_fragment': _icon(star), 'sprite_dust': _icon(dust), 'mimic_tooth': _icon(tooth), 'hollow_ember': _icon(ember), 'spire_core': _icon(core)}


def wyvern_scale_icon(d, s):
    d.polygon([(16 * s, 3 * s), (27 * s, 12 * s), (24 * s, 25 * s), (16 * s, 29 * s), (8 * s, 25 * s), (5 * s, 12 * s)], fill=(60, 140, 80, 255))
    d.polygon([(16 * s, 6 * s), (23 * s, 13 * s), (16 * s, 25 * s)], fill=(110, 200, 120, 255))
    d.line([(16 * s, 5 * s), (16 * s, 27 * s)], fill=(214, 160, 40, 255), width=int(1.2 * s))
    d.arc([8 * s, 14 * s, 24 * s, 30 * s], 200, 340, fill=(30, 80, 40, 255), width=int(1 * s))


# ======================================================================================
# block textures (16 x 16)
# ======================================================================================
def spawner_texture():
    a = tex.new(32, 32, rgb('140a20'))
    rng = np.random.default_rng(1109)
    a[..., :3] = np.array(rgb('1a0c2a')[:3]) * (0.8 + rng.random((32, 32, 1)) * 0.3)
    # a glowing heart behind the bars
    yy, xx = np.mgrid[0:32, 0:32]
    d = np.sqrt((yy - 15.5) ** 2 + (xx - 15.5) ** 2)
    glow = np.clip(1 - d / 11, 0, 1)[..., None]
    a[..., :3] = a[..., :3] * (1 - glow) + np.array(rgb('c070ff')[:3]) * glow
    bar = np.array(rgb('2a2a34')[:3])
    hi = np.array(rgb('5a5a6a')[:3])
    for k in range(0, 32, 8):
        a[:, k:k + 2, :3] = bar
        a[k:k + 2, :, :3] = bar
        a[:, k, :3] = hi
        a[k, :, :3] = hi
    a[..., 3] = 255
    return a


def obelisk_texture():
    a = tex.new(32, 32, rgb('202028'))
    rng = np.random.default_rng(1110)
    a[..., :3] = np.array(rgb('2b2b35')[:3]) * (0.85 + rng.random((32, 32, 1)) * 0.25)
    c = np.array(rgb('60e0ff')[:3])
    for (y0, x0, y1, x1) in ((6, 15, 26, 17), (10, 9, 12, 23), (18, 10, 20, 22), (24, 12, 26, 20), (6, 11, 8, 21)):
        a[y0:y1, x0:x1, :3] = c
    a[0, :, :3] *= 1.3
    a[:, 0, :3] *= 1.2
    a[-1, :, :3] *= 0.7
    a[..., 3] = 255
    return np.clip(a, 0, 255)
