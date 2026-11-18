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
        self.traps = []

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
        return {'palette': self.palette, 'blocks': flat, 'columns': cols, 'chests': self.chests, 'spawns': self.spawns, 'traps': self.traps}


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


def dungeon():
    """Ancient magic dungeon. Anchor = the surface block above the entrance."""
    b = BP()
    random.seed(11)

    def brick():
        r = random.random()
        return 'minecraft:mossy_stone_bricks' if r < 0.22 else ('minecraft:cracked_stone_bricks' if r < 0.38 else 'minecraft:stone_bricks')

    def shell(x0, x1, y0, y1, z0, z1):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    if x in (x0, x1) or y in (y0, y1) or z in (z0, z1):
                        b.put(x, y, z, brick())

    def carve(x0, x1, y0, y1, z0, z1):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    b.put(x, y, z, 'minecraft:air')

    floor = -13
    # ---------------- shells
    for i in range(13):                                    # stairway down along +z
        z = i - 1
        top = -i + 4
        for x in range(-2, 3):
            b.put(x, -i - 1, z, brick())
            if top <= 0:
                b.put(x, top, z, brick())
        for y in range(-i - 1, min(top, 1)):
            b.put(-2, y, z, brick())
            b.put(2, y, z, brick())
    shell(-3, 3, floor, floor + 5, 12, 31)                   # trap corridor
    shell(-8, 8, floor, floor + 7, 31, 46)                   # guardian hall
    shell(8, 15, floor, floor + 5, 35, 43)                   # treasure vault
    # ---------------- carve interiors
    for i in range(13):
        carve(-1, 1, -i, -i + 3, i - 1, i - 1)
    carve(-2, 2, floor + 1, floor + 4, 12, 31)
    carve(-7, 7, floor + 1, floor + 6, 32, 45)
    carve(9, 14, floor + 1, floor + 4, 36, 42)
    carve(8, 8, floor + 1, floor + 3, 38, 39)                # vault doorway
    carve(-1, 1, floor + 1, floor + 4, 31, 31)               # hall doorway
    # ---------------- details
    for x, z in ((-4, 35), (4, 35), (-4, 41), (4, 41)):
        for y in range(floor + 1, floor + 7):
            b.put(x, y, z, 'minecraft:chiseled_stone_bricks' if y in (floor + 1, floor + 6) else 'minecraft:stone_bricks')
    for x, z in ((-5, 38), (5, 38), (0, 34), (0, 43)):
        b.put(x, floor + 7, z, 'minecraft:sea_lantern')
    for z in (15, 20, 25, 30):
        b.put(0, floor + 5, z, 'minecraft:sea_lantern')
    for z in (14, 19, 24, 29):
        for x in (-2, 2):
            if random.random() < 0.5:
                b.put(x, floor + 4, z, 'minecraft:web')
    b.put(0, floor + 1, 44, 'bc:grimoire_altar', {'minecraft:cardinal_direction': 'north'})
    for x in (-3, 3):
        b.put(x, floor + 1, 45, 'minecraft:chest', {'minecraft:cardinal_direction': 'north'})
        b.chests.append([x, floor + 1, 45, 'dungeon'])
    for z in (37, 41):
        b.put(14, floor + 1, z, 'minecraft:chest', {'minecraft:cardinal_direction': 'west'})
        b.chests.append([14, floor + 1, z, 'dungeon'])
    b.put(11, floor + 1, 39, 'minecraft:gold_block')
    for x, z in ((-6, 33), (6, 33), (-6, 44), (6, 44), (9, 36), (13, 42)):
        b.put(x, floor + 1, z, 'minecraft:soul_lantern', {'hanging': False})
    # ruined entrance above ground
    for x in range(-3, 4):
        for z in range(-3, 4):
            if x in (-3, 3) or z in (-3, 3):
                h = random.randint(1, 4)
                for y in range(1, h + 1):
                    if not (z == -3 and abs(x) <= 1):
                        b.put(x, y, z, brick())
    for y in (1, 2, 3, 4):
        b.put(-2, y, -3, 'minecraft:chiseled_stone_bricks')
        b.put(2, y, -3, 'minecraft:chiseled_stone_bricks')
    for x in (-2, -1, 0, 1, 2):
        b.put(x, 5, -3, 'minecraft:stone_brick_slab', {'minecraft:vertical_half': 'bottom'})
    carve(-1, 1, 1, 3, -2, 2)
    # traps (flame jets) and residents
    b.traps += [[0, floor + 1, 16], [0, floor + 1, 21], [0, floor + 1, 26]]
    b.spawns += [[0, floor + 1, 18, 'minecraft:skeleton'], [1, floor + 1, 24, 'minecraft:skeleton'],
                 [0, floor + 1, 38, 'bc:dungeon_golem'], [-5, floor + 4, 40, 'bc:imp'], [5, floor + 4, 40, 'bc:imp']]
    return b


