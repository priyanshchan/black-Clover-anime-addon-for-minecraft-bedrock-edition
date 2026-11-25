"""v1.3.0 models: devil hosts (one look per devil, with the parts that show as their union deepens), the Crowned Vessel,
the union sprites for players (horns and wings) and the new icons. All designs are original."""
from __future__ import annotations

import math

import numpy as np

from .. import tex
from ..geo import Geo
from ..tex import P, rgb
from .mobs import _veins
from .sea import SKIN, _humanoid_bones, humanoid_animations
from .v11 import _icon

# which bones belong to which union stage (the render controller hides them below it)
HALF_BONES = ['horns', 'devilArm', 'marks']
FULL_BONES = ['rightWing', 'rightWingTip', 'leftWing', 'leftWingTip', 'tail0', 'tail1', 'tail2', 'tail3']
VESSEL_HALF = ['horns', 'devilArm', 'devilArmL', 'marks']
VESSEL_FULL = FULL_BONES + ['halo']


def _r(*h):
    return tex.ramp(*h)


def _glow(color, alpha=120):
    c = [int(v) for v in rgb(color)[:3]]
    hx = lambda t: ''.join(f'{max(0, min(255, int(v))):02x}' for v in t)   # noqa: E731
    lo = hx(v * 0.45 for v in c)
    hi = hx(v * 0.5 + 128 for v in c)
    return tex.Energy(tex.ramp(lo, hx(c), hi, 'fffaf0'), alpha=alpha)


def _host_face(eye):
    """A pale face with the devil's eyes - they glow even before the union shows."""
    e = np.array(rgb(eye)[:3], np.float32)

    def fn(a, ctx):
        h, w = a.shape[:2]
        ey = int(h * 0.46)
        for ex in (int(w * 0.18), int(w * 0.6)):
            a[ey:ey + 2, ex:ex + int(w * 0.22), :3] = e
            a[ey:ey + 2, ex:ex + int(w * 0.22), 3] = 140
        a[ey - 2, int(w * 0.15):int(w * 0.42), :3] *= 0.45
        a[ey - 2, int(w * 0.58):int(w * 0.85), :3] *= 0.45
        a[int(h * 0.78), int(w * 0.32):int(w * 0.68), :3] = rgb('2a0a0a')[:3]
        return a
    return fn


