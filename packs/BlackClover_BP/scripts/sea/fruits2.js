// Wave 3 Abyss Fruits: Frost, Barrier, Wolf (beast) and Hawk (beast).
import { BlockPermutation, ButtonState, InputButton, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { HOSTILE_PROJECTILES, aimEntity, center, effect, groundBelow, hurt, knock, knockFrom, launch, projectiles, targetsAlong, targetsAround } from '../core/combat.js';
import { COLORS, particle, rgb, shakeArea, shockwave, sound } from '../core/fx.js';
import { V, alive, repeat, safe, timer } from '../core/util.js';
import { trackPrison } from '../magic/summons.js';
import { ABILITIES, allies, dash, drained, from, isSealed } from './fruits.js';
import { sea } from './state.js';

const up = { x: 0, y: 1, z: 0 };
const col = (fid) => rgb(DATA.fruits[fid].color);

function perm(id) {
  try {
    return BlockPermutation.resolve(id);
  } catch {
    return undefined;
  }
}

/** Temporarily turn water surface blocks into frosted ice (it melts back on its own). */
function freezeWater(dim, cx, cy, cz, r) {
  const ice = perm('minecraft:frosted_ice');
  if (!ice) return;
  for (let x = -r; x <= r; x++) {
    for (let z = -r; z <= r; z++) {
      if (x * x + z * z > r * r) continue;
      const b = safe(() => dim.getBlock({ x: Math.floor(cx) + x, y: cy, z: Math.floor(cz) + z }));
      const above = safe(() => dim.getBlock({ x: Math.floor(cx) + x, y: cy + 1, z: Math.floor(cz) + z }));
      if (b && above && b.typeId === 'minecraft:water' && above.isAir) safe(() => b.setPermutation(ice));
    }
  }
}

const walls = [];

Object.assign(ABILITIES, {
  // ------------------------------------------------ Frost
  frost_lance(x) {
    sound(x.dim, 'bc.ice.form', x.c.location, 0.8, 1.5);
    launch(x.c, 'bc:ice_spear', from(x), x.dir, 2.4, { spell: 'frost_lance', attr: 'ice', damage: 8 * x.pw, pierce: 0 });
  },
  glacial_path(x) {
    const dir = V.flat(x.dir);
    const start = x.c.location;
    const end = V.add(start, V.mul(dir, 11));
    sound(x.dim, 'bc.ice.form', start, 1, 0.8);
    for (let i = 1; i <= 11; i++) {
      timer(i, () => {
        const p = V.add(start, V.mul(dir, i));
        particle(x.dim, 'bc:ice_shatter', V.add(p, { x: 0, y: 0.4, z: 0 }), { scale: 0.4 });
        freezeWater(x.dim, p.x, Math.floor(p.y) - 1, p.z, 1);
      });
    }
    for (const t of targetsAlong(x.dim, V.add(start, up), V.add(end, up), 1.6, x.c)) {
      hurt(t, 7 * x.pw, x.c, 'freezing');
      effect(t, 'slowness', 3, 4, false);
      const e = safe(() => x.dim.spawnEntity('bc:ice_prison', t.location));
      if (e) trackPrison(e, t, x.c, 4 * x.pw, 60);
    }
  },
  ice_age(x) {
    const at = x.c.location;
    particle(x.dim, 'bc:snowstorm', at, { radius: 7 });
    shockwave(x.dim, at, 'ice', 8);
    sound(x.dim, 'bc.ice.form', at, 1.5, 0.6);
    freezeWater(x.dim, at.x, Math.floor(at.y) - 1, at.z, 6);
    for (const t of targetsAround(x.dim, at, 7.5, x.c)) {
      hurt(t, 10 * x.pw, x.c, 'freezing');
      effect(t, 'slowness', 4, 6, false);
      const e = safe(() => x.dim.spawnEntity('bc:ice_prison', t.location));
      if (e) trackPrison(e, t, x.c, 5 * x.pw, 80);
    }
  },
  // ------------------------------------------------ Barrier
  barrier_wall(x) {
    const dir = V.flat(x.dir);
    const r = { x: -dir.z, y: 0, z: dir.x };
    const base = V.add(x.c.location, V.mul(dir, 2.6));
    const glass = perm('minecraft:light_blue_stained_glass');
    const placed = [];
    for (let w = -2; w <= 2; w++) {
      for (let h = 0; h < 3; h++) {
        const loc = { x: Math.floor(base.x + r.x * w), y: Math.floor(base.y) + h, z: Math.floor(base.z + r.z * w) };
        const b = safe(() => x.dim.getBlock(loc));
        if (b && b.isAir && glass) {
          safe(() => b.setPermutation(glass));
          placed.push(loc);
        }
      }
    }
    if (!placed.length) return false;
    sound(x.dim, 'bc.mirror', base, 1, 0.6);
    walls.push({ dim: x.dim, placed, until: system.currentTick + 160 });
  },
  barrier_dome(x) {
    const at = x.c.location;
    particle(x.dim, 'bc:shockwave', at, { radius: 6, color: col('barrier') });
    sound(x.dim, 'bc.mirror', at, 1.2, 0.8);
    for (const a of allies(x.c, at, 6)) {
      effect(a, 'resistance', 6, 1, false);
      effect(a, 'absorption', 6, 1, false);
    }
    repeat(30, 4, (i) => {
      if (!alive(x.c)) return false;
      if (i % 5 === 0) particle(x.dim, 'bc:shockwave', at, { radius: 6, color: col('barrier') });
      safe(() => {
        for (const p of x.dim.getEntities({ location: at, maxDistance: 6 })) {
          const pm = projectiles.get(p.id);
          const hostile = (p.matches({ families: ['bc_spell'] }) && (!pm || pm.owner !== x.c.id) && !['bc:tornado', 'bc:black_hole', 'bc:ice_prison', 'bc:warp_gate'].includes(p.typeId))
            || HOSTILE_PROJECTILES.includes(p.typeId);
          if (!hostile) continue;
          particle(x.dim, 'bc:shard_burst', p.location, { color: col('barrier'), scale: 0.4 });
          p.remove();
        }
      });
    });
  },
  barrier_crash(x) {
    const dir = V.flat(x.dir);
    const a = V.add(x.c.location, up);
    const b = V.add(a, V.mul(dir, 8));
    for (let t = 1; t < 8; t += 1.2) particle(x.dim, 'bc:shard_burst', V.add(a, V.mul(dir, t)), { color: col('barrier'), scale: 0.35 });
    sound(x.dim, 'bc.golem.slam', a, 0.8, 1.5);
    for (const t of targetsAlong(x.dim, a, b, 1.8, x.c)) {
      hurt(t, 8 * x.pw, x.c);
      knock(t, dir, 2.6, 0.4);
    }
  },
  // ------------------------------------------------ Wolf
  pounce(x) {
    const t = x.target ?? (x.c.getViewDirection ? aimEntity(x.c, 16) : undefined);
    const goal = t ? t.location : V.add(x.c.location, V.mul(V.flat(x.dir), 7));
    const d = V.sub(goal, x.c.location);
    dash(x.c, d, Math.min(3.2, V.len(d) * 0.35 + 0.8), 0.5);
    sound(x.dim, 'bc.howl', x.c.location, 0.4, 1.8);
    timer(8, () => {
      for (const v of targetsAround(x.dim, x.c.location, 3, x.c)) {
        hurt(v, 9 * x.pw, x.c);
        effect(v, 'slowness', 2, 1);
        particle(x.dim, 'bc:slash_fx', center(v), { size: 2.2 });
      }
    });
  },
  howl(x) {
    const at = x.c.location;
    sound(x.dim, 'bc.howl', at, 1.4, 1);
    particle(x.dim, 'bc:shockwave', at, { radius: 10, color: col('wolf') });
    effect(x.c, 'strength', 10, 1, false);
    effect(x.c, 'speed', 10, 1, false);
    for (const a of allies(x.c, at, 10)) if (a.id !== x.c.id) effect(a, 'strength', 6, 0);
    for (const v of targetsAround(x.dim, at, 10, x.c)) {
      effect(v, 'weakness', 6, 1);
      effect(v, 'slowness', 3, 1);
    }
  },
  rending_frenzy(x) {
    repeat(5, 3, (i) => {
      if (!alive(x.c)) return false;
      const dir = V.flat(x.c.getViewDirection ? x.c.getViewDirection() : x.dir);
      const at = V.add(x.c.location, V.add(V.mul(dir, 1.8), up));
      particle(x.dim, 'bc:slash_fx', at, { size: 2.4, rot: i * 37 });
      for (const v of targetsAround(x.dim, at, 2.4, x.c)) hurt(v, 3.5 * x.pw, x.c);
    });
  },
  // ------------------------------------------------ Hawk
  sky_ascent(x) {
    knock(x.c, { x: 0, y: 0, z: 0 }, 0, 2.4);
    effect(x.c, 'slow_falling', 4, 0, false);
    particle(x.dim, 'bc:shard_burst', x.c.location, { color: col('hawk'), scale: 1 });
    particle(x.dim, 'bc:wind_burst', x.c.location, { scale: 0.6 });
    sound(x.dim, 'bc.wind.gust', x.c.location, 1, 1.4);
  },
  talon_dive(x) {
    const goal = x.aim;
    const d = V.sub(goal, x.c.location);
    dash(x.c, d, Math.min(3.4, V.len(d) * 0.3 + 1), -0.4);
    sound(x.dim, 'bc.wind.gust', x.c.location, 1, 0.8);
    timer(10, () => {
      const at = x.c.location;
      particle(x.dim, 'bc:rock_debris', at, { scale: 0.8 });
      shockwave(x.dim, at, 'wind', 4);
      shakeArea(x.dim, at, 10, 0.3, 0.4);
      for (const v of targetsAround(x.dim, at, 3.5, x.c)) {
        hurt(v, 12 * x.pw, x.c);
        knock(v, up, 0, 0.8);
      }
    });
  },
  feather_storm(x) {
    sound(x.dim, 'bc.wind.gust', x.c.location, 0.8, 1.7);
    for (const off of [-14, -7, 0, 7, 14]) {
      launch(x.c, 'bc:wind_blade', from(x, 1.2, 0.4), V.yaw(x.dir, off), 2.3, { spell: 'feather_storm', attr: 'wind', damage: 5 * x.pw, pierce: 0 });
    }
  },
});

// ------------------------------------------------------------------ passives
system.runInterval(() => {
  const t = system.currentTick;
  for (let i = walls.length - 1; i >= 0; i--) {
    const w = walls[i];
    if (w.until > t) continue;
    for (const loc of w.placed) {
      const b = safe(() => w.dim.getBlock(loc));
      if (b && b.typeId === 'minecraft:light_blue_stained_glass') safe(() => b.setType('minecraft:air'));
    }
    walls.splice(i, 1);
  }
  for (const p of world.getAllPlayers()) {
    const fid = sea(p).fruit;
    if (!fid || isSealed(p) || drained(p)) continue;
    safe(() => {
      if (fid === 'frost') {
        if (!p.isInWater && !p.isFalling) freezeWater(p.dimension, p.location.x, Math.floor(p.location.y) - 1, p.location.z, 2);
      } else if (fid === 'barrier') {
        const v = p.getVelocity();
        if (Math.abs(v.x) + Math.abs(v.z) < 0.02) effect(p, 'resistance', 1, 0, false);
      } else if (fid === 'wolf') {
        effect(p, 'speed', 2, 0, false);
        if (t % 40 === 0) effect(p, 'night_vision', 12, 0, false);
      } else if (fid === 'hawk') {
        const vy = p.getVelocity().y;
        if (p.isFalling && vy < -0.4) effect(p, 'slow_falling', 1, 0, false);
        if (p.isFalling && p.inputInfo.getButtonState(InputButton.Jump) === ButtonState.Pressed) {
          effect(p, 'slow_falling', 1, 0, false);
          if (t % 4 === 0) knock(p, p.getViewDirection(), 0.7, 0.05);
        }
      }
    });
  }
}, 5);

export { groundBelow, knockFrom, COLORS };
