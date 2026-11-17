"""Wave 3 models: spell entities, golems, imp, Tidewatch navy, beast forms, pirate weapons, icons.

All designs are original.
"""
from __future__ import annotations

import math

import numpy as np

from .. import fpsolve, tex
from ..geo import Geo
from ..tex import P, rgb
from .sea import DARK_WOOD, IRON, LIGHT_WOOD, ROCK, SKIN, Planks, _face, _humanoid_bones, _rock

ORIENT = ['-q.target_x_rotation', '-q.target_y_rotation', 0]
STEEL = tex.ramp('3b4250', '5a6372', '7d8796', 'a3adbb', 'c9d1dc', 'eef2f7')


# ======================================================================================
# spell entities
# ======================================================================================
def steel_lance():
    g = Geo('geometry.bc.steel_lance', res=2, atlas_width=64, visible=(2, 2, (0, 0, 0)))
    g.bone('root', pivot=(0, 0, 0))
    m = tex.Metal(STEEL, sheen=0.5)
    g.box('root', (0, 0, 2), (1.2, 1.2, 18), m)
    g.box('root', (0, 0, -8.5), (2.8, 2.8, 4.5), m, rotation=[0, 0, 45], pivot=(0, 0, -8.5))
    g.box('root', (0, 0, -11.5), (1.4, 1.4, 2.6), m, rotation=[0, 0, 45], pivot=(0, 0, -11.5))
    for z in (4, 7):
        g.box('root', (0, 0, z), (2.0, 2.0, 0.8), tex.Metal(P['gold']))
    anim = {'animation.bc.steel_lance.fly': {'loop': True, 'bones': {'root': {'rotation': ['-q.target_x_rotation', '-q.target_y_rotation', 'q.life_time * 600.0']}}}}
    return g, 'emissive', anim


def _swirl(a, ctx):
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (w / 2)
    ang = np.arctan2(yy - cy, xx - cx)
    v = (np.sin(ang * 3 + r * 12) * 0.5 + 0.5) * (1 - r)
    col = tex.smooth_ramp(tex.ramp('3a0a5a', '8a2ad0', 'e08aff', 'ffe8ff'), np.clip(v + (1 - r) * 0.4, 0, 1))
    a[:] = col
    a[..., 3] = np.where(r < 0.98, 135, 0)
    return a


def warp_gate():
    g = Geo('geometry.bc.warp_gate', res=2, atlas_width=128, visible=(3, 3, (0, 1, 0)))
    g.bone('root', pivot=(0, 16, 0))
    g.bone('ring', 'root', (0, 16, 0))
    g.bone('swirl', 'root', (0, 16, 0))
    rim = tex.Energy(tex.ramp('5a1a8a', '9a3ad8', 'e08aff', 'ffffff'), alpha=135)
    gold = tex.Metal(P['gold'])
    for k in range(20):
        a = k * 18
        r = math.radians(a)
        cx, cy = math.cos(r) * 11, 16 + math.sin(r) * 11
        g.box('ring', (cx, cy, 0), (3.8, 1.6, 1.6), rim if k % 2 else gold, rotation=[0, 0, a + 90], pivot=(cx, cy, 0))
    g.cube('swirl', (-10, 6, -0.1), (20, 20, 0.2), _swirl)
    anim = {'animation.bc.warp_gate.spin': {'loop': True, 'bones': {
        'ring': {'rotation': [0, 0, 'q.life_time * 40.0']},
        'swirl': {'rotation': [0, 0, '-q.life_time * 220.0']},
        'root': {'scale': 'math.min(q.life_time * 4.0, 1.0)'},
    }}}
    return g, 'emissive', anim


