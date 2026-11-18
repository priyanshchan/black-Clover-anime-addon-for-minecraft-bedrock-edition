"""v0.9.0: the rebuilt spell projectile (layered shapes, gradient tint textures, halo and element trails) and the new
full-body cast animations for the player. All designs are original."""
from __future__ import annotations

import math

import numpy as np

from .. import tex
from ..tex import rgb

ORIENT = ['-q.target_x_rotation', '-q.target_y_rotation', 0]
SHAPES = ['orb', 'shard', 'blade', 'needle', 'comet']
BAND = {'core': 0, 'hot': 1, 'body': 2, 'edge': 3, 'rock': 4}


# ======================================================================================
# the projectile: one 20x4 texture per tint, five bands (white-hot core, hot, body, edge, rock)
# ======================================================================================
def bolt_texture(hexcol):
    c = np.array(rgb(hexcol)[:3], dtype=np.float32)
    a = tex.new(4, 20)
    bands = [
        (np.array([255, 255, 255], np.float32) * 0.9 + c * 0.1, 110),   # core: emissive (alpha < 255 glows)
        (c + (255 - c) * 0.55, 120),                                      # hot
        (c * 1.0, 135),                                                   # body
        (c * 0.55, 170),                                                  # edge
        (np.array([46, 38, 36], np.float32), 255),                        # rock (comet core, unlit)
    ]
    for i, (col, alpha) in enumerate(bands):
        for x in range(4):
            shade = 1.0 + (0.12 if x in (1, 2) else -0.06)
            a[:, i * 4 + x, :3] = np.clip(col * shade, 0, 255)
            a[:, i * 4 + x, 3] = alpha
    # a few hot cracks in the rock band
    a[1, 17, :3] = np.clip(c + (255 - c) * 0.4, 0, 255)
    a[1, 17, 3] = 120
    a[2, 18, :3] = np.clip(c + (255 - c) * 0.4, 0, 255)
    a[2, 18, 3] = 120
    return a


def _uv(band):
    face = {'uv': [BAND[band] * 4, 0], 'uv_size': [4, 4]}
    return {f: dict(face) for f in ('north', 'south', 'east', 'west', 'up', 'down')}


def _cube(center, size, band, rot=None, inflate=0.0):
    c = {'origin': [round(center[i] - size[i] / 2, 4) for i in range(3)], 'size': [round(v, 4) for v in size], 'uv': _uv(band)}
    if rot:
        c['rotation'] = list(rot)
        c['pivot'] = [round(v, 4) for v in center]
    if inflate:
        c['inflate'] = inflate
    return c


def _ring(r, thick, n, band, plane='xy', z=0.0):
    out = []
    for i in range(n):
        a = i / n * math.tau
        seg = math.tau * r / n * 1.15
        if plane == 'xy':
            out.append(_cube((math.cos(a) * r, math.sin(a) * r, z), (seg, thick, thick), band, (0, 0, -(math.degrees(a) + 90))))
        else:  # xz
            out.append(_cube((math.cos(a) * r, z, math.sin(a) * r), (seg, thick, thick), band, (0, -math.degrees(a) - 90, 0)))
    return out


def _tail(length, start, width, bands=('hot', 'body', 'edge')):
    out = []
    n = len(bands) + 1
    for i in range(n):
        f = i / n
        w = width * (1 - f * 0.8)
        seg = length / n
        out.append(_cube((0, 0, start + seg * (i + 0.5)), (w, w, seg * 1.05), bands[min(i, len(bands) - 1)], (0, 0, 45)))
    return out


