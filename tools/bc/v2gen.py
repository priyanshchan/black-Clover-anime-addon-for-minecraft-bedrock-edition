"""v0.2.0 pack content: new enemies (Raider Gunner, Tidewatch Marksman, Hellhound, Mana Wraith), the Fallen Captain boss,
companion behaviour groups on Magic Knights (health tiers, passive stance), pack alerts, new items and recipes, and
the extra animation sets for knights, enemies, bosses and the player."""
from __future__ import annotations

import json

from . import out
from .data import FACTIONS, NS
from .models import v2
from .out import BP, RP, write_json, write_png
from .packgen import Ctx, item_json, mob_base, shaped
from .seagen import _client, _entity, _melee_ai
from .wave4gen import FACTION_FILES, add_team_groups

NEW_FILES = {
    'bc:raider_gunner': 'entities/v2/raider_gunner.json',
    'bc:tidewatch_marksman': 'entities/v2/tidewatch_marksman.json',
    'bc:hellhound': 'entities/v2/hellhound.json',
}
# hurt one, and its kind come running
ALERT_FILES = {
    'bc:dark_disciple': 'entities/dark_disciple.json', 'bc:imp': 'entities/grand/imp.json', 'bc:sea_raider': 'entities/sea/sea_raider.json',
    'bc:tidewatch_sentinel': 'entities/grand/tidewatch_sentinel.json', **NEW_FILES, 'bc:mana_wraith': 'entities/v2/mana_wraith.json',
}


def _icon(ctx, key, arr):
    icon = f'bc_{key}'
    ctx.item_textures[icon] = f'textures/items/bc/{key}'
    write_png(RP, f'textures/items/bc/{key}.png', arr)
    return icon


def _load(path, base=BP):
    with open(out.path(base, path)) as fh:
        return json.load(fh)


def _pool(item, lo, hi, chance=1.0):
    entries = [{'type': 'item', 'name': item, 'weight': 100, 'functions': [{'function': 'set_count', 'count': {'min': lo, 'max': hi}}]}]
    if chance < 1:
        entries.append({'type': 'empty', 'weight': int(100 * (1 - chance) / max(chance, 0.01))})
    return {'rolls': 1, 'entries': entries}


def keep_distance(families, dist=5.0):
    flt = {'any_of': [{'test': 'is_family', 'subject': 'other', 'value': f} for f in families]}
    return {'minecraft:behavior.avoid_mob_type': {'priority': 2, 'remove_target': False, 'entity_types': [
        {'filters': flt, 'max_dist': dist, 'walk_speed_multiplier': 1.1, 'sprint_speed_multiplier': 1.3}]}}


# ======================================================================================
def gen_items(ctx: Ctx):
    ic = v2.v2_icons()
    usable = {'minecraft:use_modifiers': {'use_duration': 0.6, 'movement_modifier': 1.0}}
    write_json(BP, 'items/v2/companion_whistle.json', item_json(f'{NS}:companion_whistle', '§bCompanion Whistle', _icon(ctx, 'companion_whistle', ic['companion_whistle']),
                                                                {'minecraft:max_stack_size': {'value': 1}, **usable}))
    write_json(BP, 'items/v2/mana_cookie.json', item_json(f'{NS}:mana_cookie', '§bMana Cookie', _icon(ctx, 'mana_cookie', ic['mana_cookie']), {
        'minecraft:max_stack_size': {'value': 64},
        'minecraft:food': {'nutrition': 3, 'saturation_modifier': 0.4, 'can_always_eat': True},
        'minecraft:use_modifiers': {'use_duration': 0.8, 'movement_modifier': 0.6},
        'minecraft:use_animation': 'eat',
    }))
    write_json(BP, 'items/v2/fallen_seal.json', item_json(f'{NS}:fallen_seal', '§4Seal of the Fallen Captain', _icon(ctx, 'fallen_seal', ic['fallen_seal']),
                                                          {'minecraft:max_stack_size': {'value': 1}, 'minecraft:glint': {'value': True}, **usable}))
    write_json(BP, 'recipes/v2/companion_whistle.json', shaped('companion_whistle', [' G ', 'GMG', ' I '], {
        'G': 'minecraft:gold_ingot', 'M': f'{NS}:mana_crystal', 'I': 'minecraft:iron_ingot'}))
    write_json(BP, 'recipes/v2/mana_cookie.json', {
        'format_version': '1.20.10',
        'minecraft:recipe_shapeless': {
            'description': {'identifier': f'{NS}:mana_cookie'}, 'tags': ['crafting_table'],
            'ingredients': [{'item': 'minecraft:cookie'}, {'item': 'minecraft:cookie'}, {'item': f'{NS}:mana_crystal'}],
            'unlock': {'context': 'AlwaysUnlocked'}, 'result': {'item': f'{NS}:mana_cookie', 'count': 4}}})
    write_json(BP, 'recipes/v2/fallen_seal.json', shaped('fallen_seal', ['OHO', 'KDK', 'OHO'], {
        'O': 'minecraft:crying_obsidian', 'H': f'{NS}:devil_heart', 'K': f'{NS}:knight_contract', 'D': 'minecraft:diamond'}))


