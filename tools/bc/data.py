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

# ======================================================================================
# v0.2.0: eight more grimoires, eight more fruits, enemy spell kits, companions
# ======================================================================================
ATTRIBUTES.update({
    'cotton': dict(name='Cotton', color='f4eee0', leaves=3, cover=('4a4438', '6a6252', '8a826e', 'aaa28c', 'c8c0aa', 'e0d8c4'), trim='gold', mc='§f'),
    'paper': dict(name='Paper', color='efe6c8', leaves=3, cover=('3a3020', '54462e', '6e5e40', '8a7854', 'a6946a', 'c2b084'), trim='silver', mc='§f'),
    'smoke': dict(name='Smoke', color='9a9aa4', leaves=3, cover=('141418', '202026', '2e2e36', '3e3e48', '50505c', '646472'), trim='blackiron', mc='§8'),
    'glass': dict(name='Glass', color='c8f0ff', leaves=3, cover=('163240', '204656', '2c5c70', '3a748a', '4a8ea6', '5ea8c0'), trim='silver', mc='§b'),
    'gold': dict(name='Gold', color='ffcf40', leaves=4, cover=('3a2606', '5a3c0a', '7a5410', '9c6e18', 'be8a22', 'dca832'), trim='gold', mc='§6'),
    'beast': dict(name='Beast', color='c08040', leaves=3, cover=('2a1a0c', '402814', '58381c', '704826', '8a5a30', 'a46c3c'), trim='blackiron', mc='§6'),
    'spirit': dict(name='Spirit', color='90ffe8', leaves=4, cover=('062a26', '0c3e38', '14564e', '1e7066', '2a8c80', '3aa89a'), trim='silver', mc='§3'),
    'rune': dict(name='Rune', color='b070ff', leaves=4, cover=('14082a', '22103e', '321856', '442270', '582e8c', '6e3ca8'), trim='gold', mc='§5'),
})
ATTR_ORDER += ['cotton', 'paper', 'smoke', 'glass', 'gold', 'beast', 'spirit', 'rune']

SPELLS.update({
    'cotton': [
        _s('cotton_puffs', 'Cotton Puffs', 10, 0.6, 1, 'Three soft puffs that tangle and slow foes.', t='bolt', d=3, n=3, spread=10, shape=0, size=1, speed=1.6, fx='cotton', eff=[['slowness', 2, 1]]),
        _s('cotton_bind', 'Cotton Bind', 24, 7.0, 3, 'Wrap enemies near your aim in thick cotton.', t='prison', d=4, r=3, dur=4, fx='cotton'),
        _s('cloud_cushion', 'Cloud Cushion', 30, 14.0, 6, 'A cloud of cotton heals you and your allies.', t='heal', heal=7, r=7, regen=5, fx='cotton'),
        _s('cotton_fortress', 'Cotton Fortress', 75, 26.0, 10, 'Armour of packed cotton for your allies, and a smothering field around you.', t='buff', allies=8, fx='cotton',
           self=[['resistance', 10, 1], ['absorption', 10, 2]], then=dict(t='zone', at='self', d=0, r=7, dur=6, fx='cotton', eff=[['slowness', 2, 2], ['weakness', 2, 0]])),
    ],
    'paper': [
        _s('paper_cuts', 'Paper Cuts', 10, 0.6, 1, 'Four razor-edged sheets of paper.', t='bolt', d=3, n=4, spread=16, shape=2, speed=2.2, fx='paper'),
        _s('paper_cranes', 'Paper Cranes', 28, 8.0, 3, 'Folded cranes dive onto enemies near your aim.', t='strikes', d=7, n=4, r=9, fx='paper'),
        _s('paper_wall', 'Paper Wall', 22, 12.0, 6, 'Raise a wall of tightly folded paper.', t='wall', block='minecraft:white_wool', w=5, h=3, dur=10, fx='paper'),
        _s('thousand_sheets', 'Thousand Sheets', 80, 24.0, 10, 'Two storms of paper blades burst out from you.', t='radial', d=6, n=30, rings=2, shape=2, speed=1.8, fx='paper'),
    ],
    'smoke': [
        _s('smoke_shot', 'Smoke Shot', 12, 0.8, 1, 'A ball of smoke that bursts and blinds.', t='bolt', d=5, shape=0, size=1, speed=1.6, aoe=2.2, fx='smoke', eff=[['blindness', 2, 0]]),
        _s('smokescreen', 'Smokescreen', 24, 14.0, 3, 'Vanish into thick smoke that blinds those nearby.', t='buff', fx='smoke', self=[['invisibility', 6, 0], ['speed', 6, 1]],
           then=dict(t='zone', at='self', d=0, r=6, dur=6, fx='smoke', eff=[['blindness', 2, 0]])),
        _s('choking_cloud', 'Choking Cloud', 30, 9.0, 6, 'A choking cloud settles over your aim.', t='zone', d=1.5, r=5, dur=6, fx='smoke', eff=[['nausea', 3, 0], ['weakness', 3, 1]]),
        _s('smoke_dragon', 'Smoke Dragon', 78, 22.0, 10, 'A dragon of smoke coils through every foe in its path.', t='bolt', d=14, shape=2, size=3, speed=1.3, pierce=5, fx='smoke', eff=[['blindness', 3, 0]]),
    ],
    'glass': [
        _s('glass_shards', 'Glass Shards', 12, 0.8, 1, 'Five shards of glass in a wide spray.', t='bolt', d=3, n=5, spread=20, shape=1, speed=2.0, fx='glass'),
        _s('glass_wall', 'Glass Wall', 22, 12.0, 3, 'A clear wall of glass blocks the way.', t='wall', block='minecraft:glass', w=5, h=3, dur=12, fx='glass'),
        _s('shatter_prison', 'Shatter Prison', 36, 9.0, 6, 'Encase enemies in glass, then shatter it.', t='prison', d=12, r=3.5, dur=3, fx='glass'),
        _s('glass_rain', 'Glass Rain', 80, 24.0, 10, 'A storm of falling glass over your aim.', t='rain', d=5, n=16, r=6, every=2, fx='glass'),
    ],
    'gold': [
        _s('gold_coins', 'Golden Coins', 12, 0.8, 1, 'Three heavy golden coins.', t='bolt', d=4, n=3, spread=8, shape=0, speed=2.0, fx='gold'),
        _s('gilded_armor', 'Gilded Armour', 30, 20.0, 3, 'Coat yourself in gold: resistance, absorption and strength.', t='buff', fx='gold', self=[['resistance', 10, 1], ['absorption', 10, 1], ['strength', 10, 0]]),
        _s('golden_chains', 'Golden Chains', 36, 9.0, 6, 'Golden chains bind everything near your aim.', t='prison', d=8, r=4, dur=4, fx='gold'),
        _s('midas_judgment', 'Midas Judgment', 85, 26.0, 10, 'A colossal golden coin falls from the sky.', t='meteor', d=26, n=1, r=0, aoe=6, size=3, fx='gold'),
    ],
    'beast': [
        _s('beast_claws', 'Beast Claws', 10, 0.8, 1, 'Spirit claws rake everything in front of you.', t='nova', at='front', d=7, r=3, kb=[0.8, 0.2], fx='beast'),
        _s('beast_charge', 'Beast Charge', 20, 4.0, 3, 'Charge forward like a wild beast.', t='leap', d=9, dist=10, mode='dash', fx='beast'),
        _s('predator_roar', 'Predator Roar', 30, 14.0, 6, 'A roar that weakens and scatters foes.', t='nova', d=3, r=7, kb=[1.6, 0.4], fx='beast', eff=[['weakness', 5, 1], ['slowness', 3, 1]], self=[['strength', 8, 1]]),
        _s('primal_rampage', 'Primal Rampage', 75, 24.0, 10, 'Five savage strikes in a row.', t='repeat', n=5, every=5, fx='beast', spec=dict(t='nova', at='front', d=7, r=3.2, kb=[0.5, 0.2], fx='beast')),
    ],
    'spirit': [
        _s('wisp_bolts', 'Wisp Bolts', 12, 0.8, 1, 'Three spirit wisps that feed your life.', t='bolt', d=4, n=3, spread=12, shape=0, speed=1.8, ls=0.3, fx='spirit'),
        _s('spirit_mend', 'Spirit Mend', 32, 14.0, 3, 'Spirits mend you and your allies.', t='heal', heal=8, r=8, regen=6, fx='spirit'),
        _s('soul_chains', 'Soul Chains', 36, 9.0, 6, 'Spirit chains drag foes together and tear at them.', t='vortex', d=8, r=6, dur=2, fx='spirit'),
        _s('spirit_storm', 'Spirit Storm', 85, 26.0, 10, 'A host of spirits strikes every foe around your aim.', t='strikes', d=10, n=8, r=12, ls=0.2, fx='spirit'),
    ],
    'rune': [
        _s('rune_darts', 'Rune Darts', 12, 0.7, 1, 'Two glowing rune darts.', t='bolt', d=5, n=2, spread=6, shape=3, speed=2.4, fx='rune'),
        _s('rune_trap', 'Rune Trap', 26, 10.0, 3, 'A rune circle that bites everything that walks over it.', t='zone', d=4, r=3, dur=10, fx='rune', eff=[['slowness', 2, 3]]),
        _s('sealing_circle', 'Sealing Circle', 40, 12.0, 6, 'A circle of runes seals the strength of enemies near your aim.', t='prison', d=6, r=5, dur=4, fx='rune', eff=[['weakness', 6, 2]]),
        _s('grand_runecraft', 'Grand Runecraft', 85, 26.0, 10, 'Runic lines burst out in eight directions.', t='wave', d=14, len=14, dirs=8, fx='rune', kb=[0.2, 0.9]),
    ],
})
ALTAR_WEIGHTS.update({'cotton': 7, 'paper': 7, 'smoke': 7, 'glass': 7, 'gold': 4, 'beast': 7, 'spirit': 4, 'rune': 4})

FRUITS.update({
    'spore': dict(name='Spore Fruit', color='c8a070', mc='§6', power='Spore Body', beast=False,
                  passive='A haze of spores poisons whoever strikes you.',
                  abilities=[('spore_shot', 'Spore Shot', 1.8, 'A puffball that bursts into poison.', dict(t='bolt', d=4, shape=0, size=1, speed=1.5, aoe=2.5, fx='poison', eff=[['poison', 4, 0]])),
                             ('spore_burst', 'Spore Burst', 9.0, 'A cloud of spores around you.', dict(t='zone', at='self', d=1, r=5, dur=4, fx='poison', eff=[['poison', 3, 1]])),
                             ('fungal_bloom', 'Fungal Bloom', 16.0, 'Healing mushrooms sprout around you.', dict(t='heal', heal=6, r=6, regen=5, fx='leaf'))]),
    'thread': dict(name='Thread Fruit', color='e8e8f0', mc='§f', power='Thread Hands', beast=False,
                   passive='Silk lines catch you: you never take fall damage.',
                   abilities=[('thread_lash', 'Thread Lash', 2.0, 'A razor-thin line slices everything ahead.', dict(t='beam', d=9, range=18, width=0.8, fx='paper')),
                              ('string_cage', 'String Cage', 9.0, 'A cage of threads binds foes near your aim.', dict(t='prison', d=8, r=4, dur=4, fx='paper')),
                              ('puppet_strings', 'Puppet Strings', 12.0, 'Strings drag foes together.', dict(t='vortex', d=6, r=6, dur=2, fx='paper'))]),
    'slime': dict(name='Slime Fruit', color='60e060', mc='§a', power='Slime Body', beast=False,
                  passive='A bouncy body: falls barely hurt you and knockback slides off.',
                  abilities=[('slime_ball', 'Slime Ball', 1.8, 'A lobbed slime ball that splats and sticks.', dict(t='bolt', d=5, shape=0, size=2, speed=1.3, grav=0.03, aoe=2.5, fx='acid', eff=[['slowness', 3, 2]])),
                             ('sticky_pool', 'Sticky Pool', 9.0, 'A pool of slime glues enemies in place.', dict(t='zone', d=1, r=4, dur=6, fx='acid', eff=[['slowness', 2, 4]])),
                             ('slime_slam', 'Slime Slam', 10.0, 'Bounce high and splat down on your aim.', dict(t='dive', d=12, r=5, fx='acid'))]),
    'chain': dict(name='Chain Fruit', color='a0a0a8', mc='§7', power='Chain Arms', beast=False,
                  passive='Iron links: your punches hit like a hammer.',
                  abilities=[('chain_hook', 'Chain Hook', 2.0, 'A hooked chain that pierces and slows.', dict(t='bolt', d=6, shape=3, speed=2.6, pierce=1, fx='metal', eff=[['slowness', 2, 2]])),
                             ('chain_whirl', 'Chain Whirl', 8.0, 'Chains whirl out in every direction.', dict(t='radial', d=6, n=12, shape=2, speed=1.6, fx='metal')),
                             ('binding_chains', 'Binding Chains', 12.0, 'Chains erupt and bind every foe near your aim.', dict(t='prison', d=10, r=4, dur=4, fx='metal'))]),
    'lion': dict(name='Lion Fruit', color='e0a040', mc='§6', power='Lion Form', beast=True,
                 passive='Beast form: a king\'s strength and a thick mane.',
                 abilities=[('pride_pounce', 'Pride Pounce', 4.0, 'Pounce onto your aim.', dict(t='dive', d=12, r=4, fx='beast')),
                            ('mane_lash', 'Mane Lash', 6.0, 'Three heavy swipes.', dict(t='repeat', n=3, every=5, spec=dict(t='nova', at='front', d=7, r=3, kb=[0.7, 0.2], fx='beast'))),
                            ('roar_of_kings', 'Roar of Kings', 18.0, 'A roar that cows every foe and fires your blood.', dict(t='nova', d=4, r=8, kb=[1.8, 0.4], fx='sound', eff=[['weakness', 6, 1], ['slowness', 4, 1]], self=[['strength', 10, 1], ['resistance', 10, 0]]))]),
    'shark': dict(name='Shark Fruit', color='4a86c8', mc='§9', power='Shark Form', beast=True,
                  passive='Beast form: you swim like a shark - the sea does not drain you.',
                  abilities=[('shark_bite', 'Shark Bite', 2.0, 'A crushing bite in front of you.', dict(t='nova', at='front', d=14, r=2.6, kb=[0.4, 0.1], fx='water')),
                             ('tidal_rush', 'Tidal Rush', 5.0, 'Rush forward on a wave.', dict(t='leap', d=9, dist=12, mode='dash', fx='water')),
                             ('riptide', 'Riptide', 14.0, 'A riptide drags foes together and under.', dict(t='vortex', d=8, r=6, dur=2, fx='water'))]),
    'phoenix': dict(name='Phoenix Fruit', color='ff8a30', mc='§6', power='Phoenix Form', beast=True,
                    passive='Beast form: blue flame mends you, you glide on burning wings, fire cannot touch you.',
                    abilities=[('blazing_feathers', 'Blazing Feathers', 2.4, 'A fan of burning feathers.', dict(t='bolt', d=4, n=5, spread=30, shape=2, speed=2.0, fire=3, fx='flame')),
                               ('firewing_dive', 'Firewing Dive', 10.0, 'Dive onto your aim wreathed in flame.', dict(t='dive', d=14, r=5, fire=4, fx='flame')),
                               ('rebirth_flame', 'Rebirth Flame', 20.0, 'Blue flames heal you and your allies.', dict(t='heal', heal=10, r=6, regen=6, fx='spirit'))]),
    'spider': dict(name='Spider Fruit', color='7a4a8a', mc='§5', power='Spider Form', beast=True,
                   passive='Beast form: you see in the dark and webs never slow you.',
                   abilities=[('web_shot', 'Web Shot', 2.0, 'Three strands of sticky web.', dict(t='bolt', d=3, n=3, spread=12, shape=3, speed=2.0, fx='paper', eff=[['slowness', 3, 3]])),
                              ('venom_bite', 'Venom Bite', 3.0, 'A venomous bite in front of you.', dict(t='nova', at='front', d=10, r=2.6, fx='poison', eff=[['poison', 5, 1]])),
                              ('web_trap', 'Web Trap', 12.0, 'Webs pin down every foe near your aim.', dict(t='prison', d=4, r=4, dur=5, fx='paper'))]),
})
for _f in FRUITS.values():
    _f.setdefault('beast', False)
FRUIT_ORDER += ['spore', 'thread', 'slime', 'chain', 'lion', 'shark', 'phoenix', 'spider']

# Spell kits for script-driven enemies (run by the tactical brain). src = tint/colour source.
ENEMY_KITS = {
    'bc:dark_disciple': dict(src='a:dark', kit=[dict(t='prison', d=4, r=2.5, dur=2, fx='dark'), dict(t='bolt', d=5, n=3, spread=14, shape=2, speed=1.8, fx='dark', eff=[['weakness', 3, 0]])]),
    'bc:imp': dict(src='a:flame', kit=[dict(t='bolt', d=4, shape=0, speed=1.6, fire=2, fx='flame'), dict(t='dive', d=6, r=2.5, fx='flame')]),
    'bc:sea_raider': dict(src='f:blast', kit=[dict(t='bolt', d=6, shape=0, size=1, speed=1.2, grav=0.03, aoe=2.5, fx='flame')]),
    'bc:raider_gunner': dict(src='a:steel', kit=[dict(t='bolt', d=6, shape=3, speed=3.0, fx='gun'), dict(t='bolt', d=7, shape=0, size=1, speed=1.2, grav=0.03, aoe=2.8, fx='flame')]),
    'bc:tidewatch_marksman': dict(src='a:steel', kit=[dict(t='bolt', d=7, shape=3, speed=3.2, fx='gun'), dict(t='bolt', d=4, n=3, spread=6, shape=3, speed=3.0, fx='gun')]),
    'bc:hellhound': dict(src='a:magma', kit=[dict(t='leap', d=7, dist=8, mode='dash', fire=3, fx='flame'), dict(t='beam', d=5, range=6, width=1.4, fire=4, fx='flame')]),
    'bc:mana_wraith': dict(src='a:spirit', kit=[dict(t='beam', d=5, range=14, ls=0.5, fx='spirit'), dict(t='leap', d=3, dist=8, mode='blink', fx='spirit'), dict(t='prison', d=3, r=3, dur=2, fx='spirit')]),
}

# Companions (hired Magic Knights): levels 1-20, health tiers, bond ranks
COMPANION_XP = [0, 0, 20, 60, 120, 200, 320, 480, 700, 1000, 1400, 1900, 2500, 3200, 4000, 5000, 6200, 7600, 9200, 11000, 13000]
COMPANION_HP = [(1, 40), (5, 60), (10, 80), (15, 100), (20, 130)]   # (from level, max health)
BOND = [(0, 'Stranger', 'Follows and fights at your side.'),
        (100, 'Comrade', 'Keeps formation and casts 10% harder.'),
        (300, 'Friend', 'Mana Link: tops up your mana when it runs low (60s cooldown).'),
        (700, 'Sworn Ally', 'Guardian: shields you when you fall below 25% health (90s cooldown).'),
        (1500, 'Soulbound', 'Union Magic: unleash a combined spell together from the whistle (120s cooldown).')]
