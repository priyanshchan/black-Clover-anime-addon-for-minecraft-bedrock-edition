"""Wave 3 pack content: new mobs & allies, pirate weapons, items, recipes, loot, spawn rules."""
from __future__ import annotations

from . import out
from .data import NS
from .models import grand, mobs, spells as _spells  # noqa: F401
from .out import BP, RP, write_json, write_png
from .packgen import ENTITY_FMT, Ctx, item_json, mob_base, shaped
from .seagen import _client, _entity, _melee_ai, _projectile


def _icon(ctx, key, arr):
    icon = f'bc_{key}'
    ctx.item_textures[icon] = f'textures/items/bc/{key}'
    write_png(RP, f'textures/items/bc/{key}.png', arr)
    return icon


def gen_items(ctx: Ctx):
    ic = grand.wave3_icons()
    usable = {'minecraft:use_modifiers': {'use_duration': 0.6, 'movement_modifier': 1.0}}
    simple = {
        'ancient_page': ('§eAncient Grimoire Page', {'minecraft:max_stack_size': {'value': 16}, 'minecraft:glint': {'value': True}, **usable}),
        'treasure_map': ('§6Treasure Map', {'minecraft:max_stack_size': {'value': 1}, **usable}),
        'lead_shot': ('§7Lead Shot', {'minecraft:max_stack_size': {'value': 64}}),
        'wanted_poster': ('§cWanted Poster', {'minecraft:max_stack_size': {'value': 1}, **usable}),
        'hearty_roast': ('§6Hearty Roast', {
            'minecraft:max_stack_size': {'value': 16},
            'minecraft:food': {'nutrition': 10, 'saturation_modifier': 1.2, 'can_always_eat': False},
            'minecraft:use_modifiers': {'use_duration': 1.8, 'movement_modifier': 0.35},
            'minecraft:use_animation': 'eat',
        }),
    }
    for key, (name, comps) in simple.items():
        write_json(BP, f'items/grand/{key}.json', item_json(f'{NS}:{key}', name, _icon(ctx, key, ic[key]), comps))
    # held pirate weapons with 3D attachables
    ctx.animations['attachables/weapons.animation.json'] = grand.weapon_animations()
    weapons = {
        'cutlass': ('§fCutlass', {'minecraft:damage': {'value': 7}, 'minecraft:hand_equipped': {'value': True},
                                 'minecraft:enchantable': {'slot': 'sword', 'value': 12}, 'minecraft:durability': {'max_durability': 900},
                                 'minecraft:tags': {'tags': ['minecraft:is_sword']}}),
        'flintlock': ('§6Flintlock Pistol', {'minecraft:damage': {'value': 2}, 'minecraft:durability': {'max_durability': 400}}),
        'harpoon': ('§3Harpoon', {'minecraft:damage': {'value': 5}, 'minecraft:hand_equipped': {'value': True}, 'minecraft:durability': {'max_durability': 500}}),
    }
    for kind, (name, comps) in weapons.items():
        write_json(BP, f'items/grand/{kind}.json', item_json(f'{NS}:{kind}', name, _icon(ctx, kind, ic[kind]), {
            'minecraft:max_stack_size': {'value': 1}, **usable, **comps}, category='equipment'))
        g = grand.weapon_geo(kind)
        g.write(out.path(RP, f'models/entity/bc/{kind}.geo.json'), out.path(RP, f'textures/entity/bc/{kind}.png'))
        write_json(RP, f'attachables/{kind}.json', {
            'format_version': '1.10.0',
            'minecraft:attachable': {'description': {
                'identifier': f'{NS}:{kind}',
                'materials': {'default': 'entity_alphatest', 'enchanted': 'entity_alphatest_glint'},
                'textures': {'default': f'textures/entity/bc/{kind}', 'enchanted': 'textures/misc/enchanted_item_glint'},
                'geometry': {'default': f'geometry.bc.{kind}'},
                'animations': {'third_person': f'animation.bc.{kind}.third_person', 'first_person': f'animation.bc.{kind}.first_person'},
                'scripts': {'animate': [{'third_person': '!c.is_first_person'}, {'first_person': 'c.is_first_person'}]},
                'render_controllers': ['controller.render.bc.attachable'],
            }},
        })


