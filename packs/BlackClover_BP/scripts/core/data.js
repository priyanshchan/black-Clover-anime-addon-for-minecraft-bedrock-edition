// Per-player magic state, persisted in dynamic properties.
import { EquipmentSlot, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { clamp } from './util.js';

export const MAX_LEVEL = 20;
const KEYS = { attr: 'bc:attr', level: 'bc:level', xp: 'bc:xp', mana: 'bc:mana', spell: 'bc:spell', anti: 'bc:anti', joined: 'bc:joined' };

/**
 * @typedef {Object} MagicState
 * @property {string} attr      attribute id ('' when the player has no grimoire yet)
 * @property {number} level
 * @property {number} xp
 * @property {number} mana
 * @property {number} spell     selected spell index
 * @property {number} anti      anti-magic gauge 0..100
 * @property {number} lastCast  tick of the last cast (HUD stays visible after)
 * @property {Map<string, number>} cd  spell id -> tick when ready
 * @property {boolean} dirty
 */

/** @type {Map<string, MagicState>} */
const cache = new Map();

/** @param {import('@minecraft/server').Player} p @returns {MagicState} */
export function state(p) {
  let s = cache.get(p.id);
  if (s) return s;
  const num = (k, d) => {
    const v = p.getDynamicProperty(k);
    return typeof v === 'number' ? v : d;
  };
  const a = p.getDynamicProperty(KEYS.attr);
  s = {
    attr: typeof a === 'string' ? a : '',
    level: num(KEYS.level, 1),
    xp: num(KEYS.xp, 0),
    mana: num(KEYS.mana, 100),
    spell: num(KEYS.spell, 0),
    anti: num(KEYS.anti, 0),
    lastCast: -1000,
    cd: new Map(),
    dirty: false,
  };
  cache.set(p.id, s);
  return s;
}

export function save(p) {
  const s = cache.get(p.id);
  if (!s) return;
  p.setDynamicProperty(KEYS.attr, s.attr);
  p.setDynamicProperty(KEYS.level, s.level);
  p.setDynamicProperty(KEYS.xp, Math.floor(s.xp));
  p.setDynamicProperty(KEYS.mana, Math.floor(s.mana));
  p.setDynamicProperty(KEYS.spell, s.spell);
  p.setDynamicProperty(KEYS.anti, Math.floor(s.anti));
  s.dirty = false;
}

export function forget(id) {
  cache.delete(id);
}

export function hasJoined(p) {
  return p.getDynamicProperty(KEYS.joined) === true;
}
export function markJoined(p) {
  p.setDynamicProperty(KEYS.joined, true);
}

// ----------------------------------------------------------------------------------- robes
export function robe(p) {
  try {
    const eq = p.getComponent('minecraft:equippable');
    const item = eq?.getEquipment(EquipmentSlot.Chest);
    if (item && item.typeId.startsWith('bc:') && item.typeId.endsWith('_robe')) return item.typeId.slice(3);
  } catch {
    /* not equippable */
  }
  return '';
}

// ----------------------------------------------------------------------------------- stats
export function maxMana(p, s = state(p)) {
  return 100 + (s.level - 1) * 12 + (robe(p) === 'golden_dawn_robe' ? 40 : 0);
}

export function regenPerSecond(p, s = state(p)) {
  let r = 3 + s.level * 0.3;
  if (robe(p) === 'black_bull_robe') r *= 1.25;
  return r;
}

export function xpToNext(level) {
  return 30 + level * 22;
}

export function spellPower(p, s = state(p)) {
  let m = 1 + (s.level - 1) * 0.05;
  const r = robe(p);
  if (r === 'golden_dawn_robe') m *= 1.1;
  if (r === 'black_bull_robe') {
    const hp = p.getComponent('minecraft:health');
    if (hp && hp.currentValue < hp.effectiveMax * 0.4) m *= 1.25;
  }
  if (r === 'crimson_lion_robe' && s.attr === 'flame') m *= 1.15;
  return m;
}

export function spellsOf(attr) {
  return DATA.spells[attr] ?? [];
}

export function unlocked(s, spellIndex) {
  const sp = spellsOf(s.attr)[spellIndex];
  return !!sp && s.level >= sp.level;
}

export function addMana(p, amount) {
  const s = state(p);
  s.mana = clamp(s.mana + amount, 0, maxMana(p, s));
  s.dirty = true;
}

/** Periodically flush dirty states. */
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    const s = cache.get(p.id);
    if (s && s.dirty) {
      try {
        save(p);
      } catch {
        /* player left */
      }
    }
  }
}, 40);
