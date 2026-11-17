"""Procedural blueprints for script-placed sea structures (exported to JS).

Blueprint format (all coordinates relative to the anchor):
    palette: [[block id, states], ...]
    blocks:  flat list [dx, dy, dz, paletteIndex, ...]
    columns: flat list [dx, dz, topDy, ...]  (island only: fill from seabed up to topDy)
    chests:  [[dx, dy, dz, lootTable], ...]
    spawns:  [[dx, dy, dz, entityId], ...]
"""
from __future__ import annotations

import json
import math
import random


class BP:
    def __init__(self):
        self.palette = []
        self.index = {}
        self.blocks = {}
        self.columns = []
        self.chests = []
        self.spawns = []

    def pal(self, name, states=None):
        key = (name, json.dumps(states or {}, sort_keys=True))
        if key not in self.index:
            self.index[key] = len(self.palette)
            self.palette.append([name, states or {}])
        return self.index[key]

    def put(self, x, y, z, name, states=None):
        self.blocks[(int(x), int(y), int(z))] = self.pal(name, states)

    def box(self, x0, y0, z0, x1, y1, z1, name, states=None, hollow=False):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    if hollow and x0 < x < x1 and y0 < y < y1 and z0 < z < z1:
                        continue
                    self.put(x, y, z, name, states)

    def export(self):
        flat = []
        for (x, y, z), p in sorted(self.blocks.items(), key=lambda kv: (kv[0][1], kv[0][0], kv[0][2])):
            flat += [x, y, z, p]
        cols = []
        for c in self.columns:
            cols += list(c)
        return {'palette': self.palette, 'blocks': flat, 'columns': cols, 'chests': self.chests, 'spawns': self.spawns}


LEAVES = ('minecraft:jungle_leaves', {'persistent_bit': True})


def _palm(b, x, z, base, height, lean):
    dx, dz = lean
    cx, cz = x, z
    for i in range(height):
        if i == height // 2:
            cx += dx
            cz += dz
        b.put(cx, base + i, cz, 'minecraft:jungle_log', {'pillar_axis': 'y'})
    top = base + height
    b.put(cx, top, cz, *LEAVES)
    for ox, oz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for k in range(1, 4):
            y = top - (1 if k == 3 else 0)
            b.put(cx + ox * k, y, cz + oz * k, *LEAVES)
    for ox, oz in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
        b.put(cx + ox, top, cz + oz, *LEAVES)
        b.put(cx + ox * 2, top - 1, cz + oz * 2, *LEAVES)


def outpost():
    """Pirate outpost island. Anchor = water surface block at the island centre."""
    b = BP()
    rx, rz = 10, 8
    for x in range(-rx - 1, rx + 2):
        for z in range(-rz - 1, rz + 2):
            d = (x / rx) ** 2 + (z / rz) ** 2
            if d > 1.0:
                continue
            top = 0 if d > 0.7 else (1 if d > 0.3 else 2)
            b.columns.append((x, z, top))
            if d < 0.22:
                b.put(x, top, z, 'minecraft:grass_block')
    # palms
    _palm(b, -6, -3, 2, 6, (-1, 0))
    _palm(b, 5, 4, 2, 7, (1, 1))
    _palm(b, -3, 5, 2, 5, (0, 1))
    # tent (red/white striped, open at the front which faces -z)
    for z in range(0, 5):
        for k, h in enumerate((0, 1, 2, 1, 0)):
            x = -2 + k
            wool = 'minecraft:red_wool' if (x + 10) % 2 == 0 else 'minecraft:white_wool'
            b.put(x, 3 + h, z, wool)
        if z == 4:
            b.box(-1, 3, 4, 1, 4, 4, 'minecraft:white_wool')
            b.put(0, 5, 4, 'minecraft:red_wool')
    b.put(1, 3, 3, 'minecraft:chest', {'minecraft:cardinal_direction': 'north'})
    b.chests.append([1, 3, 3, 'outpost'])
    b.put(-1, 3, 3, 'minecraft:barrel', {'facing_direction': 1})
    # camp
    b.put(0, 3, -3, 'minecraft:campfire', {'extinguished': False, 'minecraft:cardinal_direction': 'north'})
    for x, z in ((-2, -4), (2, -4)):
        b.put(x, 3, z, 'minecraft:spruce_log', {'pillar_axis': 'x'})
    b.put(4, 3, -2, 'minecraft:barrel', {'facing_direction': 1})
    b.put(4, 4, -2, 'minecraft:barrel', {'facing_direction': 1})
    b.put(5, 2, -2, 'minecraft:barrel', {'facing_direction': 1})
    # bounty board and lantern post
    b.put(-4, 2, -4, 'bc:bounty_board', {'minecraft:cardinal_direction': 'north'})
    b.put(3, 2, -5, 'minecraft:oak_fence')
    b.put(3, 3, -5, 'minecraft:oak_fence')
    b.put(3, 4, -5, 'minecraft:lantern', {'hanging': False})
    # dock heading out of the island toward -z
    for z in range(-8, -16, -1):
        for x in (-1, 0, 1):
            b.put(x, 1, z, 'minecraft:spruce_planks')
        if z % 3 == 0:
            for x in (-2, 2):
                for y in (-3, -2, -1, 0, 1, 2):
                    b.put(x, y, z, 'minecraft:spruce_log', {'pillar_axis': 'y'})
    b.put(2, 3, -15, 'minecraft:lantern', {'hanging': False})
    b.spawns += [[0, 3, -1, 'bc:sea_raider'], [3, 3, 1, 'bc:sea_raider'], [-4, 3, 1, 'bc:sea_raider'], [0, 3, -6, 'captain']]
    return b