# ======================================================================================
# golems
# ======================================================================================
def _rune_lines(color):
    def fn(a, ctx):
        h, w = a.shape[:2]
        rng = np.random.default_rng(ctx.seed)
        for _ in range(max(1, (h * w) // 160)):
            y, x = int(rng.integers(1, max(2, h - 1))), int(rng.integers(1, max(2, w - 1)))
            for i in range(int(rng.integers(3, 7))):
                if rng.random() < 0.5:
                    x = int(np.clip(x + rng.choice([-1, 1]), 0, w - 1))
                else:
                    y = int(np.clip(y + rng.choice([-1, 1]), 0, h - 1))
                a[y, x, :3] = rgb(color)[:3]
                a[y, x, 3] = 135
        return a
    return fn


def _golem_eyes(color):
    def fn(a, ctx):
        h, w = a.shape[:2]
        for ex in (int(w * 0.18), int(w * 0.62)):
            a[int(h * 0.42):int(h * 0.42) + 3, ex:ex + max(2, int(w * 0.2)), :3] = rgb(color)[:3]
            a[int(h * 0.42):int(h * 0.42) + 3, ex:ex + max(2, int(w * 0.2)), 3] = 130
        a[int(h * 0.3), :, :3] *= 0.5
        return a
    return fn


def golem_geo(kind):
    earth = kind == 'earth_golem'
    rock_r = tex.ramp('2a2116', '3c3020', '50412c', '665439', '7d6a49', '96805a') if earth else P['deepslate']
    rune = 'ffb347' if earth else '5ad8ff'
    g = Geo(f'geometry.bc.{kind}', res=2, atlas_width=256, visible=(3, 4, (0, 1.5, 0)))
    rock = tex.Painted(tex.Stone(rock_r, brick=0), {'*': _rune_lines(rune)})
    plain = tex.Stone(rock_r, brick=0)
    moss = tex.Material(P['clover_green'][1:5], noise=0.25)
    crystal = tex.Crystal(tex.ramp('0a3a5a', '125a8a', '2a8ac8', '5ad8ff', 'c8f4ff'), alpha=210)
    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 18, 0))
    g.bone('head', 'body', (0, 30, -3))
    g.bone('rightArm', 'body', (-10.5, 29, 0))
    g.bone('leftArm', 'body', (10.5, 29, 0))
    g.bone('rightLeg', 'root', (-4.5, 12, 0))
    g.bone('leftLeg', 'root', (4.5, 12, 0))
    g.cube('body', (-9, 13, -5.5), (18, 17, 11), rock)
    g.cube('body', (-6, 11, -4.5), (12, 3, 9), plain)
    g.cube('head', (-4.5, 27, -9.5), (9, 8, 8), tex.Painted(plain, {'north': _golem_eyes(rune)}))
    g.cube('head', (-5.2, 33.5, -10.2), (10.4, 1.6, 9.4), plain)
    for side, sx in (('rightArm', -1), ('leftArm', 1)):
        x0 = -16 if sx < 0 else 10
        g.cube(side, (x0, 9, -4), (6, 21, 8), rock)
        g.cube(side, (x0 - 0.8, 3, -5), (7.6, 7, 10), plain)
        if earth:
            g.cube(side, (x0 - 0.3, 27.5, -4.3), (6.6, 3, 8.6), moss)
        else:
            g.box(side, (sx * 13, 31.5, 0), (2.4, 4, 2.4), crystal, rotation=[0, 0, sx * -20], pivot=(sx * 13, 30, 0))
    for side, x0 in (('rightLeg', -8), ('leftLeg', 1)):
        g.cube(side, (x0, 0, -4), (7, 13, 8), rock)
    if earth:
        g.cube('body', (-9.3, 26, -5.8), (18.6, 4.4, 11.6), moss)
    else:
        for k, (x, y) in enumerate(((-4, 26), (3, 28), (0, 22))):
            g.box('body', (x, y, 6.5), (3, 6 + k, 3), crystal, rotation=[-25, k * 30, 10], pivot=(x, y - 3, 5.5))
    return g


def golem_animations(kind):
    walk = 'math.cos(q.modified_distance_moved * 25.0) * 26.0 * q.modified_move_speed'
    return {
        f'animation.bc.{kind}.idle': {'loop': True, 'bones': {
            'body': {'rotation': ['math.sin(q.life_time * 60.0) * 1.5', 0, 0]},
            'rightArm': {'rotation': ['math.sin(q.life_time * 60.0) * 3.0', 0, 3]},
            'leftArm': {'rotation': ['-math.sin(q.life_time * 60.0) * 3.0', 0, -3]},
        }},
        f'animation.bc.{kind}.walk': {'loop': True, 'bones': {
            'rightLeg': {'rotation': [walk, 0, 0]},
            'leftLeg': {'rotation': [f'-({walk})', 0, 0]},
            'rightArm': {'rotation': [f'-({walk}) * 0.8', 0, 0]},
            'leftArm': {'rotation': [f'({walk}) * 0.8', 0, 0]},
            'body': {'rotation': [0, f'({walk}) * 0.15', 0]},
        }},
        f'animation.bc.{kind}.look_at_target': {'loop': True, 'bones': {'head': {'rotation': ['q.target_x_rotation * 0.6', 'q.target_y_rotation * 0.6', 0]}}},
        f'animation.bc.{kind}.slam': {'animation_length': 0.9, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.35': [-160, 0, -10], '0.55': [-20, 0, 0], '0.9': [0, 0, 0]}},
            'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.35': [-160, 0, 10], '0.55': [-20, 0, 0], '0.9': [0, 0, 0]}},
            'body': {'rotation': {'0.0': [0, 0, 0], '0.35': [-12, 0, 0], '0.55': [18, 0, 0], '0.9': [0, 0, 0]}},
        }},
    }


