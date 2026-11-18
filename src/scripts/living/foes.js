// What makes the v0.7.0 enemies more than spell kits:
// * BANDIT THIEF - when it hits you it snatches doubloons (or a valuable) and runs, invisible and fast. Catch it and it
//   drops everything; let it get 40 blocks away and it is gone. Bandits near their king fight harder.
// * SHADOW ASSASSIN - stalks you invisibly (a faint shadow gives it away), blinks behind its prey and backstabs, and
//   vanishes in a smoke bomb when hurt.
// * CULTIST - chants a dark ritual every so often to call imps; the devils around it protect it (warband.js).
// * HIVE EGG - hatches into drones unless it is destroyed first.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { canHit, center, effect, hurt } from '../core/combat.js';
import { anim, particle, rgb, sound } from '../core/fx.js';
import { V, alive, rand, safe } from '../core/util.js';
import { emit } from '../core/bus.js';

const VALUABLES = ['bc:doubloon', 'minecraft:emerald', 'minecraft:diamond', 'minecraft:gold_ingot', 'bc:mana_crystal'];
/** @type {Map<string, {from: string, until: number}>} thief id -> who it robbed */
const thieves = new Map();
/** @type {Map<string, {next: number, vanish: number}>} */
const assassins = new Map();
const rituals = new Map();
const SHADOW = rgb('2a1040');

// ------------------------------------------------------------------------------- the thief
function steal(thief, p) {
  const inv = p.getComponent('minecraft:inventory')?.container;
  if (!inv) return;
  const already = safe(() => thief.getDynamicProperty('bc:stolen'));
  if (typeof already === 'string') return;
  for (const id of VALUABLES) {
    for (let i = 0; i < inv.size; i++) {
      const it = inv.getItem(i);
      if (it?.typeId !== id || i === p.selectedSlotIndex) continue;
      const n = Math.min(it.amount, id === 'bc:doubloon' ? 10 + Math.floor(Math.random() * 15) : Math.max(1, Math.ceil(it.amount / 3)));
      if (it.amount - n > 0) {
        it.amount -= n;
        inv.setItem(i, it);
      } else inv.setItem(i, undefined);
      safe(() => thief.setDynamicProperty('bc:stolen', JSON.stringify({ id, n, from: p.id })));
      thieves.set(thief.id, { from: p.id, until: system.currentTick + 900 });
      effect(thief, 'invisibility', 6, 0, false);
      effect(thief, 'speed', 15, 1, false);
      particle(thief.dimension, 'bc:smoke_burst', center(thief), { scale: 0.6 });
      sound(thief.dimension, 'bc.coins', thief.location, 1, 1.4);
      const label = id === 'bc:doubloon' ? `${n} doubloons` : `${n}× ${id.replace(/^(bc|minecraft):/, '').replace(/_/g, ' ')}`;
      safe(() => p.onScreenDisplay.setActionBar(`§6A thief snatched your ${label}! §7Catch them!`));
      return;
    }
  }
}

world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const src = ev.damageSource.damagingEntity;
  const p = ev.hurtEntity;
  if (src?.typeId === 'bc:bandit_thief' && p instanceof Player) steal(src, p);
}, 'thief'));

world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const e = ev.deadEntity;
  if (e.typeId !== 'bc:bandit_thief') return;
  const raw = safe(() => e.getDynamicProperty('bc:stolen'));
  thieves.delete(e.id);
  if (typeof raw !== 'string') return;
  const s = JSON.parse(raw);
  safe(() => e.dimension.spawnItem(new ItemStack(s.id, s.n), e.location));
  const p = world.getEntity(s.from);
  if (p instanceof Player) safe(() => p.onScreenDisplay.setActionBar('§aYou caught the thief - your goods are on the ground!'));
  if (p instanceof Player) emit('thief', p);
}, 'thiefDie'));

