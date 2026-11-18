"""v0.8.0 armour: eight styles of helmet, chestplate, leggings and boots (worn as attachables on the player skeleton),
their icons, the armour materials, the runes and the Magic Forge block. All designs are original."""
from __future__ import annotations

import math

import numpy as np

from .. import tex
from ..data import ARMOR_SETS, RUNES
from ..geo import Geo
from ..tex import P, ramp, rgb

def _t(c):
    """A colour as a PIL fill tuple."""
    c = rgb(c) if isinstance(c, str) else c
    return tuple(int(v) for v in list(c)[:4]) + ((255,) if len(list(c)) < 4 else ())


CHITIN = ramp('1e0f04', '3a2008', '5e360e', '855016', 'ad6e20', 'd4922e', 'f0b850')


# ------------------------------------------------------------------------------------------------ decals
def _decal(fn):
    """Wrap a PIL drawing fn(d, w, h, s) as a face decal."""
    def apply(a, ctx):
        h, w = a.shape[:2]
        if h < 3 or w < 3:
            return a
        lay = tex.draw_layer(h, w, lambda d, s: fn(d, w, h, s), 4)
        lay[..., 3] = np.where(lay[..., 3] > 100, 255, 0)
        tex.alpha_over(a, lay)
        return a
    return apply


def _runes(color):
    c = _t(color)

    def fn(d, w, h, s):
        lw = max(1, int(s * 0.9))
        d.line([(w * s * 0.2, h * s * 0.5), (w * s * 0.8, h * s * 0.5)], fill=c, width=lw)
        d.line([(w * s * 0.35, h * s * 0.25), (w * s * 0.35, h * s * 0.75)], fill=c, width=lw)
        d.line([(w * s * 0.65, h * s * 0.3), (w * s * 0.5, h * s * 0.5), (w * s * 0.65, h * s * 0.7)], fill=c, width=lw)
    return _decal(fn)


def _scales(dark):
    c = _t(dark)

    def fn(d, w, h, s):
        step = 2.0 * s
        for row, y in enumerate(np.arange(0, h * s + step, step)):
            off = step / 2 if row % 2 else 0
            for x in np.arange(-step, w * s + step, step):
                d.arc([x + off, y - step / 2, x + off + step, y + step / 2], 0, 180, fill=c, width=max(1, int(s * 0.5)))
    return _decal(fn)


def _stars(color):
    c = _t(color)

    def fn(d, w, h, s):
        rng = np.random.default_rng(int(w * 31 + h * 7))
        for _ in range(max(1, int(w * h / 18))):
            x, y = rng.uniform(0, w * s), rng.uniform(0, h * s)
            r = s * 0.45
            d.polygon([(x, y - r * 2), (x + r * 0.6, y), (x, y + r * 2), (x - r * 0.6, y)], fill=c)
            d.polygon([(x - r * 2, y), (x, y - r * 0.6), (x + r * 2, y), (x, y + r * 0.6)], fill=c)
    return _decal(fn)


def _bands(color):
    c = _t(color)

    def fn(d, w, h, s):
        for k in range(1, 4):
            y = h * s * k / 4
            d.line([(0, y), (w * s, y)], fill=c, width=max(1, int(s * 0.7)))
    return _decal(fn)


def _emblem(color):
    c = _t(color)

    def fn(d, w, h, s):
        tex.clover_shape(d, w * s / 2, h * s / 2, min(w, h) * s * 0.38, 4, c, stem=False)
    return _decal(fn)


# ------------------------------------------------------------------------------------------------ materials
def mats(sid):
    """Materials for a set: base, dark, accent, glow, cloth."""
    s = ARMOR_SETS[sid]
    glow = tex.Flat(s['glow'])
    st = s['style']
    if st == 'knight':
        return dict(base=tex.Metal(P['steel']), dark=tex.Metal(P['blackiron']), accent=tex.Metal(P['water'], sheen=0.5), glow=glow,
                    cloth=tex.Cloth(P['navy']), deco=tex.Painted(tex.Metal(P['steel']), {'north': _emblem(rgb('7cc8ff'))}))
    if st == 'royal':
        silver = tex.Metal(P['silver'])
        return dict(base=silver, dark=tex.Metal(P['steel']), accent=tex.Metal(P['gold'], sheen=0.5), glow=glow,
                    cloth=tex.Cloth(P['white_cloth']), deco=tex.Painted(silver, {'north': _emblem(rgb('d39a2c'))}))
    if st == 'devil':
        hide = tex.Material(P['devil_skin'], noise=0.2, cell=1.6)
        return dict(base=hide, dark=tex.Material(P['obsidian']), accent=tex.Material(P['bone'], noise=0.08), glow=glow,
                    cloth=tex.Cloth(P['black_cloth']), deco=tex.Painted(hide, {'north': _runes('ff4a4a')}))
    if st == 'abyssal':
        scale = tex.Painted(tex.Metal(P['aqua_cloth'], sheen=0.5), {'*': _scales('0b363c')})
        return dict(base=scale, dark=tex.Metal(P['navy']), accent=tex.Metal(P['water'], sheen=0.5), glow=glow,
                    cloth=tex.Material(P['aqua_cloth']), deco=scale)
    if st == 'shadow':
        cloth = tex.Cloth(P['black_cloth'])
        return dict(base=cloth, dark=tex.Material(P['leather']), accent=tex.Cloth(P['purple_cloth']), glow=glow,
                    cloth=tex.Cloth(P['purple_cloth']), deco=cloth)
    if st == 'chitin':
        shell = tex.Painted(tex.Metal(CHITIN, sheen=0.45), {'*': _bands('2a1606')})
        return dict(base=shell, dark=tex.Metal(P['blackiron']), accent=tex.Metal(CHITIN, sheen=0.6, tone_shift=0.15), glow=glow,
                    cloth=tex.Material(P['leather']), deco=shell)
    if st == 'rune':
        stone = tex.Painted(tex.Metal(P['stone'], sheen=0.2), {'north': _runes('60e0ff'), 'east': _runes('60e0ff'), 'west': _runes('60e0ff')})
        return dict(base=stone, dark=tex.Metal(P['deepslate']), accent=tex.Metal(P['mossstone']), glow=glow,
                    cloth=tex.Material(P['mossstone']), deco=stone)
    # mage
    robe = tex.Painted(tex.Cloth(P['navy']), {'*': _stars('ff9cff')})
    return dict(base=robe, dark=tex.Cloth(P['purple_cloth']), accent=tex.Metal(P['gold'], sheen=0.5), glow=glow,
                cloth=tex.Cloth(P['purple_cloth']), deco=robe)


