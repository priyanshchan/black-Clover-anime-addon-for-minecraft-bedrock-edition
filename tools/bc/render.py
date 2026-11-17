"""Software preview renderer for Bedrock .geo.json models (dev-only tool).

Implements the Bedrock conventions used by Blockbench:
  * file X is mirrored for display
  * rotations [rx, ry, rz] -> display Rz(rz) * Ry(-ry) * Rx(-rx)
  * bone local = T(anim_pos) T(pivot) R S T(-pivot)
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

from . import molang


def rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]], np.float64)


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]], np.float64)


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], np.float64)


def T(v):
    m = np.eye(4)
    m[:3, 3] = v
    return m


def Sc(v):
    m = np.eye(4)
    m[0, 0], m[1, 1], m[2, 2] = v
    return m


def rot_disp(r):
    x, y, z = [math.radians(float(v)) for v in r]
    return rz(z) @ ry(-y) @ rx(-x)


def d(v):
    """file -> display coordinates."""
    return np.array([-v[0], v[1], v[2]], np.float64)


FACE_CORNERS = {
    'north': lambda x0, x1, y0, y1, z0, z1: [((x0, y1, z0), (0, 0)), ((x1, y1, z0), (1, 0)), ((x1, y0, z0), (1, 1)), ((x0, y0, z0), (0, 1))],
    'south': lambda x0, x1, y0, y1, z0, z1: [((x1, y1, z1), (0, 0)), ((x0, y1, z1), (1, 0)), ((x0, y0, z1), (1, 1)), ((x1, y0, z1), (0, 1))],
    'east': lambda x0, x1, y0, y1, z0, z1: [((x0, y1, z1), (0, 0)), ((x0, y1, z0), (1, 0)), ((x0, y0, z0), (1, 1)), ((x0, y0, z1), (0, 1))],
    'west': lambda x0, x1, y0, y1, z0, z1: [((x1, y1, z0), (0, 0)), ((x1, y1, z1), (1, 0)), ((x1, y0, z1), (1, 1)), ((x1, y0, z0), (0, 1))],
    'up': lambda x0, x1, y0, y1, z0, z1: [((x0, y1, z1), (0, 0)), ((x1, y1, z1), (1, 0)), ((x1, y1, z0), (1, 1)), ((x0, y1, z0), (0, 1))],
    'down': lambda x0, x1, y0, y1, z0, z1: [((x0, y0, z0), (0, 0)), ((x1, y0, z0), (1, 0)), ((x1, y0, z1), (1, 1)), ((x0, y0, z1), (0, 1))],
}


class Model:
    def __init__(self, geo_json, texture: np.ndarray, blend=False, emissive=False):
        g = geo_json['minecraft:geometry'][0] if 'minecraft:geometry' in geo_json else geo_json
        self.desc = g['description']
        self.bones = g['bones']
        self.tex = texture
        self.blend = blend
        self.emissive = emissive
        self.byname = {b['name'].lower(): b for b in self.bones}

    def world_mats(self, pose):
        cache = {}

        def mat(name):
            key = name.lower()
            if key in cache:
                return cache[key]
            b = self.byname[key]
            p = pose.get(key, {})
            rot = [float(v) for v in b.get('rotation', [0, 0, 0])]
            ar = p.get('rotation', [0, 0, 0])
            rot = [rot[i] + ar[i] for i in range(3)]
            pos = p.get('position', [0, 0, 0])
            sc = p.get('scale', [1, 1, 1])
            if isinstance(sc, (int, float)):
                sc = [sc] * 3
            piv = d(b.get('pivot', [0, 0, 0]))
            local = T(d(pos)) @ T(piv) @ rot_disp(rot) @ Sc(sc) @ T(-piv)
            parent = b.get('parent')
            m = (mat(parent) @ local) if parent and parent.lower() in self.byname else local
            cache[key] = m
            return m

        return {b['name'].lower(): mat(b['name']) for b in self.bones}

    def quads(self, pose=None, root=np.eye(4), hidden=()):
        pose = pose or {}
        mats = self.world_mats(pose)
        tw, th = self.desc['texture_width'], self.desc['texture_height']
        ph, pw = self.tex.shape[:2]
        su, sv = pw / tw, ph / th
        out = []
        for b in self.bones:
            if b['name'].lower() in hidden:
                continue
            M = root @ mats[b['name'].lower()]
            for c in b.get('cubes', []):
                o = c['origin']
                s = c['size']
                inf = c.get('inflate', 0)
                x0, y0, z0 = o[0] - inf, o[1] - inf, o[2] - inf
                x1, y1, z1 = o[0] + s[0] + inf, o[1] + s[1] + inf, o[2] + s[2] + inf
                CM = np.eye(4)
                if 'rotation' in c:
                    piv = d(c.get('pivot', [0, 0, 0]))
                    CM = T(piv) @ rot_disp(c['rotation']) @ T(-piv)
                for f, spec in c.get('uv', {}).items():
                    u, v = spec['uv']
                    w, h = spec['uv_size']
                    corners = FACE_CORNERS[f](x0, x1, y0, y1, z0, z1)
                    pts = []
                    uvs = []
                    for p, (fu, fv) in corners:
                        P = M @ CM @ np.append(d(p), 1.0)
                        pts.append(P[:3])
                        uvs.append(((u + fu * w) * su, (v + fv * h) * sv))
                    out.append((np.array(pts), np.array(uvs)))
        return out


def look_at(eye, target, up=(0, 1, 0)):
    eye, target, up = map(lambda a: np.array(a, np.float64), (eye, target, up))
    f = target - eye
    f /= np.linalg.norm(f)
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    m = np.eye(4)
    m[0, :3], m[1, :3], m[2, :3] = r, u, -f
    m[:3, 3] = -m[:3, :3] @ eye
    return m


class Scene:
    def __init__(self, w=512, h=512, bg=(0, 0, 0, 0), ss=2):
        self.W, self.H, self.ss = w * ss, h * ss, ss
        self.out_w, self.out_h = w, h
        self.color = np.zeros((self.H, self.W, 4), np.float32)
        self.color[:] = bg
        self.z = np.full((self.H, self.W), np.inf, np.float32)
        self.items = []

    def add(self, model: Model, pose=None, root=np.eye(4), hidden=()):
        self.items.append((model, model.quads(pose, root, hidden)))

    def render(self, eye, target, fov=40.0, ortho=None, light=(0.4, 0.8, -0.6)):
        V = look_at(eye, target)
        L = np.array(light, np.float64)
        L /= np.linalg.norm(L)
        f = 1.0 / math.tan(math.radians(fov) / 2)
        tris = []
        for model, quads in self.items:
            for pts, uvs in quads:
                for idx in ((0, 1, 2), (0, 2, 3)):
                    tris.append((model, pts[list(idx)], uvs[list(idx)]))
        # draw opaque first, translucent afterwards (sorted far -> near)
        def depth(t):
            P = (V @ np.c_[t[1], np.ones(3)].T).T
            return P[:, 2].mean()
        tris.sort(key=lambda t: (t[0].blend, depth(t) if t[0].blend else 0))
        for model, pts, uvs in tris:
            P = (V @ np.c_[pts, np.ones(3)].T).T[:, :3]
            # normal in world for lighting
            n = np.cross(pts[1] - pts[0], pts[2] - pts[0])
            nn = np.linalg.norm(n)
            if nn < 1e-9:
                continue
            n /= nn
            shade = 0.62 + 0.38 * abs(float(n @ L))
            if abs(n[1]) > 0.7:
                shade = 1.0 if n[1] > 0 else 0.55
            zc = -P[:, 2]
            if np.any(zc <= 0.05):
                continue
            if ortho:
                sx = P[:, 0] / ortho * (self.H / 2) + self.W / 2
                sy = -P[:, 1] / ortho * (self.H / 2) + self.H / 2
                invw = np.ones(3)
            else:
                sx = (P[:, 0] * f / zc) * (self.H / 2) + self.W / 2
                sy = (-P[:, 1] * f / zc) * (self.H / 2) + self.H / 2
                invw = 1.0 / zc
            self._raster(model, sx, sy, zc, invw, uvs, shade)

    def _raster(self, model, sx, sy, zc, invw, uvs, shade):
        xmin = max(int(math.floor(sx.min())), 0)
        xmax = min(int(math.ceil(sx.max())), self.W - 1)
        ymin = max(int(math.floor(sy.min())), 0)
        ymax = min(int(math.ceil(sy.max())), self.H - 1)
        if xmin > xmax or ymin > ymax:
            return
        ys, xs = np.mgrid[ymin:ymax + 1, xmin:xmax + 1].astype(np.float64) + 0.5
        x0, x1, x2 = sx
        y0, y1, y2 = sy
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-12:
            return
        w0 = ((y1 - y2) * (xs - x2) + (x2 - x1) * (ys - y2)) / den
        w1 = ((y2 - y0) * (xs - x2) + (x0 - x2) * (ys - y2)) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            return
        iw = w0 * invw[0] + w1 * invw[1] + w2 * invw[2]
        z = 1.0 / iw
        u = (w0 * uvs[0, 0] * invw[0] + w1 * uvs[1, 0] * invw[1] + w2 * uvs[2, 0] * invw[2]) * z
        v = (w0 * uvs[0, 1] * invw[0] + w1 * uvs[1, 1] * invw[1] + w2 * uvs[2, 1] * invw[2]) * z
        th, tw = model.tex.shape[:2]
        ui = np.clip(np.floor(u).astype(int), 0, tw - 1)
        vi = np.clip(np.floor(v).astype(int), 0, th - 1)
        texel = model.tex[vi, ui]
        a = texel[..., 3]
        zbuf = self.z[ymin:ymax + 1, xmin:xmax + 1]
        cbuf = self.color[ymin:ymax + 1, xmin:xmax + 1]
        visible = inside & (z < zbuf)
        if model.blend:
            m = visible & (a > 8)
            al = (a / 255.0)[..., None]
            rgb = texel[..., :3] * shade
            cbuf[..., :3] = np.where(m[..., None], cbuf[..., :3] * (1 - al) + rgb * al, cbuf[..., :3])
            cbuf[..., 3] = np.where(m, np.maximum(cbuf[..., 3], a), cbuf[..., 3])
        else:
            m = visible & (a >= 100)
            emiss = (a < 250)[..., None] & m[..., None]
            sh = np.where(emiss, 1.0, shade) if model.emissive else shade
            rgb = texel[..., :3] * sh
            cbuf[..., :3] = np.where(m[..., None], rgb, cbuf[..., :3])
            cbuf[..., 3] = np.where(m, 255, cbuf[..., 3])
            zbuf[...] = np.where(m, z, zbuf)

    def image(self):
        img = Image.fromarray(np.clip(self.color, 0, 255).astype(np.uint8), 'RGBA')
        if self.ss > 1:
            img = img.resize((self.out_w, self.out_h), Image.LANCZOS)
        return img


# ------------------------------------------------------------------------- animation
def _interp(frames, t, env):
    keys = sorted(frames.keys(), key=float)
    times = [float(k) for k in keys]

    def val(k, which='pre'):
        fr = frames[k]
        if isinstance(fr, dict):
            fr = fr.get(which, fr.get('post', fr.get('pre')))
        return [molang.evaluate(x, env) for x in fr] if isinstance(fr, list) else [molang.evaluate(fr, env)] * 3

    if t <= times[0]:
        return val(keys[0])
    if t >= times[-1]:
        return val(keys[-1], 'post')
    for i in range(len(times) - 1):
        if times[i] <= t <= times[i + 1]:
            a = val(keys[i], 'post')
            b = val(keys[i + 1])
            f = (t - times[i]) / (times[i + 1] - times[i])
            return [a[j] + (b[j] - a[j]) * f for j in range(3)]
    return [0, 0, 0]


def pose_from_anim(anim, t, env=None, pose=None):
    """Evaluate an animation dict at time t into a pose dict (bone -> channels)."""
    env = dict(env or {})
    env.setdefault('q.anim_time', t)
    env.setdefault('q.life_time', t)
    pose = pose if pose is not None else {}
    length = anim.get('animation_length')
    if anim.get('loop') is True and length:
        t = t % length
        env['q.anim_time'] = t
    for bone, ch in anim.get('bones', {}).items():
        bp = pose.setdefault(bone.lower(), {})
        for k in ('rotation', 'position', 'scale'):
            if k not in ch:
                continue
            v = ch[k]
            if isinstance(v, dict) and not ('pre' in v or 'post' in v):
                vals = _interp(v, t, env)
            elif isinstance(v, list):
                vals = [molang.evaluate(x, env) for x in v]
            else:
                x = molang.evaluate(v, env)
                vals = [x, x, x]
            if k == 'scale':
                old = bp.get('scale', [1, 1, 1])
                bp['scale'] = [old[i] * vals[i] for i in range(3)]
            else:
                old = bp.get(k, [0, 0, 0])
                bp[k] = [old[i] + vals[i] for i in range(3)]
    return pose


def orbit_eye(target, dist, yaw_deg, pitch_deg):
    """Camera position orbiting a target. yaw 0 = looking at the model's front."""
    y, p = math.radians(yaw_deg), math.radians(pitch_deg)
    tx, ty, tz = target
    return (tx + dist * math.sin(y) * math.cos(p), ty + dist * math.sin(p), tz - dist * math.cos(y) * math.cos(p))
