"""Procedural pixel-art texture toolkit.

All painters work on float32 numpy arrays shaped (h, w, 4) with RGBA in 0..255.
Colours are quantised onto hand-picked ramps so the results read as pixel art
instead of noisy photographs.
"""
from __future__ import annotations

import math
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


# --------------------------------------------------------------------------------------
# colour helpers
# --------------------------------------------------------------------------------------
def rgb(h: str, a: int = 255):
    h = h.lstrip('#')
    return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a], dtype=np.float32)


def ramp(*hexes):
    return [rgb(h) for h in hexes]


def mix(a, b, t):
    return a * (1 - t) + b * t


def seed_of(*parts) -> int:
    return zlib.crc32('|'.join(str(p) for p in parts).encode()) & 0xFFFFFFFF


def value_noise(h: int, w: int, cell: float, seed: int, octaves: int = 2) -> np.ndarray:
    """Smooth value noise in [-1, 1]."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    c = max(cell, 1.0)
    for _ in range(octaves):
        gh, gw = int(h / c) + 2, int(w / c) + 2
        grid = rng.uniform(-1, 1, (gh, gw)).astype(np.float32)
        ys = np.arange(h) / c
        xs = np.arange(w) / c
        y0 = np.floor(ys).astype(int)
        x0 = np.floor(xs).astype(int)
        fy = (ys - y0)[:, None]
        fx = (xs - x0)[None, :]
        fy = fy * fy * (3 - 2 * fy)
        fx = fx * fx * (3 - 2 * fx)
        g00 = grid[y0][:, x0]
        g01 = grid[y0][:, x0 + 1]
        g10 = grid[y0 + 1][:, x0]
        g11 = grid[y0 + 1][:, x0 + 1]
        n = mix(mix(g00, g01, fx), mix(g10, g11, fx), fy)
        out += n * amp
        total += amp
        amp *= 0.5
        c = max(c / 2, 1.0)
    return out / total


def white_noise(h, w, seed):
    return np.random.default_rng(seed).uniform(-1, 1, (h, w)).astype(np.float32)


def quantize(r, t: np.ndarray) -> np.ndarray:
    """Map t in [0,1] onto ramp colours (nearest entry) -> (h,w,4)."""
    n = len(r)
    idx = np.clip(np.rint(t * (n - 1)), 0, n - 1).astype(int)
    arr = np.stack(r)
    return arr[idx]


def smooth_ramp(r, t: np.ndarray) -> np.ndarray:
    n = len(r)
    x = np.clip(t, 0, 1) * (n - 1)
    i0 = np.clip(np.floor(x).astype(int), 0, n - 1)
    i1 = np.clip(i0 + 1, 0, n - 1)
    f = (x - i0)[..., None]
    arr = np.stack(r)
    return arr[i0] * (1 - f) + arr[i1] * f


# --------------------------------------------------------------------------------------
# image helpers
# --------------------------------------------------------------------------------------
def new(h, w, color=None):
    a = np.zeros((h, w, 4), np.float32)
    if color is not None:
        a[:] = color
    return a


def to_image(a: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(np.rint(a), 0, 255).astype(np.uint8), 'RGBA')


def from_image(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert('RGBA')).astype(np.float32)


def save(a: np.ndarray, path: str):
    to_image(a).save(path, optimize=True)


def alpha_over(dst: np.ndarray, src: np.ndarray):
    """In-place 'src over dst' compositing."""
    sa = src[..., 3:4] / 255.0
    da = dst[..., 3:4] / 255.0
    oa = sa + da * (1 - sa)
    rgb_ = np.where(oa > 0, (src[..., :3] * sa + dst[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    dst[..., :3] = rgb_
    dst[..., 3:4] = oa * 255.0
    return dst


def draw_layer(h, w, fn, supersample=1):
    """Run a PIL ImageDraw function on a transparent layer, return float array."""
    ss = supersample
    img = Image.new('RGBA', (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fn(d, ss)
    if ss > 1:
        img = img.resize((w, h), Image.LANCZOS)
    return from_image(img)


def outline(a: np.ndarray, color, thickness=1, alpha_thresh=10):
    """Add an outline around opaque pixels (outside)."""
    mask = a[..., 3] > alpha_thresh
    grown = mask.copy()
    for _ in range(thickness):
        g = grown.copy()
        g[1:, :] |= grown[:-1, :]
        g[:-1, :] |= grown[1:, :]
        g[:, 1:] |= grown[:, :-1]
        g[:, :-1] |= grown[:, 1:]
        grown = g
    ring = grown & ~mask
    a[ring] = color
    return a


def inner_edge(a, factor=0.7, sides=('t', 'b', 'l', 'r'), width=1):
    h, w = a.shape[:2]
    for i in range(width):
        if 't' in sides and h > 2 * i:
            a[i, :, :3] *= factor
        if 'b' in sides and h > 2 * i:
            a[h - 1 - i, :, :3] *= factor
        if 'l' in sides and w > 2 * i:
            a[:, i, :3] *= factor
        if 'r' in sides and w > 2 * i:
            a[:, w - 1 - i, :3] *= factor
    return a


def glow(a: np.ndarray, radius: float, strength=1.0):
    """Soft additive glow from the image itself (used for particles/glyphs)."""
    img = to_image(a)
    blurred = from_image(img.filter(ImageFilter.GaussianBlur(radius)))
    out = a.copy()
    ba = blurred[..., 3:4] / 255.0 * strength
    out_a = np.maximum(out[..., 3:4], np.clip(ba * 255.0, 0, 255))
    # colour where only glow exists comes from the blurred colour
    only_glow = (a[..., 3:4] < 1)
    out[..., :3] = np.where(only_glow, blurred[..., :3], out[..., :3])
    out[..., 3:4] = out_a
    return out


# --------------------------------------------------------------------------------------
# face painting context
# --------------------------------------------------------------------------------------
FACE_TONE = {'up': 0.72, 'north': 0.55, 'south': 0.5, 'east': 0.48, 'west': 0.48, 'down': 0.3}


class FaceCtx:
    def __init__(self, face, w, h, res, cube, seed):
        self.face = face
        self.w = w          # pixels
        self.h = h
        self.res = res      # pixels per model unit
        self.cube = cube    # dict with origin/size/name
        self.seed = seed

    @property
    def is_side(self):
        return self.face not in ('up', 'down')


# --------------------------------------------------------------------------------------
# materials
# --------------------------------------------------------------------------------------
class Material:
    """Base material: shaded, noisy, edge-darkened surface quantised to a ramp."""

    def __init__(self, r, noise=0.12, cell=2.5, edge=0.72, highlight=True, grad=0.12,
                 alpha=255, emissive=False, smooth=False, tone_shift=0.0):
        self.r = r
        self.noise = noise
        self.cell = cell
        self.edge = edge
        self.highlight = highlight
        self.grad = grad
        self.alpha = alpha
        self.emissive = emissive
        self.smooth = smooth
        self.tone_shift = tone_shift

    def tone(self, ctx: FaceCtx) -> np.ndarray:
        h, w = ctx.h, ctx.w
        t = np.full((h, w), FACE_TONE[ctx.face] + self.tone_shift, np.float32)
        if ctx.is_side and self.grad:
            t += np.linspace(self.grad, -self.grad, h, dtype=np.float32)[:, None]
        t += value_noise(h, w, self.cell * ctx.res / 2 + 1, ctx.seed) * self.noise
        t += white_noise(h, w, ctx.seed + 7) * self.noise * 0.45
        return t

    def finish(self, a, ctx):
        h, w = a.shape[:2]
        if self.edge and h > 2 and w > 2:
            inner_edge(a, self.edge)
        if self.highlight and ctx.is_side and h > 3:
            a[0, 1:-1, :3] = np.minimum(a[0, 1:-1, :3] * 1.25 + 12, 255)
        a[..., 3] = self.alpha
        return a

    def __call__(self, a, ctx):
        t = self.tone(ctx)
        col = smooth_ramp(self.r, t) if self.smooth else quantize(self.r, t)
        a[:] = col
        return self.finish(a, ctx)


class Metal(Material):
    def __init__(self, r, sheen=0.35, **kw):
        kw.setdefault('noise', 0.06)
        super().__init__(r, **kw)
        self.sheen = sheen

    def tone(self, ctx):
        t = super().tone(ctx)
        h, w = ctx.h, ctx.w
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d = (xx / max(w, 1) + yy / max(h, 1))
        band = np.exp(-((d - 0.75) ** 2) / 0.02) * self.sheen
        band2 = np.exp(-((d - 1.25) ** 2) / 0.008) * self.sheen * 0.6
        return t + band + band2


class Cloth(Material):
    def __init__(self, r, folds=0.18, **kw):
        kw.setdefault('noise', 0.08)
        kw.setdefault('highlight', False)
        super().__init__(r, **kw)
        self.folds = folds

    def tone(self, ctx):
        t = super().tone(ctx)
        h, w = ctx.h, ctx.w
        if ctx.is_side:
            xx = np.arange(w, dtype=np.float32)
            ph = (ctx.seed % 100) / 15.0
            fold = np.sin(xx / max(2.2 * ctx.res, 1.5) + ph) * self.folds
            t += fold[None, :]
        yy, xx = np.mgrid[0:h, 0:w]
        t += ((xx + yy) % 2 == 0) * 0.03
        return t


class Stone(Material):
    def __init__(self, r, brick=4, **kw):
        kw.setdefault('noise', 0.16)
        kw.setdefault('cell', 1.5)
        super().__init__(r, **kw)
        self.brick = brick

    def __call__(self, a, ctx):
        super().__call__(a, ctx)
        h, w = ctx.h, ctx.w
        b = self.brick * ctx.res
        if b >= 3 and ctx.is_side:
            for y in range(0, h, b):
                a[y, :, :3] *= 0.7
                off = (y // b) % 2 * (b // 1)
                for x in range(off % (2 * b), w, 2 * b):
                    a[y:y + b, x, :3] *= 0.75
        rng = np.random.default_rng(ctx.seed + 3)
        for _ in range(max(1, (h * w) // 140)):
            y, x = rng.integers(0, h), rng.integers(0, w)
            ln = rng.integers(2, 5)
            for i in range(ln):
                yy, xx = min(h - 1, y + i), min(w - 1, x + rng.integers(-1, 2))
                a[yy, xx, :3] *= 0.65
        a[..., 3] = self.alpha
        return a


class Wood(Material):
    def __init__(self, r, **kw):
        kw.setdefault('noise', 0.06)
        super().__init__(r, **kw)

    def tone(self, ctx):
        t = super().tone(ctx)
        h, w = ctx.h, ctx.w
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        along_y = h >= w
        coord = xx if along_y else yy
        n = value_noise(h, w, 3, ctx.seed + 11)
        t += np.sin(coord * 1.7 + n * 3.0) * 0.12
        return t


class Crystal(Material):
    def __init__(self, r, alpha=200, **kw):
        kw.setdefault('noise', 0.05)
        kw.setdefault('edge', 0)
        kw.setdefault('highlight', False)
        super().__init__(r, alpha=alpha, **kw)

    def __call__(self, a, ctx):
        h, w = ctx.h, ctx.w
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        t = 0.35 + 0.45 * (1 - yy / max(h - 1, 1)) * 0.6 + 0.3 * (xx / max(w - 1, 1))
        facet = ((xx * 0.7 + yy) % (3 * ctx.res + 2)) < ctx.res
        t = t + facet * 0.18 + value_noise(h, w, 2, ctx.seed) * self.noise
        a[:] = quantize(self.r, np.clip(t, 0, 1))
        a[..., 3] = self.alpha
        # bright rim
        if h > 1 and w > 1:
            for edge in (a[0, :], a[:, 0]):
                edge[:, :3] = np.minimum(edge[:, :3] * 1.35 + 30, 255)
                edge[:, 3] = min(255, self.alpha + 40)
            a[-1, :, :3] *= 0.85
            a[:, -1, :3] *= 0.85
        return a


class Energy(Material):
    """Bright glowing surface; core alpha marks emissive pixels."""

    def __init__(self, r, alpha=130, flicker=0.25, **kw):
        kw.setdefault('edge', 0)
        kw.setdefault('highlight', False)
        super().__init__(r, alpha=alpha, **kw)
        self.flicker = flicker

    def __call__(self, a, ctx):
        h, w = ctx.h, ctx.w
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        cy, cx = (h - 1) / 2, (w - 1) / 2
        d = np.sqrt(((yy - cy) / max(cy, 0.5)) ** 2 + ((xx - cx) / max(cx, 0.5)) ** 2) / 1.42
        t = 1.0 - d * 0.65 + value_noise(h, w, 2, ctx.seed) * self.flicker
        a[:] = quantize(self.r, np.clip(t, 0, 1))
        a[..., 3] = self.alpha
        return a


class Flat(Material):
    def __init__(self, color, alpha=None, **kw):
        c = rgb(color) if isinstance(color, str) else color
        super().__init__([c], **kw)
        self.c = c
        if alpha is not None:
            self.alpha = alpha

    def __call__(self, a, ctx):
        a[:] = self.c
        a[..., 3] = self.alpha
        return a


class Painted:
    """Wrap a base material and apply decal callbacks per face."""

    def __init__(self, base, decals: dict):
        self.base = base
        self.decals = decals  # face -> fn(a, ctx) ; '*' wildcard

    def __call__(self, a, ctx):
        self.base(a, ctx)
        fn = self.decals.get(ctx.face) or self.decals.get('*')
        if fn:
            fn(a, ctx)
        return a


class PerFace:
    def __init__(self, default, **faces):
        self.default = default
        self.faces = faces

    def __call__(self, a, ctx):
        m = self.faces.get(ctx.face, self.default)
        return m(a, ctx)


# --------------------------------------------------------------------------------------
# palettes (dark -> light)
# --------------------------------------------------------------------------------------
P = {
    'obsidian': ramp('0b0a10', '15131d', '201c2b', '2c2738', '3a3349', '4c435d'),
    'blackiron': ramp('08080a', '121216', '1c1c22', '26262e', '33333d', '474756', '62627a'),
    'steel': ramp('2d313a', '434955', '5c6370', '7a8290', '9aa3b1', 'c3cad6', 'eef2f8'),
    'gold': ramp('4a2a08', '7a4a10', 'a8701c', 'd39a2c', 'f0c24a', 'ffe58a', 'fff6cf'),
    'silver': ramp('3b3f48', '5d6370', '858c9a', 'aab1be', 'cfd5df', 'f1f4f8'),
    'leather': ramp('24140c', '3a2214', '553220', '6e432c', '8a573a', 'a36d4b'),
    'wood': ramp('2b1a0e', '42291a', '5c3a24', '764c2f', '8f5f3b', 'a8744a'),
    'paper': ramp('8d7b5c', 'b09b74', 'cdb98d', 'e3d3a8', 'f2e7c6', 'fbf5e2'),
    'stone': ramp('2a2b31', '3b3d45', '4d5059', '61656f', '777c87', '9196a1'),
    'mossstone': ramp('1f2a24', '2e3b33', '3e4c42', '515f53', '667464', '7f8c7a'),
    'deepslate': ramp('16161c', '202028', '2b2b35', '373743', '454553', '575768'),
    'red_cloth': ramp('2a0508', '470a10', '6a1018', '8f1a22', 'b32a2c', 'd8463c'),
    'black_cloth': ramp('060608', '0e0e12', '17171d', '212129', '2d2d38', '3c3c4a'),
    'white_cloth': ramp('6f7480', '9399a6', 'b7bdc8', 'd5dae2', 'eceff4', 'ffffff'),
    'purple_cloth': ramp('120818', '1f0e2a', '2f1640', '432058', '5a2c74', '763c94'),
    'devil_skin': ramp('0c0507', '1a0a0e', '2b1016', '3e1720', '541f2b', '6d2a37'),
    'bone': ramp('5b5244', '7d725f', 'a0957f', 'c2b8a0', 'ddd5bf', 'f3eedf'),
    'clover_green': ramp('0b2412', '133a1c', '1d5427', '2a7234', '3c9444', '5cb85a', '8fde7e'),
    # spell energies (dark -> bright core)
    'wind': ramp('1c6b4c', '2f9a68', '4fc884', '84e6a8', 'c2f7d2', 'f0fff4'),
    'flame': ramp('5a0d05', '9c1f07', 'd9420b', 'f7791a', 'ffb43a', 'ffe58a', 'fffbe0'),
    'water': ramp('0b2a6b', '1446a0', '1f6fd0', '3c9cf0', '7cc8ff', 'c8ecff'),
    'lightning': ramp('6b4a00', 'b58300', 'f2c200', 'ffe23d', 'fff38c', 'fffde0'),
    'light': ramp('8a6a1e', 'c99a2e', 'f2cd5a', 'ffe9a0', 'fff6d6', 'ffffff'),
    'dark': ramp('05030a', '12081f', '240f3a', '3b1860', '5a2690', '8a46c8', 'c08cff'),
    'ice': ramp('1a4a6e', '2b7aa6', '4fb0d8', '8ad8f0', 'c6f0fb', 'f2fdff'),
    'anti': ramp('000000', '0a0a0a', '161214', '2a1a1c', '5a1a1e', 'b0202a', 'ff4a4a'),
}

ELEMENT_COLORS = {
    # hex used for particles/HUD tints
    'wind': '6fe0a0', 'flame': 'ff7a1a', 'water': '3ca8ff', 'lightning': 'ffe03a',
    'light': 'fff1b0', 'dark': '8a46c8', 'ice': '8ae6ff', 'anti': '1a1a1a',
}


# --------------------------------------------------------------------------------------
# decal helpers
# --------------------------------------------------------------------------------------
def clover_shape(d: ImageDraw.ImageDraw, cx, cy, r, leaves, fill, stem=True, devil=False, rot=0.0):
    """Draw a clover with `leaves` heart-ish leaves (uses circles)."""
    for i in range(leaves):
        ang = rot + (-math.pi / 2) + i * 2 * math.pi / leaves
        for side in (-1, 1):
            a2 = ang + side * 0.42
            lx = cx + math.cos(a2) * r * 0.55
            ly = cy + math.sin(a2) * r * 0.55
            rr = r * 0.36
            d.ellipse([lx - rr, ly - rr, lx + rr, ly + rr], fill=fill)
        tx = cx + math.cos(ang) * r * 0.2
        ty = cy + math.sin(ang) * r * 0.2
        rr = r * 0.25
        d.ellipse([tx - rr, ty - rr, tx + rr, ty + rr], fill=fill)
    if stem:
        w = max(1, r * 0.12)
        d.line([(cx, cy), (cx + r * 0.35, cy + r * 1.05)], fill=fill, width=int(round(w)))
    if devil:
        # little horns on the top leaf
        d.polygon([(cx - r * 0.35, cy - r * 0.85), (cx - r * 0.55, cy - r * 1.3), (cx - r * 0.15, cy - r * 0.95)], fill=fill)
        d.polygon([(cx + r * 0.35, cy - r * 0.85), (cx + r * 0.55, cy - r * 1.3), (cx + r * 0.15, cy - r * 0.95)], fill=fill)


def stamp(a: np.ndarray, layer: np.ndarray):
    alpha_over(a, layer)
    return a


def rune_ring(h, w, color, seed, ss=4, thickness=1.0, rings=2, glyphs=12):
    """Magic circle drawing (white-ish with alpha) for particles/decals."""
    rng = np.random.default_rng(seed)

    def fn(d, s):
        cx, cy = w * s / 2, h * s / 2
        R = min(w, h) * s / 2 - 1 * s
        lw = max(1, int(thickness * s))
        d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=color, width=lw)
        R2 = R * 0.84
        d.ellipse([cx - R2, cy - R2, cx + R2, cy + R2], outline=color, width=lw)
        # glyph band
        for i in range(glyphs):
            ang = i * 2 * math.pi / glyphs
            gx = cx + math.cos(ang) * (R + R2) / 2
            gy = cy + math.sin(ang) * (R + R2) / 2
            gs = (R - R2) * 0.32
            kind = rng.integers(0, 4)
            if kind == 0:
                d.line([(gx - gs, gy), (gx + gs, gy)], fill=color, width=lw)
                d.line([(gx, gy - gs), (gx, gy + gs)], fill=color, width=lw)
            elif kind == 1:
                d.ellipse([gx - gs * 0.7, gy - gs * 0.7, gx + gs * 0.7, gy + gs * 0.7], outline=color, width=lw)
            elif kind == 2:
                d.polygon([(gx, gy - gs), (gx + gs, gy + gs), (gx - gs, gy + gs)], outline=color)
            else:
                d.line([(gx - gs, gy - gs), (gx + gs, gy + gs)], fill=color, width=lw)
                d.line([(gx - gs, gy + gs), (gx + gs, gy - gs)], fill=color, width=lw)
        # star / pentagram style
        if rings >= 2:
            R3 = R2 * 0.92
            pts = [(cx + math.cos(-math.pi / 2 + k * 4 * math.pi / 5) * R3,
                    cy + math.sin(-math.pi / 2 + k * 4 * math.pi / 5) * R3) for k in range(6)]
            d.line(pts, fill=color, width=lw)
            R4 = R2 * 0.45
            d.ellipse([cx - R4, cy - R4, cx + R4, cy + R4], outline=color, width=lw)
            # hexagon
            pts = [(cx + math.cos(k * math.pi / 3) * R2 * 0.7, cy + math.sin(k * math.pi / 3) * R2 * 0.7) for k in range(7)]
            d.line(pts, fill=color, width=max(1, lw // 2 + 1))
    return draw_layer(h, w, fn, ss)
