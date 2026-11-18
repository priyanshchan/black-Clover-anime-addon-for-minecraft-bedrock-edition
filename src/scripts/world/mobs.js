// Dark Disciples and the Devil boss.
import { Player, system, world } from '@minecraft/server';
import { center, effect, groundBelow, hurt, knock, knockFrom, launch, targetsAround } from '../core/combat.js';
import { anim, burst, particle, rgb, shakeArea, shockwave, sound, title } from '../core/fx.js';
import { V, alive, pick, rand, repeat, safe, timer } from '../core/util.js';

// ------------------------------------------------------------------------ casting anims
world.afterEvents.entitySpawn.subscribe((ev) => safe(() => {
  const e = ev.entity;
  const id = e.typeId;
  if (id !== 'bc:dark_bolt' && id !== 'bc:devil_orb') return;
  const owner = e.getComponent('minecraft:projectile')?.owner;
  if (!owner || !alive(owner)) return;
  if (owner.typeId === 'bc:dark_disciple') {
    anim(owner, 'animation.bc.dark_disciple.cast');
    particle(owner.dimension, 'bc:magic_circle', V.add(owner.getHeadLocation(), V.mul(owner.getViewDirection(), 1)), {
      color: rgb('a066e0'), size: 1.3, dir: owner.getViewDirection(),
    });
    sound(owner.dimension, 'mob.evocation_illager.cast_spell', owner.location, 0.7, 1.3);
  } else if (owner.typeId === 'bc:devil') {
    anim(owner, 'animation.bc.devil.cast');
  }
}, 'spawnFx'));

// ------------------------------------------------------------------------ disciple blink
const blinkCd = new Map();
world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const e = ev.hurtEntity;
  if (e.typeId !== 'bc:dark_disciple' || !alive(e)) return;
  const hp = e.getComponent('minecraft:health');
  const attacker = ev.damageSource.damagingEntity;
  if (!hp || !attacker || hp.currentValue > hp.effectiveMax * 0.6) return;
  const t = system.currentTick;
  if ((blinkCd.get(e.id) ?? 0) > t || Math.random() > 0.45) return;
  blinkCd.set(e.id, t + 120);
  const behind = V.add(attacker.location, V.mul(V.flat(attacker.getViewDirection()), -3));
  const dest = groundBelow(e.dimension, V.add(behind, { x: 0, y: 2, z: 0 }), 5);
  particle(e.dimension, 'bc:dark_mist', e.location, { scale: 0.6 });
  particle(e.dimension, 'bc:burst_dark', center(e), { scale: 0.8, color: rgb('2a1040') });
  sound(e.dimension, 'mob.endermen.portal', e.location, 1, 0.8);
  e.teleport(dest, { keepVelocity: false, facingLocation: attacker.location });
  particle(e.dimension, 'bc:burst_dark', center(e), { scale: 0.8, color: rgb('2a1040') });
}, 'blink'));

// ------------------------------------------------------------------------ the Devil
/** @type {Map<string, {nextSpecial:number, nextMelee:number, phase2:boolean, angle:number}>} */
const devils = new Map();

function devilState(e) {
  let d = devils.get(e.id);
  if (!d) {
    d = { nextSpecial: system.currentTick + 120, nextMelee: 0, phase2: false, angle: Math.random() * 6.28 };
    devils.set(e.id, d);
  }
  return d;
}

export function summonDevil(dim, loc, summoner) {
  particle(dim, 'bc:magic_circle_dark', loc, { size: 9, life: 3.2 });
  particle(dim, 'bc:warning_circle', loc, { size: 7, life: 3 });
  sound(dim, 'bc.devil.roar', loc, 1.6, 0.6);
  shakeArea(dim, loc, 30, 0.3, 3);
  repeat(6, 10, (i) => {
    particle(dim, 'bc:dark_lightning', V.add(loc, { x: rand(-5, 5), y: 0, z: rand(-5, 5) }));
    particle(dim, 'bc:black_aura', loc, { scale: 1 + i * 0.3 });
    sound(dim, 'ambient.weather.thunder', loc, 0.5, 0.6);
  }, () => {
    const e = safe(() => dim.spawnEntity('bc:devil', V.add(loc, { x: 0, y: 0.5, z: 0 })));
    if (!e) return;
    burst(dim, V.add(loc, { x: 0, y: 2, z: 0 }), 'anti', 3);
    shockwave(dim, loc, 'anti', 10);
    sound(dim, 'mob.wither.spawn', loc, 1.2, 0.8);
    for (const p of dim.getPlayers({ location: loc, maxDistance: 48 })) title(p, '§4§lDEVIL', '§cA devil has crossed into this world!', 60);
    devilState(e);
  });
}