def _shape(kind):
    bones = {k: {'name': k, 'parent': 'root', 'pivot': [0, 0, 0], 'cubes': []} for k in ('spin', 'ring_a', 'ring_b', 'tail', 'core')}
    root = {'name': 'root', 'pivot': [0, 0, 0], 'cubes': []}
    if kind == 'orb':
        bones['core']['cubes'] += [_cube((0, 0, 0), (2.4, 2.4, 2.4), 'core', (45, 45, 0)), _cube((0, 0, 0), (2.0, 2.0, 2.0), 'core', (0, 45, 45))]
        bones['spin']['cubes'] += [_cube((0, 0, 0), (4.2, 4.2, 1.2), 'hot', (0, 0, 45)), _cube((0, 0, 0), (4.2, 1.2, 4.2), 'hot', (0, 45, 0)),
                                   _cube((0, 0, 0), (1.2, 4.2, 4.2), 'hot', (45, 0, 0)), _cube((0, 0, 0), (3.6, 3.6, 3.6), 'body', (30, 30, 30))]
        bones['ring_a']['cubes'] += _ring(4.6, 0.45, 12, 'body', 'xy')
        bones['ring_b']['cubes'] += _ring(5.4, 0.35, 14, 'hot', 'xz')
        bones['tail']['cubes'] += _tail(8.0, 2.4, 2.6)
    elif kind == 'shard':
        bones['core']['cubes'] += [_cube((0, 0, -1), (1.2, 1.2, 9.0), 'core', (0, 0, 45))]
        bones['spin']['cubes'] += [_cube((0, 0, -1), (2.6, 2.6, 7.0), 'hot', (0, 0, 45)), _cube((0, 0, -5.4), (1.6, 1.6, 2.4), 'body', (0, 0, 45)),
                                   _cube((0, 0, -6.8), (0.8, 0.8, 1.4), 'core', (0, 0, 45)),
                                   _cube((0, 0, 1.2), (0.5, 5.2, 4.2), 'body'), _cube((0, 0, 1.2), (5.2, 0.5, 4.2), 'body')]
        bones['ring_a']['cubes'] += _ring(2.8, 0.3, 8, 'hot', 'xy', z=-2.0)
        bones['tail']['cubes'] += _tail(6.0, 3.2, 1.6)
    elif kind == 'blade':
        for i in range(13):
            th = -74 + 148 * (i + 0.5) / 13
            t = math.radians(th)
            R = 6.4
            f = abs(th) / 74
            seg = 2 * math.radians(74) * R / 13 * 1.25
            bones['spin']['cubes'].append(_cube((R * math.sin(t), 0, -R * math.cos(t) + 4), (seg, 0.7, 0.5 + 2.8 * (1 - f)), 'body' if f > 0.5 else 'hot', (0, -th, 0)))
            bones['core']['cubes'].append(_cube((R * 1.02 * math.sin(t), 0, -R * 1.02 * math.cos(t) + 4), (seg, 0.4, 0.4), 'core', (0, -th, 0)))
        bones['spin']['cubes'].append(_cube((0, 0, -1.4), (3.4, 0.9, 1.4), 'hot'))
        bones['tail']['cubes'] += [_cube((0, 0, 3.0), (2.2, 0.4, 3.2), 'body'), _cube((0, 0, 5.2), (1.2, 0.3, 2.0), 'edge')]
    elif kind == 'needle':
        bones['core']['cubes'] += [_cube((0, 0, 0), (0.7, 0.7, 12.0), 'core', (0, 0, 45))]
        bones['spin']['cubes'] += [_cube((0, 0, 0), (1.3, 1.3, 10.0), 'hot', (0, 0, 45)), _cube((0, 0, -6.6), (1.8, 1.8, 2.0), 'body', (0, 0, 45)),
                                   _cube((0, 0, -8.0), (0.8, 0.8, 1.4), 'core', (0, 0, 45))]
        for k in range(10):
            a = k * 72
            bones['ring_a']['cubes'].append(_cube((math.cos(math.radians(a)) * 1.3, math.sin(math.radians(a)) * 1.3, -4 + k * 1.0), (0.45, 0.45, 0.9), 'body'))
        bones['tail']['cubes'] += _tail(5.0, 5.4, 1.0, ('body', 'edge'))
    else:  # comet: a burning rock with a long flame tail
        bones['core']['cubes'] += [_cube((0, 0, 0), (5.2, 5.2, 5.2), 'rock', (20, 35, 10)), _cube((0, 0, 0), (4.6, 4.6, 4.6), 'rock', (60, 10, 40)),
                                   _cube((0, 0, 0), (3.0, 3.0, 3.0), 'core', (45, 45, 0))]
        bones['spin']['cubes'] += [_cube((0, 0, 0.6), (6.6, 6.6, 0.9), 'hot', (0, 0, 45)), _cube((0, 0, 0.6), (6.6, 0.9, 6.6), 'hot', (0, 45, 0)),
                                   _cube((0, 0, 0.6), (0.9, 6.6, 6.6), 'body', (45, 0, 0))]
        bones['ring_b']['cubes'] += _ring(5.0, 0.6, 10, 'hot', 'xy', z=1.0)
        bones['tail']['cubes'] += _tail(16.0, 2.5, 5.4, ('hot', 'hot', 'body', 'edge'))
    return {
        'description': {'identifier': f'geometry.bc.bolt_{kind}', 'texture_width': 20, 'texture_height': 4,
                        'visible_bounds_width': 3, 'visible_bounds_height': 3, 'visible_bounds_offset': [0, 0, 0]},
        'bones': [root, *bones.values()],
    }


