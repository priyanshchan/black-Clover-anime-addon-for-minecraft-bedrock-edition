// Landmarks (v1.1.0): every region has three to eight of them, seeded where they lie - Mage Spires, Wyvern Roosts,
// Ancient Catacombs, ruined hamlets, graveyards, Mana Obelisks, fairy rings, watchtowers, wrecked caravans, star craters,
// colossal bones, forgotten battlefields, Lost Waygates and hedge witch huts. A landmark is raised out of sight as
// explorers come near (never in front of you), fitted to the ground, and filled with random loot for its region's danger.
// Its guards and its master appear when someone gets close; Mana Spawners call up more until they are broken.
import { BlockPermutation, ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { CATA, LANDMARK_BP } from '../generated/landmarks.js';
import { emit } from '../core/bus.js';
import { anim, particle, rgb, sound, title } from '../core/fx.js';
import { chestItems, fillChest, makeRelic, rollRarity } from '../core/loot.js';
import { addMods, mods } from '../core/mods.js';
import { addMana, maxMana, state } from '../core/data.js';
import { hash, pickR, pickW, rng, worldSeed } from '../core/seed.js';
import { loadBig, saveBig } from '../core/store.js';
import { V, alive, pick, rand, safe, yawOf } from '../core/util.js';
import { cellOf, chooseKind, compassWord, groundAt, keyOf, kindFits, regionAt, regions, stars as starText } from './regions.js';
import { addGate } from './waygate.js';
import { makeElite } from './elites.js';
import { setupKnight } from './knights.js';
import { joinParty } from './companions.js';

const W = DATA.world;
const KEY = 'bc:landmarks';
const EXTRA = 'bc:extra_slots';
const SPAWNERS = 'bc:spawners';
const BUILD_R = 112;   // raised this far out...
const VIEW_OK = 84;    // ...where you might see it only when it is this far away (or very close and out of sight)
const FOUND_R = 26;

/** @typedef {{id: string, kind: string, sub: string, x: number, y: number, z: number, dim: string, stars: number, state: string, region: string,
 *   found: string[], looted: string[], cleared: boolean, spawns: [number, number, number, string][], marks: Record<string, number[][]>,
 *   chests: [number, number, number, string][], mimics: number[][], boss: string, night: number, prayed: string[], done: string[], resident: string, t: number}} LRec */

// ------------------------------------------------------------------------------- records
/** @type {Record<string, LRec> | undefined} */
let recs;
let dirty = false;
export function landmarks() {
  if (!recs) recs = loadBig(KEY, {});
  return /** @type {Record<string, LRec>} */ (recs);
}
function persist() {
  dirty = true;
}
system.runInterval(() => {
  if (!dirty || !recs) return;
  dirty = false;
  if (!saveBig(KEY, recs)) {
    const ks = Object.keys(recs).sort((a, b) => (recs?.[a].t ?? 0) - (recs?.[b].t ?? 0));
    for (const k of ks.slice(0, Math.ceil(ks.length / 4))) delete recs[k];
    saveBig(KEY, recs);
  }
}, 100);

/** Extra, one-off landmarks (the stars of a Starfall night). @type {{id: string, x: number, z: number, kind: string, until: number}[] | undefined} */
let extraList;
function extras() {
  if (!extraList) extraList = loadBig(EXTRA, []);
  return /** @type {{id: string, x: number, z: number, kind: string, until: number}[]} */ (extraList);
}
export function addExtraSlot(kind, x, z, days = 1) {
  const list = extras().filter((e) => e.until >= (safe(() => world.getDay()) ?? 0));
  const id = `x${hash(kind, x, z, Date.now()) % 1000000}`;
  list.push({ id, x: Math.floor(x), z: Math.floor(z), kind, until: (safe(() => world.getDay()) ?? 0) + days });
  extraList = list.slice(-40);
  saveBig(EXTRA, extraList);
  return id;
}

/**
 * Every landmark slot near a point (in regions somebody has discovered), with its record if it has been raised.
 * @returns {{id: string, x: number, z: number, kind: string, region: string, rec?: LRec}[]}
 */
export function slotsNear(x, z, cells = 1) {
  const { rx, rz } = cellOf(x, z);
  const all = regions();
  const out = [];
  for (let i = rx - cells; i <= rx + cells; i++) {
    for (let j = rz - cells; j <= rz + cells; j++) {
      const k = keyOf(i, j);
      const r = all[k];
      if (!r) continue;
      r.slots.forEach((s, n) => {
        const id = `${k}#${n}`;
        out.push({ id, x: s.x, z: s.z, kind: landmarks()[id]?.kind ?? s.kind, region: k, rec: landmarks()[id] });
      });
    }
  }
  const day = safe(() => world.getDay()) ?? 0;
  for (const e of extras()) {
    if (e.until < day && !landmarks()[e.id]) continue;
    if (Math.abs(e.x - x) > SIZE_CELLS(cells) || Math.abs(e.z - z) > SIZE_CELLS(cells)) continue;
    const { rx: ex, rz: ez } = cellOf(e.x, e.z);
    out.push({ id: e.id, x: e.x, z: e.z, kind: e.kind, region: keyOf(ex, ez), rec: landmarks()[e.id] });
  }
  return out;
}
const SIZE_CELLS = (cells) => W.regionSize * (cells + 1);

export function nameOf(kind) {
  return kind === 'starfall' ? 'Fallen Star' : W.landmarks[kind]?.name ?? 'landmark';
}
/** The nearest landmark a player has not found yet (optionally of one kind). */
export function nearestUnfound(p, kind = '', maxDist = 900) {
  let best;
  let bd = maxDist;
  for (const s of slotsNear(p.location.x, p.location.z, 2)) {
    if (s.rec?.state === 'lost' || s.rec?.found.includes(p.id) || (kind && s.kind !== kind)) continue;
    const d = Math.hypot(s.x - p.location.x, s.z - p.location.z);
    if (d < bd) {
      bd = d;
      best = s;
    }
  }
  return best;
}
export function foundBy(p) {
  return Object.values(landmarks()).filter((r) => r.found.includes(p.id));
}

// ------------------------------------------------------------------------------- building
const PERM = new Map();
function perm(name, states) {
  const k = states ? `${name}${JSON.stringify(states)}` : name;
  if (PERM.has(k)) return PERM.get(k);
  let pm;
  try {
    pm = BlockPermutation.resolve(name, states);
  } catch {
    try {
      pm = BlockPermutation.resolve(name);
    } catch {
      pm = undefined;
    }
  }
  PERM.set(k, pm);
  return pm;
}
const SOFT = (id) => id === 'minecraft:air' || id.includes('leaves') || id.includes('grass') && id !== 'minecraft:grass_block' || id.includes('flower') || id.includes('fern')
  || id.includes('bush') || id === 'minecraft:snow_layer' || id.includes('water') || id.includes('vine') || id.includes('sapling') || id.includes('mushroom');
const FILLER = { capital: 'minecraft:stone_bricks', diamond_fort: 'minecraft:stone_bricks', spade_citadel: 'minecraft:blackstone', spire: 'minecraft:stone_bricks', roost: 'minecraft:stone', catacombs: 'minecraft:stone_bricks', obelisk: 'minecraft:polished_deepslate',
  watchtower: 'minecraft:cobblestone', lost_waygate: 'minecraft:stone_bricks', crater: 'minecraft:stone' };
const RADIUS = { capital: 24, diamond_fort: 11, spade_citadel: 11, heart_sanctum: 10, spire: 7, roost: 10, catacombs: 4, hamlet: 6, graveyard: 9, obelisk: 5, fairy_ring: 7, watchtower: 6, caravan: 7, crater: 8, skeleton: 9,
  battlefield: 10, lost_waygate: 5, witch_hut: 6, starfall: 5 };
const TOL = { capital: 9, diamond_fort: 7, spade_citadel: 7, spire: 6, roost: 9, catacombs: 8, crater: 7, battlefield: 7, starfall: 7 };

/**
 * Lay one blueprint into the world (a generator, so big builds are spread over ticks). Absolute positions of its chests,
 * spawners, marks, spawns and traps are added to `out`.
 */
function* layBlueprint(dim, bp, ax, ay, az, filler, out) {
  const air = perm('minecraft:air');
  const fill = perm(filler);
  let n = 0;
  const cl = bp.clears ?? [];
  for (let i = 0; i < cl.length; i += 4) {
    for (let y = cl[i + 2]; y <= cl[i + 3]; y++) {
      const b = safe(() => dim.getBlock({ x: ax + cl[i], y: ay + y, z: az + cl[i + 1] }));
      if (b && !b.isAir) safe(() => b.setPermutation(air));
      if (++n % 220 === 0) yield;
    }
  }
  const fd = bp.found ?? [];
  for (let i = 0; i < fd.length; i += 2) {
    for (let y = ay - 1; y > ay - 14; y--) {
      const b = safe(() => dim.getBlock({ x: ax + fd[i], y, z: az + fd[i + 1] }));
      if (!b || !SOFT(b.typeId)) break;
      safe(() => b.setPermutation(fill));
      if (++n % 220 === 0) yield;
    }
  }
  const pal = bp.palette.map(([nm, st]) => perm(nm, st));
  const bl = bp.blocks;
  for (let i = 0; i < bl.length; i += 4) {
    const b = safe(() => dim.getBlock({ x: ax + bl[i], y: ay + bl[i + 1], z: az + bl[i + 2] }));
    const p = pal[bl[i + 3]];
    if (b && p) safe(() => b.setPermutation(p));
    if (++n % 220 === 0) yield;
  }
  for (const c of bp.chests) out.chests.push([ax + c[0], ay + c[1], az + c[2], String(c[3])]);
  for (const s of bp.spawners ?? []) out.spawners.push([ax + s[0], ay + s[1], az + s[2], String(s[3])]);
  for (const s of bp.spawns) out.spawns.push([ax + s[0] + 0.5, ay + s[1], az + s[2] + 0.5, String(s[3])]);
  for (const t of bp.traps ?? []) out.traps.push([ax + t[0], ay + t[1], az + t[2]]);
  for (const [name, dx, dy, dz] of bp.marks ?? []) (out.marks[name] ??= []).push([ax + dx, ay + dy, az + dz]);
}

/** Lay a blueprint over several ticks; `finish(out)` runs when it is done (v1.2.0: the Royal Capital is built this way). */
export function buildBlueprint(dim, bp, x, y, z, filler, finish) {
  const out = { chests: [], spawners: [], spawns: [], traps: [], marks: {} };
  function* job() {
    yield* layBlueprint(dim, bp, x, y, z, filler, out);
    safe(() => finish?.(out));
  }
  system.runJob(job());
  return out;
}

function* layBlocks(dim, list) {
  let n = 0;
  for (const [x, y, z, name] of list) {
    const b = safe(() => dim.getBlock({ x, y, z }));
    const p = perm(name);
    if (b && p) safe(() => b.setPermutation(p));
    if (++n % 220 === 0) yield;
  }
}

/** Is a spot level enough for a landmark of this size? Returns the ground there, or undefined. */
export function levelAt(dim, x, z, kind) {
  const g = groundAt(dim, x, z);
  if (!g || g.water) return undefined;
  const r = RADIUS[kind] ?? 6;
  const tol = TOL[kind] ?? 5;
  for (const [dx, dz] of [[r, 0], [-r, 0], [0, r], [0, -r], [r * 0.7, r * 0.7], [-r * 0.7, r * 0.7], [r * 0.7, -r * 0.7], [-r * 0.7, -r * 0.7]]) {
    const o = groundAt(dim, Math.floor(x + dx), Math.floor(z + dz));
    if (!o || (o.water && kind !== 'caravan') || Math.abs(o.y - g.y) > tol) return undefined;
  }
  return g;
}

const WYVERN_OF = (land) => Object.entries(W.wyverns).find(([, w]) => w.land.includes(land))?.[0] ?? 'storm_wyvern';

/**
 * Raise a landmark at a slot. Returns 'built', 'lost' (no room here, ever) or 'wait' (the ground is not loaded yet).
 * @param {{id: string, x: number, z: number, kind: string, region: string}} slot
 */
export function raise(dim, slot, opts = {}) {
  const r = rng(hash(worldSeed(), 'landmark', slot.id));
  const g0 = groundAt(dim, slot.x, slot.z);
  if (!g0) return 'wait';
  const reg = regions()[slot.region];
  const stars = reg?.stars ?? 1;
  const traits = reg?.traits ?? [];
  let kind = slot.kind;
  if (kind !== 'starfall' && !kindFits(kind, g0.land)) kind = g0.water ? kind : chooseKind(r, g0.land, stars, traits, ['spire', 'roost', 'catacombs', 'lost_waygate'], reg?.kingdom ?? '');
  let spot;
  for (const [ox, oz] of [[0, 0], [9, 0], [-9, 0], [0, 9], [0, -9], [14, 14], [-14, -14], [14, -14], [-14, 14]]) {
    const g = levelAt(dim, slot.x + ox, slot.z + oz, kind);
    if (g) {
      spot = { x: slot.x + ox, y: g.y, z: slot.z + oz, land: g.land };
      break;
    }
  }
  /** @type {LRec} */
  const rec = { id: slot.id, kind, sub: '', x: slot.x, y: g0.y, z: slot.z, dim: dim.id, stars, state: 'lost', region: slot.region, found: [], looted: [],
    cleared: false, spawns: [], marks: {}, chests: [], mimics: [], boss: '', night: -1, prayed: [], done: [], resident: '', t: Date.now() };
  if (!spot) {
    landmarks()[slot.id] = rec;
    persist();
    return 'lost';
  }
  rec.x = spot.x;
  rec.y = spot.y;
  rec.z = spot.z;
  rec.state = 'built';
  const out = { chests: [], spawners: [], spawns: [], traps: [], marks: {} };
  const jobs = [];
  const filler = FILLER[kind] ?? (spot.land === 'desert' ? 'minecraft:sandstone' : spot.land === 'frozen' ? 'minecraft:packed_ice' : 'minecraft:dirt');
  if (kind === 'roost') {
    rec.sub = WYVERN_OF(spot.land);
    jobs.push(layBlueprint(dim, LANDMARK_BP[`roost_${rec.sub.split('_')[0]}`], spot.x, spot.y, spot.z, filler, out));
  } else if (kind === 'hamlet') {
    rec.sub = pickW(r, [['empty', 3], ['bandits', 3], ['hollow', 2], ['hermit', 2]]);
    jobs.push(layBlueprint(dim, LANDMARK_BP.hamlet_well, spot.x, spot.y, spot.z, filler, out));
    const parts = ['cottage', 'cottage', 'longhouse', 'chapel', 'farm', 'graves', 'cottage'].sort(() => r() - 0.5).slice(0, 3 + Math.floor(r() * 3));
    const placed = [];
    for (const part of parts) {
      for (let tries = 0; tries < 8; tries++) {
        const a = r() * Math.PI * 2;
        const d = 11 + r() * 6;
        const px = Math.floor(spot.x + Math.cos(a) * d);
        const pz = Math.floor(spot.z + Math.sin(a) * d);
        if (placed.some(([qx, qz]) => Math.hypot(qx - px, qz - pz) < 11)) continue;
        const g = groundAt(dim, px, pz);
        if (!g || g.water || Math.abs(g.y - spot.y) > 6) continue;
        placed.push([px, pz]);
        jobs.push(layBlueprint(dim, LANDMARK_BP[`hamlet_${part}`], px, g.y, pz, filler, out));
        break;
      }
    }
    if (rec.sub === 'bandits') {
      for (let i = 0; i < 3 + Math.floor(r() * 3); i++) out.spawns.push([spot.x + rand(-10, 10), spot.y + 1, spot.z + rand(-10, 10), i === 0 ? 'bc:bandit_archer' : 'bc:bandit']);
    }
  } else if (kind === 'catacombs') {
    catacombs(dim, spot, r, stars, filler, out, jobs);
  } else {
    const bp = LANDMARK_BP[kind];
    if (!bp) return 'lost';
    jobs.push(layBlueprint(dim, bp, spot.x, spot.y, spot.z, filler, out));
  }
  landmarks()[slot.id] = rec;
  const finish = () => {
    rec.spawns = out.spawns;
    rec.marks = out.marks;
    rec.chests = out.chests;
    const loot = { treasure: traits.includes('treasure'), untamed: traits.includes('untamed') };
    for (const [x, y, z, table] of out.chests) {
      const b = safe(() => dim.getBlock({ x, y, z }));
      if (b) safe(() => fillChest(b, table, stars, loot));
      if (!['spire_top', 'hoard', 'witch', 'starfall'].includes(table) && Math.random() < W.encounters.mimic.chance) rec.mimics.push([x, y, z]);
    }
    // v1.2.0: a roost's hoard often holds an egg
    if (kind === 'roost' && out.chests.length && Math.random() < DATA.dragon.fromHoard) {
      const [x, y, z] = out.chests[0];
      const inv = safe(() => dim.getBlock({ x, y, z })?.getComponent('minecraft:inventory')?.container);
      if (inv) safe(() => inv.setItem(Math.floor(Math.random() * inv.size), new ItemStack(`bc:${DATA.dragon.eggs[rec.sub || 'storm_wyvern']}`, 1)));
      rec.done.push('egg');
    }
    const list = spawnerList();
    for (const [x, y, z, pool] of out.spawners) list.push([x, y, z, pool, dim.id]);
    saveSpawners(list);
    if (out.traps.length) {
      let traps = [];
      safe(() => {
        const v = world.getDynamicProperty('bc:traps');
        traps = typeof v === 'string' ? JSON.parse(v) : [];
      });
      for (const t of out.traps) traps.push([...t, dim.id]);
      safe(() => world.setDynamicProperty('bc:traps', JSON.stringify(traps.slice(-150))));
    }
    persist();
    emit('landmark_raised', rec);
  };
  function* all() {
    for (const j of jobs) yield* j;
    finish();
  }
  system.runJob(all());
  if (opts.log) console.log(`[Black Clover] raised ${kind} at ${spot.x} ${spot.y} ${spot.z}`);
  return 'built';
}

// ------------------------------------------------------------------------------- the Ancient Catacombs: a new maze every time
const ROOM_W = [['crypt', 3], ['library', 2], ['treasure', 1.5], ['spawner', 2.5], ['trap', 1.5], ['prison', 1], ['shrine', 1]];
function catacombs(dim, spot, r, stars, filler, out, jobs) {
  const n = Math.min(10, 5 + Math.floor(stars) + Math.floor(r() * 3));
  const cells = [[0, 0]];
  const has = new Set(['0,0']);
  /** @type {[number[], number[]][]} */
  const edges = [];
  for (let tries = 0; tries < 300 && cells.length < n; tries++) {
    const [i, j] = cells[Math.floor(r() * cells.length)];
    const [di, dj] = pickR(r, [[1, 0], [-1, 0], [0, 1], [0, -1]]);
    const ni = i + di;
    const nj = j + dj;
    if (Math.abs(ni) > 3 || Math.abs(nj) > 3 || has.has(`${ni},${nj}`)) continue;
    has.add(`${ni},${nj}`);
    cells.push([ni, nj]);
    edges.push([[i, j], [ni, nj]]);
  }
  // the guardian's hall is the room farthest from the stair
  const dist = { '0,0': 0 };
  const queue = ['0,0'];
  while (queue.length) {
    const k = /** @type {string} */ (queue.shift());
    for (const [a, b] of edges) {
      const ka = `${a[0]},${a[1]}`;
      const kb = `${b[0]},${b[1]}`;
      const nb = ka === k ? kb : kb === k ? ka : '';
      if (nb && dist[nb] === undefined) {
        dist[nb] = dist[k] + 1;
        queue.push(nb);
      }
    }
  }
  const bossKey = Object.entries(dist).sort((a, b) => b[1] - a[1])[0][0];
  const floor = spot.y - CATA.depth;
  const C = CATA.cell;
  const radius = (k) => (k === bossKey ? 7 : 5);
  const extra = [];
  for (const [i, j] of cells) {
    const k = `${i},${j}`;
    const type = k === '0,0' ? pickR(r, ['library', 'shrine']) : k === bossKey ? 'boss' : pickW(r, ROOM_W);
    const cx = spot.x + i * C;
    const cz = spot.z + j * C;
    jobs.push(layBlueprint(dim, LANDMARK_BP[type === 'boss' ? 'cata_boss' : `cata_${type}`], cx, floor, cz, 'minecraft:stone', out));
    // seal the doorways that lead nowhere
    const R = radius(k);
    for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      if (has.has(`${i + di},${j + dj}`) && edges.some(([a, b]) => (a[0] === i && a[1] === j && b[0] === i + di && b[1] === j + dj) || (b[0] === i && b[1] === j && a[0] === i + di && a[1] === j + dj))) continue;
      for (let w = -1; w <= 1; w++) {
        for (let y = 1; y <= 3; y++) extra.push([cx + (di ? di * R : w), floor + y, cz + (dj ? dj * R : w), 'minecraft:stone_bricks']);
      }
    }
  }
  // halls between connected rooms
  for (const [a, b] of edges) {
    const di = b[0] - a[0];
    const dj = b[1] - a[1];
    const ka = `${a[0]},${a[1]}`;
    const kb = `${b[0]},${b[1]}`;
    const ax = spot.x + a[0] * C;
    const az = spot.z + a[1] * C;
    for (let t = radius(ka) + 1; t <= C - radius(kb) - 1; t++) {
      for (let w = -2; w <= 2; w++) {
        const x = ax + (di ? di * t : w);
        const z = az + (dj ? dj * t : w);
        for (let y = 0; y <= 4; y++) {
          const wall = Math.abs(w) === 2 || y === 0 || y === 4;
          const name = !wall ? 'minecraft:air' : y === 4 && w === 0 && t === Math.round(C / 2) ? 'minecraft:sea_lantern'
            : r() < 0.25 ? 'minecraft:mossy_stone_bricks' : r() < 0.2 ? 'minecraft:cracked_stone_bricks' : 'minecraft:stone_bricks';
          extra.push([x, floor + y, z, name]);
        }
      }
    }
  }
  jobs.push(layBlocks(dim, extra));
  // the stair down, last, so its shaft opens through the first room's ceiling
  jobs.push(layBlueprint(dim, LANDMARK_BP.cata_entrance, spot.x, spot.y, spot.z, filler, out));
}

