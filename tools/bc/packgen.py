"""Generates every behavior/resource pack JSON + model + texture."""
from __future__ import annotations

from . import out, tex
from .data import ATTR_ORDER, ATTRIBUTES, NS, ROBES, SPELLS, SWORDS
from .models import items, mobs, spells, world
from .out import BP, RP, write_json, write_png, write_text

VERSION = [1, 3, 0]  # v1.3.0 - bump on every release so Minecraft replaces the installed packs
MIN_ENGINE = [1, 21, 90]
ITEM_FMT = '1.21.60'
ENTITY_FMT = '1.21.0'

# --------------------------------------------------------------------------------------
# spell entity specifications
# --------------------------------------------------------------------------------------
SPELL_ENTITIES = {
    # name: kind, collision size, trail particle, lifetime (s), display name
    'wind_blade': dict(kind='projectile', box=0.8, trail='bc:trail_wind', life=2.5, name='Gale Blade'),
    'fireball': dict(kind='projectile', box=0.5, trail='bc:trail_flame', life=4, name='Flame Bullet'),
    'flame_lion': dict(kind='projectile', box=1.2, trail='bc:trail_flame_big', life=5, name='Inferno Lion'),
    'water_orb': dict(kind='projectile', box=0.45, trail='bc:trail_water', life=3, name='Water Bullet'),
    'water_dragon': dict(kind='projectile', box=1.1, trail='bc:trail_water_big', life=4, name='Sea Dragon'),
    'thunder_spear': dict(kind='projectile', box=0.5, trail='bc:trail_lightning', life=3, name='Thunder Spear'),
    'light_sword': dict(kind='projectile', box=0.5, trail='bc:trail_light', life=4, name='Sword of Light'),
    'dark_crescent': dict(kind='projectile', box=1.2, trail='bc:trail_dark', life=3, name='Dark Crescent'),
    'ice_spear': dict(kind='projectile', box=0.5, trail='bc:trail_ice', life=3, name='Ice Spear'),
    'anti_magic_slash': dict(kind='projectile', box=1.4, trail='bc:trail_anti', life=2.5, name='Black Meteorite'),
    'dark_bolt': dict(kind='mob_projectile', box=0.4, trail='bc:trail_dark', life=6, name='Dark Bolt', damage=5, power=1.1),
    'devil_orb': dict(kind='mob_projectile', box=0.7, trail='bc:trail_devil', life=7, name='Devil Orb', damage=9, power=0.9),
    'tornado': dict(kind='static', box=1.0, trail='bc:tornado_fx', life=7, name='Tempest Tornado'),
    'black_hole': dict(kind='static', box=0.5, trail='bc:black_hole_fx', life=8, name='Abyssal Hole'),
    'ice_prison': dict(kind='static', box=0.5, trail='bc:snow_fall', life=6, name='Frost Prison'),
}


# ======================================================================================
# helpers
# ======================================================================================
def manifest_bp():
    return {
        'format_version': 2,
        'header': {
            'name': 'Black Clover: Grimoire Awakening §7(Behavior)',
            'description': 'v1.3.0 - Devil Union: devils walk in borrowed bodies, changing as their union deepens; make a pact with a devil of your own and join with it at 50% and 100% union; free possessed knights; face the Crowned Vessel. Plus wyverns to raise and ride, the neighbouring kingdoms, the Royal Capital, named regions, landmarks, random loot, a living world, 40 grimoires, 34 Abyss Fruits and companions. Unofficial fan addon.',
            'uuid': out.uid('bp-header'),
            'version': VERSION,
            'min_engine_version': MIN_ENGINE,
        },
        'modules': [
            {'type': 'data', 'uuid': out.uid('bp-data'), 'version': VERSION},
            {'type': 'script', 'language': 'javascript', 'uuid': out.uid('bp-script'), 'version': VERSION, 'entry': 'scripts/main.js'},
        ],
        'dependencies': [
            {'uuid': out.uid('rp-header'), 'version': VERSION},
            {'module_name': '@minecraft/server', 'version': '2.0.0'},
            {'module_name': '@minecraft/server-ui', 'version': '2.0.0'},
        ],
        'metadata': {'authors': ['sub0pc'], 'license': 'MIT', 'product_type': 'addon'},
    }


def manifest_rp():
    return {
        'format_version': 2,
        'header': {
            'name': 'Black Clover: Grimoire Awakening §7(Resources)',
            'description': 'v1.3.0 - devil hosts and their union stages, the Crowned Vessel, Pact Sigils and union horns and wings; tamed and saddled wyverns, wyvern eggs, kingdom soldiers, the Royal Capital; Mana Wyverns, the Spire Warden, mimics, sprites, relics; HD spell effects, 3D grimoires, armour, companions, bosses, particles and sounds. Unofficial fan addon.',
            'uuid': out.uid('rp-header'),
            'version': VERSION,
            'min_engine_version': MIN_ENGINE,
        },
        'modules': [{'type': 'resources', 'uuid': out.uid('rp-res'), 'version': VERSION}],
        'dependencies': [{'uuid': out.uid('bp-header'), 'version': VERSION}],
        'metadata': {'authors': ['sub0pc'], 'license': 'MIT', 'product_type': 'addon'},
    }