# ======================================================================================
# imp (low-rank devil)
# ======================================================================================
def _imp_face(a, ctx):
    h, w = a.shape[:2]
    for ex in (int(w * 0.18), int(w * 0.6)):
        a[int(h * 0.38):int(h * 0.38) + 2, ex:ex + max(2, int(w * 0.22)), :3] = rgb('ffd23a')[:3]
        a[int(h * 0.38):int(h * 0.38) + 2, ex:ex + max(2, int(w * 0.22)), 3] = 130
    a[int(h * 0.72), int(w * 0.25):int(w * 0.75), :3] = rgb('f0ece0')[:3]
    return a


def imp_geo():
    from .mobs import _membrane
    g = Geo('geometry.bc.imp', res=2, atlas_width=128, visible=(2, 2, (0, 0.6, 0)))
    skin = tex.Material(tex.ramp('2a0508', '470a10', '6a1018', '8f1a22', 'a83028'), noise=0.15)
    horn = tex.Material(P['bone'], noise=0.06, grad=0.3)
    mem = tex.Painted(tex.Material(tex.ramp('120206', '22040c', '360812', '4a0c1a'), noise=0.2, edge=0, highlight=False), {'*': _membrane})
    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 8, 0))
    g.bone('head', 'body', (0, 12, 0))
    g.bone('rightArm', 'body', (-3, 11, 0))
    g.bone('leftArm', 'body', (3, 11, 0))
    g.bone('rightWing', 'body', (-1, 11, 1.5))
    g.bone('leftWing', 'body', (1, 11, 1.5))
    g.bone('tail', 'body', (0, 6.5, 1.5))
    g.cube('body', (-2.5, 6, -1.5), (5, 6, 3), skin)
    g.cube('body', (-2, 3.5, -1.2), (1.8, 3, 2.4), skin)
    g.cube('body', (0.2, 3.5, -1.2), (1.8, 3, 2.4), skin)
    g.cube('head', (-3, 12, -3), (6, 5, 5), tex.Painted(skin, {'north': _imp_face}))
    for sx in (-1, 1):
        g.box('head', (sx * 2.4, 18.0, -1), (1.2, 2.8, 1.2), horn, rotation=[-20, 0, sx * -25], pivot=(sx * 2.2, 16.8, -1))
        g.cube('head', (sx * 3 - (0 if sx > 0 else 1), 14, -1.5), (1, 2, 1), skin)
    g.cube('rightArm', (-4.6, 6.5, -1), (1.6, 5, 2), skin)
    g.cube('leftArm', (3, 6.5, -1), (1.6, 5, 2), skin)
    g.cube('rightWing', (-9, 6, 1.5), (8, 7, 0), mem)
    g.cube('leftWing', (1, 6, 1.5), (8, 7, 0), mem)
    g.cube('tail', (-0.5, 6, 1.5), (1, 1, 5), skin, rotation=[30, 0, 0], pivot=(0, 6.5, 1.5))
    g.box('tail', (0, 3.6, 5.6), (1.8, 0.6, 1.8), horn, rotation=[0, 45, 0], pivot=(0, 3.6, 5.6))
    return g


def imp_animations():
    flap = 'math.sin(q.life_time * 1200.0)'
    return {
        'animation.bc.imp.fly': {'loop': True, 'bones': {
            'root': {'position': [0, f'math.sin(q.life_time * 180.0) * 1.0', 0]},
            'rightWing': {'rotation': [0, f'-20.0 + {flap} * 40.0', 0]},
            'leftWing': {'rotation': [0, f'20.0 - {flap} * 40.0', 0]},
            'tail': {'rotation': [0, 'math.sin(q.life_time * 200.0) * 25.0', 0]},
            'rightArm': {'rotation': ['-30.0 + math.sin(q.life_time * 180.0) * 10.0', 0, 0]},
            'leftArm': {'rotation': ['-30.0 - math.sin(q.life_time * 180.0) * 10.0', 0, 0]},
        }},
        'animation.bc.imp.look_at_target': {'loop': True, 'bones': {'head': {'rotation': ['q.target_x_rotation', 'q.target_y_rotation', 0]}}},
    }


