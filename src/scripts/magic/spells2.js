// Wave 3 spells: Spatial, Earth, Steel and Mirror magic.
import { Player, system, world } from '@minecraft/server';
import {
  HOSTILE_PROJECTILES, aimEntity, aimPoint, center, effect, groundBelow, hurt, knock, knockFrom, launch, muzzle, projectiles, targetsAlong, targetsAround,
} from '../core/combat.js';
import { COLORS, anim, beam, groundCircle, particle, rgb, shakeArea, shockwave, sound } from '../core/fx.js';
import { V, alive, rand, repeat, safe, timer, yawOf } from '../core/util.js';
import { registerHandler } from './projectiles.js';

const up = { x: 0, y: 1, z: 0 };
const MUD = rgb('6b4a2a');

/** @typedef {import('./spells.js').CastCtx} CastCtx */

// ------------------------------------------------------------------ warp gates
/** @type {{a: any, b: any, until: number, cd: Map<string, number>}[]} */
const gatePairs = [];

function ownedAlly(owner, e) {
  return e.getDynamicProperty('bc:owner') === owner.id;
}

/** Owner-bound summon helper (golems, mirror images). */
function summonAlly(c, type, count, name) {
  for (let i = 0; i < count; i++) {
    const a = (i / count) * Math.PI * 2 + rand(0, 1);
    const at = groundBelow(c.dim, V.add(c.p.location, { x: Math.cos(a) * 2.2, y: 2, z: Math.sin(a) * 2.2 }), 6);
    timer(4 + i * 4, () => {
      const e = safe(() => c.dim.spawnEntity(type, at));
      if (!e) return;
      safe(() => e.setDynamicProperty('bc:owner', c.p.id));
      e.nameTag = `§7${c.p.name}'s ${name}`;
      particle(c.dim, 'bc:burst', V.add(at, up), { color: COLORS[c.attr], scale: 0.8 });
    });
  }
}