class Ctx:
    def __init__(self):
        self.item_textures = {}
        self.terrain_textures = {}
        self.animations = {}          # file -> {anim name: data}
        self.lang = []
        self.geo_files = []


# ======================================================================================
# items
# ======================================================================================
def item_json(ident, name, icon, comps=None, category='items', group=None):
    c = {
        'minecraft:icon': {'textures': {'default': icon}},
        'minecraft:display_name': {'value': name},
    }
    c.update(comps or {})
    desc = {'identifier': ident, 'menu_category': {'category': category}}
    if group:
        desc['menu_category']['group'] = group
    return {'format_version': ITEM_FMT, 'minecraft:item': {'description': desc, 'components': c}}


def gen_grimoires(ctx: Ctx):
    anims = items.grimoire_animations()
    ctx.animations['attachables/grimoire.animation.json'] = anims
    for attr in ATTR_ORDER:
        a = ATTRIBUTES[attr]
        ident = f'{NS}:grimoire_{attr}'
        leaves = {3: 'Three', 4: 'Four', 5: 'Five'}[a['leaves']]
        name = f"{a['mc']}{a['name']} Grimoire §7({leaves}-Leaf)"
        icon = f'bc_grimoire_{attr}'
        ctx.item_textures[icon] = f'textures/items/bc/grimoire_{attr}'
        write_png(RP, f'textures/items/bc/grimoire_{attr}.png', items.grimoire_icon(attr))
        write_json(BP, f'items/grimoire_{attr}.json', item_json(ident, name, icon, {
            'minecraft:max_stack_size': {'value': 1},
            'minecraft:use_modifiers': {'use_duration': 0.6, 'movement_modifier': 1.0},
            'minecraft:glint': {'value': attr == 'anti'},
            'minecraft:can_destroy_in_creative': {'value': False},
            'minecraft:tags': {'tags': ['bc:grimoire', f'bc:attr_{attr}']},
        }))
        g = items.grimoire_geo(attr)
        g.write(out.path(RP, f'models/entity/bc/grimoire_{attr}.geo.json'), out.path(RP, f'textures/entity/bc/grimoire_{attr}.png'))
        write_json(RP, f'attachables/grimoire_{attr}.json', {
            'format_version': '1.10.0',
            'minecraft:attachable': {'description': {
                'identifier': ident,
                'materials': {'default': 'entity_emissive_alpha'},
                'textures': {'default': f'textures/entity/bc/grimoire_{attr}'},
                'geometry': {'default': f'geometry.bc.grimoire_{attr}'},
                'animations': {
                    'third_person': 'animation.bc.grimoire.third_person',
                    'first_person': 'animation.bc.grimoire.first_person',
                    'page_flip': 'animation.bc.grimoire.page_flip',
                },
                'scripts': {'animate': [{'third_person': '!c.is_first_person'}, {'first_person': 'c.is_first_person'}, 'page_flip']},
                'render_controllers': ['controller.render.bc.attachable'],
            }},
        })


def gen_swords(ctx: Ctx):
    ctx.animations['attachables/swords.animation.json'] = items.sword_animations()
    for kind, s in SWORDS.items():
        ident = f'{NS}:{kind}'
        icon = f'bc_{kind}'
        ctx.item_textures[icon] = f'textures/items/bc/{kind}'
        write_png(RP, f'textures/items/bc/{kind}.png', items.sword_icon(kind))
        write_json(BP, f'items/{kind}.json', item_json(ident, f"§8{s['name']}", icon, {
            'minecraft:max_stack_size': {'value': 1},
            'minecraft:hand_equipped': {'value': True},
            'minecraft:damage': {'value': s['damage']},
            'minecraft:enchantable': {'slot': 'sword', 'value': 14},
            'minecraft:can_destroy_in_creative': {'value': False},
            'minecraft:use_modifiers': {'use_duration': 0.6, 'movement_modifier': 1.0},
            'minecraft:tags': {'tags': ['minecraft:is_sword', 'bc:demon_sword']},
            'minecraft:digger': {'use_efficiency': True, 'destroy_speeds': [{'block': 'minecraft:web', 'speed': 15}]},
        }, category='equipment', group='minecraft:itemGroup.name.sword'))
        g = items.sword_geo(kind)
        g.write(out.path(RP, f'models/entity/bc/{kind}.geo.json'), out.path(RP, f'textures/entity/bc/{kind}.png'))
        write_json(RP, f'attachables/{kind}.json', {
            'format_version': '1.10.0',
            'minecraft:attachable': {'description': {
                'identifier': ident,
                'materials': {'default': 'entity_emissive_alpha', 'enchanted': 'entity_alphatest_glint'},
                'textures': {'default': f'textures/entity/bc/{kind}', 'enchanted': 'textures/misc/enchanted_item_glint'},
                'geometry': {'default': f'geometry.bc.{kind}'},
                'animations': {
                    'third_person': f'animation.bc.{kind}.third_person',
                    'first_person': f'animation.bc.{kind}.first_person',
                },
                'scripts': {'animate': [{'third_person': '!c.is_first_person'}, {'first_person': 'c.is_first_person'}]},
                'render_controllers': ['controller.render.bc.attachable'],
            }},
        })