PARTY_MAX = 4
COMPANION_LINES = {
    'join': ['My grimoire is yours, {p}.', 'Point me at the enemy, {p}.', 'Together, then. Let\'s go!'],
    'summon': ['Here!', 'At your side.', 'Ready when you are, {p}.', 'Did you call?'],
    'return': ['That one hurt... but I\'m back.', 'You can\'t get rid of me that easily.', 'Back on my feet!'],
    'level': ['I can feel my magic growing!', 'My grimoire turned a new page!', 'Stronger every day!'],
    'kill': ['Got one!', 'Down it goes.', 'Next!', 'Too easy.'],
    'low': ['{p}, you\'re hurt - fall back!', 'Hang in there, {p}!', 'I\'ll cover you!'],
    'boss': ['That thing is huge...', 'Stay together - this is a big one!', 'Careful, {p}!'],
    'idle': ['Nice weather for a stroll.', 'I wonder what the Wizard King is doing.', 'My feet hurt.', 'Want to spar later?'],
    'gift': ['For me? Thank you, {p}!', 'Delicious!', 'You\'re too kind.'],
    'union': ['Now, {p}! Together!', 'Our magic as one!'],
    'loot': ['I picked these up for you.', 'Don\'t forget your loot!'],
}
MERCHANT += [('bc:companion_whistle', 1, 80, 'Companion Whistle'), ('bc:mana_cookie', 6, 40, 'Mana Cookies x6')]

# v0.2.0 units join the War Table armies
FACTIONS['devils']['units'] += ['bc:hellhound']
FACTIONS['raiders']['units'] += ['bc:raider_gunner']
FACTIONS['navy']['units'] += ['bc:tidewatch_marksman']

# ======================================================================================
# v0.3.0: awakened spells, missions, amulets, brooms, the Rogue Mages
# ======================================================================================
# Each grimoire (except Anti-Magic) awakens a fifth spell at magic level 15.
AWAKENED = {
    'wind': _s('gale_emperor', 'Gale Emperor', 110, 38.0, 15, 'A colossal cyclone drags every foe in and hurls them skyward.', t='vortex', d=18, r=10, dur=3, fx='wind', kb=[0.5, 1.6]),
    'flame': _s('crown_of_suns', 'Crown of Suns', 115, 38.0, 15, 'A crown of suns rains fire around your aim.', t='meteor', d=16, n=8, r=7, aoe=3.5, fire=6, size=2, fx='flame'),
    'water': _s('ocean_sovereign', 'Ocean Sovereign', 110, 36.0, 15, 'A tidal wave crashes out in every direction.', t='wave', d=16, len=16, dirs=12, fx='water', kb=[1.8, 0.8]),
    'lightning': _s('thousand_bolts', 'Thousand Bolts', 115, 38.0, 15, 'Lightning strikes every foe in sight, three times over.', t='repeat', n=3, every=10, fx='lightning', spec=dict(t='strikes', d=10, n=6, r=14, fx='lightning')),
    'light': _s('judgment_day', 'Judgment Day', 120, 40.0, 15, 'A pillar of judgment for every foe near your aim.', t='strikes', d=15, n=10, r=14, fx='light'),
    'dark': _s('void_eclipse', 'Void Eclipse', 120, 40.0, 15, 'An eclipse swallows everything around your aim.', t='vortex', d=22, r=9, dur=4, fx='dark', eff=[['blindness', 3, 0]]),
    'ice': _s('eternal_winter', 'Eternal Winter', 120, 40.0, 15, 'Freeze every foe around you solid, then shatter them.', t='timestop', d=16, r=11, dur=4, fx='ice'),
    'spatial': _s('dimension_collapse', 'Dimension Collapse', 115, 38.0, 15, 'Space folds in on your aim and tears apart.', t='vortex', d=24, r=8, dur=2, fx='spatial'),
    'earth': _s('world_splitter', 'World Splitter', 115, 38.0, 15, 'The earth splits open in twelve directions.', t='wave', d=18, len=18, dirs=12, fx='earth', kb=[0.3, 1.2]),
    'steel': _s('iron_tempest_grand', 'Iron Tempest', 110, 36.0, 15, 'Three storms of steel blades burst out from you.', t='radial', d=9, n=24, rings=3, shape=2, speed=1.8, fx='steel'),
    'mirror': _s('hall_of_mirrors', 'Hall of Mirrors', 115, 38.0, 15, 'Mirrors catch every foe near your aim and burn them with light.', t='strikes', d=13, n=8, r=12, fx='mirror'),
    'sand': _s('endless_desert', 'Endless Desert', 110, 38.0, 15, 'A desert storm that blinds and buries everything around you.', t='zone', at='self', d=5, r=11, dur=8, fx='sand', eff=[['blindness', 2, 0], ['slowness', 2, 2]]),
    'bubble': _s('bubble_cataclysm', 'Bubble Cataclysm', 110, 36.0, 15, 'A sky full of bubbles bursts over your aim.', t='rain', d=7, n=24, r=7, every=2, fx='bubble'),
    'plant': _s('world_tree', 'World Tree', 120, 40.0, 15, 'A giant tree heals your allies and crushes your foes.', t='heal', heal=12, r=10, regen=8, fx='leaf', then=dict(t='nova', d=16, r=10, kb=[0.6, 1.2], fx='leaf')),
    'poison': _s('venom_kingdom', 'Venom Kingdom', 110, 38.0, 15, 'A kingdom of poison spreads over your aim.', t='zone', d=3, r=9, dur=8, fx='poison', eff=[['poison', 3, 2], ['wither', 2, 0]]),
    'blood': _s('crimson_feast', 'Crimson Feast', 90, 38.0, 15, 'Feast on the life of every foe around you. Costs 10 health.', t='nova', d=20, r=10, ls=0.5, hp=10, fx='blood'),
    'star': _s('starfall', 'Starfall', 120, 40.0, 15, 'A shower of comets falls around your aim.', t='meteor', d=18, n=7, r=8, aoe=4, size=2, fx='star'),
    'sound': _s('requiem', 'Requiem', 110, 36.0, 15, 'Three crashing chords stun everything around you.', t='repeat', n=3, every=8, fx='sound', spec=dict(t='nova', d=9, r=9, kb=[1.4, 0.4], fx='sound', eff=[['nausea', 4, 0]])),
    'mist': _s('phantom_realm', 'Phantom Realm', 115, 38.0, 15, 'Vanish, and let phantom blades strike every foe near your aim.', t='buff', fx='mist', self=[['invisibility', 6, 0], ['speed', 6, 1]],
               then=dict(t='strikes', d=11, n=8, r=12, fx='mist')),
    'crystal': _s('crystal_cathedral', 'Crystal Cathedral', 115, 38.0, 15, 'Crystal spires erupt in ten directions.', t='wave', d=17, len=16, dirs=10, fx='crystal', kb=[0.2, 1.0]),
    'bone': _s('ossuary_gate', 'Ossuary Gate', 110, 45.0, 15, 'Four bone warriors rise to fight for you.', t='summon', id='bc:construct', variant=2, n=4, life=40, fx='bone'),
    'magma': _s('volcanic_wrath', 'Volcanic Wrath', 120, 40.0, 15, 'Lava erupts all around your aim.', t='rain', d=12, n=18, r=9, every=2, fire=6, kb=[0, 1.2], fx='magma'),
    'time': _s('end_of_time', 'End of Time', 130, 45.0, 15, 'Stop time for six seconds; every frozen foe takes the blows at once.', t='timestop', d=30, r=14, dur=6, fx='time'),
    'cotton': _s('cloud_kingdom', 'Cloud Kingdom', 110, 40.0, 15, 'Clouds shield your allies and smother your foes.', t='buff', allies=10, fx='cotton', self=[['resistance', 8, 2], ['regeneration', 8, 0]],
                 then=dict(t='zone', at='self', d=0, r=10, dur=8, fx='cotton', eff=[['slowness', 2, 3], ['weakness', 2, 1]])),
    'paper': _s('origami_army', 'Origami Army', 110, 38.0, 15, 'A storm of paper cranes strikes again and again.', t='repeat', n=3, every=10, fx='paper', spec=dict(t='strikes', d=9, n=6, r=12, fx='paper')),
    'smoke': _s('smoke_kingdom', 'Smoke Kingdom', 110, 38.0, 15, 'A choking kingdom of smoke over your aim.', t='zone', d=3, r=10, dur=8, fx='smoke', eff=[['blindness', 2, 0], ['nausea', 3, 0], ['weakness', 2, 1]]),
    'glass': _s('shattered_sky', 'Shattered Sky', 115, 38.0, 15, 'The sky shatters into falling glass.', t='rain', d=7, n=30, r=9, every=1, fx='glass'),
    'gold': _s('golden_age', 'Golden Age', 125, 42.0, 15, 'Golden armour for your allies, and a rain of gold on your foes.', t='buff', allies=10, fx='gold', self=[['resistance', 10, 1], ['absorption', 10, 3], ['strength', 10, 1]],
               then=dict(t='meteor', d=18, n=4, r=6, aoe=4, size=2, fx='gold')),
    'beast': _s('beast_king', 'Beast King', 110, 38.0, 15, 'Six savage strikes and the strength of a beast king.', t='repeat', n=6, every=5, fx='beast', self=[['strength', 10, 2]],
                spec=dict(t='nova', at='front', d=9, r=3.5, kb=[0.6, 0.2], fx='beast')),
    'spirit': _s('spirit_host', 'Spirit Host', 120, 40.0, 15, 'Spirits heal your allies, then drain every foe near your aim.', t='heal', heal=10, r=10, regen=8, fx='spirit',
                 then=dict(t='strikes', d=10, n=8, r=12, ls=0.3, fx='spirit')),
    'rune': _s('runic_apocalypse', 'Runic Apocalypse', 125, 42.0, 15, 'A vast rune circle seals and shatters every foe inside.', t='prison', d=24, r=9, dur=5, fx='rune', eff=[['weakness', 6, 3]]),
}
for _a, _sp in AWAKENED.items():
    SPELLS[_a].append(_sp)

# Magic Knight missions (Mission Board): id, kind, target, count, title, tier
#   kinds: kill (entity id or family), boss, gate, cast, xp, deliver (item), companion (kills by your companions), rescue
MISSIONS = [
    ('m_disciples', 'kill', 'bc:dark_disciple', 8, 'Rout the Dark Disciples', 1),
    ('m_imps', 'kill', 'bc:imp', 10, 'Clear out the Imps', 1),
    ('m_hounds', 'kill', 'bc:hellhound', 4, 'Hunt down Hellhounds', 2),
    ('m_raiders', 'kill', 'bc_pirate', 8, 'Drive off the Sea Raiders', 1),
    ('m_wraiths', 'kill', 'bc:mana_wraith', 4, 'Banish Mana Wraiths', 2),
    ('m_rogues', 'kill', 'bc:rogue_mage', 5, 'Bring Rogue Mages to justice', 2),
    ('m_monsters', 'kill', 'monster', 30, 'Patrol: defeat 30 monsters', 1),
    ('m_boss', 'boss', 'boss', 1, 'Defeat a great foe (any boss)', 3),
    ('m_gate', 'gate', 'bc:devil_gate', 1, 'Seal a Devil Gate', 2),
    ('m_cast', 'cast', '', 40, 'Training: cast 40 spells or fruit powers', 1),
    ('m_xp', 'xp', '', 600, 'Training: earn 600 magic XP', 2),
    ('m_crystals', 'deliver', 'bc:mana_crystal', 12, 'Deliver 12 Mana Crystals', 1),
    ('m_pages', 'deliver', 'bc:ancient_page', 3, 'Recover 3 Ancient Grimoire Pages', 2),
    ('m_bones', 'deliver', 'minecraft:bone', 24, 'Deliver 24 bones for the healers', 1),
    ('m_squad', 'companion', '', 10, 'Lead your companions to 10 victories', 2),
]
MISSION_REWARDS = {1: dict(stars=1, coins=30, xp=120), 2: dict(stars=2, coins=70, xp=250), 3: dict(stars=3, coins=150, xp=500)}

# Amulets: hold one in your off hand
AMULETS = {
    'amulet_mana': ('§bMana Heart', '+30 max mana and 20% faster mana regeneration'),
    'amulet_swift': ('§aSwift Sigil', 'Spell cooldowns 12% shorter'),
    'amulet_power': ('§cBattle Charm', '+12% spell power'),
    'amulet_guard': ('§eGuardian Ward', 'Resistance II while below 40% health'),
    'amulet_vigor': ('§dVigor Band', 'Two extra hearts and faster healing'),
}

# Brooms: tier -> (name, top speed blocks/tick, mana per second)
BROOMS = {'broom': ('§6Magic Broom', 0.55, 1.5), 'swift_broom': ('§bSwift Broom', 0.85, 2.5)}

FACTIONS['rogues'] = dict(name='Rogue Mages', mc='§5', units=['bc:rogue_mage'], leader='bc:rogue_mage')
MERCHANT += [('bc:broom', 1, 120, 'Magic Broom'), ('random_amulet', 1, 220, 'Mystery Amulet')]

# ======================================================================================
# v0.5.0: the companion update (personalities, specialisations, party tactics, mood, trials,
# the reserve roster and expeditions), four more grimoires and the Soul Puppeteer
# ======================================================================================
ATTRIBUTES.update({
    'gravity': dict(name='Gravity', color='8a6cff', leaves=4, cover=('120c26', '1c1438', '281e4c', '362a62', '46387a', '584894'), trim='silver', mc='§5'),
    'moon': dict(name='Moon', color='c8d8ff', leaves=4, cover=('0c1226', '141c38', '1e284c', '2a3662', '38467a', '485894'), trim='silver', mc='§9'),
    'thorn': dict(name='Thorn', color='6a9a3a', leaves=3, cover=('142008', '1e300c', '2a4212', '385618', '486c20', '5a842a'), trim='blackiron', mc='§2'),
    'ash': dict(name='Ash', color='9a8a80', leaves=3, cover=('1e1a18', '2c2624', '3a3330', '4a423e', '5c524c', '6e645c'), trim='gold', mc='§7'),
})
ATTR_ORDER += ['gravity', 'moon', 'thorn', 'ash']
SPELLS.update({
    'gravity': [
        _s('gravity_orb', 'Gravity Orb', 12, 0.8, 1, 'A heavy orb that crushes and slows whatever it hits.', t='bolt', d=5, shape=0, size=2, speed=1.5, aoe=2.4, fx='gravity', eff=[['slowness', 2, 2]]),
        _s('crushing_field', 'Crushing Field', 28, 8.0, 3, 'Gravity multiplies around your aim, dragging foes to the ground.', t='zone', d=3, r=4, dur=5, pull=0.3, fx='gravity', eff=[['slowness', 2, 3]]),
        _s('skyward_lift', 'Skyward Lift', 34, 10.0, 6, 'Gravity lets go: foes near your aim float helplessly into the air.', t='nova', at='aim', d=6, r=5, fx='gravity', eff=[['levitation', 2, 2]]),
        _s('singularity', 'Singularity', 82, 24.0, 10, 'A point of crushing gravity swallows everything nearby.', t='vortex', d=18, r=8, dur=3, fx='gravity'),
    ],
    'moon': [
        _s('moonbeam_darts', 'Moonbeam Darts', 10, 0.6, 1, 'Three darts of pale moonlight.', t='bolt', d=4, n=3, spread=10, shape=1, speed=2.2, fx='moon'),
        _s('crescent_arc', 'Crescent Arc', 22, 5.0, 3, 'A sweeping crescent of moonlight in front of you.', t='nova', at='front', d=9, r=4, kb=[1.0, 0.3], fx='moon'),
        _s('lunar_blessing', 'Lunar Blessing', 32, 14.0, 6, 'Moonlight mends you and your allies.', t='heal', heal=8, r=8, regen=5, fx='moon'),
        _s('moonlight_pillars', 'Moonlight Pillars', 84, 24.0, 10, 'Pillars of moonlight fall on every foe near your aim.', t='strikes', d=11, n=7, r=12, fx='moon', eff=[['blindness', 2, 0]]),
    ],
    'thorn': [
        _s('thorn_needles', 'Thorn Needles', 10, 0.6, 1, 'Four poisoned needles.', t='bolt', d=3, n=4, spread=14, shape=3, speed=2.4, fx='thorn', eff=[['poison', 2, 0]]),
        _s('bramble_snare', 'Bramble Snare', 26, 8.0, 3, 'Brambles burst up and bind foes near your aim.', t='prison', d=5, r=3, dur=4, fx='thorn', eff=[['poison', 3, 0]]),
        _s('bramble_armour', 'Bramble Armour', 30, 18.0, 6, 'Armour of thorns: anyone close to you is cut.', t='buff', fx='thorn', self=[['resistance', 10, 1]],
           then=dict(t='zone', at='self', d=2, r=3, dur=8, fx='thorn')),
        _s('thorn_forest', 'Thorn Forest', 80, 24.0, 10, 'A forest of thorns erupts in eight directions.', t='wave', d=14, len=14, dirs=8, fx='thorn', eff=[['slowness', 3, 1]]),
    ],
    'ash': [
        _s('cinder_flick', 'Cinder Flick', 10, 0.6, 1, 'Two smouldering cinders.', t='bolt', d=4, n=2, spread=8, shape=0, speed=2.0, fire=2, fx='ash'),
        _s('ash_cloud', 'Ash Cloud', 26, 9.0, 3, 'A choking cloud of ash settles over your aim.', t='zone', d=1.5, r=5, dur=6, fx='ash', eff=[['blindness', 2, 0], ['wither', 2, 0]]),
        _s('rekindle', 'Rekindle', 32, 14.0, 6, 'Warm embers mend you and your allies.', t='heal', heal=7, r=7, regen=5, fx='ash'),
        _s('ashen_storm', 'Ashen Storm', 82, 24.0, 10, 'Burning ash rains over your aim.', t='rain', d=7, n=16, r=7, every=2, fire=3, fx='ash'),
    ],
})
ALTAR_WEIGHTS.update({'gravity': 4, 'moon': 4, 'thorn': 7, 'ash': 7})
AWAKENED.update({
    'gravity': _s('event_horizon', 'Event Horizon', 120, 40.0, 15, 'A black star swallows the battlefield, then bursts.', t='vortex', d=22, r=11, dur=4, fx='gravity',
                  then=dict(t='nova', d=12, r=11, kb=[2.0, 0.8], fx='gravity')),
    'moon': _s('full_moon_requiem', 'Full Moon Requiem', 115, 38.0, 15, 'The full moon rains silver light on everything around your aim.', t='rain', d=9, n=22, r=9, every=2, fx='moon', eff=[['blindness', 2, 0]]),
    'thorn': _s('crown_of_thorns', 'Crown of Thorns', 110, 38.0, 15, 'A crown of thorns rises around you, poisoning and slowing every foe inside.', t='zone', at='self', d=5, r=10, dur=8, fx='thorn', eff=[['poison', 2, 1], ['slowness', 2, 2]]),
    'ash': _s('ashfall_cataclysm', 'Ashfall Cataclysm', 120, 40.0, 15, 'Burning mountains of ash crash down around your aim.', t='meteor', d=16, n=6, r=8, aoe=3.5, fire=6, size=2, fx='ash'),
})
for _a in ('gravity', 'moon', 'thorn', 'ash'):
    SPELLS[_a].append(AWAKENED[_a])

