"""v0.5.0 pack content: the companion update (Squad Banner, Training Dummy, Clover Leaf of Return, Field Rations,
Companion Tome, companion emotes and broom riding) and the Soul Puppeteer with its marionettes."""
from __future__ import annotations

import json

from . import out
from .data import NS
from .models import v5
from .out import BP, RP, write_json, write_png
from .packgen import Ctx, item_json, mob_base, shaped
from .seagen import _client, _entity, _melee_ai
from .v2gen import keep_distance
from .v3gen import _amulet_pool, _flyer, _icon, _pool


def _load(rel, base=BP):
    with open(out.path(base, rel), encoding='utf-8') as fh:
        return json.load(fh)


# ======================================================================================
def gen_items(ctx: Ctx):
    ic = v5.v5_icons()
    usable = {'minecraft:use_modifiers': {'use_duration': 0.6, 'movement_modifier': 1.0}}
    one = {'minecraft:max_stack_size': {'value': 1}}
    write_json(BP, 'items/v5/training_dummy.json', item_json(f'{NS}:training_dummy', '§6Training Dummy', _icon(ctx, 'training_dummy', ic['training_dummy']),
                                                             {'minecraft:max_stack_size': {'value': 16}, **usable}, category='items'))
    write_json(BP, 'items/v5/clover_leaf.json', item_json(f'{NS}:clover_leaf', '§aClover Leaf of Return', _icon(ctx, 'clover_leaf', ic['clover_leaf']),
                                                          {'minecraft:max_stack_size': {'value': 16}, 'minecraft:glint': {'value': True}, **usable}))
    write_json(BP, 'items/v5/field_rations.json', item_json(f'{NS}:field_rations', '§6Field Rations', _icon(ctx, 'field_rations', ic['field_rations']), {
        'minecraft:max_stack_size': {'value': 16},
        'minecraft:food': {'nutrition': 8, 'saturation_modifier': 0.8, 'can_always_eat': False},
        'minecraft:use_modifiers': {'use_duration': 1.6, 'movement_modifier': 0.35},
        'minecraft:use_animation': 'eat',
    }))
    write_json(BP, 'items/v5/companion_tome.json', item_json(f'{NS}:companion_tome', '§bCompanion Tome', _icon(ctx, 'companion_tome', ic['companion_tome']),
                                                             {**one, 'minecraft:glint': {'value': True}, **usable}))
    write_json(BP, 'items/v5/cursed_spool.json', item_json(f'{NS}:cursed_spool', '§5Cursed Spool', _icon(ctx, 'cursed_spool', ic['cursed_spool']),
                                                           {**one, 'minecraft:glint': {'value': True}, **usable}))
    # recipes
    write_json(BP, 'recipes/v5/squad_banner.json', shaped('squad_banner', ['WCW', 'WGW', ' S '], {
        'W': 'minecraft:green_wool', 'C': f'{NS}:mana_crystal', 'G': 'minecraft:gold_ingot', 'S': 'minecraft:stick'}))
    write_json(BP, 'recipes/v5/training_dummy.json', shaped('training_dummy', ['HTH', ' S ', ' S '], {
        'H': 'minecraft:hay_block', 'T': 'minecraft:target', 'S': 'minecraft:stick'}))
    write_json(BP, 'recipes/v5/clover_leaf.json', shaped('clover_leaf', ['ECE', 'CGC', 'ECE'], {
        'E': 'minecraft:emerald', 'C': f'{NS}:mana_crystal', 'G': 'minecraft:golden_apple'}))
    write_json(BP, 'recipes/v5/field_rations.json', {
        'format_version': '1.20.10',
        'minecraft:recipe_shapeless': {
            'description': {'identifier': f'{NS}:field_rations'}, 'tags': ['crafting_table'],
            'ingredients': [{'item': 'minecraft:bread'}, {'item': 'minecraft:cooked_beef'}, {'item': 'minecraft:apple'}, {'item': f'{NS}:mana_cookie'}],
            'unlock': {'context': 'AlwaysUnlocked'}, 'result': {'item': f'{NS}:field_rations', 'count': 3}}})
    write_json(BP, 'recipes/v5/companion_tome.json', {
        'format_version': '1.20.10',
        'minecraft:recipe_shapeless': {
            'description': {'identifier': f'{NS}:companion_tome'}, 'tags': ['crafting_table'],
            'ingredients': [{'item': 'minecraft:book'}, {'item': f'{NS}:ancient_page'}, {'item': f'{NS}:mana_crystal'}],
            'unlock': {'context': 'AlwaysUnlocked'}, 'result': {'item': f'{NS}:companion_tome', 'count': 1}}})
    write_json(BP, 'recipes/v5/cursed_spool.json', shaped('cursed_spool', ['SHS', 'PEP', 'SHS'], {
        'S': 'minecraft:string', 'H': f'{NS}:devil_heart', 'P': 'minecraft:phantom_membrane', 'E': 'minecraft:ender_pearl'}))