def gen_loot(ctx: Ctx):
    write_json(BP, 'loot_tables/entities/bc_raider_gunner.json', {'pools': [_pool(f'{NS}:doubloon', 2, 5), _pool(f'{NS}:lead_shot', 2, 6, 0.6), _pool(f'{NS}:flintlock', 1, 1, 0.05)]})
    write_json(BP, 'loot_tables/entities/bc_tidewatch_marksman.json', {'pools': [_pool(f'{NS}:doubloon', 3, 7), _pool(f'{NS}:lead_shot', 3, 8, 0.6), _pool(f'{NS}:flintlock', 1, 1, 0.08)]})
    write_json(BP, 'loot_tables/entities/bc_hellhound.json', {'pools': [_pool('minecraft:blaze_powder', 1, 2, 0.6), _pool(f'{NS}:mana_crystal', 0, 1), _pool(f'{NS}:devil_heart', 1, 1, 0.02)]})
    write_json(BP, 'loot_tables/entities/bc_mana_wraith.json', {'pools': [_pool(f'{NS}:mana_crystal', 2, 4), _pool('minecraft:phantom_membrane', 0, 1)]})
    write_json(BP, 'loot_tables/entities/bc_fallen_captain.json', {'pools': [
        _pool(f'{NS}:clover_charm', 1, 1, 0.5), _pool(f'{NS}:knight_contract', 2, 3), _pool(f'{NS}:ancient_page', 4, 6), _pool(f'{NS}:mana_crystal', 12, 20),
        _pool(f'{NS}:devil_heart', 1, 2), _pool('minecraft:netherite_ingot', 1, 1, 0.35)]})


