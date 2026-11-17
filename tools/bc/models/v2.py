"""v0.2.0 models and animations: Raider Gunner, Tidewatch Marksman, Hellhound, Mana Wraith, the Fallen Captain,
extra animation sets for knights / companions, enemies and bosses, and new item icons. All designs are original."""
from __future__ import annotations

import math

import numpy as np

from .. import tex
from ..geo import Geo
from ..tex import P, rgb
from .sea import IRON, SKIN, _face, _humanoid_bones, humanoid_animations

STEEL = tex.ramp('3b4250', '5a6372', '7d8796', 'a3adbb', 'c9d1dc', 'eef2f7')
WOOD = tex.ramp('2a180c', '3e2414', '54321c', '6a4226', '805230')


def _musket(g, bone, x=-6):
    """A long gun gripped in the right hand along the arm: barrel points down at rest, forward when aiming."""
    g.bone('gun', bone, (x, 12.5, 0))
    wood = tex.Wood(WOOD)
    iron = tex.Metal(IRON, sheen=0.3)
    brass = tex.Metal(P['gold'])
    g.cube('gun', (x - 0.8, 11.0, -4.0), (1.6, 6.0, 2.4), wood)          # stock along the forearm
    g.cube('gun', (x - 0.6, 3.0, -3.6), (1.2, 8.0, 1.6), wood)           # fore-end
    g.cube('gun', (x - 0.45, -6.0, -3.35), (0.9, 17.0, 0.9), iron)       # barrel
    g.cube('gun', (x - 0.7, 10.0, -4.6), (1.4, 1.4, 1.4), brass)         # lock
    g.cube('gun', (x - 0.6, 9.2, -2.6), (1.2, 0.6, 1.2), iron)           # trigger guard