def gen_block(ctx: Ctx):
    g = v5.squad_banner_geo()
    g.paint()
    a = g.atlas
    a[..., 3] = (a[..., 3] > 0) * 255.0
    write_json(RP, 'models/blocks/bc/squad_banner.geo.json', g.to_json())
    write_png(RP, 'textures/blocks/bc/squad_banner.png', a)
    ctx.terrain_textures['bc_squad_banner'] = 'textures/blocks/bc/squad_banner'
    dirs = {'north': 0, 'east': -90, 'south': 180, 'west': 90}
    write_json(BP, 'blocks/squad_banner.json', {
        'format_version': '1.21.90',
        'minecraft:block': {
            'description': {
                'identifier': f'{NS}:squad_banner',
                'menu_category': {'category': 'items'},
                'traits': {'minecraft:placement_direction': {'enabled_states': ['minecraft:cardinal_direction'], 'y_rotation_offset': 180}},
            },
            'components': {
                'minecraft:geometry': 'geometry.bc.squad_banner',
                'minecraft:material_instances': {'*': {'texture': 'bc_squad_banner', 'render_method': 'alpha_test'}},
                'minecraft:collision_box': {'origin': [-4, 0, -4], 'size': [8, 16, 8]},
                'minecraft:selection_box': {'origin': [-7, 0, -4], 'size': [14, 16, 8]},
                'minecraft:destructible_by_mining': {'seconds_to_destroy': 1.0},
                'minecraft:destructible_by_explosion': {'explosion_resistance': 5},
                'minecraft:light_dampening': 0,
                'minecraft:light_emission': 4,
                'minecraft:map_color': '#1e5628',
                'bc:squad_banner': {},
            },
            'permutations': [
                {'condition': f"q.block_state('minecraft:cardinal_direction') == '{d}'",
                 'components': {'minecraft:transformation': {'rotation': [0, r, 0]}}}
                for d, r in dirs.items()
            ],
        },
    })
    ctx.lang.append(f'tile.{NS}:squad_banner.name=§2Squad Banner')


def gen_loot(ctx: Ctx):
    write_json(BP, 'loot_tables/entities/bc_soul_puppeteer.json', {'pools': [
        _pool(f'{NS}:mana_crystal', 10, 16), _pool(f'{NS}:ancient_page', 2, 4), _amulet_pool(0.6), _pool(f'{NS}:clover_leaf', 1, 1, 0.5),
        _pool(f'{NS}:companion_tome', 1, 1, 0.35), _pool('minecraft:string', 6, 12), _pool(f'{NS}:clover_charm', 1, 1, 0.25)]})
    write_json(BP, 'loot_tables/entities/bc_puppet.json', {'pools': [_pool('minecraft:string', 0, 2), _pool('minecraft:stick', 0, 1)]})


