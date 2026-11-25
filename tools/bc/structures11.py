"""v1.1.0 landmark blueprints (exported to scripts/generated/landmarks.js).

Same format as structures.py, plus:
    found:    [dx, dz, ...]            foundation columns: filled from the anchor down to the ground, so a landmark sits on hills
    marks:    [[name, dx, dy, dz]]     named points the scripts use (the boss, the reward chest, the obelisk core...)
    spawners: [[dx, dy, dz, pool]]     Mana Spawner blocks and what they call up
    spawns are deferred: they appear when a player first comes near, not when the landmark is built.

Every blueprint is anchored at ground level (y 0 = the ground block, y 1 = the first block of air).
"""
from __future__ import annotations

import json
import math
import random

from .structures import BP

S = 'minecraft:'
LIT = {'hanging': False}
CHEST_S = {'minecraft:cardinal_direction': 'south'}
CHEST_N = {'minecraft:cardinal_direction': 'north'}
Y_AXIS = {'pillar_axis': 'y'}
X_AXIS = {'pillar_axis': 'x'}


class LBP(BP):
    def __init__(self, seed):
        super().__init__()
        self.found = []
        self.marks = []
        self.spawners = []
        self.clears = []
        self.rng = random.Random(seed)

    def export(self):
        d = super().export()
        d['found'] = [v for xz in self.found for v in xz]
        d['marks'] = self.marks
        d['spawners'] = self.spawners
        d['clears'] = [v for c in self.clears for v in c]
        return d

    def brick(self, moss=0.2, crack=0.18):
        r = self.rng.random()
        return S + ('mossy_stone_bricks' if r < moss else 'cracked_stone_bricks' if r < moss + crack else 'stone_bricks')

    def chest(self, x, y, z, table, facing=CHEST_S):
        self.put(x, y, z, S + 'chest', facing)
        self.chests.append([x, y, z, table])

    def spawner(self, x, y, z, pool):
        self.put(x, y, z, 'bc:mana_spawner')
        self.spawners.append([x, y, z, pool])

    def clear_above(self, x, z, y0=1, y1=7):
        """Air from y0 to y1 in a column (applied before the blocks, so anything placed there wins)."""
        self.clears.append((x, z, y0, y1))

    def clear_box(self, x0, x1, y0, y1, z0, z1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                self.clears.append((x, z, y0, y1))

    def pad(self, r, floor, alt=None, alt_chance=0.0, clear=6, round_=True):
        """A level pad of radius r at y 0 with air above and a foundation under it."""
        for x in range(-r, r + 1):
            for z in range(-r, r + 1):
                if round_ and x * x + z * z > r * r + r:
                    continue
                self.put(x, 0, z, alt if alt and self.rng.random() < alt_chance else floor)
                self.found.append((x, z))
                self.clear_above(x, z, 1, clear)


# ======================================================================================
# helpers
# ======================================================================================
def _ring(r):
    """The cells of a square ring of radius r, walked clockwise from the north-west corner."""
    cells = [(x, -r) for x in range(-r, r)] + [(r, z) for z in range(-r, r)] + [(x, r) for x in range(r, -r, -1)] + [(-r, z) for z in range(r, -r, -1)]
    return cells


def _spiral(b, y0, y1, r, mat, floors=()):
    """A spiral of solid steps around a square ring, rising one block per step; holes are cut in the floors above."""
    cells = _ring(r)
    for i in range(y1 - y0 + 1):
        x, z = cells[i % len(cells)]
        h = y0 + i
        b.put(x, h, z, mat)
        for hh in (h + 1, h + 2, h + 3):
            if hh in floors or (x, hh, z) in b.blocks:
                b.put(x, hh, z, S + 'air')


# ======================================================================================
# the Mage Spire
# ======================================================================================
def spire():
    """Five floors of the old kingdom's magic, a spiral stair inside, a Mana Spawner on three floors and the Spire Warden
    waiting on the roof. Anchor = the ground at the centre of the tower."""
    b = LBP(1101)
    R = 5
    floors = [0, 7, 14, 21, 28, 35]
    top = 35

    def inside(x, z):
        return max(abs(x), abs(z)) <= R and abs(x) + abs(z) <= 8

    def wall(x, z):
        return inside(x, z) and any(not inside(x + dx, z + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    for x in range(-R - 1, R + 2):
        for z in range(-R - 1, R + 2):
            if not inside(x, z):
                if max(abs(x), abs(z)) <= R + 1:
                    b.found.append((x, z))
                    b.put(x, 0, z, S + 'stone_bricks')
                    b.clear_above(x, z, 1, 4)
                continue
            b.found.append((x, z))
            for y in range(0, top + 1):
                if wall(x, z):
                    trim = y in floors or y == top
                    b.put(x, y, z, S + ('polished_deepslate' if trim else 'stone_bricks') if trim else b.brick(0.18, 0.16))
                elif y in floors:
                    b.put(x, y, z, S + ('deepslate_tiles' if (x + z) % 2 else 'polished_deepslate'))
            if not wall(x, z):
                for f in floors[:-1]:
                    b.clear_above(x, z, f + 1, f + 6)
                b.clear_above(x, z, top + 1, top + 6)
    # crenellations, a crystal spire on the roof
    for x in range(-R, R + 1):
        for z in range(-R, R + 1):
            if wall(x, z) and (x + z) % 2 == 0:
                b.put(x, top + 1, z, S + 'stone_bricks')
                b.put(x, top + 2, z, S + 'deepslate_bricks')
    # door (south), slit windows on every floor
    for y in (1, 2, 3):
        for x in (-1, 0, 1):
            b.put(x, y, R if abs(x) + R <= 8 else R - 1, S + 'air')
    b.put(-1, 4, R, S + 'chiseled_stone_bricks')
    b.put(1, 4, R, S + 'chiseled_stone_bricks')
    b.put(0, 4, R, S + 'chiseled_stone_bricks')
    for f in floors[:-1]:
        for (x, z) in ((R, 0), (-R, 0), (0, -R)):
            b.put(x, f + 3, z, S + 'air')
            b.put(x, f + 4, z, S + 'air')
    # the stair
    _spiral(b, 1, top, 3, S + 'polished_deepslate', floors=set(floors[1:]))
    # floor furniture: lanterns, bookshelves against the walls, a chest and a spawner in the middle
    pools = {7: 'arcane', 14: 'hollow', 21: 'arcane'}
    for k, f in enumerate(floors[:-1]):
        y = f + 1
        for x, z in ((-2, -2), (2, 2)):
            b.put(x, y, z, S + 'soul_lantern', LIT)
        for x, z in ((-4, -1), (-4, 1), (4, -1), (4, 1)):
            if k % 2 == 0:
                b.put(x, y, z, S + 'bookshelf')
                b.put(x, y + 1, z, S + 'bookshelf')
        if f in pools:
            b.spawner(0, y, 0, pools[f])
            b.put(0, y + 1, 0, S + 'air')
        if k >= 1:
            b.chest(-1, y, 1, f'spire_{min(k, 4)}')
        for _ in range(4):
            b.put(b.rng.randint(-2, 2), f + 6, b.rng.randint(-2, 2), S + 'web')
    b.chest(1, 1, -1, 'spire_1')
    # guards that wait on the lower floors (they appear when you come near)
    b.spawns += [[2, 1, 2, 'bc:rogue_mage'], [-2, 8, 2, 'bc:mana_wraith'], [2, 8, -2, 'bc:rogue_mage'], [-2, 15, -2, 'bc:hollow_knight'],
                 [2, 15, 2, 'bc:hollow_knight'], [2, 22, 2, 'bc:mana_wraith'], [-2, 22, -2, 'bc:rogue_mage'], [0, 22, 2, 'chance:0.5:bc:rogue_mage']]
    b.marks += [['boss', 0, top + 1, 0], ['reward', 0, top + 1, -2]]
    return b


# ======================================================================================
# Wyvern Roosts (one per wyvern, in its own stone)
# ======================================================================================
ROOST_STONE = {
    'ember': (S + 'blackstone', S + 'basalt', S + 'magma', S + 'coarse_dirt'),
    'frost': (S + 'packed_ice', S + 'snow', S + 'blue_ice', S + 'stone'),
    'storm': (S + 'tuff', S + 'andesite', S + 'calcite', S + 'gravel'),
}


def roost(kind):
    """A mound of rock with a nest of bones and gold on top. Anchor = the ground at the centre."""
    b = LBP({'ember': 1201, 'frost': 1202, 'storm': 1203}[kind])
    main, second, accent, ground = ROOST_STONE[kind]
    R = 9
    for x in range(-R - 1, R + 2):
        for z in range(-R - 1, R + 2):
            d = math.sqrt(x * x + z * z)
            if d > R + 0.6:
                continue
            b.found.append((x, z))
            h = max(0, int(round((R - d) * 0.55 + b.rng.random() * 1.2)))
            for y in range(0, h + 1):
                r = b.rng.random()
                b.put(x, y, z, accent if r < 0.07 else second if r < 0.35 else main)
            b.clear_above(x, z, h + 1, h + 8)
    # the nest: a bowl lined with bones and gold
    for x in range(-4, 5):
        for z in range(-4, 5):
            d = math.sqrt(x * x + z * z)
            if d > 4.4:
                continue
            top = 4 if d < 3.2 else 5
            b.clear_above(x, z, top + 1, top + 3)
            r = b.rng.random()
            b.put(x, top, z, S + ('gold_block' if r < 0.12 else 'raw_gold_block' if r < 0.2 else 'bone_block' if d > 3.2 else ground), Y_AXIS if d > 3.2 and r >= 0.2 else None)
    for k in range(10):
        a = k / 10 * math.tau
        x, z = round(math.cos(a) * 4.6), round(math.sin(a) * 4.6)
        b.put(x, 6, z, S + 'bone_block', Y_AXIS)
        if k % 3 == 0:
            b.put(x, 7, z, S + 'bone_block', Y_AXIS)
    b.chest(-2, 5, -2, 'hoard')
    b.chest(2, 5, 2, 'hoard')
    b.marks += [['boss', 0, 5, 0]]
    return b


# ======================================================================================
# the Ancient Catacombs: an entrance, room templates and a stairwell; the scripts lay them out at random
# ======================================================================================
CATA_DEPTH = 15          # rooms' floor this far below the ground
CATA_CELL = 16           # room centres this far apart (11-wide rooms and 5-long halls)


def cata_entrance():
    """A small mausoleum over a spiral stair down to the first room. Anchor = the ground above the first room's centre."""
    b = LBP(1301)
    for x in range(-3, 4):
        for z in range(-3, 4):
            b.found.append((x, z))
            b.put(x, 0, z, S + 'polished_deepslate')
            for y in range(1, 6):
                edge = abs(x) == 3 or abs(z) == 3
                if edge and not (z == 3 and abs(x) <= 1 and y <= 3):
                    b.put(x, y, z, S + ('chiseled_deepslate' if abs(x) == 3 and abs(z) == 3 else 'deepslate_bricks'))
                else:
                    b.put(x, y, z, S + 'air')
            b.put(x, 6, z, S + 'deepslate_tiles')
    b.put(0, 7, 0, S + 'soul_lantern', LIT)
    # the shaft: a 5x5 hole down to the room's ceiling with a spiral around a pillar
    for y in range(-CATA_DEPTH + 6, 1):
        for x in range(-2, 3):
            for z in range(-2, 3):
                edge = abs(x) == 2 or abs(z) == 2
                b.put(x, y, z, b.brick(0.25, 0.2) if edge and y < 0 else S + 'polished_deepslate' if edge else S + 'air')
        b.put(0, y, 0, S + 'chiseled_stone_bricks' if y % 4 == 0 else S + 'stone_bricks')
    _spiral(b, -CATA_DEPTH + 1, 0, 1, S + 'polished_deepslate')
    b.put(0, 1, 0, S + 'air')
    return b


def _room_shell(b, R=5, H=6, base=0):
    """Walls, floor and ceiling of an 11x11 room with a doorway in the middle of each wall."""
    b.clear_box(-R + 1, R - 1, base + 1, base + H - 1, -R + 1, R - 1)
    for x in range(-R, R + 1):
        for z in range(-R, R + 1):
            for y in range(base, base + H + 1):
                edge = abs(x) == R or abs(z) == R or y in (base, base + H)
                door = (abs(x) == R and abs(z) <= 1 or abs(z) == R and abs(x) <= 1) and base < y <= base + 3
                if not edge:
                    continue
                b.put(x, y, z, S + 'air' if door else (S + 'polished_deepslate' if y == base and (x + z) % 2 else b.brick(0.25, 0.2)))
    for x, z in ((-R + 1, -R + 1), (R - 1, -R + 1), (-R + 1, R - 1), (R - 1, R - 1)):
        for y in range(base + 1, base + H):
            b.put(x, y, z, S + 'chiseled_stone_bricks' if y in (base + 1, base + H - 1) else S + 'stone_bricks')
    b.put(0, base + H, 0, S + 'sea_lantern')


def cata_room(kind):
    """A catacomb room. Anchor = the centre of the room's floor (y 0 = floor)."""
    b = LBP(1400 + ['crypt', 'library', 'treasure', 'spawner', 'trap', 'prison', 'shrine'].index(kind))
    _room_shell(b)
    if kind == 'crypt':
        for x in (-3, 3):
            for z in (-2, 2):
                b.put(x, 1, z, S + 'polished_deepslate')
                b.put(x, 1, z + (1 if z < 0 else -1), S + 'polished_deepslate')
        b.spawner(0, 1, 0, 'hollow')
        b.spawns += [[2, 1, 0, 'bc:hollow_knight']]
        b.chest(0, 1, -3, 'cata_room')
    elif kind == 'library':
        for x in range(-4, 5):
            for z in (-4, 4):
                if abs(x) > 1:
                    for y in (1, 2, 3):
                        b.put(x, y, z, S + 'bookshelf')
        b.put(0, 1, 0, S + 'crafting_table')
        b.chest(-3, 1, 0, 'library', CHEST_N)
        b.spawns += [[2, 1, 2, 'bc:rogue_mage']]
        for _ in range(5):
            b.put(b.rng.randint(-4, 4), 5, b.rng.randint(-4, 4), S + 'web')
    elif kind == 'treasure':
        b.chest(-2, 1, -3, 'cata_treasure')
        b.chest(2, 1, -3, 'cata_treasure')
        for x, z in ((0, -4), (-1, -4), (1, -4)):
            b.put(x, 1, z, S + 'gold_block')
        for x in (-3, 3):
            b.put(x, 1, 2, S + 'soul_lantern', LIT)
        b.spawns += [[0, 1, 1, 'bc:mana_wraith'], [1, 1, -1, 'chance:0.5:bc:mana_wraith']]
    elif kind == 'spawner':
        b.spawner(0, 1, 0, 'arcane')
        b.chest(3, 1, -3, 'cata_room')
        for x, z in ((-2, -2), (2, 2), (-2, 2), (2, -2)):
            b.put(x, 1, z, S + 'cracked_stone_bricks')
    elif kind == 'trap':
        for x, z in ((0, -2), (0, 2), (-2, 0), (2, 0)):
            b.traps.append([x, 1, z])
            b.put(x, 0, z, S + 'chiseled_stone_bricks')
        b.chest(0, 1, 0, 'cata_treasure')
    elif kind == 'prison':
        for cx in (-3, 3):
            for z in range(-4, 5):
                for y in (1, 2, 3):
                    if abs(z) != 0 or y == 3:
                        b.put(cx, y, z, S + 'iron_bars')
        b.marks += [['captive', -4, 1, 2]]
        b.spawns += [[4, 1, -2, 'bc:bandit'], [4, 1, 2, 'bc:bandit_archer']]
        b.chest(4, 1, 0, 'cata_room')
    elif kind == 'shrine':
        b.put(0, 1, -3, S + 'polished_deepslate')
        b.put(0, 2, -3, 'bc:obelisk_core')
        b.put(0, 3, -3, S + 'chiseled_deepslate')
        for x in (-2, 2):
            b.put(x, 1, -3, S + 'soul_lantern', LIT)
        b.marks += [['core', 0, 2, -3]]
    return b


def cata_boss():
    """The guardian's hall: a bigger room with pillars, the guardian and its hoard. Anchor = floor centre."""
    b = LBP(1450)
    _room_shell(b, R=7, H=8)
    for x, z in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        for y in range(1, 8):
            b.put(x, y, z, S + 'chiseled_stone_bricks' if y in (1, 7) else S + 'polished_deepslate')
    b.put(0, 1, -6, 'bc:grimoire_altar', {'minecraft:cardinal_direction': 'south'})
    b.chest(-2, 1, -6, 'cata_boss')
    b.chest(2, 1, -6, 'cata_boss')
    for x, z in ((-6, 0), (6, 0)):
        b.put(x, 1, z, S + 'soul_lantern', LIT)
    b.marks += [['boss', 0, 1, 0]]
    b.spawns += [[-5, 1, 5, 'bc:imp'], [5, 1, 5, 'bc:imp']]
    return b


# ======================================================================================
# a ruined hamlet's parts (the scripts arrange four to six of them around a well)
# ======================================================================================
def _house(b, w, d, h, wall_mat, roof_mat, ruin, door_side='south'):
    rx, rz = w // 2, d // 2
    for x in range(-rx, rx + 1):
        for z in range(-rz, rz + 1):
            b.found.append((x, z))
            b.put(x, 0, z, S + ('oak_planks' if b.rng.random() > 0.15 else 'coarse_dirt'))
            for y in range(1, h + 2):
                b.put(x, y, z, S + 'air')
            edge = abs(x) == rx or abs(z) == rz
            if not edge:
                continue
            hh = h if b.rng.random() > ruin else b.rng.randint(0, h - 1)
            for y in range(1, hh + 1):
                corner = abs(x) == rx and abs(z) == rz
                b.put(x, y, z, S + ('oak_log' if corner else wall_mat), Y_AXIS if corner else None)
    for x in range(-rx, rx + 1):
        for z in range(-rz, rz + 1):
            if b.rng.random() > ruin * 1.3:
                b.put(x, h + 1, z, S + roof_mat)
    for y in (1, 2):
        b.put(0, y, rz if door_side == 'south' else -rz, S + 'air')
    b.put(-rx, 2, 0, S + 'air')
    b.put(rx, 2, 0, S + 'air')


def hamlet_part(kind):
    """Anchor = the ground at the part's centre."""
    b = LBP(1500 + ['cottage', 'longhouse', 'well', 'chapel', 'farm', 'graves'].index(kind))
    if kind == 'cottage':
        _house(b, 7, 7, 3, 'cobblestone', 'spruce_planks', 0.25)
        b.chest(-2, 1, -2, 'hamlet')
        b.put(2, 1, -2, S + 'crafting_table')
        b.put(2, 1, 1, S + 'barrel', {'facing_direction': 1})
    elif kind == 'longhouse':
        _house(b, 11, 7, 4, 'oak_planks', 'dark_oak_planks', 0.35)
        b.chest(-4, 1, -2, 'hamlet')
        b.put(4, 1, -2, S + 'barrel', {'facing_direction': 1})
        b.put(3, 1, -2, S + 'barrel', {'facing_direction': 1})
        b.put(0, 1, -2, S + 'campfire', {'extinguished': True, 'minecraft:cardinal_direction': 'north'})
        b.marks += [['bed', 3, 1, 1]]
    elif kind == 'well':
        for x in range(-2, 3):
            for z in range(-2, 3):
                b.found.append((x, z))
                b.put(x, 0, z, S + 'cobblestone')
                b.clear_above(x, z, 1, 5)
        for x in range(-1, 2):
            for z in range(-1, 2):
                if x or z:
                    b.put(x, 1, z, S + 'mossy_cobblestone')
                else:
                    for y in range(-3, 1):
                        b.put(0, y, 0, S + 'water')
        for x, z in ((-1, -1), (1, 1)):
            b.put(x, 2, z, S + 'oak_fence')
            b.put(x, 3, z, S + 'oak_fence')
        for x in (-1, 0, 1):
            for z in (-1, 0, 1):
                b.put(x, 4, z, S + 'spruce_planks')
    elif kind == 'chapel':
        _house(b, 7, 11, 5, 'stone_bricks', 'deepslate_tiles', 0.3, door_side='south')
        b.put(0, 1, -4, S + 'polished_deepslate')
        b.put(0, 2, -4, S + 'soul_lantern', LIT)
        b.chest(-2, 1, -4, 'crypt')
        for z in (-1, 1, 3):
            for x in (-2, 2):
                b.put(x, 1, z, S + 'spruce_planks')
    elif kind == 'farm':
        for x in range(-4, 5):
            for z in range(-3, 4):
                b.found.append((x, z))
                b.clear_above(x, z, 1, 3)
                edge = abs(x) == 4 or abs(z) == 3
                b.put(x, 0, z, S + ('grass_block' if edge else 'farmland' if b.rng.random() < 0.7 else 'coarse_dirt'))
                if edge:
                    b.put(x, 1, z, S + 'oak_fence')
                elif b.rng.random() < 0.3:
                    b.put(x, 1, z, S + 'deadbush')
        b.put(0, 1, 3, S + 'air')
        b.put(3, 1, -2, S + 'composter')
        b.put(-3, 1, -2, S + 'hay_block', Y_AXIS)
    elif kind == 'graves':
        for x in range(-3, 4):
            for z in range(-3, 4):
                b.found.append((x, z))
                b.put(x, 0, z, S + ('podzol' if b.rng.random() < 0.5 else 'coarse_dirt'))
                b.clear_above(x, z, 1, 3)
        for x, z in ((-2, -2), (0, -2), (2, -2), (-2, 1), (1, 1)):
            b.put(x, 1, z, S + 'mossy_cobblestone')
            b.put(x, 2, z, S + 'stone_bricks' if b.rng.random() < 0.5 else S + 'cobblestone')
        b.marks += [['grave', 0, 1, 0]]
    return b


# ======================================================================================
# the rest of the landmarks
# ======================================================================================
def graveyard():
    """An old graveyard: a low wall, rows of tombstones, dead bushes and a crypt with a Mana Spawner below."""
    b = LBP(1601)
    for x in range(-8, 9):
        for z in range(-7, 8):
            b.found.append((x, z))
            b.put(x, 0, z, S + ('podzol' if b.rng.random() < 0.4 else 'coarse_dirt' if b.rng.random() < 0.5 else 'grass_block'))
            b.clear_above(x, z, 1, 7)
            if abs(x) == 8 or abs(z) == 7:
                if not (z == 7 and abs(x) <= 1):
                    b.put(x, 1, z, S + ('mossy_cobblestone' if b.rng.random() < 0.5 else 'cobblestone'))
                    if (x + z) % 3 == 0:
                        b.put(x, 2, z, S + 'iron_bars')
    for x in range(-6, 7, 3):
        for z in (-4, -1, 2, 5):
            if abs(x) <= 1 and z <= -1:
                continue
            if b.rng.random() < 0.8:
                b.put(x, 1, z, S + 'mossy_stone_bricks' if b.rng.random() < 0.5 else S + 'stone_bricks')
                if b.rng.random() < 0.6:
                    b.put(x, 2, z, S + 'cracked_stone_bricks')
            elif b.rng.random() < 0.6:
                b.put(x, 1, z, S + 'deadbush')
    # the crypt: a mausoleum with a stair down to a little vault
    for x in range(-2, 3):
        for z in range(-5, 0):
            for y in range(1, 5):
                edge = abs(x) == 2 or z in (-5, -1)
                door = z == -1 and x == 0 and y <= 2
                b.put(x, y, z, S + ('deepslate_bricks' if edge and not door else 'air'))
            b.put(x, 5, z, S + 'deepslate_tiles')
    b.put(0, 6, -3, S + 'soul_lantern', LIT)
    b.clear_box(-2, 2, -5, -3, -12, -7)
    for x in range(-3, 4):
        for z in range(-13, -5):
            for y in range(-6, -1):
                edge = abs(x) == 3 or z in (-13, -6) or y in (-6, -2)
                if edge:
                    b.put(x, y, z, b.brick(0.3, 0.2))
    for i in range(1, 6):
        b.put(0, -i, -2 - i, S + 'polished_deepslate')
        for k in (1, 2, 3):
            b.put(0, -i + k, -2 - i, S + 'air')
    b.spawner(0, -5, -11, 'hollow')
    b.chest(-2, -5, -12, 'crypt')
    b.chest(2, -5, -12, 'crypt')
    b.marks += [['grave', -3, 1, 3], ['grave', 3, 1, 3], ['grave', -6, 1, -4], ['grave', 6, 1, 2]]
    return b


def obelisk():
    """A Mana Obelisk: a black needle of stone with a rune core that answers prayers."""
    b = LBP(1602)
    b.pad(4, S + 'polished_deepslate', S + 'deepslate_tiles', 0.3, clear=12)
    for x in range(-1, 2):
        for z in range(-1, 2):
            b.put(x, 1, z, S + 'deepslate_bricks')
    for y in range(2, 11):
        b.put(0, y, 0, S + ('chiseled_deepslate' if y in (5, 10) else 'deepslate_bricks'))
    b.put(0, 11, 0, S + 'sea_lantern')
    b.put(0, 2, 1, 'bc:obelisk_core')
    for x, z in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        b.put(x, 1, z, S + 'soul_lantern', LIT)
    b.marks += [['core', 0, 2, 1]]
    return b


def fairy_ring():
    """A ring of mushrooms around a glowing heart, flowers inside, sprites at play."""
    b = LBP(1603)
    b.pad(7, S + 'moss_block', S + 'grass_block', 0.4, clear=4)
    for k in range(18):
        a = k / 18 * math.tau
        x, z = round(math.cos(a) * 5), round(math.sin(a) * 5)
        b.put(x, 1, z, S + ('red_mushroom' if k % 2 else 'brown_mushroom'))
    for _ in range(14):
        x, z = b.rng.randint(-3, 3), b.rng.randint(-3, 3)
        if x or z:
            b.put(x, 1, z, S + b.rng.choice(['azure_bluet', 'oxeye_daisy', 'allium', 'cornflower', 'lily_of_the_valley', 'dandelion']))
    b.put(0, 0, 0, S + 'shroomlight')
    b.spawns += [[2, 2, 0, 'bc:mana_sprite'], [-2, 2, 1, 'bc:mana_sprite'], [0, 2, -2, 'bc:mana_sprite']]
    b.marks += [['heart', 0, 1, 0]]
    return b


def watchtower():
    """A broken Magic Knight watchtower: a stone shaft, steps round the outside, a Mana Spawner at its foot."""
    b = LBP(1604)
    b.pad(5, S + 'cobblestone', S + 'gravel', 0.35, clear=14)
    for x in range(-2, 3):
        for z in range(-2, 3):
            for y in range(1, 13):
                edge = abs(x) == 2 or abs(z) == 2
                if edge:
                    if y > 9 and b.rng.random() < 0.3:
                        continue
                    b.put(x, y, z, b.brick(0.3, 0.25))
                else:
                    b.put(x, y, z, S + 'air')
            b.put(x, 12, z, S + 'spruce_planks')
    for x in (-2, 0, 2):
        for z in (-2, 2):
            b.put(x, 13, z, S + 'stone_bricks')
    for y in (1, 2):
        b.put(0, y, 2, S + 'air')
    # outside steps climbing the walls
    cells = _ring(3)
    for i in range(12):
        x, z = cells[(i + 14) % len(cells)]
        b.put(x, i + 1, z, S + 'polished_andesite')
    b.spawner(0, 1, 0, 'bandit')
    b.chest(1, 13, 1, 'watchtower')
    b.put(-1, 13, -1, S + 'lantern', LIT)
    b.spawns += [[1, 13, -1, 'bc:bandit_archer'], [3, 1, 4, 'bc:bandit'], [-3, 1, 4, 'bc:bandit']]
    return b


def caravan():
    """A wrecked caravan: a broken cart, scattered cargo, a cold campfire."""
    b = LBP(1605)
    b.pad(6, S + 'grass_path', S + 'coarse_dirt', 0.5, clear=4, round_=False)
    for x in range(-2, 3):
        for z in range(-1, 2):
            b.put(x, 2, z, S + 'spruce_planks' if not (x == 2 and z == 1) else S + 'air')
    for x in (-2, 2):
        for z in (-2, 2):
            b.put(x, 1, z, S + 'dark_oak_log', X_AXIS)
    b.put(3, 1, 0, S + 'oak_fence')
    b.chest(0, 3, 0, 'caravan')
    for x, z in ((-4, 3), (4, -3), (-3, -4), (5, 2)):
        b.put(x, 1, z, S + ('barrel' if b.rng.random() < 0.5 else 'hay_block'), {'facing_direction': 1} if b.rng.random() < 0.5 else Y_AXIS)
    b.put(-4, 1, -1, S + 'campfire', {'extinguished': True, 'minecraft:cardinal_direction': 'north'})
    for x, z in ((5, 4), (6, 4), (5, 5)):
        b.put(x, 1, z, S + 'bone_block', X_AXIS)
    b.marks += [['ambush', 0, 1, 6]]
    return b


def crater(small=False):
    """A star crater: a scorched bowl with crystal and a fallen star at its heart."""
    b = LBP(1606 if not small else 1607)
    R = 7 if not small else 4
    for x in range(-R - 1, R + 2):
        for z in range(-R - 1, R + 2):
            d = math.sqrt(x * x + z * z)
            if d > R + 0.8:
                continue
            b.found.append((x, z))
            depth = max(0, int(round((R - d) * 0.45)))
            b.clear_above(x, z, -depth + 1, 5)
            r = b.rng.random()
            b.put(x, -depth, z, S + ('magma' if r < 0.12 else 'blackstone' if r < 0.5 else 'obsidian' if r < 0.6 else 'coarse_dirt'))
    cy = -int(round(R * 0.45))
    b.put(0, cy, 0, S + 'amethyst_block')
    b.put(1, cy + 1, 0, S + 'amethyst_block')
    b.put(-1, cy + 1, 1, S + 'budding_amethyst')
    b.put(0, cy + 1, -1, S + 'crying_obsidian')
    b.chest(0, cy + 1, 1, 'crater' if not small else 'starfall')
    if not small:
        b.spawns += [[2, cy + 1, 2, 'bc:mana_wraith'], [-2, cy + 1, -2, 'chance:0.5:bc:mana_wraith']]
    b.marks += [['star', 0, cy + 2, 0]]
    return b


def skeleton():
    """The bones of something enormous: a spine, ribs and a skull with a treasure inside."""
    b = LBP(1608)
    b.pad(3, S + 'coarse_dirt', S + 'gravel', 0.4, clear=3, round_=False)
    for z in range(-10, 13):
        y = 2 + int(round(math.sin((z + 10) / 22 * math.pi) * 3))
        b.put(0, y, z, S + 'bone_block', {'pillar_axis': 'z'})
        if z % 3 == 0 and -8 <= z <= 8:
            for k in range(0, 8):
                a = k / 7 * math.pi * 0.85
                for sx in (-1, 1):
                    x = sx * round(math.sin(a) * 5)
                    yy = y - round((1 - math.cos(a)) * 3.2)
                    if yy >= 1:
                        b.put(x, yy, z, S + 'bone_block', Y_AXIS)
    for x in range(-3, 4):
        for z in range(-17, -11):
            for y in range(1, 6):
                edge = abs(x) == 3 or z in (-17, -12) or y in (1, 5)
                eye = z == -17 and y == 3 and abs(x) == 2
                b.put(x, y, z, S + ('air' if (not edge or eye) else 'bone_block'), Y_AXIS if edge and not eye else None)
            b.found.append((x, z))
            b.put(x, 0, z, S + 'coarse_dirt')
    b.put(0, 2, -12, S + 'air')
    b.put(0, 3, -12, S + 'air')
    b.chest(0, 2, -15, 'bones')
    for k in range(4):
        b.put(-3 + k * 2, 1, -18, S + 'bone_block', Y_AXIS)
    return b


def battlefield():
    """A forgotten battlefield: torn banners, broken carts, craters, the dead of two armies - and their loot."""
    b = LBP(1609)
    for x in range(-12, 13):
        for z in range(-12, 13):
            if x * x + z * z > 150:
                continue
            r = b.rng.random()
            if r < 0.35:
                b.put(x, 0, z, S + ('coarse_dirt' if r < 0.2 else 'gravel'))
    for k in range(7):
        x, z = b.rng.randint(-10, 10), b.rng.randint(-10, 10)
        wool = S + ('red_wool' if k % 2 else 'blue_wool')
        b.put(x, 1, z, S + 'spruce_fence')
        b.put(x, 2, z, S + 'spruce_fence')
        b.put(x, 3, z, S + 'spruce_fence')
        b.put(x + 1, 3, z, wool)
        b.put(x + 1, 2, z, wool)
    for k in range(10):
        x, z = b.rng.randint(-11, 11), b.rng.randint(-11, 11)
        b.put(x, 1, z, S + 'bone_block', X_AXIS if k % 2 else {'pillar_axis': 'z'})
    for k in range(4):
        x, z = b.rng.randint(-9, 9), b.rng.randint(-9, 9)
        b.put(x, 0, z, S + 'air')
        b.put(x, -1, z, S + 'coarse_dirt')
    b.chest(0, 1, 0, 'battlefield')
    b.put(-1, 1, 0, S + 'spruce_planks')
    b.put(1, 1, 0, S + 'barrel', {'facing_direction': 1})
    b.marks += [['grave', -6, 1, 4], ['grave', 5, 1, -5], ['grave', 7, 1, 6], ['grave', -5, 1, -7]]
    return b


def lost_waygate():
    """A ruined arch of the old kingdom around a Mana Waygate that still hums."""
    b = LBP(1610)
    b.pad(4, S + 'stone_bricks', S + 'mossy_stone_bricks', 0.4, clear=8)
    for y in range(1, 7):
        for x in (-3, 3):
            if y < 6 or b.rng.random() < 0.6:
                b.put(x, y, 0, b.brick(0.35, 0.3))
    for x in range(-3, 4):
        if b.rng.random() < 0.7:
            b.put(x, 7, 0, S + 'chiseled_stone_bricks' if x == 0 else b.brick(0.35, 0.3))
    for x, z in ((-2, -3), (3, 2), (-3, 3)):
        b.put(x, 1, z, S + 'cracked_stone_bricks')
    b.put(0, 1, 0, 'bc:waygate')
    b.marks += [['gate', 0, 1, 0]]
    return b


def witch_hut():
    """A hedge witch's stilt hut: a cauldron, a brewing stand, jars and a chest of odd things."""
    b = LBP(1611)
    b.pad(5, S + 'coarse_dirt', S + 'podzol', 0.5, clear=10)
    for x in (-3, 3):
        for z in (-3, 3):
            for y in range(1, 4):
                b.put(x, y, z, S + 'spruce_log', Y_AXIS)
    for x in range(-3, 4):
        for z in range(-3, 4):
            b.put(x, 4, z, S + 'spruce_planks')
            for y in range(5, 8):
                edge = abs(x) == 3 or abs(z) == 3
                door = z == 3 and x == 0 and y <= 6
                window = abs(x) == 3 and z == 0 and y == 6
                b.put(x, y, z, S + ('spruce_planks' if edge and not (door or window) else 'air'))
            b.put(x, 8, z, S + 'dark_oak_planks')
    for x in range(-2, 3):
        b.put(x, 9, 0, S + 'dark_oak_planks')
    for i in range(4):
        b.put(0, i + 1, 4 + (3 - i), S + 'spruce_planks')
    b.put(-2, 5, -2, S + 'cauldron')
    b.put(2, 5, -2, S + 'brewing_stand')
    b.put(2, 5, 1, S + 'flower_pot')
    b.chest(-2, 5, 1, 'witch')
    b.put(0, 7, -2, S + 'lantern', LIT)
    b.marks += [['witch', 0, 5, 0]]
    return b


# ======================================================================================
BLUEPRINTS = {
    'spire': spire, 'roost_ember': lambda: roost('ember'), 'roost_frost': lambda: roost('frost'), 'roost_storm': lambda: roost('storm'),
    'cata_entrance': cata_entrance, 'cata_boss': cata_boss,
    **{f'cata_{k}': (lambda k=k: cata_room(k)) for k in ('crypt', 'library', 'treasure', 'spawner', 'trap', 'prison', 'shrine')},
    **{f'hamlet_{k}': (lambda k=k: hamlet_part(k)) for k in ('cottage', 'longhouse', 'well', 'chapel', 'farm', 'graves')},
    'graveyard': graveyard, 'obelisk': obelisk, 'fairy_ring': fairy_ring, 'watchtower': watchtower, 'caravan': caravan,
    'crater': crater, 'starfall': lambda: crater(small=True), 'skeleton': skeleton, 'battlefield': battlefield,
    'lost_waygate': lost_waygate, 'witch_hut': witch_hut,
}


def export_js():
    from .structures12 import BLUEPRINTS as V12   # v1.2.0: the Royal Capital and the kingdoms' forts
    from .structures13 import BLUEPRINTS as V13   # v1.3.0: the Underworld Breach
    data = {k: fn().export() for k, fn in {**BLUEPRINTS, **V12, **V13}.items()}
    return ('// AUTO-GENERATED by tools/build.py (tools/bc/structures11.py) - do not edit by hand.\n'
            f'export const LANDMARK_BP = {json.dumps(data, separators=(",", ":"))};\n'
            f'export const CATA = {json.dumps(dict(depth=CATA_DEPTH, cell=CATA_CELL))};\n')
