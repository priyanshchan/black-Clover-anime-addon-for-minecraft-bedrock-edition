"""Shared content definitions used by every generator."""

NS = 'bc'

# attribute id -> display data. `cover` = grimoire cover ramp, `trim` = metal fittings
ATTRIBUTES = {
    'wind': dict(name='Wind', color='6fe0a0', leaves=3, cover=('0c2b1a', '144128', '1d5a36', '277446', '348f57', '45a96a'), trim='silver', mc='§a'),
    'flame': dict(name='Flame', color='ff7a1a', leaves=3, cover=('2a0507', '480a0e', '6a1116', '8c1b1d', 'ad2b26', 'cc4232'), trim='gold', mc='§c'),
    'water': dict(name='Water', color='3ca8ff', leaves=3, cover=('06132e', '0b2150', '133474', '1c4a98', '2a62b6', '3f7fd0'), trim='silver', mc='§9'),
    'lightning': dict(name='Lightning', color='ffe03a', leaves=3, cover=('241703', '3d2806', '5a3d0a', '7a5510', '9b6e18', 'bd8c24'), trim='gold', mc='§e'),
    'light': dict(name='Light', color='fff1b0', leaves=4, cover=('5d5546', '857b66', 'aca28a', 'cfc7ae', 'e9e3cf', 'fbf8ee'), trim='gold', mc='§f'),
    'dark': dict(name='Dark', color='8a46c8', leaves=4, cover=('07040b', '120a1c', '1e1030', '2c1847', '3d2261', '52307e'), trim='silver', mc='§5'),
    'ice': dict(name='Ice', color='8ae6ff', leaves=3, cover=('0d2a36', '154052', '205a70', '2d778f', '3f95ad', '5ab3c8'), trim='silver', mc='§b'),
    'anti': dict(name='Anti-Magic', color='e23a3a', leaves=5, cover=('020203', '070708', '0d0d10', '141418', '1c1c22', '26262e'), trim='blackiron', mc='§8'),
}

ATTR_ORDER = ['wind', 'flame', 'water', 'lightning', 'light', 'dark', 'ice', 'anti']

# Spells: (id, display name, mana cost, cooldown seconds, unlock level, description)
SPELLS = {
    'wind': [
        ('gale_blades', 'Gale Blades', 14, 0.8, 1, 'Fires a fan of three cutting wind crescents.'),
        ('cyclone_step', 'Cyclone Step', 18, 3.0, 3, 'Dash forward on a gust, flinging foes aside.'),
        ('tempest_tornado', 'Tempest Tornado', 40, 8.0, 6, 'A roaming tornado that drags enemies skyward.'),
        ('storm_ascension', 'Storm Ascension', 70, 20.0, 10, 'Erupt into the sky with a devastating wind burst.'),
    ],
    'flame': [
        ('flame_bullet', 'Flame Bullet', 12, 0.7, 1, 'A searing fireball that ignites on impact.'),
        ('blazing_pillar', 'Blazing Pillar', 24, 4.0, 3, 'Pillars of fire erupt where you look.'),
        ('inferno_lion', 'Inferno Lion', 45, 9.0, 6, 'A roaring lion of flame that explodes on impact.'),
        ('solar_nova', 'Solar Nova', 75, 22.0, 10, 'An expanding ring of solar fire around you.'),
    ],
    'water': [
        ('water_bullet', 'Water Bullet', 10, 0.5, 1, 'Rapid pressurised water orbs.'),
        ('healing_spring', 'Healing Spring', 30, 10.0, 3, 'Restores health to you and nearby allies.'),
        ('sea_dragon', 'Sea Dragon Roar', 45, 9.0, 6, 'A water dragon that pierces through every enemy.'),
        ('tidal_prison', 'Tidal Prison', 70, 22.0, 10, 'Traps all nearby enemies in crushing water bubbles.'),
    ],
    'lightning': [
        ('thunder_spear', 'Thunder Spear', 14, 0.8, 1, 'A lightning spear that chains between foes.'),
        ('flash_step', 'Flash Step', 16, 2.5, 3, 'Blink forward in a flash, shocking anything in the path.'),
        ('thunder_armor', 'Thunder Fiend Armor', 40, 25.0, 6, 'Clad yourself in lightning: speed, haste and shock strikes.'),
        ('heavens_judgment', "Heaven's Judgment", 80, 24.0, 10, 'Call down a storm of judgment bolts on all foes.'),
    ],
    'light': [
        ('light_swords', 'Swords of Light', 22, 1.5, 1, 'Summon blades of light that hunt your target.'),
        ('light_speed', 'Light Speed', 20, 3.0, 3, 'Move at the speed of light.'),
        ('holy_ray', 'Holy Ray', 40, 7.0, 6, 'A piercing beam of pure light.'),
        ('radiant_rain', 'Radiant Rain', 85, 25.0, 10, 'A rain of light swords over the battlefield.'),
    ],
    'dark': [
        ('dark_crescent', 'Dark Crescent', 18, 1.2, 1, 'A cloaked crescent slash that pierces through foes.'),
        ('abyssal_hole', 'Abyssal Hole', 38, 9.0, 3, 'A black hole that devours enemies and magic.'),
        ('shadow_cloak', 'Shadow Cloak', 30, 20.0, 6, 'Vanish into darkness and strike unseen.'),
        ('rift_slash', 'Dimension Rift Slash', 90, 26.0, 10, 'A slash that cuts through space itself.'),
    ],
    'ice': [
        ('ice_spear', 'Ice Spear', 12, 0.7, 1, 'A crystal spear that chills its target.'),
        ('frost_prison', 'Frost Prison', 30, 8.0, 3, 'Encase enemies around your target in ice.'),
        ('glacier_wall', 'Glacier Wall', 26, 10.0, 6, 'Raise a temporary wall of glacial ice.'),
        ('absolute_zero', 'Absolute Zero', 80, 24.0, 10, 'A blizzard that freezes everything around you.'),
    ],
    'anti': [
        ('demon_slayer', 'Demon-Slayer Sword', 0, 2.0, 1, 'Draw the massive Demon-Slayer Sword from your grimoire.'),
        ('demon_dweller', 'Demon-Dweller Sword', 0, 2.0, 3, 'Draw the Demon-Dweller Sword, which returns spells.'),
        ('demon_destroyer', 'Demon-Destroyer Sword', 0, 2.0, 6, 'Draw the Demon-Destroyer Sword, which breaks curses.'),
        ('black_form', 'Black Form', 0, 45.0, 10, 'Unleash the devil within. Requires a full Anti-Magic gauge.'),
    ],
}