// ------------------------------------------------------------------------------- raising landmarks as explorers come near
function inView(p, x, z) {
  const d = { x: x - p.location.x, y: 0, z: z - p.location.z };
  const rel = Math.abs(((yawOf(d) - yawOf(p.getViewDirection()) + 540) % 360) - 180);
  return rel < 60;
}
system.runInterval(() => {
  const ps = world.getAllPlayers().filter((p) => p.dimension.id === 'minecraft:overworld');
  /** @type {{p: any, s: any, d: number} | undefined} */
  let best;
  for (const p of ps) {
    safe(() => {
      for (const s of slotsNear(p.location.x, p.location.z, 1)) {
        if (s.rec) continue;
        const d = Math.hypot(s.x - p.location.x, s.z - p.location.z);
        if (d > BUILD_R) continue;
        if (d > 32 && d < VIEW_OK && inView(p, s.x, s.z)) continue;
        if (!best || d < best.d) best = { p, s, d };
      }
    }, 'landmarkScan');
  }
  if (best) {
    const b = best;
    safe(() => raise(b.p.dimension, b.s), 'landmarkRaise');
  }
}, 40);

// ------------------------------------------------------------------------------- the Mana Spawners
const POOLS = { arcane: ['bc:rogue_mage', 'bc:mana_wraith'], hollow: ['bc:hollow_knight', 'bc:hollow_knight', 'bc:mana_wraith'], bandit: ['bc:bandit', 'bc:bandit_archer'],
  devil: ['bc:imp', 'bc:imp', 'bc:dark_disciple'] };
