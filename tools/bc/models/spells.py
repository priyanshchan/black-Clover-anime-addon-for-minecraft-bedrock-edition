"""Spell entity models (forward = -Z). Each returns (Geo, material_kind, animations)."""
from __future__ import annotations

import math

import numpy as np

from .. import tex
from ..geo import Geo
from ..tex import P, rgb

ORIENT = ['-q.target_x_rotation', '-q.target_y_rotation', 0]


def arc(g, bone, R, deg, n, thick, depth_fn, mat, y=0.0, zshift=0.0, plane='xz', roff=None):
    """Crescent made of short boxes along an arc that bulges toward -Z."""
    R0 = R
    for i in range(n):
        th = -deg + (2 * deg) * (i + 0.5) / n
        t = math.radians(th)
        R = R0 + (roff(abs(th) / deg) if roff else 0.0)
        seg = 2 * math.radians(deg) * R / n * 1.25
        dep = depth_fn(abs(th) / deg)
        cx, cz = R * math.sin(t), -R * math.cos(t) + zshift
        if plane == 'xz':
            g.box(bone, (cx, y, cz), (seg, thick, dep), mat, rotation=[0, -th, 0], pivot=(cx, y, cz))
        else:  # vertical crescent in the YZ plane
            g.box(bone, (0, cx + y, cz), (thick, seg, dep), mat, rotation=[th, 0, 0], pivot=(0, cx + y, cz))


def ring(g, bone, R, n, thick, height, mat, y=0.0, phase=0.0, tilt=None):
    for i in range(n):
        th = phase + i * 360.0 / n
        t = math.radians(th)
        seg = 2 * math.pi * R / n * 1.12
        cx, cz = R * math.sin(t), R * math.cos(t)
        g.box(bone, (cx, y, cz), (seg, height, thick), mat, rotation=[0, th, 0], pivot=(cx, y, cz))


def _orient_anim(name, extra=None, spin=None):
    bones = {'root': {'rotation': ORIENT}}
    if spin:
        bones['spin'] = {'rotation': spin}
    if extra:
        bones.update(extra)
    return {name: {'loop': True, 'bones': bones}}


# ----------------------------------------------------------------------------- blades
def wind_blade():
    g = Geo('geometry.bc.wind_blade', res=2, atlas_width=64, visible=(2, 1, (0, 0, 0)))
    g.bone('root', pivot=(0, 0, 0))
    outer = tex.Energy(P['wind'], alpha=150)
    core = tex.Energy(P['wind'][2:], alpha=130)
    arc(g, 'root', 9, 70, 11, 0.6, lambda f: 0.6 + 2.6 * (1 - f) ** 0.8, outer, zshift=6)
    arc(g, 'root', 9.6, 55, 9, 0.9, lambda f: 0.4 + 1.0 * (1 - f), core, zshift=6)
    anim = _orient_anim('animation.bc.wind_blade.fly', {'root': {'rotation': ORIENT, 'scale': ['1.0 + math.sin(q.life_time * 900.0) * 0.06', 1, 1]}})
    return g, 'emissive', anim


def dark_crescent():
    g = Geo('geometry.bc.dark_crescent', res=2, atlas_width=128, visible=(4, 3, (0, 0.5, 0)))
    g.bone('root', pivot=(0, 0, 0))
    g.bone('tilt', 'root', (0, 0, 0), rotation=[0, 0, 28])
    edge = tex.Energy(P['dark'][3:], alpha=135)
    core = tex.Material(P['dark'][:3], noise=0.2, edge=0, highlight=False)
    dep = lambda f: 0.8 + 5.6 * (1 - f) ** 0.7
    arc(g, 'tilt', 16, 74, 17, 2.4, dep, core, zshift=10)
    arc(g, 'tilt', 16, 70, 15, 3.0, lambda f: 0.5 + 1.4 * (1 - f) ** 0.7, edge, zshift=10, roff=lambda f: dep(f) / 2)
    arc(g, 'tilt', 16, 60, 11, 1.2, lambda f: 0.4 + 0.8 * (1 - f), edge, zshift=10, roff=lambda f: -dep(f) / 2)
    anim = _orient_anim('animation.bc.dark_crescent.fly')
    return g, 'emissive', anim


