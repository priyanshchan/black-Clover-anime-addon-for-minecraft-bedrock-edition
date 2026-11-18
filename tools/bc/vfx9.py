"""v0.9.0 VFX library: high-resolution particle textures and layered particle effects (bc:fx_*).

Every effect reads the same Molang variables the scripts send (core/fx.js `particle()`):
  v.color (rgb), v.scale, v.size, v.radius, v.life, v.dir (vector), v.rot, v.len
so one effect serves every element; the element's character comes from which effects are layered (core/vfx.js).
Projectile trails read v.tr/v.tg/v.tb (the bolt's tint) and v.fk (its element flavour), set by the bolt's animation.
"""
from __future__ import annotations

import math

import numpy as np

from . import tex
from .out import RP, write_json, write_png

TD = 'textures/particle/bc/v9/'

# ======================================================================================
# textures (white or grey: the particles tint them)
# ======================================================================================
def _grid(w, h):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return xx, yy


def _alpha(v, rgb=None):
    h, w = v.shape
    a = tex.new(h, w, tex.rgb('ffffff'))
    if rgb is not None:
        a[..., :3] = rgb
    a[..., 3] = np.clip(v, 0, 1) * 255
    return a


def t_soft(n=64):
    xx, yy = _grid(n, n)
    c = (n - 1) / 2
    d2 = ((xx - c) ** 2 + (yy - c) ** 2) / (n / 2) ** 2
    return _alpha(np.exp(-d2 / 0.16) * 0.75 + np.exp(-d2 / 0.02) * 0.6)


def t_flare(n=128):
    xx, yy = _grid(n, n)
    c = (n - 1) / 2
    dx, dy = (xx - c) / (n / 2), (yy - c) / (n / 2)
    d2 = dx ** 2 + dy ** 2
    core = np.exp(-d2 / 0.006) * 1.2 + np.exp(-d2 / 0.05) * 0.55 + np.exp(-d2 / 0.3) * 0.18
    rays = np.exp(-(dy ** 2) / 0.0006) * np.clip(1 - np.abs(dx), 0, 1) ** 2 + np.exp(-(dx ** 2) / 0.0006) * np.clip(1 - np.abs(dy), 0, 1) ** 2
    u, w = (dx + dy) / 1.414, (dx - dy) / 1.414
    diag = (np.exp(-(w ** 2) / 0.0004) * np.clip(1 - np.abs(u) * 1.6, 0, 1) ** 2 + np.exp(-(u ** 2) / 0.0004) * np.clip(1 - np.abs(w) * 1.6, 0, 1) ** 2) * 0.45
    ring = np.exp(-((np.sqrt(d2) - 0.62) ** 2) / 0.0015) * 0.12
    return _alpha(core + rays * 0.9 + diag + ring)


def t_streak(w=16, h=64):
    xx, yy = _grid(w, h)
    x = (xx - (w - 1) / 2) / (w / 2)
    y = (yy - (h - 1) / 2) / (h / 2)
    taper = np.clip(1 - np.abs(y), 0, 1) ** 0.7 * np.where(y < 0, 1.0, np.clip(1 - y * 0.6, 0, 1))
    return _alpha(np.exp(-(x ** 2) / (0.09 * (0.3 + taper))) * taper * 1.25)


def t_beam(w=32, h=32):
    xx, yy = _grid(w, h)
    x = (xx - (w - 1) / 2) / (w / 2)
    v = np.exp(-(x ** 2) / 0.02) * 1.1 + np.exp(-(x ** 2) / 0.18) * 0.45
    return _alpha(v)


def t_ring(n=128):
    xx, yy = _grid(n, n)
    c = (n - 1) / 2
    d = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / (n / 2)
    v = np.exp(-((d - 0.86) ** 2) / 0.0025) + np.where(d < 0.86, np.exp(-((d - 0.86) ** 2) / 0.03) * 0.4, 0)
    return _alpha(v)


def t_shock(n=128):
    xx, yy = _grid(n, n)
    c = (n - 1) / 2
    d = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / (n / 2)
    ang = np.arctan2(yy - c, xx - c)
    wob = 1 + 0.25 * np.sin(ang * 9) * np.sin(ang * 4 + 1)
    v = np.exp(-((d - 0.9) ** 2) / 0.0012) * 1.1 + np.where(d < 0.9, np.exp(-((d - 0.9) ** 2) / 0.012) * 0.35 * wob, 0)
    return _alpha(v)


def _noise(n, cell, seed, octaves=3):
    """Value noise in 0..1."""
    return np.clip((tex.value_noise(n, n, cell, seed, octaves) + 1) / 2, 0, 1)


def _blob(xx, yy, cx, cy, sx, sy):
    return np.exp(-(((xx - cx) / sx) ** 2 + ((yy - cy) / sy) ** 2))


def t_fire(n=64, frames=8, seed=31):
    """Licking flame tongues that narrow as they rise; later frames die down."""
    a = tex.new(n * frames, n)
    xx, yy = _grid(n, n)
    rng = np.random.default_rng(seed)
    for f in range(frames):
        k = f / (frames - 1)
        v = np.zeros((n, n), np.float32)
        base_y = n * (0.74 - k * 0.1)
        # narrowing upward: squash x more the higher the pixel is
        rise = np.clip((base_y - yy) / n, 0, 1)
        sq = 1 + rise * 3.2
        tongues = [(0.0, 1.0, 0.42)] + [(rng.uniform(-0.18, 0.18), rng.uniform(0.45, 0.75), rng.uniform(0.25, 0.38)) for _ in range(3)]
        for ox, amp, h in tongues:
            cx = n / 2 + ox * n + math.sin(f * 1.3 + ox * 9) * n * 0.03
            g = np.exp(-(((xx - cx) * sq / (n * 0.17)) ** 2) - (((yy - (base_y - n * h * 0.55)) / (n * h)) ** 2))
            v = np.maximum(v, g * amp)
        v += _blob(xx, yy, n / 2, base_y, n * 0.22, n * 0.13) * 0.6
        nz = _noise(n, 4, seed + f * 7, 3)
        v = v * (0.65 + nz * 0.7) * (1.0 - k * 0.55)
        v = np.clip(v * 1.35, 0, 1)
        lum = np.clip(0.35 + v * 0.9, 0, 1)
        layer = tex.new(n, n)
        layer[..., :3] = (lum[..., None] * 255).astype(np.float32)
        layer[..., 3] = (v ** 1.1) * 255
        a[f * n:(f + 1) * n] = layer
    return a


def _puff(n, rng, count, spread, size, grow):
    xx, yy = _grid(n, n)
    v = np.zeros((n, n), np.float32)
    for _ in range(count):
        ang = rng.uniform(0, math.tau)
        r = rng.uniform(0, spread) * n * grow
        cx, cy = n / 2 + math.cos(ang) * r, n / 2 + math.sin(ang) * r
        sz = rng.uniform(*size) * n * (0.8 + grow * 0.25)
        v += _blob(xx, yy, cx, cy, sz, sz) * rng.uniform(0.6, 1.0)
    return v