# ------------------------------------------------------------------------------------------------ geometry helpers
def _mirror(o, s, rot=None):
    """Mirror a right-side cube (negative x) to the left side."""
    o2 = (-(o[0] + s[0]), o[1], o[2])
    r2 = None if rot is None else (rot[0], -rot[1], -rot[2])
    return o2, r2


def _pair(g, rbone, lbone, o, s, m, rot=None, pivot=None):
    g.cube(rbone, o, s, m, rotation=rot, pivot=pivot)
    o2, r2 = _mirror(o, s, rot)
    p2 = None if pivot is None else (-pivot[0], pivot[1], pivot[2])
    g.cube(lbone, o2, s, m, rotation=r2, pivot=p2)


BONES = {
    'head': [('ar_head', 'head', (0, 24, 0))],
    'chest': [('ar_body', 'body', (0, 24, 0)), ('ar_rarm', 'rightArm', (-5, 22, 0)), ('ar_larm', 'leftArm', (5, 22, 0))],
    'legs': [('ar_belt', 'body', (0, 12, 0)), ('ar_rleg', 'rightLeg', (-1.9, 12, 0)), ('ar_lleg', 'leftLeg', (1.9, 12, 0))],
    'feet': [('ar_rfoot', 'rightLeg', (-1.9, 12, 0)), ('ar_lfoot', 'leftLeg', (1.9, 12, 0))],
}
CAPE = {'royal': 'cape', 'mage': 'coat', 'shadow': 'scarf'}


def has_cape(sid, slot):
    return slot == 'chest' and ARMOR_SETS[sid]['style'] in CAPE


def armor_geo(sid, slot):
    st = ARMOR_SETS[sid]['style']
    m = mats(sid)
    g = Geo(f'geometry.bc.{sid}_{slot}', res=2, atlas_width=128, visible=(3, 3, (0, 1, 0)))
    g.skeleton()
    for name, parent, pivot in BONES[slot]:
        g.bone(name, parent, pivot)
    if has_cape(sid, slot):
        g.bone('ar_cape', 'body', (0, 24, 2.8))
    g.bone('ar_held', 'rightItem', (-6, 15, 1))
    {'head': _helmet, 'chest': _chest, 'legs': _legs, 'feet': _boots}[slot](g, st, m)
    _held(g, slot, m)
    return g


