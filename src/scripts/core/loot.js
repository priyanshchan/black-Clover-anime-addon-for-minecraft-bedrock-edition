// Random loot (v1.1.0): rarities from Common to Mythic, relics and weapons with rolled affixes and their own names,
// and the chest tables of the landmarks. Danger stars, luck (relics), and a Lucky Stars omen push rolls up the ladder.
//
// A rolled item keeps its roll in its lore: a visible line per affix and a hidden token the scripts read,
//   relics:  §8br|<rarity index>|<affix code><value>,...      weapons: §8bw|<rarity index>|<affix code><value>,...
import { ItemStack, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { makeScroll } from './scrolls.js';
import { pick, rand, safe } from './util.js';
import { pieceId, writeUpgrades } from './armor.js';

const L = DATA.loot;
export const RARITIES = L.rarities;
export const RARITY_IDS = RARITIES.map((r) => r.id);
const R_INDEX = Object.fromEntries(RARITY_IDS.map((id, i) => [id, i]));
// two-letter codes keep the hidden token short (lore lines must stay under 50 characters)
const CODES = {
  mana: 'mn', regen: 'rg', power: 'pw', haste: 'hs', vigor: 'vg', ward: 'wd', guard: 'gd', thorns: 'th', leech: 'lc', might: 'mt', luck: 'lk',
  scholar: 'sc', fortune: 'ft', swift: 'sw', leap: 'lp', sight: 'si', gills: 'gl', ember: 'em',
  sharp: 'sh', burning: 'bu', frost: 'fr', storm: 'st', vampiric: 'va', mana_thirst: 'mh', executioner: 'ex', giantslayer: 'gs', cleave: 'cl', quick: 'qk',
};
const FROM_CODE = Object.fromEntries(Object.entries(CODES).map(([k, v]) => [v, k]));
export const RELIC_IDS = Object.keys(L.relics).map((k) => `bc:${k}`);

// ------------------------------------------------------------------------------- the luck of the world today
/** @type {(() => number)} extra rarity luck from the day's omen (omens.js) */
let omenLuck = () => 0;
export function setOmenLuck(fn) {
  omenLuck = fn;
}

/**
 * Roll a rarity. Danger stars, luck (percentage points) and the day's omen push it up the ladder.
 * @returns {typeof RARITIES[number]}
 */
export function rollRarity(stars = 1, luck = 0, min = 'common', r = Math.random) {
  const lift = (1 + L.starShift * Math.max(0, stars - 1)) * (1 + luck / 100) * (1 + omenLuck());
  const lo = R_INDEX[min] ?? 0;
  const pool = RARITIES.map((x, i) => ({ rar: x, w: i < lo ? 0 : x.weight * lift ** i }));
  const total = pool.reduce((s, e) => s + e.w, 0);
  let x = r() * total;
  for (const e of pool) {
    x -= e.w;
    if (x <= 0) return e.rar;
  }
  return RARITIES[RARITIES.length - 1];
}

// ------------------------------------------------------------------------------- names
function legendName() {
  const [a, b] = L.legendSyllables;
  return `${pick(a)}${pick(b)}, ${pick(L.epithets)}`;
}
const BASE_NAMES = {
  'minecraft:stone_sword': 'Stone Sword', 'minecraft:iron_sword': 'Sword', 'minecraft:diamond_sword': 'Diamond Blade', 'minecraft:netherite_sword': 'Netherite Blade',
  'minecraft:stone_axe': 'Stone Axe', 'minecraft:iron_axe': 'Axe', 'minecraft:diamond_axe': 'Diamond Axe', 'minecraft:netherite_axe': 'Netherite Axe',
};
function plainName(first, base) {
  const name = `${L.prefix[first] ?? 'Old'} ${base} ${pick(L.suffix)}`;
  return name.length <= 38 ? name : `${L.prefix[first] ?? 'Old'} ${base}`;
}

// ------------------------------------------------------------------------------- rolling affixes
function value(base, power) {
  return Math.max(1, Math.round(base * power * rand(0.75, 1.25)));
}
/** @returns {Record<string, number>} */
function rollRelicAffixes(baseKey, rar) {
  const favour = L.relics[baseKey]?.favour ?? [];
  const all = Object.keys(L.relicAffixes);
  /** @type {Record<string, number>} */
  const out = {};
  for (let i = 0; i < rar.affixes && i < 8; i++) {
    let id = '';
    for (let tries = 0; tries < 12 && (!id || out[id] !== undefined); tries++) id = Math.random() < 0.6 ? pick(favour) : pick(all);
    if (!id || out[id] !== undefined) continue;
    const a = L.relicAffixes[id];
    out[id] = a.flag ? 1 : value(a.base, rar.power);
  }
  return out;
}
/** @returns {Record<string, number>} */
function rollWeaponAffixes(rar) {
  const all = Object.keys(L.weaponAffixes);
  /** @type {Record<string, number>} */
  const out = {};
  for (let i = 0; i < rar.affixes; i++) {
    let id = '';
    for (let tries = 0; tries < 12 && (!id || out[id] !== undefined); tries++) id = pick(all);
    if (!id || out[id] !== undefined) continue;
    const a = L.weaponAffixes[id];
    out[id] = id === 'quick' ? 1 : value(a.base, rar.power);
  }
  return out;
}

export function affixLine(kind, id, v) {
  const a = kind === 'relic' ? L.relicAffixes[id] : L.weaponAffixes[id];
  return a ? `§7${a.label.replace('{v}', String(v))}` : '';
}

// ------------------------------------------------------------------------------- reading and writing a roll
/** @typedef {{kind: 'relic' | 'weapon', rarity: string, affixes: Record<string, number>, name: string}} Roll */

/** The roll on an item, or undefined. @returns {Roll | undefined} */
export function readRoll(item) {
  const lore = safe(() => item?.getLore?.()) ?? [];
  const tok = lore.find((l) => typeof l === 'string' && (l.startsWith('§8br|') || l.startsWith('§8bw|')));
  if (!tok) return undefined;
  const [head, ri, list] = tok.slice(2).split('|');
  const rarity = RARITY_IDS[Number(ri)] ?? 'common';
  /** @type {Record<string, number>} */
  const affixes = {};
  for (const part of (list ?? '').split(',')) {
    const id = FROM_CODE[part.slice(0, 2)];
    const v = Number(part.slice(2));
    if (id && Number.isFinite(v)) affixes[id] = v;
  }
  const name = String(safe(() => item.nameTag) ?? '').replace(/§./g, '');
  return { kind: head === 'br' ? 'relic' : 'weapon', rarity, affixes, name };
}

/** Write a roll onto an item: its name, a line per affix, and the hidden token. */
export function writeRoll(item, roll) {
  const rar = RARITIES[R_INDEX[roll.rarity] ?? 0];
  const lines = [`${rar.mc}${rar.name} ${roll.kind === 'relic' ? 'Relic' : 'Weapon'}`];
  for (const [id, v] of Object.entries(roll.affixes)) lines.push(affixLine(roll.kind, id, v));
  if (roll.kind === 'relic') lines.push('§8Works from your hotbar (up to 3)');
  const tok = `§8${roll.kind === 'relic' ? 'br' : 'bw'}|${R_INDEX[roll.rarity] ?? 0}|${Object.entries(roll.affixes).map(([id, v]) => `${CODES[id]}${v}`).join(',')}`;
  lines.push(tok.slice(0, 49));
  safe(() => item.setLore(lines.filter(Boolean)));
  safe(() => (item.nameTag = `${rar.mc}${roll.name}`));
  return item;
}

/** A relic, rolled. @returns {ItemStack} */
export function makeRelic(stars = 1, opts = {}) {
  const rar = opts.rarity ? RARITIES[R_INDEX[opts.rarity] ?? 0] : rollRarity(stars, opts.luck ?? 0, opts.min ?? 'common');
  const baseKey = opts.base ?? pick(Object.keys(L.relics));
  const affixes = rollRelicAffixes(baseKey, rar);
  const first = Object.keys(affixes)[0] ?? 'mana';
  const name = R_INDEX[rar.id] >= R_INDEX.legendary ? legendName() : plainName(first, L.relics[baseKey].name);
  return writeRoll(new ItemStack(`bc:${baseKey}`, 1), { kind: 'relic', rarity: rar.id, affixes, name });
}

/** A weapon (a vanilla sword or axe), rolled. @returns {ItemStack} */
export function makeWeapon(stars = 1, opts = {}) {
  const rar = opts.rarity ? RARITIES[R_INDEX[opts.rarity] ?? 0] : rollRarity(stars, opts.luck ?? 0, opts.min ?? 'common');
  const id = pick(L.weaponBases[rar.id] ?? L.weaponBases.common);
  const affixes = rollWeaponAffixes(rar);
  const first = Object.keys(affixes)[0] ?? 'sharp';
  const name = R_INDEX[rar.id] >= R_INDEX.legendary ? legendName() : plainName(first, BASE_NAMES[id] ?? 'Blade');
  return writeRoll(new ItemStack(id, 1), { kind: 'weapon', rarity: rar.id, affixes, name });
}

/** A relic or a weapon (relics a little likelier). */
export function makeRolled(stars = 1, opts = {}) {
  return Math.random() < 0.58 ? makeRelic(stars, opts) : makeWeapon(stars, opts);
}

/** Reroll an item's affixes, keeping its rarity (and a Legendary's name). Returns the new roll, or undefined. */
export function reforge(item) {
  const roll = readRoll(item);
  if (!roll) return undefined;
  const rar = RARITIES[R_INDEX[roll.rarity] ?? 0];
  if (roll.kind === 'relic') {
    const baseKey = item.typeId.replace('bc:', '');
    roll.affixes = rollRelicAffixes(baseKey, rar);
    if (R_INDEX[rar.id] < R_INDEX.legendary) roll.name = plainName(Object.keys(roll.affixes)[0] ?? 'mana', L.relics[baseKey]?.name ?? 'Relic');
  } else {
    roll.affixes = rollWeaponAffixes(rar);
    if (R_INDEX[rar.id] < R_INDEX.legendary) roll.name = plainName(Object.keys(roll.affixes)[0] ?? 'sharp', BASE_NAMES[item.typeId] ?? 'Blade');
  }
  writeRoll(item, roll);
  return roll;
}

/** A piece of armour from one of the sets, already reinforced (and sometimes inscribed) by an old smith. */
export function makeArmorPiece(stars = 1) {
  const A = DATA.armor;
  const sets = Object.keys(A.sets).filter((k) => k !== 'royal' && k !== 'wyvernscale');
  const it = new ItemStack(pieceId(pick(sets), pick(A.slots)), 1);
  const plus = Math.min(A.reinforceMax, 1 + Math.floor(Math.random() * Math.min(3, 1 + stars / 2)));
  writeUpgrades(it, { plus, rune: Math.random() < 0.3 ? pick(Object.keys(A.runes)) : '', mantle: '' });
  return it;
}

// ------------------------------------------------------------------------------- chest tables
/** @type {{journal?: (stars: number, treasure?: boolean) => ItemStack | undefined, map?: (stars: number) => ItemStack | undefined}} */
const makers = {};
/** exploration.js registers how journals and Explorer's Maps are written. */
export function setLootMakers(m) {
  Object.assign(makers, m);
}

// [item, min, max, chance]; specials: scroll, journal, map (an Explorer's Map), tmap (a treasure map), amulet, armor
// rolled: [chance, lowest rarity]
const TABLES = {
  spire_1: { items: [['bc:mana_crystal', 2, 5, 0.9], ['bc:ancient_page', 1, 2, 0.6], ['scroll', 1, 1, 0.4], ['minecraft:book', 1, 3, 0.5], ['journal', 1, 1, 0.3]], rolled: [0.3, 'common'] },
  spire_2: { items: [['bc:mana_crystal', 3, 6, 0.9], ['bc:rune_shard', 1, 2, 0.5], ['scroll', 1, 2, 0.5], ['bc:mana_potion', 1, 2, 0.5]], rolled: [0.45, 'common'] },
  spire_3: { items: [['bc:mana_crystal', 4, 8, 0.9], ['bc:rune_shard', 1, 3, 0.6], ['scroll', 1, 2, 0.6], ['bc:greater_mana_potion', 1, 1, 0.4], ['map', 1, 1, 0.2]], rolled: [0.6, 'uncommon'] },
  spire_4: { items: [['bc:mana_crystal', 5, 10, 1], ['bc:star_fragment', 1, 1, 0.3], ['scroll', 2, 3, 0.6], ['amulet', 1, 1, 0.2], ['armor', 1, 1, 0.25]], rolled: [0.75, 'uncommon'] },
  spire_top: { items: [['bc:mana_crystal', 8, 14, 1], ['bc:star_fragment', 1, 2, 1], ['bc:ancient_page', 2, 4, 1], ['bc:doubloon', 60, 120, 1], ['amulet', 1, 1, 0.4]],
    rolled: [1, 'rare'], extra: 1 },
  hoard: { items: [['bc:doubloon', 40, 90, 1], ['minecraft:gold_ingot', 4, 10, 1], ['minecraft:diamond', 1, 3, 0.5], ['bc:star_fragment', 1, 1, 0.3], ['tmap', 1, 1, 0.3]],
    rolled: [0.85, 'uncommon'] },
  cata_room: { items: [['bc:mana_crystal', 1, 4, 0.8], ['minecraft:bone', 2, 6, 0.7], ['bc:ancient_page', 1, 2, 0.5], ['scroll', 1, 1, 0.35], ['journal', 1, 1, 0.3]], rolled: [0.3, 'common'] },
  cata_treasure: { items: [['bc:doubloon', 25, 60, 1], ['minecraft:gold_ingot', 2, 6, 0.8], ['minecraft:diamond', 1, 2, 0.35], ['minecraft:emerald', 1, 4, 0.5], ['armor', 1, 1, 0.2]],
    rolled: [0.7, 'uncommon'] },
  cata_boss: { items: [['bc:ancient_page', 3, 6, 1], ['bc:mana_crystal', 6, 12, 1], ['bc:star_fragment', 1, 1, 0.5], ['bc:doubloon', 50, 100, 1], ['amulet', 1, 1, 0.3]],
    rolled: [1, 'rare'] },
  library: { items: [['bc:ancient_page', 2, 4, 1], ['minecraft:book', 2, 5, 0.8], ['scroll', 1, 2, 0.8], ['journal', 1, 2, 0.8], ['map', 1, 1, 0.2]], rolled: [0.2, 'common'] },
  hamlet: { items: [['minecraft:bread', 2, 5, 0.7], ['minecraft:coal', 2, 6, 0.5], ['minecraft:iron_ingot', 1, 3, 0.4], ['bc:doubloon', 4, 15, 0.7], ['journal', 1, 1, 0.5],
    ['tmap', 1, 1, 0.08]], rolled: [0.2, 'common'] },
  crypt: { items: [['minecraft:bone', 3, 8, 0.9], ['bc:doubloon', 8, 25, 0.8], ['bc:hollow_ember', 1, 2, 0.5], ['journal', 1, 1, 0.3], ['scroll', 1, 1, 0.3]], rolled: [0.35, 'common'] },
  watchtower: { items: [['minecraft:arrow', 6, 16, 0.8], ['minecraft:iron_ingot', 1, 4, 0.6], ['bc:doubloon', 10, 30, 0.9], ['scroll', 1, 1, 0.4], ['map', 1, 1, 0.15]],
    rolled: [0.3, 'common'] },
  caravan: { items: [['bc:doubloon', 15, 40, 1], ['minecraft:emerald', 1, 3, 0.6], ['minecraft:bread', 2, 6, 0.7], ['bc:mana_potion', 1, 2, 0.5], ['map', 1, 1, 0.2]],
    rolled: [0.25, 'common'] },
  crater: { items: [['bc:star_fragment', 1, 2, 1], ['bc:mana_crystal', 4, 8, 1], ['minecraft:amethyst_shard', 3, 8, 0.8]], rolled: [0.3, 'uncommon'] },
  starfall: { items: [['bc:star_fragment', 1, 1, 1], ['bc:mana_crystal', 1, 3, 0.8]], rolled: [0.1, 'common'] },
  bones: { items: [['bc:doubloon', 20, 50, 1], ['minecraft:bone', 4, 10, 1], ['minecraft:gold_ingot', 1, 4, 0.6], ['tmap', 1, 1, 0.3]], rolled: [0.5, 'uncommon'] },
  battlefield: { items: [['minecraft:iron_ingot', 2, 5, 0.8], ['bc:doubloon', 10, 30, 0.9], ['scroll', 1, 2, 0.5], ['journal', 1, 1, 0.5], ['bc:hollow_ember', 1, 2, 0.5],
    ['armor', 1, 1, 0.2]], rolled: [0.45, 'common'] },
  witch: { items: [['bc:mana_potion', 1, 3, 0.9], ['bc:greater_mana_potion', 1, 1, 0.3], ['bc:sprite_dust', 1, 3, 0.7], ['scroll', 1, 1, 0.5], ['minecraft:glowstone_dust', 2, 6, 0.6]],
    rolled: [0.25, 'common'], relicsOnly: true },
  cache: { items: [['bc:doubloon', 25, 60, 1], ['minecraft:gold_ingot', 2, 5, 0.8], ['minecraft:emerald', 1, 4, 0.6], ['bc:mana_crystal', 2, 5, 0.6]], rolled: [0.6, 'common'] },
};
export const TABLE_NAMES = Object.keys(TABLES);

/**
 * The items of a landmark chest.
 * @param {string} table @param {number} stars @param {{luck?: number, fortune?: number, treasure?: boolean, untamed?: boolean}} [o]
 * @returns {ItemStack[]}
 */
export function chestItems(table, stars = 1, o = {}) {
  const T = TABLES[table];
  if (!T) return [];
  const out = [];
  const more = 1 + 0.15 * Math.max(0, stars - 1);
  for (const [id, lo, hi, chance] of T.items) {
    const c = id === 'tmap' && o.treasure ? Math.min(1, chance * 2.5) : chance;
    if (Math.random() > c) continue;
    const n = Math.max(1, Math.floor(rand(lo, hi + 1) * (id === 'bc:doubloon' ? more * (1 + (o.fortune ?? 0) / 100) : id.startsWith('bc:') || id.startsWith('minecraft:') ? more : 1)));
    let it;
    if (id === 'scroll') it = makeScroll();
    else if (id === 'journal') it = makers.journal?.(stars, !!o.treasure);
    else if (id === 'map') it = makers.map?.(stars);
    else if (id === 'tmap') it = new ItemStack('bc:treasure_map', 1);
    else if (id === 'amulet') it = new ItemStack(`bc:${pick(Object.keys(DATA.amulets))}`, 1);
    else if (id === 'armor') it = makeArmorPiece(stars);
    else it = safe(() => new ItemStack(id, Math.min(64, n)));
    if (it) out.push(it);
  }
  const [chance, min] = T.rolled;
  const luck = (o.luck ?? 0) + (o.untamed ? 20 : 0);
  const rolls = 1 + (T.extra ?? 0) + (Math.random() < luck / 100 ? 1 : 0);
  for (let i = 0; i < rolls; i++) {
    if (Math.random() > Math.min(1, chance + 0.05 * Math.max(0, stars - 1))) continue;
    out.push(T.relicsOnly ? makeRelic(stars, { min, luck }) : makeRolled(stars, { min, luck }));
  }
  return out;
}

/** Fill a chest block with a table's items. Returns the items (for tests and logs). */
export function fillChest(block, table, stars = 1, o = {}) {
  const items = chestItems(table, stars, o);
  const inv = safe(() => block.getComponent('minecraft:inventory')?.container);
  if (!inv) return items;
  const free = [];
  for (let i = 0; i < inv.size; i++) free.push(i);
  free.sort(() => Math.random() - 0.5);
  items.forEach((it, k) => safe(() => inv.setItem(free[k % free.length], it)));
  return items;
}

/** Is this a Legendary or Mythic roll? */
export function isLegend(roll) {
  return !!roll && (R_INDEX[roll.rarity] ?? 0) >= R_INDEX.legendary;
}
export function rarityIndex(id) {
  return R_INDEX[id] ?? 0;
}
export { world };