def _ragged(a, ctx):
    """Torn hems and scorch marks on a host's coat."""
    h, w = a.shape[:2]
    rng = np.random.default_rng(ctx.seed + 3)
    for x in range(w):
        cut = int(rng.integers(0, max(1, h // 6)))
        if cut:
            a[h - cut:, x, :3] *= 0.55
    return a


def _horns(g, style, horn, glow):
    """Each devil marks its host with its own horns."""
    for sx in (-1, 1):
        if style == 'vharog':        # thick horns that hook forward like a bull's
            g.box('horns', (sx * 4.3, 31.2, -0.5), (2.2, 2.2, 2.2), horn, rotation=[0, 0, sx * -20], pivot=(sx * 4, 31, -0.5))
            g.box('horns', (sx * 5.4, 33.2, -1.2), (1.8, 2.6, 1.8), horn, rotation=[-25, 0, sx * -10], pivot=(sx * 5.2, 32.2, -1))
            g.box('horns', (sx * 5.6, 35.2, -2.6), (1.2, 2.2, 1.2), horn, rotation=[-55, 0, 0], pivot=(sx * 5.6, 34.4, -2.2))
            g.box('horns', (sx * 5.6, 36.0, -3.9), (0.8, 1.4, 0.8), glow, rotation=[-70, 0, 0], pivot=(sx * 5.6, 35.6, -3.4))
        elif style == 'sileth':      # long, thin horns swept straight back, like frozen antlers
            for k in range(4):
                g.box('horns', (sx * 3.2, 32.5 + k * 0.9, 1 + k * 1.8), (1.0, 1.0, 2.2), horn, rotation=[20, sx * 10, 0], pivot=(sx * 3.2, 32 + k * 0.9, k * 1.8))
            g.box('horns', (sx * 3.6, 35.4, 3.4), (0.6, 2.4, 0.6), glow, rotation=[15, 0, sx * -20], pivot=(sx * 3.6, 34.4, 3.4))
            g.box('horns', (sx * 3.4, 33.6, 7.6), (0.7, 0.7, 1.8), glow, rotation=[25, 0, 0], pivot=(sx * 3.4, 33.4, 7))
        elif style == 'morvane':     # a hollow crown: a ring of short horns
            for k in range(3):
                x = sx * (1.2 + k * 1.4)
                hgt = 3.6 - k * 0.8
                g.box('horns', (x, 32 + hgt / 2, -2.2 + k * 0.6), (0.9, hgt, 0.9), horn, rotation=[-8, 0, sx * (8 + k * 12)], pivot=(x, 32, -2))
            g.box('horns', (sx * 4.3, 32.6, 1.5), (0.9, 2.4, 0.9), horn, rotation=[10, 0, sx * 25], pivot=(sx * 4.2, 32, 1.5))
        elif style == 'ghorza':      # curled ram's horns and a jagged tusk
            g.box('horns', (sx * 4.6, 31.4, 0.5), (1.8, 2.4, 2.4), horn, rotation=[0, 0, sx * -15], pivot=(sx * 4.4, 30.5, 0.5))
            g.box('horns', (sx * 5.6, 31.0, 2.6), (1.6, 2.2, 2.2), horn, rotation=[40, 0, sx * -10], pivot=(sx * 5.4, 31, 2))
            g.box('horns', (sx * 5.8, 29.0, 2.6), (1.4, 2.0, 1.8), horn, rotation=[80, 0, 0], pivot=(sx * 5.8, 29.6, 2.4))
            g.box('horns', (sx * 5.6, 28.0, 0.8), (1.0, 1.4, 1.2), glow, rotation=[120, 0, 0], pivot=(sx * 5.6, 28.4, 1.2))
        else:                        # lesser devils: two short stubby spikes
            g.box('horns', (sx * 2.6, 32.6, -1), (1.2, 2.2, 1.2), horn, rotation=[-15, 0, sx * -18], pivot=(sx * 2.6, 32, -1))


def _wings(g, side, sx, membrane, wing_bone, horn, span=1.0, z=2.2, y=22.5):
    wx0 = 1 if sx > 0 else -1 - 12 * span
    g.cube(f'{side}Wing', (wx0, y, z), (12 * span, 1.6, 1.6), wing_bone)
    g.cube(f'{side}Wing', (wx0, y - 12 * span, z + 0.7), (12 * span, 12 * span, 0), membrane)
    tx0 = 1 + 12 * span if sx > 0 else -1 - 22 * span
    g.cube(f'{side}WingTip', (tx0, y + 0.2, z + 0.2), (10 * span, 1.2, 1.2), wing_bone)
    g.cube(f'{side}WingTip', (tx0, y - 9.5 * span, z + 0.8), (10 * span, 9.5 * span, 0), membrane)
    g.box(f'{side}WingTip', (sx * (1 + 22 * span), y + 2.4, z + 0.6), (0.9, 3.4, 0.9), horn, rotation=[0, 0, sx * 25], pivot=(sx * (1 + 22 * span), y + 0.8, z + 0.6))


def _membrane_ribs(a, ctx):
    h, w = a.shape[:2]
    for k in range(1, 4):
        x0 = int(w * k / 4)
        a[:, max(0, x0 - 1):x0, :3] *= 0.55
    a[-2:, :, :3] *= 0.6
    return a


def devil_host_geo(devil, upto=2):
    """A devil host: a mage in a tattered coat of the devil's colours. At 50% union horns, a devil's arm and glowing
    marks break through; at 100% wings and a tail. `upto` is only for previews (the game hides stages by property)."""
    from ..data import DEVILS
    D = DEVILS[devil]
    g = Geo(f'geometry.bc.devil_host_{devil}', res=2, atlas_width=128, visible=(4, 3, (0, 1.4, 0)), seed=1301 + list(DEVILS).index(devil))
    _humanoid_bones(g)
    skin = tex.Material(SKIN, noise=0.08, edge=0.85)
    devil_skin = tex.Painted(tex.Material(_r(*D['skin']), noise=0.16, edge=0.7), {'*': _veins(150)})
    coat = tex.Painted(tex.Cloth(_r(*D['cloth']), folds=0.26), {'*': _ragged})
    trim = tex.Cloth(_r(*D['skin'][1:5]))
    horn = tex.Material(tex.ramp('0a0806', '1c1610', '3a3024', '5a4a38', '7a6850', 'a08a6c'), noise=0.08, grad=0.3)
    glow = _glow(D['color'])
    claw = tex.Material(P['bone'], noise=0.06)
    wing_bone = tex.Material(_r(*D['cloth'][:3], '3a2a30'), noise=0.1)
    membrane = tex.Painted(tex.Material(_r(*D['skin'][:4]), noise=0.2, edge=0, highlight=False), {'*': _membrane_ribs})
    g.bone('horns', 'head', (0, 31, 0))
    g.bone('marks', 'head', (0, 28, -4))
    g.bone('devilArm', 'rightArm', (-5, 22, 0))
    for side in ('right', 'left'):
        sx = -1 if side == 'right' else 1
        g.bone(f'{side}Wing', 'body', (sx * 1, 22.5, 2.2))
        g.bone(f'{side}WingTip', f'{side}Wing', (sx * 13, 22.6, 2.4))
    g.bone('tail0', 'waist', (0, 12, 2))
    for k in range(1, 4):
        g.bone(f'tail{k}', f'tail{k - 1}', (0, 12 - k * 1.2, 2 + k * 4.2))

    # the host
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(skin, {'north': _host_face(D['color'])}))
    g.cube('head', (-4.3, 29.6, -4.3), (8.6, 2.8, 8.6), tex.Material(_r('0a0808', '141010', '201818', '2c2222'), noise=0.2))   # hair
    g.cube('head', (-4.3, 25, 1.2), (8.6, 5, 3.2), tex.Material(_r('0a0808', '141010', '201818', '2c2222'), noise=0.2))
    g.cube('body', (-4, 12, -2), (8, 12, 4), coat)
    g.cube('body', (-4.5, 2, -2.5), (9, 10.5, 5), coat)                                   # long coat
    g.cube('body', (-4.6, 21.5, -2.6), (9.2, 2.8, 5.2), trim)                               # collar
    g.cube('body', (-0.7, 12, -2.3), (1.4, 9, 0.3), trim)
    for side, x0 in (('rightArm', -8), ('leftArm', 4)):
        g.cube(side, (x0, 12, -2), (4, 12, 4), coat)
        g.cube(side, (x0 + 0.2, 12, -1.8), (3.6, 1.6, 3.6), skin)
    for side, x0 in (('rightLeg', -3.9), ('leftLeg', -0.1)):
        g.cube(side, (x0, 0, -2), (4, 12, 4), tex.Cloth(_r(*D['cloth'][:3])))
    # 50%: horns, the devil's arm, glowing marks
    if upto >= 1:
        _horns(g, devil, horn, glow)
        g.cube('devilArm', (-8.7, 11, -2.7), (5.4, 9.5, 5.4), devil_skin)
        g.cube('devilArm', (-9.0, 18.8, -3.0), (6, 4.6, 6), horn)
        g.box('devilArm', (-9.8, 24, 0), (1.2, 3, 1.2), horn, rotation=[0, 0, 25], pivot=(-9.6, 22.6, 0))
        for k in range(4):
            cx = -8.2 + k * 1.3
            g.box('devilArm', (cx, 9.6, -2.0), (0.8, 3.2, 0.8), claw, rotation=[-25, 0, 0], pivot=(cx, 11, -2.0))
        g.box('devilArm', (-6, 15, -2.9), (2.6, 0.6, 0.2), glow)
        g.box('marks', (-2, 28.2, -4.12), (2.6, 0.5, 0.2), glow)
        g.box('marks', (2, 28.2, -4.12), (2.6, 0.5, 0.2), glow)
        g.box('marks', (-3.1, 26.4, -4.12), (0.5, 2.6, 0.2), glow, rotation=[0, 0, 20], pivot=(-3.1, 26.4, -4.12))
        g.box('marks', (3.1, 26.4, -4.12), (0.5, 2.6, 0.2), glow, rotation=[0, 0, -20], pivot=(3.1, 26.4, -4.12))
    # 100%: wings and a tail
    if upto >= 2:
        for side, sx in (('right', -1), ('left', 1)):
            _wings(g, side, sx, membrane, wing_bone, horn)
        for k in range(4):
            s = 2.4 - k * 0.45
            g.cube(f'tail{k}', (-s / 2, 12 - k * 1.2 - s / 2, 2 + k * 4.2), (s, s, 4.4), devil_skin)
        g.box('tail3', (0, 8.4, 19.6), (2.6, 0.6, 2.6), glow, rotation=[0, 45, 0], pivot=(0, 8.4, 19.6))
    return g


def host_animations(prefix='devil_host'):
    a = humanoid_animations(prefix)
    a[f'animation.bc.{prefix}.cast'] = {'animation_length': 0.8, 'bones': {
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.25': [-130, 15, 15], '0.55': [-95, 0, 0], '0.8': [0, 0, 0]}},
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.25': [-60, -10, -20], '0.8': [0, 0, 0]}},
        'body': {'rotation': {'0.0': [0, 0, 0], '0.25': [-8, -15, 0], '0.8': [0, 0, 0]}},
    }}
    a[f'animation.bc.{prefix}.roar'] = {'animation_length': 1.2, 'bones': {
        'body': {'rotation': {'0.0': [0, 0, 0], '0.3': [-22, 0, 0], '0.9': [-18, 0, 0], '1.2': [0, 0, 0]}},
        'head': {'rotation': {'0.0': [0, 0, 0], '0.3': [-30, 0, 0], '0.9': [-25, 0, 0], '1.2': [0, 0, 0]}},
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.3': [-30, 0, 70], '0.9': [-30, 0, 65], '1.2': [0, 0, 0]}},
        'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.3': [-30, 0, -70], '0.9': [-30, 0, -65], '1.2': [0, 0, 0]}},
    }}
    u = "q.property('bc:union')"
    flap = 'math.sin(q.life_time * 200.0)'
    bones = {
        'root': {'scale': [f'1.0 + {u} * 0.08'] * 3, 'position': [0, f'({u} >= 2) ? 1.5 + math.sin(q.life_time * 120.0) * 0.8 : 0.0', 0]},
        'rightWing': {'rotation': [0, f'-20.0 + {flap} * 28.0', f'10.0 + {flap} * 10.0']},
        'leftWing': {'rotation': [0, f'20.0 - {flap} * 28.0', f'-10.0 - {flap} * 10.0']},
        'rightWingTip': {'rotation': [0, f'-18.0 + {flap} * 22.0', 0]},
        'leftWingTip': {'rotation': [0, f'18.0 - {flap} * 22.0', 0]},
        'devilArm': {'scale': [f'1.0 + math.sin(q.life_time * 160.0) * 0.03'] * 3},
    }
    for k in range(4):
        bones[f'tail{k}'] = {'rotation': [f'{-10 + k * 6} + math.sin(q.life_time * 100.0 - {k * 45}) * 6.0', f'math.sin(q.life_time * 80.0 - {k * 50}) * 16.0', 0]}
    a[f'animation.bc.{prefix}.union'] = {'loop': True, 'bones': bones}
    return a