def gen_entities(ctx: Ctx):
    rcs = {}
    # ---------------------------------------------------------------- the Training Dummy
    comps = {
        'minecraft:type_family': {'family': ['bc_dummy']},
        'minecraft:health': {'value': 1000, 'max': 1000},
        'minecraft:collision_box': {'width': 0.8, 'height': 1.9},
        'minecraft:physics': {},
        'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': False},
        'minecraft:knockback_resistance': {'value': 1.0},
        'minecraft:movement': {'value': 0.0},
        'minecraft:persistent': {},
        'minecraft:nameable': {'always_show': True, 'allow_name_tag_renaming': False},
        'minecraft:damage_sensor': {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'suffocation', 'deals_damage': 'no'}, {'cause': 'drowning', 'deals_damage': 'no'}]},
        'minecraft:interact': {'interactions': [{'interact_text': 'action.interact.bc_pickup', 'on_interact': {
            'filters': {'all_of': [{'test': 'is_family', 'subject': 'other', 'value': 'player'}, {'test': 'is_sneaking', 'subject': 'other', 'value': True}]},
            'event': 'bc:poke', 'target': 'self'}}]},
    }
    ent = _entity('training_dummy', comps)
    ent['minecraft:entity']['events'] = {'bc:poke': {}}
    write_json(BP, 'entities/v5/training_dummy.json', ent)
    g = v5.training_dummy_geo()
    g.write(out.path(RP, 'models/entity/bc/training_dummy.geo.json'), out.path(RP, 'textures/entity/bc/training_dummy.png'))
    ta = v5.training_dummy_animations()
    ctx.animations['entity/training_dummy.animation.json'] = ta
    _client('training_dummy', 'geometry.bc.training_dummy', 'textures/entity/bc/training_dummy', 'entity_alphatest', {k.split('.')[-1]: k for k in ta}, [])
    ctx.lang += [f'entity.{NS}:training_dummy.name=Training Dummy', 'action.interact.bc_pickup=Pick up']

    # ---------------------------------------------------------------- the Soul Puppeteer
    comps = mob_base('soul_puppeteer', ['bc_devil', 'bc_puppeteer', 'bc_boss', 'monster', 'mob', 'boss'], 600, (0.9, 3.0), 0.3,
                     'loot_tables/entities/bc_soul_puppeteer.json', 300)
    _flyer(comps, [3, 6], 0.22)
    comps['minecraft:boss'] = {'should_darken_sky': True, 'hud_range': 64}
    comps['minecraft:behavior.nearest_attackable_target'] = {'priority': 2, 'must_see': False, 'reselect_targets': True, 'entity_types': [
        {'filters': {'any_of': [{'test': 'is_family', 'subject': 'other', 'value': f} for f in ('player', 'bc_knight', 'bc_navy')]}, 'max_dist': 40}]}
    comps.update(keep_distance(['player', 'bc_knight'], 7.0))
    write_json(BP, 'entities/v5/soul_puppeteer.json', _entity('soul_puppeteer', comps))
    g = v5.puppeteer_geo()
    g.write(out.path(RP, 'models/entity/bc/soul_puppeteer.geo.json'), out.path(RP, 'textures/entity/bc/soul_puppeteer.png'))
    pa = v5.puppeteer_animations()
    ctx.animations['entity/soul_puppeteer.animation.json'] = pa
    _client('soul_puppeteer', 'geometry.bc.soul_puppeteer', 'textures/entity/bc/soul_puppeteer', 'entity_alphatest',
            {**{k.split('.')[-1]: k for k in pa}, 'aura': 'animation.bc.mob.aura'}, ['float', 'look_at_target', 'aura'],
            particles={'aura': 'bc:devil_aura'}, egg={'base_color': '#180a20', 'overlay_color': '#dcd8dc'}, scale='1.3')
    ctx.lang += [f'entity.{NS}:soul_puppeteer.name=§5§lThe Soul Puppeteer', f'item.spawn_egg.entity.{NS}:soul_puppeteer.name=Soul Puppeteer Spawn Egg']

    # ---------------------------------------------------------------- marionettes
    comps = mob_base('puppet', ['bc_puppet', 'bc_devil', 'monster', 'mob'], 16, (0.5, 1.0), 0.34, 'loot_tables/entities/bc_puppet.json', 3)
    comps.update(_melee_ai(3, targets=('player', 'bc_knight', 'bc_navy')))
    write_json(BP, 'entities/v5/puppet.json', _entity('puppet', comps))
    g = v5.puppet_geo()
    g.write(out.path(RP, 'models/entity/bc/puppet.geo.json'), out.path(RP, 'textures/entity/bc/puppet.png'))
    pu = v5.puppet_animations()
    ctx.animations['entity/puppet.animation.json'] = pu
    _client('puppet', 'geometry.bc.puppet', 'textures/entity/bc/puppet', 'entity_alphatest', {k.split('.')[-1]: k for k in pu},
            [{'idle': 'q.modified_move_speed < 0.02'}, {'walk': 'q.modified_move_speed >= 0.02'}], egg={'base_color': '#86583a', 'overlay_color': '#741a2a'})
    ctx.lang += [f'entity.{NS}:puppet.name=Marionette', f'item.spawn_egg.entity.{NS}:puppet.name=Marionette Spawn Egg']
    return rcs


def gen_companion_anims(ctx: Ctx):
    """Companion emotes and broom riding for knights (and the Rogue Mages, who share their animations)."""
    extra = v5.knight_v5_animations()
    ctx.animations['entity/magic_knight.animation.json'].update(extra)
    for ident in ('magic_knight', 'rogue_mage'):
        rel = f'entity/bc/{ident}.entity.json'
        d = _load(rel, RP)
        desc = d['minecraft:client_entity']['description']
        for k in extra:
            desc['animations'][k.split('.')[-1]] = k
        animate = desc['scripts']['animate']
        if not any(isinstance(a, dict) and 'ride' in a for a in animate):
            animate.append({'ride': 'q.is_riding'})
        write_json(RP, rel, d)
    # companions can ride brooms too
    rel = 'entities/v3/broom.json'
    d = _load(rel)
    ride = d['minecraft:entity']['components']['minecraft:rideable']
    if 'bc_knight' not in ride['family_types']:
        ride['family_types'].append('bc_knight')
    write_json(BP, rel, d)


def build(ctx: Ctx):
    gen_items(ctx)
    gen_block(ctx)
    gen_loot(ctx)
    rcs = gen_entities(ctx)
    gen_companion_anims(ctx)
    if rcs:
        write_json(RP, 'render_controllers/bc_v5.render_controllers.json', {'format_version': '1.10.0', 'render_controllers': rcs})
