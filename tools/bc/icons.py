"""2D icons: misc items, HUD glyph font page, pack icons."""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from . import tex
from .data import ATTR_ORDER, ATTRIBUTES
from .tex import P, rgb

GLYPH_PAGE = 'E7'  # characters U+E700 - U+E7FF
ATTR_GLYPH0 = 0xA0   # attribute icons: 0xA0 - 0xBF
ATTR_GLYPH1 = 0x80   # attribute icons 33-48: 0x80 - 0x8F


def attr_glyph_index(i):
    return ATTR_GLYPH0 + i if i < 32 else ATTR_GLYPH1 + i - 32
FRUIT_GLYPH0 = 0xC0  # fruit icons: 0xC0 - 0xDF


def _crystal_icon():
    S = 32
    img = tex.new(S, S)

    def fn(d, s):
        cols = [(60, 30, 120, 255), (124, 74, 216, 255), (165, 124, 240, 255), (230, 214, 255, 255)]
        shards = [((16, 3), (22, 12), (19, 28), (12, 28), (10, 12)), ((8, 12), (12, 16), (11, 28), (6, 27), (5, 17)),
                  ((24, 11), (27, 17), (26, 27), (21, 28), (20, 16))]
        for k, poly in enumerate(shards):
            pts = [(x * s, y * s) for x, y in poly]
            d.polygon(pts, fill=cols[1 + (k == 0)])
            d.line([pts[0], pts[2]], fill=cols[3], width=int(s))
        d.polygon([(16 * s, 3 * s), (19 * s, 12 * s), (16 * s, 26 * s)], fill=cols[3])
    a = tex.draw_layer(S, S, fn, 4)
    a[..., 3] = np.where(a[..., 3] > 100, 255, 0)
    tex.outline(a, rgb('1a0a33'))
    return a


def _heart_icon():
    S = 32
    img = tex.new(S, S)

    def fn(d, s):
        d.ellipse([5 * s, 6 * s, 17 * s, 18 * s], fill=(110, 10, 20, 255))
        d.ellipse([15 * s, 6 * s, 27 * s, 18 * s], fill=(110, 10, 20, 255))
        d.polygon([(5.5 * s, 13 * s), (26.5 * s, 13 * s), (16 * s, 28 * s)], fill=(110, 10, 20, 255))
        d.ellipse([8 * s, 8 * s, 13 * s, 13 * s], fill=(200, 40, 50, 255))
        tex.clover_shape(d, 16 * s, 16 * s, 5 * s, 5, (20, 0, 0, 255), stem=False, devil=True)
    a = tex.draw_layer(S, S, fn, 4)
    a[..., 3] = np.where(a[..., 3] > 100, 255, 0)
    tex.outline(a, rgb('1a0003'))
    return a


def _charm_icon():
    S = 32

    def fn(d, s):
        d.ellipse([3 * s, 3 * s, 29 * s, 29 * s], outline=(240, 194, 74, 255), width=int(2.4 * s))
        tex.clover_shape(d, 16 * s, 15 * s, 9 * s, 4, (92, 184, 90, 255), stem=True)
        d.ellipse([14.5 * s, 13.5 * s, 17.5 * s, 16.5 * s], fill=(255, 246, 207, 255))
    a = tex.draw_layer(S, S, fn, 4)
    a[..., 3] = np.where(a[..., 3] > 100, 255, 0)
    tex.outline(a, rgb('0b2412'))
    return a


def _contract_icon():
    S = 32
    a = tex.new(S, S)
    yy, xx = np.mgrid[0:S, 0:S]
    paper = (xx >= 7) & (xx <= 25) & (yy >= 4) & (yy <= 28)
    t = 0.55 + tex.value_noise(S, S, 3, 5) * 0.2 - (yy - 4) / 60
    a[paper] = tex.quantize(tex.ramp('5a2a1a', '7d4a2e', 'a07050', 'c49a74'), np.clip(t, 0, 1))[paper]
    for y in range(8, 25, 3):
        a[y, 10:23] = rgb('2a0a08')
    lay = tex.draw_layer(S, S, lambda d, s: tex.clover_shape(d, 16 * s, 18 * s, 6.5 * s, 5, (200, 20, 30, 255), stem=False, devil=True), 4)
    lay[..., 3] = np.where(lay[..., 3] > 100, 255, 0)
    tex.alpha_over(a, lay)
    a[4:7, 6:27] = rgb('3a1a0e')
    a[26:29, 6:27] = rgb('3a1a0e')
    tex.outline(a, rgb('140504'))
    return a


def _handbook_icon():
    S = 32
    a = tex.new(S, S)
    a[4:28, 8:25] = rgb('6e432c')
    a[4:28, 8:10] = rgb('3a2214')
    a[5:27, 24:27] = rgb('e9dcb8')
    a[26:28, 9:27] = rgb('cdb98d')
    a[6, 11:23] = rgb('f0c24a')
    a[25, 11:23] = rgb('f0c24a')
    lay = tex.draw_layer(S, S, lambda d, s: d.regular_polygon((16.5 * s, 15.5 * s, 5.5 * s), 5, fill=(240, 194, 74, 255)), 4)
    lay[..., 3] = np.where(lay[..., 3] > 100, 255, 0)
    tex.alpha_over(a, lay)
    tex.outline(a, rgb('140a05'))
    return a


def misc_icons():
    return {'mana_crystal': _crystal_icon(), 'devil_heart': _heart_icon(), 'clover_charm': _charm_icon(),
            'devil_contract': _contract_icon(), 'handbook': _handbook_icon()}


