// The tactical AI brain for spell-casting NPCs: Magic Knights and companions, Raider Captains, and the spellcasting
// enemies (Dark Disciples, Imps, Sea Raiders, Raider Gunners, Tidewatch Marksmen, Hellhounds, Mana Wraiths, Rogue Mages).
//
// Every NPC has a combat ROLE (striker, controller, brawler, support) worked out from the spells it knows,
// and two TRAITS: skill (aim, dodging, reaction) and courage (when it retreats). Each "think" it:
//   1. dodges spells and arrows flying at it (with a dodge animation),
//   2. picks a target (closest, weakest, its army's or owner's focus, whoever hurt it),
//   3. retreats to its allies when badly hurt (if it is not brave), holds a commanded position,
//      or - for pack hunters - circles its prey with the pack before lunging,
//   4. scores every spell it knows for the situation (range, clustered enemies, hurt allies, its owner's health,
//      cooldowns) and casts the best one with the matching animation, leading moving targets.
// Companions get extra information (focus target, stance, owner in danger, robe perks) from companions.js.
import { Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { center, foesOf, ownerOf, projectiles, teamOf } from '../core/combat.js';
import { anim, particle, rgb } from '../core/fx.js';
import { V, alive, rand, safe, yawOf } from '../core/util.js';
import { castAbility, isSealed } from '../sea/fruits.js';
import { unitInfo } from './battle.js';
import { castSpec, friends } from './engine.js';
import { kitFor, knightAttr, knightLevel, onKnightLevel, setRoleProvider } from './knights.js';
import { escape } from './danger.js';

const KITTED = Object.keys(DATA.enemyKits);
const MANAGED = new Set(['bc:magic_knight', 'bc:raider_captain', 'bc:rogue_mage', ...KITTED]);
/** mages who cast from a grimoire (knights, companions and Rogue Mages) */
const MAGES = new Set(['bc:magic_knight', 'bc:rogue_mage']);
const ROLES = ['striker', 'controller', 'brawler', 'support'];
/** default cooldowns (ticks) by template, for kits that do not come from a grimoire */
const CD = { bolt: 40, beam: 80, wave: 120, zone: 160, nova: 120, rain: 140, meteor: 220, buff: 300, heal: 200, prison: 160, summon: 600,
  wall: 9999, radial: 160, timestop: 500, leap: 100, vortex: 160, strikes: 140, dive: 140, rewind: 300, repeat: 140 };
/** casting animation per template (knights / companions; v0.9.0: the full-body set the players use) */
const KNIGHT_ANIM = { bolt: 'cast_forward', beam: 'cast_channel', zone: 'cast_channel', vortex: 'cast_channel', nova: 'cast_slam', dive: 'cast_slam',
  wave: 'cast_sweep', rain: 'cast_raise', meteor: 'cast_raise', strikes: 'cast_raise', buff: 'cast_buff', heal: 'cast_heal', summon: 'cast_summon',
  timestop: 'cast_summon', radial: 'cast_spin', leap: 'cast_dash', prison: 'cast_push', rewind: 'cast_raise' };
const KNIGHT_FRUIT_ANIM = { bolt: 'fruit_punch', beam: 'cast_push', wave: 'fruit_stomp', nova: 'fruit_stomp', buff: 'fruit_roar' };
/** casting animation per creature */
const TYPE_ANIM = {
  'bc:raider_captain': 'animation.bc.raider_captain.cast', 'bc:dark_disciple': 'animation.bc.dark_disciple.cast',
  'bc:raider_gunner': 'animation.bc.raider_gunner.shoot', 'bc:tidewatch_marksman': 'animation.bc.tidewatch_marksman.shoot',
  'bc:sea_raider': 'animation.bc.sea_raider.attack', 'bc:hellhound': 'animation.bc.hellhound.bite', 'bc:mana_wraith': 'animation.bc.mana_wraith.cast',
  'bc:bandit': 'animation.bc.bandit.cast', 'bc:bandit_archer': 'animation.bc.bandit.shoot', 'bc:bandit_thief': 'animation.bc.bandit.cast',
  'bc:shadow_assassin': 'animation.bc.shadow_assassin.cast', 'bc:cultist': 'animation.bc.cultist.cast', 'bc:hive_drone': 'animation.bc.hive_drone.spit',
};
const AIM_ANIM = { 'bc:raider_gunner': 'animation.bc.raider_gunner.aim', 'bc:tidewatch_marksman': 'animation.bc.tidewatch_marksman.aim' };
const PACK = new Set(['bc:hellhound', 'bc:hive_drone']);

/**
 * @typedef {{ id: string, name: string, spec?: Record<string, any>, cd: number, cast: (target: any, aim: any, pwMul: number) => any,
 *             score?: (ctx: any, target: any) => number }} Action
 * @typedef {{ role: string, skill: number, courage: number, next: number, castAt: number, dodgeAt: number, cds: Map<string, number>,
 *             target: string, retreatUntil: number, buffUntil: number, lastHitBy: string, lastHitAt: number, aimUntil: number, orbit: number,
 *             skillNow?: number }} Brain
 * @typedef {{ focus?: string, passive?: boolean, ownerLow?: boolean, pwMul?: number, cdMul?: number, castMul?: number, role?: string,
 *             skill?: number, courage?: number, extra?: Action[], bonus?: (foe: any, dist: number) => number, echo?: number }} CompanionInfo
 */
/** @type {Map<string, Brain>} */
const brains = new Map();
/** @type {Map<string, {id: string, until: number}>} taunts and other forced targets */
const forced = new Map();
/** Make an NPC fight `target` for a while (a Vanguard's taunt). */
export function forceTarget(e, target, ticks) {
  forced.set(e.id, { id: target.id, until: system.currentTick + ticks });
}
/** How many spells and fruit powers the brain has cast (for reports and tests). */
export const castStats = { spells: 0, fruit: 0, skills: 0 };
/** Is this entity run by the tactical brain? */
export function hasBrain(e) {
  return brains.has(e.id);
}
/** @type {(e: any) => CompanionInfo | undefined} */
let companionInfo = () => undefined;
/** companions.js tells the brain about focus targets, stances and robe perks */
export function setCompanionProvider(fn) {
  companionInfo = fn;
}
/** @type {(e: any) => ({focus?: string, slot?: any, flee?: boolean, bonus?: (f: any) => number} | undefined)} */
let bandInfo = () => undefined;
/** warband.js tells hostile NPCs about their group's focus, their flank slot and whether they are fleeing */
export function setBandProvider(fn) {
  bandInfo = fn;
}
/** Is this caster's grimoire silenced (the Grimoire Devourer)? */
export function isSilenced(e) {
  const v = safe(() => e.getDynamicProperty('bc:silenced_until'));
  return typeof v === 'number' && v > system.currentTick;
}

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
  if (MAGES.has(e.typeId)) {
    const attr = knightAttr(e);
    const lvl = knightLevel(e);
    const pw = 0.8 + lvl * 0.05;
    const spells = DATA.spells[attr] ?? [];
    // a companion who finished its first trial has an awakened grimoire: every page is open
    const awake = safe(() => e.getDynamicProperty('bc:awake')) === true;
    (isSilenced(e) ? [] : kitFor(attr, awake ? Math.max(lvl, 15) : lvl)).forEach((spec, i) => {
      const sp = spells.find((x) => x.spec === spec || JSON.stringify(x.spec) === JSON.stringify(spec));
      out.push({ id: `k${i}`, name: sp?.name ?? spec.t, spec, cd: Math.max(30, Math.round((sp ? sp.cooldown * 20 * 1.5 : CD[spec.t] ?? 100))),
        cast: (t, aim, mul) => castSpec(e, spec, `a:${attr}`, pw * mul, t, { aim }) });
    });
    // v0.6.0: knights who carry an Abyss Fruit (your companions) fight with its powers too
    const fruit = safe(() => e.getDynamicProperty('bc:fruit'));
    const f = typeof fruit === 'string' ? DATA.fruits[fruit] : undefined;
    const wet = fruit !== 'shark' && !!safe(() => e.isInWater);
    if (f && !isSealed(e) && !wet) {
      f.abilities.forEach((ab) => {
        if (ab.will && !awake && lvl < (DATA.companion.fruitLevel ?? 10)) return;
        out.push({ id: `f:${ab.id}`, name: ab.name, spec: ab.spec, cd: Math.max(40, Math.round(ab.cooldown * 20 * 1.4)),
          cast: (t, aim, mul) => castAbility(e, fruit, ab.id, t, (0.8 + lvl * 0.03) * mul / 0.8) });
      });
    }
  } else if (e.typeId === 'bc:raider_captain') {
    const fruit = safe(() => e.getDynamicProperty('bc:fruit'));
    const f = typeof fruit === 'string' ? DATA.fruits[fruit] : undefined;
    if (!f || isSealed(e)) return out;
    for (const ab of f.abilities) {
      out.push({ id: ab.id, name: ab.name, spec: ab.spec, cd: Math.max(40, Math.round(ab.cooldown * 20 * 1.6)),
        cast: (t) => castAbility(e, fruit, ab.id, t) });
    }
  } else if (DATA.enemyKits[e.typeId]) {
    const k = DATA.enemyKits[e.typeId];
    k.kit.forEach((spec, i) => {
      out.push({ id: `e${i}`, name: spec.t, spec, cd: Math.max(40, Math.round((CD[spec.t] ?? 100) * (i === 0 ? 1 : 1.6))),
        cast: (t, aim, mul) => castSpec(e, spec, k.src, 0.9 * mul, t, { aim }) });
    });
  }
  return out;
}