# ======================================================================================
# the Crowned Vessel: a Magic Knight commander who gave himself to a higher-rank devil
# ======================================================================================
def _crest(a, ctx):
    h, w = a.shape[:2]
    lay = tex.draw_layer(h, w, lambda d, s: tex.clover_shape(d, w * s / 2, h * s * 0.45, min(w, h) * s * 0.26, 5, (220, 30, 50, 255), stem=False, devil=True), 4)
    m = lay[..., 3] > 90
    a[m, :3] = lay[m, :3]
    a[m, 3] = 120
    return a


def vessel_geo(upto=2):
    from ..data import DEVILS
    D = DEVILS['vaelgrim']
    g = Geo('geometry.bc.crowned_vessel', res=2, atlas_width=256, visible=(6, 5, (0, 2.0, 0)), seed=1310)
    _humanoid_bones(g)
    plate = tex.Metal(_r('0c0a0e', '16121a', '221c28', '302838', '423850'), sheen=0.45)
    crimson = tex.Cloth(_r('2a0408', '44080e', '620c16', '86121e'), folds=0.2)
    gold = tex.Metal(P['gold'])
    skin = tex.Material(_r('6a5a58', '7e6c6a', '94807c', 'a8948e'), noise=0.08, edge=0.85)
    devil_skin = tex.Painted(tex.Material(_r(*D['skin']), noise=0.16, edge=0.7), {'*': _veins(150)})
    horn = tex.Material(tex.ramp('0a0806', '1c1610', '3a3024', '5a4a38', '7a6850', 'a08a6c'), noise=0.08, grad=0.3)
    glow = _glow(D['color'])
    claw = tex.Material(P['bone'], noise=0.06)
    wing_bone = tex.Material(_r('060204', '120608', '1e0a0e', '2c1016'), noise=0.1)
    membrane = tex.Painted(tex.Material(_r('1a0406', '2e080c', '440c14', '5c121c'), noise=0.2, edge=0, highlight=False), {'*': _membrane_ribs})
    steel = tex.Metal(_r('3a3e48', '585e6c', '7a8292', 'a4aebe', 'd4dce8'), sheen=0.6)
    g.bone('cape', 'body', (0, 24, 2.2))
    g.bone('sword', 'rightArm', (-6, 13, 0))
    g.bone('horns', 'head', (0, 31, 0))
    g.bone('marks', 'head', (0, 28, -4))
    g.bone('devilArm', 'rightArm', (-5, 22, 0))
    g.bone('devilArmL', 'leftArm', (5, 22, 0))
    g.bone('halo', 'head', (0, 38, 3))
    for side in ('right', 'left'):
        sx = -1 if side == 'right' else 1
        g.bone(f'{side}Wing', 'body', (sx * 1, 23, 3))
        g.bone(f'{side}WingTip', f'{side}Wing', (sx * 19, 23.2, 3.2))
    g.bone('tail0', 'waist', (0, 12, 2.5))
    for k in range(1, 4):
        g.bone(f'tail{k}', f'tail{k - 1}', (0, 12 - k * 1.2, 2.5 + k * 5))

    # armour and crown
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.Painted(skin, {'north': _host_face(D['color'])}))
    g.cube('head', (-4.4, 27, -4.4), (8.8, 5.4, 8.8), tex.PerFace(plate, north=tex.Flat('0a0a0c', alpha=255)))
    g.cube('head', (-4.6, 31.6, -4.6), (9.2, 1.4, 9.2), gold)
    for k in range(8):
        a = k / 8 * math.tau
        g.box('head', (math.cos(a) * 4.3, 33.8, math.sin(a) * 4.3), (1.2, 2.6 if k % 2 else 3.8, 1.2), gold)
    g.box('head', (0, 32.6, -4.7), (1.6, 1.6, 0.4), glow, rotation=[0, 0, 45], pivot=(0, 32.6, -4.7))
    g.cube('body', (-4, 12, -2), (8, 12, 4), crimson)
    g.cube('body', (-4.6, 13, -2.7), (9.2, 11.2, 5.4), tex.Painted(plate, {'north': _crest}))
    g.cube('body', (-4.8, 9, -2.9), (9.6, 4, 5.8), plate)
    g.cube('body', (-4.6, 2, -2.6), (9.2, 7.2, 5.2), crimson)
    g.cube('cape', (-5, 1, 2.6), (10, 23, 0.6), crimson)
    for side, x0, sx in (('rightArm', -8, -1), ('leftArm', 4, 1)):
        g.cube(side, (x0, 12, -2), (4, 12, 4), crimson)
        g.cube(side, (x0 - 0.5, 18.5, -2.7), (5, 6, 5.4), plate)
        g.cube(side, (x0 - 0.3, 12, -2.3), (4.6, 4.4, 4.6), plate)
        g.box(side, (x0 + 2 + sx * 2.2, 24.8, 0), (1.2, 2.8, 1.2), gold, rotation=[0, 0, sx * -30], pivot=(x0 + 2, 23.6, 0))
    for side, x0 in (('rightLeg', -3.9), ('leftLeg', -0.1)):
        g.cube(side, (x0, 0, -2), (4, 12, 4), crimson)
        g.cube(side, (x0 - 0.3, 0, -2.4), (4.6, 7, 4.8), plate)
    # a black greatsword
    g.cube('sword', (-6.7, -16, -0.4), (1.4, 24, 0.8), steel)
    g.cube('sword', (-7.7, 7.8, -1.2), (3.4, 1.0, 2.4), gold)
    g.cube('sword', (-6.5, 8.8, -0.5), (1.0, 4.2, 1.0), tex.Material(_r('1a0e08', '2a1810', '3a2218')))
    g.box('sword', (-6, -4, -0.6), (0.4, 18, 0.2), glow)
    # 50%: great horns through the crown, both arms turn
    if upto >= 1:
        for sx in (-1, 1):
            g.box('horns', (sx * 4.8, 33.4, -0.4), (2.4, 3.4, 2.4), horn, rotation=[0, 0, sx * -28], pivot=(sx * 4.4, 31.8, -0.4))
            g.box('horns', (sx * 6.4, 36.2, 0.4), (1.8, 3.4, 1.8), horn, rotation=[15, 0, sx * -12], pivot=(sx * 6.0, 34.8, 0.2))
            g.box('horns', (sx * 7.0, 39.0, 1.8), (1.2, 3.0, 1.2), horn, rotation=[35, 0, 0], pivot=(sx * 7, 37.6, 1.2))
            g.box('horns', (sx * 7.0, 40.6, 3.4), (0.8, 2.0, 0.8), glow, rotation=[55, 0, 0], pivot=(sx * 7, 39.8, 2.8))
        for bone, x0, sx in (('devilArm', -8.7, -1), ('devilArmL', 3.3, 1)):
            g.cube(bone, (x0, 11, -2.7), (5.4, 7.5, 5.4), devil_skin)
            for k in range(4):
                cx = x0 + 0.5 + k * 1.3
                g.box(bone, (cx, 9.6, -2.0), (0.8, 3.2, 0.8), claw, rotation=[-25, 0, 0], pivot=(cx, 11, -2.0))
            g.box(bone, (x0 + 2.7, 15, -2.9), (2.6, 0.6, 0.2), glow)
        g.box('marks', (-2, 28.2, -4.62), (2.6, 0.5, 0.2), glow)
        g.box('marks', (2, 28.2, -4.62), (2.6, 0.5, 0.2), glow)
    # 100%: great wings, a tail and a burning halo
    if upto >= 2:
        for side, sx in (('right', -1), ('left', 1)):
            _wings(g, side, sx, membrane, wing_bone, horn, span=1.5, z=3.4, y=23)
        for k in range(4):
            s = 3.0 - k * 0.55
            g.cube(f'tail{k}', (-s / 2, 12 - k * 1.2 - s / 2, 2.5 + k * 5), (s, s, 5.2), devil_skin)
        g.box('tail3', (0, 8.4, 23.4), (3, 0.6, 3), glow, rotation=[0, 45, 0], pivot=(0, 8.4, 23.4))
        for k in range(12):
            a = math.radians(k * 30)
            cx, cy = math.cos(a) * 6, 38 + math.sin(a) * 6
            g.box('halo', (cx, cy, 5), (2.8, 1.0, 1.0), glow if k % 2 else horn, rotation=[0, 0, k * 30 + 90], pivot=(cx, cy, 5))
    return g


