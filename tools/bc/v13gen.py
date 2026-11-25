"""v1.3.0 pack content: devil hosts and the Crowned Vessel (with the parts their union shows), the Pact Sigils and the
other new items, and the union sprites players wear while joined with their devil."""
from __future__ import annotations

from . import out
from .data import DEVILS, NS, PACT_DEVILS, V13_ITEMS
from .models import v13
from .out import RP, BP, write_json, write_png
from .packgen import Ctx, item_json, mob_base, shaped
from .seagen import _entity, _melee_ai
from .v3gen import _icon, _pool
from .v8gen import _shapeless

HOST_LOOKS = ['vharog', 'sileth', 'morvane', 'ghorza', 'lesser']   # bc:devil property -> look
PT = 'textures/particle/bc/v13/'


def gen_items(ctx: Ctx):
    ic = v13.v13_icons()
    usable = {'minecraft:use_modifiers': {'use_duration': 0.6, 'movement_modifier': 1.0}}
    for key, (name, _) in V13_ITEMS.items():
        stack = 1 if key.startswith('pact_') or key == 'abyssal_crown' else 16 if key == 'binding_chain' else 64
        comps = {'minecraft:max_stack_size': {'value': stack}}
        if key != 'host_horn':
            comps.update(usable)
        if key.startswith('pact_') or key == 'abyssal_crown':
            comps['minecraft:glint'] = {'value': True}
        write_json(BP, f'items/v13/{key}.json', item_json(f'{NS}:{key}', name, _icon(ctx, key, ic[key]), comps,
                                                          category='equipment' if key.startswith('pact_') else 'items'))
    write_json(BP, 'recipes/v13/binding_chain.json', shaped('binding_chain', ['I', 'H', 'I'], {
        'I': 'minecraft:chain', 'H': f'{NS}:host_horn'}, count=2))
    write_json(BP, 'recipes/v13/abyssal_crown.json', shaped('abyssal_crown', ['HGH', 'DOD', 'HGH'], {
        'H': f'{NS}:host_horn', 'G': 'minecraft:gold_ingot', 'D': f'{NS}:devil_heart', 'O': 'minecraft:crying_obsidian'}))


def gen_loot(ctx: Ctx):
    L = 'loot_tables/entities'
    write_json(BP, f'{L}/bc_devil_host.json', {'pools': [_pool(f'{NS}:devil_heart', 1, 1, 0.25), _pool(f'{NS}:doubloon', 4, 12),
                                                         _pool(f'{NS}:mana_crystal', 1, 2, 0.4), _pool('minecraft:blaze_powder', 1, 2, 0.3)]})
    write_json(BP, f'{L}/bc_crowned_vessel.json', {'pools': [_pool(f'{NS}:devil_heart', 3, 5), _pool(f'{NS}:host_horn', 2, 4),
                                                             _pool(f'{NS}:mana_crystal', 6, 10), _pool('minecraft:netherite_scrap', 1, 2),
                                                             _pool(f'{NS}:doubloon', 40, 80)]})


