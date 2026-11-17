"""v0.3.0 pack content: flying brooms, amulets, the Mission Board block, Rogue Mages, the Witch Sisters, the Bone Dragon
and their items, recipes, loot and spawn rules."""
from __future__ import annotations

import json

from . import out
from .data import AMULETS, BROOMS, FACTIONS, NS
from .models import v2, v3
from .out import BP, RP, write_json, write_png
from .packgen import ENTITY_FMT, Ctx, item_json, mob_base, shaped
from .seagen import _client, _entity, _melee_ai
from .v2gen import keep_distance
from .wave4gen import add_team_groups

BROOM_TIERS = list(BROOMS)
ROGUE_VARIANTS = [k for k, _ in v3.ROGUE_COLORS]


def _icon(ctx, key, arr):
    icon = f'bc_{key}'
    ctx.item_textures[icon] = f'textures/items/bc/{key}'
    write_png(RP, f'textures/items/bc/{key}.png', arr)
    return icon


def _pool(item, lo, hi, chance=1.0):
    entries = [{'type': 'item', 'name': item, 'weight': 100, 'functions': [{'function': 'set_count', 'count': {'min': lo, 'max': hi}}]}]
    if chance < 1:
        entries.append({'type': 'empty', 'weight': int(100 * (1 - chance) / max(chance, 0.01))})
    return {'rolls': 1, 'entries': entries}


def _amulet_pool(chance):
    entries = [{'type': 'item', 'name': f'{NS}:{k}', 'weight': 10} for k in AMULETS]
    entries.append({'type': 'empty', 'weight': int(10 * len(AMULETS) * (1 - chance) / chance)})
    return {'rolls': 1, 'entries': entries}


# ======================================================================================
def gen_items(ctx: Ctx):
    ic = v3.v3_icons()
    usable = {'minecraft:use_modifiers': {'use_duration': 0.6, 'movement_modifier': 1.0}}
    for tier, (name, _, _) in BROOMS.items():
        write_json(BP, f'items/v3/{tier}.json', item_json(f'{NS}:{tier}', name, _icon(ctx, tier, ic[tier]), {'minecraft:max_stack_size': {'value': 1}, **usable}, category='equipment'))
    for key, (name, perk) in AMULETS.items():
        write_json(BP, f'items/v3/{key}.json', item_json(f'{NS}:{key}', name, _icon(ctx, key, ic[key]), {
            'minecraft:max_stack_size': {'value': 1}, 'minecraft:allow_off_hand': {'value': True}, 'minecraft:glint': {'value': True}}, category='equipment'))
    write_json(BP, 'items/v3/twin_moon_charm.json', item_json(f'{NS}:twin_moon_charm', '§bTwin §cMoon §fCharm', _icon(ctx, 'twin_moon_charm', ic['twin_moon_charm']),
                                                               {'minecraft:max_stack_size': {'value': 1}, 'minecraft:glint': {'value': True}, **usable}))
    write_json(BP, 'items/v3/bone_totem.json', item_json(f'{NS}:bone_totem', '§aDragon Bone Totem', _icon(ctx, 'bone_totem', ic['bone_totem']),
                                                          {'minecraft:max_stack_size': {'value': 1}, 'minecraft:glint': {'value': True}, **usable}))
    # recipes
    write_json(BP, 'recipes/v3/broom.json', shaped('broom', ['  M', ' S ', 'H  '], {'M': f'{NS}:mana_crystal', 'S': 'minecraft:stick', 'H': 'minecraft:hay_block'}))
    write_json(BP, 'recipes/v3/swift_broom.json', shaped('swift_broom', ['FDF', ' B ', ' F '], {'F': 'minecraft:feather', 'D': 'minecraft:diamond', 'B': f'{NS}:broom'}))
    gems = {'amulet_mana': 'minecraft:lapis_block', 'amulet_swift': 'minecraft:emerald', 'amulet_power': 'minecraft:redstone_block',
            'amulet_guard': 'minecraft:iron_block', 'amulet_vigor': 'minecraft:golden_apple'}
    for key, gem in gems.items():
        write_json(BP, f'recipes/v3/{key}.json', shaped(key, ['GSG', 'GMG', ' X '], {'G': 'minecraft:gold_nugget', 'S': 'minecraft:string',
                                                                                       'M': f'{NS}:mana_crystal', 'X': gem}))
    write_json(BP, 'recipes/v3/twin_moon_charm.json', shaped('twin_moon_charm', ['ICM', 'CAC', 'MCI'], {
        'I': 'minecraft:packed_ice', 'M': 'minecraft:magma', 'C': f'{NS}:mana_crystal', 'A': 'minecraft:amethyst_block'}))
    write_json(BP, 'recipes/v3/bone_totem.json', shaped('bone_totem', ['BSB', 'BCB', 'BBB'], {
        'B': 'minecraft:bone_block', 'S': 'minecraft:wither_skeleton_skull', 'C': f'{NS}:mana_crystal'}))
    write_json(BP, 'recipes/v3/mission_board.json', shaped('mission_board', ['PPP', 'XGX', 'S S'], {
        'P': 'minecraft:oak_planks', 'X': 'minecraft:paper', 'G': 'minecraft:green_dye', 'S': 'minecraft:stick'}))


