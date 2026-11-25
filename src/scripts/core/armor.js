// Armour (v0.8.0): what an entity wears, its set bonuses, runes, reinforcement and squad mantle - the numbers the
// mana and spell maths (core/data.js), casting, Abyss Fruits and the armour systems (living/armor.js) read.
// A piece carries its upgrades in its lore: a visible line for each, and a hidden token the scripts read.
import { EquipmentSlot, Player, system } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { safe } from './util.js';

const A = DATA.armor;
export const PIECE_NAME = { head: 'helmet', chest: 'chestplate', legs: 'leggings', feet: 'boots' };
const EQUIP = { head: EquipmentSlot.Head, chest: EquipmentSlot.Chest, legs: EquipmentSlot.Legs, feet: EquipmentSlot.Feet };
/** @type {Record<string, {set: string, slot: string, idx: number}>} item id -> its set and slot */
export const PIECES = {};
for (const sid of Object.keys(A.sets)) A.slots.forEach((slot, idx) => (PIECES[`bc:${sid}_${PIECE_NAME[slot]}`] = { set: sid, slot, idx }));

export function pieceId(sid, slot) {
  return `bc:${sid}_${PIECE_NAME[slot]}`;
}
export function pieceName(id) {
  const pc = PIECES[id];
  return pc ? A.sets[pc.set].pieces[pc.idx] : id;
}

// ------------------------------------------------------------------------------- upgrades in the lore
const TOKEN = '§8bc|';
/** @typedef {{plus: number, rune: string, mantle: string}} Upgrades */
/** @returns {Upgrades} */
export function readUpgrades(item) {
  const up = { plus: 0, rune: '', mantle: '' };
  const lore = safe(() => item?.getLore?.()) ?? [];
  const tok = lore.find((l) => typeof l === 'string' && l.startsWith(TOKEN));
  if (!tok) return up;
  const [plus, rune, mantle] = tok.slice(TOKEN.length).split('|');
  up.plus = Math.max(0, Math.min(A.reinforceMax, Number(plus) || 0));
  up.rune = A.runes[rune] ? rune : '';
  up.mantle = DATA.robes[mantle] ? mantle : '';
  return up;
}
/** Write upgrades onto an item (every lore line stays under the 50-character limit). */
export function writeUpgrades(item, up) {
  const lines = [];
  if (up.plus) lines.push(`§7Reinforced §f+${up.plus}`);
  if (up.rune) lines.push(`§d${A.runes[up.rune].name}`);
  if (up.mantle) lines.push(`§6Mantle: ${String(DATA.robes[up.mantle]).replace(/§./g, '')}`);
  if (up.plus || up.rune || up.mantle) lines.push(`${TOKEN}${up.plus}|${up.rune}|${up.mantle}`);
  safe(() => item.setLore(lines));
  return item;
}

// ------------------------------------------------------------------------------- what is worn
/** @typedef {{id: string, set: string, slot: string, idx: number, plus: number, rune: string, mantle: string}} Piece */
/** @typedef {{pieces: Piece[], sets: Record<string, number>, runes: Record<string, number>, plus: number, mantle: string}} Gear */
/** @type {((e: any) => Piece[] | undefined)[]} where non-players (companions) keep their armour */
const providers = [];
export function setGearProvider(fn) {
  providers.push(fn);
}
/** The worn pieces of a player, read from its equipment. */
export function wornPieces(p) {
  /** @type {Piece[]} */
  const out = [];
  const eq = safe(() => p.getComponent('minecraft:equippable'));
  if (!eq) return out;
  for (const slot of A.slots) {
    const it = safe(() => eq.getEquipment(EQUIP[slot]));
    const pc = it && PIECES[it.typeId];
    if (pc) out.push({ id: it.typeId, ...pc, ...readUpgrades(it) });
  }
  return out;
}
/** @type {Map<string, {t: number, g: Gear}>} */
const cache = new Map();
/** @returns {Gear} */
export function gearOf(e) {
  const t = system.currentTick;
  const id = safe(() => e.id) ?? '';
  const c = cache.get(id);
  if (c && c.t === t) return c.g;
  let pieces = [];
  if (e instanceof Player) pieces = wornPieces(e);
  else {
    for (const fn of providers) {
      const r = safe(() => fn(e));
      if (r) {
        pieces = r;
        break;
      }
    }
  }
  /** @type {Gear} */
  const g = { pieces, sets: {}, runes: {}, plus: 0, mantle: '' };
  for (const pc of pieces) {
    g.sets[pc.set] = (g.sets[pc.set] ?? 0) + 1;
    if (pc.rune) g.runes[pc.rune] = (g.runes[pc.rune] ?? 0) + 1;
    g.plus += pc.plus;
    if (pc.slot === 'chest' && pc.mantle) g.mantle = pc.mantle;
  }
  cache.set(id, { t, g });
  return g;
}
system.runInterval(() => cache.clear(), 1200);

