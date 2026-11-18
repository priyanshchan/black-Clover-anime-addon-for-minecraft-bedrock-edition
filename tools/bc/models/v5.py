"""v0.5.0 models and animations: companion emotes and riding, the Squad Banner, the Training Dummy, the Soul Puppeteer
and its marionettes, and new icons. All designs are original."""
from __future__ import annotations

import numpy as np

from .. import tex
from ..geo import Geo
from ..tex import P, rgb


# ======================================================================================
# companion animations (Magic Knight bones: root, waist, body, head, arms, legs, cape, book)
# ======================================================================================
def knight_v5_animations():
    """Emotes, combat stances and riding for companions."""
    return {
        'animation.bc.magic_knight.kneel': {'loop': 'hold_on_last_frame', 'animation_length': 0.5, 'bones': {
            'root': {'position': {'0.0': [0, 0, 0], '0.5': [0, -4, 0]}},
            'rightLeg': {'rotation': {'0.0': [0, 0, 0], '0.5': [-62, 0, 0]}},
            'leftLeg': {'rotation': {'0.0': [0, 0, 0], '0.5': [55, 0, 0]}},
            'body': {'rotation': {'0.0': [0, 0, 0], '0.5': [12, 0, 0]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.5': [18, 0, 0]}},
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.5': [-35, 0, 8]}},
            'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.5': [-20, 0, -8]}},
            'cape': {'rotation': {'0.0': [4, 0, 0], '0.5': [10, 0, 0]}},
        }},
        'animation.bc.magic_knight.point': {'animation_length': 1.4, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-92, -6, 0], '1.1': [-90, -4, 0], '1.4': [0, 0, 0]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.2': [-6, -8, 0], '1.4': [0, 0, 0]}},
            'body': {'rotation': {'0.0': [0, 0, 0], '0.2': [0, -10, 0], '1.4': [0, 0, 0]}},
        }},
        'animation.bc.magic_knight.guard': {'animation_length': 1.0, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.12': [-75, 35, 0], '0.85': [-75, 35, 0], '1.0': [0, 0, 0]}},
            'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.12': [-75, -35, 0], '0.85': [-75, -35, 0], '1.0': [0, 0, 0]}},
            'body': {'rotation': {'0.0': [0, 0, 0], '0.12': [8, 0, 0], '1.0': [0, 0, 0]}},
            'rightLeg': {'rotation': {'0.0': [0, 0, 0], '0.12': [-18, 0, 6], '1.0': [0, 0, 0]}},
            'leftLeg': {'rotation': {'0.0': [0, 0, 0], '0.12': [16, 0, -6], '1.0': [0, 0, 0]}},
        }},
        'animation.bc.magic_knight.victory': {'animation_length': 1.6, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.25': [-178, 0, 8], '1.3': [-178, 0, 8], '1.6': [0, 0, 0]}},
            'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.25': [-10, 0, -30], '1.6': [0, 0, 0]}},
            'root': {'position': {'0.0': [0, 0, 0], '0.25': [0, 4, 0], '0.45': [0, 0, 0], '0.8': [0, 2.5, 0], '1.0': [0, 0, 0]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.25': [-20, 0, 0], '1.6': [0, 0, 0]}},
            'cape': {'rotation': {'0.0': [4, 0, 0], '0.25': [35, 0, 0], '0.45': [10, 0, 0], '0.8': [28, 0, 0], '1.6': [4, 0, 0]}},
        }},
        'animation.bc.magic_knight.wave': {'animation_length': 1.4, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-160, 0, 20], '0.45': [-160, 0, -5], '0.7': [-160, 0, 20], '0.95': [-160, 0, -5], '1.4': [0, 0, 0]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.2': [0, 0, 6], '1.4': [0, 0, 0]}},
        }},
        'animation.bc.magic_knight.ride': {'loop': True, 'bones': {
            'root': {'position': [0, -11, 0]},
            'rightLeg': {'rotation': [-75, 12, 0]},
            'leftLeg': {'rotation': [-75, -12, 0]},
            'rightArm': {'rotation': ['-55.0 + math.sin(q.life_time * 200.0) * 3.0', 8, 0]},
            'leftArm': {'rotation': ['-50.0 + math.sin(q.life_time * 200.0 + 60.0) * 3.0', -8, 0]},
            'body': {'rotation': [10, 0, 0]},
            'cape': {'rotation': ['45.0 + math.sin(q.life_time * 500.0) * 8.0', 0, 0]},
        }},
        'animation.bc.magic_knight.sleep': {'loop': True, 'bones': {
            'root': {'position': [0, 2, -12], 'rotation': [-90, 0, 0]},
            'head': {'rotation': [0, 0, 'math.sin(q.life_time * 40.0) * 2.0']},
            'rightArm': {'rotation': [-5, 0, 10]},
            'leftArm': {'rotation': [-5, 0, -10]},
        }},
        'animation.bc.magic_knight.eat': {'animation_length': 1.6, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.25': [-110, -30, 0], '0.5': [-100, -30, 0], '0.75': [-110, -30, 0], '1.0': [-100, -30, 0], '1.25': [-110, -30, 0], '1.6': [0, 0, 0]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.25': [8, 0, 0], '0.5': [14, 0, 0], '0.75': [8, 0, 0], '1.0': [14, 0, 0], '1.6': [0, 0, 0]}},
        }},
        'animation.bc.magic_knight.taunt': {'animation_length': 1.2, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-30, 0, 75], '0.6': [-30, 0, 75], '0.8': [-80, 0, 20], '0.95': [-60, 0, 40], '1.2': [0, 0, 0]}},
            'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-30, 0, -75], '0.6': [-30, 0, -75], '1.2': [0, 0, 0]}},
            'body': {'rotation': {'0.0': [0, 0, 0], '0.2': [-12, 0, 0], '0.6': [-12, 0, 0], '1.2': [0, 0, 0]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.2': [-20, 0, 0], '1.2': [0, 0, 0]}},
        }},
    }


