// The Royal Capital (v1.2.0): once per world, a walled town rises 150-230 blocks from the world spawn - its gate, a plaza
// with a fountain and a statue of light, the Magic Knight HQ (Mission Board, War Table, Squad Banner), a smithy with a
// Magic Forge, an inn, a market of shopkeepers (a cartographer, a peddler, an apothecary, a bard and the quartermaster
// of the war office), houses, Magic Knights on watch and a Mana Waygate. Inside its walls no ambushes come and no
// monsters spawn; the first time you walk in, it becomes your home (you wake there, unless you sleep elsewhere).
import { Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { LANDMARK_BP } from '../generated/landmarks.js';
import { emit } from '../core/bus.js';
import { sound, title } from '../core/fx.js';
import { rngFor } from '../core/seed.js';
import { V, safe, yawOf } from '../core/util.js';
import { setupKnight } from './knights.js';
import { buildBlueprint, levelAt } from './landmarks.js';
import { addGate } from './waygate.js';
import { compassWord, groundAt } from './regions.js';

const C = DATA.capital;
const KEY = 'bc:capital';
/** @type {((dim: any, loc: any, kind: string, opts?: any) => any) | undefined} */
let makeResident;
/** wanderers.js hands over how shopkeepers are made */
export function setCapitalResidentMaker(fn) {
  makeResident = fn;
}

/** @typedef {{x: number, y: number, z: number, dim: string, built: boolean, marks: Record<string, number[][]>, residents: Record<string, string>, guards: string[], gate: boolean}} Capital */
/** @returns {Capital | undefined} */
export function capital() {
  const v = safe(() => world.getDynamicProperty(KEY));
  try {
    return typeof v === 'string' ? JSON.parse(v) : undefined;
  } catch {
    return undefined;
  }
}
function save(c) {
  safe(() => world.setDynamicProperty(KEY, JSON.stringify(c)));
}
function spawnPoint() {
  const s = safe(() => world.getDefaultSpawnLocation());
  return s && Number.isFinite(s.x) && Math.abs(s.x) < 3e7 ? { x: s.x, z: s.z } : { x: 0, z: 0 };
}
/** Where the Capital is meant to stand (before it is built): candidate spots around the seeded direction. */
export function capitalSites() {
  const r = rngFor('capital');
  const sp = spawnPoint();
  const a0 = r() * Math.PI * 2;
  const [lo, hi] = C.distance;
  const out = [];
  for (let i = 0; i < 10; i++) {
    const a = a0 + (i % 5) * 0.55 * (i % 2 ? 1 : -1);
    const d = lo + ((hi - lo) * ((i * 37) % 10)) / 10;
    out.push({ x: Math.floor(sp.x + Math.cos(a) * d), z: Math.floor(sp.z + Math.sin(a) * d) });
  }
  return out;
}

/** Raise the Capital at the first good site (or at `at`). Returns the record, or undefined when no site is loaded yet. */
export function raiseCapital(dim, at = undefined) {
  if (capital()?.built) return capital();
  let site;
  if (at) {
    const g = groundAt(dim, Math.floor(at.x), Math.floor(at.z));
    if (g) site = { x: Math.floor(at.x), y: g.y, z: Math.floor(at.z) };
  } else {
    let best;
    for (const s of capitalSites()) {
      const g = levelAt(dim, s.x, s.z, 'capital');
      if (g) {
        site = { x: s.x, y: g.y, z: s.z };
        break;
      }
      const g0 = groundAt(dim, s.x, s.z);
      if (g0 && !g0.water && !best) best = { x: s.x, y: g0.y, z: s.z };
    }
    site = site ?? best;
  }
  if (!site) return undefined;
  /** @type {Capital} */
  const c = { ...site, dim: dim.id, built: true, marks: {}, residents: {}, guards: [], gate: false };
  save(c);
  buildBlueprint(dim, LANDMARK_BP.capital, site.x, site.y, site.z, 'minecraft:stone_bricks', (out) => {
    const cur = capital() ?? c;
    cur.marks = out.marks;
    save(cur);
  });
  return c;
}

/** Is a point inside the Capital's safe streets? */
export function inCapital(loc, r = C.safe) {
  const c = capital();
  return !!c && c.built && Math.hypot(loc.x - c.x, loc.z - c.z) <= r;
}

// raise it as an explorer comes near (out of sight where possible)
system.runInterval(() => {
  if (capital()?.built) return;
  for (const p of world.getAllPlayers()) safe(() => {
    if (p.dimension.id !== 'minecraft:overworld') return;
    for (const s of capitalSites()) {
      const d = Math.hypot(s.x - p.location.x, s.z - p.location.z);
      if (d > 120) continue;
      const rel = Math.abs(((yawOf({ x: s.x - p.location.x, y: 0, z: s.z - p.location.z }) - yawOf(p.getViewDirection()) + 540) % 360) - 180);
      if (d > 40 && d < 90 && rel < 60) continue;
      if (raiseCapital(p.dimension)) return;
    }
  }, 'capitalRaise');
}, 60);

// walking in: the title, a home, the gate, the people
system.runInterval(() => {
  const c = capital();
  if (!c?.built) return;
  for (const p of world.getAllPlayers()) safe(() => {
    if (p.dimension.id !== c.dim) return;
    const d = Math.hypot(p.location.x - c.x, p.location.z - c.z);
    if (d > C.radius + 8) return;
    if (safe(() => p.getDynamicProperty('bc:capital_seen')) !== true) {
      safe(() => p.setDynamicProperty('bc:capital_seen', true));
      title(p, '§6§lTHE ROYAL CAPITAL', '§7Heart of the Clover Kingdom', 80);
      sound(p.dimension, 'bc.fanfare', p.location, 1, 1);
      if (!safe(() => p.getSpawnPoint())) {
        safe(() => p.setSpawnPoint({ dimension: p.dimension, x: c.x + 0.5, y: c.y + 1, z: c.z + 8.5 }));
        safe(() => p.sendMessage('§6The Royal Capital is now your home. §7You will wake here (unless you sleep in a bed elsewhere).'));
      }
      emit('capital', p);
    }
    const dim = p.dimension;
    const gate = c.marks.gate?.[0];
    if (gate && !c.gate) {
      c.gate = true;
      addGate(p, { x: gate[0], y: gate[1], z: gate[2] }, 'The Royal Capital');
      save(c);
    }
    // shopkeepers and guards (brought back if lost)
    let changed = false;
    for (const [mark, list] of Object.entries(c.marks)) {
      if (!mark.startsWith('res_')) continue;
      const kind = mark.slice(4);
      const have = c.residents[kind] ? world.getEntity(c.residents[kind]) : undefined;
      if (have) continue;
      const m = list[0];
      const titles = { hermit: 'Apothecary', bard: 'Innkeeper', peddler: 'Market Trader', cartographer: 'Royal Cartographer', quartermaster: 'Quartermaster' };
      const e = makeResident?.(dim, { x: m[0] + 0.5, y: m[1], z: m[2] + 0.5 }, kind, { stay: true, title: titles[kind] });
      if (e) {
        c.residents[kind] = e.id;
        changed = true;
      }
    }
    const alive = c.guards.filter((id) => world.getEntity(id));
    if (alive.length < (c.marks.guard?.length ?? 0)) {
      for (const m of (c.marks.guard ?? []).slice(alive.length)) {
        const k = safe(() => dim.spawnEntity('bc:magic_knight', { x: m[0] + 0.5, y: m[1], z: m[2] + 0.5 }));
        if (!k) continue;
        setupKnight(k, { level: 4 + Math.floor(Math.random() * 4), randomRobe: true, prefix: '§a' });
        safe(() => k.setDynamicProperty('bc:capital_guard', true));
        alive.push(k.id);
      }
      c.guards = alive;
      changed = true;
    }
    if (changed) save(c);
  }, 'capitalVisit');
}, 40);

// no monsters inside the walls
world.afterEvents.entitySpawn.subscribe((ev) => safe(() => {
  const e = ev.entity;
  if (!safe(() => e.matches({ families: ['monster'] })) || safe(() => e.matches({ families: ['boss'] }))) return;
  if (typeof safe(() => e.getDynamicProperty('bc:owner')) === 'string') return;
  if (inCapital(e.location, C.radius + 4)) safe(() => e.remove());
}, 'capitalSafe'));

/** A line for the Atlas: where the Capital is. */
export function capitalLine(p) {
  const c = capital();
  if (c?.built) {
    const d = Math.round(Math.hypot(c.x - p.location.x, c.z - p.location.z));
    return `§6The Royal Capital §7- ${compassWord(c.x - p.location.x, c.z - p.location.z)}, ${d} blocks`;
  }
  const s = capitalSites()[0];
  return `§6The Royal Capital §7- somewhere ${compassWord(s.x - p.location.x, s.z - p.location.z)} of here, not yet found`;
}

// cheat: /scriptevent bc:capital [here]
system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (ev.id !== 'bc:capital') return;
  const p = ev.sourceEntity instanceof Player ? ev.sourceEntity : world.getAllPlayers()[0];
  if (!p) return;
  if (ev.message.trim() === 'here' && !capital()?.built) {
    const back = V.flat(p.getViewDirection());
    raiseCapital(p.dimension, { x: p.location.x - back.x * 40, z: p.location.z - back.z * 40 });
  }
  safe(() => p.sendMessage(capitalLine(p)));
});