def bolt_geometry_file():
    return {'format_version': '1.16.0', 'minecraft:geometry': [_shape(k) for k in SHAPES]}


def bolt_animations():
    return {'animation.bc.mana_bolt.fly': {'loop': True, 'bones': {
        'root': {'rotation': ORIENT},
        'core': {'scale': '1.0 + math.sin(q.life_time * 1800.0) * 0.12'},
        'spin': {'rotation': [0, 0, 'q.life_time * 540.0'], 'scale': '1.0 + math.sin(q.life_time * 1100.0) * 0.07'},
        'ring_a': {'rotation': [0, 0, 'q.life_time * -900.0']},
        'ring_b': {'rotation': [0, 'q.life_time * 700.0', 0]},
        'tail': {'scale': [1, 1, '1.0 + math.sin(q.life_time * 900.0) * 0.18']},
    }}}


# element flavour of each tint, for the trail (index into vfx9.FLAVORS)
FLAVOR_OF_KIT = {
    'flame': 'fire', 'magma': 'fire', 'devil': 'fire', 'ash': 'earth', 'water': 'water', 'blood': 'water', 'bubble': 'bubble', 'acid': 'bubble',
    'poison': 'bubble', 'mist': 'wind', 'cotton': 'wind', 'smoke': 'earth', 'ice': 'ice', 'crystal': 'star', 'glass': 'star', 'mirror': 'star',
    'lightning': 'spark', 'steel': 'spark', 'metal': 'spark', 'gold': 'spark', 'gun': 'spark', 'light': 'star', 'star': 'star', 'moon': 'star',
    'dark': 'void', 'gravity': 'void', 'ink': 'void', 'anti': 'void', 'spatial': 'void', 'time': 'energy', 'rune': 'energy', 'paper': 'energy',
    'sound': 'energy', 'spirit': 'wind', 'beast': 'energy', 'earth': 'earth', 'sand': 'earth', 'bone': 'earth', 'leaf': 'leaf', 'thorn': 'leaf',
    'wind': 'wind',
}
# keep in step with core/vfx.js FRUIT_KIT
FRUIT_KIT = {
    'ember': 'flame', 'stone': 'earth', 'gravity': 'gravity', 'shadow': 'dark', 'bloom': 'leaf', 'quicksilver': 'metal', 'frost': 'ice',
    'barrier': 'crystal', 'wolf': 'beast', 'hawk': 'wind', 'lava': 'magma', 'ash': 'ash', 'prism': 'light', 'bounce': 'bubble', 'blast': 'flame',
    'acid': 'acid', 'lodestone': 'metal', 'cloud': 'cotton', 'ink': 'ink', 'bear': 'beast', 'tiger': 'beast', 'wyvern': 'flame', 'spore': 'poison',
    'thread': 'paper', 'slime': 'bubble', 'chain': 'steel', 'lion': 'flame', 'shark': 'water', 'phoenix': 'flame', 'spider': 'dark',
    'spark': 'lightning', 'echo': 'sound', 'sand': 'sand', 'gale': 'wind',
}
ATTR_KIT = {'plant': 'leaf', 'storm': 'lightning', 'blossom': 'leaf', 'coral': 'crystal', 'dream': 'spirit'}