system.runInterval(() => {
  const t = system.currentTick;
  for (const [id, th] of thieves) {
    const e = world.getEntity(id);
    const p = world.getEntity(th.from);
    if (!e || !alive(e)) {
      thieves.delete(id);
      continue;
    }
    if (!(p instanceof Player) || th.until < t || V.dist(e.location, p.location) > 40) {
      // it got away
      thieves.delete(id);
      particle(e.dimension, 'bc:smoke_burst', e.location, { scale: 0.8 });
      if (p instanceof Player) safe(() => p.sendMessage('§6The thief got away with your goods.'));
      safe(() => e.remove());
      continue;
    }
    const away = V.flat(V.sub(e.location, p.location));
    safe(() => e.applyImpulse({ x: away.x * 0.3, y: 0, z: away.z * 0.3 }));
    if (t % 40 === 0) particle(e.dimension, 'bc:dust_burst', e.location, { color: rgb('d39a2c'), scale: 0.4 });
  }
  // bandits near their king fight harder
  for (const p of world.getAllPlayers()) {
    for (const king of safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 48, type: 'bc:bandit_king' })) ?? []) {
      for (const b of safe(() => king.dimension.getEntities({ location: king.location, maxDistance: 16, families: ['bc_bandit'] })) ?? []) {
        if (b.id !== king.id) effect(b, 'strength', 3, 0, false);
      }
    }
  }
}, 10);

// ------------------------------------------------------------------------------- the assassin
function assassinState(e) {
  let st = assassins.get(e.id);
  if (!st) assassins.set(e.id, (st = { next: system.currentTick + 40, vanish: 0 }));
  return st;
}

function backstab(e, target) {
  const behind = V.add(target.location, V.mul(V.flat(target.getViewDirection()), -1.6));
  particle(e.dimension, 'bc:burst_dark', center(e), { scale: 0.7, color: SHADOW });
  safe(() => e.teleport(behind, { facingLocation: target.location }));
  safe(() => e.removeEffect('invisibility'));
  anim(e, 'animation.bc.shadow_assassin.backstab');
  sound(e.dimension, 'bc.anti.slash', e.location, 1, 1.5);
  system.runTimeout(() => {
    if (!alive(e) || !alive(target) || V.dist(e.location, target.location) > 3.5 || !canHit(e, target)) return;
    hurt(target, 10, e);
    particle(e.dimension, 'bc:slash_fx', center(target), { size: 2.4, color: rgb('c070ff') });
    effect(target, 'weakness', 4, 0);
    if (target instanceof Player) safe(() => target.onScreenDisplay.setActionBar('§5A blade from the shadows!'));
  }, 5);
}

function vanish(e) {
  particle(e.dimension, 'bc:smoke_burst', center(e), { scale: 1.2 });
  sound(e.dimension, 'random.fizz', e.location, 1, 0.7);
  for (const v of safe(() => e.dimension.getEntities({ location: e.location, maxDistance: 4 })) ?? []) {
    if (v.id !== e.id && canHit(e, v)) effect(v, 'blindness', 3, 0);
  }
  for (const p of safe(() => e.dimension.getPlayers({ location: e.location, maxDistance: 4 })) ?? []) effect(p, 'blindness', 3, 0);
  effect(e, 'invisibility', 5, 0, false);
  effect(e, 'speed', 4, 2, false);
  const a = Math.random() * Math.PI * 2;
  safe(() => e.teleport(V.add(e.location, { x: Math.cos(a) * 8, y: 0.5, z: Math.sin(a) * 8 })));
}

world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const e = ev.hurtEntity;
  if (e.typeId !== 'bc:shadow_assassin') return;
  const st = assassinState(e);
  const h = e.getComponent('minecraft:health');
  if (h && h.currentValue / h.effectiveMax < 0.4 && st.vanish < system.currentTick) {
    st.vanish = system.currentTick + 300;
    vanish(e);
  }
}, 'assassinHurt'));

// ------------------------------------------------------------------------------- the loop: assassins, cultists, eggs
system.runInterval(() => {
  const t = system.currentTick;
  const seen = new Set();
  for (const p of world.getAllPlayers()) {
    const near = safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 48 })) ?? [];
    for (const e of near) {
      if (seen.has(e.id)) continue;
      seen.add(e.id);
      if (e.typeId === 'bc:shadow_assassin') safe(() => assassinTick(e, t), 'assassin');
      else if (e.typeId === 'bc:cultist') safe(() => cultistTick(e, t), 'cultist');
      else if (e.typeId === 'bc:hive_egg') safe(() => eggTick(e, t), 'egg');
    }
  }
}, 10);