/** @type {[number, number, number, string, string][] | undefined} */
let spawnerCache;
/** @returns {[number, number, number, string, string][]} */
export function spawnerList() {
  if (!spawnerCache) spawnerCache = loadBig(SPAWNERS, []);
  return [...(spawnerCache ?? [])];
}
function saveSpawners(list) {
  spawnerCache = list.slice(-500);
  saveBig(SPAWNERS, spawnerCache);
}
/** One tick of a spawner: call up a foe when someone is near and the room is not already full. */
export function pulseSpawner(dim, sp) {
  const [x, y, z, pool] = sp;
  const at = { x: x + 0.5, y: y + 1, z: z + 0.5 };
  const kinds = POOLS[pool] ?? POOLS.arcane;
  const near = safe(() => dim.getEntities({ location: at, maxDistance: 12 }).filter((e) => kinds.includes(e.typeId)).length) ?? 0;
  if (near >= 4) return 0;
  const n = Math.random() < 0.3 ? 2 : 1;
  for (let i = 0; i < n; i++) {
    const spot = { x: x + 0.5 + rand(-2.5, 2.5), y: y + 1, z: z + 0.5 + rand(-2.5, 2.5) };
    particle(dim, 'bc:magic_circle_ground', V.add(spot, { x: 0, y: 0.05, z: 0 }), { color: rgb('c070ff'), size: 1.6, life: 0.8 });
    safe(() => dim.spawnEntity(pick(kinds), spot));
  }
  particle(dim, 'bc:burst_spark', at, { color: rgb('c070ff'), scale: 0.6 });
  sound(dim, 'bc.portal', at, 0.6, 1.4);
  return n;
}
system.runInterval(() => {
  const list = spawnerList();
  if (!list.length) return;
  let changed = false;
  const ps = world.getAllPlayers();
  for (let i = list.length - 1; i >= 0; i--) {
    const sp = list[i];
    const near = ps.some((p) => p.dimension.id === sp[4] && Math.hypot(p.location.x - sp[0], p.location.y - sp[1], p.location.z - sp[2]) < 20);
    if (!near) continue;
    const dim = safe(() => world.getDimension(sp[4]));
    const b = dim && safe(() => dim.getBlock({ x: sp[0], y: sp[1], z: sp[2] }));
    if (b && b.typeId !== 'bc:mana_spawner') {
      list.splice(i, 1);
      changed = true;
      continue;
    }
    if (dim) safe(() => pulseSpawner(dim, sp));
  }
  if (changed) saveSpawners(list);
}, 100);

