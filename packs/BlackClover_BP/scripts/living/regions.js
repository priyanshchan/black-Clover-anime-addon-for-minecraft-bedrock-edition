// Regions (v1.1.0): the world is cut into 320-block regions, and every one is a place of its own - a name made from
// what its land is like ("Kelmoor Fen", "the Whispering Pines"), a realm by its distance from the world spawn (the Noble
// Realm, the Common Realm, the Forsaken Realm, then the Marches toward the neighbouring kingdoms), danger stars, one to
// three traits (Mana-Rich, Haunted, Wyvern Territory, Fae Wilds...) and a line of lore. Everything is rolled from the
// world's seed, so the map is the same every time you come back - and different in every new world.
//
// Walking into a region you have never seen shows its name, realm, danger and traits; the Handbook's Atlas keeps them.
// Each region also gets its landmarks: where they lie and what they are is decided the first time anyone enters it.
import { Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { emit } from '../core/bus.js';
import { particle, rgb, sound, title } from '../core/fx.js';
import { addMods } from '../core/mods.js';
import { addXp } from '../core/progress.js';
import { hash, pickR, pickW, rng, worldSeed } from '../core/seed.js';
import { loadBig, saveBig } from '../core/store.js';
import { V, safe, yawOf } from '../core/util.js';

const W = DATA.world;
export const SIZE = W.regionSize;
const KEY = 'bc:regions';
const MAX = 400;

/** @typedef {{x: number, z: number, kind: string}} Slot */
/** @typedef {{k: string, rx: number, rz: number, name: string, base: string, land: string, realm: string, realmName: string, mc: string,
 *   stars: number, traits: string[], lore: string, slots: Slot[], by: string[], day: number, kingdom?: string}} Region */

// ------------------------------------------------------------------------------- where things are
export function cellOf(x, z) {
  return { rx: Math.floor(x / SIZE), rz: Math.floor(z / SIZE) };
}
export function keyOf(rx, rz) {
  return `${rx},${rz}`;
}
export function centerOf(rx, rz) {
  return { x: rx * SIZE + SIZE / 2, z: rz * SIZE + SIZE / 2 };
}
function spawnPoint() {
  const s = safe(() => world.getDefaultSpawnLocation());
  return s && Number.isFinite(s.x) && Math.abs(s.x) < 3e7 ? { x: s.x, z: s.z } : { x: 0, z: 0 };
}
export function compassWord(dx, dz) {
  const yaw = yawOf({ x: dx, y: 0, z: dz });
  const names = ['south', 'south-west', 'west', 'north-west', 'north', 'north-east', 'east', 'south-east'];
  return names[((Math.round(yaw / 45) % 8) + 8) % 8];
}

/** The realm a point lies in (by its distance from the world spawn). */
export function realmAt(x, z) {
  const sp = spawnPoint();
  const d = Math.hypot(x - sp.x, z - sp.z);
  const realm = W.realms.find((r) => d <= r.upTo) ?? W.realms[W.realms.length - 1];
  let name = realm.name;
  let kingdom = '';
  if (realm.id === 'marches') {
    const dir = compassWord(x - sp.x, z - sp.z).split('-')[0];
    name = W.marches[dir] ?? realm.name;
    kingdom = DATA.marchKingdom[dir] ?? '';   // v1.2.0: the Diamond, Spade and Heart Marches belong to their kingdoms
  }
  return { ...realm, name, kingdom, dist: d };
}

// ------------------------------------------------------------------------------- what the land is made of
const LEAVES = {
  'minecraft:jungle_leaves': 'jungle', 'minecraft:spruce_leaves': 'taiga', 'minecraft:dark_oak_leaves': 'darkwood', 'minecraft:pale_oak_leaves': 'darkwood',
  'minecraft:cherry_leaves': 'blossom', 'minecraft:mangrove_leaves': 'swamp', 'minecraft:acacia_leaves': 'savanna', 'minecraft:oak_leaves': 'forest',
  'minecraft:birch_leaves': 'forest', 'minecraft:azalea_leaves': 'forest', 'minecraft:azalea_leaves_flowered': 'forest',
};
const GROUND = {
  'minecraft:sand': 'desert', 'minecraft:sandstone': 'desert', 'minecraft:red_sand': 'badlands', 'minecraft:red_sandstone': 'badlands',
  'minecraft:terracotta': 'badlands', 'minecraft:hardened_clay': 'badlands', 'minecraft:snow': 'frozen', 'minecraft:snow_layer': 'frozen',
  'minecraft:powder_snow': 'frozen', 'minecraft:ice': 'frozen', 'minecraft:packed_ice': 'frozen', 'minecraft:blue_ice': 'frozen',
  'minecraft:mud': 'swamp', 'minecraft:mangrove_roots': 'swamp', 'minecraft:muddy_mangrove_roots': 'swamp', 'minecraft:clay': 'swamp',
  'minecraft:water': 'water', 'minecraft:flowing_water': 'water', 'minecraft:mycelium': 'mushroom', 'minecraft:podzol': 'taiga',
  'minecraft:coarse_dirt': 'savanna', 'minecraft:grass_block': 'plains', 'minecraft:dirt': 'plains', 'minecraft:grass_path': 'plains', 'minecraft:moss_block': 'forest',
};
const PASS = (id) => id.includes('leaves') || id.includes('log') || id.endsWith('_stem') || id.includes('vine')
  || id.includes('grass') && id !== 'minecraft:grass_block' && id !== 'minecraft:grass_path'
  || id.includes('fern') || id.includes('flower') || id.includes('bush') || id.includes('mushroom') || id === 'minecraft:snow_layer' || id.includes('sapling')
  || id.includes('poppy') || id.includes('dandelion') || id.includes('tulip') || id.includes('daisy') || id.includes('bluet') || id.includes('allium')
  || id.includes('orchid') || id.includes('cornflower') || id.includes('lily') || id.includes('petals') || id.includes('roots') && !id.includes('mangrove')
  || id.includes('bamboo') || id.includes('kelp') || id.includes('seagrass') || id === 'minecraft:air' || id.includes('moss_carpet') || id.includes('cactus');

/**
 * The ground under a column: its height and land class, skipping trees, plants and snow layers.
 * @returns {{y: number, id: string, land: string, water: boolean} | undefined}
 */
export function groundAt(dim, x, z) {
  const top = safe(() => dim.getTopmostBlock({ x, z }));
  if (!top) return undefined;
  let y = top.location.y;
  let canopy = '';
  for (let i = 0; i < 40; i++) {
    const b = safe(() => dim.getBlock({ x, y, z }));
    if (!b) return undefined;
    const id = b.typeId;
    if (!canopy && LEAVES[id]) canopy = LEAVES[id];
    if (id === 'minecraft:snow_layer' && !canopy) canopy = 'frozen';
    if (id === 'minecraft:water' || id === 'minecraft:flowing_water') return { y, id, land: 'water', water: true };
    if (!PASS(id)) {
      let land = GROUND[id] ?? (id.includes('terracotta') ? 'badlands' : '');
      if (!land) land = y > 100 ? 'mountains' : 'hills';
      if (canopy && (land === 'plains' || land === 'hills' || land === 'forest')) land = canopy;
      if (canopy === 'frozen' && land !== 'water') land = 'frozen';
      if (y > 112 && land !== 'frozen' && land !== 'water') land = 'mountains';
      return { y, id, land, water: false };
    }
    y--;
  }
  return undefined;
}

/** The most common land class around a point. */
export function landAround(dim, x, z, r = 40) {
  /** @type {Record<string, number>} */
  const n = {};
  for (const [dx, dz] of [[0, 0], [r, 0], [-r, 0], [0, r], [0, -r], [r * 0.7, r * 0.7], [-r * 0.7, -r * 0.7]]) {
    const g = groundAt(dim, Math.floor(x + dx), Math.floor(z + dz));
    if (g) n[g.land] = (n[g.land] ?? 0) + (dx === 0 && dz === 0 ? 2 : 1);
  }
  const best = Object.entries(n).sort((a, b) => b[1] - a[1])[0];
  return best ? best[0] : 'plains';
}

// ------------------------------------------------------------------------------- rolling a region
/** The parts of a region that only depend on the seed (its base name, realm, stars, where its landmarks lie). */
export function seededRegion(rx, rz) {
  const r = rng(hash(worldSeed(), 'region', rx, rz));
  const c = centerOf(rx, rz);
  const realm = realmAt(c.x, c.z);
  const [s1, s2, s3] = W.syllables;
  const base = `${pickR(r, s1)}${pickR(r, s2)}${pickR(r, s3)}`;
  const jitter = r() < 0.25 ? -1 : r() < 0.67 ? 0 : 1;
  const stars = Math.max(1, Math.min(5, realm.stars + jitter + (realm.id === 'marches' && r() < 0.4 ? 1 : 0)));
  return { rx, rz, base, realm, stars, r };
}

function rollTraits(r, land, realm) {
  const n = realm.traits + (realm.id === 'marches' && r() < 0.35 ? 1 : 0);
  /** @type {string[]} */
  const out = [];
  for (let i = 0; i < n; i++) {
    const entries = Object.entries(W.traits).filter(([k]) => !out.includes(k)).map(([k, t]) => {
      let w = t.land.length ? (t.land.includes(land) ? 3 : 0.4) : 1;
      if (k === 'sanctuary') w *= realm.id === 'noble' ? 2.5 : realm.id === 'common' ? 1 : 0;
      if (k === 'untamed') w *= realm.id === 'forsaken' || realm.id === 'marches' ? 1.5 : 0.2;
      if (k === 'devil_scarred' && realm.id === 'noble') w *= 0.3;
      if (out.includes('sanctuary') && ['haunted', 'untamed', 'devil_scarred', 'bandit_country'].includes(k)) w = 0;
      return [k, w];
    });
    const k = pickW(r, entries);
    if (k) out.push(k);
  }
  return out;
}

const UNIQUE = new Set(['spire', 'roost', 'catacombs', 'lost_waygate', 'diamond_fort', 'spade_citadel', 'heart_sanctum', 'underworld_breach']);
const BOOST = {
  ancient: { spire: 2, catacombs: 2, obelisk: 2, graveyard: 1.5 }, haunted: { graveyard: 2.5, battlefield: 2.5 }, wyvern_lands: { roost: 4 },
  fae_wilds: { fairy_ring: 4 }, bandit_country: { watchtower: 2.5, caravan: 2.5 }, treasure: { skeleton: 2.5, crater: 2 }, sanctuary: { hamlet: 2, obelisk: 2 },
  devil_scarred: { crater: 1.5, battlefield: 1.5, underworld_breach: 4 },
};
/** Can a landmark kind stand on this land? */
export function kindFits(kind, land) {
  const L = W.landmarks[kind];
  if (!L || land === 'water') return false;
  if (kind === 'roost') return Object.values(W.wyverns).some((w) => w.land.includes(land));
  return L.land === '*' || L.land.includes(land);
}
export function chooseKind(r, land, stars, traits, taken, kingdom = '') {
  const entries = Object.entries(W.landmarks).map(([k, L]) => {
    if (!kindFits(k, land) || stars < L.stars || (UNIQUE.has(k) && taken.includes(k))) return [k, 0];
    if ((L.kingdom ?? '') !== '' && L.kingdom !== kingdom) return [k, 0];   // v1.2.0: forts stand only in their own Marches
    let w = L.weight;
    for (const t of traits) w *= BOOST[t]?.[k] ?? 1;
    return [k, w];
  });
  return pickW(r, entries) ?? 'obelisk';
}

function rollSlots(seed, land, traits) {
  const { r, rx, rz, stars } = seed;
  const kingdom = seed.realm.kingdom ?? '';
  const sp = spawnPoint();
  const n = Math.min(8, W.landmarkBase + Math.round(stars * W.landmarkPerStar + r()) + (traits.includes('ancient') ? 2 : 0));
  /** @type {Slot[]} */
  const out = [];
  const taken = [];
  for (let tries = 0; tries < 60 && out.length < n; tries++) {
    const x = Math.floor(rx * SIZE + 28 + r() * (SIZE - 56));
    const z = Math.floor(rz * SIZE + 28 + r() * (SIZE - 56));
    if (Math.hypot(x - sp.x, z - sp.z) < 90) continue;
    if (out.some((s) => Math.hypot(s.x - x, s.z - z) < 72)) continue;
    const kind = chooseKind(r, land, stars, traits, taken, kingdom);
    taken.push(kind);
    out.push({ x, z, kind });
  }
  return out;
}

function nameFor(seed, land, r) {
  const forms = W.landforms[land] ?? W.landforms.plains;
  const form = pickR(r, forms);
  const x = r();
  if (x < 0.5) return `${seed.base} ${form}`;
  if (x < 0.75) return `the ${form} of ${seed.base}`;
  return `the ${pickR(r, W.adjectives)} ${form}`;
}

// ------------------------------------------------------------------------------- the atlas of discovered regions
/** @type {Record<string, Region> | undefined} */
let atlas;
let dirty = false;
export function regions() {
  if (!atlas) atlas = loadBig(KEY, {});
  return /** @type {Record<string, Region>} */ (atlas);
}
function persist() {
  dirty = true;
}
system.runInterval(() => {
  if (!dirty || !atlas) return;
  dirty = false;
  const keys = Object.keys(atlas);
  if (keys.length > MAX) {
    keys.sort((a, b) => (atlas?.[a].day ?? 0) - (atlas?.[b].day ?? 0));
    for (const k of keys.slice(0, keys.length - MAX)) delete atlas[k];
  }
  if (!saveBig(KEY, atlas)) {
    // too big to keep: forget the oldest quarter
    const ks = Object.keys(atlas).sort((a, b) => (atlas?.[a].day ?? 0) - (atlas?.[b].day ?? 0));
    for (const k of ks.slice(0, Math.ceil(ks.length / 4))) delete atlas[k];
    saveBig(KEY, atlas);
  }
}, 100);

/** The region record (rolling it now, if nobody has been here before - the land is read around `at`). @returns {Region} */
export function ensureRegion(dim, rx, rz, at) {
  const all = regions();
  const k = keyOf(rx, rz);
  if (all[k]) return all[k];
  const seed = seededRegion(rx, rz);
  const c = centerOf(rx, rz);
  const land = landAround(dim, at?.x ?? c.x, at?.z ?? c.z);
  const r = rng(hash(worldSeed(), 'region-land', rx, rz, land));
  const traits = rollTraits(r, land, seed.realm);
  const name = nameFor(seed, land, r);
  const loreList = W.lore[traits[0]] ?? ['{name} keeps its secrets.'];
  const lore = pickR(r, loreList).replace('{name}', name.replace(/^the /, 'the '));
  /** @type {Region} */
  const rec = { k, rx, rz, name, base: seed.base, land, realm: seed.realm.id, realmName: seed.realm.name, mc: seed.realm.mc, stars: seed.stars, traits, lore,
    kingdom: seed.realm.kingdom ?? '',
    slots: rollSlots(seed, land, traits), by: [], day: safe(() => world.getDay()) ?? 0 };
  all[k] = rec;
  persist();
  return rec;
}

/** The discovered region at a point, if any. @returns {Region | undefined} */
export function regionAt(x, z) {
  const { rx, rz } = cellOf(x, z);
  return regions()[keyOf(rx, rz)];
}
/** Danger stars at a point (rolled from the seed when the region is still unknown). */
export function starsAt(loc) {
  if (!loc) return 1;
  const r = regionAt(loc.x, loc.z);
  if (r) return r.stars;
  const { rx, rz } = cellOf(loc.x, loc.z);
  return seededRegion(rx, rz).stars;
}
export function traitsAt(loc) {
  return loc ? regionAt(loc.x, loc.z)?.traits ?? [] : [];
}
export function hasTrait(loc, t) {
  return traitsAt(loc).includes(t);
}
export function stars(n) {
  return `§e${'★'.repeat(n)}§8${'★'.repeat(Math.max(0, 5 - n))}`;
}
export function traitText(rec) {
  return rec.traits.map((t) => `${W.traits[t].mc}${W.traits[t].name}`).join('§7, ');
}
/** How a region is named in a sentence ("Kelmoor Fen", "the Whispering Pines"). */
export function regionName(rec) {
  return rec ? rec.name : 'the wilds';
}

// ------------------------------------------------------------------------------- walking into regions
/** @type {Map<string, string>} player id -> the region they stand in */
const where = new Map();
/** @type {Map<string, number>} player id -> tick of the last "entering" note */
const noteAt = new Map();

export function currentRegion(p) {
  return regionAt(p.location.x, p.location.z);
}

/** A player walks into a region (discovering it if it is new to them). */
export function enterRegion(p, rec) {
  const first = !rec.by.includes(p.id);
  if (first) {
    rec.by.push(p.id);
    persist();
    title(p, `§6${rec.name}`, `${rec.mc}${rec.realmName} §7· ${stars(rec.stars)}`, 70);
    safe(() => p.sendMessage(`§6Discovered: §f${rec.name} §7- ${rec.mc}${rec.realmName}§7, danger ${stars(rec.stars)}§7. ${traitText(rec)}`));
    safe(() => p.sendMessage(`§8§o${rec.lore}`));
    sound(p.dimension, 'bc.chord', p.location, 0.8, 1.2);
    particle(p.dimension, 'bc:level_up', p.location);
    addXp(p, W.findXp);
    emit('region', p, rec);
  } else {
    const t = system.currentTick;
    if (t - (noteAt.get(p.id) ?? -9999) > 20 * 20) {
      noteAt.set(p.id, t);
      safe(() => p.onScreenDisplay.setActionBar(`§7Entering §6${rec.name} §7${stars(rec.stars)}`));
    }
  }
}

system.runInterval(() => {
  for (const p of world.getAllPlayers()) safe(() => {
    if (p.dimension.id !== 'minecraft:overworld') return;
    const { rx, rz } = cellOf(p.location.x, p.location.z);
    const k = keyOf(rx, rz);
    if (where.get(p.id) === k) return;
    where.set(p.id, k);
    enterRegion(p, ensureRegion(p.dimension, rx, rz, p.location));
  }, 'regions');
}, 20);

// ------------------------------------------------------------------------------- what the land does to you
addMods((p) => {
  const t = traitsAt(p.location);
  if (!t.length) return undefined;
  return { regen: t.includes('mana_rich') ? 1.3 : 1, power: t.includes('ley_line') ? 1.1 : 1, wild: t.includes('wild_magic') };
});

// a little of each region's air: mana motes, ghost lights, ash, fae sparkles
const AIR = { mana_rich: ['bc:mana_aura', '60c8ff'], haunted: ['bc:will_spark', '7ad0ff'], devil_scarred: ['bc:smoke_burst', '3a1a14'],
  fae_wilds: ['bc:burst_spark', 'a8ffd0'], wild_magic: ['bc:burst_spark', 'ff70e0'], ley_line: ['bc:burst_spark', 'c08cff'] };
system.runInterval(() => {
  for (const p of world.getAllPlayers()) safe(() => {
    const night = safe(() => world.getTimeOfDay()) ?? 6000;
    for (const t of traitsAt(p.location)) {
      const a = AIR[t];
      if (!a || (t === 'haunted' && (night < 13000 || night > 23000))) continue;
      const at = V.add(p.location, { x: (Math.random() - 0.5) * 16, y: 1 + Math.random() * 3, z: (Math.random() - 0.5) * 16 });
      particle(p.dimension, a[0], at, { color: rgb(a[1]), scale: 0.4 });
    }
  }, 'regionAir');
}, 60);

// cheat: /scriptevent bc:region - where am I?
system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (ev.id !== 'bc:region') return;
  const p = ev.sourceEntity instanceof Player ? ev.sourceEntity : world.getAllPlayers()[0];
  if (!p) return;
  const rec = currentRegion(p);
  if (rec) safe(() => p.sendMessage(`§6${rec.name} §7(${rec.k}) ${rec.mc}${rec.realmName} ${stars(rec.stars)} §7${traitText(rec)} §8land: ${rec.land}, ${rec.slots.length} landmarks`));
});
