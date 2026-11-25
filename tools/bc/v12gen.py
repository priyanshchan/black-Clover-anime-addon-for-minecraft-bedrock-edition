"""v1.2.0 pack content: Wyvern Eggs and tamed wyverns, the kingdom soldiers, the new items and relics."""
from __future__ import annotations

from . import out
from .data import KINGDOMS, NS, RELICS, V12_ITEMS, WYVERN_STAGES, WYVERNS
from .models import v11, v12
from .out import BP, RP, write_json
from .packgen import Ctx, item_json, mob_base, shaped
from .seagen import _client, _entity, _melee_ai
from .v3gen import _icon, _pool
from .v8gen import _shapeless

ELEMENTS = list(WYVERNS)   # ember, frost, storm


def gen_items(ctx: Ctx):
    ic = v12.v12_icons()
    usable = {'minecraft:use_modifiers': {'use_duration': 0.6, 'movement_modifier': 1.0}}
    for key, (name, _) in V12_ITEMS.items():
        stack = 1 if key.startswith('wyvern_') else 16 if key == 'spirit_draught' else 64
        comps = {'minecraft:max_stack_size': {'value': stack}}
        if key.startswith('wyvern_') or key == 'spirit_draught':
            comps.update(usable)
        if key.startswith('wyvern_egg'):
            comps['minecraft:glint'] = {'value': True}
        write_json(BP, f'items/v12/{key}.json', item_json(f'{NS}:{key}', name, _icon(ctx, key, ic[key]), comps,
                                                          category='equipment' if key in ('wyvern_whistle', 'wyvern_saddle') else 'items'))
    for key in ('relic_prism', 'relic_brand', 'relic_blossom'):
        name = RELICS[key][0]
        write_json(BP, f'items/v12/{key}.json', item_json(f'{NS}:{key}', f'§d{name}', _icon(ctx, key, ic[key]), {
            'minecraft:max_stack_size': {'value': 1}, 'minecraft:glint': {'value': True}}, category='equipment'))
    write_json(BP, 'recipes/v12/wyvern_whistle.json', shaped('wyvern_whistle', ['G', 'S', 'B'], {
        'G': 'minecraft:gold_ingot', 'S': f'{NS}:wyvern_scale', 'B': 'minecraft:bone'}))
    write_json(BP, 'recipes/v12/wyvern_saddle.json', shaped('wyvern_saddle', ['LSL', 'LIL'], {
        'L': 'minecraft:leather', 'S': f'{NS}:wyvern_scale', 'I': 'minecraft:iron_ingot'}))
    write_json(BP, 'recipes/v12/spirit_draught.json', _shapeless('spirit_draught', [f'{NS}:heart_bloom', f'{NS}:mana_crystal', 'minecraft:glass_bottle']))


def gen_loot(ctx: Ctx):
    L = 'loot_tables/entities'
    write_json(BP, f'{L}/bc_diamond_legionnaire.json', {'pools': [_pool(f'{NS}:diamond_shard', 1, 2, 0.7), _pool(f'{NS}:doubloon', 3, 9), _pool('minecraft:iron_ingot', 1, 2, 0.3)]})
    write_json(BP, f'{L}/bc_spade_zealot.json', {'pools': [_pool(f'{NS}:spade_sigil', 1, 2, 0.7), _pool(f'{NS}:doubloon', 3, 9), _pool(f'{NS}:ancient_page', 1, 1, 0.2)]})
    write_json(BP, f'{L}/bc_heart_guardian.json', {'pools': [_pool(f'{NS}:heart_bloom', 0, 1)]})