world.afterEvents.playerBreakBlock.subscribe((ev) => safe(() => {
  if (ev.brokenBlockPermutation.type.id !== 'bc:mana_spawner') return;
  const l = ev.block.location;
  const list = spawnerList().filter((s) => !(s[0] === l.x && s[1] === l.y && s[2] === l.z));
  saveSpawners(list);
  const at = { x: l.x + 0.5, y: l.y + 0.5, z: l.z + 0.5 };
  safe(() => ev.dimension.spawnItem(new ItemStack('bc:mana_crystal', 2 + Math.floor(Math.random() * 3)), at));
  for (let i = 0; i < 5; i++) safe(() => ev.dimension.spawnEntity('minecraft:xp_orb', at));
  particle(ev.dimension, 'bc:shard_burst', at, { color: rgb('c070ff'), scale: 1 });
  sound(ev.dimension, 'random.glass', at, 1, 0.7);
  safe(() => ev.player.onScreenDisplay.setActionBar('§5The Mana Spawner shatters!'));
  emit('spawner', ev.player);
}, 'spawnerBreak'));

// ------------------------------------------------------------------------------- residents and masters
/** @type {((dim: any, loc: any, kind: string, opts?: any) => any) | undefined} wanderers.js lets landmarks house wanderers */
let residentMaker;
export function setResidentMaker(fn) {
  residentMaker = fn;
}
const dist3 = (a, b) => Math.hypot(a.x - b[0], a.y - b[1], a.z - b[2]);
const isNight = () => {
  const t = safe(() => world.getTimeOfDay()) ?? 6000;
  return t > 13000 && t < 23000;
};