def gen_particles(ctx: Ctx):
    write_png(RP, f'{PT}union_wings.png', v13.wings_sprite())
    write_png(RP, f'{PT}union_horns.png', v13.horns_sprite())

    def sprite(ident, texture, w, h, size, mode, direction=None, life='0.14'):
        bb = {'size': size, 'facing_camera_mode': mode,
              'uv': {'texture_width': w, 'texture_height': h, 'uv': [0, 0], 'uv_size': [w, h]}}
        if direction:
            bb['direction'] = {'mode': 'custom', 'custom_direction': direction}
        return {'format_version': '1.10.0', 'particle_effect': {
            'description': {'identifier': ident, 'basic_render_parameters': {'material': 'particles_blend', 'texture': PT + texture}},
            'components': {
                'minecraft:emitter_initialization': {'creation_expression': 'v.sc = v.scale ?? 1.0;'},
                'minecraft:emitter_rate_instant': {'num_particles': 1}, 'minecraft:emitter_lifetime_once': {'active_time': 0.05},
                'minecraft:emitter_shape_point': {},
                'minecraft:particle_lifetime_expression': {'max_lifetime': life},
                'minecraft:particle_appearance_billboard': bb,
                'minecraft:particle_appearance_tinting': {'color': ['v.color.r ?? 1.0', 'v.color.g ?? 0.3', 'v.color.b ?? 0.2',
                                                                    'math.clamp(v.particle_age * 30.0, 0.0, 1.0) * 0.92']},
            }}}
    write_json(RP, 'particles/bc/v13/union_wings.particle.json',
               sprite('bc:union_wings', 'union_wings', 128, 64, ['1.25 * v.sc', '0.62 * v.sc'], 'direction_z', ['v.dir.x ?? 0', '0', 'v.dir.z ?? 1']))
    write_json(RP, 'particles/bc/v13/union_horns.particle.json',
               sprite('bc:union_horns', 'union_horns', 64, 32, ['0.42 * v.sc', '0.21 * v.sc'], 'lookat_y'))


def _visibility(half, full):
    return [{'*': True}] + [{b: "q.property('bc:union') >= 1"} for b in half] + [{b: "q.property('bc:union') >= 2"} for b in full]