function nearestPlayer(e, range) {
  let best;
  let bd = range;
  for (const p of e.dimension.getPlayers({ location: e.location, maxDistance: range })) {
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

function devilSpecial(e, d, target) {
  const dim = e.dimension;
  const minions = dim.getEntities({ location: e.location, maxDistance: 24, type: 'bc:dark_disciple' }).length;
  const moves = ['lightning', 'roar', 'orbs', d.phase2 ? 'lightning' : 'orbs'];
  if (minions < 4) moves.push('summon');
  const move = pick(moves);
  if (move === 'lightning') {
    anim(e, 'animation.bc.devil.cast');
    const victims = dim.getPlayers({ location: e.location, maxDistance: 32 }).filter((p) => {
      const gm = safe(() => p.getGameMode());
      return gm !== 'Creative' && gm !== 'Spectator';
    });
    for (const v of victims) {
      const spot = groundBelow(dim, V.add(v.location, { x: 0, y: 1, z: 0 }), 6);
      particle(dim, 'bc:warning_circle', spot, { size: 4.5, life: 1.1 });
      timer(22, () => {
        particle(dim, 'bc:dark_lightning', spot);
        particle(dim, 'bc:anti_burst', V.add(spot, { x: 0, y: 0.5, z: 0 }), { scale: 1.2 });
        sound(dim, 'ambient.weather.thunder', spot, 0.8, 0.7);
        for (const t of targetsAround(dim, spot, 2.6, e)) {
          if (t.typeId === 'bc:devil' || t.typeId === 'bc:dark_disciple') continue;
          hurt(t, d.phase2 ? 16 : 12, e, 'lightning');
          effect(t, 'darkness', 4, 0);
        }
      });
    }
  } else if (move === 'roar') {
    anim(e, 'animation.bc.devil.cast');
    sound(dim, 'bc.devil.roar', e.location, 2, 0.8);
    shockwave(dim, e.location, 'anti', 9);
    shakeArea(dim, e.location, 20, 0.6, 1);
    for (const t of targetsAround(dim, e.location, 9, e)) {
      if (t.typeId === 'bc:dark_disciple') continue;
      hurt(t, d.phase2 ? 10 : 7, e, 'magic');
      knockFrom(t, e.location, 2.6, 0.7);
      effect(t, 'darkness', 5, 0);
      effect(t, 'weakness', 5, 0);
    }
  } else if (move === 'orbs') {
    anim(e, 'animation.bc.devil.cast');
    const n = d.phase2 ? 7 : 5;
    const from = V.add(e.location, { x: 0, y: 3.2, z: 0 });
    const dir = V.norm(V.sub(center(target), from));
    for (let i = 0; i < n; i++) {
      timer(i * 3, () => alive(e) && launch(e, 'bc:devil_orb', from, V.yaw(dir, (i - (n - 1) / 2) * 11), 1.0,
        { spell: 'devil_orb', attr: 'anti', damage: 0, pierce: 0 }));
    }
    sound(dim, 'mob.wither.shoot', from, 1.2, 0.6);
  } else {
    anim(e, 'animation.bc.devil.cast');
    sound(dim, 'mob.evocation_illager.prepare_summon', e.location, 1.2, 0.7);
    for (let i = 0; i < 2; i++) {
      const spot = groundBelow(dim, V.add(e.location, { x: rand(-5, 5), y: 1, z: rand(-5, 5) }), 10);
      particle(dim, 'bc:magic_circle_dark', spot, { size: 2.5, life: 1.2 });
      timer(18, () => {
        safe(() => dim.spawnEntity('bc:dark_disciple', spot));
        particle(dim, 'bc:dark_mist', spot, { scale: 0.6 });
      });
    }
  }
}

system.runInterval(() => {
  for (const id of [...devils.keys()]) {
    const e = world.getEntity(id);
    if (!e || !alive(e)) devils.delete(id);
  }
  for (const [id, d] of devils) {
    const e = world.getEntity(id);
    if (!e) continue;
    safe(() => tickDevil(e, d), 'devil');
  }
}, 2);

function tickDevil(e, d) {
  const t = system.currentTick;
  const hp = e.getComponent('minecraft:health');
  if (hp && !d.phase2 && hp.currentValue < hp.effectiveMax * 0.5) {
    d.phase2 = true;
    anim(e, 'animation.bc.devil.cast');
    sound(e.dimension, 'bc.devil.roar', e.location, 2, 0.6);
    shockwave(e.dimension, e.location, 'anti', 12);
    effect(e, 'speed', 9999, 1, false);
    effect(e, 'resistance', 9999, 0, false);
    for (const p of e.dimension.getPlayers({ location: e.location, maxDistance: 48 })) title(p, '§4The Devil awakens', '§cIts true power is unleashed!', 50);
  }
  if (d.phase2 && t % 6 === 0) particle(e.dimension, 'bc:anti_crackle', V.add(e.location, { x: 0, y: 2.2, z: 0 }), { radius: 1.6 });
  const target = nearestPlayer(e, 40);
  if (!target) return;
  // hover around the target
  d.angle += d.phase2 ? 0.035 : 0.022;
  const radius = 6.5;
  const goal = V.add(target.location, { x: Math.cos(d.angle) * radius, y: 2.5, z: Math.sin(d.angle) * radius });
  const delta = V.sub(goal, e.location);
  const dist = V.len(delta);
  if (dist > 28) {
    safe(() => e.teleport(goal, { facingLocation: target.location }));
    particle(e.dimension, 'bc:burst_dark', center(e), { scale: 1.5, color: rgb('300408') });
  } else if (dist > 0.5) {
    const speed = Math.min(d.phase2 ? 0.16 : 0.11, dist * 0.04);
    safe(() => e.applyImpulse(V.mul(V.norm(delta), speed)));
  }
  safe(() => e.setRotation({ x: 0, y: (Math.atan2(-(target.location.x - e.location.x), target.location.z - e.location.z) * 180) / Math.PI }));
  // claw swipe when close
  const close = V.dist(target.location, e.location);
  if (close < 4.5 && d.nextMelee <= t) {
    d.nextMelee = t + (d.phase2 ? 24 : 34);
    anim(e, 'animation.bc.devil.attack');
    timer(5, () => {
      if (!alive(e) || !alive(target) || V.dist(target.location, e.location) > 5.5) return;
      hurt(target, d.phase2 ? 15 : 11, e);
      knockFrom(target, e.location, 1.6, 0.45);
      particle(e.dimension, 'bc:slash_fx', center(target), { size: 3.5, rot: rand(-50, 50) });
      sound(e.dimension, 'mob.ravager.bite', target.location, 1, 0.7);
    });
  }
  if (d.nextSpecial <= t) {
    d.nextSpecial = t + (d.phase2 ? 100 : 150) + Math.floor(rand(0, 60));
    devilSpecial(e, d, target);
  }
}

// discover devils after reloads
world.afterEvents.entitySpawn.subscribe((ev) => {
  if (ev.entity.typeId === 'bc:devil') safe(() => devilState(ev.entity));
});
world.afterEvents.entityLoad.subscribe((ev) => {
  if (ev.entity.typeId === 'bc:devil') safe(() => devilState(ev.entity));
});

world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const e = ev.deadEntity;
  if (e.typeId !== 'bc:devil') return;
  const loc = e.location;
  const dim = e.dimension;
  devils.delete(e.id);
  burst(dim, V.add(loc, { x: 0, y: 2, z: 0 }), 'anti', 3.5);
  shockwave(dim, loc, 'anti', 14);
  particle(dim, 'bc:magic_circle_dark', loc, { size: 10, life: 3 });
  sound(dim, 'bc.devil.roar', loc, 2, 0.5);
  sound(dim, 'random.explode', loc, 1.5, 0.6);
  shakeArea(dim, loc, 40, 0.7, 1.5);
  for (const p of dim.getPlayers({ location: loc, maxDistance: 64 })) title(p, '§6§lDEVIL DEFEATED', '§eThe contract is broken', 70);
}, 'devilDeath'));

export { knock, Player };
