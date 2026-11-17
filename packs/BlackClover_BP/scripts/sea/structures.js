// Script-placed sea structures: pirate outpost islands and sunken wrecks.
// They appear out of sight (behind the player) while sailing over deep water.
import { BlockPermutation, ItemStack, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { STRUCTURES } from '../generated/structures.js';
import { V, pick, rand, safe, yawOf } from '../core/util.js';
import { spawnCaptain } from './captains.js';

const SPACING = 200;
const KEY = 'bc:sea_structs';

const LOOT = {
  outpost: [['bc:doubloon', 6, 14, 1], ['bc:cannonball', 2, 6, 0.8], ['minecraft:gunpowder', 2, 5, 0.6], ['minecraft:cooked_cod', 2, 5, 0.7],
    ['bc:mana_crystal', 1, 3, 0.6], ['bc:ship_kit', 1, 1, 0.08], ['fruit', 1, 1, 0.1]],
  wreck: [['bc:doubloon', 15, 30, 1], ['minecraft:gold_ingot', 2, 5, 0.8], ['minecraft:emerald', 1, 3, 0.6], ['bc:mana_crystal', 2, 4, 0.7],
    ['minecraft:heart_of_the_sea', 1, 1, 0.12], ['fruit', 1, 1, 0.35], ['bc:leviathan_lure', 1, 1, 0.06], ['bc:treasure_map', 1, 1, 0.3]],
  dungeon: [['bc:ancient_page', 1, 3, 0.9], ['bc:mana_crystal', 2, 5, 0.8], ['minecraft:gold_ingot', 3, 7, 0.7], ['minecraft:diamond', 1, 2, 0.35],
    ['robe', 1, 1, 0.15], ['bc:clover_charm', 1, 1, 0.04], ['bc:treasure_map', 1, 1, 0.2]],
  camp: [['bc:mana_crystal', 2, 4, 0.9], ['bc:mana_cookie', 2, 5, 0.7], ['minecraft:bread', 3, 6, 0.8], ['bc:knight_contract', 1, 1, 0.25],
    ['bc:ancient_page', 1, 1, 0.3], ['amulet', 1, 1, 0.08], ['robe', 1, 1, 0.1], ['bc:companion_whistle', 1, 1, 0.15]],
  treasure: [['bc:doubloon', 30, 60, 1], ['minecraft:gold_ingot', 4, 9, 0.9], ['minecraft:diamond', 1, 4, 0.6], ['minecraft:emerald', 2, 6, 0.6],
    ['fruit', 1, 1, 0.2], ['bc:ancient_page', 1, 2, 0.4]],
};
const ROBE_IDS = Object.keys(DATA.robes);

function perm(name, states) {
  try {
    return BlockPermutation.resolve(name, states);
  } catch {
    try {
      return BlockPermutation.resolve(name);
    } catch {
      return undefined;
    }
  }
}

function isWaterId(id) {
  return id === 'minecraft:water' || id === 'minecraft:flowing_water';
}

/** Water surface and sea floor at a column, or undefined if not open water. */
export function column(dim, x, z) {
  let surface;
  for (let y = 78; y >= 30; y--) {
    const b = safe(() => dim.getBlock({ x, y, z }));
    if (!b) return undefined; // chunk not loaded
    if (surface === undefined) {
      if (isWaterId(b.typeId)) surface = y;
      else if (!b.isAir) return undefined; // land
      continue;
    }
    if (!isWaterId(b.typeId) && !b.isWaterlogged) return { surface, floor: y };
  }
  return surface === undefined ? undefined : { surface, floor: 30 };
}

function records() {
  const v = world.getDynamicProperty(KEY);
  try {
    return typeof v === 'string' ? JSON.parse(v) : [];
  } catch {
    return [];
  }
}

function remember(x, z) {
  const r = records();
  r.push([Math.round(x), Math.round(z)]);
  world.setDynamicProperty(KEY, JSON.stringify(r.slice(-300)));
}

export function farFromOthers(x, z, min = SPACING) {
  return records().every(([a, b]) => (a - x) ** 2 + (b - z) ** 2 > min * min);
}

export function lootItems(table) {
  const out = [];
  for (const [id, lo, hi, chance] of LOOT[table]) {
    if (Math.random() > chance) continue;
    const n = Math.floor(rand(lo, hi + 1));
    if (id === 'fruit') out.push(new ItemStack(`bc:fruit_${pick(DATA.fruitOrder)}`, 1));
    else if (id === 'robe') out.push(new ItemStack(`bc:${pick(ROBE_IDS)}`, 1));
    else if (id === 'amulet') out.push(new ItemStack(`bc:${pick(Object.keys(DATA.amulets))}`, 1));
    else out.push(new ItemStack(id, Math.max(1, n)));
  }
  return out;
}

export function fill(block, table) {
  const inv = block.getComponent('minecraft:inventory')?.container;
  if (!inv) return;
  for (const it of lootItems(table)) inv.setItem(Math.floor(Math.random() * inv.size), it);
}

/**
 * Build a blueprint. Runs as a background job so big structures never lag the game.
 * @param {import('@minecraft/server').Dimension} dim
 * @param {'outpost'|'wreck'|'dungeon'|'camp'} kind
 * @param {{x:number,y:number,z:number}} anchor
 * @param {{bountyFor?: string, captainName?: string, captainFruit?: string}} [opts]
 */
export function build(dim, kind, anchor, opts = {}) {
  const bp = STRUCTURES[kind];
  const pal = bp.palette.map(([n, s]) => perm(n, s));
  const sand = perm('minecraft:sand');
  const sandstone = perm('minecraft:sandstone');
  const ax = Math.floor(anchor.x);
  const ay = Math.floor(anchor.y);
  const az = Math.floor(anchor.z);
  function* job() {
    let n = 0;
    const cols = bp.columns;
    for (let i = 0; i < cols.length; i += 3) {
      const x = ax + cols[i];
      const z = az + cols[i + 1];
      const top = ay + cols[i + 2];
      let floor = ay - 1;
      for (let y = ay; y > ay - 40; y--) {
        const b = safe(() => dim.getBlock({ x, y, z }));
        if (!b) break;
        if (!isWaterId(b.typeId) && !b.isAir) {
          floor = y;
          break;
        }
        floor = y - 1;
      }
      for (let y = floor + 1; y <= top; y++) {
        const b = safe(() => dim.getBlock({ x, y, z }));
        const p = top - y < 3 ? sand : sandstone;
        if (b && p) safe(() => b.setPermutation(p));
        if (++n % 160 === 0) yield;
      }
    }
    const bl = bp.blocks;
    for (let i = 0; i < bl.length; i += 4) {
      const b = safe(() => dim.getBlock({ x: ax + bl[i], y: ay + bl[i + 1], z: az + bl[i + 2] }));
      const p = pal[bl[i + 3]];
      if (b && p) safe(() => b.setPermutation(p));
      if (++n % 160 === 0) yield;
    }
    yield;
    for (const c of bp.chests) {
      const [dx, dy, dz, table] = [Number(c[0]), Number(c[1]), Number(c[2]), String(c[3])];
      const b = safe(() => dim.getBlock({ x: ax + dx, y: ay + dy, z: az + dz }));
      if (b) safe(() => fill(b, table));
    }
    for (const sp of bp.spawns) {
      const [dx, dy, dz, what] = [Number(sp[0]), Number(sp[1]), Number(sp[2]), String(sp[3])];
      const loc = { x: ax + dx + 0.5, y: ay + dy, z: az + dz + 0.5 };
      if (what === 'captain') {
        if (opts.bountyFor || Math.random() < 0.6) spawnCaptain(dim, loc, { name: opts.captainName, fruit: opts.captainFruit, bountyFor: opts.bountyFor });
      } else safe(() => dim.spawnEntity(what, loc));
    }
  }
  remember(ax, az);
  if (bp.traps?.length) {
    const v = world.getDynamicProperty('bc:traps');
    let traps = [];
    try {
      traps = typeof v === 'string' ? JSON.parse(v) : [];
    } catch {
      traps = [];
    }
    for (const t of bp.traps) traps.push([ax + Number(t[0]), ay + Number(t[1]), az + Number(t[2]), dim.id]);
    world.setDynamicProperty('bc:traps', JSON.stringify(traps.slice(-150)));
  }
  system.runJob(job());
}

/** Try to raise a structure somewhere behind a sailing player. */
function trySpawn(p) {
  if (p.dimension.id !== 'minecraft:overworld') return;
  const here = column(p.dimension, Math.floor(p.location.x), Math.floor(p.location.z));
  if (!here || here.surface - here.floor < 5) return;
  const yaw = yawOf(p.getViewDirection()) + 180 + rand(-70, 70);
  const r = (yaw * Math.PI) / 180;
  const dist = rand(56, 80);
  const x = Math.floor(p.location.x - Math.sin(r) * dist);
  const z = Math.floor(p.location.z + Math.cos(r) * dist);
  if (!farFromOthers(x, z)) return;
  const col = column(p.dimension, x, z);
  if (!col) return;
  const depth = col.surface - col.floor;
  if (depth >= 10 && Math.random() < 0.45) build(p.dimension, 'wreck', { x, y: col.floor + 1, z });
  else if (depth >= 4 && depth <= 30) build(p.dimension, 'outpost', { x, y: col.surface, z });
}

system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    if (Math.random() < 0.35) safe(() => trySpawn(p), 'seaSpawn');
  }
}, 200);

export { V };