SWORDS = {
    'demon_slayer_sword': dict(name='Demon-Slayer Sword', damage=12, speed='heavy'),
    'demon_dweller_sword': dict(name='Demon-Dweller Sword', damage=9, speed='fast'),
    'demon_destroyer_sword': dict(name='Demon-Destroyer Sword', damage=10, speed='medium'),
}

ROBES = {
    'black_bull_robe': dict(name='Black Bull Robe', cloth='black_cloth', trim='gold', lining='red_cloth', emblem='bull'),
    'golden_dawn_robe': dict(name='Golden Dawn Robe', cloth='white_cloth', trim='gold', lining='white_cloth', emblem='sun'),
    'crimson_lion_robe': dict(name='Crimson Lion Robe', cloth='red_cloth', trim='gold', lining='black_cloth', emblem='lion'),
}

# ======================================================================================
# Abyssal Seas expansion (original crossover content: fruits, Will, the sea)
# ======================================================================================
# fruit id -> name, colour, power item name, passive, and abilities (id, name, cooldown s, description)
FRUITS = {
    'ember': dict(name='Ember Fruit', color='ff6a1a', mc='§6', power='Ember Body',
                  passive='Immune to fire. Your punches set foes ablaze.',
                  abilities=[('ember_fist', 'Ember Fist', 1.6, 'Hurl a fist of fire that bursts on impact.'),
                             ('blaze_step', 'Blaze Step', 4.0, 'Dash forward, leaving a trail of fire.'),
                             ('cinder_nova', 'Cinder Nova', 14.0, 'Detonate in a ring of white-hot flame.')]),
    'stone': dict(name='Stone Fruit', color='a89a86', mc='§7', power='Stone Body',
                  passive='Hardened skin: you take less damage and shrug off knockback.',
                  abilities=[('boulder_fist', 'Boulder Fist', 2.0, 'Launch a boulder that shatters on impact.'),
                             ('earth_spikes', 'Earth Spikes', 5.0, 'Stone spikes erupt in a line ahead of you.'),
                             ('fortress_skin', 'Fortress Skin', 20.0, 'Turn to granite: huge resistance, slower steps.')]),
    'gravity': dict(name='Gravity Fruit', color='8a5cff', mc='§d', power='Gravity Grip',
                    passive='You never take fall damage.',
                    abilities=[('gravity_crush', 'Gravity Crush', 4.0, 'Slam everything near your aim into the ground.'),
                               ('repulse', 'Repulse', 6.0, 'Hurl everything around you away.'),
                               ('falling_star', 'Falling Star', 18.0, 'Pull a burning meteor down onto your aim.')]),
    'shadow': dict(name='Shadow Fruit', color='3a2a5a', mc='§8', power='Shadow Grasp',
                   passive='Night vision, and you vanish while sneaking in the dark.',
                   abilities=[('shadow_bind', 'Shadow Bind', 6.0, 'Shadows pin down every enemy near your aim.'),
                              ('shade_step', 'Shade Step', 3.0, 'Step through the shadows behind your target.'),
                              ('umbral_legion', 'Umbral Legion', 30.0, 'Raise three shade soldiers to fight for you.')]),
    'bloom': dict(name='Bloom Fruit', color='5cc85a', mc='§a', power='Bloom Touch',
                  passive='You slowly regenerate while standing on grass or leaves.',
                  abilities=[('thorn_lash', 'Thorn Lash', 1.8, 'A whip of poisoned thorns lashes ahead.'),
                             ('healing_pollen', 'Healing Pollen', 12.0, 'Pollen heals you and nearby allies.'),
                             ('rooting_grove', 'Rooting Grove', 18.0, 'Roots seize and crush every enemy around you.')]),
    'quicksilver': dict(name='Quicksilver Fruit', color='c8d0dc', mc='§f', power='Quicksilver Arm',
                        passive='Liquid-metal body: arrows and blades glance off you more often.',
                        abilities=[('mercury_blades', 'Mercury Blades', 2.2, 'Fling a fan of liquid-metal blades.'),
                                   ('flow_dash', 'Flow Dash', 4.0, 'Pour yourself forward through every enemy.'),
                                   ('silver_storm', 'Silver Storm', 16.0, 'A storm of spinning blades surrounds you.')]),
}
FRUIT_ORDER = ['ember', 'stone', 'gravity', 'shadow', 'bloom', 'quicksilver']

WILL_MAX_LEVEL = 10

# Raider captains get generated names from these parts (original, no real characters)
CAPTAIN_FIRST = ['Rust', 'Iron', 'Salt', 'Storm', 'Grim', 'Bone', 'Gold', 'Ash', 'Coral', 'Sable', 'Brine', 'Cinder']
CAPTAIN_LAST = ['fang', 'hook', 'tide', 'eye', 'scale', 'jaw', 'gale', 'brand', 'skull', 'wake', 'reef', 'claw']

# Bounty board shop: item -> (count, price in doubloons, label)
SHOP = [
    ('bc:mana_crystal', 4, 20, 'Mana Crystals x4'),
    ('bc:cannonball', 8, 15, 'Cannonballs x8'),
    ('bc:ship_kit', 1, 60, 'Sailing Ship Kit'),
    ('bc:leviathan_lure', 1, 150, 'Leviathan Lure'),
    ('random_fruit', 1, 400, 'Mystery Abyss Fruit'),
]

# ======================================================================================
# Wave 3: more magic, squads, fruits, ranks
# ======================================================================================
ATTRIBUTES.update({
    'spatial': dict(name='Spatial', color='e08aff', leaves=4, cover=('1a0a24', '2c1240', '421c5e', '5a287e', '74369c', '9048ba'), trim='gold', mc='§d'),
    'earth': dict(name='Earth', color='c49a5a', leaves=3, cover=('1e140a', '33230f', '4a3417', '624520', '7a582a', '936c36'), trim='silver', mc='§6'),
    'steel': dict(name='Steel', color='b8c4d0', leaves=3, cover=('16191e', '22262e', '30353f', '404652', '525a68', '687282'), trim='silver', mc='§7'),
    'mirror': dict(name='Mirror', color='c8d8ff', leaves=4, cover=('1a2236', '26304a', '34405f', '455276', '58668e', '6e7ea8'), trim='silver', mc='§9'),
})
ATTR_ORDER += ['spatial', 'earth', 'steel', 'mirror']

