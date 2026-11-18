"""v0.9.0 pack content: the rebuilt spell projectile (mana bolt) - layered shapes plus a comet, gradient tint textures,
a glowing halo and element trails."""
from __future__ import annotations

import json

from . import out, vfx9
from .models import v9
from .models.wave4 import TINTS
from .out import BP, RP, write_json, write_png
from .packgen import Ctx, NS


def gen_bolt(ctx: Ctx):
    with open(out.path(RP, 'models/entity/bc/mana_bolt.geo.json'), 'w') as fh:
        json.dump(v9.bolt_geometry_file(), fh, indent=1)
    textures = {}
    for i, (_, hexc) in enumerate(TINTS):
        write_png(RP, f'textures/entity/bc/bolt/t{i}.png', v9.bolt_texture(hexc))
        textures[f't{i}'] = f'textures/entity/bc/bolt/t{i}'
    script = v9.trail_script(TINTS, vfx9.FLAVORS)
    effects = {'halo': 'bc:fx_halo', **{f'trail{i}': ident for i, ident in enumerate(vfx9.TRAIL_IDS)}}
    ctx.animations['entity/mana_bolt.animation.json'] = {
        **v9.bolt_animations(),
        'animation.bc.mana_bolt.trail': {'loop': 'hold_on_last_frame', 'animation_length': 0.05, 'particle_effects': {
            '0.0': [{'effect': name, 'pre_effect_script': script} for name in effects]}},
    }
    write_json(RP, 'entity/bc/mana_bolt.entity.json', {'format_version': '1.10.0', 'minecraft:client_entity': {'description': {
        'identifier': f'{NS}:mana_bolt',
        'materials': {'default': 'entity_emissive_alpha'},
        'textures': textures,
        'geometry': {k: f'geometry.bc.bolt_{k}' for k in v9.SHAPES},
        'animations': {'fly': 'animation.bc.mana_bolt.fly', 'trail': 'animation.bc.mana_bolt.trail'},
        'particle_effects': effects,
        'scripts': {'animate': ['fly', 'trail'], 'scale': "1.0 + q.property('bc:size') * 0.55"},
        'render_controllers': ['controller.render.bc.mana_bolt'],
    }}})
    # the comet is a fifth shape
    p = out.path(BP, 'entities/living/mana_bolt.json')
    with open(p) as fh:
        d = json.load(fh)
    d['minecraft:entity']['description']['properties']['bc:shape']['range'] = [0, len(v9.SHAPES) - 1]
    write_json(BP, 'entities/living/mana_bolt.json', d)
    p = out.path(RP, 'render_controllers/bc_living.render_controllers.json')
    with open(p) as fh:
        rc = json.load(fh)
    rc['render_controllers']['controller.render.bc.mana_bolt']['arrays']['geometries'] = {'Array.shapes': [f'Geometry.{k}' for k in v9.SHAPES]}
    write_json(RP, 'render_controllers/bc_living.render_controllers.json', rc)


def gen_knight_casts(ctx: Ctx):
    """Magic Knights, companions and Rogue Mages share the player's bones: they get the same full-body cast animations."""
    anims = v9.player_v9_animations(lambda x: x)
    ctx.animations['entity/knight_v9.animation.json'] = {
        name.replace('animation.bc.player.', 'animation.bc.magic_knight.v9_'): a for name, a in anims.items()}


def build(ctx: Ctx):
    gen_bolt(ctx)
    gen_knight_casts(ctx)