def t_smoke(n=64, frames=8, seed=53):
    """A billowing puff that spreads and thins out."""
    a = tex.new(n * frames, n)
    for f in range(frames):
        k = f / (frames - 1)
        rng = np.random.default_rng(seed)
        v = _puff(n, rng, 9, 0.24, (0.11, 0.2), 1.0 + k * 0.6)
        nz = _noise(n, 6, seed + f * 3, 3)
        v = np.clip(v * (0.7 + nz * 0.5), 0, 1.4)
        v = (np.clip(v / 1.7, 0, 1) ** 1.25) * (1 - k * 0.5)
        lum = 0.6 + 0.4 * _noise(n, 5, seed + 200, 2)
        layer = tex.new(n, n)
        layer[..., :3] = (np.clip(lum, 0, 1)[..., None] * 255).astype(np.float32)
        layer[..., 3] = np.clip(v, 0, 1) * 255
        a[f * n:(f + 1) * n] = layer
    return a


def t_dust(n=64, seed=71):
    rng = np.random.default_rng(seed)
    v = _puff(n, rng, 8, 0.22, (0.1, 0.19), 1.0)
    nz = _noise(n, 5, seed, 3)
    return _alpha(np.clip(v * (0.6 + nz * 0.6) / 1.8, 0, 1) ** 1.3)


def t_sigil(n=256):
    def fn(d, s):
        c = n * s / 2
        W = (255, 255, 255, 255)

        def circ(r, w):
            d.ellipse([c - r, c - r, c + r, c + r], outline=W, width=max(1, int(w)))
        R = c * 0.96
        circ(R, 2.4 * s)
        circ(R * 0.9, 1.2 * s)
        circ(R * 0.66, 1.8 * s)
        circ(R * 0.6, 0.9 * s)
        circ(R * 0.24, 1.6 * s)
        # rune band between the outer rings
        for k in range(28):
            a = k / 28 * math.tau
            r0, r1 = R * 0.915, R * 0.69
            x0, y0 = c + math.cos(a) * r0, c + math.sin(a) * r0
            mid = (r0 + r1) / 2
            gx, gy = c + math.cos(a) * mid, c + math.sin(a) * mid
            ta = a + math.pi / 2
            seg = R * 0.07
            kind = k % 4
            if kind == 0:
                d.line([(gx - math.cos(ta) * seg, gy - math.sin(ta) * seg), (gx + math.cos(ta) * seg, gy + math.sin(ta) * seg)], fill=W, width=int(1.4 * s))
                d.line([(gx, gy), (c + math.cos(a) * (mid + seg), c + math.sin(a) * (mid + seg))], fill=W, width=int(1.4 * s))
            elif kind == 1:
                d.ellipse([gx - seg * 0.55, gy - seg * 0.55, gx + seg * 0.55, gy + seg * 0.55], outline=W, width=int(1.3 * s))
            elif kind == 2:
                pts = [(c + math.cos(a + o) * (mid + rr), c + math.sin(a + o) * (mid + rr)) for o, rr in ((-0.05, -seg), (0, seg), (0.05, -seg))]
                d.line(pts, fill=W, width=int(1.3 * s))
            else:
                d.line([(c + math.cos(a - 0.04) * (mid - seg), c + math.sin(a - 0.04) * (mid - seg)),
                        (c + math.cos(a + 0.04) * (mid + seg), c + math.sin(a + 0.04) * (mid + seg))], fill=W, width=int(1.3 * s))
            _ = (x0, y0)
        # hexagram
        for off in (0, math.pi / 3):
            pts = [(c + math.cos(off + i * math.tau / 3 - math.pi / 2) * R * 0.6, c + math.sin(off + i * math.tau / 3 - math.pi / 2) * R * 0.6) for i in range(3)]
            d.polygon(pts, outline=W, width=int(1.6 * s))
        # dots at the star points
        for i in range(6):
            a = i * math.tau / 6 - math.pi / 2
            px, py = c + math.cos(a) * R * 0.6, c + math.sin(a) * R * 0.6
            d.ellipse([px - 3 * s, py - 3 * s, px + 3 * s, py + 3 * s], fill=W)
        tex.clover_shape(d, c, c, R * 0.2, 4, W, stem=False)
    a = tex.draw_layer(n, n, fn, 2)
    return tex.glow(a, 2.5, 0.55)


def t_crack(n=128, seed=5):
    rng = np.random.default_rng(seed)

    def fn(d, s):
        c = n * s / 2
        for k in range(9):
            a = k / 9 * math.tau + rng.uniform(-0.25, 0.25)
            x, y = c, c
            w = 3.2
            for step in range(9):
                a += rng.uniform(-0.45, 0.45)
                L = n * s * rng.uniform(0.04, 0.07)
                nx, ny = x + math.cos(a) * L, y + math.sin(a) * L
                d.line([(x, y), (nx, ny)], fill=(255, 255, 255, 255), width=max(1, int(w * s)))
                if rng.random() < 0.3 and step > 1:
                    b = a + rng.choice([-1, 1]) * rng.uniform(0.5, 1.0)
                    d.line([(nx, ny), (nx + math.cos(b) * L * 0.8, ny + math.sin(b) * L * 0.8)], fill=(255, 255, 255, 220), width=max(1, int(w * 0.6 * s)))
                x, y = nx, ny
                w = max(0.8, w * 0.8)
        d.ellipse([c - 7 * s, c - 7 * s, c + 7 * s, c + 7 * s], fill=(255, 255, 255, 255))
    a = tex.draw_layer(n, n, fn, 4)
    xx, yy = _grid(n, n)
    fade = np.clip(1.15 - np.sqrt((xx - n / 2) ** 2 + (yy - n / 2) ** 2) / (n / 2), 0, 1)
    a[..., 3] = a[..., 3] * fade
    return a


def t_bolt(w=64, h=256, frames=4, seed=11):
    out = tex.new(h, w * frames)
    for f in range(frames):
        rng = np.random.default_rng(seed + f * 13)

        def fn(d, s, rng=rng):
            x = w * s / 2
            pts = [(x, 0)]
            for i in range(1, 18):
                x = w * s / 2 + rng.uniform(-w * s * 0.28, w * s * 0.28)
                pts.append((x, h * s * i / 17))
            d.line(pts, fill=(255, 255, 255, 255), width=int(3.0 * s), joint='curve')
            for _ in range(4):
                i = int(rng.integers(2, 14))
                bx, by = pts[i]
                tx = bx + rng.uniform(-w * s * 0.42, w * s * 0.42)
                ty = by + h * s * rng.uniform(0.06, 0.16)
                d.line([(bx, by), ((bx + tx) / 2 + rng.uniform(-6, 6) * s, (by + ty) / 2), (tx, ty)], fill=(255, 255, 255, 230), width=int(1.6 * s))
        layer = tex.draw_layer(h, w, fn, 3)
        out[:, f * w:(f + 1) * w] = tex.glow(layer, 3.0, 0.9)
    return out


def t_slash(w=128, h=64):
    def fn(d, s):
        for wid, alpha in ((14, 70), (9, 140), (5, 210), (2.2, 255)):
            d.arc([w * s * 0.04, h * s * 0.06, w * s * 0.96, h * s * 1.94], 192, 348, fill=(255, 255, 255, alpha), width=int(wid * s))
    a = tex.draw_layer(h, w, fn, 4)
    xx, _ = _grid(w, h)
    taper = np.clip(np.sin(np.clip((xx / (w - 1)), 0, 1) * math.pi) * 1.4, 0, 1)
    a[..., 3] = a[..., 3] * taper
    return a


def _sprite(n, fn, ss=4):
    return tex.draw_layer(n, n, fn, ss)