def anti_magic_slash():
    g = Geo('geometry.bc.anti_magic_slash', res=2, atlas_width=128, visible=(5, 3, (0, 0.5, 0)))
    g.bone('root', pivot=(0, 0, 0))
    g.bone('tilt', 'root', (0, 0, 0), rotation=[0, 0, -12])
    black = tex.Material(P['anti'][:3], noise=0.25, edge=0, highlight=False)
    red = tex.Energy(P['anti'][4:], alpha=140)
    dep = lambda f: 0.8 + 6.0 * (1 - f) ** 0.6
    arc(g, 'tilt', 19, 76, 19, 2.6, dep, black, zshift=12)
    arc(g, 'tilt', 19, 72, 17, 3.2, lambda f: 0.4 + 1.2 * (1 - f) ** 0.6, red, zshift=12, roff=lambda f: dep(f) / 2)
    # crackling shards
    rng = np.random.default_rng(7)
    for i in range(9):
        th = math.radians(rng.uniform(-60, 60))
        r = rng.uniform(13, 18)
        cx, cz = r * math.sin(th), -r * math.cos(th) + 12
        g.box('tilt', (cx, rng.uniform(-2, 2), cz), (0.6, 3.2, 0.6), red,
              rotation=[rng.uniform(-50, 50), 0, rng.uniform(-60, 60)], pivot=(cx, 0, cz))
    anim = _orient_anim('animation.bc.anti_magic_slash.fly', {'tilt': {'scale': ['1.0 + math.sin(q.life_time * 1200.0) * 0.04', 1, 1]}})
    return g, 'emissive', anim


# ----------------------------------------------------------------------------- orbs
def _orb(name, ramp_core, ramp_shell, size=5.0, spikes=0, tail=0, alpha=150, kind='emissive', core_dark=False):
    g = Geo(f'geometry.bc.{name}', res=2, atlas_width=64, visible=(2, 2, (0, 0, 0)))
    g.bone('root', pivot=(0, 0, 0))
    g.bone('spin', 'root', (0, 0, 0))
    core = tex.Material(ramp_core, noise=0.25, edge=0, highlight=False) if core_dark else tex.Energy(ramp_core, alpha=alpha)
    shell = tex.Energy(ramp_shell, alpha=alpha)
    g.box('spin', (0, 0, 0), (size, size, size), core)
    s2 = size * 1.25
    g.box('spin', (0, 0, 0), (s2, s2 * 0.7, s2 * 0.7), shell, rotation=[45, 0, 0], pivot=(0, 0, 0))
    g.box('spin', (0, 0, 0), (s2 * 0.7, s2, s2 * 0.7), shell, rotation=[0, 45, 0], pivot=(0, 0, 0))
    g.box('spin', (0, 0, 0), (s2 * 0.7, s2 * 0.7, s2), shell, rotation=[0, 0, 45], pivot=(0, 0, 0))
    for i in range(spikes):
        ang = i * 360 / spikes
        g.box('spin', (0, 0, 0), (1.0, size * 2.2, 1.0), shell, rotation=[ang, 0, 45 if i % 2 else -45], pivot=(0, 0, 0))
    for k in range(tail):
        s = size * (0.85 - k * 0.18)
        g.box('root', (0, 0, size * 0.6 + k * size * 0.55), (s, s, s), shell, rotation=[45 + k * 20, 45, 0], pivot=(0, 0, size * 0.6 + k * size * 0.55))
    anim = _orient_anim(f'animation.bc.{name}.fly', spin=['q.life_time * 540.0', 'q.life_time * 360.0', 0],
                        extra={'spin': {'rotation': ['q.life_time * 540.0', 'q.life_time * 360.0', 0],
                                        'scale': '1.0 + math.sin(q.life_time * 1100.0) * 0.08'}})
    return g, kind, anim


def fireball():
    return _orb('fireball', P['flame'][3:], P['flame'][1:5], size=5, tail=3)


def water_orb():
    return _orb('water_orb', P['water'][3:], P['water'][1:5], size=4.5, tail=2, alpha=175, kind='blend')


def dark_bolt():
    return _orb('dark_bolt', P['dark'][:3], P['dark'][3:], size=3.6, tail=2, core_dark=True)


