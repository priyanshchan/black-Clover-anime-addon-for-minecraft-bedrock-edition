"""v1.2.0 blueprints: the Royal Capital and the kingdoms' border forts (exported with the landmarks)."""
from __future__ import annotations

import math

from .structures11 import CHEST_S, LIT, LBP, S, Y_AXIS

FACE = {'north': {'minecraft:cardinal_direction': 'north'}, 'south': {'minecraft:cardinal_direction': 'south'},
        'east': {'minecraft:cardinal_direction': 'east'}, 'west': {'minecraft:cardinal_direction': 'west'}}


def _walls(b, x0, x1, z0, z1, h, mat, door=None, roof=None, corner=None):
    """A hollow building: walls from y 1 to h, a floor at 0, a flat roof at h + 1, a doorway on one side."""
    b.clear_box(x0 + 1, x1 - 1, 1, h, z0 + 1, z1 - 1)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            b.put(x, 0, z, S + 'spruce_planks' if roof != 'stone' else S + 'polished_andesite')
            edge = x in (x0, x1) or z in (z0, z1)
            if edge:
                for y in range(1, h + 1):
                    c = corner and x in (x0, x1) and z in (z0, z1)
                    b.put(x, y, z, S + (corner if c else mat), Y_AXIS if c else None)
            b.put(x, h + 1, z, S + ('dark_oak_planks' if roof != 'stone' else 'deepslate_tiles'))
    if door:
        side, at = door
        for y in (1, 2, 3):
            for k in (-1, 0, 1):
                if side == 'south':
                    b.put(at + k, y, z1, S + 'air')
                elif side == 'north':
                    b.put(at + k, y, z0, S + 'air')
                elif side == 'east':
                    b.put(x1, y, at + k, S + 'air')
                else:
                    b.put(x0, y, at + k, S + 'air')
    # windows
    for x in range(x0 + 2, x1 - 1, 3):
        for z in (z0, z1):
            if b.blocks.get((x, 2, z)) != b.pal(S + 'air'):
                b.put(x, 2, z, S + 'glass_pane')
    for z in range(z0 + 2, z1 - 1, 3):
        for x in (x0, x1):
            if b.blocks.get((x, 2, z)) != b.pal(S + 'air'):
                b.put(x, 2, z, S + 'glass_pane')


