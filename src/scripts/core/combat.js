// Targeting, damage and projectile helpers.
import { Player, system, world } from '@minecraft/server';
import { V, alive, safe, segDist } from './util.js';

const EXCLUDE_TYPES = ['minecraft:item', 'minecraft:xp_orb', 'minecraft:arrow', 'minecraft:armor_stand', 'minecraft:painting',
  'minecraft:leash_knot', 'minecraft:fishing_hook', 'minecraft:ender_crystal', 'minecraft:villager_v2', 'minecraft:villager',
  'minecraft:wandering_trader', 'minecraft:npc'];
const EXCLUDE_FAMILIES = ['bc_spell', 'inanimate'];

/** Projectile types (vanilla + ours) that anti-magic can cut or swallow. */
export const HOSTILE_PROJECTILES = ['minecraft:arrow', 'minecraft:fireball', 'minecraft:small_fireball', 'minecraft:wither_skull',
  'minecraft:wither_skull_dangerous', 'minecraft:dragon_fireball', 'minecraft:shulker_bullet', 'minecraft:llama_spit',
  'minecraft:breeze_wind_charge_projectile', 'minecraft:snowball', 'minecraft:thrown_trident', 'minecraft:evocation_fang'];

// ---------------------------------------------------------------------------- factions
/** Natural sides: entities of one side never hurt each other with magic. */
const FACTION = {
  'bc:magic_knight': 'clover', 'bc:construct': 'clover', 'bc:magic_merchant': 'clover',
  'bc:dark_disciple': 'devil', 'bc:devil': 'devil', 'bc:imp': 'devil', 'bc:archdevil': 'devil', 'bc:devil_gate': 'devil',
  'bc:sea_raider': 'pirate', 'bc:raider_captain': 'pirate', 'bc:phantom_raider': 'pirate', 'bc:phantom_galleon': 'pirate',
  'bc:tidewatch_sentinel': 'navy', 'bc:tidewatch_commodore': 'navy',
  'bc:raider_gunner': 'pirate', 'bc:tidewatch_marksman': 'navy', 'bc:hellhound': 'devil', 'bc:mana_wraith': 'devil', 'bc:fallen_captain': 'devil',
  'bc:rogue_mage': 'rogue', 'bc:frost_witch': 'witch', 'bc:ember_witch': 'witch', 'bc:bone_dragon': 'undead',
  'bc:soul_puppeteer': 'devil', 'bc:puppet': 'devil',
};
/** NPCs that only harm a player who attacked them first. */
const PEACEFUL = new Set(['bc:magic_knight', 'bc:construct', 'bc:magic_merchant', 'bc:shade_soldier', 'bc:earth_golem', 'bc:mirror_clone']);
/** @type {Map<string, Map<string, number>>} npc id -> player id -> tick the grudge ends */
const grudges = new Map();

export function factionOf(e) {
  return FACTION[safe(() => e.typeId) ?? ''] ?? '';
}
/** War Table side ('a' / 'b') or ''. */
export function teamOf(e) {
  const v = safe(() => e.getDynamicProperty('bc:team'));
  return typeof v === 'string' ? v : '';
}
export function ownerOf(e) {
  const v = safe(() => e.getDynamicProperty('bc:owner'));
  return typeof v === 'string' ? v : '';
}
export function holdGrudge(npc, player, ticks = 600) {
  let m = grudges.get(npc.id);
  if (!m) grudges.set(npc.id, (m = new Map()));
  m.set(player.id, system.currentTick + ticks);
}
function angryAt(npc, player) {
  return (grudges.get(npc.id)?.get(player.id) ?? 0) > system.currentTick;
}

/** What each wild faction hunts (players are hunted by every hostile side, and by peaceful NPCs only after a grudge). */
const HUNTS = {
  clover: ['monster'],
  devil: ['bc_knight', 'bc_navy'],
  pirate: ['bc_knight', 'bc_navy'],
  navy: ['bc_pirate', 'bc_devil', 'bc_disciple', 'bc_rogue'],
  rogue: ['bc_knight', 'bc_navy'],
  witch: ['bc_knight', 'bc_navy'],
  undead: ['bc_knight', 'bc_navy'],
};
export const TEAMS = ['a', 'b', 'c'];

