"""v0.8.0 pack content: eight armour sets (32 pieces with 3D attachables), armour materials, runes and the Magic Forge."""
from __future__ import annotations

import json

from . import out
from .data import ARMOR_DUR, ARMOR_MATERIALS, ARMOR_SETS, ARMOR_SLOTS, NS, RUNES
from .models import v8
from .out import BP, RP, write_json, write_png
from .packgen import Ctx, item_json
from .v3gen import _icon

PIECE = {'head': 'helmet', 'chest': 'chestplate', 'legs': 'leggings', 'feet': 'boots'}
WEAR_SLOT = {'head': 'slot.armor.head', 'chest': 'slot.armor.chest', 'legs': 'slot.armor.legs', 'feet': 'slot.armor.feet'}
ENCHANT = {'head': 'armor_head', 'chest': 'armor_torso', 'legs': 'armor_legs', 'feet': 'armor_feet'}
GROUP = {'head': 'minecraft:itemGroup.name.helmet', 'chest': 'minecraft:itemGroup.name.chestplate',
         'legs': 'minecraft:itemGroup.name.leggings', 'feet': 'minecraft:itemGroup.name.boots'}
LAYER = {'head': 'v.helmet_layer_visible = 0.0;', 'chest': 'v.chest_layer_visible = 0.0;',
         'legs': 'v.leg_layer_visible = 0.0;', 'feet': 'v.boot_layer_visible = 0.0;'}


def piece_id(sid, slot):
    return f'{sid}_{PIECE[slot]}'


def _shapeless(ident, ingredients, count=1):
    return {'format_version': '1.20.10', 'minecraft:recipe_shapeless': {
        'description': {'identifier': f'{NS}:{ident}'}, 'tags': ['crafting_table'],
        'ingredients': [{'item': i} for i in ingredients],
        'unlock': {'context': 'AlwaysUnlocked'}, 'result': {'item': f'{NS}:{ident}', 'count': count}}}


def gen_armor(ctx: Ctx):
    anims = {}
    for sid, s in ARMOR_SETS.items():
        for k, slot in enumerate(ARMOR_SLOTS):
            pid = piece_id(sid, slot)
            ident = f'{NS}:{pid}'
            icon = _icon(ctx, pid, v8.piece_icon(sid, slot))
            mat = f"{NS}:{s['material']}"
            repair = [mat] if s['material'] == 'mana_steel_ingot' else [mat, f'{NS}:mana_steel_ingot']
            write_json(BP, f'items/v8/{pid}.json', item_json(ident, f"{s['mc']}{s['pieces'][k]}", icon, {
                'minecraft:max_stack_size': {'value': 1},
                'minecraft:wearable': {'slot': WEAR_SLOT[slot], 'protection': s['prot'][k]},
                'minecraft:durability': {'max_durability': int(s['dur'] * ARMOR_DUR[slot])},
                'minecraft:enchantable': {'slot': ENCHANT[slot], 'value': 15 if s['style'] in ('mage', 'royal') else 12},
                'minecraft:repairable': {'repair_items': [{'items': repair, 'repair_amount': int(s['dur'] * ARMOR_DUR[slot] * 0.25)}]},
                'minecraft:tags': {'tags': ['minecraft:is_armor', 'bc:armor', f'bc:armor_{sid}']},
            }, category='equipment', group=GROUP[slot]))
            g = v8.armor_geo(sid, slot)
            g.write(out.path(RP, f'models/entity/bc/armor/{sid}_{slot}.geo.json'), out.path(RP, f'textures/entity/bc/armor/{sid}_{slot}.png'))
            anims.update(v8.armor_animation(sid, slot))
            write_json(RP, f'attachables/armor/{pid}.json', {
                'format_version': '1.10.0',
                'minecraft:attachable': {'description': {
                    'identifier': ident,
                    'materials': {'default': 'entity_alphatest', 'enchanted': 'entity_alphatest_glint'},
                    'textures': {'default': f'textures/entity/bc/armor/{sid}_{slot}', 'enchanted': 'textures/misc/enchanted_item_glint'},
                    'geometry': {'default': f'geometry.bc.{sid}_{slot}'},
                    'animations': {'wear': f'animation.bc.armor.{sid}_{slot}'},
                    'scripts': {'parent_setup': LAYER[slot], 'animate': ['wear']},
                    'render_controllers': ['controller.render.bc.attachable'],
                }},
            })
    ctx.animations['attachables/armor.animation.json'] = anims