def devil_orb():
    return _orb('devil_orb', ramp_core=tex.ramp('050000', '1a0204', '2e0508'), ramp_shell=P['anti'][3:], size=6, spikes=6, tail=2, core_dark=True)


# ----------------------------------------------------------------------------- spears & swords
def thunder_spear():
    g = Geo('geometry.bc.thunder_spear', res=2, atlas_width=64, visible=(2, 2, (0, 0, 0)))
    g.bone('root', pivot=(0, 0, 0))
    g.bone('bolts', 'root', (0, 0, 0))
    e = tex.Energy(P['lightning'], alpha=135)
    hot = tex.Energy(P['lightning'][3:], alpha=125)
    g.box('root', (0, 0, 2), (1.2, 1.2, 18), e)
    g.box('root', (0, 0, -8.5), (2.6, 2.6, 4.5), hot, rotation=[0, 0, 45], pivot=(0, 0, -8.5))
    g.box('root', (0, 0, -11.5), (1.4, 1.4, 2.5), hot, rotation=[0, 0, 45], pivot=(0, 0, -11.5))
    rng = np.random.default_rng(3)
    z = -7.0
    for i in range(8):
        a = math.radians(i * 137)
        ox, oy = math.cos(a) * 1.8, math.sin(a) * 1.8
        g.box('bolts', (ox, oy, z), (0.5, 0.5, 3.6), hot, rotation=[rng.uniform(-40, 40), rng.uniform(-40, 40), 0], pivot=(ox, oy, z))
        z += 2.2
    anim = _orient_anim('animation.bc.thunder_spear.fly', {'bolts': {'rotation': [0, 0, 'q.life_time * 2000.0'], 'scale': '1.0 + math.sin(q.life_time * 3000.0) * 0.15'}})
    return g, 'emissive', anim


def light_sword():
    g = Geo('geometry.bc.light_sword', res=2, atlas_width=64, visible=(2, 2, (0, 0, 0)))
    g.bone('root', pivot=(0, 0, 0))
    blade = tex.Energy(P['light'], alpha=128)
    gold = tex.Energy(P['gold'][3:], alpha=140)
    g.cube('root', (-1.3, -0.3, -9), (2.6, 0.6, 14), blade)
    g.cube('root', (-0.9, -0.3, -11.5), (1.8, 0.6, 2.5), blade)
    g.box('root', (0, 0, -12.2), (1.2, 0.6, 1.2), blade, rotation=[0, 45, 0], pivot=(0, 0, -12.2))
    g.box('root', (0, 0, 5.4), (7.5, 1.0, 1.4), gold)
    g.box('root', (0, 0, 7.8), (1.0, 1.0, 3.6), gold)
    g.box('root', (0, 0, 10.0), (1.6, 1.6, 1.6), gold, rotation=[45, 45, 0], pivot=(0, 0, 10.0))
    anim = _orient_anim('animation.bc.light_sword.fly')
    return g, 'emissive', anim


def ice_spear():
    g = Geo('geometry.bc.ice_spear', res=2, atlas_width=64, visible=(2, 2, (0, 0, 0)))
    g.bone('root', pivot=(0, 0, 0))
    ice = tex.Crystal(P['ice'], alpha=205)
    g.box('root', (0, 0, 3), (1.6, 1.6, 16), ice, rotation=[0, 0, 45], pivot=(0, 0, 3))
    g.box('root', (0, 0, -7), (3.4, 3.4, 5), ice, rotation=[0, 0, 45], pivot=(0, 0, -7))
    g.box('root', (0, 0, -10.5), (2.0, 2.0, 3), ice, rotation=[0, 0, 45], pivot=(0, 0, -10.5))
    g.box('root', (0, 0, -12.5), (0.9, 0.9, 1.6), ice, rotation=[0, 0, 45], pivot=(0, 0, -12.5))
    for sx in (-1, 1):
        g.box('root', (sx * 1.8, 0, -4.2), (0.9, 0.9, 3.8), ice, rotation=[0, sx * 28, 0], pivot=(sx * 1.8, 0, -4.2))
        g.box('root', (0, sx * 1.8, -4.2), (0.9, 0.9, 3.8), ice, rotation=[sx * -28, 0, 0], pivot=(0, sx * 1.8, -4.2))
    anim = _orient_anim('animation.bc.ice_spear.fly', {'root': {'rotation': ['-q.target_x_rotation', '-q.target_y_rotation', 'q.life_time * 360.0']}})
    return g, 'blend', anim


