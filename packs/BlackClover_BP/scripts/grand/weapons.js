// Pirate weapons (cutlass whirl, flintlock, grappling harpoon) and the Hearty Roast.
import { system, world } from '@minecraft/server';
import { center, effect, hurt, knock, launch, muzzle, targetsAround } from '../core/combat.js';
import { anim, particle, sound } from '../core/fx.js';
import { V, isCreative, safe } from '../core/util.js';
import { registerHandler } from '../magic/projectiles.js';

const cd = new Map();

function ready(p, key, ticks) {
  const t = system.currentTick;
  const k = `${p.id}:${key}`;
  if ((cd.get(k) ?? 0) > t) return false;
  cd.set(k, t + ticks);
  return true;
}

function takeOne(p, typeId) {
  if (isCreative(p)) return true;
  const inv = p.getComponent('minecraft:inventory')?.container;
  if (!inv) return false;
  for (let i = 0; i < inv.size; i++) {
    const it = inv.getItem(i);
    if (it?.typeId !== typeId) continue;
    if (it.amount > 1) {
      it.amount -= 1;
      inv.setItem(i, it);
    } else inv.setItem(i, undefined);
    return true;
  }
  return false;
}

export function useWeapon(p, id) {
  const dim = p.dimension;
  if (id === 'bc:cutlass') {
    if (!ready(p, id, 60)) return;
    anim(p, 'animation.bc.player.cast_sweep');
    sound(dim, 'bc.wind.gust', p.location, 0.6, 1.7);
    for (let k = 0; k < 6; k++) {
      const a = (k / 6) * Math.PI * 2;
      particle(dim, 'bc:slash_fx', { x: p.location.x + Math.cos(a) * 2, y: p.location.y + 1, z: p.location.z + Math.sin(a) * 2 }, { size: 2, rot: k * 60 });
    }
    for (const t of targetsAround(dim, p.location, 3.2, p)) {
      hurt(t, 6, p);
      knock(t, V.sub(t.location, p.location), 0.8, 0.2);
    }
  } else if (id === 'bc:flintlock') {
    if (!ready(p, id, 32)) return;
    if (!takeOne(p, 'bc:lead_shot')) {
      safe(() => p.onScreenDisplay.setActionBar('§7Out of lead shot. §8(iron nugget + gunpowder)'));
      sound(dim, 'random.click', p.location, 1, 1.4);
      return;
    }
    const at = muzzle(p, 1.2, 0.2);
    launch(p, 'bc:lead_shot', at, p.getViewDirection(), 3.4, { spell: 'flintlock', attr: 'steel', damage: 10, pierce: 0 });
    particle(dim, 'bc:smoke_burst', at, { scale: 0.35 });
    particle(dim, 'bc:spark', at, { color: { red: 1, green: 0.8, blue: 0.4 } });
    sound(dim, 'bc.pistol', at, 1.2, 0.95 + Math.random() * 0.1);
    anim(p, 'animation.bc.player.cast_forward');
  } else if (id === 'bc:harpoon') {
    if (!ready(p, id, 40)) return;
    launch(p, 'bc:harpoon_bolt', muzzle(p, 1.2, 0.3), p.getViewDirection(), 2.3, { spell: 'harpoon', attr: 'water', damage: 8, pierce: 0 });
    sound(dim, 'item.trident.throw', p.location, 1, 1);
    anim(p, 'animation.bc.player.cast_forward');
  }
}

registerHandler('bc:lead_shot', {
  fx: 'light',
  entity(m, o, t, loc) {
    hurt(t, m.damage, o, 'projectile');
    particle(t.dimension, 'bc:spark', loc);
  },
  block(m, o, loc, dim) {
    particle(dim, 'bc:smoke_burst', loc, { scale: 0.2 });
  },
});

registerHandler('bc:harpoon_bolt', {
  fx: 'water',
  // spear an enemy and haul it in
  entity(m, o, t, loc) {
    hurt(t, m.damage, o);
    if (o) knock(t, V.sub(o.location, t.location), Math.min(2.6, V.dist(o.location, t.location) * 0.22), 0.4);
    sound(t.dimension, 'random.splash', loc, 0.6, 1.4);
  },
  // hit a wall: reel yourself in (grapple)
  block(m, o, loc, dim) {
    if (!o) return;
    const d = V.sub(loc, o.location);
    knock(o, d, Math.min(3.6, V.len(d) * 0.2 + 0.6), Math.min(1.1, Math.max(0.35, d.y * 0.12 + 0.4)));
    particle(dim, 'bc:rock_debris', loc, { scale: 0.3 });
  },
});

world.afterEvents.itemCompleteUse.subscribe((ev) => safe(() => {
  if (ev.itemStack.typeId !== 'bc:hearty_roast') return;
  const p = ev.source;
  effect(p, 'regeneration', 6, 1);
  effect(p, 'absorption', 30, 0);
  sound(p.dimension, 'random.burp', p.location, 1, 1);
  particle(p.dimension, 'bc:heal', center(p));
}, 'roast'));