# ----------------------------------------------------------------------------- companions
# Personalities: how a companion fights and talks. courage/aggro/keep shift its brain; xp/morale are multipliers.
PERSONALITIES = {
    'brave': dict(name='Brave', desc='First into every fight and never backs down.', courage=0.35, aggro=1.2, keep=0.8, xp=1.0, morale=1.0, pw=1.0,
                  lines={'kill': ['Is that all?', 'Who\'s next?'], 'low': ['Stand behind me, {p}!'], 'boss': ['A worthy foe! Let\'s go!'], 'idle': ['I could fight a dragon today.']}),
    'cautious': dict(name='Cautious', desc='Keeps its distance and falls back early - rarely gets hurt.', courage=-0.3, aggro=0.8, keep=1.5, xp=1.0, morale=1.0, pw=1.0,
                     lines={'kill': ['Safe... for now.'], 'low': ['{p}, pull back - now!'], 'boss': ['We should be careful with this one.'], 'idle': ['Did you hear something?']}),
    'loyal': dict(name='Loyal', desc='Sticks to your side and protects you before anything else.', courage=0.2, aggro=1.0, keep=1.0, xp=1.0, morale=1.1, pw=1.0, guard=True,
                  lines={'kill': ['For you, {p}.'], 'low': ['Nobody touches {p}!'], 'boss': ['I\'m with you, {p}. Always.'], 'idle': ['Wherever you go, I go.']}),
    'hothead': dict(name='Hothead', desc='Charges the strongest foe and hits harder, but takes risks.', courage=0.5, aggro=1.4, keep=0.6, xp=1.0, morale=0.9, pw=1.08,
                    lines={'kill': ['HA! Got it!', 'Too slow!'], 'low': ['Who did that?! I\'ll burn them!'], 'boss': ['That one\'s MINE!'], 'idle': ['I\'m bored. Let\'s find a fight.']}),
    'cheerful': dict(name='Cheerful', desc='Lifts the whole party\'s spirits - morale recovers faster around them.', courage=0.1, aggro=1.0, keep=1.0, xp=1.0, morale=1.6, pw=1.0,
                     lines={'kill': ['Yay! We did it!', 'Teamwork!'], 'low': ['Don\'t give up, {p}! I\'ve got you!'], 'boss': ['Big, scary... we\'ve got this!'], 'idle': ['What a lovely day!', 'Shall I sing something?']}),
    'scholar': dict(name='Scholar', desc='Studies every fight: learns 25% faster and picks spells more cleverly.', courage=0.0, aggro=1.0, keep=1.2, xp=1.25, morale=1.0, pw=1.0, skill=0.1,
                    lines={'kill': ['As predicted.', 'Fascinating technique.'], 'low': ['{p}, your vitals are failing - retreat!'], 'boss': ['I\'ve read about creatures like this...'], 'idle': ['Did you know mana flows like water?']}),
}
# Specialisations: chosen once a companion reaches level 10. 'mastery' arrives at level 20 (or through its second trial).
SPECS = {
    'vanguard': dict(name='Vanguard', role='brawler', desc='A front-line guardian: resistance in battle, taunts foes onto itself and shield-bashes them.',
                     skills='Taunt (pull every nearby foe and boss onto itself), Shield Bash (a stunning blow up close)',
                     mastery='Bulwark: Resistance II while taunting, and Taunt reaches twice as far.'),
    'arcanist': dict(name='Arcanist', role='striker', desc='A spell master: +15% spell power, cooldowns 15% shorter, and an arcane barrage.',
                     skills='Arcane Barrage (five homing darts of its own magic)',
                     mastery='Spell Echo: a quarter of its spells are cast again at half power.'),
    'warden': dict(name='Warden', role='support', desc='A protector: shields the party, cleanses curses, cuts down arrows aimed at you and revives fallen friends quickly.',
                   skills='Aegis (absorption and resistance for you and the party), Cleanse (removes poison, wither, slowness, blindness - and breaks mind control)',
                   mastery='Sanctuary: Aegis also heals and cleanses.'),
    'ranger': dict(name='Ranger', role='striker', desc='A sharpshooter: fights from 10-16 blocks away, fires piercing volleys and marks targets for the party.',
                   skills='Volley (three piercing long-range bolts), Mark (the party deals +20% damage to the target)',
                   mastery='Hawk Eye: marked foes take +35% damage, and Volley fires five bolts.'),
}
SPEC_LEVEL = 10
# Party tactics, chosen with the whistle
TACTICS_PARTY = {
    'balanced': ('Balanced', 'Each companion fights its own way.'),
    'focus': ('Focus fire', 'Everyone attacks the same foe - your target, or the weakest enemy near you.'),
    'protect': ('Protect me', 'Stay within six blocks of you and only fight what comes close to you.'),
    'spread': ('Spread out', 'Keep apart from each other - best against big area attacks.'),
    'kite': ('Hit and run', 'Strike, then back off; ranged companions keep their distance.'),
}
# Mood: morale (0-100) and fatigue (0-100)
MOOD = dict(start_morale=70, inspired=80, shaken=30, exhausted=80)
# Personal trials: offered at bond 'Friend' (stage 1: awakens their fifth spell) and 'Sworn Ally' (stage 2: mastery)
TRIALS = [
    ('kill', 'monster', 25, 'Help me prove myself - defeat 25 monsters with me at your side.'),
    ('kill', 'bc_devil', 10, 'Devils burned my village. Help me banish 10 of them.'),
    ('kill', 'bc_pirate', 10, 'Sea raiders took everything my family had. Ten of them will answer for it.'),
    ('kill', 'bc:rogue_mage', 4, 'A rogue mage stole my master\'s grimoire. Help me bring four rogues to justice.'),
    ('boss', '', 1, 'I want to stand against a great foe with you. Any of the giants will do.'),
    ('cast', '', 60, 'Train with me: cast 60 spells while I watch your back.'),
    ('kill', 'undead', 20, 'The restless dead frighten me. Help me face 20 of them.'),
]
TRIAL_TITLES = ['the Unbroken', 'the Steadfast', 'the Bright', 'the Relentless', 'Stormheart', 'the Unyielding', 'Dawnbringer', 'the Watchful']
# Roster & expeditions: (id, name, real minutes, min level, danger 1-5, description, loot [(item, lo, hi, chance)], xp)
RESERVE_MAX = 6
EXPEDITIONS = [
    ('patrol', 'Border Patrol', 8, 1, 1, 'Walk the kingdom border and chase off bandits.', [('bc:doubloon', 10, 25, 1.0), ('bc:mana_crystal', 1, 3, 0.8), ('minecraft:bread', 2, 5, 0.6)], 120),
    ('escort', 'Merchant Escort', 15, 4, 2, 'Guard a merchant caravan through the hills.', [('bc:doubloon', 30, 60, 1.0), ('bc:mana_cookie', 2, 4, 0.7), ('bc:treasure_map', 1, 1, 0.25)], 220),
    ('ruins', 'Ancient Ruins', 20, 6, 2, 'Search a ruined temple for lost grimoire pages.', [('bc:ancient_page', 1, 3, 0.9), ('bc:mana_crystal', 2, 5, 0.8), ('minecraft:gold_ingot', 2, 5, 0.6), ('robe', 1, 1, 0.08)], 320),
    ('devil_hunt', 'Devil Hunt', 30, 10, 3, 'Track down a nest of devils and seal it.', [('bc:mana_crystal', 4, 8, 1.0), ('bc:devil_heart', 1, 1, 0.2), ('bc:ancient_page', 1, 2, 0.6), ('amulet', 1, 1, 0.15)], 600),
    ('witch_woods', 'The Witch Woods', 40, 14, 4, 'Brave the woods where the Witch Sisters were last seen.', [('bc:mana_crystal', 6, 10, 1.0), ('amulet', 1, 1, 0.35), ('minecraft:blaze_rod', 2, 5, 0.6), ('bc:clover_leaf', 1, 1, 0.15)], 900),
    ('graveyard', "Dragon's Graveyard", 60, 18, 5, 'Climb into the bone valley where dragons go to die.', [('minecraft:bone_block', 6, 14, 1.0), ('minecraft:netherite_scrap', 1, 2, 0.4), ('bc:clover_charm', 1, 1, 0.08), ('amulet', 1, 1, 0.4), ('bc:clover_leaf', 1, 1, 0.25)], 1400),
]
# Things to say when you talk to them
HOMETOWNS = ['Willowmere', 'Ashford', 'Saltcrest', 'Thornvale', 'Brightwater', 'Kestrel Point', 'Duskholm', 'Emberglen', 'Frostmere', 'Oakhollow']
DREAMS = ['to lead my own squad one day', 'to protect my little brother', 'to master every page of my grimoire', 'to see the sea beyond the kingdom',
          'to become the strongest mage in the kingdom', 'to pay back the knight who saved my life', 'to write a book about every kind of magic', 'to never lose a friend again']
TIPS = ['Sneak and use the Companion Whistle while looking at a foe - the whole party will attack it.',
        'A Warden companion can break the Soul Puppeteer\'s strings with Cleanse.',
        'Spread out when a boss draws warning circles - we can\'t all dodge in the same direction.',
        'Field Rations take the weariness out of a long day of fighting.',
        'Rest near a camp and our spirits recover faster.',
        'Mana Cookies are the best gift. Just saying.',
        'At level 10 we can specialise: Vanguard, Arcanist, Warden or Ranger.',
        'A Squad Banner lets you keep more of us in reserve and send us on expeditions.',
        'Hit the Training Dummy with us around and we\'ll practise on it too.',
        'Union Magic needs a Soulbound companion. Keep giving gifts!',
        'Flying a broom? We\'ll grab ours and follow you.',
        'If one of us falls, stand by the glowing clover and we\'ll pull them back up.']
COMPANION_LINES.update({
    'camp': ['Finally, a rest.', 'I\'ll get the fire going.', 'My feet thank you, {p}.'],
    'watch': ['I\'ll keep watch tonight.', 'Sleep, {p}. I\'ve got the first watch.'],
    'alarm': ['Movement in the dark - get up!', 'We\'ve got company!', 'Something\'s coming, {p}!'],
    'revive': ['Hold on - I\'ve got you!', 'Come on, get up!', 'Not today. Up you get.'],
    'revived': ['Thanks... I owe you one.', 'I thought that was the end of me.', 'Back in the fight!'],
    'taunt': ['Over here, you brute!', 'Face ME!', 'Come on then!'],
    'combo': ['Now! Hit it while it\'s stuck!', 'It\'s bound - finish it!', 'Combo!'],
    'mark': ['Target marked!', 'Hit the marked one!'],
    'aegis': ['Shields up!', 'I\'ll protect you all!'],
    'controlled': ['My body... won\'t listen...', 'Strings... in my head...', 'Run, {p}! I can\'t stop myself!'],
    'freed': ['I\'m free! Sorry, {p}...', 'The strings are gone - let\'s get that puppeteer!'],
    'tired': ['I need a rest...', 'My mana feels so heavy.'],
    'inspired': ['I feel like I could take on anything!', 'Nothing can stop us now!'],
    'broom': ['Brooms out!', 'Race you, {p}!', 'I love flying!'],
    'trial': ['{p}, can I ask you something? There\'s a trial I have to face...'],
    'trial_done': ['We did it! I can feel my grimoire awakening!', 'Thank you, {p}. I won\'t forget this.'],
    'spar_win': ['Good match!', 'Better luck next time!'],
    'spar_lose': ['You got me this time.', 'I need more training...'],
    'expedition': ['We\'re back! You won\'t believe what we found.', 'The road was long, but we made it.'],
})
BANTER = [
    ('Do you ever wonder what the Wizard King eats for breakfast?', 'Probably mana crystals. Raw.'),
    ('Your spell nearly singed my cape back there.', 'Your cape was in the way of my spell.'),
    ('I counted. I got more kills than you today.', 'You counted the imps twice.'),
    ('When this is over, I\'m sleeping for a week.', 'You said that last week.'),
    ('Nice work back there.', 'You too. Don\'t let it go to your head.'),
    ('Is it just me, or is {p} getting stronger?', 'It\'s not just you.'),
    ('I miss home sometimes.', 'Me too. But this squad is a kind of home now, isn\'t it?'),
    ('Race you to the next hill!', 'You\'re on!'),
    ('What\'s the scariest thing you\'ve ever fought?', 'That cooking you made last night.'),
    ('If I fall, tell my grimoire I loved it.', 'You\'re not falling on my watch.'),
]
# New items
PUPPET_ITEMS = {
    'squad_banner': 'Squad Banner', 'training_dummy': 'Training Dummy', 'clover_leaf': 'Clover Leaf of Return', 'field_rations': 'Field Rations',
    'companion_tome': 'Companion Tome', 'cursed_spool': 'Cursed Spool',
}
MERCHANT += [('bc:field_rations', 4, 40, 'Field Rations x4'), ('bc:clover_leaf', 1, 260, 'Clover Leaf of Return'), ('bc:companion_tome', 1, 150, 'Companion Tome')]

# ======================================================================================
# v0.6.0: a new move for every grimoire (level 12) and every Abyss Fruit (Will 2), and
# companions who fight with a grimoire and a fruit
# ======================================================================================
NEW_MOVE_LEVEL = 12
NEW_FRUIT_WILL = 2
COMPANION_FRUIT_LEVEL = 10   # companions use their fruit's fourth move from this level
NEW_MOVES = {
    'wind': _s('vacuum_cutter', 'Vacuum Cutter', 60, 16.0, 12, 'Three lanes of vacuum blades rip along the ground.', t='wave', d=12, len=16, lanes=3, fx='wind', kb=[1.2, 0.4]),
    'flame': _s('flame_emperor_ring', "Flame Emperor's Ring", 64, 18.0, 12, 'Two rings of fireballs burst out from you.', t='radial', d=8, n=16, rings=2, shape=0, speed=1.6, fire=4, fx='flame'),
    'water': _s('riptide_whirlpool', 'Riptide Whirlpool', 60, 18.0, 12, 'A whirlpool drags foes into its crushing heart.', t='vortex', d=14, r=7, dur=3, fx='water'),
    'lightning': _s('chain_storm', 'Chain Storm', 62, 16.0, 12, 'Lightning leaps from foe to foe near your aim.', t='strikes', d=12, n=6, r=12, fx='lightning', eff=[['slowness', 2, 1]]),
    'light': _s('sacred_cage', 'Sacred Cage', 64, 18.0, 12, 'Cages of light bind foes near your aim, then burst.', t='prison', d=12, r=4, dur=3, fx='light', eff=[['blindness', 2, 0]]),
    'dark': _s('night_fangs', 'Night Fangs', 62, 16.0, 12, 'Fangs of darkness tear out in four directions.', t='wave', d=12, len=14, dirs=4, fx='dark', eff=[['weakness', 4, 1]]),
    'ice': _s('frost_barrage', 'Frost Barrage', 60, 18.0, 12, 'Icicles rain over your aim.', t='rain', d=7, n=16, r=6, every=2, fx='ice', eff=[['slowness', 2, 1]]),
    'anti': _s('black_hurricane', 'Black Hurricane', 0, 14.0, 12, 'Spin with your swords: cut every spell around you out of the air, slash and seal everyone close. Costs 25% of the Anti-Magic gauge.'),
    'spatial': _s('folding_strike', 'Folding Strike', 58, 14.0, 12, 'Fold space to appear among your foes and blast them apart.', t='leap', mode='blink', d=10, dist=10, fx='spatial',
                  then=dict(t='nova', d=10, r=4, kb=[1.4, 0.5], fx='spatial')),
    'earth': _s('stone_fist_rain', 'Stone Fist Rain', 62, 18.0, 12, 'Giant stone fists fall from the sky around your aim.', t='meteor', d=12, n=4, r=6, aoe=3, size=2, fx='earth'),
    'steel': _s('blade_cage', 'Blade Cage', 60, 18.0, 12, 'A cage of swords closes around foes near your aim.', t='prison', d=12, r=4, dur=3, fx='metal'),
    'mirror': _s('prism_beam', 'Prism Beam', 60, 14.0, 12, 'A beam of light bounced through a hundred mirrors.', t='beam', d=14, range=24, width=1.2, fx='mirror'),
    'sand': _s('sand_spear_barrage', 'Sand Spear Barrage', 58, 14.0, 12, 'Six spears of packed sand.', t='bolt', d=6, n=6, spread=24, shape=3, speed=2.4, pierce=1, fx='sand'),
    'bubble': _s('bubble_armour', 'Bubble Armour', 56, 22.0, 12, 'Bubbles armour you and your allies.', t='buff', allies=8, fx='bubble', self=[['absorption', 10, 1], ['resistance', 8, 0]]),
    'plant': _s('strangler_vines', 'Strangler Vines', 60, 16.0, 12, 'Vines erupt and strangle everything near your aim.', t='zone', d=3, r=5, dur=6, pull=0.3, fx='leaf', eff=[['slowness', 2, 2], ['poison', 2, 0]]),
    'poison': _s('toxic_rain', 'Toxic Rain', 60, 16.0, 12, 'Venom rains down over your aim.', t='rain', d=4, n=16, r=6, every=2, fx='poison', eff=[['poison', 3, 1]]),
    'blood': _s('crimson_scythe', 'Crimson Scythe', 50, 12.0, 12, 'A scythe of blood sweeps in front of you and feeds you.', t='nova', at='front', d=12, r=5, ls=0.4, kb=[1.0, 0.3], fx='blood'),
    'star': _s('polaris_beam', 'Polaris Beam', 64, 16.0, 12, 'A beam of starlight from the north star.', t='beam', d=16, range=28, width=1.4, fx='star'),
    'sound': _s('echo_field', 'Echo Field', 58, 16.0, 12, 'A field of endless echoes that dizzies and weakens foes near your aim.', t='zone', d=3, r=6, dur=6, fx='sound', eff=[['nausea', 3, 0], ['weakness', 3, 1]]),
    'mist': _s('mist_bind', 'Mist Bind', 56, 16.0, 12, 'Thick mist solidifies around foes near your aim.', t='prison', d=6, r=4, dur=4, fx='mist', eff=[['blindness', 3, 0]]),
    'crystal': _s('crystal_prison', 'Crystal Prison', 62, 18.0, 12, 'Encase foes in crystal, then shatter it.', t='prison', d=12, r=3.5, dur=3, fx='crystal'),
    'bone': _s('bone_rain', 'Bone Rain', 60, 16.0, 12, 'A storm of bone spears falls over your aim.', t='rain', d=8, n=14, r=6, every=2, fx='bone'),
    'magma': _s('magma_serpent', 'Magma Serpent', 66, 18.0, 12, 'A serpent of magma burns through everything in its path.', t='bolt', d=14, shape=2, size=3, speed=1.3, pierce=5, fire=5, fx='magma'),
    'time': _s('quickened_hour', 'Quickened Hour', 60, 24.0, 12, 'Speed up time for you and your allies.', t='buff', allies=8, fx='time', self=[['speed', 8, 2], ['haste', 8, 1], ['jump_boost', 8, 1]]),
    'cotton': _s('cotton_cannon', 'Cotton Cannon', 54, 12.0, 12, 'A huge ball of packed cotton that bowls foes over.', t='bolt', d=8, size=3, shape=0, speed=1.2, aoe=3.5, kb=[1.6, 0.8], fx='cotton', eff=[['slowness', 3, 1]]),
    'paper': _s('paper_prison', 'Paper Prison', 56, 16.0, 12, 'Sheets of paper wrap foes near your aim into tight bundles.', t='prison', d=8, r=4, dur=4, fx='paper'),
    'smoke': _s('smog_vortex', 'Smog Vortex', 58, 16.0, 12, 'A choking whirl of smoke drags foes together.', t='vortex', d=10, r=6, dur=3, fx='smoke', eff=[['blindness', 2, 0]]),
    'glass': _s('glass_lances', 'Glass Lances', 60, 16.0, 12, 'Glass spikes erupt in three directions.', t='wave', d=12, len=14, dirs=3, fx='glass'),
    'gold': _s('golden_barrage', 'Golden Barrage', 62, 16.0, 12, 'Two rings of heavy gold coins burst out from you.', t='radial', d=6, n=20, rings=2, shape=0, speed=1.8, fx='gold'),
    'beast': _s('beast_spirit_pounce', 'Beast Spirit Pounce', 56, 12.0, 12, 'Leap like a beast and crash down on your target.', t='dive', d=14, r=4, fx='beast'),
    'spirit': _s('soul_lance', 'Soul Lance', 60, 14.0, 12, 'A lance of spirit light that feeds on the life it pierces.', t='beam', d=13, range=24, width=1.0, ls=0.3, fx='spirit'),
    'rune': _s('rune_barrier', 'Rune Barrier', 60, 24.0, 12, 'A barrier of runes guards you and your allies.', t='buff', allies=8, fx='rune', self=[['resistance', 10, 1], ['absorption', 10, 1]]),
    'gravity': _s('meteor_pull', 'Meteor Pull', 64, 18.0, 12, 'Gravity drags rocks down from the sky around your aim.', t='meteor', d=14, n=3, r=5, aoe=3.5, size=2, fx='gravity'),
    'moon': _s('moonlit_prison', 'Moonlit Prison', 60, 18.0, 12, 'Moonlight freezes foes near your aim in place.', t='prison', d=10, r=4, dur=3, fx='moon', eff=[['blindness', 2, 0]]),
    'thorn': _s('thorn_barrage', 'Thorn Barrage', 58, 16.0, 12, 'Two rings of poisoned thorns burst out from you.', t='radial', d=5, n=24, rings=2, shape=3, speed=2.0, fx='thorn', eff=[['poison', 2, 0]]),
    'ash': _s('ash_phoenix', 'Ash Phoenix', 58, 14.0, 12, 'Burst into burning ash and crash down on your foes.', t='dive', d=14, r=4, fire=4, fx='ash'),
}
for _a, _sp in NEW_MOVES.items():
    _lst = SPELLS[_a]
    _i = next((i for i, x in enumerate(_lst) if x[4] >= 15), len(_lst))
    _lst.insert(_i, _sp)