def t_shard(n=32):
    def fn(d, s):
        c = n * s / 2
        d.polygon([(c, 1 * s), (c + 6 * s, c - 2 * s), (c + 2 * s, n * s - 2 * s), (c - 5 * s, c + 2 * s)], fill=(255, 255, 255, 255))
        d.polygon([(c, 1 * s), (c + 6 * s, c - 2 * s), (c + 1 * s, c)], fill=(200, 200, 200, 255))
    return _sprite(n, fn)


def t_leaf(n=32):
    def fn(d, s):
        d.ellipse([7 * s, 3 * s, 25 * s, 29 * s], fill=(255, 255, 255, 255))
        d.line([(16 * s, 4 * s), (16 * s, 29 * s)], fill=(170, 170, 170, 255), width=int(1.4 * s))
        for y in (10, 15, 20):
            d.line([(16 * s, y * s), (10 * s, (y - 4) * s)], fill=(190, 190, 190, 255), width=int(1 * s))
            d.line([(16 * s, y * s), (22 * s, (y - 4) * s)], fill=(190, 190, 190, 255), width=int(1 * s))
    return _sprite(n, fn)


def t_drop(n=32):
    def fn(d, s):
        d.ellipse([9 * s, 12 * s, 23 * s, 27 * s], fill=(255, 255, 255, 230))
        d.polygon([(16 * s, 3 * s), (22.5 * s, 17 * s), (9.5 * s, 17 * s)], fill=(255, 255, 255, 230))
        d.ellipse([12 * s, 15 * s, 15.5 * s, 19 * s], fill=(255, 255, 255, 255))
    return _sprite(n, fn)


def t_flake(n=32):
    def fn(d, s):
        c = n * s / 2
        for k in range(6):
            a = k * math.pi / 3
            ex, ey = c + math.cos(a) * 13 * s, c + math.sin(a) * 13 * s
            d.line([(c, c), (ex, ey)], fill=(255, 255, 255, 255), width=int(1.8 * s))
            for t in (0.5, 0.75):
                bx, by = c + math.cos(a) * 13 * s * t, c + math.sin(a) * 13 * s * t
                for side in (-1, 1):
                    b = a + side * 0.7
                    d.line([(bx, by), (bx + math.cos(b) * 4 * s, by + math.sin(b) * 4 * s)], fill=(255, 255, 255, 255), width=int(1.3 * s))
    return tex.glow(_sprite(n, fn), 1.2, 0.5)


def t_bubble(n=32):
    def fn(d, s):
        d.ellipse([3 * s, 3 * s, 29 * s, 29 * s], outline=(255, 255, 255, 255), width=int(2 * s))
        d.ellipse([3 * s, 3 * s, 29 * s, 29 * s], fill=(255, 255, 255, 40))
        d.ellipse([9 * s, 8 * s, 14 * s, 13 * s], fill=(255, 255, 255, 255))
    return _sprite(n, fn)


def t_star(n=32):
    xx, yy = _grid(n, n)
    c = (n - 1) / 2
    dx, dy = np.abs(xx - c) / (n / 2), np.abs(yy - c) / (n / 2)
    v = np.clip(1 - dx * 7 - dy, 0, 1) + np.clip(1 - dy * 7 - dx, 0, 1) + np.exp(-(dx ** 2 + dy ** 2) / 0.02) * 0.9
    return _alpha(v)


def t_note(n=32):
    def fn(d, s):
        d.ellipse([5 * s, 19 * s, 15 * s, 28 * s], fill=(255, 255, 255, 255))
        d.rectangle([12.5 * s, 4 * s, 15 * s, 24 * s], fill=(255, 255, 255, 255))
        d.polygon([(15 * s, 4 * s), (26 * s, 9 * s), (26 * s, 14 * s), (15 * s, 9 * s)], fill=(255, 255, 255, 255))
    return tex.glow(_sprite(n, fn), 1.2, 0.5)


def t_wisp(n=64):
    def fn(d, s):
        for k, (wid, al) in enumerate(((10, 60), (6, 140), (3, 255))):
            d.arc([8 * s, 8 * s, 56 * s, 56 * s], 200, 330, fill=(255, 255, 255, al), width=int(wid * s))
    a = _sprite(n, fn)
    return tex.glow(a, 2.0, 0.6)


