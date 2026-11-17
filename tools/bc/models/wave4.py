"""Wave 4 models: the mana bolt family, Magic Knights, the merchant, constructs, the Stone Colossus,
the Storm Kraken, the Phantom Galleon, the devil gate, the War Table and new item icons.

All designs are original.
"""
from __future__ import annotations

import math

import numpy as np

from .. import tex
from ..data import ATTR_ORDER, ATTRIBUTES, FRUIT_ORDER, FRUITS, ROBES
from ..geo import Geo
from ..tex import P, rgb
from .items import _emblem
from .sea import SKIN, _face, _humanoid_bones, humanoid_animations

ORIENT = ['-q.target_x_rotation', '-q.target_y_rotation', 0]

# every spell source (grimoire attribute or fruit) gets a bolt tint
TINTS = [(f'a:{k}', ATTRIBUTES[k]['color']) for k in ATTR_ORDER] + [(f'f:{k}', FRUITS[k]['color']) for k in FRUIT_ORDER]
TINTS = [(k, 'e23a3a' if k == 'a:anti' else c) for k, c in TINTS]
BOLT_SHAPES = ['orb', 'shard', 'blade', 'needle']


# ======================================================================================
# mana bolt: 4 flat-shaded shapes that share one 4x4 palette texture per tint
# ======================================================================================
def _fc(col):
    """Per-face uv pointing every face at one palette pixel (0 core, 1 mid, 2 outer, 3 dark)."""
    face = {'uv': [col, 0], 'uv_size': [1, 1]}
    return {f: dict(face) for f in ('north', 'south', 'east', 'west', 'up', 'down')}


def _cube(center, size, col, rot=None):
    c = {'origin': [round(center[i] - size[i] / 2, 4) for i in range(3)], 'size': [round(v, 4) for v in size], 'uv': _fc(col)}
    if rot:
        c['rotation'] = rot
        c['pivot'] = [round(v, 4) for v in center]
    return c


def _bolt_shape(kind):
    root = {'name': 'root', 'pivot': [0, 0, 0], 'cubes': []}
    spin = {'name': 'spin', 'parent': 'root', 'pivot': [0, 0, 0], 'cubes': []}
    tail = {'name': 'tail', 'parent': 'root', 'pivot': [0, 0, 0], 'cubes': []}
    if kind == 'orb':
        spin['cubes'] += [_cube((0, 0, 0), (2.8, 2.8, 2.8), 0, [45, 45, 0]),
                          _cube((0, 0, 0), (5.2, 5.2, 1.0), 1, [0, 0, 45]), _cube((0, 0, 0), (5.2, 1.0, 5.2), 1, [0, 45, 0]),
                          _cube((0, 0, 0), (1.0, 5.2, 5.2), 1, [45, 0, 0])]
        tail['cubes'] += [_cube((0, 0, 3.6), (2.2, 2.2, 3.0), 2, [0, 0, 45]), _cube((0, 0, 6.6), (1.2, 1.2, 3.0), 2, [0, 0, 45]),
                          _cube((0, 0, 9.0), (0.6, 0.6, 2.0), 3)]
    elif kind == 'shard':
        spin['cubes'] += [_cube((0, 0, -1), (2.2, 2.2, 8.0), 0, [0, 0, 45]), _cube((0, 0, -4.4), (1.2, 1.2, 2.0), 1, [0, 0, 45]),
                          _cube((0, 0, 0.5), (0.5, 4.6, 4.0), 1), _cube((0, 0, 0.5), (4.6, 0.5, 4.0), 1)]
        tail['cubes'] += [_cube((0, 0, 4.6), (0.9, 0.9, 4.0), 2, [0, 0, 45]), _cube((0, 0, 7.4), (0.5, 0.5, 2.0), 3)]
    elif kind == 'blade':
        for i in range(9):
            th = -70 + 140 * (i + 0.5) / 9
            t = math.radians(th)
            R = 6.0
            f = abs(th) / 70
            seg = 2 * math.radians(70) * R / 9 * 1.3
            spin['cubes'].append(_cube((R * math.sin(t), 0, -R * math.cos(t) + 4), (seg, 0.6, 0.6 + 2.6 * (1 - f)), 1 if f > 0.4 else 0, [0, -th, 0]))
        spin['cubes'].append(_cube((0, 0, -1.2), (3.0, 0.8, 1.2), 0))
        tail['cubes'] += [_cube((0, 0, 3.0), (1.6, 0.4, 3.0), 2)]
    else:  # needle
        spin['cubes'] += [_cube((0, 0, 0), (0.8, 0.8, 11.0), 0, [0, 0, 45]), _cube((0, 0, -6.2), (1.4, 1.4, 1.8), 1, [0, 0, 45]),
                          _cube((0, 0, -7.6), (0.6, 0.6, 1.2), 0, [0, 0, 45])]
        for k in range(3):
            a = k * 120
            spin['cubes'].append(_cube((math.cos(math.radians(a)) * 0.9, math.sin(math.radians(a)) * 0.9, 4.2), (0.4, 0.4, 2.6), 2))
        tail['cubes'] += [_cube((0, 0, 7.4), (0.5, 0.5, 3.0), 3)]
    return {
        'description': {'identifier': f'geometry.bc.bolt_{kind}', 'texture_width': 4, 'texture_height': 4,
                        'visible_bounds_width': 2, 'visible_bounds_height': 2, 'visible_bounds_offset': [0, 0, 0]},
        'bones': [root, spin, tail],
    }