# ======================================================================================
# Tidewatch navy (original naval faction)
# ======================================================================================
def _naval_trim(color):
    def fn(a, ctx):
        h, w = a.shape[:2]
        a[-2:, :, :3] = rgb(color)[:3]
        if ctx.face == 'north':
            cx = w // 2
            a[:, cx - 1:cx + 1, :3] = rgb(color)[:3]
            for y in range(3, h - 2, max(3, h // 5)):
                a[y, cx - 3:cx - 1, :3] = rgb('f0c24a')[:3]
        return a
    return fn


def _anchor_badge(a, ctx):
    h, w = a.shape[:2]
    cx, cy = w // 2, h // 2
    a[cy - 2:cy + 3, cx, :3] = rgb('f0c24a')[:3]
    a[cy + 2, cx - 2:cx + 3, :3] = rgb('f0c24a')[:3]
    a[cy - 1, cx - 1:cx + 2, :3] = rgb('f0c24a')[:3]
    return a


def _saber(g, bone):
    steel = tex.Metal(STEEL, sheen=0.5)
    gold = tex.Metal(P['gold'])
    g.bone('saber', bone, (-6, 12.5, 0))
    g.box('saber', (-6, 12.0, 0.6), (1.2, 1.2, 3.0), tex.Material(P['leather']))
    g.box('saber', (-6, 12.0, -1.2), (2.2, 2.6, 0.6), gold)
    g.cube('saber', (-6.25, 11.6, -13.5), (0.5, 1.0, 12), steel)


def navy_geo(kind):
    officer = kind == 'tidewatch_commodore'
    g = Geo(f'geometry.bc.{kind}', res=2, atlas_width=128, visible=(2, 3, (0, 1.2, 0)))
    _humanoid_bones(g)
    skin = tex.Material(SKIN[1:] if not officer else tex.ramp('7a5038', '94664a', 'ae7e5c', 'c69872'), noise=0.08, edge=0.85)
    white = tex.Cloth(P['white_cloth'], folds=0.1)
    navy = tex.Cloth(P['navy'], folds=0.14)
    gold = tex.Metal(P['gold'])
    boots = tex.Material(tex.ramp('08080a', '121216', '1c1c22', '28282f'), noise=0.1)
    hat = tex.Painted(tex.Material(P['navy'], noise=0.08), {'*': lambda a, c: (a.__setitem__((slice(0, 1), slice(None), slice(0, 3)), rgb('eceff4')[:3]), a)[1]})
    coat = tex.Painted(navy if officer else white, {'north': _naval_trim('d39a2c' if officer else '23345f'), 'south': _naval_trim('d39a2c' if officer else '23345f')})
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(skin, {'north': _face(beard=officer, scar=False)}))
    # bicorne hat (worn sideways), with a plume for the commodore
    g.cube('head', (-4.3, 31.2, -4.3), (8.6, 2.0, 8.6), hat)
    g.cube('head', (-7.5, 32.2, -1.8), (15, 4.6, 3.6), tex.Painted(hat, {'north': _anchor_badge}))
    if officer:
        g.box('head', (5.2, 37.2, 0), (1.4, 4.5, 1.4), tex.Material(P['white_cloth']), rotation=[0, 0, -30], pivot=(5, 35, 0))
    g.cube('body', (-4, 12, -2), (8, 12, 4), white)
    g.cube('body', (-4.4, 11.5 if officer else 13.5, -2.4), (8.8, 12.8 if officer else 10.8, 4.8), coat)
    g.cube('body', (-4.6, 13, -2.6), (9.2, 1.6, 5.2), tex.Material(P['leather'] if not officer else P['gold']))
    if officer:
        g.bone('coattails', 'body', (0, 13, 2))
        g.cube('coattails', (-4.4, 1.5, 1.6), (8.8, 11, 1.0), coat)
        g.cube('body', (-4.6, 16, -2.6), (2.0, 8, 5.2), tex.Cloth(P['red_cloth']), rotation=[0, 0, 30], pivot=(-3.6, 20, 0))  # sash
    for side, x0 in (('rightArm', -8), ('leftArm', 4)):
        g.cube(side, (x0 - 0.4, 14, -2.4), (4.8, 10, 4.8), navy if officer else white)
        g.cube(side, (x0 - 0.5, 14, -2.5), (5.0, 1.4, 5.0), gold if officer else navy)
        if officer:
            g.cube(side, (x0 - 0.6, 21.6, -2.6), (5.2, 1.6, 5.2), gold)
        g.cube(side, (x0, 12, -2), (4, 2, 4), skin)
    trousers = white if officer else navy
    g.cube('rightLeg', (-3.9, 3, -2), (4, 9, 4), trousers)
    g.cube('leftLeg', (-0.1, 3, -2), (4, 9, 4), trousers)
    g.cube('rightLeg', (-4.1, 0, -2.3), (4.4, 5 if officer else 3.4, 4.6), boots)
    g.cube('leftLeg', (-0.3, 0, -2.3), (4.4, 5 if officer else 3.4, 4.6), boots)
    _saber(g, 'rightArm')
    return g


def navy_animations(kind):
    from .sea import humanoid_animations
    anims = humanoid_animations(kind)
    anims[f'animation.bc.{kind}.cast'] = {'animation_length': 0.8, 'bones': {
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-150, 0, -10], '0.55': [-140, 0, 0], '0.8': [0, 0, 0]}},
        'head': {'rotation': {'0.0': [0, 0, 0], '0.2': [-15, 0, 0], '0.8': [0, 0, 0]}},
    }}
    if kind == 'tidewatch_commodore':
        anims[f'animation.bc.{kind}.idle']['bones']['coattails'] = {'rotation': ['5.0 + math.sin(q.life_time * 120.0) * 3.0', 0, 0]}
        anims[f'animation.bc.{kind}.walk']['bones']['coattails'] = {'rotation': ['math.abs(math.cos(q.modified_distance_moved * 38.17)) * 25.0 * q.modified_move_speed', 0, 0]}
    return anims


