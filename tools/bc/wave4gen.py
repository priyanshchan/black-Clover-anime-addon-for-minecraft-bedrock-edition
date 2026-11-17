"""Wave 4 pack content: the mana bolt, Magic Knights, merchant, constructs, four giant bosses, the devil gate,
phantom crew, the War Table, boss summoning items, faction targeting and War Table team groups."""
from __future__ import annotations

import copy
import json

from . import out, tex
from .data import FACTIONS, KNIGHT_ROBES, NS
from .fx import tint_script
from .models import grand, mobs, sea, wave4
from .out import BP, RP, write_json, write_png
from .packgen import ENTITY_FMT, Ctx, item_json, mob_base, shaped
from .seagen import _client, _entity, _melee_ai


def _icon(ctx, key, arr):
    icon = f'bc_{key}'
    ctx.item_textures[icon] = f'textures/items/bc/{key}'
    write_png(RP, f'textures/items/bc/{key}.png', arr)
    return icon


def _load(rel):
    with open(out.path(BP, rel)) as fh:
        return json.load(fh)


# ======================================================================================
# items, block, recipes, loot
# ======================================================================================
def gen_items(ctx: Ctx):
    ic = wave4.wave4_icons()
    usable = {'minecraft:use_modifiers': {'use_duration': 0.6, 'movement_modifier': 1.0}}
    specs = {
        'archdevil_sigil': ('§4Archdevil Sigil', True),
        'colossus_core': ('§6Colossus Core', True),
        'galleon_bell': ('§3Phantom Galleon Bell', True),
        'kraken_lure': ('§9Storm Kraken Lure', True),
        'knight_contract': ('§aKnight Contract', False),
        'skirmish_horn': ('§eSkirmish Horn', False),
    }
    for key, (name, glint) in specs.items():
        write_json(BP, f'items/living/{key}.json', item_json(f'{NS}:{key}', name, _icon(ctx, key, ic[key]), {
            'minecraft:max_stack_size': {'value': 1 if key != 'knight_contract' else 16},
            'minecraft:glint': {'value': glint}, **usable}))
    _icon(ctx, 'war_table', ic['war_table'])


def gen_block(ctx: Ctx):
    g = wave4.war_table_geo()
    g.paint()
    a = g.atlas
    a[..., 3] = (a[..., 3] > 0) * 255.0
    write_json(RP, 'models/blocks/bc/war_table.geo.json', g.to_json())
    write_png(RP, 'textures/blocks/bc/war_table.png', a)
    ctx.terrain_textures['bc_war_table'] = 'textures/blocks/bc/war_table'
    dirs = {'north': 0, 'east': -90, 'south': 180, 'west': 90}
    write_json(BP, 'blocks/war_table.json', {
        'format_version': '1.21.90',
        'minecraft:block': {
            'description': {
                'identifier': f'{NS}:war_table',
                'menu_category': {'category': 'items'},
                'traits': {'minecraft:placement_direction': {'enabled_states': ['minecraft:cardinal_direction'], 'y_rotation_offset': 180}},
            },
            'components': {
                'minecraft:geometry': 'geometry.bc.war_table',
                'minecraft:material_instances': {'*': {'texture': 'bc_war_table', 'render_method': 'alpha_test'}},
                'minecraft:collision_box': {'origin': [-8, 0, -8], 'size': [16, 13, 16]},
                'minecraft:selection_box': {'origin': [-8, 0, -8], 'size': [16, 16, 16]},
                'minecraft:destructible_by_mining': {'seconds_to_destroy': 2.0},
                'minecraft:destructible_by_explosion': {'explosion_resistance': 6},
                'minecraft:flammable': {'catch_chance_modifier': 5, 'destroy_chance_modifier': 20},
                'minecraft:light_dampening': 0,
                'minecraft:map_color': '#8a6a40',
                'bc:war_table': {},
            },
            'permutations': [
                {'condition': f"q.block_state('minecraft:cardinal_direction') == '{d}'",
                 'components': {'minecraft:transformation': {'rotation': [0, r, 0]}}}
                for d, r in dirs.items()
            ],
        },
    })
    ctx.lang.append(f'tile.{NS}:war_table.name=§6War Table')


