"""v0.7.5 pack content: mana potions, elixirs, smoke bombs and spell scrolls (items and recipes)."""
from __future__ import annotations

from .data import CONSUMABLES, NS
from .models import v75
from .out import BP, write_json
from .packgen import Ctx, item_json
from .v3gen import _icon

DRINKS = {'mana_potion', 'greater_mana_potion', 'elixir_iron', 'elixir_haste'}


def _shapeless(ident, ingredients, count=1):
    return {'format_version': '1.20.10', 'minecraft:recipe_shapeless': {
        'description': {'identifier': f'{NS}:{ident}'}, 'tags': ['crafting_table'],
        'ingredients': [{'item': i} for i in ingredients],
        'unlock': {'context': 'AlwaysUnlocked'}, 'result': {'item': f'{NS}:{ident}', 'count': count}}}


def gen_items(ctx: Ctx):
    ic = v75.v75_icons()
    for key, (name, _) in CONSUMABLES.items():
        comps = {'minecraft:max_stack_size': {'value': 16}}
        if key in DRINKS:
            comps.update({'minecraft:food': {'nutrition': 0, 'saturation_modifier': 0, 'can_always_eat': True},
                          'minecraft:use_modifiers': {'use_duration': 1.2, 'movement_modifier': 0.5}, 'minecraft:use_animation': 'drink'})
        else:
            comps['minecraft:use_modifiers'] = {'use_duration': 0.4, 'movement_modifier': 1.0}
        if key in ('greater_mana_potion', 'spell_scroll'):
            comps['minecraft:glint'] = {'value': True}
        write_json(BP, f'items/v75/{key}.json', item_json(f'{NS}:{key}', name, _icon(ctx, key, ic[key]), comps))
    crystal = f'{NS}:mana_crystal'
    write_json(BP, 'recipes/v75/mana_potion.json', _shapeless('mana_potion', ['minecraft:glass_bottle', crystal, crystal]))
    write_json(BP, 'recipes/v75/greater_mana_potion.json', _shapeless('greater_mana_potion', [f'{NS}:mana_potion', f'{NS}:mana_potion', 'minecraft:glowstone_dust']))
    write_json(BP, 'recipes/v75/elixir_iron.json', _shapeless('elixir_iron', ['minecraft:glass_bottle', 'minecraft:iron_block', crystal]))
    write_json(BP, 'recipes/v75/elixir_haste.json', _shapeless('elixir_haste', ['minecraft:glass_bottle', 'minecraft:sugar', 'minecraft:feather', crystal]))
    write_json(BP, 'recipes/v75/smoke_bomb.json', _shapeless('smoke_bomb', ['minecraft:gunpowder', 'minecraft:coal', 'minecraft:string'], count=2))
    write_json(BP, 'recipes/v75/spell_scroll.json', _shapeless('spell_scroll', ['minecraft:paper', f'{NS}:ancient_page', crystal]))


def build(ctx: Ctx):
    gen_items(ctx)