// ---------------------------------------------------------------------------- hooks
// Other systems (sparring, rival squads, the Soul Puppeteer's strings, training dummies) bend the normal sides:
/** @type {((attacker: any, target: any) => boolean | undefined)[]} */
const relations = [];
/** @type {((e: any, range: number) => any[])[]} */
const extraFoes = [];
/** @type {((target: any, attacker: any, amount: number) => number)[]} */
const damageMods = [];
/** A rule that can force `attacker` to be hostile (true) or friendly (false) to `target`; undefined = no opinion. */
export function addRelation(fn) {
  relations.push(fn);
}
/** Extra candidates an NPC may fight (still filtered by canHit). */
export function addFoes(fn) {
  extraFoes.push(fn);
}
/** Scale script damage (combos, marks, sparring). */
export function addDamageMod(fn) {
  damageMods.push(fn);
}

/**
 * The nearest enemy an NPC should fight: the other armies in a battle, otherwise its faction's foes and players.
 * @returns {import('@minecraft/server').Entity | undefined}
 */
export function foeOf(e, range = 18) {
  let best;
  let bd = Infinity;
  for (const x of foesOf(e, range)) {
    const d = Math.hypot(x.location.x - e.location.x, x.location.y - e.location.y, x.location.z - e.location.z);
    if (d < bd) {
      bd = d;
      best = x;
    }
  }
  return best;
}

/** Every enemy of an NPC within range (see foeOf). */
export function foesOf(e, range = 18) {
  const tm = teamOf(e);
  let list = [];
  safe(() => {
    if (tm) {
      for (const other of TEAMS) if (other !== tm) list.push(...e.dimension.getEntities({ location: e.location, maxDistance: range, families: [`bc_team_${other}`] }));
    } else {
      const fams = HUNTS[factionOf(e)] ?? ['monster'];
      for (const f of fams) list.push(...e.dimension.getEntities({ location: e.location, maxDistance: range, families: [f] }));
      for (const p of e.dimension.getPlayers({ location: e.location, maxDistance: range })) {
        const gm = p.getGameMode();
        if (gm !== 'Creative' && gm !== 'Spectator') list.push(p);
      }
    }
    for (const fn of extraFoes) list.push(...(fn(e, range) ?? []));
  });
  const seen = new Set();
  return list.filter((x) => {
    if (seen.has(x.id)) return false;
    seen.add(x.id);
    return canHit(e, x);
  });
}

/** May `attacker` hurt `target` with magic? */
export function canHit(attacker, target) {
  if (!alive(target) || target === attacker) return false;
  if (attacker && target.id === attacker.id) return false;
  if (attacker) {
    for (const fn of relations) {
      const r = fn(attacker, target);
      if (r !== undefined) return r && (!(target instanceof Player) || safe(() => target.getGameMode()) !== 'Creative');
    }
  }
  if (attacker && !(attacker instanceof Player)) {
    const ta = teamOf(attacker);
    if (ta) {
      if (target instanceof Player) return angryAt(attacker, target);
      const tt = teamOf(target);
      return !!tt && tt !== ta;
    }
    const owner = ownerOf(attacker);
    if (owner && (owner === target.id || ownerOf(target) === owner)) return false;
    if (target instanceof Player && PEACEFUL.has(attacker.typeId)) return angryAt(attacker, target);
    const fa = factionOf(attacker);
    if (fa && fa === factionOf(target) && !teamOf(target)) return false;
  }
  if (attacker instanceof Player && ownerOf(target) === attacker.id) return false;
  if (target instanceof Player) {
    if (!(attacker instanceof Player)) return true;
    try {
      if (!world.gameRules.pvp) return false;
    } catch {
      return false;
    }
    const gm = safe(() => target.getGameMode());
    if (gm === 'Creative' || gm === 'Spectator') return false;
    return true;
  }
  if (!target.getComponent('minecraft:health')) return false;
  // crews don't hurt each other
  if (attacker && safe(() => attacker.matches({ families: ['bc_pirate'] })) && safe(() => target.matches({ families: ['bc_pirate'] }))) return false;
  if (attacker instanceof Player && target.typeId === 'bc:shade_soldier' && target.getDynamicProperty('bc:owner') === attacker.id) return false;
  if (target.typeId === 'bc:sail_ship') return false;
  // never hurt the caster's own pets
  const tame = target.getComponent('minecraft:tameable');
  if (tame && attacker && tame.tamedToPlayerId === attacker.id) return false;
  return true;
}

