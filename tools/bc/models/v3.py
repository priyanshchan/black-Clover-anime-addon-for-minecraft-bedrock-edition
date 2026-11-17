"""v0.3.0 models and animations: flying brooms, the Mission Board, Rogue Mages, the Witch Sisters, the Bone Dragon,
and new icons (brooms, amulets, boss summons). All designs are original."""
from __future__ import annotations

import math

import numpy as np

from .. import tex
from ..geo import Geo
from ..tex import P, rgb
from .sea import SKIN, _face, _humanoid_bones, humanoid_animations

ROGUE_COLORS = [
    ('crimson', tex.ramp('1a0406', '2e080c', '440e14', '5c141c', '761c26')),
    ('forest', tex.ramp('08140a', '0e2212', '16321a', '204426', '2a5832')),
    ('ash', tex.ramp('121216', '1e1e24', '2c2c34', '3c3c46', '4e4e5a')),
    ('violet', tex.ramp('12081a', '1e0e2c', '2c1640', '3c2056', '4e2a6e')),
]


# ======================================================================================
# brooms (rideable): one geometry, a texture per tier
# ======================================================================================
def broom_geo(tier):
    swift = tier == 'swift_broom'
    g = Geo('geometry.bc.broom', res=2, atlas_width=64, visible=(3, 2, (0, 0.4, 0)), seed=31)
    handle = tex.Wood(tex.ramp('2a180c', '3e2414', '54321c', '6a4226') if not swift else tex.ramp('101820', '1a2632', '263646', '34485c'))
    straw = tex.Material(tex.ramp('6a4a14', '8a6420', 'aa8030', 'c89c44', 'e0b85a') if not swift else tex.ramp('2a4a6a', '3a6a8a', '5a8aaa', '8ab4cc', 'c0dcea'), noise=0.35)
    band = tex.Metal(P['gold'] if not swift else P['silver'])
    gem = tex.Energy(tex.ramp('3a0a3a', '7a1a7a', 'c040c0', 'ff9aff', 'ffffff') if not swift else tex.ramp('0a3a6a', '1a6ab0', '4aa8ff', 'a8e0ff', 'ffffff'), alpha=135)
    g.bone('root', pivot=(0, 0, 0))
    g.bone('bristles', 'root', (0, 6, 7))
    g.cube('root', (-0.9, 5.1, -16), (1.8, 1.8, 24), handle)
    g.cube('root', (-1.1, 4.9, -14.5), (2.2, 2.2, 1.2), band)
    g.cube('root', (-1.1, 4.9, 4.5), (2.2, 2.2, 1.6), band)
    g.box('root', (0, 6, -17.4), (2.2, 2.2, 2.2), gem, rotation=[45, 45, 0], pivot=(0, 6, -17.4))
    g.cube('bristles', (-2.5, 3.5, 7), (5, 5, 5), straw)
    g.cube('bristles', (-3.2, 2.8, 11.5), (6.4, 6.4, 5.5), straw)
    g.cube('bristles', (-2.8, 3.2, 16.5), (5.6, 5.6, 2.5), straw)
    g.cube('bristles', (-2.7, 3.3, 7.4), (5.4, 5.4, 1.0), band)
    if True:  # little fins (painted plain on the basic broom, feathers on the swift one)
        fin = tex.Material(tex.ramp('8a1a1a', 'b02a2a', 'd04040') if not swift else tex.ramp('c8e0ff', 'e8f4ff', 'ffffff'), noise=0.1)
        for sx in (-1, 1):
            g.box('bristles', (sx * 3.6, 7.5, 13), (0.4, 3, 5), fin, rotation=[0, 0, sx * -25], pivot=(sx * 3.2, 6, 13))
    return g


def broom_animations():
    return {'animation.bc.broom.fly': {'loop': True, 'bones': {
        'root': {'position': [0, 'math.sin(q.life_time * 160.0) * 0.6', 0],
                 'rotation': ['-math.clamp(q.modified_move_speed * 25.0, 0.0, 15.0) + math.sin(q.life_time * 120.0) * 2.0', 0, 'math.sin(q.life_time * 90.0) * 3.0']},
        'bristles': {'rotation': [0, 'math.sin(q.life_time * 400.0) * (2.0 + q.modified_move_speed * 10.0)', 0]},
    }}}