def knight_camp():
    """A Magic Knight field camp. Anchor = the ground block at the camp's centre (y 0 = ground level)."""
    b = BP()
    random.seed(23)
    # clear the air above and lay a trodden floor
    for x in range(-8, 9):
        for z in range(-8, 9):
            if x * x + z * z > 72:
                continue
            for y in range(1, 6):
                b.put(x, y, z, 'minecraft:air')
            if random.random() < 0.45:
                b.put(x, 0, z, 'minecraft:coarse_dirt')
            else:
                b.put(x, 0, z, 'minecraft:grass_block')

    def tent(cx, cz, wool, facing):
        # an A-frame tent 3 wide and 4 deep, open at the front (facing = +1 opens toward +z, -1 toward -z)
        for dz in range(4):
            z = cz + dz * facing
            for dx in (-1, 1):
                b.put(cx + dx, 1, z, wool)
            b.put(cx, 2, z, wool)
            if dz == 3:
                b.put(cx, 1, z, wool)
        b.put(cx, 3, cz, 'minecraft:oak_fence')
        b.put(cx, 1, cz + facing * 1, 'minecraft:white_carpet')
    tent(-5, -6, 'minecraft:green_wool', 1)
    tent(5, -6, 'minecraft:white_wool', 1)
    tent(0, 7, 'minecraft:green_wool', -1)
    # campfire and log benches
    b.put(0, 1, 0, 'minecraft:campfire', {'extinguished': False, 'minecraft:cardinal_direction': 'north'})
    for x, z, axis in ((-2, 0, 'z'), (2, 0, 'z'), (0, -2, 'x')):
        b.put(x, 1, z, 'minecraft:oak_log', {'pillar_axis': axis})
    # mission board, supplies, a lantern post
    b.put(3, 1, -2, 'bc:mission_board', {'minecraft:cardinal_direction': 'west'})
    b.put(-3, 1, 3, 'minecraft:chest', {'minecraft:cardinal_direction': 'east'})
    b.chests.append([-3, 1, 3, 'camp'])
    b.put(-4, 1, 3, 'minecraft:crafting_table')
    for x, z in ((6, 2), (6, 3), (-6, 1)):
        b.put(x, 1, z, 'minecraft:hay_block')
    b.put(6, 2, 2, 'minecraft:hay_block')
    for y in (1, 2):
        b.put(-6, y, -2, 'minecraft:oak_fence')
    b.put(-6, 3, -2, 'minecraft:lantern', {'hanging': False})
    b.spawns += [[1, 1, 2, 'bc:magic_knight'], [-2, 1, -2, 'bc:magic_knight'], [3, 1, 1, 'bc:magic_knight'], [4, 1, 4, 'minecraft:armor_stand']]
    return b


def _clearing(b, r, floor, alt=None, alt_chance=0.0, seed=0):
    random.seed(seed)
    for x in range(-r, r + 1):
        for z in range(-r, r + 1):
            if x * x + z * z > r * r:
                continue
            for y in range(1, 7):
                b.put(x, y, z, 'minecraft:air')
            b.put(x, 0, z, alt if alt and random.random() < alt_chance else floor)


def bandit_hideout():
    """A bandit hideout: a palisade, two shacks, a watchtower, a campfire and their loot. Anchor = ground at the centre."""
    b = BP()
    _clearing(b, 9, 'minecraft:coarse_dirt', 'minecraft:gravel', 0.25, seed=41)
    # the palisade, with a gap to the south
    for k in range(48):
        a = k / 48 * math.tau
        x, z = round(math.cos(a) * 9), round(math.sin(a) * 9)
        if z > 6 and abs(x) <= 2:
            continue
        for y in (1, 2):
            b.put(x, y, z, 'minecraft:spruce_fence' if y == 2 else 'minecraft:spruce_log')
    # two shacks open to the centre
    for cx, cz in ((-5, -3), (4, -4)):
        b.box(cx - 2, 1, cz - 2, cx + 2, 3, cz + 1, 'minecraft:spruce_planks', hollow=True)
        for x in range(cx - 1, cx + 2):
            for y in (1, 2):
                b.put(x, y, cz + 1, 'minecraft:air')
        b.box(cx - 2, 4, cz - 2, cx + 2, 4, cz + 1, 'minecraft:dark_oak_planks')
    # the watchtower
    for y in range(1, 6):
        for x, z in ((5, 4), (7, 4), (5, 6), (7, 6)):
            b.put(x, y, z, 'minecraft:spruce_log')
    b.box(5, 6, 4, 7, 6, 6, 'minecraft:spruce_planks')
    for x, z in ((5, 4), (7, 4), (5, 6), (7, 6)):
        b.put(x, 7, z, 'minecraft:spruce_fence')
    # the fire, the loot, a red banner of wool
    b.put(0, 1, 0, 'minecraft:campfire', {'extinguished': False, 'minecraft:cardinal_direction': 'north'})
    b.put(-5, 1, -4, 'minecraft:chest', {'minecraft:cardinal_direction': 'south'})
    b.chests.append([-5, 1, -4, 'hideout'])
    b.put(4, 1, -5, 'minecraft:chest', {'minecraft:cardinal_direction': 'south'})
    b.chests.append([4, 1, -5, 'hideout_vault'])
    for x, z in ((-2, 3), (2, 3), (3, 2)):
        b.put(x, 1, z, 'minecraft:barrel')
    b.put(-1, 1, -7, 'minecraft:spruce_log')
    b.put(-1, 2, -7, 'minecraft:spruce_log')
    b.put(-1, 3, -7, 'minecraft:red_wool')
    b.put(-1, 4, -7, 'minecraft:red_wool')
    b.spawns += [[0, 1, 2, 'bc:bandit'], [-2, 1, -1, 'bc:bandit'], [2, 1, -1, 'bc:bandit'], [6, 7, 5, 'bc:bandit_archer'],
                 [-4, 1, 0, 'bc:bandit_archer'], [3, 1, 3, 'bc:bandit_thief'], [0, 1, -2, 'chance:0.2:bc:bandit_king']]
    return b


