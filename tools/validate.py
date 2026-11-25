#!/usr/bin/env python3
"""Cross-reference checks for the generated packs (run after build.py)."""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BP = os.path.join(ROOT, 'packs', 'BlackClover_BP')
RP = os.path.join(ROOT, 'packs', 'BlackClover_RP')
errors = []


def load(p):
    with open(p, encoding='utf-8') as fh:
        return json.load(fh)


def walk(base, ext):
    for d, _, fs in os.walk(base):
        for f in fs:
            if f.endswith(ext):
                yield os.path.join(d, f)


# every json parses
for base in (BP, RP):
    for p in walk(base, '.json'):
        try:
            load(p)
        except Exception as e:
            errors.append(f'bad json {p}: {e}')

geos = set()
for p in walk(os.path.join(RP, 'models'), '.json'):
    for g in load(p).get('minecraft:geometry', []):
        geos.add(g['description']['identifier'])
anims = set()
for p in walk(os.path.join(RP, 'animations'), '.json'):
    anims |= set(load(p)['animations'])
particles = set()
looping = set()
for p in walk(os.path.join(RP, 'particles'), '.json'):
    d = load(p)['particle_effect']
    particles.add(d['description']['identifier'])
    if 'minecraft:emitter_lifetime_expression' in d['components']:
        looping.add(d['description']['identifier'])
    tex = d['description']['basic_render_parameters']['texture']
    if not os.path.exists(os.path.join(RP, tex + '.png')):
        errors.append(f'particle texture missing {tex}')
RC_DEFS = {}
for p_ in walk(os.path.join(RP, 'render_controllers'), '.json'):
    RC_DEFS.update(load(p_)['render_controllers'])
rcs = set(RC_DEFS)
item_tex = load(os.path.join(RP, 'textures', 'item_texture.json'))['texture_data']
for k, v in item_tex.items():
    if not os.path.exists(os.path.join(RP, v['textures'] + '.png')):
        errors.append(f'item texture missing {v}')
sounds = set(load(os.path.join(RP, 'sounds', 'sound_definitions.json'))['sound_definitions'])
for k, v in load(os.path.join(RP, 'sounds', 'sound_definitions.json'))['sound_definitions'].items():
    for s in v['sounds']:
        if not os.path.exists(os.path.join(RP, s['name'] + '.ogg')):
            errors.append(f'sound file missing {s}')

def check_client(desc, where):
    for g in desc.get('geometry', {}).values():
        if g not in geos:
            errors.append(f'{where}: unknown geometry {g}')
    for t in desc.get('textures', {}).values():
        if not t.startswith('textures/misc/') and not os.path.exists(os.path.join(RP, t + '.png')):
            errors.append(f'{where}: missing texture {t}')
    for a in desc.get('animations', {}).values():
        if a not in anims:
            errors.append(f'{where}: unknown animation {a}')
    for pe in desc.get('particle_effects', {}).values():
        if pe not in particles:
            errors.append(f'{where}: unknown particle {pe}')
    for rc in desc.get('render_controllers', []):
        name = rc if isinstance(rc, str) else list(rc)[0]
        if name.startswith('controller.render.bc') and name not in rcs:
            errors.append(f'{where}: unknown render controller {name}')
        # array entries must name textures / geometries this client entity defines
        for kind, key in (('textures', 'textures'), ('geometries', 'geometry')):
            for arr in RC_DEFS.get(name, {}).get('arrays', {}).get(kind, {}).values():
                for ref in arr:
                    if ref.split('.', 1)[1] not in desc.get(key, {}):
                        errors.append(f'{where}: render controller {name} uses missing {ref}')

bp_ids = set()
ent_props = set()    # entity property names (bc:tint ...)
ent_events = set()   # entity event names (bc:team_a ...)
for p in walk(os.path.join(BP, 'entities'), '.json'):
    ent = load(p)['minecraft:entity']
    bp_ids.add(ent['description']['identifier'])
    ent_props.update(ent['description'].get('properties', {}))
    ent_events.update(ent.get('events', {}))