def gen_entities(ctx: Ctx):
    rcs = {}
    union_prop = {'bc:union': {'type': 'int', 'range': [0, 2], 'default': 0, 'client_sync': True}}
    union_events = {f'bc:union_{i}': {'set_property': {'bc:union': i}} for i in range(3)}
    # ---------------------------------------------------------------- devil hosts
    comps = mob_base('devil_host', ['bc_devil', 'bc_devil_host', 'bc_magic', 'monster', 'mob'], 70, (0.6, 1.95), 0.29,
                     'loot_tables/entities/bc_devil_host.json', 24)
    comps.update(_melee_ai(6, targets=('player', 'bc_knight', 'bc_navy', 'bc_kingdom')))
    comps['minecraft:behavior.hurt_by_target'] = {'priority': 1, 'alert_same_type': True}
    comps['minecraft:damage_sensor'] = {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}]}
    ent = _entity('devil_host', comps)
    e = ent['minecraft:entity']
    e['description']['properties'] = {'bc:devil': {'type': 'int', 'range': [0, len(HOST_LOOKS) - 1], 'default': 0, 'client_sync': True}, **union_prop}
    e['events'] = {**{f'bc:devil_{i}': {'set_property': {'bc:devil': i}} for i in range(len(HOST_LOOKS))}, **union_events}
    write_json(BP, 'entities/v13/devil_host.json', ent)
    geos, texs = {}, {}
    for i, d in enumerate(HOST_LOOKS):
        g = v13.devil_host_geo(d)
        g.write(out.path(RP, f'models/entity/bc/devil_host_{d}.geo.json'), out.path(RP, f'textures/entity/bc/devil_host/{d}.png'))
        geos[d] = f'geometry.bc.devil_host_{d}'
        texs[d] = f'textures/entity/bc/devil_host/{d}'
    ha = v13.host_animations()
    ctx.animations['entity/devil_host.animation.json'] = ha
    write_json(RP, 'entity/bc/devil_host.entity.json', {'format_version': '1.10.0', 'minecraft:client_entity': {'description': {
        'identifier': f'{NS}:devil_host', 'materials': {'default': 'entity_emissive_alpha'}, 'textures': texs, 'geometry': geos,
        'animations': {k.split('.')[-1]: k for k in ha},
        'scripts': {'animate': ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look_at_target', 'union']},
        'render_controllers': ['controller.render.bc.devil_host'], 'spawn_egg': {'base_color': '#1a0a0e', 'overlay_color': '#ff3a2a'}}}})
    rcs['controller.render.bc.devil_host'] = {
        'arrays': {'textures': {'Array.skins': [f'Texture.{d}' for d in HOST_LOOKS]}, 'geometries': {'Array.geos': [f'Geometry.{d}' for d in HOST_LOOKS]}},
        'geometry': "Array.geos[q.property('bc:devil')]", 'materials': [{'*': 'Material.default'}], 'textures': ["Array.skins[q.property('bc:devil')]"],
        'part_visibility': _visibility(v13.HALF_BONES, v13.FULL_BONES)}
    ctx.lang += [f'entity.{NS}:devil_host.name=Devil Host', f'item.spawn_egg.entity.{NS}:devil_host.name=Devil Host Spawn Egg']

    # ---------------------------------------------------------------- the Crowned Vessel
    comps = mob_base('crowned_vessel', ['bc_devil', 'bc_devil_host', 'bc_magic', 'monster', 'mob', 'boss'], 900, (1.0, 2.9), 0.3,
                     'loot_tables/entities/bc_crowned_vessel.json', 600)
    comps.update(_melee_ai(14, targets=('player', 'bc_knight', 'bc_navy', 'bc_kingdom')))
    comps.pop('minecraft:despawn', None)
    comps['minecraft:persistent'] = {}
    comps['minecraft:knockback_resistance'] = {'value': 0.9}
    comps['minecraft:fire_immune'] = True
    comps['minecraft:pushable'] = {'is_pushable': False, 'is_pushable_by_piston': False}
    comps['minecraft:damage_sensor'] = {'triggers': [{'cause': 'fall', 'deals_damage': 'no'}, {'cause': 'fire', 'deals_damage': 'no'},
                                                     {'cause': 'fire_tick', 'deals_damage': 'no'}, {'cause': 'lava', 'deals_damage': 'no'}]}
    ent = _entity('crowned_vessel', comps)
    e = ent['minecraft:entity']
    e['description']['properties'] = dict(union_prop)
    e['events'] = dict(union_events)
    write_json(BP, 'entities/v13/crowned_vessel.json', ent)
    g = v13.vessel_geo()
    g.write(out.path(RP, 'models/entity/bc/crowned_vessel.geo.json'), out.path(RP, 'textures/entity/bc/crowned_vessel.png'))
    va = v13.vessel_animations()
    ctx.animations['entity/crowned_vessel.animation.json'] = va
    write_json(RP, 'entity/bc/crowned_vessel.entity.json', {'format_version': '1.10.0', 'minecraft:client_entity': {'description': {
        'identifier': f'{NS}:crowned_vessel', 'materials': {'default': 'entity_emissive_alpha'}, 'textures': {'default': 'textures/entity/bc/crowned_vessel'},
        'geometry': {'default': 'geometry.bc.crowned_vessel'}, 'animations': {k.split('.')[-1]: k for k in va},
        'scripts': {'animate': ['idle', {'walk': 'q.modified_move_speed > 0.01'}, 'look_at_target', 'union']},
        'render_controllers': ['controller.render.bc.crowned_vessel'], 'spawn_egg': {'base_color': '#16121a', 'overlay_color': '#ff2a4a'}}}})
    rcs['controller.render.bc.crowned_vessel'] = {
        'geometry': 'Geometry.default', 'materials': [{'*': 'Material.default'}], 'textures': ['Texture.default'],
        'part_visibility': _visibility(v13.VESSEL_HALF, v13.VESSEL_FULL)}
    ctx.lang += [f'entity.{NS}:crowned_vessel.name=§4The Crowned Vessel', f'item.spawn_egg.entity.{NS}:crowned_vessel.name=Crowned Vessel Spawn Egg']
    return rcs


def build(ctx: Ctx):
    gen_items(ctx)
    gen_loot(ctx)
    gen_particles(ctx)
    rcs = gen_entities(ctx)
    write_json(RP, 'render_controllers/bc_v13.render_controllers.json', {'format_version': '1.10.0', 'render_controllers': rcs})
    assert set(PACT_DEVILS) <= set(DEVILS)