def _helmet(g, st, m):
    b = 'ar_head'
    base, acc, dark, glow = m['base'], m['accent'], m['dark'], m['glow']
    hood = st in ('devil', 'shadow', 'mage')
    shell = m['cloth'] if st == 'shadow' else base
    # the shell: top, back and sides (the face stays open unless the helm is closed)
    g.cube(b, (-4.6, 31.4, -4.6), (9.2, 1.4, 9.2), shell)
    g.cube(b, (-4.6, 23.4 if hood else 24.0, 3.4), (9.2, 8.0 if hood else 7.4, 1.2), shell)
    g.cube(b, (-4.6, 23.4 if hood else 24.0, -4.6), (1.2, 8.0 if hood else 7.4, 8.0), shell)
    g.cube(b, (3.4, 23.4 if hood else 24.0, -4.6), (1.2, 8.0 if hood else 7.4, 8.0), shell)
    g.cube(b, (-4.6, 30.0, -4.6), (9.2, 1.6, 1.0), acc if st in ('knight', 'royal', 'mage', 'abyssal') else shell)
    if st in ('knight', 'rune'):
        # a closed helm: a face plate with an eye slit
        g.cube(b, (-4.6, 24.0, -4.8), (9.2, 3.4, 1.2), base)
        g.cube(b, (-4.6, 28.4, -4.8), (9.2, 1.8, 1.2), base)
        if st == 'rune':
            g.cube(b, (-3.4, 27.5, -4.5), (6.8, 0.8, 0.4), glow)
            g.cube(b, (-5.0, 31.0, -5.0), (10.0, 2.2, 10.0), m['dark'])
            g.cube(b, (-1.0, 33.0, -4.0), (2.0, 1.0, 8.0), glow)
        else:
            g.cube(b, (-0.7, 32.6, -4.2), (1.4, 2.6, 8.6), acc)       # crest
            g.cube(b, (-0.5, 24.0, -5.2), (1.0, 3.4, 0.6), acc)      # nasal ridge
    elif st == 'royal':
        g.cube(b, (-4.6, 24.0, -4.6), (1.8, 4.0, 1.2), base)         # cheek guards
        g.cube(b, (2.8, 24.0, -4.6), (1.8, 4.0, 1.2), base)
        g.cube(b, (-4.9, 31.0, -4.9), (9.8, 1.4, 9.8), acc)          # crown band
        for x in (-3.8, -1.4, 1.0, 3.2):
            g.cube(b, (x - 0.3, 32.4, -4.9), (0.9, 1.6, 0.9), acc)
        g.cube(b, (-0.6, 32.4, -5.1), (1.2, 2.4, 1.0), glow)
        _pair(g, b, b, (-5.6, 27.5, -1.0), (0.6, 5.0, 4.0), m['cloth'], rot=(0, 0, 18), pivot=(-5.0, 28.0, 1.0))  # wings
    elif st == 'devil':
        g.cube(b, (-4.6, 29.4, -5.2), (9.2, 1.2, 1.0), dark)          # hood brim
        _pair(g, b, b, (-6.0, 30.0, -1.2), (2.0, 2.0, 2.2), acc)      # horns, curving out and up
        _pair(g, b, b, (-7.4, 31.2, -1.0), (1.6, 1.8, 1.8), acc, rot=(0, 0, 20), pivot=(-6.6, 32.0, 0))
        _pair(g, b, b, (-8.2, 32.8, -0.8), (1.2, 2.0, 1.4), acc, rot=(0, 0, 8), pivot=(-7.6, 33.6, 0))
        _pair(g, b, b, (-8.4, 34.6, -0.6), (0.8, 1.6, 1.0), dark)
        g.cube(b, (-2.6, 30.2, -5.0), (5.2, 0.6, 0.4), glow)
    elif st == 'abyssal':
        for k, x in enumerate((-3.0, -1.0, 0.8, 2.6)):
            h = 2.6 if k in (1, 2) else 1.8
            g.cube(b, (x - 0.2, 32.6, -3.0 + k * 0.4), (0.5, h, 5.0), acc)
        _pair(g, b, b, (-5.6, 26.0, -2.0), (1.0, 4.4, 5.0), acc, rot=(0, 0, -10), pivot=(-4.6, 28.0, 0))  # ear fins
        g.cube(b, (-0.8, 30.4, -5.0), (1.6, 1.6, 0.6), glow)
    elif st == 'shadow':
        g.cube(b, (-4.6, 24.0, -4.9), (9.2, 3.2, 1.0), base)          # face mask
        g.cube(b, (-4.6, 30.2, -5.0), (9.2, 1.4, 1.0), base)          # hood brim
    elif st == 'chitin':
        g.cube(b, (-4.8, 30.2, -5.2), (9.6, 1.6, 1.4), acc)           # brow plate
        _pair(g, b, b, (-4.4, 23.6, -5.4), (1.4, 2.6, 1.6), dark, rot=(0, 20, 0), pivot=(-3.6, 24.6, -4.6))  # mandibles
        _pair(g, b, b, (-2.4, 32.4, -4.0), (0.5, 4.0, 0.5), dark, rot=(-30, 0, 15), pivot=(-2.2, 32.4, -3.8))  # antennae
        _pair(g, b, b, (-3.2, 35.6, -6.0), (0.5, 0.5, 0.5), m['glow'])
    elif st == 'mage':
        g.cube(b, (-3.6, 32.6, -3.0), (7.2, 2.0, 7.2), base, rotation=(-8, 0, 0), pivot=(0, 32.6, 0))   # a tall, drooping hood
        g.cube(b, (-2.6, 34.2, -1.6), (5.2, 2.0, 5.2), base, rotation=(-16, 0, 0), pivot=(0, 34.2, 0))
        g.cube(b, (-1.6, 35.8, 0.2), (3.2, 2.0, 3.2), base, rotation=(-26, 0, 0), pivot=(0, 35.8, 1.5))
        g.cube(b, (-0.8, 37.2, 2.0), (1.6, 1.6, 1.6), acc, rotation=(-36, 0, 0), pivot=(0, 37.2, 2.6))
        g.cube(b, (-4.8, 29.6, -5.0), (9.6, 1.0, 1.2), acc)
        g.cube(b, (-0.7, 30.6, -5.2), (1.4, 1.4, 0.6), glow)