block_ids = set()
for p in walk(os.path.join(BP, 'blocks'), '.json'):
    blk = load(p)['minecraft:block']
    block_ids.add(blk['description']['identifier'])
    block_ids.update(k for k in blk['components'] if k.startswith('bc:'))
for p in walk(os.path.join(RP, 'entity'), '.json'):
    d = load(p)['minecraft:client_entity']['description']
    check_client(d, p)
    if d['identifier'] not in bp_ids:
        errors.append(f'client entity without server entity {d["identifier"]}')
item_ids = set()
for p in walk(os.path.join(BP, 'items'), '.json'):
    it = load(p)['minecraft:item']
    item_ids.add(it['description']['identifier'])
    icon = it['components']['minecraft:icon']['textures']['default']
    if icon not in item_tex:
        errors.append(f'{p}: icon {icon} not in item_texture.json')
for p in walk(os.path.join(RP, 'attachables'), '.json'):
    d = load(p)['minecraft:attachable']['description']
    check_client(d, p)
    if d['identifier'] not in item_ids:
        errors.append(f'attachable for unknown item {d["identifier"]}')
blk = load(os.path.join(BP, 'blocks', 'grimoire_altar.json'))['minecraft:block']
if blk['components']['minecraft:geometry'] not in geos:
    errors.append('altar geometry missing')
terrain = load(os.path.join(RP, 'textures', 'terrain_texture.json'))['texture_data']
for mi in blk['components']['minecraft:material_instances'].values():
    if mi['texture'] not in terrain:
        errors.append(f'altar texture {mi["texture"]} not in terrain_texture.json')

# recipes / loot reference known items
known = item_ids | {'bc:grimoire_altar'}
for p in list(walk(os.path.join(BP, 'recipes'), '.json')) + list(walk(os.path.join(BP, 'loot_tables'), '.json')):
    for m in re.findall(r'"(bc:[a-z_]+)"', open(p).read()):
        if m not in known and not p.endswith('.json') is False:
            pass
        if m not in known and 'recipes' in p and m != load(p).get('minecraft:recipe_shaped', load(p).get('minecraft:recipe_shapeless', {})).get('description', {}).get('identifier'):
            errors.append(f'{p}: unknown item {m}')

# scripts: particles, sounds, animations, entity types referenced
VANILLA_SOUNDS = {'mob.blaze.shoot', 'mob.blaze.breathe', 'mob.ghast.fireball', 'bucket.empty_water', 'random.splash', 'ambient.weather.thunder',
                  'beacon.activate', 'mob.wither.shoot', 'mob.wither.spawn', 'mob.endermen.portal', 'mob.warden.sonic_boom', 'random.glass',
                  'random.explode', 'random.orb', 'random.anvil_land', 'mob.evocation_illager.cast_spell', 'mob.evocation_illager.prepare_summon',
                  'mob.ravager.bite', 'random.click', 'item.trident.throw', 'random.burp', 'mob.skeleton.say', 'mob.enderdragon.flap',
                  'mob.enderdragon.growl', 'random.pop', 'random.fizz', 'random.levelup', 'fire.ignite', 'dig.wood', 'mob.slime.big', 'random.fuse',
                  'armor.equip_iron', 'random.break', 'random.anvil_use', 'random.chestclosed', 'dig.grass', 'dig.stone', 'mob.zombie.unfect'}
js = ''
for p in walk(os.path.join(BP, 'scripts'), '.js'):
    js += open(p, encoding='utf-8').read()