def bolt_geometry_file():
    return {'format_version': '1.16.0', 'minecraft:geometry': [_bolt_shape(k) for k in BOLT_SHAPES]}


def bolt_tint_texture(hexcol):
    c = np.array(rgb(hexcol)[:3], dtype=np.float32)
    core = c + (255 - c) * 0.72
    a = tex.new(4, 4)
    for col, (rgbv, alpha) in enumerate(((core, 130), (c, 130), (c * 0.62, 140), (c * 0.32, 255))):
        a[:, col, :3] = np.clip(rgbv, 0, 255)
        a[:, col, 3] = alpha
    return a


def bolt_animations():
    return {'animation.bc.mana_bolt.fly': {'loop': True, 'bones': {
        'root': {'rotation': ORIENT},
        'spin': {'rotation': [0, 0, 'q.life_time * 540.0'], 'scale': '1.0 + math.sin(q.life_time * 1100.0) * 0.07'},
        'tail': {'scale': [1, 1, '1.0 + math.sin(q.life_time * 900.0) * 0.15']},
    }}}


# ======================================================================================
# Magic Knight (one geometry, nine robe textures)
# ======================================================================================
HAIR = [tex.ramp('1a120c', '2a1e14', '3c2c1e', '503c2a'), tex.ramp('6a4a1a', '9a6e28', 'c89a3e', 'e8c26a'),
        tex.ramp('3a0e0a', '5e1a12', '84281c', 'a83c2a'), tex.ramp('5a5a62', '82828c', 'a8a8b2', 'd0d0d8'),
        tex.ramp('0c0c14', '161624', '22223a', '303052'), tex.ramp('2a1a0e', '42291a', '5c3a24', '764c2f')]


def knight_geo(rid, idx=0):
    r = ROBES[rid]
    g = Geo('geometry.bc.magic_knight', res=2, atlas_width=128, visible=(2, 3, (0, 1.2, 0)), seed=11)
    _humanoid_bones(g)
    g.bone('cape', 'body', (0, 24, 2.6))
    g.bone('book', 'waist', (4.8, 12, 0))
    skin = tex.Material(SKIN[1:] if idx % 3 else tex.ramp('6a4430', '84583e', '9e6c4e', 'b88460'), noise=0.08, edge=0.85)
    hair = tex.Material(HAIR[idx % len(HAIR)], noise=0.2)
    cloth = tex.Cloth(P[r['cloth']])
    lining = tex.Cloth(P[r['lining']])
    trim = tex.Metal(P[r['trim']])
    trim_c = P[r['trim']][-2]
    tunic = tex.Cloth(tex.ramp('16181e', '20232b', '2c303a', '3a3f4b'), folds=0.12)
    trousers = tex.Cloth(tex.ramp('1c1610', '2a2118', '3a2e22', '4a3c2c'), folds=0.1)
    boots = tex.Material(tex.ramp('0e0a08', '1a1410', '281e18', '362a20'), noise=0.1)
    leather = tex.Material(P['leather'], noise=0.1)
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(skin, {'north': _face()}))
    g.cube('head', (-4.3, 30.2, -4.3), (8.6, 2.4, 8.6), hair)
    g.cube('head', (-4.3, 25.4, 2.4), (8.6, 5.2, 1.9), hair)
    g.cube('head', (-4.4, 28.4, -4.4), (1.6, 2.4, 6.0), hair)
    g.cube('head', (2.8, 28.4, -4.4), (1.6, 2.4, 6.0), hair)
    g.cube('body', (-4, 12, -2), (8, 12, 4), tunic)
    g.cube('body', (-4.3, 12.6, -2.3), (8.6, 1.6, 4.6), leather)
    g.cube('body', (-1.0, 12.4, -2.5), (2.0, 2.0, 0.4), trim)
    # robe mantle
    g.cube('body', (-4.6, 17.6, -2.6), (9.2, 6.6, 5.2), cloth)
    g.cube('body', (-3.4, 23.6, -2.9), (6.8, 1.4, 5.8), tex.PerFace(cloth, up=lining))
    g.cube('body', (-1.0, 21.6, -3.05), (2.0, 1.6, 0.5), trim)
    g.cube('body', (-4.7, 17.3, -2.7), (9.4, 0.5, 5.4), trim)
    g.cube('cape', (-5.0, 8.0, 2.6), (10.0, 16.0, 0.8), tex.PerFace(tex.Painted(cloth, {'south': _emblem(r['emblem'], trim_c)}), north=lining))
    for side, x0 in (('rightArm', -8), ('leftArm', 4)):
        g.cube(side, (x0, 14, -2), (4, 10, 4), tunic)
        g.cube(side, (x0 - 0.4, 17.4, -2.4), (4.8, 6.9, 4.8), cloth)
        g.cube(side, (x0 - 0.5, 17.1, -2.5), (5.0, 0.5, 5.0), trim)
        g.cube(side, (x0 - 0.2, 13.4, -2.2), (4.4, 1.4, 4.4), leather)
        g.cube(side, (x0, 12, -2), (4, 2, 4), skin)
    g.cube('rightLeg', (-3.9, 3, -2), (4, 9, 4), trousers)
    g.cube('leftLeg', (-0.1, 3, -2), (4, 9, 4), trousers)
    g.cube('rightLeg', (-4.1, 0, -2.3), (4.4, 4.2, 4.6), boots)
    g.cube('leftLeg', (-0.3, 0, -2.3), (4.4, 4.2, 4.6), boots)
    # grimoire hanging from the belt
    g.cube('book', (4.3, 8.6, -1.8), (1.6, 4.4, 3.6), tex.Material(tex.ramp('2a1608', '3e2210', '58321a', '704428'), noise=0.1))
    g.cube('book', (4.2, 9.6, -1.9), (1.8, 0.6, 3.8), trim)
    return g