function preyNear(e, r) {
  let best;
  let bd = r;
  for (const x of [...(safe(() => e.dimension.getPlayers({ location: e.location, maxDistance: r })) ?? []),
    ...(safe(() => e.dimension.getEntities({ location: e.location, maxDistance: r, families: ['bc_knight'] })) ?? [])]) {
    if (!canHit(e, x)) continue;
    const d = V.dist(x.location, e.location);
    if (d < bd) {
      bd = d;
      best = x;
    }
  }
  return best;
}

function assassinTick(e, t) {
  const st = assassinState(e);
  const prey = preyNear(e, 7);
  if (!prey) {
    // stalking: invisible, a faint shadow gives it away
    effect(e, 'invisibility', 2, 0, false);
    if (t % 30 === 0) particle(e.dimension, 'bc:dust_burst', e.location, { color: SHADOW, scale: 0.3 });
    return;
  }
  if (st.next <= t) {
    st.next = t + 120;
    backstab(e, prey);
  }
}

function cultistTick(e, t) {
  const next = rituals.get(e.id) ?? t + 100;
  if (!rituals.has(e.id)) rituals.set(e.id, next);
  if (next > t) return;
  const foe = preyNear(e, 20);
  if (!foe) return;
  rituals.set(e.id, t + 360);
  const imps = safe(() => e.dimension.getEntities({ location: e.location, maxDistance: 24, type: 'bc:imp' }).length) ?? 0;
  if (imps >= 6) return;
  safe(() => e.playAnimation('animation.bc.cultist.ritual', { stopExpression: 'q.anim_time > 3.0' }));
  particle(e.dimension, 'bc:magic_circle_dark', V.add(e.location, { x: 0, y: 0.1, z: 0 }), { size: 3, life: 3, color: rgb('8a1010') });
  sound(e.dimension, 'bc.devil.roar', e.location, 0.8, 1.3);
  system.runTimeout(() => {
    if (!alive(e)) return;
    for (let i = 0; i < 2; i++) {
      const at = V.add(e.location, { x: rand(-2.5, 2.5), y: 0.5, z: rand(-2.5, 2.5) });
      particle(e.dimension, 'bc:burst_dark', at, { scale: 0.8, color: rgb('8a1010') });
      safe(() => e.dimension.spawnEntity('bc:imp', at));
    }
  }, 60);
}

function eggTick(e, t) {
  let at = safe(() => e.getDynamicProperty('bc:hatch_at'));
  if (typeof at !== 'number') {
    at = t + 500;
    safe(() => e.setDynamicProperty('bc:hatch_at', at));
  }
  if (t % 40 === 0) particle(e.dimension, 'bc:bubble_burst', V.add(e.location, { x: 0, y: 0.8, z: 0 }), { color: rgb('b8f040'), scale: 0.3 });
  if (at > t) return;
  hatch(e);
}

/** Hatch an egg now: two drones crawl out. */
export function hatch(e) {
  if (!alive(e)) return;
  const loc = { ...e.location };
  particle(e.dimension, 'bc:bubble_burst', V.add(loc, { x: 0, y: 0.6, z: 0 }), { color: rgb('b8f040'), scale: 1 });
  sound(e.dimension, 'random.glass', loc, 0.8, 0.6);
  safe(() => e.remove());
  for (let i = 0; i < 2; i++) safe(() => e.dimension.spawnEntity('bc:hive_drone', V.add(loc, { x: rand(-0.8, 0.8), y: 0.3, z: rand(-0.8, 0.8) })));
}

/** Lay an egg that hatches after `ticks`. */
export function layEgg(dim, loc, ticks = 500) {
  const e = safe(() => dim.spawnEntity('bc:hive_egg', loc));
  if (e) safe(() => e.setDynamicProperty('bc:hatch_at', system.currentTick + ticks));
  return e;
}