def t_debris(n=32, seed=3):
    out = tex.new(n * 2, n * 2)
    rng = np.random.default_rng(seed)
    for i in range(4):
        ox, oy = (i % 2) * n, (i // 2) * n

        def fn(d, s):
            c = n * s / 2
            pts = []
            k = int(rng.integers(5, 8))
            for j in range(k):
                a = j / k * math.tau + rng.uniform(-0.3, 0.3)
                r = n * s * rng.uniform(0.28, 0.44)
                pts.append((c + math.cos(a) * r, c + math.sin(a) * r))
            d.polygon(pts, fill=(255, 255, 255, 255))
            d.polygon(pts[:3] + [(c, c)], fill=(205, 205, 205, 255))
        layer = _sprite(n, fn)
        tex.outline(layer, (60, 60, 60, 255))
        out[oy:oy + n, ox:ox + n] = layer
    return out


GLYPH_STROKES = [
    [((8, 8), (24, 8)), ((16, 8), (16, 26)), ((10, 20), (22, 20))],
    [((8, 26), (16, 6), (24, 26)), ((11, 18), (21, 18))],
    [((10, 6), (10, 26)), ((10, 6), (22, 12), (10, 18)), ((10, 18), (22, 26))],
    [((16, 5), (16, 27)), ((8, 12), (24, 20)), ((24, 12), (8, 20))],
    [((8, 8), (24, 24)), ((24, 8), (8, 24)), ((16, 4), (16, 10))],
    [((8, 16), (16, 6), (24, 16), (16, 26), (8, 16))],
    [((9, 7), (23, 7), (9, 25), (23, 25))],
    [((16, 6), (16, 26)), ((16, 10), (24, 6)), ((16, 16), (8, 12)), ((16, 22), (24, 18))],
]


def t_glyphs(n=32):
    out = tex.new(n * len(GLYPH_STROKES), n)
    for i, strokes in enumerate(GLYPH_STROKES):
        def fn(d, s, strokes=strokes):
            for line in strokes:
                d.line([(x * s, y * s) for x, y in line], fill=(255, 255, 255, 255), width=int(2.2 * s), joint='curve')
        out[i * n:(i + 1) * n] = tex.glow(_sprite(n, fn), 1.5, 0.6)
    return out


TEXTURES = {
    'soft': (t_soft, (64, 64)), 'flare': (t_flare, (128, 128)), 'streak': (t_streak, (16, 64)), 'beam': (t_beam, (32, 32)),
    'ring': (t_ring, (128, 128)), 'shock': (t_shock, (128, 128)), 'fire': (t_fire, (64, 512)), 'smoke': (t_smoke, (64, 512)),
    'dust': (t_dust, (64, 64)), 'sigil': (t_sigil, (256, 256)), 'crack': (t_crack, (128, 128)), 'bolt': (t_bolt, (256, 256)),
    'slash': (t_slash, (128, 64)), 'shard': (t_shard, (32, 32)), 'leaf': (t_leaf, (32, 32)), 'drop': (t_drop, (32, 32)),
    'flake': (t_flake, (32, 32)), 'bubble': (t_bubble, (32, 32)), 'star': (t_star, (32, 32)), 'note': (t_note, (32, 32)),
    'wisp': (t_wisp, (64, 64)), 'debris': (t_debris, (64, 64)), 'glyph': (t_glyphs, (32, 256)),
}


def gen_textures():
    for name, (fn, _) in TEXTURES.items():
        write_png(RP, f'{TD}{name}.png', fn())


# ======================================================================================
# particle effects
# ======================================================================================
T_ = 'v.particle_age / v.particle_lifetime'
R1, R2, R3, R4 = 'v.particle_random_1', 'v.particle_random_2', 'v.particle_random_3', 'v.particle_random_4'
SC = 'v.sc'
INIT = {'minecraft:emitter_initialization': {'creation_expression': 'v.sc = v.scale ?? 1.0; v.sz = v.size ?? 1.0;'}}


def P(ident, texture, material, comps):
    return ident, {'format_version': '1.10.0', 'particle_effect': {
        'description': {'identifier': ident, 'basic_render_parameters': {'material': material, 'texture': TD + texture}},
        'components': comps}}


def uvs(name, frames=None, fps=None, pick=None):
    w, h = TEXTURES[name][1]
    if frames:
        fh = h // frames
        return {'texture_width': w, 'texture_height': h, 'flipbook': {
            'base_UV': [0, 0], 'size_UV': [w, fh], 'step_UV': [0, fh], 'frames_per_second': fps or 8, 'max_frame': frames,
            'stretch_to_lifetime': fps is None, 'loop': False}}
    if pick:
        cols, rows, cw, ch = pick
        return {'texture_width': w, 'texture_height': h,
                'uv': [f'math.floor({R3} * {cols - 0.01}) * {cw}' if cols > 1 else 0, f'math.floor({R4} * {rows - 0.01}) * {ch}' if rows > 1 else 0],
                'uv_size': [cw, ch]}
    return {'texture_width': w, 'texture_height': h, 'uv': [0, 0], 'uv_size': [w, h]}


def bb(name, size, mode='lookat_xyz', direction=None, **kw):
    b = {'size': size, 'facing_camera_mode': mode, 'uv': uvs(name, **kw)}
    if direction == 'velocity':
        b['direction'] = {'mode': 'derive_from_velocity', 'min_speed_threshold': 0.01}
    elif direction:
        b['direction'] = {'mode': 'custom', 'custom_direction': direction}
    return b


def col(default='1.0, 1.0, 1.0', alpha='1.0', white=None, mul='1.0'):
    """Tint from v.color (with a default); `white` is a 0..1 expression mixing toward white."""
    d = [x.strip() for x in default.split(',')]
    ch = []
    for i, c in enumerate('rgb'):
        base = f'(v.color.{c} ?? {d[i]})'
        ch.append(f'math.lerp(1.0, {base}, {white}) * {mul}' if white else f'{base} * {mul}')
    return {'color': ch + [alpha]}


FADE = f'(1.0 - {T_})'
POP = f'math.clamp(v.particle_age * 14.0, 0.0, 1.0)'
INOUT = f'math.clamp(v.particle_age * 6.0, 0.0, 1.0) * math.clamp((v.particle_lifetime - v.particle_age) * 3.0, 0.0, 1.0)'
DIR = ['v.dir.x ?? 0', 'v.dir.y ?? 0', 'v.dir.z ?? 1']


def once(n):
    return {'minecraft:emitter_rate_instant': {'num_particles': n}, 'minecraft:emitter_lifetime_once': {'active_time': 0.05}}


def steady(rate, mx, active):
    return {'minecraft:emitter_rate_steady': {'spawn_rate': rate, 'max_particles': mx}, 'minecraft:emitter_lifetime_once': {'active_time': active}}


def life(expr):
    return {'minecraft:particle_lifetime_expression': {'max_lifetime': expr}}


def dyn(acc=(0, 0, 0), drag=0.0, spin_drag=None):
    d = {'linear_acceleration': list(acc), 'linear_drag_coefficient': drag}
    if spin_drag is not None:
        d['rotation_drag_coefficient'] = spin_drag
    return {'minecraft:particle_motion_dynamic': d}


def collide(rest=0.3, drag=2.0, radius=0.05):
    return {'minecraft:particle_motion_collision': {'enabled': True, 'collision_drag': drag, 'coefficient_of_restitution': rest, 'collision_radius': radius}}


def spin(rate, start='math.random(0, 360)'):
    return {'minecraft:particle_initial_spin': {'rotation': start, 'rotation_rate': rate}}


def sphere(radius, direction='outwards', surface=False, offset=None):
    d = {'radius': radius, 'direction': direction, 'surface_only': surface}
    if offset:
        d['offset'] = offset
    return {'minecraft:emitter_shape_sphere': d}


def disc(radius, direction='outwards', surface=False):
    return {'minecraft:emitter_shape_disc': {'radius': radius, 'plane_normal': [0, 1, 0], 'direction': direction, 'surface_only': surface}}


def point(direction=None):
    d = {}
    if direction:
        d['direction'] = direction
    return {'minecraft:emitter_shape_point': d}


def grad3(c0, c2, alpha, split=0.3):
    """White-hot -> v.color -> c2 over the particle's life."""
    out = []
    for i, ch in enumerate('rgb'):
        mid = f'(v.color.{ch} ?? {[1.0, 0.55, 0.15][i]})'
        out.append(f'({T_} < {split} ? math.lerp({c0[i]}, {mid}, {T_} / {split}) : math.lerp({mid}, {c2[i]}, ({T_} - {split}) / {1 - split}))')
    return {'color': out + [alpha]}


def effects():
    out = []
    add = 'particles_add'
    blend = 'particles_blend'
    alpha = 'particles_alpha'
    # ---------------------------------------------------------------- flashes and glows
    out.append(P('bc:fx_flash', 'flare', add, {**INIT, **once(1), **point(), **life('v.life ?? 0.3'), **spin(0),
        'minecraft:particle_appearance_billboard': bb('flare', [f'v.sz * 2.4 * (0.35 + 0.9 * {POP}) * (1.0 - {T_} * 0.45)'] * 2),
        'minecraft:particle_appearance_tinting': col(alpha=f'math.pow({FADE}, 1.6)', white=f'math.min({T_} * 2.2, 1.0)')}))
    out.append(P('bc:fx_core', 'soft', add, {**INIT, **once(2), **point(), **life('0.16'),
        'minecraft:particle_appearance_billboard': bb('soft', [f'v.sz * 1.1 * (0.5 + {POP} * 0.5)'] * 2),
        'minecraft:particle_appearance_tinting': col(alpha=FADE, white='0.25')}))
    out.append(P('bc:fx_glow', 'soft', add, {**INIT, **once(1), **point(), **life('v.life ?? 0.6'),
        'minecraft:particle_appearance_billboard': bb('soft', [f'v.sz * 1.4 * (1.0 + math.sin(v.particle_age * 900.0) * 0.08)'] * 2),
        'minecraft:particle_appearance_tinting': col(alpha=f'0.85 * {INOUT}', white='0.75')}))
    out.append(P('bc:fx_charge', 'soft', add, {**INIT, **once(2), **point(), **life('v.life ?? 0.5'),
        'minecraft:particle_appearance_billboard': bb('soft', [f'v.sz * (0.15 + {T_} * 1.05) * (1.0 + math.sin(v.particle_age * 2200.0) * 0.12)'] * 2),
        'minecraft:particle_appearance_tinting': col(alpha=f'math.min(v.particle_age * 8.0, 1.0)', white=f'math.min({T_} * 1.5, 1.0)')}))
    # ---------------------------------------------------------------- sparks, sprays, embers
    out.append(P('bc:fx_sparks', 'streak', add, {**INIT, **once(f'math.round(18 * {SC})'), **sphere(f'0.2 * {SC}'),
        **life('0.35 + v.particle_random_1 * 0.4'), 'minecraft:particle_initial_speed': f'(5.0 + {R2} * 9.0) * math.sqrt({SC})',
        **dyn((0, -11, 0), 1.3), **collide(0.35, 2.0),
        'minecraft:particle_appearance_billboard': bb('streak', ['0.045 * math.sqrt(v.sc)', f'0.26 * math.sqrt(v.sc) * {FADE}'], 'lookat_direction', 'velocity'),
        'minecraft:particle_appearance_tinting': col(alpha=FADE, white=f'math.min({T_} * 2.5, 1.0)')}))
    out.append(P('bc:fx_spray', 'streak', add, {**INIT, **once(f'math.round(16 * {SC})'),
        **point([f'(v.dir.x ?? 0) + math.random(-0.38, 0.38)', f'(v.dir.y ?? 0) + math.random(-0.3, 0.38)', f'(v.dir.z ?? 1) + math.random(-0.38, 0.38)']),
        **life('0.25 + v.particle_random_1 * 0.3'), 'minecraft:particle_initial_speed': f'(9.0 + {R2} * 10.0) * math.sqrt({SC})',
        **dyn((0, -5, 0), 2.6),
        'minecraft:particle_appearance_billboard': bb('streak', ['0.06 * math.sqrt(v.sc)', f'0.42 * math.sqrt(v.sc) * {FADE}'], 'lookat_direction', 'velocity'),
        'minecraft:particle_appearance_tinting': col(alpha=FADE, white=f'math.min({T_} * 2.0, 1.0)')}))
    out.append(P('bc:fx_embers', 'soft', add, {**INIT, **once(f'math.round(14 * {SC})'), **sphere(f'0.6 * {SC}'),
        **life('1.0 + v.particle_random_1 * 1.3'), 'minecraft:particle_initial_speed': f'0.6 + {R2} * 1.6',
        **dyn((0, 1.1, 0), 1.2),
        'minecraft:particle_appearance_billboard': bb('soft', ['0.07 + v.particle_random_3 * 0.05'] * 2),
        'minecraft:particle_appearance_tinting': col('1.0, 0.55, 0.15', alpha=f'{FADE} * (0.55 + math.sin(v.particle_age * 1100.0 + {R4} * 360.0) * 0.45)',
                                                     white=f'0.4 + {T_} * 0.6')}))
    # ---------------------------------------------------------------- smoke, dust, mist
    out.append(P('bc:fx_smoke', 'smoke', blend, {**INIT, **once(f'math.round(9 * {SC})'), **sphere(f'0.5 * {SC}'),
        **life('1.1 + v.particle_random_1 * 1.0'), 'minecraft:particle_initial_speed': f'(0.6 + {R2} * 1.4) * {SC}',
        **dyn((0, 0.7, 0), 1.6), **spin(f'math.random(-40, 40)'),
        'minecraft:particle_appearance_billboard': bb('smoke', [f'(0.45 + {T_} * 1.1) * {SC}'] * 2, frames=8),
        'minecraft:particle_appearance_tinting': col('0.22, 0.21, 0.23', alpha=f'0.6 * {INOUT}')}))
    out.append(P('bc:fx_dust', 'dust', blend, {**INIT, **once(f'math.round(22 * {SC})'), **disc(f'0.35 * {SC}'),
        **life('0.8 + v.particle_random_1 * 0.6'), 'minecraft:particle_initial_speed': f'(4.0 + {R2} * 5.0) * math.sqrt({SC})',
        **dyn((0, 0.35, 0), 3.2), **spin('math.random(-60, 60)'),
        'minecraft:particle_appearance_billboard': bb('dust', [f'(0.35 + {T_} * 0.9) * math.sqrt({SC})'] * 2),
        'minecraft:particle_appearance_tinting': col('0.55, 0.5, 0.44', alpha=f'0.65 * {FADE}')}))
    out.append(P('bc:fx_mist', 'dust', add, {**INIT, **once(f'math.round(10 * {SC})'), **sphere(f'0.7 * {SC}'),
        **life('1.2 + v.particle_random_1 * 0.9'), 'minecraft:particle_initial_speed': '0.5 + v.particle_random_2 * 0.6',
        **dyn((0, 0.15, 0), 1.0), **spin('math.random(-30, 30)'),
        'minecraft:particle_appearance_billboard': bb('dust', [f'(0.6 + {T_} * 0.9) * {SC}'] * 2),
        'minecraft:particle_appearance_tinting': col(alpha=f'0.28 * {INOUT}', white='0.85')}))
    out.append(P('bc:fx_void', 'smoke', blend, {**INIT, **once(f'math.round(12 * {SC})'), **sphere(f'0.45 * {SC}'),
        **life('0.6 + v.particle_random_1 * 0.5'), 'minecraft:particle_initial_speed': f'(2.0 + {R2} * 2.5) * {SC}',
        **dyn((0, 0.2, 0), 3.0), **spin('math.random(-90, 90)'),
        'minecraft:particle_appearance_billboard': bb('smoke', [f'(0.4 + {T_} * 0.6) * {SC}'] * 2, frames=8),
        'minecraft:particle_appearance_tinting': col('0.25, 0.08, 0.35', alpha=f'0.85 * {INOUT}', mul='0.22')}))
    # ---------------------------------------------------------------- rings, shocks, ground
    out.append(P('bc:fx_ring', 'ring', add, {**INIT, **once(1), **point(), **life('v.life ?? 0.42'),
        'minecraft:particle_appearance_billboard': bb('ring', [f'(v.radius ?? 3.0) * (1.0 - math.pow(1.0 - {T_}, 3.0))'] * 2, 'emitter_transform_xz'),
        'minecraft:particle_appearance_tinting': col(alpha=f'math.pow({FADE}, 1.4)', white=f'math.min({T_} * 3.0, 1.0)')}))
    out.append(P('bc:fx_shock', 'shock', add, {**INIT, **once(1), **point(), **life('v.life ?? 0.3'),
        'minecraft:particle_appearance_billboard': bb('shock', [f'(v.radius ?? 1.6) * (0.2 + 0.8 * (1.0 - math.pow(1.0 - {T_}, 2.5)))'] * 2, 'direction_z', DIR),
        'minecraft:particle_appearance_tinting': col(alpha=FADE, white=f'math.min({T_} * 3.0, 1.0)')}))
    out.append(P('bc:fx_crack', 'crack', blend, {**INIT, **once(1), **point(), **life('v.life ?? 2.6'), **spin(0),
        'minecraft:particle_appearance_billboard': bb('crack', [f'v.sz * (0.55 + 0.45 * math.min(v.particle_age * 10.0, 1.0))'] * 2, 'emitter_transform_xz'),
        'minecraft:particle_appearance_tinting': {'color': ['0.06', '0.05', '0.05', f'0.85 * math.clamp(({FADE}) * 2.5, 0.0, 1.0)']}}))
    out.append(P('bc:fx_crack_glow', 'crack', add, {**INIT, **once(1), **point(), **life('v.life ?? 1.4'), **spin(0),
        'minecraft:particle_appearance_billboard': bb('crack', [f'v.sz * (0.55 + 0.45 * math.min(v.particle_age * 10.0, 1.0))'] * 2, 'emitter_transform_xz'),
        'minecraft:particle_appearance_tinting': col('1.0, 0.5, 0.1', alpha=f'math.pow({FADE}, 1.5)', white='1.0')}))
    out.append(P('bc:fx_debris', 'debris', alpha, {**INIT, **once(f'math.round(10 * {SC})'),
        **sphere(f'0.35 * {SC}', ['math.random(-1, 1)', 'math.random(0.7, 1.6)', 'math.random(-1, 1)']),
        **life('1.3 + v.particle_random_1 * 0.8'), 'minecraft:particle_initial_speed': f'(4.0 + {R2} * 6.0) * math.sqrt({SC})',
        **dyn((0, -22, 0), 0.4), **collide(0.25, 5.0, 0.08), **spin('math.random(-720, 720)'),
        'minecraft:particle_appearance_billboard': bb('debris', [f'(0.07 + {R4} * 0.12) * math.sqrt({SC})'] * 2, pick=(2, 2, 32, 32)),
        'minecraft:particle_appearance_tinting': col('0.55, 0.52, 0.5', mul=f'(0.65 + {R1} * 0.35)'),
        'minecraft:particle_appearance_lighting': {}}))
    # ---------------------------------------------------------------- charge-up, sigils
    out.append(P('bc:fx_converge', 'streak', add, {**INIT, **steady(70, 60, 'v.life ?? 0.5'),
        **sphere('v.radius ?? 2.0', 'inwards', True), **life('0.4'), 'minecraft:particle_initial_speed': '(v.radius ?? 2.0) / 0.42',
        'minecraft:particle_appearance_billboard': bb('streak', ['0.05', f'0.3 * (0.4 + {T_})'], 'lookat_direction', 'velocity'),
        'minecraft:particle_appearance_tinting': col(alpha=f'math.min(v.particle_age * 10.0, 1.0)', white=f'{T_}')}))
    for ident, mode, direction in (('bc:fx_sigil', 'direction_z', DIR), ('bc:fx_sigil_ground', 'emitter_transform_xz', None)):
        b = bb('sigil', [f'v.sz * ({T_} < 0.12 ? ({T_} / 0.12) * 1.12 : 1.12 - math.min(({T_} - 0.12) * 1.5, 0.12))'] * 2, mode, direction)
        out.append(P(ident, 'sigil', add, {**INIT, **once(1), **point(), **life('v.life ?? 0.9'), **spin(90 if 'ground' not in ident else 45, 0),
            'minecraft:particle_appearance_billboard': b,
            'minecraft:particle_appearance_tinting': col(alpha=f'{INOUT} * (0.85 + math.sin(v.particle_age * 1500.0) * 0.15)', white='0.85')}))
    # ---------------------------------------------------------------- beams, lightning, slashes, pillars
    along = [f'(v.dir.x ?? 0) * (v.len ?? 4.0) * {R1}', f'(v.dir.y ?? 0) * (v.len ?? 4.0) * {R1}', f'(v.dir.z ?? 1) * (v.len ?? 4.0) * {R1}']
    for ident, width, white, lf in (('bc:fx_beam', '1.0', '0.6', 'v.life ?? 0.32'), ('bc:fx_beam_core', '0.32', '0.0', '(v.life ?? 0.32) * 0.8')):
        out.append(P(ident, 'beam', add, {**INIT, **once('math.max(4, (v.len ?? 4.0) * 5.0)'), **point(), **life(lf),
            'minecraft:particle_motion_parametric': {'relative_position': along},
            'minecraft:particle_appearance_billboard': bb('beam', [f'v.sz * {width} * (1.0 - {T_} * 0.6) * (0.85 + math.sin(v.particle_age * 3000.0 + {R2} * 360.0) * 0.15)', '0.45'],
                                                          'lookat_direction', DIR),
            'minecraft:particle_appearance_tinting': col(alpha=f'math.pow({FADE}, 1.2)', white=white if white != '0.0' else '0.0')}))
    out.append(P('bc:fx_bolt', 'bolt', add, {**INIT, **once(1), **point(), **life('v.life ?? 0.24'),
        'minecraft:particle_appearance_billboard': bb('bolt', ['v.sz * 0.6', '(v.len ?? 6.0) * 0.5'], 'lookat_direction', DIR, pick=(4, 1, 64, 256)),
        'minecraft:particle_appearance_tinting': col('1.0, 0.95, 0.5', alpha=f'{FADE} * (math.mod(math.floor(v.particle_age * 40.0), 2) == 0 ? 1.0 : 0.45)',
                                                     white='0.45')}))
    out.append(P('bc:fx_slash', 'slash', add, {**INIT, **once(1), **point(), **life('v.life ?? 0.26'),
        'minecraft:particle_initial_spin': {'rotation': 'v.rot ?? math.random(-40, 40)', 'rotation_rate': 0},
        'minecraft:particle_appearance_billboard': bb('slash', [f'v.sz * (0.7 + 0.3 * math.min(v.particle_age * 12.0, 1.0))', f'v.sz * 0.5 * (0.7 + 0.3 * math.min(v.particle_age * 12.0, 1.0))']),
        'minecraft:particle_appearance_tinting': col(alpha=f'math.pow({FADE}, 1.3)', white=f'math.min({T_} * 2.0, 1.0)')}))
    out.append(P('bc:fx_pillar', 'streak', add, {**INIT, **steady(90, 60, '0.25'), **disc('(v.radius ?? 0.6) * 0.6', [0, 1, 0]),
        **life('0.35 + v.particle_random_1 * 0.3'), 'minecraft:particle_initial_speed': '12.0 + v.particle_random_2 * 8.0', **dyn((0, 0, 0), 0.6),
        'minecraft:particle_appearance_billboard': bb('streak', ['0.07 * v.sz', f'0.8 * v.sz * {FADE}'], 'lookat_direction', 'velocity'),
        'minecraft:particle_appearance_tinting': col(alpha=FADE, white=f'math.min({T_} * 2.0, 1.0)')}))
    out.append(P('bc:fx_swirl', 'wisp', add, {**INIT, **steady(34, 60, 'v.life ?? 0.9'), **point(), **life('0.8 + v.particle_random_1 * 0.3'),
        'minecraft:particle_motion_parametric': {'relative_position': [
            f'math.cos(v.particle_age * 420.0 + {R1} * 360.0) * (v.radius ?? 1.2) * (0.55 + {R2} * 0.45)',
            f'v.particle_age * (2.2 + {R3})',
            f'math.sin(v.particle_age * 420.0 + {R1} * 360.0) * (v.radius ?? 1.2) * (0.55 + {R2} * 0.45)'],
            'rotation': f'v.particle_age * 420.0 + {R1} * 360.0'},
        'minecraft:particle_appearance_billboard': bb('wisp', ['0.35 * v.sz'] * 2),
        'minecraft:particle_appearance_tinting': col(alpha=INOUT, white='0.8')}))
    out.append(P('bc:fx_aura', 'soft', add, {**INIT, **steady(30, 50, 'v.life ?? 1.0'), **disc('0.55', [0, 1, 0]),
        **life('0.6 + v.particle_random_1 * 0.5'), 'minecraft:particle_initial_speed': '0.9 + v.particle_random_2 * 1.2', **dyn((0, 0.6, 0), 0.6),
        'minecraft:particle_appearance_billboard': bb('soft', ['0.09 + v.particle_random_3 * 0.07'] * 2),
        'minecraft:particle_appearance_tinting': col(alpha=f'{INOUT} * (0.6 + math.sin(v.particle_age * 1400.0 + {R4} * 360.0) * 0.4)', white='0.5')}))
    # ---------------------------------------------------------------- element particles
    out.append(P('bc:fx_fire', 'fire', add, {**INIT, **once(f'math.round(16 * {SC})'), **sphere(f'0.35 * {SC}'),
        **life('0.5 + v.particle_random_1 * 0.45'), 'minecraft:particle_initial_speed': f'(2.0 + {R2} * 4.0) * math.sqrt({SC})',
        **dyn((0, 2.8, 0), 2.6), **spin('math.random(-60, 60)'),
        'minecraft:particle_appearance_billboard': bb('fire', [f'(0.35 + {R3} * 0.3) * {SC} * (0.7 + {T_} * 0.6)'] * 2, frames=8),
        'minecraft:particle_appearance_tinting': grad3(('1.0', '0.95', '0.75'), ('0.35', '0.04', '0.0'), FADE)}))
    out.append(P('bc:fx_water', 'drop', add, {**INIT, **once(f'math.round(24 * {SC})'),
        **sphere(f'0.3 * {SC}', ['math.random(-1, 1)', 'math.random(0.2, 1.4)', 'math.random(-1, 1)']),
        **life('0.6 + v.particle_random_1 * 0.5'), 'minecraft:particle_initial_speed': f'(3.5 + {R2} * 5.0) * math.sqrt({SC})',
        **dyn((0, -16, 0), 0.6), **collide(0.15, 4.0),
        'minecraft:particle_appearance_billboard': bb('drop', ['0.08 + v.particle_random_3 * 0.06'] * 2, 'lookat_direction', 'velocity'),
        'minecraft:particle_appearance_tinting': col('0.35, 0.65, 1.0', alpha=FADE, white='0.7')}))
    out.append(P('bc:fx_ice', 'shard', add, {**INIT, **once(f'math.round(16 * {SC})'), **sphere(f'0.3 * {SC}'),
        **life('0.6 + v.particle_random_1 * 0.5'), 'minecraft:particle_initial_speed': f'(4.0 + {R2} * 6.0) * math.sqrt({SC})',
        **dyn((0, -12, 0), 1.0), **collide(0.3, 3.0), **spin('math.random(-500, 500)'),
        'minecraft:particle_appearance_billboard': bb('shard', ['0.1 + v.particle_random_3 * 0.1'] * 2),
        'minecraft:particle_appearance_tinting': col('0.7, 0.9, 1.0', alpha=FADE, white=f'0.3 + {T_} * 0.7')}))
    out.append(P('bc:fx_flake', 'flake', add, {**INIT, **once(f'math.round(12 * {SC})'), **sphere(f'0.7 * {SC}'),
        **life('1.4 + v.particle_random_1 * 1.0'), 'minecraft:particle_initial_speed': '0.8 + v.particle_random_2 * 1.4',
        **dyn((0, -0.9, 0), 1.6), **spin('math.random(-140, 140)'),
        'minecraft:particle_appearance_billboard': bb('flake', ['0.06 + v.particle_random_3 * 0.05'] * 2),
        'minecraft:particle_appearance_tinting': col('0.8, 0.95, 1.0', alpha=INOUT, white='0.6')}))
    out.append(P('bc:fx_leaf', 'leaf', alpha, {**INIT, **once(f'math.round(12 * {SC})'), **sphere(f'0.4 * {SC}'),
        **life('1.5 + v.particle_random_1 * 1.0'), 'minecraft:particle_initial_speed': f'(2.5 + {R2} * 3.5) * math.sqrt({SC})',
        **dyn((0, -2.2, 0), 2.6), **spin('math.random(-320, 320)'),
        'minecraft:particle_appearance_billboard': bb('leaf', ['0.1 + v.particle_random_3 * 0.07'] * 2),
        'minecraft:particle_appearance_tinting': col('0.35, 0.75, 0.3', mul=f'(0.75 + {R4} * 0.25)'),
        'minecraft:particle_appearance_lighting': {}}))
    out.append(P('bc:fx_bubble', 'bubble', add, {**INIT, **once(f'math.round(12 * {SC})'), **sphere(f'0.5 * {SC}'),
        **life('0.8 + v.particle_random_1 * 0.7'), 'minecraft:particle_initial_speed': '1.0 + v.particle_random_2 * 2.0',
        **dyn((0, 1.6, 0), 2.2),
        'minecraft:particle_appearance_billboard': bb('bubble', ['0.08 + v.particle_random_3 * 0.14'] * 2),
        'minecraft:particle_appearance_tinting': col('0.6, 0.85, 1.0', alpha=f'{FADE} * 0.9', white='0.5')}))
    out.append(P('bc:fx_star', 'star', add, {**INIT, **once(f'math.round(12 * {SC})'), **sphere(f'0.4 * {SC}'),
        **life('0.6 + v.particle_random_1 * 0.6'), 'minecraft:particle_initial_speed': f'(2.0 + {R2} * 3.5) * math.sqrt({SC})',
        **dyn((0, 0.3, 0), 3.0), **spin('math.random(-180, 180)'),
        'minecraft:particle_appearance_billboard': bb('star', [f'(0.08 + {R3} * 0.1) * (0.6 + math.sin(v.particle_age * 1600.0 + {R4} * 360.0) * 0.4)'] * 2),
        'minecraft:particle_appearance_tinting': col(alpha=FADE, white=f'0.6 - {T_} * 0.4')}))
    out.append(P('bc:fx_note', 'note', add, {**INIT, **once(f'math.round(7 * {SC})'), **sphere(f'0.4 * {SC}'),
        **life('0.9 + v.particle_random_1 * 0.4'), 'minecraft:particle_initial_speed': '1.5 + v.particle_random_2 * 1.5', **dyn((0, 1.0, 0), 2.0),
        'minecraft:particle_appearance_billboard': bb('note', ['0.14'] * 2),
        'minecraft:particle_appearance_tinting': col(alpha=INOUT, white='0.4')}))
    out.append(P('bc:fx_glyph', 'glyph', add, {**INIT, **once(f'math.round(8 * {SC})'), **sphere(f'0.8 * {SC}'),
        **life('0.9 + v.particle_random_1 * 0.6'), 'minecraft:particle_initial_speed': '0.5 + v.particle_random_2 * 0.8', **dyn((0, 0.9, 0), 1.6),
        'minecraft:particle_appearance_billboard': bb('glyph', ['0.15'] * 2, pick=(1, 8, 32, 32)),
        'minecraft:particle_appearance_tinting': col(alpha=INOUT, white='0.5')}))
    return out


# ---------------------------------------------------------------- projectile halo and element trails
FLAVORS = ['energy', 'fire', 'water', 'ice', 'spark', 'earth', 'leaf', 'void', 'star', 'wind', 'bubble']


def trail_effects():
    out = []
    add = 'particles_add'
    TC = ['v.tr ?? 1.0', 'v.tg ?? 1.0', 'v.tb ?? 1.0']

    def tint(alpha, white=None):
        if white:
            return {'color': [f'math.lerp(1.0, {c}, {white})' for c in TC] + [alpha]}
        return {'color': TC + [alpha]}

    def trail(ident, texture, material, flavor, rate, lifetime, size, extra, tinting, mode='lookat_xyz', direction=None, **uvkw):
        rate_expr = f'(v.fk ?? 0) == {FLAVORS.index(flavor)} ? {rate} : 0' if flavor else rate
        c = {'minecraft:emitter_rate_steady': {'spawn_rate': rate_expr, 'max_particles': 80},
             'minecraft:emitter_lifetime_expression': {'activation_expression': 1, 'expiration_expression': 0},
             'minecraft:emitter_local_space': {'position': False, 'rotation': False},
             **life(lifetime), **extra,
             'minecraft:particle_appearance_billboard': bb(texture, size, mode, direction, **uvkw),
             'minecraft:particle_appearance_tinting': tinting}
        if 'minecraft:emitter_shape_sphere' not in extra and 'minecraft:emitter_shape_point' not in extra:
            c.update(sphere(0.12))
        return P(ident, texture, material, c)

    # the halo: a soft glow that rides on the bolt (local space), sized by v.hs
    out.append(P('bc:fx_halo', 'soft', add, {
        'minecraft:emitter_rate_steady': {'spawn_rate': 30, 'max_particles': 4},
        'minecraft:emitter_lifetime_expression': {'activation_expression': 1, 'expiration_expression': 0},
        'minecraft:emitter_local_space': {'position': True, 'rotation': False}, **point(), **life('0.12'),
        'minecraft:particle_appearance_billboard': bb('soft', ['(v.hs ?? 1.0) * 0.9 * (1.0 + math.sin(v.particle_age * 3000.0) * 0.1)'] * 2),
        'minecraft:particle_appearance_tinting': tint('0.75', '0.8')}))
    # every bolt: a bright streaking core
    out.append(trail('bc:fx_trail', 'soft', add, None, 70, '0.28 + v.particle_random_1 * 0.12', [f'(v.hs ?? 1.0) * 0.32 * {FADE}'] * 2,
                     {'minecraft:particle_initial_speed': 0.15}, tint(FADE, f'math.min({T_} * 2.0, 1.0)')))
    out.append(trail('bc:fx_trail_energy', 'star', add, 'energy', 18, '0.35 + v.particle_random_1 * 0.3', ['0.07 + v.particle_random_3 * 0.05'] * 2,
                     {'minecraft:particle_initial_speed': 0.8, **dyn((0, 0, 0), 2.0)}, tint(FADE, '0.6')))
    out.append(trail('bc:fx_trail_fire', 'fire', add, 'fire', 45, '0.35 + v.particle_random_1 * 0.25', [f'(0.22 + {R3} * 0.15) * (v.hs ?? 1.0)'] * 2,
                     {'minecraft:particle_initial_speed': 0.4, **dyn((0, 2.0, 0), 2.0), **spin('math.random(-60, 60)')},
                     grad3(('1.0', '0.95', '0.75'), ('0.3', '0.03', '0.0'), FADE), frames=8))
    out.append(trail('bc:fx_trail_water', 'drop', add, 'water', 30, '0.4 + v.particle_random_1 * 0.3', ['0.07'] * 2,
                     {'minecraft:particle_initial_speed': 1.0, **dyn((0, -9, 0), 0.8)}, tint(FADE, '0.7'), 'lookat_direction', 'velocity'))
    out.append(trail('bc:fx_trail_ice', 'flake', add, 'ice', 22, '0.6 + v.particle_random_1 * 0.4', ['0.06'] * 2,
                     {'minecraft:particle_initial_speed': 0.4, **dyn((0, -0.8, 0), 1.2), **spin('math.random(-200, 200)')}, tint(FADE, '0.5')))
    out.append(trail('bc:fx_trail_spark', 'streak', add, 'spark', 40, '0.18 + v.particle_random_1 * 0.12', ['0.035', '0.18'],
                     {'minecraft:particle_initial_speed': '3.0 + v.particle_random_2 * 4.0'}, tint(FADE, '0.4'), 'lookat_direction', 'velocity'))
    out.append(trail('bc:fx_trail_earth', 'dust', 'particles_blend', 'earth', 22, '0.6 + v.particle_random_1 * 0.4', [f'(0.18 + {T_} * 0.35) * (v.hs ?? 1.0)'] * 2,
                     {'minecraft:particle_initial_speed': 0.4, **dyn((0, -0.4, 0), 1.6)},
                     {'color': ['0.55', '0.5', '0.42', f'0.55 * {FADE}']}))
    out.append(trail('bc:fx_trail_leaf', 'leaf', 'particles_alpha', 'leaf', 14, '0.9 + v.particle_random_1 * 0.5', ['0.08'] * 2,
                     {'minecraft:particle_initial_speed': 0.6, **dyn((0, -1.0, 0), 2.0), **spin('math.random(-300, 300)'),
                      'minecraft:particle_appearance_lighting': {}}, tint('1.0')))
    out.append(trail('bc:fx_trail_void', 'smoke', 'particles_blend', 'void', 28, '0.5 + v.particle_random_1 * 0.3', [f'(0.25 + {T_} * 0.35) * (v.hs ?? 1.0)'] * 2,
                     {'minecraft:particle_initial_speed': 0.3, **dyn((0, 0.2, 0), 1.5)},
                     {'color': ['(v.tr ?? 0.3) * 0.2', '(v.tg ?? 0.1) * 0.2', '(v.tb ?? 0.4) * 0.2', f'0.8 * {FADE}']}, frames=8))
    out.append(trail('bc:fx_trail_star', 'star', add, 'star', 26, '0.5 + v.particle_random_1 * 0.4',
                     [f'0.09 * (0.6 + math.sin(v.particle_age * 1600.0 + {R4} * 360.0) * 0.4)'] * 2,
                     {'minecraft:particle_initial_speed': 0.7, **dyn((0, 0, 0), 2.0), **spin('math.random(-180, 180)')}, tint(FADE, '0.5')))
    out.append(trail('bc:fx_trail_wind', 'wisp', add, 'wind', 22, '0.35 + v.particle_random_1 * 0.2', [f'0.3 * (v.hs ?? 1.0)'] * 2,
                     {'minecraft:particle_initial_speed': 0.6, **spin('math.random(-600, 600)')}, tint(f'0.8 * {FADE}', '0.7')))
    out.append(trail('bc:fx_trail_bubble', 'bubble', add, 'bubble', 20, '0.5 + v.particle_random_1 * 0.4', ['0.06 + v.particle_random_3 * 0.08'] * 2,
                     {'minecraft:particle_initial_speed': 0.5, **dyn((0, 1.0, 0), 2.0)}, tint(FADE, '0.6')))
    return out


TRAIL_IDS = ['bc:fx_trail'] + [f'bc:fx_trail_{f}' for f in FLAVORS if f in
                                ('energy', 'fire', 'water', 'ice', 'spark', 'earth', 'leaf', 'void', 'star', 'wind', 'bubble')]


def build():
    gen_textures()
    for ident, data in effects() + trail_effects():
        write_json(RP, f"particles/bc/v9/{ident.split(':')[1]}.particle.json", data)