def knight_animations():
    anims = humanoid_animations('magic_knight')
    anims['animation.bc.magic_knight.idle']['bones']['cape'] = {'rotation': ['4.0 + math.sin(q.life_time * 110.0) * 2.5', 0, 0]}
    anims['animation.bc.magic_knight.walk']['bones']['cape'] = {'rotation': ['math.clamp(q.modified_move_speed * 70.0, 0.0, 50.0)', 0, 0]}
    anims['animation.bc.magic_knight.cast'] = {'animation_length': 0.8, 'bones': {
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.18': [-95, 12, 0], '0.55': [-90, 8, 0], '0.8': [0, 0, 0]}},
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.18': [-70, -20, 0], '0.55': [-65, -15, 0], '0.8': [0, 0, 0]}},
        'body': {'rotation': {'0.0': [0, 0, 0], '0.18': [0, -12, 0], '0.8': [0, 0, 0]}},
        'cape': {'rotation': {'0.0': [4, 0, 0], '0.2': [28, 0, 0], '0.8': [4, 0, 0]}},
    }}
    return anims


# ======================================================================================
# Magic Merchant
# ======================================================================================
def merchant_geo():
    g = Geo('geometry.bc.magic_merchant', res=2, atlas_width=128, visible=(2, 3, (0, 1.2, 0)))
    _humanoid_bones(g)
    g.bone('pack', 'body', (0, 20, 2))
    g.bone('hat', 'head', (0, 32, 0))
    skin = tex.Material(tex.ramp('7a5038', '94664a', 'ae7e5c', 'c69872'), noise=0.08, edge=0.85)
    coat = tex.Cloth(tex.ramp('0a2a2c', '10403e', '185856', '227270', '2e8e8a'), folds=0.18)
    sash = tex.Cloth(tex.ramp('4a2a06', '7a4a10', 'a8701c', 'd39a2c'))
    hatm = tex.Material(tex.ramp('1a0e22', '2a1636', '3c2050', '502c6a'), noise=0.1)
    wood = tex.Wood(P['wood'])
    canvas = tex.Cloth(tex.ramp('4a3c28', '6a583c', '8a7652', 'a8946c'), folds=0.2)
    glass = [tex.Crystal(tex.ramp('3a0a3a', '7a1a7a', 'c040c0', 'ff9aff'), alpha=200), tex.Crystal(P['ice'], alpha=200),
             tex.Crystal(tex.ramp('0a3a0a', '1a7a1a', '40c040', '9aff9a'), alpha=200)]
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(skin, {'north': _face(beard=True)}))
    g.cube('hat', (-7, 31.4, -7), (14, 0.8, 14), hatm)
    g.cube('hat', (-4.2, 32.2, -4.2), (8.4, 4.6, 8.4), hatm)
    g.cube('hat', (-4.4, 32.2, -4.4), (8.8, 1.0, 8.8), sash)
    g.box('hat', (4.4, 36, 1), (0.8, 6, 1.6), tex.Material(tex.ramp('8a1010', 'c02020', 'ff5a3a')), rotation=[-20, 0, -25], pivot=(4.4, 33, 1))
    g.cube('body', (-4.4, 8, -2.4), (8.8, 16, 4.8), coat)
    g.cube('body', (-4.6, 13, -2.6), (9.2, 2.0, 5.2), sash)
    for side, x0 in (('rightArm', -8), ('leftArm', 4)):
        g.cube(side, (x0 - 0.4, 13.5, -2.4), (4.8, 10.5, 4.8), coat)
        g.cube(side, (x0, 12, -2), (4, 2, 4), skin)
    g.cube('rightLeg', (-3.9, 0, -2), (4, 8, 4), tex.Material(tex.ramp('1a1410', '281e18', '362a20')))
    g.cube('leftLeg', (-0.1, 0, -2), (4, 8, 4), tex.Material(tex.ramp('1a1410', '281e18', '362a20')))
    # the huge backpack
    g.cube('pack', (-5, 9, 2.4), (10, 14, 6), canvas)
    g.cube('pack', (-5.4, 22, 2.0), (10.8, 2.0, 6.8), wood)
    g.cube('pack', (-5.4, 9, 2.0), (10.8, 1.6, 6.8), wood)
    for k, x in enumerate((-3.5, 0, 3.0)):
        g.box('pack', (x, 25.5, 5.5), (1.6, 3.2 + k, 1.6), glass[k])
    g.box('pack', (0, 27, 3.2), (12, 1.6, 1.6), tex.Material(P['paper']), rotation=[0, 0, 8], pivot=(0, 27, 3.2))
    g.box('pack', (5.6, 16, 5.2), (1.4, 3, 3), tex.Metal(P['gold']))
    return g