def gen_materials(ctx: Ctx):
    ic = v8.material_icons()
    for key, (name, _, _) in ARMOR_MATERIALS.items():
        write_json(BP, f'items/v8/{key}.json', item_json(f'{NS}:{key}', name, _icon(ctx, key, ic[key]), {'minecraft:max_stack_size': {'value': 64}}))
    crystal = f'{NS}:mana_crystal'
    write_json(BP, 'recipes/v8/mana_steel_ingot.json', _shapeless('mana_steel_ingot', ['minecraft:iron_ingot', crystal, crystal]))
    ric = v8.rune_icons()
    for rid, (name, color, _, extra) in RUNES.items():
        key = f'rune_{rid}'
        write_json(BP, f'items/v8/{key}.json', item_json(f'{NS}:{key}', f'§d{name}', _icon(ctx, key, ric[key]), {
            'minecraft:max_stack_size': {'value': 16}, 'minecraft:glint': {'value': True}}))
        write_json(BP, f'recipes/v8/{key}.json', _shapeless(key, [f'{NS}:rune_shard', f'{NS}:rune_shard', crystal, extra]))


def gen_forge(ctx: Ctx):
    g = v8.forge_geo()
    g.paint()
    a = g.atlas
    a[..., 3] = (a[..., 3] > 0) * 255.0
    write_json(RP, 'models/blocks/bc/magic_forge.geo.json', g.to_json())
    write_png(RP, 'textures/blocks/bc/magic_forge.png', a)
    ctx.terrain_textures['bc_magic_forge'] = 'textures/blocks/bc/magic_forge'
    _icon(ctx, 'magic_forge', v8.forge_icon())
    dirs = {'north': 0, 'east': -90, 'south': 180, 'west': 90}
    write_json(BP, 'blocks/magic_forge.json', {
        'format_version': '1.21.90',
        'minecraft:block': {
            'description': {
                'identifier': f'{NS}:magic_forge',
                'menu_category': {'category': 'items'},
                'traits': {'minecraft:placement_direction': {'enabled_states': ['minecraft:cardinal_direction'], 'y_rotation_offset': 180}},
            },
            'components': {
                'minecraft:geometry': 'geometry.bc.magic_forge',
                'minecraft:material_instances': {'*': {'texture': 'bc_magic_forge', 'render_method': 'alpha_test'}},
                'minecraft:collision_box': {'origin': [-8, 0, -8], 'size': [16, 14, 16]},
                'minecraft:selection_box': {'origin': [-8, 0, -8], 'size': [16, 15, 16]},
                'minecraft:destructible_by_mining': {'seconds_to_destroy': 3.0},
                'minecraft:destructible_by_explosion': {'explosion_resistance': 20},
                'minecraft:light_emission': 9,
                'minecraft:light_dampening': 0,
                'minecraft:map_color': '#4d5059',
                'bc:magic_forge': {},
            },
            'permutations': [
                {'condition': f"q.block_state('minecraft:cardinal_direction') == '{d}'",
                 'components': {'minecraft:transformation': {'rotation': [0, r, 0]}}}
                for d, r in dirs.items()
            ],
        },
    })
    ctx.lang.append(f'tile.{NS}:magic_forge.name=§bMagic Forge')
    write_json(BP, 'recipes/v8/magic_forge.json', {'format_version': '1.20.10', 'minecraft:recipe_shaped': {
        'description': {'identifier': f'{NS}:magic_forge'}, 'tags': ['crafting_table'],
        'pattern': ['MAM', 'IBI', 'SSS'],
        'key': {'M': {'item': f'{NS}:mana_crystal'}, 'A': {'item': 'minecraft:anvil'}, 'I': {'item': 'minecraft:iron_block'},
                'B': {'item': 'minecraft:blast_furnace'}, 'S': {'item': 'minecraft:stone_bricks'}},
        'unlock': {'context': 'AlwaysUnlocked'}, 'result': {'item': f'{NS}:magic_forge'}}})


def knights_wear_armor():
    """Let Magic Knights (and so companions) show the armour they are given."""
    p = out.path(RP, 'entity/bc/magic_knight.entity.json')
    with open(p) as f:
        d = json.load(f)
    d['minecraft:client_entity']['description']['enable_attachables'] = True
    write_json(RP, 'entity/bc/magic_knight.entity.json', d)


def build(ctx: Ctx):
    gen_armor(ctx)
    gen_materials(ctx)
    gen_forge(ctx)
    knights_wear_armor()
