"""Bedrock geometry builder with automatic per-face UV atlas packing + painting.

Coordinates are Bedrock *file* coordinates (model faces -Z / "north").
Per-face UV orientation used by the painter (and by render.py):
    north (-Z): u -> +x, v -> -y        south (+Z): u -> -x, v -> -y
    east  (-X): u -> -z, v -> -y        west  (+X): u -> +z, v -> -y
    up    (+Y): u -> +x, v -> -z        down  (-Y): u -> +x, v -> +z
"""
from __future__ import annotations

import json
import math

import numpy as np

from . import tex

FACES = ('north', 'south', 'east', 'west', 'up', 'down')


def face_dims(size, face):
    sx, sy, sz = size
    if face in ('north', 'south'):
        return sx, sy
    if face in ('east', 'west'):
        return sz, sy
    return sx, sz


class Cube:
    def __init__(self, origin, size, mat, rotation=None, pivot=None, inflate=0.0, faces=None, name='', mi=None):
        self.mi = mi  # block material instance name
        self.origin = [float(v) for v in origin]
        self.size = [float(v) for v in size]
        self.mat = mat
        self.rotation = rotation
        self.pivot = pivot
        self.inflate = inflate
        self.name = name
        if faces is None:
            faces = list(FACES)
            # zero-thickness planes only need the two faces with area
            for f in FACES:
                w, h = face_dims(self.size, f)
                if w <= 0 or h <= 0:
                    faces.remove(f)
        self.faces = faces
        self.uv = {}  # face -> (u, v, w, h) in model units


class Bone:
    def __init__(self, name, parent=None, pivot=(0, 0, 0), rotation=None, binding=None, locators=None, mirror=False):
        self.name = name
        self.parent = parent
        self.pivot = [float(v) for v in pivot]
        self.rotation = rotation
        self.binding = binding
        self.locators = locators or {}
        self.cubes: list[Cube] = []