def gen_robes(ctx: Ctx):
    ctx.animations['attachables/robes.animation.json'] = items.robe_animations()
    for rid, r in ROBES.items():
        ident = f'{NS}:{rid}'
        icon = f'bc_{rid}'
        ctx.item_textures[icon] = f'textures/items/bc/{rid}'
        write_png(RP, f'textures/items/bc/{rid}.png', items.robe_icon(rid))
        write_json(BP, f'items/{rid}.json', item_json(ident, f"§6{r['name']}", icon, {
            'minecraft:max_stack_size': {'value': 1},
            'minecraft:wearable': {'slot': 'slot.armor.chest', 'protection': 6},
            'minecraft:durability': {'max_durability': 560},
            'minecraft:enchantable': {'slot': 'armor_torso', 'value': 14},
            'minecraft:repairable': {'repair_items': [{'items': [f'{NS}:mana_crystal'], 'repair_amount': 140}]},
            'minecraft:tags': {'tags': ['minecraft:is_armor', 'bc:robe']},
        }, category='equipment', group='minecraft:itemGroup.name.chestplate'))
        g = items.robe_geo(rid)
        g.write(out.path(RP, f'models/entity/bc/{rid}.geo.json'), out.path(RP, f'textures/entity/bc/{rid}.png'))
        write_json(RP, f'attachables/{rid}.json', {
            'format_version': '1.10.0',
            'minecraft:attachable': {'description': {
                'identifier': ident,
                'materials': {'default': 'entity_alphatest', 'enchanted': 'entity_alphatest_glint'},
                'textures': {'default': f'textures/entity/bc/{rid}', 'enchanted': 'textures/misc/enchanted_item_glint'},
                'geometry': {'default': f'geometry.bc.{rid}'},
                'animations': {'wear': 'animation.bc.robe.wear'},
                'scripts': {'parent_setup': 'v.chest_layer_visible = 0.0;', 'animate': ['wear']},
                'render_controllers': ['controller.render.bc.attachable'],
            }},
        })


def gen_misc_items(ctx: Ctx):
    from .icons import misc_icons
    icons = misc_icons()
    specs = {
        'mana_crystal': ('§bMana Crystal', {'minecraft:max_stack_size': {'value': 64},
                                            'minecraft:use_modifiers': {'use_duration': 0.6, 'movement_modifier': 1.0}}),
        'devil_heart': ('§4Devil Heart', {'minecraft:max_stack_size': {'value': 16}, 'minecraft:glint': {'value': True}}),
        'clover_charm': ('§aWishing Clover Charm', {'minecraft:max_stack_size': {'value': 1}, 'minecraft:glint': {'value': True},
                                                    'minecraft:use_modifiers': {'use_duration': 0.6, 'movement_modifier': 1.0}}),
        'devil_contract': ('§cDevil Summoning Contract', {'minecraft:max_stack_size': {'value': 1},
                                                          'minecraft:use_modifiers': {'use_duration': 0.6, 'movement_modifier': 1.0}}),
        'handbook': ("§eMagic Knight's Handbook", {'minecraft:max_stack_size': {'value': 1},
                                                   'minecraft:use_modifiers': {'use_duration': 0.6, 'movement_modifier': 1.0}}),
    }
    for key, (name, comps) in specs.items():
        icon = f'bc_{key}'
        ctx.item_textures[icon] = f'textures/items/bc/{key}'
        write_png(RP, f'textures/items/bc/{key}.png', icons[key])
        write_json(BP, f'items/{key}.json', item_json(f'{NS}:{key}', name, icon, comps))


# ======================================================================================
# block
# ======================================================================================
def gen_altar(ctx: Ctx):
    g = world.altar_geo()
    g.paint()
    a = g.atlas
    a[..., 3] = (a[..., 3] > 0) * 255.0
    write_json(RP, 'models/blocks/bc/grimoire_altar.geo.json', g.to_json())
    write_png(RP, 'textures/blocks/bc/grimoire_altar.png', a)
    ctx.terrain_textures['bc_grimoire_altar'] = 'textures/blocks/bc/grimoire_altar'
    dirs = {'north': 0, 'east': -90, 'south': 180, 'west': 90}
    write_json(BP, 'blocks/grimoire_altar.json', {
        'format_version': '1.21.90',
        'minecraft:block': {
            'description': {
                'identifier': f'{NS}:grimoire_altar',
                'menu_category': {'category': 'items'},
                'traits': {'minecraft:placement_direction': {'enabled_states': ['minecraft:cardinal_direction'], 'y_rotation_offset': 180}},
            },
            'components': {
                'minecraft:geometry': 'geometry.bc.grimoire_altar',
                'minecraft:material_instances': {
                    '*': {'texture': 'bc_grimoire_altar', 'render_method': 'alpha_test'},
                    'crystal': {'texture': 'bc_grimoire_altar', 'render_method': 'alpha_test'},
                },
                'minecraft:collision_box': {'origin': [-8, 0, -8], 'size': [16, 13, 16]},
                'minecraft:selection_box': {'origin': [-8, 0, -8], 'size': [16, 16, 16]},
                'minecraft:destructible_by_mining': {'seconds_to_destroy': 3.0},
                'minecraft:destructible_by_explosion': {'explosion_resistance': 1200},
                'minecraft:light_emission': 9,
                'minecraft:light_dampening': 0,
                'minecraft:map_color': '#2b2b35',
                'minecraft:display_name': 'tile.bc:grimoire_altar.name',
                'minecraft:tick': {'interval_range': [10, 20], 'looping': True},
                'bc:altar_logic': {},
            },
            'permutations': [
                {'condition': f"q.block_state('minecraft:cardinal_direction') == '{d}'",
                 'components': {'minecraft:transformation': {'rotation': [0, r, 0]}}}
                for d, r in dirs.items()
            ],
        },
    })
    write_json(BP, 'recipes/grimoire_altar.json', shaped('grimoire_altar', ['MBM', 'GLG', 'SSS'], {
        'M': f'{NS}:mana_crystal', 'B': 'minecraft:book', 'G': 'minecraft:gold_ingot', 'L': 'minecraft:lectern', 'S': 'minecraft:stone_bricks'}))


