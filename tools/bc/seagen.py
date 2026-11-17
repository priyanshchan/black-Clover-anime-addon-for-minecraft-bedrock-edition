"""Abyssal Seas expansion: items, blocks, entities, loot, recipes, spawn rules (BP + RP)."""
from __future__ import annotations

from . import icons, out
from .data import FRUITS, NS
from .models import mobs, sea
from .out import BP, RP, write_json, write_png
from .packgen import ENTITY_FMT, ITEM_FMT, Ctx, item_json, mob_base, shaped


def _tex_item(ctx, key, arr):
    icon = f'bc_{key}'
    ctx.item_textures[icon] = f'textures/items/bc/{key}'
    write_png(RP, f'textures/items/bc/{key}.png', arr)
    return icon


def gen_items(ctx: Ctx):
    ic = icons.sea_icons()
    usable = {'minecraft:use_modifiers': {'use_duration': 0.6, 'movement_modifier': 1.0}}
    # ---------------------------------------------------------------- fruits (eaten)
    for fid, f in FRUITS.items():
        icon = _tex_item(ctx, f'fruit_{fid}', ic[f'fruit_{fid}'])
        write_json(BP, f'items/sea/fruit_{fid}.json', item_json(f'{NS}:fruit_{fid}', f"{f['mc']}{f['name']} §8(Abyss Fruit)", icon, {
            'minecraft:max_stack_size': {'value': 1},
            'minecraft:food': {'nutrition': 2, 'saturation_modifier': 0.1, 'can_always_eat': True},
            'minecraft:use_modifiers': {'use_duration': 1.6, 'movement_modifier': 0.35},
            'minecraft:use_animation': 'eat',
            'minecraft:tags': {'tags': ['bc:abyss_fruit']},
        }))
        # power item (cast fruit abilities) with an aura on the casting arm
        picon = _tex_item(ctx, f'power_{fid}', ic[f'power_{fid}'])
        write_json(BP, f'items/sea/power_{fid}.json', item_json(f'{NS}:power_{fid}', f"{f['mc']}{f['power']} §7(Abyss Power)", picon, {
            'minecraft:max_stack_size': {'value': 1},
            'minecraft:can_destroy_in_creative': {'value': False},
            'minecraft:tags': {'tags': ['bc:abyss_power']},
            **usable,
        }))
        g = sea.power_geo(fid)
        g.write(out.path(RP, f'models/entity/bc/power_{fid}.geo.json'), out.path(RP, f'textures/entity/bc/power_{fid}.png'))
        write_json(RP, f'attachables/power_{fid}.json', {
            'format_version': '1.10.0',
            'minecraft:attachable': {'description': {
                'identifier': f'{NS}:power_{fid}',
                'materials': {'default': 'entity_emissive_alpha'},
                'textures': {'default': f'textures/entity/bc/power_{fid}'},
                'geometry': {'default': f'geometry.bc.power_{fid}'},
                'animations': {'aura': 'animation.bc.power.aura'},
                'scripts': {'animate': ['aura']},
                'render_controllers': ['controller.render.bc.attachable'],
            }},
        })
    ctx.animations['attachables/powers.animation.json'] = sea.power_animations()
    # ---------------------------------------------------------------- sea gear
    specs = {
        'ship_kit': ('§6Sailing Ship', {'minecraft:max_stack_size': {'value': 1}, **usable}),
        'cannonball': ('§7Cannonball', {'minecraft:max_stack_size': {'value': 64}, **usable}),
        'doubloon': ('§eDoubloon', {'minecraft:max_stack_size': {'value': 64}}),
        'leviathan_lure': ('§3Leviathan Lure', {'minecraft:max_stack_size': {'value': 1}, 'minecraft:glint': {'value': True}, **usable}),
        'leviathan_scale': ('§3Leviathan Scale', {'minecraft:max_stack_size': {'value': 16}, **usable}),
    }
    for key, (name, comps) in specs.items():
        icon = _tex_item(ctx, key, ic[key])
        write_json(BP, f'items/sea/{key}.json', item_json(f'{NS}:{key}', name, icon, comps))