def hive_nest():
    """A hive nest: a mound of wax and moss with eggs, honey and a hollow heart. Anchor = ground at the centre."""
    b = BP()
    _clearing(b, 8, 'minecraft:moss_block', 'minecraft:mud', 0.3, seed=43)
    random.seed(44)
    # the mound: a dome of honeycomb with mossy patches, hollow inside, open to the west
    for x in range(-5, 6):
        for y in range(1, 6):
            for z in range(-5, 6):
                r = math.sqrt(x * x + (y * 1.3) ** 2 + z * z)
                if r > 5.6 or r < 4.3:
                    continue
                if x < -3 and abs(z) <= 1 and y <= 2:
                    continue
                b.put(x, y, z, 'minecraft:moss_block' if random.random() < 0.25 else 'minecraft:honeycomb_block')
    for x, z in ((1, 1), (-1, 2), (2, -2)):
        b.put(x, 1, z, 'minecraft:honey_block')
    for x, z in ((6, 3), (-6, -4), (4, -6), (-3, 6)):
        b.put(x, 1, z, 'minecraft:web')
    b.put(0, 1, -2, 'minecraft:chest', {'minecraft:cardinal_direction': 'west'})
    b.chests.append([0, 1, -2, 'hive'])
    b.spawns += [[-1, 1, 0, 'bc:hive_egg'], [1, 1, 2, 'bc:hive_egg'], [2, 1, -1, 'bc:hive_egg'], [6, 1, -2, 'bc:hive_egg'], [-6, 1, 2, 'bc:hive_egg'],
                 [-7, 1, 0, 'bc:hive_drone'], [5, 1, 5, 'bc:hive_drone'], [0, 1, 6, 'bc:hive_drone'], [0, 1, 0, 'chance:0.12:bc:hive_queen']]
    return b


def cultist_shrine():
    """A cultist shrine: a ring of broken pillars around a crying-obsidian altar. Anchor = ground at the centre."""
    b = BP()
    _clearing(b, 8, 'minecraft:blackstone', 'minecraft:polished_blackstone_bricks', 0.4, seed=45)
    random.seed(46)
    for k in range(8):
        a = k / 8 * math.tau
        x, z = round(math.cos(a) * 6), round(math.sin(a) * 6)
        h = 2 + random.randint(0, 3)
        for y in range(1, h + 1):
            b.put(x, y, z, random.choice(['minecraft:stone_bricks', 'minecraft:cracked_stone_bricks', 'minecraft:mossy_stone_bricks']))
        if h >= 4:
            b.put(x, h + 1, z, 'minecraft:soul_lantern', {'hanging': False})
    # the altar
    b.box(-1, 1, -1, 1, 1, 1, 'minecraft:polished_blackstone_bricks')
    b.put(0, 2, 0, 'minecraft:crying_obsidian')
    for x, z in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        b.put(x, 2, z, 'minecraft:soul_lantern', {'hanging': False})
    for x, z in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        b.put(x, 0, z, 'minecraft:redstone_block')
    b.put(0, 1, -4, 'minecraft:chest', {'minecraft:cardinal_direction': 'south'})
    b.chests.append([0, 1, -4, 'shrine'])
    b.spawns += [[3, 1, 2, 'bc:cultist'], [-3, 1, 2, 'bc:cultist'], [0, 1, 4, 'bc:cultist'], [2, 1, -2, 'bc:imp'], [-2, 1, -2, 'bc:imp']]
    return b


def export_js():
    data = {'outpost': outpost().export(), 'wreck': wreck().export(), 'dungeon': dungeon().export(), 'camp': knight_camp().export(),
            'hideout': bandit_hideout().export(), 'nest': hive_nest().export(), 'shrine': cultist_shrine().export()}
    return ('// AUTO-GENERATED by tools/build.py (tools/bc/structures.py) - do not edit by hand.\n'
            f'export const STRUCTURES = {json.dumps(data, separators=(",", ":"))};\n')