def gen_enemies(ctx: Ctx):
    # ---------------------------------------------------------------- Raider Gunner (from the Sea Raider)
    d = _load('entities/sea/sea_raider.json')
    e = d['minecraft:entity']
    e['description']['identifier'] = f'{NS}:raider_gunner'
    c = e['components']
    c['minecraft:type_family'] = {'family': ['bc_pirate', 'bc_gunner', 'monster', 'mob']}
    c['minecraft:health'] = {'value': 26, 'max': 26}
    c['minecraft:attack'] = {'damage': 3}
    c['minecraft:loot'] = {'table': 'loot_tables/entities/bc_raider_gunner.json'}
    c.update(keep_distance(['player', 'bc_knight', 'bc_navy']))
    write_json(BP, NEW_FILES['bc:raider_gunner'], d)
    g = v2.gunner_geo()
    g.write(out.path(RP, 'models/entity/bc/raider_gunner.geo.json'), out.path(RP, 'textures/entity/bc/raider_gunner.png'))
    ctx.animations['entity/raider_gunner.animation.json'] = v2.gun_animations('raider_gunner')
    _client('raider_gunner', 'geometry.bc.raider_gunner', 'textures/entity/bc/raider_gunner', 'entity_alphatest',
            {k.split('.')[-1]: k for k in v2.gun_animations('raider_gunner')}, ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look_at_target'],
            egg={'base_color': '#3e2818', 'overlay_color': '#d39a2c'})
    write_json(BP, 'spawn_rules/raider_gunner.json', {'format_version': '1.8.0', 'minecraft:spawn_rules': {
        'description': {'identifier': f'{NS}:raider_gunner', 'population_control': 'monster'},
        'conditions': [{'minecraft:spawns_on_surface': {}, 'minecraft:brightness_filter': {'min': 0, 'max': 7, 'adjust_for_weather': True},
                        'minecraft:difficulty_filter': {'min': 'easy', 'max': 'hard'}, 'minecraft:weight': {'default': 3},
                        'minecraft:herd': {'min_size': 1, 'max_size': 2}, 'minecraft:density_limit': {'surface': 3},
                        'minecraft:biome_filter': {'test': 'has_biome_tag', 'value': 'beach'}}]}})
    ctx.lang += [f'entity.{NS}:raider_gunner.name=Raider Gunner', f'item.spawn_egg.entity.{NS}:raider_gunner.name=Raider Gunner Spawn Egg']

    # ---------------------------------------------------------------- Tidewatch Marksman (from the Sentinel)
    d = _load('entities/grand/tidewatch_sentinel.json')
    e = d['minecraft:entity']
    e['description']['identifier'] = f'{NS}:tidewatch_marksman'
    for k in ('component_groups', 'events'):
        e.pop(k, None)
    c = e['components']
    c['minecraft:type_family'] = {'family': ['bc_navy', 'bc_marksman', 'monster', 'mob']}
    c['minecraft:health'] = {'value': 30, 'max': 30}
    c['minecraft:attack'] = {'damage': 3}
    c['minecraft:loot'] = {'table': 'loot_tables/entities/bc_tidewatch_marksman.json'}
    c.update(keep_distance(['player', 'bc_pirate', 'bc_devil', 'bc_disciple']))
    write_json(BP, NEW_FILES['bc:tidewatch_marksman'], d)
    g = v2.marksman_geo()
    g.write(out.path(RP, 'models/entity/bc/tidewatch_marksman.geo.json'), out.path(RP, 'textures/entity/bc/tidewatch_marksman.png'))
    ctx.animations['entity/tidewatch_marksman.animation.json'] = v2.gun_animations('tidewatch_marksman')
    _client('tidewatch_marksman', 'geometry.bc.tidewatch_marksman', 'textures/entity/bc/tidewatch_marksman', 'entity_alphatest',
            {k.split('.')[-1]: k for k in v2.gun_animations('tidewatch_marksman')}, ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look_at_target'],
            egg={'base_color': '#23345f', 'overlay_color': '#eceff4'})
    ctx.lang += [f'entity.{NS}:tidewatch_marksman.name=Tidewatch Marksman', f'item.spawn_egg.entity.{NS}:tidewatch_marksman.name=Tidewatch Marksman Spawn Egg']

    # ---------------------------------------------------------------- Hellhound (devil beast, packs)
    comps = mob_base('hellhound', ['bc_devil', 'bc_hound', 'monster', 'mob'], 30, (0.9, 1.1), 0.36, 'loot_tables/entities/bc_hellhound.json', 10)
    comps.update(_melee_ai(6, targets=('player', 'bc_knight', 'bc_navy', 'irongolem')))
    comps['minecraft:behavior.melee_box_attack']['speed_multiplier'] = 1.35
    comps['minecraft:fire_immune'] = True
    comps['minecraft:behavior.leap_at_target'] = {'priority': 3, 'yd': 0.4, 'must_be_on_ground': True}
    comps.pop('minecraft:can_climb', None)
    comps['minecraft:hurt_on_condition'] = {'damage_conditions': [{'filters': {'test': 'in_water', 'subject': 'self'}, 'cause': 'drowning', 'damage_per_tick': 1}]}
    write_json(BP, NEW_FILES['bc:hellhound'], _entity('hellhound', comps, spawnable=True))
    g = v2.hellhound_geo()
    g.write(out.path(RP, 'models/entity/bc/hellhound.geo.json'), out.path(RP, 'textures/entity/bc/hellhound.png'))
    ha = v2.hellhound_animations()
    ctx.animations['entity/hellhound.animation.json'] = ha
    _client('hellhound', 'geometry.bc.hellhound', 'textures/entity/bc/hellhound', 'entity_emissive_alpha',
            {k.split('.')[-1]: k for k in ha}, ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look_at_target'],
            egg={'base_color': '#1a0c0c', 'overlay_color': '#ff6a1a'})
    write_json(BP, 'spawn_rules/hellhound.json', {'format_version': '1.8.0', 'minecraft:spawn_rules': {
        'description': {'identifier': f'{NS}:hellhound', 'population_control': 'monster'},
        'conditions': [
            {'minecraft:spawns_on_surface': {}, 'minecraft:brightness_filter': {'min': 0, 'max': 7, 'adjust_for_weather': True},
             'minecraft:difficulty_filter': {'min': 'normal', 'max': 'hard'}, 'minecraft:weight': {'default': 2},
             'minecraft:herd': {'min_size': 2, 'max_size': 3}, 'minecraft:density_limit': {'surface': 3},
             'minecraft:biome_filter': {'test': 'has_biome_tag', 'value': 'monster'}},
            {'minecraft:spawns_on_surface': {}, 'minecraft:weight': {'default': 8}, 'minecraft:herd': {'min_size': 2, 'max_size': 4},
             'minecraft:density_limit': {'surface': 6}, 'minecraft:biome_filter': {'test': 'has_biome_tag', 'value': 'nether'}},
        ]}})
    ctx.lang += [f'entity.{NS}:hellhound.name=Hellhound', f'item.spawn_egg.entity.{NS}:hellhound.name=Hellhound Spawn Egg']

    # ---------------------------------------------------------------- Mana Wraith (night spirit, drains mana)
    d = _load('entities/grand/imp.json')
    e = d['minecraft:entity']
    e['description']['identifier'] = f'{NS}:mana_wraith'
    for k in ('component_groups', 'events'):
        e.pop(k, None)
    c = e['components']
    c['minecraft:type_family'] = {'family': ['bc_spirit', 'undead', 'monster', 'mob']}
    c['minecraft:health'] = {'value': 24, 'max': 24}
    c['minecraft:collision_box'] = {'width': 0.7, 'height': 2.0}
    c['minecraft:attack'] = {'damage': 4}
    c['minecraft:loot'] = {'table': 'loot_tables/entities/bc_mana_wraith.json'}
    c['minecraft:behavior.random_hover']['hover_height'] = [1, 3]
    c.update(keep_distance(['player', 'bc_knight'], 4.0))
    c['minecraft:burns_in_daylight'] = {}
    write_json(BP, 'entities/v2/mana_wraith.json', d)
    g = v2.wraith_geo()
    g.write(out.path(RP, 'models/entity/bc/mana_wraith.geo.json'), out.path(RP, 'textures/entity/bc/mana_wraith.png'))
    wa = v2.wraith_animations()
    ctx.animations['entity/mana_wraith.animation.json'] = wa
    _client('mana_wraith', 'geometry.bc.mana_wraith', 'textures/entity/bc/mana_wraith', 'entity_emissive_alpha',
            {k.split('.')[-1]: k for k in wa}, ['float', 'look_at_target'], egg={'base_color': '#0c1c1a', 'overlay_color': '#90ffe8'})
    write_json(BP, 'spawn_rules/mana_wraith.json', {'format_version': '1.8.0', 'minecraft:spawn_rules': {
        'description': {'identifier': f'{NS}:mana_wraith', 'population_control': 'monster'},
        'conditions': [{'minecraft:spawns_on_surface': {}, 'minecraft:brightness_filter': {'min': 0, 'max': 6, 'adjust_for_weather': True},
                        'minecraft:difficulty_filter': {'min': 'easy', 'max': 'hard'}, 'minecraft:weight': {'default': 3},
                        'minecraft:herd': {'min_size': 1, 'max_size': 2}, 'minecraft:density_limit': {'surface': 3},
                        'minecraft:biome_filter': {'any_of': [{'test': 'has_biome_tag', 'value': 'swamp'}, {'test': 'has_biome_tag', 'value': 'roofed'},
                                                              {'test': 'has_biome_tag', 'value': 'taiga'}, {'test': 'has_biome_tag', 'value': 'forest'}]}}]}})
    ctx.lang += [f'entity.{NS}:mana_wraith.name=Mana Wraith', f'item.spawn_egg.entity.{NS}:mana_wraith.name=Mana Wraith Spawn Egg']


