// Sailing ships: placing, steering from the helm and firing the cannons.
// The first player aboard is the captain: look where you want to sail, hold forward to
// catch the wind, hold back to brake. Use a Cannonball while aboard to fire a broadside.
import { Player, system, world } from '@minecraft/server';
import { center, hurt, knock, launch, targetsAround } from '../core/combat.js';
import { particle, shake, shakeArea, sound } from '../core/fx.js';
import { V, isCreative, safe, yawOf } from '../core/util.js';
import { registerHandler } from '../magic/projectiles.js';

const MAX_SPEED = 0.42; // blocks per tick
const TURN = 2.6;       // degrees per tick
/** @type {Map<string, {yaw: number, speed: number}>} */
const ships = new Map();
const cannonCd = new Map();

function isWater(b) {
  return !!b && (b.typeId === 'minecraft:water' || b.typeId === 'minecraft:flowing_water' || b.isWaterlogged);
}

function shipOf(p) {
  return safe(() => p.getComponent('minecraft:riding')?.entityRidingOn);
}

/** Place a ship from a Ship Kit onto the water the player is looking at. */
export function placeShip(p) {
  const hit = safe(() => p.getBlockFromViewDirection({ maxDistance: 8, includeLiquidBlocks: true, includePassableBlocks: true }));
  const b = hit?.block;
  if (!b || !isWater(b)) {
    safe(() => p.onScreenDisplay.setActionBar('§7Look at open water to launch your ship.'));
    return false;
  }
  const loc = { x: b.location.x + 0.5, y: b.location.y + 0.6, z: b.location.z + 0.5 };
  const e = safe(() => p.dimension.spawnEntity('bc:sail_ship', loc));
  if (!e) return false;
  const yaw = yawOf(p.getViewDirection());
  safe(() => e.setRotation({ x: 0, y: yaw }));
  ships.set(e.id, { yaw, speed: 0 });
  sound(p.dimension, 'bc.ship.bell', loc, 1, 1);
  particle(p.dimension, 'bc:water_splash', loc, { scale: 1.2 });
  if (!isCreative(p)) {
    const inv = p.getComponent('minecraft:inventory')?.container;
    const it = inv?.getItem(p.selectedSlotIndex);
    if (it?.typeId === 'bc:ship_kit') inv.setItem(p.selectedSlotIndex, undefined);
  }
  return true;
}

function track(e) {
  if (e.typeId !== 'bc:sail_ship' || ships.has(e.id)) return;
  ships.set(e.id, { yaw: safe(() => e.getRotation().y) ?? 0, speed: 0 });
}
world.afterEvents.entitySpawn.subscribe((ev) => safe(() => track(ev.entity)));
world.afterEvents.entityLoad.subscribe((ev) => safe(() => track(ev.entity)));

system.runInterval(() => {
  for (const [id, st] of ships) {
    const e = world.getEntity(id);
    if (!e) {
      ships.delete(id);
      continue;
    }
    safe(() => steer(e, st), 'ship');
  }
}, 1);

function steer(e, st) {
  const riders = e.getComponent('minecraft:rideable')?.getRiders() ?? [];
  const captain = riders.find((r) => r instanceof Player);
  const below = e.dimension.getBlock({ x: Math.floor(e.location.x), y: Math.floor(e.location.y - 0.2), z: Math.floor(e.location.z) });
  const afloat = isWater(below) || e.isInWater;
  let thrust = 0;
  if (captain) {
    const look = yawOf(captain.getViewDirection());
    let diff = ((look - st.yaw + 540) % 360) - 180;
    diff = Math.max(-TURN, Math.min(TURN, diff));
    st.yaw += diff * (afloat ? 1 : 0.3);
    const mv = safe(() => captain.inputInfo.getMovementVector()) ?? { x: 0, y: 0 };
    thrust = mv.y;
  }
  const target = afloat ? (thrust > 0.1 ? MAX_SPEED * thrust : thrust < -0.1 ? -0.08 : 0) : 0;
  st.speed += (target - st.speed) * (thrust > 0.1 ? 0.03 : 0.06);
  const r = (st.yaw * Math.PI) / 180;
  const fwd = { x: -Math.sin(r), y: 0, z: Math.cos(r) };
  const v = e.getVelocity();
  const want = V.mul(fwd, st.speed);
  safe(() => e.applyImpulse({ x: (want.x - v.x) * 0.35, y: 0, z: (want.z - v.z) * 0.35 }));
  safe(() => e.setRotation({ x: 0, y: st.yaw }));
  if (Math.abs(st.speed) > 0.15 && system.currentTick % 6 === 0) {
    const stern = V.add(e.location, V.add(V.mul(fwd, -1.6), { x: 0, y: 0.3, z: 0 }));
    particle(e.dimension, 'bc:water_splash', stern, { scale: 0.25 });
  }
  // ramming small boats/mobs out of the way
  if (Math.abs(st.speed) > 0.3 && system.currentTick % 10 === 0) {
    for (const t of targetsAround(e.dimension, V.add(e.location, V.mul(fwd, 2.2)), 1.8, captain)) {
      if (riders.some((x) => x.id === t.id)) continue;
      hurt(t, 4, captain);
      knock(t, fwd, 1.4, 0.3);
    }
  }
}