def gunner_geo():
    g = Geo('geometry.bc.raider_gunner', res=2, atlas_width=128, visible=(2, 3, (0, 1.2, 0)))
    _humanoid_bones(g)
    skin = tex.Material(SKIN, noise=0.08, edge=0.85)
    coat = tex.Cloth(tex.ramp('2a1a10', '3e2818', '563822', '6e4a2e', '86603c'), folds=0.18)
    shirt = tex.Cloth(P['white_cloth'], folds=0.1)
    hat = tex.Material(tex.ramp('0c0a08', '1a1612', '28221c', '362e26'), noise=0.1)
    belt = tex.Material(P['leather'], noise=0.1)
    pants = tex.Cloth(tex.ramp('1a1610', '262018', '332a20', '40362a'))
    boots = tex.Material(tex.ramp('120c08', '1e1510', '2a1e16', '382a1e'), noise=0.1)
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(skin, {'north': _face(beard=True, scar=True)}))
    # tricorne hat
    g.cube('head', (-5.5, 31.0, -5.5), (11, 1.2, 11), hat)
    g.cube('head', (-3.8, 32.0, -3.8), (7.6, 3.0, 7.6), hat)
    for a in (0, 120, 240):
        r = math.radians(a)
        g.box('head', (math.sin(r) * 5.0, 32.6, -math.cos(r) * 5.0), (5.5, 2.4, 1.0), hat, rotation=[0, -a, 0], pivot=(math.sin(r) * 5.0, 32.6, -math.cos(r) * 5.0))
    g.cube('body', (-4, 12, -2), (8, 12, 4), shirt)
    g.cube('body', (-4.5, 6, -2.5), (9, 18, 5), tex.Painted(coat, {'north': lambda a, c: (a.__setitem__((slice(None), slice(a.shape[1] // 2 - 1, a.shape[1] // 2 + 1), 3), 0), a)[1]}))
    g.cube('body', (-4.7, 12.5, -2.7), (9.4, 1.6, 5.4), belt)
    g.box('body', (2.5, 14, -3.0), (2.0, 2.4, 1.0), tex.Metal(P['gold']))   # powder flask
    for side, x0 in (('rightArm', -8), ('leftArm', 4)):
        g.cube(side, (x0 - 0.3, 14, -2.3), (4.6, 10, 4.6), coat)
        g.cube(side, (x0, 12, -2), (4, 2, 4), skin)
    g.cube('rightLeg', (-3.9, 3, -2), (4, 9, 4), pants)
    g.cube('leftLeg', (-0.1, 3, -2), (4, 9, 4), pants)
    g.cube('rightLeg', (-4.1, 0, -2.3), (4.4, 5, 4.6), boots)
    g.cube('leftLeg', (-0.3, 0, -2.3), (4.4, 5, 4.6), boots)
    _musket(g, 'rightArm')
    return g


def marksman_geo():
    g = Geo('geometry.bc.tidewatch_marksman', res=2, atlas_width=128, visible=(2, 3, (0, 1.2, 0)))
    _humanoid_bones(g)
    skin = tex.Material(SKIN[1:], noise=0.08, edge=0.85)
    white = tex.Cloth(P['white_cloth'], folds=0.1)
    navy = tex.Cloth(P['navy'], folds=0.14)
    gold = tex.Metal(P['gold'])
    boots = tex.Material(tex.ramp('08080a', '121216', '1c1c22', '28282f'), noise=0.1)
    shako = tex.Painted(tex.Material(P['navy'], noise=0.08), {'north': lambda a, c: (a.__setitem__((slice(a.shape[0] // 3, a.shape[0] // 3 + 2), slice(a.shape[1] // 3, 2 * a.shape[1] // 3), slice(0, 3)), rgb('f0c24a')[:3]), a)[1]})
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(skin, {'north': _face()}))
    g.cube('head', (-3.6, 31.4, -3.6), (7.2, 5.5, 7.2), shako)
    g.cube('head', (-4.0, 31.0, -5.2), (8, 0.8, 4), tex.Material(tex.ramp('08080a', '121216')))   # visor
    g.box('head', (0, 37.6, -3.0), (1.2, 2.4, 1.2), tex.Material(P['white_cloth']))              # plume
    g.cube('body', (-4, 12, -2), (8, 12, 4), white)
    g.cube('body', (-4.4, 13.5, -2.4), (8.8, 10.8, 4.8), navy)
    g.cube('body', (-4.6, 13, -2.6), (9.2, 1.6, 5.2), tex.Material(P['leather']))
    g.cube('body', (-0.6, 13.5, -2.6), (1.2, 10.5, 0.4), gold)
    g.cube('body', (-4.5, 16.5, 2.4), (9, 1.2, 1.0), tex.Material(P['leather']), rotation=[0, 0, 35], pivot=(0, 19, 2.4))   # strap
    for side, x0 in (('rightArm', -8), ('leftArm', 4)):
        g.cube(side, (x0 - 0.4, 14, -2.4), (4.8, 10, 4.8), navy)
        g.cube(side, (x0 - 0.5, 14, -2.5), (5.0, 1.4, 5.0), white)
        g.cube(side, (x0, 12, -2), (4, 2, 4), skin)
    g.cube('rightLeg', (-3.9, 3, -2), (4, 9, 4), white)
    g.cube('leftLeg', (-0.1, 3, -2), (4, 9, 4), white)
    g.cube('rightLeg', (-4.1, 0, -2.3), (4.4, 5, 4.6), boots)
    g.cube('leftLeg', (-0.3, 0, -2.3), (4.4, 5, 4.6), boots)
    _musket(g, 'rightArm')
    return g


def gun_animations(prefix):
    anims = humanoid_animations(prefix)
    anims[f'animation.bc.{prefix}.aim'] = {'animation_length': 1.0, 'bones': {
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.15': [-88, -8, 0], '0.8': [-88, -8, 0], '1.0': [0, 0, 0]}},
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.15': [-80, 35, 0], '0.8': [-80, 35, 0], '1.0': [0, 0, 0]}},
        'head': {'rotation': {'0.0': [0, 0, 0], '0.15': [5, -10, 0], '1.0': [0, 0, 0]}},
    }}
    anims[f'animation.bc.{prefix}.shoot'] = {'animation_length': 0.4, 'bones': {
        'rightArm': {'rotation': {'0.0': [-88, -8, 0], '0.05': [-110, -8, 0], '0.4': [-60, 0, 0]}},
        'leftArm': {'rotation': {'0.0': [-80, 35, 0], '0.05': [-100, 35, 0], '0.4': [-40, 10, 0]}},
        'body': {'rotation': {'0.0': [0, 0, 0], '0.05': [-6, 0, 0], '0.4': [0, 0, 0]}},
    }}
    anims[f'animation.bc.{prefix}.throw'] = {'animation_length': 0.6, 'bones': {
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-170, 0, -10], '0.35': [-50, 0, 0], '0.6': [0, 0, 0]}},
        'body': {'rotation': {'0.0': [0, 0, 0], '0.2': [-8, 15, 0], '0.35': [10, -10, 0], '0.6': [0, 0, 0]}},
    }}
    return anims


# ======================================================================================
# Hellhound (devil beast, hunts in packs)
# ======================================================================================
def _hound_eyes(a, ctx):
    h, w = a.shape[:2]
    for ex in (int(w * 0.15), int(w * 0.65)):
        a[int(h * 0.3):int(h * 0.3) + 2, ex:ex + max(2, int(w * 0.2)), :3] = rgb('ffb030')[:3]
        a[int(h * 0.3):int(h * 0.3) + 2, ex:ex + max(2, int(w * 0.2)), 3] = 130
    return a


def _ember_cracks(a, ctx):
    h, w = a.shape[:2]
    rng = np.random.default_rng(ctx.seed)
    for _ in range(max(1, (h * w) // 60)):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        a[y, x, :3] = rgb('ff6a1a')[:3]
        a[y, x, 3] = 130
    return a


def hellhound_geo():
    g = Geo('geometry.bc.hellhound', res=2, atlas_width=128, visible=(3, 2, (0, 0.8, 0)))
    hide = tex.Painted(tex.Material(tex.ramp('0c0606', '1a0c0c', '2a1414', '3c1c1a', '502622'), noise=0.25, edge=0.75), {'*': _ember_cracks})
    flame = tex.Energy(tex.ramp('8a1a00', 'd04a08', 'ff8a2a', 'ffd08a', 'fff4d0'), alpha=135)
    horn = tex.Material(P['bone'], noise=0.06)
    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 11, 0))
    g.bone('neck', 'body', (0, 13, -7))
    g.bone('head', 'neck', (0, 15, -10))
    g.bone('jaw', 'head', (0, 13, -11))
    g.bone('tail', 'body', (0, 13, 8))
    for name, x, z in (('legFR', -3, -5), ('legFL', 3, -5), ('legBR', -3, 6), ('legBL', 3, 6)):
        g.bone(name, 'root', (x, 9, z))
        g.cube(name, (x - 1.5, 0, z - 1.5), (3, 9, 3), hide)
        g.cube(name, (x - 1.8, 0, z - 2.4), (3.6, 1.4, 3.6), hide)
    g.cube('body', (-4, 8, -7), (8, 7, 15), hide)
    g.cube('body', (-4.5, 9, -7.5), (9, 7, 6), hide)                       # chest
    for k in range(5):
        g.box('body', (0, 15.5 + (k % 2) * 0.5, -5 + k * 3), (1.6, 3.5 + (k % 2), 1.6), flame, rotation=[-20, 0, 0], pivot=(0, 15, -5 + k * 3))
    g.cube('neck', (-2.5, 11.5, -10.5), (5, 5, 5), hide, rotation=[-25, 0, 0], pivot=(0, 13, -8))
    g.cube('head', (-3, 13, -15), (6, 5, 6), tex.Painted(hide, {'north': _hound_eyes}))
    g.cube('head', (-2, 13.2, -18.5), (4, 2.6, 4), hide)                    # snout
    g.cube('jaw', (-1.8, 11.6, -18.2), (3.6, 1.6, 4.2), hide)
    for sx in (-1, 1):
        g.box('head', (sx * 2.4, 19.5, -12.5), (1.2, 4, 1.2), horn, rotation=[-35, 0, sx * -20], pivot=(sx * 2.4, 18, -12.5))
        g.box('head', (sx * 2.6, 18.5, -11), (1.6, 2.2, 1.0), hide, rotation=[0, 0, sx * -15], pivot=(sx * 2.6, 17.5, -11))
    g.cube('tail', (-0.8, 12.2, 8), (1.6, 1.6, 8), hide, rotation=[-35, 0, 0], pivot=(0, 13, 8))
    g.box('tail', (0, 17.5, 14.5), (2.4, 4, 2.4), flame, rotation=[-35, 0, 0], pivot=(0, 16, 14))
    return g


def hellhound_animations():
    walk = 'math.cos(q.modified_distance_moved * 40.0) * 40.0 * q.modified_move_speed'
    return {
        'animation.bc.hellhound.idle': {'loop': True, 'bones': {
            'body': {'scale': [1, '1.0 + math.sin(q.life_time * 200.0) * 0.02', 1]},
            'tail': {'rotation': [0, 'math.sin(q.life_time * 250.0) * 15.0', 0]},
            'jaw': {'rotation': ['math.max(0.0, math.sin(q.life_time * 120.0)) * 10.0', 0, 0]},
        }},
        'animation.bc.hellhound.walk': {'loop': True, 'bones': {
            'legFR': {'rotation': [walk, 0, 0]}, 'legBL': {'rotation': [walk, 0, 0]},
            'legFL': {'rotation': [f'-({walk})', 0, 0]}, 'legBR': {'rotation': [f'-({walk})', 0, 0]},
            'body': {'rotation': [f'math.sin(q.modified_distance_moved * 80.0) * 3.0 * q.modified_move_speed', 0, 0]},
        }},
        'animation.bc.hellhound.look_at_target': {'loop': True, 'bones': {'head': {'rotation': ['q.target_x_rotation * 0.7', 'q.target_y_rotation * 0.7', 0]}}},
        'animation.bc.hellhound.bite': {'animation_length': 0.45, 'bones': {
            'neck': {'rotation': {'0.0': [0, 0, 0], '0.15': [-25, 0, 0], '0.25': [20, 0, 0], '0.45': [0, 0, 0]}},
            'jaw': {'rotation': {'0.0': [0, 0, 0], '0.15': [35, 0, 0], '0.25': [0, 0, 0]}},
            'body': {'position': {'0.0': [0, 0, 0], '0.2': [0, 0, -2.5], '0.45': [0, 0, 0]}},
        }},
        'animation.bc.hellhound.howl': {'animation_length': 1.4, 'bones': {
            'neck': {'rotation': {'0.0': [0, 0, 0], '0.3': [-55, 0, 0], '1.1': [-55, 0, 0], '1.4': [0, 0, 0]}},
            'jaw': {'rotation': {'0.0': [0, 0, 0], '0.3': [25, 0, 0], '1.1': [25, 0, 0], '1.4': [0, 0, 0]}},
        }},
    }


# ======================================================================================
# Mana Wraith (night spirit that drains mana)
# ======================================================================================
def _wraith_face(a, ctx):
    h, w = a.shape[:2]
    a[:, :, :3] = rgb('05080a')[:3]
    for ex in (int(w * 0.22), int(w * 0.6)):
        a[int(h * 0.42):int(h * 0.42) + 2, ex:ex + max(2, int(w * 0.18)), :3] = rgb('90ffe8')[:3]
        a[int(h * 0.42):int(h * 0.42) + 2, ex:ex + max(2, int(w * 0.18)), 3] = 130
    return a


def _tatter(a, ctx):
    h, w = a.shape[:2]
    rng = np.random.default_rng(ctx.seed)
    for x in range(w):
        cut = int(rng.integers(0, max(1, h // 3)))
        if cut:
            a[h - cut:, x, 3] = 0
    return a


def wraith_geo():
    g = Geo('geometry.bc.mana_wraith', res=2, atlas_width=128, visible=(3, 3, (0, 1.4, 0)))
    robe = tex.Painted(tex.Cloth(tex.ramp('06100e', '0c1c1a', '142a28', '1e3a36', '2a4c48'), folds=0.25), {'*': _tatter})
    glow = tex.Energy(tex.ramp('0a4a40', '1a8a7a', '50e0c8', '90ffe8', 'e8fffa'), alpha=135)
    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 16, 0))
    g.bone('head', 'body', (0, 30, 0))
    g.bone('rightArm', 'body', (-5, 28, 0))
    g.bone('leftArm', 'body', (5, 28, 0))
    g.bone('tail', 'body', (0, 14, 0))
    g.cube('head', (-4, 29, -4.5), (8, 9, 8), tex.PerFace(robe, north=tex.Painted(robe, {'north': _wraith_face})))
    g.cube('head', (-4.4, 34, -4.0), (8.8, 4.5, 8.8), robe)
    g.cube('body', (-5, 16, -3), (10, 13, 6), robe)
    g.box('body', (0, 24, -3.2), (3, 3, 0.4), glow, rotation=[0, 0, 45], pivot=(0, 24, -3.2))
    g.cube('tail', (-4.5, 6, -2.5), (9, 10, 5), robe)
    g.cube('tail', (-3.2, -1, -1.8), (6.4, 7, 3.6), robe)
    for side, x0 in (('rightArm', -9), ('leftArm', 5)):
        g.cube(side, (x0, 17, -2), (4, 11, 4), robe)
        g.cube(side, (x0 + 0.5, 14, -1.5), (3, 3, 3), glow)
        for k in range(3):
            g.box(side, (x0 + 0.8 + k * 1.2, 12.5, -1), (0.6, 3, 0.6), glow, rotation=[-15, 0, 0], pivot=(x0 + 0.8 + k * 1.2, 14, -1))
    return g


def wraith_animations():
    return {
        'animation.bc.mana_wraith.float': {'loop': True, 'bones': {
            'root': {'position': [0, '4.0 + math.sin(q.life_time * 100.0) * 1.5', 0]},
            'tail': {'rotation': ['10.0 + math.sin(q.life_time * 150.0) * 8.0', 'math.sin(q.life_time * 90.0) * 10.0', 0]},
            'rightArm': {'rotation': ['-20.0 + math.sin(q.life_time * 110.0) * 10.0', 0, 10]},
            'leftArm': {'rotation': ['-20.0 - math.sin(q.life_time * 110.0) * 10.0', 0, -10]},
        }},
        'animation.bc.mana_wraith.look_at_target': {'loop': True, 'bones': {'head': {'rotation': ['q.target_x_rotation', 'q.target_y_rotation', 0]}}},
        'animation.bc.mana_wraith.cast': {'animation_length': 0.8, 'bones': {
            'rightArm': {'rotation': {'0.0': [-20, 0, 10], '0.2': [-100, -20, 0], '0.6': [-95, -15, 0], '0.8': [-20, 0, 10]}},
            'leftArm': {'rotation': {'0.0': [-20, 0, -10], '0.2': [-100, 20, 0], '0.6': [-95, 15, 0], '0.8': [-20, 0, -10]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.2': [-15, 0, 0], '0.8': [0, 0, 0]}},
        }},
    }


# ======================================================================================
# The Fallen Captain (boss): a Magic Knight captain corrupted by a devil
# ======================================================================================
def _captain_face(a, ctx):
    h, w = a.shape[:2]
    ey = int(h * 0.48)
    for ex in (int(w * 0.19), int(w * 0.62)):
        a[ey:ey + 2, ex:ex + int(w * 0.18), :3] = rgb('ff2a2a')[:3]
        a[ey:ey + 2, ex:ex + int(w * 0.18), 3] = 130
    for y in range(ey + 2, h):
        x = int(w * 0.25) + (y % 2)
        a[y, x, :3] = rgb('40080c')[:3]
    a[int(h * 0.8), int(w * 0.35):int(w * 0.65), :3] = rgb('200408')[:3]
    return a


def _corrupt(a, ctx):
    h, w = a.shape[:2]
    rng = np.random.default_rng(ctx.seed)
    for _ in range(max(1, (h * w) // 70)):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        L = int(rng.integers(2, 5))
        for i in range(L):
            yy = min(h - 1, y + i)
            xx = min(w - 1, x + (i % 2))
            a[yy, xx, :3] = rgb('d0202a')[:3]
            a[yy, xx, 3] = 130
    return a


def fallen_captain_geo():
    g = Geo('geometry.bc.fallen_captain', res=2, atlas_width=256, visible=(4, 4, (0, 1.4, 0)))
    _humanoid_bones(g)
    g.bone('cape', 'body', (0, 24, 2.6))
    g.bone('book', 'body', (8, 26, 0))
    g.bone('blade', 'rightArm', (-6, 12.5, 0))
    skin = tex.Material(tex.ramp('3a3036', '4e4248', '62565c', '766a70'), noise=0.1, edge=0.8)
    armor = tex.Painted(tex.Metal(tex.ramp('0a0a0e', '16161c', '24242c', '34343e', '4a4a56'), sheen=0.4), {'*': _corrupt})
    cloth = tex.Painted(tex.Cloth(tex.ramp('0a0204', '180408', '28080e', '3a0c14'), folds=0.2), {'*': _tatter})
    gold = tex.Metal(tex.ramp('3a2606', '5a3c0a', '7a5410', '9c6e18'))
    horn = tex.Material(tex.ramp('0a0806', '1c1610', '3a3024', '5a4a38'), noise=0.08)
    hair = tex.Material(tex.ramp('c8c8d0', 'e0e0e8', 'f4f4f8'), noise=0.15)
    steel = tex.Painted(tex.Metal(STEEL, sheen=0.6), {'*': _corrupt})
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(skin, {'north': _captain_face}))
    g.cube('head', (-4.3, 30.4, -4.3), (8.6, 2.2, 8.6), hair)
    g.cube('head', (-4.3, 24.5, 2.6), (8.6, 7, 1.8), hair)
    g.box('head', (-3, 34, -1), (1.4, 5, 1.4), horn, rotation=[-15, 0, 25], pivot=(-3, 32, -1))
    g.box('head', (3, 33, -1), (1.4, 2.6, 1.4), horn, rotation=[-15, 0, -25], pivot=(3, 32, -1))   # broken horn
    g.cube('body', (-4.4, 12, -2.4), (8.8, 12.4, 4.8), armor)
    g.cube('body', (-4.8, 21, -2.8), (9.6, 3.6, 5.6), armor)
    g.cube('body', (-0.8, 15, -2.9), (1.6, 6, 0.4), gold)
    g.cube('cape', (-5.5, 3.0, 2.6), (11, 21, 0.8), cloth)
    for side, x0 in (('rightArm', -8), ('leftArm', 4)):
        g.cube(side, (x0 - 0.4, 12, -2.4), (4.8, 12, 4.8), armor)
        g.cube(side, (x0 - 0.9, 20, -2.9), (5.8, 4.4, 5.8), armor)
        g.box(side, ((x0 + 2) + (-2 if x0 < 0 else 2), 25.5, 0), (1.2, 3, 1.2), horn, rotation=[0, 0, -30 if x0 < 0 else 30], pivot=(x0 + 2, 24, 0))
    for side, x0 in (('rightLeg', -3.9), ('leftLeg', -0.1)):
        g.cube(side, (x0 - 0.2, 0, -2.2), (4.4, 12, 4.4), armor)
    g.cube('blade', (-6.35, 11.3, -17.5), (0.7, 1.8, 16), steel)
    g.cube('blade', (-6.9, 10.9, -1.6), (1.8, 2.6, 0.9), gold)
    g.cube('blade', (-6.5, 11.4, -0.6), (1.0, 1.4, 3.4), tex.Material(P['leather']))
    g.cube('book', (8.5, 24, -2.5), (1.8, 6, 5), tex.Painted(tex.Material(tex.ramp('10040a', '200810', '300c18')), {'*': _corrupt}))
    g.box('book', (9.5, 27, 0), (2.4, 2.4, 0.4), tex.Energy(tex.ramp('5a0008', 'b0101a', 'ff4a3a', 'ffc8a0'), alpha=130), rotation=[0, 90, 45], pivot=(9.5, 27, 0))
    return g


def fallen_captain_animations():
    anims = humanoid_animations('fallen_captain')
    anims['animation.bc.fallen_captain.idle']['bones']['cape'] = {'rotation': ['6.0 + math.sin(q.life_time * 110.0) * 3.0', 0, 0]}
    anims['animation.bc.fallen_captain.idle']['bones']['book'] = {'position': [0, 'math.sin(q.life_time * 140.0) * 1.2', 0], 'rotation': [0, 'q.life_time * 40.0', 0]}
    anims['animation.bc.fallen_captain.walk']['bones']['cape'] = {'rotation': ['math.clamp(q.modified_move_speed * 80.0, 0.0, 55.0)', 0, 0]}
    anims['animation.bc.fallen_captain.slash'] = {'animation_length': 0.5, 'bones': {
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.12': [-160, 40, 30], '0.25': [-40, -50, -10], '0.5': [0, 0, 0]}},
        'body': {'rotation': {'0.0': [0, 0, 0], '0.12': [0, 30, 0], '0.25': [0, -35, 0], '0.5': [0, 0, 0]}},
    }}
    anims['animation.bc.fallen_captain.cast'] = {'animation_length': 0.9, 'bones': {
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-150, 0, -25], '0.7': [-140, 0, -20], '0.9': [0, 0, 0]}},
        'book': {'position': {'0.0': [0, 0, 0], '0.2': [-4, 6, -4], '0.7': [-4, 6, -4], '0.9': [0, 0, 0]}},
        'head': {'rotation': {'0.0': [0, 0, 0], '0.2': [-20, 0, 0], '0.9': [0, 0, 0]}},
    }}
    anims['animation.bc.fallen_captain.roar'] = {'animation_length': 1.4, 'bones': {
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.3': [-30, 0, 60], '1.1': [-30, 0, 60], '1.4': [0, 0, 0]}},
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.3': [-30, 0, -60], '1.1': [-30, 0, -60], '1.4': [0, 0, 0]}},
        'head': {'rotation': {'0.0': [0, 0, 0], '0.3': [-35, 0, 0], '1.1': [-35, 0, 0], '1.4': [0, 0, 0]}},
        'body': {'rotation': {'0.0': [0, 0, 0], '0.3': [-12, 0, 0], '1.4': [0, 0, 0]}},
    }}
    anims['animation.bc.fallen_captain.parry'] = {'animation_length': 0.35, 'bones': {
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.08': [-100, 60, 0], '0.35': [0, 0, 0]}},
        'body': {'rotation': {'0.0': [0, 0, 0], '0.08': [0, 25, 0], '0.35': [0, 0, 0]}},
    }}
    return anims


# ======================================================================================
# extra animation sets
# ======================================================================================
def knight_extra_animations():
    """Cast variants, dodges, reactions and emotes for Magic Knights and companions."""
    return {
        'animation.bc.magic_knight.cast_raise': {'animation_length': 0.9, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-165, 0, 20], '0.7': [-160, 0, 15], '0.9': [0, 0, 0]}},
            'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-165, 0, -20], '0.7': [-160, 0, -15], '0.9': [0, 0, 0]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.2': [-20, 0, 0], '0.9': [0, 0, 0]}},
            'cape': {'rotation': {'0.0': [4, 0, 0], '0.2': [30, 0, 0], '0.9': [4, 0, 0]}},
        }},
        'animation.bc.magic_knight.channel': {'animation_length': 1.0, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.15': [-90, 15, 0], '0.85': [-88, 12, 0], '1.0': [0, 0, 0]}},
            'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.15': [-90, -15, 0], '0.85': [-88, -12, 0], '1.0': [0, 0, 0]}},
            'body': {'rotation': {'0.0': [0, 0, 0], '0.15': [8, 0, 0], '1.0': [0, 0, 0]}},
            'rightLeg': {'rotation': {'0.0': [0, 0, 0], '0.15': [-15, 0, 0], '1.0': [0, 0, 0]}},
            'leftLeg': {'rotation': {'0.0': [0, 0, 0], '0.15': [15, 0, 0], '1.0': [0, 0, 0]}},
        }},
        'animation.bc.magic_knight.slam': {'animation_length': 0.7, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.25': [-170, 0, 10], '0.4': [-30, 0, 0], '0.7': [0, 0, 0]}},
            'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.25': [-170, 0, -10], '0.4': [-30, 0, 0], '0.7': [0, 0, 0]}},
            'body': {'rotation': {'0.0': [0, 0, 0], '0.25': [-10, 0, 0], '0.4': [25, 0, 0], '0.7': [0, 0, 0]}},
        }},
        'animation.bc.magic_knight.dodge': {'animation_length': 0.4, 'bones': {
            'body': {'rotation': {'0.0': [0, 0, 0], '0.1': [0, 0, 25], '0.4': [0, 0, 0]}},
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.1': [-20, 0, 40], '0.4': [0, 0, 0]}},
            'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.1': [-20, 0, -40], '0.4': [0, 0, 0]}},
        }},
        'animation.bc.magic_knight.flinch': {'animation_length': 0.3, 'bones': {
            'body': {'rotation': {'0.0': [0, 0, 0], '0.06': [-12, 0, 0], '0.3': [0, 0, 0]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.06': [-18, 0, 0], '0.3': [0, 0, 0]}},
        }},
        'animation.bc.magic_knight.salute': {'animation_length': 1.2, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.25': [-140, 30, -25], '0.95': [-140, 30, -25], '1.2': [0, 0, 0]}},
            'body': {'rotation': {'0.0': [0, 0, 0], '0.25': [-3, 0, 0], '1.2': [0, 0, 0]}},
        }},
        'animation.bc.magic_knight.cheer': {'animation_length': 1.3, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-170, 0, 15], '0.45': [-150, 0, 25], '0.7': [-170, 0, 15], '1.0': [-150, 0, 25], '1.3': [0, 0, 0]}},
            'root': {'position': {'0.0': [0, 0, 0], '0.2': [0, 3, 0], '0.4': [0, 0, 0], '0.7': [0, 3, 0], '0.9': [0, 0, 0]}},
        }},
        'animation.bc.magic_knight.sit': {'loop': True, 'bones': {
            'root': {'position': [0, -9, 0]},
            'rightLeg': {'rotation': [-80, 10, 0]},
            'leftLeg': {'rotation': [-80, -10, 0]},
            'rightArm': {'rotation': [-20, 0, 10]},
            'leftArm': {'rotation': [-20, 0, -10]},
            'cape': {'rotation': [40, 0, 0]},
        }},
    }


