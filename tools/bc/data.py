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