# (id, name, cooldown, description, engine recipe, Will level)
NEW_FRUIT_MOVES = {
    'ember': ('ember_storm', 'Ember Storm', 16.0, 'Burning embers rain over your aim.', dict(t='rain', d=6, n=14, r=6, every=2, fire=4, fx='flame')),
    'stone': ('landslide', 'Landslide', 16.0, 'Three lanes of crashing rock.', dict(t='wave', d=12, len=14, lanes=3, fx='earth', kb=[1.2, 0.5])),
    'gravity': ('black_star', 'Black Star', 18.0, 'A tiny black star swallows everything around it.', dict(t='vortex', d=16, r=7, dur=3, fx='gravity')),
    'shadow': ('night_parade', 'Night Parade', 16.0, 'Shadows rise under every foe near your aim.', dict(t='strikes', d=10, n=6, r=12, fx='dark', eff=[['blindness', 2, 0]])),
    'bloom': ('pollen_storm', 'Pollen Storm', 16.0, 'A storm of stinging pollen over your aim.', dict(t='zone', d=2, r=6, dur=6, fx='leaf', eff=[['poison', 2, 0], ['slowness', 2, 1]])),
    'quicksilver': ('mercury_rain', 'Mercury Rain', 16.0, 'Blades of liquid metal rain down.', dict(t='rain', d=7, n=16, r=6, every=2, fx='metal')),
    'frost': ('glacier_crash', 'Glacier Crash', 18.0, 'Blocks of glacier ice crash down around your aim.', dict(t='meteor', d=13, n=3, r=5, aoe=3.5, size=2, fx='ice', eff=[['slowness', 3, 2]])),
    'barrier': ('barrier_prison', 'Barrier Prison', 16.0, 'Seal foes near your aim inside barrier cubes.', dict(t='prison', d=8, r=4, dur=4, fx='glass')),
    'wolf': ('moon_fang', 'Moon Fang', 14.0, 'Three savage bites in a row.', dict(t='repeat', n=3, every=6, fx='beast', spec=dict(t='nova', at='front', d=8, r=3, kb=[0.6, 0.2], fx='beast'))),
    'hawk': ('gale_feathers', 'Gale Feathers', 14.0, 'A ring of razor feathers bursts out from you.', dict(t='radial', d=6, n=16, shape=2, speed=2.0, fx='wind')),
    'lava': ('lava_serpent', 'Lava Serpent', 18.0, 'A serpent of lava burns through everything in its path.', dict(t='bolt', d=13, shape=2, size=3, speed=1.3, pierce=5, fire=5, fx='magma')),
    'ash': ('cinder_phoenix', 'Cinder Phoenix', 16.0, 'Burst into cinders and crash down on your foes.', dict(t='dive', d=14, r=4, fire=4, fx='ash')),
    'prism': ('spectrum_prison', 'Spectrum Prison', 16.0, 'Foes near your aim are trapped in prisms of light.', dict(t='prison', d=9, r=4, dur=3, fx='crystal')),
    'bounce': ('rubber_barrage', 'Rubber Barrage', 12.0, 'Six bouncing balls that knock foes flying.', dict(t='bolt', d=4, n=6, spread=30, shape=0, size=1, speed=1.8, kb=[1.2, 0.6], fx='gold')),
    'blast': ('chain_blast', 'Chain Blast', 16.0, 'Explosions ripple across every foe near your aim.', dict(t='strikes', d=12, n=6, r=10, fx='flame')),
    'acid': ('acid_flood', 'Acid Flood', 16.0, 'Waves of acid surge out in six directions.', dict(t='wave', d=10, len=14, dirs=6, fx='acid', eff=[['poison', 2, 1]])),
    'lodestone': ('iron_maiden', 'Iron Maiden', 18.0, 'Pull scrap metal into a crushing cage around foes near your aim.', dict(t='prison', d=12, r=3.5, dur=3, fx='metal')),
    'cloud': ('hailstorm', 'Hailstorm', 16.0, 'A thundercloud pours hail over your aim.', dict(t='rain', d=6, n=18, r=7, every=2, fx='ice')),
    'ink': ('ink_prison', 'Ink Prison', 16.0, 'Drown foes near your aim in a bubble of ink.', dict(t='prison', d=7, r=4, dur=4, fx='ink', eff=[['blindness', 3, 0]])),
    'bear': ('avalanche_charge', 'Avalanche Charge', 14.0, 'Charge like an avalanche, then slam the ground.', dict(t='leap', mode='dash', d=10, dist=10, fx='beast', kb=[1.6, 0.5],
                                                                                                                     then=dict(t='nova', d=8, r=4, kb=[1.4, 0.6], fx='earth'))),
    'tiger': ('tiger_strike', 'Tiger Strike', 14.0, 'Pounce high and land claws-first on your prey.', dict(t='dive', d=14, r=3.5, fx='beast')),
    'wyvern': ('dragon_rain', 'Dragon Rain', 18.0, 'Fireballs rain from the sky around your aim.', dict(t='meteor', d=12, n=4, r=6, aoe=3, fire=4, size=1, fx='flame')),
    'spore': ('fairy_ring', 'Fairy Ring', 16.0, 'A ring of toxic mushrooms bursts up around you.', dict(t='zone', at='self', d=3, r=6, dur=6, fx='poison', eff=[['poison', 2, 1], ['slowness', 2, 0]])),
    'thread': ('thousand_threads', 'Thousand Threads', 16.0, 'Two rings of razor threads lash out from you.', dict(t='radial', d=5, n=24, rings=2, shape=3, speed=2.2, fx='paper')),
    'slime': ('slime_rain', 'Slime Rain', 16.0, 'Sticky slime rains over your aim.', dict(t='rain', d=5, n=14, r=6, every=2, fx='acid', eff=[['slowness', 3, 2]])),
    'chain': ('chain_storm_fruit', 'Chain Storm', 16.0, 'Chains whip down on every foe near your aim.', dict(t='strikes', d=10, n=6, r=10, fx='metal', eff=[['slowness', 2, 1]])),
    'lion': ('kings_charge', "King's Charge", 14.0, 'A royal charge that ends in a thunderous roar.', dict(t='leap', mode='dash', d=11, dist=12, fx='beast', kb=[1.6, 0.5],
                                                                                                         then=dict(t='nova', d=6, r=5, kb=[1.8, 0.6], fx='beast', eff=[['weakness', 4, 1]]))),
    'shark': ('feeding_frenzy', 'Feeding Frenzy', 14.0, 'Four bites in a row, each one feeding you.', dict(t='repeat', n=4, every=6, fx='water', spec=dict(t='nova', at='front', d=7, r=3, ls=0.25, fx='water'))),
    'phoenix': ('phoenix_halo', 'Phoenix Halo', 22.0, 'A halo of healing fire for you and your allies, and a burst of flame for your foes.', dict(t='buff', allies=8, fx='flame',
                                                                                                         self=[['regeneration', 8, 1], ['fire_resistance', 12, 0]], then=dict(t='nova', d=8, r=5, fire=4, fx='flame'))),
    'spider': ('venom_rain', 'Venom Rain', 16.0, 'Venom drips from webs strung over your aim.', dict(t='rain', d=4, n=14, r=6, every=2, fx='poison', eff=[['poison', 3, 1]])),
}
for _f, (_id, _n, _cd, _desc, _spec) in NEW_FRUIT_MOVES.items():
    FRUITS[_f]['abilities'].append((_id, _n, _cd, _desc, _spec, NEW_FRUIT_WILL))

# ======================================================================================
# v0.7.0: the Bandit Brotherhood, Shadow Assassins, Cultists, the Hive, three new bosses,
# warband tactics and a new event director
# ======================================================================================
ENEMY_KITS.update({
    'bc:bandit': dict(src='a:steel', kit=[dict(t='nova', at='front', d=6, r=2.6, kb=[0.9, 0.3], fx='metal'),
                                          dict(t='leap', d=6, dist=7, mode='dash', fx='metal')]),
    'bc:bandit_archer': dict(src='a:wind', kit=[dict(t='bolt', d=6, shape=3, speed=2.8, fx='wind'),
                                                dict(t='bolt', d=4, n=3, spread=10, shape=3, speed=2.6, fx='wind')]),
    'bc:bandit_thief': dict(src='a:smoke', kit=[dict(t='bolt', d=3, n=2, spread=8, shape=2, speed=2.4, fx='metal')]),
    'bc:shadow_assassin': dict(src='a:dark', kit=[dict(t='bolt', d=5, n=3, spread=12, shape=2, speed=2.6, fx='dark', eff=[['weakness', 3, 0]]),
                                                  dict(t='nova', at='front', d=8, r=2.6, fx='dark')]),
    'bc:cultist': dict(src='a:blood', kit=[dict(t='bolt', d=5, shape=0, speed=1.6, ls=0.3, fx='blood'),
                                           dict(t='heal', heal=6, r=8, regen=3, fx='blood'),
                                           dict(t='prison', d=3, r=2.5, dur=2, fx='dark')]),
    'bc:hive_drone': dict(src='f:acid', kit=[dict(t='bolt', d=4, shape=0, size=1, speed=1.6, fx='acid', eff=[['poison', 2, 0]]),
                                             dict(t='leap', d=5, dist=6, mode='dash', fx='acid')]),
})
FACTIONS['bandits'] = dict(name='Bandit Brotherhood', mc='§6', units=['bc:bandit', 'bc:bandit', 'bc:bandit_archer', 'bc:bandit_thief'], leader='bc:bandit')
FACTIONS['hive'] = dict(name='The Hive', mc='§e', units=['bc:hive_drone'], leader='bc:hive_drone')
V7_ITEMS = {
    'bandit_crown': ('§6Bandit\'s Crown', 'Challenge the Bandit King'),
    'forbidden_tome': ('§5Forbidden Tome', 'Wake the Grimoire Devourer'),
    'royal_jelly': ('§eRoyal Jelly', 'Call the Hive Queen'),
}

# ======================================================================================
# v0.7.5: elite enemies, lairs (bandit hideouts, hive nests, cultist shrines), potions,
# elixirs, smoke bombs, spell scrolls and feats
# ======================================================================================
# Elite affixes: id -> (name, colour, description)
ELITE_AFFIXES = {
    'vampiric': ('Vampiric', '§4', 'heals itself for 30% of the damage it deals'),
    'shielded': ('Shielded', '§b', 'a mana shield halves spell damage until three blows break it'),
    'swift': ('Swift', '§a', 'fast, skilled and hard to hit'),
    'explosive': ('Explosive', '§c', 'bursts one second after it falls - get clear!'),
    'summoner': ('Summoner', '§5', 'calls two lesser copies of itself every 15 seconds'),
    'arcane': ('Arcane', '§d', 'casts a spell from a random grimoire every 8 seconds'),
    'frenzied': ('Frenzied', '§6', 'below half health it gains Strength II and Speed'),
}
ELITE_CHANCE = 0.06
# Consumables: id -> (name, description)
CONSUMABLES = {
    'mana_potion': ('§bMana Potion', 'Restores 60 mana (or 30% of the Anti-Magic gauge).'),
    'greater_mana_potion': ('§9Greater Mana Potion', 'Restores all your mana and grants Regeneration for 10 s.'),
    'elixir_iron': ('§7Elixir of Iron', 'Resistance II and Absorption II for 60 s.'),
    'elixir_haste': ('§aElixir of Haste', 'Speed and 25% shorter spell cooldowns for 60 s.'),
    'smoke_bomb': ('§8Smoke Bomb', 'Blinds foes around you and hides you in smoke for 4 s.'),
    'spell_scroll': ('§eSpell Scroll', 'Read it to cast the spell written on it - from any grimoire, even without one of your own.'),
}
# Feats: (id, name, description, counter, goal, stars, doubloons, title)
FEATS = [
    ('first_blood', 'First Blood', 'Defeat your first monster.', 'kills', 1, 0, 10, 'the Rookie'),
    ('hunter', 'Monster Hunter', 'Defeat 100 hostile creatures.', 'kills', 100, 1, 50, 'the Hunter'),
    ('scourge', 'Scourge of Monsters', 'Defeat 1000 hostile creatures.', 'kills', 1000, 3, 300, 'the Scourge'),
    ('giant_slayer', 'Giant Slayer', 'Defeat a boss.', 'bosses', 1, 1, 60, 'Giant Slayer'),
    ('legend', 'Legend', 'Defeat 10 bosses.', 'bosses', 10, 3, 300, 'the Legend'),
    ('bane', 'Bane of Giants', 'Defeat 8 different bosses.', 'boss_kinds', 8, 3, 400, 'Bane of Giants'),
    ('spellslinger', 'Spellslinger', 'Cast 500 spells or fruit powers.', 'casts', 500, 1, 60, 'the Spellslinger'),
    ('archmage', 'Archmage', 'Cast 5000 spells or fruit powers.', 'casts', 5000, 3, 300, 'the Archmage'),
    ('seasoned', 'Seasoned Knight', 'Reach magic level 10.', 'level', 10, 1, 80, 'the Seasoned'),
    ('grand_knight', 'Grand Magic Knight', 'Reach magic level 20.', 'level', 20, 3, 300, 'Grand Magic Knight'),
    ('captain', 'Squad Captain', 'Lead four companions at once.', 'party', 4, 1, 80, 'Squad Captain'),
    ('soulbound', 'Soulbound', 'Reach Soulbound with a companion.', 'soulbound', 1, 2, 150, 'the Soulbound'),
    ('reliable', 'Reliable', 'Complete 10 missions.', 'missions', 10, 1, 80, 'the Reliable'),
    ('hero', 'Hero of the Kingdom', 'Complete 50 missions.', 'missions', 50, 3, 300, 'Hero of the Kingdom'),
    ('defender', 'Defender', 'Win 10 events (raids, rituals, hives...).', 'events', 10, 2, 150, 'the Defender'),
    ('elite_hunter', 'Elite Hunter', 'Defeat 10 elite enemies.', 'elites', 10, 2, 150, 'Elite Hunter'),
    ('not_my_purse', 'Not My Purse', 'Catch a thief.', 'thieves', 1, 1, 40, 'the Vigilant'),
    ('exterminator', 'Exterminator', 'Smash 25 hive eggs.', 'eggs', 25, 1, 80, 'the Exterminator'),
    ('scroll_scholar', 'Scroll Scholar', 'Read 10 spell scrolls.', 'scrolls', 10, 1, 60, 'the Scholar'),
    ('sea_cursed', 'Cursed by the Sea', 'Eat an Abyss Fruit.', 'fruit', 1, 0, 30, 'Sea-Cursed'),
    ('sky_rider', 'Sky Rider', 'Fly a magic broom.', 'broom', 1, 0, 30, 'Sky Rider'),
    ('lair_raider', 'Lair Raider', 'Loot 3 lairs (hideouts, nests, shrines).', 'lairs', 3, 2, 120, 'the Raider'),
]
MERCHANT += [('bc:mana_potion', 3, 45, 'Mana Potions x3'), ('bc:elixir_iron', 1, 60, 'Elixir of Iron'), ('bc:smoke_bomb', 3, 30, 'Smoke Bombs x3'),
             ('bc:spell_scroll', 1, 70, 'Spell Scroll')]

