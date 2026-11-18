// Fighting as a squad. This layer sits on top of the tactical brain (ai.js) and tells each companion how to fight:
// * PERSONALITY (brave, cautious, loyal, hothead, cheerful, scholar) shifts courage, skill, power and where it stands.
// * SPECIALISATION (from level 10): Vanguard (taunt, shield bash, stands between you and danger), Arcanist (more power,
//   shorter cooldowns, an arcane barrage, Spell Echo at mastery), Warden (Aegis shields, Cleanse, cuts down arrows and
//   spells aimed at you, revives friends twice as fast), Ranger (fights from range, piercing volleys, marks targets).
// * PARTY TACTICS: balanced, focus fire, protect me, spread out, hit and run.
// * COMBOS & MARKS: foes held by a prison or a time stop take +25% from the squad; marked foes +20% (+35% at mastery).
// * DANGER: companions step out of telegraphed blows and spell fields (danger.js).
// * REVIVES: a fallen companion leaves a glowing clover. Stand by it (sneaking) or let a squadmate kneel there for a
//   few seconds and they get back up at half health. A Clover Leaf of Return revives everyone at once.
// * BROOMS: when you fly a broom, your companions mount their own and fly in formation behind you.
import { Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { on } from '../core/bus.js';
import { addDamageMod, canHit, center, effect, foesOf, ownerOf, projectiles } from '../core/combat.js';
import { anim, particle, rgb, sound } from '../core/fx.js';
import { V, alive, clamp, isCreative, safe, yawOf } from '../core/util.js';
import { forceTarget, hasBrain } from './ai.js';
import { setCompanionHooks } from './knights.js';
import { addThreat, isBoss } from './bosses.js';
import { escape } from './danger.js';
import { freeFromStrings, isControlled } from './puppeteer.js';
import { castSpec, colorOf, heal } from './engine.js';
import {
  RESPAWN_MS, addBond, addInfo, addProfileLines, bark, consumeHeld, entityOf, hpFrac, line, memberOf, onMemberTick, onPartyTick, party, save,
  spawnMember,
} from './companions.js';

const C = DATA.companion;
const BAD_EFFECTS = ['poison', 'wither', 'slowness', 'weakness', 'blindness', 'nausea', 'mining_fatigue', 'darkness', 'levitation', 'hunger'];
/** @type {Map<string, number>} entity id -> tick its crowd control ends */
const ccUntil = new Map();
/** @type {Map<string, {until: number, mul: number, owner: string}>} */
const marks = new Map();
/** @type {Map<string, {id: string, until: number}>} focus-fire target per player */
const partyTarget = new Map();
/** @type {Map<string, number>} cid -> revive progress (ticks) */
const reviving = new Map();
/** @type {Map<string, {pid: string, cid: string, idx: number, landing: number}>} broom entity id -> its companion rider */
const flyers = new Map();
const comboNote = new Map();
const guardCd = new Map();
const tauntUntil = new Map();

on('cc', (v, ticks) => ccUntil.set(v.id, system.currentTick + ticks));

function companionOwner(attacker) {
  if (!attacker) return '';
  if (attacker instanceof Player) return attacker.id;
  return typeof safe(() => attacker.getDynamicProperty('bc:cid')) === 'string' ? ownerOf(attacker) : '';
}

// ------------------------------------------------------------------------------- combos and marks
addDamageMod((target, attacker, amount) => {
  const owner = companionOwner(attacker);
  if (!owner || !target) return amount;
  const t = system.currentTick;
  let mul = 1;
  const mk = marks.get(target.id);
  if (mk && mk.until > t && mk.owner === owner) mul *= mk.mul;
  if ((ccUntil.get(target.id) ?? 0) > t && !(attacker instanceof Player)) {
    mul *= 1.25;
    if ((comboNote.get(owner) ?? 0) < t) {
      comboNote.set(owner, t + 60);
      const p = world.getEntity(owner);
      if (p instanceof Player) safe(() => p.onScreenDisplay.setActionBar('§6§lCombo! §r§7the squad hits a bound foe for +25%'));
      const mo = memberOf(attacker);
      if (mo && Math.random() < 0.3) bark(mo.m, mo.p, 'combo');
    }
  }
  return amount * mul;
});

// ------------------------------------------------------------------------------- specialisation skills
function friendsOf(p, e, r) {
  const out = [p];
  for (const m of party(p).m) {
    const x = entityOf(m);
    if (x && V.dist(x.location, e.location) <= r) out.push(x);
  }
  return out.filter((x) => alive(x) && x.dimension.id === e.dimension.id && V.dist(x.location, e.location) <= r);
}

function badEffects(x) {
  return (safe(() => x.getEffects()) ?? []).filter((ef) => BAD_EFFECTS.includes(ef.typeId.replace('minecraft:', '')));
}

/** The extra actions a specialised companion can take (Action objects for the brain). */
function specActions(e, p, m) {
  const spec = m.spec;
  const src = `a:${m.attr}`;
  const pw = 0.8 + m.level * 0.05;
  const out = [];
  if (spec === 'vanguard') {
    const reach = m.mastery ? 20 : 10;
    out.push({
      id: 'taunt', name: 'Taunt', cd: m.mastery ? 300 : 400,
      score: (ctx) => {
        const close = ctx.foes.filter((f) => V.dist(f.location, e.location) < reach).length;
        return close >= 2 || ctx.ownerLow || ctx.foes.some((f) => isBoss(f)) ? 14 : 0;
      },
      cast: () => {
        anim(e, 'animation.bc.magic_knight.taunt');
        bark(m, p, 'taunt');
        particle(e.dimension, 'bc:shockwave', e.location, { color: rgb('ff9a3a'), radius: reach * 0.6 });
        sound(e.dimension, 'bc.horn', e.location, 0.8, 0.7);
        for (const f of foesOf(e, reach)) {
          if (hasBrain(f)) forceTarget(f, e, 100);
          if (isBoss(f)) addThreat(f, e, 600);
        }
        tauntUntil.set(e.id, system.currentTick + 100);
        effect(e, 'resistance', 5, m.mastery ? 1 : 0, false);
        return true;
      },
    });
    const bash = { t: 'nova', at: 'front', d: 7, r: 3, kb: [1.6, 0.3], eff: [['slowness', 2, 3], ['weakness', 2, 1]], fx: m.attr };
    out.push({ id: 'bash', name: 'Shield Bash', spec: bash, cd: 160, score: (ctx) => (ctx.d < 4 ? 9 : 0),
      cast: (t, aim, mul) => castSpec(e, bash, src, pw * mul, t, { aim }) });
  } else if (spec === 'arcanist') {
    const barrage = { t: 'bolt', d: 6, n: 5, spread: 26, shape: 3, speed: 2.4, fx: m.attr };
    out.push({ id: 'barrage', name: 'Arcane Barrage', spec: barrage, cd: 220, cast: (t, aim, mul) => castSpec(e, barrage, src, pw * mul, t, { aim }) });
  } else if (spec === 'warden') {
    out.push({
      id: 'aegis', name: 'Aegis', cd: m.mastery ? 480 : 600,
      score: (ctx) => {
        const hurtPal = friendsOf(p, e, 14).some((x) => hpFrac(x) < 0.5);
        return ctx.ownerLow ? 26 : hurtPal || ctx.foes.some((f) => isBoss(f)) ? 15 : ctx.foes.length >= 3 ? 8 : 0;
      },
      cast: () => {
        anim(e, 'animation.bc.magic_knight.cast_raise');
        bark(m, p, 'aegis');
        particle(e.dimension, 'bc:shockwave', e.location, { color: rgb('ffe080'), radius: 6 });
        sound(e.dimension, 'bc.chord', e.location, 0.8, 1.3);
        for (const x of friendsOf(p, e, 14)) {
          effect(x, 'absorption', 8, 1, false);
          effect(x, 'resistance', 6, 0, false);
          if (m.mastery) {
            heal(x, 6);
            for (const ef of badEffects(x)) safe(() => x.removeEffect(ef.typeId));
          }
          if (x !== e) line(e, x, rgb('ffe080'));
        }
        return true;
      },
    });
    out.push({
      id: 'cleanse', name: 'Cleanse', cd: 300,
      score: () => (friendsOf(p, e, 14).some((x) => badEffects(x).length > 0 || isControlled(x)) ? 16 : 0),
      cast: () => {
        anim(e, 'animation.bc.magic_knight.channel');
        particle(e.dimension, 'bc:heal', center(e), { scale: 1.4 });
        for (const x of friendsOf(p, e, 14)) {
          for (const ef of badEffects(x)) safe(() => x.removeEffect(ef.typeId));
          particle(x.dimension, 'bc:light_burst', center(x), { scale: 0.6 });
        }
        for (const mm of party(p).m) {
          const x = entityOf(mm);
          if (x && isControlled(x) && V.dist(x.location, e.location) < 16) freeFromStrings(x, 'cleanse');
        }
        return true;
      },
    });
  } else if (spec === 'ranger') {
    const volley = { t: 'bolt', d: 7, n: m.mastery ? 5 : 3, spread: 6, shape: 3, speed: 3.0, pierce: 2, fx: m.attr };
    out.push({ id: 'volley', name: 'Volley', spec: volley, cd: 160, score: (ctx) => (ctx.d >= 8 && ctx.d <= 32 ? 10 : ctx.d >= 4 ? 4 : 0),
      cast: (t, aim, mul) => castSpec(e, volley, src, pw * mul, t, { aim }) });
    out.push({
      id: 'mark', name: 'Mark', cd: 300,
      score: (ctx, target) => {
        const mk = marks.get(target.id);
        if (mk && mk.until > system.currentTick) return 0;
        return isBoss(target) || hpFrac(target) > 0.6 ? 11 : 0;
      },
      cast: (target) => {
        marks.set(target.id, { until: system.currentTick + 160, mul: m.mastery ? 1.35 : 1.2, owner: p.id });
        anim(e, 'animation.bc.magic_knight.point');
        particle(target.dimension, 'bc:warning_circle', target.location, { size: 1.6, life: 2.0 });
        particle(target.dimension, 'bc:burst_spark', center(target), { color: rgb('ff4040'), scale: 0.8 });
        if (Math.random() < 0.5) bark(m, p, 'mark');
        return true;
      },
    });
  }
  return out;
}


// ------------------------------------------------------------------------------- what the brain is told
addInfo((e, p, m, info) => {
  const pers = C.personalities[m.personality] ?? C.personalities.brave;
  const spec = C.specs[m.spec];
  const t = system.currentTick;
  const inspired = m.morale >= C.mood.inspired;
  const shaken = m.morale <= C.mood.shaken;
  const tired = m.fatigue >= C.mood.exhausted;
  info.courage = clamp(m.courage + pers.courage + (shaken ? -0.25 : 0) + (inspired ? 0.1 : 0), 0, 1.3);
  info.skill = m.skill + (pers.skill ?? 0) + (spec ? 0.05 : 0) + Math.min(0.1, m.level * 0.005);
  info.pwMul *= (pers.pw ?? 1) * (m.spec === 'arcanist' ? 1.15 : 1) * (inspired ? 1.1 : shaken ? 0.9 : 1) * (m.amulet === 'amulet_power' ? 1.12 : 1);
  info.cdMul *= (m.spec === 'arcanist' ? 0.85 : 1) * (m.amulet === 'amulet_swift' ? 0.88 : 1) * (m.amulet === 'amulet_mana' ? 0.92 : 1);
  info.castMul = (tired ? 1.3 : 1) * (1 - ((pers.aggro ?? 1) - 1) * 0.5);
  if (spec) info.role = spec.role;
  info.echo = m.spec === 'arcanist' && m.mastery ? 0.25 : 0;
  info.extra = specActions(e, p, m);
  const tactic = party(p).cfg.tactic;
  if (tactic === 'focus') {
    const pt = partyTarget.get(p.id);
    if (pt && pt.until > t && !info.focus) info.focus = pt.id;
  }
  info.bonus = (f, d) => {
    let b = 0;
    if (f.typeId === 'bc:training_dummy') return -40;
    const cc = (ccUntil.get(f.id) ?? 0) > t;
    if (cc) b += info.role === 'controller' ? -4 : 8;
    const mk = marks.get(f.id);
    if (mk && mk.until > t && mk.owner === p.id) b += 8;
    const fromOwner = V.dist(f.location, p.location);
    if (tactic === 'protect' && fromOwner > 8) b -= 30;
    if (pers.guard && fromOwner < 6) b += 6;
    if (m.personality === 'hothead') b += Math.min(10, (safe(() => f.getComponent('minecraft:health')?.effectiveMax) ?? 20) / 30);
    if (m.spec === 'ranger') b += Math.min(6, d * 0.25);
    if (m.spec === 'vanguard' && fromOwner < 8) b += 6;
    return b;
  };
});

// Scholars learn faster
setCompanionHooks({ xpMul: (e) => (memberOf(e)?.m.personality === 'scholar' ? C.personalities.scholar.xp : 1) });

addProfileLines((m) => {
  const mood = m.fatigue >= C.mood.exhausted ? '§8exhausted' : m.morale >= C.mood.inspired ? '§dinspired' : m.morale <= C.mood.shaken ? '§9shaken' : '§asteady';
  const lines = [`§7Mood: ${mood}§7 (morale §f${Math.round(m.morale)}§7, weariness §f${Math.round(m.fatigue)}§7)`];
  if (m.amulet) lines.push(`§7Amulet: ${DATA.amulets[m.amulet]?.name ?? m.amulet}`);
  return lines;
});

// ------------------------------------------------------------------------------- positioning in a fight
onMemberTick((p, m, e, i, pt, t, fighting) => {
  if (!fighting) return;
  if (escape(e, 0.5)) return;
  const tactic = pt.cfg.tactic;
  const pers = C.personalities[m.personality];
  const foes = safe(() => foesOf(e, 16)) ?? [];
  let nearest;
  let nd = Infinity;
  for (const f of foes) {
    const d = V.dist(f.location, e.location);
    if (d < nd) {
      nd = d;
      nearest = f;
    }
  }
  const push = (dir, k) => safe(() => e.applyImpulse({ x: dir.x * k, y: 0, z: dir.z * k }));
  const toOwner = V.dist(e.location, p.location);
  if ((tactic === 'protect' || pers.guard) && toOwner > (tactic === 'protect' ? 6 : 10)) push(V.flat(V.sub(p.location, e.location)), 0.25);
  if (tactic === 'spread') {
    for (const o of pt.m) {
      const x = entityOf(o);
      if (!x || x.id === e.id || V.dist(x.location, e.location) > 3.5) continue;
      push(V.flat(V.sub(e.location, x.location)), 0.25);
    }
  }
  if (m.spec === 'vanguard') {
    // stand between you and the closest danger
    let threat;
    let td = 10;
    for (const f of foes) {
      const d = V.dist(f.location, p.location);
      if (d < td) {
        td = d;
        threat = f;
      }
    }
    if (threat) {
      const spot = V.add(p.location, V.mul(V.flat(V.sub(threat.location, p.location)), Math.min(2.5, td * 0.5)));
      if (V.dist(spot, e.location) > 1.5) push(V.flat(V.sub(spot, e.location)), 0.3);
    }
    if (t % 40 === 0) effect(e, 'resistance', 3, (tauntUntil.get(e.id) ?? 0) > t && m.mastery ? 1 : 0, false);
  } else if (nearest && C.specs[m.spec]?.role !== 'brawler') {
    const keep = m.spec === 'ranger' ? 10 : tactic === 'kite' ? 8 : m.personality === 'cautious' ? 5 : 0;
    if (keep && nd < keep) push(V.flat(V.sub(e.location, nearest.location)), 0.3);
  }
  // a Warden cuts down spells and arrows flying at you
  if (m.spec === 'warden' && (guardCd.get(e.id) ?? 0) < t) {
    for (const pr of safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 4.5 })) ?? []) {
      const meta = projectiles.get(pr.id);
      const isArrow = pr.typeId === 'minecraft:arrow';
      if (!meta && !isArrow) continue;
      const shooterId = meta?.owner ?? safe(() => pr.getComponent('minecraft:projectile')?.owner?.id);
      const shooter = shooterId ? world.getEntity(shooterId) : undefined;
      if (!shooter || shooter.id === p.id || ownerOf(shooter) === p.id || !safe(() => canHit(shooter, p))) continue;
      particle(pr.dimension, 'bc:burst_spark', pr.location, { color: rgb('ffe080'), scale: 0.6 });
      safe(() => pr.remove());
      projectiles.delete(pr.id);
      anim(e, 'animation.bc.magic_knight.guard');
      guardCd.set(e.id, t + 60);
      break;
    }
  }
});

