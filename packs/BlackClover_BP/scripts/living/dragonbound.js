// Dragonbound (v1.2.0): a Mana Wyvern of your own.
// * EGGS come from roost hoards and slain wyverns. Place one and keep it in its element - fire for Ember, snow or ice for
//   Frost, a lightning rod (or copper, or high ground) for Storm - and after four minutes it hatches, bonded to you.
// * It GROWS from hatchling to juvenile to adult while you are near (feed it meat, fish or mana crystals to speed it up).
//   A juvenile fights beside you and breathes its element at your foes; an adult can be SADDLED and RIDDEN.
// * The WYVERN WHISTLE: use it to switch follow / stay / roam, sneak-use to call your wyvern to you, and while riding,
//   use it to breathe fire, frost or lightning where you look.
// * If your wyvern falls, it leaves an egg behind - its bond is not broken.
import { ButtonState, InputButton, ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { emit } from '../core/bus.js';
import { effect, targetsAround } from '../core/combat.js';
import { particle, rgb, sound, title } from '../core/fx.js';
import { V, alive, isCreative, pick, safe, yawOf } from '../core/util.js';
import { castSpec, heal } from './engine.js';

const D = DATA.dragon;
const W = DATA.world.wyverns;
const KINDS = Object.keys(D.eggs);                       // ember_wyvern, frost_wyvern, storm_wyvern
const EGG_ITEM = Object.fromEntries(KINDS.map((k) => [`bc:${D.eggs[k]}`, k]));
const NEEDS = {
  ember_wyvern: (id) => id === 'minecraft:fire' || id === 'minecraft:lava' || id === 'minecraft:flowing_lava' || id === 'minecraft:magma' || id.endsWith('campfire'),
  frost_wyvern: (id) => id.includes('snow') || id.endsWith('ice'),
  storm_wyvern: (id) => id === 'minecraft:lightning_rod' || id.includes('copper'),
};
const BREATH = {
  ember_wyvern: { t: 'beam', d: 9, range: 22, width: 1.6, fire: 4, fx: 'flame' },
  frost_wyvern: { t: 'beam', d: 8, range: 22, width: 1.6, fx: 'ice', eff: [['slowness', 3, 2]] },
  storm_wyvern: { t: 'beam', d: 9, range: 24, width: 1.3, fx: 'lightning' },
};
const kindOf = (e) => KINDS[Number(safe(() => e.getProperty('bc:element')) ?? 0)] ?? 'ember_wyvern';
const stageOf = (e) => Number(safe(() => e.getProperty('bc:stage')) ?? 0);
const ownerIdOf = (e) => String(safe(() => e.getDynamicProperty('bc:owner')) ?? '');

function consume(p, id) {
  if (isCreative(p)) return true;
  const inv = p.getComponent('minecraft:inventory')?.container;
  const it = inv?.getItem(p.selectedSlotIndex);
  if (it?.typeId !== id) return false;
  if (it.amount > 1) {
    it.amount -= 1;
    inv.setItem(p.selectedSlotIndex, it);
  } else inv.setItem(p.selectedSlotIndex, undefined);
  return true;
}

// ------------------------------------------------------------------------------- eggs
/** Place a Wyvern Egg in front of a player. Returns the egg entity. */
export function placeEgg(p, itemId) {
  const kind = EGG_ITEM[itemId];
  if (!kind) return undefined;
  const dir = V.flat(p.getViewDirection());
  const at = { x: Math.floor(p.location.x + dir.x * 2) + 0.5, y: Math.floor(p.location.y), z: Math.floor(p.location.z + dir.z * 2) + 0.5 };
  const e = safe(() => p.dimension.spawnEntity('bc:wyvern_egg', at, { spawnEvent: `bc:element_${KINDS.indexOf(kind)}` }));
  if (!e) return undefined;
  safe(() => {
    e.setDynamicProperty('bc:owner', p.id);
    e.setDynamicProperty('bc:kind', kind);
    e.setDynamicProperty('bc:warmth', 0);
    e.nameTag = `§7${W[kind].name} Egg`;
  });
  consume(p, itemId);
  safe(() => p.sendMessage(`§6You set down the ${W[kind].name} Egg. §7It needs ${D.needs[kind]} to hatch.`));
  sound(p.dimension, 'dig.grass', at, 1, 0.8);
  return e;
}

/** Is the egg kept in its element? */
export function eggCosy(e) {
  const kind = String(safe(() => e.getDynamicProperty('bc:kind')) ?? kindOf(e));
  const ok = NEEDS[kind];
  const l = e.location;
  if (kind === 'storm_wyvern' && l.y >= 100) return true;
  for (let dx = -4; dx <= 4; dx++) {
    for (let dy = -2; dy <= 2; dy++) {
      for (let dz = -4; dz <= 4; dz++) {
        const b = safe(() => e.dimension.getBlock({ x: Math.floor(l.x) + dx, y: Math.floor(l.y) + dy, z: Math.floor(l.z) + dz }));
        if (b && ok(b.typeId)) return true;
      }
    }
  }
  return false;
}

/** Hatch an egg: a hatchling bonded to the egg's owner. */
export function hatch(e) {
  const kind = String(safe(() => e.getDynamicProperty('bc:kind')) ?? kindOf(e));
  const owner = world.getEntity(ownerIdOf(e));
  const at = { ...e.location };
  const dim = e.dimension;
  safe(() => e.remove());
  const w = safe(() => dim.spawnEntity('bc:tamed_wyvern', at, { spawnEvent: `bc:element_${KINDS.indexOf(kind)}` }));
  if (!w) return undefined;
  const name = `${pick(D.names[0])}${pick(D.names[1])}`;
  safe(() => {
    w.setDynamicProperty('bc:owner', ownerIdOf(e));
    w.setDynamicProperty('bc:wname', name);
    w.setDynamicProperty('bc:kind', kind);
    w.setDynamicProperty('bc:growth', 0);
    w.setDynamicProperty('bc:mode', 'follow');
  });
  if (owner instanceof Player) safe(() => w.getComponent('minecraft:tameable')?.tame(owner));
  nameWyvern(w);
  particle(dim, 'bc:burst_spark', V.add(at, { x: 0, y: 0.6, z: 0 }), { color: rgb(W[kind].color), scale: 1 });
  sound(dim, 'random.pop', at, 1, 0.7);
  if (owner instanceof Player) {
    title(owner, `§6§l${name}`, `§7A ${W[kind].name} hatchling chirps at you`, 60);
    safe(() => owner.sendMessage(`§6Your egg hatched! §f${name}§6 the ${W[kind].name} hatchling is yours. §7Feed it meat, fish or mana crystals and keep it near to grow it.`));
    emit('hatch', owner, w);
  }
  return w;
}

system.runInterval(() => {
  const seen = new Set();
  for (const p of world.getAllPlayers()) {
    for (const e of safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 64, type: 'bc:wyvern_egg' })) ?? []) safe(() => {
      if (seen.has(e.id)) return;
      seen.add(e.id);
      if (!eggCosy(e)) return;
      const warmth = Number(e.getDynamicProperty('bc:warmth') ?? 0) + 5;
      e.setDynamicProperty('bc:warmth', warmth);
      const kind = String(e.getDynamicProperty('bc:kind') ?? kindOf(e));
      particle(e.dimension, 'bc:burst_spark', V.add(e.location, { x: 0, y: 0.8, z: 0 }), { color: rgb(W[kind].color), scale: 0.3 });
      if (warmth >= D.hatchSeconds) hatch(e);
    });
  }
}, 100);

