"""v0.7.0 pack content: the Bandit Brotherhood (brawler, archer, thief, the Bandit King), the Shadow Assassin, the Cultist,
the Hive (drones, eggs, the Hive Queen), the Grimoire Devourer, and their summoning items."""
from __future__ import annotations

from . import out
from .data import NS, V7_ITEMS
from .models import v7
from .out import BP, RP, write_json
from .packgen import Ctx, item_json, mob_base, shaped
from .seagen import _client, _entity, _melee_ai
from .v2gen import keep_distance
from .v3gen import _amulet_pool, _flyer, _icon, _pool
from .wave4gen import add_team_groups

HUNT = ('player', 'bc_knight', 'bc_navy', 'irongolem', 'villager')


def _spawn(ident, biomes, weight, herd, night=None):
    cond = {'minecraft:spawns_on_surface': {}, 'minecraft:difficulty_filter': {'min': 'easy', 'max': 'hard'}, 'minecraft:weight': {'default': weight},
            'minecraft:herd': {'min_size': herd[0], 'max_size': herd[1]}, 'minecraft:density_limit': {'surface': herd[1] + 1},
            'minecraft:biome_filter': {'any_of': [{'test': 'has_biome_tag', 'value': b} for b in biomes]}}
    if night is True:
        cond['minecraft:brightness_filter'] = {'min': 0, 'max': 7, 'adjust_for_weather': True}
    write_json(BP, f'spawn_rules/{ident}.json', {'format_version': '1.8.0', 'minecraft:spawn_rules': {
        'description': {'identifier': f'{NS}:{ident}', 'population_control': 'monster'}, 'conditions': [cond]}})


def gen_items(ctx: Ctx):
    ic = v7.v7_icons()
    usable = {'minecraft:use_modifiers': {'use_duration': 0.6, 'movement_modifier': 1.0}}
    for key, (name, _) in V7_ITEMS.items():
        write_json(BP, f'items/v7/{key}.json', item_json(f'{NS}:{key}', name, _icon(ctx, key, ic[key]),
                                                         {'minecraft:max_stack_size': {'value': 1}, 'minecraft:glint': {'value': True}, **usable}))
    write_json(BP, 'recipes/v7/bandit_crown.json', shaped('bandit_crown', ['GEG', 'GDG'], {
        'G': 'minecraft:gold_ingot', 'E': 'minecraft:emerald', 'D': f'{NS}:doubloon'}))
    write_json(BP, 'recipes/v7/forbidden_tome.json', shaped('forbidden_tome', ['PHP', 'PBP', 'PHP'], {
        'P': f'{NS}:ancient_page', 'H': f'{NS}:devil_heart', 'B': 'minecraft:book'}))
    write_json(BP, 'recipes/v7/royal_jelly.json', shaped('royal_jelly', ['CHC', 'HMH', 'CHC'], {
        'C': 'minecraft:honeycomb', 'H': 'minecraft:honey_bottle', 'M': f'{NS}:mana_crystal'}))