# ======================================================================================
# beast forms (worn while holding the Wolf / Hawk power)
# ======================================================================================
def beast_geo(fid):
    g = Geo(f'geometry.bc.power_{fid}', res=2, atlas_width=128, visible=(3, 3, (0, 1, 0)))
    g.skeleton()
    if fid == 'wolf':
        fur = tex.Material(tex.ramp('4a4238', '625a4e', '7c7366', '988e80', 'b4aa9a'), noise=0.25)
        dark = tex.Material(tex.ramp('2a241e', '3a322a', '4a4036'), noise=0.2)
        claw = tex.Material(P['bone'], noise=0.05)
        g.bone('ears', 'head', (0, 32, 0))
        for sx in (-1, 1):
            g.box('ears', (sx * 2.7, 33.6, 0), (2.4, 3.6, 1.4), tex.PerFace(fur, north=dark), rotation=[0, 0, sx * -14], pivot=(sx * 2.7, 32, 0))
        g.cube('body', (-4.6, 21.0, -2.6), (9.2, 3.4, 5.2), fur)                                # fur ruff
        g.bone('tail', 'body', (0, 13, 2))
        g.cube('tail', (-1.4, 12.6, 2), (2.8, 2.8, 7), fur, rotation=[-35, 0, 0], pivot=(0, 13, 2))
        g.cube('tail', (-1.1, 8.7, 7.2), (2.2, 2.2, 4), tex.PerFace(fur, south=dark), rotation=[-60, 0, 0], pivot=(0, 10, 7.5))
        for side, x0, piv in (('rightArm', -8, -6), ('leftArm', 4, 6)):
            g.cube(side, (x0 - 0.5, 14, -2.5), (5, 3, 5), fur)
            for k in range(3):
                g.cube(side, (x0 + 0.6 + k * 1.2, 10.4, -2.4), (0.6, 2.4, 0.6), claw, rotation=[-25, 0, 0], pivot=(x0 + 0.9 + k * 1.2, 12, -2.1))
        anim = {'loop': True, 'bones': {
            'tail': {'rotation': [0, 'math.sin(q.life_time * 400.0) * 18.0', 0]},
            'ears': {'rotation': ['math.max(0.0, math.sin(q.life_time * 90.0)) * 8.0', 0, 0]},
        }}
    else:  # hawk
        feather = tex.Material(tex.ramp('3a2410', '5a3a1c', '7a5228', '9c6c36', 'c08c48'), noise=0.2)
        tip = tex.Material(tex.ramp('1a120a', '2a1e12', '3a2a1a'), noise=0.15)
        g.bone('rightWing', 'body', (-2, 22.5, 2.5))
        g.bone('leftWing', 'body', (2, 22.5, 2.5))
        for side, sx in (('rightWing', -1), ('leftWing', 1)):
            x0 = -16 if sx < 0 else 2
            g.cube(side, (x0, 20.5, 2.5), (14, 2.4, 1.2), feather)
            for k in range(5):
                fx = (-4 - k * 2.6) if sx < 0 else (2 + k * 2.6)
                ln = 9 + k * 1.6
                g.cube(side, (fx, 21 - ln, 3.0 + k * 0.05), (2.6, ln, 0.4), tex.PerFace(feather, south=tip, north=tip) if k > 2 else feather,
                       rotation=[0, 0, sx * (8 + k * 4)], pivot=(fx + 1.3, 21, 3.0))
        g.cube('body', (-3, 6, 2.2), (6, 7, 0.6), feather, rotation=[25, 0, 0], pivot=(0, 12, 2.2))   # tail feathers
        for side, x0 in (('rightArm', -8), ('leftArm', 4)):
            g.cube(side, (x0 - 0.4, 15, -2.4), (4.8, 4, 4.8), feather)
        anim = {'loop': True, 'bones': {
            'rightWing': {'rotation': ['5.0', 'math.sin(q.life_time * 260.0) * 18.0 - 15.0', '22.0 + math.sin(q.life_time * 260.0) * 12.0']},
            'leftWing': {'rotation': ['5.0', '-math.sin(q.life_time * 260.0) * 18.0 + 15.0', '-22.0 - math.sin(q.life_time * 260.0) * 12.0']},
        }}
    return g, {f'animation.bc.power.beast_{fid}': anim}