# ======================================================================================
# HUD glyphs
# ======================================================================================
def _star_pts(cx, cy, ro, ri, n=5):
    pts = []
    for k in range(n * 2):
        r = ro if k % 2 == 0 else ri
        a = -math.pi / 2 + k * math.pi / n
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def _attr_glyph(attr):
    n = 16
    col = rgb(ATTRIBUTES[attr]['color'])
    c = tuple(int(v) for v in col[:3]) + (255,)
    dark = (20, 20, 26, 255)

    def fn(d, s):
        m = n * s
        if attr == 'wind':
            for k, r in enumerate((6.5, 4.5, 2.5)):
                d.arc([m / 2 - r * s, m / 2 - r * s, m / 2 + r * s, m / 2 + r * s], 200 + k * 40, 470 + k * 40, fill=c, width=int(1.6 * s))
        elif attr == 'flame':
            d.polygon([(8 * s, 1 * s), (13 * s, 9 * s), (12 * s, 14 * s), (4 * s, 14 * s), (3 * s, 9 * s), (6 * s, 6 * s)], fill=c)
            d.polygon([(8 * s, 6 * s), (10.5 * s, 11 * s), (8 * s, 14 * s), (5.5 * s, 11 * s)], fill=(255, 240, 180, 255))
        elif attr == 'water':
            d.ellipse([3.5 * s, 6 * s, 12.5 * s, 15 * s], fill=c)
            d.polygon([(8 * s, 1 * s), (12.2 * s, 9 * s), (3.8 * s, 9 * s)], fill=c)
            d.ellipse([5.5 * s, 9 * s, 7.5 * s, 11 * s], fill=(220, 240, 255, 255))
        elif attr == 'lightning':
            d.polygon([(10 * s, 0.5 * s), (3 * s, 9 * s), (7.5 * s, 9 * s), (5.5 * s, 15.5 * s), (13 * s, 6 * s), (8.5 * s, 6 * s)], fill=c)
        elif attr == 'light':
            for k in range(8):
                ang = k * math.pi / 4
                d.line([(8 * s, 8 * s), (8 * s + math.cos(ang) * 7 * s, 8 * s + math.sin(ang) * 7 * s)], fill=c, width=int(1.4 * s))
            d.ellipse([4.5 * s, 4.5 * s, 11.5 * s, 11.5 * s], fill=(255, 255, 255, 255))
        elif attr == 'dark':
            d.ellipse([2 * s, 2 * s, 14 * s, 14 * s], fill=c)
            d.ellipse([5 * s, 1 * s, 15 * s, 11 * s], fill=(0, 0, 0, 0))
        elif attr == 'ice':
            for k in range(3):
                ang = k * math.pi / 3 + math.pi / 2
                dx, dy = math.cos(ang) * 7 * s, math.sin(ang) * 7 * s
                d.line([(8 * s - dx, 8 * s - dy), (8 * s + dx, 8 * s + dy)], fill=c, width=int(1.8 * s))
            d.ellipse([6 * s, 6 * s, 10 * s, 10 * s], fill=(240, 252, 255, 255))
        elif attr == 'spatial':
            d.ellipse([2 * s, 2 * s, 14 * s, 14 * s], outline=c, width=int(2 * s))
            d.ellipse([5.5 * s, 5.5 * s, 10.5 * s, 10.5 * s], fill=(255, 220, 255, 255))
        elif attr == 'earth':
            d.polygon([(1 * s, 14 * s), (6 * s, 4 * s), (9 * s, 9 * s), (11 * s, 6 * s), (15 * s, 14 * s)], fill=c)
            d.polygon([(6 * s, 4 * s), (7.5 * s, 7 * s), (4.5 * s, 7 * s)], fill=(240, 230, 210, 255))
        elif attr == 'steel':
            d.polygon([(8 * s, 0.5 * s), (10 * s, 3 * s), (9.2 * s, 11 * s), (6.8 * s, 11 * s), (6 * s, 3 * s)], fill=c)
            d.rectangle([3.5 * s, 11 * s, 12.5 * s, 12.5 * s], fill=(200, 160, 60, 255))
            d.rectangle([7 * s, 12.5 * s, 9 * s, 15.5 * s], fill=(110, 80, 50, 255))
        elif attr == 'mirror':
            d.polygon([(8 * s, 1 * s), (14 * s, 8 * s), (8 * s, 15 * s), (2 * s, 8 * s)], fill=c)
            d.line([(5 * s, 6 * s), (8 * s, 3 * s)], fill=(255, 255, 255, 255), width=int(1.4 * s))
            d.line([(6 * s, 9 * s), (10 * s, 5 * s)], fill=(255, 255, 255, 255), width=int(1.2 * s))
        elif attr == 'sand':
            d.polygon([(0.5 * s, 14.5 * s), (5 * s, 7 * s), (9 * s, 11 * s), (12 * s, 6 * s), (15.5 * s, 14.5 * s)], fill=c)
            d.line([(5 * s, 7 * s), (7 * s, 9.5 * s)], fill=(255, 240, 200, 255), width=int(1.2 * s))
            for x, y in ((3, 3), (8, 2.5), (13, 3.5)):
                d.ellipse([(x - 0.9) * s, (y - 0.9) * s, (x + 0.9) * s, (y + 0.9) * s], fill=c)
        elif attr == 'bubble':
            for x, y, r in ((6, 9, 4.6), (11.5, 5, 3.0), (12, 12, 2.4)):
                d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s], outline=c, width=int(1.5 * s))
                d.ellipse([(x - r * 0.55) * s, (y - r * 0.6) * s, (x - r * 0.15) * s, (y - r * 0.2) * s], fill=(255, 255, 255, 255))
        elif attr == 'plant':
            d.polygon([(2 * s, 14 * s), (4 * s, 6 * s), (9 * s, 2 * s), (14 * s, 1.5 * s), (13 * s, 7 * s), (9 * s, 12 * s)], fill=c)
            d.line([(2.5 * s, 13.5 * s), (12.5 * s, 2.5 * s)], fill=(200, 255, 190, 255), width=int(1.2 * s))
        elif attr == 'poison':
            d.ellipse([3 * s, 6 * s, 13 * s, 15.5 * s], fill=c)
            d.rectangle([6.5 * s, 1.5 * s, 9.5 * s, 7 * s], fill=c)
            d.rectangle([5.5 * s, 0.8 * s, 10.5 * s, 2.4 * s], fill=(200, 200, 210, 255))
            for x, y, r in ((6, 11, 1.4), (10, 9.5, 1.0), (9, 13, 0.8)):
                d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s], fill=(40, 70, 10, 255))
        elif attr == 'blood':
            d.ellipse([3.5 * s, 6 * s, 12.5 * s, 15 * s], fill=c)
            d.polygon([(8 * s, 0.5 * s), (12.2 * s, 9 * s), (3.8 * s, 9 * s)], fill=c)
            d.ellipse([5.3 * s, 8.5 * s, 7.3 * s, 11 * s], fill=(255, 150, 160, 255))
            d.ellipse([10.2 * s, 10.5 * s, 11.6 * s, 12.5 * s], fill=(90, 0, 10, 255))
        elif attr == 'star':
            d.polygon(_star_pts(8 * s, 8.6 * s, 7.6 * s, 3.2 * s), fill=c)
            d.polygon(_star_pts(8 * s, 8.6 * s, 3.4 * s, 1.5 * s), fill=(255, 255, 255, 255))
        elif attr == 'sound':
            d.ellipse([2 * s, 10 * s, 7.5 * s, 14.5 * s], fill=c)
            d.rectangle([5.8 * s, 2 * s, 7.5 * s, 12.5 * s], fill=c)
            d.polygon([(7.5 * s, 2 * s), (13.5 * s, 4.5 * s), (13.5 * s, 7.5 * s), (7.5 * s, 5 * s)], fill=c)
            d.ellipse([10 * s, 9 * s, 14.5 * s, 12.5 * s], fill=c)
            d.rectangle([12.8 * s, 5 * s, 14.5 * s, 11 * s], fill=c)
        elif attr == 'mist':
            for k, y in enumerate((4, 8, 12)):
                pts = [((x / 2) * s, (y + math.sin(x * 0.6 + k) * 1.2) * s) for x in range(1, 32)]
                d.line(pts, fill=c, width=int(1.8 * s))
        elif attr == 'crystal':
            d.polygon([(8 * s, 0.5 * s), (11 * s, 5 * s), (10 * s, 15 * s), (6 * s, 15 * s), (5 * s, 5 * s)], fill=c)
            d.polygon([(3.5 * s, 6 * s), (5.5 * s, 9 * s), (5 * s, 15 * s), (2 * s, 15 * s), (1.5 * s, 9 * s)], fill=c)
            d.polygon([(12.5 * s, 5 * s), (14.5 * s, 8.5 * s), (14 * s, 15 * s), (11 * s, 15 * s), (10.8 * s, 8.5 * s)], fill=c)
            d.line([(8 * s, 1.5 * s), (8 * s, 14 * s)], fill=(230, 255, 248, 255), width=int(1.0 * s))
        elif attr == 'bone':
            for (x0, y0, x1, y1) in ((3, 3, 13, 13), (13, 3, 3, 13)):
                d.line([(x0 * s, y0 * s), (x1 * s, y1 * s)], fill=c, width=int(2.4 * s))
                for (x, y) in ((x0, y0), (x1, y1)):
                    for ox, oy in ((-1, 0.6), (0.6, -1)) if (x < 8) == (y < 8) else ((1, 0.6), (-0.6, -1)):
                        d.ellipse([(x + ox * 1.1 - 1.5) * s, (y + oy * 1.1 - 1.5) * s, (x + ox * 1.1 + 1.5) * s, (y + oy * 1.1 + 1.5) * s], fill=c)
        elif attr == 'magma':
            d.polygon([(0.5 * s, 15 * s), (5.5 * s, 5 * s), (10.5 * s, 5 * s), (15.5 * s, 15 * s)], fill=(70, 34, 24, 255))
            d.polygon([(5.5 * s, 5 * s), (10.5 * s, 5 * s), (9.5 * s, 9 * s), (8 * s, 12 * s), (6.8 * s, 8 * s)], fill=c)
            for x, y in ((6, 2), (8.5, 1), (11, 2.5)):
                d.ellipse([(x - 1) * s, (y - 1) * s, (x + 1) * s, (y + 1) * s], fill=(255, 200, 80, 255))
        elif attr == 'time':
            d.ellipse([1.5 * s, 1.5 * s, 14.5 * s, 14.5 * s], fill=(40, 30, 14, 255), outline=c, width=int(1.8 * s))
            d.line([(8 * s, 8 * s), (8 * s, 3.5 * s)], fill=c, width=int(1.5 * s))
            d.line([(8 * s, 8 * s), (11.5 * s, 9.5 * s)], fill=c, width=int(1.5 * s))
            for k in range(4):
                ang = k * math.pi / 2
                d.ellipse([(8 + math.cos(ang) * 5 - 0.7) * s, (8 + math.sin(ang) * 5 - 0.7) * s, (8 + math.cos(ang) * 5 + 0.7) * s, (8 + math.sin(ang) * 5 + 0.7) * s], fill=c)
        elif attr == 'cotton':
            for x, y, r in ((5, 9, 3.6), (9, 6, 3.8), (11.5, 10, 3.2), (7.5, 11.5, 3)):
                d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s], fill=c)
            d.ellipse([6 * s, 5 * s, 8.5 * s, 7.5 * s], fill=(255, 255, 255, 255))
        elif attr == 'paper':
            d.polygon([(2 * s, 10 * s), (8 * s, 2 * s), (14 * s, 10 * s), (8 * s, 8 * s)], fill=c)
            d.polygon([(2 * s, 10 * s), (8 * s, 8 * s), (8 * s, 14 * s)], fill=(200, 190, 160, 255))
            d.polygon([(14 * s, 10 * s), (8 * s, 8 * s), (8 * s, 14 * s)], fill=(230, 222, 196, 255))
        elif attr == 'smoke':
            for k, (x, y, r) in enumerate(((5, 12, 3.5), (9, 9, 3.8), (6, 5.5, 3), (11, 4, 2.4))):
                d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s], fill=tuple(int(v * (0.8 + k * 0.07)) for v in c[:3]) + (255,))
        elif attr == 'glass':
            d.rectangle([3 * s, 2 * s, 13 * s, 14 * s], outline=c, width=int(1.6 * s))
            d.line([(5 * s, 9 * s), (9 * s, 4 * s)], fill=(255, 255, 255, 255), width=int(1.2 * s))
            d.line([(7 * s, 12 * s), (11 * s, 7 * s)], fill=(255, 255, 255, 255), width=int(1 * s))
        elif attr == 'gold':
            d.ellipse([1.5 * s, 1.5 * s, 14.5 * s, 14.5 * s], fill=c)
            d.ellipse([4 * s, 4 * s, 12 * s, 12 * s], outline=(150, 100, 20, 255), width=int(1.2 * s))
            d.polygon(_star_pts(8 * s, 8.2 * s, 3 * s, 1.3 * s), fill=(255, 245, 200, 255))
        elif attr == 'beast':
            for k in range(3):
                x = 4 + k * 3.5
                d.polygon([(x * s, 2 * s), ((x + 2.2) * s, 2 * s), ((x + 0.8) * s, 14 * s)], fill=c)
            d.polygon([(13 * s, 3 * s), (15 * s, 3 * s), (13.6 * s, 12 * s)], fill=c)
        elif attr == 'spirit':
            d.ellipse([3 * s, 5 * s, 13 * s, 14 * s], fill=c)
            d.polygon([(4 * s, 9 * s), (8 * s, 0.5 * s), (12 * s, 9 * s)], fill=c)
            d.ellipse([5.5 * s, 8 * s, 7.3 * s, 10 * s], fill=(20, 60, 60, 255))
            d.ellipse([8.7 * s, 8 * s, 10.5 * s, 10 * s], fill=(20, 60, 60, 255))
        elif attr == 'gravity':
            d.ellipse([2 * s, 2 * s, 14 * s, 14 * s], outline=c, width=int(1.3 * s))
            d.ellipse([5 * s, 5 * s, 11 * s, 11 * s], outline=c, width=int(1.1 * s))
            d.ellipse([6.8 * s, 6.8 * s, 9.2 * s, 9.2 * s], fill=c)
            d.polygon([(8 * s, 15.5 * s), (6 * s, 12.5 * s), (10 * s, 12.5 * s)], fill=c)
        elif attr == 'moon':
            d.ellipse([1.5 * s, 1.5 * s, 14.5 * s, 14.5 * s], fill=c)
            d.ellipse([5 * s, 0 * s, 17 * s, 12 * s], fill=(0, 0, 0, 0))
            d.ellipse([4 * s, 9 * s, 5.6 * s, 10.6 * s], fill=(255, 255, 255, 255))
        elif attr == 'thorn':
            d.line([(3 * s, 14 * s), (13 * s, 2 * s)], fill=c, width=int(2.0 * s))
            for k in range(4):
                x = 4.5 + k * 2.5
                y = 12.2 - k * 3
                d.polygon([(x * s, y * s), ((x - 2.6) * s, (y - 1.6) * s), ((x - 0.4) * s, (y - 0.8) * s)], fill=c)
                d.polygon([((x + 0.6) * s, (y + 0.4) * s), ((x + 3) * s, (y + 1.4) * s), ((x + 1.2) * s, (y - 0.4) * s)], fill=c)
        elif attr == 'ash':
            for k, (x, y, r) in enumerate(((5, 11, 3.4), (10, 10, 3.6), (7.5, 6, 3))):
                d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s], fill=tuple(int(v * (0.75 + k * 0.1)) for v in c[:3]) + (255,))
            for x, y in ((4, 3), (12, 4.5), (9, 1.5)):
                d.ellipse([(x - 0.9) * s, (y - 0.9) * s, (x + 0.9) * s, (y + 0.9) * s], fill=(255, 150, 60, 255))
        elif attr == 'rune':
            d.ellipse([1.5 * s, 1.5 * s, 14.5 * s, 14.5 * s], outline=c, width=int(1.4 * s))
            d.line([(8 * s, 3 * s), (8 * s, 13 * s)], fill=c, width=int(1.4 * s))
            d.line([(8 * s, 6 * s), (11.5 * s, 3.5 * s)], fill=c, width=int(1.2 * s))
            d.line([(8 * s, 9 * s), (4.5 * s, 6.5 * s)], fill=c, width=int(1.2 * s))
            d.line([(8 * s, 11 * s), (11 * s, 13 * s)], fill=c, width=int(1.2 * s))
        else:  # anti-magic: black five-leaf devil clover on red
            d.ellipse([0.5 * s, 0.5 * s, 15.5 * s, 15.5 * s], fill=(150, 20, 26, 255))
            tex.clover_shape(d, 8 * s, 8.5 * s, 6.2 * s, 5, (5, 5, 5, 255), stem=False, devil=True)
    a = tex.draw_layer(n, n, fn, 4)
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    if attr != 'anti':
        tex.outline(a, rgb('101016'))
    return a