// ------------------------------------------------------------------------------- focus fire, revives, flying
function chooseFocus(p) {
  let best;
  let bs = -Infinity;
  for (const f of safe(() => foesOf(p, 16)) ?? []) {
    if (f instanceof Player || f.typeId === 'bc:training_dummy') continue;
    let s = (1 - hpFrac(f)) * 10 - V.dist(f.location, p.location) * 0.3;
    if ((ccUntil.get(f.id) ?? 0) > system.currentTick) s += 4;
    if (marks.get(f.id)?.owner === p.id) s += 4;
    if (s > bs) {
      bs = s;
      best = f;
    }
  }
  return best;
}

function reviveSpot(m) {
  const l = m.fallenLoc;
  return l ? { x: l.x, y: l.y, z: l.z } : undefined;
}

/** Bring a fallen companion back where they fell (or beside you). */
export function revive(p, m, by, at) {
  const spot = at ?? reviveSpot(m) ?? p.location;
  reviving.delete(m.cid);
  m.fallenAt = 0;
  const e = spawnMember(p, m, true, { at: spot, hp: 0.5, quiet: true });
  if (!e) return false;
  m.morale = Math.min(100, m.morale + 5);
  particle(p.dimension, 'bc:clover_leaves', V.add(spot, { x: 0, y: 1, z: 0 }), { scale: 1.4 });
  particle(p.dimension, 'bc:heal', V.add(spot, { x: 0, y: 1, z: 0 }), { scale: 1.2 });
  sound(p.dimension, 'bc.chord', spot, 1, 1.4);
  bark(m, p, 'revived', true);
  if (by && by !== p) {
    const mo = memberOf(by);
    if (mo) {
      addBond(p, mo.m, 5, 'revive');
      addBond(p, m, 5, 'revive');
    }
  } else addBond(p, m, 10, 'revive');
  save(p);
  return true;
}