def _chest(g, st, m):
    b, ra, la = 'ar_body', 'ar_rarm', 'ar_larm'
    base, acc, dark, glow, cloth = m['base'], m['accent'], m['dark'], m['glow'], m['cloth']
    g.cube(b, (-4.8, 12.6, -2.8), (9.6, 11.8, 5.6), m['deco'] if st in ('knight', 'royal', 'devil') else base)
    g.cube(b, (-4.9, 12.0, -2.9), (9.8, 1.4, 5.8), dark if st not in ('royal', 'mage') else acc)    # lower band
    g.cube(b, (-4.0, 23.4, -2.9), (8.0, 1.6, 5.8), acc if st in ('knight', 'royal', 'mage') else dark)  # collar
    # sleeves
    for bone, x0 in ((ra, -8.6), (la, 3.6)):
        g.cube(bone, (x0, 13.4, -2.6), (5.0, 10.6, 5.2), cloth if st in ('shadow', 'mage') else base)
        g.cube(bone, (x0 - 0.1, 13.0, -2.7), (5.2, 1.0, 5.4), acc)                                   # cuff
    # pauldrons
    big = st in ('royal', 'rune', 'knight')
    if st == 'rune':
        _pair(g, ra, la, (-10.2, 20.6, -3.6), (7.0, 4.2, 7.2), base)
        _pair(g, ra, la, (-10.4, 19.0, -3.8), (6.0, 1.6, 7.6), dark)
        _pair(g, ra, la, (-10.4, 22.4, -1.0), (0.4, 1.0, 2.0), glow)
        g.cube(b, (-1.6, 17.0, -3.4), (3.2, 3.2, 0.8), glow)                                             # core gem
        g.cube(b, (-2.4, 16.2, -3.2), (4.8, 4.8, 0.5), dark)
    elif st in ('devil', 'chitin'):
        _pair(g, ra, la, (-9.4, 21.2, -3.2), (6.0, 3.2, 6.4), acc if st == 'devil' else base)
        for z in (-2.2, 0.2):
            _pair(g, ra, la, (-8.2, 24.2, z), (1.4, 2.4, 1.4), acc if st == 'chitin' else m['accent'], rot=(0, 0, 25), pivot=(-7.6, 24.2, z + 0.7))
        if st == 'chitin':
            for y in (15.0, 17.6, 20.2):
                g.cube(b, (-4.9, y, -3.1), (9.8, 0.6, 0.5), dark)
        else:
            for y in (15.0, 17.5, 20.0):
                g.cube(b, (-4.4, y, -3.1), (8.8, 0.7, 0.4), m['accent'])                              # bone ribs
            g.cube(b, (-1.0, 18.2, -3.4), (2.0, 2.0, 0.6), glow)
    elif st == 'abyssal':
        _pair(g, ra, la, (-9.4, 21.0, -3.2), (6.0, 3.0, 6.4), acc)
        _pair(g, ra, la, (-7.4, 24.0, -2.6), (0.5, 2.8, 5.2), acc, rot=(0, 0, 20), pivot=(-7.2, 24.0, 0))  # shoulder fins
        g.cube(b, (-1.2, 18.0, -3.3), (2.4, 2.4, 0.6), glow)
    elif st == 'shadow':
        g.cube(b, (-4.6, 22.0, -3.1), (9.2, 2.4, 6.2), acc)                                             # scarf
        g.cube(b, (-4.9, 15.0, -3.0), (9.8, 1.0, 0.4), dark, rotation=(0, 0, 30), pivot=(0, 15.5, -3.0))  # strap
        g.cube('ar_cape', (0.6, 12.4, 2.9), (2.6, 10.6, 0.5), acc)                                      # scarf tail
    elif st == 'mage':
        g.cube(b, (-4.4, 23.6, -3.2), (8.8, 3.0, 6.4), acc)                                            # high collar
        g.cube(b, (-0.8, 13.0, -3.1), (1.6, 10.6, 0.4), acc)                                           # gold seam
        g.cube(b, (-1.0, 20.2, -3.4), (2.0, 2.0, 0.5), glow)
        _pair(g, ra, la, (-9.2, 21.6, -3.0), (5.6, 2.4, 6.0), acc)
        g.cube('ar_cape', (-4.6, 2.0, 2.8), (9.2, 10.6, 0.6), tex.PerFace(base, north=m['dark']))      # coat tails
    if big and st != 'rune':
        _pair(g, ra, la, (-9.6, 20.6, -3.4), (6.2, 3.8, 6.8), acc if st == 'royal' else base)
        _pair(g, ra, la, (-9.8, 19.4, -3.6), (5.4, 1.4, 7.2), base if st == 'royal' else acc)
    if st == 'royal':
        g.cube(b, (-2.4, 4.6, -3.1), (4.8, 8.0, 0.5), tex.PerFace(cloth, north=tex.Painted(cloth, {'north': _emblem(rgb('d39a2c'))})))  # tabard
        g.cube('ar_cape', (-4.8, 4.0, 2.8), (9.6, 19.4, 0.7), tex.PerFace(cloth, north=acc))           # cape
    if st == 'knight':
        g.cube(b, (-1.2, 18.4, -3.3), (2.4, 2.4, 0.6), glow)