def _pip(kind, palette):
    a = tex.new(16, 16)
    fill_c, hi_c, empty_c, edge_c = palette
    a[3:13, 0:6] = edge_c
    inner = a[4:12, 1:5]
    if kind == 'full':
        inner[:] = fill_c
        inner[0:2, :] = hi_c
    elif kind == 'half':
        inner[:] = empty_c
        inner[4:, :] = fill_c
    else:
        inner[:] = empty_c
    return a


def _cap(side, edge_c):
    a = tex.new(16, 16)
    if side == 'left':
        a[2:14, 0:2] = edge_c
        a[2:3, 0:3] = edge_c
        a[13:14, 0:3] = edge_c
    else:
        a[2:14, 1:3] = edge_c
        a[2:3, 0:3] = edge_c
        a[13:14, 0:3] = edge_c
    return a


def glyph_page():
    page = tex.new(256, 256)

    def put(idx, cell):
        r, c = divmod(idx, 16)
        page[r * 16:(r + 1) * 16, c * 16:(c + 1) * 16] = cell
    for i, attr in enumerate(ATTR_ORDER):
        put(attr_glyph_index(i), _attr_glyph(attr))
    mana = (rgb('3ca8ff'), rgb('c8ecff'), rgb('16243a'), rgb('0a0f18'))
    anti = (rgb('d0202a'), rgb('ff7a7a'), rgb('1a0a0c'), rgb('050505'))
    put(0x10, _cap('left', rgb('c9d4e6')))
    put(0x11, _pip('full', mana))
    put(0x12, _pip('half', mana))
    put(0x13, _pip('empty', mana))
    put(0x14, _cap('right', rgb('c9d4e6')))
    put(0x15, _pip('full', anti))
    put(0x16, _pip('half', anti))
    put(0x17, _pip('empty', anti))
    for i, leaves in enumerate((3, 4, 5)):
        cell = tex.draw_layer(16, 16, lambda d, s, L=leaves: tex.clover_shape(d, 8 * s, 7.5 * s, 6 * s, L, (92, 184, 90, 255) if L < 5 else (20, 20, 20, 255), stem=True, devil=L == 5), 4)
        cell[..., 3] = np.where(cell[..., 3] > 110, 255, 0)
        tex.outline(cell, rgb('0b2412') if leaves < 5 else rgb('a01818'))
        put(0x18 + i, cell)
    star = tex.draw_layer(16, 16, lambda d, s: d.regular_polygon((8 * s, 8.5 * s, 7 * s), 5, fill=(255, 210, 70, 255)), 4)
    star[..., 3] = np.where(star[..., 3] > 110, 255, 0)
    tex.outline(star, rgb('5a3a00'))
    put(0x20, star)
    hour = tex.draw_layer(16, 16, lambda d, s: (d.polygon([(3 * s, 1 * s), (13 * s, 1 * s), (8 * s, 8 * s)], fill=(200, 200, 210, 255)),
                                                d.polygon([(3 * s, 15 * s), (13 * s, 15 * s), (8 * s, 8 * s)], fill=(140, 140, 150, 255))), 4)
    hour[..., 3] = np.where(hour[..., 3] > 110, 255, 0)
    put(0x21, hour)
    lock = tex.new(16, 16)
    lock[7:15, 3:13] = rgb('8a8f9c')
    lock[3:8, 4:6] = rgb('8a8f9c')
    lock[3:8, 10:12] = rgb('8a8f9c')
    lock[2:4, 5:11] = rgb('8a8f9c')
    lock[10:12, 7:9] = rgb('2a2e36')
    put(0x22, lock)
    return page