/** @type {Record<string, (c: CastCtx) => boolean | void>} */
export const SPELLS2 = {
  // ================================================================= SPATIAL
  warp_gate(c) {
    const dir = V.flat(c.p.getViewDirection());
    const { point } = aimPoint(c.p, 30);
    const at = groundBelow(c.dim, V.add(point, up), 8);
    const here = V.add(c.p.location, V.mul(dir, 1.6));
    if (V.dist(at, here) < 4) return false;
    const yaw = yawOf(dir);
    const a = safe(() => c.dim.spawnEntity('bc:warp_gate', here));
    const b = safe(() => c.dim.spawnEntity('bc:warp_gate', at));
    if (!a || !b) return false;
    safe(() => a.setRotation({ x: 0, y: yaw }));
    safe(() => b.setRotation({ x: 0, y: yaw }));
    gatePairs.push({ a, b, until: system.currentTick + 400, cd: new Map([[c.p.id, system.currentTick + 20]]) });
    anim(c.p, 'animation.bc.player.cast_forward');
    sound(c.dim, 'bc.portal', here, 1, 1);
    sound(c.dim, 'bc.portal', at, 1, 1);
  },
  space_cleave(c) {
    anim(c.p, 'animation.bc.player.cast_sweep');
    const head = c.p.getHeadLocation();
    const dir = c.p.getViewDirection();
    const a = V.add(head, V.mul(dir, 1));
    const b = V.add(head, V.mul(dir, 24));
    sound(c.dim, 'bc.portal', head, 1, 1.6);
    beam(c.dim, a, b, 'spatial', 0.4, 0.8, 0.4);
    for (let t = 2; t < 24; t += 3) particle(c.dim, 'bc:burst_spark', V.add(head, V.mul(dir, t)), { color: COLORS.spatial, scale: 0.4 });
    for (const t of targetsAlong(c.dim, a, b, 1.6, c.p)) {
      hurt(t, 13 * c.pw, c.p, 'magic');
      particle(c.dim, 'bc:burst', center(t), { color: COLORS.spatial, scale: 0.6 });
    }
  },
  pocket_dimension(c) {
    const t0 = aimEntity(c.p, 30);
    const at = t0 ? t0.location : aimPoint(c.p, 26).point;
    const victims = targetsAround(c.dim, at, 4.5, c.p);
    if (!victims.length) return false;
    anim(c.p, 'animation.bc.player.cast_forward');
    sound(c.dim, 'bc.portal', at, 1.2, 0.7);
    for (const v of victims) {
      particle(c.dim, 'bc:magic_circle_ground', v.location, { color: COLORS.spatial, size: 2.5, life: 0.6 });
      hurt(v, 6 * c.pw, c.p, 'magic');
      if (safe(() => v.matches({ families: ['boss'] }))) continue;
      const sky = V.add(v.location, { x: 0, y: 14, z: 0 });
      safe(() => v.teleport(sky, { keepVelocity: false }));
      particle(c.dim, 'bc:burst', sky, { color: COLORS.spatial, scale: 0.8 });
    }
  },
  gate_barrage(c) {
    const target = aimEntity(c.p, 32);
    const goal = target ? center(target) : aimPoint(c.p, 28).point;
    anim(c.p, 'animation.bc.player.cast_raise');
    const gates = [];
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2;
      gates.push({ x: goal.x + Math.cos(a) * 5, y: goal.y + rand(0.5, 3.5), z: goal.z + Math.sin(a) * 5 });
    }
    for (const g of gates) particle(c.dim, 'bc:magic_circle', g, { color: COLORS.spatial, size: 1.6, life: 2.2, dir: V.norm(V.sub(goal, g)) });
    sound(c.dim, 'bc.portal', goal, 1.4, 0.8);
    repeat(12, 4, (i) => {
      const g = gates[i % gates.length];
      const now = target && alive(target) ? center(target) : goal;
      beam(c.dim, g, now, 'spatial', 0.45, 0.6, 0.3);
      for (const v of targetsAround(c.dim, now, 1.8, c.p)) hurt(v, 5 * c.pw, c.p, 'magic');
    });
  },

  // ================================================================= EARTH
  stone_bullets(c) {
    anim(c.p, 'animation.bc.player.cast_forward');
    sound(c.dim, 'bc.stone.crack', c.p.location, 0.7, 1.4);
    const dir = c.p.getViewDirection();
    for (const off of [-6, 0, 6]) {
      launch(c.p, 'bc:boulder', muzzle(c.p, 1.3, 0.4), V.yaw(dir, off), 1.9, { spell: 'stone_bullets', attr: 'earth', damage: 6 * c.pw, pierce: 0 });
    }
  },
  mud_mire(c) {
    const { point } = aimPoint(c.p, 24);
    const at = groundBelow(c.dim, V.add(point, up), 8);
    anim(c.p, 'animation.bc.player.cast_forward');
    groundCircle(c.dim, at, 'earth', 9, 6);
    sound(c.dim, 'bc.water.surge', at, 1, 0.5);
    repeat(12, 10, () => {
      for (let k = 0; k < 3; k++) particle(c.dim, 'bc:burst', V.add(at, { x: rand(-4, 4), y: 0.3, z: rand(-4, 4) }), { color: MUD, scale: 0.35 });
      for (const v of targetsAround(c.dim, at, 4.5, c.p)) {
        effect(v, 'slowness', 1, 3, false);
        hurt(v, 2 * c.pw, c.p, 'magic');
      }
    });
  },
  earth_golem(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    sound(c.dim, 'bc.golem.slam', c.p.location, 1, 1.2);
    particle(c.dim, 'bc:rock_debris', V.add(c.p.location, up), { scale: 1 });
    summonAlly(c, 'bc:earth_golem', 1, 'Earth Golem');
  },
  continental_quake(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    const at = c.p.location;
    groundCircle(c.dim, at, 'earth', 12, 1.8);
    shakeArea(c.dim, at, 30, 0.7, 1.6);
    const hit = new Set();
    for (const [k, r] of [[0, 4], [1, 8], [2, 12]]) {
      timer(k * 8, () => {
        sound(c.dim, 'bc.golem.slam', at, 1.4, 0.8 + k * 0.1);
        shockwave(c.dim, at, 'earth', r);
        for (let i = 0; i < 10 + k * 6; i++) {
          const a = (i / (10 + k * 6)) * Math.PI * 2;
          particle(c.dim, 'bc:rock_debris', { x: at.x + Math.cos(a) * r, y: at.y + 0.3, z: at.z + Math.sin(a) * r }, { scale: 0.5 });
        }
        for (const v of targetsAround(c.dim, at, r + 1, c.p)) {
          if (hit.has(v.id) && k < 2) continue;
          hit.add(v.id);
          hurt(v, 14 * c.pw, c.p);
          knock(v, up, 0, 1.0);
        }
      });
    }
  },

  // ================================================================= STEEL
  steel_lances(c) {
    anim(c.p, 'animation.bc.player.cast_forward');
    sound(c.dim, 'random.anvil_land', c.p.location, 0.3, 1.8);
    const dir = c.p.getViewDirection();
    for (const off of [-5, 0, 5]) {
      launch(c.p, 'bc:steel_lance', muzzle(c.p, 1.2, 0.3), V.yaw(dir, off), 2.6, { spell: 'steel_lances', attr: 'steel', damage: 7 * c.pw, pierce: 1 });
    }
  },
  iron_bulwark(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    effect(c.p, 'resistance', 6, 2, false);
    effect(c.p, 'slowness', 6, 0, false);
    c.p.setDynamicProperty('bc:bulwark_until', system.currentTick + 120);
    particle(c.dim, 'bc:shard_burst', V.add(c.p.location, up), { color: COLORS.steel, scale: 1 });
    sound(c.dim, 'random.anvil_land', c.p.location, 0.6, 0.8);
  },
  blade_rain(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    const { point } = aimPoint(c.p, 28);
    const base = groundBelow(c.dim, V.add(point, up), 10);
    groundCircle(c.dim, base, 'steel', 10, 2.2);
    repeat(12, 3, () => {
      if (!alive(c.p)) return false;
      for (let k = 0; k < 2; k++) {
        const a = Math.random() * Math.PI * 2;
        const r = Math.sqrt(Math.random()) * 5;
        const from = { x: base.x + Math.cos(a) * r, y: base.y + 12, z: base.z + Math.sin(a) * r };
        launch(c.p, 'bc:steel_lance', from, { x: 0, y: -1, z: 0 }, 2.4, { spell: 'blade_rain', attr: 'steel', damage: 7 * c.pw, pierce: 0 });
      }
    });
  },
  steel_maelstrom(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    sound(c.dim, 'random.anvil_land', c.p.location, 0.6, 0.6);
    repeat(40, 3, (i) => {
      if (!alive(c.p)) return false;
      const at = c.p.location;
      for (let k = 0; k < 6; k++) {
        const a = i * 0.5 + (k * Math.PI) / 3;
        particle(c.dim, 'bc:shard_burst', { x: at.x + Math.cos(a) * 3.2, y: at.y + 1 + (k % 2), z: at.z + Math.sin(a) * 3.2 }, { color: COLORS.steel, scale: 0.25 });
      }
      for (const v of targetsAround(c.dim, V.add(at, up), 4.5, c.p)) hurt(v, 3 * c.pw, c.p);
      if (i % 8 === 0) sound(c.dim, 'random.glass', at, 0.4, 1.8);
    });
  },

  // ================================================================= MIRROR
  mirror_shot(c) {
    anim(c.p, 'animation.bc.player.cast_forward');
    const head = c.p.getHeadLocation();
    const dir = c.p.getViewDirection();
    const t0 = aimEntity(c.p, 32);
    const end = t0 ? center(t0) : aimPoint(c.p, 32).point;
    const a = V.add(head, V.mul(dir, 0.8));
    beam(c.dim, a, end, 'mirror', 0.4, 0.7, 0.4);
    sound(c.dim, 'bc.mirror', head, 1, 1.2);
    const hitIds = new Set();
    for (const t of targetsAlong(c.dim, a, end, 1.2, c.p)) {
      hurt(t, 9 * c.pw, c.p, 'magic');
      hitIds.add(t.id);
    }
    const bounce = targetsAround(c.dim, end, 10, c.p).filter((e) => !hitIds.has(e.id))
      .sort((x, y) => V.dist(x.location, end) - V.dist(y.location, end))[0];
    particle(c.dim, 'bc:shard_burst', end, { color: COLORS.mirror, scale: 0.5 });
    if (bounce) {
      timer(2, () => {
        beam(c.dim, end, center(bounce), 'mirror', 0.4, 0.6, 0.4);
        hurt(bounce, 7 * c.pw, c.p, 'magic');
      });
    }
  },
  mirror_image(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    sound(c.dim, 'bc.mirror', c.p.location, 1, 0.8);
    summonAlly(c, 'bc:mirror_clone', 2, 'Mirror Image');
  },
  reflection_barrier(c) {
    anim(c.p, 'animation.bc.player.guard');
    c.p.setDynamicProperty('bc:reflect_until', system.currentTick + 140);
    particle(c.dim, 'bc:shockwave', c.p.location, { radius: 3, color: COLORS.mirror });
    sound(c.dim, 'bc.mirror', c.p.location, 1, 1.4);
  },
  kaleidoscope(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    const t0 = aimEntity(c.p, 30);
    const goal = t0 ? t0.location : aimPoint(c.p, 26).point;
    const panes = [];
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      panes.push({ x: goal.x + Math.cos(a) * 5, y: goal.y + 1 + (i % 3), z: goal.z + Math.sin(a) * 5 });
    }
    for (const p of panes) particle(c.dim, 'bc:magic_circle', p, { color: COLORS.mirror, size: 1.4, life: 2.2, dir: V.norm(V.sub(goal, p)) });
    sound(c.dim, 'bc.mirror', goal, 1.6, 0.7);
    repeat(10, 4, (i) => {
      const mid = V.add(goal, { x: 0, y: 1, z: 0 });
      for (let k = i % 2; k < panes.length; k += 2) beam(c.dim, panes[k], mid, 'mirror', 0.6, 0.45, 0.25);
      for (const v of targetsAround(c.dim, mid, 3.8, c.p)) {
        hurt(v, 4 * c.pw, c.p, 'magic');
        effect(v, 'blindness', 1.5, 0, false);
      }
    });
  },
};