def gen_recipes(ctx: Ctx):
    def shapeless(name, ingredients, count=1):
        write_json(BP, f'recipes/grand/{name}.json', {
            'format_version': '1.20.10',
            'minecraft:recipe_shapeless': {
                'description': {'identifier': f'{NS}:{name}'},
                'tags': ['crafting_table'],
                'ingredients': [{'item': i} for i in ingredients],
                'unlock': {'context': 'AlwaysUnlocked'},
                'result': {'item': f'{NS}:{name}', 'count': count},
            },
        })
    shapeless('lead_shot', ['minecraft:iron_nugget', 'minecraft:gunpowder'], 6)
    shapeless('hearty_roast', ['minecraft:cooked_beef', 'minecraft:cooked_porkchop', 'minecraft:bread'], 2)
    write_json(BP, 'recipes/grand/cutlass.json', shaped('cutlass', [' I ', ' I ', 'GS '], {'I': 'minecraft:iron_ingot', 'G': 'minecraft:gold_ingot', 'S': 'minecraft:stick'}))
    write_json(BP, 'recipes/grand/flintlock.json', shaped('flintlock', ['III', 'FPG', ' P '], {
        'I': 'minecraft:iron_ingot', 'F': 'minecraft:flint', 'P': 'minecraft:oak_planks', 'G': 'minecraft:gold_ingot'}))
    write_json(BP, 'recipes/grand/harpoon.json', shaped('harpoon', ['  I', ' S ', 'T  '], {'I': 'minecraft:iron_ingot', 'S': 'minecraft:stick', 'T': 'minecraft:string'}))


def gen_loot(ctx: Ctx):
    def pool(item, lo, hi, chance=1.0):
        entries = [{'type': 'item', 'name': item, 'weight': 100, 'functions': [{'function': 'set_count', 'count': {'min': lo, 'max': hi}}]}]
        if chance < 1:
            entries.append({'type': 'empty', 'weight': int(100 * (1 - chance) / max(chance, 0.01))})
        return {'rolls': 1, 'entries': entries}
    write_json(BP, 'loot_tables/entities/bc_dungeon_golem.json', {'pools': [
        pool(f'{NS}:ancient_page', 2, 4), pool(f'{NS}:mana_crystal', 4, 8), pool('minecraft:diamond', 1, 3), pool(f'{NS}:clover_charm', 1, 1, 0.08)]})
    write_json(BP, 'loot_tables/entities/bc_imp.json', {'pools': [pool(f'{NS}:mana_crystal', 0, 1), pool('minecraft:blaze_powder', 1, 1, 0.3)]})
    write_json(BP, 'loot_tables/entities/bc_tidewatch_sentinel.json', {'pools': [
        pool(f'{NS}:doubloon', 2, 6), pool(f'{NS}:lead_shot', 2, 6, 0.5), pool('minecraft:iron_ingot', 1, 2, 0.3)]})
    write_json(BP, 'loot_tables/entities/bc_tidewatch_commodore.json', {'pools': [
        pool(f'{NS}:doubloon', 25, 45), pool(f'{NS}:treasure_map', 1, 1, 0.5), pool(f'{NS}:flintlock', 1, 1, 0.25), pool('minecraft:emerald', 2, 5)]})