# ======================================================================================
# pirate weapons (held) - modelled along +Y like the swords
# ======================================================================================
def weapon_geo(kind):
    g = Geo(f'geometry.bc.{kind}', res=3, atlas_width=96, visible=(3, 3, (0, 1.5, 0)))
    g.skeleton()
    g.bone('weapon', 'rightItem', (0, 0, 0))
    steel = tex.Metal(STEEL, sheen=0.45)
    gold = tex.Metal(P['gold'])
    wood = tex.Wood(LIGHT_WOOD)
    dwood = tex.Wood(DARK_WOOD)
    if kind == 'cutlass':
        g.box('weapon', (0, -2.6, 0), (1.4, 5.2, 1.4), tex.Material(P['leather']))
        g.box('weapon', (0, -5.6, 0), (1.8, 1.0, 1.8), gold)
        g.box('weapon', (0, 0.5, 0.2), (1.0, 1.2, 4.2), gold)                        # guard
        g.box('weapon', (0, -2.4, 2.2), (0.8, 6.0, 0.8), gold)                       # knuckle bow
        g.cube('weapon', (-0.3, 1.0, -1.1), (0.6, 13, 2.4), steel)
        g.cube('weapon', (-0.3, 13.6, -0.6), (0.6, 4.0, 1.9), steel, rotation=[-14, 0, 0], pivot=(0, 13.6, 1.3))
        g.cube('weapon', (-0.32, 2.0, 0.9), (0.64, 11, 0.4), tex.Metal(tex.ramp('9aa3b1', 'c9d1dc', 'eef2f7')))   # bright edge
    elif kind == 'flintlock':
        g.box('weapon', (0, -1.2, 1.2), (1.8, 5.0, 2.4), dwood, rotation=[-18, 0, 0], pivot=(0, 0.5, 0.5))    # grip
        g.box('weapon', (0, -4.2, 2.1), (2.2, 1.4, 2.8), gold, rotation=[-18, 0, 0], pivot=(0, 0.5, 0.5))     # butt cap
        g.box('weapon', (0, 4.6, 0), (1.9, 9.5, 1.9), wood)                                                   # stock
        g.box('weapon', (0, 6.5, -0.3), (1.3, 12.5, 1.3), tex.Metal(IRON, sheen=0.3))                         # barrel
        g.box('weapon', (0, 12.6, -0.3), (1.6, 0.8, 1.6), gold)
        g.box('weapon', (0, 1.2, 1.3), (0.8, 2.0, 1.2), steel, rotation=[30, 0, 0], pivot=(0, 1, 1))         # hammer
        g.box('weapon', (0, 0.0, -1.1), (0.5, 1.6, 0.9), steel)                                               # trigger
    else:  # harpoon
        g.box('weapon', (0, 4, 0), (1.1, 26, 1.1), dwood)
        g.box('weapon', (0, -8.6, 0), (1.5, 1.2, 1.5), tex.Metal(IRON))
        g.box('weapon', (0, 18.5, 0), (1.6, 1.6, 1.6), tex.Metal(IRON))
        g.box('weapon', (0, 21.5, 0), (2.4, 2.4, 2.4), steel, rotation=[45, 0, 0], pivot=(0, 21.5, 0))
        for sz in (-1, 1):
            g.box('weapon', (0, 20.0, sz * 1.4), (0.6, 3.0, 0.6), steel, rotation=[sz * -35, 0, 0], pivot=(0, 21, sz * 0.8))
        g.box('weapon', (0, 2, 0.8), (0.4, 8, 0.4), tex.Material(tex.ramp('5a4630', '7a6040', '977a52')))  # rope
    return g


