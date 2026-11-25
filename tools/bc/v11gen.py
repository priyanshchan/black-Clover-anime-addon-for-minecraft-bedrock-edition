"""v1.1.0 pack content: the Mana Wyverns, the Spire Warden, the Mimic, the Mana Sprite, the Will-o'-Wisp, the Rootwarden,
the Hollow Knight and the Wanderer; relics and exploration items; the Mana Spawner and the Obelisk Core."""
from __future__ import annotations

from . import out
from .data import NS, RELICS, V11_ITEMS, WANDERERS, WYVERNS
from .models import v11
from .out import BP, RP, write_json, write_png
from .packgen import Ctx, item_json, mob_base, shaped
from .seagen import _client, _entity, _melee_ai
from .v3gen import _flyer, _icon, _pool

FOES = ('player', 'bc_knight', 'bc_navy', 'villager')


def _spawn(ident, biomes, weight, herd, night=None, pop='monster'):
    cond = {'minecraft:spawns_on_surface': {}, 'minecraft:difficulty_filter': {'min': 'easy', 'max': 'hard'}, 'minecraft:weight': {'default': weight},
            'minecraft:herd': {'min_size': herd[0], 'max_size': herd[1]}, 'minecraft:density_limit': {'surface': herd[1] + 1},
            'minecraft:biome_filter': {'any_of': [{'test': 'has_biome_tag', 'value': b} for b in biomes]}}
    if night is True:
        cond['minecraft:brightness_filter'] = {'min': 0, 'max': 7, 'adjust_for_weather': True}
    elif night is False:
        cond['minecraft:brightness_filter'] = {'min': 8, 'max': 15, 'adjust_for_weather': True}
    write_json(BP, f'spawn_rules/{ident}.json', {'format_version': '1.8.0', 'minecraft:spawn_rules': {
        'description': {'identifier': f'{NS}:{ident}', 'population_control': pop}, 'conditions': [cond]}})


def _targets(dist=32, must_see=False):
    return {'priority': 2, 'must_see': must_see, 'reselect_targets': True, 'entity_types': [
        {'filters': {'any_of': [{'test': 'is_family', 'subject': 'other', 'value': f} for f in FOES]}, 'max_dist': dist}]}


# ======================================================================================
def gen_items(ctx: Ctx):
    ic = v11.v11_icons()
    usable = {'minecraft:use_modifiers': {'use_duration': 0.6, 'movement_modifier': 1.0}}
    for key, (name, _) in V11_ITEMS.items():
        stack = 1 if key in ('explorer_map', 'spire_core') else 16 if key == 'journal_page' else 64
        comps = {'minecraft:max_stack_size': {'value': stack}}
        if key in ('explorer_map', 'journal_page', 'spire_core'):
            comps.update(usable)
        if key in ('star_fragment', 'spire_core'):
            comps['minecraft:glint'] = {'value': True}
        write_json(BP, f'items/v11/{key}.json', item_json(f'{NS}:{key}', name, _icon(ctx, key, ic[key]), comps))
    for key, (name, _, _) in RELICS.items():
        write_json(BP, f'items/v11/{key}.json', item_json(f'{NS}:{key}', f'§d{name}', _icon(ctx, key, ic[key]), {
            'minecraft:max_stack_size': {'value': 1}, 'minecraft:glint': {'value': True}}, category='equipment'))
    write_json(BP, 'recipes/v11/explorer_map.json', shaped('explorer_map', ['PPP', 'PCP', 'PPP'], {'P': 'minecraft:paper', 'C': 'minecraft:compass'}))


def _block(ident, texture, name, comps):
    base = {
        'minecraft:geometry': 'minecraft:geometry.full_block',
        'minecraft:material_instances': {'*': {'texture': texture, 'render_method': 'opaque'}},
        'minecraft:map_color': '#5a2a8a',
    }
    base.update(comps)
    write_json(BP, f'blocks/{ident}.json', {'format_version': '1.21.90', 'minecraft:block': {
        'description': {'identifier': f'{NS}:{ident}', 'menu_category': {'category': 'items'}}, 'components': base}})


