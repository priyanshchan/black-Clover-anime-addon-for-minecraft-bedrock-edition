// Large world records (v1.1.0): a JSON value split over several dynamic properties, so the atlas of regions and
// landmarks can grow past the 32 767-character limit of a single property.
import { world } from '@minecraft/server';

const CHUNK = 30000;
const MAX_CHUNKS = 12;

/** Read a big JSON value saved with saveBig (or `fallback`). */
export function loadBig(key, fallback) {
  try {
    const n = world.getDynamicProperty(`${key}#n`);
    if (typeof n !== 'number') return fallback;
    let s = '';
    for (let i = 0; i < n; i++) {
      const part = world.getDynamicProperty(`${key}#${i}`);
      if (typeof part !== 'string') return fallback;
      s += part;
    }
    return JSON.parse(s);
  } catch {
    return fallback;
  }
}

/** Save a big JSON value. Returns false when it would not fit (the caller should trim it). */
export function saveBig(key, value) {
  try {
    const s = JSON.stringify(value);
    const n = Math.ceil(s.length / CHUNK) || 1;
    if (n > MAX_CHUNKS) return false;
    const old = world.getDynamicProperty(`${key}#n`);
    for (let i = 0; i < n; i++) world.setDynamicProperty(`${key}#${i}`, s.slice(i * CHUNK, (i + 1) * CHUNK));
    if (typeof old === 'number') for (let i = n; i < old; i++) world.setDynamicProperty(`${key}#${i}`, undefined);
    world.setDynamicProperty(`${key}#n`, n);
    return true;
  } catch {
    return false;
  }
}