/** Clover Leaf of Return: every fallen companion gets straight back up beside you. */
export function useCloverLeaf(p) {
  const fallen = party(p).m.filter((m) => m.active && m.fallenAt && !entityOf(m));
  if (!fallen.length) {
    safe(() => p.onScreenDisplay.setActionBar('§7None of your companions has fallen.'));
    return false;
  }
  fallen.forEach((m, i) => revive(p, m, p, V.add(p.location, V.yaw({ x: 1.6, y: 0.2, z: 0 }, 90 * i))));
  if (!isCreative(p)) consumeHeld(p, 'bc:clover_leaf');
  return true;
}

onPartyTick((p, pt, active, t, fighting) => {
  // focus fire: the weakest foe near you, re-picked every second
  if (pt.cfg.tactic === 'focus' && t % 20 === 0) {
    const f = chooseFocus(p);
    if (f) partyTarget.set(p.id, { id: f.id, until: t + 40 });
  }
  // the fallen: a glowing clover where they fell, and someone to pull them back up
  for (const m of active) {
    if (!m.fallenAt || entityOf(m) || !m.fallenLoc || m.fallenLoc.dim !== p.dimension.id) continue;
    if (Date.now() - m.fallenAt > RESPAWN_MS) continue;
    const spot = reviveSpot(m);
    if (t % 20 === 0) particle(p.dimension, 'bc:clover_leaves', V.add(spot, { x: 0, y: 0.6, z: 0 }), { scale: 0.5 });
    let prog = reviving.get(m.cid) ?? 0;
    let helper;
    if (p.isSneaking && V.dist(p.location, spot) < 2.5) {
      helper = p;
      prog += 10;
    } else {
      const wardens = active.filter((x) => x !== m && entityOf(x)).sort((a, b) => (b.spec === 'warden' ? 1 : 0) - (a.spec === 'warden' ? 1 : 0));
      const foesNear = (safe(() => foesOf(p, 24)) ?? []).filter((f) => !(f instanceof Player) && V.dist(f.location, spot) < 8).length;
      for (const x of wardens) {
        if (foesNear && x.spec !== 'warden') continue;
        const e = entityOf(x);
        const d = V.dist(e.location, spot);
        if (d > 24) continue;
        if (d > 1.8) {
          safe(() => e.applyImpulse(V.mul(V.flat(V.sub(spot, e.location)), 0.35)));
          break;
        }
        helper = e;
        prog += x.spec === 'warden' ? 20 : 10;
        if (t % 40 === 0) {
          anim(e, 'animation.bc.magic_knight.kneel');
          if (prog <= 20) bark(x, p, 'revive', true);
          line(e, { location: spot, getHeadLocation: () => spot, dimension: e.dimension }, colorOf(`a:${x.attr}`));
        }
        break;
      }
    }
    if (helper) {
      if (helper === p && t % 20 === 0) safe(() => p.onScreenDisplay.setActionBar(`§aReviving §b${m.name}§a... ${Math.min(100, Math.round((prog / 60) * 100))}%`));
      if (prog >= 60) revive(p, m, helper);
      else reviving.set(m.cid, prog);
    }
  }
  // brooms: when you fly, they fly
  const myBroom = safe(() => p.getComponent('minecraft:riding')?.entityRidingOn);
  const flying = myBroom?.typeId === 'bc:broom';
  if (flying) {
    active.forEach((m, i) => {
      const e = entityOf(m);
      if (!e || safe(() => e.getComponent('minecraft:riding')?.entityRidingOn)) return;
      if (V.dist(e.location, p.location) > 64) return;
      const b = safe(() => e.dimension.spawnEntity('bc:broom', V.add(e.location, { x: 0, y: 0.3, z: 0 })));
      if (!b) return;
      safe(() => {
        b.setProperty('bc:tier', m.level >= 12 ? 1 : 0);
        b.setDynamicProperty('bc:cbroom', m.cid);
        b.getComponent('minecraft:rideable')?.addRider(e);
      });
      flyers.set(b.id, { pid: p.id, cid: m.cid, idx: i, landing: 0 });
      particle(e.dimension, 'bc:burst_spark', center(e), { color: colorOf(`a:${m.attr}`), scale: 0.6 });
      if (i === 0) bark(m, p, 'broom');
    });
  }
});