def glyph(idx):
    return chr(0xE700 + idx)


# ======================================================================================
# pack icon
# ======================================================================================
def pack_icon(render_img: Image.Image | None = None):
    S = 256
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    d = np.sqrt((xx - S / 2) ** 2 + (yy - S / 2) ** 2) / (S / 1.4)
    bg = tex.smooth_ramp(tex.ramp('2a0a10', '160610', '08040a', '030203'), np.clip(d, 0, 1))
    bg[..., 3] = 255
    a = bg
    ring = tex.rune_ring(S, S, (200, 40, 50, 255), 3, ss=2, thickness=2.5, rings=2, glyphs=16)
    ring[..., 3] *= 0.55
    tex.alpha_over(a, ring)
    clover = tex.draw_layer(S, S, lambda dr, s: tex.clover_shape(dr, 128 * s, 120 * s, 70 * s, 5, (10, 10, 12, 255), stem=True, devil=True), 2)
    edge = clover.copy()
    edge[..., :3] = (220, 40, 50)
    edge = tex.glow(edge, 4, 1.0)
    tex.alpha_over(a, edge)
    tex.alpha_over(a, clover)
    img = tex.to_image(a)
    if render_img is not None:
        img.alpha_composite(render_img.resize((S, S), Image.LANCZOS))
    return img


