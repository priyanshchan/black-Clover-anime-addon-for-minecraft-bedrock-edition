#!/usr/bin/env python3
"""Render README preview images from the real addon models (dev tool).

    python3 tools/previews.py
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


if __name__ == '__main__':
    hero()
    spells_sheet()
    gear_sheet()
    mobs_sheet()
    robes_sheet()
    hud_mock()
    icons_strip()
    print('previews written to docs/images')


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