def capital():
    """The Royal Capital: a walled town with a gate, a plaza and fountain, the Magic Knight HQ, a smithy, an inn, a market,
    houses and a Waygate. Anchor = the ground at the plaza's centre."""
    b = LBP(1701)
    R = 26
    for x in range(-R, R + 1):
        for z in range(-R, R + 1):
            b.found.append((x, z))
            road = abs(x) <= 2 or abs(z) <= 2 or x * x + z * z <= 64
            if road:
                b.put(x, 0, z, S + 'polished_andesite')
            b.clear_above(x, z, 1, 14)
    # the walls, crenellations and the south gate
    for x in range(-R, R + 1):
        for z in range(-R, R + 1):
            if max(abs(x), abs(z)) != R:
                continue
            gate = z == R and abs(x) <= 2
            for y in range(1, 7):
                if not (gate and y <= 4):
                    b.put(x, y, z, b.brick(0.15, 0.1))
            if (x + z) % 2 == 0:
                b.put(x, 7, z, S + 'stone_bricks')
    for x in (-3, 3):
        for y in range(1, 9):
            b.put(x, y, R, S + 'chiseled_stone_bricks')
    for x in range(-3, 4):
        b.put(x, 5, R, S + 'chiseled_stone_bricks')
        b.put(x, 9, R, S + 'stone_bricks')
    for x in (-2, 2):
        for y in (6, 7, 8):
            b.put(x, y, R + 1, S + 'green_wool')
    # corner towers
    for cx in (-R, R):
        for cz in (-R, R):
            for x in range(cx - 2, cx + 3):
                for z in range(cz - 2, cz + 3):
                    edge = abs(x - cx) == 2 or abs(z - cz) == 2
                    for y in range(1, 11):
                        if edge:
                            b.put(x, y, z, b.brick(0.15, 0.1))
                    if (x + z) % 2 == 0 and edge:
                        b.put(x, 11, z, S + 'stone_bricks')
                    if not edge:
                        b.put(x, 10, z, S + 'spruce_planks')
            b.put(cx, 11, cz, S + 'lantern', LIT)
    # the plaza: a fountain with a statue of light, flower beds and lamp posts
    for k in range(24):
        a = k / 24 * math.tau
        x, z = round(math.cos(a) * 3), round(math.sin(a) * 3)
        b.put(x, 1, z, S + 'stone_bricks')
    for x in range(-2, 3):
        for z in range(-2, 3):
            if x * x + z * z <= 5:
                b.put(x, 0, z, S + 'water')
    for y in range(1, 5):
        b.put(0, y, 0, S + 'quartz_pillar', Y_AXIS)
    b.put(0, 5, 0, S + 'gold_block')
    b.put(0, 6, 0, S + 'sea_lantern')
    for x, z in ((-6, -6), (6, -6), (-6, 6), (6, 6)):
        b.put(x, 1, z, S + 'oak_fence')
        b.put(x, 2, z, S + 'oak_fence')
        b.put(x, 3, z, S + 'lantern', LIT)
    for x, z in ((-5, 2), (-5, 3), (5, -3), (5, -2)):
        b.put(x, 0, z, S + 'grass_block')
        b.put(x, 1, z, S + b.rng.choice(['poppy', 'cornflower', 'oxeye_daisy', 'allium']))
    b.put(5, 1, 5, 'bc:waygate')
    b.marks += [['gate', 5, 1, 5], ['center', 0, 1, 0]]
    # lamp posts down the main street
    for z in (10, 16, 22):
        for x in (-3, 3):
            b.put(x, 1, z, S + 'oak_fence')
            b.put(x, 2, z, S + 'lantern', LIT)
    # the Magic Knight HQ (north)
    _walls(b, -9, 9, -22, -11, 7, 'stone_bricks', door=('south', 0), roof='stone', corner='spruce_log')
    for x in range(-7, 8):
        b.put(x, 9, -16, S + 'deepslate_tiles')
    b.put(-4, 1, -20, 'bc:mission_board', FACE['south'])
    b.put(0, 1, -18, 'bc:war_table', FACE['south'])
    b.put(4, 1, -20, 'bc:squad_banner', FACE['south'])
    for x in (-8, 8):
        b.put(x, 4, -10, S + 'green_wool')
        b.put(x, 5, -10, S + 'green_wool')
    for x, z in ((-7, -13), (7, -13), (-7, -21), (7, -21)):
        b.put(x, 1, z, S + 'lantern', LIT)
    b.marks += [['res_quartermaster', 2, 1, -14], ['guard', -4, 1, -8], ['guard', 4, 1, -8], ['guard', -3, 1, 20], ['guard', 3, 1, 20]]
    # the smithy (east): an open workshop with a Magic Forge
    _walls(b, 12, 21, -6, 4, 5, 'cobblestone', door=('west', -1), corner='spruce_log')
    b.put(19, 1, -4, 'bc:magic_forge', FACE['west'])
    b.put(19, 1, 2, S + 'smithing_table')
    b.put(17, 1, -4, S + 'cauldron')
    b.put(14, 1, 2, S + 'barrel', {'facing_direction': 1})
    b.put(15, 1, 2, S + 'barrel', {'facing_direction': 1})
    # the inn (west)
    _walls(b, -21, -12, -6, 6, 5, 'oak_planks', door=('east', 0), corner='oak_log')
    for x, z in ((-18, -3), (-18, 3), (-15, -3), (-15, 3)):
        b.put(x, 1, z, S + 'oak_fence')
        b.put(x, 2, z, S + 'oak_pressure_plate')
    b.put(-20, 1, 0, S + 'barrel', {'facing_direction': 1})
    b.put(-20, 1, 1, S + 'barrel', {'facing_direction': 1})
    b.put(-16, 1, 0, S + 'lantern', LIT)
    b.marks += [['res_bard', -17, 1, 0]]
    # the market (south-east and south-west): stalls with wool awnings
    for (sx, sz, wool, who) in ((8, 10, 'red_wool', 'res_peddler'), (14, 10, 'blue_wool', 'res_cartographer'), (-8, 10, 'yellow_wool', 'res_hermit'),
                                (-14, 10, 'lime_wool', None)):
        for x, z in ((sx - 2, sz - 2), (sx + 2, sz - 2), (sx - 2, sz + 2), (sx + 2, sz + 2)):
            for y in (1, 2, 3):
                b.put(x, y, z, S + 'spruce_fence')
        for x in range(sx - 2, sx + 3):
            for z in range(sz - 2, sz + 3):
                b.put(x, 4, z, S + wool if (x + z) % 2 == 0 else S + 'white_wool')
        b.put(sx, 1, sz - 1, S + 'barrel', {'facing_direction': 1})
        if who:
            b.marks += [[who, sx, 1, sz]]
    # houses in the corners
    for (hx, hz) in ((-17, -18), (16, -18), (-18, 18), (17, 18)):
        _walls(b, hx - 3, hx + 3, hz - 3, hz + 3, 4, 'oak_planks' if b.rng.random() < 0.5 else 'spruce_planks', door=('south' if hz < 0 else 'north', hx),
               corner='spruce_log')
    return b