SPELLS.update({
    'spatial': [
        ('warp_gate', 'Warp Gate', 30, 6.0, 1, 'Open linked gates at your feet and where you look.'),
        ('space_cleave', 'Space Cleave', 22, 3.0, 3, 'A slash through space itself - walls cannot stop it.'),
        ('pocket_dimension', 'Pocket Dimension', 40, 10.0, 6, 'Fling every enemy near your aim high into the sky.'),
        ('gate_barrage', 'Gate Barrage', 80, 22.0, 10, 'Portals surround your target and fire from every side.'),
    ],
    'earth': [
        ('stone_bullets', 'Stone Bullets', 12, 0.9, 1, 'Three hardened stone bullets.'),
        ('mud_mire', 'Mud Mire', 26, 7.0, 3, 'Turn the ground near your aim into sucking mud.'),
        ('earth_golem', 'Earth Golem', 50, 30.0, 6, 'Raise a stone golem that fights at your side.'),
        ('continental_quake', 'Continental Quake', 85, 24.0, 10, 'Rings of shattering earth roll out from you.'),
    ],
    'steel': [
        ('steel_lances', 'Steel Lances', 14, 1.0, 1, 'Three steel lances that pierce one enemy each.'),
        ('iron_bulwark', 'Iron Bulwark', 28, 14.0, 3, 'Steel skin: huge resistance and attackers are cut.'),
        ('blade_rain', 'Blade Rain', 40, 9.0, 6, 'Steel blades rain down on your aim.'),
        ('steel_maelstrom', 'Steel Maelstrom', 80, 24.0, 10, 'A whirlwind of orbiting blades shreds everything near you.'),
    ],
    'mirror': [
        ('mirror_shot', 'Mirror Shot', 16, 1.4, 1, 'A light beam that bounces to a second enemy.'),
        ('mirror_image', 'Mirror Image', 36, 20.0, 3, 'Two mirror doubles fight for you.'),
        ('reflection_barrier', 'Reflection Barrier', 30, 12.0, 6, 'For a while, incoming spells and arrows are reflected.'),
        ('kaleidoscope', 'Kaleidoscope', 85, 25.0, 10, 'Mirror panes surround your aim and burn it from every angle.'),
    ],
})

ROBES.update({
    'silver_eagle_robe': dict(name='Silver Eagle Robe', cloth='white_cloth', trim='silver', lining='black_cloth', emblem='eagle'),
    'blue_rose_robe': dict(name='Blue Rose Robe', cloth='navy', trim='silver', lining='white_cloth', emblem='rose'),
    'green_mantis_robe': dict(name='Green Mantis Robe', cloth='green_cloth', trim='gold', lining='black_cloth', emblem='mantis'),
    'coral_peacock_robe': dict(name='Coral Peacock Robe', cloth='coral_cloth', trim='gold', lining='white_cloth', emblem='peacock'),
    'purple_orca_robe': dict(name='Purple Orca Robe', cloth='purple_cloth', trim='silver', lining='black_cloth', emblem='orca'),
    'aqua_deer_robe': dict(name='Aqua Deer Robe', cloth='aqua_cloth', trim='gold', lining='white_cloth', emblem='deer'),
})

# perk text shown in the Handbook / README (implemented in scripts)
ROBE_PERKS = {
    'black_bull_robe': '+25% mana regen, +25% spell power below 40% health',
    'golden_dawn_robe': '+40 max mana, +10% spell power',
    'crimson_lion_robe': 'Flame spells cost 15% less and hit 15% harder',
    'silver_eagle_robe': '+20% spell power while your mana is above 75%',
    'blue_rose_robe': 'Healing and shield spells are 30% stronger; +15 max mana',
    'green_mantis_robe': 'Spell cooldowns are 15% shorter',
    'coral_peacock_robe': 'Every cast has a 20% chance to refund its mana',
    'purple_orca_robe': 'Water breathing, and Water/Ice spells hit 15% harder',
    'aqua_deer_robe': 'Swiftness while out of combat, and +30% mana regen while moving',
}

FRUITS.update({
    'frost': dict(name='Frost Fruit', color='a8e8ff', mc='§b', power='Frost Body', beast=False,
                  passive='Immune to freezing; the sea freezes under your feet.',
                  abilities=[('frost_lance', 'Frost Lance', 1.6, 'Hurl a lance of ice that slows its target.'),
                             ('glacial_path', 'Glacial Path', 6.0, 'Freeze a path ahead, encasing enemies in it.'),
                             ('ice_age', 'Ice Age', 20.0, 'Freeze everything around you solid.')]),
    'barrier': dict(name='Barrier Fruit', color='f0e6a0', mc='§e', power='Barrier Palm', beast=False,
                    passive='Standing still hardens the air around you (damage resistance).',
                    abilities=[('barrier_wall', 'Barrier Wall', 8.0, 'A wall of hardened air blocks the way.'),
                               ('barrier_dome', 'Barrier Dome', 16.0, 'A dome that shields allies and stops projectiles.'),
                               ('barrier_crash', 'Barrier Crash', 5.0, 'Shove a barrier forward, crushing enemies.')]),
    'wolf': dict(name='Wolf Fruit', color='a89c8c', mc='§7', power='Wolf Form', beast=True,
                 passive='Beast form: speed, keen night sight and sharp claws.',
                 abilities=[('pounce', 'Pounce', 3.0, 'Leap onto the enemy you are looking at.'),
                            ('howl', 'Howl', 18.0, 'A howl that strengthens you and cows nearby enemies.'),
                            ('rending_frenzy', 'Rending Frenzy', 10.0, 'A flurry of claw strikes in front of you.')]),
    'hawk': dict(name='Hawk Fruit', color='d49a52', mc='§6', power='Hawk Form', beast=True,
                 passive='Beast form: glide by holding Jump while falling; no fall damage.',
                 abilities=[('sky_ascent', 'Sky Ascent', 6.0, 'Beat your wings and soar straight up.'),
                            ('talon_dive', 'Talon Dive', 5.0, 'Dive onto your aim with crushing talons.'),
                            ('feather_storm', 'Feather Storm', 2.4, 'A fan of razor feathers.')]),
})
for _f in FRUITS.values():
    _f.setdefault('beast', False)
FRUIT_ORDER += ['frost', 'barrier', 'wolf', 'hawk']