function spawnMaster(dim, rec, type, at, opts = {}) {
  const e = safe(() => dim.spawnEntity(type, { x: at[0] + 0.5, y: at[1] + (opts.up ?? 0), z: at[2] + 0.5 }));
  if (!e) return undefined;
  rec.boss = e.id;
  safe(() => e.setDynamicProperty('bc:landmark', rec.id));
  persist();
  return e;
}

/** A wyvern on its roost: asleep on the hoard until someone comes too close. */
export function wakeWyvern(e, p) {
  if (!alive(e) || safe(() => e.getProperty('bc:asleep')) !== true) return;
  safe(() => e.triggerEvent('bc:wake'));
  anim(e, 'animation.bc.wyvern.roar');
  sound(e.dimension, 'mob.enderdragon.growl', e.location, 3, 0.8);
  const w = W.wyverns[e.typeId.replace('bc:', '')];
  for (const q of e.dimension.getPlayers({ location: e.location, maxDistance: 64 })) title(q, `§l${w?.name ?? 'Mana Wyvern'}`, '§7You woke it. It is not pleased.', 60);
  if (p) emit('wyvern_woken', p);
}

function approach(p, rec) {
  const dim = p.dimension;
  const d2 = Math.hypot(rec.x - p.location.x, rec.z - p.location.z);
  if (d2 < FOUND_R && !rec.found.includes(p.id)) {
    rec.found.push(p.id);
    persist();
    const reg = regions()[rec.region];
    safe(() => p.onScreenDisplay.setActionBar(`§6Landmark found: §f${nameOf(rec.kind)}${reg ? ` §7- ${reg.name}` : ''}`));
    sound(dim, 'bc.chord', p.location, 0.7, 1.4);
    emit('landmark', p, rec);
  }
  // its guards wake as you come near
  if (rec.spawns.length) {
    const keep = [];
    for (const s of rec.spawns) {
      if (dist3(p.location, s) > 30) {
        keep.push(s);
        continue;
      }
      const what = s[3];
      if (what.startsWith('chance:')) {
        const [, pr, ...rest] = what.split(':');
        if (Math.random() < Number(pr)) safe(() => dim.spawnEntity(rest.join(':'), { x: s[0], y: s[1], z: s[2] }));
      } else safe(() => dim.spawnEntity(what, { x: s[0], y: s[1], z: s[2] }));
    }
    if (keep.length !== rec.spawns.length) {
      rec.spawns = keep;
      persist();
    }
  }
  if (rec.cleared) return;
  const boss = rec.boss ? world.getEntity(rec.boss) : undefined;
  const mark = rec.marks.boss?.[0];
  if (rec.kind === 'spire' && mark && !boss && dist3(p.location, mark) < 11) {
    const e = spawnMaster(dim, rec, 'bc:spire_warden', mark, { up: 0.2 });
    if (e) for (const q of dim.getPlayers({ location: p.location, maxDistance: 32 })) title(q, '§b§lTHE SPIRE WARDEN', '§7The guardian of the old kingdom\'s magic', 70);
  } else if (rec.kind === 'roost' && mark && !boss && d2 < 52) {
    const e = spawnMaster(dim, rec, `bc:${rec.sub || 'storm_wyvern'}`, mark, { up: 0.5 });
    if (e) safe(() => e.triggerEvent('bc:sleep'));
  } else if (rec.kind === 'roost' && boss && mark && dist3(p.location, mark) < 13) {
    wakeWyvern(boss, p);
  } else if (W.landmarks[rec.kind]?.master === 'commander' && mark && !boss && dist3(p.location, mark) < 12) {
    // v1.2.0: a kingdom fort's commander
    const K = DATA.kingdoms[W.landmarks[rec.kind].kingdom];
    const e = spawnMaster(dim, rec, `bc:${K.soldier}`, mark, { up: 0.2 });
    if (e) {
      makeElite(e, undefined, 'infernal');
      safe(() => (e.nameTag = `${K.mc}§l${K.commander}§r ${String(e.nameTag).replace(/^[^(]*/, '§7')}`));
      for (const q of dim.getPlayers({ location: p.location, maxDistance: 32 })) title(q, `${K.mc}§l${K.commander.toUpperCase()}`, `§7The ${K.name} holds this fort`, 60);
    }
  } else if (rec.kind === 'underworld_breach' && mark && !boss && dist3(p.location, mark) < 16) {
    // v1.3.0: the Crowned Vessel stands in the rift
    const e = spawnMaster(dim, rec, 'bc:crowned_vessel', mark, { up: 0.2 });
    if (e) {
      particle(dim, 'bc:magic_circle_dark', { x: mark[0] + 0.5, y: mark[1] + 0.1, z: mark[2] + 0.5 }, { size: 5, life: 1.5, color: rgb('ff2a4a') });
      for (const q of dim.getPlayers({ location: p.location, maxDistance: 40 })) title(q, '§4§lTHE CROWNED VESSEL', '§7It has been waiting for you', 70);
    }
  } else if (rec.kind === 'catacombs' && mark && !boss && dist3(p.location, mark) < 14) {
    const e = spawnMaster(dim, rec, 'bc:dungeon_golem', mark, { up: 0.2 });
    if (e) title(p, '§6§lTHE GUARDIAN WAKES', '§7The catacombs\' heart will not let you leave with its gold', 60);
  }
  // the Hollow rise from graves at night
  const graves = rec.marks.grave ?? [];
  const day = safe(() => world.getDay()) ?? 0;
  if (graves.length && isNight() && rec.night !== day && d2 < 34 && (rec.kind !== 'hamlet' || rec.sub === 'hollow')) {
    rec.night = day;
    persist();
    for (const gpos of graves.slice(0, 2 + Math.floor(rec.stars / 2))) {
      particle(dim, 'bc:magic_circle_dark', { x: gpos[0] + 0.5, y: gpos[1] + 0.05, z: gpos[2] + 0.5 }, { size: 1.6, life: 1.2, color: rgb('7ad0ff') });
      system.runTimeout(() => safe(() => dim.spawnEntity('bc:hollow_knight', { x: gpos[0] + 0.5, y: gpos[1], z: gpos[2] + 0.5 })), 20);
    }
    safe(() => p.onScreenDisplay.setActionBar('§8The ground stirs... the Hollow are rising!'));
    sound(dim, 'mob.zombie.unfect', p.location, 1, 0.6);
  }
  // a Lost Waygate wakes at a touch
  const gate = rec.marks.gate?.[0];
  if (gate && !rec.done.includes('gate') && dist3(p.location, gate) < 6) {
    rec.done.push('gate');
    persist();
    const reg = regions()[rec.region];
    addGate(p, { x: gate[0], y: gate[1], z: gate[2] }, `Waygate of ${(reg?.base ?? 'the Wilds')}`.slice(0, 24));
    title(p, '§b§lA LOST WAYGATE', '§7It hums awake and joins your network', 60);
    emit('lost_waygate', p);
  }
  // residents: a hedge witch (or something worse), a hermit in a ruined hamlet, a captive in the catacombs
  const home = rec.marks.witch?.[0] ?? rec.marks.priestess?.[0] ?? (rec.kind === 'hamlet' && rec.sub === 'hermit' ? rec.marks.bed?.[0] : undefined);
  if (home && !rec.resident && d2 < 26) {
    if (rec.kind === 'heart_sanctum') {
      const e = residentMaker?.(dim, { x: home[0] + 0.5, y: home[1], z: home[2] + 0.5 }, 'priestess', { stay: true });
      rec.resident = e?.id ?? 'none';
    } else if (rec.kind === 'witch_hut' && Math.random() < 0.4) {
      const e = safe(() => dim.spawnEntity('bc:rogue_mage', { x: home[0] + 0.5, y: home[1], z: home[2] + 0.5 }));
      if (e) {
        makeElite(e, undefined, 'champion');
        safe(() => (e.nameTag = '§5Cursed Hedge Witch'));
        for (let i = 0; i < 2; i++) safe(() => dim.spawnEntity('bc:imp', { x: home[0] + rand(-3, 3), y: home[1] + 1, z: home[2] + rand(-3, 3) }));
        rec.resident = e.id;
      }
    } else {
      const e = residentMaker?.(dim, { x: home[0] + 0.5, y: home[1], z: home[2] + 0.5 }, 'hermit', { title: rec.kind === 'witch_hut' ? 'Hedge Witch' : 'Hermit', stay: true });
      rec.resident = e?.id ?? 'none';
    }
    persist();
  }
  const cap = rec.marks.captive?.[0];
  if (cap && !rec.done.includes('captive')) {
    if (!rec.resident && dist3(p.location, cap) < 24) {
      const k = safe(() => dim.spawnEntity('bc:magic_knight', { x: cap[0] + 0.5, y: cap[1], z: cap[2] + 0.5 }));
      if (k) {
        setupKnight(k, { level: 2 + Math.floor(Math.random() * 4), randomRobe: true });
        rec.resident = k.id;
        persist();
      }
    } else if (rec.resident && dist3(p.location, cap) < 3.5) {
      const k = world.getEntity(rec.resident);
      const guards = safe(() => dim.getEntities({ location: p.location, maxDistance: 14, families: ['bc_bandit'] }).length) ?? 0;
      if (k && alive(k) && guards === 0) {
        rec.done.push('captive');
        persist();
        if (joinParty(k, p, 120)) safe(() => p.sendMessage('§bThe captive knight§f: You came for me? ...Then my grimoire is yours.'));
        else safe(() => p.sendMessage('§bThe captive knight§f: Thank you. I will find my own way home.'));
        emit('rescue', p);
      }
    }
  }
}