// ------------------------------------------------------------------ steel lance hits
registerHandler('bc:steel_lance', {
  fx: 'light',
  entity(m, o, t, loc) {
    hurt(t, m.damage, o);
    particle(t.dimension, 'bc:shard_burst', loc, { color: COLORS.steel, scale: 0.4 });
    knock(t, m.vel, 0.5, 0.15);
  },
  block(m, o, loc, dim) {
    particle(dim, 'bc:shard_burst', loc, { color: COLORS.steel, scale: 0.4 });
    if (m.spell === 'blade_rain') for (const t of targetsAround(dim, loc, 1.6, o)) hurt(t, m.damage * 0.6, o);
  },
}, true);

// ------------------------------------------------------------------ gates, reflection, bulwark
system.runInterval(() => {
  const t = system.currentTick;
  for (let i = gatePairs.length - 1; i >= 0; i--) {
    const g = gatePairs[i];
    if (t > g.until || !alive(g.a) || !alive(g.b)) {
      for (const e of [g.a, g.b]) if (alive(e)) safe(() => e.remove());
      gatePairs.splice(i, 1);
      continue;
    }
    for (const [from, to] of [[g.a, g.b], [g.b, g.a]]) {
      safe(() => {
        const c = V.add(from.location, up);
        for (const e of from.dimension.getEntities({ location: c, maxDistance: 1.3, excludeFamilies: ['bc_spell'] })) {
          if ((g.cd.get(e.id) ?? 0) > t) continue;
          g.cd.set(e.id, t + 40);
          const dest = V.add(to.location, { x: 0, y: 0.2, z: 0 });
          safe(() => e.teleport(dest, { keepVelocity: true }));
          particle(from.dimension, 'bc:burst', c, { color: COLORS.spatial, scale: 0.6 });
          particle(to.dimension, 'bc:burst', V.add(to.location, up), { color: COLORS.spatial, scale: 0.6 });
          sound(to.dimension, 'bc.portal', to.location, 0.7, 1.5);
        }
      });
    }
  }
  // reflection barrier
  for (const p of world.getAllPlayers()) {
    const until = p.getDynamicProperty('bc:reflect_until');
    if (typeof until !== 'number' || until <= t) continue;
    safe(() => {
      if (t % 6 === 0) particle(p.dimension, 'bc:shard_burst', V.add(p.location, up), { color: COLORS.mirror, scale: 0.25 });
      for (const x of p.dimension.getEntities({ location: p.location, maxDistance: 3.2 })) {
        const xm = projectiles.get(x.id);
        const hostile = (x.matches({ families: ['bc_spell'] }) && (!xm || xm.owner !== p.id) && !['bc:tornado', 'bc:black_hole', 'bc:ice_prison', 'bc:warp_gate'].includes(x.typeId))
          || HOSTILE_PROJECTILES.includes(x.typeId);
        if (!hostile) continue;
        const from = x.location;
        x.remove();
        const foe = targetsAround(p.dimension, from, 16, p).sort((a, b) => V.dist(a.location, from) - V.dist(b.location, from))[0];
        sound(p.dimension, 'bc.mirror', from, 0.8, 1.6);
        if (foe) {
          beam(p.dimension, from, center(foe), 'mirror', 0.5, 0.5, 0.3);
          hurt(foe, 8, p, 'magic');
        }
      }
    });
  }
}, 2);