# ======================================================================================
# Abyssal Seas icons
# ======================================================================================
def _finish(a, outline='0a0a0f'):
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    tex.outline(a, rgb(outline))
    return a


def fruit_icon(fid, S=32):
    s4 = 4

    def fn(d, s):
        def P_(x, y):
            return (x * s, y * s)
        if fid == 'ember':
            d.polygon([P_(16, 6), P_(22, 13), P_(23, 21), P_(19, 27), P_(13, 27), P_(9, 21), P_(10, 13)], fill=(220, 70, 20, 255))
            d.polygon([P_(16, 10), P_(19, 16), P_(18, 23), P_(16, 25), P_(14, 23), P_(13, 16)], fill=(255, 150, 40, 255))
            for x0, y0, x1, y1 in ((16, 9, 14, 24), (16, 9, 19, 23), (12, 15, 11, 22), (20, 15, 21, 22)):
                d.line([P_(x0, y0), P_(x1, y1)], fill=(255, 235, 140, 255), width=int(0.9 * s))
            d.polygon([P_(16, 7), P_(13, 3), P_(18, 2), P_(19, 5)], fill=(60, 120, 40, 255))
        elif fid == 'stone':
            d.ellipse([P_(6, 8), P_(26, 28)], fill=(110, 102, 92, 255))
            for (x, y, r) in ((11, 14, 4), (19, 12, 4), (21, 21, 4.5), (12, 22, 4), (16, 17, 3)):
                d.ellipse([P_(x - r, y - r), P_(x + r, y + r)], fill=(150, 140, 126, 255), outline=(70, 64, 58, 255), width=int(0.8 * s))
            d.line([P_(16, 9), P_(14, 15), P_(17, 19), P_(15, 26)], fill=(255, 170, 60, 255), width=int(0.9 * s))
            d.polygon([P_(16, 8), P_(14, 3), P_(19, 4)], fill=(80, 110, 50, 255))
        elif fid == 'gravity':
            d.ellipse([P_(8, 8), P_(24, 24)], fill=(60, 30, 120, 255))
            d.ellipse([P_(10, 10), P_(17, 17)], fill=(140, 100, 255, 255))
            d.arc([P_(3, 12), P_(29, 21)], 160, 380, fill=(200, 180, 255, 255), width=int(1.2 * s))
            for x, y in ((6, 6), (26, 8), (25, 26), (5, 25)):
                d.ellipse([P_(x - 0.8, y - 0.8), P_(x + 0.8, y + 0.8)], fill=(255, 255, 255, 255))
            d.polygon([P_(16, 8), P_(15, 4), P_(19, 5)], fill=(90, 70, 140, 255))
        elif fid == 'shadow':
            for k in range(4):
                d.polygon([P_(9 + k * 4, 12), P_(8 + k * 4, 3 + (k % 2) * 2), P_(11 + k * 4, 11)], fill=(30, 20, 50, 255))
            d.ellipse([P_(7, 9), P_(25, 28)], fill=(18, 12, 30, 255))
            d.ellipse([P_(11, 16), P_(21, 21)], fill=(170, 90, 255, 255))
            d.ellipse([P_(14.5, 16.5), P_(17.5, 20.5)], fill=(20, 0, 30, 255))
        elif fid == 'bloom':
            d.ellipse([P_(8, 11), P_(24, 28)], fill=(70, 170, 70, 255))
            d.ellipse([P_(11, 14), P_(17, 20)], fill=(140, 220, 120, 255))
            for k in range(5):
                a = math.radians(-90 + (k - 2) * 32)
                cx, cy = 16 + math.cos(a) * 6, 10 + math.sin(a) * 4
                d.ellipse([P_(cx - 3, cy - 3), P_(cx + 3, cy + 3)], fill=(240, 120, 170, 255))
            d.ellipse([P_(14, 7), P_(18, 11)], fill=(255, 220, 90, 255))
        elif fid == 'frost':
            d.polygon([P_(16, 4), P_(25, 14), P_(22, 27), P_(10, 27), P_(7, 14)], fill=(150, 220, 250, 255))
            d.polygon([P_(16, 7), P_(21, 14), P_(16, 25), P_(11, 14)], fill=(230, 250, 255, 255))
            for x0, y0, x1, y1 in ((16, 8, 16, 24), (10, 16, 22, 16)):
                d.line([P_(x0, y0), P_(x1, y1)], fill=(80, 170, 220, 255), width=int(0.9 * s))
            d.polygon([P_(16, 5), P_(14, 2), P_(18, 2)], fill=(90, 140, 160, 255))
        elif fid == 'barrier':
            d.rounded_rectangle([P_(7, 8), P_(25, 27)], radius=5 * s, fill=(240, 220, 120, 255))
            d.rounded_rectangle([P_(10, 11), P_(22, 24)], radius=3 * s, outline=(255, 250, 220, 255), width=int(1.3 * s))
            d.line([P_(16, 11), P_(16, 24)], fill=(200, 170, 70, 255), width=int(s))
            d.polygon([P_(16, 8), P_(14, 3), P_(19, 4)], fill=(110, 140, 60, 255))
        elif fid == 'wolf':
            d.ellipse([P_(7, 9), P_(25, 28)], fill=(150, 140, 125, 255))
            d.polygon([P_(9, 12), P_(10, 4), P_(14, 10)], fill=(150, 140, 125, 255))
            d.polygon([P_(23, 12), P_(22, 4), P_(18, 10)], fill=(150, 140, 125, 255))
            for k in range(3):
                d.line([P_(11 + k * 4, 15), P_(13 + k * 4, 24)], fill=(80, 70, 60, 255), width=int(1.1 * s))
            d.ellipse([P_(12, 13), P_(15, 16)], fill=(255, 210, 80, 255))
            d.ellipse([P_(18, 13), P_(21, 16)], fill=(255, 210, 80, 255))
        elif fid == 'hawk':
            d.ellipse([P_(9, 9), P_(23, 28)], fill=(200, 140, 70, 255))
            for k in range(4):
                d.polygon([P_(9 - k, 14 + k * 3), P_(2, 11 + k * 3), P_(9, 17 + k * 3)], fill=(150, 100, 50, 255))
                d.polygon([P_(23 + k, 14 + k * 3), P_(30, 11 + k * 3), P_(23, 17 + k * 3)], fill=(150, 100, 50, 255))
            d.polygon([P_(16, 15), P_(19, 18), P_(16, 22), P_(13, 18)], fill=(250, 220, 120, 255))
            d.polygon([P_(16, 9), P_(15, 4), P_(18, 5)], fill=(90, 120, 50, 255))
        elif fid == 'lava':
            d.ellipse([P_(6, 8), P_(26, 28)], fill=(46, 22, 18, 255))
            for pts in (((16, 9), (13, 15), (17, 19), (14, 27)), ((9, 16), (13, 18), (11, 24)), ((23, 14), (19, 19), (22, 25))):
                d.line([P_(*q) for q in pts], fill=(255, 110, 30, 255), width=int(1.4 * s))
            d.ellipse([P_(10, 11), P_(14, 14)], fill=(255, 180, 70, 255))
            d.polygon([P_(16, 8), P_(13, 3), P_(19, 4)], fill=(70, 50, 30, 255))
        elif fid == 'ash':
            d.ellipse([P_(7, 10), P_(25, 28)], fill=(118, 118, 128, 255))
            d.ellipse([P_(10, 13), P_(16, 18)], fill=(170, 170, 180, 255))
            for k in range(3):
                d.arc([P_(9 + k * 5, 1 + k), P_(16 + k * 5, 10 + k)], 180, 360, fill=(90, 90, 100, 255), width=int(1.2 * s))
            for x, y in ((12, 22), (19, 20), (16, 25)):
                d.ellipse([P_(x - 1, y - 1), P_(x + 1, y + 1)], fill=(255, 120, 40, 255))
        elif fid == 'prism':
            pts = [P_(16, 4), P_(25, 12), P_(22, 27), P_(10, 27), P_(7, 12)]
            d.polygon(pts, fill=(220, 160, 255, 255))
            cols = [(255, 90, 90, 255), (255, 200, 60, 255), (90, 230, 120, 255), (80, 170, 255, 255), (190, 110, 255, 255)]
            for k in range(5):
                a, b = pts[k], pts[(k + 1) % 5]
                d.polygon([P_(16, 16), a, b], fill=cols[k])
            d.polygon([P_(16, 9), P_(20, 14), P_(16, 19), P_(12, 14)], fill=(255, 255, 255, 255))
        elif fid == 'bounce':
            d.ellipse([P_(7, 8), P_(25, 27)], fill=(255, 140, 190, 255))
            for k in range(4):
                d.arc([P_(7, 9 + k * 4), P_(25, 14 + k * 4)], 0, 180, fill=(200, 70, 130, 255), width=int(1.2 * s))
            d.ellipse([P_(11, 11), P_(15, 14)], fill=(255, 220, 235, 255))
            d.polygon([P_(16, 8), P_(14, 3), P_(19, 4)], fill=(80, 130, 60, 255))
        elif fid == 'blast':
            d.ellipse([P_(7, 10), P_(25, 28)], fill=(240, 150, 30, 255))
            d.ellipse([P_(10, 13), P_(15, 18)], fill=(255, 220, 120, 255))
            d.line([P_(16, 10), P_(18, 5), P_(22, 3)], fill=(90, 70, 50, 255), width=int(1.4 * s))
            for k in range(6):
                a = math.radians(k * 60)
                d.line([P_(22, 3), P_(22 + math.cos(a) * 3, 3 + math.sin(a) * 3)], fill=(255, 240, 120, 255), width=int(0.9 * s))
        elif fid == 'acid':
            d.ellipse([P_(7, 9), P_(25, 26)], fill=(140, 230, 50, 255))
            d.polygon([P_(13, 24), P_(15, 30), P_(17, 24)], fill=(140, 230, 50, 255))
            for x, y, r in ((12, 14, 2), (19, 17, 2.6), (14, 20, 1.4), (20, 12, 1.2)):
                d.ellipse([P_(x - r, y - r), P_(x + r, y + r)], fill=(210, 255, 150, 255), outline=(70, 130, 20, 255), width=int(0.6 * s))
            d.polygon([P_(16, 9), P_(14, 4), P_(19, 5)], fill=(60, 100, 40, 255))
        elif fid == 'lodestone':
            d.arc([P_(6, 6), P_(26, 26)], 180, 360, fill=(190, 70, 60, 255), width=int(6 * s))
            d.rectangle([P_(6, 15), P_(12, 24)], fill=(190, 70, 60, 255))
            d.rectangle([P_(20, 15), P_(26, 24)], fill=(190, 70, 60, 255))
            d.rectangle([P_(6, 22), P_(12, 27)], fill=(210, 215, 225, 255))
            d.rectangle([P_(20, 22), P_(26, 27)], fill=(210, 215, 225, 255))
            d.arc([P_(9, 9), P_(23, 23)], 200, 260, fill=(255, 160, 150, 255), width=int(1.2 * s))
        elif fid == 'cloud':
            for x, y, r in ((11, 18, 6), (18, 15, 7), (23, 20, 5), (15, 22, 6)):
                d.ellipse([P_(x - r, y - r), P_(x + r, y + r)], fill=(236, 242, 255, 255))
            for x, y, r in ((10, 16, 2.5), (17, 12, 2.5)):
                d.ellipse([P_(x - r, y - r), P_(x + r, y + r)], fill=(255, 255, 255, 255))
            d.arc([P_(8, 18), P_(28, 28)], 0, 180, fill=(170, 180, 210, 255), width=int(1.2 * s))
            d.polygon([P_(18, 8), P_(16, 3), P_(21, 4)], fill=(90, 130, 70, 255))
        elif fid == 'ink':
            d.ellipse([P_(7, 11), P_(25, 28)], fill=(50, 40, 90, 255))
            d.polygon([P_(16, 3), P_(23.5, 16), P_(8.5, 16)], fill=(50, 40, 90, 255))
            d.arc([P_(11, 14), P_(21, 24)], 30, 300, fill=(140, 120, 220, 255), width=int(1.4 * s))
            d.ellipse([P_(15, 18), P_(17, 20)], fill=(140, 120, 220, 255))
        elif fid == 'bear':
            d.ellipse([P_(7, 9), P_(25, 28)], fill=(138, 90, 58, 255))
            for x in (9, 23):
                d.ellipse([P_(x - 3.5, 5.5), P_(x + 3.5, 12.5)], fill=(138, 90, 58, 255))
                d.ellipse([P_(x - 1.6, 7.4), P_(x + 1.6, 10.6)], fill=(90, 56, 34, 255))
            d.ellipse([P_(12, 17), P_(20, 25)], fill=(90, 56, 34, 255))
            for k in range(4):
                d.ellipse([P_(11 + k * 2.6, 13), P_(13 + k * 2.6, 16)], fill=(90, 56, 34, 255))
        elif fid == 'tiger':
            d.ellipse([P_(7, 9), P_(25, 28)], fill=(255, 150, 40, 255))
            d.polygon([P_(8, 13), P_(9, 5), P_(14, 10)], fill=(255, 150, 40, 255))
            d.polygon([P_(24, 13), P_(23, 5), P_(18, 10)], fill=(255, 150, 40, 255))
            for y in (13, 18, 23):
                d.polygon([P_(7, y), P_(13, y + 1), P_(7, y + 2.4)], fill=(30, 20, 14, 255))
                d.polygon([P_(25, y), P_(19, y + 1), P_(25, y + 2.4)], fill=(30, 20, 14, 255))
            d.polygon([P_(16, 9), P_(15, 15), P_(17, 15)], fill=(30, 20, 14, 255))
        elif fid == 'wyvern':
            for sx in (-1, 1):
                d.polygon([P_(16 + sx * 6, 14), P_(16 + sx * 15, 6), P_(16 + sx * 13, 13), P_(16 + sx * 14, 19)], fill=(60, 140, 100, 255))
            d.ellipse([P_(9, 10), P_(23, 28)], fill=(90, 180, 138, 255))
            for k in range(3):
                d.arc([P_(11, 13 + k * 4), P_(21, 19 + k * 4)], 0, 180, fill=(40, 100, 70, 255), width=int(1.0 * s))
            d.polygon([P_(13, 11), P_(12, 5), P_(15, 10)], fill=(220, 210, 180, 255))
            d.polygon([P_(19, 11), P_(20, 5), P_(17, 10)], fill=(220, 210, 180, 255))
        elif fid == 'spore':
            d.ellipse([P_(6, 6), P_(26, 18)], fill=(190, 140, 90, 255))
            for x, y in ((11, 10), (17, 8), (21, 12), (14, 14)):
                d.ellipse([P_(x - 1.6, y - 1.6), P_(x + 1.6, y + 1.6)], fill=(250, 235, 200, 255))
            d.rectangle([P_(13, 17), P_(19, 28)], fill=(230, 215, 180, 255))
        elif fid == 'thread':
            d.ellipse([P_(7, 8), P_(25, 27)], fill=(225, 225, 235, 255))
            for k in range(6):
                d.arc([P_(7, 6 + k * 3), P_(25, 14 + k * 3)], 200, 340, fill=(150, 150, 170, 255), width=int(0.8 * s))
            d.line([P_(24, 18), P_(30, 30)], fill=(200, 200, 215, 255), width=int(0.8 * s))
        elif fid == 'slime':
            d.rounded_rectangle([P_(6, 9), P_(26, 27)], radius=6 * s, fill=(90, 220, 90, 255))
            d.rounded_rectangle([P_(10, 12), P_(22, 23)], radius=3 * s, fill=(60, 170, 60, 255))
            d.ellipse([P_(11, 13), P_(14, 16)], fill=(220, 255, 220, 255))
            d.polygon([P_(16, 9), P_(14, 4), P_(19, 5)], fill=(60, 110, 50, 255))
        elif fid == 'chain':
            for k in range(3):
                y = 6 + k * 7
                d.ellipse([P_(9 + (k % 2) * 4, y), P_(19 + (k % 2) * 4, y + 9)], outline=(160, 160, 170, 255), width=int(2.4 * s))
        elif fid == 'lion':
            for k in range(12):
                a = math.radians(k * 30)
                d.ellipse([P_(16 + math.cos(a) * 8 - 4, 17 + math.sin(a) * 8 - 4), P_(16 + math.cos(a) * 8 + 4, 17 + math.sin(a) * 8 + 4)], fill=(200, 110, 30, 255))
            d.ellipse([P_(9, 10), P_(23, 24)], fill=(240, 180, 70, 255))
            d.polygon([P_(14, 18), P_(18, 18), P_(16, 21)], fill=(80, 40, 20, 255))
        elif fid == 'shark':
            d.ellipse([P_(5, 11), P_(27, 25)], fill=(80, 130, 200, 255))
            d.polygon([P_(14, 11), P_(19, 3), P_(21, 12)], fill=(60, 110, 180, 255))
            d.polygon([P_(8, 21), P_(24, 21), P_(22, 24), P_(10, 24)], fill=(240, 240, 250, 255))
            for k in range(5):
                d.polygon([P_(10 + k * 3, 21), P_(11.5 + k * 3, 23), P_(13 + k * 3, 21)], fill=(255, 255, 255, 255))
        elif fid == 'phoenix':
            d.polygon([P_(16, 2), P_(25, 14), P_(22, 28), P_(10, 28), P_(7, 14)], fill=(255, 120, 40, 255))
            d.polygon([P_(16, 8), P_(21, 16), P_(18, 26), P_(14, 26), P_(11, 16)], fill=(255, 210, 90, 255))
            d.polygon([P_(16, 14), P_(18, 20), P_(16, 24), P_(14, 20)], fill=(140, 200, 255, 255))
        elif fid == 'spider':
            for k in range(4):
                for sx in (-1, 1):
                    d.line([P_(16 + sx * 5, 14 + k * 3), P_(16 + sx * 13, 9 + k * 5)], fill=(60, 30, 60, 255), width=int(1.2 * s))
            d.ellipse([P_(9, 10), P_(23, 27)], fill=(120, 70, 140, 255))
            for x in (13, 16, 19):
                d.ellipse([P_(x - 1, 13), P_(x + 1, 15)], fill=(255, 60, 60, 255))
        else:  # quicksilver
            d.ellipse([P_(8, 12), P_(24, 28)], fill=(170, 180, 196, 255))
            d.polygon([P_(16, 3), P_(23.5, 17), P_(8.5, 17)], fill=(170, 180, 196, 255))
            d.ellipse([P_(11, 15), P_(16, 21)], fill=(250, 252, 255, 255))
            d.arc([P_(10, 16), P_(22, 27)], 20, 120, fill=(90, 98, 112, 255), width=int(1.2 * s))
    a = tex.draw_layer(S, S, fn, s4)
    return _finish(a)