def vessel_animations():
    a = host_animations('crowned_vessel')
    a['animation.bc.crowned_vessel.slash'] = {'animation_length': 0.7, 'bones': {
        'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.2': [-170, -20, 20], '0.38': [-20, 30, -20], '0.7': [0, 0, 0]}},
        'body': {'rotation': {'0.0': [0, 0, 0], '0.2': [-8, 25, 0], '0.38': [10, -30, 0], '0.7': [0, 0, 0]}},
    }}
    u = a['animation.bc.crowned_vessel.union']['bones']
    u['root']['scale'] = ["1.35 + q.property('bc:union') * 0.12"] * 3
    u['cape'] = {'rotation': ['6.0 + math.sin(q.life_time * 110.0) * 4.0 + q.modified_move_speed * 30.0', 0, 0]}
    u['halo'] = {'rotation': [0, 0, 'q.life_time * 40.0']}
    u['devilArmL'] = dict(u['devilArm'])
    return a


# ======================================================================================
# union sprites for players (particle textures, tinted by the devil's colour)
# ======================================================================================
def wings_sprite():
    """Both wings, spread, seen from behind - white so the particle can tint them."""
    def fn(d, s):
        for sx in (-1, 1):
            cx = 64
            bone = [(cx + sx * 6, 30), (cx + sx * 30, 8), (cx + sx * 58, 4)]
            ribs = [(cx + sx * 30, 8), (cx + sx * 44, 6), (cx + sx * 58, 4)]
            pts = [(cx + sx * 4, 34), (cx + sx * 30, 8), (cx + sx * 58, 4), (cx + sx * 56, 30), (cx + sx * 48, 26), (cx + sx * 44, 44),
                   (cx + sx * 34, 36), (cx + sx * 28, 54), (cx + sx * 18, 42), (cx + sx * 8, 50)]
            d.polygon([(x * s, y * s) for x, y in pts], fill=(210, 210, 210, 200))
            d.line([(x * s, y * s) for x, y in bone], fill=(255, 255, 255, 255), width=int(3 * s))
            for (x0, y0), (x1, y1) in zip(ribs, [(cx + sx * 28, 54), (cx + sx * 44, 44), (cx + sx * 56, 30)]):
                d.line([(x0 * s, y0 * s), (x1 * s, y1 * s)], fill=(255, 255, 255, 230), width=int(1.6 * s))
            d.polygon([(x * s, y * s) for x, y in [(cx + sx * 58, 4), (cx + sx * 63, -2), (cx + sx * 60, 8)]], fill=(255, 255, 255, 255))
    return tex.draw_layer(64, 128, fn, 4)


