// Targeting, damage and projectile helpers.
import { Player, world } from '@minecraft/server';
import { V, alive, safe, segDist } from './util.js';

const EXCLUDE_TYPES = ['minecraft:item', 'minecraft:xp_orb', 'minecraft:arrow', 'minecraft:armor_stand', 'minecraft:painting',
  'minecraft:leash_knot', 'minecraft:fishing_hook', 'minecraft:ender_crystal', 'minecraft:villager_v2', 'minecraft:villager',
  'minecraft:wandering_trader', 'minecraft:npc'];
const EXCLUDE_FAMILIES = ['bc_spell', 'inanimate'];

/** Projectile types (vanilla + ours) that anti-magic can cut or swallow. */
export const HOSTILE_PROJECTILES = ['minecraft:arrow', 'minecraft:fireball', 'minecraft:small_fireball', 'minecraft:wither_skull',
  'minecraft:wither_skull_dangerous', 'minecraft:dragon_fireball', 'minecraft:shulker_bullet', 'minecraft:llama_spit',
  'minecraft:breeze_wind_charge_projectile', 'minecraft:snowball', 'minecraft:thrown_trident', 'minecraft:evocation_fang'];

/** May `attacker` hurt `target` with magic? */
export function canHit(attacker, target) {
  if (!alive(target) || target === attacker) return false;
  if (attacker && target.id === attacker.id) return false;
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
    return target.applyDamage(Math.max(0, amount), opts);
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
    const e = owner.dimension.spawnEntity(type, from);
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