world.afterEvents.playerInteractWithEntity.subscribe((ev) => safe(() => {
  const e = ev.target;
  if (e.typeId !== 'bc:wyvern_egg') return;
  const kind = String(safe(() => e.getDynamicProperty('bc:kind')) ?? kindOf(e));
  const pct = Math.min(100, Math.round((Number(safe(() => e.getDynamicProperty('bc:warmth')) ?? 0) / D.hatchSeconds) * 100));
  const cosy = eggCosy(e);
  safe(() => ev.player.onScreenDisplay.setActionBar(cosy ? `§6The egg is warm and stirring §f(${pct}%)` : `§7The egg is still (${pct}%). It needs ${D.needs[kind]}.`));
}, 'eggLook'));

// a broken egg (or a wild wyvern's, or a fallen companion's) comes back as an item
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const e = ev.deadEntity;
  if (e.typeId === 'bc:wyvern_egg') {
    const kind = String(safe(() => e.getDynamicProperty('bc:kind')) ?? 'ember_wyvern');
    safe(() => e.dimension.spawnItem(new ItemStack(`bc:${D.eggs[kind]}`, 1), e.location));
  } else if (W[e.typeId.replace('bc:', '')] && Math.random() < D.fromWyvern) {
    safe(() => e.dimension.spawnItem(new ItemStack(`bc:${D.eggs[e.typeId.replace('bc:', '')]}`, 1), e.location));
  } else if (e.typeId === 'bc:tamed_wyvern') {
    const kind = String(safe(() => e.getDynamicProperty('bc:kind')) ?? kindOf(e));
    const name = String(safe(() => e.getDynamicProperty('bc:wname')) ?? 'Your wyvern');
    safe(() => e.dimension.spawnItem(new ItemStack(`bc:${D.eggs[kind]}`, 1), e.location));
    const owner = world.getEntity(ownerIdOf(e));
    if (owner instanceof Player) safe(() => owner.sendMessage(`§c${name} has fallen... §7but it leaves an egg behind. Its bond is not broken - hatch it again.`));
  }
}, 'eggDie'));

