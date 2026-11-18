// The Soul Puppeteer's strings. It can take hold of a companion for a few seconds: the companion turns its magic on
// you and its friends. Strike it (lightly - the squad holds back) a few times, or have a Warden Cleanse it, and the
// strings snap. Without companions nearby, the strings drag you towards the Puppeteer instead.
import { Player, system, world } from '@minecraft/server';
import { addDamageMod, addFoes, addRelation, center, effect, ownerOf, pull } from '../core/combat.js';
import { anim, particle, rgb, sound } from '../core/fx.js';
import { V, alive, pick, safe } from '../core/util.js';
import { nameKnight } from './knights.js';
import { addInfo, bark, entityOf, memberOf, party } from './companions.js';

const STRING = rgb('e8e4f0');
const HITS_TO_FREE = 3;
/** @type {Map<string, {until: number, hits: number, boss: string, owner: string}>} */
const held = new Map();

export function isControlled(e) {
  const h = e ? held.get(e.id) : undefined;
  return !!h && h.until > system.currentTick;
}

function partyOf(ownerId) {
  const p = world.getEntity(ownerId);
  if (!(p instanceof Player)) return [];
  return party(p).m.map((m) => entityOf(m)).filter(Boolean);
}

/** Snap the strings. */
export function freeFromStrings(e, why = 'struck') {
  const h = held.get(e.id);
  if (!h) return;
  held.delete(e.id);
  safe(() => e.setDynamicProperty('bc:puppet_of', undefined));
  nameKnight(e);
  particle(e.dimension, 'bc:burst_spark', center(e), { color: STRING, scale: 1 });
  sound(e.dimension, 'random.glass', e.location, 0.8, 1.6);
  const mo = memberOf(e);
  if (mo) {
    bark(mo.m, mo.p, 'freed', true);
    safe(() => mo.p.onScreenDisplay.setActionBar(`§aThe strings snap! §b${mo.m.name}§a is free${why === 'cleanse' ? ' (Cleanse)' : ''}.`));
  }
}

export function freeAll(bossId) {
  for (const [id, h] of held) {
    if (bossId && h.boss !== bossId) continue;
    const e = world.getEntity(id);
    if (e) freeFromStrings(e, 'boss');
    else held.delete(id);
  }
}

/** The Puppeteer's move: take a companion near `target`, or drag the target itself. */
export function pullStrings(boss, target, phase = 1, count = 1) {
  const owner = target instanceof Player ? target : world.getEntity(ownerOf(target));
  const pool = owner instanceof Player
    ? partyOf(owner.id).filter((x) => alive(x) && !isControlled(x) && V.dist(x.location, boss.location) < 32)
    : [];
  anim(boss, 'animation.bc.soul_puppeteer.control');
  sound(boss.dimension, 'bc.chord', boss.location, 1.2, 0.5);
  if (!pool.length) {
    // no puppets to take: drag the target in
    if (!alive(target)) return false;
    for (let s = 0; s <= 1; s += 0.15) particle(boss.dimension, 'bc:beam_dot', V.lerp(center(boss), center(target), s), { color: STRING, size: 0.3, life: 0.8 });
    if (target instanceof Player) safe(() => target.applyKnockback({ x: (boss.location.x - target.location.x) * 0.15, z: (boss.location.z - target.location.z) * 0.15 }, 0.35));
    else pull(target, boss.location, 1.2);
    effect(target, 'slowness', 3, 1);
    effect(target, 'weakness', 3, 0);
    return true;
  }
  const ticks = phase >= 3 ? 280 : 200;
  for (let i = 0; i < Math.min(count, pool.length); i++) {
    const victim = pick(pool.filter((x) => !isControlled(x)));
    if (!victim) break;
    held.set(victim.id, { until: system.currentTick + ticks, hits: 0, boss: boss.id, owner: owner.id });
    safe(() => {
      victim.setDynamicProperty('bc:puppet_of', boss.id);
      victim.nameTag = `§c§l(Strings)§r ${victim.nameTag}`;
    });
    anim(victim, 'animation.bc.magic_knight.flinch');
    const mo = memberOf(victim);
    if (mo) {
      bark(mo.m, mo.p, 'controlled', true);
      safe(() => mo.p.onScreenDisplay.setActionBar(`§c${mo.m.name} is caught in the Puppeteer's strings! §7Strike them ${HITS_TO_FREE} times or Cleanse them.`));
    }
  }
  return true;
}