def gen_fallen_captain(ctx: Ctx):
    comps = mob_base('fallen_captain', ['bc_devil', 'bc_boss', 'monster', 'mob', 'boss'], 700, (0.7, 2.1), 0.34, 'loot_tables/entities/bc_fallen_captain.json', 300)
    comps.update(_melee_ai(13, targets=('player', 'bc_knight', 'bc_navy', 'irongolem')))
    comps['minecraft:behavior.melee_box_attack']['speed_multiplier'] = 1.3
    comps['minecraft:boss'] = {'should_darken_sky': True, 'hud_range': 64}
    comps['minecraft:knockback_resistance'] = {'value': 0.7}
    comps['minecraft:persistent'] = {}
    comps['minecraft:follow_range'] = {'value': 64, 'max': 64}
    comps.pop('minecraft:despawn', None)
    comps['minecraft:damage_sensor'] = {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'drowning', 'deals_damage': 'no'}]}
    write_json(BP, 'entities/v2/fallen_captain.json', _entity('fallen_captain', comps))
    g = v2.fallen_captain_geo()
    g.write(out.path(RP, 'models/entity/bc/fallen_captain.geo.json'), out.path(RP, 'textures/entity/bc/fallen_captain.png'))
    fa = v2.fallen_captain_animations()
    ctx.animations['entity/fallen_captain.animation.json'] = fa
    _client('fallen_captain', 'geometry.bc.fallen_captain', 'textures/entity/bc/fallen_captain', 'entity_emissive_alpha',
            {**{k.split('.')[-1]: k for k in fa}, 'aura': 'animation.bc.mob.aura'}, ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look_at_target', 'aura'],
            particles={'aura': 'bc:devil_aura'}, egg={'base_color': '#16161c', 'overlay_color': '#d0202a'}, scale='1.15')
    ctx.lang += [f'entity.{NS}:fallen_captain.name=§4§lThe Fallen Captain', f'item.spawn_egg.entity.{NS}:fallen_captain.name=Fallen Captain Spawn Egg']