# ======================================================================================
# recipes & loot
# ======================================================================================
def shaped(result, pattern, key, count=1):
    return {
        'format_version': '1.20.10',
        'minecraft:recipe_shaped': {
            'description': {'identifier': f'{NS}:{result}'},
            'tags': ['crafting_table'],
            'pattern': pattern,
            'key': {k: {'item': v} for k, v in key.items()},
            'unlock': {'context': 'AlwaysUnlocked'},
            'result': {'item': f'{NS}:{result}', 'count': count},
        },
    }


def gen_recipes(ctx: Ctx):
    write_json(BP, 'recipes/mana_crystal.json', {
        'format_version': '1.20.10',
        'minecraft:recipe_shapeless': {
            'description': {'identifier': f'{NS}:mana_crystal'},
            'tags': ['crafting_table'],
            'ingredients': [{'item': 'minecraft:amethyst_shard'}, {'item': 'minecraft:lapis_lazuli'}, {'item': 'minecraft:glowstone_dust'}],
            'unlock': {'context': 'AlwaysUnlocked'},
            'result': {'item': f'{NS}:mana_crystal', 'count': 2},
        },
    })
    wool = {'black_bull_robe': ('minecraft:black_wool', 'minecraft:gold_nugget'),
            'golden_dawn_robe': ('minecraft:white_wool', 'minecraft:gold_ingot'),
            'crimson_lion_robe': ('minecraft:red_wool', 'minecraft:blaze_powder')}
    for rid, (w, extra) in wool.items():
        write_json(BP, f'recipes/{rid}.json', shaped(rid, ['WXW', 'WMW', 'WWW'], {'W': w, 'X': extra, 'M': f'{NS}:mana_crystal'}))
    write_json(BP, 'recipes/devil_contract.json', shaped('devil_contract', ['CMC', 'MBM', 'CMC'], {
        'C': 'minecraft:crying_obsidian', 'M': f'{NS}:mana_crystal', 'B': 'minecraft:book'}))
    write_json(BP, 'recipes/clover_charm.json', shaped('clover_charm', ['EME', 'MHM', 'EME'], {
        'E': 'minecraft:emerald', 'M': f'{NS}:mana_crystal', 'H': f'{NS}:devil_heart'}))
    write_json(BP, 'recipes/handbook.json', {
        'format_version': '1.20.10',
        'minecraft:recipe_shapeless': {
            'description': {'identifier': f'{NS}:handbook'},
            'tags': ['crafting_table'],
            'ingredients': [{'item': 'minecraft:book'}, {'item': f'{NS}:mana_crystal'}],
            'unlock': {'context': 'AlwaysUnlocked'},
            'result': {'item': f'{NS}:handbook'},
        },
    })


def gen_loot(ctx: Ctx):
    write_json(BP, 'loot_tables/entities/bc_dark_disciple.json', {'pools': [
        {'rolls': 1, 'entries': [{'type': 'item', 'name': f'{NS}:mana_crystal', 'weight': 1,
                                  'functions': [{'function': 'set_count', 'count': {'min': 1, 'max': 3}},
                                                {'function': 'looting_enchant', 'count': {'min': 0, 'max': 1}}]}]},
        {'rolls': 1, 'entries': [{'type': 'item', 'name': 'minecraft:book', 'weight': 1}, {'type': 'empty', 'weight': 6}]},
        {'rolls': 1, 'entries': [{'type': 'item', 'name': 'minecraft:amethyst_shard', 'weight': 2,
                                  'functions': [{'function': 'set_count', 'count': {'min': 1, 'max': 2}}]}, {'type': 'empty', 'weight': 3}]},
    ]})
    write_json(BP, 'loot_tables/entities/bc_devil.json', {'pools': [
        {'rolls': 1, 'entries': [{'type': 'item', 'name': f'{NS}:devil_heart', 'weight': 1}]},
        {'rolls': 1, 'entries': [{'type': 'item', 'name': f'{NS}:mana_crystal', 'weight': 1,
                                  'functions': [{'function': 'set_count', 'count': {'min': 8, 'max': 14}}]}]},
        {'rolls': 1, 'entries': [{'type': 'item', 'name': 'minecraft:diamond', 'weight': 1,
                                  'functions': [{'function': 'set_count', 'count': {'min': 2, 'max': 4}}]}]},
        {'rolls': 1, 'entries': [{'type': 'item', 'name': 'minecraft:netherite_scrap', 'weight': 1}, {'type': 'empty', 'weight': 1}]},
    ]})