def gen_recipes(ctx: Ctx):
    write_json(BP, 'recipes/living/war_table.json', shaped('war_table', ['MBF', 'PPP', 'S S'], {
        'M': 'minecraft:map', 'B': 'minecraft:iron_sword', 'F': 'minecraft:feather', 'P': 'minecraft:oak_planks', 'S': 'minecraft:stick'}))
    write_json(BP, 'recipes/living/skirmish_horn.json', shaped('skirmish_horn', ['  B', ' G ', 'G  '], {
        'B': 'minecraft:bone', 'G': 'minecraft:gold_ingot'}))
    write_json(BP, 'recipes/living/knight_contract.json', shaped('knight_contract', ['EPE', 'PCP', 'EPE'], {
        'E': 'minecraft:emerald', 'P': 'minecraft:paper', 'C': f'{NS}:mana_crystal'}))
    write_json(BP, 'recipes/living/archdevil_sigil.json', shaped('archdevil_sigil', ['OCO', 'CHC', 'OCO'], {
        'O': 'minecraft:crying_obsidian', 'C': f'{NS}:mana_crystal', 'H': f'{NS}:devil_heart'}))
    write_json(BP, 'recipes/living/colossus_core.json', shaped('colossus_core', ['SPS', 'PDP', 'SPS'], {
        'S': 'minecraft:mossy_cobblestone', 'P': f'{NS}:ancient_page', 'D': 'minecraft:diamond_block'}))
    write_json(BP, 'recipes/living/galleon_bell.json', shaped('galleon_bell', ['MDM', 'DBD', 'MDM'], {
        'M': 'minecraft:phantom_membrane', 'D': f'{NS}:doubloon', 'B': 'minecraft:bell'}))
    write_json(BP, 'recipes/living/kraken_lure.json', shaped('kraken_lure', ['SLS', 'LHL', 'SLS'], {
        'S': f'{NS}:leviathan_scale', 'L': 'minecraft:lightning_rod', 'H': 'minecraft:heart_of_the_sea'}))


def gen_loot(ctx: Ctx):
    def pool(item, lo, hi, chance=1.0):
        entries = [{'type': 'item', 'name': item, 'weight': 100, 'functions': [{'function': 'set_count', 'count': {'min': lo, 'max': hi}}]}]
        if chance < 1:
            entries.append({'type': 'empty', 'weight': int(100 * (1 - chance) / max(chance, 0.01))})
        return {'rolls': 1, 'entries': entries}
    write_json(BP, 'loot_tables/entities/bc_magic_knight.json', {'pools': [pool(f'{NS}:mana_crystal', 1, 2), pool(f'{NS}:ancient_page', 1, 1, 0.15)]})
    write_json(BP, 'loot_tables/entities/bc_archdevil.json', {'pools': [
        pool(f'{NS}:devil_heart', 2, 3), pool(f'{NS}:clover_charm', 1, 1, 0.6), pool(f'{NS}:mana_crystal', 12, 20), pool('minecraft:netherite_scrap', 2, 4),
        pool(f'{NS}:ancient_page', 3, 5)]})
    write_json(BP, 'loot_tables/entities/bc_stone_colossus.json', {'pools': [
        pool('minecraft:diamond', 4, 8), pool('minecraft:emerald', 6, 12), pool(f'{NS}:ancient_page', 4, 6), pool(f'{NS}:mana_crystal', 10, 16),
        pool(f'{NS}:clover_charm', 1, 1, 0.25)]})
    write_json(BP, 'loot_tables/entities/bc_phantom_galleon.json', {'pools': [
        pool(f'{NS}:doubloon', 120, 220), pool(f'{NS}:treasure_map', 2, 3), pool('minecraft:phantom_membrane', 4, 8), pool(f'{NS}:galleon_bell', 1, 1, 0.1)]})
    write_json(BP, 'loot_tables/entities/bc_storm_kraken.json', {'pools': [
        pool(f'{NS}:leviathan_scale', 4, 8), pool(f'{NS}:doubloon', 80, 160), pool('minecraft:heart_of_the_sea', 1, 2), pool('minecraft:trident', 1, 1, 0.5)]})
    write_json(BP, 'loot_tables/entities/bc_phantom_raider.json', {'pools': [pool(f'{NS}:doubloon', 1, 4), pool('minecraft:phantom_membrane', 0, 1)]})
    write_json(BP, 'loot_tables/entities/bc_devil_gate.json', {'pools': [pool(f'{NS}:mana_crystal', 4, 8), pool(f'{NS}:devil_heart', 1, 1, 0.2)]})


# ======================================================================================
# entities
# ======================================================================================
def _static(ident, comps, groups=None, events=None, props=None):
    d = {'identifier': f'{NS}:{ident}', 'is_spawnable': False, 'is_summonable': True}
    if props:
        d['properties'] = props
    return {'format_version': ENTITY_FMT, 'minecraft:entity': {'description': d, 'component_groups': groups or {}, 'components': comps, 'events': events or {}}}