def _keep(b, R, wall, trim, light, banner, glass):
    b.pad(R + 3, S + 'gravel', S + 'cobblestone', 0.4, clear=14, round_=False)
    for x in range(-R, R + 1):
        for z in range(-R, R + 1):
            edge = max(abs(x), abs(z)) == R
            if not edge:
                continue
            gate = z == R and abs(x) <= 1
            for y in range(1, 9):
                if gate and y <= 3:
                    continue
                b.put(x, y, z, S + (trim if y in (1, 8) else glass if y == 5 and (x + z) % 4 == 0 and not gate else wall))
            if (x + z) % 2 == 0:
                b.put(x, 9, z, S + wall)
    for cx in (-R, R):
        for cz in (-R, R):
            for y in range(1, 13):
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        b.put(cx + dx, y, cz + dz, S + (trim if y in (1, 12) else wall))
            b.put(cx, 13, cz, S + light)
    for x in (-2, 2):
        for y in (5, 6, 7):
            b.put(x, y, R + 1, S + banner)
    # a raised keep in the middle
    for x in range(-3, 4):
        for z in range(-4, 2):
            edge = abs(x) == 3 or z in (-4, 1)
            for y in range(1, 7):
                if edge and not (z == 1 and x == 0 and y <= 3):
                    b.put(x, y, z, S + wall)
            b.put(x, 7, z, S + trim)
    b.put(0, 8, -1, S + light)


def diamond_fort():
    b = LBP(1711)
    _keep(b, 8, 'polished_andesite', 'stone_bricks', 'sea_lantern', 'light_blue_wool', 'light_blue_stained_glass')
    b.chest(-5, 1, -5, 'fort_diamond')
    b.chest(5, 1, -5, 'fort_diamond')
    b.marks += [['boss', 0, 1, -2]]
    b.spawns += [[-5, 1, 4, 'bc:diamond_legionnaire'], [5, 1, 4, 'bc:diamond_legionnaire'], [-8, 13, -8, 'bc:diamond_legionnaire'],
                 [8, 13, 8, 'bc:diamond_legionnaire'], [0, 1, 5, 'chance:0.5:bc:diamond_legionnaire']]
    return b


def spade_citadel():
    b = LBP(1712)
    _keep(b, 8, 'polished_blackstone_bricks', 'blackstone', 'soul_lantern', 'purple_wool', 'crying_obsidian')
    b.chest(-5, 1, -5, 'fort_spade')
    b.chest(5, 1, -5, 'fort_spade')
    b.marks += [['boss', 0, 1, -2]]
    b.spawns += [[-5, 1, 4, 'bc:spade_zealot'], [5, 1, 4, 'bc:spade_zealot'], [-8, 13, -8, 'bc:spade_zealot'], [8, 13, 8, 'bc:spade_zealot'],
                 [0, 1, 5, 'chance:0.5:bc:spade_zealot']]
    return b


def heart_sanctum():
    """A spirit grove: a ring of flowering azaleas around a blossoming spirit tree and a little shrine."""
    b = LBP(1713)
    b.pad(10, S + 'moss_block', S + 'grass_block', 0.4, clear=12)
    for k in range(20):
        a = k / 20 * math.tau
        x, z = round(math.cos(a) * 9), round(math.sin(a) * 9)
        if abs(x) <= 1 and z > 0:
            continue
        b.put(x, 1, z, S + ('flowering_azalea' if k % 2 else 'azalea'))
    for y in range(1, 8):
        b.put(0, y, -3, S + 'cherry_log', Y_AXIS)
    for x in range(-4, 5):
        for z in range(-7, 2):
            for y in (7, 8, 9):
                d = x * x + (z + 3) ** 2 + (y - 8) ** 2 * 2
                if d <= 16 and b.rng.random() < 0.9:
                    b.put(x, y, z, S + 'cherry_leaves', {'persistent_bit': True})
    for _ in range(18):
        x, z = b.rng.randint(-7, 7), b.rng.randint(-7, 7)
        if x * x + z * z < 64 and (x, 1, z) not in b.blocks:
            b.put(x, 1, z, S + b.rng.choice(['pink_tulip', 'allium', 'lily_of_the_valley', 'azure_bluet']))
    b.put(0, 1, 2, S + 'stone_bricks')
    b.put(0, 2, 2, S + 'sea_lantern')
    b.marks += [['priestess', 2, 1, 1]]
    b.spawns += [[-4, 1, 3, 'bc:heart_guardian'], [4, 1, 3, 'bc:heart_guardian'], [0, 1, -6, 'bc:heart_guardian']]
    return b


BLUEPRINTS = {'capital': capital, 'diamond_fort': diamond_fort, 'spade_citadel': spade_citadel, 'heart_sanctum': heart_sanctum}