def gen_loot(ctx: Ctx):
    L = 'loot_tables/entities'
    write_json(BP, f'{L}/bc_bandit.json', {'pools': [_pool(f'{NS}:doubloon', 2, 6), _pool('minecraft:bread', 1, 2, 0.4), _pool('minecraft:iron_ingot', 1, 1, 0.15)]})
    write_json(BP, f'{L}/bc_bandit_archer.json', {'pools': [_pool(f'{NS}:doubloon', 2, 5), _pool('minecraft:arrow', 2, 6, 0.7), _pool('minecraft:string', 1, 2, 0.4)]})
    write_json(BP, f'{L}/bc_bandit_thief.json', {'pools': [_pool(f'{NS}:doubloon', 4, 10), _pool('minecraft:emerald', 1, 2, 0.3), _pool(f'{NS}:treasure_map', 1, 1, 0.05)]})
    write_json(BP, f'{L}/bc_bandit_king.json', {'pools': [_pool(f'{NS}:doubloon', 60, 120), _pool('minecraft:gold_ingot', 4, 9), _amulet_pool(0.6),
                                                           _pool(f'{NS}:clover_leaf', 1, 1, 0.35), _pool(f'{NS}:treasure_map', 1, 1, 0.5), _pool(f'{NS}:clover_charm', 1, 1, 0.2)]})
    write_json(BP, f'{L}/bc_shadow_assassin.json', {'pools': [_pool(f'{NS}:doubloon', 3, 8), _pool('minecraft:ender_pearl', 1, 1, 0.3),
                                                               _pool(f'{NS}:ancient_page', 1, 1, 0.2), _amulet_pool(0.04)]})
    write_json(BP, f'{L}/bc_cultist.json', {'pools': [_pool(f'{NS}:mana_crystal', 1, 3), _pool(f'{NS}:devil_heart', 1, 1, 0.06), _pool(f'{NS}:ancient_page', 1, 1, 0.25)]})
    write_json(BP, f'{L}/bc_hive_drone.json', {'pools': [_pool('minecraft:honeycomb', 0, 1), _pool('minecraft:slime_ball', 0, 1)]})
    write_json(BP, f'{L}/bc_hive_egg.json', {'pools': [_pool('minecraft:slime_ball', 0, 2)]})
    write_json(BP, f'{L}/bc_hive_queen.json', {'pools': [_pool('minecraft:honey_block', 2, 4), _pool('minecraft:honeycomb', 6, 12), _pool(f'{NS}:mana_crystal', 10, 16),
                                                          _amulet_pool(0.7), _pool(f'{NS}:clover_leaf', 1, 1, 0.4), _pool(f'{NS}:clover_charm', 1, 1, 0.25)]})
    write_json(BP, f'{L}/bc_grimoire_devourer.json', {'pools': [_pool(f'{NS}:ancient_page', 6, 12), _pool(f'{NS}:mana_crystal', 10, 18), _amulet_pool(0.6),
                                                                 _pool(f'{NS}:companion_tome', 1, 1, 0.5), _pool(f'{NS}:clover_charm', 1, 1, 0.35)]})


def _humanoid_client(ident, geo, prefix, anims, egg, scale=None, extra_animate=None):
    animate = ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look_at_target'] + (extra_animate or [])
    _client(ident, geo, f'textures/entity/bc/{ident}', 'entity_alphatest', {k.split('.')[-1]: k for k in anims}, animate, egg=egg, scale=scale)