# ======================================================================================
# Ancient constructs (summons + War Table faction): one geometry, four textures
# ======================================================================================
CONSTRUCT_KINDS = ['sand', 'plant', 'bone', 'crystal']


def construct_geo(kind):
    mats = {
        'sand': (tex.Stone(tex.ramp('5a4424', '7a5f34', '967a46', 'b29558', 'cdb070', 'e0c88a'), brick=0), tex.Material(tex.ramp('8a6a3a', 'b0894c', 'd6ae62')), 'ffcc66'),
        'plant': (tex.Wood(tex.ramp('2a1a0e', '3e2814', '54381c', '6a4826', '805a30')), tex.Material(P['clover_green'][1:6], noise=0.25), '9aff6a'),
        'bone': (tex.Material(P['bone'], noise=0.08, edge=0.7), tex.Material(tex.ramp('3a3228', '5a5040', '7a705c'), noise=0.1), 'a0ffe8'),
        'crystal': (tex.Crystal(tex.ramp('0a3a32', '125a4e', '2a8e7e', '5ad8c0', 'c8fff4'), alpha=230), tex.Crystal(tex.ramp('2a1a4a', '4a2a7a', '7a4ac0', 'c08aff'), alpha=210), 'ffffff'),
    }
    body, accent, eye = mats[kind]
    g = Geo('geometry.bc.construct', res=2, atlas_width=128, visible=(3, 3, (0, 1.2, 0)), seed=23)
    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 14, 0))
    g.bone('head', 'body', (0, 25, -1))
    g.bone('rightArm', 'body', (-7, 23, 0))
    g.bone('leftArm', 'body', (7, 23, 0))
    g.bone('rightLeg', 'root', (-3, 11, 0))
    g.bone('leftLeg', 'root', (3, 11, 0))

    def eyes(a, ctx):
        h, w = a.shape[:2]
        for ex in (int(w * 0.2), int(w * 0.6)):
            a[int(h * 0.45):int(h * 0.45) + 2, ex:ex + max(2, int(w * 0.2)), :3] = rgb(eye)[:3]
            a[int(h * 0.45):int(h * 0.45) + 2, ex:ex + max(2, int(w * 0.2)), 3] = 130
        return a
    g.cube('body', (-6, 11, -3.5), (12, 13, 7), body)
    g.cube('body', (-4, 15, -3.9), (8, 6, 0.6), accent)
    g.cube('head', (-3.5, 24.5, -5), (7, 7, 7), tex.Painted(body, {'north': eyes}))
    g.cube('head', (-4, 30.5, -5.5), (8, 1.4, 8), accent)
    for side, sx in (('rightArm', -1), ('leftArm', 1)):
        x0 = -10.5 if sx < 0 else 6.5
        g.cube(side, (x0, 9, -2.5), (4, 14, 5), body)
        g.cube(side, (x0 - 0.5, 6, -3), (5, 4, 6), accent)
        g.box(side, (sx * 9, 25, 0), (2, 4, 2), accent, rotation=[0, 0, sx * -25], pivot=(sx * 9, 23, 0))
    for side, x0 in (('rightLeg', -5.5), ('leftLeg', 0.5)):
        g.cube(side, (x0, 0, -2.5), (5, 11, 5), body)
    for k, (x, y) in enumerate(((-3, 22), (2.5, 20), (0, 17))):
        g.box('body', (x, y, 4.2), (1.8, 4 + k, 1.8), accent, rotation=[-30, 0, k * 15 - 15], pivot=(x, y - 2, 3.5))
    return g