def gen_blocks(ctx: Ctx):
    write_png(RP, 'textures/blocks/bc/mana_spawner.png', v11.spawner_texture())
    ctx.terrain_textures['bc_mana_spawner'] = 'textures/blocks/bc/mana_spawner'
    _block('mana_spawner', 'bc_mana_spawner', 'Mana Spawner', {
        'minecraft:destructible_by_mining': {'seconds_to_destroy': 3.0},
        'minecraft:destructible_by_explosion': {'explosion_resistance': 6},
        'minecraft:light_emission': 7,
        'minecraft:loot': 'loot_tables/empty.json',
    })
    write_png(RP, 'textures/blocks/bc/obelisk_core.png', v11.obelisk_texture())
    ctx.terrain_textures['bc_obelisk_core'] = 'textures/blocks/bc/obelisk_core'
    _block('obelisk_core', 'bc_obelisk_core', 'Obelisk Core', {
        'minecraft:destructible_by_mining': {'seconds_to_destroy': 25.0},
        'minecraft:destructible_by_explosion': {'explosion_resistance': 1200},
        'minecraft:light_emission': 9,
        'minecraft:map_color': '#60e0ff',
        'bc:obelisk': {},
    })
    write_json(BP, 'loot_tables/empty.json', {'pools': []})
    ctx.lang += [f'tile.{NS}:mana_spawner.name=§5Mana Spawner', f'tile.{NS}:obelisk_core.name=§bObelisk Core']


# ======================================================================================
def gen_loot(ctx: Ctx):
    L = 'loot_tables/entities'
    for wid in WYVERNS:
        write_json(BP, f'{L}/bc_{wid}.json', {'pools': [_pool('minecraft:gold_ingot', 4, 9), _pool(f'{NS}:doubloon', 40, 80),
                                                         _pool(f'{NS}:star_fragment', 1, 1, 0.5), _pool(f'{NS}:mana_crystal', 6, 12)]})
    write_json(BP, f'{L}/bc_spire_warden.json', {'pools': [_pool(f'{NS}:spire_core', 1, 1), _pool(f'{NS}:rune_shard', 4, 8), _pool(f'{NS}:mana_crystal', 8, 14),
                                                          _pool(f'{NS}:ancient_page', 2, 4)]})
    write_json(BP, f'{L}/bc_mimic.json', {'pools': [_pool(f'{NS}:mimic_tooth', 1, 2), _pool(f'{NS}:doubloon', 15, 35), _pool('minecraft:gold_ingot', 1, 3, 0.6)]})
    write_json(BP, f'{L}/bc_mana_sprite.json', {'pools': [_pool(f'{NS}:sprite_dust', 1, 2)]})
    write_json(BP, f'{L}/bc_rootwarden.json', {'pools': [_pool('minecraft:oak_log', 3, 6), _pool('minecraft:oak_sapling', 1, 3), _pool('minecraft:moss_block', 1, 3, 0.6),
                                                         _pool(f'{NS}:sprite_dust', 1, 2, 0.4)]})
    write_json(BP, f'{L}/bc_hollow_knight.json', {'pools': [_pool(f'{NS}:hollow_ember', 0, 1), _pool('minecraft:bone', 0, 2), _pool(f'{NS}:doubloon', 1, 4, 0.5)]})


