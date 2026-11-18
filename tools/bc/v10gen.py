"""v1.0.0 pack content: the Mana Waygate block."""
from __future__ import annotations

from .models import v10
from .out import BP, RP, write_json, write_png
from .packgen import NS, Ctx
from .v3gen import _icon


def gen_waygate(ctx: Ctx):
    g = v10.waygate_geo()
    g.paint()
    a = g.atlas
    a[..., 3] = (a[..., 3] > 0) * 255.0
    write_json(RP, 'models/blocks/bc/waygate.geo.json', g.to_json())
    write_png(RP, 'textures/blocks/bc/waygate.png', a)
    ctx.terrain_textures['bc_waygate'] = 'textures/blocks/bc/waygate'
    _icon(ctx, 'waygate', v10.waygate_icon())
    write_json(BP, 'blocks/waygate.json', {
        'format_version': '1.21.90',
        'minecraft:block': {
            'description': {'identifier': f'{NS}:waygate', 'menu_category': {'category': 'items'}},
            'components': {
                'minecraft:geometry': 'geometry.bc.waygate',
                'minecraft:material_instances': {'*': {'texture': 'bc_waygate', 'render_method': 'alpha_test'}},
                'minecraft:collision_box': {'origin': [-8, 0, -8], 'size': [16, 3, 16]},
                'minecraft:selection_box': {'origin': [-8, 0, -8], 'size': [16, 16, 16]},
                'minecraft:destructible_by_mining': {'seconds_to_destroy': 4.0},
                'minecraft:destructible_by_explosion': {'explosion_resistance': 30},
                'minecraft:light_emission': 10,
                'minecraft:light_dampening': 0,
                'minecraft:map_color': '#60b8ff',
                'bc:waygate': {},
            },
        },
    })
    ctx.lang.append(f'tile.{NS}:waygate.name=§bMana Waygate')
    write_json(BP, 'recipes/v10/waygate.json', {'format_version': '1.20.10', 'minecraft:recipe_shaped': {
        'description': {'identifier': f'{NS}:waygate'}, 'tags': ['crafting_table'], 'pattern': ['SCS', 'SES', 'SRS'],
        'key': {'S': {'item': 'minecraft:stone_bricks'}, 'C': {'item': f'{NS}:mana_crystal'}, 'E': {'item': 'minecraft:ender_pearl'},
                'R': {'item': f'{NS}:rune_shard'}},
        'unlock': {'context': 'AlwaysUnlocked'}, 'result': {'item': f'{NS}:waygate'}}})


def build(ctx: Ctx):
    gen_waygate(ctx)
