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
