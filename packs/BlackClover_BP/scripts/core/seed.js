// Seeded randomness (v1.1.0): every world rolls its own seed once, and everything about the land - region names,
// traits, where the landmarks lie - is derived from it, so the same world always tells the same story, and every
// new world tells a different one.
import { world } from '@minecraft/server';

/** A 32-bit hash of any parts (FNV-1a). */
export function hash(...parts) {
  let h = 0x811c9dc5;
  const s = parts.join('|');
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h >>> 0;
}

/** A seeded random number generator (mulberry32): returns numbers in [0, 1). */
export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

let cached = 0;
/** This world's seed (rolled the first time it is needed, then kept forever). */
export function worldSeed() {
  if (cached) return cached;
  let v = 0;
  try {
    v = /** @type {number} */ (world.getDynamicProperty('bc:seed') ?? 0);
  } catch {
    v = 0;
  }
  if (typeof v !== 'number' || !v) {
    v = 1 + Math.floor(Math.random() * 2147483000);
    try {
      world.setDynamicProperty('bc:seed', v);
    } catch {
      /* not ready yet - try again next time */
      return v;
    }
  }
  cached = v;
  return v;
}

/** A generator for one thing in this world (a region, a landmark...). */
export function rngFor(...parts) {
  return rng(hash(worldSeed(), ...parts));
}

/** Pick from a list with a seeded generator. */
export function pickR(r, arr) {
  return arr[Math.floor(r() * arr.length)];
}

/** Weighted pick: entries are [item, weight]. */
export function pickW(r, entries) {
  const total = entries.reduce((s, e) => s + Math.max(0, e[1]), 0);
  let x = r() * total;
  for (const [item, w] of entries) {
    x -= Math.max(0, w);
    if (x <= 0) return item;
  }
  return entries[entries.length - 1]?.[0];
}