def power_icon(fid, color_hex, S=32):
    col = tuple(int(color_hex[i:i + 2], 16) for i in (0, 2, 4))

    def fn(d, s):
        d.ellipse([2 * s, 2 * s, 30 * s, 30 * s], fill=(16, 14, 22, 255), outline=col + (255,), width=int(2.2 * s))
        # clenched fist
        d.rounded_rectangle([10 * s, 11 * s, 22 * s, 22 * s], radius=3 * s, fill=(220, 180, 140, 255))
        for k in range(4):
            d.ellipse([(10 + k * 3) * s, 9 * s, (13 + k * 3) * s, 13 * s], fill=(235, 196, 156, 255))
        d.rectangle([12 * s, 21 * s, 20 * s, 26 * s], fill=(200, 160, 120, 255))
        d.line([(10 * s, 16 * s), (15 * s, 17 * s)], fill=(160, 120, 90, 255), width=int(s))
    a = tex.draw_layer(S, S, fn, 4)
    a = _finish(a)
    g = a.copy()
    g[..., :3] = np.array(col)
    g = tex.glow(g, 2.0, 0.7)
    tex.alpha_over(g, a)
    return g


def coin_icon(S=32):
    def fn(d, s):
        d.ellipse([4 * s, 4 * s, 28 * s, 28 * s], fill=(200, 140, 30, 255))
        d.ellipse([6 * s, 6 * s, 26 * s, 26 * s], fill=(240, 194, 74, 255))
        d.line([(16 * s, 10 * s), (16 * s, 22 * s)], fill=(150, 100, 20, 255), width=int(1.4 * s))
        d.arc([10 * s, 15 * s, 22 * s, 24 * s], 20, 160, fill=(150, 100, 20, 255), width=int(1.4 * s))
        tex.clover_shape(d, 16 * s, 11.5 * s, 3.4 * s, 4, (120, 80, 14, 255), stem=False)
        d.arc([7 * s, 7 * s, 25 * s, 25 * s], 200, 260, fill=(255, 246, 207, 255), width=int(1.4 * s))
    return _finish(tex.draw_layer(S, S, fn, 4), '3a2400')