def boss_extra_animations():
    """Roars, throws, stomps, blinks and dives for the giant bosses (keyed by animation file)."""
    return {
        'entity/stone_colossus.animation.json': {
            'animation.bc.stone_colossus.throw': {'animation_length': 1.0, 'bones': {
                'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.4': [-190, 0, -15], '0.6': [-40, 0, 0], '1.0': [0, 0, 0]}},
                'body': {'rotation': {'0.0': [0, 0, 0], '0.4': [-15, 20, 0], '0.6': [15, -20, 0], '1.0': [0, 0, 0]}},
            }},
            'animation.bc.stone_colossus.stomp': {'animation_length': 0.9, 'bones': {
                'rightLeg': {'rotation': {'0.0': [0, 0, 0], '0.35': [-50, 0, 0], '0.5': [5, 0, 0], '0.9': [0, 0, 0]}},
                'body': {'rotation': {'0.0': [0, 0, 0], '0.35': [-8, 0, 6], '0.5': [6, 0, 0], '0.9': [0, 0, 0]}},
            }},
            'animation.bc.stone_colossus.roar': {'animation_length': 1.6, 'bones': {
                'head': {'rotation': {'0.0': [0, 0, 0], '0.4': [-40, 0, 0], '1.2': [-40, 0, 0], '1.6': [0, 0, 0]}},
                'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.4': [-40, 0, 45], '1.2': [-40, 0, 45], '1.6': [0, 0, 0]}},
                'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.4': [-40, 0, -45], '1.2': [-40, 0, -45], '1.6': [0, 0, 0]}},
                'body': {'rotation': {'0.0': [0, 0, 0], '0.4': [-15, 0, 0], '1.6': [0, 0, 0]}},
            }},
        },
        'entity/archdevil.animation.json': {
            'animation.bc.archdevil.roar': {'animation_length': 1.5, 'bones': {
                'chest': {'rotation': {'0.0': [0, 0, 0], '0.3': [-25, 0, 0], '1.2': [-25, 0, 0], '1.5': [0, 0, 0]}},
                'jaw': {'rotation': {'0.0': [0, 0, 0], '0.3': [30, 0, 0], '1.2': [30, 0, 0], '1.5': [0, 0, 0]}},
                'rightWing': {'rotation': {'0.0': [0, 0, 0], '0.3': [0, -60, 30], '1.2': [0, -60, 30], '1.5': [0, 0, 0]}},
                'leftWing': {'rotation': {'0.0': [0, 0, 0], '0.3': [0, 60, -30], '1.2': [0, 60, -30], '1.5': [0, 0, 0]}},
            }},
            'animation.bc.archdevil.blink': {'animation_length': 0.6, 'bones': {
                'rightWing': {'rotation': {'0.0': [0, 0, 0], '0.2': [0, 70, 0], '0.6': [0, 0, 0]}},
                'leftWing': {'rotation': {'0.0': [0, 0, 0], '0.2': [0, -70, 0], '0.6': [0, 0, 0]}},
                'root': {'scale': {'0.0': 1.0, '0.2': 0.6, '0.4': 1.1, '0.6': 1.0}},
            }},
        },
        'entity/storm_kraken.animation.json': {
            'animation.bc.storm_kraken.submerge': {'animation_length': 1.2, 'bones': {
                'root': {'position': {'0.0': [0, 0, 0], '0.8': [0, -18, 0], '1.2': [0, -18, 0]}, 'scale': {'0.0': 1.0, '1.2': 0.6}},
            }},
            'animation.bc.storm_kraken.emerge': {'animation_length': 1.0, 'bones': {
                'root': {'position': {'0.0': [0, -18, 0], '0.7': [0, 3, 0], '1.0': [0, 0, 0]}, 'scale': {'0.0': 0.6, '0.7': 1.05, '1.0': 1.0}},
            }},
        },
        'entity/phantom_galleon.animation.json': {
            'animation.bc.phantom_galleon.broadside': {'animation_length': 0.8, 'bones': {
                'hull': {'rotation': {'0.0': [0, 0, 0], '0.1': [0, 0, 8], '0.8': [0, 0, 0]}},
                'mast': {'rotation': {'0.0': [0, 0, 0], '0.1': [0, 0, 8], '0.8': [0, 0, 0]}},
            }},
            'animation.bc.phantom_galleon.ram': {'animation_length': 1.2, 'bones': {
                'root': {'rotation': {'0.0': [0, 0, 0], '0.3': [-18, 0, 0], '0.9': [10, 0, 0], '1.2': [0, 0, 0]}},
            }},
        },
    }