def weapon_animations():
    out = {}
    poses = {
        'cutlass': ([-6.0, 12.6, -1.2], [80.0, 0.0, 0.0], -2.6, 0.95, (0.42, 0.78, 0.46)),
        'flintlock': ([-6.0, 12.4, -1.0], [90.0, 0.0, 0.0], 0.0, 1.0, (0.08, 0.32, 1.0)),
        'harpoon': ([-6.0, 13.0, -1.0], [75.0, 0.0, 0.0], -1.0, 0.8, (0.3, 0.7, 0.65)),
    }
    hand = fpsolve.hand_point()
    for kind, (tpp, tpr, grip_y, fps, bdir) in poses.items():
        blade = np.array(bdir, float)
        blade /= np.linalg.norm(blade)
        cam = np.array([-0.35, 0.0, -1.0])
        R = fpsolve.basis(blade, np.cross(cam, blade))
        fpp, fpr, fpsc = fpsolve.solve(hand + np.array([0.0, 0.6, 0.2]), R, scale=fps, local_anchor=(0, grip_y, 0))
        out[f'animation.bc.{kind}.third_person'] = {'loop': True, 'bones': {'weapon': {'position': tpp, 'rotation': tpr}}}
        out[f'animation.bc.{kind}.first_person'] = {'loop': True, 'bones': {'weapon': {'position': fpp, 'rotation': fpr, 'scale': fpsc}}}
    return out


def harpoon_bolt():
    g = Geo('geometry.bc.harpoon_bolt', res=2, atlas_width=64, visible=(2, 2, (0, 0, 0)))
    g.bone('root', pivot=(0, 0, 0))
    g.box('root', (0, 0, 4), (1.0, 1.0, 20), tex.Wood(DARK_WOOD))
    g.box('root', (0, 0, -7.5), (2.2, 2.2, 3), tex.Metal(STEEL), rotation=[0, 0, 45], pivot=(0, 0, -7.5))
    for sx in (-1, 1):
        g.box('root', (sx * 1.3, 0, -5.2), (0.5, 0.5, 2.6), tex.Metal(STEEL), rotation=[0, sx * -35, 0], pivot=(sx * 0.8, 0, -6))
    anim = {'animation.bc.harpoon_bolt.fly': {'loop': True, 'bones': {'root': {'rotation': ORIENT}}}}
    return g, anim


def lead_shot():
    return _rock('lead_shot', 1.8, palette=IRON)


# ======================================================================================
# 2D icons
# ======================================================================================
def _icon(fn, outline='0a0a0f'):
    a = tex.draw_layer(32, 32, fn, 4)
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    tex.outline(a, rgb(outline))
    return a