# ======================================================================================
# the Mission Board block
# ======================================================================================
def _mission_sheet(kind):
    def fn(a, ctx):
        h, w = a.shape[:2]
        a[:] = tex.quantize(P['paper'], np.clip(0.6 + tex.white_noise(h, w, ctx.seed) * 0.08, 0, 1))
        for y in range(2, h - 2, 2):
            a[y, 1:w - 1 - (y * 3 + kind) % 3, :3] = rgb('6a5a40')[:3]
        a[0:2, :, :3] = rgb('2a7234')[:3] if kind % 2 == 0 else rgb('d39a2c')[:3]
        a[..., 3] = 255
        return a
    return fn


def mission_board_geo():
    g = Geo('geometry.bc.mission_board', res=2, atlas_width=128, visible=(2, 2, (0, 0.5, 0)))
    g.bone('board', pivot=(0, 0, 0))
    post = tex.Wood(tex.ramp('1e130b', '2c1c10', '3b2716', '4c331d'))
    board = tex.Wood(tex.ramp('4a3420', '62462b', '7a5a37', '927044'))
    green = tex.Cloth(P['green_cloth'])
    gold = tex.Metal(P['gold'])
    g.cube('board', (-7.5, 0, -1), (2, 15, 2), post)
    g.cube('board', (5.5, 0, -1), (2, 15, 2), post)
    g.cube('board', (-6, 3.5, -0.5), (12, 10, 1), board)
    g.cube('board', (-8, 13.5, -2.5), (16, 1.5, 5), post)
    g.cube('board', (-6, 13, -1.0), (12, 2.0, 0.6), green)
    for k, (x, y) in enumerate(((-5.2, 8.4), (-1.5, 9.0), (2.2, 8.2), (-3.6, 4.4), (0.4, 4.6))):
        g.cube('board', (x, y, -0.9), (3.0, 3.8, 0.4), tex.PerFace(_mission_sheet(k), south=_mission_sheet(k)))

    def crest(a, ctx):
        h, w = a.shape[:2]

        def draw(d, s):
            tex.clover_shape(d, w * s / 2, h * s / 2, min(w, h) * s * 0.42, 4, (92, 184, 90, 255), stem=False)
        lay = tex.draw_layer(h, w, draw, 4)
        lay[..., 3] = np.where(lay[..., 3] > 100, 255, 0)
        tex.alpha_over(a, lay)
        return a
    g.cube('board', (-1.6, 15, -0.6), (3.2, 3.2, 1.2), tex.Painted(gold, {'north': crest, 'south': crest}))
    return g