# ----------------------------------------------------------------------------- creatures of magic
def flame_lion():
    g = Geo('geometry.bc.flame_lion', res=2, atlas_width=128, visible=(4, 4, (0, 0, 0)))
    g.bone('root', pivot=(0, 0, 0))
    g.bone('head', 'root', (0, 0, 0))
    g.bone('jaw', 'head', (0, -2.5, -2))
    g.bone('mane', 'head', (0, 0, 1))
    fur = tex.Energy(P['flame'][2:], alpha=140)
    mane_m = tex.Energy(P['flame'][1:6], alpha=135)
    dark = tex.Material(tex.ramp('2a0300', '4a0800', '6a1000'), edge=0, highlight=False)

    def eyes(a, ctx):
        h, w = a.shape[:2]
        for ex in (int(w * 0.18), int(w * 0.66)):
            a[int(h * 0.3):int(h * 0.3) + 3, ex:ex + 4, :3] = rgb('fffbe0')[:3]
            a[int(h * 0.3):int(h * 0.3) + 3, ex:ex + 4, 3] = 128
            a[int(h * 0.3) - 1, ex - 1:ex + 5, :3] = rgb('6a1000')[:3]
        return a
    face = tex.Painted(fur, {'north': eyes})
    g.cube('head', (-5, -3.5, -5), (10, 9, 9), face)
    g.cube('head', (-3, -3.0, -9), (6, 4.5, 4.5), fur)            # muzzle
    g.cube('head', (-1.2, 0.6, -9.3), (2.4, 1.4, 1.2), dark)       # nose
    g.cube('head', (-4.5, 5.0, -2), (2.5, 2.5, 2), fur)            # ears
    g.cube('head', (2.0, 5.0, -2), (2.5, 2.5, 2), fur)
    g.cube('jaw', (-2.8, -5.2, -8.6), (5.6, 2.0, 4.2), fur)
    g.cube('jaw', (-2.4, -3.4, -8.4), (4.8, 0.6, 3.6), dark)       # mouth interior
    for sx in (-1.8, 1.0):                                          # fangs
        g.cube('head', (sx, -3.6, -8.9), (0.8, 1.2, 0.8), tex.Flat('fff6d6', alpha=140))
    deep = tex.Energy(tex.ramp('7a1004', 'b02206', 'e0480c', 'ff7a1a'), alpha=140)
    for i in range(18):
        ang = i * 20
        r = 8.0 + (i % 2) * 1.5
        cx, cy = math.sin(math.radians(ang)) * r, math.cos(math.radians(ang)) * r
        g.box('mane', (cx, cy, 1.0), (4.0, 9.0 + (i % 2) * 3, 3.5), deep if i % 2 else mane_m, rotation=[0, 0, -ang], pivot=(cx, cy, 1.0))
    for i in range(10):
        ang = i * 36 + 18
        r = 4.0
        cx, cy = math.sin(math.radians(ang)) * r, math.cos(math.radians(ang)) * r
        g.box('mane', (cx, cy, 4.5), (2.6, 6.0, 4.0), fur, rotation=[25, 0, -ang], pivot=(cx, cy, 4.5))
    g.bone('trail', 'root', (0, 0, 6))
    for k in range(4):
        s = 6.5 - k * 1.4
        g.box('trail', (0, 0.5 * k, 8 + k * 4.2), (s, s, 4.5), mane_m, rotation=[0, 0, 45], pivot=(0, 0.5 * k, 8 + k * 4.2))
    anim = {
        'animation.bc.flame_lion.fly': {
            'loop': True,
            'bones': {
                'root': {'rotation': ORIENT},
                'head': {'position': [0, 'math.sin(q.life_time * 400.0) * 0.6', 0]},
                'jaw': {'rotation': ['15.0 + math.sin(q.life_time * 700.0) * 12.0', 0, 0]},
                'mane': {'scale': '1.0 + math.sin(q.life_time * 1500.0) * 0.07', 'rotation': [0, 0, 'math.sin(q.life_time * 300.0) * 6.0']},
                'trail': {'rotation': [0, 0, 'q.life_time * 400.0'], 'scale': '1.0 + math.sin(q.life_time * 1200.0) * 0.12'},
            },
        }
    }
    return g, 'emissive', anim