for m in set(re.findall(r"'(bc:[a-z_]+)'", js)):
    if m in particles or m in bp_ids or m in item_ids or m in block_ids or m in ent_props or m in ent_events:
        continue
    if m in ('bc:attr', 'bc:level', 'bc:xp', 'bc:mana', 'bc:spell', 'bc:anti', 'bc:joined', 'bc:thunder_until', 'bc:shadow_strike',
             'bc:black_form', 'bc:expire', 'bc:altar_logic', 'bc:grimoire_', 'bc:demon_',
             # Abyssal Seas: dynamic-property keys, id prefixes and custom component names
             'bc:sealed', 'bc:fruit', 'bc:fruit_', 'bc:fruit_ab', 'bc:will', 'bc:will_xp', 'bc:will_lv', 'bc:owner', 'bc:power_',
             'bc:bounty_logic', 'bc:bounty', 'bc:fortress_until', 'bc:sea_structs',
             'bc:stars', 'bc:notoriety', 'bc:traps', 'bc:bulwark_until', 'bc:reflect_until', 'bc:tx', 'bc:tz',
             # living world: dynamic-property keys and the /scriptevent id
             'bc:team', 'bc:kname', 'bc:leave_at', 'bc:events', 'bc:event',
             # AI & simulation: knight progression, traits, orders and the world state
             'bc:klv', 'bc:kxp', 'bc:kills', 'bc:prefix', 'bc:skill', 'bc:courage', 'bc:order', 'bc:anchor', 'bc:stance', 'bc:world',
             # companions: the saved party, companion ids and starting bond
             'bc:party', 'bc:cid', 'bc:bond0',
             # v0.3.0: the daily missions
             'bc:missions',
             # v0.5.0: awakened companions, companion brooms, rival squads, sparring, mind control, the dummy's owner
             'bc:awake', 'bc:cbroom', 'bc:rival', 'bc:spar', 'bc:puppet_of', 'bc:dummy_owner',
             # v0.7.0: stolen goods, egg timers, silenced grimoires, the event log and the Mana Eclipse
             'bc:stolen', 'bc:hatch_at', 'bc:silenced_until', 'bc:event_log', 'bc:eclipse_until', 'bc:lair',
             # v0.7.5: elites and their minions, lairs, the Elixir of Haste, feats and titles
             'bc:elite', 'bc:minion', 'bc:lairs', 'bc:haste_until', 'bc:feats', 'bc:title',
             # v1.0.0: the living world
             'bc:incidents', 'bc:incident', 'bc:waygates',
             # v1.1.0: the world seed, regions, landmarks, spawners, omens, wanderers, relics, elites' tiers, maps and journals
             'bc:seed', 'bc:regions', 'bc:region', 'bc:landmarks', 'bc:landmark', 'bc:extra_slots', 'bc:spawners', 'bc:omen', 'bc:relic_',
             'bc:wkind', 'bc:wname', 'bc:wtitle', 'bc:wborn', 'bc:wstay', 'bc:wreq', 'bc:requests', 'bc:track_lm', 'bc:tid', 'bc:text', 'bc:cache',
             'bc:elites', 'bc:etier', 'bc:mimic_loot', 'bc:flyby', 'bc:flee_until'):
        continue
    errors.append(f'script references unknown id {m}')
for m in set(re.findall(r"'(bc:[a-z_]+)'", js)):
    if m in looping:
        errors.append(f'script spawns never-ending emitter {m}')
for m in set(re.findall(r"sound\([^,]+,\s*'([a-z0-9_.]+)'", js)):
    if m not in sounds and m not in VANILLA_SOUNDS:
        errors.append(f'script plays unknown sound {m}')
for m in set(re.findall(r"'(animation\.[a-z0-9_.]+)'", js)):
    if m not in anims:
        errors.append(f'script plays unknown animation {m}')

# lang keys for entities
lang = open(os.path.join(RP, 'texts', 'en_US.lang'), encoding='utf-8').read()
for e in bp_ids:
    if f'entity.{e}.name=' not in lang:
        errors.append(f'missing lang for {e}')

print(f'geometries={len(geos)} animations={len(anims)} particles={len(particles)} items={len(item_ids)} entities={len(bp_ids)} sounds={len(sounds)}')
if errors:
    print('\n'.join('ERROR: ' + e for e in errors))
    sys.exit(1)
print('validation OK')