# ======================================================================================
# v0.8.0: armour - eight sets of four pieces with set bonuses, materials dropped by the foes that suit them,
# runes, reinforcement and squad mantles at the Magic Forge.
# ======================================================================================
ARMOR_SLOTS = ('head', 'chest', 'legs', 'feet')
# piece share of a set's durability (like vanilla armour)
ARMOR_DUR = {'head': 0.69, 'chest': 1.0, 'legs': 0.94, 'feet': 0.81}
# Armour sets: id -> dict(name, pieces (helmet, chest, legs, boots names), prot (h, c, l, b), dur (chest durability),
#   material, style (for the models), colours, stars (rank needed to forge), b2/b4 (set bonus texts; implemented in scripts))
ARMOR_SETS = {
    'manasteel': dict(name='Mana-Steel', pieces=('Mana-Steel Helm', 'Mana-Steel Cuirass', 'Mana-Steel Greaves', 'Mana-Steel Boots'),
                      prot=(2, 6, 5, 2), dur=300, material='mana_steel_ingot', stars=0, mc='§b',
                      style='knight', base='steel', accent='water', glow='7cc8ff',
                      b2='+25 max mana', b4='+25% mana regeneration, and spells cost 10% less mana'),
    'royal': dict(name='Royal Knight', pieces=('Royal Knight Helm', 'Royal Knight Plate', 'Royal Knight Tassets', 'Royal Knight Sabatons'),
                  prot=(3, 8, 6, 3), dur=460, material='mana_steel_ingot', stars=8, mc='§e',
                  style='royal', base='white_cloth', accent='gold', glow='ffe58a',
                  b2='+10% spell power',
                  b4='Royal Aegis: falling below 30% health grants Absorption III and Resistance II for 6 s (once a minute); companions within 16 blocks fight 10% harder'),
    'devilhide': dict(name='Devilhide', pieces=('Horned Devilhide Hood', 'Devilhide Jerkin', 'Devilhide Breeches', 'Devilhide Boots'),
                      prot=(3, 7, 6, 3), dur=400, material='devil_hide', stars=0, mc='§4',
                      style='devil', base='devil_skin', accent='anti', glow='ff4a4a',
                      b2='Fire Resistance',
                      b4='Your spells heal you for 8% of the damage they deal, and hit 20% harder while you are below 30% health'),
    'abyssal': dict(name='Abyssal Scale', pieces=('Abyssal Scale Crown', 'Abyssal Scale Mail', 'Abyssal Scale Leggings', 'Abyssal Scale Treads'),
                    prot=(3, 7, 5, 3), dur=380, material='leviathan_scale', stars=0, mc='§3',
                    style='abyssal', base='aqua_cloth', accent='water', glow='7cf0ff',
                    b2='Water Breathing, and Conduit Power while in water',
                    b4='The sea no longer drains Abyss Fruit users, and fruit powers recharge 15% faster'),
    'shadow': dict(name='Shadowweave', pieces=('Shadowweave Cowl', 'Shadowweave Vest', 'Shadowweave Trousers', 'Shadowweave Wraps'),
                   prot=(2, 4, 3, 2), dur=240, material='shadow_silk', stars=0, mc='§8',
                   style='shadow', base='black_cloth', accent='purple_cloth', glow='a060ff',
                   b2='Speed I',
                   b4='Evasion: a 20% chance to shrug off a melee blow; sneak still for 2 s to vanish, and your first blow from hiding deals double damage'),
    'chitin': dict(name='Hive Chitin', pieces=('Chitin Helm', 'Chitin Carapace', 'Chitin Leg Plates', 'Chitin Boots'),
                   prot=(2, 6, 5, 2), dur=340, material='chitin_plate', stars=0, mc='§6',
                   style='chitin', base='leather', accent='gold', glow='ffc030',
                   b2='Immune to poison (the Hive\'s acid included)',
                   b4='Barbed: melee attackers take 3 damage and are poisoned; Regeneration I while you are below half health'),
    'runeplate': dict(name='Runeplate', pieces=('Runeplate Greathelm', 'Runeplate Breastplate', 'Runeplate Cuisses', 'Runeplate Stompers'),
                      prot=(3, 8, 6, 3), dur=560, material='rune_shard', stars=15, mc='§9',
                      style='rune', base='stone', accent='mossstone', glow='60e0ff',
                      b2='Explosions and falls hurt you 40% less',
                      b4='Resistance I; spells hurt you 20% less; when struck, a 15% chance of a rune pulse that hurls foes back (4 damage)'),
    'archmage': dict(name='Archmage', pieces=('Archmage Hood', 'Archmage Regalia', 'Archmage Skirts', 'Archmage Slippers'),
                     prot=(2, 5, 4, 2), dur=280, material='arcane_thread', stars=0, mc='§d',
                     style='mage', base='navy', accent='gold', glow='ff9cff',
                     b2='Spell and fruit power cooldowns 10% shorter', b4='+20% spell power and +40 max mana'),
}
# what each piece costs at the Magic Forge: (set material, mana-steel ingots, mana crystals) per slot
ARMOR_COST = {'head': (3, 1, 2), 'chest': (5, 2, 4), 'legs': (4, 2, 3), 'feet': (2, 1, 2)}
# special costs: the Mana-Steel set is made of ingots only; the Royal set adds gold and diamonds
ARMOR_EXTRA = {'royal': {'head': [('minecraft:gold_ingot', 2), ('minecraft:diamond', 1)], 'chest': [('minecraft:gold_ingot', 4), ('minecraft:diamond', 2)],
                         'legs': [('minecraft:gold_ingot', 3), ('minecraft:diamond', 2)], 'feet': [('minecraft:gold_ingot', 2), ('minecraft:diamond', 1)]}}
# Materials: id -> (name, description, {entity: (chance, min, max)})
ARMOR_MATERIALS = {
    'mana_steel_ingot': ('§bMana-Steel Ingot', 'Iron steeped in mana. Craft: an iron ingot and two mana crystals (any crafting grid).', {}),
    'devil_hide': ('§4Devil Hide', 'Tough, ember-warm hide from the Devil Host.', {
        'bc:devil': (1.0, 3, 5), 'bc:archdevil': (1.0, 6, 10), 'bc:hellhound': (0.4, 1, 2), 'bc:imp': (0.25, 1, 1),
        'bc:cultist': (0.2, 1, 1), 'bc:dark_disciple': (0.15, 1, 1), 'bc:fallen_captain': (1.0, 3, 6)}),
    'shadow_silk': ('§8Shadow Silk', 'Silk that drinks the light, worn by thieves and assassins.', {
        'bc:shadow_assassin': (0.6, 1, 2), 'bc:bandit_thief': (0.35, 1, 1), 'bc:bandit': (0.08, 1, 1), 'bc:bandit_king': (1.0, 4, 6)}),
    'chitin_plate': ('§6Chitin Plate', 'A plate of hive armour, light and hard as iron.', {
        'bc:hive_drone': (0.4, 1, 1), 'bc:hive_egg': (0.25, 1, 1), 'bc:hive_queen': (1.0, 6, 10)}),
    'rune_shard': ('§9Rune Shard', 'A shard of ancient rune-stone that still hums with old magic.', {
        'bc:construct': (0.5, 1, 2), 'bc:dungeon_golem': (1.0, 3, 5), 'bc:stone_colossus': (1.0, 6, 10), 'bc:mana_wraith': (0.25, 1, 1)}),
    'arcane_thread': ('§dArcane Thread', 'Thread spun from loose spellwork.', {
        'bc:rogue_mage': (0.35, 1, 1), 'bc:grimoire_devourer': (1.0, 6, 10), 'bc:frost_witch': (1.0, 2, 4), 'bc:ember_witch': (1.0, 2, 4),
        'bc:soul_puppeteer': (1.0, 3, 5)}),
}
# the Abyssal set is made from Leviathan Scales (an existing item); these foes now drop them too
SCALE_DROPS = {'bc:raider_captain': (0.5, 1, 2), 'bc:phantom_raider': (0.15, 1, 1), 'bc:sea_raider': (0.06, 1, 1)}
# Runes: id -> (name, colour, effect per rune, the item that gives it its nature)
RUNES = {
    'vitality': ('Rune of Vitality', 'ff5a6a', '+2 max health per rune', 'minecraft:glistering_melon_slice'),
    'warding': ('Rune of Warding', '7cc8ff', 'spells hurt you 6% less per rune', 'minecraft:amethyst_shard'),
    'mana': ('Rune of Mana', '4a7cff', '+15 max mana per rune', 'minecraft:lapis_block'),
    'swiftness': ('Rune of Swiftness', '80ff9a', 'Speed I with two runes, Speed II with four', 'minecraft:rabbit_foot'),
    'thorns': ('Rune of Thorns', '6ad040', 'melee attackers take 1 damage per rune', 'minecraft:cactus'),
    'focus': ('Rune of Focus', 'ffd060', 'spell cooldowns 4% shorter per rune', 'minecraft:clock'),
}
# Reinforcement: +1 to +5 per piece; each level cuts all damage you take by 1.5% (a full +5 set: 30%)
REINFORCE_MAX = 5
REINFORCE_PCT = 1.5
# cost of reaching level n: (mana-steel ingots, mana crystals, diamonds)
REINFORCE_COST = {1: (1, 3, 0), 2: (2, 6, 0), 3: (3, 9, 0), 4: (4, 12, 1), 5: (5, 15, 2)}
FEATS += [
    ('armoured', 'Fully Armoured', 'Wear all four pieces of an armour set.', 'fullset', 1, 1, 60, 'the Armoured'),
    ('collector', 'Armour Collector', 'Wear four different full armour sets.', 'set_kinds', 4, 3, 300, 'the Collector'),
    ('forgemaster', 'Forgemaster', 'Forge 20 pieces of armour.', 'forged', 20, 2, 150, 'Forgemaster'),
    ('master_smith', 'Master Smith', 'Reinforce a piece of armour to +5.', 'reinforce5', 1, 2, 150, 'Master Smith'),
    ('runesmith', 'Runesmith', 'Inscribe 8 runes.', 'runes', 8, 1, 100, 'the Runesmith'),
]
MERCHANT += [('bc:mana_steel_ingot', 4, 40, 'Mana-Steel Ingots x4'), ('bc:rune_shard', 2, 55, 'Rune Shards x2')]

# ======================================================================================
# v1.0.0: the living world (incidents out in the world - see src/scripts/living/world.js), four more grimoires,
# four more Abyss Fruits, Mana Waygates, and more feats and missions.
# ======================================================================================
ATTRIBUTES.update({
    'storm': dict(name='Storm', color='6a8ac8', leaves=4, cover=('0c1222', '141c34', '1e2a48', '2a3a5e', '384a76', '485c8e'), trim='silver', mc='§9'),
    'blossom': dict(name='Blossom', color='ff9ac8', leaves=3, cover=('2a0c1a', '3e1428', '561e38', '70284a', '8c345e', 'a84274'), trim='gold', mc='§d'),
    'coral': dict(name='Coral', color='ff7a5a', leaves=3, cover=('2a0e0a', '401812', '5a2218', '762e20', '923c28', 'ae4c32'), trim='gold', mc='§c'),
    'dream': dict(name='Dream', color='b08cff', leaves=4, cover=('140c26', '201438', '2c1e4c', '3a2862', '4a347a', '5c4294'), trim='silver', mc='§5'),
})
ATTR_ORDER += ['storm', 'blossom', 'coral', 'dream']
SPELLS.update({
    'storm': [
        _s('storm_bolt', 'Storm Bolt', 10, 0.6, 1, 'A crackling bolt torn from the storm.', t='bolt', d=5, shape=3, speed=2.6, fx='lightning', eff=[['slowness', 1, 0]]),
        _s('squall_ring', 'Squall Ring', 24, 6.0, 3, 'A ring of howling wind blasts everyone away from you.', t='nova', d=7, r=4.5, kb=[1.6, 0.5], fx='wind'),
        _s('thunderhead', 'Thunderhead', 34, 12.0, 6, 'A thundercloud gathers over your aim and lashes it with lightning.', t='rain', d=6, n=12, r=6, every=2, fx='lightning'),
        _s('tempest_eye', 'Tempest Eye', 82, 24.0, 10, 'The eye of a storm drags foes into its heart, then lightning falls.', t='vortex', d=16, r=8, dur=3, fx='wind',
           then=dict(t='strikes', d=8, n=5, r=8, fx='lightning')),
    ],
    'blossom': [
        _s('petal_darts', 'Petal Darts', 10, 0.6, 1, 'Three petals as sharp as blades.', t='bolt', d=3.5, n=3, spread=12, shape=2, speed=2.2, fx='leaf'),
        _s('sakura_veil', 'Sakura Veil', 28, 12.0, 3, 'A veil of falling blossoms mends you and your allies.', t='heal', heal=6, r=6, regen=4, fx='leaf'),
        _s('petal_storm', 'Petal Storm', 30, 9.0, 6, 'A storm of cutting petals over your aim.', t='zone', d=2.5, r=5, dur=6, fx='leaf', eff=[['slowness', 2, 1]]),
        _s('thousand_blossoms', 'Thousand Blossoms', 80, 22.0, 10, 'Two rings of blossom blades burst out from you.', t='radial', d=6, n=24, rings=2, shape=2, speed=2.0, fx='leaf'),
    ],
    'coral': [
        _s('coral_shard', 'Coral Shard', 10, 0.6, 1, 'A jagged shard of living coral.', t='bolt', d=5, shape=1, speed=2.2, fx='crystal'),
        _s('reef_spikes', 'Reef Spikes', 26, 8.0, 3, 'Coral spikes burst out of the ground ahead of you.', t='wave', d=8, len=11, fx='crystal', kb=[0.2, 0.8]),
        _s('tide_pool', 'Tide Pool', 30, 10.0, 6, 'A swirling tide pool slows and drags foes near your aim.', t='zone', d=2, r=4, dur=6, pull=0.25, fx='water', eff=[['slowness', 2, 2]]),
        _s('barrier_reef', 'Barrier Reef', 60, 20.0, 10, 'A wall of coral rises in front of you.', t='wall', block='minecraft:brain_coral_block', w=7, h=3, dur=10, fx='crystal'),
    ],
    'dream': [
        _s('drowsy_mote', 'Drowsy Mote', 10, 0.6, 1, 'A drifting mote of sleep that slows what it touches.', t='bolt', d=4, shape=0, speed=1.8, fx='spirit', eff=[['slowness', 2, 1]]),
        _s('lullaby', 'Lullaby', 28, 10.0, 3, 'A lullaby makes every foe around you heavy with sleep.', t='nova', d=3, r=6, fx='sound', eff=[['slowness', 4, 3], ['weakness', 4, 1]]),
        _s('nightmare', 'Nightmare', 36, 12.0, 6, 'Nightmares fall on foes near your aim.', t='strikes', d=9, n=4, r=10, fx='dark', eff=[['blindness', 3, 0]]),
        _s('dreamscape', 'Dreamscape', 80, 24.0, 10, 'The world around your aim becomes a dream: everything in it drifts and weakens.', t='zone', d=4, r=8, dur=8, fx='spirit',
           eff=[['slowness', 2, 2], ['weakness', 2, 1], ['nausea', 3, 0]]),
    ],
})
ALTAR_WEIGHTS.update({'storm': 4, 'blossom': 7, 'coral': 7, 'dream': 4})
_V1_MOVES = {
    'storm': _s('lightning_lattice', 'Lightning Lattice', 62, 18.0, 12, 'A lattice of lightning strikes every foe near your aim.', t='strikes', d=12, n=6, r=12, fx='lightning'),
    'blossom': _s('blooming_prison', 'Blooming Prison', 58, 18.0, 12, 'Foes near your aim are wrapped in blossoming vines.', t='prison', d=10, r=4, dur=3, fx='leaf', eff=[['weakness', 3, 1]]),
    'coral': _s('riptide_reef', 'Riptide Reef', 62, 18.0, 12, 'A reef-lined whirlpool drags foes into its jaws.', t='vortex', d=14, r=7, dur=3, fx='water'),
    'dream': _s('waking_nightmare', 'Waking Nightmare', 60, 18.0, 12, 'Trap foes near your aim inside their worst dream.', t='prison', d=12, r=4, dur=4, fx='dark', eff=[['blindness', 3, 0]]),
}
for _a, _sp in _V1_MOVES.items():
    SPELLS[_a].append(_sp)
AWAKENED.update({
    'storm': _s('heavens_wrath', "Heaven's Wrath", 120, 40.0, 15, 'The sky itself answers: lightning on every foe in sight, then a thunderclap.', t='strikes', d=18, n=10, r=14, fx='lightning',
                then=dict(t='nova', d=10, r=8, kb=[1.8, 0.6], fx='wind')),
    'blossom': _s('spring_eternal', 'Spring Eternal', 110, 38.0, 15, 'An endless spring: blossoms heal you and your allies, and cut down every foe near you.', t='heal', heal=12, r=10, regen=8, fx='leaf',
                  then=dict(t='zone', at='self', d=4, r=8, dur=6, fx='leaf')),
    'coral': _s('leviathan_reef', 'Leviathan Reef', 115, 38.0, 15, 'A reef erupts in eight directions, as vast as a sea serpent.', t='wave', d=16, len=16, dirs=8, fx='crystal', kb=[0.3, 1.0]),
    'dream': _s('eternal_slumber', 'Eternal Slumber', 120, 40.0, 15, 'Every foe around you falls into a dream where time does not move.', t='timestop', d=14, r=14, dur=5, fx='spirit'),
})
for _a in ('storm', 'blossom', 'coral', 'dream'):
    SPELLS[_a].append(AWAKENED[_a])