def cannonball_icon(S=32):
    def fn(d, s):
        d.ellipse([6 * s, 6 * s, 26 * s, 26 * s], fill=(34, 36, 42, 255))
        d.ellipse([9 * s, 9 * s, 15 * s, 15 * s], fill=(110, 116, 128, 255))
        d.ellipse([10 * s, 10 * s, 13 * s, 13 * s], fill=(200, 205, 215, 255))
    return _finish(tex.draw_layer(S, S, fn, 4))


def ship_kit_icon(S=32):
    def fn(d, s):
        d.polygon([(3 * s, 20 * s), (29 * s, 20 * s), (25 * s, 27 * s), (7 * s, 27 * s)], fill=(92, 60, 34, 255))
        d.rectangle([3 * s, 20 * s, 29 * s, 21.5 * s], fill=(211, 154, 44, 255))
        d.rectangle([15 * s, 3 * s, 16.6 * s, 20 * s], fill=(70, 46, 26, 255))
        d.polygon([(8 * s, 6 * s), (24 * s, 6 * s), (23 * s, 17 * s), (9 * s, 17 * s)], fill=(236, 238, 242, 255))
        tex.clover_shape(d, 16 * s, 11 * s, 3 * s, 4, (30, 110, 52, 255), stem=False)
        d.polygon([(17 * s, 2 * s), (22 * s, 3.5 * s), (17 * s, 5 * s)], fill=(20, 20, 24, 255))
    return _finish(tex.draw_layer(S, S, fn, 4))