def player_extra_animations(k):
    return {
        'animation.bc.player.cast_channel': {'animation_length': 1.0, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.12': [k(-90), k(12), 0], '0.85': [k(-88), k(10), 0], '1.0': [0, 0, 0]}},
            'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.12': [k(-90), k(-12), 0], '0.85': [k(-88), k(-10), 0], '1.0': [0, 0, 0]}},
            'body': {'rotation': {'0.0': [0, 0, 0], '0.12': [k(6), 0, 0], '1.0': [0, 0, 0]}},
        }},
        'animation.bc.player.cast_slam': {'animation_length': 0.7, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.25': [k(-170), 0, k(10)], '0.4': [k(-25), 0, 0], '0.7': [0, 0, 0]}},
            'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.25': [k(-170), 0, k(-10)], '0.4': [k(-25), 0, 0], '0.7': [0, 0, 0]}},
            'body': {'rotation': {'0.0': [0, 0, 0], '0.25': [k(-8), 0, 0], '0.4': [k(20), 0, 0], '0.7': [0, 0, 0]}},
        }},
    }


# ======================================================================================
# icons
# ======================================================================================
def _icon(fn, outline='0a0a0f'):
    a = tex.draw_layer(32, 32, fn, 4)
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    tex.outline(a, rgb(outline))
    return a


