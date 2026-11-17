// Small math / safety helpers shared by every module.
import { GameMode, system, world } from '@minecraft/server';

/** @typedef {{x:number,y:number,z:number}} Vec */

export const V = {
  /** @returns {Vec} */ v: (x, y, z) => ({ x, y, z }),
  /** @param {Vec} a @param {Vec} b */ add: (a, b) => ({ x: a.x + b.x, y: a.y + b.y, z: a.z + b.z }),
  /** @param {Vec} a @param {Vec} b */ sub: (a, b) => ({ x: a.x - b.x, y: a.y - b.y, z: a.z - b.z }),
  /** @param {Vec} a @param {number} s */ mul: (a, s) => ({ x: a.x * s, y: a.y * s, z: a.z * s }),
  /** @param {Vec} a */ len: (a) => Math.sqrt(a.x * a.x + a.y * a.y + a.z * a.z),
  /** @param {Vec} a @param {Vec} b */ dist: (a, b) => Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2),
  /** @param {Vec} a @param {Vec} b */ dot: (a, b) => a.x * b.x + a.y * b.y + a.z * b.z,
  /** @param {Vec} a */
  norm: (a) => {
    const l = Math.sqrt(a.x * a.x + a.y * a.y + a.z * a.z) || 1;
    return { x: a.x / l, y: a.y / l, z: a.z / l };
  },
  /** horizontal unit vector @param {Vec} a */
  flat: (a) => {
    const l = Math.sqrt(a.x * a.x + a.z * a.z) || 1;
    return { x: a.x / l, y: 0, z: a.z / l };
  },
  /** rotate around Y axis by degrees @param {Vec} a @param {number} deg */
  yaw: (a, deg) => {
    const r = (deg * Math.PI) / 180;
    const c = Math.cos(r), s = Math.sin(r);
    return { x: a.x * c - a.z * s, y: a.y, z: a.x * s + a.z * c };
  },
  /** @param {Vec} a @param {Vec} b @param {number} t */
  lerp: (a, b, t) => ({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, z: a.z + (b.z - a.z) * t }),
};

export const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
export const rand = (a, b) => a + Math.random() * (b - a);
export const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

/** Entity still usable? */
export function alive(e) {
  try {
    return !!e && e.isValid;
  } catch {
    return false;
  }
}

/** Run fn and swallow (but log) errors so one bad tick never kills a loop. */
export function safe(fn, label = 'bc') {
  try {
    return fn();
  } catch (err) {
    console.warn(`[${label}] ${err}`);
    return undefined;
  }
}

export function isCreative(player) {
  try {
    return player.getGameMode() === GameMode.Creative;
  } catch {
    return false;
  }
}

export function now() {
  return system.currentTick;
}

/** Shortest distance from point p to segment a-b. */
export function segDist(p, a, b) {
  const ab = V.sub(b, a);
  const t = clamp(V.dot(V.sub(p, a), ab) / (V.dot(ab, ab) || 1), 0, 1);
  return V.dist(p, V.add(a, V.mul(ab, t)));
}

export function yawOf(dir) {
  return (Math.atan2(-dir.x, dir.z) * 180) / Math.PI;
}

export function timer(ticks, fn) {
  return system.runTimeout(() => safe(fn, 'timer'), ticks);
}

/** Repeats fn every `every` ticks `times` times (fn receives index). */
export function repeat(times, every, fn, done) {
  let i = 0;
  const id = system.runInterval(() => {
    if (i >= times) {
      system.clearRun(id);
      if (done) safe(done, 'repeat-done');
      return;
    }
    const r = safe(() => fn(i), 'repeat');
    i++;
    if (r === false) {
      system.clearRun(id);
      if (done) safe(done, 'repeat-done');
    }
  }, every);
  return id;
}

export function players() {
  return world.getAllPlayers();
}