def _legs(g, st, m):
    b, rl, ll = 'ar_belt', 'ar_rleg', 'ar_lleg'
    base, acc, dark, glow, cloth = m['base'], m['accent'], m['dark'], m['glow'], m['cloth']
    g.cube(b, (-4.6, 10.6, -2.6), (9.2, 2.2, 5.2), dark if st not in ('royal', 'mage') else acc)
    g.cube(b, (-0.8, 10.5, -2.9), (1.6, 1.6, 0.5), glow if st in ('rune', 'abyssal', 'devil', 'mage') else acc)     # buckle
    legmat = cloth if st in ('shadow',) else base
    if st == 'mage':
        _pair(g, rl, ll, (-4.6, 1.6, -2.8), (5.2, 10.6, 5.6), base)               # long skirts
        _pair(g, rl, ll, (-4.7, 1.4, -2.9), (5.4, 0.8, 5.8), acc)
        return
    _pair(g, rl, ll, (-4.4, 3.4, -2.5), (4.9, 8.8, 5.0), legmat)
    knee = acc if st in ('knight', 'royal', 'abyssal', 'chitin') else dark
    _pair(g, rl, ll, (-4.0, 5.0, -3.0), (4.2, 2.4, 0.8), knee)
    if st in ('royal', 'knight', 'rune'):
        g.cube(b, (-4.8, 7.6, -2.9), (4.4, 3.4, 0.6), acc if st == 'royal' else base)                  # tassets
        g.cube(b, (0.4, 7.6, -2.9), (4.4, 3.4, 0.6), acc if st == 'royal' else base)
    if st == 'rune':
        _pair(g, rl, ll, (-3.0, 7.4, -3.0), (2.0, 0.6, 0.3), glow)
    if st == 'chitin':
        _pair(g, rl, ll, (-4.6, 8.0, -1.0), (0.6, 2.0, 2.0), dark, rot=(0, 0, 20), pivot=(-4.4, 9.0, 0))
    if st == 'shadow':
        _pair(g, rl, ll, (-4.5, 8.4, -2.7), (5.0, 0.8, 5.4), dark)                  # wraps
        _pair(g, rl, ll, (-4.5, 6.0, -2.7), (5.0, 0.8, 5.4), dark)


def _boots(g, st, m):
    rf, lf = 'ar_rfoot', 'ar_lfoot'
    base, acc, dark, glow = m['base'], m['accent'], m['dark'], m['glow']
    shoe = m['cloth'] if st in ('shadow', 'mage') else base
    _pair(g, rf, lf, (-4.5, -0.1, -2.6), (5.1, 4.8, 5.2), shoe)
    _pair(g, rf, lf, (-4.3, -0.1, -3.4), (4.7, 2.0, 1.0), dark if st != 'royal' else acc)                  # toe caps
    _pair(g, rf, lf, (-4.6, 4.3, -2.7), (5.3, 1.0, 5.4), acc)                                              # cuffs
    if st == 'rune':
        _pair(g, rf, lf, (-4.7, -0.2, -3.6), (5.5, 1.0, 6.4), dark)                                        # heavy soles
        _pair(g, rf, lf, (-2.6, 2.0, -3.5), (1.6, 0.6, 0.2), glow)
    elif st == 'chitin':
        _pair(g, rf, lf, (-3.0, 1.0, 2.4), (1.2, 1.2, 2.0), dark, rot=(30, 0, 0), pivot=(-2.4, 1.6, 2.6))     # heel spurs
    elif st == 'abyssal':
        _pair(g, rf, lf, (-5.0, 1.4, -1.6), (0.5, 3.4, 3.6), acc, rot=(0, 0, -12), pivot=(-4.6, 2.0, 0))      # ankle fins
    elif st == 'mage':
        _pair(g, rf, lf, (-3.0, 1.6, -4.4), (1.6, 1.2, 1.4), acc, rot=(30, 0, 0), pivot=(-2.2, 1.6, -3.8))    # curled toes
    elif st == 'devil':
        _pair(g, rf, lf, (-3.0, 0.0, -4.4), (1.4, 1.2, 1.4), m['accent'])                                  # claws
    elif st == 'shadow':
        _pair(g, rf, lf, (-4.6, 2.2, -2.7), (5.3, 0.6, 5.4), dark)


def _held(g, slot, m):
    """A folded piece shown when it is held in the hand instead of worn."""
    h = 'ar_held'
    base, acc = m['base'], m['accent']
    if slot == 'head':
        g.cube(h, (-8.8, 10.8, -5.2), (5.6, 4.4, 5.6), base)
        g.cube(h, (-9.0, 13.6, -5.4), (6.0, 0.8, 6.0), acc)
    elif slot == 'chest':
        g.cube(h, (-9.0, 9.0, -5.4), (6.0, 6.6, 3.4), base)
        g.cube(h, (-9.2, 14.6, -5.6), (6.4, 1.0, 3.8), acc)
    elif slot == 'legs':
        g.cube(h, (-9.0, 9.0, -5.0), (2.6, 6.4, 2.8), base)
        g.cube(h, (-6.0, 9.0, -5.0), (2.6, 6.4, 2.8), base)
        g.cube(h, (-9.2, 14.6, -5.2), (6.0, 1.0, 3.2), acc)
    else:
        g.cube(h, (-9.0, 9.0, -6.0), (2.6, 3.4, 4.0), base)
        g.cube(h, (-6.0, 9.0, -6.0), (2.6, 3.4, 4.0), base)
        g.cube(h, (-9.2, 12.2, -5.0), (6.0, 0.8, 3.0), acc)


def armor_animation(sid, slot):
    held = "(c.item_slot == 'main_hand' || c.item_slot == 'off_hand')"
    bones = {name: {'scale': f'{held} ? 0.0 : 1.0'} for name, _, _ in BONES[slot]}
    if has_cape(sid, slot):
        swing = 'math.clamp(q.modified_move_speed * 70.0, 0.0, 55.0) + math.sin(q.life_time * 110.0) * 2.5 + (q.is_sneaking ? 22.0 : 4.0)'
        if ARMOR_SETS[sid]['style'] == 'mage':
            swing = 'math.clamp(q.modified_move_speed * 50.0, 0.0, 35.0) + math.sin(q.life_time * 90.0) * 2.0'
        bones['ar_cape'] = {'scale': f'{held} ? 0.0 : 1.0', 'rotation': [swing, 0, 0]}
    bones['ar_held'] = {'scale': f'{held} ? 1.0 : 0.0'}
    return {f'animation.bc.armor.{sid}_{slot}': {'loop': True, 'bones': bones}}