def gen_block(ctx: Ctx):
    g = sea.bounty_board_geo()
    g.paint()
    a = g.atlas
    a[..., 3] = (a[..., 3] > 0) * 255.0
    write_json(RP, 'models/blocks/bc/bounty_board.geo.json', g.to_json())
    write_png(RP, 'textures/blocks/bc/bounty_board.png', a)
    ctx.terrain_textures['bc_bounty_board'] = 'textures/blocks/bc/bounty_board'
    dirs = {'north': 0, 'east': -90, 'south': 180, 'west': 90}
    write_json(BP, 'blocks/bounty_board.json', {
        'format_version': '1.21.90',
        'minecraft:block': {
            'description': {
                'identifier': f'{NS}:bounty_board',
                'menu_category': {'category': 'items'},
                'traits': {'minecraft:placement_direction': {'enabled_states': ['minecraft:cardinal_direction'], 'y_rotation_offset': 180}},
            },
            'components': {
                'minecraft:geometry': 'geometry.bc.bounty_board',
                'minecraft:material_instances': {'*': {'texture': 'bc_bounty_board', 'render_method': 'alpha_test'}},
                'minecraft:collision_box': {'origin': [-8, 0, -2], 'size': [16, 16, 4]},
                'minecraft:selection_box': {'origin': [-8, 0, -2], 'size': [16, 16, 4]},
                'minecraft:destructible_by_mining': {'seconds_to_destroy': 1.5},
                'minecraft:destructible_by_explosion': {'explosion_resistance': 5},
                'minecraft:flammable': {'catch_chance_modifier': 5, 'destroy_chance_modifier': 20},
                'minecraft:light_dampening': 0,
                'minecraft:map_color': '#7a5a37',
                'bc:bounty_logic': {},
            },
            'permutations': [
                {'condition': f"q.block_state('minecraft:cardinal_direction') == '{d}'",
                 'components': {'minecraft:transformation': {'rotation': [0, r, 0]}}}
                for d, r in dirs.items()
            ],
        },
    })
    ctx.lang.append(f'tile.{NS}:bounty_board.name=§6Bounty Board')


def gen_recipes(ctx: Ctx):
    write_json(BP, 'recipes/sea/ship_kit.json', shaped('ship_kit', [' W ', 'PIP', 'PPP'], {
        'W': 'minecraft:white_wool', 'P': 'minecraft:oak_planks', 'I': 'minecraft:iron_ingot'}))
    write_json(BP, 'recipes/sea/bounty_board.json', shaped('bounty_board', ['PPP', 'XXX', 'S S'], {
        'P': 'minecraft:oak_planks', 'X': 'minecraft:paper', 'S': 'minecraft:stick'}))
    for name, ingredients, count in (
        ('cannonball', ['minecraft:iron_ingot', 'minecraft:gunpowder'], 4),
        ('leviathan_lure', ['minecraft:heart_of_the_sea', 'minecraft:prismarine_crystals', f'{NS}:mana_crystal', f'{NS}:mana_crystal'], 1),
    ):
        write_json(BP, f'recipes/sea/{name}.json', {
            'format_version': '1.20.10',
            'minecraft:recipe_shapeless': {
                'description': {'identifier': f'{NS}:{name}'},
                'tags': ['crafting_table'],
                'ingredients': [{'item': i} for i in ingredients],
                'unlock': {'context': 'AlwaysUnlocked'},
                'result': {'item': f'{NS}:{name}', 'count': count},
            },
        })


def gen_loot(ctx: Ctx):
    def coins(lo, hi):
        return {'rolls': 1, 'entries': [{'type': 'item', 'name': f'{NS}:doubloon', 'weight': 1,
                                         'functions': [{'function': 'set_count', 'count': {'min': lo, 'max': hi}},
                                                       {'function': 'looting_enchant', 'count': {'min': 0, 'max': 2}}]}]}
    write_json(BP, 'loot_tables/entities/bc_sea_raider.json', {'pools': [
        coins(1, 4),
        {'rolls': 1, 'entries': [{'type': 'item', 'name': 'minecraft:gunpowder', 'weight': 1}, {'type': 'item', 'name': f'{NS}:cannonball', 'weight': 1,
                                  'functions': [{'function': 'set_count', 'count': {'min': 1, 'max': 3}}]}, {'type': 'empty', 'weight': 3}]},
    ]})
    write_json(BP, 'loot_tables/entities/bc_raider_captain.json', {'pools': [
        coins(15, 30),
        {'rolls': 1, 'entries': [{'type': 'item', 'name': f'{NS}:cannonball', 'weight': 1, 'functions': [{'function': 'set_count', 'count': {'min': 4, 'max': 8}}]}]},
        {'rolls': 1, 'entries': [{'type': 'item', 'name': 'minecraft:emerald', 'weight': 1, 'functions': [{'function': 'set_count', 'count': {'min': 1, 'max': 4}}]}, {'type': 'empty', 'weight': 1}]},
    ]})
    write_json(BP, 'loot_tables/entities/bc_leviathan.json', {'pools': [
        {'rolls': 1, 'entries': [{'type': 'item', 'name': f'{NS}:leviathan_scale', 'weight': 1, 'functions': [{'function': 'set_count', 'count': {'min': 3, 'max': 6}}]}]},
        coins(80, 120),
        {'rolls': 1, 'entries': [{'type': 'item', 'name': 'minecraft:heart_of_the_sea', 'weight': 1}]},
        {'rolls': 1, 'entries': [{'type': 'item', 'name': 'minecraft:trident', 'weight': 1}, {'type': 'empty', 'weight': 2}]},
    ]})
    write_json(BP, 'loot_tables/entities/bc_ship.json', {'pools': [
        {'rolls': 1, 'entries': [{'type': 'item', 'name': f'{NS}:ship_kit', 'weight': 1}]}]})
    write_json(BP, 'loot_tables/entities/bc_empty.json', {'pools': []})