system.runInterval(() => {
  const all = Object.values(landmarks());
  if (!all.length) return;
  for (const p of world.getAllPlayers()) safe(() => {
    for (const rec of all) {
      if (rec.state !== 'built' || rec.dim !== p.dimension.id) continue;
      if (Math.abs(rec.x - p.location.x) > 70 || Math.abs(rec.z - p.location.z) > 70) continue;
      approach(p, rec);
    }
  }, 'landmarkApproach');
}, 20);

// the master falls: the landmark is cleared
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const e = ev.deadEntity;
  const id = safe(() => e.getDynamicProperty('bc:landmark'));
  if (typeof id !== 'string') return;
  const rec = landmarks()[id];
  if (!rec || rec.boss !== e.id) return;
  rec.cleared = true;
  persist();
  const dim = e.dimension;
  const players = dim.getPlayers({ location: e.location, maxDistance: 56 });
  if (rec.kind === 'spire') {
    const m = rec.marks.reward?.[0];
    if (m) {
      const b = safe(() => dim.getBlock({ x: m[0], y: m[1], z: m[2] }));
      if (b) {
        safe(() => b.setPermutation(BlockPermutation.resolve('minecraft:chest')));
        system.run(() => safe(() => fillChest(b, 'spire_top', rec.stars)));
        rec.chests.push([m[0], m[1], m[2], 'spire_top']);
      }
    }
    for (const p of players) {
      title(p, '§b§lTHE SPIRE IS YOURS', '§7Its treasure lies open on the roof', 70);
      emit('warden', p);
    }
  }
  if (rec.kind === 'roost') for (const p of players) emit('wyvern', p);
  if (W.landmarks[rec.kind]?.master === 'commander') for (const p of players) emit('commander', p, rec);
  for (const p of players) emit('landmark_clear', p, rec);
}, 'landmarkMaster'));