# ======================================================================================
# the Squad Banner block
# ======================================================================================
def squad_banner_geo():
    g = Geo('geometry.bc.squad_banner', res=2, atlas_width=128, visible=(2, 3, (0, 1.0, 0)))
    g.bone('banner', pivot=(0, 0, 0))
    pole = tex.Wood(tex.ramp('1e130b', '2c1c10', '3b2716', '4c331d'))
    gold = tex.Metal(P['gold'])
    stone = tex.Stone(P['stone'])
    cloth_r = tex.ramp('0c2a12', '14401c', '1e5628', '2a6e34', '388a42')

    def emblem(a, ctx):
        h, w = a.shape[:2]
        a[:, :2, :3] = rgb('d39a2c')[:3]
        a[:, w - 2:, :3] = rgb('d39a2c')[:3]
        a[h - 2:, :, :3] = rgb('d39a2c')[:3]

        def draw(d, s):
            tex.clover_shape(d, w * s / 2, h * s * 0.42, min(w, h) * s * 0.34, 4, (232, 210, 120, 255), stem=True)
        lay = tex.draw_layer(h, w, draw, 4)
        lay[..., 3] = np.where(lay[..., 3] > 100, 255, 0)
        tex.alpha_over(a, lay)
        return a
    cloth = tex.Painted(tex.Cloth(cloth_r, folds=0.2), {'north': emblem, 'south': emblem})
    g.cube('banner', (-4, 0, -4), (8, 2, 8), stone)
    g.cube('banner', (-1, 2, -1), (2, 26, 2), pole)
    g.cube('banner', (-7, 26, -0.75), (14, 1.5, 1.5), pole)
    g.box('banner', (-7.4, 26.75, 0), (1.6, 1.6, 1.6), gold)
    g.box('banner', (7.4, 26.75, 0), (1.6, 1.6, 1.6), gold)
    g.box('banner', (0, 28.4, 0), (1.8, 1.8, 1.8), gold, rotation=[45, 45, 0], pivot=(0, 28.4, 0))
    g.cube('banner', (-6, 9, -0.4), (12, 17, 0.8), cloth)
    for x in (-6, -2, 2):
        g.cube('banner', (x, 7.5, -0.4), (4, 1.5, 0.8), tex.Cloth(cloth_r))
    return g