FRUITS.update({
    'spark': dict(name='Spark Fruit', color='ffe03a', mc='§e', power='Spark Body', beast=False,
                  passive='Lightning in your veins: you move faster.',
                  abilities=[('spark_jolt', 'Spark Jolt', 1.6, 'A jolt of lightning from your fingertips.', dict(t='bolt', d=5, shape=3, speed=2.8, fx='lightning', eff=[['slowness', 1, 1]])),
                             ('thunder_step', 'Thunder Step', 6.0, 'Become lightning and strike through everything to your aim.', dict(t='leap', mode='blink', d=7, dist=10, fx='lightning')),
                             ('storm_cage', 'Storm Cage', 12.0, 'A cage of lightning around foes near your aim.', dict(t='prison', d=10, r=4, dur=3, fx='lightning'))]),
    'echo': dict(name='Echo Fruit', color='a0e0d0', mc='§3', power='Echo Voice', beast=False,
                 passive='You hear everything: you see in the dark.',
                 abilities=[('sonic_shot', 'Sonic Shot', 1.6, 'A bullet of compressed sound.', dict(t='bolt', d=5, shape=0, speed=2.4, fx='sound')),
                            ('echo_burst', 'Echo Burst', 7.0, 'A shout that throws everyone around you back and rattles them.', dict(t='nova', d=6, r=5, kb=[1.6, 0.4], fx='sound', eff=[['nausea', 4, 0]])),
                            ('resonance', 'Resonance', 9.0, 'A wave of sound tears along the ground ahead.', dict(t='wave', d=9, len=14, fx='sound'))]),
    'sand': dict(name='Sand Fruit', color='d8b878', mc='§6', power='Sand Body', beast=False,
                 passive='A body of sand: you are tougher on dry ground.',
                 abilities=[('sand_blades', 'Sand Blades', 1.8, 'Three blades of hardened sand.', dict(t='bolt', d=4, n=3, spread=14, shape=2, speed=2.0, fx='sand')),
                            ('quicksand', 'Quicksand', 9.0, 'The ground near your aim turns to quicksand.', dict(t='zone', d=1, r=4, dur=6, pull=0.4, fx='sand', eff=[['slowness', 2, 3]])),
                            ('desert_coffin', 'Desert Coffin', 12.0, 'Sand swallows and crushes foes near your aim.', dict(t='prison', d=10, r=4, dur=3, fx='sand'))]),
    'gale': dict(name='Gale Fruit', color='b0f0d0', mc='§a', power='Gale Body', beast=False,
                 passive='The wind carries you: you fall gently and jump higher.',
                 abilities=[('air_bullet', 'Air Bullet', 1.4, 'Two bullets of compressed air.', dict(t='bolt', d=4, n=2, spread=6, shape=1, speed=3.0, fx='wind')),
                            ('tailwind', 'Tailwind', 14.0, 'A tailwind for you and your allies.', dict(t='buff', allies=8, fx='wind', self=[['speed', 12, 1], ['jump_boost', 12, 1]])),
                            ('cyclone', 'Cyclone', 10.0, 'A cyclone pulls foes in and flings them.', dict(t='vortex', d=8, r=6, dur=2, fx='wind'))]),
})
FRUIT_ORDER += ['spark', 'echo', 'sand', 'gale']
_V1_FRUIT_MOVES = {
    'spark': ('gigavolt', 'Gigavolt', 16.0, 'Lightning strikes every foe near your aim.', dict(t='strikes', d=14, n=6, r=10, fx='lightning')),
    'echo': ('requiem_wave', 'Requiem Wave', 16.0, 'Waves of sound tear out in eight directions.', dict(t='wave', d=12, len=12, dirs=8, fx='sound', eff=[['weakness', 3, 1]])),
    'sand': ('sandstorm', 'Sandstorm', 18.0, 'A blinding sandstorm drags foes into its heart.', dict(t='vortex', d=14, r=8, dur=3, fx='sand', eff=[['blindness', 2, 0]])),
    'gale': ('sky_splitter', 'Sky Splitter', 16.0, 'Three lanes of cutting wind.', dict(t='wave', d=12, len=16, lanes=3, fx='wind', kb=[1.2, 0.4])),
}
for _f, (_id, _n, _cd, _desc, _spec) in _V1_FRUIT_MOVES.items():
    FRUITS[_f]['abilities'].append((_id, _n, _cd, _desc, _spec, NEW_FRUIT_WILL))

# Mana Waygates: a network of gates you build; travel costs mana (or a mana crystal)
WAYGATE_MANA_BASE = 20
WAYGATE_MANA_PER_100 = 15
WAYGATE_COOLDOWN = 30   # seconds
FEATS += [
    ('answer_the_call', 'Answer the Call', 'Win 10 world events (incidents) where they happen.', 'events', 10, 2, 150, 'the Answerer'),
    ('gatebreaker', 'Gatebreaker', 'Seal 5 Devil Gates.', 'gates', 5, 2, 150, 'Gatebreaker'),
    ('wayfarer', 'Wayfarer', 'Travel by Mana Waygate 10 times.', 'waygate', 10, 1, 60, 'the Wayfarer'),
    ('new_bloom', 'Late Bloomer', 'Receive one of the four newest grimoires (Storm, Blossom, Coral or Dream).', 'new_grimoire', 1, 1, 50, 'the Late Bloomer'),
]
MISSIONS += [
    ('m_incident', 'event', '', 1, 'Answer a call: win a world event where it happens', 2),
    ('m_bandit_band', 'kill', 'bc:bandit', 8, 'Break up a bandit band', 1),
]
MERCHANT += [('bc:waygate', 1, 160, 'Mana Waygate')]

# ======================================================================================
# v1.1.0: the Untamed Kingdom - a named, random world. Regions with their own names, realms, danger and traits;
# landmarks seeded across every region (Mage Spires, Wyvern Roosts, Catacombs, ruined hamlets, graveyards...);
# random loot with rarities, rolled relics and weapons; Champion and Infernal elites; encounters your own actions wake;
# daily omens; wanderers with rumours, trades and requests; journals that tell the land's story.
# ======================================================================================
REGION_SIZE = 320            # a region is a 320 x 320 block cell of the world
# realms by distance from the world spawn: (up to, id, name, colour, base danger stars, traits)
REALMS = [
    (600, 'noble', 'Noble Realm', '§e', 1, 1),
    (1500, 'common', 'Common Realm', '§a', 2, 1),
    (2800, 'forsaken', 'Forsaken Realm', '§7', 3, 2),
    (10 ** 9, 'marches', 'the Marches', '§c', 4, 2),
]
# past the Forsaken Realm the land runs toward the neighbouring kingdoms (by compass direction)
MARCHES = {'north': 'the Spade Marches', 'east': 'the Heart Marches', 'south': 'the Southern Wilds', 'west': 'the Diamond Marches'}
# region names: syllables and landforms that suit what the land is made of
REGION_SYLLABLES = (
    ['Ash', 'Bel', 'Cor', 'Dun', 'El', 'Fen', 'Gal', 'Hal', 'Ir', 'Kel', 'Lor', 'Mor', 'Nor', 'Os', 'Pel', 'Quen', 'Rav', 'Sel', 'Thal', 'Ul',
     'Var', 'Wyn', 'Yr', 'Zan', 'Brin', 'Cael', 'Drav', 'Ery', 'Gor', 'Hest', 'Myr', 'Tor', 'Vel', 'Ald', 'Bram', 'Cyr'],
    ['a', 'e', 'i', 'o', 'en', 'ar', 'or', 'ith', 'an', 'el', 'and', 'ow', '', '', ''],
    ['mere', 'dale', 'wick', 'holm', 'ford', 'moor', 'reach', 'hollow', 'vale', 'crest', 'fell', 'gard', 'stead', 'thorn', 'wood', 'more',
     'brook', 'spire', 'haven', 'watch', 'barrow', 'rest', 'mark', 'shade'],
)
REGION_ADJECTIVES = ['Whispering', 'Ashen', 'Sunken', 'Shattered', 'Silent', 'Weeping', 'Gilded', 'Thorned', 'Howling', 'Drowned', 'Blighted',
                     'Starlit', 'Hollow', 'Crimson', 'Pale', 'Burning', 'Forgotten', 'Broken', 'Wandering', 'Restless', 'Golden', 'Moonlit',
                     'Bleak', 'Verdant', 'Iron', 'Lonely', 'Cursed', 'Singing']
REGION_LANDFORMS = {
    'forest': ['Wood', 'Woods', 'Weald', 'Grove', 'Thicket', 'Forest'],
    'darkwood': ['Darkwood', 'Gloom', 'Shadowwood', 'Wildwood', 'Tangles'],
    'jungle': ['Jungle', 'Tangle', 'Verdance', 'Wilds'],
    'taiga': ['Pines', 'Taiga', 'Firwood', 'Hollows'],
    'plains': ['Fields', 'Plains', 'Meadows', 'Downs', 'Leas', 'Heath'],
    'desert': ['Sands', 'Dunes', 'Wastes', 'Expanse'],
    'badlands': ['Badlands', 'Mesas', 'Scar', 'Canyons'],
    'savanna': ['Savanna', 'Steppe', 'Grasslands', 'Barrens'],
    'frozen': ['Tundra', 'Frostlands', 'Snowfields', 'Rime', 'Glacier'],
    'mountains': ['Peaks', 'Highlands', 'Crags', 'Heights', 'Spires'],
    'swamp': ['Fen', 'Marsh', 'Mire', 'Bog', 'Swamp'],
    'water': ['Coast', 'Shallows', 'Lakes', 'Strand', 'Isles'],
    'blossom': ['Vale', 'Gardens', 'Bloomwood', 'Glade'],
    'mushroom': ['Sporelands', 'Fungal Isles'],
    'hills': ['Hills', 'Wolds', 'Tors', 'Downs'],
}
# what each region is like: id -> (name, colour, description, the land classes it favours)
REGION_TRAITS = {
    'mana_rich': ('Mana-Rich', '§b', '+30% mana regeneration', []),
    'ley_line': ('Ley Line', '§d', '+10% spell power', []),
    'wild_magic': ('Wild Magic', '§5', 'spells may surge (free, or cast twice) - or misfire', []),
    'haunted': ('Haunted', '§8', 'Hollow Knights and wraiths walk at night; ghost lights drift', ['darkwood', 'swamp', 'taiga', 'plains', 'frozen']),
    'bandit_country': ('Bandit Country', '§c', 'bandits roam and ambush travellers', ['plains', 'savanna', 'desert', 'badlands', 'hills']),
    'devil_scarred': ('Devil-Scarred', '§4', 'imps lurk, and Devil Gates tear open more often', ['badlands', 'desert', 'darkwood', 'swamp']),
    'wyvern_lands': ('Wyvern Territory', '§2', 'wyverns roost in the heights and hunt overhead', ['mountains', 'badlands', 'desert', 'frozen', 'hills', 'savanna']),
    'fae_wilds': ('Fae Wilds', '§a', 'sprites dance in fairy rings - mischievous, and generous', ['forest', 'blossom', 'plains', 'jungle', 'mushroom']),
    'ancient': ('Ancient Ruins', '§6', 'the old kingdom\'s spires, crypts and obelisks lie thick here', []),
    'sanctuary': ('Sanctuary', '§f', 'a quiet land: no ambushes, and wanderers come here to rest', ['plains', 'blossom', 'forest']),
    'treasure': ('Hoard-Rich', '§e', 'treasure maps and journals that mark buried caches turn up far more often', ['desert', 'water', 'badlands']),
    'untamed': ('Untamed', '§4', 'elites are twice as common - and drop better loot', ['jungle', 'darkwood', 'mountains', 'frozen']),
}
# one-line lore for a region, chosen by its first trait ({name} = the region's name)
REGION_LORE = {
    'mana_rich': ['The air of {name} hums; even the grass glitters with spent mana.', 'Old mages came to {name} to drink the ley-wells dry. They never could.'],
    'ley_line': ['A ley line runs under {name}. Spells cast here leave scorch-marks on the sky.', 'Grimoires flutter open by themselves in {name}.'],
    'wild_magic': ['Magic misbehaves in {name}. Locals cast their spells twice, or not at all.', 'In {name} the wind sometimes tastes of lightning.'],
    'haunted': ['Knights fell by the hundred in {name}. Some of them still keep watch.', 'Nobody lights a fire in {name} after dark. The lights come anyway.'],
    'bandit_country': ['{name} belongs to whoever holds the road. Today that is the Brotherhood.', 'Travellers cross {name} in convoys, or not at all.'],
    'devil_scarred': ['Something tore through {name} long ago. The scars still smoke.', 'Imps nest in the cracks of {name}, waiting for the next gate.'],
    'wyvern_lands': ['Shadows cross {name} at noon - wyverns, circling their hoards.', 'Shepherds in {name} count their flocks twice a day, and still come up short.'],
    'fae_wilds': ['Sprites dance in the rings of {name}. Bring something shiny.', 'Paths in {name} lead somewhere different each time you walk them.'],
    'ancient': ['The old kingdom built its spires in {name}, and its dead lie beneath them.', 'Every stone in {name} remembers a spell.'],
    'sanctuary': ['{name} is a quiet country. Wanderers come here to rest their feet.', 'Even the wolves of {name} seem tired of fighting.'],
    'treasure': ['They say {name} is paved with buried gold, if you know where to dig.', 'Every fool with a map ends up in {name} sooner or later.'],
    'untamed': ['Nothing in {name} has ever been tamed - least of all its monsters.', 'The beasts of {name} grow strong on the bones of knights.'],
}

# Landmarks seeded across the world: id -> dict(name, weight, land (classes, '*' = any dry land), stars (min), master, desc)
LANDMARKS = {
    'spire': dict(name='Mage Spire', weight=6, land='*', stars=2, master='bc:spire_warden',
                  desc='a five-floor tower of the old kingdom - each floor guarded, the Spire Warden waiting at the top'),
    'roost': dict(name='Wyvern Roost', weight=6, land=['mountains', 'badlands', 'desert', 'frozen', 'hills', 'savanna', 'taiga'], stars=2, master='wyvern',
                  desc='a nest of bones and gold where a Mana Wyvern (Ember, Frost or Storm) sleeps on its hoard'),
    'catacombs': dict(name='Ancient Catacombs', weight=6, land='*', stars=1, master='bc:dungeon_golem',
                      desc='a stair down into a maze of crypts - every one different - with a guardian at its heart'),
    'hamlet': dict(name='Ruined Hamlet', weight=9, land=['plains', 'forest', 'savanna', 'taiga', 'hills', 'blossom', 'frozen'], stars=1, master='',
                   desc='a village nobody lives in any more - some are empty, some are not'),
    'graveyard': dict(name='Old Graveyard', weight=8, land='*', stars=1, master='bc:hollow_knight',
                      desc='tombstones, a crypt, and the Hollow who rise from it at night'),
    'obelisk': dict(name='Mana Obelisk', weight=7, land='*', stars=1, master='',
                    desc='an ancient obelisk that answers a prayer with a boon - or a curse'),
    'fairy_ring': dict(name='Fairy Ring', weight=6, land=['forest', 'blossom', 'plains', 'jungle', 'mushroom', 'darkwood', 'taiga'], stars=1, master='',
                       desc='a ring of mushrooms where sprites bargain - your offering for a random gift'),
    'watchtower': dict(name='Ruined Watchtower', weight=7, land='*', stars=1, master='',
                       desc='a broken Magic Knight watchtower, now held by bandits - with a mana spawner'),
    'caravan': dict(name='Wrecked Caravan', weight=7, land=['plains', 'savanna', 'desert', 'badlands', 'forest', 'hills'], stars=1, master='',
                    desc='a broken cart and scattered cargo - and maybe the bandits who broke it'),
    'crater': dict(name='Star Crater', weight=5, land='*', stars=1, master='',
                   desc='where a star fell long ago: mana crystals, a Star Fragment, and something guarding them'),
    'skeleton': dict(name='Colossal Bones', weight=5, land=['desert', 'badlands', 'savanna', 'plains', 'frozen', 'hills'], stars=1, master='',
                     desc='the bones of something enormous, with a treasure hidden in its skull'),
    'battlefield': dict(name='Forgotten Battlefield', weight=5, land=['plains', 'savanna', 'hills', 'taiga', 'frozen', 'badlands'], stars=2, master='',
                        desc='old banners and broken grimoires where two armies died - the Hollow still fight here at night'),
    'lost_waygate': dict(name='Lost Waygate', weight=5, land='*', stars=1, master='',
                         desc='a ruined Mana Waygate of the old kingdom - touch it to add it to the network'),
    'witch_hut': dict(name='Hedge Witch Hut', weight=5, land=['swamp', 'darkwood', 'forest', 'taiga', 'jungle'], stars=1, master='',
                      desc='a stilt hut where a hedge witch lives - a trader, or a curse'),
}
# how many landmarks a region gets: base + per danger star (the Ancient Ruins trait adds 2)
LANDMARK_BASE = 2
LANDMARK_PER_STAR = 0.6

# ------------------------------------------------------------------------------------- random loot
# rarities: (id, name, colour, weight, affixes, power)
RARITIES = [
    ('common', 'Common', '§f', 50, 1, 1.0),
    ('uncommon', 'Uncommon', '§a', 28, 1, 1.35),
    ('rare', 'Rare', '§9', 14, 2, 1.7),
    ('epic', 'Epic', '§5', 6, 2, 2.1),
    ('legendary', 'Legendary', '§6', 1.8, 3, 2.7),
    ('mythic', 'Mythic', '§c', 0.2, 4, 3.4),
]
RARITY_STAR_SHIFT = 0.28     # each danger star above one makes every step up the rarity ladder 28% likelier
# relics: hold up to three in your hotbar. id -> (name, description, favoured affixes)
RELICS = {
    'relic_ring': ('Signet Ring', 'a ring cut with an old house\'s sigil', ['mana', 'regen', 'power', 'scholar']),
    'relic_talisman': ('Rune Talisman', 'a stone tablet humming with a single rune', ['haste', 'ward', 'guard', 'mana']),
    'relic_idol': ('Bone Idol', 'a little carved idol of a forgotten god', ['vigor', 'thorns', 'leech', 'guard']),
    'relic_eye': ('Crystal Eye', 'a crystal that sees in the dark', ['sight', 'luck', 'power', 'fortune']),
    'relic_fang': ('Wyvern Fang', 'a fang that is still warm', ['might', 'leech', 'ember', 'thorns']),
    'relic_feather': ('Spirit Feather', 'a feather lighter than air', ['swift', 'leap', 'gills', 'regen']),
}
RELIC_SLOTS = 3
# relic affixes: id -> (label with {v}, base value at Common, flag = an effect with no number)
RELIC_AFFIXES = {
    'mana': ('+{v} max mana', 8, False),
    'regen': ('+{v}% mana regeneration', 6, False),
    'power': ('+{v}% spell power', 4, False),
    'haste': ('-{v}% spell cooldowns', 3, False),
    'vigor': ('+{v} max health', 2, False),
    'ward': ('-{v}% damage from spells', 4, False),
    'guard': ('-{v}% damage taken', 2, False),
    'thorns': ('melee attackers take {v} damage', 1, False),
    'leech': ('heal {v}% of melee damage dealt', 3, False),
    'might': ('+{v}% melee damage', 5, False),
    'luck': ('+{v}% chance of extra loot', 6, False),
    'scholar': ('+{v}% magic XP', 5, False),
    'fortune': ('+{v}% doubloons found', 8, False),
    'swift': ('Swiftness', 1, True),
    'leap': ('Jump Boost', 1, True),
    'sight': ('Night Vision', 1, True),
    'gills': ('Water Breathing', 1, True),
    'ember': ('Fire Resistance', 1, True),
}
# rolled weapons (vanilla swords and axes): affix id -> (label with {v}, base value at Common)
WEAPON_AFFIXES = {
    'sharp': ('+{v}% damage', 6),
    'burning': ('sets foes ablaze ({v}s)', 2),
    'frost': ('{v}% chance to freeze', 12),
    'storm': ('{v}% chance to call lightning', 5),
    'vampiric': ('heal {v}% of damage dealt', 4),
    'mana_thirst': ('+{v} mana per hit', 2),
    'executioner': ('+{v}% damage below 30% health', 15),
    'giantslayer': ('+{v}% damage to bosses and elites', 10),
    'cleave': ('cleaves a nearby foe for {v}%', 25),
    'quick': ('Haste while held', 1),
}
WEAPON_BASES = {
    'common': ['minecraft:stone_sword', 'minecraft:iron_sword', 'minecraft:stone_axe'],
    'uncommon': ['minecraft:iron_sword', 'minecraft:iron_axe'],
    'rare': ['minecraft:iron_sword', 'minecraft:iron_axe', 'minecraft:diamond_sword'],
    'epic': ['minecraft:diamond_sword', 'minecraft:diamond_axe'],
    'legendary': ['minecraft:diamond_sword', 'minecraft:diamond_axe', 'minecraft:netherite_sword'],
    'mythic': ['minecraft:netherite_sword', 'minecraft:netherite_axe'],
}
# item names: "<prefix> <base> of <suffix>"; Legendary and Mythic items get a name of their own
ITEM_PREFIX = {'mana': 'Arcane', 'regen': 'Flowing', 'power': 'Empowered', 'haste': 'Quickened', 'vigor': 'Hale', 'ward': 'Warding',
               'guard': 'Stalwart', 'thorns': 'Thorned', 'leech': 'Thirsting', 'might': 'Mighty', 'luck': 'Lucky', 'scholar': 'Learned',
               'fortune': 'Gilded', 'swift': 'Swift', 'leap': 'Bounding', 'sight': 'Watchful', 'gills': 'Tidal', 'ember': 'Emberproof',
               'sharp': 'Keen', 'burning': 'Burning', 'frost': 'Frozen', 'storm': 'Thundering', 'vampiric': 'Vampiric', 'mana_thirst': 'Mana-Drinking',
               'executioner': 'Merciless', 'giantslayer': 'Giant-Felling', 'cleave': 'Cleaving', 'quick': 'Hasty'}