def gen_entities(ctx: Ctx):
    # ---------------------------------------------------------------- projectiles
    g, kind, anims = grand.steel_lance()
    _projectile('steel_lance', 0.5, 3, 'bc:trail_light', lambda: (g, anims), material='entity_emissive_alpha', name='Steel Lance', ctx=ctx)
    _projectile('harpoon_bolt', 0.5, 3, 'bc:trail_dust', grand.harpoon_bolt, gravity=0.02, name='Harpoon', ctx=ctx)
    _projectile('lead_shot', 0.25, 2, 'bc:trail_dust', grand.lead_shot, power=3.0, name='Lead Shot', ctx=ctx)

    # ---------------------------------------------------------------- warp gate (static)
    g, kind, anims = grand.warp_gate()
    g.write(out.path(RP, 'models/entity/bc/warp_gate.geo.json'), out.path(RP, 'textures/entity/bc/warp_gate.png'))
    write_json(BP, 'entities/grand/warp_gate.json', {
        'format_version': ENTITY_FMT,
        'minecraft:entity': {
            'description': {'identifier': f'{NS}:warp_gate', 'is_spawnable': False, 'is_summonable': True},
            'component_groups': {'bc:expire': {'minecraft:instant_despawn': {}}},
            'components': {
                'minecraft:collision_box': {'width': 0.2, 'height': 0.2},
                'minecraft:type_family': {'family': ['bc_spell', 'inanimate']},
                'minecraft:physics': {'has_gravity': False, 'has_collision': False},
                'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': False},
                'minecraft:damage_sensor': {'triggers': [{'cause': 'all', 'deals_damage': 'no'}]},
                'minecraft:health': {'value': 1, 'max': 1},
                'minecraft:timer': {'looping': False, 'time': 22, 'randomInterval': False, 'time_down_event': {'event': 'bc:expire', 'target': 'self'}},
            },
            'events': {'bc:expire': {'add': {'component_groups': ['bc:expire']}}},
        },
    })
    ctx.animations['entity/grand.animation.json'] = dict(anims)
    _client('warp_gate', 'geometry.bc.warp_gate', 'textures/entity/bc/warp_gate', 'entity_emissive_alpha',
            {'spin': 'animation.bc.warp_gate.spin'}, ['spin'])
    ctx.lang.append(f'entity.{NS}:warp_gate.name=Warp Gate')

    # ---------------------------------------------------------------- allies: earth golem & mirror clone
    for ident, health, dmg, life, geo_fn, anim_prefix, material, label in (
        ('earth_golem', 80, 9, 40, lambda: grand.golem_geo('earth_golem'), 'earth_golem', 'entity_emissive_alpha', 'Earth Golem'),
        ('mirror_clone', 24, 5, 22, lambda: mobs.disciple_geo('mirror'), 'dark_disciple', 'entity_emissive_alpha', 'Mirror Image'),
    ):
        comps = mob_base(ident, ['bc_shade', 'mob'], health, (0.9, 2.1) if ident == 'earth_golem' else (0.6, 1.95), 0.28,
                         'loot_tables/entities/bc_empty.json', 0)
        comps.update(_melee_ai(dmg, targets=('monster', 'bc_pirate')))
        comps['minecraft:timer'] = {'looping': False, 'time': life, 'randomInterval': False, 'time_down_event': {'event': 'bc:expire', 'target': 'self'}}
        comps['minecraft:damage_sensor'] = {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'drowning', 'deals_damage': 'no'}]}
        comps['minecraft:knockback_resistance'] = {'value': 0.8 if ident == 'earth_golem' else 0.0}
        ent = _entity(ident, comps)
        ent['minecraft:entity']['component_groups'] = {'bc:expire': {'minecraft:instant_despawn': {}}}
        ent['minecraft:entity']['events'] = {'bc:expire': {'add': {'component_groups': ['bc:expire']}}}
        write_json(BP, f'entities/grand/{ident}.json', ent)
        g = geo_fn()
        g.write(out.path(RP, f'models/entity/bc/{ident}.geo.json'), out.path(RP, f'textures/entity/bc/{ident}.png'))
        if ident == 'earth_golem':
            ga = grand.golem_animations('earth_golem')
            ctx.animations['entity/earth_golem.animation.json'] = ga
        _client(ident, f'geometry.bc.{ident}', f'textures/entity/bc/{ident}', material,
                {'idle': f'animation.bc.{anim_prefix}.idle', 'walk': f'animation.bc.{anim_prefix}.walk', 'look': f'animation.bc.{anim_prefix}.look_at_target'},
                ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look'])
        ctx.lang.append(f'entity.{NS}:{ident}.name={label}')

    # ---------------------------------------------------------------- Dungeon Golem (mini-boss)
    comps = mob_base('dungeon_golem', ['bc_magic', 'bc_golem', 'monster', 'mob'], 220, (1.4, 3.0), 0.22, 'loot_tables/entities/bc_dungeon_golem.json', 120)
    comps.update(_melee_ai(14, targets=('player', 'irongolem', 'bc_shade')))
    comps['minecraft:boss'] = {'should_darken_sky': False, 'hud_range': 32}
    comps['minecraft:knockback_resistance'] = {'value': 1.0}
    comps['minecraft:persistent'] = {}
    comps.pop('minecraft:despawn', None)
    comps['minecraft:damage_sensor'] = {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'projectile', 'damage_multiplier': 0.5}]}
    write_json(BP, 'entities/grand/dungeon_golem.json', _entity('dungeon_golem', comps))
    g = grand.golem_geo('dungeon_golem')
    g.write(out.path(RP, 'models/entity/bc/dungeon_golem.geo.json'), out.path(RP, 'textures/entity/bc/dungeon_golem.png'))
    ctx.animations['entity/dungeon_golem.animation.json'] = grand.golem_animations('dungeon_golem')
    _client('dungeon_golem', 'geometry.bc.dungeon_golem', 'textures/entity/bc/dungeon_golem', 'entity_emissive_alpha',
            {'idle': 'animation.bc.dungeon_golem.idle', 'walk': 'animation.bc.dungeon_golem.walk', 'look': 'animation.bc.dungeon_golem.look_at_target'},
            ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look'], egg={'base_color': '#202028', 'overlay_color': '#5ad8ff'}, scale='1.45')
    ctx.lang += [f'entity.{NS}:dungeon_golem.name=§bDungeon Guardian', f'item.spawn_egg.entity.{NS}:dungeon_golem.name=Dungeon Guardian Spawn Egg']

    # ---------------------------------------------------------------- Imp (low-rank devil)
    comps = mob_base('imp', ['bc_magic', 'bc_devil', 'monster', 'mob'], 14, (0.5, 0.8), 0.32, 'loot_tables/entities/bc_imp.json', 6)
    comps.update({
        'minecraft:can_fly': {},
        'minecraft:flying_speed': {'value': 0.3},
        'minecraft:navigation.hover': {'can_path_over_water': True, 'can_sink': False, 'can_pass_doors': True, 'can_path_from_air': True, 'avoid_water': True},
        'minecraft:movement.hover': {},
        'minecraft:physics': {'has_gravity': False},
        'minecraft:attack': {'damage': 3},
        'minecraft:despawn': {'despawn_from_distance': {}},
        'minecraft:fire_immune': True,
        'minecraft:behavior.float': {'priority': 0},
        'minecraft:behavior.hurt_by_target': {'priority': 1},
        'minecraft:behavior.melee_box_attack': {'priority': 2, 'speed_multiplier': 1.4, 'track_target': True},
        'minecraft:behavior.nearest_attackable_target': {'priority': 3, 'must_see': False, 'reselect_targets': True,
                                                          'entity_types': [{'filters': {'test': 'is_family', 'subject': 'other', 'value': 'player'}, 'max_dist': 24}]},
        'minecraft:behavior.random_hover': {'priority': 6, 'xz_dist': 8, 'y_dist': 4, 'y_offset': -1, 'interval': 1, 'hover_height': [1, 4]},
        'minecraft:damage_sensor': {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}]},
    })
    write_json(BP, 'entities/grand/imp.json', _entity('imp', comps, spawnable=True))
    g = grand.imp_geo()
    g.write(out.path(RP, 'models/entity/bc/imp.geo.json'), out.path(RP, 'textures/entity/bc/imp.png'))
    ctx.animations['entity/imp.animation.json'] = grand.imp_animations()
    _client('imp', 'geometry.bc.imp', 'textures/entity/bc/imp', 'entity_emissive_alpha',
            {'fly': 'animation.bc.imp.fly', 'look': 'animation.bc.imp.look_at_target'}, ['fly', 'look'],
            egg={'base_color': '#6a1018', 'overlay_color': '#ffd23a'})
    ctx.lang += [f'entity.{NS}:imp.name=Imp', f'item.spawn_egg.entity.{NS}:imp.name=Imp Spawn Egg']
    write_json(BP, 'spawn_rules/imp.json', {
        'format_version': '1.8.0',
        'minecraft:spawn_rules': {
            'description': {'identifier': f'{NS}:imp', 'population_control': 'monster'},
            'conditions': [{
                'minecraft:spawns_on_surface': {},
                'minecraft:brightness_filter': {'min': 0, 'max': 7, 'adjust_for_weather': True},
                'minecraft:difficulty_filter': {'min': 'easy', 'max': 'hard'},
                'minecraft:weight': {'default': 4},
                'minecraft:herd': {'min_size': 2, 'max_size': 3},
                'minecraft:density_limit': {'surface': 4},
                'minecraft:biome_filter': {'test': 'has_biome_tag', 'value': 'monster'},
            }],
        },
    })

    # ---------------------------------------------------------------- Tidewatch navy (original faction)
    for kind, health, dmg, label, egg in (
        ('tidewatch_sentinel', 34, 5, 'Tidewatch Sentinel', ('#eceff4', '#23345f')),
        ('tidewatch_commodore', 140, 10, '§9Tidewatch Commodore', ('#23345f', '#f0c24a')),
    ):
        comps = mob_base(kind, ['bc_navy', 'monster', 'mob'], health, (0.6, 1.95), 0.3, f'loot_tables/entities/bc_{kind}.json', 30 if 'commodore' in kind else 10)
        comps.update(_melee_ai(dmg, targets=('player', 'bc_pirate')))
        comps['minecraft:persistent'] = {}
        comps.pop('minecraft:despawn', None)
        if 'commodore' in kind:
            comps['minecraft:knockback_resistance'] = {'value': 0.6}
            comps['minecraft:boss'] = {'should_darken_sky': False, 'hud_range': 32}
        write_json(BP, f'entities/grand/{kind}.json', _entity(kind, comps))
        g = grand.navy_geo(kind)
        g.write(out.path(RP, f'models/entity/bc/{kind}.geo.json'), out.path(RP, f'textures/entity/bc/{kind}.png'))
        ctx.animations[f'entity/{kind}.animation.json'] = grand.navy_animations(kind)
        _client(kind, f'geometry.bc.{kind}', f'textures/entity/bc/{kind}', 'entity_alphatest',
                {'idle': f'animation.bc.{kind}.idle', 'walk': f'animation.bc.{kind}.walk', 'look': f'animation.bc.{kind}.look_at_target'},
                ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look'], egg={'base_color': egg[0], 'overlay_color': egg[1]})
        ctx.lang += [f'entity.{NS}:{kind}.name={label}', f'item.spawn_egg.entity.{NS}:{kind}.name={label} Spawn Egg']


def build(ctx: Ctx):
    gen_items(ctx)
    gen_recipes(ctx)
    gen_loot(ctx)
    gen_entities(ctx)