# ======================================================================================
# entities
# ======================================================================================
def gen_spell_entities(ctx: Ctx):
    anim_file = {}
    for name, spec in SPELL_ENTITIES.items():
        g, kind, anims = spells.ALL[name]()
        anim_file.update(anims)
        g.write(out.path(RP, f'models/entity/bc/{name}.geo.json'), out.path(RP, f'textures/entity/bc/{name}.png'))
        comps = {
            'minecraft:collision_box': {'width': spec['box'], 'height': spec['box']},
            'minecraft:type_family': {'family': ['bc_spell', 'inanimate']},
            'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': False},
            'minecraft:timer': {'looping': False, 'time': spec['life'], 'randomInterval': False,
                                'time_down_event': {'event': 'bc:expire', 'target': 'self'}},
            'minecraft:conditional_bandwidth_optimization': {'default_values': {'max_optimized_distance': 96.0, 'max_dropped_ticks': 4, 'use_motion_prediction_hints': True}},
        }
        if spec['kind'] in ('projectile', 'mob_projectile'):
            on_hit = {'remove_on_hit': {}}
            if spec['kind'] == 'mob_projectile':
                on_hit['impact_damage'] = {'damage': spec['damage'], 'knockback': True, 'semi_random_diff_damage': False}
            comps['minecraft:projectile'] = {
                'on_hit': on_hit,
                'power': spec.get('power', 1.6),
                'gravity': 0.0,
                'inertia': 1.0,
                'liquid_inertia': 1.0,
                'uncertainty_base': 2.0 if spec['kind'] == 'mob_projectile' else 0.0,
                'uncertainty_multiplier': 0.0,
                'anchor': 1,
                'offset': [0, -0.1, 0],
                'reflect_on_hurt': spec['kind'] == 'mob_projectile',
            }
            comps['minecraft:physics'] = {}
        else:
            comps['minecraft:physics'] = {'has_gravity': False, 'has_collision': False}
            comps['minecraft:damage_sensor'] = {'triggers': [{'cause': 'all', 'deals_damage': 'no'}]}
            comps['minecraft:health'] = {'value': 1, 'max': 1}
            comps['minecraft:knockback_resistance'] = {'value': 1.0}
        write_json(BP, f'entities/spells/{name}.json', {
            'format_version': ENTITY_FMT,
            'minecraft:entity': {
                'description': {'identifier': f'{NS}:{name}', 'is_spawnable': False, 'is_summonable': True},
                'component_groups': {'bc:expire': {'minecraft:instant_despawn': {}}},
                'components': comps,
                'events': {'bc:expire': {'add': {'component_groups': ['bc:expire']}}},
            },
        })
        anim_ids = {k.split('.')[-1]: k for k in anims}
        anim_ids['trail'] = 'animation.bc.spell.trail'
        write_json(RP, f'entity/bc/{name}.entity.json', {
            'format_version': '1.10.0',
            'minecraft:client_entity': {'description': {
                'identifier': f'{NS}:{name}',
                'materials': {'default': 'entity_alphablend' if kind == 'blend' else 'entity_emissive_alpha'},
                'textures': {'default': f'textures/entity/bc/{name}'},
                'geometry': {'default': f'geometry.bc.{name}'},
                'animations': anim_ids,
                'particle_effects': {'trail': spec['trail']},
                'scripts': {'animate': list(anim_ids.keys())},
                'render_controllers': ['controller.render.bc.default'],
            }},
        })
        ctx.lang.append(f'entity.{NS}:{name}.name={spec["name"]}')
    anim_file['animation.bc.spell.trail'] = {
        'loop': 'hold_on_last_frame', 'animation_length': 0.05,
        'particle_effects': {'0.0': {'effect': 'trail'}},
    }
    ctx.animations['entity/spells.animation.json'] = anim_file


def mob_base(ident, family, health, box, speed, loot, xp):
    return {
        'minecraft:type_family': {'family': family},
        'minecraft:health': {'value': health, 'max': health},
        'minecraft:collision_box': {'width': box[0], 'height': box[1]},
        'minecraft:movement': {'value': speed},
        'minecraft:physics': {},
        'minecraft:pushable': {'is_pushable': True, 'is_pushable_by_piston': True},
        'minecraft:breathable': {'total_supply': 15, 'suffocate_time': 0},
        'minecraft:nameable': {},
        'minecraft:loot': {'table': loot},
        'minecraft:experience_reward': {'on_death': f'q.last_hit_by_player ? {xp} : 0'},
        'minecraft:follow_range': {'value': 40, 'max': 40},
        'minecraft:conditional_bandwidth_optimization': {},
        'minecraft:hurt_on_condition': {'damage_conditions': [{'filters': {'test': 'in_lava', 'subject': 'self'}, 'cause': 'lava', 'damage_per_tick': 4}]},
    }