class Geo:
    def __init__(self, identifier, res=1, atlas_width=64, visible=(2, 2, (0, 0.5, 0)), seed=0):
        self.identifier = identifier
        self.res = res
        self.atlas_width = atlas_width  # in pixels
        self.bones: list[Bone] = []
        self.by_name = {}
        self.visible = visible
        self.seed = seed or tex.seed_of(identifier)
        self.atlas = None
        self.tex_w = None
        self.tex_h = None

    # ------------------------------------------------------------------ building
    def bone(self, name, parent=None, pivot=(0, 0, 0), rotation=None, binding=None, locators=None):
        b = Bone(name, parent, pivot, rotation, binding, locators)
        self.bones.append(b)
        self.by_name[name] = b
        return b

    def cube(self, bone, origin, size, mat, rotation=None, pivot=None, inflate=0.0, faces=None, name='', mi=None):
        b = self.by_name[bone] if isinstance(bone, str) else bone
        c = Cube(origin, size, mat, rotation, pivot, inflate, faces, name, mi)
        b.cubes.append(c)
        return c

    def box(self, bone, center, size, mat, **kw):
        """Cube by centre instead of origin."""
        o = [center[i] - size[i] / 2 for i in range(3)]
        return self.cube(bone, o, size, mat, **kw)

    def skeleton(self, root_parent_item=True):
        """Player skeleton bones (no cubes) so attachables follow the player pose."""
        self.bone('root', pivot=(0, 0, 0))
        self.bone('waist', 'root', (0, 12, 0))
        self.bone('body', 'waist', (0, 24, 0))
        self.bone('head', 'body', (0, 24, 0))
        self.bone('leftArm', 'body', (5, 22, 0))
        self.bone('leftItem', 'leftArm', (6, 15, 1))
        self.bone('rightArm', 'body', (-5, 22, 0))
        self.bone('rightItem', 'rightArm', (-6, 15, 1))
        self.bone('leftLeg', 'root', (1.9, 12, 0))
        self.bone('rightLeg', 'root', (-1.9, 12, 0))

    # ------------------------------------------------------------------ uv atlas
    def pack(self):
        res = self.res
        rects = []
        for b in self.bones:
            for ci, c in enumerate(b.cubes):
                for f in c.faces:
                    w, h = face_dims(c.size, f)
                    pw = max(1, int(math.ceil(w * res - 1e-6)))
                    ph = max(1, int(math.ceil(h * res - 1e-6)))
                    rects.append((ph, pw, b, ci, c, f))
        rects.sort(key=lambda r: (-r[0], -r[1]))
        W = self.atlas_width
        while True:
            x = y = shelf_h = 0
            placed = []
            ok = True
            for ph, pw, b, ci, c, f in rects:
                if pw > W:
                    ok = False
                    break
                if x + pw > W:
                    y += shelf_h
                    x = 0
                    shelf_h = 0
                placed.append((x, y, pw, ph, c, f, b, ci))
                x += pw
                shelf_h = max(shelf_h, ph)
            if ok:
                break
            W *= 2
        H = y + shelf_h
        # power-of-two-ish heights keep things tidy
        step = 16 * res
        Hp = max(step, int(math.ceil(H / step)) * step)
        if W % res or Hp % res:
            raise ValueError('atlas size must be multiple of res')
        self.atlas_px = (Hp, W)
        self.tex_w = W / res
        self.tex_h = Hp / res
        self._placed = placed

    def paint(self):
        self.pack()
        Hp, W = self.atlas_px
        a = tex.new(Hp, W)
        for x, y, pw, ph, c, f, b, ci in self._placed:
            region = tex.new(ph, pw)
            mat = c.mat
            ctx = tex.FaceCtx(f, pw, ph, self.res, {'origin': c.origin, 'size': c.size, 'name': c.name, 'bone': b.name},
                              tex.seed_of(self.identifier, b.name, ci, f))
            if isinstance(mat, dict):
                m = mat.get(f) or mat.get('*')
            else:
                m = mat
            if m is None:
                continue
            m(region, ctx)
            a[y:y + ph, x:x + pw] = region
            w, h = face_dims(c.size, f)
            c.uv[f] = (x / self.res, y / self.res, w, h)
        self.atlas = a
        return a

    # ------------------------------------------------------------------ export
    def to_json(self):
        if self.atlas is None:
            self.paint()
        bones = []
        for b in self.bones:
            jb = {'name': b.name}
            if b.parent:
                jb['parent'] = b.parent
            jb['pivot'] = [round(v, 4) for v in b.pivot]
            if b.rotation:
                jb['rotation'] = list(b.rotation)
            if b.binding:
                jb['binding'] = b.binding
            if b.locators:
                jb['locators'] = b.locators
            cubes = []
            for c in b.cubes:
                jc = {'origin': [round(v, 4) for v in c.origin], 'size': [round(v, 4) for v in c.size]}
                if c.rotation:
                    jc['rotation'] = list(c.rotation)
                    jc['pivot'] = [round(v, 4) for v in (c.pivot or [c.origin[i] + c.size[i] / 2 for i in range(3)])]
                if c.inflate:
                    jc['inflate'] = c.inflate
                uv = {}
                for f in c.faces:
                    if f in c.uv:
                        u, v, w, h = c.uv[f]
                        uv[f] = {'uv': [round(u, 4), round(v, 4)], 'uv_size': [round(w, 4), round(h, 4)]}
                        if c.mi:
                            uv[f]['material_instance'] = c.mi
                jc['uv'] = uv
                cubes.append(jc)
            if cubes:
                jb['cubes'] = cubes
            bones.append(jb)
        vw, vh, vo = self.visible
        return {
            'format_version': '1.16.0',
            'minecraft:geometry': [{
                'description': {
                    'identifier': self.identifier,
                    'texture_width': self.tex_w,
                    'texture_height': self.tex_h,
                    'visible_bounds_width': vw,
                    'visible_bounds_height': vh,
                    'visible_bounds_offset': list(vo),
                },
                'bones': bones,
            }],
        }

    def write(self, geo_path, tex_path):
        j = self.to_json()
        with open(geo_path, 'w') as fh:
            json.dump(j, fh, indent=1)
        tex.save(self.atlas, tex_path)
        return j


def merge_geo_files(geos, path):
    """Write several Geo objects into one .geo.json file."""
    out = {'format_version': '1.16.0', 'minecraft:geometry': []}
    for g in geos:
        out['minecraft:geometry'] += g.to_json()['minecraft:geometry']
    with open(path, 'w') as fh:
        json.dump(out, fh, indent=1)