# ------------------------------------------------------------------------------------------------ icons
def _ic(fn, outline='0a0a0f'):
    a = tex.draw_layer(32, 32, fn, 4)
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    tex.outline(a, rgb(outline))
    return a


def _cols(sid):
    s = ARMOR_SETS[sid]
    st = s['style']
    base = {'knight': P['steel'], 'royal': P['silver'], 'devil': P['devil_skin'], 'abyssal': P['aqua_cloth'], 'shadow': P['black_cloth'],
            'chitin': CHITIN, 'rune': P['stone'], 'mage': P['navy']}[st]
    acc = {'knight': P['water'], 'royal': P['gold'], 'devil': P['bone'], 'abyssal': P['water'], 'shadow': P['purple_cloth'],
           'chitin': P['blackiron'], 'rune': P['mossstone'], 'mage': P['gold']}[st]
    c = lambda r, i: tuple(int(v) for v in r[min(len(r) - 1, i)][:3]) + (255,)  # noqa: E731
    return st, c(base, len(base) - 3), c(base, len(base) - 1), c(base, 1), c(acc, len(acc) - 2), _t(s['glow'])


def piece_icon(sid, slot):
    st, mid, light, dark, acc, glow = _cols(sid)

    def helmet(d, s):
        if st == 'mage':
            d.polygon([(6 * s, 27 * s), (10 * s, 10 * s), (19 * s, 3 * s), (24 * s, 6 * s), (21 * s, 12 * s), (26 * s, 27 * s)], fill=mid)
            d.polygon([(11 * s, 18 * s), (21 * s, 18 * s), (22 * s, 27 * s), (10 * s, 27 * s)], fill=dark)
            d.rectangle([7 * s, 25 * s, 25 * s, 28 * s], fill=acc)
            d.ellipse([22 * s, 3 * s, 26 * s, 7 * s], fill=acc)
            return
        d.rounded_rectangle([6 * s, 7 * s, 26 * s, 28 * s], radius=6 * s, fill=mid)
        d.rectangle([6 * s, 8 * s, 26 * s, 12 * s], fill=light)
        if st in ('knight', 'rune'):
            d.rectangle([9 * s, 16 * s, 23 * s, 18.5 * s], fill=glow if st == 'rune' else dark)
            if st == 'knight':
                d.rectangle([15 * s, 2 * s, 17 * s, 9 * s], fill=acc)
        else:
            d.rounded_rectangle([10 * s, 14 * s, 22 * s, 28 * s], radius=2 * s, fill=dark)
        if st == 'royal':
            d.rectangle([6 * s, 8 * s, 26 * s, 11 * s], fill=acc)
            for x in (8, 13, 18, 23):
                d.polygon([(x * s, 8 * s), ((x + 1.5) * s, 3 * s), ((x + 3) * s, 8 * s)], fill=acc)
        if st == 'devil':
            for sx in (-1, 1):
                cx = 16 + sx * 9
                d.polygon([(cx * s, 11 * s), ((cx + sx * 5) * s, 6 * s), ((cx + sx * 6) * s, 0.5 * s), ((cx + sx * 2) * s, 8 * s)], fill=acc)
        if st == 'abyssal':
            for x in (10, 14, 18, 22):
                d.polygon([(x * s, 8 * s), ((x + 1) * s, 2 * s), ((x + 2.5) * s, 8 * s)], fill=acc)
        if st == 'chitin':
            d.line([(12 * s, 8 * s), (8 * s, 1 * s)], fill=dark, width=int(1.4 * s))
            d.line([(20 * s, 8 * s), (24 * s, 1 * s)], fill=dark, width=int(1.4 * s))
        if st == 'shadow':
            d.rectangle([10 * s, 21 * s, 22 * s, 28 * s], fill=mid)
            d.rectangle([10 * s, 16 * s, 22 * s, 18 * s], fill=glow)

    def chest(d, s):
        d.polygon([(4 * s, 6 * s), (12 * s, 4 * s), (16 * s, 7 * s), (20 * s, 4 * s), (28 * s, 6 * s), (28 * s, 15 * s), (24 * s, 15 * s),
                   (24 * s, 29 * s), (8 * s, 29 * s), (8 * s, 15 * s), (4 * s, 15 * s)], fill=mid)
        d.rectangle([4 * s, 6 * s, 11 * s, 10 * s], fill=acc)
        d.rectangle([21 * s, 6 * s, 28 * s, 10 * s], fill=acc)
        d.rectangle([8 * s, 26 * s, 24 * s, 29 * s], fill=dark)
        d.polygon([(12 * s, 4 * s), (16 * s, 9 * s), (20 * s, 4 * s)], fill=dark)
        d.ellipse([13.5 * s, 14 * s, 18.5 * s, 19 * s], fill=glow)
        if st == 'mage':
            d.rectangle([15 * s, 9 * s, 17 * s, 29 * s], fill=acc)

    def legs(d, s):
        d.rectangle([7 * s, 4 * s, 25 * s, 9 * s], fill=dark)
        d.polygon([(7 * s, 9 * s), (15 * s, 9 * s), (14.5 * s, 29 * s), (8 * s, 29 * s)], fill=mid)
        d.polygon([(17 * s, 9 * s), (25 * s, 9 * s), (24 * s, 29 * s), (17.5 * s, 29 * s)], fill=mid)
        d.rectangle([8 * s, 17 * s, 14 * s, 20 * s], fill=acc)
        d.rectangle([18 * s, 17 * s, 24 * s, 20 * s], fill=acc)
        d.rectangle([15 * s, 5 * s, 17 * s, 8 * s], fill=glow)

    def boots(d, s):
        for x0 in (3, 17):
            d.polygon([(x0 * s, 8 * s), ((x0 + 7) * s, 8 * s), ((x0 + 7) * s, 22 * s), ((x0 + 12) * s, 24 * s), ((x0 + 12) * s, 28 * s),
                       (x0 * s, 28 * s)], fill=mid)
            d.rectangle([x0 * s, 8 * s, (x0 + 7) * s, 11 * s], fill=acc)
            d.rectangle([x0 * s, 26 * s, (x0 + 12) * s, 28.5 * s], fill=dark)
    fn = {'head': helmet, 'chest': chest, 'legs': legs, 'feet': boots}[slot]
    return _ic(fn)