world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const p = ev.hurtEntity;
  if (!(p instanceof Player)) return;
  const until = p.getDynamicProperty('bc:bulwark_until');
  const att = ev.damageSource.damagingEntity;
  if (typeof until === 'number' && until > system.currentTick && att && att.id !== p.id && ev.damageSource.cause === 'entityAttack') {
    hurt(att, 4, p);
    particle(p.dimension, 'bc:shard_burst', center(att), { color: COLORS.steel, scale: 0.4 });
  }
}, 'bulwark'));

// owner-bound allies (earth golems, mirror images) stay close
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    safe(() => {
      for (const e of p.dimension.getEntities({ location: p.location, maxDistance: 64, families: ['bc_shade'] })) {
        if (!ownedAlly(p, e) || e.typeId === 'bc:shade_soldier') continue;
        if (V.dist(e.location, p.location) > 16) safe(() => e.teleport(V.add(p.location, { x: rand(-2, 2), y: 0.5, z: rand(-2, 2) })));
      }
    });
  }
}, 40);

// earth golem slam visuals
world.afterEvents.entityHitEntity.subscribe((ev) => {
  const a = ev.damagingEntity;
  if (a.typeId === 'bc:earth_golem' || a.typeId === 'bc:dungeon_golem') {
    anim(a, `animation.bc.${a.typeId.slice(3)}.slam`);
    particle(a.dimension, 'bc:rock_debris', ev.hitEntity.location, { scale: 0.6 });
    sound(a.dimension, 'bc.golem.slam', a.location, 0.7, 1.2);
  }
});

export { knockFrom };