# ======================================================================================
# Stone Colossus (giant boss; reuses the golem bone layout & animations)
# ======================================================================================
def _colossus_runes(a, ctx):
    h, w = a.shape[:2]
    rng = np.random.default_rng(ctx.seed)
    for _ in range(max(1, (h * w) // 160)):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        L = int(rng.integers(2, 6))
        horiz = rng.random() < 0.5
        for i in range(L):
            xx, yy = (x + i, y) if horiz else (x, y + i)
            if 0 <= xx < w and 0 <= yy < h:
                a[yy, xx, :3] = rgb('ff8a2a')[:3]
                a[yy, xx, 3] = 130
    return a


def colossus_geo():
    g = Geo('geometry.bc.stone_colossus', res=2, atlas_width=256, visible=(4, 5, (0, 2, 0)))
    rock = tex.Painted(tex.Stone(P['mossstone'], brick=0), {'*': _colossus_runes})
    plain = tex.Stone(tex.ramp('22241e', '30332a', '404437', '525646', '686c58', '80846c'), brick=0)
    moss = tex.Material(P['clover_green'][1:5], noise=0.3)
    core = tex.Energy(tex.ramp('8a1a00', 'd04a08', 'ff8a2a', 'ffd08a', 'ffffff'), alpha=130)
    bark = tex.Wood(P['wood'])
    crystal = tex.Crystal(tex.ramp('5a1a00', '9a3a08', 'e07a20', 'ffc070', 'fff0d0'), alpha=215)

    def eyes(a, ctx):
        h, w = a.shape[:2]
        for ex in (int(w * 0.2), int(w * 0.6)):
            a[int(h * 0.5):int(h * 0.5) + 3, ex:ex + max(2, int(w * 0.2)), :3] = rgb('ff9a3a')[:3]
            a[int(h * 0.5):int(h * 0.5) + 3, ex:ex + max(2, int(w * 0.2)), 3] = 130
        a[int(h * 0.36), :, :3] *= 0.5
        return a
    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 16, 0))
    g.bone('head', 'body', (0, 30, -6))
    g.bone('rightArm', 'body', (-12, 29, 0))
    g.bone('leftArm', 'body', (12, 29, 0))
    g.bone('rightLeg', 'root', (-5, 12, 0))
    g.bone('leftLeg', 'root', (5, 12, 0))
    # hunched torso
    g.cube('body', (-11, 14, -6), (22, 17, 13), rock, rotation=[12, 0, 0], pivot=(0, 16, 0))
    g.cube('body', (-7, 11, -4.5), (14, 4, 9), plain)
    g.box('body', (0, 22, -6.6), (5, 5, 1.6), core, rotation=[12, 0, 45], pivot=(0, 22, -6.6))
    g.cube('body', (-11.4, 28, -4), (22.8, 4, 12.6), moss, rotation=[12, 0, 0], pivot=(0, 16, 0))
    # a little tree grows on its back
    g.box('body', (4, 33, 6), (1.6, 7, 1.6), bark, rotation=[-10, 0, 8], pivot=(4, 30, 6))
    g.box('body', (4.5, 39, 6), (6, 4, 6), moss)
    g.box('body', (4.5, 42, 6), (3.6, 2.4, 3.6), moss)
    for k, (x, z) in enumerate(((-6, 4), (-2, 7), (8, 2))):
        g.box('body', (x, 30.5 + k % 2, z), (2.4, 4 + k, 2.4), crystal, rotation=[-20, k * 40, 15], pivot=(x, 29, z))
    # small head sunk between the shoulders
    g.cube('head', (-4.5, 26, -13), (9, 8, 8), tex.Painted(plain, {'north': eyes}))
    g.cube('head', (-5.2, 32.5, -13.6), (10.4, 1.8, 9.2), moss)
    # massive arms that reach the ground
    for side, sx in (('rightArm', -1), ('leftArm', 1)):
        x0 = -20 if sx < 0 else 12
        g.cube(side, (x0, 14, -5), (8, 16, 10), rock)
        g.cube(side, (x0 - 1, 2, -6), (10, 12, 12), plain)
        g.cube(side, (x0 - 1.4, 24, -5.4), (10.8, 7, 10.8), tex.Painted(tex.Stone(P['mossstone'], brick=0), {'up': lambda a, c: (a.__setitem__((slice(None), slice(None), slice(0, 3)), np.clip(a[..., :3] * 0.8 + np.array([20, 60, 20]), 0, 255)), a)[1]}))
        for k in range(3):
            g.box(side, (x0 + 4 + (k - 1) * 3, 1.0, -6.4), (2.4, 3, 2.4), plain)
        g.box(side, (sx * 16, 32, 0), (3, 5, 3), crystal, rotation=[0, 0, sx * -25], pivot=(sx * 16, 30, 0))
    for side, x0 in (('rightLeg', -10), ('leftLeg', 1)):
        g.cube(side, (x0, 0, -5), (9, 13, 10), rock)
    return g


# ======================================================================================
# Storm Kraken (sea boss)
# ======================================================================================
KRAKEN = tex.ramp('0a0a1e', '141434', '1e1e4a', '2a2a62', '38387c', '4a4a98')


