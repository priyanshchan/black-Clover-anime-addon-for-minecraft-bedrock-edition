"""Held / worn item models: grimoires, anti-magic swords, squad robes."""
from __future__ import annotations

import math

import numpy as np

from .. import tex
from ..data import ATTRIBUTES, ROBES
from ..geo import Geo
from .. import fpsolve
from ..tex import P, rgb


# ======================================================================================
# decals
# ======================================================================================
def _emblem_layer(h, w, color, leaves, devil=False, scale=0.34):
    def fn(d, s):
        cx, cy = w * s / 2, h * s / 2
        r = min(w, h) * s * scale
        tex.clover_shape(d, cx, cy - r * 0.08, r, leaves, tuple(int(c) for c in color), stem=True, devil=devil)
    return tex.draw_layer(h, w, fn, 4)


def cover_decal(attr):
    a_ = ATTRIBUTES[attr]
    trim = P[a_['trim']]

    def fn(a, ctx):
        h, w = a.shape[:2]
        # inset border line
        b = max(1, ctx.res // 2)
        col = trim[-3]
        a[b:b + 1, b:w - b, :3] = col[:3]
        a[h - b - 1:h - b, b:w - b, :3] = col[:3]
        a[b:h - b, b:b + 1, :3] = col[:3]
        a[b:h - b, w - b - 1:w - b, :3] = col[:3]
        lay = _emblem_layer(h, w, trim[-2], a_['leaves'], devil=(attr == 'anti'), scale=0.3)
        # emblem shadow
        sh = lay.copy()
        sh[..., :3] = 0
        sh[..., 3] *= 0.6
        sh = np.roll(np.roll(sh, 1, 0), 1, 1)
        tex.alpha_over(a, sh)
        tex.alpha_over(a, lay)
        if attr == 'anti':
            rng = np.random.default_rng(ctx.seed)
            for _ in range(10):  # scratches & grime
                y, x = rng.integers(0, h), rng.integers(0, w)
                for i in range(rng.integers(2, 6)):
                    yy, xx = min(h - 1, y + i), min(w - 1, max(0, x + i * rng.choice([-1, 1])))
                    a[yy, xx, :3] = a[yy, xx, :3] * 0.5 + 20
        a[..., 3] = 255
        return a
    return fn


def page_decal(attr):
    glow = rgb(ATTRIBUTES[attr]['color'])
    ink = rgb('3a2c1a')

    def fn(a, ctx):
        h, w = a.shape[:2]
        rng = np.random.default_rng(ctx.seed)
        y = 2
        while y < h - 2:
            x = 2
            while x < w - 2:
                ln = int(rng.integers(2, 6))
                c = glow if rng.random() < 0.55 else ink
                for i in range(ln):
                    if x + i < w - 2:
                        a[y, x + i, :3] = c[:3]
                        a[y, x + i, 3] = 130 if c is glow else 255
                x += ln + 1
            y += 2
        return a
    return fn


def sigil_layer(attr):
    color = rgb(ATTRIBUTES[attr]['color'])
    leaves = ATTRIBUTES[attr]['leaves']

    def fn(a, ctx):
        h, w = a.shape[:2]
        a[:] = 0
        ring = tex.rune_ring(h, w, tuple(int(c) for c in color[:3]) + (255,), ctx.seed, ss=4, thickness=0.6, rings=1, glyphs=8)
        lay = _emblem_layer(h, w, color, leaves, devil=(attr == 'anti'), scale=0.24)
        tex.alpha_over(a, ring)
        tex.alpha_over(a, lay)
        m = a[..., 3] > 60
        a[..., 3] = np.where(m, 140, 0)
        return a
    return fn


def page_edges(a, ctx):
    h, w = a.shape[:2]
    a[:] = rgb('e9dcb8')
    for y in range(h):
        if y % 2 == 0:
            a[y, :, :3] *= 0.86
    a[..., 3] = 255
    return a


# ======================================================================================
# grimoire
# ======================================================================================
def _book(g: Geo, p: str, parent: str, attr: str):
    a_ = ATTRIBUTES[attr]
    cover_r = tex.ramp(*a_['cover'])
    trim_r = P[a_['trim']]
    cover = tex.Material(cover_r, noise=0.14, edge=0.65)
    cover_out = tex.Painted(cover, {'down': cover_decal(attr)})
    paper = tex.Material(P['paper'], noise=0.06, edge=0.9, highlight=False)
    pages = tex.PerFace(page_edges, up=tex.Painted(paper, {'up': page_decal(attr)}))
    metal = tex.Metal(trim_r)

    g.bone(p, parent, (0, 0, 0))
    g.bone(f'{p}_a', p, (0, 0, 0), rotation=[0, 0, 12])
    g.bone(f'{p}_b', p, (0, 0, 0), rotation=[0, 0, -12])
    for side, sx in (('a', -1), ('b', 1)):
        bn = f'{p}_{side}'
        x0 = -6.2 if sx < 0 else 0.0
        g.cube(bn, (x0, -0.5, -4.2), (6.2, 0.5, 8.4), cover_out)
        px0 = -5.8 if sx < 0 else 0.2
        g.cube(bn, (px0, 0.0, -3.9), (5.6, 0.9, 7.8), pages)
        # corner fittings
        cx = -6.3 if sx < 0 else 4.9
        for cz in (-4.3, 3.1):
            g.cube(bn, (cx, -0.65, cz), (1.4, 0.75, 1.2), metal)
    g.cube(p, (-0.7, -0.95, -4.25), (1.4, 0.7, 8.5), tex.Painted(cover, {'*': _spine_bands(trim_r)}))
    # ribbon bookmark
    g.cube(p, (-0.3, -3.2, 4.0), (0.6, 3.6, 0), tex.Material(P['red_cloth'], edge=0, highlight=False))
    # flipping page
    g.bone(f'{p}_page', p, (0, 0.95, 0))
    g.cube(f'{p}_page', (0.0, 0.95, -3.7), (5.4, 0, 7.4), tex.Painted(paper, {'*': page_decal(attr)}))
    # hovering sigil
    g.bone(f'{p}_sigil', p, (0, 4.5, 0))
    g.cube(f'{p}_sigil', (-3.2, 4.5, -3.2), (6.4, 0, 6.4), sigil_layer(attr))


def _spine_bands(trim_r):
    def fn(a, ctx):
        h, w = a.shape[:2]
        n = max(w, h)
        for k in (0.2, 0.5, 0.8):
            i = int(n * k)
            if w >= h:
                a[:, max(0, i - 1):i + 1, :3] = trim_r[-2][:3]
            else:
                a[max(0, i - 1):i + 1, :, :3] = trim_r[-2][:3]
        return a
    return fn


def grimoire_geo(attr):
    g = Geo(f'geometry.bc.grimoire_{attr}', res=4, atlas_width=128, visible=(3, 3, (0, 1.2, 0)))
    g.skeleton()
    g.bone('tp_root', 'body', (0, 0, 0))
    _book(g, 'tp_book', 'tp_root', attr)
    g.bone('fp_root', 'rightItem', (0, 0, 0))
    _book(g, 'fp_book', 'fp_root', attr)
    return g


def grimoire_animations():
    bob = 'math.sin(q.life_time * 110.0) * 0.6'
    flip = {"0.0": [0, 0, 0], "0.6": [0, 0, 0], "1.3": [0, 0, 178], "2.2": [0, 0, 178]}
    hide = [0, 0, 0]
    tp = {
        'loop': True,
        'bones': {
            'tp_root': {'scale': 1.0},
            'fp_root': {'scale': 0.0},
            'tp_book': {
                'position': [-13.0, f'26.5 + {bob}', -4.5],
                'rotation': [f'48.0 + math.sin(q.life_time * 80.0) * 4.0', -28.0, f'math.sin(q.life_time * 60.0) * 3.0'],
                'scale': 0.72,
            },
            'tp_book_sigil': {'rotation': [0, 'q.life_time * 70.0', 0], 'scale': 'math.sin(q.life_time * 200.0) * 0.06 + 1.0'},
        },
    }
    pos, rot, sc = fpsolve.solve((-5.4, 18.4, 16.0), fpsolve.basis((0.30, 0.45, -0.84), (0.0, 1.0, 0.0)), scale=0.52)
    fp = {
        'loop': True,
        'bones': {
            'tp_root': {'scale': 0.0},
            'fp_root': {'scale': 1.0},
            'fp_book': {
                'position': [pos[0], f'{pos[1]} + {bob}', pos[2]],
                'rotation': rot,
                'scale': sc,
            },
            'fp_book_sigil': {'rotation': [0, 'q.life_time * 70.0', 0]},
        },
    }
    flip_tp = {'loop': True, 'animation_length': 2.2, 'bones': {'tp_book_page': {'rotation': flip}, 'fp_book_page': {'rotation': flip}}}
    return {
        'animation.bc.grimoire.third_person': tp,
        'animation.bc.grimoire.first_person': fp,
        'animation.bc.grimoire.page_flip': flip_tp,
    }


def grimoire_icon(attr, size=32):
    """2D inventory icon: closed grimoire with clover emblem."""
    a_ = ATTRIBUTES[attr]
    cover_r = tex.ramp(*a_['cover'])
    trim = P[a_['trim']]
    S = size
    img = tex.new(S, S)
    x0, y0, x1, y1 = 7, 3, 26, 29
    # pages block (right side, bottom)
    img[y0 + 2:y1 + 1, x1 - 1:x1 + 3] = rgb('e3d3a8')
    for y in range(y0 + 2, y1 + 1, 2):
        img[y, x1 - 1:x1 + 3, :3] *= 0.85
    img[y1:y1 + 2, x0 + 2:x1 + 3] = rgb('cdb98d')
    # cover with vertical gradient
    t = np.linspace(0.85, 0.35, y1 - y0)[:, None] + tex.value_noise(y1 - y0, x1 - x0, 3, tex.seed_of(attr)) * 0.12
    img[y0:y1, x0:x1] = tex.quantize(cover_r, np.clip(t, 0, 1))
    # spine shading
    img[y0:y1, x0:x0 + 2, :3] *= 0.6
    img[y0:y1, x0 + 2, :3] = np.minimum(img[y0:y1, x0 + 2, :3] * 1.3, 255)
    # border trim
    tc = trim[-3]
    img[y0 + 1, x0 + 3:x1 - 1] = tc
    img[y1 - 2, x0 + 3:x1 - 1] = tc
    img[y0 + 1:y1 - 1, x0 + 3] = tc
    img[y0 + 1:y1 - 1, x1 - 2] = tc
    # corners
    for cy in (y0, y1 - 3):
        img[cy:cy + 3, x1 - 3:x1] = trim[-2]
        img[cy + 1, x1 - 2] = trim[-1]
    # emblem
    em = tex.draw_layer(S, S, lambda d, s: tex.clover_shape(
        d, (x0 + x1) / 2 * s + s, (y0 + y1) / 2 * s - s, 6.2 * s, a_['leaves'], tuple(int(c) for c in trim[-2]),
        stem=True, devil=(attr == 'anti')), 4)
    em[..., 3] = np.where(em[..., 3] > 90, 255, 0)
    sh = em.copy()
    sh[..., :3] = cover_r[0][:3]
    tex.alpha_over(img, np.roll(sh, 1, 0))
    tex.alpha_over(img, em)
    # glow gem in centre of the emblem in element colour
    gc = rgb(a_['color'])
    cx, cy = (x0 + x1) // 2 + 1, (y0 + y1) // 2 - 1
    img[cy:cy + 2, cx - 1:cx + 1] = gc
    img[cy, cx - 1] = np.minimum(gc * 1.2 + 40, 255)
    tex.outline(img, rgb('0a0a0f'))
    return img


# ======================================================================================
# anti-magic swords (modelled: length +Y, width along Z, thickness along X)
# ======================================================================================
def _blade_cracks(seed_extra=0, glow=False):
    def fn(a, ctx):
        h, w = a.shape[:2]
        rng = np.random.default_rng(ctx.seed + seed_extra)
        for _ in range(max(2, h // 10)):
            y, x = int(rng.integers(0, h)), int(rng.integers(1, max(2, w - 1)))
            for i in range(int(rng.integers(3, 9))):
                y = min(h - 1, y + 1)
                x = int(np.clip(x + rng.integers(-1, 2), 0, w - 1))
                a[y, x, :3] = (rgb('5a0f14')[:3] if glow else a[y, x, :3] * 0.4)
        # light bevel on long edges (first/last columns)
        a[:, 0, :3] = np.minimum(a[:, 0, :3] * 1.6 + 25, 255)
        a[:, -1, :3] = np.minimum(a[:, -1, :3] * 1.6 + 25, 255)
        return a
    return fn


def _wrap(a, ctx):
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    band = ((yy + xx) // max(1, ctx.res)) % 3 == 0
    a[band, :3] *= 0.55
    a[((yy - xx) // max(1, ctx.res)) % 6 == 0, :3] *= 0.8
    return a


def sword_geo(kind):
    g = Geo(f'geometry.bc.{kind}', res=3, atlas_width=192, visible=(4, 4, (0, 1.5, 0)))
    g.skeleton()
    g.bone('sword', 'rightItem', (0, 0, 0))
    black = tex.Material(P['obsidian'], noise=0.1, edge=0.6)
    iron = tex.Metal(P['blackiron'], sheen=0.4)
    steel = tex.Metal(P['steel'], sheen=0.3)
    grip = tex.Painted(tex.Material(P['leather'], noise=0.1), {'*': _wrap})
    gripblack = tex.Painted(tex.Material(P['black_cloth'], noise=0.1), {'*': _wrap})

    if kind == 'demon_slayer_sword':
        blade = tex.Painted(tex.Material(P['obsidian'], noise=0.16, edge=0.55, grad=0.06), {
            'east': _blade_cracks(1, glow=True), 'west': _blade_cracks(2, glow=True), '*': _blade_cracks(3)})
        g.box('sword', (0, -6.2, 0), (2.4, 1.6, 2.4), iron)               # pommel
        g.box('sword', (0, -7.2, 0), (1.2, 0.6, 1.2), iron)
        g.box('sword', (0, -2.4, 0), (1.7, 6.2, 1.7), grip)               # grip
        g.box('sword', (0, 1.2, 0), (2.6, 1.8, 8.4), iron)                # guard bar
        for sz in (-1, 1):
            g.box('sword', (0, 0.0, sz * 3.7), (2.2, 1.6, 1.0), iron)     # guard prongs
        g.box('sword', (0, 2.4, 0), (2.9, 2.4, 3.4), iron)                # blade collar
        g.cube('sword', (-0.65, 3.0, -3.2), (1.3, 22.5, 6.4), blade)      # broad blade
        g.cube('sword', (-0.8, 3.6, -0.9), (1.6, 20.5, 1.8), tex.Material(P['blackiron'], noise=0.08, edge=0.7))  # fuller
        g.cube('sword', (-0.65, 25.5, -2.6), (1.3, 1.2, 5.2), blade)      # chamfered tip
        g.cube('sword', (-0.65, 26.7, -1.8), (1.3, 0.8, 3.6), blade)
        for y in (6.0, 9.0):                                               # rivets
            g.box('sword', (0, y, 1.9), (1.9, 0.8, 0.8), steel)
    elif kind == 'demon_dweller_sword':
        blade = tex.Painted(tex.Material(P['obsidian'], noise=0.08, edge=0.7), {
            'east': _edge_line('north'), 'west': _edge_line('north'), '*': None})
        g.box('sword', (0, -7.0, 0), (1.6, 0.8, 1.9), iron)
        g.box('sword', (0, -3.0, 0), (1.4, 7.2, 1.7), gripblack)
        g.box('sword', (0, 0.9, 0), (3.6, 0.6, 3.6), tex.Painted(iron, {'up': _tsuba, 'down': _tsuba}))
        g.box('sword', (0, 1.6, 0), (1.0, 0.9, 1.9), tex.Metal(P['gold']))  # habaki
        # slightly curved blade in three segments
        g.bone('dweller_b1', 'sword', (0, 2.0, 0))
        g.cube('dweller_b1', (-0.35, 2.0, -0.95), (0.7, 9.0, 1.9), blade)
        g.bone('dweller_b2', 'dweller_b1', (0, 11.0, 0.95), rotation=[-4, 0, 0])
        g.cube('dweller_b2', (-0.35, 11.0, -0.85), (0.7, 8.0, 1.8), blade)
        g.bone('dweller_b3', 'dweller_b2', (0, 19.0, 0.9), rotation=[-6, 0, 0])
        g.cube('dweller_b3', (-0.35, 19.0, -0.7), (0.7, 4.5, 1.6), blade)
        g.cube('dweller_b3', (-0.3, 23.5, -0.2), (0.6, 1.6, 1.1), blade, rotation=[-30, 0, 0], pivot=(0, 23.5, 0.9))
    else:  # demon_destroyer_sword
        blade = tex.Painted(tex.Material(P['blackiron'], noise=0.12, edge=0.6), {
            'east': _runes, 'west': _runes, '*': _blade_cracks(5)})
        g.box('sword', (0, -6.6, 0), (2.0, 2.0, 2.0), iron, rotation=[45, 0, 0], pivot=(0, -6.6, 0))
        g.box('sword', (0, -2.6, 0), (1.6, 6.4, 1.6), grip)
        # ring guard (square ring in the Y/Z plane)
        for (cy, cz, sy, sz) in ((1.0, 0, 0.9, 6.0), (4.6, 0, 0.9, 6.0), (2.8, -2.6, 2.8, 0.9), (2.8, 2.6, 2.8, 0.9)):
            g.box('sword', (0, cy, cz), (1.6, sy, sz), iron)
        g.box('sword', (0, 2.8, 0), (1.2, 2.8, 1.6), steel)
        g.cube('sword', (-0.5, 5.0, -1.6), (1.0, 10.0, 3.2), blade)
        g.cube('sword', (-0.55, 15.0, -2.8), (1.1, 6.5, 5.6), blade)   # widened head
        # jagged broken tip
        g.cube('sword', (-0.5, 21.5, -2.8), (1.0, 2.6, 2.0), blade)
        g.cube('sword', (-0.5, 21.5, -0.4), (1.0, 1.4, 1.6), blade)
        g.cube('sword', (-0.5, 21.5, 1.2), (1.0, 3.4, 1.6), blade, rotation=[12, 0, 0], pivot=(0, 21.5, 2.0))
        g.box('sword', (0, 16.5, 0), (1.3, 1.3, 1.3), tex.Flat('8a1a1a', alpha=140), rotation=[45, 0, 0], pivot=(0, 16.5, 0))
    return g


def _edge_line(_):
    def fn(a, ctx):
        h, w = a.shape[:2]
        a[:, :1, :3] = rgb('9aa3b1')[:3]
        a[:, 1:2, :3] = rgb('5c6370')[:3]
        return a
    return fn


def _tsuba(a, ctx):
    h, w = a.shape[:2]
    a[0, :, :3] = a[-1, :, :3] = rgb('d39a2c')[:3]
    a[:, 0, :3] = a[:, -1, :3] = rgb('d39a2c')[:3]
    return a


def _runes(a, ctx):
    h, w = a.shape[:2]
    rng = np.random.default_rng(ctx.seed)
    for y in range(2, h - 2, 4):
        x = w // 2 + int(rng.integers(-1, 2))
        a[y, max(0, x - 1):x + 1, :3] = rgb('3d3d48')[:3]
        a[y + 1, x, :3] = rgb('3d3d48')[:3]
    a[:, 0, :3] = np.minimum(a[:, 0, :3] * 1.5 + 20, 255)
    a[:, -1, :3] = np.minimum(a[:, -1, :3] * 1.5 + 20, 255)
    return a


def sword_animations():
    out = {}
    # kind: (third-person pos, rot, grip anchor y, fp scale)
    poses = {
        'demon_slayer_sword': ([-6.0, 12.6, -1.4], [78.0, 0.0, 0.0], -2.4, 0.72),
        'demon_dweller_sword': ([-6.0, 12.6, -1.2], [80.0, 0.0, 0.0], -3.0, 0.9),
        'demon_destroyer_sword': ([-6.0, 12.6, -1.3], [80.0, 0.0, 0.0], -2.6, 0.82),
    }
    hand = fpsolve.hand_point()
    blade_dir = np.array([0.42, 0.78, 0.46])
    cam = np.array([-0.35, 0.0, -1.0])
    z_hint = np.cross(cam, blade_dir / np.linalg.norm(blade_dir))
    for kind, (tpp, tpr, grip_y, fps) in poses.items():
        R = fpsolve.basis(blade_dir, z_hint)
        fpp, fpr, fpsc = fpsolve.solve(hand + np.array([0.0, 0.6, 0.2]), R, scale=fps, local_anchor=(0, grip_y, 0))
        out[f'animation.bc.{kind}.third_person'] = {'loop': True, 'bones': {'sword': {'position': tpp, 'rotation': tpr}}}
        out[f'animation.bc.{kind}.first_person'] = {'loop': True, 'bones': {'sword': {'position': fpp, 'rotation': fpr, 'scale': fpsc}}}
    return out


def sword_icon(kind, size=32):
    S = size
    img = tex.new(S, S)

    def line(x0, y0, x1, y1, col, w=1):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n):
            t = i / max(n - 1, 1)
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            for dx in range(w):
                for dy in range(w):
                    xi, yi = int(round(x)) + dx, int(round(y)) + dy
                    if 0 <= xi < S and 0 <= yi < S:
                        img[yi, xi] = col
    o = P['obsidian']
    k = P['blackiron']
    if kind == 'demon_slayer_sword':
        for i in range(6):  # broad blade diagonal
            line(9 + i, 21 - i + 0, 26 + i - 2, 4 - i + 2, o[2 + (i % 3)] if 0 < i < 5 else o[5], 1)
        line(10, 21, 27, 4, o[1])
        line(14, 23, 13, 26, k[2], 2)  # guard
        line(7, 18, 12, 23, k[4], 2)
        line(5, 26, 9, 22, P['leather'][3], 2)
        img[27:29, 3:5] = k[5]
        line(18, 13, 22, 9, rgb('5a0f14'))
    elif kind == 'demon_dweller_sword':
        line(10, 21, 27, 3, o[3], 2)
        line(11, 21, 28, 3, P['steel'][4], 1)
        line(7, 20, 12, 25, rgb('d39a2c'), 2)
        line(4, 27, 9, 22, P['black_cloth'][4], 2)
        img[27:29, 2:4] = k[5]
    else:
        line(11, 20, 21, 10, k[3], 3)
        for i in range(5):
            line(19 + i, 13 - i, 25 + i % 2, 5 - i % 3, k[2 + i % 3], 2)
        line(8, 18, 13, 23, k[5], 2)
        line(9, 19, 12, 22, rgb('8a1a1a'))
        line(4, 27, 9, 22, P['leather'][3], 2)
        img[27:29, 2:4] = k[5]
    tex.outline(img, rgb('3a1015') if kind == 'demon_slayer_sword' else rgb('101015'))
    return img


# ======================================================================================
# robes
# ======================================================================================
def _emblem(kind, color):
    col = tuple(int(c) for c in color[:3]) + (255,)

    def fn(a, ctx):
        h, w = a.shape[:2]

        def draw(d, s):
            cx, cy, r = w * s / 2, h * s * 0.36, min(w, h * 0.5) * s * 0.32
            if kind == 'bull':
                d.ellipse([cx - r * 0.55, cy - r * 0.45, cx + r * 0.55, cy + r * 0.75], fill=col)
                for sx in (-1, 1):
                    d.polygon([(cx + sx * r * 0.4, cy - r * 0.2), (cx + sx * r * 1.25, cy - r * 0.55),
                               (cx + sx * r * 1.05, cy - r * 1.05), (cx + sx * r * 0.85, cy - r * 0.6),
                               (cx + sx * r * 0.35, cy - r * 0.45)], fill=col)
                bg = (0, 0, 0, 255)
                d.ellipse([cx - r * 0.35, cy, cx - r * 0.12, cy + r * 0.2], fill=bg)
                d.ellipse([cx + r * 0.12, cy, cx + r * 0.35, cy + r * 0.2], fill=bg)
            elif kind == 'sun':
                for k in range(12):
                    ang = k * math.pi / 6
                    d.polygon([(cx + math.cos(ang - 0.14) * r * 0.55, cy + math.sin(ang - 0.14) * r * 0.55),
                               (cx + math.cos(ang) * r * 1.15, cy + math.sin(ang) * r * 1.15),
                               (cx + math.cos(ang + 0.14) * r * 0.55, cy + math.sin(ang + 0.14) * r * 0.55)], fill=col)
                d.ellipse([cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55], fill=col)
            else:  # lion
                for k in range(10):
                    ang = k * math.pi / 5
                    d.ellipse([cx + math.cos(ang) * r * 0.75 - r * 0.3, cy + math.sin(ang) * r * 0.75 - r * 0.3,
                               cx + math.cos(ang) * r * 0.75 + r * 0.3, cy + math.sin(ang) * r * 0.75 + r * 0.3], fill=col)
                d.ellipse([cx - r * 0.6, cy - r * 0.6, cx + r * 0.6, cy + r * 0.6], fill=(120, 20, 20, 255))
                d.polygon([(cx - r * 0.3, cy - r * 0.1), (cx + r * 0.3, cy - r * 0.1), (cx, cy + r * 0.45)], fill=col)
        lay = tex.draw_layer(h, w, draw, 4)
        lay[..., 3] = np.where(lay[..., 3] > 100, 255, 0)
        tex.alpha_over(a, lay)
        # hem trim
        a[-2:, :, :3] = color[:3]
        return a
    return fn


def robe_geo(rid):
    r = ROBES[rid]
    g = Geo(f'geometry.bc.{rid}', res=2, atlas_width=128, visible=(3, 3, (0, 1, 0)))
    g.skeleton()
    cloth = tex.Cloth(P[r['cloth']])
    lining = tex.Cloth(P[r['lining']])
    trim = tex.Metal(P[r['trim']])
    trim_c = P[r['trim']][-2]
    g.bone('robe_body', 'body', (0, 24, 0))
    g.bone('robe_rarm', 'rightArm', (-5, 22, 0))
    g.bone('robe_larm', 'leftArm', (5, 22, 0))
    g.bone('robe_cape', 'body', (0, 24, 2.6))
    g.bone('robe_held', 'rightItem', (-6, 15, 1))
    # mantle around the shoulders/torso top
    g.cube('robe_body', (-4.6, 17.6, -2.6), (9.2, 6.6, 5.2), cloth)
    g.cube('robe_body', (-3.4, 23.6, -2.9), (6.8, 1.4, 5.8), tex.PerFace(cloth, up=lining))   # collar
    g.cube('robe_body', (-1.0, 21.6, -3.05), (2.0, 1.6, 0.5), trim)                          # clasp
    g.cube('robe_body', (-3.6, 20.2, 2.4), (7.2, 4.4, 1.6), cloth)                            # folded hood
    g.cube('robe_body', (-4.7, 17.3, -2.7), (9.4, 0.5, 5.4), trim)                            # trim band
    g.cube('robe_rarm', (-8.7, 17.4, -2.7), (5.4, 6.9, 5.4), cloth)
    g.cube('robe_rarm', (-8.8, 17.1, -2.8), (5.6, 0.5, 5.6), trim)
    g.cube('robe_larm', (3.3, 17.4, -2.7), (5.4, 6.9, 5.4), cloth)
    g.cube('robe_larm', (3.2, 17.1, -2.8), (5.6, 0.5, 5.6), trim)
    cape_out = tex.Painted(cloth, {'south': _emblem(r['emblem'], trim_c)})
    g.cube('robe_cape', (-5.0, 8.0, 2.6), (10.0, 16.0, 0.8), tex.PerFace(cape_out, north=lining))
    # folded robe for when it is held in the hand
    g.cube('robe_held', (-9.0, 11.0, -6.0), (6.0, 2.4, 6.0), tex.PerFace(cloth, up=tex.Painted(cloth, {'up': _emblem(r['emblem'], trim_c)})))
    g.cube('robe_held', (-9.2, 12.0, -6.2), (6.4, 0.4, 6.4), trim)
    return g


def robe_animations():
    held = "(c.item_slot == 'main_hand' || c.item_slot == 'off_hand')"
    return {
        'animation.bc.robe.wear': {
            'loop': True,
            'bones': {
                'robe_body': {'scale': f'{held} ? 0.0 : 1.0'},
                'robe_rarm': {'scale': f'{held} ? 0.0 : 1.0'},
                'robe_larm': {'scale': f'{held} ? 0.0 : 1.0'},
                'robe_cape': {
                    'scale': f'{held} ? 0.0 : 1.0',
                    'rotation': ['math.clamp(q.modified_move_speed * 70.0, 0.0, 55.0) + math.sin(q.life_time * 110.0) * 2.5 + (q.is_sneaking ? 22.0 : 4.0)', 0, 0],
                },
                'robe_held': {'scale': f'{held} ? 1.0 : 0.0'},
            },
        },
    }


def robe_icon(rid, size=32):
    r = ROBES[rid]
    S = size
    cloth = P[r['cloth']]
    trim = P[r['trim']]
    img = tex.new(S, S)
    yy, xx = np.mgrid[0:S, 0:S]
    # cape silhouette
    shape = (yy >= 6) & (yy <= 29) & (np.abs(xx - 15.5) <= 6 + (yy - 6) * 0.32)
    t = 0.75 - (yy - 6) / 30 + np.sin(xx * 0.9) * 0.08
    img[shape] = tex.quantize(cloth, np.clip(t, 0, 1))[shape]
    # shoulders / collar
    coll = (yy >= 4) & (yy <= 8) & (np.abs(xx - 15.5) <= 8)
    img[coll] = tex.quantize(cloth, np.clip(t + 0.2, 0, 1))[coll]
    img[8, 8:24] = trim[-3]
    img[5:8, 14:18] = trim[-2]
    img[29, 6:26] = trim[-3]
    em = _emblem(r['emblem'], trim[-2])
    sub = img[10:26, 8:24].copy()
    em(sub, tex.FaceCtx('south', 16, 16, 1, {}, 1))
    img[10:26, 8:24] = np.where(shape[10:26, 8:24, None], sub, img[10:26, 8:24])
    tex.outline(img, rgb('0a0a0f'))
    return img