// ------------------------------------------------------------------------------- your wyvern
/** @type {Map<string, {rider: string, speed: number, yaw: number, breathAt: number, attackAt: number, rides: number}>} */
const flight = new Map();
function st(e) {
  let s = flight.get(e.id);
  if (!s) {
    s = { rider: '', speed: 0, yaw: safe(() => e.getRotation().y) ?? 0, breathAt: 0, attackAt: 0, rides: 0 };
    flight.set(e.id, s);
  }
  return s;
}

export function nameWyvern(e) {
  const kind = String(safe(() => e.getDynamicProperty('bc:kind')) ?? kindOf(e));
  const name = String(safe(() => e.getDynamicProperty('bc:wname')) ?? 'Wyvern');
  const stage = D.stages[stageOf(e)]?.name ?? 'hatchling';
  safe(() => (e.nameTag = `§6${name}\n§7${W[kind].name}, ${stage}`));
}

/** Your wyverns (near you, or anywhere loaded). */
export function wyvernsOf(p) {
  const out = [];
  for (const e of safe(() => p.dimension.getEntities({ type: 'bc:tamed_wyvern' })) ?? []) if (ownerIdOf(e) === p.id) out.push(e);
  return out;
}

/** Add growth points; a wyvern that reaches the next stage grows up on the spot. */
export function grow(e, points) {
  const g = Number(safe(() => e.getDynamicProperty('bc:growth')) ?? 0) + points;
  safe(() => e.setDynamicProperty('bc:growth', g));
  const stage = stageOf(e);
  const next = D.stages[stage + 1];
  if (!next || g < next.at) return stage;
  safe(() => e.triggerEvent(`bc:grow_${stage + 1}`));
  safe(() => e.setProperty('bc:stage', stage + 1));
  const owner = world.getEntity(ownerIdOf(e));
  const name = String(safe(() => e.getDynamicProperty('bc:wname')) ?? 'Your wyvern');
  particle(e.dimension, 'bc:level_up', e.location);
  sound(e.dimension, 'mob.enderdragon.growl', e.location, 1, 1.6 - stage * 0.3);
  nameWyvern(e);
  if (owner instanceof Player) {
    title(owner, `§6${name} grows!`, next.ride ? '§7Fully grown - saddle it and take to the sky' : '§7A juvenile now: it fights beside you', 60);
    if (next.ride) emit('wyvern_adult', owner, e);
  }
  return stage + 1;
}