def v2_icons():
    def whistle(d, s):
        d.rounded_rectangle([4 * s, 12 * s, 22 * s, 21 * s], radius=4 * s, fill=(210, 170, 70, 255))
        d.rectangle([20 * s, 14 * s, 29 * s, 19 * s], fill=(190, 150, 60, 255))
        d.ellipse([8 * s, 14 * s, 13 * s, 19 * s], fill=(60, 40, 20, 255))
        d.line([(6 * s, 12 * s), (4 * s, 4 * s), (12 * s, 3 * s)], fill=(140, 40, 40, 255), width=int(1.4 * s))
        tex.clover_shape(d, 16 * s, 16.5 * s, 2.6 * s, 4, (255, 240, 200, 255), stem=False)

    def cookie(d, s):
        d.ellipse([4 * s, 4 * s, 28 * s, 28 * s], fill=(200, 140, 70, 255))
        d.ellipse([7 * s, 7 * s, 25 * s, 25 * s], fill=(220, 160, 90, 255))
        for x, y in ((11, 11), (19, 10), (14, 18), (21, 19), (10, 21)):
            d.ellipse([(x - 1.6) * s, (y - 1.6) * s, (x + 1.6) * s, (y + 1.6) * s], fill=(120, 200, 255, 255))

    def seal(d, s):
        d.ellipse([3 * s, 3 * s, 29 * s, 29 * s], fill=(30, 20, 26, 255), outline=(180, 30, 40, 255), width=int(2 * s))
        tex.clover_shape(d, 16 * s, 16 * s, 8 * s, 4, (120, 20, 28, 255), stem=False)
        d.line([(9 * s, 9 * s), (23 * s, 23 * s)], fill=(220, 220, 230, 255), width=int(2 * s))
        d.line([(23 * s, 9 * s), (17 * s, 15 * s)], fill=(220, 220, 230, 255), width=int(1.4 * s))
    return {'companion_whistle': _icon(whistle), 'mana_cookie': _icon(cookie, '3a2408'), 'fallen_seal': _icon(seal)}