def material_icons():
    def ingot(d, s):
        d.polygon([(4 * s, 20 * s), (10 * s, 12 * s), (28 * s, 12 * s), (22 * s, 20 * s)], fill=(160, 200, 240, 255))
        d.polygon([(4 * s, 20 * s), (22 * s, 20 * s), (22 * s, 26 * s), (4 * s, 26 * s)], fill=(90, 120, 170, 255))
        d.polygon([(22 * s, 20 * s), (28 * s, 12 * s), (28 * s, 18 * s), (22 * s, 26 * s)], fill=(60, 90, 140, 255))
        d.line([(12 * s, 16 * s), (22 * s, 16 * s)], fill=(124, 200, 255, 255), width=int(1.2 * s))

    def hide(d, s):
        d.polygon([(6 * s, 6 * s), (14 * s, 9 * s), (20 * s, 5 * s), (27 * s, 9 * s), (24 * s, 17 * s), (28 * s, 26 * s), (18 * s, 24 * s),
                   (12 * s, 28 * s), (5 * s, 22 * s), (8 * s, 15 * s)], fill=(110, 32, 44, 255))
        for x, y in ((12, 13), (19, 15), (14, 20)):
            d.ellipse([x * s, y * s, (x + 2.5) * s, (y + 2.5) * s], fill=(60, 14, 22, 255))
        d.line([(9 * s, 10 * s), (22 * s, 22 * s)], fill=(255, 74, 74, 255), width=int(0.8 * s))

    def silk(d, s):
        d.ellipse([5 * s, 7 * s, 27 * s, 27 * s], fill=(28, 26, 36, 255))
        d.ellipse([10 * s, 12 * s, 22 * s, 22 * s], fill=(70, 40, 110, 255))
        d.arc([7 * s, 9 * s, 25 * s, 25 * s], 200, 320, fill=(160, 96, 255, 255), width=int(1.4 * s))
        d.line([(22 * s, 24 * s), (29 * s, 30 * s)], fill=(28, 26, 36, 255), width=int(2 * s))

    def chitin(d, s):
        pts = [(16 + 12 * math.cos(math.radians(a)), 16 + 12 * math.sin(math.radians(a))) for a in range(30, 390, 60)]
        d.polygon([(x * s, y * s) for x, y in pts], fill=(213, 146, 46, 255))
        pts2 = [(16 + 7 * math.cos(math.radians(a)), 16 + 7 * math.sin(math.radians(a))) for a in range(30, 390, 60)]
        d.polygon([(x * s, y * s) for x, y in pts2], fill=(133, 80, 22, 255))
        d.line([(10 * s, 9 * s), (14 * s, 13 * s)], fill=(240, 184, 80, 255), width=int(1.2 * s))

    def shard(d, s):
        d.polygon([(16 * s, 2 * s), (25 * s, 12 * s), (21 * s, 29 * s), (9 * s, 27 * s), (7 * s, 11 * s)], fill=(97, 101, 111, 255))
        d.polygon([(16 * s, 2 * s), (25 * s, 12 * s), (16 * s, 15 * s)], fill=(145, 150, 161, 255))
        d.line([(12 * s, 12 * s), (12 * s, 22 * s), (18 * s, 22 * s)], fill=(96, 224, 255, 255), width=int(1.4 * s))
        d.line([(15 * s, 17 * s), (20 * s, 13 * s)], fill=(96, 224, 255, 255), width=int(1.4 * s))

    def thread(d, s):
        d.rectangle([9 * s, 5 * s, 23 * s, 8 * s], fill=(120, 80, 50, 255))
        d.rectangle([9 * s, 24 * s, 23 * s, 27 * s], fill=(120, 80, 50, 255))
        d.rectangle([11 * s, 8 * s, 21 * s, 24 * s], fill=(220, 110, 230, 255))
        for y in (10, 13, 16, 19, 22):
            d.line([(11 * s, y * s), (21 * s, (y + 1) * s)], fill=(255, 190, 255, 255), width=int(0.8 * s))
        d.line([(21 * s, 20 * s), (28 * s, 29 * s)], fill=(255, 156, 255, 255), width=int(1.0 * s))
    return {'mana_steel_ingot': _ic(ingot), 'devil_hide': _ic(hide), 'shadow_silk': _ic(silk), 'chitin_plate': _ic(chitin),
            'rune_shard': _ic(shard), 'arcane_thread': _ic(thread)}