def wreck():
    """Sunken ship on the sea floor. Anchor = first water block above the floor."""
    b = BP()
    random.seed(7)
    wood = 'minecraft:dark_oak_planks'
    # tilted hull: each cross-section shifted by the roll
    for z in range(-10, 11):
        taper = 0 if abs(z) < 7 else abs(z) - 6
        half = 4 - taper
        for x in range(-half, half + 1):
            # broken holes
            if random.random() < 0.12:
                continue
            b.put(x, 0, z, wood)
        for y in range(1, 5):
            for side in (-half - 1, half + 1):
                lift = 1 if side > 0 else 0
                if random.random() < 0.15:
                    continue
                b.put(side, y + lift, z, wood)
        if abs(z) < 7 and z % 2 == 0:
            for x in range(-half, half + 1):
                if random.random() < 0.3:
                    continue
                b.put(x, 4, z, 'minecraft:dark_oak_slab', {'minecraft:vertical_half': 'bottom'})
    # cabin at the stern with the treasure
    b.box(-3, 1, 6, 3, 4, 9, wood, hollow=True)
    for x in range(-2, 3):
        for y in range(2, 4):
            b.blocks.pop((x, y, 6), None)
    b.put(-1, 1, 8, 'minecraft:chest', {'minecraft:cardinal_direction': 'north'})
    b.put(1, 1, 8, 'minecraft:chest', {'minecraft:cardinal_direction': 'north'})
    b.chests += [[-1, 1, 8, 'wreck'], [1, 1, 8, 'wreck']]
    b.put(0, 3, 8, 'minecraft:sea_lantern')
    # broken mast lying across the deck
    for x in range(-9, 6):
        b.put(x, 5 + (1 if x > 2 else 0), -2 + x // 4, 'minecraft:spruce_log', {'pillar_axis': 'x'})
    b.put(0, 1, -3, 'minecraft:sea_lantern')
    for x, z in ((-2, -6), (2, 2), (-3, 3)):
        b.put(x, 1, z, 'minecraft:web')
    for x, z in ((-6, -8), (6, 5), (-5, 9), (7, -4)):
        b.put(x, 0, z, 'minecraft:gravel')
    b.spawns += [[0, 1, 0, 'minecraft:drowned'], [-2, 1, -5, 'minecraft:drowned'], [2, 1, 4, 'minecraft:drowned']]
    return b


def export_js():
    data = {'outpost': outpost().export(), 'wreck': wreck().export()}
    return ('// AUTO-GENERATED by tools/build.py (tools/bc/structures.py) - do not edit by hand.\n'
            f'export const STRUCTURES = {json.dumps(data, separators=(",", ":"))};\n')
