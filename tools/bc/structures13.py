"""v1.3.0 landmark blueprints: the Underworld Breach (where the Crowned Vessel waits)."""
from __future__ import annotations

import math

from .structures11 import LBP, S, Y_AXIS


def underworld_breach():
    """A scorched bowl around a wound in the world: blackstone and smouldering netherrack, crying-obsidian spires
    with soul fire, broken Magic Knight banners, and a rift of glowing crimson at the heart where the Vessel stands."""
    b = LBP(1801)
    R = 11
    for x in range(-R - 1, R + 2):
        for z in range(-R - 1, R + 2):
            d = math.sqrt(x * x + z * z)
            if d > R + 0.8:
                continue
            b.found.append((x, z))
            depth = max(0, int(round((R - d) * 0.3)))
            b.clear_above(x, z, -depth + 1, 8)
            r = b.rng.random()
            mat = 'magma' if r < 0.1 else 'netherrack' if r < 0.35 else 'blackstone' if r < 0.7 else 'basalt' if r < 0.8 else 'soul_soil'
            b.put(x, -depth, z, S + mat, Y_AXIS if mat == 'basalt' else None)
            if mat == 'netherrack' and b.rng.random() < 0.25:
                b.put(x, -depth + 1, z, S + 'fire')
            if mat == 'soul_soil' and b.rng.random() < 0.3:
                b.put(x, -depth + 1, z, S + 'soul_fire')
    cy = -int(round(R * 0.3))
    # the rift: a ring of crimson glow around a pit of obsidian
    for x in range(-3, 4):
        for z in range(-3, 4):
            d = math.sqrt(x * x + z * z)
            if d <= 1.5:
                b.put(x, cy, z, S + 'crying_obsidian')
            elif d <= 3.2:
                b.put(x, cy, z, S + ('shroomlight' if (x + z) % 2 else 'nether_wart_block'))
    # crying-obsidian spires with soul fire on top
    for k in range(5):
        a = k / 5 * math.tau + 0.3
        x, z = round(math.cos(a) * 7), round(math.sin(a) * 7)
        base = -max(0, int(round((R - 7) * 0.3)))
        h = 4 + b.rng.randint(0, 3)
        for y in range(1, h + 1):
            b.put(x, base + y, z, S + ('crying_obsidian' if b.rng.random() < 0.6 else 'obsidian'))
        b.put(x, base + h + 1, z, S + 'soul_fire')
        b.put(x, base + h, z, S + 'soul_soil')
    # broken banners of the knights who came before
    for x, z in ((-9, 3), (8, -5), (2, 9)):
        base = -max(0, int(round((R - math.hypot(x, z)) * 0.3)))
        b.put(x, base + 1, z, S + 'oak_fence')
        b.put(x, base + 2, z, S + 'black_wool')
    b.chest(0, cy + 1, 3, 'breach')
    b.marks += [['boss', 0, cy + 1, 0]]
    b.spawns += [[-5, cy + 2, 5, 'bc:imp'], [5, cy + 2, -5, 'bc:imp'], [6, cy + 2, 5, 'chance:0.6:bc:devil_host'], [-6, cy + 2, -5, 'chance:0.4:bc:cultist']]
    return b


BLUEPRINTS = {'underworld_breach': underworld_breach}
