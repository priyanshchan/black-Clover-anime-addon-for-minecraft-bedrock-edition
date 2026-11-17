// The tactical AI brain for spell-casting NPCs (Magic Knights and Raider Captains).
//
// Every NPC has a combat ROLE (striker, controller, brawler, support) worked out from the spells it knows,
// and two TRAITS: skill (aim, dodging, reaction) and courage (when it retreats). Each "think" it:
//   1. dodges spells and arrows flying at it,
//   2. picks a target (closest, weakest, its army's focus target, whoever hurt it),
//   3. retreats to its allies when badly hurt (if it is not brave), or holds a commanded position,
//   4. scores every spell it knows for the situation (range, clustered enemies, hurt allies, cooldowns)
//      and casts the best one, leading moving targets.
// Spellcasters also back away from foes that get too close (a keep-distance behaviour group in their JSON).
import { Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { center, foesOf, ownerOf, projectiles, teamOf } from '../core/combat.js';
import { anim, particle, rgb } from '../core/fx.js';
import { V, alive, rand, safe, yawOf } from '../core/util.js';
import { castAbility, isSealed } from '../sea/fruits.js';
import { unitInfo } from './battle.js';
import { castSpec, friends } from './engine.js';
import { kitFor, knightAttr, knightLevel, onKnightLevel, setRoleProvider } from './knights.js';

const MANAGED = new Set(['bc:magic_knight', 'bc:raider_captain']);
const ROLES = ['striker', 'controller', 'brawler', 'support'];
/** default cooldowns (ticks) by template, for kits that do not come from a grimoire */
const CD = { bolt: 40, beam: 80, wave: 120, zone: 160, nova: 120, rain: 140, meteor: 220, buff: 300, heal: 200, prison: 160, summon: 600,
  wall: 9999, radial: 160, timestop: 500, leap: 100, vortex: 160, strikes: 140, dive: 140, rewind: 300, repeat: 140 };
const up = { x: 0, y: 1, z: 0 };

/**
 * @typedef {{ id: string, name: string, spec?: Record<string, any>, cd: number, cast: (target: any, aim: any) => any }} Action
 * @typedef {{ role: string, skill: number, courage: number, next: number, castAt: number, dodgeAt: number, cds: Map<string, number>,
 *             target: string, retreatUntil: number, buffUntil: number, lastHitBy: string, lastHitAt: number }} Brain
 */
/** @type {Map<string, Brain>} */
const brains = new Map();

// ------------------------------------------------------------------------------- traits & roles
function trait(e, key, lo, hi) {
  let v = safe(() => e.getDynamicProperty(key));
  if (typeof v !== 'number') {
    v = Math.round(rand(lo, hi) * 100) / 100;
    safe(() => e.setDynamicProperty(key, v));
  }
  return /** @type {number} */ (v);
}

function roleOf(specs) {
  const n = { striker: 0, controller: 0, brawler: 0, support: 0 };
  for (const s of specs) {
    if (!s) continue;
    const t = s.t === 'repeat' ? s.spec?.t : s.t;
    if (['bolt', 'beam', 'strikes', 'radial', 'meteor'].includes(t)) n.striker += 1;
    else if (['prison', 'zone', 'vortex', 'timestop', 'rain', 'wave'].includes(t)) n.controller += 1;
    else if (['dive'].includes(t) || (t === 'nova' && s.at !== 'aim') || (t === 'leap' && s.mode !== 'blink')) n.brawler += 1.2;
    else if (['heal', 'rewind'].includes(t) || (t === 'buff' && s.allies)) n.support += 1.5;
  }
  let best = 'striker';
  for (const r of ROLES) if (n[r] > n[best]) best = r;
  return best;
}

/** What this NPC can cast right now. */
function actionsOf(e) {
  /** @type {Action[]} */
  const out = [];
  if (e.typeId === 'bc:magic_knight') {
    const attr = knightAttr(e);
    const lvl = knightLevel(e);
    const pw = 0.8 + lvl * 0.05;
    const spells = DATA.spells[attr] ?? [];
    kitFor(attr, lvl).forEach((spec, i) => {
      const sp = spells.find((x) => x.spec === spec || JSON.stringify(x.spec) === JSON.stringify(spec));
      out.push({ id: `k${i}`, name: sp?.name ?? spec.t, spec, cd: Math.max(30, Math.round((sp ? sp.cooldown * 20 * 1.5 : CD[spec.t] ?? 100))),
        cast: (t, aim) => castSpec(e, spec, `a:${attr}`, pw, t, { aim }) });
    });
  } else if (e.typeId === 'bc:raider_captain') {
    const fruit = safe(() => e.getDynamicProperty('bc:fruit'));
    const f = typeof fruit === 'string' ? DATA.fruits[fruit] : undefined;
    if (!f || isSealed(e)) return out;
    for (const ab of f.abilities) {
      out.push({ id: ab.id, name: ab.name, spec: ab.spec, cd: Math.max(40, Math.round(ab.cooldown * 20 * 1.6)),
        cast: (t) => castAbility(e, fruit, ab.id, t) });
    }
  }
  return out;
}

function brainOf(e) {
  let b = brains.get(e.id);
  if (b) return b;
  const acts = actionsOf(e);
  const beast = e.typeId === 'bc:raider_captain' && DATA.fruits[/** @type {string} */ (safe(() => e.getDynamicProperty('bc:fruit')) ?? '')]?.beast;
  b = {
    role: beast ? 'brawler' : roleOf(acts.map((a) => a.spec)),
    skill: Math.min(1, trait(e, 'bc:skill', 0.4, 0.95) + (e.typeId === 'bc:magic_knight' ? knightLevel(e) * 0.02 : 0)),
    courage: trait(e, 'bc:courage', 0.15, 1.0),
    next: system.currentTick + Math.floor(rand(0, 10)), castAt: system.currentTick + 30, dodgeAt: 0, cds: new Map(),
    target: '', retreatUntil: 0, buffUntil: 0, lastHitBy: '', lastHitAt: 0,
  };
  brains.set(e.id, b);
  // spellcasters keep their distance (behaviour group chosen per side)
  if (b.role !== 'brawler' && e.typeId === 'bc:magic_knight') safe(() => e.triggerEvent(`bc:ranged_${teamOf(e) || 'wild'}`));
  return b;
}

export function brainInfo(e) {
  const b = brainOf(e);
  return { role: b.role, skill: b.skill, courage: b.courage };
}
/** Forget a cached brain (after a level-up or a change of side). */
export function rethink(e) {
  const old = brains.get(e.id);
  brains.delete(e.id);
  const b = brainOf(e);
  if (old) b.cds = old.cds;
}

setRoleProvider((e) => brainInfo(e));
onKnightLevel((e) => rethink(e));

function track(e) {
  if (!MANAGED.has(e.typeId) || brains.has(e.id)) return;
  system.runTimeout(() => {
    if (alive(e)) safe(() => brainOf(e), 'brain');
  }, 2);
}
world.afterEvents.entitySpawn.subscribe((ev) => safe(() => track(ev.entity)));
world.afterEvents.entityLoad.subscribe((ev) => safe(() => track(ev.entity)));
world.afterEvents.entityHurt.subscribe((ev) => {
  const b = brains.get(ev.hurtEntity.id);
  const src = ev.damageSource.damagingEntity;
  if (!b || !src) return;
  b.lastHitBy = src.id;
  b.lastHitAt = system.currentTick;
});

// ------------------------------------------------------------------------------- senses
function hpFrac(e) {
  const h = safe(() => e.getComponent('minecraft:health'));
  return h ? h.currentValue / Math.max(1, h.effectiveMax) : 1;
}

/** Spells and arrows on a collision course: side-step them. */
function tryDodge(e, b, t) {
  let list = [];
  safe(() => {
    list = e.dimension.getEntities({ location: e.location, maxDistance: 8, families: ['bc_spell'] });
    list.push(...e.dimension.getEntities({ location: e.location, maxDistance: 8, type: 'minecraft:arrow' }));
  });
  const c = center(e);
  for (const p of list) {
    const m = projectiles.get(p.id);
    const ownerId = m?.owner ?? safe(() => p.getComponent('minecraft:projectile')?.owner?.id);
    if (!ownerId || ownerId === e.id) continue;
    const owner = world.getEntity(ownerId);
    if (owner && teamOf(owner) && teamOf(owner) === teamOf(e)) continue;
    if (owner && ownerOf(e) && (owner.id === ownerOf(e) || ownerOf(owner) === ownerOf(e))) continue;
    const v = safe(() => p.getVelocity());
    if (!v) continue;
    const speed = V.len(v);
    if (speed < 0.25) continue;
    const dir = V.mul(v, 1 / speed);
    const to = V.sub(c, p.location);
    const along = V.dot(to, dir);
    if (along <= 0 || along / speed > 14) continue;
    const miss = V.len(V.sub(to, V.mul(dir, along)));
    if (miss > 1.8) continue;
    if (Math.random() > b.skill * 0.75) {
      b.dodgeAt = t + 20;
      return;
    }
    let side = V.flat({ x: -dir.z, y: 0, z: dir.x });
    if (Math.random() < 0.5) side = V.mul(side, -1);
    safe(() => e.applyImpulse({ x: side.x * 0.6, y: 0.2, z: side.z * 0.6 }));
    particle(e.dimension, 'bc:dust_burst', e.location, { color: rgb('c8c8c8'), scale: 0.4 });
    b.dodgeAt = t + Math.round(60 - b.skill * 30);
    return;
  }
}

function pickTarget(e, b, foes, info) {
  const owner = ownerOf(e);
  const ownerEnt = owner ? world.getEntity(owner) : undefined;
  const defensive = ownerEnt && safe(() => e.getDynamicProperty('bc:stance')) === 'defensive';
  let best;
  let bs = -Infinity;
  for (const f of foes) {
    const d = V.dist(f.location, e.location);
    if (defensive && V.dist(f.location, ownerEnt.location) > 10) continue;
    let s = 24 - d + (1 - hpFrac(f)) * 8;
    if (info && f.id === info.focus) s += 10;
    if (f.id === b.target) s += 5;
    if (f.id === b.lastHitBy && system.currentTick - b.lastHitAt < 100) s += 6;
    if (info && f.id === info.enemyLeader) s += 3;
    if (s > bs) {
      bs = s;
      best = f;
    }
  }
  return best;
}

// ------------------------------------------------------------------------------- deciding what to cast
function score(a, ctx) {
  const s = a.spec;
  if (!s) return ctx.d <= 14 ? 6 + ctx.cluster : 0; // classic fruit powers: use them in range
  const t = s.t === 'repeat' ? s.spec?.t : s.t;
  const { d, cluster, near, hp, ally, role } = ctx;
  switch (t) {
    case 'bolt': return d >= 2.5 && d <= 24 ? 5 + (s.aoe ? cluster * 2 : 0) + (s.pierce ? cluster : 0) + (role === 'striker' ? 2 : 0) : 1;
    case 'beam': return d <= (s.range ?? 20) ? 6 + cluster * 2 : 0;
    case 'radial': return near(6) * 3;
    case 'wave': return d <= (s.len ?? 12) + 1 ? 4 + cluster * 2 : 0;
    case 'zone': return s.at === 'self' ? near(s.r ?? 5) * 3 : d <= 22 ? 2 + cluster * 3 : 0;
    case 'rain': case 'meteor': return d <= 24 ? 2 + cluster * 3 : 0;
    case 'vortex': return d <= 22 ? 1 + cluster * 3 : 0;
    case 'prison': return d <= 22 ? 3 + cluster * 3 : 0;
    case 'strikes': return d <= 24 ? 3 * Math.min(s.n ?? 4, cluster + 1) : 0;
    case 'nova': return s.at === 'aim' ? (d <= 22 ? 2 + cluster * 3 : 0) : near((s.r ?? 5) + (s.at === 'front' ? 1 : 0)) * 4;
    case 'timestop': return near(s.r ?? 10) >= 3 ? 16 : 0;
    case 'heal': case 'rewind': return ally > 0.35 || hp < 0.5 ? 12 + 10 * Math.max(ally, 1 - hp) : 0;
    case 'buff': return ctx.now > ctx.buffUntil ? (s.allies ? 8 : 6) + (hp < 0.6 ? 2 : 0) : 0;
    case 'summon': return ctx.summons < 2 ? 6 : 0;
    case 'leap':
      if (s.mode === 'blink') return role !== 'brawler' && d < 3.5 && hp < 0.7 ? 9 : role === 'brawler' && d > 6 ? 7 : 0;
      return d >= 2 && d <= 9 ? 6 + cluster : 0;
    case 'dive': return d >= 4 && d <= 16 ? 7 + cluster * 2 : 0;
    default: return 0;
  }
}

function lead(e, target, a, skill) {
  const c = center(target);
  const v = safe(() => target.getVelocity()) ?? { x: 0, y: 0, z: 0 };
  const speed = a.spec?.speed ?? 1.6;
  const ticks = Math.min(20, V.dist(e.location, c) / Math.max(0.5, speed)) * skill;
  const wobble = (1 - skill) * 1.2;
  return { x: c.x + v.x * ticks + rand(-wobble, wobble), y: c.y + rand(-wobble, wobble) * 0.5, z: c.z + v.z * ticks + rand(-wobble, wobble) };
}

function decide(e, b, target, foes, t) {
  const acts = actionsOf(e);
  if (!acts.length) return;
  const d = V.dist(target.location, e.location);
  const tl = target.location;
  const cluster = foes.filter((f) => V.dist(f.location, tl) < 3.5).length;
  const near = (r) => foes.filter((f) => V.dist(f.location, e.location) <= r).length;
  let ally = 0;
  for (const f of friends(e, e.location, 10)) if (f.id !== e.id) ally = Math.max(ally, 1 - hpFrac(f));
  const summons = safe(() => e.dimension.getEntities({ location: e.location, maxDistance: 24, type: 'bc:construct' })
    .filter((x) => ownerOf(x) === e.id).length) ?? 0;
  const ctx = { d, cluster, near, hp: hpFrac(e), ally, role: b.role, now: t, buffUntil: b.buffUntil, summons };
  let best;
  let bs = 2.5;
  for (const a of acts) {
    if ((b.cds.get(a.id) ?? 0) > t) continue;
    const s = score(a, ctx) + rand(0, (1 - b.skill) * 4);
    if (s > bs) {
      bs = s;
      best = a;
    }
  }
  if (!best) return;
  let aim = lead(e, target, best, b.skill);
  if (best.spec?.t === 'leap' && best.spec.mode === 'blink' && b.role !== 'brawler') {
    aim = V.add(e.location, V.mul(V.flat(V.sub(e.location, target.location)), 10)); // blink away
  }
  safe(() => e.setRotation({ x: 0, y: yawOf(V.sub(target.location, e.location)) }));
  anim(e, e.typeId === 'bc:raider_captain' ? 'animation.bc.raider_captain.cast' : 'animation.bc.magic_knight.cast');
  const ok = safe(() => best.cast(target, aim), 'ai-cast');
  if (ok === false) {
    b.castAt = t + 10;
    return;
  }
  b.cds.set(best.id, t + best.cd);
  if (best.spec?.t === 'buff') b.buffUntil = t + 240;
  b.castAt = t + Math.round(26 + (1 - b.skill) * 40 + rand(0, 14));
}

// ------------------------------------------------------------------------------- movement orders
function holdPosition(e) {
  if (safe(() => e.getDynamicProperty('bc:order')) !== 'hold') return false;
  const a = safe(() => e.getDynamicProperty('bc:anchor'));
  if (typeof a !== 'string') return false;
  const anchor = JSON.parse(a);
  const dist = V.dist(anchor, e.location);
  if (dist > 20) safe(() => e.teleport(anchor));
  else if (dist > 3) {
    const dir = V.flat(V.sub(anchor, e.location));
    safe(() => e.applyImpulse({ x: dir.x * 0.22, y: 0, z: dir.z * 0.22 }));
  }
  return true;
}

function think(e, b, t) {
  const info = unitInfo(e.id);
  if (info?.routing) return;
  if (b.dodgeAt <= t) tryDodge(e, b, t);
  const foes = foesOf(e, 24);
  const target = pickTarget(e, b, foes, info);
  if (!target) {
    holdPosition(e);
    return;
  }
  b.target = target.id;
  const hp = hpFrac(e);
  // cowards fall back to their friends when badly hurt
  if (hp < 0.3 && b.courage < 0.6 && b.retreatUntil < t - 200) {
    b.retreatUntil = t + 60;
    if (info) particle(e.dimension, 'bc:dust_burst', e.location, { color: rgb('a0a0a0'), scale: 0.5 });
  }
  if (b.retreatUntil > t) {
    const pals = friends(e, e.location, 20).filter((f) => f.id !== e.id);
    const away = V.flat(V.sub(e.location, target.location));
    const toPals = pals.length ? V.flat(V.sub(pals[0].location, e.location)) : away;
    const dir = V.norm(V.add(away, toPals));
    safe(() => e.applyImpulse({ x: dir.x * 0.3, y: 0, z: dir.z * 0.3 }));
  } else if (holdPosition(e) && V.dist(target.location, e.location) > 12) {
    return;
  }
  if (b.castAt <= t) decide(e, b, target, foes, t);
}

system.runInterval(() => {
  const t = system.currentTick;
  for (const [id, b] of brains) {
    if (b.next > t) continue;
    const e = world.getEntity(id);
    if (!e || !alive(e)) {
      brains.delete(id);
      continue;
    }
    b.next = t + 5 + Math.floor(rand(0, 4));
    safe(() => think(e, b, t), 'think');
  }
}, 2);

export { Player, up };