ITEM_SUFFIX = ['of the Wyvern', 'of Embers', 'of the Hollow', 'of Ley Lines', 'of the Fae', 'of the Old Kingdom', 'of Stars', 'of the Marches',
               'of Dawn', 'of the Deep', 'of Ashes', 'of the Spire', 'of Thorns', 'of the Moon', 'of the Lost Squad', 'of Tides']
LEGEND_SYLLABLES = (['Vel', 'Mor', 'Ash', 'Kael', 'Ser', 'Thra', 'Ul', 'Ys', 'Dra', 'Cor', 'Nym', 'Zeph', 'Rhae', 'Ost'],
                    ['mora', 'ith', 'andel', 'yra', 'oth', 'iel', 'ane', 'orn', 'essa', 'ion', 'ar', 'uin'])
LEGEND_EPITHETS = ['the Ashen Promise', 'Last Light of the Spire', 'the Unbroken Oath', 'Whisper of the Deep', 'the Wyvern\'s Due',
                   'Bane of the Hollow', 'the Starfallen', 'Keeper of Ley Lines', 'the Queen\'s Regret', 'the Seventh Leaf',
                   'Song of the Marches', 'the Gravewarden', 'the Thousandth Spell', 'Heart of the Old Kingdom']
REFORGE_COST = {'common': (2, 0, 0), 'uncommon': (4, 0, 0), 'rare': (6, 1, 0), 'epic': (10, 2, 1), 'legendary': (16, 3, 2), 'mythic': (24, 4, 3)}
# (mana crystals, sprite dust, star fragments)

# ------------------------------------------------------------------------------------- elites: Champions and Infernals
ELITE_AFFIXES.update({
    'blinking': ('Blinking', '§5', 'teleports behind its foe every few seconds'),
    'frostbound': ('Frostbound', '§b', 'its blows freeze: slowness and mining fatigue'),
    'stormcaller': ('Stormcaller', '§e', 'calls lightning down on its foe every 6 seconds'),
    'gravitic': ('Gravitic', '§d', 'drags its foes toward it'),
    'regenerating': ('Regenerating', '§a', 'heals 2% of its health every second'),
    'reflective': ('Reflective', '§f', 'turns a quarter of spell damage back on the caster'),
    'webbing': ('Webbing', '§7', 'tangles its foes in cobwebs'),
    'splitting': ('Splitting', '§6', 'splits into two lesser copies when it falls'),
    'ghostly': ('Ghostly', '§8', 'fades from sight now and then'),
    'juggernaut': ('Juggernaut', '§4', 'cannot be knocked back, and hits like a hammer'),
})
# tiers: (id, name, colour, affixes, health boost level)
ELITE_TIERS = [('elite', 'Elite', '§6', 1, 2), ('champion', 'Champion', '§e', 2, 4), ('infernal', 'Infernal', '§c', 3, 7)]
ELITE_TIER_CHANCE = {'champion': 0.22, 'infernal': 0.05}   # of all elites, before danger stars
ELITE_STAR_BONUS = 0.012     # elite chance added per danger star above one

# ------------------------------------------------------------------------------------- encounters your actions wake
# id -> (chance per action, what appears, message)
ENCOUNTERS = {
    'chop': (0.004, 'bc:rootwarden', '§2The tree groans... a Rootwarden tears itself free of the bark!'),
    'mine': (0.002, 'bc:mana_wraith', '§7The rock splits open - a Mana Wraith seeps out of the stone!'),
    'grass': (0.0015, 'bc:mana_sprite', '§aSomething giggles in the grass...'),
    'bed': (0.05, 'bc:hollow_knight', '§8You wake with a start. A Hollow Knight stands over your bed.'),
    'mimic': (0.12, 'bc:mimic', '§cThe chest has TEETH!'),
    'wraith': (0.03, 'bc:mana_wraith', '§8Its spirit will not rest...'),
}

# ------------------------------------------------------------------------------------- omens: a new one most mornings
OMEN_CHANCE = 0.6
OMENS = {
    'mana_tide': ('Mana Tide', '§b', 'The ley lines swell: +25% mana regeneration for everyone today.'),
    'wild_surge': ('Wild Surge', '§d', 'Magic runs wild today: spells may surge, or misfire, anywhere.'),
    'starfall': ('Starfall', '§e', 'Stars will fall tonight. Find where they land - each leaves a Star Fragment.'),
    'hollow_night': ('Hollow Night', '§8', 'The Hollow walk tonight: fallen knights rise across the land.'),
    'wyvern_migration': ('Wyvern Migration', '§2', 'Wyverns are on the wing today. Watch the skies.'),
    'merchants_fair': ('Merchants\' Fair', '§6', 'Wanderers are on every road, and the merchant sells for 20% less.'),
    'bandit_moon': ('Bandit Moon', '§c', 'Bandits are bold today - and their purses are heavy.'),
    'fae_revel': ('Fae Revel', '§a', 'The fae are generous today: fairy-ring bargains favour you.'),
    'calm': ('Calm Skies', '§f', 'A quiet day: no ambushes, and wounds heal faster.'),
    'lucky_stars': ('Lucky Stars', '§6', 'Fortune smiles: loot is far likelier to roll a rarer item today.'),
}

# ------------------------------------------------------------------------------------- wanderers
# kind -> (title, what they do, texture variant)
WANDERERS = {
    'pilgrim': ('Pilgrim', 'walks from shrine to shrine and knows every road', 0),
    'cartographer': ('Cartographer', 'sells Explorer\'s Maps to the landmarks nobody has found', 1),
    'peddler': ('Peddler', 'trades odd goods - and now and then a relic', 2),
    'hermit': ('Hermit Mage', 'knows the old magic and sells spell scrolls', 3),
    'bard': ('Bard', 'trades in tales - true ones point the way to treasure', 4),
    'lost_knight': ('Lost Knight', 'a Magic Knight far from their squad, who may join yours', 5),
}
WANDERER_FIRST = ['Oswin', 'Maren', 'Tobiah', 'Ilse', 'Corwin', 'Nell', 'Fenwick', 'Ysolde', 'Barnaby', 'Wren', 'Ambrose', 'Tilda', 'Garrow',
                  'Liesel', 'Quill', 'Rosamund', 'Hob', 'Edda', 'Percival', 'Saffi']
WANDERER_EPITHET = ['the Wanderer', 'of the Long Road', 'Two-Boots', 'the Grey', 'Lightfoot', 'the Unlucky', 'of Nowhere in Particular',
                    'Mapmaker', 'the Patient', 'Sixpence', 'the Last of Their Squad', 'Old Lantern']
WANDERER_GREETINGS = {
    'pilgrim': ['Peace on your road, friend.', 'I have walked from the Noble Realm on these feet. Ask me anything.'],
    'cartographer': ['Maps! Maps to places nobody has found yet!', 'Every blank on my map is a fortune, if you are brave.'],
    'peddler': ['Buttons, buckles, the odd cursed ring - what\'ll it be?', 'Fell off a cart. Several carts, actually.'],
    'hermit': ['Hm. A grimoire. Not a bad one, either.', 'I left the Capital to read in peace. Then people kept finding me.'],
    'bard': ['Sit! A tale for a doubloon, a true one for two.', 'I have a song about a wyvern. It ends badly for the knight.'],
    'lost_knight': ['My squad... we were scattered. Have you seen a camp?', 'I have not slept in three days. Is it over? Did we win?'],
}
# rumours point at real landmarks: {what}, {dir}, {dist}, {region}
RUMORS = ['There is a {what} to the {dir}, {dist} blocks or so. I would not go alone.',
          'Folk in {region} whisper about a {what} out {dir}. About {dist} blocks.',
          'I passed a {what} to the {dir}, maybe {dist} blocks back. Something watched me the whole way.',
          'If it is treasure you want, try the {what} {dist} blocks {dir} of here.',
          'Do not go {dir}. There is a {what} out there, {dist} blocks off, and nobody comes back the same.']
# requests: fetch an item (id, count min, max) or deal with a landmark
WANDERER_FETCH = [('minecraft:bread', 4, 8), ('bc:mana_crystal', 5, 10), ('minecraft:iron_ingot', 4, 8), ('minecraft:leather', 3, 6),
                  ('bc:sprite_dust', 2, 4), ('bc:hollow_ember', 2, 4), ('minecraft:cooked_beef', 4, 8), ('bc:doubloon', 20, 40),
                  ('minecraft:torch', 16, 32), ('bc:rune_shard', 1, 3), ('minecraft:book', 2, 4), ('bc:mimic_tooth', 1, 1)]

# ------------------------------------------------------------------------------------- journals
# {region} {other} (another region) {what} (a landmark) {dir} {dist} {name} {day}
JOURNALS = [
    'Day {day}. We made camp in {region}. {name} swears the {what} to the {dir} still holds its treasure. We go at first light.',
    'If you read this, do not climb the {what}. Whatever waits at the top does not sleep, and it does not forget.',
    'The road from {other} was long. {name} is gone - taken in the night, near the {what}. I am writing this so someone knows.',
    'Note to self: the sprites of {region} want shiny things. Bring something shiny. Do NOT bring something you love.',
    'Squad orders: hold the {what} until relieved. That was forty days ago. Nobody has come.',
    'The merchant swore this map was real. If it is, the {what} is {dist} blocks {dir} of {region}.',
    '{name} found a grimoire in the dirt today, burned at the edges. It still turned its own pages.',
    'They say a wyvern sleeps on a bed of gold somewhere in the heights. They say a lot of things.',
]
# journals that mark a buried cache: the cache lies {dist} blocks {dir} of where the page was found
CACHE_JOURNALS = [
    'We buried our pay {dist} paces {dir} of this spot, under the old stone. If I do not come back, {name}, it is yours.',
    'Hid the sack {dist} paces to the {dir}. Mark it in your head; never on paper. ...I wrote it on paper.',
    'The captain\'s purse is buried {dist} paces {dir} of here. The captain does not need it any more.',
]

# ------------------------------------------------------------------------------------- items, materials, feats, missions
V11_ITEMS = {
    'explorer_map': ('§6Explorer\'s Map', 'Leads you to a landmark nobody has found. Hold it to follow the arrow.'),
    'journal_page': ('§fTorn Journal Page', 'Read it: a page of someone\'s story. Some mark a buried cache.'),
    'star_fragment': ('§eStar Fragment', 'A shard of a fallen star. Reforges Epic and better relics and weapons.'),
    'sprite_dust': ('§aSprite Dust', 'Glittering dust shed by Mana Sprites. Used to reforge relics and weapons.'),
    'mimic_tooth': ('§cMimic Tooth', 'A tooth from a chest that bit back. Merchants pay well for them.'),
    'hollow_ember': ('§8Hollow Ember', 'The last spark of a Hollow Knight\'s grimoire. Wanderers collect them.'),
    'spire_core': ('§bSpire Core', 'The heart of a Spire Warden. Use it to raise a Mana Waygate in an instant.'),
}
REGION_FIND_XP = 40          # magic XP for discovering a new region
FEATS += [
    ('cartographer', 'Cartographer', 'Discover 10 regions.', 'regions', 10, 1, 80, 'the Cartographer'),
    ('world_walker', 'World Walker', 'Discover 40 regions.', 'regions', 40, 3, 300, 'the World Walker'),
    ('trailblazer', 'Trailblazer', 'Find 15 landmarks.', 'landmarks', 15, 2, 150, 'the Trailblazer'),
    ('spire_breaker', 'Spire Breaker', 'Defeat a Spire Warden at the top of its spire.', 'wardens', 1, 2, 150, 'Spire Breaker'),
    ('wyvernslayer', 'Wyvernslayer', 'Defeat 3 Mana Wyverns.', 'wyverns', 3, 3, 250, 'the Wyvernslayer'),
    ('legendary', 'Legend Hunter', 'Find a Legendary or Mythic item.', 'legendaries', 1, 2, 150, 'the Fortunate'),
    ('it_bit_me', 'It Bit Me', 'Defeat a Mimic.', 'mimics', 1, 1, 40, 'Chest-Wary'),
    ('infernal', 'Into the Inferno', 'Defeat an Infernal elite.', 'infernals', 1, 2, 150, 'the Unburnt'),
    ('good_samaritan', 'Good Samaritan', 'Fulfil 5 wanderers\' requests.', 'requests', 5, 2, 120, 'the Kind'),
]
MISSIONS += [
    ('m_landmark', 'landmark', '', 2, 'Explore: find 2 landmarks', 1),
    ('m_region', 'discover', '', 2, 'Explore: discover 2 new regions', 1),
    ('m_hollow', 'kill', 'bc:hollow_knight', 6, 'Lay 6 Hollow Knights to rest', 2),
]
MERCHANT += [('bc:explorer_map', 1, 60, 'Explorer\'s Map')]
# merchant buys mimic teeth for doubloons (see living/merchant.js)
MIMIC_TOOTH_PRICE = 45

# the Wyvernscale armour set (forged from Wyvern Scales)
ARMOR_SETS['wyvernscale'] = dict(
    name='Wyvernscale', pieces=('Wyvernscale Helm', 'Wyvernscale Hauberk', 'Wyvernscale Greaves', 'Wyvernscale Talons'),
    prot=(3, 8, 6, 3), dur=500, material='wyvern_scale', stars=8, mc='§2',
    style='wyvern', base='wyvern', accent='gold', glow='ffb040',
    b2='Fire Resistance, and you take no fall damage',
    b4='Wyvern\'s Fury: fire, ice and lightning spells hit 20% harder, and fire and lightning hurt you 40% less')
ARMOR_MATERIALS['wyvern_scale'] = ('§2Wyvern Scale', 'A scale shed by a Mana Wyvern - harder than mana-steel, warm to the touch.', {
    'bc:ember_wyvern': (1.0, 5, 9), 'bc:frost_wyvern': (1.0, 5, 9), 'bc:storm_wyvern': (1.0, 5, 9)})
# the three Mana Wyverns: id -> (name, element, colour, breath effect, the land they roost in)
WYVERNS = {
    'ember_wyvern': ('Ember Wyvern', 'flame', 'ff7a2a', 'fire', ['desert', 'badlands', 'savanna']),
    'frost_wyvern': ('Frost Wyvern', 'ice', '8ae6ff', 'freeze', ['frozen', 'taiga', 'mountains']),
    'storm_wyvern': ('Storm Wyvern', 'lightning', 'ffe03a', 'shock', ['hills', 'mountains', 'plains', 'forest', 'jungle']),
}

# ======================================================================================
# v1.2.0: Dragonbound & Kingdoms - hatch, raise and ride a Mana Wyvern of your own; the neighbouring kingdoms hold the
# Marches with soldiers, border forts and commanders (the Heart Kingdom is friendly); the Royal Capital rises near home.
# ======================================================================================
WYVERN_EGGS = {'ember_wyvern': 'wyvern_egg_ember', 'frost_wyvern': 'wyvern_egg_frost', 'storm_wyvern': 'wyvern_egg_storm'}
EGG_HATCH_SECONDS = 240           # seconds of the right conditions
EGG_NEEDS = {
    'ember_wyvern': 'fire, a campfire, lava or magma within 4 blocks',
    'frost_wyvern': 'snow or ice within 4 blocks',
    'storm_wyvern': 'a lightning rod or copper within 4 blocks, or high ground (y 100 or above)',
}
EGG_FROM_HOARD = 0.4              # a roost's hoard holds an egg
EGG_FROM_WYVERN = 0.15            # a slain wild wyvern leaves an egg
# growth stages: (name, growth points needed, health, rideable)
WYVERN_STAGES = [('hatchling', 0, 24, False), ('juvenile', 600, 80, False), ('adult', 1800, 200, True)]
WYVERN_GROWTH_PER_SECOND = 1      # while its owner is within 64 blocks
WYVERN_FOOD = {
    'minecraft:beef': 40, 'minecraft:porkchop': 40, 'minecraft:mutton': 40, 'minecraft:chicken': 30, 'minecraft:rabbit': 30,
    'minecraft:cod': 30, 'minecraft:salmon': 30, 'minecraft:cooked_beef': 60, 'minecraft:cooked_porkchop': 60, 'minecraft:cooked_mutton': 60,
    'minecraft:cooked_chicken': 45, 'minecraft:cooked_cod': 45, 'minecraft:cooked_salmon': 45, 'bc:mana_crystal': 90,
}
WYVERN_NAMES = (['Skar', 'Vael', 'Ory', 'Thun', 'Ash', 'Kry', 'Zeph', 'Mor', 'Ign', 'Fros', 'Bryn', 'Cael', 'Rhaz', 'Tyr'],
                ['vath', 'ira', 'gorn', 'axis', 'mere', 'dris', 'yx', 'wing', 'fang', 'is', 'ael', 'thor', 'ka', 'veil'])