# ======================================================================================
# Rogue Mages (hostile mages with stolen grimoires); bone layout matches the Magic Knight
# ======================================================================================
def rogue_geo(variant):
    cloak_r = dict(ROGUE_COLORS)[variant]
    g = Geo('geometry.bc.rogue_mage', res=2, atlas_width=128, visible=(2, 3, (0, 1.2, 0)), seed=41)
    _humanoid_bones(g)
    g.bone('cape', 'body', (0, 24, 2.6))
    g.bone('book', 'waist', (4.8, 12, 0))
    skin = tex.Material(SKIN, noise=0.08, edge=0.85)
    cloak = tex.Cloth(cloak_r, folds=0.22)
    leather = tex.Material(tex.ramp('1a120c', '2a1e14', '3a2a1c', '4a3624'), noise=0.15)
    mask = tex.Cloth(tex.ramp('08080a', '121216', '1c1c22'))
    chain = tex.Metal(tex.ramp('2a2d33', '393d45', '4c515b', '636975'), sheen=0.3)

    def masked(a, ctx):
        _face()(a, ctx)
        h = a.shape[0]
        a[int(h * 0.62):, :, :3] = rgb('0c0c10')[:3]
        return a
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(skin, {'north': masked}))
    g.cube('head', (-4.6, 26.0, -4.6), (9.2, 6.8, 9.2), tex.PerFace(cloak, north=tex.Painted(cloak, {'north': lambda a, c: (a.__setitem__((slice(a.shape[0] // 4, None), slice(a.shape[1] // 6, a.shape[1] - a.shape[1] // 6), 3), 0), a)[1]})))
    g.cube('head', (-3.0, 32.5, -2.5), (6, 2, 6), cloak)
    g.cube('head', (-4.2, 24.0, -4.4), (8.4, 2.4, 0.6), mask)
    g.cube('body', (-4, 12, -2), (8, 12, 4), leather)
    g.cube('body', (-4.5, 8, -2.5), (9, 16, 5), tex.Painted(cloak, {'north': lambda a, c: (a.__setitem__((slice(None), slice(a.shape[1] // 2 - 2, a.shape[1] // 2 + 2), 3), 0), a)[1]}))
    g.cube('body', (-4.7, 12.4, -2.7), (9.4, 1.6, 5.4), leather)
    g.cube('cape', (-5.0, 4.0, 2.6), (10.0, 20.0, 0.8), cloak)
    for side, x0 in (('rightArm', -8), ('leftArm', 4)):
        g.cube(side, (x0 - 0.3, 14, -2.3), (4.6, 10, 4.6), cloak)
        g.cube(side, (x0 - 0.1, 12, -2.1), (4.2, 3, 4.2), leather)
    g.cube('rightLeg', (-3.9, 0, -2), (4, 12, 4), leather)
    g.cube('leftLeg', (-0.1, 0, -2), (4, 12, 4), leather)
    # the stolen grimoire, chained to the belt
    g.cube('book', (4.3, 7.6, -1.8), (1.6, 4.4, 3.6), tex.Material(tex.ramp('2a0a0a', '3e1010', '581818'), noise=0.1))
    g.cube('book', (4.25, 9.3, -2.0), (1.7, 0.6, 4.0), chain)
    g.cube('book', (4.6, 11.0, -0.4), (0.6, 1.6, 0.6), chain)
    return g


# ======================================================================================
# the Witch Sisters
# ======================================================================================
WITCH = {
    'frost_witch': dict(dress=tex.ramp('0a1a2e', '122a46', '1c3c60', '2a527c', '3a6a98'), trim=tex.ramp('8ad8f0', 'c6f0fb', 'f2fdff'),
                        hair=tex.ramp('a8c8d8', 'c8e0ec', 'e8f4fa'), eye='7ae8ff', orb=tex.Crystal(P['ice'], alpha=210)),
    'ember_witch': dict(dress=tex.ramp('1a0404', '2e0808', '460c0c', '601414', '7a1c1c'), trim=tex.ramp('d39a2c', 'f0c24a', 'ffe58a'),
                        hair=tex.ramp('3a0a04', '5a1408', '7a2010', '9a3018'), eye='ffb030', orb=tex.Energy(P['flame'][1:], alpha=135)),
}


def witch_geo(kind):
    w = WITCH[kind]
    g = Geo(f'geometry.bc.{kind}', res=2, atlas_width=128, visible=(3, 4, (0, 1.6, 0)))
    skin = tex.Material(tex.ramp('8a6a5a', 'a8887a', 'c4a696', 'dcc0b0'), noise=0.06, edge=0.85)
    dress = tex.Cloth(w['dress'], folds=0.22)
    trim = tex.Metal(w['trim'])
    hair = tex.Material(w['hair'], noise=0.2)
    hat = tex.Material(tex.ramp('08080c', '121218', '1c1c24', '282832'), noise=0.1)
    wood = tex.Wood(tex.ramp('1e130b', '2c1c10', '3b2716', '4c331d'))

    def face(a, ctx):
        h, wd = a.shape[:2]
        for ex in (int(wd * 0.2), int(wd * 0.6)):
            a[int(h * 0.48):int(h * 0.48) + 2, ex:ex + max(2, int(wd * 0.2)), :3] = rgb(w['eye'])[:3]
            a[int(h * 0.48):int(h * 0.48) + 2, ex:ex + max(2, int(wd * 0.2)), 3] = 130
        a[int(h * 0.78), int(wd * 0.38):int(wd * 0.62), :3] = rgb('6a1a2a')[:3]
        return a
    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 14, 0))
    g.bone('skirt', 'body', (0, 14, 0))
    g.bone('head', 'body', (0, 26, 0))
    g.bone('hat', 'head', (0, 33, 0))
    g.bone('rightArm', 'body', (-5, 24, 0))
    g.bone('leftArm', 'body', (5, 24, 0))
    g.bone('staff', 'rightArm', (-6, 14.5, 0))
    g.cube('head', (-4, 26, -4), (8, 8, 8), tex.Painted(skin, {'north': face}))
    g.cube('head', (-4.3, 26.5, 2.4), (8.6, 7.5, 2.4), hair)
    g.cube('head', (-4.4, 19.0, 3.0), (8.8, 8, 1.6), hair)
    g.cube('hat', (-7.5, 32.6, -7.5), (15, 1.0, 15), hat)
    g.cube('hat', (-4.4, 33.4, -4.4), (8.8, 4.0, 8.8), hat)
    g.cube('hat', (-4.6, 33.4, -4.6), (9.2, 1.2, 9.2), trim)
    g.box('hat', (0, 39.0, 0.6), (6, 4, 6), hat, rotation=[-12, 0, 0], pivot=(0, 37.5, 0))
    g.box('hat', (0, 42.6, 2.0), (3.6, 4, 3.6), hat, rotation=[-25, 0, 0], pivot=(0, 41, 1))
    g.box('hat', (0, 45.4, 4.4), (1.8, 3, 1.8), hat, rotation=[-45, 0, 0], pivot=(0, 44.5, 3))
    g.cube('body', (-3.5, 14, -2), (7, 12, 4), dress)
    g.cube('body', (-3.7, 20.5, -2.2), (7.4, 1.2, 4.4), trim)
    for k, (wd, y0) in enumerate(((9, 9), (11, 4), (13, -1), (15, -5))):
        g.cube('skirt', (-wd / 2, y0, -wd / 2.6), (wd, 5.2, wd / 1.3), dress)
    g.cube('skirt', (-7.6, -5.2, -5.9), (15.2, 0.8, 11.8), trim)
    for side, x0 in (('rightArm', -8), ('leftArm', 4)):
        g.cube(side, (x0 + 0.3, 15, -1.7), (3.4, 9, 3.4), dress)
        g.cube(side, (x0 - 0.3, 14, -2.3), (4.6, 3, 4.6), dress)
        g.cube(side, (x0 + 0.5, 12.5, -1.5), (3, 2, 3), skin)
    g.cube('staff', (-6.6, 6, -0.6), (1.2, 28, 1.2), wood)
    g.box('staff', (-6, 35.5, 0), (3.2, 3.2, 3.2), w['orb'], rotation=[45, 45, 0], pivot=(-6, 35.5, 0))
    g.box('staff', (-6, 33.5, 0), (4.2, 0.6, 0.6), trim)
    return g


def witch_animations(kind):
    return {
        f'animation.bc.{kind}.float': {'loop': True, 'bones': {
            'root': {'position': [0, '3.0 + math.sin(q.life_time * 110.0) * 1.2', 0]},
            'skirt': {'rotation': ['math.sin(q.life_time * 130.0) * 4.0', 0, 'math.cos(q.life_time * 100.0) * 3.0']},
            'leftArm': {'rotation': ['-15.0 + math.sin(q.life_time * 90.0) * 5.0', 0, -8]},
            'rightArm': {'rotation': ['-10.0', 0, 6]},
            'hat': {'rotation': ['math.sin(q.life_time * 70.0) * 2.0', 0, 0]},
        }},
        f'animation.bc.{kind}.look_at_target': {'loop': True, 'bones': {'head': {'rotation': ['q.target_x_rotation', 'q.target_y_rotation', 0]}}},
        f'animation.bc.{kind}.cast': {'animation_length': 0.9, 'bones': {
            'rightArm': {'rotation': {'0.0': [-10, 0, 6], '0.25': [-160, 0, 10], '0.7': [-150, 0, 8], '0.9': [-10, 0, 6]}},
            'leftArm': {'rotation': {'0.0': [-15, 0, -8], '0.25': [-100, -20, -10], '0.9': [-15, 0, -8]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.25': [-15, 0, 0], '0.9': [0, 0, 0]}},
        }},
        f'animation.bc.{kind}.sweep': {'animation_length': 0.7, 'bones': {
            'rightArm': {'rotation': {'0.0': [-10, 0, 6], '0.2': [-90, 70, 0], '0.45': [-90, -60, 0], '0.7': [-10, 0, 6]}},
            'body': {'rotation': {'0.0': [0, 0, 0], '0.2': [0, 25, 0], '0.45': [0, -25, 0], '0.7': [0, 0, 0]}},
        }},
        f'animation.bc.{kind}.roar': {'animation_length': 1.4, 'bones': {
            'rightArm': {'rotation': {'0.0': [-10, 0, 6], '0.3': [-30, 0, 70], '1.1': [-30, 0, 70], '1.4': [-10, 0, 6]}},
            'leftArm': {'rotation': {'0.0': [-15, 0, -8], '0.3': [-30, 0, -70], '1.1': [-30, 0, -70], '1.4': [-15, 0, -8]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.3': [-35, 0, 0], '1.1': [-35, 0, 0], '1.4': [0, 0, 0]}},
        }},
    }


# ======================================================================================
# the Bone Dragon
# ======================================================================================
def _bone_cracks(a, ctx):
    h, w = a.shape[:2]
    rng = np.random.default_rng(ctx.seed)
    for _ in range(max(1, (h * w) // 50)):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        a[y, x, :3] = (a[y, x, :3] * 0.55).astype(a.dtype)
    return a


def _membrane(a, ctx):
    h, w = a.shape[:2]
    rng = np.random.default_rng(ctx.seed)
    for _ in range(max(1, (h * w) // 30)):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        a[y, x, 3] = 0
    for x in range(w):
        cut = int(rng.integers(0, max(1, h // 4)))
        if cut:
            a[h - cut:, x, 3] = 0
    return a


def bone_dragon_geo():
    g = Geo('geometry.bc.bone_dragon', res=2, atlas_width=256, visible=(8, 6, (0, 2, 0)))
    bone = tex.Painted(tex.Material(P['bone'], noise=0.12, edge=0.7), {'*': _bone_cracks})
    dark = tex.Material(tex.ramp('1a1612', '2a241e', '3a322a', '4a4036'), noise=0.15)
    membrane = tex.Painted(tex.Material(tex.ramp('12081a', '1e0e2c', '2c1640', '3c2056'), noise=0.2, edge=0, highlight=False), {'*': _membrane})
    glow = tex.Energy(tex.ramp('1a4a0a', '3a8a1a', '7ae04a', 'c8ff9a', 'f4ffe8'), alpha=130)

    def sockets(a, ctx):
        h, w = a.shape[:2]
        for ex in (int(w * 0.12), int(w * 0.62)):
            a[int(h * 0.25):int(h * 0.25) + 3, ex:ex + max(2, int(w * 0.26)), :3] = rgb('7ae04a')[:3]
            a[int(h * 0.25):int(h * 0.25) + 3, ex:ex + max(2, int(w * 0.26)), 3] = 130
        return a
    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 16, 0))
    g.bone('neck0', 'body', (0, 20, -9))
    g.bone('neck1', 'neck0', (0, 22, -15))
    g.bone('head', 'neck1', (0, 24, -21))
    g.bone('jaw', 'head', (0, 22.5, -23))
    for side, sx in (('right', -1), ('left', 1)):
        g.bone(f'{side}Wing', 'body', (sx * 5, 22, -2))
        g.bone(f'{side}WingTip', f'{side}Wing', (sx * 21, 22, -2))
        g.bone(f'{side}Leg', 'body', (sx * 4, 12, 4))
    prev = 'body'
    for k in range(4):
        g.bone(f'tail{k}', prev, (0, 16 - k * 0.5, 9 + k * 7))
        prev = f'tail{k}'
    # ribcage body: spine + ribs
    g.cube('body', (-1.5, 18, -9), (3, 3, 20), bone)
    for k in range(6):
        z = -7 + k * 3
        for sx in (-1, 1):
            g.box('body', (sx * 4.2, 15, z), (1.2, 7, 1.2), bone, rotation=[0, 0, sx * 25], pivot=(sx * 1.5, 19, z))
            g.box('body', (sx * 5.2, 10.5, z), (1.0, 4, 1.0), bone, rotation=[0, 0, sx * -15], pivot=(sx * 5, 12.5, z))
    g.box('body', (0, 14, 1), (5, 5, 5), glow, rotation=[45, 45, 0], pivot=(0, 14, 1))         # the soul core
    g.cube('body', (-4, 13, 8), (8, 5, 5), bone)                                              # pelvis
    for k in range(5):
        g.box('body', (0, 22, -7 + k * 4), (1.0, 3, 1.4), dark, rotation=[-20, 0, 0], pivot=(0, 21, -7 + k * 4))
    # neck & skull
    g.cube('neck0', (-1.5, 19, -15), (3, 3, 7), bone, rotation=[15, 0, 0], pivot=(0, 20, -9))
    g.cube('neck1', (-1.4, 21, -21), (2.8, 2.8, 7), bone, rotation=[10, 0, 0], pivot=(0, 22, -15))
    g.cube('head', (-3.5, 22, -28), (7, 6, 8), tex.Painted(bone, {'north': sockets, 'east': sockets, 'west': sockets}))
    g.cube('head', (-2.5, 22.5, -33), (5, 3, 5), bone)                                        # snout
    for k in range(4):
        g.box('head', (-1.8 + k * 1.2, 21.6, -32.5 + (k % 2)), (0.5, 1.2, 0.5), tex.Flat('f0eadc'))
    g.cube('jaw', (-2.3, 20.4, -32.5), (4.6, 1.6, 9.5), bone)
    for sx in (-1, 1):
        g.box('head', (sx * 3, 29.5, -23), (1.4, 6, 1.4), dark, rotation=[-50, 0, sx * -20], pivot=(sx * 3, 27.5, -24))
        g.box('head', (sx * 4.5, 27, -25), (1.0, 3.4, 1.0), dark, rotation=[-30, 0, sx * -45], pivot=(sx * 4, 26, -25))
    # wings: bone struts with tattered membranes
    for side, sx in (('right', -1), ('left', 1)):
        x0 = -21 if sx < 0 else 5
        g.cube(f'{side}Wing', (x0, 21, -3), (16, 2, 2), bone)
        g.cube(f'{side}Wing', (x0, 6, -1.8), (16, 15, 0), membrane)
        tx0 = -37 if sx < 0 else 21
        g.cube(f'{side}WingTip', (tx0, 21.3, -2.7), (16, 1.5, 1.5), bone)
        g.cube(f'{side}WingTip', (tx0, 9, -1.6), (16, 12, 0), membrane)
        for k in range(3):
            fx = sx * (24 + k * 5)
            g.box(f'{side}WingTip', (fx, 15, -1.9), (0.8, 12, 0.8), bone, rotation=[0, 0, sx * (15 + k * 10)], pivot=(fx, 21, -1.9))
        g.box(f'{side}WingTip', (sx * 37.5, 23, -2), (1.2, 4, 1.2), dark, rotation=[0, 0, sx * 30], pivot=(sx * 37, 21.5, -2))
        lx = sx * 4
        g.cube(f'{side}Leg', (lx - 1, 4, 3), (2, 8, 2), bone, rotation=[15, 0, 0], pivot=(lx, 12, 4))
        g.cube(f'{side}Leg', (lx - 1.5, 0, 0.5), (3, 1.5, 4), bone)
    for k in range(4):
        s = 2.6 - k * 0.5
        g.cube(f'tail{k}', (-s / 2, 15.5 - k * 0.5 - s / 2, 9 + k * 7), (s, s, 7.2), bone)
    g.box('tail3', (0, 14, 37), (3.6, 0.8, 4.4), dark, rotation=[0, 45, 0], pivot=(0, 14, 37))
    return g


def bone_dragon_animations():
    flap = 'math.sin(q.life_time * 160.0)'
    bones = {
        'root': {'position': [0, '4.0 + math.sin(q.life_time * 80.0) * 2.0', 0]},
        'rightWing': {'rotation': [0, f'-10.0 + {flap} * 15.0', f'10.0 + {flap} * 25.0']},
        'leftWing': {'rotation': [0, f'10.0 - {flap} * 15.0', f'-10.0 - {flap} * 25.0']},
        'rightWingTip': {'rotation': [0, 0, f'{flap} * 20.0']},
        'leftWingTip': {'rotation': [0, 0, f'-{flap} * 20.0']},
        'neck0': {'rotation': ['math.sin(q.life_time * 90.0) * 4.0', 'math.sin(q.life_time * 60.0) * 6.0', 0]},
        'jaw': {'rotation': ['math.max(0.0, math.sin(q.life_time * 50.0)) * 8.0', 0, 0]},
        'rightLeg': {'rotation': ['20.0', 0, 0]}, 'leftLeg': {'rotation': ['20.0', 0, 0]},
    }
    for k in range(4):
        bones[f'tail{k}'] = {'rotation': [f'math.sin(q.life_time * 100.0 - {k * 40}) * 6.0', f'math.sin(q.life_time * 80.0 - {k * 50}) * 12.0', 0]}
    return {
        'animation.bc.bone_dragon.fly': {'loop': True, 'bones': bones},
        'animation.bc.bone_dragon.look_at_target': {'loop': True, 'bones': {'head': {'rotation': ['q.target_x_rotation * 0.6', 'q.target_y_rotation * 0.6', 0]}}},
        'animation.bc.bone_dragon.breath': {'animation_length': 1.4, 'bones': {
            'neck0': {'rotation': {'0.0': [0, 0, 0], '0.3': [-20, 0, 0], '0.5': [15, 0, 0], '1.2': [15, 0, 0], '1.4': [0, 0, 0]}},
            'jaw': {'rotation': {'0.0': [0, 0, 0], '0.4': [40, 0, 0], '1.2': [40, 0, 0], '1.4': [0, 0, 0]}},
        }},
        'animation.bc.bone_dragon.roar': {'animation_length': 1.6, 'bones': {
            'neck0': {'rotation': {'0.0': [0, 0, 0], '0.4': [-35, 0, 0], '1.2': [-35, 0, 0], '1.6': [0, 0, 0]}},
            'jaw': {'rotation': {'0.0': [0, 0, 0], '0.4': [45, 0, 0], '1.2': [45, 0, 0], '1.6': [0, 0, 0]}},
            'rightWing': {'rotation': {'0.0': [0, 0, 0], '0.4': [0, -40, 50], '1.2': [0, -40, 50], '1.6': [0, 0, 0]}},
            'leftWing': {'rotation': {'0.0': [0, 0, 0], '0.4': [0, 40, -50], '1.2': [0, 40, -50], '1.6': [0, 0, 0]}},
        }},
        'animation.bc.bone_dragon.dive': {'animation_length': 1.2, 'bones': {
            'body': {'rotation': {'0.0': [0, 0, 0], '0.3': [25, 0, 0], '0.9': [25, 0, 0], '1.2': [0, 0, 0]}},
            'rightWing': {'rotation': {'0.0': [0, 0, 0], '0.3': [0, 50, 10], '0.9': [0, 50, 10], '1.2': [0, 0, 0]}},
            'leftWing': {'rotation': {'0.0': [0, 0, 0], '0.3': [0, -50, -10], '0.9': [0, -50, -10], '1.2': [0, 0, 0]}},
        }},
        'animation.bc.bone_dragon.tail': {'animation_length': 0.8, 'bones': {
            'tail0': {'rotation': {'0.0': [0, 0, 0], '0.3': [0, 60, 0], '0.55': [0, -60, 0], '0.8': [0, 0, 0]}},
            'tail1': {'rotation': {'0.0': [0, 0, 0], '0.3': [0, 30, 0], '0.55': [0, -30, 0], '0.8': [0, 0, 0]}},
        }},
    }


# ======================================================================================
# icons (32 x 32)
# ======================================================================================
def _icon(fn, outline='0a0a0f'):
    a = tex.draw_layer(32, 32, fn, 4)
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    tex.outline(a, rgb(outline))
    return a


def v3_icons():
    def broom(swift):
        def fn(d, s):
            d.line([(4 * s, 28 * s), (22 * s, 10 * s)], fill=(60, 40, 30, 255) if not swift else (40, 60, 80, 255), width=int(2.2 * s))
            col = (210, 170, 70, 255) if not swift else (140, 190, 220, 255)
            d.polygon([(20 * s, 8 * s), (30 * s, 2 * s), (31 * s, 6 * s), (24 * s, 14 * s)], fill=col)
            d.polygon([(22 * s, 8 * s), (29 * s, 1 * s), (31 * s, 1 * s), (31 * s, 8 * s), (24 * s, 12 * s)], fill=col)
            d.rectangle([19 * s, 10 * s, 23 * s, 13 * s], fill=(240, 200, 80, 255) if not swift else (220, 230, 240, 255))
            d.ellipse([2 * s, 26 * s, 6 * s, 30 * s], fill=(200, 80, 200, 255) if not swift else (80, 170, 255, 255))
        return fn

    def amulet(color, sym):
        def fn(d, s):
            d.arc([6 * s, 1 * s, 26 * s, 18 * s], 200, 340, fill=(200, 170, 80, 255), width=int(1.2 * s))
            d.ellipse([8 * s, 10 * s, 24 * s, 28 * s], fill=(180, 140, 50, 255))
            d.ellipse([10.5 * s, 12.5 * s, 21.5 * s, 25.5 * s], fill=color)
            if sym == 'heart':
                d.polygon([(16 * s, 23 * s), (12 * s, 18 * s), (14 * s, 15 * s), (16 * s, 17 * s), (18 * s, 15 * s), (20 * s, 18 * s)], fill=(255, 255, 255, 255))
            elif sym == 'bolt':
                d.polygon([(17 * s, 14 * s), (13 * s, 20 * s), (16 * s, 20 * s), (15 * s, 24 * s), (19 * s, 18 * s), (16 * s, 18 * s)], fill=(255, 255, 255, 255))
            elif sym == 'sword':
                d.line([(16 * s, 14 * s), (16 * s, 23 * s)], fill=(255, 255, 255, 255), width=int(1.4 * s))
                d.line([(13.5 * s, 20 * s), (18.5 * s, 20 * s)], fill=(255, 255, 255, 255), width=int(1.2 * s))
            elif sym == 'shield':
                d.polygon([(12.5 * s, 15 * s), (19.5 * s, 15 * s), (19 * s, 21 * s), (16 * s, 24 * s), (13 * s, 21 * s)], fill=(255, 255, 255, 255))
            else:
                d.ellipse([13 * s, 15.5 * s, 19 * s, 21.5 * s], outline=(255, 255, 255, 255), width=int(1.2 * s))
        return fn

    def charm(d, s):
        d.ellipse([3 * s, 3 * s, 29 * s, 29 * s], fill=(30, 20, 40, 255), outline=(200, 200, 220, 255), width=int(1.5 * s))
        d.pieslice([7 * s, 7 * s, 25 * s, 25 * s], 90, 270, fill=(120, 210, 255, 255))
        d.pieslice([7 * s, 7 * s, 25 * s, 25 * s], 270, 450, fill=(255, 120, 50, 255))
        d.ellipse([13 * s, 13 * s, 19 * s, 19 * s], fill=(30, 20, 40, 255))

    def totem(d, s):
        d.rectangle([12 * s, 8 * s, 20 * s, 30 * s], fill=(220, 210, 190, 255))
        d.ellipse([8 * s, 2 * s, 24 * s, 14 * s], fill=(230, 222, 200, 255))
        d.ellipse([11 * s, 6 * s, 15 * s, 10 * s], fill=(120, 230, 80, 255))
        d.ellipse([17 * s, 6 * s, 21 * s, 10 * s], fill=(120, 230, 80, 255))
        for y in (16, 21, 26):
            d.line([(12 * s, y * s), (20 * s, y * s)], fill=(140, 130, 110, 255), width=int(1.2 * s))
    return {
        'broom': _icon(broom(False)), 'swift_broom': _icon(broom(True)),
        'amulet_mana': _icon(amulet((60, 150, 255, 255), 'heart')), 'amulet_swift': _icon(amulet((70, 200, 90, 255), 'bolt')),
        'amulet_power': _icon(amulet((220, 50, 50, 255), 'sword')), 'amulet_guard': _icon(amulet((240, 200, 60, 255), 'shield')),
        'amulet_vigor': _icon(amulet((220, 90, 200, 255), 'ring')),
        'twin_moon_charm': _icon(charm), 'bone_totem': _icon(totem),
    }