def gen_mana_bolt(ctx: Ctx):
    with open(out.path(RP, 'models/entity/bc/mana_bolt.geo.json'), 'w') as fh:
        json.dump(wave4.bolt_geometry_file(), fh, indent=1)
    textures = {}
    for i, (key, hexc) in enumerate(wave4.TINTS):
        write_png(RP, f'textures/entity/bc/bolt/t{i}.png', wave4.bolt_tint_texture(hexc))
        textures[f't{i}'] = f'textures/entity/bc/bolt/t{i}'
    comps = {
        'minecraft:collision_box': {'width': 0.5, 'height': 0.5},
        'minecraft:type_family': {'family': ['bc_spell', 'inanimate']},
        'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': False},
        'minecraft:physics': {},
        'minecraft:timer': {'looping': False, 'time': 4, 'randomInterval': False, 'time_down_event': {'event': 'bc:expire', 'target': 'self'}},
        'minecraft:projectile': {'on_hit': {'remove_on_hit': {}}, 'power': 1.6, 'gravity': 0.0, 'inertia': 1.0, 'liquid_inertia': 0.9,
                                 'uncertainty_base': 0.0, 'uncertainty_multiplier': 0.0, 'anchor': 1, 'offset': [0, -0.1, 0]},
        'minecraft:conditional_bandwidth_optimization': {'default_values': {'max_optimized_distance': 96.0, 'max_dropped_ticks': 4, 'use_motion_prediction_hints': True}},
    }
    props = {'bc:tint': {'type': 'int', 'range': [0, 63], 'default': 0, 'client_sync': True},
             'bc:shape': {'type': 'int', 'range': [0, 3], 'default': 0, 'client_sync': True},
             'bc:size': {'type': 'int', 'range': [0, 3], 'default': 0, 'client_sync': True}}
    heavy = copy.deepcopy(comps['minecraft:projectile'])
    heavy['gravity'] = 0.035
    write_json(BP, 'entities/living/mana_bolt.json', _static('mana_bolt', comps,
                                                           {'bc:expire': {'minecraft:instant_despawn': {}}, 'bc:heavy': {'minecraft:projectile': heavy}},
                                                           {'bc:expire': {'add': {'component_groups': ['bc:expire']}},
                                                            'bc:heavy': {'add': {'component_groups': ['bc:heavy']}}}, props))
    ctx.animations['entity/mana_bolt.animation.json'] = {
        **wave4.bolt_animations(),
        'animation.bc.mana_bolt.trail': {'loop': 'hold_on_last_frame', 'animation_length': 0.05,
                                         'particle_effects': {'0.0': {'effect': 'trail', 'pre_effect_script': tint_script(wave4.TINTS)}}},
    }
    write_json(RP, 'entity/bc/mana_bolt.entity.json', {'format_version': '1.10.0', 'minecraft:client_entity': {'description': {
        'identifier': f'{NS}:mana_bolt',
        'materials': {'default': 'entity_emissive_alpha'},
        'textures': textures,
        'geometry': {k: f'geometry.bc.bolt_{k}' for k in wave4.BOLT_SHAPES},
        'animations': {'fly': 'animation.bc.mana_bolt.fly', 'trail': 'animation.bc.mana_bolt.trail'},
        'particle_effects': {'trail': 'bc:trail_mana'},
        'scripts': {'animate': ['fly', 'trail'], 'scale': "1.0 + q.property('bc:size') * 0.55"},
        'render_controllers': ['controller.render.bc.mana_bolt'],
    }}})
    ctx.lang.append(f'entity.{NS}:mana_bolt.name=Spell')
    return {'controller.render.bc.mana_bolt': {
        'arrays': {'textures': {'Array.tints': [f'Texture.t{i}' for i in range(len(wave4.TINTS))]},
                   'geometries': {'Array.shapes': [f'Geometry.{k}' for k in wave4.BOLT_SHAPES]}},
        'geometry': "Array.shapes[q.property('bc:shape')]",
        'materials': [{'*': 'Material.default'}],
        'textures': ["Array.tints[q.property('bc:tint')]"],
    }}


def _wild_groups(comps):
    """Move despawning into a removable group so hired / War Table units stay."""
    despawn = comps.pop('minecraft:despawn', {'despawn_from_distance': {}})
    return {'bc:wild': {'minecraft:despawn': despawn}}