def _kraken_spots(a, ctx):
    h, w = a.shape[:2]
    rng = np.random.default_rng(ctx.seed)
    for _ in range(max(1, (h * w) // 40)):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        a[y, x, :3] = np.minimum(a[y, x, :3] * 1.5 + 20, 255)
    if ctx.face == 'north' and ctx.cube.get('name') == 'mantle_front':
        for ex in (int(w * 0.18), int(w * 0.66)):
            ey = int(h * 0.6)
            a[ey:ey + 3, ex:ex + 3, :3] = rgb('7ae8ff')[:3]
            a[ey:ey + 3, ex:ex + 3, 3] = 130
            a[ey + 1, ex + 1, :3] = rgb('ffffff')[:3]
    return a


def _suckers(a, ctx):
    h, w = a.shape[:2]
    a[..., :3] = np.clip(a[..., :3] * 0.6 + np.array([60, 50, 80]), 0, 255)
    for y in range(1, h, 3):
        a[y, w // 2 - 1:w // 2 + 1, :3] = rgb('c8b8e8')[:3]
    return a


def _bolt_stripe(a, ctx):
    h, w = a.shape[:2]
    for y in range(h):
        x = int(w / 2 + math.sin(y * 0.9) * w * 0.25)
        a[y, max(0, x):min(w, x + 1), :3] = rgb('9ae8ff')[:3]
        a[y, max(0, x):min(w, x + 1), 3] = 130
    return a


def kraken_geo():
    g = Geo('geometry.bc.storm_kraken', res=2, atlas_width=256, visible=(6, 6, (0, 2, 0)))
    skin = tex.Painted(tex.Material(KRAKEN, noise=0.2, edge=0.7), {'*': _kraken_spots})
    under = tex.Painted(tex.Material(KRAKEN, noise=0.15), {'*': _suckers})
    stripe = tex.Painted(tex.Material(KRAKEN, noise=0.2), {'*': _bolt_stripe})
    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 14, 0))
    g.bone('mantle', 'body', (0, 22, 2))
    g.cube('body', (-9, 10, -9), (18, 12, 18), skin)
    g.cube('body', (-7, 20, -9.6), (14, 7, 2), skin, name='mantle_front')
    g.cube('mantle', (-8.5, 21, -7.5), (17, 10, 16), stripe)
    g.cube('mantle', (-7.5, 30, -5.5), (15, 9, 15), skin)
    g.cube('mantle', (-6, 38, -3), (12, 8, 13), stripe)
    g.cube('mantle', (-4, 45, 0), (8, 6, 9), skin)
    g.cube('mantle', (-2.5, 50, 3), (5, 4, 5), skin)
    for k in range(8):
        a = k * 45 + 22.5
        r = math.radians(a)
        bx, bz = math.sin(r) * 7, -math.cos(r) * 7
        prev = 'body'
        y = 11.0
        dist = 7.0
        for s in range(4):
            name = f't{k}_{s}'
            g.bone(name, prev, (round(math.sin(r) * dist, 3), y, round(-math.cos(r) * dist, 3)))
            th = 5.0 - s * 1.0
            ln = 10.0 - s * 1.2
            cx = math.sin(r) * (dist + ln / 2)
            cz = -math.cos(r) * (dist + ln / 2)
            g.box(name, (cx, y - th / 2 + 0.2, cz), (th, th, ln), tex.PerFace(skin, down=under), rotation=[0, -a, 0], pivot=(cx, y, cz))
            dist += ln
            y -= 0.6
            prev = name
        del bx, bz
    return g


def kraken_animations():
    bones = {'body': {'rotation': ['math.sin(q.life_time * 50.0) * 3.0', 0, 'math.cos(q.life_time * 40.0) * 2.0']},
             'mantle': {'rotation': ['-6.0 + math.sin(q.life_time * 70.0) * 5.0', 0, 0], 'scale': [1, '1.0 + math.sin(q.life_time * 120.0) * 0.03', 1]}}
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        for s in range(4):
            amp = 10 + s * 6
            ph = k * 45 + s * 55
            # curl around the axis that is tangent to the ring (so tentacles rise and fall)
            bones[f't{k}_{s}'] = {'rotation': [f'math.sin(q.life_time * 140.0 - {ph}) * {amp * math.cos(a):.2f}',
                                               f'math.sin(q.life_time * 90.0 - {ph}) * 8.0',
                                               f'math.sin(q.life_time * 140.0 - {ph}) * {amp * math.sin(a):.2f}']}
    slam = {}
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        for s in range(4):
            up = -40 if s == 0 else 25
            slam[f't{k}_{s}'] = {'rotation': {'0.0': [0, 0, 0], '0.45': [round(up * math.cos(a), 2), 0, round(up * math.sin(a), 2)],
                                              '0.7': [round(-up * 0.6 * math.cos(a), 2), 0, round(-up * 0.6 * math.sin(a), 2)], '1.1': [0, 0, 0]}}
    return {
        'animation.bc.storm_kraken.swim': {'loop': True, 'bones': bones},
        'animation.bc.storm_kraken.slam': {'animation_length': 1.1, 'bones': slam},
        'animation.bc.storm_kraken.look_at_target': {'loop': True, 'bones': {'body': {'rotation': [0, 'q.target_y_rotation * 0.4', 0]}}},
    }


# ======================================================================================
# Phantom Galleon: the sailing ship, repainted as a ghost
# ======================================================================================
def ghostify(a):
    rgbf = a[..., :3].astype(np.float32)
    lum = (rgbf[..., 0] * 0.3 + rgbf[..., 1] * 0.55 + rgbf[..., 2] * 0.15) / 255.0
    dark = np.array([10, 30, 34], dtype=np.float32)
    light = np.array([150, 255, 220], dtype=np.float32)
    t = np.clip(lum * 1.4, 0, 1)[..., None]
    out = dark * (1 - t) + light * t
    a = a.copy()
    a[..., :3] = out.astype(np.uint8)
    glow = (lum > 0.5) & (a[..., 3] > 0)
    a[..., 3] = np.where(glow, 140, np.where(a[..., 3] > 0, 255, 0))
    return a


def galleon_animations():
    return {'animation.bc.phantom_galleon.drift': {'loop': True, 'bones': {
        'root': {'position': [0, 'math.sin(q.life_time * 60.0) * 2.0', 0], 'rotation': ['math.sin(q.life_time * 45.0) * 2.0', 0, 'math.sin(q.life_time * 35.0) * 3.0']},
        'sail': {'rotation': ['math.sin(q.life_time * 90.0) * 3.0', 0, 0], 'scale': [1, 1, '1.4 + math.sin(q.life_time * 70.0) * 0.2']},
        'topsail': {'rotation': ['math.sin(q.life_time * 100.0) * 3.0', 0, 0]},
        'flag': {'rotation': [0, 'math.sin(q.life_time * 320.0) * 18.0', 0]},
        'wheel': {'rotation': [0, 0, 'q.life_time * 40.0']},
    }}}


def recolor_devil(a):
    rgbf = a[..., :3].astype(np.float32)
    lum = rgbf.max(axis=-1) / 255.0
    r = tex.ramp('0a0204', '2a0408', '5a0810', '9a1018', 'e02a2a', 'ff9a6a', 'fff0d8')
    q = tex.quantize(r, np.clip(lum, 0, 1))
    a = a.copy()
    a[..., :3] = q[..., :3]
    return a


# ======================================================================================
# War Table block (16 x 16 x 16 block space; origin at the block's bottom centre)
# ======================================================================================
def _map_top(a, ctx):
    h, w = a.shape[:2]
    a[:] = tex.quantize(P['paper'], np.clip(0.55 + tex.value_noise(h, w, 3, ctx.seed) * 0.25, 0, 1))
    rng = np.random.default_rng(3)
    for _ in range(6):
        cx, cy, r = rng.integers(2, w - 2), rng.integers(2, h - 2), rng.integers(2, 5)
        yy, xx = np.mgrid[0:h, 0:w]
        m = (xx - cx) ** 2 + (yy - cy) ** 2 < r * r
        a[m, :3] = np.clip(a[m, :3] * np.array([0.7, 0.85, 0.65]), 0, 255)
    for y in range(h):
        x = int(w * 0.5 + math.sin(y * 0.4) * w * 0.15)
        a[y, max(0, x):x + 1, :3] = rgb('3c7ac8')[:3]
    a[[0, -1], :, :3] = rgb('5a3a20')[:3]
    a[:, [0, -1], :3] = rgb('5a3a20')[:3]
    a[..., 3] = 255
    return a


def war_table_geo():
    g = Geo('geometry.bc.war_table', res=4, atlas_width=128, visible=(2, 2, (0, 0.5, 0)))
    g.bone('table', pivot=(0, 0, 0))
    wood = tex.Wood(P['wood'])
    dark = tex.Wood(tex.ramp('1a0e06', '2a180c', '3a2214', '4a2e1a'))
    g.cube('table', (-8, 11, -8), (16, 2, 16), tex.PerFace(wood, up=tex.Painted(wood, {'up': _map_top})), mi='*')
    for x, z in ((-7, -7), (5, -7), (-7, 5), (5, 5)):
        g.cube('table', (x, 0, z), (2, 11, 2), dark, mi='*')
    g.cube('table', (-6, 3, -6.5), (12, 1.5, 1), dark, mi='*')
    g.cube('table', (-6, 3, 5.5), (12, 1.5, 1), dark, mi='*')
    red = tex.Material(tex.ramp('4a0a0a', '7a1414', 'b02020', 'e04a3a'), noise=0.05)
    blue = tex.Material(tex.ramp('0a1a4a', '14307a', '2050b0', '4a80e0'), noise=0.05)
    for k, (x, z) in enumerate(((-5, -3), (-3, -5), (-4, 0))):
        g.cube('table', (x, 13, z), (1.4, 2.6, 1.4), red, mi='*')
        g.cube('table', (x + 0.2, 15.6, z + 0.2), (1.0, 1.0, 1.0), red, mi='*')
    for k, (x, z) in enumerate(((3.5, 2), (2, 4), (4.5, -1))):
        g.cube('table', (x, 13, z), (1.4, 2.6, 1.4), blue, mi='*')
        g.cube('table', (x + 0.2, 15.6, z + 0.2), (1.0, 1.0, 1.0), blue, mi='*')
    g.cube('table', (5.5, 13, -6.5), (1.6, 2.4, 1.6), tex.Material(tex.ramp('c8c0a8', 'e8e0c8', 'fff8e8')), mi='*')
    g.cube('table', (6.05, 15.4, -5.95), (0.5, 0.9, 0.5), tex.Flat('ffd36a', alpha=130), mi='*')
    return g


# ======================================================================================
# icons (32 x 32)
# ======================================================================================
def _icon(fn, outline='0a0a0f'):
    a = tex.draw_layer(32, 32, fn, 4)
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    tex.outline(a, rgb(outline))
    return a


def wave4_icons():
    def sigil(d, s):
        d.ellipse([3 * s, 3 * s, 29 * s, 29 * s], fill=(60, 8, 14, 255), outline=(200, 40, 40, 255), width=int(2 * s))
        pts = []
        for k in range(10):
            r = 11 if k % 2 == 0 else 4.5
            a = -math.pi / 2 + k * math.pi / 5
            pts.append(((16 + math.cos(a) * r) * s, (16.5 + math.sin(a) * r) * s))
        d.polygon(pts, fill=(255, 80, 60, 255))
        for sx in (-1, 1):
            d.polygon([((16 + sx * 6) * s, 7 * s), ((16 + sx * 11) * s, 1 * s), ((16 + sx * 8) * s, 9 * s)], fill=(30, 20, 20, 255))

    def core(d, s):
        d.polygon([(16 * s, 2 * s), (27 * s, 10 * s), (27 * s, 22 * s), (16 * s, 30 * s), (5 * s, 22 * s), (5 * s, 10 * s)], fill=(70, 74, 62, 255))
        d.polygon([(16 * s, 7 * s), (22 * s, 12 * s), (22 * s, 20 * s), (16 * s, 25 * s), (10 * s, 20 * s), (10 * s, 12 * s)], fill=(255, 140, 50, 255))
        d.polygon([(16 * s, 11 * s), (19 * s, 14 * s), (19 * s, 18 * s), (16 * s, 21 * s), (13 * s, 18 * s), (13 * s, 14 * s)], fill=(255, 230, 170, 255))

    def bell(d, s):
        d.polygon([(10 * s, 8 * s), (22 * s, 8 * s), (25 * s, 24 * s), (7 * s, 24 * s)], fill=(90, 200, 170, 255))
        d.ellipse([10 * s, 3 * s, 22 * s, 13 * s], fill=(90, 200, 170, 255))
        d.rectangle([5 * s, 23 * s, 27 * s, 26 * s], fill=(60, 150, 130, 255))
        d.ellipse([14 * s, 25 * s, 18 * s, 29 * s], fill=(200, 255, 240, 255))
        d.line([(13 * s, 9 * s), (11 * s, 21 * s)], fill=(200, 255, 240, 255), width=int(1.3 * s))

    def lure(d, s):
        d.ellipse([8 * s, 4 * s, 24 * s, 20 * s], fill=(40, 40, 110, 255))
        for k in range(5):
            x = 9 + k * 3.5
            d.line([(x * s, 17 * s), ((x + math.sin(k) * 2) * s, 29 * s)], fill=(60, 60, 140, 255), width=int(2 * s))
        d.ellipse([11 * s, 9 * s, 14 * s, 12 * s], fill=(130, 240, 255, 255))
        d.ellipse([18 * s, 9 * s, 21 * s, 12 * s], fill=(130, 240, 255, 255))
        d.line([(16 * s, 1 * s), (13 * s, 6 * s), (18 * s, 6 * s), (15 * s, 11 * s)], fill=(255, 255, 160, 255), width=int(1.2 * s))

    def contract(d, s):
        d.rectangle([7 * s, 3 * s, 25 * s, 28 * s], fill=(236, 222, 186, 255))
        for y in (8, 12, 16):
            d.line([(10 * s, y * s), (22 * s, y * s)], fill=(120, 100, 70, 255), width=int(s))
        d.ellipse([16 * s, 19 * s, 24 * s, 27 * s], fill=(190, 30, 30, 255))
        tex.clover_shape(d, 20 * s, 23 * s, 3 * s, 4, (255, 210, 90, 255), stem=False)
        d.rectangle([5 * s, 2 * s, 27 * s, 5 * s], fill=(130, 90, 50, 255))

    def horn(d, s):
        d.polygon([(4 * s, 22 * s), (24 * s, 6 * s), (28 * s, 10 * s), (10 * s, 26 * s)], fill=(220, 200, 160, 255))
        d.ellipse([20 * s, 3 * s, 30 * s, 13 * s], fill=(200, 170, 110, 255))
        d.ellipse([22.5 * s, 5.5 * s, 27.5 * s, 10.5 * s], fill=(60, 40, 20, 255))
        for k in range(3):
            x = 9 + k * 5
            d.line([((x) * s, (22 - k * 4) * s), ((x + 3) * s, (25 - k * 4) * s)], fill=(160, 110, 40, 255), width=int(1.4 * s))
        d.ellipse([2 * s, 20 * s, 7 * s, 25 * s], fill=(160, 110, 40, 255))

    def table(d, s):
        d.polygon([(2 * s, 14 * s), (16 * s, 7 * s), (30 * s, 14 * s), (16 * s, 21 * s)], fill=(214, 196, 150, 255))
        d.polygon([(2 * s, 14 * s), (16 * s, 21 * s), (16 * s, 24 * s), (2 * s, 17 * s)], fill=(110, 70, 40, 255))
        d.polygon([(30 * s, 14 * s), (16 * s, 21 * s), (16 * s, 24 * s), (30 * s, 17 * s)], fill=(80, 50, 28, 255))
        for x in (4, 15, 28):
            d.rectangle([x * s, 17 * s, (x + 1.6) * s, 29 * s], fill=(70, 44, 24, 255))
        d.rectangle([10 * s, 9 * s, 12 * s, 14 * s], fill=(200, 40, 40, 255))
        d.rectangle([19 * s, 12 * s, 21 * s, 17 * s], fill=(50, 90, 210, 255))
    return {'archdevil_sigil': _icon(sigil), 'colossus_core': _icon(core), 'galleon_bell': _icon(bell), 'kraken_lure': _icon(lure),
            'knight_contract': _icon(contract), 'skirmish_horn': _icon(horn), 'war_table': _icon(table)}
