// The Abyssal Leviathan: a sea-serpent boss summoned with a Leviathan Lure.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { center, effect, hurt, knock, knockFrom, launch, targetsAround } from '../core/combat.js';
import { anim, particle, rgb, shakeArea, shockwave, sound, title } from '../core/fx.js';
import { V, isCreative, pick, rand, repeat, safe, timer } from '../core/util.js';
import { column } from './structures.js';
import { addWillXp } from './will.js';

/** @type {Map<string, {next:number, bite:number, phase2:boolean, surface:number}>} */
const bosses = new Map();

export function useLure(p) {
  const dim = p.dimension;
  const dir = V.flat(p.getViewDirection());
  const at = V.add(p.location, V.mul(dir, 12));
  const col = column(dim, Math.floor(at.x), Math.floor(at.z));
  if (!col || col.surface - col.floor < 6) {
    safe(() => p.onScreenDisplay.setActionBar('§3The lure needs deep open water in front of you.'));
    return false;
  }
  if (!isCreative(p)) {
    const inv = p.getComponent('minecraft:inventory')?.container;
    const it = inv?.getItem(p.selectedSlotIndex);
    if (it?.typeId === 'bc:leviathan_lure') inv.setItem(p.selectedSlotIndex, undefined);
  }
  const surf = { x: at.x, y: col.surface + 1, z: at.z };
  safe(() => p.sendMessage('§3You blow into the lure... the sea answers.'));
  sound(dim, 'bc.leviathan.roar', surf, 1.5, 0.7);
  shakeArea(dim, surf, 40, 0.25, 3);
  repeat(6, 10, (i) => {
    particle(dim, 'bc:warning_circle', surf, { size: 8 + i, life: 0.7 });
    particle(dim, 'bc:water_splash', V.add(surf, { x: rand(-4, 4), y: 0, z: rand(-4, 4) }), { scale: 1.4 });
  }, () => {
    const e = safe(() => dim.spawnEntity('bc:leviathan', { x: surf.x, y: col.surface - 3, z: surf.z }));
    if (!e) return;
    bosses.set(e.id, { next: system.currentTick + 80, bite: 0, phase2: false, surface: col.surface });
    particle(dim, 'bc:water_splash', surf, { scale: 3 });
    shockwave(dim, surf, 'water', 10);
    anim(e, 'animation.bc.leviathan.roar');
    for (const pl of dim.getPlayers({ location: surf, maxDistance: 64 })) title(pl, '§3§lABYSSAL LEVIATHAN', '§bThe deep has awoken', 60);
  });
  return true;
}

world.afterEvents.entityLoad.subscribe((ev) => {
  if (ev.entity.typeId === 'bc:leviathan' && !bosses.has(ev.entity.id)) {
    const col = column(ev.entity.dimension, Math.floor(ev.entity.location.x), Math.floor(ev.entity.location.z));
    bosses.set(ev.entity.id, { next: system.currentTick + 80, bite: 0, phase2: false, surface: col?.surface ?? 62 });
  }
});
world.afterEvents.entitySpawn.subscribe((ev) => {
  if (ev.entity.typeId === 'bc:leviathan' && !bosses.has(ev.entity.id)) bosses.set(ev.entity.id, { next: system.currentTick + 80, bite: 0, phase2: false, surface: 62 });
});

function target(e) {
  let best;
  let bd = 48;
  for (const p of e.dimension.getPlayers({ location: e.location, maxDistance: 48 })) {
    const gm = safe(() => p.getGameMode());
    if (gm === 'Creative' || gm === 'Spectator') continue;
    const d = V.dist(p.location, e.location);
    if (d < bd) {
      bd = d;
      best = p;
    }
  }
  return best;
}