def gen_mobs(ctx: Ctx):
    # ---------------------------------------------------------------- Dark Disciple
    comps = mob_base('dark_disciple', ['bc_magic', 'bc_disciple', 'monster', 'mob'], 40, (0.6, 1.95), 0.27,
                     'loot_tables/entities/bc_dark_disciple.json', 12)
    comps.update({
        'minecraft:navigation.walk': {'can_path_over_water': True, 'avoid_water': True, 'can_open_doors': True, 'avoid_damage_blocks': True},
        'minecraft:movement.basic': {},
        'minecraft:jump.static': {},
        'minecraft:can_climb': {},
        'minecraft:attack': {'damage': 4},
        'minecraft:shooter': {'def': f'{NS}:dark_bolt'},
        'minecraft:despawn': {'despawn_from_distance': {}},
        'minecraft:behavior.float': {'priority': 0},
        'minecraft:behavior.hurt_by_target': {'priority': 1},
        'minecraft:behavior.ranged_attack': {'priority': 2, 'attack_interval_min': 2.2, 'attack_interval_max': 3.6, 'attack_radius': 16.0, 'speed_multiplier': 1.0},
        'minecraft:behavior.nearest_attackable_target': {
            'priority': 2, 'must_see': True, 'reselect_targets': True,
            'entity_types': [
                {'filters': {'any_of': [{'test': 'is_family', 'subject': 'other', 'value': 'player'},
                                        {'test': 'is_family', 'subject': 'other', 'value': 'irongolem'},
                                        {'test': 'is_family', 'subject': 'other', 'value': 'villager'}]}, 'max_dist': 24}]},
        'minecraft:behavior.random_stroll': {'priority': 6, 'speed_multiplier': 0.8},
        'minecraft:behavior.look_at_player': {'priority': 7, 'look_distance': 10, 'probability': 0.03},
        'minecraft:behavior.random_look_around': {'priority': 8},
        'minecraft:damage_sensor': {'triggers': [{'cause': 'fall', 'damage_multiplier': 0.5}]},
    })
    write_json(BP, 'entities/dark_disciple.json', {
        'format_version': ENTITY_FMT,
        'minecraft:entity': {
            'description': {'identifier': f'{NS}:dark_disciple', 'is_spawnable': True, 'is_summonable': True},
            'components': comps,
            'events': {},
        },
    })
    write_json(BP, 'spawn_rules/dark_disciple.json', {
        'format_version': '1.8.0',
        'minecraft:spawn_rules': {
            'description': {'identifier': f'{NS}:dark_disciple', 'population_control': 'monster'},
            'conditions': [{
                'minecraft:spawns_on_surface': {},
                'minecraft:brightness_filter': {'min': 0, 'max': 7, 'adjust_for_weather': True},
                'minecraft:difficulty_filter': {'min': 'easy', 'max': 'hard'},
                'minecraft:weight': {'default': 6},
                'minecraft:herd': {'min_size': 1, 'max_size': 2},
                'minecraft:density_limit': {'surface': 3},
                'minecraft:biome_filter': {'test': 'has_biome_tag', 'value': 'monster'},
            }],
        },
    })
    g = mobs.disciple_geo()
    g.write(out.path(RP, 'models/entity/bc/dark_disciple.geo.json'), out.path(RP, 'textures/entity/bc/dark_disciple.png'))
    da = mobs.disciple_animations()
    ctx.animations['entity/dark_disciple.animation.json'] = da
    write_json(RP, 'entity/bc/dark_disciple.entity.json', {
        'format_version': '1.10.0',
        'minecraft:client_entity': {'description': {
            'identifier': f'{NS}:dark_disciple',
            'materials': {'default': 'entity_emissive_alpha'},
            'textures': {'default': 'textures/entity/bc/dark_disciple'},
            'geometry': {'default': 'geometry.bc.dark_disciple'},
            'animations': {'idle': 'animation.bc.dark_disciple.idle', 'walk': 'animation.bc.dark_disciple.walk',
                           'look': 'animation.bc.dark_disciple.look_at_target', 'aura': 'animation.bc.mob.aura'},
            'particle_effects': {'aura': 'bc:disciple_aura'},
            'scripts': {'animate': ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look', 'aura']},
            'render_controllers': ['controller.render.bc.default'],
            'spawn_egg': {'base_color': '#1e1030', 'overlay_color': '#a066e0'},
        }},
    })
    ctx.lang += [f'entity.{NS}:dark_disciple.name=Dark Disciple', f'item.spawn_egg.entity.{NS}:dark_disciple.name=Dark Disciple Spawn Egg']

    # ---------------------------------------------------------------- Devil
    comps = mob_base('devil', ['bc_magic', 'bc_devil', 'monster', 'mob', 'boss'], 420, (1.4, 3.4), 0.3,
                     'loot_tables/entities/bc_devil.json', 400)
    comps.update({
        'minecraft:boss': {'should_darken_sky': True, 'hud_range': 64},
        'minecraft:flying_speed': {'value': 0.28},
        'minecraft:can_fly': {},
        'minecraft:navigation.hover': {'can_path_over_water': True, 'can_sink': False, 'can_pass_doors': False,
                                       'can_path_from_air': True, 'avoid_water': True, 'avoid_damage_blocks': True, 'avoid_sun': False},
        'minecraft:movement.hover': {},
        'minecraft:attack': {'damage': 14},
        'minecraft:shooter': {'def': f'{NS}:devil_orb'},
        'minecraft:knockback_resistance': {'value': 0.9},
        'minecraft:fire_immune': True,
        'minecraft:persistent': {},
        'minecraft:damage_sensor': {'triggers': [{'cause': 'fall', 'deals_damage': 'no'},
                                                 {'cause': 'suffocation', 'deals_damage': 'no'},
                                                 {'cause': 'fire', 'deals_damage': 'no'},
                                                 {'cause': 'fire_tick', 'deals_damage': 'no'}]},
        'minecraft:behavior.hurt_by_target': {'priority': 1},
        'minecraft:behavior.ranged_attack': {'priority': 2, 'attack_interval_min': 1.6, 'attack_interval_max': 2.8, 'attack_radius': 24.0, 'speed_multiplier': 1.2},
        'minecraft:behavior.nearest_attackable_target': {
            'priority': 2, 'must_see': False, 'reselect_targets': True, 'within_radius': 40,
            'entity_types': [{'filters': {'any_of': [{'test': 'is_family', 'subject': 'other', 'value': 'player'},
                                                     {'test': 'is_family', 'subject': 'other', 'value': 'irongolem'}]}, 'max_dist': 40}]},
        'minecraft:behavior.random_hover': {'priority': 6, 'xz_dist': 8, 'y_dist': 4, 'y_offset': -1, 'interval': 1, 'hover_height': [2, 5]},
        'minecraft:behavior.look_at_player': {'priority': 7, 'look_distance': 16},
    })
    write_json(BP, 'entities/devil.json', {
        'format_version': ENTITY_FMT,
        'minecraft:entity': {
            'description': {'identifier': f'{NS}:devil', 'is_spawnable': True, 'is_summonable': True},
            'components': comps,
            'events': {},
        },
    })
    g = mobs.devil_geo()
    g.write(out.path(RP, 'models/entity/bc/devil.geo.json'), out.path(RP, 'textures/entity/bc/devil.png'))
    dv = mobs.devil_animations()
    ctx.animations['entity/devil.animation.json'] = dv
    write_json(RP, 'entity/bc/devil.entity.json', {
        'format_version': '1.10.0',
        'minecraft:client_entity': {'description': {
            'identifier': f'{NS}:devil',
            'materials': {'default': 'entity_emissive_alpha'},
            'textures': {'default': 'textures/entity/bc/devil'},
            'geometry': {'default': 'geometry.bc.devil'},
            'animations': {'hover': 'animation.bc.devil.hover', 'wings': 'animation.bc.devil.wings',
                           'look': 'animation.bc.devil.look_at_target', 'aura': 'animation.bc.mob.aura'},
            'particle_effects': {'aura': 'bc:devil_aura'},
            'scripts': {'animate': ['hover', 'wings', 'look', 'aura']},
            'render_controllers': ['controller.render.bc.default'],
            'spawn_egg': {'base_color': '#2b1016', 'overlay_color': '#ff3a2a'},
        }},
    })
    ctx.animations['entity/mob_fx.animation.json'] = {
        'animation.bc.mob.aura': {'loop': 'hold_on_last_frame', 'animation_length': 0.05, 'particle_effects': {'0.0': {'effect': 'aura'}}},
    }
    ctx.lang += [f'entity.{NS}:devil.name=§4Devil', f'item.spawn_egg.entity.{NS}:devil.name=Devil Spawn Egg']


# ======================================================================================
# player animations (played from scripts with playAnimation)
# ======================================================================================
def player_animations():
    tp = '(1.0 - v.is_first_person)'

    def k(x):
        return f'({x}) * {tp}'
    from .models.v2 import player_extra_animations
    from .models.v9 import player_v9_animations
    extra = player_extra_animations(k)
    return {**extra, 
        'animation.bc.player.cast_forward': {
            'animation_length': 0.55,
            'bones': {
                'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.08': [k(-95), k(8), 0], '0.35': [k(-90), k(5), 0], '0.55': [0, 0, 0]},
                             'position': {'0.0': [0, 0, 0], '0.08': [0, 0, '-2.0 * v.is_first_person'], '0.35': [0, 0, '-1.0 * v.is_first_person'], '0.55': [0, 0, 0]}},
                'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.1': [k(-30), 0, k(-12)], '0.55': [0, 0, 0]}},
                'body': {'rotation': {'0.0': [0, 0, 0], '0.08': [0, k(-14), 0], '0.55': [0, 0, 0]}},
            },
        },
        'animation.bc.player.cast_raise': {
            'animation_length': 0.9,
            'bones': {
                'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.15': [k(-165), 0, k(18)], '0.6': [k(-160), 0, k(15)], '0.9': [0, 0, 0]}},
                'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.15': [k(-165), 0, k(-18)], '0.6': [k(-160), 0, k(-15)], '0.9': [0, 0, 0]}},
                'head': {'rotation': {'0.0': [0, 0, 0], '0.15': [k(-15), 0, 0], '0.9': [0, 0, 0]}},
            },
        },
        'animation.bc.player.cast_sweep': {
            'animation_length': 0.6,
            'bones': {
                'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.08': [k(-90), k(70), 0], '0.3': [k(-90), k(-55), 0], '0.6': [0, 0, 0]}},
                'body': {'rotation': {'0.0': [0, 0, 0], '0.08': [0, k(25), 0], '0.3': [0, k(-25), 0], '0.6': [0, 0, 0]}},
            },
        },
        'animation.bc.player.sword_slash': {
            'animation_length': 0.55,
            'bones': {
                'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.12': [k(-175), k(10), k(10)], '0.26': [k(-40), k(-10), k(-5)], '0.55': [0, 0, 0]}},
                'body': {'rotation': {'0.0': [0, 0, 0], '0.12': [k(-8), k(10), 0], '0.26': [k(12), k(-12), 0], '0.55': [0, 0, 0]}},
                'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.12': [k(-40), 0, 0], '0.55': [0, 0, 0]}},
            },
        },
        'animation.bc.player.sword_thrust': {
            'animation_length': 0.5,
            'bones': {
                'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.1': [k(-70), k(30), 0], '0.22': [k(-95), k(-5), 0], '0.5': [0, 0, 0]}},
                'body': {'rotation': {'0.0': [0, 0, 0], '0.1': [0, k(25), 0], '0.22': [0, k(-20), 0], '0.5': [0, 0, 0]}},
            },
        },
        'animation.bc.player.guard': {
            'animation_length': 0.6,
            'bones': {
                'rightArm': {'rotation': {'0.0': [0, 0, 0], '0.1': [k(-70), k(45), 0], '0.45': [k(-70), k(45), 0], '0.6': [0, 0, 0]}},
                'leftArm': {'rotation': {'0.0': [0, 0, 0], '0.1': [k(-60), k(-30), 0], '0.45': [k(-60), k(-30), 0], '0.6': [0, 0, 0]}},
            },
        },
        # v0.9.0: smooth, full-body cast animations replace the old ones of the same name
        **player_v9_animations(k),
    }