// feeding, saddling and mounting
world.afterEvents.playerInteractWithEntity.subscribe((ev) => safe(() => {
  const e = ev.target;
  if (e.typeId !== 'bc:tamed_wyvern') return;
  const p = ev.player;
  const name = String(safe(() => e.getDynamicProperty('bc:wname')) ?? 'The wyvern');
  if (ownerIdOf(e) !== p.id) {
    safe(() => p.onScreenDisplay.setActionBar(`§7${name} eyes you warily. It answers only to its own rider.`));
    return;
  }
  const held = safe(() => p.getComponent('minecraft:inventory')?.container?.getItem(p.selectedSlotIndex)?.typeId) ?? '';
  if (D.food[held]) {
    consume(p, held);
    heal(e, 4);
    const s = grow(e, D.food[held]);
    particle(e.dimension, 'bc:heal', V.add(e.location, { x: 0, y: 1, z: 0 }), { scale: 0.6 });
    sound(e.dimension, 'random.burp', e.location, 0.8, 1.4);
    const g = Number(safe(() => e.getDynamicProperty('bc:growth')) ?? 0);
    const next = D.stages[s + 1];
    safe(() => p.onScreenDisplay.setActionBar(next ? `§6${name} gobbles it up §7(growth ${g}/${next.at})` : `§6${name} gobbles it up §7(fully grown)`));
    emit('wyvern_fed', p, e);
    return;
  }
  if (held === 'bc:wyvern_saddle') {
    if (stageOf(e) < 2) {
      safe(() => p.onScreenDisplay.setActionBar(`§7${name} is too small for a saddle. Let it grow up first.`));
      return;
    }
    if (safe(() => e.getProperty('bc:saddled')) === true) return;
    consume(p, held);
    safe(() => e.triggerEvent('bc:saddle'));
    safe(() => e.setProperty('bc:saddled', true));
    safe(() => p.sendMessage(`§6${name} is saddled! §7Use it (empty-handed or with the whistle) to climb on. Look to steer, hold forward to fly, jump to climb, sneak to step off.`));
    return;
  }
  if (stageOf(e) >= 2 && safe(() => e.getProperty('bc:saddled')) === true) mount(p, e);
}, 'wyvernInteract'));

/** Climb onto your saddled adult wyvern. */
export function mount(p, e) {
  if (ownerIdOf(e) !== p.id || stageOf(e) < 2 || safe(() => e.getProperty('bc:saddled')) !== true) return false;
  if (safe(() => p.getComponent('minecraft:riding')?.entityRidingOn)) return false;
  safe(() => e.triggerEvent('bc:mount'));
  const ok = safe(() => e.getComponent('minecraft:rideable')?.addRider(p)) ?? false;
  if (ok !== false) {
    const s = st(e);
    s.rider = p.id;
    s.yaw = yawOf(p.getViewDirection());
    s.rides++;
    emit('wyvern_ride', p, e);
  }
  return ok !== false;
}

// the whistle: commands on the ground, breath in the air
export function useWhistle(p) {
  const riding = safe(() => p.getComponent('minecraft:riding')?.entityRidingOn);
  if (riding?.typeId === 'bc:tamed_wyvern') return breathe(riding, p);
  const mine = wyvernsOf(p);
  if (!mine.length) {
    safe(() => p.onScreenDisplay.setActionBar('§7You whistle... but no wyvern of yours is near.'));
    return false;
  }
  sound(p.dimension, 'note.flute', p.location, 1, 1.4);
  if (p.isSneaking) {
    for (const e of mine) {
      const at = V.add(p.location, V.mul(V.flat(p.getViewDirection()), -2.5));
      safe(() => e.teleport(at));
      particle(e.dimension, 'bc:burst_spark', e.location, { color: rgb(W[kindOf(e)].color), scale: 0.6 });
    }
    safe(() => p.onScreenDisplay.setActionBar('§2Your wyvern swoops down to your side.'));
    return true;
  }
  for (const e of mine) {
    const mode = String(safe(() => e.getDynamicProperty('bc:mode')) ?? 'follow');
    const next = mode === 'follow' ? 'stay' : mode === 'stay' ? 'roam' : 'follow';
    safe(() => e.setDynamicProperty('bc:mode', next));
    safe(() => e.triggerEvent(next === 'follow' ? 'bc:stand' : next === 'stay' ? 'bc:sit' : 'bc:roam'));
    safe(() => p.onScreenDisplay.setActionBar(`§2${safe(() => e.getDynamicProperty('bc:wname')) ?? 'Your wyvern'}: §f${{ follow: 'follow me', stay: 'stay here', roam: 'roam free' }[next]}`));
  }
  return true;
}