function brainOf(e) {
  let b = brains.get(e.id);
  if (b) return b;
  const acts = actionsOf(e);
  const beast = e.typeId === 'bc:raider_captain' && DATA.fruits[/** @type {string} */ (safe(() => e.getDynamicProperty('bc:fruit')) ?? '')]?.beast;
  const enemy = !!DATA.enemyKits[e.typeId];
  b = {
    role: beast || PACK.has(e.typeId) ? 'brawler' : roleOf(acts.map((a) => a.spec)),
    skill: Math.min(1, trait(e, 'bc:skill', enemy ? 0.3 : 0.4, enemy ? 0.8 : 0.95) + (MAGES.has(e.typeId) ? knightLevel(e) * 0.02 : 0)),
    courage: trait(e, 'bc:courage', 0.15, 1.0),
    next: system.currentTick + Math.floor(rand(0, 10)), castAt: system.currentTick + 30, dodgeAt: 0, cds: new Map(),
    target: '', retreatUntil: 0, buffUntil: 0, lastHitBy: '', lastHitAt: 0, aimUntil: 0, orbit: Math.random() < 0.5 ? 1 : -1,
  };
  brains.set(e.id, b);
  // knight spellcasters keep their distance (behaviour group chosen per side)
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
  if (!b) return;
  if (src) {
    b.lastHitBy = src.id;
    b.lastHitAt = system.currentTick;
  }
  if (MAGES.has(ev.hurtEntity.typeId) && Math.random() < 0.35) anim(ev.hurtEntity, 'animation.bc.magic_knight.flinch');
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
    if (Math.random() > (b.skillNow ?? b.skill) * 0.75) {
      b.dodgeAt = t + 20;
      return;
    }
    let side = V.flat({ x: -dir.z, y: 0, z: dir.x });
    if (Math.random() < 0.5) side = V.mul(side, -1);
    safe(() => e.applyImpulse({ x: side.x * 0.6, y: 0.2, z: side.z * 0.6 }));
    if (MAGES.has(e.typeId)) anim(e, 'animation.bc.magic_knight.dodge');
    particle(e.dimension, 'bc:dust_burst', e.location, { color: rgb('c8c8c8'), scale: 0.4 });
    b.dodgeAt = t + Math.round(60 - b.skill * 30);
    return;
  }
}