# Magic Knight ranks: (stars needed, title)
RANKS = [
    (0, 'Junior Magic Knight'),
    (3, 'Intermediate Magic Knight'),
    (8, 'Senior Magic Knight'),
    (15, 'First Class Senior Magic Knight'),
    (25, 'Vice-Captain'),
    (40, 'Magic Knight Captain'),
    (60, 'Wizard King Candidate'),
]

# Notoriety thresholds for the naval hunters: (bounty, title)
NOTORIETY = [(300, 'Small-time Pirate'), (1500, 'Notorious Pirate'), (5000, 'Sea Tyrant'), (12000, 'Scourge of the Seas')]

SHOP += [('bc:treasure_map', 1, 45, 'Treasure Map'), ('bc:lead_shot', 12, 10, 'Lead Shot x12'), ('bc:hearty_roast', 2, 12, 'Hearty Roast x2')]

# ======================================================================================
# Wave 4: a living world - data-driven spells, more grimoires & fruits, bosses, factions
# ======================================================================================
# Spell specs are read by the script spell engine (src/scripts/living/engine.js).
#   t        template: bolt beam wave zone nova rain meteor buff heal prison summon wall radial
#            timestop leap vortex strikes dive rewind repeat
#   d        base damage (scaled by spell power)      r / dur / n / range   radius, seconds, count, reach
#   shape    bolt shape: 0 orb, 1 shard, 2 blade, 3 needle      size: bolt size step 0-3
#   eff      effects on targets [[id, seconds, amplifier]]      self: effects on the caster
#   fire     seconds of fire      kb [horizontal, vertical]      ls lifesteal fraction
#   hp       health the caster pays (Blood magic)               then: another spec cast right after
#   fx       visual style (sand bubble leaf poison blood star sound mist crystal bone magma time
#            flame wind water lightning light dark ice earth steel ash ink acid metal smoke)
ATTRIBUTES.update({
    'sand': dict(name='Sand', color='e0c27a', leaves=3, cover=('2e2312', '463519', '5f4922', '7a5f2e', '967a3e', 'b29552'), trim='gold', mc='§6'),
    'bubble': dict(name='Bubble', color='9ad8ff', leaves=3, cover=('0e2a3c', '164058', '205a78', '2e7698', '4294b8', '62b2d4'), trim='silver', mc='§b'),
    'plant': dict(name='Plant', color='3fae4a', leaves=3, cover=('0b2010', '123018', '1a4422', '24592d', '307038', '3f8a46'), trim='gold', mc='§2'),
    'poison': dict(name='Poison', color='b6e83a', leaves=3, cover=('141a06', '222c0a', '33420f', '465a16', '5c741e', '748e2a'), trim='blackiron', mc='§a'),
    'blood': dict(name='Blood', color='d01a34', leaves=3, cover=('1a0306', '2c050b', '420812', '5a0c1a', '741224', '901a30'), trim='blackiron', mc='§4'),
    'star': dict(name='Star', color='9fb4ff', leaves=4, cover=('05081a', '0a102c', '111a42', '1a265a', '243474', '30448e'), trim='gold', mc='§9'),
    'sound': dict(name='Sound', color='ff8ad8', leaves=3, cover=('2a0a22', '421034', '5c184a', '782262', '942e7c', 'b03c96'), trim='silver', mc='§d'),
    'mist': dict(name='Mist', color='c8d2dc', leaves=3, cover=('1e2228', '2c3238', '3c434b', '4e565f', '626b75', '78828c'), trim='silver', mc='§7'),
    'crystal': dict(name='Crystal', color='7affd8', leaves=3, cover=('062a24', '0c4038', '14584e', '1e7266', '2a8e80', '3aaa9a'), trim='silver', mc='§3'),
    'bone': dict(name='Bone', color='e8e0c8', leaves=3, cover=('2a2620', '3c3630', '524a40', '6a6052', '847866', '9e927c'), trim='blackiron', mc='§f'),
    'magma': dict(name='Magma', color='ff4a1a', leaves=3, cover=('1a0604', '2e0a06', '46100a', '60180e', '7c2212', '982e18'), trim='blackiron', mc='§c'),
    'time': dict(name='Time', color='e8c060', leaves=4, cover=('1e1608', '30240e', '463416', '5e461e', '785a28', '927034'), trim='gold', mc='§e'),
})
ATTR_ORDER += ['sand', 'bubble', 'plant', 'poison', 'blood', 'star', 'sound', 'mist', 'crystal', 'bone', 'magma', 'time']


def _s(sid_, name_, mana_, cd_, lv_, desc_, **spec):
    return (sid_, name_, mana_, cd_, lv_, desc_, spec)