def horns_sprite():
    def fn(d, s):
        for sx in (-1, 1):
            cx = 32
            pts = [(cx + sx * 6, 30), (cx + sx * 12, 30), (cx + sx * 20, 16), (cx + sx * 24, 4), (cx + sx * 18, 12), (cx + sx * 12, 20)]
            d.polygon([(x * s, y * s) for x, y in pts], fill=(240, 240, 240, 255))
            d.line([(cx + sx * 8) * s, 28 * s, (cx + sx * 20) * s, 10 * s], fill=(255, 255, 255, 255), width=int(1.2 * s))
    return tex.draw_layer(32, 64, fn, 4)


# ======================================================================================
# icons
# ======================================================================================
def v13_icons():
    from ..data import DEVILS

    def sigil(color, crown=False):
        c = tuple(int(v) for v in rgb(color)[:3])

        def fn(d, s):
            d.ellipse([3 * s, 3 * s, 29 * s, 29 * s], fill=(24, 12, 16, 255))
            d.ellipse([5 * s, 5 * s, 27 * s, 27 * s], fill=(48, 22, 28, 255))
            tex.clover_shape(d, 16 * s, 16.5 * s, 8 * s, 5, c + (255,), stem=False, devil=True)
            d.ellipse([14 * s, 14.5 * s, 18 * s, 18.5 * s], fill=(255, 240, 220, 255))
            if crown:
                d.polygon([(9 * s, 6 * s), (12 * s, 1 * s), (16 * s, 5 * s), (20 * s, 1 * s), (23 * s, 6 * s)], fill=(230, 180, 60, 255))
        return fn

    def horn(d, s):
        d.polygon([(8 * s, 29 * s), (15 * s, 29 * s), (19 * s, 20 * s), (24 * s, 9 * s), (26 * s, 2 * s), (20 * s, 8 * s), (13 * s, 18 * s)], fill=(90, 70, 52, 255))
        d.polygon([(10 * s, 28 * s), (14 * s, 28 * s), (13 * s, 22 * s)], fill=(140, 116, 88, 255))
        d.line([(25 * s, 3 * s), (21 * s, 9 * s)], fill=(255, 80, 60, 255), width=int(1.6 * s))

    def chain(d, s):
        for k in range(4):
            x, y = 6 + k * 6, 24 - k * 6
            d.ellipse([(x - 4) * s, (y - 3) * s, (x + 4) * s, (y + 3) * s], outline=(170, 176, 190, 255), width=int(2 * s))
        d.ellipse([20 * s, 2 * s, 30 * s, 12 * s], fill=(200, 60, 60, 255))
        d.ellipse([23 * s, 5 * s, 27 * s, 9 * s], fill=(255, 220, 220, 255))

    def crown(d, s):
        d.polygon([(4 * s, 24 * s), (4 * s, 10 * s), (10 * s, 17 * s), (16 * s, 5 * s), (22 * s, 17 * s), (28 * s, 10 * s), (28 * s, 24 * s)], fill=(60, 14, 22, 255))
        d.rectangle([4 * s, 22 * s, 28 * s, 27 * s], fill=(210, 160, 50, 255))
        for x in (9, 16, 23):
            d.ellipse([(x - 2) * s, 23 * s, (x + 2) * s, 27 * s], fill=(255, 40, 60, 255))
        d.line([(4 * s, 10 * s), (1 * s, 4 * s)], fill=(90, 70, 52, 255), width=int(2 * s))
        d.line([(28 * s, 10 * s), (31 * s, 4 * s)], fill=(90, 70, 52, 255), width=int(2 * s))
    out = {f'pact_{k}': _icon(sigil(DEVILS[k]['color'], crown=k == 'vaelgrim')) for k in ('vharog', 'sileth', 'morvane', 'ghorza', 'vaelgrim')}
    out.update({'host_horn': _icon(horn), 'binding_chain': _icon(chain), 'abyssal_crown': _icon(crown)})
    return out