def flavor_of(tint_key, flavors):
    kind, ident = tint_key.split(':')
    kit = FRUIT_KIT.get(ident, 'wind') if kind == 'f' else ATTR_KIT.get(ident, ident)
    return flavors.index(FLAVOR_OF_KIT.get(kit, 'energy'))


def trail_script(tints, flavors):
    """Molang: the bolt's tint index -> v.tr/v.tg/v.tb (colour), v.fk (element flavour) and v.hs (halo size)."""
    chans = []
    for ci, name in enumerate(('tr', 'tg', 'tb')):
        expr = '1.0'
        for i, (_, hexc) in reversed(list(enumerate(tints))):
            expr = f'(v.tt == {i} ? {round(int(hexc[ci * 2:ci * 2 + 2], 16) / 255, 3)} : {expr})'
        chans.append(f'v.{name} = {expr};')
    fk = '0'
    for i, (key, _) in reversed(list(enumerate(tints))):
        f = flavor_of(key, flavors)
        if f:
            fk = f'(v.tt == {i} ? {f} : {fk})'
    return ("v.tt = q.property('bc:tint'); " + ' '.join(chans) + f' v.fk = {fk};'
            " v.hs = (1.0 + q.property('bc:size') * 0.55) * (q.property('bc:shape') == 4 ? 2.0 : 1.0);")


# ======================================================================================
# player cast animations: anticipation, a strike with overshoot, follow-through and a settle, on the whole body
# ======================================================================================
def _kf(frames, smooth=True):
    """{time: [x, y, z]} -> Bedrock keyframes (catmull-rom where smooth)."""
    out = {}
    for t, v in sorted(frames.items()):
        key = f'{t:.2f}'.rstrip('0').rstrip('.') if t else '0.0'
        out[key] = {'post': v, 'lerp_mode': 'catmullrom'} if smooth else v
    return out


