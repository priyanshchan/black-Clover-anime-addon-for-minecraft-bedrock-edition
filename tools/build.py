#!/usr/bin/env python3
"""Build the Black Clover: Grimoire Awakening addon.

    python3 tools/build.py            # regenerate packs/ and dist/
    python3 tools/build.py --no-audio # skip re-synthesising sounds

Everything in packs/ is generated: edit the generators in tools/bc or the
scripts in src/scripts and rebuild.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bc import audio, fx, icons, out, packgen  # noqa: E402
from bc import structures  # noqa: E402
from bc import vfx9  # noqa: E402
from bc.data import (ALTAR_WEIGHTS, ATTR_ORDER, ATTRIBUTES, BOND, CAPTAIN_FIRST, CAPTAIN_LAST, COMPANION_HP, COMPANION_LINES,  # noqa: E402
                     COMPANION_XP, ENEMY_KITS, FACTIONS, FRUIT_ORDER, FRUITS, PARTY_MAX, MISSIONS, MISSION_REWARDS, AMULETS, BROOMS,
                     KNIGHT_FIRST, KNIGHT_LAST, KNIGHT_ROBES, MERCHANT, NOTORIETY, NPC_KITS, RANKS, ROBE_PERKS, ROBES, SHOP, SPELLS,
                     SWORDS, WILL_MAX_LEVEL)
from bc.data import (BANTER, DREAMS, EXPEDITIONS, HOMETOWNS, MOOD, PERSONALITIES, RESERVE_MAX, SPEC_LEVEL, SPECS, TACTICS_PARTY,  # noqa: E402
                     TIPS, TRIAL_TITLES, TRIALS, COMPANION_FRUIT_LEVEL)
from bc.data import CONSUMABLES, ELITE_AFFIXES, ELITE_CHANCE, FEATS  # noqa: E402
from bc.data import (ARMOR_COST, ARMOR_EXTRA, ARMOR_MATERIALS, ARMOR_SETS, ARMOR_SLOTS, REINFORCE_COST, REINFORCE_MAX,  # noqa: E402
                     REINFORCE_PCT, RUNES, SCALE_DROPS)
from bc.data import (ELITE_STAR_BONUS, ELITE_TIER_CHANCE, ELITE_TIERS, ENCOUNTERS, ITEM_PREFIX, ITEM_SUFFIX, JOURNALS, CACHE_JOURNALS,  # noqa: E402
                     LANDMARK_BASE, LANDMARK_PER_STAR, LANDMARKS, LEGEND_EPITHETS, LEGEND_SYLLABLES, MARCHES, MIMIC_TOOTH_PRICE, OMEN_CHANCE,
                     OMENS, RARITIES, RARITY_STAR_SHIFT, REALMS, REFORGE_COST, REGION_ADJECTIVES, REGION_FIND_XP, REGION_LANDFORMS, REGION_LORE,
                     REGION_SIZE, REGION_SYLLABLES, REGION_TRAITS, RELIC_AFFIXES, RELIC_SLOTS, RELICS, RUMORS, V11_ITEMS, WANDERER_EPITHET,
                     WANDERER_FETCH, WANDERER_FIRST, WANDERER_GREETINGS, WANDERERS, WEAPON_AFFIXES, WEAPON_BASES, WYVERNS)
from bc import structures11  # noqa: E402
from bc.data import (CAPITAL_DISTANCE, CAPITAL_RADIUS, CAPITAL_SAFE, EGG_FROM_HOARD, EGG_FROM_WYVERN, EGG_HATCH_SECONDS, EGG_NEEDS,  # noqa: E402
                     KINGDOMS, MARCH_KINGDOM, SPOILS_PRICE, V12_ITEMS, WYVERN_BREATH_COOLDOWN, WYVERN_EGGS, WYVERN_FOOD,
                     WYVERN_GROWTH_PER_SECOND, WYVERN_NAMES, WYVERN_RIDE_SPEED, WYVERN_STAGES)
from bc.models import wave4  # noqa: E402

ROOT = out.ROOT
SRC_SCRIPTS = os.path.join(ROOT, 'src', 'scripts')
DIST = os.path.join(ROOT, 'dist')


def clean(keep_sounds):
    for base in (out.BP, out.RP):
        if not os.path.isdir(base):
            continue
        for name in os.listdir(base):
            p = os.path.join(base, name)
            if keep_sounds and base == out.RP and name == 'sounds':
                continue
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)


def gen_script_data():
    data = {
        'attributes': {k: {'name': v['name'], 'color': v['color'], 'leaves': v['leaves'], 'mc': v['mc'],
                           'glyph': icons.glyph(icons.attr_glyph_index(ATTR_ORDER.index(k)))} for k, v in ATTRIBUTES.items()},
        'order': ATTR_ORDER,
        'spells': {k: [dict(id=s[0], name=s[1], mana=s[2], cooldown=s[3], level=s[4], desc=s[5], **({'spec': s[6]} if len(s) > 6 else {}))
                       for s in v] for k, v in SPELLS.items()},
        'swords': {k: v['name'] for k, v in SWORDS.items()},
        'robes': {k: v['name'] for k, v in ROBES.items()},
        'glyphs': {
            'capL': icons.glyph(0x10), 'full': icons.glyph(0x11), 'half': icons.glyph(0x12), 'empty': icons.glyph(0x13), 'capR': icons.glyph(0x14),
            'antiFull': icons.glyph(0x15), 'antiHalf': icons.glyph(0x16), 'antiEmpty': icons.glyph(0x17),
            'clover3': icons.glyph(0x18), 'clover4': icons.glyph(0x19), 'clover5': icons.glyph(0x1A),
            'star': icons.glyph(0x20), 'hourglass': icons.glyph(0x21), 'lock': icons.glyph(0x22),
            'will': icons.glyph(0x36), 'coin': icons.glyph(0x37),
            'arrows': [icons.glyph(0x40 + k) for k in range(8)],
        },
        'fruits': {k: {'name': v['name'], 'color': v['color'], 'mc': v['mc'], 'power': v['power'], 'passive': v['passive'],
                       'glyph': icons.glyph(icons.FRUIT_GLYPH0 + FRUIT_ORDER.index(k)), 'beast': v.get('beast', False),
                       'abilities': [dict(id=a[0], name=a[1], cooldown=a[2], desc=a[3], **({'spec': a[4]} if len(a) > 4 else {}),
                                          **({'will': a[5]} if len(a) > 5 else {}))
                                     for a in v['abilities']]} for k, v in FRUITS.items()},
        'fruitOrder': FRUIT_ORDER,
        'willMax': WILL_MAX_LEVEL,
        'captainFirst': CAPTAIN_FIRST,
        'captainLast': CAPTAIN_LAST,
        'shop': [dict(item=i, count=c, price=p, label=lbl) for i, c, p, lbl in SHOP],
        'robePerks': ROBE_PERKS,
        'ranks': [dict(stars=s_, title=t_) for s_, t_ in RANKS],
        'notoriety': [dict(bounty=b_, title=t_) for b_, t_ in NOTORIETY],
        'tints': {k: i for i, (k, _) in enumerate(wave4.TINTS)},
        'altarWeights': ALTAR_WEIGHTS,
        'npcKits': NPC_KITS,
        'knightFirst': KNIGHT_FIRST,
        'knightLast': KNIGHT_LAST,
        'knightRobes': KNIGHT_ROBES,
        'merchant': [dict(item=i, count=c, price=p, label=lbl) for i, c, p, lbl in MERCHANT],
        'factions': FACTIONS,
        'enemyKits': ENEMY_KITS,
        'missions': [dict(id=i, kind=k, target=t, count=c, title=n, tier=tr) for i, k, t, c, n, tr in MISSIONS],
        'missionRewards': MISSION_REWARDS,
        'amulets': {k: dict(name=n, perk=d) for k, (n, d) in AMULETS.items()},
        'brooms': {k: dict(name=n, speed=sp, mana=m) for k, (n, sp, m) in BROOMS.items()},
        'elites': {k: dict(name=n, mc=c, desc=d) for k, (n, c, d) in ELITE_AFFIXES.items()},
        'eliteChance': ELITE_CHANCE,
        'consumables': {k: dict(name=n, desc=d) for k, (n, d) in CONSUMABLES.items()},
        'feats': [dict(id=i, name=n, desc=d, counter=c, goal=g, stars=st, coins=co, title=t) for i, n, d, c, g, st, co, t in FEATS],
        'armor': {
            'slots': list(ARMOR_SLOTS),
            'sets': {k: dict(name=v['name'], pieces=list(v['pieces']), prot=list(v['prot']), material=v['material'], stars=v['stars'], mc=v['mc'],
                             glow=v['glow'], b2=v['b2'], b4=v['b4']) for k, v in ARMOR_SETS.items()},
            'cost': {k: list(v) for k, v in ARMOR_COST.items()},
            'extra': {k: {sl: [list(x) for x in lst] for sl, lst in v.items()} for k, v in ARMOR_EXTRA.items()},
            'materials': {k: dict(name=n, desc=d, drops={e: list(c) for e, c in dr.items()}) for k, (n, d, dr) in ARMOR_MATERIALS.items()},
            'scaleDrops': {e: list(c) for e, c in SCALE_DROPS.items()},
            'runes': {k: dict(name=n, color=c, desc=d, item=x) for k, (n, c, d, x) in RUNES.items()},
            'reinforceMax': REINFORCE_MAX, 'reinforcePct': REINFORCE_PCT, 'reinforceCost': {str(k): list(v) for k, v in REINFORCE_COST.items()},
        },
        'world': {
            'regionSize': REGION_SIZE, 'findXp': REGION_FIND_XP,
            'realms': [dict(upTo=u, id=i, name=n, mc=c, stars=st, traits=tr) for u, i, n, c, st, tr in REALMS], 'marches': MARCHES,
            'syllables': [list(x) for x in REGION_SYLLABLES], 'adjectives': REGION_ADJECTIVES, 'landforms': REGION_LANDFORMS,
            'traits': {k: dict(name=n, mc=c, desc=d, land=l) for k, (n, c, d, l) in REGION_TRAITS.items()}, 'lore': REGION_LORE,
            'landmarks': {k: dict(v) for k, v in LANDMARKS.items()}, 'landmarkBase': LANDMARK_BASE, 'landmarkPerStar': LANDMARK_PER_STAR,
            'wyverns': {k: dict(name=n, attr=a, color=c, breath=b, land=l) for k, (n, a, c, b, l) in WYVERNS.items()},
            'encounters': {k: dict(chance=c, id=i, msg=m) for k, (c, i, m) in ENCOUNTERS.items()},
            'omenChance': OMEN_CHANCE, 'omens': {k: dict(name=n, mc=c, desc=d) for k, (n, c, d) in OMENS.items()},
            'wanderers': {k: dict(title=t, desc=d, look=lk) for k, (t, d, lk) in WANDERERS.items()}, 'wandererFirst': WANDERER_FIRST,
            'wandererEpithet': WANDERER_EPITHET, 'greetings': WANDERER_GREETINGS, 'rumors': RUMORS,
            'fetch': [list(x) for x in WANDERER_FETCH], 'journals': JOURNALS, 'cacheJournals': CACHE_JOURNALS,
            'items': {k: dict(name=n, desc=d) for k, (n, d) in V11_ITEMS.items()}, 'mimicToothPrice': MIMIC_TOOTH_PRICE,
        },
        'loot': {
            'rarities': [dict(id=i, name=n, mc=c, weight=w, affixes=a, power=pw) for i, n, c, w, a, pw in RARITIES], 'starShift': RARITY_STAR_SHIFT,
            'relics': {k: dict(name=n, desc=d, favour=f) for k, (n, d, f) in RELICS.items()}, 'relicSlots': RELIC_SLOTS,
            'relicAffixes': {k: dict(label=lb, base=b, flag=f) for k, (lb, b, f) in RELIC_AFFIXES.items()},
            'weaponAffixes': {k: dict(label=lb, base=b) for k, (lb, b) in WEAPON_AFFIXES.items()}, 'weaponBases': WEAPON_BASES,
            'prefix': ITEM_PREFIX, 'suffix': ITEM_SUFFIX, 'legendSyllables': [list(x) for x in LEGEND_SYLLABLES], 'epithets': LEGEND_EPITHETS,
            'reforge': {k: list(v) for k, v in REFORGE_COST.items()},
        },
        'dragon': {
            'eggs': WYVERN_EGGS, 'hatchSeconds': EGG_HATCH_SECONDS, 'needs': EGG_NEEDS, 'fromHoard': EGG_FROM_HOARD, 'fromWyvern': EGG_FROM_WYVERN,
            'stages': [dict(name=n, at=a, hp=h, ride=r) for n, a, h, r in WYVERN_STAGES], 'growthPerSecond': WYVERN_GROWTH_PER_SECOND,
            'food': WYVERN_FOOD, 'names': [list(x) for x in WYVERN_NAMES], 'rideSpeed': WYVERN_RIDE_SPEED, 'breathCooldown': WYVERN_BREATH_COOLDOWN,
        },
        'kingdoms': {k: dict(v) for k, v in KINGDOMS.items()}, 'marchKingdom': MARCH_KINGDOM,
        'capital': {'distance': list(CAPITAL_DISTANCE), 'radius': CAPITAL_RADIUS, 'safe': CAPITAL_SAFE},
        'spoilsPrice': SPOILS_PRICE, 'v12Items': {k: dict(name=n, desc=d) for k, (n, d) in V12_ITEMS.items()},
        'eliteTiers': [dict(id=i, name=n, mc=c, affixes=a, boost=b) for i, n, c, a, b in ELITE_TIERS], 'eliteTierChance': ELITE_TIER_CHANCE,
        'eliteStarBonus': ELITE_STAR_BONUS,
        'companion': {'xp': COMPANION_XP, 'hp': COMPANION_HP, 'bond': [dict(at=a, name=n, perk=k) for a, n, k in BOND],
                      'partyMax': PARTY_MAX, 'lines': COMPANION_LINES, 'personalities': PERSONALITIES, 'specs': SPECS, 'specLevel': SPEC_LEVEL,
                      'tactics': {k: dict(name=n, desc=d) for k, (n, d) in TACTICS_PARTY.items()}, 'mood': MOOD,
                      'trials': [dict(kind=k, target=t, count=c, text=x) for k, t, c, x in TRIALS], 'trialTitles': TRIAL_TITLES,
                      'reserveMax': RESERVE_MAX, 'fruitLevel': COMPANION_FRUIT_LEVEL, 'hometowns': HOMETOWNS, 'dreams': DREAMS, 'tips': TIPS, 'banter': BANTER,
                      'expeditions': [dict(id=i, name=n, minutes=mi, level=lv, danger=dg, desc=ds, loot=lt, xp=xp) for i, n, mi, lv, dg, ds, lt, xp in EXPEDITIONS]},
    }
    js = ('// AUTO-GENERATED by tools/build.py from tools/bc/data.py - do not edit by hand.\n'
          f'export const DATA = {json.dumps(data, indent=2, ensure_ascii=True)};\n')
    out.write_text(out.BP, 'scripts/generated/data.js', js)
    out.write_text(out.BP, 'scripts/generated/structures.js', structures.export_js())
    out.write_text(out.BP, 'scripts/generated/landmarks.js', structures11.export_js())


def copy_scripts():
    for dirpath, _, files in os.walk(SRC_SCRIPTS):
        for f in files:
            src = os.path.join(dirpath, f)
            rel = os.path.relpath(src, SRC_SCRIPTS)
            dst = os.path.join(out.BP, 'scripts', rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)


def gen_ui():
    out.write_png(out.RP, f'font/glyph_{icons.GLYPH_PAGE}.png', icons.sea_glyphs(icons.glyph_page()))
    icon = icons.pack_icon(_pack_render())
    for base in (out.BP, out.RP):
        icon.save(out.path(base, 'pack_icon.png'))


def _pack_render():
    """3D render of the anti-magic grimoire + Demon-Slayer Sword for the pack icon."""
    try:
        from bc import render
        from bc.models import items
        import numpy as np
        g = items.sword_geo('demon_slayer_sword')
        g.paint()
        m = render.Model(g.to_json(), g.atlas, emissive=True)
        pose = {'sword': {'rotation': [0, 0, -38], 'position': [6, 2, 0]}}
        sc = render.Scene(256, 256, ss=3)
        sc.add(m, pose)
        sc.render(render.orbit_eye((0, 12, 0), 62, 90, 5), (0, 12, 0), fov=40)
        img = sc.image()
        a = np.asarray(img).astype('float32')
        from bc import tex
        return tex.to_image(tex.glow(a, 3, 0.8))
    except Exception as exc:  # icon still works without the render
        print('pack icon render skipped:', exc)
        return None


def package():
    os.makedirs(DIST, exist_ok=True)
    targets = {
        'BlackClover_GrimoireAwakening.mcaddon': [(out.BP, 'BlackClover_BP'), (out.RP, 'BlackClover_RP')],
        'BlackClover_BP.mcpack': [(out.BP, '')],
        'BlackClover_RP.mcpack': [(out.RP, '')],
    }
    for name, parts in targets.items():
        path = os.path.join(DIST, name)
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            for base, prefix in parts:
                for dirpath, _, files in os.walk(base):
                    for f in sorted(files):
                        full = os.path.join(dirpath, f)
                        rel = os.path.relpath(full, base)
                        z.write(full, os.path.join(prefix, rel) if prefix else rel)
        print(f'  {name}: {os.path.getsize(path) // 1024} KiB')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-audio', action='store_true', help='keep existing sounds instead of re-synthesising')
    ap.add_argument('--no-package', action='store_true')
    args = ap.parse_args()
    print('cleaning packs/ ...')
    clean(keep_sounds=args.no_audio)
    print('models, textures, items, entities ...')
    packgen.build()
    print('particles ...')
    fx.build()
    vfx9.build()
    print('ui ...')
    gen_ui()
    if not args.no_audio:
        print('sounds ...')
        audio.build()
    print('scripts ...')
    gen_script_data()
    copy_scripts()
    if not args.no_package:
        print('packaging ...')
        package()
    print('done.')


if __name__ == '__main__':
    main()