function flySlot(p, idx) {
  const f = V.flat(p.getViewDirection());
  const r = { x: -f.z, y: 0, z: f.x };
  const side = (idx % 2 ? 1 : -1) * (2.2 + Math.floor(idx / 2) * 1.6);
  return V.add(p.location, V.add(V.mul(r, side), V.add(V.mul(f, -2.5 - Math.floor(idx / 2) * 1.8), { x: 0, y: 0.6 + (idx % 2) * 0.5, z: 0 })));
}

system.runInterval(() => {
  for (const [id, fl] of flyers) {
    const b = world.getEntity(id);
    const p = world.getEntity(fl.pid);
    if (!b || !alive(b)) {
      flyers.delete(id);
      continue;
    }
    safe(() => {
      const riders = b.getComponent('minecraft:rideable')?.getRiders() ?? [];
      if (!riders.length || !(p instanceof Player)) {
        particle(b.dimension, 'bc:clover_leaves', b.location, { scale: 0.4 });
        b.remove();
        flyers.delete(id);
        return;
      }
      const ownerOnBroom = safe(() => p.getComponent('minecraft:riding')?.entityRidingOn)?.typeId === 'bc:broom';
      let want;
      if (ownerOnBroom) {
        fl.landing = 0;
        want = flySlot(p, fl.idx);
      } else {
        // land beside you, then step off
        fl.landing += 1;
        const ground = safe(() => b.dimension.getTopmostBlock({ x: b.location.x, z: b.location.z }));
        want = { x: b.location.x, y: ground ? ground.location.y + 1 : b.location.y - 1, z: b.location.z };
        if (V.dist(want, b.location) < 1.2 || fl.landing > 120) {
          for (const r of riders) safe(() => b.getComponent('minecraft:rideable')?.ejectRider(r));
          b.remove();
          flyers.delete(id);
          return;
        }
      }
      const to = V.sub(want, b.location);
      const dist = V.len(to);
      const speed = Math.min(1.2, dist * 0.12);
      const vel = dist > 0.01 ? V.mul(to, speed / dist) : { x: 0, y: 0, z: 0 };
      const v = b.getVelocity();
      b.applyImpulse({ x: (vel.x - v.x) * 0.35, y: (vel.y - v.y) * 0.35, z: (vel.z - v.z) * 0.35 });
      if (dist > 0.5) b.setRotation({ x: 0, y: yawOf(to) });
      if (dist > 40) b.teleport(want);
    }, 'companionBroom');
  }
}, 2);

// a companion's broom left over from an earlier session simply puts its rider down
world.afterEvents.entityLoad.subscribe((ev) => safe(() => {
  const b = ev.entity;
  if (b.typeId !== 'bc:broom' || flyers.has(b.id) || !isCompanionBroom(b)) return;
  for (const r of b.getComponent('minecraft:rideable')?.getRiders() ?? []) b.getComponent('minecraft:rideable')?.ejectRider(r);
  b.remove();
}, 'companionBroomLoad'));

/** Does this broom belong to a companion (it is steered here, not by brooms.js)? */
export function isCompanionBroom(b) {
  return typeof safe(() => b.getDynamicProperty('bc:cbroom')) === 'string';
}

