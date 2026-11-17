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