function attack(e, st, t) {
  const dim = e.dimension;
  const move = pick(st.phase2 ? ['volley', 'slam', 'slam', 'roar'] : ['volley', 'slam', 'volley']);
  if (move === 'volley') {
    anim(e, 'animation.bc.leviathan.roar');
    const from = V.add(e.location, { x: 0, y: 2.5, z: 0 });
    const n = st.phase2 ? 7 : 5;
    for (let i = 0; i < n; i++) {
      timer(4 + i * 3, () => {
        const tgt = target(e);
        if (!tgt) return;
        launch(e, 'bc:water_orb', from, V.yaw(V.sub(center(tgt), from), rand(-8, 8)), 1.6, { spell: 'leviathan', attr: 'water', damage: 7, pierce: 0 });
      });
    }
    sound(dim, 'bc.water.surge', from, 1.5, 0.6);
  } else if (move === 'slam') {
    const tgt = target(e);
    if (!tgt) return;
    const spot = { ...tgt.location };
    particle(dim, 'bc:warning_circle', spot, { size: 9, life: 1.2 });
    timer(24, () => {
      particle(dim, 'bc:water_splash', spot, { scale: 2.5 });
      shockwave(dim, spot, 'water', 6);
      sound(dim, 'random.splash', spot, 2, 0.5);
      shakeArea(dim, spot, 16, 0.5, 0.6);
      for (const v of targetsAround(dim, spot, 4.5, e)) {
        hurt(v, st.phase2 ? 15 : 11, e);
        knock(v, { x: 0, y: 0, z: 0 }, 0, 1.0);
      }
      for (const s of safe(() => dim.getEntities({ location: spot, maxDistance: 5, type: 'bc:sail_ship' })) ?? []) safe(() => s.applyDamage(25, { cause: 'entityAttack' }));
    });
  } else {
    anim(e, 'animation.bc.leviathan.roar');
    sound(dim, 'bc.leviathan.roar', e.location, 2, 0.8);
    shockwave(dim, e.location, 'water', 12);
    for (const v of targetsAround(dim, e.location, 14, e)) {
      effect(v, 'mining_fatigue', 6, 2);
      effect(v, 'slowness', 4, 1);
    }
    for (let i = 0; i < 2; i++) safe(() => dim.spawnEntity('minecraft:drowned', V.add(e.location, { x: rand(-4, 4), y: 1, z: rand(-4, 4) })));
  }
}

system.runInterval(() => {
  const t = system.currentTick;
  for (const [id, st] of bosses) {
    const e = world.getEntity(id);
    if (!e) {
      bosses.delete(id);
      continue;
    }
    safe(() => {
      const hp = e.getComponent('minecraft:health');
      if (hp && !st.phase2 && hp.currentValue < hp.effectiveMax * 0.5) {
        st.phase2 = true;
        anim(e, 'animation.bc.leviathan.roar');
        sound(e.dimension, 'bc.leviathan.roar', e.location, 2, 0.6);
        for (const pl of e.dimension.getPlayers({ location: e.location, maxDistance: 64 })) title(pl, '§3The Leviathan rages', '§bThe whole sea churns!', 40);
      }
      const tgt = target(e);
      if (!tgt) return;
      // swim toward the target but stay under the surface
      const goal = { x: tgt.location.x, y: Math.min(tgt.location.y - 1.5, st.surface - 1.5), z: tgt.location.z };
      const d = V.sub(goal, e.location);
      const dist = V.len(d);
      if (dist > 3) safe(() => e.applyImpulse(V.mul(V.norm(d), st.phase2 ? 0.09 : 0.065)));
      const v = e.getVelocity();
      if (V.len(v) > 0.6) safe(() => e.applyImpulse(V.mul(v, -0.2)));
      if (e.location.y > st.surface + 1) safe(() => e.applyImpulse({ x: 0, y: -0.08, z: 0 }));
      safe(() => e.setRotation({ x: 0, y: (Math.atan2(-d.x, d.z) * 180) / Math.PI }));
      if (V.dist(tgt.location, e.location) < 6.5 && st.bite <= t) {
        st.bite = t + (st.phase2 ? 24 : 34);
        anim(e, 'animation.bc.leviathan.bite');
        timer(5, () => {
          if (V.dist(tgt.location, e.location) > 8) return;
          hurt(tgt, st.phase2 ? 18 : 14, e);
          knockFrom(tgt, e.location, 1.5, 0.5);
          particle(e.dimension, 'bc:water_splash', center(tgt), { scale: 0.8 });
        });
      }
      if (st.next <= t) {
        st.next = t + (st.phase2 ? 90 : 130);
        attack(e, st, t);
      }
    }, 'leviathan');
  }
}, 2);

world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const e = ev.deadEntity;
  if (e.typeId !== 'bc:leviathan') return;
  bosses.delete(e.id);
  const dim = e.dimension;
  const loc = e.location;
  dim.spawnItem(new ItemStack(`bc:fruit_${pick(DATA.fruitOrder)}`, 1), loc);
  particle(dim, 'bc:water_splash', loc, { scale: 3 });
  shockwave(dim, loc, 'water', 14);
  sound(dim, 'bc.leviathan.roar', loc, 2, 0.5);
  for (const p of dim.getPlayers({ location: loc, maxDistance: 64 })) title(p, '§3§lLEVIATHAN SLAIN', '§bThe sea grows calm', 70);
  const k = ev.damageSource.damagingEntity;
  if (k instanceof Player) addWillXp(k, 0);
}, 'levDeath'));

export { rgb };
