// Per-player state for the Abyssal Seas expansion (fruit, Will, bounty), persisted in dynamic properties.
import { system, world } from '@minecraft/server';
import { clamp } from '../core/util.js';

/**
 * @typedef {Object} SeaState
 * @property {string} fruit        eaten Abyss Fruit id ('' if none)
 * @property {number} ability      selected fruit ability index
 * @property {number} willLv
 * @property {number} willXp
 * @property {number} will         Will gauge 0..100
 * @property {any} bounty          active bounty or null
 * @property {Map<string, number>} cd   ability id -> tick when ready
 * @property {number} lastUse
 * @property {boolean} dirty
 */

/** @type {Map<string, SeaState>} */
const cache = new Map();

/** @param {import('@minecraft/server').Player} p @returns {SeaState} */
export function sea(p) {
  let s = cache.get(p.id);
  if (s) return s;
  const num = (k, d) => {
    const v = p.getDynamicProperty(k);
    return typeof v === 'number' ? v : d;
  };
  const f = p.getDynamicProperty('bc:fruit');
  let bounty = null;
  const b = p.getDynamicProperty('bc:bounty');
  if (typeof b === 'string' && b) {
    try {
      bounty = JSON.parse(b);
    } catch {
      bounty = null;
    }
  }
  s = { fruit: typeof f === 'string' ? f : '', ability: num('bc:fruit_ab', 0), willLv: num('bc:will_lv', 0), willXp: num('bc:will_xp', 0),
    will: num('bc:will', 100), bounty, cd: new Map(), lastUse: -1000, dirty: false };
  cache.set(p.id, s);
  return s;
}

export function saveSea(p) {
  const s = cache.get(p.id);
  if (!s) return;
  p.setDynamicProperty('bc:fruit', s.fruit);
  p.setDynamicProperty('bc:fruit_ab', s.ability);
  p.setDynamicProperty('bc:will_lv', s.willLv);
  p.setDynamicProperty('bc:will_xp', Math.floor(s.willXp));
  p.setDynamicProperty('bc:will', Math.floor(s.will));
  p.setDynamicProperty('bc:bounty', s.bounty ? JSON.stringify(s.bounty) : '');
  s.dirty = false;
}

export function forgetSea(id) {
  cache.delete(id);
}

export function willToNext(lv) {
  return 25 + lv * 20;
}

export function addWill(p, amount) {
  const s = sea(p);
  s.will = clamp(s.will + amount, 0, 100);
  s.dirty = true;
}

system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    const s = cache.get(p.id);
    if (s && s.dirty) {
      try {
        saveSea(p);
      } catch {
        /* left */
      }
    }
  }
}, 40);