SPELLS.update({
    'sand': [
        _s('sand_bullets', 'Sand Bullets', 10, 0.6, 1, 'Three grains of hardened sand that grind foes down.', t='bolt', d=4, n=3, spread=6, shape=0, speed=1.9, fx='sand', eff=[['slowness', 1, 0]]),
        _s('quicksand', 'Quicksand', 26, 7.0, 3, 'The ground near your aim becomes sucking quicksand.', t='zone', d=1.5, r=4, dur=5, pull=0.25, fx='sand', eff=[['slowness', 2, 3]]),
        _s('sand_coffin', 'Sand Coffin', 40, 9.0, 6, 'Bury enemies near your aim in sand, then crush them.', t='prison', d=14, r=3.5, dur=3, fx='sand'),
        _s('desert_storm', 'Desert Storm', 80, 24.0, 10, 'A roaring sandstorm around you blinds and shreds foes.', t='zone', at='self', d=3, r=9, dur=6, fx='sand', eff=[['blindness', 2, 0], ['slowness', 2, 1]]),
    ],
    'bubble': [
        _s('bubble_shot', 'Bubble Shot', 8, 0.5, 1, 'A big bubble that pops with a stunning burst.', t='bolt', d=3.5, speed=1.0, shape=0, size=2, aoe=2.2, fx='bubble', eff=[['slowness', 2, 1]]),
        _s('bubble_barrage', 'Bubble Barrage', 22, 3.0, 3, 'A fan of seven popping bubbles.', t='bolt', d=3, n=7, spread=26, speed=0.9, shape=0, size=1, aoe=1.5, fx='bubble'),
        _s('bubble_prison', 'Bubble Prison', 34, 9.0, 6, 'Trap enemies in floating bubbles and lift them away.', t='prison', d=6, r=4, dur=4, fx='bubble', eff=[['levitation', 3, 1]]),
        _s('foam_flood', 'Foam Flood', 72, 22.0, 10, 'A wide wall of crashing foam rolls over everything ahead.', t='wave', d=10, len=16, lanes=3, fx='bubble', kb=[1.8, 0.6]),
    ],
    'plant': [
        _s('thorn_seeds', 'Thorn Seeds', 12, 0.8, 1, 'Three thorned seeds that poison what they hit.', t='bolt', d=4, n=3, spread=10, shape=3, fx='leaf', eff=[['poison', 2, 0]]),
        _s('vine_snare', 'Vine Snare', 24, 6.0, 3, 'Vines burst up and bind enemies near your aim.', t='prison', d=4, r=3, dur=3, fx='leaf'),
        _s('healing_garden', 'Healing Garden', 34, 14.0, 6, 'A blooming garden heals you and your allies.', t='heal', heal=8, r=7, regen=6, fx='leaf'),
        _s('great_tree_wrath', 'Great Tree Wrath', 85, 26.0, 10, 'Giant roots erupt all around you and hurl foes skyward.', t='nova', d=16, r=9, kb=[0.6, 1.1], fx='leaf', eff=[['slowness', 4, 2]]),
    ],
    'poison': [
        _s('venom_needles', 'Venom Needles', 10, 0.6, 1, 'Two needles dripping with venom.', t='bolt', d=3, n=2, spread=4, shape=3, speed=2.2, fx='poison', eff=[['poison', 4, 0]]),
        _s('toxic_mist', 'Toxic Mist', 28, 8.0, 3, 'A cloud of choking poison settles over your aim.', t='zone', d=1, r=4.5, dur=6, fx='poison', eff=[['poison', 3, 1], ['nausea', 4, 0]]),
        _s('serpent_fang', 'Serpent Fang', 36, 7.0, 6, 'A venom serpent fang that pierces a line of foes.', t='bolt', d=12, shape=2, speed=2.0, pierce=3, size=1, fx='poison', eff=[['poison', 5, 1]]),
        _s('plague_bloom', 'Plague Bloom', 80, 24.0, 10, 'A flower of plague bursts open around you.', t='nova', d=10, r=8, fx='poison', eff=[['poison', 8, 2], ['weakness', 8, 1]]),
    ],
    'blood': [
        _s('blood_lances', 'Blood Lances', 6, 0.7, 1, 'Three lances of blood that heal you as they hit. Costs 2 health.', t='bolt', d=6, n=3, spread=5, shape=3, speed=2.0, fx='blood', ls=0.25, hp=2),
        _s('crimson_drain', 'Crimson Drain', 18, 4.0, 3, 'A beam that drains the life of everything it touches.', t='beam', d=8, range=20, fx='blood', ls=0.6),
        _s('blood_rage', 'Blood Rage', 20, 18.0, 6, 'Spend your own blood for raw power and speed. Costs 6 health.', t='buff', fx='blood', hp=6, self=[['strength', 12, 1], ['speed', 12, 1], ['haste', 12, 1]]),
        _s('sanguine_moon', 'Sanguine Moon', 80, 26.0, 10, 'A blood moon strikes every foe around you and feeds you. Costs 8 health.', t='strikes', d=14, n=8, r=12, fx='blood', ls=0.3, hp=8),
    ],
    'star': [
        _s('star_shards', 'Star Shards', 14, 1.0, 1, 'A spray of five shards of starlight.', t='bolt', d=3.5, n=5, spread=18, shape=1, speed=2.0, fx='star'),
        _s('constellation', 'Constellation', 30, 8.0, 3, 'Stars lock onto enemies near your aim and strike them.', t='strikes', d=9, n=5, r=8, fx='star'),
        _s('comet_fall', 'Comet Fall', 48, 12.0, 6, 'Call a comet down on your aim.', t='meteor', d=20, n=1, r=0, aoe=5, size=3, fx='star'),
        _s('supernova', 'Supernova', 90, 26.0, 10, 'Explode with the light of a dying star.', t='nova', d=22, r=11, kb=[2.0, 0.8], fx='star', eff=[['blindness', 3, 0]]),
    ],
    'sound': [
        _s('sonic_pulse', 'Sonic Pulse', 10, 0.6, 1, 'A ringing pulse that passes through foes.', t='bolt', d=5, shape=0, speed=2.4, pierce=2, fx='sound', kb=[1.2, 0.3]),
        _s('resonance', 'Resonance', 24, 6.0, 3, 'A shattering chord blasts everything away from you.', t='nova', d=6, r=5, kb=[2.2, 0.5], fx='sound', eff=[['nausea', 4, 0]]),
        _s('war_song', 'War Song', 30, 20.0, 6, 'A battle song that strengthens you and your allies.', t='buff', allies=8, fx='sound', self=[['strength', 10, 0], ['speed', 10, 0], ['regeneration', 6, 0]]),
        _s('sonic_boom', 'Sonic Boom', 78, 22.0, 10, 'A deafening boom that tears through everything ahead.', t='beam', d=20, range=28, width=2.0, fx='sound', kb=[2.5, 0.8]),
    ],
    'mist': [
        _s('mist_needles', 'Mist Needles', 10, 0.6, 1, 'Three needles of condensed mist.', t='bolt', d=3.5, n=3, spread=8, shape=3, speed=2.0, fx='mist', eff=[['slowness', 2, 0]]),
        _s('vanishing_mist', 'Vanishing Mist', 26, 16.0, 3, 'Vanish into a thick mist that blinds those nearby.', t='buff', fx='mist', self=[['invisibility', 8, 0], ['speed', 8, 1]],
           then=dict(t='zone', at='self', d=0, r=5, dur=5, fx='mist', eff=[['blindness', 2, 0]])),
        _s('phantom_step', 'Phantom Step', 18, 3.0, 6, 'Blink through the mist, cutting everything you pass.', t='leap', d=6, dist=10, mode='blink', fx='mist'),
        _s('mist_labyrinth', 'Mist Labyrinth', 70, 24.0, 10, 'Trap your foes in a maze of mist that saps their strength.', t='zone', d=2, r=8, dur=8, fx='mist', eff=[['blindness', 2, 0], ['slowness', 2, 2], ['weakness', 2, 1]]),
    ],
    'crystal': [
        _s('crystal_shards', 'Crystal Shards', 12, 0.8, 1, 'Three razor crystal shards.', t='bolt', d=4.5, n=3, spread=8, shape=1, speed=2.0, fx='crystal'),
        _s('prism_wall', 'Prism Wall', 24, 12.0, 3, 'Raise a wall of crystal.', t='wall', block='minecraft:light_blue_stained_glass', w=5, h=3, dur=10, fx='crystal'),
        _s('crystal_lances', 'Crystal Lances', 36, 7.0, 6, 'Crystal lances burst from the ground in a line.', t='wave', d=11, len=14, fx='crystal', kb=[0.2, 0.9]),
        _s('diamond_storm', 'Diamond Storm', 82, 24.0, 10, 'Two rings of diamond shards blast out from you.', t='radial', d=8, n=24, rings=2, shape=1, speed=1.4, fx='crystal'),
    ],
    'bone': [
        _s('bone_spear', 'Bone Spear', 12, 0.8, 1, 'A heavy spear of bone that pierces one foe.', t='bolt', d=7, shape=3, speed=2.0, pierce=1, size=1, fx='bone'),
        _s('ribcage_prison', 'Ribcage Prison', 28, 9.0, 3, 'A cage of ribs snaps shut around enemies near your aim.', t='prison', d=6, r=3, dur=4, fx='bone'),
        _s('bone_legion', 'Bone Legion', 50, 30.0, 6, 'Raise two bone warriors to fight for you.', t='summon', id='bc:construct', variant=2, n=2, life=30, fx='bone'),
        _s('graveyard', 'Graveyard', 80, 24.0, 10, 'Bone spikes tear out of the ground in eight directions.', t='wave', d=12, len=12, dirs=8, fx='bone', kb=[0.2, 0.8]),
    ],
    'magma': [
        _s('magma_ball', 'Magma Ball', 14, 0.9, 1, 'A lobbed ball of magma that bursts into flame.', t='bolt', d=6, shape=0, size=1, speed=1.4, grav=0.03, aoe=2.2, fire=4, fx='magma'),
        _s('lava_geyser', 'Lava Geyser', 30, 7.0, 3, 'Geysers of lava erupt at your aim.', t='rain', d=8, n=3, r=2, every=4, fire=5, kb=[0, 1.0], fx='magma'),
        _s('molten_wall', 'Molten Wall', 30, 12.0, 6, 'Raise a wall of glowing magma.', t='wall', block='minecraft:magma', w=5, h=2, dur=8, fx='magma'),
        _s('eruption', 'Eruption', 85, 26.0, 10, 'Lava bombs rain down around your aim.', t='meteor', d=12, n=10, r=8, aoe=3, fire=6, size=1, fx='magma'),
    ],
    'time': [
        _s('clock_hands', 'Clock Hands', 12, 0.8, 1, 'Two clock-hand blades that slow what they cut.', t='bolt', d=5, n=2, spread=6, shape=2, speed=2.0, fx='time', eff=[['slowness', 2, 1]]),
        _s('rewind', 'Rewind', 34, 20.0, 3, 'Turn back your own clock to where you stood 3 seconds ago, and heal.', t='rewind', heal=6, fx='time'),
        _s('accelerate', 'Accelerate', 30, 22.0, 6, 'Speed up your own time.', t='buff', fx='time', self=[['speed', 10, 2], ['haste', 10, 2], ['jump_boost', 10, 1]]),
        _s('time_stop', 'Time Stop', 90, 30.0, 10, 'Stop time for every foe around you. When it flows again, the hits land at once.', t='timestop', d=10, r=12, dur=5, fx='time'),
    ],
})

