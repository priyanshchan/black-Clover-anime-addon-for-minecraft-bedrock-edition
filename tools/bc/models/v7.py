"""v0.7.0 models and animations: the Bandit Brotherhood (brawler, archer, thief, the Bandit King), the Shadow Assassin,
the Cultist, the Hive (drones, eggs, the Hive Queen) and the Grimoire Devourer. All designs are original."""
from __future__ import annotations

import math

import numpy as np

from .. import tex
from ..geo import Geo
from ..tex import P, rgb
from .sea import SKIN, _face, _humanoid_bones, humanoid_animations

LEATHER = tex.ramp('2a1a0e', '3c2614', '52341c', '684426', '7e5632')
BANDIT_CLOTH = {'brawler': tex.ramp('3a0e08', '541610', '6e2016', '8a2c1e', 'a63a28'),
                'archer': tex.ramp('1a2a10', '243a16', '304c1e', '3e6026', '4e7430'),
                'thief': tex.ramp('1a1a20', '24242c', '30303a', '3e3e4a', '4e4e5c')}


def _blade(g, bone, x, y, z, length=9, curve=False, gold=False):
    steel = tex.Metal(P['steel'] if not gold else P['gold'], sheen=0.5)
    grip = tex.Material(P['leather'], noise=0.1)
    g.cube(bone, (x - 0.5, y - 2.5, z - 0.5), (1, 2.5, 1), grip)
    g.cube(bone, (x - 1.4, y - 0.1, z - 0.6), (2.8, 0.6, 1.2), tex.Metal(P['gold']))
    if curve:
        g.box(bone, (x, y + length / 2, z - 0.4), (0.5, length, 1.6), steel, rotation=[8, 0, 0], pivot=(x, y, z))
    else:
        g.cube(bone, (x - 0.25, y + 0.4, z - 0.6), (0.5, length, 1.2), steel)


def _arms(g, cloth, skin, wraps=None):
    for side, x0 in (('rightArm', -8), ('leftArm', 4)):
        g.cube(side, (x0, 14, -2), (4, 10, 4), cloth)
        g.cube(side, (x0 - 0.1, 12, -2.1), (4.2, 3, 4.2), wraps or skin)