GLYPHS = {
    'vitality': [((16, 9), (16, 23)), ((9, 16), (23, 16))],
    'warding': [((10, 9), (22, 9), (22, 17), (16, 24), (10, 17), (10, 9))],
    'mana': [((16, 8), (23, 16), (16, 24), (9, 16), (16, 8))],
    'swiftness': [((10, 22), (16, 10), (22, 22)), ((12, 17), (20, 17))],
    'thorns': [((16, 8), (16, 24)), ((16, 12), (10, 9)), ((16, 16), (22, 13)), ((16, 20), (10, 17))],
    'focus': [((16, 9), (16, 16), (21, 19))],
}


def rune_icons():
    out = {}
    for rid, (_, color, _, _) in RUNES.items():
        def fn(d, s, rid=rid, color=color):
            d.rounded_rectangle([5 * s, 4 * s, 27 * s, 29 * s], radius=6 * s, fill=(84, 88, 98, 255))
            d.rounded_rectangle([7 * s, 6 * s, 25 * s, 27 * s], radius=5 * s, fill=(112, 117, 128, 255))
            c = _t(color)
            for line in GLYPHS[rid]:
                d.line([(x * s, y * s) for x, y in line], fill=c, width=int(2.0 * s), joint='curve')
            if rid == 'focus':
                d.ellipse([10 * s, 10 * s, 22 * s, 22 * s], outline=c, width=int(1.6 * s))
        out[f'rune_{rid}'] = _ic(fn)
    return out


def forge_icon():
    def fn(d, s):
        d.rectangle([5 * s, 18 * s, 27 * s, 29 * s], fill=(77, 80, 89, 255))
        d.rectangle([4 * s, 16 * s, 28 * s, 19 * s], fill=(58, 61, 69, 255))
        d.ellipse([9 * s, 13 * s, 23 * s, 19 * s], fill=(60, 156, 240, 255))
        d.ellipse([12 * s, 14 * s, 20 * s, 17.5 * s], fill=(200, 236, 255, 255))
        d.polygon([(8 * s, 4 * s), (24 * s, 4 * s), (21 * s, 8 * s), (11 * s, 8 * s)], fill=(38, 38, 46, 255))
        d.rectangle([14 * s, 8 * s, 18 * s, 13 * s], fill=(38, 38, 46, 255))
        d.rectangle([12 * s, 23 * s, 20 * s, 26 * s], fill=(255, 140, 40, 255))
    return _ic(fn)


# ------------------------------------------------------------------------------------------------ the Magic Forge block
def forge_geo():
    g = Geo('geometry.bc.magic_forge', res=2, atlas_width=128, visible=(2, 2, (0, 0.5, 0)))
    g.bone('forge', pivot=(0, 0, 0))
    stone = tex.Stone(P['stone'])
    dark = tex.Metal(P['blackiron'])
    iron = tex.Metal(P['steel'])
    mana = tex.Energy(P['water'], alpha=255)
    ember = tex.Energy(P['flame'], alpha=255)
    gold = tex.Metal(P['gold'])
    g.cube('forge', (-8, 0, -8), (16, 7, 16), stone)                      # hearth
    g.cube('forge', (-8.2, 6.2, -8.2), (16.4, 1.2, 16.4), dark)            # rim
    g.cube('forge', (-3.0, 1.0, -8.3), (6.0, 3.6, 0.6), ember)             # fire mouth
    g.cube('forge', (-6.5, 7.4, -6.5), (6.0, 2.4, 6.0), dark)              # crucible
    g.cube('forge', (-5.5, 9.2, -5.5), (4.0, 0.6, 4.0), mana)              # molten mana
    g.cube('forge', (1.0, 7.4, -2.5), (5.0, 2.0, 4.0), dark)               # anvil base
    g.cube('forge', (1.8, 9.4, -1.5), (3.4, 1.6, 2.0), dark)
    g.cube('forge', (0.0, 11.0, -2.5), (7.2, 2.2, 4.0), iron)              # anvil face
    g.cube('forge', (7.2, 11.6, -1.5), (1.4, 1.2, 2.0), iron)              # horn
    g.cube('forge', (2.0, 13.2, -0.6), (3.6, 1.2, 1.2), gold, rotation=(0, 30, 0), pivot=(3.8, 13.8, 0))   # hammer head
    g.cube('forge', (3.4, 13.4, -2.8), (0.8, 0.8, 4.0), tex.Wood(P['wood']), rotation=(0, 30, 0), pivot=(3.8, 13.8, 0))
    for x, z in ((-7.5, 5.5), (5.5, 5.5)):
        g.cube('forge', (x, 7.4, z), (2.0, 5.0, 2.0), stone)               # chimney posts
    g.cube('forge', (-7.8, 12.4, 5.2), (15.6, 2.0, 2.6), stone)
    return g