def gen_block(ctx: Ctx):
    g = v3.mission_board_geo()
    g.paint()
    a = g.atlas
    a[..., 3] = (a[..., 3] > 0) * 255.0
    write_json(RP, 'models/blocks/bc/mission_board.geo.json', g.to_json())
    write_png(RP, 'textures/blocks/bc/mission_board.png', a)
    ctx.terrain_textures['bc_mission_board'] = 'textures/blocks/bc/mission_board'
    dirs = {'north': 0, 'east': -90, 'south': 180, 'west': 90}
    write_json(BP, 'blocks/mission_board.json', {
        'format_version': '1.21.90',
        'minecraft:block': {
            'description': {
                'identifier': f'{NS}:mission_board',
                'menu_category': {'category': 'items'},
                'traits': {'minecraft:placement_direction': {'enabled_states': ['minecraft:cardinal_direction'], 'y_rotation_offset': 180}},
            },
            'components': {
                'minecraft:geometry': 'geometry.bc.mission_board',
                'minecraft:material_instances': {'*': {'texture': 'bc_mission_board', 'render_method': 'alpha_test'}},
                'minecraft:collision_box': {'origin': [-8, 0, -2], 'size': [16, 16, 4]},
                'minecraft:selection_box': {'origin': [-8, 0, -2], 'size': [16, 16, 4]},
                'minecraft:destructible_by_mining': {'seconds_to_destroy': 1.5},
                'minecraft:destructible_by_explosion': {'explosion_resistance': 5},
                'minecraft:flammable': {'catch_chance_modifier': 5, 'destroy_chance_modifier': 20},
                'minecraft:light_dampening': 0,
                'minecraft:map_color': '#2a7234',
                'bc:mission_board': {},
            },
            'permutations': [
                {'condition': f"q.block_state('minecraft:cardinal_direction') == '{d}'",
                 'components': {'minecraft:transformation': {'rotation': [0, r, 0]}}}
                for d, r in dirs.items()
            ],
        },
    })
    ctx.lang.append(f'tile.{NS}:mission_board.name=§2Mission Board')


def gen_loot(ctx: Ctx):
    write_json(BP, 'loot_tables/entities/bc_rogue_mage.json', {'pools': [
        _pool(f'{NS}:ancient_page', 1, 1, 0.4), _pool(f'{NS}:mana_crystal', 1, 3), _pool(f'{NS}:doubloon', 3, 8), _amulet_pool(0.03)]})
    for w in ('frost_witch', 'ember_witch'):
        write_json(BP, f'loot_tables/entities/bc_{w}.json', {'pools': [
            _pool(f'{NS}:mana_crystal', 8, 14), _pool(f'{NS}:ancient_page', 2, 4), _amulet_pool(0.5),
            _pool('minecraft:packed_ice' if w == 'frost_witch' else 'minecraft:blaze_rod', 4, 8), _pool(f'{NS}:clover_charm', 1, 1, 0.2)]})
    write_json(BP, 'loot_tables/entities/bc_bone_dragon.json', {'pools': [
        _pool('minecraft:bone_block', 8, 16), _pool('minecraft:wither_skeleton_skull', 1, 1, 0.5), _pool(f'{NS}:mana_crystal', 12, 20),
        _amulet_pool(0.8), _pool('minecraft:netherite_scrap', 2, 4), _pool(f'{NS}:clover_charm', 1, 1, 0.3)]})


