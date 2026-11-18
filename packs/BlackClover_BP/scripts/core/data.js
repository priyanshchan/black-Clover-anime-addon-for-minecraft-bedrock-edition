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
 * @property {number} [noRegen]  tick until which mana does not regenerate (broom flight)
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
/** The amulet held in the off hand, or ''. */
export function amuletOf(p) {
  try {
    const id = p.getComponent('minecraft:equippable')?.getEquipment(EquipmentSlot.Offhand)?.typeId ?? '';
    const key = id.startsWith('bc:') ? id.slice(3) : '';
    return key.startsWith('amulet_') ? key : '';
  } catch {
    return '';
  }
}

function rankBonus(p) {
  const st = p.getDynamicProperty('bc:stars');
  const n = typeof st === 'number' ? st : 0;
  let idx = 0;
  DATA.ranks.forEach((r, i) => {
    if (n >= r.stars) idx = i;
  });
  return idx * 5;
}

export function maxMana(p, s = state(p)) {
  const r = robe(p);
  return 100 + (s.level - 1) * 12 + (r === 'golden_dawn_robe' ? 40 : 0) + (r === 'blue_rose_robe' ? 15 : 0) + rankBonus(p) + (amuletOf(p) === 'amulet_mana' ? 30 : 0);
}

export function regenPerSecond(p, s = state(p)) {
  let r = 3 + s.level * 0.3;
  const rb = robe(p);
  if (rb === 'black_bull_robe') r *= 1.25;
  if (amuletOf(p) === 'amulet_mana') r *= 1.2;
  if (rb === 'aqua_deer_robe') {
    const v = p.getVelocity();
    if (Math.abs(v.x) + Math.abs(v.z) > 0.05) r *= 1.3;
  }
  return r;
}

export function xpToNext(level) {
  return 30 + level * 22;
}

/** The Mana Eclipse world event: +25% spell power for everyone while it lasts. */
export function eclipseMul() {
  const v = world.getDynamicProperty('bc:eclipse_until');
  return typeof v === 'number' && v > system.currentTick ? 1.25 : 1;
}

export function spellPower(p, s = state(p)) {
  let m = (1 + (s.level - 1) * 0.05) * eclipseMul();
  const r = robe(p);
  if (r === 'golden_dawn_robe') m *= 1.1;
  if (r === 'black_bull_robe') {
    const hp = p.getComponent('minecraft:health');
    if (hp && hp.currentValue < hp.effectiveMax * 0.4) m *= 1.25;
  }
  if (r === 'crimson_lion_robe' && s.attr === 'flame') m *= 1.15;
  if (r === 'silver_eagle_robe' && s.mana > maxMana(p, s) * 0.75) m *= 1.2;
  if (r === 'purple_orca_robe' && (s.attr === 'water' || s.attr === 'ice')) m *= 1.15;
  if (amuletOf(p) === 'amulet_power') m *= 1.12;
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