# ======================================================================================
# shared RP files
# ======================================================================================
def gen_render_controllers():
    rc = {'geometry': 'Geometry.default', 'materials': [{'*': 'Material.default'}], 'textures': ['Texture.default']}
    write_json(RP, 'render_controllers/bc.render_controllers.json', {
        'format_version': '1.10.0',
        'render_controllers': {
            'controller.render.bc.default': dict(rc),
            'controller.render.bc.attachable': dict(rc),
        },
    })


def gen_lang(ctx: Ctx):
    rp_lang = ['pack.name=Black Clover: Grimoire Awakening', 'pack.description=Unofficial Black Clover fan addon',
               f'tile.{NS}:grimoire_altar.name=§dGrimoire Altar'] + ctx.lang
    bp_lang = ['pack.name=Black Clover: Grimoire Awakening', 'pack.description=Unofficial Black Clover fan addon']
    write_text(RP, 'texts/en_US.lang', '\n'.join(rp_lang) + '\n')
    write_text(BP, 'texts/en_US.lang', '\n'.join(bp_lang) + '\n')
    write_json(RP, 'texts/languages.json', ['en_US'])
    write_json(BP, 'texts/languages.json', ['en_US'])


def flush(ctx: Ctx):
    ctx.animations['player/bc_player.animation.json'] = player_animations()
    for rel, anims in ctx.animations.items():
        write_json(RP, f'animations/{rel}', {'format_version': '1.10.0', 'animations': anims})
    write_json(RP, 'textures/item_texture.json', {
        'resource_pack_name': 'black_clover', 'texture_name': 'atlas.items',
        'texture_data': {k: {'textures': v} for k, v in sorted(ctx.item_textures.items())},
    })
    write_json(RP, 'textures/terrain_texture.json', {
        'resource_pack_name': 'black_clover', 'texture_name': 'atlas.terrain', 'padding': 8, 'num_mip_levels': 4,
        'texture_data': {k: {'textures': v} for k, v in sorted(ctx.terrain_textures.items())},
    })
    write_json(RP, 'blocks.json', {'format_version': [1, 1, 0], f'{NS}:grimoire_altar': {'sound': 'stone'}, f'{NS}:bounty_board': {'sound': 'wood'},
                            f'{NS}:war_table': {'sound': 'wood'}, f'{NS}:mission_board': {'sound': 'wood'}, f'{NS}:squad_banner': {'sound': 'wood'},
                            f'{NS}:magic_forge': {'sound': 'metal'}, f'{NS}:waygate': {'sound': 'stone'},
                            f'{NS}:mana_spawner': {'sound': 'metal'}, f'{NS}:obelisk_core': {'sound': 'stone'}})
    gen_render_controllers()
    gen_lang(ctx)
    write_json(BP, 'manifest.json', manifest_bp())
    write_json(RP, 'manifest.json', manifest_rp())


def build():
    ctx = Ctx()
    gen_grimoires(ctx)
    gen_swords(ctx)
    gen_robes(ctx)
    gen_misc_items(ctx)
    gen_altar(ctx)
    gen_recipes(ctx)
    gen_loot(ctx)
    gen_spell_entities(ctx)
    gen_mobs(ctx)
    from . import grandgen, seagen, v2gen, v3gen, v5gen, v7gen, v8gen, v9gen, v10gen, v11gen, v12gen, v13gen, v75gen, wave4gen  # expansions (import this module, so loaded lazily)
    seagen.build(ctx)
    grandgen.build(ctx)
    wave4gen.build(ctx)
    v2gen.build(ctx)
    v3gen.build(ctx)
    v5gen.build(ctx)
    v7gen.build(ctx)
    v75gen.build(ctx)
    v8gen.build(ctx)
    v9gen.build(ctx)
    v10gen.build(ctx)
    v11gen.build(ctx)
    v12gen.build(ctx)
    v13gen.build(ctx)
    v3gen.check_armies()
    flush(ctx)
    return ctx