def wave3_icons():
    def page(d, s):
        d.polygon([(7 * s, 4 * s), (25 * s, 3 * s), (26 * s, 28 * s), (6 * s, 29 * s)], fill=(214, 196, 150, 255))
        for y in range(8, 26, 3):
            d.line([(10 * s, y * s), (22 * s, (y + 0.4) * s)], fill=(90, 70, 40, 255), width=int(0.8 * s))
        tex.clover_shape(d, 16 * s, 15 * s, 4.5 * s, 4, (40, 140, 60, 255), stem=False)

    def tmap(d, s):
        d.polygon([(4 * s, 7 * s), (12 * s, 4 * s), (20 * s, 7 * s), (28 * s, 4 * s), (28 * s, 25 * s), (20 * s, 28 * s), (12 * s, 25 * s), (4 * s, 28 * s)], fill=(222, 200, 150, 255))
        d.line([(8 * s, 22 * s), (12 * s, 16 * s), (17 * s, 18 * s), (21 * s, 12 * s)], fill=(140, 90, 50, 255), width=int(1.1 * s))
        d.line([(19 * s, 8 * s), (24 * s, 13 * s)], fill=(200, 30, 30, 255), width=int(1.6 * s))
        d.line([(24 * s, 8 * s), (19 * s, 13 * s)], fill=(200, 30, 30, 255), width=int(1.6 * s))

    def shot(d, s):
        for k, (x, y) in enumerate(((11, 12), (19, 11), (15, 19), (22, 20), (9, 21))):
            d.ellipse([(x - 3) * s, (y - 3) * s, (x + 3) * s, (y + 3) * s], fill=(60, 64, 74, 255))
            d.ellipse([(x - 1.6) * s, (y - 1.8) * s, (x) * s, (y - 0.4) * s], fill=(170, 176, 188, 255))

    def roast(d, s):
        d.line([(6 * s, 26 * s), (13 * s, 19 * s)], fill=(236, 230, 214, 255), width=int(3 * s))
        d.ellipse([3 * s, 24 * s, 9 * s, 30 * s], fill=(236, 230, 214, 255))
        d.ellipse([10 * s, 5 * s, 28 * s, 23 * s], fill=(150, 70, 30, 255))
        d.ellipse([13 * s, 8 * s, 22 * s, 15 * s], fill=(200, 110, 50, 255))
        d.arc([10 * s, 5 * s, 28 * s, 23 * s], 100, 200, fill=(90, 40, 15, 255), width=int(1.4 * s))

    def cutlass(d, s):
        d.arc([2 * s, 2 * s, 46 * s, 46 * s], 200, 262, fill=(200, 208, 220, 255), width=int(2.6 * s))
        d.line([(7 * s, 20 * s), (13 * s, 26 * s)], fill=(211, 154, 44, 255), width=int(2 * s))
        d.line([(4 * s, 28 * s), (9 * s, 23 * s)], fill=(110, 67, 44, 255), width=int(2.2 * s))
        d.arc([2 * s, 19 * s, 14 * s, 31 * s], 200, 350, fill=(211, 154, 44, 255), width=int(1.2 * s))

    def pistol(d, s):
        d.polygon([(4 * s, 22 * s), (9 * s, 15 * s), (12 * s, 16 * s), (8 * s, 25 * s)], fill=(92, 60, 34, 255))
        d.rectangle([9 * s, 13 * s, 28 * s, 16 * s], fill=(60, 64, 74, 255))
        d.rectangle([8 * s, 12 * s, 18 * s, 17 * s], fill=(122, 90, 55, 255))
        d.rectangle([26 * s, 12.5 * s, 28.5 * s, 16.5 * s], fill=(211, 154, 44, 255))
        d.line([(11 * s, 12 * s), (9 * s, 9 * s)], fill=(160, 166, 180, 255), width=int(1.2 * s))

    def harpoon(d, s):
        d.line([(4 * s, 28 * s), (24 * s, 8 * s)], fill=(92, 60, 34, 255), width=int(1.8 * s))
        d.polygon([(22 * s, 6 * s), (29 * s, 3 * s), (26 * s, 10 * s)], fill=(200, 208, 220, 255))
        d.line([(23 * s, 9 * s), (20 * s, 6 * s)], fill=(200, 208, 220, 255), width=int(1.2 * s))

    def poster(d, s):
        d.rectangle([6 * s, 3 * s, 26 * s, 29 * s], fill=(222, 200, 150, 255))
        d.rectangle([8 * s, 5 * s, 24 * s, 8 * s], fill=(70, 40, 20, 255))
        d.ellipse([12 * s, 10 * s, 20 * s, 18 * s], fill=(70, 50, 36, 255))
        d.rectangle([10 * s, 17 * s, 22 * s, 21 * s], fill=(70, 50, 36, 255))
        d.rectangle([9 * s, 24 * s, 23 * s, 26 * s], fill=(160, 110, 30, 255))

    return {'ancient_page': _icon(page, '2a1e10'), 'treasure_map': _icon(tmap, '3a2810'), 'lead_shot': _icon(shot),
            'hearty_roast': _icon(roast, '2a1206'), 'cutlass': _icon(cutlass), 'flintlock': _icon(pistol),
            'harpoon': _icon(harpoon), 'wanted_poster': _icon(poster, '3a2810')}