// ------------------------------------------------------------------------------- how the strings bend the sides
addRelation((attacker, target) => {
  const ha = held.get(attacker.id);
  if (ha && ha.until > system.currentTick) {
    if (target.id === ha.boss || target.typeId === 'bc:puppet' || target.typeId === 'bc:soul_puppeteer') return false;
    if (target.id === ha.owner || ownerOf(target) === ha.owner) return true;
  }
  const ht = held.get(target.id);
  if (ht && ht.until > system.currentTick) {
    const owner = attacker instanceof Player ? attacker.id : ownerOf(attacker);
    if (owner === ht.owner) return true;
  }
  return undefined;
});

addFoes((e, range) => {
  const h = held.get(e.id);
  if (h && h.until > system.currentTick) {
    const p = world.getEntity(h.owner);
    return [p, ...partyOf(h.owner)].filter((x) => x && x.id !== e.id && V.dist(x.location, e.location) <= range);
  }
  if (!held.size) return [];
  const owner = ownerOf(e);
  if (!owner) return [];
  const out = [];
  for (const [id, hh] of held) {
    if (hh.owner !== owner || hh.until <= system.currentTick) continue;
    const x = world.getEntity(id);
    if (x && V.dist(x.location, e.location) <= range) out.push(x);
  }
  return out;
});

addDamageMod((target, attacker, amount) => {
  const h = held.get(target.id);
  if (!h || !attacker) return amount;
  const owner = attacker instanceof Player ? attacker.id : ownerOf(attacker);
  if (owner !== h.owner) return amount;
  return amount * 0.25; // the squad pulls its punches
});

// any blow from its own side counts towards breaking the strings (melee too)
world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const e = ev.hurtEntity;
  const h = held.get(e.id);
  if (!h) return;
  const src = ev.damageSource.damagingEntity;
  const owner = src instanceof Player ? src.id : src ? ownerOf(src) : '';
  if (owner !== h.owner) return;
  h.hits += src instanceof Player ? 2 : 1;
  if (h.hits >= HITS_TO_FREE) freeFromStrings(e, 'struck');
}, 'strings'));

// a controlled companion goes for you
addInfo((e, p, m, info) => {
  if (!isControlled(e)) return;
  info.focus = p.id;
  info.passive = false;
  info.extra = [];
  info.bonus = undefined;
});

system.runInterval(() => {
  const t = system.currentTick;
  for (const [id, h] of held) {
    const e = world.getEntity(id);
    const boss = world.getEntity(h.boss);
    if (!e || !alive(e)) {
      held.delete(id);
      continue;
    }
    if (h.until <= t || !boss || !alive(boss)) {
      freeFromStrings(e, 'time');
      continue;
    }
    // the strings, from the Puppeteer's hands to its puppet
    const a = V.add(center(boss), { x: 0, y: 1.5, z: 0 });
    const b = V.add(center(e), { x: 0, y: 1.2, z: 0 });
    for (let s = 0; s <= 1; s += 0.12) particle(e.dimension, 'bc:beam_dot', V.lerp(a, b, s), { color: STRING, size: 0.22, life: 0.55 });
  }
}, 10);

world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  if (ev.deadEntity.typeId === 'bc:soul_puppeteer') freeAll(ev.deadEntity.id);
  if (held.has(ev.deadEntity.id)) held.delete(ev.deadEntity.id);
}, 'puppeteerDie'));