def gen_entities(ctx: Ctx):
    rcs = {}
    # ---------------------------------------------------------------- the Mana Wyverns
    wa = v11.wyvern_animations()
    ctx.animations['entity/mana_wyvern.animation.json'] = wa
    textures = {}
    for i, (wid, (label, _, color, _, _)) in enumerate(WYVERNS.items()):
        comps = mob_base(wid, ['bc_wyvern', 'bc_boss', 'monster', 'mob', 'boss'], 320, (2.4, 2.2), 0.3, f'loot_tables/entities/bc_{wid}.json', 160)
        comps.pop('minecraft:movement', None)
        comps['minecraft:boss'] = {'should_darken_sky': False, 'hud_range': 48}
        comps['minecraft:knockback_resistance'] = {'value': 0.9}
        comps['minecraft:persistent'] = {}
        comps['minecraft:damage_sensor'] = {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'suffocation', 'deals_damage': 'no'}] +
                                            ([{'cause': 'fire', 'deals_damage': 'no'}, {'cause': 'fire_tick', 'deals_damage': 'no'}, {'cause': 'lava', 'deals_damage': 'no'}]
                                             if wid == 'ember_wyvern' else [{'cause': 'freezing', 'deals_damage': 'no'}] if wid == 'frost_wyvern'
                                             else [{'cause': 'lightning', 'deals_damage': 'no'}])}
        comps['minecraft:physics'] = {'has_gravity': False}
        awake = {}
        _flyer(awake, [5, 12], 0.32)
        awake.pop('minecraft:damage_sensor', None)
        awake.pop('minecraft:physics', None)
        awake.pop('minecraft:persistent', None)
        awake['minecraft:movement'] = {'value': 0.3}
        awake['minecraft:behavior.nearest_attackable_target'] = _targets(40)
        asleep = {'minecraft:movement': {'value': 0.0}, 'minecraft:flying_speed': {'value': 0.0}}
        ent = _entity(wid, comps)
        e = ent['minecraft:entity']
        e['description']['properties'] = {'bc:asleep': {'type': 'bool', 'default': False, 'client_sync': True}}
        e['component_groups'] = {'bc:awake': awake, 'bc:asleep': asleep}
        e['events'] = {
            'minecraft:entity_spawned': {'add': {'component_groups': ['bc:awake']}},
            'bc:sleep': {'remove': {'component_groups': ['bc:awake']}, 'add': {'component_groups': ['bc:asleep']}, 'set_property': {'bc:asleep': True}},
            'bc:wake': {'remove': {'component_groups': ['bc:asleep']}, 'add': {'component_groups': ['bc:awake']}, 'set_property': {'bc:asleep': False}},
        }
        write_json(BP, f'entities/v11/{wid}.json', ent)
        g = v11.wyvern_geo(wid)
        g.write(out.path(RP, 'models/entity/bc/mana_wyvern.geo.json'), out.path(RP, f'textures/entity/bc/{wid}.png'))
        textures[wid] = f'textures/entity/bc/{wid}'
        _client(wid, 'geometry.bc.mana_wyvern', f'textures/entity/bc/{wid}', 'entity_alphatest', {k.split('.')[-1]: k for k in wa},
                [{'fly': "!q.is_on_ground && !q.property('bc:asleep')"}, {'ground': "q.is_on_ground && !q.property('bc:asleep')"},
                 {'walk': "q.is_on_ground && q.modified_move_speed > 0.05 && !q.property('bc:asleep')"}, {'sleep': "q.property('bc:asleep')"},
                 {'look': "!q.property('bc:asleep')"}],
                egg={'base_color': f'#{color}', 'overlay_color': '#1a1a1a'}, scale='1.35')
        ctx.lang += [f'entity.{NS}:{wid}.name=§l{label}', f'item.spawn_egg.entity.{NS}:{wid}.name={label} Spawn Egg']

    # ---------------------------------------------------------------- the Spire Warden
    comps = mob_base('spire_warden', ['bc_construct', 'bc_boss', 'monster', 'mob', 'boss'], 600, (1.4, 2.9), 0.24, 'loot_tables/entities/bc_spire_warden.json', 300)
    comps.update(_melee_ai(12, targets=FOES))
    comps.pop('minecraft:despawn', None)
    comps['minecraft:boss'] = {'should_darken_sky': True, 'hud_range': 48}
    comps['minecraft:knockback_resistance'] = {'value': 1.0}
    comps['minecraft:persistent'] = {}
    comps['minecraft:damage_sensor'] = {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'drowning', 'deals_damage': 'no'}]}
    write_json(BP, 'entities/v11/spire_warden.json', _entity('spire_warden', comps))
    g = v11.warden_geo()
    g.write(out.path(RP, 'models/entity/bc/spire_warden.geo.json'), out.path(RP, 'textures/entity/bc/spire_warden.png'))
    sw = v11.warden_animations()
    ctx.animations['entity/spire_warden.animation.json'] = sw
    _client('spire_warden', 'geometry.bc.spire_warden', 'textures/entity/bc/spire_warden', 'entity_emissive_alpha', {k.split('.')[-1]: k for k in sw},
            ['idle', 'look'], egg={'base_color': '#3b3d45', 'overlay_color': '#60e0ff'})
    ctx.lang += [f'entity.{NS}:spire_warden.name=§b§lThe Spire Warden', f'item.spawn_egg.entity.{NS}:spire_warden.name=Spire Warden Spawn Egg']

    # ---------------------------------------------------------------- the Mimic
    comps = mob_base('mimic', ['bc_mimic', 'monster', 'mob'], 50, (0.9, 0.95), 0.32, 'loot_tables/entities/bc_mimic.json', 25)
    comps.update(_melee_ai(8, targets=FOES))
    comps.pop('minecraft:despawn', None)
    comps['minecraft:behavior.leap_at_target'] = {'priority': 3, 'yd': 0.5, 'must_be_on_ground': True}
    comps['minecraft:knockback_resistance'] = {'value': 0.6}
    write_json(BP, 'entities/v11/mimic.json', _entity('mimic', comps))
    g = v11.mimic_geo()
    g.write(out.path(RP, 'models/entity/bc/mimic.geo.json'), out.path(RP, 'textures/entity/bc/mimic.png'))
    ma = v11.mimic_animations()
    ctx.animations['entity/mimic.animation.json'] = ma
    _client('mimic', 'geometry.bc.mimic', 'textures/entity/bc/mimic', 'entity_alphatest', {k.split('.')[-1]: k for k in ma},
            ['idle', {'hop': 'q.modified_move_speed > 0.01'}], egg={'base_color': '#764c2f', 'overlay_color': '#ffd040'})
    ctx.lang += [f'entity.{NS}:mimic.name=Mimic', f'item.spawn_egg.entity.{NS}:mimic.name=Mimic Spawn Egg']

    # ---------------------------------------------------------------- the Mana Sprite
    comps = mob_base('mana_sprite', ['bc_fae', 'bc_sprite', 'mob'], 8, (0.4, 0.7), 0.3, 'loot_tables/entities/bc_mana_sprite.json', 3)
    _flyer(comps, [1, 3], 0.36)
    comps.pop('minecraft:persistent', None)
    comps['minecraft:knockback_resistance'] = {'value': 0.0}
    comps['minecraft:behavior.panic'] = {'priority': 1, 'speed_multiplier': 1.6}
    comps['minecraft:despawn'] = {'despawn_from_distance': {}}
    write_json(BP, 'entities/v11/mana_sprite.json', _entity('mana_sprite', comps, spawnable=True))
    g = v11.sprite_geo()
    g.write(out.path(RP, 'models/entity/bc/mana_sprite.geo.json'), out.path(RP, 'textures/entity/bc/mana_sprite.png'))
    sa = v11.sprite_animations()
    ctx.animations['entity/mana_sprite.animation.json'] = sa
    _client('mana_sprite', 'geometry.bc.mana_sprite', 'textures/entity/bc/mana_sprite', 'entity_emissive_alpha',
            {'fly': 'animation.bc.mana_sprite.fly', 'aura': 'animation.bc.mob.aura'}, ['fly', 'aura'],
            particles={'aura': 'bc:mana_aura'}, egg={'base_color': '#58b07a', 'overlay_color': '#d8fff0'})
    _spawn('mana_sprite', ['flower_forest', 'birch', 'cherry_grove', 'meadow', 'forest'], 2, (1, 3), night=False, pop='ambient')
    ctx.lang += [f'entity.{NS}:mana_sprite.name=Mana Sprite', f'item.spawn_egg.entity.{NS}:mana_sprite.name=Mana Sprite Spawn Egg']

    # ---------------------------------------------------------------- the Will-o'-Wisp
    comps = {
        'minecraft:type_family': {'family': ['bc_wisp', 'inanimate']},
        'minecraft:health': {'value': 1, 'max': 1},
        'minecraft:collision_box': {'width': 0.3, 'height': 0.3},
        'minecraft:physics': {'has_gravity': False, 'has_collision': False},
        'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': False},
        'minecraft:damage_sensor': {'triggers': [{'cause': 'all', 'deals_damage': 'no'}]},
        'minecraft:knockback_resistance': {'value': 1.0},
        'minecraft:persistent': {},
    }
    write_json(BP, 'entities/v11/wisp.json', _entity('wisp', comps))
    g = v11.wisp_geo()
    g.write(out.path(RP, 'models/entity/bc/wisp.geo.json'), out.path(RP, 'textures/entity/bc/wisp.png'))
    wpa = v11.wisp_animations()
    ctx.animations['entity/wisp.animation.json'] = wpa
    _client('wisp', 'geometry.bc.wisp', 'textures/entity/bc/wisp', 'entity_emissive_alpha', {'float': 'animation.bc.wisp.float'}, ['float'],
            egg={'base_color': '#4a9ad0', 'overlay_color': '#f0fbff'})
    ctx.lang += [f'entity.{NS}:wisp.name=Will-o\'-Wisp', f'item.spawn_egg.entity.{NS}:wisp.name=Will-o\'-Wisp Spawn Egg']

    # ---------------------------------------------------------------- the Rootwarden
    comps = mob_base('rootwarden', ['bc_fae', 'bc_rootwarden', 'monster', 'mob'], 90, (1.2, 2.8), 0.22, 'loot_tables/entities/bc_rootwarden.json', 30)
    comps.update(_melee_ai(9, targets=FOES))
    comps['minecraft:knockback_resistance'] = {'value': 0.6}
    write_json(BP, 'entities/v11/rootwarden.json', _entity('rootwarden', comps))
    g = v11.rootwarden_geo()
    g.write(out.path(RP, 'models/entity/bc/rootwarden.geo.json'), out.path(RP, 'textures/entity/bc/rootwarden.png'))
    ra = v11.rootwarden_animations()
    ctx.animations['entity/rootwarden.animation.json'] = ra
    _client('rootwarden', 'geometry.bc.rootwarden', 'textures/entity/bc/rootwarden', 'entity_alphatest', {k.split('.')[-1]: k for k in ra},
            ['idle', {'walk': 'q.modified_move_speed > 0.01'}], egg={'base_color': '#3c2a18', 'overlay_color': '#9cff6a'})
    ctx.lang += [f'entity.{NS}:rootwarden.name=Rootwarden', f'item.spawn_egg.entity.{NS}:rootwarden.name=Rootwarden Spawn Egg']

    # ---------------------------------------------------------------- the Hollow Knight
    comps = mob_base('hollow_knight', ['bc_hollow', 'undead', 'monster', 'mob'], 34, (0.6, 1.95), 0.27, 'loot_tables/entities/bc_hollow_knight.json', 10)
    comps.update(_melee_ai(6, targets=FOES))
    comps['minecraft:burns_in_daylight'] = {}
    write_json(BP, 'entities/v11/hollow_knight.json', _entity('hollow_knight', comps, spawnable=True))
    g = v11.hollow_knight_geo()
    g.write(out.path(RP, 'models/entity/bc/hollow_knight.geo.json'), out.path(RP, 'textures/entity/bc/hollow_knight.png'))
    ha = v11.hollow_knight_animations()
    ctx.animations['entity/hollow_knight.animation.json'] = ha
    _client('hollow_knight', 'geometry.bc.hollow_knight', 'textures/entity/bc/hollow_knight', 'entity_alphatest', {k.split('.')[-1]: k for k in ha},
            ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look_at_target'], egg={'base_color': '#17141e', 'overlay_color': '#7ad0ff'})
    _spawn('hollow_knight', ['plains', 'taiga', 'swamp', 'roofed', 'extreme_hills', 'cold'], 2, (1, 2), night=True)
    ctx.lang += [f'entity.{NS}:hollow_knight.name=Hollow Knight', f'item.spawn_egg.entity.{NS}:hollow_knight.name=Hollow Knight Spawn Egg']

    # ---------------------------------------------------------------- the Wanderer
    comps = mob_base('wanderer', ['bc_wanderer', 'mob'], 30, (0.6, 1.95), 0.25, 'loot_tables/empty.json', 0)
    comps.update({
        'minecraft:navigation.walk': {'can_path_over_water': True, 'avoid_water': True, 'can_open_doors': True, 'avoid_damage_blocks': True},
        'minecraft:movement.basic': {}, 'minecraft:jump.static': {}, 'minecraft:can_climb': {},
        'minecraft:persistent': {},
        'minecraft:behavior.float': {'priority': 0},
        'minecraft:behavior.panic': {'priority': 1, 'speed_multiplier': 1.4},
        'minecraft:behavior.look_at_player': {'priority': 4, 'look_distance': 8, 'probability': 0.6},
        'minecraft:behavior.random_stroll': {'priority': 6, 'speed_multiplier': 0.7, 'interval': 60},
        'minecraft:interact': {'interactions': [{'on_interact': {'filters': {'test': 'is_family', 'subject': 'other', 'value': 'player'}, 'event': 'bc:noop'},
                                                 'interact_text': 'action.interact.talk'}]},
    })
    n = len(WANDERERS)
    ent = _entity('wanderer', comps)
    ent['minecraft:entity']['description']['properties'] = {'bc:look': {'type': 'int', 'range': [0, n - 1], 'default': 0, 'client_sync': True}}
    ent['minecraft:entity']['events'] = {'bc:noop': {}, **{f'bc:look_{i}': {'set_property': {'bc:look': i}} for i in range(n)}}
    write_json(BP, 'entities/v11/wanderer.json', ent)
    wtex = {}
    for i in range(n):
        g = v11.wanderer_geo(i)
        g.write(out.path(RP, 'models/entity/bc/wanderer.geo.json'), out.path(RP, f'textures/entity/bc/wanderer/{i}.png'))
        wtex[f'v{i}'] = f'textures/entity/bc/wanderer/{i}'
    wn = v11.wanderer_animations()
    ctx.animations['entity/wanderer.animation.json'] = wn
    write_json(RP, 'entity/bc/wanderer.entity.json', {'format_version': '1.10.0', 'minecraft:client_entity': {'description': {
        'identifier': f'{NS}:wanderer', 'materials': {'default': 'entity_alphatest'}, 'textures': wtex,
        'geometry': {'default': 'geometry.bc.wanderer'}, 'animations': {k.split('.')[-1]: k for k in wn},
        'scripts': {'animate': ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look_at_target']},
        'render_controllers': ['controller.render.bc.wanderer'], 'spawn_egg': {'base_color': '#3a8452', 'overlay_color': '#9c6c18'}}}})
    rcs['controller.render.bc.wanderer'] = {
        'arrays': {'textures': {'Array.looks': [f'Texture.v{i}' for i in range(n)]}},
        'geometry': 'Geometry.default', 'materials': [{'*': 'Material.default'}], 'textures': ["Array.looks[q.property('bc:look')]"]}
    ctx.lang += [f'entity.{NS}:wanderer.name=Wanderer', f'item.spawn_egg.entity.{NS}:wanderer.name=Wanderer Spawn Egg']
    return rcs


def build(ctx: Ctx):
    gen_items(ctx)
    gen_blocks(ctx)
    gen_loot(ctx)
    rcs = gen_entities(ctx)
    write_json(RP, 'render_controllers/bc_v11.render_controllers.json', {'format_version': '1.10.0', 'render_controllers': rcs})