def gen_knight(ctx: Ctx):
    comps = mob_base('magic_knight', ['bc_knight', 'mob'], 40, (0.6, 1.95), 0.3, 'loot_tables/entities/bc_magic_knight.json', 8)
    comps.update(_melee_ai(6, targets=('monster', 'bc_pirate', 'bc_devil', 'bc_disciple')))
    comps['minecraft:behavior.nearest_attackable_target']['must_see'] = False
    comps['minecraft:behavior.nearest_attackable_target']['entity_types'][0]['max_dist'] = 24
    comps['minecraft:behavior.melee_box_attack']['priority'] = 3
    comps['minecraft:damage_sensor'] = {'triggers': [{'cause': 'fall', 'damage_multiplier': 0.5}]}
    groups = _wild_groups(comps)
    groups['bc:hired'] = {
        'minecraft:persistent': {},
        'minecraft:tameable': {'probability': 0.0, 'tame_items': 'minecraft:emerald_block'},
        'minecraft:behavior.follow_owner': {'priority': 4, 'speed_multiplier': 1.25, 'start_distance': 9, 'stop_distance': 3},
        'minecraft:behavior.owner_hurt_by_target': {'priority': 1},
        'minecraft:behavior.owner_hurt_target': {'priority': 2},
    }
    props = {'bc:robe': {'type': 'int', 'range': [0, len(KNIGHT_ROBES) - 1], 'default': 0, 'client_sync': True}}
    events = {
        'minecraft:entity_spawned': {'sequence': [
            {'add': {'component_groups': ['bc:wild']}},
            {'randomize': [{'weight': 1, 'set_property': {'bc:robe': i}} for i in range(len(KNIGHT_ROBES))]},
        ]},
        'bc:hire': {'remove': {'component_groups': ['bc:wild']}, 'add': {'component_groups': ['bc:hired']}},
    }
    ent = _entity('magic_knight', comps, spawnable=True)
    ent['minecraft:entity']['description']['properties'] = props
    ent['minecraft:entity']['component_groups'] = groups
    ent['minecraft:entity']['events'] = events
    write_json(BP, 'entities/living/magic_knight.json', ent)
    textures = {}
    for i, rid in enumerate(KNIGHT_ROBES):
        g = wave4.knight_geo(rid, i)
        g.write(out.path(RP, 'models/entity/bc/magic_knight.geo.json'), out.path(RP, f'textures/entity/bc/knight/{rid}.png'))
        textures[f'r{i}'] = f'textures/entity/bc/knight/{rid}'
    ctx.animations['entity/magic_knight.animation.json'] = wave4.knight_animations()
    write_json(RP, 'entity/bc/magic_knight.entity.json', {'format_version': '1.10.0', 'minecraft:client_entity': {'description': {
        'identifier': f'{NS}:magic_knight',
        'materials': {'default': 'entity_alphatest'},
        'textures': textures,
        'geometry': {'default': 'geometry.bc.magic_knight'},
        'animations': {'idle': 'animation.bc.magic_knight.idle', 'walk': 'animation.bc.magic_knight.walk',
                       'look': 'animation.bc.magic_knight.look_at_target', 'cast': 'animation.bc.magic_knight.cast',
                       'attack': 'animation.bc.magic_knight.attack'},
        'scripts': {'animate': ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look']},
        'render_controllers': ['controller.render.bc.magic_knight'],
        'spawn_egg': {'base_color': '#1a1a22', 'overlay_color': '#d39a2c'},
    }}})
    write_json(BP, 'spawn_rules/magic_knight.json', {
        'format_version': '1.8.0',
        'minecraft:spawn_rules': {
            'description': {'identifier': f'{NS}:magic_knight', 'population_control': 'animal'},
            'conditions': [{
                'minecraft:spawns_on_surface': {},
                'minecraft:brightness_filter': {'min': 8, 'max': 15, 'adjust_for_weather': False},
                'minecraft:weight': {'default': 3},
                'minecraft:herd': {'min_size': 1, 'max_size': 3},
                'minecraft:density_limit': {'surface': 3},
                'minecraft:biome_filter': {'any_of': [{'test': 'has_biome_tag', 'value': 'plains'}, {'test': 'has_biome_tag', 'value': 'forest'},
                                                      {'test': 'has_biome_tag', 'value': 'meadow'}, {'test': 'has_biome_tag', 'value': 'savanna'}]},
            }],
        },
    })
    ctx.lang += [f'entity.{NS}:magic_knight.name=Magic Knight', f'item.spawn_egg.entity.{NS}:magic_knight.name=Magic Knight Spawn Egg']
    return {'controller.render.bc.magic_knight': {
        'arrays': {'textures': {'Array.robes': [f'Texture.r{i}' for i in range(len(KNIGHT_ROBES))]}},
        'geometry': 'Geometry.default', 'materials': [{'*': 'Material.default'}],
        'textures': ["Array.robes[q.property('bc:robe')]"],
    }}


def gen_merchant(ctx: Ctx):
    comps = mob_base('magic_merchant', ['bc_merchant', 'mob'], 30, (0.6, 1.95), 0.22, 'loot_tables/entities/bc_empty.json', 0)
    comps.update({
        'minecraft:navigation.walk': {'can_path_over_water': True, 'avoid_water': True, 'can_open_doors': True, 'avoid_damage_blocks': True},
        'minecraft:movement.basic': {},
        'minecraft:jump.static': {},
        'minecraft:persistent': {},
        'minecraft:interact': {'interactions': [{'on_interact': {'filters': {'test': 'is_family', 'subject': 'other', 'value': 'player'}, 'event': 'bc:noop'},
                                                'interact_text': 'action.interact.trade'}]},
        'minecraft:behavior.float': {'priority': 0},
        'minecraft:behavior.panic': {'priority': 1, 'speed_multiplier': 1.3},
        'minecraft:behavior.look_at_player': {'priority': 2, 'look_distance': 8, 'probability': 0.4},
        'minecraft:behavior.random_stroll': {'priority': 6, 'speed_multiplier': 0.6, 'xz_dist': 6},
        'minecraft:damage_sensor': {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}]},
    })
    ent = _entity('magic_merchant', comps)
    ent['minecraft:entity']['component_groups'] = {'bc:leave': {'minecraft:instant_despawn': {}}}
    ent['minecraft:entity']['events'] = {'bc:noop': {}, 'bc:leave': {'add': {'component_groups': ['bc:leave']}}}
    write_json(BP, 'entities/living/magic_merchant.json', ent)
    g = wave4.merchant_geo()
    g.write(out.path(RP, 'models/entity/bc/magic_merchant.geo.json'), out.path(RP, 'textures/entity/bc/magic_merchant.png'))
    ctx.animations['entity/magic_merchant.animation.json'] = sea.humanoid_animations('magic_merchant')
    _client('magic_merchant', 'geometry.bc.magic_merchant', 'textures/entity/bc/magic_merchant', 'entity_emissive_alpha',
            {'idle': 'animation.bc.magic_merchant.idle', 'walk': 'animation.bc.magic_merchant.walk', 'look': 'animation.bc.magic_merchant.look_at_target'},
            ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look'], egg={'base_color': '#185856', 'overlay_color': '#d39a2c'})
    ctx.lang += [f'entity.{NS}:magic_merchant.name=§bTravelling Magic Merchant', f'item.spawn_egg.entity.{NS}:magic_merchant.name=Magic Merchant Spawn Egg']


def gen_construct(ctx: Ctx):
    comps = mob_base('construct', ['bc_construct', 'mob'], 50, (0.8, 2.0), 0.27, 'loot_tables/entities/bc_empty.json', 0)
    comps.update(_melee_ai(7, targets=('monster', 'bc_pirate')))
    comps['minecraft:knockback_resistance'] = {'value': 0.5}
    comps['minecraft:damage_sensor'] = {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'drowning', 'deals_damage': 'no'}]}
    comps.pop('minecraft:despawn', None)
    groups = {'bc:expire': {'minecraft:instant_despawn': {}},
              'bc:summoned': {'minecraft:timer': {'looping': False, 'time': 30, 'randomInterval': False, 'time_down_event': {'event': 'bc:expire', 'target': 'self'}}}}
    props = {'bc:variant': {'type': 'int', 'range': [0, 3], 'default': 0, 'client_sync': True}}
    events = {'bc:expire': {'add': {'component_groups': ['bc:expire']}}, 'bc:summoned': {'add': {'component_groups': ['bc:summoned']}}}
    ent = _entity('construct', comps)
    ent['minecraft:entity']['description']['properties'] = props
    ent['minecraft:entity']['component_groups'] = groups
    ent['minecraft:entity']['events'] = events
    write_json(BP, 'entities/living/construct.json', ent)
    textures = {}
    for i, kind in enumerate(wave4.CONSTRUCT_KINDS):
        g = wave4.construct_geo(kind)
        g.write(out.path(RP, 'models/entity/bc/construct.geo.json'), out.path(RP, f'textures/entity/bc/construct/{kind}.png'))
        textures[f'v{i}'] = f'textures/entity/bc/construct/{kind}'
    ctx.animations['entity/construct.animation.json'] = grand.golem_animations('construct')
    write_json(RP, 'entity/bc/construct.entity.json', {'format_version': '1.10.0', 'minecraft:client_entity': {'description': {
        'identifier': f'{NS}:construct',
        'materials': {'default': 'entity_emissive_alpha'},
        'textures': textures,
        'geometry': {'default': 'geometry.bc.construct'},
        'animations': {'idle': 'animation.bc.construct.idle', 'walk': 'animation.bc.construct.walk', 'look': 'animation.bc.construct.look_at_target',
                       'slam': 'animation.bc.construct.slam'},
        'scripts': {'animate': ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look']},
        'render_controllers': ['controller.render.bc.construct'],
        'spawn_egg': {'base_color': '#967a46', 'overlay_color': '#5ad8c0'},
    }}})
    ctx.lang += [f'entity.{NS}:construct.name=Ancient Construct', f'item.spawn_egg.entity.{NS}:construct.name=Ancient Construct Spawn Egg']
    return {'controller.render.bc.construct': {
        'arrays': {'textures': {'Array.kinds': [f'Texture.v{i}' for i in range(len(wave4.CONSTRUCT_KINDS))]}},
        'geometry': 'Geometry.default', 'materials': [{'*': 'Material.default'}],
        'textures': ["Array.kinds[q.property('bc:variant')]"],
    }}


def gen_bosses(ctx: Ctx):
    # ---------------------------------------------------------------- the Archdevil (from the Devil)
    d = _load('entities/devil.json')
    e = d['minecraft:entity']
    e['description']['identifier'] = f'{NS}:archdevil'
    c = e['components']
    c['minecraft:type_family'] = {'family': ['bc_magic', 'bc_devil', 'bc_boss', 'monster', 'mob', 'boss']}
    c['minecraft:health'] = {'value': 900, 'max': 900}
    c['minecraft:collision_box'] = {'width': 1.2, 'height': 3.6}
    c['minecraft:loot'] = {'table': 'loot_tables/entities/bc_archdevil.json'}
    c['minecraft:experience_reward'] = {'on_death': 'q.last_hit_by_player ? 400 : 0'}
    c['minecraft:boss'] = {'should_darken_sky': True, 'hud_range': 64}
    c['minecraft:attack'] = {'damage': 16}
    c['minecraft:follow_range'] = {'value': 64, 'max': 64}
    c['minecraft:knockback_resistance'] = {'value': 1.0}
    c.pop('minecraft:shooter', None)
    c.pop('minecraft:behavior.ranged_attack', None)
    c['minecraft:behavior.melee_box_attack'] = {'priority': 3, 'speed_multiplier': 1.3, 'track_target': True}
    c['minecraft:behavior.nearest_attackable_target']['entity_types'][0]['max_dist'] = 48
    write_json(BP, 'entities/living/archdevil.json', d)
    g = mobs.devil_geo(True)
    g.write(out.path(RP, 'models/entity/bc/archdevil.geo.json'), out.path(RP, 'textures/entity/bc/archdevil.png'))
    ctx.animations['entity/archdevil.animation.json'] = {'animation.bc.archdevil.halo': {'loop': True, 'bones': {
        'halo': {'rotation': [0, 0, 'q.life_time * 50.0'], 'scale': '1.0 + math.sin(q.life_time * 180.0) * 0.05'}}}}
    _client('archdevil', 'geometry.bc.archdevil', 'textures/entity/bc/archdevil', 'entity_emissive_alpha',
            {'hover': 'animation.bc.devil.hover', 'wings': 'animation.bc.devil.wings', 'look': 'animation.bc.devil.look_at_target',
             'halo': 'animation.bc.archdevil.halo', 'aura': 'animation.bc.mob.aura', 'attack': 'animation.bc.devil.attack', 'cast': 'animation.bc.devil.cast'},
            ['hover', 'wings', 'look', 'halo', 'aura'], particles={'aura': 'bc:devil_aura'}, egg={'base_color': '#3e0a12', 'overlay_color': '#ffb030'}, scale='1.5')
    ctx.lang += [f'entity.{NS}:archdevil.name=§4§lThe Archdevil', f'item.spawn_egg.entity.{NS}:archdevil.name=Archdevil Spawn Egg']

    # ---------------------------------------------------------------- Stone Colossus
    comps = mob_base('stone_colossus', ['bc_magic', 'bc_golem', 'bc_boss', 'monster', 'mob'], 1200, (2.6, 6.4), 0.2,
                     'loot_tables/entities/bc_stone_colossus.json', 300)
    comps.update(_melee_ai(22, targets=('player', 'irongolem', 'bc_knight', 'bc_shade', 'bc_construct')))
    comps['minecraft:behavior.melee_box_attack']['speed_multiplier'] = 1.0
    comps['minecraft:boss'] = {'should_darken_sky': False, 'hud_range': 64}
    comps['minecraft:knockback_resistance'] = {'value': 1.0}
    comps['minecraft:persistent'] = {}
    comps['minecraft:follow_range'] = {'value': 64, 'max': 64}
    comps.pop('minecraft:despawn', None)
    comps['minecraft:pushable'] = {'is_pushable': False, 'is_pushable_by_piston': False}
    comps['minecraft:damage_sensor'] = {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'drowning', 'deals_damage': 'no'},
                                                     {'cause': 'projectile', 'damage_multiplier': 0.6}, {'cause': 'suffocation', 'deals_damage': 'no'}]}
    write_json(BP, 'entities/living/stone_colossus.json', _entity('stone_colossus', comps))
    g = wave4.colossus_geo()
    g.write(out.path(RP, 'models/entity/bc/stone_colossus.geo.json'), out.path(RP, 'textures/entity/bc/stone_colossus.png'))
    ctx.animations['entity/stone_colossus.animation.json'] = grand.golem_animations('stone_colossus')
    _client('stone_colossus', 'geometry.bc.stone_colossus', 'textures/entity/bc/stone_colossus', 'entity_emissive_alpha',
            {'idle': 'animation.bc.stone_colossus.idle', 'walk': 'animation.bc.stone_colossus.walk', 'look': 'animation.bc.stone_colossus.look_at_target',
             'slam': 'animation.bc.stone_colossus.slam'},
            ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look'], egg={'base_color': '#404437', 'overlay_color': '#ff8a2a'}, scale='3.0')
    ctx.lang += [f'entity.{NS}:stone_colossus.name=§6§lThe Stone Colossus', f'item.spawn_egg.entity.{NS}:stone_colossus.name=Stone Colossus Spawn Egg']

    # ---------------------------------------------------------------- Storm Kraken (from the Leviathan)
    d = _load('entities/sea/leviathan.json')
    e = d['minecraft:entity']
    e['description']['identifier'] = f'{NS}:storm_kraken'
    c = e['components']
    c['minecraft:type_family'] = {'family': ['bc_kraken', 'bc_boss', 'monster', 'mob', 'boss']}
    c['minecraft:health'] = {'value': 1000, 'max': 1000}
    c['minecraft:collision_box'] = {'width': 3.0, 'height': 3.0}
    c['minecraft:loot'] = {'table': 'loot_tables/entities/bc_storm_kraken.json'}
    c['minecraft:experience_reward'] = {'on_death': 'q.last_hit_by_player ? 350 : 0'}
    c['minecraft:boss'] = {'should_darken_sky': True, 'hud_range': 64}
    c['minecraft:attack'] = {'damage': 14}
    write_json(BP, 'entities/living/storm_kraken.json', d)
    g = wave4.kraken_geo()
    g.write(out.path(RP, 'models/entity/bc/storm_kraken.geo.json'), out.path(RP, 'textures/entity/bc/storm_kraken.png'))
    ctx.animations['entity/storm_kraken.animation.json'] = wave4.kraken_animations()
    _client('storm_kraken', 'geometry.bc.storm_kraken', 'textures/entity/bc/storm_kraken', 'entity_emissive_alpha',
            {'swim': 'animation.bc.storm_kraken.swim', 'look': 'animation.bc.storm_kraken.look_at_target', 'slam': 'animation.bc.storm_kraken.slam'},
            ['swim', 'look'], particles={'aura': 'bc:leviathan_bubbles'}, egg={'base_color': '#141434', 'overlay_color': '#9ae8ff'}, scale='2.2')
    ctx.lang += [f'entity.{NS}:storm_kraken.name=§9§lThe Storm Kraken', f'item.spawn_egg.entity.{NS}:storm_kraken.name=Storm Kraken Spawn Egg']

    # ---------------------------------------------------------------- Phantom Galleon (a flying ghost ship)
    comps = mob_base('phantom_galleon', ['bc_pirate', 'bc_phantom', 'bc_boss', 'undead', 'monster', 'mob'], 800, (4.0, 4.0), 0.25,
                     'loot_tables/entities/bc_phantom_galleon.json', 300)
    comps.update({
        'minecraft:can_fly': {},
        'minecraft:flying_speed': {'value': 0.18},
        'minecraft:navigation.hover': {'can_path_over_water': True, 'can_sink': False, 'can_pass_doors': False, 'can_path_from_air': True, 'avoid_water': False},
        'minecraft:movement.hover': {},
        'minecraft:physics': {'has_gravity': False},
        'minecraft:boss': {'should_darken_sky': True, 'hud_range': 64},
        'minecraft:knockback_resistance': {'value': 1.0},
        'minecraft:persistent': {},
        'minecraft:fire_immune': True,
        'minecraft:follow_range': {'value': 64, 'max': 64},
        'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': False},
        'minecraft:damage_sensor': {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'drowning', 'deals_damage': 'no'}, {'cause': 'suffocation', 'deals_damage': 'no'}]},
        'minecraft:behavior.hurt_by_target': {'priority': 1},
        'minecraft:behavior.nearest_attackable_target': {'priority': 2, 'must_see': False, 'reselect_targets': True,
                                                          'entity_types': [{'filters': {'any_of': [{'test': 'is_family', 'subject': 'other', 'value': 'player'},
                                                                                                   {'test': 'is_family', 'subject': 'other', 'value': 'bc_navy'}]}, 'max_dist': 48}]},
        'minecraft:behavior.random_hover': {'priority': 6, 'xz_dist': 16, 'y_dist': 4, 'y_offset': 0, 'interval': 1, 'hover_height': [8, 14]},
    })
    comps.pop('minecraft:hurt_on_condition', None)
    write_json(BP, 'entities/living/phantom_galleon.json', _entity('phantom_galleon', comps))
    g = sea.ship_geo()
    g.identifier = 'geometry.bc.phantom_galleon'
    g.paint()
    g.atlas = wave4.ghostify(g.atlas)
    g.write(out.path(RP, 'models/entity/bc/phantom_galleon.geo.json'), out.path(RP, 'textures/entity/bc/phantom_galleon.png'))
    ctx.animations['entity/phantom_galleon.animation.json'] = wave4.galleon_animations()
    _client('phantom_galleon', 'geometry.bc.phantom_galleon', 'textures/entity/bc/phantom_galleon', 'entity_emissive_alpha',
            {'drift': 'animation.bc.phantom_galleon.drift', 'aura': 'animation.bc.mob.aura'}, ['drift', 'aura'],
            particles={'aura': 'bc:disciple_aura'}, egg={'base_color': '#0a1e22', 'overlay_color': '#96ffdc'}, scale='1.6')
    ctx.lang += [f'entity.{NS}:phantom_galleon.name=§3§lThe Phantom Galleon', f'item.spawn_egg.entity.{NS}:phantom_galleon.name=Phantom Galleon Spawn Egg']

    # ---------------------------------------------------------------- phantom crew (ghostly raiders)
    d = _load('entities/sea/sea_raider.json')
    e = d['minecraft:entity']
    e['description']['identifier'] = f'{NS}:phantom_raider'
    e['description']['is_spawnable'] = True
    c = e['components']
    c['minecraft:type_family'] = {'family': ['bc_pirate', 'bc_phantom', 'undead', 'monster', 'mob']}
    c['minecraft:loot'] = {'table': 'loot_tables/entities/bc_phantom_raider.json'}
    c['minecraft:fire_immune'] = True
    c['minecraft:breathable'] = {'total_supply': 15, 'suffocate_time': 0, 'breathes_water': True}
    write_json(BP, 'entities/living/phantom_raider.json', d)
    from PIL import Image
    ghost = wave4.ghostify(tex.from_image(Image.open(out.path(RP, 'textures/entity/bc/sea_raider.png')).convert('RGBA')))
    write_png(RP, 'textures/entity/bc/phantom_raider.png', ghost)
    _client('phantom_raider', 'geometry.bc.sea_raider', 'textures/entity/bc/phantom_raider', 'entity_emissive_alpha',
            {'idle': 'animation.bc.sea_raider.idle', 'walk': 'animation.bc.sea_raider.walk', 'look': 'animation.bc.sea_raider.look_at_target'},
            ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look'], egg={'base_color': '#0a1e22', 'overlay_color': '#96ffdc'})
    ctx.lang += [f'entity.{NS}:phantom_raider.name=Phantom Raider', f'item.spawn_egg.entity.{NS}:phantom_raider.name=Phantom Raider Spawn Egg']

    # ---------------------------------------------------------------- devil gate (event portal)
    g, _, anims = grand.warp_gate()
    g.paint()
    write_png(RP, 'textures/entity/bc/devil_gate.png', wave4.recolor_devil(g.atlas))
    comps = {
        'minecraft:type_family': {'family': ['bc_devil', 'bc_gate', 'monster']},
        'minecraft:health': {'value': 120, 'max': 120},
        'minecraft:collision_box': {'width': 2.4, 'height': 4.0},
        'minecraft:physics': {'has_gravity': False},
        'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': False},
        'minecraft:knockback_resistance': {'value': 1.0},
        'minecraft:persistent': {},
        'minecraft:fire_immune': True,
        'minecraft:loot': {'table': 'loot_tables/entities/bc_devil_gate.json'},
        'minecraft:experience_reward': {'on_death': 'q.last_hit_by_player ? 60 : 0'},
        'minecraft:damage_sensor': {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'suffocation', 'deals_damage': 'no'}]},
    }
    write_json(BP, 'entities/living/devil_gate.json', _static('devil_gate', comps))
    _client('devil_gate', 'geometry.bc.warp_gate', 'textures/entity/bc/devil_gate', 'entity_emissive_alpha',
            {'spin': 'animation.bc.warp_gate.spin', 'aura': 'animation.bc.mob.aura'}, ['spin', 'aura'], particles={'aura': 'bc:devil_aura'}, scale='2.4')
    ctx.lang.append(f'entity.{NS}:devil_gate.name=§4Devil Gate')