# altar odds per attribute (the anti-magic five-leaf stays rare)
ALTAR_WEIGHTS = {
    'wind': 11, 'flame': 11, 'water': 11, 'lightning': 11, 'ice': 11, 'earth': 10, 'steel': 9, 'light': 8, 'dark': 8, 'spatial': 6, 'mirror': 6, 'anti': 5,
    'sand': 8, 'bubble': 8, 'plant': 9, 'poison': 7, 'blood': 5, 'star': 4, 'sound': 7, 'mist': 7, 'crystal': 7, 'bone': 6, 'magma': 7, 'time': 3,
}

# Simple casting kits for Magic Knight NPCs whose attribute predates the spell engine
NPC_KITS = {
    'wind': [dict(t='bolt', d=4, n=3, spread=12, shape=2, speed=2.0, fx='wind', kb=[1.0, 0.3]), dict(t='nova', d=5, r=5, kb=[2.2, 0.8], fx='wind')],
    'flame': [dict(t='bolt', d=6, shape=0, speed=1.8, aoe=2, fire=4, fx='flame'), dict(t='rain', d=7, n=4, r=3, every=4, fire=4, fx='flame')],
    'water': [dict(t='bolt', d=4, n=2, spread=6, shape=0, speed=1.6, fx='water'), dict(t='heal', heal=6, r=6, fx='water')],
    'lightning': [dict(t='bolt', d=6, shape=3, speed=2.6, fx='lightning'), dict(t='strikes', d=7, n=3, r=8, fx='lightning')],
    'light': [dict(t='bolt', d=4, n=3, spread=10, shape=2, speed=2.2, fx='light'), dict(t='beam', d=9, range=22, fx='light')],
    'dark': [dict(t='bolt', d=7, shape=2, speed=1.8, pierce=2, fx='dark'), dict(t='vortex', d=6, r=5, dur=1.5, fx='dark')],
    'ice': [dict(t='bolt', d=5, shape=3, speed=2.0, fx='ice', eff=[['slowness', 3, 1]]), dict(t='prison', d=4, r=3, dur=3, fx='ice')],
    'spatial': [dict(t='bolt', d=5, shape=0, speed=2.0, fx='spatial'), dict(t='leap', d=4, dist=8, mode='blink', fx='spatial')],
    'earth': [dict(t='bolt', d=4, n=3, spread=8, shape=0, speed=1.6, grav=0.02, fx='earth'), dict(t='wave', d=8, len=10, fx='earth', kb=[0.2, 0.8])],
    'steel': [dict(t='bolt', d=5, n=3, spread=6, shape=2, speed=2.0, fx='steel'), dict(t='rain', d=5, n=6, r=3, every=2, fx='steel')],
    'mirror': [dict(t='beam', d=7, range=20, fx='mirror'), dict(t='bolt', d=4, n=2, spread=8, shape=1, speed=2.2, fx='mirror')],
}

