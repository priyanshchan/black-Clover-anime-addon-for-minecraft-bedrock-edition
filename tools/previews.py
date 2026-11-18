#!/usr/bin/env python3
"""Render README preview images from the real addon models (dev tool).

    python3 tools/previews.py              # every sheet
    python3 tools/previews.py v3_sheet     # just one
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bc import fx, geo, icons, render, tex  # noqa: E402
from bc.data import ATTR_ORDER, ATTRIBUTES, SPELLS  # noqa: E402
from bc.models import items, mobs, spells, world  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'images')
os.makedirs(OUT, exist_ok=True)


def font(size):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def background(w, h, c1='1c0a12', c2='06040a', ring=True):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - w / 2) / w) ** 2 + ((yy - h * 0.55) / h) ** 2) * 1.6
    a = tex.smooth_ramp([tex.rgb(c1), tex.rgb(c2)], np.clip(d, 0, 1))
    a[..., 3] = 255
    img = tex.to_image(a)
    if ring:
        circ = tex.to_image(fx.tex_circle(256)).resize((int(h * 0.95), int(h * 0.95)), Image.LANCZOS)
        arr = np.asarray(circ).astype(np.float32)
        arr[..., :3] = np.array([200, 40, 50])
        arr[..., 3] *= 0.35
        circ = tex.to_image(arr)
        img.alpha_composite(circ, (int(w / 2 - circ.width / 2), int(h * 0.52 - circ.height / 2)))
    return img


def model(g, blend=False):
    g.paint()
    return render.Model(g.to_json(), g.atlas, blend=blend, emissive=True)


def ref_player(skin='steve'):
    g = geo.Geo(f'geometry.ref.{skin}', res=2, atlas_width=128)
    g.skeleton()
    skin_m = tex.Material(tex.ramp('8a5a3c', 'a8714c', 'c08a62', 'd6a27a'), edge=0.85)
    hair = tex.Material(tex.ramp('d8d8d0', 'eeeeea', 'ffffff') if skin == 'anti' else tex.ramp('1c3320', '2a4a2e', '3a6a40'), noise=0.2)
    shirt = tex.Cloth(tex.ramp('101014', '18181e', '22222a', '2e2e38'))
    pants = tex.Material(tex.ramp('1c1c26', '262632', '30303e'))

    def face(a, ctx):
        h, w = a.shape[:2]
        a[int(h * 0.5):int(h * 0.5) + 2, int(w * 0.18):int(w * 0.35), :3] = (40, 160, 70) if skin != 'anti' else (200, 30, 40)
        a[int(h * 0.5):int(h * 0.5) + 2, int(w * 0.65):int(w * 0.82), :3] = (40, 160, 70) if skin != 'anti' else (200, 30, 40)
        a[:int(h * 0.3), :, :3] = hair_col
        return a
    hair_col = (230, 230, 225) if skin == 'anti' else (40, 70, 46)
    g.cube('head', (-4, 24, -4), (8, 8, 8), tex.PerFace(tex.Painted(skin_m, {'north': face}), up=hair))
    g.cube('head', (-4.3, 29, -4.3), (8.6, 3.4, 8.6), hair)
    g.cube('body', (-4, 12, -2), (8, 12, 4), shirt)
    g.cube('rightArm', (-8, 12, -2), (4, 12, 4), tex.PerFace(shirt))
    g.cube('leftArm', (4, 12, -2), (4, 12, 4), shirt)
    g.cube('rightArm', (-8, 12, -2), (4, 3, 4), skin_m)
    g.cube('leftArm', (4, 12, -2), (4, 3, 4), skin_m)
    g.cube('rightLeg', (-3.9, 0, -2), (4, 12, 4), pants)
    g.cube('leftLeg', (-0.1, 0, -2), (4, 12, 4), pants)
    return model(g)


def placed(x, z, yaw, s=1.0, y=0.0):
    m = render.T((x, y, z)) @ render.ry(math.radians(yaw)) @ render.Sc((s, s, s))
    return m


def hero():
    W, H = 1600, 760
    sc = render.Scene(W, H, ss=2)
    A_g = items.grimoire_animations()
    S = items.sword_animations()
    R = items.robe_animations()
    env = {'c.item_slot': 'chest', 'q.modified_move_speed': 0.4}
    # wind mage (left)
    p1 = ref_player('wind')
    pose1 = {'rightarm': {'rotation': [-80, 10, 0]}, 'leftarm': {'rotation': [-20, 0, -10]}}
    for a in (A_g['animation.bc.grimoire.third_person'], A_g['animation.bc.grimoire.page_flip']):
        render.pose_from_anim(a, 0.95, env=env, pose=pose1)
    render.pose_from_anim(R['animation.bc.robe.wear'], 0.3, env=env, pose=pose1)
    root1 = placed(-24, -6, -28)
    sc.add(p1, pose1, root1)
    sc.add(model(items.grimoire_geo('wind')), pose1, root1)
    sc.add(model(items.robe_geo('golden_dawn_robe')), pose1, root1)
    # anti-magic swordsman (right)
    p2 = ref_player('anti')
    pose2 = {'rightarm': {'rotation': [-40, 0, 0]}, 'leftarm': {'rotation': [-10, 0, -5]}, 'body': {'rotation': [0, -10, 0]}}
    render.pose_from_anim(S['animation.bc.demon_slayer_sword.third_person'], 0, pose=pose2)
    render.pose_from_anim(R['animation.bc.robe.wear'], 0.3, env=env, pose=pose2)
    root2 = placed(24, -4, 30)
    sc.add(p2, pose2, root2)
    sc.add(model(items.sword_geo('demon_slayer_sword')), pose2, root2)
    sc.add(model(items.robe_geo('black_bull_robe')), pose2, root2)
    # devil behind
    D = mobs.devil_animations()
    dpose = {}
    for a in (D['animation.bc.devil.hover'], D['animation.bc.devil.wings']):
        render.pose_from_anim(a, 0.4, pose=dpose)
    render.pose_from_anim(D['animation.bc.devil.attack'], 0.12, pose=dpose)
    sc.add(model(mobs.devil_geo()), dpose, placed(0, 50, 0, 1.0, 0))
    # spells in flight
    for name, x, y, z, yaw in (('wind_blade', -10, 32, -14, -60), ('fireball', -40, 46, 20, 30), ('anti_magic_slash', 12, 20, -16, 60),
                               ('thunder_spear', 44, 50, 24, -150), ('light_sword', -46, 22, 10, 160), ('dark_crescent', 40, 18, 22, 20)):
        g, kind, anim = spells.ALL[name]()
        pose = {}
        for a in anim.values():
            render.pose_from_anim(a, 0.3, pose=pose)
        sc.add(model(g, blend=(kind == 'blend')), pose, placed(x, z, yaw, 1.0, y))
    sc.render(render.orbit_eye((0, 31, 14), 118, 0, 7), (0, 31, 14), fov=42)
    img = background(W, H)
    img.alpha_composite(sc.image())
    draw = ImageDraw.Draw(img)
    draw.text((40, 30), 'BLACK CLOVER', font=font(64), fill=(235, 235, 235, 255))
    draw.text((44, 104), 'Grimoire Awakening - Minecraft Bedrock addon', font=font(26), fill=(220, 70, 80, 255))
    img.convert('RGB').save(os.path.join(OUT, 'hero.png'), optimize=True)


def grid(entries, cols, cell, name, title_txt=None, bg=('22222c', '101016')):
    rows = (len(entries) + cols - 1) // cols
    top = 60 if title_txt else 0
    W, H = cols * cell, rows * cell + top
    img = background(W, H, *bg, ring=False)
    draw = ImageDraw.Draw(img)
    if title_txt:
        draw.text((20, 14), title_txt, font=font(30), fill=(235, 235, 235, 255))
    for i, (label, m, pose, yaw, pitch, dist_mul) in enumerate(entries):
        pts = np.concatenate([q[0] for q in m.quads(pose)])
        c = (pts.min(0) + pts.max(0)) / 2
        r = np.linalg.norm(pts.max(0) - pts.min(0))
        sc = render.Scene(cell, cell, ss=2)
        sc.add(m, pose)
        sc.render(render.orbit_eye(tuple(c), r * dist_mul, yaw, pitch), tuple(c), fov=40)
        x, y = (i % cols) * cell, (i // cols) * cell + top
        img.alpha_composite(sc.image(), (x, y))
        draw.text((x + 12, y + cell - 34), label, font=font(18), fill=(225, 225, 225, 255))
    img.convert('RGB').save(os.path.join(OUT, name), optimize=True)


def spells_sheet():
    names = {'wind_blade': 'Gale Blade', 'fireball': 'Flame Bullet', 'flame_lion': 'Inferno Lion', 'water_dragon': 'Sea Dragon',
             'tornado': 'Tempest Tornado', 'thunder_spear': 'Thunder Spear', 'light_sword': 'Sword of Light', 'dark_crescent': 'Dark Crescent',
             'black_hole': 'Abyssal Hole', 'ice_spear': 'Ice Spear', 'ice_prison': 'Frost Prison', 'anti_magic_slash': 'Black Meteorite'}
    entries = []
    for k, label in names.items():
        g, kind, anim = spells.ALL[k]()
        pose = {}
        for a in anim.values():
            render.pose_from_anim(a, 0.37, pose=pose)
        entries.append((label, model(g, blend=(kind == 'blend')), pose, 35, 22, 1.5))
    grid(entries, 4, 300, 'spells.png', 'Spell models')


def gear_sheet():
    entries = []
    A = items.grimoire_animations()
    for attr in ATTR_ORDER:
        g = items.grimoire_geo(attr)
        pose = {'tp_root': {'scale': [1, 1, 1]}, 'fp_root': {'scale': [0, 0, 0]}}
        render.pose_from_anim(A['animation.bc.grimoire.page_flip'], 0.9, pose=pose)
        pose['tp_book'] = {'rotation': [40, 20, 0]}
        entries.append((f"{ATTRIBUTES[attr]['name']} Grimoire", model(g), pose, 20, 35, 1.6))
    for k, label in (('demon_slayer_sword', 'Demon-Slayer Sword'), ('demon_dweller_sword', 'Demon-Dweller Sword'), ('demon_destroyer_sword', 'Demon-Destroyer Sword')):
        entries.append((label, model(items.sword_geo(k)), {'sword': {'rotation': [0, 0, -30]}}, 90, 5, 1.3))
    alt = world.altar_geo()
    entries.append(('Grimoire Altar', model(alt), {}, 30, 28, 1.5))
    grid(entries, 4, 300, 'gear.png', 'Grimoires, demon swords & the Grimoire Altar')


def mobs_sheet():
    D = mobs.devil_animations()
    dp = {}
    for a in (D['animation.bc.devil.hover'], D['animation.bc.devil.wings']):
        render.pose_from_anim(a, 0.4, pose=dp)
    A = mobs.disciple_animations()
    cp = {}
    render.pose_from_anim(A['animation.bc.dark_disciple.idle'], 0.3, pose=cp)
    render.pose_from_anim(A['animation.bc.dark_disciple.cast'], 0.3, pose=cp)
    entries = [('Devil (boss)', model(mobs.devil_geo()), dp, 25, 10, 1.35), ('Dark Disciple', model(mobs.disciple_geo()), cp, 30, 10, 1.5)]
    grid(entries, 2, 520, 'mobs.png', 'Enemies')


def robes_sheet():
    R = items.robe_animations()
    env = {'c.item_slot': 'chest', 'q.modified_move_speed': 0.5}
    entries = []
    for rid, label in (('black_bull_robe', 'Black Bull Robe'), ('golden_dawn_robe', 'Golden Dawn Robe'), ('crimson_lion_robe', 'Crimson Lion Robe')):
        pose = {}
        render.pose_from_anim(R['animation.bc.robe.wear'], 0.3, env=env, pose=pose)
        g = items.robe_geo(rid)
        p = ref_player()
        # combine player + robe into a single scene by rendering both models
        entries.append((label, (p, model(g)), pose, 160, 12, 1.45))
    cols, cell = 3, 360
    img = background(cols * cell, cell + 60, '22222c', '101016', ring=False)
    draw = ImageDraw.Draw(img)
    draw.text((20, 14), 'Magic Knight robes', font=font(30), fill=(235, 235, 235, 255))
    for i, (label, (pm, rm), pose, yaw, pitch, dm) in enumerate(entries):
        sc = render.Scene(cell, cell, ss=2)
        sc.add(pm, pose)
        sc.add(rm, pose)
        sc.render(render.orbit_eye((0, 16, 0), 58, yaw, pitch), (0, 16, 0), fov=40)
        img.alpha_composite(sc.image(), (i * cell, 60))
        draw.text((i * cell + 12, 60 + cell - 34), label, font=font(18), fill=(225, 225, 225, 255))
    img.convert('RGB').save(os.path.join(OUT, 'robes.png'), optimize=True)


def hud_mock():
    """What the action-bar HUD looks like (glyph font + text)."""
    page = icons.glyph_page()
    cell = lambda i: tex.to_image(page[(i // 16) * 16:(i // 16) * 16 + 16, (i % 16) * 16:(i % 16) * 16 + 16]).resize((32, 32), Image.NEAREST)
    img = background(900, 150, '2a3a2a', '101810', ring=False)
    draw = ImageDraw.Draw(img)
    f = font(22)
    x, y = 30, 30
    img.alpha_composite(cell(0), (x, y))
    x += 40
    draw.text((x, y + 2), 'Gale Blades', font=f, fill=(111, 224, 160, 255))
    x += 150
    draw.text((x, y + 2), '[1/4]', font=f, fill=(110, 110, 110, 255))
    x += 72
    for i in [0x10] + [0x11] * 8 + [0x12] + [0x13] * 3 + [0x14]:
        img.alpha_composite(cell(i), (x, y))
        x += 14 if i != 0x10 else 6
    x += 30
    draw.text((x, y + 2), '96/148', font=f, fill=(85, 255, 255, 255))
    x += 90
    img.alpha_composite(cell(0x20), (x, y))
    draw.text((x + 36, y + 2), '5', font=f, fill=(255, 255, 85, 255))
    y = 90
    x = 30
    img.alpha_composite(cell(7), (x, y))
    draw.text((x + 40, y + 2), 'Demon-Slayer Sword  [1/4]', font=f, fill=(170, 170, 170, 255))
    x = 412
    for i in [0x10] + [0x15] * 10 + [0x16] + [0x17] + [0x14]:
        img.alpha_composite(cell(i), (x, y))
        x += 14 if i != 0x10 else 6
    draw.text((x + 30, y + 2), '84%', font=f, fill=(255, 85, 85, 255))
    img.convert('RGB').save(os.path.join(OUT, 'hud.png'), optimize=True)


def icons_strip():
    ims = [items.grimoire_icon(a) for a in ATTR_ORDER] + [items.sword_icon(k) for k in ('demon_slayer_sword', 'demon_dweller_sword', 'demon_destroyer_sword')]
    ims += [items.robe_icon(k) for k in ('black_bull_robe', 'golden_dawn_robe', 'crimson_lion_robe')] + list(icons.misc_icons().values())
    img = background(len(ims) * 76 + 20, 96, '22222c', '101016', ring=False)
    for i, a in enumerate(ims):
        img.alpha_composite(tex.to_image(a).resize((64, 64), Image.NEAREST), (16 + i * 76, 16))
    img.convert('RGB').save(os.path.join(OUT, 'icons.png'), optimize=True)


def seas_sheet():
    from bc.models import sea as seam
    entries = []
    ship_pose = {}
    for a in seam.ship_animations().values():
        render.pose_from_anim(a, 0.4, env={'q.modified_move_speed': 0.5}, pose=ship_pose)
    entries.append(('Sailing Ship', model(seam.ship_geo()), ship_pose, 35, 18, 1.15))
    lp = {}
    render.pose_from_anim(seam.leviathan_animations()['animation.bc.leviathan.swim'], 0.4, pose=lp)
    entries.append(('Abyssal Leviathan (boss)', model(seam.leviathan_geo()), lp, 50, 30, 1.25))
    rp = {}
    render.pose_from_anim(seam.humanoid_animations('sea_raider')['animation.bc.sea_raider.idle'], 0.3, pose=rp)
    entries.append(('Sea Raider', model(seam.raider_geo()), rp, 30, 10, 1.5))
    cp = {}
    render.pose_from_anim(seam.humanoid_animations('raider_captain')['animation.bc.raider_captain.cast'], 0.3, pose=cp)
    entries.append(('Raider Captain', model(seam.captain_geo()), cp, 30, 10, 1.5))
    entries.append(('Bounty Board', model(seam.bounty_board_geo()), {}, 20, 10, 1.4))
    sp = {}
    render.pose_from_anim(mobs.disciple_animations()['animation.bc.dark_disciple.idle'], 0.3, pose=sp)
    entries.append(('Shade Soldier', model(mobs.disciple_geo('shade')), sp, 30, 10, 1.5))
    grid(entries, 3, 340, 'seas.png', 'The Abyssal Seas')


def fruits_strip():
    ic = icons.sea_icons()
    keys = [f'fruit_{k}' for k in ('ember', 'stone', 'gravity', 'shadow', 'bloom', 'quicksilver')] + \
           [f'power_{k}' for k in ('ember', 'stone', 'gravity', 'shadow', 'bloom', 'quicksilver')] + \
           ['doubloon', 'cannonball', 'ship_kit', 'leviathan_lure', 'leviathan_scale']
    img = background(len(keys) * 76 + 20, 96, '0b2b3a', '06121a', ring=False)
    for i, k in enumerate(keys):
        img.alpha_composite(tex.to_image(ic[k]).resize((64, 64), Image.NEAREST), (16 + i * 76, 16))
    img.convert('RGB').save(os.path.join(OUT, 'sea_items.png'), optimize=True)
    # fruit power auras on the arm
    from bc.models import sea as seam
    W = 6 * 220
    out = background(W, 260, '0b2b3a', '06121a', ring=False)
    d = ImageDraw.Draw(out)
    for i, fid in enumerate(('ember', 'stone', 'gravity', 'shadow', 'bloom', 'quicksilver')):
        g = seam.power_geo(fid)
        m = model(g)
        pose = {'rightarm': {'rotation': [-70, 0, 0]}}
        render.pose_from_anim(seam.power_animations()['animation.bc.power.aura'], 0.3, pose=pose)
        arm = geo.Geo('geometry.ref.arm', res=1, atlas_width=64)
        arm.skeleton()
        arm.cube('rightArm', (-8, 12, -2), (4, 12, 4), tex.Material(tex.ramp('8a5a3c', 'a8714c', 'c08a62', 'd6a27a')))
        sc = render.Scene(220, 220, ss=2)
        sc.add(model(arm), pose)
        sc.add(m, pose)
        sc.render(render.orbit_eye((6, 15, -7), 40, 35, 15), (6, 15, -7), fov=40)
        out.alpha_composite(sc.image(), (i * 220, 10))
        d.text((i * 220 + 14, 228), {'ember': 'Ember Body', 'stone': 'Stone Body', 'gravity': 'Gravity Grip', 'shadow': 'Shadow Grasp',
                                     'bloom': 'Bloom Touch', 'quicksilver': 'Quicksilver Arm'}[fid], font=font(18), fill=(225, 225, 225, 255))
    out.convert('RGB').save(os.path.join(OUT, 'powers.png'), optimize=True)


def wave3_sheet():
    from bc.models import grand
    entries = []
    for k, label in (('earth_golem', 'Earth Golem (Earth magic)'), ('dungeon_golem', 'Dungeon Guardian')):
        pose = {}
        render.pose_from_anim(grand.golem_animations(k)[f'animation.bc.{k}.idle'], 0.3, pose=pose)
        entries.append((label, model(grand.golem_geo(k)), pose, 30, 10, 1.4))
    pose = {}
    for a in grand.imp_animations().values():
        render.pose_from_anim(a, 0.2, pose=pose)
    entries.append(('Imp', model(grand.imp_geo()), pose, 30, 10, 1.5))
    for k, label in (('tidewatch_sentinel', 'Tidewatch Sentinel'), ('tidewatch_commodore', 'Tidewatch Commodore')):
        pose = {}
        render.pose_from_anim(grand.navy_animations(k)[f'animation.bc.{k}.idle'], 0.3, pose=pose)
        entries.append((label, model(grand.navy_geo(k)), pose, 30, 10, 1.5))
    g, _, a = grand.warp_gate()
    pose = {}
    render.pose_from_anim(a['animation.bc.warp_gate.spin'], 1.0, pose=pose)
    entries.append(('Warp Gate (Spatial magic)', model(g), pose, 20, 10, 1.4))
    pose = {}
    render.pose_from_anim(mobs.disciple_animations()['animation.bc.dark_disciple.idle'], 0.3, pose=pose)
    entries.append(('Mirror Image (Mirror magic)', model(mobs.disciple_geo('mirror')), pose, 30, 10, 1.5))
    for k, label in (('cutlass', 'Cutlass'), ('flintlock', 'Flintlock Pistol'), ('harpoon', 'Grappling Harpoon')):
        entries.append((label, model(grand.weapon_geo(k)), {'weapon': {'rotation': [0, 0, -35]}}, 90, 5, 1.2))
    grid(entries, 5, 300, 'wave3.png', 'Magic, monsters, the Tidewatch & pirate arms')
    # beast forms on a player
    out_img = background(900, 330, '1a1410', '0a0806', ring=False)
    d = ImageDraw.Draw(out_img)
    d.text((20, 14), 'Beast fruits: Wolf Form & Hawk Form', font=font(26), fill=(235, 235, 235, 255))
    p = ref_player()
    for i, (fid, yaw) in enumerate((('wolf', 25), ('wolf', 160), ('hawk', 25), ('hawk', 160))):
        g, anim = grand.beast_geo(fid)
        pose = {}
        for a in anim.values():
            render.pose_from_anim(a, 0.2, pose=pose)
        sc = render.Scene(225, 280, ss=2)
        sc.add(p, pose)
        sc.add(model(g), pose)
        sc.render(render.orbit_eye((0, 18, 0), 66, yaw, 10), (0, 18, 0), fov=40)
        out_img.alpha_composite(sc.image(), (i * 225, 50))
    out_img.convert('RGB').save(os.path.join(OUT, 'beasts.png'), optimize=True)
    # new grimoires and robes
    from bc.data import ATTR_ORDER, ROBES
    ims = [items.grimoire_icon(a) for a in ATTR_ORDER[8:]] + [items.robe_icon(r) for r in list(ROBES)[3:]] + \
          [icons.fruit_icon(f) for f in ('frost', 'barrier', 'wolf', 'hawk')] + list(grand.wave3_icons().values())
    img = background(len(ims) * 76 + 20, 96, '22222c', '101016', ring=False)
    for i, a in enumerate(ims):
        img.alpha_composite(tex.to_image(a).resize((64, 64), Image.NEAREST), (16 + i * 76, 16))
    img.convert('RGB').save(os.path.join(OUT, 'wave3_items.png'), optimize=True)


def wave4_sheet():
    """A living world: knights, merchant, constructs, giant bosses, beast forms, new grimoires and fruits."""
    from bc.data import ATTR_ORDER, FRUIT_ORDER, KNIGHT_ROBES
    from bc.models import grand, sea as seam, wave4
    entries = []
    ka = wave4.knight_animations()
    for i, (rid, yaw) in enumerate(((KNIGHT_ROBES[0], 30), (KNIGHT_ROBES[1], 200), (KNIGHT_ROBES[4], 160))):
        pose = {}
        render.pose_from_anim(ka['animation.bc.magic_knight.cast' if i == 0 else 'animation.bc.magic_knight.idle'], 0.3, pose=pose)
        entries.append(('Magic Knight' if i == 0 else 'Magic Knight (robe variant)', model(wave4.knight_geo(rid, i)), pose, yaw, 10, 1.5))
    entries.append(('Travelling Magic Merchant', model(wave4.merchant_geo()), {}, 150, 10, 1.5))
    for k, label in (('sand', 'Sand Construct'), ('crystal', 'Crystal Construct')):
        entries.append((label, model(wave4.construct_geo(k)), {}, 30, 10, 1.4))
    dp = {}
    for a in mobs.devil_animations().values():
        if a.get('loop'):
            render.pose_from_anim(a, 0.3, pose=dp)
    entries.append(('The Archdevil (boss)', model(mobs.devil_geo(True)), dp, 20, 10, 1.35))
    cp = {}
    render.pose_from_anim(grand.golem_animations('stone_colossus')['animation.bc.stone_colossus.idle'], 0.3, pose=cp)
    entries.append(('The Stone Colossus (boss)', model(wave4.colossus_geo()), cp, 30, 10, 1.35))
    kp = {}
    render.pose_from_anim(wave4.kraken_animations()['animation.bc.storm_kraken.swim'], 0.7, pose=kp)
    entries.append(('The Storm Kraken (boss)', model(wave4.kraken_geo()), kp, 30, 25, 1.3))
    g = seam.ship_geo()
    g.identifier = 'geometry.bc.phantom_galleon'
    g.paint()
    g.atlas = wave4.ghostify(g.atlas)
    gp = {}
    render.pose_from_anim(wave4.galleon_animations()['animation.bc.phantom_galleon.drift'], 0.4, pose=gp)
    entries.append(('The Phantom Galleon (boss)', render.Model(g.to_json(), g.atlas, emissive=True), gp, 35, 18, 1.15))
    entries.append(('War Table', model(wave4.war_table_geo()), {}, 30, 35, 1.25))
    gate, _, ga = grand.warp_gate()
    gate.paint()
    gate.atlas = wave4.recolor_devil(gate.atlas)
    pose = {}
    render.pose_from_anim(ga['animation.bc.warp_gate.spin'], 1.0, pose=pose)
    entries.append(('Devil Gate (world event)', render.Model(gate.to_json(), gate.atlas, emissive=True), pose, 20, 10, 1.4))
    grid(entries, 4, 300, 'wave4.png', 'A living world: knights, giants, events & the War Table')
    # beast forms
    out_img = background(1350, 330, '1a1410', '0a0806', ring=False)
    d = ImageDraw.Draw(out_img)
    d.text((20, 14), 'Beast fruits: Bear, Tiger & Wyvern forms', font=font(26), fill=(235, 235, 235, 255))
    p = ref_player()
    for i, (fid, yaw) in enumerate((('bear', 25), ('bear', 160), ('tiger', 25), ('tiger', 160), ('wyvern', 25), ('wyvern', 160))):
        g, anim = grand.beast_geo(fid)
        pose = {}
        for a in anim.values():
            render.pose_from_anim(a, 0.2, pose=pose)
        sc = render.Scene(225, 280, ss=2)
        sc.add(p, pose)
        sc.add(model(g), pose)
        sc.render(render.orbit_eye((0, 18, 0), 66, yaw, 10), (0, 18, 0), fov=40)
        out_img.alpha_composite(sc.image(), (i * 225, 50))
    out_img.convert('RGB').save(os.path.join(OUT, 'beasts4.png'), optimize=True)
    # mana bolt shapes in a few tints
    bolts = background(8 * 150, 170, '101018', '06060a', ring=False)
    geo_file = wave4.bolt_geometry_file()['minecraft:geometry']
    for i, (shape, tint) in enumerate([(s, t) for s in range(4) for t in (12, 17, 23)][:8]):
        j = {'format_version': '1.16.0', 'minecraft:geometry': [geo_file[shape]]}
        m = render.Model(j, wave4.bolt_tint_texture(wave4.TINTS[tint][1]), emissive=True)
        sc = render.Scene(150, 150, ss=2)
        sc.add(m, {})
        sc.render(render.orbit_eye((0, 0, 0), 26, 60, 25), (0, 0, 0), fov=40)
        bolts.alpha_composite(sc.image(), (i * 150, 10))
    bolts.convert('RGB').save(os.path.join(OUT, 'bolts.png'), optimize=True)
    # new grimoires, fruits and items
    ims = [items.grimoire_icon(a) for a in ATTR_ORDER[12:]] + [icons.fruit_icon(f) for f in FRUIT_ORDER[10:]] + list(wave4.wave4_icons().values())
    cols = 16
    rows = (len(ims) + cols - 1) // cols
    img = background(cols * 76 + 20, rows * 76 + 20, '22222c', '101016', ring=False)
    for i, a in enumerate(ims):
        img.alpha_composite(tex.to_image(a).resize((64, 64), Image.NEAREST), (16 + (i % cols) * 76, 16 + (i // cols) * 76))
    img.convert('RGB').save(os.path.join(OUT, 'wave4_items.png'), optimize=True)


def v2_sheet():
    """v0.2.0: new enemies, the Fallen Captain, companion animations, beast forms, grimoires, fruits and items."""
    from bc.data import ATTR_ORDER, FRUIT_ORDER, KNIGHT_ROBES
    from bc.models import grand, v2, wave4
    entries = []
    ga = v2.gun_animations('raider_gunner')
    pose = {}
    render.pose_from_anim(ga['animation.bc.raider_gunner.aim'], 0.5, pose=pose)
    entries.append(('Raider Gunner (aiming)', model(v2.gunner_geo()), pose, 35, 10, 1.5))
    ma = v2.gun_animations('tidewatch_marksman')
    pose = {}
    render.pose_from_anim(ma['animation.bc.tidewatch_marksman.aim'], 0.5, pose=pose)
    entries.append(('Tidewatch Marksman', model(v2.marksman_geo()), pose, 150, 10, 1.5))
    pose = {}
    render.pose_from_anim(v2.hellhound_animations()['animation.bc.hellhound.walk'], 0.3, env={'q.modified_move_speed': 1.0, 'q.modified_distance_moved': 2.0}, pose=pose)
    entries.append(('Hellhound', model(v2.hellhound_geo()), pose, 40, 15, 1.3))
    pose = {}
    render.pose_from_anim(v2.wraith_animations()['animation.bc.mana_wraith.cast'], 0.4, pose=pose)
    entries.append(('Mana Wraith', model(v2.wraith_geo()), pose, 30, 10, 1.4))
    fa = v2.fallen_captain_animations()
    pose = {}
    render.pose_from_anim(fa['animation.bc.fallen_captain.idle'], 0.3, pose=pose)
    entries.append(('The Fallen Captain (boss)', model(v2.fallen_captain_geo()), pose, 30, 10, 1.5))
    pose = {}
    render.pose_from_anim(fa['animation.bc.fallen_captain.slash'], 0.12, pose=pose)
    entries.append(('Fallen Captain: slash', model(v2.fallen_captain_geo()), pose, 150, 10, 1.5))
    ke = v2.knight_extra_animations()
    for i, (nm, label) in enumerate((('cast_raise', 'Companion: cast'), ('channel', 'Companion: channel'), ('salute', 'Companion: salute'), ('sit', 'Companion: resting'))):
        pose = {}
        render.pose_from_anim(ke[f'animation.bc.magic_knight.{nm}'], 0.4, pose=pose)
        entries.append((label, model(wave4.knight_geo(KNIGHT_ROBES[[0, 4, 1, 6][i]], i)), pose, 30, 10, 1.5))
    grid(entries, 5, 280, 'v020.png', 'v0.2.0: new enemies, the Fallen Captain & companions')
    out_img = background(1800, 330, '1a1410', '0a0806', ring=False)
    d = ImageDraw.Draw(out_img)
    d.text((20, 14), 'Beast fruits: Lion, Shark, Phoenix & Spider forms', font=font(26), fill=(235, 235, 235, 255))
    p = ref_player()
    for i, (fid, yaw) in enumerate([(f, y) for f in ('lion', 'shark', 'phoenix', 'spider') for y in (25, 160)]):
        g, anim = grand.beast_geo(fid)
        pose = {}
        for a in anim.values():
            render.pose_from_anim(a, 0.2, pose=pose)
        sc = render.Scene(225, 280, ss=2)
        sc.add(p, pose)
        sc.add(model(g), pose)
        sc.render(render.orbit_eye((0, 18, 0), 66, yaw, 10), (0, 18, 0), fov=40)
        out_img.alpha_composite(sc.image(), (i * 225, 50))
    out_img.convert('RGB').save(os.path.join(OUT, 'beasts020.png'), optimize=True)
    ims = [items.grimoire_icon(a) for a in ATTR_ORDER[24:]] + [icons.fruit_icon(f) for f in FRUIT_ORDER[22:]] + list(v2.v2_icons().values())
    img = background(len(ims) * 76 + 20, 96, '22222c', '101016', ring=False)
    for i, a in enumerate(ims):
        img.alpha_composite(tex.to_image(a).resize((64, 64), Image.NEAREST), (16 + i * 76, 16))
    img.convert('RGB').save(os.path.join(OUT, 'items020.png'), optimize=True)


def v3_sheet():
    """v0.3.0: brooms, the Mission Board, Rogue Mages, the Witch Sisters, the Bone Dragon and the new items."""
    from bc.models import v3, wave4
    entries = []
    ka = wave4.knight_animations()
    pose = {}
    render.pose_from_anim(ka['animation.bc.magic_knight.idle'], 0.3, pose=pose)
    for t, label in (('broom', 'Magic Broom'), ('swift_broom', 'Swift Broom')):
        entries.append((label, model(v3.broom_geo(t)), {}, 45, 25, 1.2))
    entries.append(('Mission Board', model(v3.mission_board_geo()), {}, 20, 10, 1.3))
    for v, _ in v3.ROGUE_COLORS[:2]:
        entries.append((f'Rogue Mage ({v})', model(v3.rogue_geo(v)), pose, 30, 10, 1.5))
    for k, label in (('frost_witch', 'The Frost Witch'), ('ember_witch', 'The Ember Witch')):
        wp = {}
        render.pose_from_anim(v3.witch_animations(k)[f'animation.bc.{k}.cast'], 0.4, pose=wp)
        entries.append((label, model(v3.witch_geo(k)), wp, 30, 10, 1.4))
    da = v3.bone_dragon_animations()
    dp = {}
    render.pose_from_anim(da['animation.bc.bone_dragon.fly'], 0.3, pose=dp)
    entries.append(('The Bone Dragon', model(v3.bone_dragon_geo()), dp, 35, 20, 1.2))
    dp = {}
    render.pose_from_anim(da['animation.bc.bone_dragon.breath'], 0.8, pose=dp)
    entries.append(('Bone Dragon: breath', model(v3.bone_dragon_geo()), dp, 100, 15, 1.2))
    grid(entries, 5, 280, 'v030.png', 'v0.3.0: brooms, Rogue Mages, the Witch Sisters & the Bone Dragon')
    ims = list(v3.v3_icons().values())
    img = background(len(ims) * 76 + 20, 96, '22222c', '101016', ring=False)
    for i, a in enumerate(ims):
        img.alpha_composite(tex.to_image(a).resize((64, 64), Image.NEAREST), (16 + i * 76, 16))
    img.convert('RGB').save(os.path.join(OUT, 'items030.png'), optimize=True)


def v5_sheet():
    """v0.5.0: companion emotes and riding, the Squad Banner, the Training Dummy, the Soul Puppeteer and its marionettes."""
    from bc.data import ATTR_ORDER, KNIGHT_ROBES
    from bc.models import v5, wave4
    entries = []
    ka = v5.knight_v5_animations()
    for i, (nm, label) in enumerate((('kneel', 'Reviving a friend'), ('taunt', 'Vanguard: taunt'), ('guard', 'Warden: guard'),
                                     ('point', 'Ranger: mark'), ('victory', 'Victory'), ('sleep', 'Camp: sleeping'))):
        pose = {}
        render.pose_from_anim(ka[f'animation.bc.magic_knight.{nm}'], 0.5, pose=pose)
        g = model(wave4.knight_geo(KNIGHT_ROBES[i % len(KNIGHT_ROBES)], i % len(KNIGHT_ROBES)))
        entries.append((label, g, pose, 35, 10, 1.4))
    entries.append(('Squad Banner', model(v5.squad_banner_geo()), {}, 25, 10, 1.1))
    entries.append(('Training Dummy', model(v5.training_dummy_geo()), {}, 25, 10, 1.3))
    pa = v5.puppeteer_animations()
    pose = {}
    render.pose_from_anim(pa['animation.bc.soul_puppeteer.float'], 0.3, pose=pose)
    entries.append(('The Soul Puppeteer', model(v5.puppeteer_geo()), pose, 25, 10, 1.0))
    pose = {}
    render.pose_from_anim(v5.puppet_animations()['animation.bc.puppet.walk'], 0.1, env={'q.anim_time': 0.1}, pose=pose)
    entries.append(('Marionette', model(v5.puppet_geo()), pose, 30, 10, 1.6))
    grid(entries, 5, 280, 'v050.png', 'v0.5.0: the companion update & the Soul Puppeteer')
    ims = [items.grimoire_icon(a) for a in ATTR_ORDER[32:]] + list(v5.v5_icons().values())
    img = background(len(ims) * 76 + 20, 96, '22222c', '101016', ring=False)
    for i, a in enumerate(ims):
        img.alpha_composite(tex.to_image(a).resize((64, 64), Image.NEAREST), (16 + i * 76, 16))
    img.convert('RGB').save(os.path.join(OUT, 'items050.png'), optimize=True)


def v7_sheet():
    """v0.7.0: the Bandit Brotherhood, the Shadow Assassin, the Cultist, the Hive and three new bosses."""
    from bc.models import v7
    e = []
    ba = v7.bandit_animations('bandit')
    for kind, label in (('brawler', 'Bandit'), ('archer', 'Bandit Archer'), ('thief', 'Bandit Thief')):
        pose = {}
        render.pose_from_anim(ba['animation.bc.bandit.idle'], 0.3, pose=pose)
        e.append((label, model(v7.bandit_geo(kind)), pose, 30, 10, 1.5))
    pose = {}
    render.pose_from_anim(v7.bandit_king_animations()['animation.bc.bandit_king.slash'], 0.15, pose=pose)
    e.append(('The Bandit King', model(v7.bandit_king_geo()), pose, 30, 10, 1.5))
    pose = {}
    render.pose_from_anim(v7.assassin_animations()['animation.bc.shadow_assassin.idle'], 0.3, pose=pose)
    e.append(('Shadow Assassin', model(v7.assassin_geo()), pose, 30, 10, 1.5))
    pose = {}
    render.pose_from_anim(v7.cultist_animations()['animation.bc.cultist.ritual'], 0.3, pose=pose)
    e.append(('Cultist (ritual)', model(v7.cultist_geo()), pose, 30, 10, 1.5))
    pose = {}
    render.pose_from_anim(v7.drone_animations()['animation.bc.hive_drone.idle'], 0.3, pose=pose)
    e.append(('Hive Drone', model(v7.drone_geo()), pose, 40, 20, 1.6))
    e.append(('Hive Egg', model(v7.egg_geo()), {}, 30, 15, 1.6))
    pose = {}
    render.pose_from_anim(v7.queen_animations()['animation.bc.hive_queen.screech'], 0.5, pose=pose)
    e.append(('The Hive Queen', model(v7.queen_geo()), pose, 40, 15, 1.0))
    pose = {}
    render.pose_from_anim(v7.devourer_animations()['animation.bc.grimoire_devourer.chomp'], 0.25, pose=pose)
    e.append(('The Grimoire Devourer', model(v7.devourer_geo()), pose, 30, 15, 1.0))
    grid(e, 5, 280, 'v070.png', 'v0.7.0: bandits, assassins, cultists, the Hive & three new bosses')


def v8_sheet():
    """v0.8.0: the eight armour sets on a player, with the materials, runes and the Magic Forge."""
    from bc.data import ARMOR_SETS, ARMOR_SLOTS
    from bc.models import v8
    cell = 300
    sets = list(ARMOR_SETS)
    cols = 4
    rows = (len(sets) + cols - 1) // cols
    top = 60
    strip = 110
    W, H = cols * cell, top + rows * cell + strip
    img = background(W, H, '22222c', '101016', ring=False)
    draw = ImageDraw.Draw(img)
    draw.text((20, 14), 'v0.8.0: eight armour sets, the Magic Forge, runes & materials', font=font(30), fill=(235, 235, 235, 255))
    env = {'c.item_slot': 'chest', 'q.modified_move_speed': 0.35, 'q.life_time': 0.4, 'q.is_sneaking': 0.0}
    for i, sid in enumerate(sets):
        sc = render.Scene(cell, cell, ss=2)
        pose = {'rightarm': {'rotation': [-25, 0, 8]}, 'leftarm': {'rotation': [15, 0, -8]},
                'rightleg': {'rotation': [12, 0, 0]}, 'leftleg': {'rotation': [-12, 0, 0]}}
        for slot in ARMOR_SLOTS:
            render.pose_from_anim(v8.armor_animation(sid, slot)[f'animation.bc.armor.{sid}_{slot}'], 0.3, env=env, pose=pose)
        sc.add(ref_player(), pose)
        for slot in ARMOR_SLOTS:
            sc.add(model(v8.armor_geo(sid, slot)), pose)
        sc.render(render.orbit_eye((0, 18, 0), 62, 28 if i % 2 else -28, 8), (0, 18, 0), fov=40)
        x, y = (i % cols) * cell, top + (i // cols) * cell
        img.alpha_composite(sc.image(), (x, y))
        draw.text((x + 12, y + cell - 34), ARMOR_SETS[sid]['name'], font=font(18), fill=(225, 225, 225, 255))
    ims = list(v8.material_icons().values()) + list(v8.rune_icons().values()) + [v8.forge_icon()]
    step = W // len(ims)
    for i, a in enumerate(ims):
        img.alpha_composite(tex.to_image(a).resize((64, 64), Image.NEAREST), (i * step + (step - 64) // 2, top + rows * cell + 22))
    img.convert('RGB').save(os.path.join(OUT, 'v080.png'), optimize=True)


def v9_sheet():
    """v0.9.0: the rebuilt spell projectile (five shapes) and the new cast animations at their strongest moment."""
    from bc.models import v9
    from bc.packgen import player_animations
    W = 1400
    top = 60
    bolt_cell = 280
    pose_cell = 200
    poses = [('cast_forward', 0.16, 'Thrust'), ('cast_push', 0.2, 'Push'), ('cast_channel', 0.5, 'Channel'), ('cast_raise', 0.24, 'Call the sky'),
             ('cast_slam', 0.32, 'Slam'), ('cast_sweep', 0.22, 'Sweep'), ('cast_spin', 0.12, 'Spin'), ('cast_summon', 0.4, 'Summon'),
             ('cast_buff', 0.3, 'Power up'), ('cast_heal', 0.45, 'Heal'), ('cast_dash', 0.08, 'Dash'), ('fruit_punch', 0.14, 'Fruit: punch'),
             ('fruit_stomp', 0.18, 'Fruit: stomp'), ('fruit_roar', 0.3, 'Fruit: roar')]
    cols = 7
    rows = (len(poses) + cols - 1) // cols
    H = top + bolt_cell + rows * pose_cell + 20
    img = background(W, H, '22222c', '101016', ring=False)
    draw = ImageDraw.Draw(img)
    draw.text((20, 14), 'v0.9.0: the rebuilt spell projectile and full-body cast animations', font=font(30), fill=(235, 235, 235, 255))
    geo = v9.bolt_geometry_file()['minecraft:geometry']
    tints = [('orb', 'ff7a1a'), ('shard', '7cc8ff'), ('blade', '6fe0a0'), ('needle', 'ffe03a'), ('comet', 'ff5a1a')]
    anims = v9.bolt_animations()['animation.bc.mana_bolt.fly']
    bw = W // len(tints)
    for i, (shape, hexc) in enumerate(tints):
        g = next(x for x in geo if x['description']['identifier'] == f'geometry.bc.bolt_{shape}')
        m = render.Model({'minecraft:geometry': [g]}, v9.bolt_texture(hexc), emissive=True)
        pose = {}
        render.pose_from_anim(anims, 0.13, env={'q.target_x_rotation': 0, 'q.target_y_rotation': 0, 'q.life_time': 0.13}, pose=pose)
        sc = render.Scene(bw, bolt_cell, ss=2)
        sc.add(m, pose)
        r = 16 if shape == 'comet' else 11
        sc.render(render.orbit_eye((0, 0, 1), r * 2.2, 125, 18), (0, 0, 1), fov=40)
        img.alpha_composite(sc.image(), (i * bw, top))
        draw.text((i * bw + 14, top + bolt_cell - 30), shape.title(), font=font(18), fill=(225, 225, 225, 255))
    pa = player_animations()
    env = {'v.is_first_person': 0.0}
    for i, (name, t, label) in enumerate(poses):
        pose = {}
        render.pose_from_anim(pa[f'animation.bc.player.{name}'], t, env=env, pose=pose)
        sc = render.Scene(pose_cell, pose_cell, ss=2)
        sc.add(ref_player(), pose)
        sc.render(render.orbit_eye((0, 17, 0), 58, 35, 6), (0, 17, 0), fov=40)
        x, y = (i % cols) * pose_cell, top + bolt_cell + (i // cols) * pose_cell
        img.alpha_composite(sc.image(), (x, y))
        draw.text((x + 10, y + pose_cell - 26), label, font=font(15), fill=(225, 225, 225, 255))
    img.convert('RGB').save(os.path.join(OUT, 'v090.png'), optimize=True)


def vfx_sheet():
    """v0.9.0: the particle textures, tinted the way the game tints them, on a dark sky."""
    from bc import vfx9
    cols = {'soft': (120, 200, 255), 'flare': (255, 210, 120), 'streak': (255, 240, 160), 'beam': (120, 220, 255), 'ring': (180, 140, 255),
            'shock': (255, 255, 255), 'fire': (255, 140, 40), 'smoke': (200, 200, 200), 'dust': (190, 170, 140), 'sigil': (255, 215, 120),
            'crack': (255, 120, 40), 'bolt': (255, 240, 120), 'slash': (140, 255, 200), 'shard': (180, 230, 255), 'leaf': (110, 200, 90),
            'drop': (120, 190, 255), 'flake': (220, 240, 255), 'bubble': (150, 220, 255), 'star': (255, 240, 180), 'note': (255, 160, 220),
            'wisp': (160, 255, 200), 'debris': (170, 160, 150), 'glyph': (200, 160, 255)}
    cell = 170
    names = list(vfx9.TEXTURES)
    per = 8
    W, H = per * cell, 60 + ((len(names) + per - 1) // per) * (cell + 24)
    img = background(W, H, '1a1a24', '08080c', ring=False)
    draw = ImageDraw.Draw(img)
    draw.text((20, 14), 'v0.9.0: the new particle textures', font=font(30), fill=(235, 235, 235, 255))
    for i, name in enumerate(names):
        a = vfx9.TEXTURES[name][0]().astype(np.float32)
        if name in ('fire', 'smoke', 'glyph'):
            a = a[:a.shape[1]]                      # first frame
        if name == 'bolt':
            a = a[:, :64]
        c = np.array(cols[name], np.float32)
        rgb_ = a[..., :3] / 255 * c * (a[..., 3:4] / 255) * 1.3
        tile = Image.fromarray(np.clip(rgb_, 0, 255).astype(np.uint8)).convert('RGBA')
        tile.putalpha(Image.fromarray(np.clip(a[..., 3] * 1.0, 0, 255).astype(np.uint8)))
        w, h = tile.size
        sc = min((cell - 20) / w, (cell - 20) / h)
        tile = tile.resize((max(1, int(w * sc)), max(1, int(h * sc))), Image.LANCZOS)
        x, y = (i % per) * cell, 60 + (i // per) * (cell + 24)
        img.alpha_composite(tile, (x + (cell - tile.width) // 2, y + (cell - tile.height) // 2))
        draw.text((x + 10, y + cell), name, font=font(15), fill=(210, 210, 210, 255))
    img.convert('RGB').save(os.path.join(OUT, 'vfx090.png'), optimize=True)


def v10_sheet():
    """v1.0.0: the Mana Waygate, the four new grimoires and the four new Abyss Fruits."""
    from bc.models import v10
    cell = 260
    W, H = cell * 5, 60 + cell + 120
    img = background(W, H, '22222c', '101016', ring=False)
    draw = ImageDraw.Draw(img)
    draw.text((20, 14), 'v1.0.0: the Mana Waygate, four new grimoires and four new Abyss Fruits', font=font(28), fill=(235, 235, 235, 255))
    entries = [('Mana Waygate', model(v10.waygate_geo()), {}, 30, 12, 1.25)]
    A = items.grimoire_animations()
    for a in ('storm', 'blossom', 'coral', 'dream'):
        pose = {}
        render.pose_from_anim(A['animation.bc.grimoire.page_flip'], 0.4, env={'c.item_slot': 'main_hand'}, pose=pose)
        entries.append((f'{ATTRIBUTES[a]["name"]} Grimoire', model(items.grimoire_geo(a)), pose, 40, 20, 1.4))
    for i, (label, m, pose, yaw, pitch, dm) in enumerate(entries):
        pts = np.concatenate([q[0] for q in m.quads(pose)])
        c = (pts.min(0) + pts.max(0)) / 2
        r = np.linalg.norm(pts.max(0) - pts.min(0))
        sc = render.Scene(cell, cell, ss=2)
        sc.add(m, pose)
        sc.render(render.orbit_eye(tuple(c), r * dm, yaw, pitch), tuple(c), fov=40)
        img.alpha_composite(sc.image(), (i * cell, 50))
        draw.text((i * cell + 12, 50 + cell - 30), label, font=font(17), fill=(225, 225, 225, 255))
    rp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'packs', 'BlackClover_RP', 'textures', 'items', 'bc')
    for i, f in enumerate(('spark', 'echo', 'sand', 'gale')):
        path = os.path.join(rp, f'fruit_{f}.png')
        if not os.path.exists(path):
            continue
        ic = Image.open(path).convert('RGBA').resize((72, 72), Image.NEAREST)
        x = 40 + i * 300
        img.alpha_composite(ic, (x, 50 + cell + 20))
        draw.text((x + 86, 50 + cell + 46), f'{f.title()} Fruit', font=font(18), fill=(225, 225, 225, 255))
    img.convert('RGB').save(os.path.join(OUT, 'v100.png'), optimize=True)


BLOCK_RGB = {
    'coarse_dirt': (122, 88, 60), 'gravel': (134, 128, 126), 'spruce_log': (70, 48, 26), 'spruce_fence': (112, 82, 48), 'spruce_planks': (114, 84, 50),
    'dark_oak_planks': (68, 45, 22), 'campfire': (230, 120, 40), 'chest': (168, 116, 44), 'barrel': (120, 86, 48), 'red_wool': (170, 40, 40),
    'honey_block': (240, 170, 40), 'honeycomb_block': (226, 146, 30), 'moss_block': (92, 116, 46), 'mud': (62, 58, 62), 'web': (230, 230, 235),
    'blackstone': (44, 38, 46), 'polished_blackstone_bricks': (56, 50, 60), 'stone_bricks': (122, 122, 122), 'cracked_stone_bricks': (110, 110, 110),
    'mossy_stone_bricks': (100, 118, 90), 'crying_obsidian': (60, 20, 110), 'redstone_block': (180, 25, 20), 'soul_lantern': (100, 220, 235),
}
SMALL = {'spruce_fence': 0.32, 'campfire': 0.75, 'chest': 0.85, 'soul_lantern': 0.45, 'web': 0.6}
GLOW = {'campfire', 'soul_lantern', 'crying_obsidian', 'redstone_block'}


def iso_blueprint(bp, size=380, s=11.0):
    """An isometric block render of a structure blueprint (viewed from the south-east, above)."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    solid = {}
    for (x, y, z), i in bp.blocks.items():
        name = bp.palette[i][0].split(':')[1]
        if name != 'air':
            solid[(x, y, z)] = name
    a, b = s * 0.866, s * 0.5
    ys = [k[1] for k in solid]
    cx, cy = size / 2, size / 2 + (max(ys) * s) / 2 - 4

    def P(x, y, z):
        return (cx + (x - z) * a, cy + (x + z) * b - y * s)

    def shade(c, k, glow):
        return tuple(min(255, int(v * (1.0 if glow else k))) for v in c) + (255,)

    for (x, y, z) in sorted(solid, key=lambda k: (k[0] + k[1] + k[2], k[1])):
        name = solid[(x, y, z)]
        c = BLOCK_RGB.get(name, (128, 128, 128))
        g = name in GLOW
        w = SMALL.get(name, 1.0)
        o = (1 - w) / 2
        x0, x1, z0, z1, y1 = x + o, x + 1 - o, z + o, z + 1 - o, y + (1 if w == 1.0 or name == 'spruce_fence' else w)
        full = w == 1.0
        if not (full and solid.get((x, y + 1, z)) and SMALL.get(solid[(x, y + 1, z)], 1.0) == 1.0):
            d.polygon([P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)], fill=shade(c, 1.0, g))
        if not (full and solid.get((x + 1, y, z)) and SMALL.get(solid[(x + 1, y, z)], 1.0) == 1.0):
            d.polygon([P(x1, y, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y, z1)], fill=shade(c, 0.62, g))
        if not (full and solid.get((x, y, z + 1)) and SMALL.get(solid[(x, y, z + 1)], 1.0) == 1.0):
            d.polygon([P(x0, y, z1), P(x1, y, z1), P(x1, y1, z1), P(x0, y1, z1)], fill=shade(c, 0.8, g))
    # the guards, as coloured markers standing where they spawn
    cols = {'bandit': (210, 60, 50), 'bandit_archer': (230, 150, 50), 'bandit_thief': (150, 150, 160), 'bandit_king': (250, 210, 60),
            'hive_egg': (240, 220, 140), 'hive_drone': (250, 190, 40), 'hive_queen': (255, 120, 20), 'cultist': (150, 40, 190), 'imp': (230, 60, 60)}
    for x, y, z, ident in bp.spawns:
        kind = ident.split(':')[-1]
        px, py = P(x + 0.5, y, z + 0.5)
        col = cols.get(kind, (255, 255, 255))
        dashed = ident.startswith('chance:')
        d.ellipse([px - 5, py - 16, px + 5, py - 6], fill=col + (255,), outline=(255, 255, 255, 255) if dashed else (10, 10, 15, 255), width=2)
        d.rectangle([px - 3, py - 7, px + 3, py], fill=tuple(int(v * 0.7) for v in col) + (255,))
    return img