# ======================================================================================
# factions: new targets in the wild, plus War Table team groups
# ======================================================================================
FACTION_FILES = {
    'bc:magic_knight': 'entities/living/magic_knight.json',
    'bc:dark_disciple': 'entities/dark_disciple.json',
    'bc:imp': 'entities/grand/imp.json',
    'bc:sea_raider': 'entities/sea/sea_raider.json',
    'bc:raider_captain': 'entities/sea/raider_captain.json',
    'bc:tidewatch_sentinel': 'entities/grand/tidewatch_sentinel.json',
    'bc:tidewatch_commodore': 'entities/grand/tidewatch_commodore.json',
    'bc:construct': 'entities/living/construct.json',
}
EXTRA_TARGETS = {
    'bc:dark_disciple': ['bc_knight', 'bc_navy'],
    'bc:imp': ['bc_knight'],
    'bc:sea_raider': ['bc_knight', 'bc_navy'],
    'bc:raider_captain': ['bc_knight', 'bc_navy'],
    'bc:tidewatch_sentinel': ['bc_devil', 'bc_disciple'],
    'bc:tidewatch_commodore': ['bc_devil', 'bc_disciple'],
}


def gen_factions(ctx: Ctx):
    for ident in {u for f in FACTIONS.values() for u in f['units'] + [f['leader']]}:
        assert ident in FACTION_FILES, ident
    for ident, rel in FACTION_FILES.items():
        d = _load(rel)
        e = d['minecraft:entity']
        c = e['components']
        nat = c.get('minecraft:behavior.nearest_attackable_target')
        if nat and ident in EXTRA_TARGETS:
            et = nat['entity_types'][0]
            filt = et['filters']
            lst = filt['any_of'] if 'any_of' in filt else [filt]
            for fam in EXTRA_TARGETS[ident]:
                lst.append({'test': 'is_family', 'subject': 'other', 'value': fam})
            et['filters'] = {'any_of': lst}
        groups = e.setdefault('component_groups', {})
        events = e.setdefault('events', {})
        fam = c['minecraft:type_family']['family']
        prio = (nat or {}).get('priority', 2)
        for team, enemy in (('a', 'b'), ('b', 'a')):
            groups[f'bc:team_{team}'] = {
                'minecraft:type_family': {'family': fam + [f'bc_team_{team}']},
                'minecraft:behavior.nearest_attackable_target': {
                    'priority': prio, 'must_see': False, 'reselect_targets': True, 'scan_interval': 5,
                    'entity_types': [{'filters': {'test': 'is_family', 'subject': 'other', 'value': f'bc_team_{enemy}'}, 'max_dist': 48}]},
                'minecraft:follow_range': {'value': 64, 'max': 64},
                'minecraft:persistent': {},
            }
            ev = {'add': {'component_groups': [f'bc:team_{team}']}}
            if 'bc:wild' in groups:
                ev['remove'] = {'component_groups': ['bc:wild']}
            events[f'bc:team_{team}'] = ev
        write_json(BP, rel, d)


def build(ctx: Ctx):
    gen_items(ctx)
    gen_block(ctx)
    gen_recipes(ctx)
    gen_loot(ctx)
    rcs = {}
    rcs.update(gen_mana_bolt(ctx))
    rcs.update(gen_knight(ctx))
    gen_merchant(ctx)
    rcs.update(gen_construct(ctx))
    gen_bosses(ctx)
    gen_factions(ctx)
    write_json(RP, 'render_controllers/bc_living.render_controllers.json', {'format_version': '1.10.0', 'render_controllers': rcs})