# ======================================================================================
# the Training Dummy
# ======================================================================================
def training_dummy_geo():
    g = Geo('geometry.bc.training_dummy', res=2, atlas_width=128, visible=(2, 3, (0, 1.0, 0)), seed=51)
    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 4, 0))
    g.bone('head', 'body', (0, 22, 0))
    post = tex.Wood(tex.ramp('2a1a0c', '3e2814', '54381c', '6a4826'))
    straw = tex.Material(tex.ramp('6a5014', '8a6a20', 'a88430', 'c8a044', 'e0bc5a'), noise=0.4)
    sack = tex.Cloth(tex.ramp('5a4a32', '6e5c40', '84704e', '9a845e'), folds=0.15)
    rope = tex.Material(tex.ramp('4a3a22', '6a5432', '8a6e44'), noise=0.2)

    def target(a, ctx):
        h, w = a.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        r = np.hypot(yy - h / 2 + 0.5, xx - w / 2 + 0.5) / (min(h, w) / 2)
        ring = (np.floor(r * 3) % 2 == 0) & (r < 1)
        a[ring, :3] = rgb('b02424')[:3]
        a[r < 0.2, :3] = rgb('f0e0c0')[:3]
        return a
    g.cube('root', (-4, 0, -4), (8, 1.5, 8), post)
    g.cube('root', (-1, 1.5, -1), (2, 10, 2), post)
    g.cube('body', (-4.5, 10, -2.5), (9, 12, 5), tex.Painted(sack, {'north': target}))
    g.cube('body', (-10, 18, -1), (20, 2, 2), post)
    for x in (-10.5, 7.5):
        g.cube('body', (x, 16.5, -1.6), (3, 5, 3.2), straw)
    g.cube('body', (-4.8, 13.5, -2.8), (9.6, 1.2, 5.6), rope)
    g.cube('head', (-3.5, 22, -3.5), (7, 7, 7), tex.Painted(sack, {'north': lambda a, c: (a.__setitem__((slice(a.shape[0] // 3, a.shape[0] // 3 + 2), slice(1, 3), slice(0, 3)), rgb('1a1410')[:3]),
                                                                                       a.__setitem__((slice(a.shape[0] // 3, a.shape[0] // 3 + 2), slice(a.shape[1] - 3, a.shape[1] - 1), slice(0, 3)), rgb('1a1410')[:3]), a)[2]}))
    g.cube('head', (-4, 28.5, -4), (8, 1.5, 8), straw)
    return g


def training_dummy_animations():
    return {
        'animation.bc.training_dummy.hit': {'animation_length': 0.8, 'bones': {
            'body': {'rotation': {'0.0': [0, 0, 0], '0.08': [-14, 0, 6], '0.25': [8, 0, -4], '0.45': [-4, 0, 2], '0.65': [2, 0, -1], '0.8': [0, 0, 0]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.08': [-10, 0, 0], '0.3': [6, 0, 0], '0.8': [0, 0, 0]}},
        }},
    }


# ======================================================================================
# the Soul Puppeteer (boss) and its marionettes
# ======================================================================================
def puppeteer_geo():
    g = Geo('geometry.bc.soul_puppeteer', res=2, atlas_width=128, visible=(4, 5, (0, 2.0, 0)), seed=61)
    coat = tex.Cloth(tex.ramp('0e0612', '180a20', '24102e', '321640', '421e54'), folds=0.25)
    lining = tex.Cloth(tex.ramp('3a0a10', '560e18', '761420'))
    gold = tex.Metal(P['gold'])
    porcelain = tex.Material(tex.ramp('a8a0a4', 'c4bec2', 'dcd8dc', 'f2eef2'), noise=0.04, edge=0.85)
    hat = tex.Material(tex.ramp('08060a', '120e16', '1c1622', '28202e'), noise=0.1)
    wood = tex.Wood(tex.ramp('3a2414', '54341c', '6e4626', '8a5a32'))
    string = tex.Flat('e8e4f0')
    glove = tex.Material(tex.ramp('d8d4dc', 'eeeaf2', 'ffffff'), noise=0.05)

    def mask(a, ctx):
        h, w = a.shape[:2]
        for ex in (int(w * 0.18), int(w * 0.6)):
            a[int(h * 0.38):int(h * 0.38) + 2, ex:ex + max(2, int(w * 0.22)), :3] = rgb('100818')[:3]
        a[int(h * 0.42) + 2:int(h * 0.42) + 5, int(w * 0.28), :3] = rgb('6a40c0')[:3]  # a painted teardrop
        a[int(h * 0.72), int(w * 0.25):int(w * 0.75), :3] = rgb('7a1020')[:3]
        a[int(h * 0.70), int(w * 0.2), :3] = rgb('7a1020')[:3]
        a[int(h * 0.70), int(w * 0.78), :3] = rgb('7a1020')[:3]
        return a
    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 20, 0))
    g.bone('coat', 'body', (0, 20, 0))
    g.bone('head', 'body', (0, 36, 0))
    g.bone('hat', 'head', (0, 44, 0))
    g.bone('rightArm', 'body', (-6, 34, 0))
    g.bone('leftArm', 'body', (6, 34, 0))
    g.bone('rightBar', 'rightArm', (-7, 21, -3))
    g.bone('leftBar', 'leftArm', (7, 21, -3))
    g.bone('backArmR', 'body', (-3, 33, 3))
    g.bone('backArmL', 'body', (3, 33, 3))
    g.cube('head', (-4, 36, -4), (8, 8, 8), tex.Painted(porcelain, {'north': mask}))
    g.cube('hat', (-6, 43.6, -6), (12, 1, 12), hat)
    g.cube('hat', (-4, 44.4, -4), (8, 8, 8), hat)
    g.cube('hat', (-4.2, 45.4, -4.2), (8.4, 1.2, 8.4), lining)
    g.cube('body', (-5, 20, -3), (10, 16, 6), coat)
    for y in (24, 27.5, 31):
        g.box('body', (0, y, -3.2), (1.2, 1.2, 0.6), gold)
    g.cube('body', (-5.5, 33, -3.5), (11, 3, 7), lining)
    g.cube('body', (-4.6, 35.5, -4.6), (9.2, 1.6, 9.2), lining)  # a high collar
    for k, (wd, y0) in enumerate(((11, 13), (10, 6), (8, 0), (5, -5))):
        g.cube('coat', (-wd / 2, y0, -wd / 3), (wd, 7.2, wd / 1.5), coat)
    g.cube('coat', (-1, -8, -1), (2, 3.5, 2), lining)
    for side, x0, sx in (('rightArm', -9, -1), ('leftArm', 5, 1)):
        g.cube(side, (x0, 24, -2), (4, 11, 4), coat)
        g.cube(side, (x0 + 0.3, 21, -1.7), (3.4, 3, 3.4), glove)
    for side, bar_bone, x in (('rightBar', 'rightBar', -7), ('leftBar', 'leftBar', 7)):
        g.cube(bar_bone, (x - 4, 20.5, -3.6), (8, 1.2, 1.2), wood)
        g.cube(bar_bone, (x - 0.6, 20.5, -7.6), (1.2, 1.2, 8), wood)
        for dx, dz in ((-3.5, -3), (3.5, -3), (0, -7), (0, 0.5)):
            g.cube(bar_bone, (x + dx - 0.15, 12.5, dz - 0.15), (0.3, 8, 0.3), string)
    for side, x, sx in (('backArmR', -3, -1), ('backArmL', 3, 1)):
        g.box(side, (x + sx * 5, 38, 5), (1.6, 1.6, 12), coat, rotation=[-35, sx * 30, 0], pivot=(x, 33, 3))
        g.box(side, (x + sx * 9, 44, 9), (1.4, 1.4, 1.4), glove, rotation=[-35, sx * 30, 0], pivot=(x, 33, 3))
    return g


def puppeteer_animations():
    k = 'soul_puppeteer'
    return {
        f'animation.bc.{k}.float': {'loop': True, 'bones': {
            'root': {'position': [0, '4.0 + math.sin(q.life_time * 90.0) * 1.5', 0]},
            'coat': {'rotation': ['math.sin(q.life_time * 120.0) * 5.0', 0, 'math.cos(q.life_time * 80.0) * 4.0']},
            'rightArm': {'rotation': ['-40.0 + math.sin(q.life_time * 100.0) * 8.0', 0, 10]},
            'leftArm': {'rotation': ['-40.0 + math.sin(q.life_time * 100.0 + 90.0) * 8.0', 0, -10]},
            'rightBar': {'rotation': ['math.sin(q.life_time * 200.0) * 10.0', 0, 0]},
            'leftBar': {'rotation': ['math.sin(q.life_time * 200.0 + 120.0) * 10.0', 0, 0]},
            'backArmR': {'rotation': [0, 0, 'math.sin(q.life_time * 70.0) * 10.0']},
            'backArmL': {'rotation': [0, 0, '-math.sin(q.life_time * 70.0) * 10.0']},
            'head': {'rotation': [0, 0, 'math.sin(q.life_time * 50.0) * 6.0']},
        }},
        f'animation.bc.{k}.look_at_target': {'loop': True, 'bones': {'head': {'rotation': ['q.target_x_rotation', 'q.target_y_rotation', 0]}}},
        f'animation.bc.{k}.cast': {'animation_length': 0.9, 'bones': {
            'rightArm': {'rotation': {'0.0': [-40, 0, 10], '0.25': [-165, 0, 15], '0.7': [-160, 0, 12], '0.9': [-40, 0, 10]}},
            'leftArm': {'rotation': {'0.0': [-40, 0, -10], '0.25': [-165, 0, -15], '0.7': [-160, 0, -12], '0.9': [-40, 0, -10]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.25': [-20, 0, 0], '0.9': [0, 0, 0]}},
        }},
        f'animation.bc.{k}.control': {'animation_length': 1.4, 'bones': {
            'rightArm': {'rotation': {'0.0': [-40, 0, 10], '0.2': [-110, 0, 10], '0.4': [-60, 0, 10], '0.6': [-120, 0, 10], '0.8': [-60, 0, 10], '1.0': [-120, 0, 10], '1.4': [-40, 0, 10]}},
            'leftArm': {'rotation': {'0.0': [-40, 0, -10], '0.3': [-120, 0, -10], '0.5': [-60, 0, -10], '0.7': [-120, 0, -10], '0.9': [-60, 0, -10], '1.4': [-40, 0, -10]}},
            'rightBar': {'rotation': {'0.0': [0, 0, 0], '0.2': [30, 0, 0], '0.4': [-30, 0, 0], '0.6': [30, 0, 0], '1.4': [0, 0, 0]}},
            'leftBar': {'rotation': {'0.0': [0, 0, 0], '0.3': [-30, 0, 0], '0.5': [30, 0, 0], '0.7': [-30, 0, 0], '1.4': [0, 0, 0]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.2': [0, 0, 20], '0.7': [0, 0, -20], '1.4': [0, 0, 0]}},
        }},
        f'animation.bc.{k}.summon': {'animation_length': 1.2, 'bones': {
            'rightArm': {'rotation': {'0.0': [-40, 0, 10], '0.3': [-90, 0, 80], '0.9': [-90, 0, 80], '1.2': [-40, 0, 10]}},
            'leftArm': {'rotation': {'0.0': [-40, 0, -10], '0.3': [-90, 0, -80], '0.9': [-90, 0, -80], '1.2': [-40, 0, -10]}},
            'backArmR': {'rotation': {'0.0': [0, 0, 0], '0.3': [-40, 0, 30], '1.2': [0, 0, 0]}},
            'backArmL': {'rotation': {'0.0': [0, 0, 0], '0.3': [-40, 0, -30], '1.2': [0, 0, 0]}},
        }},
        f'animation.bc.{k}.roar': {'animation_length': 1.6, 'bones': {
            'head': {'rotation': {'0.0': [0, 0, 0], '0.3': [-40, 0, 0], '0.5': [-40, 0, 25], '0.7': [-40, 0, -25], '0.9': [-40, 0, 25], '1.3': [-40, 0, 0], '1.6': [0, 0, 0]}},
            'rightArm': {'rotation': {'0.0': [-40, 0, 10], '0.3': [-20, 0, 90], '1.3': [-20, 0, 90], '1.6': [-40, 0, 10]}},
            'leftArm': {'rotation': {'0.0': [-40, 0, -10], '0.3': [-20, 0, -90], '1.3': [-20, 0, -90], '1.6': [-40, 0, -10]}},
            'coat': {'rotation': {'0.0': [0, 0, 0], '0.3': [20, 0, 0], '1.6': [0, 0, 0]}},
        }},
    }


def puppet_geo():
    g = Geo('geometry.bc.puppet', res=2, atlas_width=64, visible=(2, 2, (0, 0.6, 0)), seed=71)
    wood = tex.Wood(tex.ramp('6a4426', '86583a', 'a2704a', 'bc885c'))
    joint = tex.Wood(tex.ramp('2a1a0c', '3e2814', '54381c'))
    dress = tex.Cloth(tex.ramp('3a0a14', '56101e', '741a2a', '922436'), folds=0.2)
    string = tex.Flat('e8e4f0')

    def face(a, ctx):
        h, w = a.shape[:2]
        for ex in (int(w * 0.2), int(w * 0.62)):
            a[int(h * 0.4):int(h * 0.4) + 2, ex:ex + 2, :3] = rgb('100818')[:3]
        a[int(h * 0.7), int(w * 0.3):int(w * 0.7), :3] = rgb('7a1020')[:3]
        a[int(h * 0.58), int(w * 0.12):int(w * 0.22), :3] = rgb('d06080')[:3]
        a[int(h * 0.58), int(w * 0.78):int(w * 0.88), :3] = rgb('d06080')[:3]
        return a
    g.bone('root', pivot=(0, 0, 0))
    g.bone('body', 'root', (0, 8, 0))
    g.bone('head', 'body', (0, 15, 0))
    g.bone('rightArm', 'body', (-3.5, 14, 0))
    g.bone('leftArm', 'body', (3.5, 14, 0))
    g.bone('rightLeg', 'root', (-1.4, 8, 0))
    g.bone('leftLeg', 'root', (1.4, 8, 0))
    g.cube('head', (-2.5, 15, -2.5), (5, 5, 5), tex.Painted(wood, {'north': face}))
    g.cube('head', (-0.15, 20, -0.15), (0.3, 6, 0.3), string)
    g.cube('body', (-2.5, 8, -1.5), (5, 7, 3), dress)
    g.box('body', (0, 14.5, 0), (1.4, 1, 1.4), joint)
    for side, x0 in (('rightArm', -4.5), ('leftArm', 2.5)):
        g.cube(side, (x0 + 0.3, 8.5, -0.7), (1.4, 5.5, 1.4), wood)
        g.box(side, (x0 + 1, 11.2, 0), (1.6, 0.8, 1.6), joint)
        g.cube(side, (x0 + 0.85, 13.8, -0.15), (0.3, 8, 0.3), string)
    for side, x0 in (('rightLeg', -2.2), ('leftLeg', 0.6)):
        g.cube(side, (x0, 0, -0.8), (1.6, 8, 1.6), wood)
        g.box(side, (x0 + 0.8, 4, 0), (1.8, 0.8, 1.8), joint)
    return g


def puppet_animations():
    k = 'puppet'
    return {
        f'animation.bc.{k}.idle': {'loop': True, 'bones': {
            'root': {'position': [0, 'math.abs(math.sin(q.life_time * 180.0)) * 0.8', 0]},
            'head': {'rotation': [0, 0, 'math.sin(q.life_time * 120.0) * 12.0']},
            'rightArm': {'rotation': ['math.sin(q.life_time * 160.0) * 15.0', 0, 20]},
            'leftArm': {'rotation': ['-math.sin(q.life_time * 160.0) * 15.0', 0, -20]},
        }},
        f'animation.bc.{k}.walk': {'loop': True, 'bones': {
            'rightLeg': {'rotation': ['math.sin(q.anim_time * 900.0) * 45.0', 0, 0]},
            'leftLeg': {'rotation': ['-math.sin(q.anim_time * 900.0) * 45.0', 0, 0]},
            'rightArm': {'rotation': ['-math.sin(q.anim_time * 900.0) * 50.0', 0, 25]},
            'leftArm': {'rotation': ['math.sin(q.anim_time * 900.0) * 50.0', 0, -25]},
            'body': {'rotation': [0, 'math.sin(q.anim_time * 450.0) * 12.0', 0]},
        }},
        f'animation.bc.{k}.attack': {'animation_length': 0.4, 'bones': {
            'rightArm': {'rotation': {'0.0': [0, 0, 20], '0.12': [-170, 0, 10], '0.25': [-30, 0, 0], '0.4': [0, 0, 20]}},
            'leftArm': {'rotation': {'0.0': [0, 0, -20], '0.12': [-170, 0, -10], '0.25': [-30, 0, 0], '0.4': [0, 0, -20]}},
            'head': {'rotation': {'0.0': [0, 0, 0], '0.12': [-25, 0, 0], '0.4': [0, 0, 0]}},
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


def v5_icons():
    def banner(d, s):
        d.rectangle([14 * s, 2 * s, 17 * s, 30 * s], fill=(90, 60, 30, 255))
        d.rectangle([6 * s, 3 * s, 26 * s, 5 * s], fill=(210, 160, 50, 255))
        d.polygon([(8 * s, 5 * s), (24 * s, 5 * s), (24 * s, 22 * s), (16 * s, 26 * s), (8 * s, 22 * s)], fill=(40, 110, 50, 255))
        tex.clover_shape(d, 16 * s, 13 * s, 5.5 * s, 4, (232, 210, 120, 255), stem=False)

    def dummy(d, s):
        d.rectangle([14.5 * s, 18 * s, 17.5 * s, 30 * s], fill=(90, 60, 30, 255))
        d.rectangle([5 * s, 12 * s, 27 * s, 15 * s], fill=(90, 60, 30, 255))
        d.rounded_rectangle([9 * s, 9 * s, 23 * s, 24 * s], radius=3 * s, fill=(170, 140, 90, 255))
        d.ellipse([12 * s, 12 * s, 20 * s, 20 * s], fill=(190, 40, 40, 255))
        d.ellipse([14.5 * s, 14.5 * s, 17.5 * s, 17.5 * s], fill=(240, 225, 190, 255))
        d.ellipse([11 * s, 1 * s, 21 * s, 10 * s], fill=(170, 140, 90, 255))

    def leaf(d, s):
        tex.clover_shape(d, 16 * s, 15 * s, 12 * s, 4, (90, 210, 110, 255), stem=True)
        d.ellipse([13 * s, 12 * s, 19 * s, 18 * s], fill=(255, 240, 150, 255))

    def rations(d, s):
        d.rounded_rectangle([4 * s, 10 * s, 28 * s, 27 * s], radius=3 * s, fill=(150, 110, 60, 255))
        d.line([(4 * s, 18 * s), (28 * s, 18 * s)], fill=(90, 60, 30, 255), width=int(1.5 * s))
        d.line([(16 * s, 10 * s), (16 * s, 27 * s)], fill=(90, 60, 30, 255), width=int(1.5 * s))
        d.ellipse([8 * s, 4 * s, 16 * s, 12 * s], fill=(210, 150, 80, 255))
        d.ellipse([16 * s, 5 * s, 24 * s, 12 * s], fill=(200, 60, 50, 255))

    def tome(d, s):
        d.rectangle([6 * s, 4 * s, 26 * s, 28 * s], fill=(40, 80, 140, 255))
        d.rectangle([8 * s, 6 * s, 24 * s, 26 * s], outline=(220, 190, 90, 255), width=int(1.2 * s))
        d.rectangle([24 * s, 5 * s, 27 * s, 27 * s], fill=(235, 225, 200, 255))
        for k in range(3):
            x = 11 + k * 5
            d.ellipse([(x - 2) * s, 13 * s, (x + 2) * s, 17 * s], fill=(120, 220, 255, 255))
        d.line([(10 * s, 21 * s), (22 * s, 21 * s)], fill=(220, 190, 90, 255), width=int(1.2 * s))

    def spool(d, s):
        d.rectangle([9 * s, 4 * s, 23 * s, 7 * s], fill=(70, 40, 90, 255))
        d.rectangle([9 * s, 25 * s, 23 * s, 28 * s], fill=(70, 40, 90, 255))
        d.rectangle([11 * s, 7 * s, 21 * s, 25 * s], fill=(230, 225, 240, 255))
        for y in range(9, 25, 3):
            d.line([(11 * s, y * s), (21 * s, (y + 1) * s)], fill=(160, 140, 190, 255), width=int(0.8 * s))
        d.line([(21 * s, 12 * s), (29 * s, 4 * s)], fill=(230, 225, 240, 255), width=int(0.8 * s))
        d.ellipse([12 * s, 13 * s, 20 * s, 21 * s], outline=(150, 40, 60, 255), width=int(1.2 * s))
    return {
        'squad_banner': _icon(banner), 'training_dummy': _icon(dummy), 'clover_leaf': _icon(leaf),
        'field_rations': _icon(rations), 'companion_tome': _icon(tome), 'cursed_spool': _icon(spool),
    }
