"""2D icons: misc items, HUD glyph font page, pack icons."""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from . import tex
from .data import ATTR_ORDER, ATTRIBUTES
from .tex import P, rgb

GLYPH_PAGE = 'E7'  # characters U+E700 - U+E7FF


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
        put(i, _attr_glyph(attr))
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