def water_dragon():
    g = Geo('geometry.bc.water_dragon', res=2, atlas_width=128, visible=(8, 5, (0, 0.5, 0)))
    water = tex.Energy(P['water'][1:], alpha=150)
    bright = tex.Energy(P['water'][3:], alpha=135)

    def eyes(a, ctx):
        h, w = a.shape[:2]
        a[1:3, 1:3, :3] = 255
        a[1:3, w - 3:w - 1, :3] = 255
        return a
    g.bone('root', pivot=(0, 0, 0))
    g.bone('head', 'root', (0, 0, -2))
    g.cube('head', (-3, -2.5, -10), (6, 5, 8), tex.Painted(water, {'up': eyes}))
    g.cube('head', (-2.3, -2.2, -14), (4.6, 2.8, 4.2), water)          # snout
    g.cube('head', (-2.1, -4.2, -13.4), (4.2, 1.6, 7), bright)        # jaw
    for sx in (-1, 1):
        g.box('head', (sx * 2.2, 3.5, -4), (0.9, 0.9, 7), bright, rotation=[-30, sx * 15, 0], pivot=(sx * 2.2, 2.5, -6))
        g.box('head', (sx * 2.6, -1.0, -12.5), (0.4, 0.4, 6), bright, rotation=[15, sx * -35, 0], pivot=(sx * 2.4, -1.0, -13))
    parent = 'root'
    z = -2.0
    for k in range(7):
        s = 5.0 - k * 0.55
        name = f'seg{k}'
        g.bone(name, parent if k == 0 else f'seg{k - 1}', (0, 0, z))
        g.cube(name, (-s / 2, -s / 2, z), (s, s, 6.2), water)
        g.cube(name, (-0.2, s / 2, z + 1), (0.4, 2.2 - k * 0.2, 4.0), bright)  # dorsal fin
        z += 6.0
    g.cube('seg6', (-0.2, -2.5, z), (0.4, 5, 4), bright)  # tail fin
    bones = {'root': {'rotation': ORIENT}, 'head': {'rotation': ['math.sin(q.life_time * 500.0) * 6.0', 0, 0]}}
    for k in range(7):
        bones[f'seg{k}'] = {'rotation': [f'math.sin(q.life_time * 420.0 - {k * 55}) * 6.0', f'math.sin(q.life_time * 360.0 - {k * 50}) * 16.0', 0]}
    bones['root']['scale'] = 1.6
    return g, 'emissive', {'animation.bc.water_dragon.fly': {'loop': True, 'bones': bones}}


def tornado():
    g = Geo('geometry.bc.tornado', res=2, atlas_width=128, visible=(5, 4, (0, 1.5, 0)))
    g.bone('root', pivot=(0, 0, 0))
    wind = tex.Energy(P['wind'][1:], alpha=150)
    pale = tex.Energy(tex.ramp('9fe8c0', 'd8fbe6', 'ffffff'), alpha=120)
    anims = {}
    for i in range(9):
        y = 1 + i * 4.6
        R = 2.2 + i * 1.35
        name = f'ring{i}'
        g.bone(name, 'root', (0, y, 0))
        ring(g, name, R, 6 + i, 0.8, 2.6, wind if i % 2 == 0 else pale, y=y, phase=i * 17)
        anims[name] = {'rotation': [0, f'q.life_time * {720 + i * 90}.0', 0],
                       'position': [f'math.sin(q.life_time * 260.0 + {i * 40}) * {0.3 + i * 0.15}', 0,
                                    f'math.cos(q.life_time * 260.0 + {i * 40}) * {0.3 + i * 0.15}']}
    anims['root'] = {'scale': '1.0 + math.sin(q.life_time * 180.0) * 0.04'}
    return g, 'emissive', {'animation.bc.tornado.spin': {'loop': True, 'bones': anims}}