def v75_sheet():
    """v0.7.5: the three lairs and the new potions, elixirs, smoke bomb and spell scroll."""
    from bc import structures
    from bc.data import CONSUMABLES
    from bc.models import v75
    cell = 380
    top = 330
    W, H = cell * 3, 50 + top + 70 + 130
    img = background(W, H, '22222c', '101016', ring=False)
    draw = ImageDraw.Draw(img)
    draw.text((20, 14), 'v0.7.5: lairs, elite enemies, potions, scrolls & feats', font=font(30), fill=(235, 235, 235, 255))
    lairs = ((structures.bandit_hideout(), 'Bandit hideout', '3 bandits, 2 archers, a thief (King: 20%)'),
             (structures.hive_nest(), 'Hive nest', '5 eggs, 3 drones (Queen: 12%)'),
             (structures.cultist_shrine(), 'Cultist shrine', '3 cultists, 2 imps'))
    for i, (bp, name, guards) in enumerate(lairs):
        img.alpha_composite(iso_blueprint(bp, cell), (i * cell, 50 - (cell - top) // 2))
        draw.text((i * cell + 20, 50 + top + 6), name, font=font(20), fill=(235, 235, 235, 255))
        draw.text((i * cell + 20, 50 + top + 34), guards, font=font(15), fill=(185, 185, 195, 255))
    icons_ = v75.v75_icons()
    n = len(icons_)
    step = W // n
    y0 = 50 + top + 80
    for i, (k, arr) in enumerate(icons_.items()):
        x = i * step + step // 2
        img.alpha_composite(tex.to_image(arr).resize((64, 64), Image.NEAREST), (x - 32, y0))
        label = strip_codes(CONSUMABLES[k][0])
        tw = draw.textlength(label, font=font(15))
        draw.text((x - tw / 2, y0 + 72), label, font=font(15), fill=(225, 225, 225, 255))
    img.convert('RGB').save(os.path.join(OUT, 'v075.png'), optimize=True)


def strip_codes(t):
    import re
    return re.sub('\u00a7.', '', t)


if __name__ == '__main__':
    names = sys.argv[1:] or ['hero', 'spells_sheet', 'gear_sheet', 'mobs_sheet', 'robes_sheet', 'hud_mock', 'icons_strip', 'seas_sheet',
                             'fruits_strip', 'wave3_sheet', 'wave4_sheet', 'v2_sheet', 'v3_sheet', 'v5_sheet', 'v7_sheet', 'v75_sheet', 'v8_sheet', 'v9_sheet', 'vfx_sheet', 'v10_sheet']
    for n in names:
        print('rendering', n)
        globals()[n]()
    print('previews written to docs/images')