def gen_entities(ctx: Ctx):
    rcs = {}
    # ---------------------------------------------------------------- the eggs
    comps = {
        'minecraft:type_family': {'family': ['bc_wyvern_egg', 'inanimate']},
        'minecraft:health': {'value': 6, 'max': 6},
        'minecraft:collision_box': {'width': 0.6, 'height': 0.9},
        'minecraft:physics': {},
        'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': False},
        'minecraft:knockback_resistance': {'value': 1.0},
        'minecraft:movement': {'value': 0.0},
        'minecraft:persistent': {},
        'minecraft:nameable': {},
        'minecraft:damage_sensor': {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'fire', 'deals_damage': 'no'},
                                                 {'cause': 'fire_tick', 'deals_damage': 'no'}, {'cause': 'lava', 'deals_damage': 'no'},
                                                 {'cause': 'freezing', 'deals_damage': 'no'}, {'cause': 'lightning', 'deals_damage': 'no'}]},
        'minecraft:interact': {'interactions': [{'on_interact': {'filters': {'test': 'is_family', 'subject': 'other', 'value': 'player'}, 'event': 'bc:noop'},
                                                 'interact_text': 'action.interact.talk'}]},
    }
    ent = _entity('wyvern_egg', comps)
    ent['minecraft:entity']['description']['properties'] = {'bc:element': {'type': 'int', 'range': [0, 2], 'default': 0, 'client_sync': True}}
    ent['minecraft:entity']['events'] = {'bc:noop': {}, **{f'bc:element_{i}': {'set_property': {'bc:element': i}} for i in range(3)}}
    write_json(BP, 'entities/v12/wyvern_egg.json', ent)
    etex = {}
    for i, k in enumerate(ELEMENTS):
        g = v12.egg_geo(k)
        g.write(out.path(RP, 'models/entity/bc/wyvern_egg.geo.json'), out.path(RP, f'textures/entity/bc/egg/{k}.png'))
        etex[f'e{i}'] = f'textures/entity/bc/egg/{k}'
    ea = v12.egg_animations()
    ctx.animations['entity/wyvern_egg.animation.json'] = ea
    write_json(RP, 'entity/bc/wyvern_egg.entity.json', {'format_version': '1.10.0', 'minecraft:client_entity': {'description': {
        'identifier': f'{NS}:wyvern_egg', 'materials': {'default': 'entity_alphatest'}, 'textures': etex,
        'geometry': {'default': 'geometry.bc.wyvern_egg'}, 'animations': {'idle': 'animation.bc.wyvern_egg.idle'},
        'scripts': {'animate': ['idle']}, 'render_controllers': ['controller.render.bc.wyvern_egg'],
        'spawn_egg': {'base_color': '#842a12', 'overlay_color': '#ffa040'}}}})
    rcs['controller.render.bc.wyvern_egg'] = {
        'arrays': {'textures': {'Array.eggs': [f'Texture.e{i}' for i in range(3)]}},
        'geometry': 'Geometry.default', 'materials': [{'*': 'Material.default'}], 'textures': ["Array.eggs[q.property('bc:element')]"]}
    ctx.lang += [f'entity.{NS}:wyvern_egg.name=Wyvern Egg', f'item.spawn_egg.entity.{NS}:wyvern_egg.name=Wyvern Egg Spawn Egg']

    # ---------------------------------------------------------------- the tamed wyvern
    comps = {
        'minecraft:type_family': {'family': ['bc_tamed_wyvern', 'mob']},
        'minecraft:breathable': {'total_supply': 15, 'suffocate_time': 0},
        'minecraft:nameable': {'always_show': True, 'allow_name_tag_renaming': True},
        'minecraft:persistent': {},
        'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': False},
        'minecraft:knockback_resistance': {'value': 0.6},
        'minecraft:tameable': {'probability': 0.0, 'tame_items': 'minecraft:emerald_block'},
        'minecraft:navigation.walk': {'can_path_over_water': True, 'avoid_water': True, 'avoid_damage_blocks': True},
        'minecraft:movement.basic': {}, 'minecraft:jump.static': {}, 'minecraft:can_climb': {},
        'minecraft:follow_range': {'value': 32, 'max': 32},
        'minecraft:damage_sensor': {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'suffocation', 'deals_damage': 'no'}]},
        'minecraft:behavior.float': {'priority': 0},
        'minecraft:behavior.owner_hurt_by_target': {'priority': 1},
        'minecraft:behavior.owner_hurt_target': {'priority': 2},
        'minecraft:behavior.melee_box_attack': {'priority': 3, 'speed_multiplier': 1.2, 'track_target': True},
        'minecraft:behavior.random_stroll': {'priority': 7, 'speed_multiplier': 0.8},
        'minecraft:behavior.look_at_player': {'priority': 8, 'look_distance': 8, 'probability': 0.3},
        'minecraft:interact': {'interactions': [{'on_interact': {'filters': {'test': 'is_family', 'subject': 'other', 'value': 'player'}, 'event': 'bc:noop'},
                                                 'interact_text': 'action.interact.talk'}]},
        'minecraft:conditional_bandwidth_optimization': {'default_values': {'max_optimized_distance': 64.0, 'max_dropped_ticks': 2, 'use_motion_prediction_hints': True}},
    }
    sizes = [(0.6, 0.6, 0.3, 2), (1.2, 1.1, 0.3, 6), (2.0, 1.8, 0.32, 11)]
    groups = {}
    for i, ((name, _, hp, _), (w, h, sp, dmg)) in enumerate(zip(WYVERN_STAGES, sizes)):
        groups[f'bc:{name}'] = {'minecraft:health': {'value': hp, 'max': hp}, 'minecraft:collision_box': {'width': w, 'height': h},
                                'minecraft:movement': {'value': sp}, 'minecraft:attack': {'damage': dmg}}
    groups['bc:rideable'] = {}
    groups['bc:rideable']['minecraft:rideable'] = {'seat_count': 1, 'crouching_skip_interact': True, 'family_types': ['player'],
                                                'interact_text': 'action.interact.ride.horse', 'pull_in_entities': False, 'seats': [{'position': [0.0, 2.05, 0.1]}]}
    groups['bc:follow'] = {'minecraft:behavior.follow_owner': {'priority': 4, 'speed_multiplier': 1.3, 'start_distance': 10, 'stop_distance': 4}}
    groups['bc:grounded'] = {'minecraft:physics': {}}
    groups['bc:mounted'] = {'minecraft:physics': {'has_gravity': False}}
    props = {'bc:element': {'type': 'int', 'range': [0, 2], 'default': 0, 'client_sync': True},
             'bc:stage': {'type': 'int', 'range': [0, 2], 'default': 0, 'client_sync': True},
             'bc:asleep': {'type': 'bool', 'default': False, 'client_sync': True},
             'bc:saddled': {'type': 'bool', 'default': False, 'client_sync': True}}
    events = {
        'minecraft:entity_spawned': {'add': {'component_groups': ['bc:hatchling', 'bc:follow', 'bc:grounded']}},
        'bc:noop': {},
        **{f'bc:element_{i}': {'set_property': {'bc:element': i}} for i in range(3)},
        'bc:grow_1': {'remove': {'component_groups': ['bc:hatchling']}, 'add': {'component_groups': ['bc:juvenile']}, 'set_property': {'bc:stage': 1}},
        'bc:grow_2': {'remove': {'component_groups': ['bc:juvenile', 'bc:hatchling']}, 'add': {'component_groups': ['bc:adult']}, 'set_property': {'bc:stage': 2}},
        'bc:sit': {'remove': {'component_groups': ['bc:follow']}, 'set_property': {'bc:asleep': True}},
        'bc:stand': {'add': {'component_groups': ['bc:follow']}, 'set_property': {'bc:asleep': False}},
        'bc:roam': {'remove': {'component_groups': ['bc:follow']}, 'set_property': {'bc:asleep': False}},
        'bc:saddle': {'add': {'component_groups': ['bc:rideable']}, 'set_property': {'bc:saddled': True}},
        'bc:mount': {'remove': {'component_groups': ['bc:grounded', 'bc:follow']}, 'add': {'component_groups': ['bc:mounted']}, 'set_property': {'bc:asleep': False}},
        'bc:dismount': {'remove': {'component_groups': ['bc:mounted']}, 'add': {'component_groups': ['bc:grounded', 'bc:follow']}},
    }
    ent = _entity('tamed_wyvern', comps)
    e = ent['minecraft:entity']
    e['description']['properties'] = props
    e['component_groups'] = groups
    e['events'] = events
    write_json(BP, 'entities/v12/tamed_wyvern.json', ent)
    ttex = {}
    for i, k in enumerate(ELEMENTS):
        g = v11.wyvern_geo(k, saddle=True)
        g.write(out.path(RP, 'models/entity/bc/tamed_wyvern.geo.json'), out.path(RP, f'textures/entity/bc/tamed/{k}.png'))
        ttex[f'e{i}'] = f'textures/entity/bc/tamed/{k}'
    ta = v12.tamed_animations()
    ctx.animations['entity/tamed_wyvern.animation.json'] = ta
    write_json(RP, 'entity/bc/tamed_wyvern.entity.json', {'format_version': '1.10.0', 'minecraft:client_entity': {'description': {
        'identifier': f'{NS}:tamed_wyvern', 'materials': {'default': 'entity_alphatest'}, 'textures': ttex,
        'geometry': {'default': 'geometry.bc.tamed_wyvern'}, 'animations': {k.split('.')[-1]: k for k in ta},
        'scripts': {'animate': ['grow', {'fly': "!q.is_on_ground && !q.property('bc:asleep')"}, {'ground': "q.is_on_ground && !q.property('bc:asleep')"},
                                {'walk': "q.is_on_ground && q.modified_move_speed > 0.05 && !q.property('bc:asleep')"}, {'sleep': "q.property('bc:asleep')"},
                                {'look': "!q.property('bc:asleep')"}]},
        'render_controllers': ['controller.render.bc.tamed_wyvern'], 'spawn_egg': {'base_color': '#286a30', 'overlay_color': '#ffa040'}}}})
    rcs['controller.render.bc.tamed_wyvern'] = {
        'arrays': {'textures': {'Array.skins': [f'Texture.e{i}' for i in range(3)]}},
        'geometry': 'Geometry.default', 'materials': [{'*': 'Material.default'}], 'textures': ["Array.skins[q.property('bc:element')]"],
        'part_visibility': [{'*': True}, {'saddle': "q.property('bc:saddled')"}]}
    ctx.lang += [f'entity.{NS}:tamed_wyvern.name=Wyvern', f'item.spawn_egg.entity.{NS}:tamed_wyvern.name=Tamed Wyvern Spawn Egg']

    # ---------------------------------------------------------------- the kingdom soldiers
    geos = {'diamond': v12.legionnaire_geo, 'spade': v12.zealot_geo, 'heart': v12.guardian_geo}
    for kid, K in KINGDOMS.items():
        ident = K['soldier']
        fams = ['bc_kingdom', f'bc_{kid}', 'mob'] + (['bc_kingdom_foe', 'monster'] if K['hostile'] else [])
        comps = mob_base(ident, fams, 38 if kid != 'heart' else 34, (0.6, 1.95), 0.28, f'loot_tables/entities/bc_{ident}.json', 12)
        comps.update(_melee_ai(7 if kid == 'diamond' else 5, targets=('player', 'bc_knight', 'bc_navy') if K['hostile'] else ('monster',)))
        comps['minecraft:behavior.hurt_by_target'] = {'priority': 1, 'alert_same_type': True}
        if K['hostile']:
            comps.pop('minecraft:despawn', None)
        write_json(BP, f'entities/v12/{ident}.json', _entity(ident, comps))
        g = geos[kid]()
        g.write(out.path(RP, f'models/entity/bc/{ident}.geo.json'), out.path(RP, f'textures/entity/bc/{ident}.png'))
        sa = v12.soldier_animations(ident)
        ctx.animations[f'entity/{ident}.animation.json'] = sa
        _client(ident, f'geometry.bc.{ident}', f'textures/entity/bc/{ident}', 'entity_alphatest', {k.split('.')[-1]: k for k in sa},
                ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look_at_target'],
                egg={'base_color': {'diamond': '#707c90', 'spade': '#1a1424', 'heart': '#e0eed8'}[kid], 'overlay_color': {'diamond': '#8ae0f8', 'spade': '#a040ff', 'heart': '#f8a0c0'}[kid]})
        ctx.lang += [f'entity.{NS}:{ident}.name={K["soldier_name"]}', f'item.spawn_egg.entity.{NS}:{ident}.name={K["soldier_name"]} Spawn Egg']
    return rcs


def build(ctx: Ctx):
    gen_items(ctx)
    gen_loot(ctx)
    rcs = gen_entities(ctx)
    write_json(RP, 'render_controllers/bc_v12.render_controllers.json', {'format_version': '1.10.0', 'render_controllers': rcs})