/** Breathe the wyvern's element where its rider looks. */
export function breathe(e, p) {
  const s = st(e);
  const t = system.currentTick;
  if (s.breathAt > t) {
    safe(() => p.onScreenDisplay.setActionBar(`§7Your wyvern draws breath... §f${Math.ceil((s.breathAt - t) / 20)}s`));
    return false;
  }
  s.breathAt = t + D.breathCooldown * 20;
  const kind = kindOf(e);
  const look = p.getViewDirection();
  const aim = V.add(e.location, V.add(V.mul(look, 22), { x: 0, y: 1, z: 0 }));
  safe(() => e.setDynamicProperty('bc:owner', p.id));
  safe(() => e.playAnimation('animation.bc.tamed_wyvern.breath'));
  sound(e.dimension, 'mob.enderdragon.growl', e.location, 1.5, 1.1);
  castSpec(e, BREATH[kind], `a:${W[kind].attr}`, 1.2, undefined, { aim });
  return true;
}

// growth, riding and fighting
system.runInterval(() => {
  const t = system.currentTick;
  for (const p of world.getAllPlayers()) {
    for (const e of wyvernsOf(p)) safe(() => {
      if (t % 20 === 0 && V.dist(p.location, e.location) < 64) grow(e, D.growthPerSecond);
      const s = st(e);
      const riders = safe(() => e.getComponent('minecraft:rideable')?.getRiders()) ?? [];
      const r = riders.find((x) => x instanceof Player);
      if (r) fly(e, r, s);
      else if (s.rider) {
        const was = world.getEntity(s.rider);
        if (was) effect(was, 'slow_falling', 4, 0, false);
        s.rider = '';
        safe(() => e.triggerEvent('bc:dismount'));
      } else if (t % 60 === 0 && stageOf(e) >= 1 && t >= s.attackAt) {
        // it breathes at whatever threatens its rider
        const foe = targetsAround(e.dimension, p.location, 14, e).find((x) => safe(() => x.matches({ families: ['monster'] })) && ownerIdOf(x) !== p.id);
        if (foe && V.dist(foe.location, e.location) < 18) {
          s.attackAt = t + 100;
          const kind = kindOf(e);
          safe(() => e.playAnimation('animation.bc.tamed_wyvern.breath'));
          castSpec(e, BREATH[kind], `a:${W[kind].attr}`, stageOf(e) >= 2 ? 1 : 0.5, foe);
        }
      }
    });
  }
}, 2);

function fly(e, p, s) {
  if (!s.rider) {
    s.rider = p.id;
    safe(() => e.triggerEvent('bc:mount'));
  }
  const look = p.getViewDirection();
  const mv = safe(() => p.inputInfo.getMovementVector()) ?? { x: 0, y: 0 };
  const jump = safe(() => p.inputInfo.getButtonState(InputButton.Jump)) === ButtonState.Pressed;
  const want = yawOf(look);
  const diff = ((want - s.yaw + 540) % 360) - 180;
  s.yaw += Math.max(-8, Math.min(8, diff));
  const top = D.rideSpeed;
  const target = mv.y > 0.1 ? top * mv.y : mv.y < -0.1 ? 0 : s.speed * 0.7;
  s.speed += (target - s.speed) * (mv.y > 0.1 ? 0.05 : 0.1);
  const dir = V.norm(look);
  const vel = V.mul(dir, s.speed);
  if (jump) vel.y = Math.max(vel.y, 0.45);
  else if (s.speed < 0.05) vel.y = -0.02;
  const v = e.getVelocity();
  safe(() => e.applyImpulse({ x: (vel.x - v.x) * 0.25, y: (vel.y - v.y) * 0.25, z: (vel.z - v.z) * 0.25 }));
  safe(() => e.setRotation({ x: 0, y: s.yaw }));
  if (s.speed > 0.4 && system.currentTick % 6 === 0) particle(e.dimension, 'bc:burst_spark', V.add(e.location, V.mul(dir, -2)), { color: rgb(W[kindOf(e)].color), scale: 0.3 });
}

export { kindOf, stageOf };