def black_hole():
    g = Geo('geometry.bc.black_hole', res=2, atlas_width=128, visible=(5, 5, (0, 1.0, 0)))
    g.bone('root', pivot=(0, 12, 0))
    g.bone('core', 'root', (0, 12, 0))
    g.bone('disk', 'root', (0, 12, 0), rotation=[18, 0, 0])
    g.bone('halo', 'root', (0, 12, 0), rotation=[-12, 0, 20])
    void = tex.Material(tex.ramp('000000', '05010a', '0b0414'), noise=0.2, edge=0, highlight=False)
    rim = tex.Energy(P['dark'][3:], alpha=135)
    g.box('core', (0, 12, 0), (9, 9, 9), void)
    g.box('core', (0, 12, 0), (10, 6.5, 6.5), void, rotation=[45, 0, 0], pivot=(0, 12, 0))
    g.box('core', (0, 12, 0), (6.5, 10, 6.5), void, rotation=[0, 45, 0], pivot=(0, 12, 0))
    g.box('core', (0, 12, 0), (6.5, 6.5, 10), void, rotation=[0, 0, 45], pivot=(0, 12, 0))
    ring(g, 'disk', 9.5, 18, 2.6, 0.6, rim, y=12)
    ring(g, 'disk', 13.0, 22, 1.4, 0.4, tex.Energy(P['dark'][2:], alpha=140), y=12, phase=8)
    ring(g, 'halo', 7.5, 14, 0.6, 0.6, tex.Energy(P['dark'][4:], alpha=125), y=12)
    anim = {'animation.bc.black_hole.spin': {'loop': True, 'bones': {
        'core': {'rotation': ['q.life_time * 90.0', 'q.life_time * 120.0', 0], 'scale': '1.0 + math.sin(q.life_time * 500.0) * 0.05'},
        'disk': {'rotation': [0, 'q.life_time * 400.0', 0]},
        'halo': {'rotation': [0, '-q.life_time * 600.0', 0]},
        'root': {'scale': 'math.min(q.life_time * 3.0, 1.0)'},
    }}}
    return g, 'emissive', anim


def ice_prison():
    g = Geo('geometry.bc.ice_prison', res=2, atlas_width=128, visible=(4, 4, (0, 1, 0)))
    g.bone('root', pivot=(0, 0, 0))
    ice = tex.Crystal(P['ice'], alpha=190)
    rng = np.random.default_rng(11)
    for i in range(10):
        ang = math.radians(i * 36 + rng.uniform(-8, 8))
        r = 8.5 + rng.uniform(-1, 1)
        x, z = math.sin(ang) * r, math.cos(ang) * r
        h = rng.uniform(16, 26)
        w = rng.uniform(3, 4.5)
        tilt_x, tilt_z = -math.cos(ang) * 14, math.sin(ang) * 14
        g.cube('root', (x - w / 2, 0, z - w / 2), (w, h, w), ice, rotation=[tilt_x, i * 23, tilt_z], pivot=(x, 0, z))
        g.box('root', (x, h, z), (w * 0.7, w * 0.7, w * 0.7), ice, rotation=[45 + tilt_x, i * 23, 45 + tilt_z], pivot=(x, 0, z))
    for i in range(6):
        ang = math.radians(i * 60 + 30)
        x, z = math.sin(ang) * 5, math.cos(ang) * 5
        g.box('root', (x, 2, z), (3, 4, 3), ice, rotation=[30, i * 40, 20], pivot=(x, 0, z))
    anim = {'animation.bc.ice_prison.form': {'loop': 'hold_on_last_frame', 'animation_length': 0.35, 'bones': {
        'root': {'scale': {'0.0': [1.0, 0.05, 1.0], '0.25': [1.05, 1.1, 1.05], '0.35': [1.0, 1.0, 1.0]}}}}}
    return g, 'blend', anim


ALL = {
    'wind_blade': wind_blade, 'dark_crescent': dark_crescent, 'anti_magic_slash': anti_magic_slash,
    'fireball': fireball, 'water_orb': water_orb, 'dark_bolt': dark_bolt, 'devil_orb': devil_orb,
    'thunder_spear': thunder_spear, 'light_sword': light_sword, 'ice_spear': ice_spear,
    'flame_lion': flame_lion, 'water_dragon': water_dragon, 'tornado': tornado,
    'black_hole': black_hole, 'ice_prison': ice_prison,
}