def gen_entities(ctx: Ctx):
    # ---------------------------------------------------------------- the Bandit Brotherhood
    ba = v7.bandit_animations('bandit')
    ctx.animations['entity/bandit.animation.json'] = ba
    for ident, kind, hp, dmg, speed, label, egg in (
            ('bandit', 'brawler', 26, 5, 0.3, 'Bandit', ('#541610', '#52341c')),
            ('bandit_archer', 'archer', 22, 3, 0.3, 'Bandit Archer', ('#243a16', '#52341c')),
            ('bandit_thief', 'thief', 20, 3, 0.36, 'Bandit Thief', ('#24242c', '#d39a2c'))):
        comps = mob_base(ident, ['bc_bandit', 'monster', 'mob'], hp, (0.6, 1.9), speed, f'loot_tables/entities/bc_{ident}.json', 8)
        comps.update(_melee_ai(dmg, targets=HUNT))
        comps['minecraft:behavior.hurt_by_target'] = {'priority': 1, 'alert_same_type': True}
        if kind == 'archer':
            comps.update(keep_distance(['player', 'bc_knight', 'bc_navy']))
        write_json(BP, f'entities/v7/{ident}.json', _entity(ident, comps, spawnable=True))
        add_team_groups(f'entities/v7/{ident}.json', f'bc:{ident}')
        g = v7.bandit_geo(kind)
        g.write(out.path(RP, f'models/entity/bc/{ident}.geo.json'), out.path(RP, f'textures/entity/bc/{ident}.png'))
        _humanoid_client(ident, g.identifier, 'bandit', ba, {'base_color': egg[0], 'overlay_color': egg[1]})
        ctx.lang += [f'entity.{NS}:{ident}.name={label}', f'item.spawn_egg.entity.{NS}:{ident}.name={label} Spawn Egg']
    _spawn('bandit', ['plains', 'savanna', 'desert', 'mesa'], 2, (2, 4))
    _spawn('bandit_archer', ['plains', 'savanna', 'desert', 'mesa'], 1, (1, 2))
    _spawn('bandit_thief', ['plains', 'savanna', 'forest'], 1, (1, 1), night=True)

    # the Bandit King (boss)
    comps = mob_base('bandit_king', ['bc_bandit', 'bc_boss', 'monster', 'mob', 'boss'], 700, (0.8, 2.4), 0.32, 'loot_tables/entities/bc_bandit_king.json', 300)
    comps.update(_melee_ai(10, targets=HUNT))
    comps['minecraft:boss'] = {'should_darken_sky': False, 'hud_range': 64}
    comps['minecraft:knockback_resistance'] = {'value': 0.8}
    comps['minecraft:persistent'] = {}
    comps.pop('minecraft:despawn', None)
    write_json(BP, 'entities/v7/bandit_king.json', _entity('bandit_king', comps))
    g = v7.bandit_king_geo()
    g.write(out.path(RP, 'models/entity/bc/bandit_king.geo.json'), out.path(RP, 'textures/entity/bc/bandit_king.png'))
    ka = v7.bandit_king_animations()
    ctx.animations['entity/bandit_king.animation.json'] = ka
    _humanoid_client('bandit_king', 'geometry.bc.bandit_king', 'bandit_king', ka, {'base_color': '#601810', 'overlay_color': '#f0c24a'}, scale='1.25')
    ctx.lang += [f'entity.{NS}:bandit_king.name=§6§lThe Bandit King', f'item.spawn_egg.entity.{NS}:bandit_king.name=Bandit King Spawn Egg']

    # ---------------------------------------------------------------- the Shadow Assassin
    comps = mob_base('shadow_assassin', ['bc_rogue', 'bc_assassin', 'monster', 'mob'], 30, (0.6, 1.9), 0.34, 'loot_tables/entities/bc_shadow_assassin.json', 14)
    comps.update(_melee_ai(7, targets=('player', 'bc_knight', 'bc_navy')))
    write_json(BP, 'entities/v7/shadow_assassin.json', _entity('shadow_assassin', comps, spawnable=True))
    g = v7.assassin_geo()
    g.write(out.path(RP, 'models/entity/bc/shadow_assassin.geo.json'), out.path(RP, 'textures/entity/bc/shadow_assassin.png'))
    sa = v7.assassin_animations()
    ctx.animations['entity/shadow_assassin.animation.json'] = sa
    _humanoid_client('shadow_assassin', 'geometry.bc.shadow_assassin', 'shadow_assassin', sa, {'base_color': '#100c16', 'overlay_color': '#c070ff'})
    _spawn('shadow_assassin', ['forest', 'taiga', 'jungle'], 1, (1, 1), night=True)
    ctx.lang += [f'entity.{NS}:shadow_assassin.name=Shadow Assassin', f'item.spawn_egg.entity.{NS}:shadow_assassin.name=Shadow Assassin Spawn Egg']

    # ---------------------------------------------------------------- the Cultist
    comps = mob_base('cultist', ['bc_devil', 'bc_cultist', 'monster', 'mob'], 28, (0.6, 1.95), 0.28, 'loot_tables/entities/bc_cultist.json', 14)
    comps.update(_melee_ai(3, targets=('player', 'bc_knight', 'bc_navy')))
    comps.update(keep_distance(['player', 'bc_knight', 'bc_navy']))
    write_json(BP, 'entities/v7/cultist.json', _entity('cultist', comps, spawnable=True))
    g = v7.cultist_geo()
    g.write(out.path(RP, 'models/entity/bc/cultist.geo.json'), out.path(RP, 'textures/entity/bc/cultist.png'))
    ca = v7.cultist_animations()
    ctx.animations['entity/cultist.animation.json'] = ca
    _humanoid_client('cultist', 'geometry.bc.cultist', 'cultist', ca, {'base_color': '#30080e', 'overlay_color': '#d8cfb8'})
    _spawn('cultist', ['plains', 'forest', 'swamp'], 1, (1, 2), night=True)
    ctx.lang += [f'entity.{NS}:cultist.name=Cultist', f'item.spawn_egg.entity.{NS}:cultist.name=Cultist Spawn Egg']

    # ---------------------------------------------------------------- the Hive
    comps = mob_base('hive_drone', ['bc_hive', 'monster', 'mob', 'arthropod'], 14, (0.7, 0.6), 0.38, 'loot_tables/entities/bc_hive_drone.json', 5)
    comps.update(_melee_ai(3, targets=('player', 'bc_knight', 'bc_navy', 'villager')))
    comps['minecraft:behavior.leap_at_target'] = {'priority': 3, 'yd': 0.4, 'must_be_on_ground': True}
    comps['minecraft:behavior.hurt_by_target'] = {'priority': 1, 'alert_same_type': True}
    write_json(BP, 'entities/v7/hive_drone.json', _entity('hive_drone', comps, spawnable=True))
    add_team_groups('entities/v7/hive_drone.json', 'bc:hive_drone')
    g = v7.drone_geo()
    g.write(out.path(RP, 'models/entity/bc/hive_drone.geo.json'), out.path(RP, 'textures/entity/bc/hive_drone.png'))
    da = v7.drone_animations()
    ctx.animations['entity/hive_drone.animation.json'] = da
    _client('hive_drone', 'geometry.bc.hive_drone', 'textures/entity/bc/hive_drone', 'entity_alphatest', {k.split('.')[-1]: k for k in da},
            ['idle', {'walk': 'q.modified_move_speed > 0.01'}], egg={'base_color': '#4a3410', 'overlay_color': '#b8f040'})
    _spawn('hive_drone', ['swamp', 'jungle'], 1, (2, 4), night=True)
    ctx.lang += [f'entity.{NS}:hive_drone.name=Hive Drone', f'item.spawn_egg.entity.{NS}:hive_drone.name=Hive Drone Spawn Egg']

    comps = {
        'minecraft:type_family': {'family': ['bc_hive', 'bc_egg', 'monster']},
        'minecraft:health': {'value': 12, 'max': 12},
        'minecraft:collision_box': {'width': 0.8, 'height': 0.8},
        'minecraft:physics': {},
        'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': False},
        'minecraft:knockback_resistance': {'value': 1.0},
        'minecraft:movement': {'value': 0.0},
        'minecraft:persistent': {},
        'minecraft:loot': {'table': 'loot_tables/entities/bc_hive_egg.json'},
        'minecraft:damage_sensor': {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'drowning', 'deals_damage': 'no'}]},
    }
    write_json(BP, 'entities/v7/hive_egg.json', _entity('hive_egg', comps))
    g = v7.egg_geo()
    g.write(out.path(RP, 'models/entity/bc/hive_egg.geo.json'), out.path(RP, 'textures/entity/bc/hive_egg.png'))
    ea = v7.egg_animations()
    ctx.animations['entity/hive_egg.animation.json'] = ea
    _client('hive_egg', 'geometry.bc.hive_egg', 'textures/entity/bc/hive_egg', 'entity_emissive_alpha', {'pulse': 'animation.bc.hive_egg.pulse'}, ['pulse'],
            egg={'base_color': '#8aa03a', 'overlay_color': '#eaffb0'})
    ctx.lang += [f'entity.{NS}:hive_egg.name=Hive Egg', f'item.spawn_egg.entity.{NS}:hive_egg.name=Hive Egg Spawn Egg']

    comps = mob_base('hive_queen', ['bc_hive', 'bc_boss', 'monster', 'mob', 'boss', 'arthropod'], 900, (2.2, 2.0), 0.26, 'loot_tables/entities/bc_hive_queen.json', 320)
    comps.update(_melee_ai(8, targets=('player', 'bc_knight', 'bc_navy', 'villager')))
    comps['minecraft:boss'] = {'should_darken_sky': True, 'hud_range': 64}
    comps['minecraft:knockback_resistance'] = {'value': 1.0}
    comps['minecraft:persistent'] = {}
    comps.pop('minecraft:despawn', None)
    write_json(BP, 'entities/v7/hive_queen.json', _entity('hive_queen', comps))
    g = v7.queen_geo()
    g.write(out.path(RP, 'models/entity/bc/hive_queen.geo.json'), out.path(RP, 'textures/entity/bc/hive_queen.png'))
    qa = v7.queen_animations()
    ctx.animations['entity/hive_queen.animation.json'] = qa
    _client('hive_queen', 'geometry.bc.hive_queen', 'textures/entity/bc/hive_queen', 'entity_alphatest', {k.split('.')[-1]: k for k in qa},
            ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look_at_target'], egg={'base_color': '#4a3410', 'overlay_color': '#f0c040'})
    ctx.lang += [f'entity.{NS}:hive_queen.name=§e§lThe Hive Queen', f'item.spawn_egg.entity.{NS}:hive_queen.name=Hive Queen Spawn Egg']

    # ---------------------------------------------------------------- the Grimoire Devourer
    comps = mob_base('grimoire_devourer', ['bc_devil', 'bc_magic', 'bc_boss', 'monster', 'mob', 'boss'], 800, (1.6, 2.6), 0.3,
                     'loot_tables/entities/bc_grimoire_devourer.json', 340)
    _flyer(comps, [2, 4], 0.2)
    comps['minecraft:boss'] = {'should_darken_sky': True, 'hud_range': 64}
    comps['minecraft:behavior.nearest_attackable_target'] = {'priority': 2, 'must_see': False, 'reselect_targets': True, 'entity_types': [
        {'filters': {'any_of': [{'test': 'is_family', 'subject': 'other', 'value': f} for f in ('player', 'bc_knight', 'bc_navy')]}, 'max_dist': 40}]}
    comps.update(keep_distance(['player', 'bc_knight'], 7.0))
    write_json(BP, 'entities/v7/grimoire_devourer.json', _entity('grimoire_devourer', comps))
    g = v7.devourer_geo()
    g.write(out.path(RP, 'models/entity/bc/grimoire_devourer.geo.json'), out.path(RP, 'textures/entity/bc/grimoire_devourer.png'))
    va = v7.devourer_animations()
    ctx.animations['entity/grimoire_devourer.animation.json'] = va
    _client('grimoire_devourer', 'geometry.bc.grimoire_devourer', 'textures/entity/bc/grimoire_devourer', 'entity_emissive_alpha',
            {**{k.split('.')[-1]: k for k in va}, 'aura': 'animation.bc.mob.aura'}, ['float', 'look_at_target', 'aura'],
            particles={'aura': 'bc:devil_aura'}, egg={'base_color': '#200a18', 'overlay_color': '#e02020'})
    ctx.lang += [f'entity.{NS}:grimoire_devourer.name=§5§lThe Grimoire Devourer', f'item.spawn_egg.entity.{NS}:grimoire_devourer.name=Grimoire Devourer Spawn Egg']


def build(ctx: Ctx):
    gen_items(ctx)
    gen_loot(ctx)
    gen_entities(ctx)