/**
 * Living entities around a point that `attacker` may hit.
 * @param {import('@minecraft/server').Dimension} dim
 */
export function targetsAround(dim, loc, radius, attacker) {
  let list = [];
  safe(() => {
    list = dim.getEntities({ location: loc, maxDistance: radius, excludeTypes: EXCLUDE_TYPES, excludeFamilies: EXCLUDE_FAMILIES });
  });
  return list.filter((e) => canHit(attacker, e));
}

/** Entities within `width` of the segment a-b. */
export function targetsAlong(dim, a, b, width, attacker) {
  const mid = V.lerp(a, b, 0.5);
  const r = V.dist(a, b) / 2 + width + 1;
  return targetsAround(dim, mid, r, attacker).filter((e) => {
    const c = e.location;
    const center = { x: c.x, y: c.y + 0.9, z: c.z };
    return segDist(center, a, b) <= width || segDist(c, a, b) <= width;
  });
}

export function center(e) {
  const l = e.location;
  let h = 0.9;
  safe(() => {
    h = e.getHeadLocation().y - l.y;
  });
  return { x: l.x, y: l.y + Math.max(0.3, h * 0.7), z: l.z };
}

/**
 * Deal magic damage attributed to the attacker (so kills count for loot / xp).
 * @param {import('@minecraft/server').Entity} target
 */
export function hurt(target, amount, attacker, cause = 'entityAttack') {
  if (!alive(target)) return false;
  return !!safe(() => {
    const opts = { cause: /** @type {any} */ (cause) };
    if (attacker && alive(attacker)) opts.damagingEntity = attacker;
    let dmg = amount;
    for (const fn of damageMods) dmg = fn(target, attacker, dmg);
    return target.applyDamage(Math.max(0, dmg), opts);
  }, 'hurt');
}

/** Knock an entity along `dir` (players and mobs). */
export function knock(target, dir, horizontal, vertical) {
  if (!alive(target)) return;
  const f = V.flat(dir);
  safe(() => target.applyKnockback({ x: f.x * horizontal, z: f.z * horizontal }, vertical), 'knock');
}

export function knockFrom(target, origin, horizontal, vertical) {
  knock(target, V.sub(target.location, origin), horizontal, vertical);
}

/** Pull a non-player entity toward a point (players get knockback instead). */
export function pull(target, to, strength) {
  if (!alive(target)) return;
  const d = V.sub(to, target.location);
  const l = V.len(d);
  if (l < 0.6) return;
  const n = V.mul(d, 1 / l);
  if (target instanceof Player) knock(target, n, strength * 1.4, Math.max(0, n.y) * strength * 0.6);
  else safe(() => target.applyImpulse(V.mul(n, strength * 0.35)), 'pull');
}

export function effect(target, id, seconds, amp = 0, particles = true) {
  safe(() => target.addEffect(id, Math.round(seconds * 20), { amplifier: amp, showParticles: particles }), 'effect');
}

// ---------------------------------------------------------------------------- projectiles
/**
 * @typedef {Object} ProjMeta
 * @property {string} owner       owner entity id
 * @property {string} spell
 * @property {string} attr
 * @property {number} damage
 * @property {number} pierce      remaining extra hits
 * @property {{x:number,y:number,z:number}} vel
 * @property {Set<string>} hit    already-damaged entity ids
 * @property {Record<string, any>} [extra]
 */
/** @type {Map<string, ProjMeta>} */
export const projectiles = new Map();