def _client(ident, geo, texture, material, animations, animate, rc='controller.render.bc.default', particles=None, egg=None, scale=None, extra_scripts=None):
    d = {
        'identifier': f'{NS}:{ident}',
        'materials': {'default': material},
        'textures': {'default': texture},
        'geometry': {'default': geo},
        'animations': animations,
        'scripts': {'animate': animate},
        'render_controllers': [rc],
    }
    if particles:
        d['particle_effects'] = particles
    if egg:
        d['spawn_egg'] = egg
    if scale:
        d['scripts']['scale'] = scale
    if extra_scripts:
        d['scripts'].update(extra_scripts)
    write_json(RP, f'entity/bc/{ident}.entity.json', {'format_version': '1.10.0', 'minecraft:client_entity': {'description': d}})


def _projectile(ident, box, life, trail, geo_fn, power=1.6, gravity=0.0, kind='projectile', material='entity_alphatest', scale=None, name='', ctx=None):
    g, anims = geo_fn()
    g.write(out.path(RP, f'models/entity/bc/{ident}.geo.json'), out.path(RP, f'textures/entity/bc/{ident}.png'))
    comps = {
        'minecraft:collision_box': {'width': box, 'height': box},
        'minecraft:type_family': {'family': ['bc_spell', 'inanimate']},
        'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': False},
        'minecraft:physics': {},
        'minecraft:timer': {'looping': False, 'time': life, 'randomInterval': False, 'time_down_event': {'event': 'bc:expire', 'target': 'self'}},
        'minecraft:projectile': {'on_hit': {'remove_on_hit': {}}, 'power': power, 'gravity': gravity, 'inertia': 1.0, 'liquid_inertia': 0.9,
                                 'uncertainty_base': 0.0, 'uncertainty_multiplier': 0.0, 'anchor': 1, 'offset': [0, -0.1, 0]},
        'minecraft:conditional_bandwidth_optimization': {'default_values': {'max_optimized_distance': 96.0, 'max_dropped_ticks': 4, 'use_motion_prediction_hints': True}},
    }
    write_json(BP, f'entities/sea/{ident}.json', {
        'format_version': ENTITY_FMT,
        'minecraft:entity': {
            'description': {'identifier': f'{NS}:{ident}', 'is_spawnable': False, 'is_summonable': True},
            'component_groups': {'bc:expire': {'minecraft:instant_despawn': {}}},
            'components': comps,
            'events': {'bc:expire': {'add': {'component_groups': ['bc:expire']}}},
        },
    })
    ids = {k.split('.')[-1]: k for k in anims}
    ids['trail'] = 'animation.bc.spell.trail'
    _client(ident, f'geometry.bc.{ident}', f'textures/entity/bc/{ident}', material, ids, list(ids), particles={'trail': trail}, scale=scale)
    ctx.animations.setdefault('entity/sea_projectiles.animation.json', {}).update(anims)
    ctx.lang.append(f'entity.{NS}:{ident}.name={name}')