def player_v9_animations(k):
    """`k(x)` zeroes an expression in first person (the body is not drawn there)."""
    def R(frames, smooth=True):
        return {'rotation': _kf({t: [k(v[0]) if v[0] else 0, k(v[1]) if v[1] else 0, k(v[2]) if v[2] else 0] for t, v in frames.items()}, smooth)}

    def FP(frames):
        """First-person arm nudge (position, only in first person)."""
        return {'position': _kf({t: [f'({v[0]}) * v.is_first_person', f'({v[1]}) * v.is_first_person', f'({v[2]}) * v.is_first_person']
                                 for t, v in frames.items()})}

    Z = [0, 0, 0]
    tremble = 'math.sin(q.anim_time * 3600.0) * 1.6'
    A = {}

    def anim(name, length, bones):
        A[f'animation.bc.player.{name}'] = {'animation_length': length, 'bones': bones}

    # one-handed thrust (bolts, single shots)
    anim('cast_forward', 0.6, {
        'rightArm': {**R({0: Z, 0.09: [-40, 28, 12], 0.16: [-104, -10, 0], 0.26: [-92, -5, 0], 0.42: [-86, -2, 0], 0.6: Z}),
                     **FP({0: Z, 0.09: [0, -0.5, 1.6], 0.16: [0, 0.4, -3.2], 0.3: [0, 0.2, -1.6], 0.6: Z})},
        'leftArm': R({0: Z, 0.09: [-25, 0, -10], 0.16: [12, 0, -18], 0.42: [6, 0, -12], 0.6: Z}),
        'body': R({0: Z, 0.09: [0, 24, 0], 0.16: [5, -20, 0], 0.3: [3, -14, 0], 0.6: Z}),
        'head': R({0: Z, 0.09: [0, -14, 0], 0.16: [0, 12, 0], 0.6: Z}),
        'rightLeg': R({0: Z, 0.16: [-14, 0, 0], 0.42: [-8, 0, 0], 0.6: Z}),
        'leftLeg': R({0: Z, 0.16: [12, 0, 0], 0.42: [6, 0, 0], 0.6: Z}),
    })
    # two-handed push (barrages, prisons, fruit beams)
    anim('cast_push', 0.7, {
        'rightArm': {**R({0: Z, 0.12: [-45, 35, 0], 0.2: [-98, 8, 0], 0.5: [-92, 6, 0], 0.7: Z}), **FP({0: Z, 0.12: [0, 0, 1.4], 0.2: [0, 0, -2.6], 0.7: Z})},
        'leftArm': {**R({0: Z, 0.12: [-45, -35, 0], 0.2: [-98, -8, 0], 0.5: [-92, -6, 0], 0.7: Z}), **FP({0: Z, 0.12: [0, 0, 1.4], 0.2: [0, 0, -2.6], 0.7: Z})},
        'body': R({0: Z, 0.12: [-8, 0, 0], 0.2: [10, 0, 0], 0.5: [6, 0, 0], 0.7: Z}),
        'rightLeg': R({0: Z, 0.2: [-12, 0, 4], 0.5: [-8, 0, 4], 0.7: Z}),
        'leftLeg': R({0: Z, 0.2: [12, 0, -4], 0.5: [8, 0, -4], 0.7: Z}),
    })
    # a sustained two-handed channel (beams, zones, vortices) with a trembling hold
    anim('cast_channel', 1.1, {
        'rightArm': {'rotation': _kf({0: Z, 0.12: [k(-96), k(14), 0], 0.85: [k(f'-90 + {tremble}'), k(10), 0], 1.1: Z})},
        'leftArm': {'rotation': _kf({0: Z, 0.12: [k(-96), k(-14), 0], 0.85: [k(f'-90 - {tremble}'), k(-10), 0], 1.1: Z})},
        'body': R({0: Z, 0.12: [10, 0, 0], 0.85: [8, 0, 0], 1.1: Z}),
        'head': R({0: Z, 0.12: [-6, 0, 0], 1.1: Z}),
        'rightLeg': R({0: Z, 0.12: [-14, 0, 8], 0.85: [-12, 0, 8], 1.1: Z}),
        'leftLeg': R({0: Z, 0.12: [14, 0, -8], 0.85: [12, 0, -8], 1.1: Z}),
    })
    # arms flung to the sky (rains, meteors, strikes, rewinds)
    anim('cast_raise', 0.95, {
        'rightArm': R({0: Z, 0.1: [25, 0, 12], 0.24: [-178, 0, 26], 0.32: [-168, 0, 20], 0.7: [-162, 0, 18], 0.95: Z}),
        'leftArm': R({0: Z, 0.1: [25, 0, -12], 0.24: [-178, 0, -26], 0.32: [-168, 0, -20], 0.7: [-162, 0, -18], 0.95: Z}),
        'body': R({0: Z, 0.1: [12, 0, 0], 0.24: [-10, 0, 0], 0.7: [-6, 0, 0], 0.95: Z}),
        'head': R({0: Z, 0.1: [10, 0, 0], 0.24: [-22, 0, 0], 0.7: [-16, 0, 0], 0.95: Z}),
        'rightLeg': R({0: Z, 0.1: [-10, 0, 0], 0.24: [4, 0, 6], 0.95: Z}),
        'leftLeg': R({0: Z, 0.1: [10, 0, 0], 0.24: [-4, 0, -6], 0.95: Z}),
    })
    # overhead then down into the ground (novas, dives, waves in every direction)
    anim('cast_slam', 0.8, {
        'rightArm': R({0: Z, 0.2: [-178, 0, 14], 0.32: [-22, 0, 8], 0.5: [-30, 0, 10], 0.8: Z}),
        'leftArm': R({0: Z, 0.2: [-178, 0, -14], 0.32: [-22, 0, -8], 0.5: [-30, 0, -10], 0.8: Z}),
        'body': R({0: Z, 0.2: [-14, 0, 0], 0.32: [30, 0, 0], 0.5: [24, 0, 0], 0.8: Z}),
        'head': R({0: Z, 0.2: [-18, 0, 0], 0.32: [-14, 0, 0], 0.8: Z}),
        'rightLeg': R({0: Z, 0.2: [8, 0, 0], 0.32: [-24, 0, 6], 0.5: [-20, 0, 6], 0.8: Z}),
        'leftLeg': R({0: Z, 0.2: [-8, 0, 0], 0.32: [24, 0, -6], 0.5: [20, 0, -6], 0.8: Z}),
    })
    # a wide horizontal sweep with the whole torso (waves)
    anim('cast_sweep', 0.65, {
        'rightArm': {**R({0: Z, 0.1: [-88, 80, 0], 0.22: [-92, -62, 0], 0.32: [-86, -72, 0], 0.65: Z}), **FP({0: Z, 0.1: [-2, 0, 0], 0.22: [2, 0, -2], 0.65: Z})},
        'leftArm': R({0: Z, 0.1: [-20, 0, -24], 0.22: [-40, -20, 0], 0.65: Z}),
        'body': R({0: Z, 0.1: [0, 38, 0], 0.22: [4, -36, 0], 0.32: [4, -42, 0], 0.65: Z}),
        'head': R({0: Z, 0.1: [0, -20, 0], 0.22: [0, 18, 0], 0.65: Z}),
        'rightLeg': R({0: Z, 0.22: [-10, 0, 0], 0.65: Z}),
        'leftLeg': R({0: Z, 0.22: [10, 0, 0], 0.65: Z}),
    })
    # arms out, twisting (bolts in every direction)
    anim('cast_spin', 0.7, {
        'rightArm': R({0: Z, 0.12: [-10, 0, 85], 0.4: [-10, 0, 90], 0.7: Z}),
        'leftArm': R({0: Z, 0.12: [-10, 0, -85], 0.4: [-10, 0, -90], 0.7: Z}),
        'body': R({0: Z, 0.12: [0, -40, 0], 0.28: [0, 40, 0], 0.42: [0, -15, 0], 0.7: Z}),
        'head': R({0: Z, 0.28: [-10, 0, 0], 0.7: Z}),
    })
    # hands together, then spread wide and high (summons, time stops)
    anim('cast_summon', 1.0, {
        'rightArm': R({0: Z, 0.15: [-82, 22, 0], 0.4: [-150, 0, 60], 0.75: [-145, 0, 55], 1.0: Z}),
        'leftArm': R({0: Z, 0.15: [-82, -22, 0], 0.4: [-150, 0, -60], 0.75: [-145, 0, -55], 1.0: Z}),
        'body': R({0: Z, 0.15: [6, 0, 0], 0.4: [-10, 0, 0], 1.0: Z}),
        'head': R({0: Z, 0.4: [-18, 0, 0], 1.0: Z}),
    })
    # power-up: fists down, back arched, a trembling roar of power (buffs)
    anim('cast_buff', 0.85, {
        'rightArm': {'rotation': _kf({0: Z, 0.12: [k(-35), 0, k(-10)], 0.3: [k(10), 0, k(38)], 0.65: [k(f'8 + {tremble}'), 0, k(34)], 0.85: Z})},
        'leftArm': {'rotation': _kf({0: Z, 0.12: [k(-35), 0, k(10)], 0.3: [k(10), 0, k(-38)], 0.65: [k(f'8 - {tremble}'), 0, k(-34)], 0.85: Z})},
        'body': R({0: Z, 0.12: [14, 0, 0], 0.3: [-14, 0, 0], 0.65: [-10, 0, 0], 0.85: Z}),
        'head': R({0: Z, 0.12: [12, 0, 0], 0.3: [-24, 0, 0], 0.65: [-18, 0, 0], 0.85: Z}),
        'rightLeg': R({0: Z, 0.12: [-8, 0, 10], 0.65: [-6, 0, 10], 0.85: Z}),
        'leftLeg': R({0: Z, 0.12: [8, 0, -10], 0.65: [6, 0, -10], 0.85: Z}),
    })
    # cupped hands rising open (healing)
    anim('cast_heal', 0.95, {
        'rightArm': R({0: Z, 0.15: [-62, 26, 0], 0.45: [-122, 0, 32], 0.75: [-118, 0, 30], 0.95: Z}),
        'leftArm': R({0: Z, 0.15: [-62, -26, 0], 0.45: [-122, 0, -32], 0.75: [-118, 0, -30], 0.95: Z}),
        'body': R({0: Z, 0.15: [8, 0, 0], 0.45: [-6, 0, 0], 0.95: Z}),
        'head': R({0: Z, 0.15: [10, 0, 0], 0.45: [-14, 0, 0], 0.95: Z}),
    })
    # a forward lunge (dashes, blinks)
    anim('cast_dash', 0.55, {
        'rightArm': R({0: Z, 0.08: [42, 0, 14], 0.35: [36, 0, 12], 0.55: Z}),
        'leftArm': R({0: Z, 0.08: [42, 0, -14], 0.35: [36, 0, -12], 0.55: Z}),
        'body': R({0: Z, 0.08: [28, 0, 0], 0.35: [24, 0, 0], 0.55: Z}),
        'head': R({0: Z, 0.08: [-22, 0, 0], 0.55: Z}),
        'rightLeg': R({0: Z, 0.08: [-38, 0, 0], 0.35: [-30, 0, 0], 0.55: Z}),
        'leftLeg': R({0: Z, 0.08: [34, 0, 0], 0.35: [28, 0, 0], 0.55: Z}),
    })
    # Abyss Fruit users fight like brawlers and beasts
    anim('fruit_punch', 0.48, {
        'rightArm': {**R({0: Z, 0.08: [-55, 34, 8], 0.14: [-96, -6, 0], 0.24: [-90, -4, 0], 0.48: Z}), **FP({0: Z, 0.08: [0, -0.4, 1.8], 0.14: [0, 0.4, -3.6], 0.28: [0, 0.2, -1.2], 0.48: Z})},
        'leftArm': R({0: Z, 0.08: [-62, -32, 0], 0.14: [-50, -28, 0], 0.48: Z}),
        'body': R({0: Z, 0.08: [0, 28, 0], 0.14: [8, -30, 0], 0.26: [6, -24, 0], 0.48: Z}),
        'head': R({0: Z, 0.08: [0, -16, 0], 0.14: [0, 16, 0], 0.48: Z}),
        'rightLeg': R({0: Z, 0.14: [-18, 0, 0], 0.48: Z}),
        'leftLeg': R({0: Z, 0.14: [16, 0, 0], 0.48: Z}),
    })
    anim('fruit_stomp', 0.75, {
        'rightLeg': R({0: Z, 0.18: [-62, 0, 6], 0.28: [8, 0, 4], 0.5: [6, 0, 4], 0.75: Z}),
        'leftLeg': R({0: Z, 0.18: [6, 0, 0], 0.28: [-6, 0, 0], 0.75: Z}),
        'body': R({0: Z, 0.18: [-10, 0, 0], 0.28: [16, 0, 0], 0.5: [12, 0, 0], 0.75: Z}),
        'rightArm': R({0: Z, 0.18: [-30, 0, 40], 0.28: [-10, 0, 52], 0.75: Z}),
        'leftArm': R({0: Z, 0.18: [-30, 0, -40], 0.28: [-10, 0, -52], 0.75: Z}),
        'head': R({0: Z, 0.28: [12, 0, 0], 0.75: Z}),
    })
    anim('fruit_roar', 0.85, {
        'body': {'rotation': _kf({0: Z, 0.14: [k(10), 0, 0], 0.3: [k(-16), 0, 0], 0.65: [k(f'-14 + {tremble}'), 0, 0], 0.85: Z})},
        'head': R({0: Z, 0.14: [14, 0, 0], 0.3: [-30, 0, 0], 0.65: [-26, 0, 0], 0.85: Z}),
        'rightArm': R({0: Z, 0.14: [-30, 0, 10], 0.3: [32, 0, 44], 0.65: [28, 0, 40], 0.85: Z}),
        'leftArm': R({0: Z, 0.14: [-30, 0, -10], 0.3: [32, 0, -44], 0.65: [28, 0, -40], 0.85: Z}),
        'rightLeg': R({0: Z, 0.3: [-10, 0, 10], 0.85: Z}),
        'leftLeg': R({0: Z, 0.3: [10, 0, -10], 0.85: Z}),
    })
    return A