/**
 * Spawn and launch one of our projectile entities.
 * @param {import('@minecraft/server').Entity} owner
 * @param {string} type
 * @param {{x:number,y:number,z:number}} from
 * @param {{x:number,y:number,z:number}} dir
 * @param {number} speed blocks per tick
 * @param {Omit<ProjMeta,'owner'|'vel'|'hit'> & {hit?: Set<string>}} meta
 */
export function launch(owner, type, from, dir, speed, meta) {
  return safe(() => {
    const ev = meta.extra?.spawnEvent;
    const e = ev ? owner.dimension.spawnEntity(type, from, { spawnEvent: ev }) : owner.dimension.spawnEntity(type, from);
    if (meta.extra?.paint) meta.extra.paint(e);
    const vel = V.mul(V.norm(dir), speed);
    const proj = e.getComponent('minecraft:projectile');
    if (proj) {
      proj.owner = owner;
      proj.shoot(vel, { uncertainty: 0 });
    }
    projectiles.set(e.id, { owner: owner.id, vel, hit: meta.hit ?? new Set(), ...meta });
    return e;
  }, 'launch');
}

/** Where the caster's projectiles leave from (in front of the eyes). */
export function muzzle(player, dist = 1.1, down = 0.25) {
  const dir = player.getViewDirection();
  const h = player.getHeadLocation();
  return { x: h.x + dir.x * dist, y: h.y + dir.y * dist - down, z: h.z + dir.z * dist };
}

/** Block (or point in the air) the player is looking at. */
export function aimPoint(player, maxDist = 24) {
  const dir = player.getViewDirection();
  const head = player.getHeadLocation();
  const hit = safe(() => player.getBlockFromViewDirection({ maxDistance: maxDist, includeLiquidBlocks: false, includePassableBlocks: false }));
  if (hit) {
    const b = hit.block.location;
    return { point: { x: b.x + hit.faceLocation.x, y: b.y + hit.faceLocation.y, z: b.z + hit.faceLocation.z }, block: hit.block };
  }
  return { point: V.add(head, V.mul(dir, maxDist)), block: undefined };
}

/** Entity the player is looking at, if any. */
export function aimEntity(player, maxDist = 32) {
  const hits = safe(() => player.getEntitiesFromViewDirection({ maxDistance: maxDist, excludeFamilies: EXCLUDE_FAMILIES, excludeTypes: EXCLUDE_TYPES })) ?? [];
  for (const h of hits) if (canHit(player, h.entity)) return h.entity;
  return undefined;
}

/** First solid block below a point (to put things on the ground). */
export function groundBelow(dim, loc, maxDown = 8) {
  for (let i = 0; i <= maxDown; i++) {
    const b = safe(() => dim.getBlock({ x: Math.floor(loc.x), y: Math.floor(loc.y) - i, z: Math.floor(loc.z) }));
    if (b && !b.isAir && !b.isLiquid) return { x: loc.x, y: Math.floor(loc.y) - i + 1, z: loc.z };
  }
  return { x: loc.x, y: loc.y - maxDown, z: loc.z };
}

/** Teleport-safe blink destination along the view direction. */
export function blinkDestination(player, maxDist) {
  const dir = player.getViewDirection();
  const head = player.getHeadLocation();
  const hit = safe(() => player.getBlockFromViewDirection({ maxDistance: maxDist, includePassableBlocks: false }));
  const d = hit ? Math.max(0, V.dist(head, V.add(hit.block.location, { x: 0.5, y: 0.5, z: 0.5 })) - 1.4) : maxDist;
  const feet = V.add(player.location, V.mul(dir, d));
  return feet;
}

// NPCs remember who struck them (so peaceful knights only fight back at that player)
world.afterEvents.entityHurt.subscribe((ev) => {
  const src = ev.damageSource.damagingEntity;
  if (!(src instanceof Player)) return;
  const e = ev.hurtEntity;
  if (PEACEFUL.has(e.typeId) || teamOf(e)) safe(() => holdGrudge(e, src));
});
system.runInterval(() => {
  for (const id of [...grudges.keys()]) if (!world.getEntity(id)) grudges.delete(id);
}, 1200);