// ------------------------------------------------------------------------------- cannons
export function fireCannon(p) {
  const ship = shipOf(p);
  if (!ship || ship.typeId !== 'bc:sail_ship') {
    safe(() => p.onScreenDisplay.setActionBar('§7Cannonballs are fired from aboard a ship.'));
    return false;
  }
  const t = system.currentTick;
  if ((cannonCd.get(p.id) ?? 0) > t) return false;
  cannonCd.set(p.id, t + 18);
  const dir = p.getViewDirection();
  const flat = V.flat(dir);
  const muzzle = V.add(ship.location, V.add(V.mul(flat, 2.0), { x: 0, y: 1.0, z: 0 }));
  launch(p, 'bc:cannonball', muzzle, V.norm({ x: dir.x, y: Math.max(dir.y, -0.1) + 0.08, z: dir.z }), 2.3,
    { spell: 'cannon', attr: 'flame', damage: 12, pierce: 0 });
  particle(p.dimension, 'bc:flame_burst', muzzle, { scale: 0.45 });
  particle(p.dimension, 'bc:smoke_burst', muzzle, { scale: 0.6 });
  sound(p.dimension, 'bc.cannon', muzzle, 1.4, 0.95 + Math.random() * 0.1);
  shake(p, 0.25, 0.3);
  if (!isCreative(p)) {
    const inv = p.getComponent('minecraft:inventory')?.container;
    const it = inv?.getItem(p.selectedSlotIndex);
    if (it?.typeId === 'bc:cannonball') {
      if (it.amount > 1) {
        it.amount -= 1;
        inv.setItem(p.selectedSlotIndex, it);
      } else inv.setItem(p.selectedSlotIndex, undefined);
    }
  }
  return true;
}

function cannonBoom(dim, loc, owner, dmg) {
  particle(dim, 'bc:flame_burst', loc, { scale: 0.9 });
  particle(dim, 'bc:smoke_burst', loc, { scale: 0.9 });
  particle(dim, 'bc:rock_debris', loc, { scale: 0.6 });
  sound(dim, 'random.explode', loc, 1, 1.2);
  shakeArea(dim, loc, 10, 0.3, 0.4);
  for (const t of targetsAround(dim, loc, 3.2, owner)) {
    hurt(t, dmg, owner, 'entityExplosion');
    knock(t, V.sub(t.location, loc), 1.2, 0.5);
  }
  // cannons do hurt ships (other than your own)
  for (const s of safe(() => dim.getEntities({ location: loc, maxDistance: 3, type: 'bc:sail_ship' })) ?? []) {
    if (owner && shipOf(owner)?.id === s.id) continue;
    safe(() => s.applyDamage(dmg, { cause: 'entityExplosion' }));
  }
}

registerHandler('bc:cannonball', {
  fx: 'flame',
  entity(m, o, t, loc) {
    cannonBoom(t.dimension, loc, o, m.damage);
  },
  block(m, o, loc, dim) {
    cannonBoom(dim, loc, o, m.damage);
  },
});

export { center };