def gen_companion_groups(ctx: Ctx):
    """Magic Knights as companions: health tiers by level, and a passive stance that picks no fights."""
    rel = 'entities/living/magic_knight.json'
    d = _load(rel)
    e = d['minecraft:entity']
    groups = e['component_groups']
    events = e['events']
    from .data import COMPANION_HP
    for i, (_, hp) in enumerate(COMPANION_HP, start=1):
        groups[f'bc:hp_{i}'] = {'minecraft:health': {'value': hp, 'max': hp}}
        events[f'bc:hp_{i}'] = {'add': {'component_groups': [f'bc:hp_{i}']}, 'remove': {'component_groups': [f'bc:hp_{j}' for j in range(1, len(COMPANION_HP) + 1) if j != i]}}
    groups['bc:passive'] = {'minecraft:behavior.nearest_attackable_target': {'priority': 3, 'must_see': True, 'entity_types': [
        {'filters': {'test': 'is_family', 'subject': 'other', 'value': 'bc_nothing'}, 'max_dist': 1}]}}
    events['bc:passive_on'] = {'add': {'component_groups': ['bc:passive']}}
    events['bc:passive_off'] = {'remove': {'component_groups': ['bc:passive']}}
    write_json(BP, rel, d)


def gen_alerts(ctx: Ctx):
    for ident, rel in ALERT_FILES.items():
        d = _load(rel)
        c = d['minecraft:entity']['components']
        hbt = c.get('minecraft:behavior.hurt_by_target', {'priority': 1})
        hbt['alert_same_type'] = True
        c['minecraft:behavior.hurt_by_target'] = hbt
        write_json(BP, rel, d)


def gen_animations(ctx: Ctx):
    ctx.animations['entity/magic_knight.animation.json'].update(v2.knight_extra_animations())
    for f, anims in v2.boss_extra_animations().items():
        ctx.animations.setdefault(f, {}).update(anims)
    # list them on the client entities so scripts can play them
    for ident, extra in (('magic_knight', v2.knight_extra_animations()),
                         ('stone_colossus', v2.boss_extra_animations()['entity/stone_colossus.animation.json']),
                         ('archdevil', v2.boss_extra_animations()['entity/archdevil.animation.json']),
                         ('storm_kraken', v2.boss_extra_animations()['entity/storm_kraken.animation.json']),
                         ('phantom_galleon', v2.boss_extra_animations()['entity/phantom_galleon.animation.json'])):
        rel = f'entity/bc/{ident}.entity.json'
        d = _load(rel, RP)
        desc = d['minecraft:client_entity']['description']
        for k in extra:
            desc['animations'][k.split('.')[-1]] = k
        write_json(RP, rel, d)


def build(ctx: Ctx):
    gen_items(ctx)
    gen_loot(ctx)
    gen_enemies(ctx)
    gen_fallen_captain(ctx)
    gen_companion_groups(ctx)
    gen_alerts(ctx)
    for ident, rel in NEW_FILES.items():
        add_team_groups(rel, ident)
    have = {**FACTION_FILES, **NEW_FILES}
    for f in FACTIONS.values():
        for u in f['units'] + [f['leader']]:
            assert u in have, f'{u} has no War Table team groups'
    gen_animations(ctx)