FRUITS.update({
    'lava': dict(name='Lava Fruit', color='ff3a10', mc='§c', power='Lava Body', beast=False,
                 passive='Immune to fire and lava; your blows scorch.',
                 abilities=[('lava_fist', 'Lava Fist', 1.8, 'Lob a fist of molten rock that bursts into flame.', dict(t='bolt', d=8, shape=0, size=1, speed=1.5, grav=0.02, aoe=2.5, fire=6, fx='magma')),
                            ('magma_pool', 'Magma Pool', 8.0, 'Turn the ground near your aim into a burning pool.', dict(t='zone', d=3, r=3.5, dur=6, fire=4, fx='magma')),
                            ('volcanic_rain', 'Volcanic Rain', 20.0, 'Lava bombs pour down around your aim.', dict(t='meteor', d=10, n=8, r=7, aoe=3, fire=5, size=1, fx='magma'))]),
    'ash': dict(name='Ash Fruit', color='8a8a94', mc='§8', power='Ash Body', beast=False,
                passive='Your body turns to ash: blows sometimes pass right through you.',
                abilities=[('cinder_spear', 'Cinder Spear', 2.0, 'A spear of glowing cinders that pierces foes.', dict(t='bolt', d=7, shape=3, speed=2.0, pierce=2, fire=3, fx='ash')),
                           ('ash_veil', 'Ash Veil', 9.0, 'A choking veil of ash smothers your aim.', dict(t='zone', d=1, r=5, dur=6, fx='ash', eff=[['blindness', 2, 0], ['wither', 2, 0]])),
                           ('ash_cyclone', 'Ash Cyclone', 16.0, 'A cyclone of ash drags foes in and burns them.', dict(t='vortex', d=12, r=7, dur=3, fire=3, fx='ash'))]),
    'prism': dict(name='Prism Fruit', color='f0a0ff', mc='§d', power='Prism Eye', beast=False,
                  passive='Your eyes drink in light: you see clearly in the dark.',
                  abilities=[('prism_ray', 'Prism Ray', 2.5, 'A blazing ray of split light.', dict(t='beam', d=10, range=26, fx='light')),
                             ('rainbow_burst', 'Rainbow Burst', 8.0, 'Sixteen shards of colour burst out from you.', dict(t='radial', d=5, n=16, shape=1, speed=1.8, fx='light')),
                             ('refraction', 'Refraction', 4.0, 'Bend the light and appear further ahead.', dict(t='leap', d=5, dist=12, mode='blink', fx='light'))]),
    'bounce': dict(name='Bounce Fruit', color='ff9ac8', mc='§d', power='Bounce Body', beast=False,
                   passive='Springy body: you jump higher and never take fall damage.',
                   abilities=[('ricochet', 'Ricochet', 3.0, 'Bounce forward, slamming into everything in your path.', dict(t='leap', d=9, dist=10, mode='dash', fx='sound')),
                              ('recoil_wave', 'Recoil Wave', 7.0, 'A springy shock that flings everything away from you.', dict(t='nova', d=7, r=5, kb=[2.6, 0.9], fx='sound')),
                              ('meteor_bounce', 'Meteor Bounce', 12.0, 'Spring sky-high and crash down on your aim.', dict(t='dive', d=12, r=4, fx='sound'))]),
    'blast': dict(name='Blast Fruit', color='ffb030', mc='§6', power='Blast Palm', beast=False,
                  passive='Your punches go off with a small blast.',
                  abilities=[('blast_shot', 'Blast Shot', 1.6, 'A shot that explodes on impact.', dict(t='bolt', d=6, shape=0, speed=1.8, aoe=3, fx='flame')),
                             ('mine_field', 'Mine Field', 9.0, 'Scatter blast mines around your aim.', dict(t='rain', d=8, n=6, r=4, every=5, fx='flame')),
                             ('big_bang', 'Big Bang', 18.0, 'Detonate yourself in a huge (harmless to you) explosion.', dict(t='nova', d=18, r=8, kb=[2.0, 1.0], fx='flame'))]),
    'acid': dict(name='Acid Fruit', color='9cff3a', mc='§a', power='Acid Body', beast=False,
                 passive='Acid blood: poison can never take hold of you.',
                 abilities=[('acid_spit', 'Acid Spit', 1.6, 'Three globs of acid that weaken foes.', dict(t='bolt', d=4, n=3, spread=10, shape=0, speed=1.6, fx='acid', eff=[['poison', 3, 0], ['weakness', 3, 0]])),
                            ('acid_rain', 'Acid Rain', 10.0, 'Acid rains down on your aim.', dict(t='rain', d=4, n=14, r=5, every=2, fx='acid', eff=[['poison', 3, 0]])),
                            ('corrode', 'Corrode', 6.0, 'A stream of acid that eats through armour and flesh.', dict(t='beam', d=8, range=16, fx='acid', eff=[['weakness', 6, 1], ['wither', 3, 0]]))]),
    'lodestone': dict(name='Lodestone Fruit', color='c05a4a', mc='§c', power='Lodestone Grip', beast=False,
                      passive='Magnetic body: arrows veer away from you.',
                      abilities=[('magnet_pull', 'Magnet Pull', 5.0, 'Drag every foe near your aim together and crush them.', dict(t='vortex', d=6, r=6, dur=1.5, fx='metal')),
                                 ('magnet_push', 'Magnet Push', 6.0, 'Repel everything around you.', dict(t='nova', d=6, r=7, kb=[3.0, 0.6], fx='metal')),
                                 ('iron_tempest', 'Iron Tempest', 16.0, 'Iron blades spin out from you in every direction.', dict(t='radial', d=7, n=16, shape=2, speed=1.6, fx='metal'))]),
    'cloud': dict(name='Cloud Fruit', color='e8f0ff', mc='§f', power='Cloud Body', beast=False,
                  passive='Light as a cloud: you drift down slowly when sneaking in the air.',
                  abilities=[('thunderhead', 'Thunderhead', 6.0, 'Thunder strikes foes near your aim.', dict(t='strikes', d=9, n=4, r=8, fx='lightning')),
                             ('cloud_ride', 'Cloud Ride', 12.0, 'Rise on a cloud and drift where you like.', dict(t='buff', fx='mist', self=[['levitation', 2, 0], ['slow_falling', 10, 0], ['speed', 10, 1]])),
                             ('downpour', 'Downpour', 10.0, 'A cold downpour that slows and soaks foes.', dict(t='zone', d=1.5, r=5, dur=6, fx='water', eff=[['slowness', 2, 1]]))]),
    'ink': dict(name='Ink Fruit', color='6050a0', mc='§5', power='Ink Body', beast=False,
                passive='Ink seeps from your wounds and blinds whoever hit you.',
                abilities=[('ink_blot', 'Ink Blot', 1.6, 'Three blots of blinding ink.', dict(t='bolt', d=4, n=3, spread=9, shape=0, speed=1.6, fx='ink', eff=[['blindness', 3, 0]])),
                           ('ink_serpent', 'Ink Serpent', 6.0, 'A serpent of ink that coils through a line of foes.', dict(t='bolt', d=10, shape=2, size=2, speed=1.4, pierce=3, fx='ink')),
                           ('ink_sea', 'Ink Sea', 16.0, 'Flood the ground around you with ink.', dict(t='zone', at='self', d=1, r=7, dur=6, fx='ink', eff=[['blindness', 2, 0], ['slowness', 2, 1]]))]),
    'bear': dict(name='Bear Fruit', color='8a5a3a', mc='§6', power='Bear Form', beast=True,
                 passive='Beast form: crushing strength and a thick hide.',
                 abilities=[('maul', 'Maul', 1.6, 'A crushing swipe at everything in front of you.', dict(t='nova', at='front', d=12, r=3, kb=[1.6, 0.4], fx='earth')),
                            ('bear_roar', 'Roar', 16.0, 'A roar that weakens and slows every foe nearby.', dict(t='nova', d=2, r=7, kb=[1.2, 0.3], fx='sound', eff=[['weakness', 6, 1], ['slowness', 4, 1]], self=[['strength', 8, 1]])),
                            ('ground_slam', 'Ground Slam', 10.0, 'Leap and slam the earth on your aim.', dict(t='dive', d=14, r=5, fx='earth'))]),
    'tiger': dict(name='Tiger Fruit', color='ff9a2a', mc='§6', power='Tiger Form', beast=True,
                  passive='Beast form: blinding speed and keen night sight.',
                  abilities=[('tiger_lunge', 'Lunge', 3.0, 'Lunge forward, tearing through your path.', dict(t='leap', d=9, dist=9, mode='dash', fx='wind')),
                             ('claw_rush', 'Claw Rush', 7.0, 'Four lightning-fast claw strikes.', dict(t='repeat', n=4, every=4, spec=dict(t='nova', at='front', d=5, r=2.8, kb=[0.4, 0.1], fx='blood'))),
                             ('predator', 'Predator', 20.0, 'Enter the hunt: speed, strength and night sight.', dict(t='buff', fx='blood', self=[['speed', 12, 2], ['strength', 12, 1], ['night_vision', 15, 0]]))]),
    'wyvern': dict(name='Wyvern Fruit', color='5ab48a', mc='§2', power='Wyvern Form', beast=True,
                   passive='Beast form: wings to glide on and a hide that ignores fire.',
                   abilities=[('wyvern_breath', 'Wyvern Breath', 3.0, 'A roaring stream of dragonfire.', dict(t='beam', d=9, range=14, width=1.6, fire=5, fx='flame')),
                              ('wing_gust', 'Wing Gust', 6.0, 'A beat of your wings blasts everything away.', dict(t='nova', d=5, r=6, kb=[2.5, 0.8], fx='wind')),
                              ('sky_dive', 'Sky Dive', 12.0, 'Soar up and dive onto your aim in flames.', dict(t='dive', d=16, r=5, fire=4, fx='flame'))]),
})
for _f in FRUITS.values():
    _f.setdefault('beast', False)