def lure_icon(S=32):
    def fn(d, s):
        d.polygon([(6 * s, 22 * s), (12 * s, 8 * s), (24 * s, 6 * s), (27 * s, 16 * s), (18 * s, 27 * s)], fill=(236, 200, 186, 255))
        for k in range(4):
            d.arc([(9 + k * 2) * s, (9 + k * 2) * s, (25 - k * 2) * s, (25 - k * 2) * s], 200 + k * 20, 330, fill=(190, 120, 120, 255), width=int(1.2 * s))
        d.ellipse([16 * s, 13 * s, 21 * s, 18 * s], fill=(120, 255, 232, 255))
    a = tex.draw_layer(S, S, fn, 4)
    return _finish(a, '3a1a1a')


def scale_icon(S=32):
    def fn(d, s):
        d.polygon([(16 * s, 3 * s), (26 * s, 14 * s), (22 * s, 27 * s), (10 * s, 27 * s), (6 * s, 14 * s)], fill=(24, 88, 107, 255))
        d.polygon([(16 * s, 6 * s), (22 * s, 14 * s), (19 * s, 24 * s), (16 * s, 25 * s)], fill=(53, 146, 163, 255))
        d.line([(16 * s, 5 * s), (16 * s, 26 * s)], fill=(140, 220, 225, 255), width=int(s))
    return _finish(tex.draw_layer(S, S, fn, 4), '04141c')


def sea_icons():
    from .data import FRUITS
    out = {f'fruit_{k}': fruit_icon(k) for k in FRUITS}
    out.update({f'power_{k}': power_icon(k, v['color']) for k, v in FRUITS.items()})
    out.update({'doubloon': coin_icon(), 'cannonball': cannonball_icon(), 'ship_kit': ship_kit_icon(),
                'leviathan_lure': lure_icon(), 'leviathan_scale': scale_icon()})
    return out


def sea_glyphs(page):
    """Add fruit, Will, coin and compass-arrow glyphs to the HUD font page."""
    from .data import FRUIT_ORDER

    def put(idx, cell):
        r, c = divmod(idx, 16)
        page[r * 16:(r + 1) * 16, c * 16:(c + 1) * 16] = cell
    for i, fid in enumerate(FRUIT_ORDER):
        img = tex.to_image(fruit_icon(fid)).resize((16, 16), Image.LANCZOS)
        cell = tex.from_image(img)
        cell[..., 3] = np.where(cell[..., 3] > 100, 255, 0)
        put(FRUIT_GLYPH0 + i, cell)
    will = tex.draw_layer(16, 16, lambda d, s: (d.polygon([(8 * s, 1 * s), (12 * s, 7 * s), (10 * s, 15 * s), (6 * s, 15 * s), (4 * s, 7 * s)], fill=(120, 60, 200, 255)),
                                                d.polygon([(8 * s, 5 * s), (10 * s, 9 * s), (8 * s, 13 * s), (6 * s, 9 * s)], fill=(235, 220, 255, 255))), 4)
    put(0x36, _finish(will, '120820'))
    put(0x37, tex.from_image(tex.to_image(coin_icon()).resize((16, 16), Image.LANCZOS)))
    for k in range(8):
        ang = k * 45

        def arrow(d, s, ang=ang):
            r = math.radians(ang - 90)
            cx, cy = 8 * s, 8 * s
            tip = (cx + math.cos(r) * 6.5 * s, cy + math.sin(r) * 6.5 * s)
            left = (cx + math.cos(r + 2.5) * 5.5 * s, cy + math.sin(r + 2.5) * 5.5 * s)
            right = (cx + math.cos(r - 2.5) * 5.5 * s, cy + math.sin(r - 2.5) * 5.5 * s)
            d.polygon([tip, left, (cx, cy), right], fill=(255, 210, 70, 255))
        put(0x40 + k, _finish(tex.draw_layer(16, 16, arrow, 4), '3a2400'))
    return page