// ------------------------------------------------------------------------------- chests: mimics, looting, ambushes
const posIn = (list, l) => list.findIndex((c) => c[0] === l.x && c[1] === l.y && c[2] === l.z);
function recOfChest(l) {
  for (const rec of Object.values(landmarks())) {
    if (Math.abs(rec.x - l.x) > 80 || Math.abs(rec.z - l.z) > 80) continue;
    if (posIn(rec.chests, l) >= 0 || posIn(rec.mimics, l) >= 0) return rec;
  }
  return undefined;
}
/** Turn a mimic chest into a Mimic. */
export function springMimic(dim, rec, l, p) {
  const k = posIn(rec.mimics, l);
  if (k < 0) return undefined;
  rec.mimics.splice(k, 1);
  const table = rec.chests[posIn(rec.chests, l)]?.[3] ?? 'cata_room';
  persist();
  const b = safe(() => dim.getBlock(l));
  if (b) {
    safe(() => b.getComponent('minecraft:inventory')?.container?.clearAll());
    safe(() => b.setPermutation(BlockPermutation.resolve('minecraft:air')));
  }
  const m = safe(() => dim.spawnEntity('bc:mimic', { x: l.x + 0.5, y: l.y, z: l.z + 0.5 }));
  if (m) safe(() => m.setDynamicProperty('bc:mimic_loot', `${table}|${rec.stars}`));
  sound(dim, 'random.chestclosed', l, 1.2, 0.5);
  particle(dim, 'bc:smoke_burst', { x: l.x + 0.5, y: l.y + 0.5, z: l.z + 0.5 }, { scale: 0.6 });
  if (p) safe(() => p.onScreenDisplay.setActionBar(W.encounters.mimic.msg));
  return m;
}
world.beforeEvents.playerInteractWithBlock.subscribe((ev) => {
  if (ev.block.typeId !== 'minecraft:chest') return;
  const l = { ...ev.block.location };
  const rec = recOfChest(l);
  if (!rec || posIn(rec.mimics, l) < 0) return;
  ev.cancel = true;
  const p = ev.player;
  const dim = ev.block.dimension;
  system.run(() => safe(() => springMimic(dim, rec, l, p), 'mimic'));
});
world.afterEvents.playerInteractWithBlock.subscribe((ev) => safe(() => {
  if (/** @type {any} */ (ev).cancel || ev.block.typeId !== 'minecraft:chest') return;
  const l = ev.block.location;
  const rec = recOfChest(l);
  if (!rec) return;
  const p = ev.player;
  if (rec.kind === 'roost' && rec.boss) wakeWyvern(world.getEntity(rec.boss), p);
  if (rec.looted.includes(p.id)) return;
  rec.looted.push(p.id);
  persist();
  emit('landmark_loot', p, rec);
  if (rec.kind === 'caravan' && !rec.done.includes('ambush') && Math.random() < 0.5) {
    rec.done.push('ambush');
    const back = V.flat(p.getViewDirection());
    for (let i = 0; i < 3 + Math.floor(rec.stars / 2); i++) {
      const at = V.add(p.location, { x: -back.x * 12 + rand(-4, 4), y: 0.5, z: -back.z * 12 + rand(-4, 4) });
      safe(() => p.dimension.spawnEntity(i === 0 ? 'bc:bandit_archer' : 'bc:bandit', at));
    }
    title(p, '§c§lAMBUSH!', '§7The caravan was bait', 40);
  }
}, 'landmarkLoot'));

// the Mimic's belly holds the chest it pretended to be
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const e = ev.deadEntity;
  if (e.typeId !== 'bc:mimic') return;
  const v = safe(() => e.getDynamicProperty('bc:mimic_loot'));
  const [table, st] = typeof v === 'string' ? v.split('|') : ['cata_room', '1'];
  for (const it of chestItems(table, Number(st) || 1)) safe(() => e.dimension.spawnItem(it, e.location));
  const k = ev.damageSource.damagingEntity;
  if (k instanceof Player) emit('mimic', k);
}, 'mimicDie'));

// ------------------------------------------------------------------------------- Mana Obelisks: a prayer, and an answer
/** @type {Map<string, {power: number, regen: number, luck: number, until: number}>} */
const boons = new Map();
addMods((p) => {
  const b = boons.get(p.id);
  if (!b || b.until < system.currentTick) return undefined;
  return { power: b.power, regen: b.regen, luck: b.luck };
});
const BOONS = ['ley', 'font', 'fortune', 'vigor', 'swift', 'revelation'];
const CURSES = ['hollow', 'drain', 'hex', 'imps'];
/** Pray at an obelisk core. Returns what happened ('' when this player already prayed here). */
export function pray(p, loc, forced = '') {
  const rec = Object.values(landmarks()).find((r) => Object.values(r.marks).some((list) => list.some((m) => Math.abs(m[0] - loc.x) <= 1 && Math.abs(m[1] - loc.y) <= 1 && Math.abs(m[2] - loc.z) <= 1)));
  const key = rec ? rec.id : `${loc.x},${loc.y},${loc.z}`;
  if (rec?.prayed.includes(p.id)) {
    safe(() => p.onScreenDisplay.setActionBar('§7The obelisk is silent. It has answered you once already.'));
    return '';
  }
  if (rec) {
    rec.prayed.push(p.id);
    persist();
  }
  const stars = rec?.stars ?? 1;
  const curse = forced ? CURSES.includes(forced) : Math.random() < 0.22 + 0.04 * stars;
  const what = forced || (curse ? pick(CURSES) : pick(BOONS));
  const dim = p.dimension;
  const at = V.add(p.location, { x: 0, y: 1, z: 0 });
  const until = system.currentTick + 20 * 600;
  void key;
  if (!curse) {
    particle(dim, 'bc:pillar', p.location, { color: rgb('60e0ff'), scale: 1.2 });
    sound(dim, 'bc.chord', p.location, 1, 1.3);
  } else {
    particle(dim, 'bc:burst_dark', at, { scale: 1.2, color: rgb('2a0a30') });
    sound(dim, 'bc.devil.roar', p.location, 0.8, 1.4);
  }
  const msg = {
    ley: '§bBlessing of the Ley: §7+20% spell power for 10 minutes.',
    font: '§bMana Font: §7your mana fills, and flows 50% faster for 10 minutes.',
    fortune: '§6Fortune: §7a relic falls from the obelisk\'s heart.',
    vigor: '§aVigor: §7two extra hearts and fast healing.',
    swift: '§aWings of Wind: §7Speed and Jump Boost for 10 minutes.',
    revelation: '§eRevelation: §7the obelisk shows you hidden places.',
    hollow: '§8Curse: the Hollow Rise! §7Fallen knights claw out of the ground.',
    drain: '§5Curse: Mana Drain. §7Your mana bleeds away.',
    hex: '§5Curse: Hex of Misfortune. §7Your luck sours for 10 minutes.',
    imps: '§4Curse: Imps! §7The obelisk was a door, and something came through.',
  }[what];
  safe(() => p.sendMessage(`§3The obelisk answers... ${msg}`));
  title(p, curse ? '§5§lCURSED' : '§b§lBLESSED', '', 30);
  if (what === 'ley') boons.set(p.id, { power: 1.2, regen: 1, luck: 0, until });
  else if (what === 'font') {
    addMana(p, maxMana(p));
    boons.set(p.id, { power: 1, regen: 1.5, luck: 0, until });
  } else if (what === 'fortune') safe(() => dim.spawnItem(makeRelic(stars + 1, { min: 'uncommon' }), at));
  else if (what === 'vigor') {
    safe(() => p.addEffect('health_boost', 20 * 600, { amplifier: 0, showParticles: false }));
    safe(() => p.addEffect('regeneration', 20 * 20, { amplifier: 1 }));
  } else if (what === 'swift') {
    safe(() => p.addEffect('speed', 20 * 600, { amplifier: 0, showParticles: false }));
    safe(() => p.addEffect('jump_boost', 20 * 600, { amplifier: 0, showParticles: false }));
  } else if (what === 'revelation') {
    const near = slotsNear(p.location.x, p.location.z, 1).filter((s) => !s.rec?.found.includes(p.id) && s.rec?.state !== 'lost')
      .sort((a, b) => Math.hypot(a.x - p.location.x, a.z - p.location.z) - Math.hypot(b.x - p.location.x, b.z - p.location.z)).slice(0, 3);
    for (const s of near) safe(() => p.sendMessage(`§e  ${nameOf(s.kind)} §7- ${compassWord(s.x - p.location.x, s.z - p.location.z)}, ${Math.round(Math.hypot(s.x - p.location.x, s.z - p.location.z))} blocks`));
  } else if (what === 'hollow') {
    for (let i = 0; i < 2 + Math.floor(stars / 2); i++) safe(() => dim.spawnEntity('bc:hollow_knight', V.add(p.location, { x: rand(-6, 6), y: 0.5, z: rand(-6, 6) })));
  } else if (what === 'drain') {
    const s = state(p);
    s.mana = 0;
    s.dirty = true;
    safe(() => p.addEffect('weakness', 20 * 60, { amplifier: 0 }));
  } else if (what === 'hex') boons.set(p.id, { power: 1, regen: 1, luck: -30, until });
  else if (what === 'imps') for (let i = 0; i < 4; i++) safe(() => dim.spawnEntity('bc:imp', V.add(p.location, { x: rand(-5, 5), y: 1, z: rand(-5, 5) })));
  emit('obelisk', p, what);
  return what;
}
system.beforeEvents.startup.subscribe((ev) => {
  ev.blockComponentRegistry.registerCustomComponent('bc:obelisk', {
    onPlayerInteract(e) {
      const p = e.player;
      if (!(p instanceof Player)) return;
      const loc = { ...e.block.location };
      system.run(() => safe(() => pray(p, loc), 'obelisk'));
    },
  });
});