def gen_entities(ctx: Ctx):
    # ---------------------------------------------------------------- projectiles
    _projectile('boulder', 0.8, 4, 'bc:trail_dust', sea.boulder, name='Boulder', ctx=ctx)
    _projectile('meteor', 1.4, 6, 'bc:trail_flame_big', sea.meteor, material='entity_emissive_alpha', scale='1.6', name='Falling Star', ctx=ctx)
    _projectile('cannonball', 0.5, 6, 'bc:trail_dust', sea.cannonball, gravity=0.025, name='Cannonball', ctx=ctx)
    _projectile('metal_blade', 0.5, 3, 'bc:trail_light', sea.metal_blade, name='Mercury Blade', ctx=ctx)

    # ---------------------------------------------------------------- the ship
    g = sea.ship_geo()
    g.write(out.path(RP, 'models/entity/bc/sail_ship.geo.json'), out.path(RP, 'textures/entity/bc/sail_ship.png'))
    ctx.animations['entity/sail_ship.animation.json'] = sea.ship_animations()
    write_json(BP, 'entities/sea/sail_ship.json', {
        'format_version': ENTITY_FMT,
        'minecraft:entity': {
            'description': {'identifier': f'{NS}:sail_ship', 'is_spawnable': False, 'is_summonable': True},
            'components': {
                'minecraft:type_family': {'family': ['bc_ship', 'inanimate']},
                'minecraft:health': {'value': 120, 'max': 120},
                'minecraft:collision_box': {'width': 2.6, 'height': 1.1},
                'minecraft:physics': {},
                'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': True},
                'minecraft:buoyant': {'base_buoyancy': 1.0, 'apply_gravity': False, 'can_auto_step_from_liquid': False,
                                      'movement_type': 'bobbing', 'liquid_blocks': ['minecraft:water', 'minecraft:flowing_water']},
                'minecraft:rideable': {
                    'seat_count': 4, 'crouching_skip_interact': True, 'family_types': ['player'],
                    'interact_text': 'action.interact.ride.boat', 'pull_in_entities': False,
                    'seats': [{'position': [0.0, 1.15, -0.7]}, {'position': [0.0, 0.8, 0.5]},
                              {'position': [-0.35, 0.8, 1.2]}, {'position': [0.35, 0.8, -0.1]}],
                },
                'minecraft:knockback_resistance': {'value': 1.0},
                'minecraft:damage_sensor': {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'drowning', 'deals_damage': 'no'},
                                                         {'cause': 'suffocation', 'deals_damage': 'no'}, {'cause': 'lightning', 'deals_damage': 'no'}]},
                'minecraft:nameable': {},
                'minecraft:persistent': {},
                'minecraft:loot': {'table': 'loot_tables/entities/bc_ship.json'},
                'minecraft:conditional_bandwidth_optimization': {},
            },
            'events': {},
        },
    })
    _client('sail_ship', 'geometry.bc.sail_ship', 'textures/entity/bc/sail_ship', 'entity_emissive_alpha',
            {'sail': 'animation.bc.sail_ship.sail', 'wake': 'animation.bc.ship.wake'}, ['sail', 'wake'],
            particles={'wake': 'bc:ship_wake'})
    ctx.animations['entity/sail_ship.animation.json']['animation.bc.ship.wake'] = {
        'loop': 'hold_on_last_frame', 'animation_length': 0.05, 'particle_effects': {'0.0': {'effect': 'wake'}}}
    ctx.lang.append(f'entity.{NS}:sail_ship.name=Sailing Ship')

    # ---------------------------------------------------------------- Sea Raider
    comps = mob_base('sea_raider', ['bc_pirate', 'monster', 'mob'], 28, (0.6, 1.9), 0.3, 'loot_tables/entities/bc_sea_raider.json', 8)
    comps.update(_melee_ai(4, targets=('player', 'irongolem', 'villager', 'bc_shade')))
    write_json(BP, 'entities/sea/sea_raider.json', _entity('sea_raider', comps, spawnable=True))
    g = sea.raider_geo()
    g.write(out.path(RP, 'models/entity/bc/sea_raider.geo.json'), out.path(RP, 'textures/entity/bc/sea_raider.png'))
    ra = sea.humanoid_animations('sea_raider')
    ctx.animations['entity/sea_raider.animation.json'] = ra
    _client('sea_raider', 'geometry.bc.sea_raider', 'textures/entity/bc/sea_raider', 'entity_alphatest',
            {'idle': 'animation.bc.sea_raider.idle', 'walk': 'animation.bc.sea_raider.walk', 'look': 'animation.bc.sea_raider.look_at_target'},
            ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look'], egg={'base_color': '#1d2f5a', 'overlay_color': '#b32a2c'})
    ctx.lang += [f'entity.{NS}:sea_raider.name=Sea Raider', f'item.spawn_egg.entity.{NS}:sea_raider.name=Sea Raider Spawn Egg']
    write_json(BP, 'spawn_rules/sea_raider.json', {
        'format_version': '1.8.0',
        'minecraft:spawn_rules': {
            'description': {'identifier': f'{NS}:sea_raider', 'population_control': 'monster'},
            'conditions': [{
                'minecraft:spawns_on_surface': {},
                'minecraft:brightness_filter': {'min': 0, 'max': 7, 'adjust_for_weather': True},
                'minecraft:difficulty_filter': {'min': 'easy', 'max': 'hard'},
                'minecraft:weight': {'default': 12},
                'minecraft:herd': {'min_size': 2, 'max_size': 3},
                'minecraft:density_limit': {'surface': 4},
                'minecraft:biome_filter': {'test': 'has_biome_tag', 'value': 'beach'},
            }],
        },
    })

    # ---------------------------------------------------------------- Raider Captain
    comps = mob_base('raider_captain', ['bc_pirate', 'bc_captain', 'monster', 'mob'], 90, (0.7, 2.05), 0.31, 'loot_tables/entities/bc_raider_captain.json', 40)
    comps.update(_melee_ai(8, targets=('player', 'irongolem', 'villager', 'bc_shade')))
    comps['minecraft:knockback_resistance'] = {'value': 0.5}
    comps['minecraft:persistent'] = {}
    write_json(BP, 'entities/sea/raider_captain.json', _entity('raider_captain', comps, spawnable=True))
    g = sea.captain_geo()
    g.write(out.path(RP, 'models/entity/bc/raider_captain.geo.json'), out.path(RP, 'textures/entity/bc/raider_captain.png'))
    ctx.animations['entity/raider_captain.animation.json'] = sea.humanoid_animations('raider_captain')
    _client('raider_captain', 'geometry.bc.raider_captain', 'textures/entity/bc/raider_captain', 'entity_alphatest',
            {'idle': 'animation.bc.raider_captain.idle', 'walk': 'animation.bc.raider_captain.walk', 'look': 'animation.bc.raider_captain.look_at_target'},
            ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look'], egg={'base_color': '#6a1018', 'overlay_color': '#f0c24a'})
    ctx.lang += [f'entity.{NS}:raider_captain.name=Raider Captain', f'item.spawn_egg.entity.{NS}:raider_captain.name=Raider Captain Spawn Egg']

    # ---------------------------------------------------------------- Shade Soldier (Shadow Fruit summon)
    comps = mob_base('shade_soldier', ['bc_shade', 'mob'], 30, (0.6, 1.95), 0.33, 'loot_tables/entities/bc_empty.json', 0)
    comps.update(_melee_ai(6, targets=('monster',)))
    comps['minecraft:timer'] = {'looping': False, 'time': 25, 'randomInterval': False, 'time_down_event': {'event': 'bc:expire', 'target': 'self'}}
    comps['minecraft:damage_sensor'] = {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'drowning', 'deals_damage': 'no'}]}
    ent = _entity('shade_soldier', comps)
    ent['minecraft:entity']['component_groups'] = {'bc:expire': {'minecraft:instant_despawn': {}}}
    ent['minecraft:entity']['events'] = {'bc:expire': {'add': {'component_groups': ['bc:expire']}}}
    write_json(BP, 'entities/sea/shade_soldier.json', ent)
    g = mobs.disciple_geo('shade')
    g.write(out.path(RP, 'models/entity/bc/shade_soldier.geo.json'), out.path(RP, 'textures/entity/bc/shade_soldier.png'))
    _client('shade_soldier', 'geometry.bc.shade_soldier', 'textures/entity/bc/shade_soldier', 'entity_emissive_alpha',
            {'idle': 'animation.bc.dark_disciple.idle', 'walk': 'animation.bc.dark_disciple.walk',
             'look': 'animation.bc.dark_disciple.look_at_target', 'aura': 'animation.bc.mob.aura'},
            ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look', 'aura'], particles={'aura': 'bc:disciple_aura'})
    ctx.lang.append(f'entity.{NS}:shade_soldier.name=Shade Soldier')

    # ---------------------------------------------------------------- Abyssal Leviathan
    comps = mob_base('leviathan', ['bc_leviathan', 'monster', 'mob', 'boss'], 600, (2.6, 2.4), 0.3, 'loot_tables/entities/bc_leviathan.json', 500)
    comps.pop('minecraft:breathable')
    comps.pop('minecraft:hurt_on_condition')
    comps.update({
        'minecraft:boss': {'should_darken_sky': False, 'hud_range': 64},
        'minecraft:breathable': {'breathes_water': True, 'breathes_air': True, 'generates_bubbles': False},
        'minecraft:physics': {'has_gravity': False},
        'minecraft:underwater_movement': {'value': 0.3},
        'minecraft:navigation.generic': {'is_amphibious': True, 'can_path_over_water': False, 'can_swim': True, 'can_walk': False, 'can_breach': True, 'can_sink': False},
        'minecraft:movement.basic': {},
        'minecraft:attack': {'damage': 16},
        'minecraft:knockback_resistance': {'value': 1.0},
        'minecraft:persistent': {},
        'minecraft:fire_immune': True,
        'minecraft:damage_sensor': {'triggers': [{'cause': 'drowning', 'deals_damage': 'no'}, {'cause': 'suffocation', 'deals_damage': 'no'},
                                                 {'cause': 'fall', 'deals_damage': 'no'}]},
        'minecraft:behavior.hurt_by_target': {'priority': 1},
        'minecraft:behavior.nearest_attackable_target': {'priority': 2, 'must_see': False, 'within_radius': 48, 'reselect_targets': True,
                                                          'entity_types': [{'filters': {'test': 'is_family', 'subject': 'other', 'value': 'player'}, 'max_dist': 48}]},
        'minecraft:behavior.swim_wander': {'priority': 5, 'interval': 0.1, 'look_ahead': 5.0, 'speed_multiplier': 1.0, 'wander_time': 4.0},
    })
    write_json(BP, 'entities/sea/leviathan.json', _entity('leviathan', comps))
    g = sea.leviathan_geo()
    g.write(out.path(RP, 'models/entity/bc/leviathan.geo.json'), out.path(RP, 'textures/entity/bc/leviathan.png'))
    ctx.animations['entity/leviathan.animation.json'] = sea.leviathan_animations()
    _client('leviathan', 'geometry.bc.leviathan', 'textures/entity/bc/leviathan', 'entity_emissive_alpha',
            {'swim': 'animation.bc.leviathan.swim', 'aura': 'animation.bc.mob.aura'}, ['swim', 'aura'],
            particles={'aura': 'bc:leviathan_bubbles'}, egg={'base_color': '#0b2b3a', 'overlay_color': '#7affe8'}, scale='1.3')
    ctx.lang += [f'entity.{NS}:leviathan.name=§3Abyssal Leviathan', f'item.spawn_egg.entity.{NS}:leviathan.name=Abyssal Leviathan Spawn Egg']


def _entity(ident, comps, spawnable=False):
    return {
        'format_version': ENTITY_FMT,
        'minecraft:entity': {
            'description': {'identifier': f'{NS}:{ident}', 'is_spawnable': spawnable, 'is_summonable': True},
            'components': comps,
            'events': {},
        },
    }


def _melee_ai(damage, targets):
    return {
        'minecraft:navigation.walk': {'can_path_over_water': True, 'can_swim': True, 'avoid_water': False, 'can_open_doors': True, 'avoid_damage_blocks': True},
        'minecraft:movement.basic': {},
        'minecraft:jump.static': {},
        'minecraft:can_climb': {},
        'minecraft:attack': {'damage': damage},
        'minecraft:despawn': {'despawn_from_distance': {}},
        'minecraft:behavior.float': {'priority': 0},
        'minecraft:behavior.hurt_by_target': {'priority': 1},
        'minecraft:behavior.melee_box_attack': {'priority': 2, 'speed_multiplier': 1.2, 'track_target': True},
        'minecraft:behavior.nearest_attackable_target': {
            'priority': 3, 'must_see': True, 'reselect_targets': True,
            'entity_types': [{'filters': {'any_of': [{'test': 'is_family', 'subject': 'other', 'value': t} for t in targets]}, 'max_dist': 20}]},
        'minecraft:behavior.random_stroll': {'priority': 6, 'speed_multiplier': 0.9},
        'minecraft:behavior.look_at_player': {'priority': 7, 'look_distance': 8, 'probability': 0.03},
        'minecraft:behavior.random_look_around': {'priority': 8},
    }


def build(ctx: Ctx):
    gen_items(ctx)
    gen_block(ctx)
    gen_recipes(ctx)
    gen_loot(ctx)
    gen_entities(ctx)