WYVERN_RIDE_SPEED = 0.95          # blocks per tick, flat out
WYVERN_BREATH_COOLDOWN = 4        # seconds
# the kingdoms beyond the Marches: id -> dict
KINGDOMS = {
    'diamond': dict(name='Diamond Kingdom', mc='§b', marches='the Diamond Marches', soldier='diamond_legionnaire', soldier_name='Diamond Legionnaire',
                    commander='Diamond Commander', hostile=True, kits=['crystal', 'steel'], fort='diamond_fort', spoils='diamond_shard',
                    desc='a war-hungry kingdom that forges its mages into weapons; its legions hold the western Marches'),
    'spade': dict(name='Spade Kingdom', mc='§5', marches='the Spade Marches', soldier='spade_zealot', soldier_name='Spade Zealot',
                  commander='Spade Inquisitor', hostile=True, kits=['dark', 'gravity'], fort='spade_citadel', spoils='spade_sigil',
                  desc='a cold kingdom ruled by dark magic; its zealots guard the northern Marches'),
    'heart': dict(name='Heart Kingdom', mc='§d', marches='the Heart Marches', soldier='heart_guardian', soldier_name='Heart Guardian',
                  commander='', hostile=False, kits=['plant', 'spirit'], fort='heart_sanctum', spoils='heart_bloom',
                  desc='a gentle kingdom of spirit magic; its guardians keep the eastern Marches and welcome friends'),
}
MARCH_KINGDOM = {'west': 'diamond', 'north': 'spade', 'east': 'heart'}
LANDMARKS.update({
    'diamond_fort': dict(name='Diamond Border Fort', weight=22, land='*', stars=3, master='commander', kingdom='diamond',
                         desc='a crystal-crowned keep of the Diamond legions - Legionnaires on the walls and a Diamond Commander inside'),
    'spade_citadel': dict(name='Spade Citadel', weight=22, land='*', stars=3, master='commander', kingdom='spade',
                          desc='a black citadel of the Spade zealots, with a Spade Inquisitor at its heart'),
    'heart_sanctum': dict(name='Heart Sanctum', weight=22, land='*', stars=3, master='', kingdom='heart',
                          desc='a spirit grove of the Heart Kingdom - its guardians are friendly, and its priestess trades'),
})
# the Royal Capital: built once per world, this far from the world spawn
CAPITAL_DISTANCE = (150, 230)
CAPITAL_RADIUS = 26               # its walls
CAPITAL_SAFE = 56                 # no ambushes, and monsters do not spawn, this close
# spoils of war: what the Capital's quartermaster pays for them (doubloons each; a star every 10)
SPOILS_PRICE = {'diamond_shard': 25, 'spade_sigil': 25}
V12_ITEMS = {
    'wyvern_egg_ember': ('§6Ember Wyvern Egg', 'Place it near fire, lava or magma and it hatches an Ember Wyvern of your own.'),
    'wyvern_egg_frost': ('§bFrost Wyvern Egg', 'Place it in snow or beside ice and it hatches a Frost Wyvern of your own.'),
    'wyvern_egg_storm': ('§eStorm Wyvern Egg', 'Place it by a lightning rod or copper, or high on a mountain, to hatch a Storm Wyvern.'),
    'wyvern_whistle': ('§2Wyvern Whistle', 'Use: follow / stay / roam. Sneak-use: call it to you. While riding: breathe!'),
    'wyvern_saddle': ('§6Wyvern Saddle', 'Use it on your grown wyvern, then ride it into the sky.'),
    'diamond_shard': ('§bDiamond Shard', 'Crystal cut from a Diamond Legionnaire\'s armour. The Capital\'s quartermaster pays for them.'),
    'spade_sigil': ('§5Spade Sigil', 'A black iron sigil carried by Spade zealots. The Capital\'s quartermaster pays for them.'),
    'heart_bloom': ('§dHeart Bloom', 'A spirit-flower of the Heart Kingdom, given in friendship. Brew it into a Spirit Draught.'),
    'spirit_draught': ('§dSpirit Draught', 'Regeneration and +50% mana regeneration for 3 minutes.'),
}
RELICS.update({
    'relic_prism': ('Legion Prism', 'a cut crystal from a Diamond commander\'s crown', ['power', 'ward', 'guard', 'might']),
    'relic_brand': ('Zealot\'s Brand', 'a black iron brand still warm from a Spade forge', ['power', 'leech', 'haste', 'thorns']),
    'relic_blossom': ('Spirit Blossom', 'a flower that never wilts, from the Heart Kingdom', ['regen', 'vigor', 'mana', 'swift']),
})
WANDERERS.update({
    'quartermaster': ('Quartermaster', 'runs the Royal Capital\'s war office: buys spoils of war, sells saddles and contracts', 7),
    'priestess': ('Heart Priestess', 'keeps a Heart Sanctum: trades spirit relics and draughts, and thanks friends with Heart Blooms', 6),
})
WANDERER_GREETINGS.update({
    'quartermaster': ['Spoils from the Marches? The Crown pays well for them.', 'Every shard you bring back is one less legion on our border.'],
    'priestess': ['Be welcome, friend of the Clover. The spirits are calm today.', 'The grove remembers kindness. So do I.'],
})
FEATS += [
    ('hatchling', 'Hatchling', 'Hatch a Wyvern Egg.', 'hatched', 1, 1, 60, 'the Egg-Warmer'),
    ('wyvern_bond', 'Wyvern Bond', 'Raise a wyvern to full size.', 'adult_wyverns', 1, 2, 150, 'Wyvernkin'),
    ('dragon_rider', 'Dragon Rider', 'Ride your wyvern into the sky.', 'wyvern_rides', 1, 2, 150, 'the Dragon Rider'),
    ('border_warden', 'Border Warden', 'Defeat 25 Diamond or Spade soldiers.', 'kingdom_kills', 25, 2, 150, 'Border Warden'),
    ('fort_breaker', 'Fort Breaker', 'Defeat a kingdom commander in their fort.', 'commanders', 1, 2, 200, 'the Fort Breaker'),
    ('friend_of_hearts', 'Friend of Hearts', 'Trade with a Heart Priestess.', 'heart_trades', 1, 1, 60, 'Friend of Hearts'),
    ('to_the_capital', 'To the Capital', 'Reach the Royal Capital.', 'capital', 1, 1, 50, 'Citizen of the Crown'),
]
MISSIONS += [
    ('m_border', 'kill', 'bc_kingdom_foe', 6, 'Hold the border: defeat 6 kingdom soldiers', 2),
]
MERCHANT += [('bc:wyvern_saddle', 1, 220, 'Wyvern Saddle')]

# ======================================================================================
# v1.3.0: Devil Union - devils of the underworld cannot walk this world without a host. Hosts change as their union with
# the devil deepens (0% -> 50% -> 100%). Defeat a host at full union and its devil may offer YOU a pact: fill a union
# gauge in battle, then join with it - at 50%, and once your bond is strong enough, at 100%. Stay joined too long and
# the devil takes the wheel. All the devils are original.
# ======================================================================================
def _dm(id_, name, cost, cd, desc, **spec):
    return dict(id=id_, name=name, cost=cost, cd=cd, desc=desc, spec=spec)


# id -> dict. rank: lower / mid / higher. attr: the grimoire colour its magic borrows. boon/price: always on while bound
# (stat modifiers, as core/mods.js reads them). moves: two at 50% union, the third only at 100%.
DEVILS = {
    'vharog': dict(name='Vharog', title='the Cinder Maw', rank='mid', vice='Wrath', attr='flame', fx='magma', color='ff5a1a', mc='§c',
                   skin=('1a0604', '3a0c08', '5e140c', '8a2010', 'b83418', 'e05a24'), cloth=('120808', '201010', '2e1612', '3e1e16'),
                   boon={'melee': 1.1}, boon_text='+10% melee damage', price={'regen': 0.9}, price_text='-10% mana regeneration',
                   desc='a devil of wrath that burns everything it is allowed to touch',
                   offer='Your anger is a fire with no fuel. Give it mine.',
                   whispers=['Burn it. Burn all of it.', 'Why do you hold back? I never do.', 'More. MORE.', 'They will run from us. Let them run.'],
                   moves=[_dm('cinder_fang', 'Cinder Fang', 8, 1.2, 'Three fangs of hellfire.', t='bolt', d=9, n=3, spread=14, shape=2, speed=2.2, fire=4, fx='magma'),
                          _dm('wrath_pillars', 'Wrath Pillars', 15, 5.0, 'Pillars of fire burst up around your aim.', t='strikes', d=12, n=5, r=9, fire=5, fx='magma'),
                          _dm('hellmouth', 'Hellmouth', 30, 14.0, 'The sky opens and hell falls through.', t='meteor', d=26, n=3, r=6, aoe=5, fire=8, size=3, fx='magma')]),
    'sileth': dict(name='Sileth', title='the Pale Choir', rank='mid', vice='Sorrow', attr='ice', fx='ice', color='9ad8ff', mc='§b',
                   skin=('0e1620', '1c2a3a', '2c4256', '486a86', '78a0be', 'b8d8ee'), cloth=('0a0e14', '121a24', '1c2836', '283a4c'),
                   boon={'ward': 0.08}, boon_text='spells hurt you 8% less', price={'melee': 0.92}, price_text='-8% melee damage',
                   desc='a devil of sorrow whose voice is a winter that never ends',
                   offer='Everyone you love will leave you. I never will. Sing with me.',
                   whispers=['Do you hear them weeping? Make them louder.', 'Cold is only another kind of quiet.', 'Stay. Stay a little longer.'],
                   moves=[_dm('grave_frost', 'Grave Frost', 8, 1.5, 'A wave of grave-cold that slows all it touches.', t='wave', d=9, len=14, lanes=3, fx='ice', eff=[['slowness', 3, 2]]),
                          _dm('mourning_bell', 'Mourning Bell', 15, 6.0, 'A frozen knell: foes around you are slowed and weakened.', t='nova', d=12, r=7, kb=[1.2, 0.4], fx='ice', eff=[['slowness', 4, 3], ['weakness', 4, 0]]),
                          _dm('pale_choir', 'The Pale Choir', 30, 16.0, 'A storm of mourning voices freezes everything around you.', t='zone', at='self', d=5, r=10, dur=6, fx='ice', eff=[['slowness', 2, 4]])]),
    'morvane': dict(name='Morvane', title='the Hollow Crown', rank='mid', vice='Pride', attr='dark', fx='gravity', color='a060ff', mc='§5',
                    skin=('0a0612', '160c24', '241438', '361e52', '4c2a70', '6a3a96'), cloth=('060408', '0e0a14', '18101e', '22182c'),
                    boon={'guard': 0.08}, boon_text='blows hurt you 8% less', price={'cd': 1.1}, price_text='spells recharge 10% slower',
                    desc='a devil of pride that wears its hosts like a borrowed crown',
                    offer='Kneel to no one. Not even to me - well. Perhaps a little, to me.',
                    whispers=['Kneel them. Every one of them.', 'You were born to be looked up at.', 'Weight is only power that has not been used yet.'],
                    moves=[_dm('crowns_weight', "Crown's Weight", 10, 3.0, 'A crushing weight pins foes around your aim.', t='prison', d=12, r=3.5, dur=3, fx='gravity'),
                           _dm('hollow_pull', 'Hollow Pull', 14, 6.0, 'A hollow in the world drags foes in and grinds them.', t='vortex', d=10, r=7, dur=2.5, fx='dark'),
                           _dm('abyssal_throne', 'Abyssal Throne', 30, 16.0, 'Five falling weights of solid night.', t='meteor', d=22, n=5, r=8, aoe=4, size=2, fx='gravity')]),
    'ghorza': dict(name='Ghorza', title='the Red Hunger', rank='mid', vice='Hunger', attr='blood', fx='blood', color='e0203a', mc='§4',
                   skin=('16040a', '2c0812', '460e1c', '641628', '8a2036', 'b03048'), cloth=('100606', '1c0c0c', '2a1212', '3a1818'),
                   boon={'leech': 1}, boon_text='your blows heal you a little', price={'maxMana': -20}, price_text='-20 max mana',
                   desc='a devil of hunger that has never once been full',
                   offer='You are starving and do not know it. I can teach you to eat.',
                   whispers=['Hungry. So hungry.', 'That one looks warm.', 'Do not stop. Never stop eating.'],
                   moves=[_dm('red_hunger', 'Red Hunger', 8, 1.5, 'A beam of hunger that drinks what it burns.', t='beam', d=10, range=18, fx='blood', ls=0.5),
                          _dm('feeding_frenzy', 'Feeding Frenzy', 14, 5.0, 'Four savage bites in a row, each one feeding you.', t='repeat', n=4, every=4,
                              spec=dict(t='nova', at='front', d=6, r=3, kb=[0.4, 0.1], fx='blood', ls=0.3)),
                          _dm('crimson_feast', 'Crimson Feast', 30, 15.0, 'Blood-red fangs rain on everything near you - and you drink.', t='strikes', d=16, n=8, r=12, fx='blood', ls=0.35)]),
    'vaelgrim': dict(name='Vaelgrim', title='the Crowned Abyss', rank='higher', vice='Dominion', attr='blood', fx='devil', color='ff2a4a', mc='§4',
                     skin=('0c0204', '1e0408', '34080e', '520c16', '761420', '9a1e2c'), cloth=('060204', '100608', '1a0a0e', '261016'),
                     boon={'power': 1.12}, boon_text='+12% spell power', price={'luck': -10}, price_text='loot rolls a little worse',
                     desc='a higher-rank devil, a lord of the deep underworld, who rules lesser devils as a king rules dogs',
                     offer='You broke my vessel. Good. Now be a better one.',
                     whispers=['On your knees, world.', 'I have ruled longer than your kingdom has had a name.', 'Let go. I will drive.'],
                     moves=[_dm('abyss_lance', 'Abyss Lance', 8, 1.2, 'A lance of the deep underworld.', t='beam', d=14, range=26, width=1.4, fx='devil'),
                            _dm('dominion', 'Dominion', 15, 6.0, 'Everything near you is thrown down.', t='nova', d=16, r=8, kb=[2.4, 0.9], fx='devil'),
                            _dm('crowned_abyss', 'The Crowned Abyss', 35, 18.0, 'The underworld itself falls on your foes.', t='meteor', d=30, n=6, r=9, aoe=5, size=3, fire=6, fx='devil')]),
    # the lesser devils that seize Magic Knights; they make no pacts
    'lesser': dict(name='a lesser devil', title='', rank='lower', vice='Spite', attr='dark', fx='devil', color='ff3a2a', mc='§c',
                   skin=('120808', '22100e', '341814', '4a221c', '603026', '7c4032'), cloth=('0c0c10', '16161c', '202028', '2c2c36'),
                   boon={}, boon_text='', price={}, price_text='', desc='a low-rank devil, small and spiteful', offer='', whispers=[],
                   moves=[_dm('spite_bolt', 'Spite Bolt', 0, 2.0, '', t='bolt', d=6, n=2, spread=10, shape=2, speed=2.0, fx='devil'),
                          _dm('spite_burst', 'Spite Burst', 0, 6.0, '', t='nova', d=8, r=5, kb=[1.4, 0.5], fx='devil'),
                          _dm('spite_rain', 'Spite Rain', 0, 10.0, '', t='rain', d=7, n=6, r=4, every=4, fx='devil')]),
}
PACT_DEVILS = ['vharog', 'sileth', 'morvane', 'ghorza', 'vaelgrim']
HOST_DEVILS = ['vharog', 'sileth', 'morvane', 'ghorza']       # the mid-rank devils that walk in hosts
DEVIL_RANKS = {'lower': 'Low-rank', 'mid': 'Mid-rank', 'higher': 'Higher-rank'}
# devil hosts: their union deepens as they are hurt
HOST = dict(hp=70, half=0.6, full=0.3, heal=0.2, sigil=0.3, sigil_pity=4, horn=0.6, possessed_free=0.35)
# the player's union with their devil
UNION = dict(
    hit=0.6, hurt=1.2, kill=6, devil_kill=14,    # gauge gained per damage dealt / taken, per kill, per devil killed
    half=50, full=100,                            # gauge needed to join at 50% / 100% (100% also needs bond 3)
    drain=(1.0, 2.2),                             # gauge lost per second at 50% / 100%
    hold=(1.0, 3.2), hold_decay=2.5,              # the devil's hold gained per second at 50% / 100%, lost per second apart
    takeover=10,                                  # seconds the devil drives once its hold is full
    bond=[0, 150, 450, 1000, 1800],               # bond points for bond levels 1-5 (a second in union = 1, a kill in union = 6)
    full_bond=3, steady_bond=5,                   # bond for 100% union; at bond 5 the devil never takes over at 50%
    half_mods=dict(power=1.25, melee=1.35, guard=0.1),
    full_mods=dict(power=1.6, melee=1.7, guard=0.2, ward=0.2, regen=1.5),
    higher=dict(power=1.15, hold=1.4),            # a higher-rank devil: stronger, and harder to hold back
    chain_seconds=120,                            # a Binding Chain keeps the devil from taking over this long
)
V13_ITEMS = {
    'pact_vharog': ('§cPact Sigil: Vharog', 'Use: hear the devil\'s offer. Bound: use to join in union, then to cast; sneak-use to switch.'),
    'pact_sileth': ('§bPact Sigil: Sileth', 'Use: hear the devil\'s offer. Bound: use to join in union, then to cast; sneak-use to switch.'),
    'pact_morvane': ('§5Pact Sigil: Morvane', 'Use: hear the devil\'s offer. Bound: use to join in union, then to cast; sneak-use to switch.'),
    'pact_ghorza': ('§4Pact Sigil: Ghorza', 'Use: hear the devil\'s offer. Bound: use to join in union, then to cast; sneak-use to switch.'),
    'pact_vaelgrim': ('§4§lPact Sigil: Vaelgrim', 'A higher-rank devil\'s sigil. Use: hear its offer.'),
    'host_horn': ('§4Host Horn', 'Shed by a devil host at full union. Exorcists and smiths want them.'),
    'binding_chain': ('§7Binding Chain', 'Use: your devil\'s hold drops to nothing, and it cannot take over for 2 minutes.'),
    'abyssal_crown': ('§4Abyssal Crown', 'Raise it at night to call the Crowned Vessel.'),
}
OMENS.update({
    'underworld_stirs': ('The Underworld Stirs', '§4', 'Devils walk in borrowed bodies tonight, and every union gauge fills 50% faster.'),
})
LANDMARKS.update({
    'underworld_breach': dict(name='Underworld Breach', weight=5, land='*', stars=3, master='bc:crowned_vessel',
                              desc='a wound in the world where the underworld shows through - the Crowned Vessel waits there for a challenger'),
})
FEATS += [
    ('pact_bound', 'Pact-Bound', 'Make a pact with a devil.', 'pacts', 1, 1, 80, 'the Pact-Bound'),
    ('half_union', 'Half a Devil', 'Join with your devil at 50% union.', 'half_unions', 1, 1, 80, 'Half-Devil'),
    ('full_union', 'Full Union', 'Join with your devil at 100% union.', 'full_unions', 1, 2, 200, 'the Devil-Joined'),
    ('devils_equal', 'Devil\'s Equal', 'Reach bond 5 with your devil.', 'bond5', 1, 3, 300, 'the Devil\'s Equal'),
    ('exorcist', 'Exorcist', 'Free 3 possessed Magic Knights.', 'exorcisms', 3, 2, 150, 'the Exorcist'),
    ('host_hunter', 'Host Hunter', 'Defeat 20 devil hosts.', 'host_kills', 20, 2, 150, 'Host Hunter'),
    ('crown_breaker', 'Crown-Breaker', 'Defeat the Crowned Vessel.', 'vessels', 1, 3, 300, 'Crown-Breaker'),
]
MISSIONS += [
    ('m_hosts', 'kill', 'bc_devil_host', 3, 'Cast out the devils: defeat 3 devil hosts', 2),
]
MERCHANT += [('bc:binding_chain', 1, 90, 'Binding Chain')]