// ------------------------------------------------------------------------------- fairy rings: the sprites' bargain
/** Offer an item to the sprites of a fairy ring. Returns the gift (or undefined, when the sprites just keep it). */
export function bargain(p, offered, rec) {
  const day = safe(() => world.getDay()) ?? 0;
  const k = `bc:fae_${day}`;
  const n = Number(safe(() => p.getDynamicProperty(k)) ?? 0);
  if (n >= 3) {
    safe(() => p.sendMessage('§aThe sprites giggle. §7"Enough for today, big one!" §8(they keep it)'));
    return undefined;
  }
  safe(() => p.setDynamicProperty(k, n + 1));
  const revel = !!safe(() => world.getDynamicProperty('bc:omen'))?.toString().includes('fae_revel');
  const stars = (rec?.stars ?? 1) + (revel ? 2 : 0);
  const r = Math.random();
  let gift;
  if (r < (revel ? 0.65 : 0.5)) gift = makeRelic(stars, { luck: mods(p).luck });
  else if (r < 0.7) gift = new ItemStack('bc:sprite_dust', 2 + Math.floor(Math.random() * 3));
  else if (r < 0.85) gift = new ItemStack('bc:mana_potion', 2);
  else if (r < 0.95) gift = undefined;
  else gift = new ItemStack('bc:star_fragment', 1);
  const what = String(safe(() => offered.nameTag) || offered.typeId.replace(/^.*:/, '').replace(/_/g, ' '));
  const dim = p.dimension;
  const at = rec?.marks.heart?.[0] ? { x: rec.marks.heart[0][0] + 0.5, y: rec.marks.heart[0][1] + 1, z: rec.marks.heart[0][2] + 0.5 } : p.location;
  particle(dim, 'bc:burst_spark', at, { color: rgb('a8ffd0'), scale: 1.2 });
  sound(dim, 'random.orb', at, 1, 1.8);
  if (gift) {
    safe(() => dim.spawnItem(gift, at));
    const gname = String(safe(() => gift.nameTag) || gift.typeId.replace(/^.*:/, '').replace(/_/g, ' '));
    safe(() => p.sendMessage(`§aThe sprites take your §f${what}§a and leave §f${gname.replace(/§./g, '')}§a.`));
  } else safe(() => p.sendMessage(`§aThe sprites take your §f${what}§a... and giggle. That's all.`));
  emit('bargain', p);
  return gift;
}
system.runInterval(() => {
  for (const rec of Object.values(landmarks())) {
    if (rec.kind !== 'fairy_ring' || rec.state !== 'built') continue;
    const h = rec.marks.heart?.[0];
    if (!h) continue;
    const dim = safe(() => world.getDimension(rec.dim));
    if (!dim) continue;
    const at = { x: h[0] + 0.5, y: h[1], z: h[2] + 0.5 };
    const p = dim.getPlayers({ location: at, maxDistance: 8 })[0];
    if (!p) continue;
    for (const it of safe(() => dim.getEntities({ location: at, maxDistance: 4.5, type: 'minecraft:item' })) ?? []) {
      const stack = safe(() => it.getComponent('minecraft:item')?.itemStack);
      if (!stack) continue;
      safe(() => it.remove());
      bargain(p, stack, rec);
    }
  }
}, 40);

// ------------------------------------------------------------------------------- cheats
// /scriptevent bc:landmark [kind] - raise one about 40 blocks behind you
system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (ev.id !== 'bc:landmark') return;
  const p = ev.sourceEntity instanceof Player ? ev.sourceEntity : world.getAllPlayers()[0];
  if (!p) return;
  const want = ev.message.trim();
  const kind = W.landmarks[want] || want === 'starfall' ? want : pick(Object.keys(W.landmarks));
  const back = V.flat(p.getViewDirection());
  const x = Math.floor(p.location.x - back.x * 40);
  const z = Math.floor(p.location.z - back.z * 40);
  const { rx, rz } = cellOf(x, z);
  const res = raise(p.dimension, { id: `cheat#${Date.now() % 1000000}`, x, z, kind, region: keyOf(rx, rz) }, { log: true });
  safe(() => p.sendMessage(res === 'built' ? `§6A ${nameOf(kind)} rises behind you.` : '§7No room for that here - try flatter ground.'));
});

export { regionAt, starText };