function pickTarget(e, b, foes, info, cinfo) {
  const f0 = forced.get(e.id);
  if (f0 && f0.until > system.currentTick) {
    const ft = world.getEntity(f0.id);
    if (ft && alive(ft) && V.dist(ft.location, e.location) < 28) return ft;
  } else if (f0) forced.delete(e.id);
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
    if (cinfo && f.id === cinfo.focus) s += 14;
    if (f.id === b.target) s += 5;
    if (f.id === b.lastHitBy && system.currentTick - b.lastHitAt < 100) s += 6;
    if (info && f.id === info.enemyLeader) s += 3;
    if (cinfo?.bonus) s += cinfo.bonus(f, d);
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
    case 'heal': case 'rewind': return ally > 0.35 || hp < 0.5 || ctx.ownerLow ? 12 + 10 * Math.max(ally, 1 - hp) + (ctx.ownerLow ? 10 : 0) : 0;
    case 'buff': return ctx.now > ctx.buffUntil ? (s.allies ? 8 : 6) + (hp < 0.6 ? 2 : 0) + (ctx.ownerLow && s.allies ? 6 : 0) : 0;
    case 'summon': return ctx.summons < 2 ? 6 : 0;
    case 'leap':
      if (s.mode === 'blink') return role !== 'brawler' && d < 3.5 && hp < 0.7 ? 9 : role === 'brawler' && d > 6 ? 7 : 0;
      return d >= 2 && d <= (s.dist ?? 9) ? 6 + cluster : 0;
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

function castAnim(e, a) {
  const kind = a.spec?.t === 'repeat' ? a.spec?.spec?.t : a.spec?.t;
  const fruit = typeof a.id === 'string' && a.id.startsWith('f:');
  if (MAGES.has(e.typeId)) anim(e, `animation.bc.magic_knight.v9_${(fruit ? KNIGHT_FRUIT_ANIM[kind] : undefined) ?? KNIGHT_ANIM[kind] ?? 'cast_forward'}`);
  else if (e.typeId === 'bc:sea_raider' || (e.typeId === 'bc:raider_gunner' && a.spec?.grav)) anim(e, `animation.bc.${e.typeId.slice(3)}.${e.typeId === 'bc:sea_raider' ? 'attack' : 'throw'}`);
  else if (TYPE_ANIM[e.typeId]) anim(e, TYPE_ANIM[e.typeId]);
}

function decide(e, b, target, foes, t, cinfo) {
  const acts = cinfo?.extra ? actionsOf(e).concat(cinfo.extra) : actionsOf(e);
  if (!acts.length) return;
  const d = V.dist(target.location, e.location);
  const tl = target.location;
  const cluster = foes.filter((f) => V.dist(f.location, tl) < 3.5).length;
  const near = (r) => foes.filter((f) => V.dist(f.location, e.location) <= r).length;
  let ally = 0;
  for (const f of friends(e, e.location, 10)) if (f.id !== e.id) ally = Math.max(ally, 1 - hpFrac(f));
  const summons = safe(() => e.dimension.getEntities({ location: e.location, maxDistance: 24, type: 'bc:construct' })
    .filter((x) => ownerOf(x) === e.id).length) ?? 0;
  const skill = b.skillNow ?? b.skill;
  const ctx = { d, cluster, near, hp: hpFrac(e), ally, role: cinfo?.role ?? b.role, now: t, buffUntil: b.buffUntil, summons, ownerLow: !!cinfo?.ownerLow,
    foes, target };
  let best;
  let bs = 2.5;
  for (const a of acts) {
    if ((b.cds.get(a.id) ?? 0) > t) continue;
    const s = (a.score ? a.score(ctx, target) : score(a, ctx)) + rand(0, (1 - skill) * 4);
    if (s > bs) {
      bs = s;
      best = a;
    }
  }
  if (!best) return;
  // marksmen raise their guns first, then fire
  if (AIM_ANIM[e.typeId] && best.spec?.t === 'bolt' && !best.spec.grav && b.aimUntil < t) {
    anim(e, AIM_ANIM[e.typeId]);
    b.aimUntil = t + 14;
    b.castAt = t + 10;
    return;
  }
  let aim = lead(e, target, best, skill);
  if (best.spec?.t === 'leap' && best.spec.mode === 'blink' && b.role !== 'brawler') {
    aim = V.add(e.location, V.mul(V.flat(V.sub(e.location, target.location)), 10)); // blink away
  }
  safe(() => e.setRotation({ x: 0, y: yawOf(V.sub(target.location, e.location)) }));
  castAnim(e, best);
  const ok = safe(() => best.cast(target, aim, cinfo?.pwMul ?? 1), 'ai-cast');
  if (ok === false) {
    b.castAt = t + 10;
    return;
  }
  b.cds.set(best.id, t + Math.round(best.cd * (cinfo?.cdMul ?? 1)));
  if (best.id.startsWith('f:')) castStats.fruit++;
  else if (best.score) castStats.skills++;
  else castStats.spells++;
  if (best.spec?.t === 'buff') b.buffUntil = t + 240;
  // an Arcanist's Spell Echo: the spell rings out once more at half power
  if (cinfo?.echo && best.spec && !best.score && Math.random() < cinfo.echo) {
    const again = best;
    system.runTimeout(() => {
      if (alive(e) && alive(target)) safe(() => again.cast(target, lead(e, target, again, skill), (cinfo.pwMul ?? 1) * 0.5), 'ai-echo');
    }, 12);
  }
  const enemy = !!DATA.enemyKits[e.typeId];
  b.castAt = t + Math.round(((enemy ? 40 : 26) + (1 - skill) * 40 + rand(0, 14)) * (cinfo?.castMul ?? 1));
}

// ------------------------------------------------------------------------------- movement
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

/** Pack hunters circle their prey together, then lunge in turn. */
function packCircle(e, b, target) {
  const pals = safe(() => e.dimension.getEntities({ location: target.location, maxDistance: 8, type: e.typeId })) ?? [];
  if (pals.length < 2) return;
  const d = V.dist(e.location, target.location);
  if (d < 2.5 || d > 9) return;
  const away = V.flat(V.sub(e.location, target.location));
  const tangent = { x: -away.z * b.orbit, y: 0, z: away.x * b.orbit };
  const keep = d < 4 ? 0.12 : d > 6 ? -0.12 : 0;
  safe(() => e.applyImpulse({ x: tangent.x * 0.22 + away.x * keep, y: 0, z: tangent.z * 0.22 + away.z * keep }));
}

function think(e, b, t) {
  const info = unitInfo(e.id);
  if (info?.routing) return;
  const cinfo = companionInfo(e);
  const binfo = cinfo ? undefined : bandInfo(e);
  b.skillNow = cinfo?.skill !== undefined ? Math.max(0.1, Math.min(1, cinfo.skill)) : b.skill;
  if (binfo?.flee) {
    // a broken warband: run from the nearest foe
    const near = foesOf(e, 16)[0];
    if (near) {
      const away = V.flat(V.sub(e.location, near.location));
      safe(() => e.applyImpulse({ x: away.x * 0.32, y: 0, z: away.z * 0.32 }));
    }
    return;
  }
  if (b.dodgeAt <= t) tryDodge(e, b, t);
  // step out of telegraphed blows and spell fields (companions always read them, others by skill)
  if (cinfo || Math.random() < b.skill * 0.6) escape(e, cinfo ? 0.5 : 0.35);
  if (cinfo?.passive) {
    holdPosition(e);
    return;
  }
  const foes = foesOf(e, 24);
  const target = pickTarget(e, b, foes, info, cinfo ?? binfo);
  if (!target) {
    // called to help a warband further away: march towards its prey
    const far = binfo?.focus ? world.getEntity(binfo.focus) : undefined;
    if (far && alive(far) && far.dimension.id === e.dimension.id && V.dist(far.location, e.location) < 48) {
      const dir = V.flat(V.sub(far.location, e.location));
      safe(() => e.applyImpulse({ x: dir.x * 0.25, y: 0, z: dir.z * 0.25 }));
      return;
    }
    holdPosition(e);
    return;
  }
  b.target = target.id;
  const hp = hpFrac(e);
  // cowards fall back to their friends when badly hurt
  const courage = cinfo?.courage ?? b.courage;
  if (hp < 0.3 && courage < 0.6 && b.retreatUntil < t - 200) {
    b.retreatUntil = t + 60;
    particle(e.dimension, 'bc:dust_burst', e.location, { color: rgb('a0a0a0'), scale: 0.5 });
  }
  if (b.retreatUntil > t) {
    const pals = friends(e, e.location, 20).filter((f) => f.id !== e.id);
    const away = V.flat(V.sub(e.location, target.location));
    const toPals = pals.length ? V.flat(V.sub(pals[0].location, e.location)) : away;
    const dir = V.norm(V.add(away, toPals));
    safe(() => e.applyImpulse({ x: dir.x * 0.3, y: 0, z: dir.z * 0.3 }));
  } else if (holdPosition(e) && V.dist(target.location, e.location) > 12) {
    return;
  } else if (PACK.has(e.typeId) && (b.cds.get('e0') ?? 0) > t) {
    packCircle(e, b, target);
  } else if (binfo?.slot && V.dist(binfo.slot, e.location) > 2) {
    // take the flank slot the warband gave us
    const dir = V.flat(V.sub(binfo.slot, e.location));
    safe(() => e.applyImpulse({ x: dir.x * 0.2, y: 0, z: dir.z * 0.2 }));
  }
  if (b.castAt <= t) decide(e, b, target, foes, t, cinfo);
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

export { Player };