# ======================================================================================
# the Bandit Brotherhood
# ======================================================================================
def bandit_geo(kind):
    g = Geo(f'geometry.bc.bandit_{kind}' if kind != 'brawler' else 'geometry.bc.bandit', res=2, atlas_width=128, visible=(2, 3, (0, 1.2, 0)), seed=81)
    _humanoid_bones(g)
    skin = tex.Material(SKIN, noise=0.08, edge=0.85)
    cloth = tex.Cloth(BANDIT_CLOTH[kind], folds=0.18)
    leather = tex.Material(LEATHER, noise=0.14)
    boots = tex.Material(tex.ramp('120c08', '1e1510', '2a1e16'), noise=0.1)
    mask = tex.Cloth(BANDIT_CLOTH[kind])

    def masked(a, ctx):
        _face(scar=kind == 'brawler')(a, ctx)
        h = a.shape[0]
        a[int(h * 0.6):, :, :3] = np.array(rgb('541610' if kind == 'brawler' else '243a16' if kind == 'archer' else '24242c')[:3])
        return a
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(skin, {'north': masked}))
    if kind == 'thief':
        g.cube('head', (-4.5, 25.5, -4.5), (9, 7.2, 9), tex.PerFace(cloth, north=tex.Painted(cloth, {'north': lambda a, c: (a.__setitem__((slice(a.shape[0] // 4, None), slice(a.shape[1] // 6, a.shape[1] - a.shape[1] // 6), 3), 0), a)[1]})))
    else:
        g.cube('head', (-4.3, 30.2, -4.3), (8.6, 2.4, 8.6), mask)      # bandana
        g.box('head', (0, 31.4, 4.8), (1.6, 1.6, 2.4), mask, rotation=[30, 0, 0], pivot=(0, 31.4, 4.2))
    g.cube('body', (-4, 12, -2), (8, 12, 4), cloth)
    g.cube('body', (-4.4, 15, -2.4), (8.8, 9, 4.8), leather)                    # vest
    g.cube('body', (-4.6, 12.4, -2.6), (9.2, 1.6, 5.2), tex.Material(P['leather'], noise=0.1))
    g.box('body', (0, 13.2, -2.8), (1.6, 1.4, 0.6), tex.Metal(P['gold']))
    _arms(g, cloth, skin, wraps=tex.Cloth(P['white_cloth']) if kind == 'brawler' else None)
    for side, x0 in (('rightLeg', -3.9), ('leftLeg', -0.1)):
        g.cube(side, (x0, 3, -2), (4, 9, 4), tex.Cloth(tex.ramp('1a1610', '262018', '332a20', '40362a')))
        g.cube(side, (x0 - 0.2, 0, -2.3), (4.4, 4.5, 4.6), boots)
    if kind == 'brawler':
        # a heavy cleaver
        g.cube('rightArm', (-6.5, 9.0, -0.6), (1.2, 4, 1.2), tex.Material(P['leather']))
        g.cube('rightArm', (-7.0, 13.0, -3.6), (2.0, 1.2, 7.5), tex.Metal(P['steel'], sheen=0.5))
        g.cube('rightArm', (-6.6, 12.6, -3.6), (1.2, 2.4, 3.0), tex.Metal(P['steel'], sheen=0.5))
    elif kind == 'archer':
        bow = tex.Wood(tex.ramp('3a2412', '54341c', '6e4626'))
        g.box('leftArm', (6, 11, -1.5), (1, 12, 1), bow, rotation=[0, 0, 0], pivot=(6, 11, -1.5))
        g.box('leftArm', (6, 17.5, -2.6), (1, 4, 1), bow, rotation=[-30, 0, 0], pivot=(6, 16, -1.5))
        g.box('leftArm', (6, 4.5, -2.6), (1, 4, 1), bow, rotation=[30, 0, 0], pivot=(6, 6, -1.5))
        g.cube('leftArm', (5.9, 3.5, -0.3), (0.2, 15, 0.2), tex.Flat('e0dccc'))
        g.box('body', (2.5, 20, 3.0), (3, 9, 3), leather, rotation=[0, 0, 20], pivot=(2.5, 20, 3))       # quiver
        for k in range(3):
            g.cube('body', (1.6 + k * 0.8, 24.5, 2.4), (0.4, 2.5, 0.4), tex.Flat('d0c8a0'))
    else:
        for side, x in (('rightArm', -6), ('leftArm', 6)):
            _blade(g, side, x, 11.5, -1.5, length=5)
        g.box('body', (-3.5, 11, 2.8), (4, 4, 3), tex.Cloth(tex.ramp('6a5432', '8a6e44', 'a68858')), rotation=[0, 0, 15], pivot=(-3.5, 11, 2.8))  # loot sack
    return g


def bandit_animations(prefix):
    anims = humanoid_animations(prefix)
    anims[f'animation.bc.{prefix}.cast'] = {'animation_length': 0.6, 'bones': {
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.15': [-160, 0, 10], '0.3': [-40, 0, 0], '0.6': [0, 0, 0]}},
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.15': [-90, 0, -10], '0.6': [0, 0, 0]}},
        'body': {'rotation': {'0.0': [0, 0, 0], '0.15': [0, 20, 0], '0.3': [0, -20, 0], '0.6': [0, 0, 0]}},
    }}
    anims[f'animation.bc.{prefix}.shoot'] = {'animation_length': 0.7, 'bones': {
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.15': [-90, 10, 0], '0.55': [-90, 10, 0], '0.7': [0, 0, 0]}},
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.15': [-90, -30, 0], '0.45': [-80, -40, 0], '0.5': [-90, -10, 0], '0.7': [0, 0, 0]}},
    }}
    anims[f'animation.bc.{prefix}.taunt'] = {'animation_length': 1.0, 'bones': {
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-170, 0, 10], '0.8': [-170, 0, 10], '1.0': [0, 0, 0]}},
        'body': {'rotation': {'0.0': [0, 0, 0], '0.2': [-10, 0, 0], '1.0': [0, 0, 0]}},
    }}
    return anims


def bandit_king_geo():
    g = Geo('geometry.bc.bandit_king', res=2, atlas_width=128, visible=(3, 4, (0, 1.6, 0)), seed=83)
    _humanoid_bones(g)
    g.bone('cape', 'body', (0, 24, 2.6))
    skin = tex.Material(SKIN, noise=0.08, edge=0.85)
    coat = tex.Cloth(tex.ramp('2a0806', '44100a', '601810', '7e2418', 'a03420'), folds=0.2)
    fur = tex.Material(tex.ramp('3a2e22', '544434', '6e5c48', '8a7660', 'a6927a'), noise=0.45)
    gold = tex.Metal(P['gold'])
    leather = tex.Material(LEATHER, noise=0.14)

    def face(a, ctx):
        _face(beard=True, scar=True, eyepatch=True)(a, ctx)
        return a
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(skin, {'north': face}))
    g.cube('head', (-4.4, 31.0, -4.4), (8.8, 1.4, 8.8), gold)                     # the crown band
    for k in range(5):
        x = -3.6 + k * 1.8
        g.cube('head', (x, 32.2, -4.4), (1.2, 2.2 if k % 2 == 0 else 1.4, 1.0), gold)
    g.box('head', (0, 33.0, -4.6), (1.2, 1.2, 0.6), tex.Energy(P['flame'][1:], alpha=150))
    g.cube('body', (-4.5, 12, -2.5), (9, 12, 5), coat)
    g.cube('body', (-5.5, 21, -3.5), (11, 3.5, 7), fur)                             # fur mantle
    g.cube('body', (-4.8, 12.4, -2.8), (9.6, 2, 5.6), leather)
    g.box('body', (0, 13.4, -3.0), (2.4, 2.0, 0.6), gold)
    g.cube('cape', (-5.5, 2.0, 2.6), (11, 22, 0.9), tex.Cloth(tex.ramp('1a0404', '2e0808', '440c0c', '5c1212'), folds=0.25))
    for side, x0 in (('rightArm', -9), ('leftArm', 5)):
        g.cube(side, (x0, 13, -2), (4, 11, 4), coat)
        g.cube(side, (x0 - 0.4, 20, -2.4), (4.8, 4.4, 4.8), fur)
        g.cube(side, (x0 - 0.1, 11.5, -2.1), (4.2, 3, 4.2), leather)
    for side, x in (('rightArm', -7), ('leftArm', 7)):
        _blade(g, side, x, 11.0, -1.5, length=11, curve=True, gold=side == 'leftArm')
    for side, x0 in (('rightLeg', -4.1), ('leftLeg', 0.1)):
        g.cube(side, (x0, 3, -2), (4, 9, 4), tex.Cloth(tex.ramp('1a1610', '262018', '332a20', '40362a')))
        g.cube(side, (x0 - 0.2, 0, -2.3), (4.4, 5.5, 4.6), tex.Material(tex.ramp('120c08', '1e1510', '2a1e16'), noise=0.1))
    return g


def bandit_king_animations():
    k = 'bandit_king'
    anims = humanoid_animations(k)
    anims[f'animation.bc.{k}.idle']['bones']['cape'] = {'rotation': ['6.0 + math.sin(q.life_time * 100.0) * 3.0', 0, 0]}
    anims[f'animation.bc.{k}.walk']['bones']['cape'] = {'rotation': ['10.0 + math.abs(math.cos(q.modified_distance_moved * 38.17)) * 30.0 * q.modified_move_speed', 0, 0]}
    anims[f'animation.bc.{k}.whirl'] = {'animation_length': 1.0, 'bones': {
        'body': {'rotation': {'0.0': [0, 0, 0], '0.25': [0, 180, 0], '0.5': [0, 360, 0], '0.75': [0, 540, 0], '1.0': [0, 720, 0]}},
        'rightArm': {'rotation': [-20, 0, 85]}, 'leftArm': {'rotation': [-20, 0, -85]},
    }}
    anims[f'animation.bc.{k}.slash'] = {'animation_length': 0.5, 'bones': {
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.15': [-170, 30, 0], '0.3': [-30, -40, 0], '0.5': [0, 0, 0]}},
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-60, 0, -40], '0.35': [-120, 40, 0], '0.5': [0, 0, 0]}},
        'body': {'rotation': {'0.0': [0, 0, 0], '0.15': [0, 25, 0], '0.3': [10, -25, 0], '0.5': [0, 0, 0]}},
    }}
    anims[f'animation.bc.{k}.command'] = {'animation_length': 1.2, 'bones': {
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.25': [-150, 0, 20], '0.9': [-150, 0, 20], '1.2': [0, 0, 0]}},
        'head': {'rotation': {'0.0': [0, 0, 0], '0.25': [-20, 0, 0], '1.2': [0, 0, 0]}},
    }}
    anims[f'animation.bc.{k}.roar'] = {'animation_length': 1.4, 'bones': {
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.3': [-40, 0, 80], '1.1': [-40, 0, 80], '1.4': [0, 0, 0]}},
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.3': [-40, 0, -80], '1.1': [-40, 0, -80], '1.4': [0, 0, 0]}},
        'head': {'rotation': {'0.0': [0, 0, 0], '0.3': [-30, 0, 0], '1.4': [0, 0, 0]}},
        'cape': {'rotation': {'0.0': [6, 0, 0], '0.3': [50, 0, 0], '1.4': [6, 0, 0]}},
    }}
    return anims


# ======================================================================================
# the Shadow Assassin and the Cultist
# ======================================================================================
def assassin_geo():
    g = Geo('geometry.bc.shadow_assassin', res=2, atlas_width=128, visible=(2, 3, (0, 1.2, 0)), seed=85)
    _humanoid_bones(g)
    g.bone('scarf', 'head', (0, 25, 3.5))
    cloth = tex.Cloth(tex.ramp('08060c', '100c16', '1a1422', '261e30', '342840'), folds=0.2)
    wrap = tex.Material(tex.ramp('0c0a10', '16121c', '201a28'), noise=0.12)
    eye = tex.Energy(tex.ramp('3a0a5a', '7a2ab0', 'c070ff', 'f0d0ff'), alpha=170)

    def hood(a, ctx):
        h, w = a.shape[:2]
        a[..., :3] = np.array(rgb('08060c')[:3])
        for ex in (int(w * 0.22), int(w * 0.62)):
            a[int(h * 0.42):int(h * 0.42) + 2, ex:ex + max(2, int(w * 0.18)), :3] = np.array(rgb('c070ff')[:3])
        return a
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(cloth, {'north': hood}))
    g.cube('head', (-4.6, 25.5, -4.6), (9.2, 7.4, 9.2), tex.PerFace(cloth, north=tex.Painted(cloth, {'north': lambda a, c: (a.__setitem__((slice(a.shape[0] // 5, None), slice(a.shape[1] // 6, a.shape[1] - a.shape[1] // 6), 3), 0), a)[1]})))
    g.box('head', (0, 33.0, 2.0), (4, 2.5, 5), cloth, rotation=[-25, 0, 0], pivot=(0, 32, 0))
    g.cube('scarf', (-1.5, 14, 3.4), (3, 11, 0.6), tex.Cloth(tex.ramp('3a0a1e', '5a1030', '7a1844')))
    g.cube('body', (-3.5, 12, -2), (7, 12, 4), cloth)
    g.cube('body', (-3.8, 12.4, -2.3), (7.6, 1.4, 4.6), wrap)
    for side, x0 in (('rightArm', -7), ('leftArm', 3.5)):
        g.cube(side, (x0, 13, -1.75), (3.5, 11, 3.5), cloth)
        g.cube(side, (x0 - 0.1, 12, -1.85), (3.7, 4, 3.7), wrap)
    for side, x in (('rightArm', -5.25), ('leftArm', 5.25)):
        _blade(g, side, x, 11.5, -1.0, length=6)
    for side, x0 in (('rightLeg', -3.6), ('leftLeg', -0.0)):
        g.cube(side, (x0, 0, -1.8), (3.6, 12, 3.6), cloth)
        g.cube(side, (x0 - 0.1, 0, -1.9), (3.8, 4, 3.8), wrap)
    g.box('head', (0, 28.5, -4.3), (0.1, 0.1, 0.1), eye)
    return g


def assassin_animations():
    k = 'shadow_assassin'
    anims = humanoid_animations(k)
    anims[f'animation.bc.{k}.idle']['bones']['scarf'] = {'rotation': ['15.0 + math.sin(q.life_time * 160.0) * 8.0', 0, 0]}
    anims[f'animation.bc.{k}.walk']['bones']['body'] = {'rotation': [12, 0, 0]}
    anims[f'animation.bc.{k}.walk']['bones']['scarf'] = {'rotation': ['35.0 + math.sin(q.life_time * 400.0) * 10.0', 0, 0]}
    anims[f'animation.bc.{k}.cast'] = {'animation_length': 0.5, 'bones': {
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.1': [-100, 30, 0], '0.25': [-90, -60, 0], '0.5': [0, 0, 0]}},
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.15': [-100, -30, 0], '0.3': [-90, 60, 0], '0.5': [0, 0, 0]}},
    }}
    anims[f'animation.bc.{k}.backstab'] = {'animation_length': 0.45, 'bones': {
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.1': [-200, 0, 0], '0.2': [-60, 0, 0], '0.45': [0, 0, 0]}},
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.1': [-200, 0, 0], '0.2': [-60, 0, 0], '0.45': [0, 0, 0]}},
        'body': {'rotation': {'0.0': [0, 0, 0], '0.1': [-15, 0, 0], '0.2': [25, 0, 0], '0.45': [0, 0, 0]}},
    }}
    return anims


def cultist_geo():
    g = Geo('geometry.bc.cultist', res=2, atlas_width=128, visible=(2, 3, (0, 1.3, 0)), seed=87)
    _humanoid_bones(g)
    robe = tex.Cloth(tex.ramp('1e0408', '30080e', '440c14', '5a121c', '701a26'), folds=0.25)
    trim = tex.Metal(tex.ramp('3a2a10', '6a5020', 'a88030', 'e0b850'))
    bone = tex.Material(P['bone'], noise=0.15)
    wood = tex.Wood(tex.ramp('1e130b', '2c1c10', '3b2716'))

    def mask(a, ctx):
        h, w = a.shape[:2]
        a[..., :3] = np.array(rgb('d8cfb8')[:3])
        for ex in (int(w * 0.18), int(w * 0.6)):
            a[int(h * 0.36):int(h * 0.36) + 3, ex:ex + max(2, int(w * 0.22)), :3] = np.array(rgb('1a0408')[:3])
        a[int(h * 0.7):int(h * 0.7) + 1, int(w * 0.3):int(w * 0.7), :3] = np.array(rgb('6a1020')[:3])
        return a
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(bone, {'north': mask}))
    g.cube('head', (-4.6, 26, -4.6), (9.2, 6.8, 9.2), tex.PerFace(robe, north=tex.Painted(robe, {'north': lambda a, c: (a.__setitem__((slice(a.shape[0] // 4, None), slice(a.shape[1] // 6, a.shape[1] - a.shape[1] // 6), 3), 0), a)[1]})))
    for sx in (-1, 1):   # horns
        g.box('head', (sx * 4.5, 33.5, -1), (1.4, 4, 1.4), bone, rotation=[0, 0, sx * -25], pivot=(sx * 3.8, 31.5, -1))
        g.box('head', (sx * 5.8, 36.2, -1), (1.0, 2.6, 1.0), bone, rotation=[0, 0, sx * -50], pivot=(sx * 5.2, 35, -1))
    g.cube('body', (-4.5, 0, -2.5), (9, 24, 5), robe)
    g.cube('body', (-4.7, 12.4, -2.7), (9.4, 1.4, 5.4), trim)
    g.cube('body', (-0.7, 2, -2.8), (1.4, 20, 0.4), trim)
    for side, x0 in (('rightArm', -8.5), ('leftArm', 4.5)):
        g.cube(side, (x0, 13, -2), (4, 11, 4), robe)
        g.cube(side, (x0 - 0.4, 12, -2.4), (4.8, 3, 4.8), robe)
    g.cube('rightArm', (-7.1, -6, -0.6), (1.2, 30, 1.2), wood)
    g.cube('rightArm', (-8.1, 23.5, -1.6), (3.2, 3.2, 3.2), bone)
    g.box('rightArm', (-6.5, 26.5, -0.0), (1.6, 1.6, 1.6), tex.Energy(tex.ramp('3a0a0a', '8a1010', 'e02020', 'ff8a8a'), alpha=150), rotation=[45, 45, 0], pivot=(-6.5, 26.5, 0))
    for side in ('rightLeg', 'leftLeg'):
        g.cube(side, (-0.1 if side == 'leftLeg' else -3.9, 0, -2), (4, 12, 4), robe)
    return g


def cultist_animations():
    k = 'cultist'
    anims = humanoid_animations(k)
    anims[f'animation.bc.{k}.cast'] = {'animation_length': 0.8, 'bones': {
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.25': [-140, 0, 10], '0.6': [-130, 0, 10], '0.8': [0, 0, 0]}},
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.25': [-90, -20, -20], '0.8': [0, 0, 0]}},
        'head': {'rotation': {'0.0': [0, 0, 0], '0.25': [-15, 0, 0], '0.8': [0, 0, 0]}},
    }}
    anims[f'animation.bc.{k}.ritual'] = {'loop': True, 'bones': {
        'rightArm': {'rotation': ['-150.0 + math.sin(q.life_time * 200.0) * 10.0', 0, 15]},
        'leftArm': {'rotation': ['-150.0 + math.sin(q.life_time * 200.0 + 180.0) * 10.0', 0, -15]},
        'head': {'rotation': [-25, 'math.sin(q.life_time * 90.0) * 15.0', 0]},
        'body': {'rotation': ['math.sin(q.life_time * 150.0) * 4.0', 0, 0]},
    }}
    return anims


# ======================================================================================
# the Hive: drones, eggs and the Hive Queen
# ======================================================================================
CHITIN = tex.ramp('1a1206', '2e200a', '4a3410', '6a4c16', '8e681e')
STRIPES = tex.ramp('0a0806', '141008', '1e180c')
WING = tex.Crystal(tex.ramp('8ab0a0', 'b0d4c4', 'd8f0e4', 'ffffff'), alpha=120)
ACID = tex.Energy(tex.ramp('2a3a06', '4a6a0a', '7ab012', 'b8f040', 'eaffb0'), alpha=150)


def _striped(a, ctx):
    h, w = a.shape[:2]
    for y in range(0, h, 4):
        a[y:y + 2, :, :3] = a[y:y + 2, :, :3] * 0.35
    return a


def drone_geo():
    g = Geo('geometry.bc.hive_drone', res=2, atlas_width=64, visible=(2, 2, (0, 0.6, 0)), seed=89)
    shell = tex.Painted(tex.Material(CHITIN, noise=0.2, edge=0.8), {f: _striped for f in ('north', 'south', 'east', 'west', 'up', 'down')})
    plain = tex.Material(CHITIN, noise=0.2, edge=0.8)
    leg = tex.Material(STRIPES, noise=0.1)
    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 6, 0))
    g.bone('head', 'body', (0, 7, -4))
    g.bone('abdomen', 'body', (0, 7, 3))
    g.bone('wingL', 'body', (1.5, 9, 0))
    g.bone('wingR', 'body', (-1.5, 9, 0))
    for i, z in enumerate((-2.2, 0, 2.2)):
        for side, sx in (('L', 1), ('R', -1)):
            g.bone(f'leg{side}{i}', 'body', (sx * 2.5, 5.5, z))
            g.box(f'leg{side}{i}', (sx * 4.5, 3.5, z), (4.5, 0.8, 0.8), leg, rotation=[0, 0, sx * -40], pivot=(sx * 2.5, 5.5, z))
    g.cube('body', (-2.5, 4.5, -3), (5, 4.5, 6), plain)
    g.cube('head', (-2, 5, -7.5), (4, 4, 4), plain)
    g.box('head', (-1.2, 8.0, -7.4), (1.0, 1.0, 1.0), ACID)
    g.box('head', (1.2, 8.0, -7.4), (1.0, 1.0, 1.0), ACID)
    for sx in (-1, 1):
        g.box('head', (sx * 1.2, 5.2, -8.6), (0.8, 0.8, 2.4), tex.Material(STRIPES), rotation=[0, sx * 20, 0], pivot=(sx * 1.2, 5.2, -7.5))
    g.box('abdomen', (0, 7, 7), (5.5, 5, 8), shell, rotation=[-12, 0, 0], pivot=(0, 7, 3))
    g.box('abdomen', (0, 5.6, 11.6), (1, 1, 2.4), tex.Material(STRIPES), rotation=[-30, 0, 0], pivot=(0, 6, 10.5))
    g.box('wingL', (5, 9.5, 1), (8, 0.2, 4), WING, rotation=[0, -15, 10], pivot=(1.5, 9, 0))
    g.box('wingR', (-5, 9.5, 1), (8, 0.2, 4), WING, rotation=[0, 15, -10], pivot=(-1.5, 9, 0))
    return g


def drone_animations():
    k = 'hive_drone'
    legs = {}
    for i in range(3):
        for side, ph in (('L', 0), ('R', 180)):
            legs[f'leg{side}{i}'] = {'rotation': [0, f'math.sin(q.anim_time * 1400.0 + {ph + i * 120}.0) * 25.0', f'math.cos(q.anim_time * 1400.0 + {ph + i * 120}.0) * 12.0']}
    return {
        f'animation.bc.{k}.idle': {'loop': True, 'bones': {
            'wingL': {'rotation': [0, 0, 'math.sin(q.life_time * 2400.0) * 25.0']},
            'wingR': {'rotation': [0, 0, '-math.sin(q.life_time * 2400.0) * 25.0']},
            'abdomen': {'rotation': ['math.sin(q.life_time * 200.0) * 5.0', 0, 0]},
            'head': {'rotation': [0, 'math.sin(q.life_time * 120.0) * 10.0', 0]},
        }},
        f'animation.bc.{k}.walk': {'loop': True, 'bones': legs},
        f'animation.bc.{k}.spit': {'animation_length': 0.5, 'bones': {
            'head': {'rotation': {'0.0': [0, 0, 0], '0.15': [-25, 0, 0], '0.3': [15, 0, 0], '0.5': [0, 0, 0]}},
            'abdomen': {'rotation': {'0.0': [0, 0, 0], '0.15': [20, 0, 0], '0.5': [0, 0, 0]}},
        }},
    }


def egg_geo():
    g = Geo('geometry.bc.hive_egg', res=2, atlas_width=64, visible=(2, 2, (0, 0.5, 0)), seed=91)
    shell = tex.Crystal(tex.ramp('6a7a2a', '8aa03a', 'aac44e', 'd0e47a', 'f0f8c0'), alpha=200)
    goo = tex.Energy(tex.ramp('2a3a06', '4a6a0a', '7ab012', 'b8f040'), alpha=140)
    g.bone('root', pivot=(0, 0, 0))
    g.bone('egg', 'root', (0, 0, 0))
    g.cube('root', (-5, 0, -5), (10, 1, 10), goo)
    g.cube('egg', (-3, 1, -3), (6, 8, 6), shell)
    g.cube('egg', (-2.4, 9, -2.4), (4.8, 2, 4.8), shell)
    g.box('egg', (0, 5, 0), (2.5, 3, 2.5), tex.Material(tex.ramp('1a1206', '2e200a', '4a3410')), name='embryo')
    for k, (x, z) in enumerate(((-4, 3), (3.5, -3.5), (4, 3.5))):
        g.cube('egg', (x - 1.2, 1, z - 1.2), (2.4, 3, 2.4), shell)
    return g


def egg_animations():
    return {'animation.bc.hive_egg.pulse': {'loop': True, 'bones': {
        'egg': {'scale': ['1.0 + math.sin(q.life_time * 240.0) * 0.06', '1.0 + math.sin(q.life_time * 240.0 + 90.0) * 0.08', '1.0 + math.sin(q.life_time * 240.0) * 0.06']},
    }}}


def queen_geo():
    g = Geo('geometry.bc.hive_queen', res=2, atlas_width=256, visible=(5, 4, (0, 1.6, 0)), seed=93)
    shell = tex.Painted(tex.Material(CHITIN, noise=0.2, edge=0.8), {f: _striped for f in ('north', 'south', 'east', 'west', 'up')})
    plain = tex.Material(CHITIN, noise=0.2, edge=0.8)
    dark = tex.Material(STRIPES, noise=0.1)
    crown = tex.Metal(tex.ramp('5a3a0a', '8a5a12', 'c08a20', 'f0c040', 'fff0a0'))
    g.bone('root', pivot=(0, 0, 0))
    g.bone('thorax', 'root', (0, 16, 0))
    g.bone('head', 'thorax', (0, 20, -10))
    g.bone('jawL', 'head', (2, 18, -16))
    g.bone('jawR', 'head', (-2, 18, -16))
    g.bone('abdomen', 'thorax', (0, 18, 9))
    g.bone('stinger', 'abdomen', (0, 14, 30))
    g.bone('wingL', 'thorax', (4, 26, 0))
    g.bone('wingR', 'thorax', (-4, 26, 0))
    for i, z in enumerate((-6, 0, 6)):
        for side, sx in (('L', 1), ('R', -1)):
            g.bone(f'leg{side}{i}', 'thorax', (sx * 7, 15, z))
            g.box(f'leg{side}{i}', (sx * 12, 12, z), (12, 2.2, 2.2), dark, rotation=[0, 0, sx * -30], pivot=(sx * 7, 15, z))
            g.box(f'leg{side}{i}', (sx * 18.5, 5, z), (2, 12, 2), dark, rotation=[0, 0, sx * 12], pivot=(sx * 17, 10, z))
    g.cube('thorax', (-7, 12, -9), (14, 12, 18), plain)
    g.cube('head', (-6, 14, -21), (12, 10, 11), plain)
    for sx in (-1, 1):
        g.box('head', (sx * 3, 21, -21.2), (3.5, 3, 1), ACID)
        g.box(f'jaw{"L" if sx > 0 else "R"}', (sx * 3.5, 16, -21), (2, 2, 7), dark, rotation=[0, sx * 25, 0], pivot=(sx * 2, 16, -17))
    # the crown crest
    for k in range(5):
        x = -5 + k * 2.5
        g.box('head', (x, 26 + (2 if k == 2 else 0), -14), (1.6, 5 + (2 if k == 2 else 0), 1.6), crown, rotation=[-20, 0, (k - 2) * 12], pivot=(x, 23, -14))
    g.box('abdomen', (0, 15, 20), (16, 14, 24), shell, rotation=[-10, 0, 0], pivot=(0, 18, 9))
    g.box('stinger', (0, 12.5, 33.5), (3, 3, 7), dark, rotation=[-25, 0, 0], pivot=(0, 14, 30))
    g.box('wingL', (12, 27, 4), (20, 0.4, 9), WING, rotation=[0, -20, 12], pivot=(4, 26, 0))
    g.box('wingR', (-12, 27, 4), (20, 0.4, 9), WING, rotation=[0, 20, -12], pivot=(-4, 26, 0))
    return g


def queen_animations():
    k = 'hive_queen'
    legs = {}
    for i in range(3):
        for side, ph in (('L', 0), ('R', 180)):
            legs[f'leg{side}{i}'] = {'rotation': [0, f'math.sin(q.anim_time * 600.0 + {ph + i * 120}.0) * 18.0', f'math.cos(q.anim_time * 600.0 + {ph + i * 120}.0) * 8.0']}
    return {
        f'animation.bc.{k}.idle': {'loop': True, 'bones': {
            'wingL': {'rotation': [0, 0, 'math.sin(q.life_time * 900.0) * 8.0']},
            'wingR': {'rotation': [0, 0, '-math.sin(q.life_time * 900.0) * 8.0']},
            'abdomen': {'rotation': ['math.sin(q.life_time * 80.0) * 4.0', 0, 0]},
            'jawL': {'rotation': [0, 'math.sin(q.life_time * 300.0) * 10.0', 0]},
            'jawR': {'rotation': [0, '-math.sin(q.life_time * 300.0) * 10.0', 0]},
        }},
        f'animation.bc.{k}.walk': {'loop': True, 'bones': legs},
        f'animation.bc.{k}.look_at_target': {'loop': True, 'bones': {'head': {'rotation': ['q.target_x_rotation * 0.5', 'q.target_y_rotation * 0.6', 0]}}},
        f'animation.bc.{k}.spit': {'animation_length': 0.8, 'bones': {
            'head': {'rotation': {'0.0': [0, 0, 0], '0.3': [-25, 0, 0], '0.5': [15, 0, 0], '0.8': [0, 0, 0]}},
            'jawL': {'rotation': {'0.0': [0, 0, 0], '0.3': [0, 35, 0], '0.8': [0, 0, 0]}},
            'jawR': {'rotation': {'0.0': [0, 0, 0], '0.3': [0, -35, 0], '0.8': [0, 0, 0]}},
        }},
        f'animation.bc.{k}.screech': {'animation_length': 1.4, 'bones': {
            'head': {'rotation': {'0.0': [0, 0, 0], '0.3': [-35, 0, 0], '1.1': [-35, 0, 0], '1.4': [0, 0, 0]}},
            'wingL': {'rotation': {'0.0': [0, 0, 0], '0.3': [0, 0, 50], '1.1': [0, 0, 50], '1.4': [0, 0, 0]}},
            'wingR': {'rotation': {'0.0': [0, 0, 0], '0.3': [0, 0, -50], '1.1': [0, 0, -50], '1.4': [0, 0, 0]}},
        }},
        f'animation.bc.{k}.lay': {'animation_length': 1.2, 'bones': {
            'abdomen': {'rotation': {'0.0': [0, 0, 0], '0.4': [25, 0, 0], '0.9': [25, 0, 0], '1.2': [0, 0, 0]}},
            'stinger': {'rotation': {'0.0': [0, 0, 0], '0.4': [30, 0, 0], '1.2': [0, 0, 0]}},
        }},
        f'animation.bc.{k}.burrow': {'animation_length': 1.0, 'bones': {
            'root': {'position': {'0.0': [0, 0, 0], '1.0': [0, -40, 0]}},
        }},
        f'animation.bc.{k}.emerge': {'animation_length': 0.8, 'bones': {
            'root': {'position': {'0.0': [0, -40, 0], '0.8': [0, 0, 0]}},
            'head': {'rotation': {'0.0': [-40, 0, 0], '0.8': [0, 0, 0]}},
        }},
    }


# ======================================================================================
# the Grimoire Devourer
# ======================================================================================
def devourer_geo():
    g = Geo('geometry.bc.grimoire_devourer', res=2, atlas_width=256, visible=(4, 4, (0, 2.0, 0)), seed=95)
    cover = tex.Material(tex.ramp('12060e', '200a18', '321026', '481836', '602046'), noise=0.15, edge=0.75)
    pages = tex.Material(tex.ramp('8a7e60', 'a89a78', 'c4b690', 'e0d4ac'), noise=0.1)
    tooth = tex.Material(P['bone'], noise=0.1)
    gold = tex.Metal(P['gold'])
    eye = tex.Energy(tex.ramp('3a0a0a', '8a1010', 'e02020', 'ffb0b0', 'ffffff'), alpha=170)
    claw = tex.Material(tex.ramp('0a0608', '160c12', '24141c'), noise=0.1)

    def runes(a, ctx):
        h, w = a.shape[:2]
        for y in range(2, h - 2, 3):
            for x in range(2, w - 2, 4):
                if (x * 7 + y * 3 + ctx.seed) % 5 < 2:
                    a[y, x:x + 2, :3] = np.array(rgb('c040ff')[:3])
        return a
    g.bone('root', pivot=(0, 0, 0))
    g.bone('book', 'root', (0, 30, 0))
    g.bone('upper', 'book', (0, 30, 8))
    g.bone('lower', 'book', (0, 30, 8))
    g.bone('armL', 'book', (12, 30, 4))
    g.bone('armR', 'book', (-12, 30, 4))
    g.bone('pages', 'book', (0, 30, 8))
    # the lower cover (jaw) with teeth, the upper cover with the eye
    g.cube('lower', (-12, 26, -10), (24, 3, 18), tex.Painted(cover, {'down': runes, 'north': runes}))
    g.cube('upper', (-12, 31, -10), (24, 3, 18), tex.Painted(cover, {'up': runes, 'north': runes}))
    g.cube('book', (-12.5, 26, 6), (25, 8, 2.5), cover)   # the spine
    for x in range(-10, 11, 3):
        g.box('lower', (x, 29.6, -9), (1.4, 2.4, 1.4), tooth, rotation=[0, 45, 0], pivot=(x, 29.6, -9))
        g.box('upper', (x + 1.5, 30.4, -9), (1.4, 2.4, 1.4), tooth, rotation=[0, 45, 0], pivot=(x + 1.5, 30.4, -9))
    g.cube('pages', (-11, 29, -9), (22, 2, 15), pages)
    g.box('upper', (0, 34.6, -2), (6, 0.8, 6), gold, rotation=[0, 45, 0], pivot=(0, 34.6, -2))
    g.box('upper', (0, 35.4, -2), (3.2, 2.2, 3.2), eye)
    for c in ((-11, -9), (11, -9), (-11, 5), (11, 5)):
        g.box('upper', (c[0], 34.3, c[1]), (2.4, 0.8, 2.4), gold)
        g.box('lower', (c[0], 25.7, c[1]), (2.4, 0.8, 2.4), gold)
    for side, sx in (('armL', 1), ('armR', -1)):
        g.box(side, (sx * 16, 26, 2), (2.6, 12, 2.6), claw, rotation=[20, 0, sx * -30], pivot=(sx * 12, 30, 4))
        for k in range(3):
            g.box(side, (sx * (19 + k * 0.6), 19, 0 + k * 1.4 - 1.4), (0.8, 4, 0.8), tooth, rotation=[30, 0, sx * -20], pivot=(sx * 19, 21, 0))
    # loose pages that orbit it
    for k in range(4):
        a = math.radians(k * 90 + 45)
        g.box('pages', (math.cos(a) * 18, 36 + (k % 2) * 4, math.sin(a) * 18), (3, 4, 0.2), pages, rotation=[0, k * 90 + 45, 15], pivot=(math.cos(a) * 18, 36, math.sin(a) * 18))
    return g


def devourer_animations():
    k = 'grimoire_devourer'
    return {
        f'animation.bc.{k}.float': {'loop': True, 'bones': {
            'root': {'position': [0, 'math.sin(q.life_time * 80.0) * 2.0', 0]},
            'upper': {'rotation': ['-8.0 - math.abs(math.sin(q.life_time * 60.0)) * 6.0', 0, 0]},
            'lower': {'rotation': ['6.0 + math.abs(math.sin(q.life_time * 60.0)) * 4.0', 0, 0]},
            'pages': {'rotation': [0, 'q.life_time * 40.0', 0]},
            'armL': {'rotation': ['math.sin(q.life_time * 100.0) * 10.0', 0, 0]},
            'armR': {'rotation': ['-math.sin(q.life_time * 100.0) * 10.0', 0, 0]},
        }},
        f'animation.bc.{k}.look_at_target': {'loop': True, 'bones': {'book': {'rotation': [0, 'q.target_y_rotation * 0.3', 0]}}},
        f'animation.bc.{k}.chomp': {'animation_length': 0.8, 'bones': {
            'upper': {'rotation': {'0.0': [-8, 0, 0], '0.25': [-55, 0, 0], '0.4': [2, 0, 0], '0.8': [-8, 0, 0]}},
            'lower': {'rotation': {'0.0': [6, 0, 0], '0.25': [35, 0, 0], '0.4': [-2, 0, 0], '0.8': [6, 0, 0]}},
        }},
        f'animation.bc.{k}.cast': {'animation_length': 1.0, 'bones': {
            'upper': {'rotation': {'0.0': [-8, 0, 0], '0.3': [-80, 0, 0], '0.8': [-80, 0, 0], '1.0': [-8, 0, 0]}},
            'armL': {'rotation': {'0.0': [0, 0, 0], '0.3': [-60, 0, -30], '1.0': [0, 0, 0]}},
            'armR': {'rotation': {'0.0': [0, 0, 0], '0.3': [-60, 0, 30], '1.0': [0, 0, 0]}},
        }},
        f'animation.bc.{k}.roar': {'animation_length': 1.4, 'bones': {
            'upper': {'rotation': {'0.0': [-8, 0, 0], '0.3': [-70, 0, 0], '1.1': [-70, 0, 0], '1.4': [-8, 0, 0]}},
            'lower': {'rotation': {'0.0': [6, 0, 0], '0.3': [40, 0, 0], '1.1': [40, 0, 0], '1.4': [6, 0, 0]}},
            'armL': {'rotation': {'0.0': [0, 0, 0], '0.3': [-30, 0, -70], '1.1': [-30, 0, -70], '1.4': [0, 0, 0]}},
            'armR': {'rotation': {'0.0': [0, 0, 0], '0.3': [-30, 0, 70], '1.1': [-30, 0, 70], '1.4': [0, 0, 0]}},
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


def v7_icons():
    def crown(d, s):
        d.polygon([(4 * s, 24 * s), (4 * s, 10 * s), (10 * s, 17 * s), (16 * s, 6 * s), (22 * s, 17 * s), (28 * s, 10 * s), (28 * s, 24 * s)], fill=(230, 180, 50, 255))
        d.rectangle([4 * s, 22 * s, 28 * s, 27 * s], fill=(200, 150, 40, 255))
        d.ellipse([14 * s, 18 * s, 18 * s, 22 * s], fill=(210, 40, 40, 255))
        d.line([(6 * s, 28 * s), (26 * s, 28 * s)], fill=(120, 30, 20, 255), width=int(1.5 * s))

    def tome(d, s):
        d.rectangle([5 * s, 4 * s, 27 * s, 28 * s], fill=(60, 20, 50, 255))
        d.rectangle([7 * s, 6 * s, 25 * s, 26 * s], outline=(200, 160, 60, 255), width=int(1.2 * s))
        d.ellipse([12 * s, 10 * s, 20 * s, 18 * s], fill=(220, 40, 40, 255))
        d.ellipse([14.5 * s, 12.5 * s, 17.5 * s, 15.5 * s], fill=(20, 0, 0, 255))
        for x in range(8, 25, 3):
            d.polygon([(x * s, 26 * s), ((x + 1.5) * s, 22 * s), ((x + 3) * s, 26 * s)], fill=(230, 220, 200, 255))

    def jelly(d, s):
        d.polygon([(10 * s, 6 * s), (22 * s, 6 * s), (26 * s, 28 * s), (6 * s, 28 * s)], fill=(200, 170, 60, 255))
        d.rectangle([9 * s, 3 * s, 23 * s, 7 * s], fill=(120, 80, 30, 255))
        d.ellipse([10 * s, 14 * s, 22 * s, 26 * s], fill=(250, 220, 90, 255))
        d.ellipse([13 * s, 16 * s, 17 * s, 20 * s], fill=(255, 250, 200, 255))
    return {'bandit_crown': _icon(crown), 'forbidden_tome': _icon(tome), 'royal_jelly': _icon(jelly)}