export function setCount(e, sid) {
  return gearOf(e).sets[sid] ?? 0;
}
export function hasSet(e, sid, n) {
  return setCount(e, sid) >= n;
}
export function runeCount(e, rid) {
  return gearOf(e).runes[rid] ?? 0;
}
/** The squad robe sewn onto the chestplate as a mantle (its perk applies). */
export function mantleOf(e) {
  return gearOf(e).mantle;
}

// ------------------------------------------------------------------------------- the numbers
export function armorMaxMana(e) {
  return (hasSet(e, 'manasteel', 2) ? 25 : 0) + (hasSet(e, 'archmage', 4) ? 40 : 0) + runeCount(e, 'mana') * 15;
}
export function armorRegenMul(e) {
  return hasSet(e, 'manasteel', 4) ? 1.25 : 1;
}
export function armorCostMul(e) {
  return hasSet(e, 'manasteel', 4) ? 0.9 : 1;
}
const WYVERN_ATTRS = new Set(['flame', 'ice', 'lightning', 'magma', 'storm', 'ash', 'crystal', 'frost']);
/** @param {number} hp the wearer's health fraction @param {string} [attr] the attribute being cast */
export function armorPowerMul(e, hp = 1, attr = '') {
  let m = 1;
  if (attr && WYVERN_ATTRS.has(attr) && hasSet(e, 'wyvernscale', 4)) m *= 1.2;
  if (hasSet(e, 'royal', 2)) m *= 1.1;
  if (hasSet(e, 'archmage', 4)) m *= 1.2;
  if (hasSet(e, 'devilhide', 4) && hp < 0.3) m *= 1.2;
  return m;
}
export function armorCdMul(e) {
  return (hasSet(e, 'archmage', 2) ? 0.9 : 1) * Math.max(0.6, 1 - runeCount(e, 'focus') * 0.04);
}
export function fruitCdMul(e) {
  return (hasSet(e, 'archmage', 2) ? 0.9 : 1) * (hasSet(e, 'abyssal', 4) ? 0.85 : 1);
}
/** Abyssal Scale (4): the sea does not drain an Abyss Fruit user. */
export function seaWard(e) {
  return hasSet(e, 'abyssal', 4);
}
/** The share of damage that gets through: reinforcement against everything; Warding runes and Runeplate (4) against magic. */
export function damageTakenMul(e, magic) {
  const g = gearOf(e);
  let m = 1 - (g.plus * A.reinforcePct) / 100;
  if (magic) {
    m *= Math.max(0.5, 1 - (g.runes.warding ?? 0) * 0.06);
    if ((g.sets.runeplate ?? 0) >= 4) m *= 0.8;
  }
  return Math.max(0.3, m);
}
/** Active set bonuses as text, for the Handbook and companion profiles. */
export function bonusLines(e) {
  const g = gearOf(e);
  const out = [];
  for (const [sid, n] of Object.entries(g.sets)) {
    const s = A.sets[sid];
    if (n >= 2) out.push(`${s.mc}${s.name} (2): §7${s.b2}`);
    if (n >= 4) out.push(`${s.mc}${s.name} (4): §7${s.b4}`);
  }
  return out;
}