def _flyer(comps, height, speed=0.22):
    comps.update({
        'minecraft:can_fly': {},
        'minecraft:flying_speed': {'value': speed},
        'minecraft:navigation.hover': {'can_path_over_water': True, 'can_sink': False, 'can_pass_doors': False, 'can_path_from_air': True, 'avoid_water': False},
        'minecraft:movement.hover': {},
        'minecraft:physics': {'has_gravity': False},
        'minecraft:knockback_resistance': {'value': 1.0},
        'minecraft:persistent': {},
        'minecraft:follow_range': {'value': 64, 'max': 64},
        'minecraft:damage_sensor': {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'drowning', 'deals_damage': 'no'}, {'cause': 'suffocation', 'deals_damage': 'no'}]},
        'minecraft:behavior.hurt_by_target': {'priority': 1},
        'minecraft:behavior.random_hover': {'priority': 6, 'xz_dist': 10, 'y_dist': 4, 'y_offset': 0, 'interval': 1, 'hover_height': height},
        'minecraft:behavior.look_at_player': {'priority': 7, 'look_distance': 16, 'probability': 0.2},
    })
    comps.pop('minecraft:hurt_on_condition', None)
    comps.pop('minecraft:despawn', None)
    return comps


def gen_entities(ctx: Ctx):
    # ---------------------------------------------------------------- brooms
    comps = {
        'minecraft:type_family': {'family': ['bc_broom', 'inanimate']},
        'minecraft:health': {'value': 30, 'max': 30},
        'minecraft:collision_box': {'width': 0.9, 'height': 0.5},
        'minecraft:physics': {'has_gravity': False},
        'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': False},
        'minecraft:knockback_resistance': {'value': 1.0},
        'minecraft:movement': {'value': 0.0},
        'minecraft:damage_sensor': {'triggers': [{'cause': 'all', 'deals_damage': 'no'}]},
        'minecraft:rideable': {'seat_count': 1, 'crouching_skip_interact': True, 'family_types': ['player'], 'interact_text': 'action.interact.ride.horse',
                               'pull_in_entities': False, 'seats': [{'position': [0.0, 0.45, 0.15]}]},
        'minecraft:conditional_bandwidth_optimization': {'default_values': {'max_optimized_distance': 64.0, 'max_dropped_ticks': 2, 'use_motion_prediction_hints': True}},
    }
    props = {'bc:tier': {'type': 'int', 'range': [0, len(BROOM_TIERS) - 1], 'default': 0, 'client_sync': True}}
    write_json(BP, 'entities/v3/broom.json', {'format_version': ENTITY_FMT, 'minecraft:entity': {
        'description': {'identifier': f'{NS}:broom', 'is_spawnable': False, 'is_summonable': True, 'properties': props},
        'component_groups': {}, 'components': comps, 'events': {}}})
    textures = {}
    for i, tier in enumerate(BROOM_TIERS):
        g = v3.broom_geo(tier)
        g.write(out.path(RP, 'models/entity/bc/broom.geo.json'), out.path(RP, f'textures/entity/bc/broom/{tier}.png'))
        textures[f't{i}'] = f'textures/entity/bc/broom/{tier}'
    ctx.animations['entity/broom.animation.json'] = v3.broom_animations()
    write_json(RP, 'entity/bc/broom.entity.json', {'format_version': '1.10.0', 'minecraft:client_entity': {'description': {
        'identifier': f'{NS}:broom', 'materials': {'default': 'entity_emissive_alpha'}, 'textures': textures,
        'geometry': {'default': 'geometry.bc.broom'}, 'animations': {'fly': 'animation.bc.broom.fly'},
        'scripts': {'animate': ['fly']}, 'render_controllers': ['controller.render.bc.broom']}}})
    ctx.lang.append(f'entity.{NS}:broom.name=Magic Broom')
    rcs = {'controller.render.bc.broom': {
        'arrays': {'textures': {'Array.tiers': [f'Texture.t{i}' for i in range(len(BROOM_TIERS))]}},
        'geometry': 'Geometry.default', 'materials': [{'*': 'Material.default'}], 'textures': ["Array.tiers[q.property('bc:tier')]"]}}

    # ---------------------------------------------------------------- Rogue Mages
    comps = mob_base('rogue_mage', ['bc_rogue', 'monster', 'mob'], 34, (0.6, 1.95), 0.3, 'loot_tables/entities/bc_rogue_mage.json', 12)
    comps.update(_melee_ai(5, targets=('player', 'bc_knight', 'bc_navy', 'irongolem')))
    comps['minecraft:behavior.hurt_by_target'] = {'priority': 1, 'alert_same_type': True}
    comps.update(keep_distance(['player', 'bc_knight', 'bc_navy']))
    props = {'bc:variant': {'type': 'int', 'range': [0, len(ROGUE_VARIANTS) - 1], 'default': 0, 'client_sync': True}}
    ent = _entity('rogue_mage', comps, spawnable=True)
    ent['minecraft:entity']['description']['properties'] = props
    ent['minecraft:entity']['events'] = {'minecraft:entity_spawned': {'randomize': [{'weight': 1, 'set_property': {'bc:variant': i}} for i in range(len(ROGUE_VARIANTS))]}}
    write_json(BP, 'entities/v3/rogue_mage.json', ent)
    add_team_groups('entities/v3/rogue_mage.json', 'bc:rogue_mage')
    textures = {}
    for i, v in enumerate(ROGUE_VARIANTS):
        g = v3.rogue_geo(v)
        g.write(out.path(RP, 'models/entity/bc/rogue_mage.geo.json'), out.path(RP, f'textures/entity/bc/rogue/{v}.png'))
        textures[f'v{i}'] = f'textures/entity/bc/rogue/{v}'
    knight_anims = {k.split('.')[-1]: k for k in ('animation.bc.magic_knight.idle', 'animation.bc.magic_knight.walk', 'animation.bc.magic_knight.look_at_target',
                                                  'animation.bc.magic_knight.cast', 'animation.bc.magic_knight.attack')}
    knight_anims.update({k.split('.')[-1]: k for k in v2.knight_extra_animations()})
    write_json(RP, 'entity/bc/rogue_mage.entity.json', {'format_version': '1.10.0', 'minecraft:client_entity': {'description': {
        'identifier': f'{NS}:rogue_mage', 'materials': {'default': 'entity_alphatest'}, 'textures': textures,
        'geometry': {'default': 'geometry.bc.rogue_mage'}, 'animations': knight_anims,
        'scripts': {'animate': ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look_at_target']},
        'render_controllers': ['controller.render.bc.rogue_mage'], 'spawn_egg': {'base_color': '#2e080c', 'overlay_color': '#4a3624'}}}})
    rcs['controller.render.bc.rogue_mage'] = {
        'arrays': {'textures': {'Array.variants': [f'Texture.v{i}' for i in range(len(ROGUE_VARIANTS))]}},
        'geometry': 'Geometry.default', 'materials': [{'*': 'Material.default'}], 'textures': ["Array.variants[q.property('bc:variant')]"]}
    write_json(BP, 'spawn_rules/rogue_mage.json', {'format_version': '1.8.0', 'minecraft:spawn_rules': {
        'description': {'identifier': f'{NS}:rogue_mage', 'population_control': 'monster'},
        'conditions': [{'minecraft:spawns_on_surface': {}, 'minecraft:brightness_filter': {'min': 0, 'max': 7, 'adjust_for_weather': True},
                        'minecraft:difficulty_filter': {'min': 'easy', 'max': 'hard'}, 'minecraft:weight': {'default': 3},
                        'minecraft:herd': {'min_size': 2, 'max_size': 3}, 'minecraft:density_limit': {'surface': 4},
                        'minecraft:biome_filter': {'any_of': [{'test': 'has_biome_tag', 'value': 'plains'}, {'test': 'has_biome_tag', 'value': 'forest'},
                                                              {'test': 'has_biome_tag', 'value': 'taiga'}, {'test': 'has_biome_tag', 'value': 'savanna'}]}}]}})
    ctx.lang += [f'entity.{NS}:rogue_mage.name=Rogue Mage', f'item.spawn_egg.entity.{NS}:rogue_mage.name=Rogue Mage Spawn Egg']

    # ---------------------------------------------------------------- the Witch Sisters
    for kind, label, egg in (('frost_witch', '§b§lThe Frost Witch', ('#122a46', '#c6f0fb')), ('ember_witch', '§c§lThe Ember Witch', ('#2e0808', '#f0c24a'))):
        comps = mob_base(kind, ['bc_witch', 'bc_boss', 'monster', 'mob', 'boss'], 450, (0.7, 2.6), 0.3, f'loot_tables/entities/bc_{kind}.json', 200)
        _flyer(comps, [2, 5], 0.24)
        comps['minecraft:boss'] = {'should_darken_sky': True, 'hud_range': 64}
        comps['minecraft:behavior.nearest_attackable_target'] = {'priority': 2, 'must_see': False, 'reselect_targets': True, 'entity_types': [
            {'filters': {'any_of': [{'test': 'is_family', 'subject': 'other', 'value': f} for f in ('player', 'bc_knight', 'bc_navy')]}, 'max_dist': 40}]}
        comps.update(keep_distance(['player', 'bc_knight'], 6.0))
        if kind == 'ember_witch':
            comps['minecraft:fire_immune'] = True
        write_json(BP, f'entities/v3/{kind}.json', _entity(kind, comps))
        g = v3.witch_geo(kind)
        g.write(out.path(RP, f'models/entity/bc/{kind}.geo.json'), out.path(RP, f'textures/entity/bc/{kind}.png'))
        wa = v3.witch_animations(kind)
        ctx.animations[f'entity/{kind}.animation.json'] = wa
        _client(kind, f'geometry.bc.{kind}', f'textures/entity/bc/{kind}', 'entity_emissive_alpha',
                {**{k.split('.')[-1]: k for k in wa}, 'aura': 'animation.bc.mob.aura'}, ['float', 'look_at_target', 'aura'],
                particles={'aura': 'bc:disciple_aura'}, egg={'base_color': egg[0], 'overlay_color': egg[1]}, scale='1.25')
        ctx.lang += [f'entity.{NS}:{kind}.name={label}', f'item.spawn_egg.entity.{NS}:{kind}.name={label.replace("§l", "")[2:]} Spawn Egg']

    # ---------------------------------------------------------------- the Bone Dragon
    comps = mob_base('bone_dragon', ['bc_dragon', 'bc_boss', 'undead', 'monster', 'mob', 'boss'], 1100, (3.0, 2.6), 0.3, 'loot_tables/entities/bc_bone_dragon.json', 400)
    _flyer(comps, [6, 12], 0.26)
    comps['minecraft:boss'] = {'should_darken_sky': True, 'hud_range': 80}
    comps['minecraft:fire_immune'] = True
    comps['minecraft:behavior.nearest_attackable_target'] = {'priority': 2, 'must_see': False, 'reselect_targets': True, 'entity_types': [
        {'filters': {'any_of': [{'test': 'is_family', 'subject': 'other', 'value': f} for f in ('player', 'bc_knight', 'bc_navy')]}, 'max_dist': 48}]}
    write_json(BP, 'entities/v3/bone_dragon.json', _entity('bone_dragon', comps))
    g = v3.bone_dragon_geo()
    g.write(out.path(RP, 'models/entity/bc/bone_dragon.geo.json'), out.path(RP, 'textures/entity/bc/bone_dragon.png'))
    da = v3.bone_dragon_animations()
    ctx.animations['entity/bone_dragon.animation.json'] = da
    _client('bone_dragon', 'geometry.bc.bone_dragon', 'textures/entity/bc/bone_dragon', 'entity_emissive_alpha',
            {k.split('.')[-1]: k for k in da}, ['fly', 'look_at_target'], egg={'base_color': '#c2b8a0', 'overlay_color': '#7ae04a'}, scale='2.4')
    ctx.lang += [f'entity.{NS}:bone_dragon.name=§a§lThe Bone Dragon', f'item.spawn_egg.entity.{NS}:bone_dragon.name=Bone Dragon Spawn Egg']
    return rcs


def check_armies():
    """Every War Table soldier must have the team groups (bc:team_a / b / c)."""
    import os
    events = {}
    for dp, _, fs in os.walk(out.path(BP, 'entities')):
        for f in fs:
            with open(os.path.join(dp, f)) as fh:
                e = json.load(fh)['minecraft:entity']
            events[e['description']['identifier']] = set(e.get('events', {}))
    for f in FACTIONS.values():
        for u in f['units'] + [f['leader']]:
            assert {'bc:team_a', 'bc:team_b', 'bc:team_c'} <= events.get(u, set()), f'{u} has no War Table team groups'


def build(ctx: Ctx):
    gen_items(ctx)
    gen_block(ctx)
    gen_loot(ctx)
    rcs = gen_entities(ctx)
    write_json(RP, 'render_controllers/bc_v3.render_controllers.json', {'format_version': '1.10.0', 'render_controllers': rcs})
    check_armies()