FRUIT_ORDER += ['lava', 'ash', 'prism', 'bounce', 'blast', 'acid', 'lodestone', 'cloud', 'ink', 'bear', 'tiger', 'wyvern']

# Magic Knight NPC names (original)
KNIGHT_FIRST = ['Aldric', 'Mirela', 'Corvin', 'Sela', 'Bastian', 'Elowen', 'Rook', 'Tamsin', 'Garrick', 'Lys', 'Oren', 'Petra',
                'Fenn', 'Ilsa', 'Dorian', 'Maren', 'Cassian', 'Wren', 'Edda', 'Lucan', 'Brielle', 'Hale', 'Odette', 'Tobias']
KNIGHT_LAST = ['Vale', 'Thorne', 'Ashford', 'Brightwater', 'Ravensworth', 'Hollow', 'Stormridge', 'Fairhaven', 'Greymoor',
               'Silverbrook', 'Oakheart', 'Duskmere', 'Emberly', 'Windmere', 'Coldwell', 'Larkspur']
KNIGHT_ROBES = ['black_bull_robe', 'golden_dawn_robe', 'crimson_lion_robe', 'silver_eagle_robe', 'blue_rose_robe',
                'green_mantis_robe', 'coral_peacock_robe', 'purple_orca_robe', 'aqua_deer_robe']

# Travelling Magic Merchant: (item, count, price in doubloons, label)
MERCHANT = [
    ('bc:mana_crystal', 8, 30, 'Mana Crystals x8'),
    ('bc:ancient_page', 2, 60, 'Ancient Grimoire Pages x2'),
    ('random_fruit', 1, 450, 'Mystery Abyss Fruit'),
    ('bc:knight_contract', 1, 140, 'Knight Contract (hire a Magic Knight)'),
    ('bc:skirmish_horn', 1, 90, 'Skirmish Horn'),
    ('bc:archdevil_sigil', 1, 600, 'Archdevil Sigil'),
    ('bc:colossus_core', 1, 500, 'Colossus Core'),
    ('bc:galleon_bell', 1, 500, 'Phantom Galleon Bell'),
    ('bc:kraken_lure', 1, 550, 'Storm Kraken Lure'),
    ('bc:clover_charm', 1, 900, 'Wishing Clover Charm'),
]

# War Table factions: id -> (label, colour code, soldier types, leader type)
FACTIONS = {
    'knights': dict(name='Clover Magic Knights', mc='§a', units=['bc:magic_knight'], leader='bc:magic_knight'),
    'devils': dict(name='Devil Host', mc='§4', units=['bc:dark_disciple', 'bc:dark_disciple', 'bc:imp'], leader='bc:dark_disciple'),
    'raiders': dict(name='Sea Raiders', mc='§c', units=['bc:sea_raider'], leader='bc:raider_captain'),
    'navy': dict(name='Tidewatch Navy', mc='§9', units=['bc:tidewatch_sentinel'], leader='bc:tidewatch_commodore'),
    'constructs': dict(name='Ancient Constructs', mc='§7', units=['bc:construct'], leader='bc:construct'),
}
