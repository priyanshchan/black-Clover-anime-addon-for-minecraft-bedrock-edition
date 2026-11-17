// AI vs AI battles: two factions spawn on opposite sides and fight until one side falls.
// Used by the War Table (with bets), the Skirmish Horn and the random "skirmish" world event.
import { Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { effect, groundBelow } from '../core/combat.js';
import { particle, rgb, sound, title } from '../core/fx.js';
import { heldKind } from '../core/hud.js';
import { V, alive, pick, rand, safe, timer } from '../core/util.js';
import { spawnCaptain } from '../sea/captains.js';
import { giveCoins } from '../sea/bounty.js';
import { setupKnight } from './knights.js';

const SIDE = {
  a: { mc: '§9', color: '4a80e0', word: 'BLUE' },
  b: { mc: '§c', color: 'e04a3a', word: 'RED' },
};
const UNIT_NAME = {
  'bc:dark_disciple': 'Disciple', 'bc:imp': 'Imp', 'bc:sea_raider': 'Raider', 'bc:tidewatch_sentinel': 'Sentinel',
  'bc:tidewatch_commodore': 'Commodore', 'bc:construct': 'Construct',
};

/**
 * @typedef {Object} Battle
 * @property {number} id
 * @property {any} dim
 * @property {{x:number,y:number,z:number}} center
 * @property {{f: string, ids: Set<string>}} a
 * @property {{f: string, ids: Set<string>}} b
 * @property {{player: string, side: string, amount: number} | undefined} bet
 * @property {number} start
 * @property {boolean} done
 */
/** @type {Map<number, Battle>} */
const battles = new Map();
let nextId = 1;

export function factionIds() {
  return Object.keys(DATA.factions);
}

function surface(dim, loc) {
  return groundBelow(dim, { x: loc.x, y: loc.y + 4, z: loc.z }, 14);
}

function spawnUnit(dim, type, loc, side, leader) {
  const s = SIDE[side];
  let e;
  if (type === 'bc:raider_captain') {
    e = spawnCaptain(dim, loc, {});
    safe(() => e?.triggerEvent(`bc:team_${side}`));
  } else {
    e = safe(() => dim.spawnEntity(type, loc, { spawnEvent: `bc:team_${side}` }));
  }
  if (!e) return undefined;
  safe(() => e.setDynamicProperty('bc:team', side));
  if (type === 'bc:magic_knight') setupKnight(e, { randomRobe: true, prefix: s.mc });
  else if (type === 'bc:raider_captain') safe(() => { e.nameTag = `${s.mc}${e.nameTag.replace(/§./g, '')}`; });
  else {
    if (type === 'bc:construct') safe(() => e.setProperty('bc:variant', Math.floor(Math.random() * 4)));
    safe(() => { e.nameTag = `${s.mc}${leader ? '★ ' : ''}${UNIT_NAME[type] ?? 'Soldier'}`; });
  }
  effect(e, 'slowness', 3.2, 10, false);
  effect(e, 'weakness', 3.2, 4, false);
  return e;
}

/**
 * Start a battle.
 * @param {{dim:any, center:{x:number,y:number,z:number}, facing:{x:number,y:number,z:number}, fa:string, fb:string, size:number,
 *          leaders?: boolean, bet?: {player: string, side: string, amount: number}, quiet?: boolean}} o
 */
export function startBattle(o) {
  const id = nextId++;
  const right = V.flat({ x: -o.facing.z, y: 0, z: o.facing.x });
  const fwd = V.flat(o.facing);
  /** @type {Battle} */
  const b = { id, dim: o.dim, center: o.center, a: { f: o.fa, ids: new Set() }, b: { f: o.fb, ids: new Set() }, bet: o.bet, start: system.currentTick + 70, done: false };
  for (const side of ['a', 'b']) {
    const f = DATA.factions[side === 'a' ? o.fa : o.fb];
    const base = V.add(o.center, V.mul(right, side === 'a' ? -9 : 9));
    particle(o.dim, 'bc:magic_circle_ground', V.add(surface(o.dim, base), { x: 0, y: 0.1, z: 0 }), { color: rgb(SIDE[side].color), size: 4.5, life: 3.5 });
    for (let i = 0; i < o.size; i++) {
      const row = Math.floor(i / 4);
      const col = (i % 4) - 1.5;
      const spot = surface(o.dim, V.add(V.add(base, V.mul(fwd, col * 1.6)), V.mul(right, (side === 'a' ? -1 : 1) * row * 1.6)));
      const leader = o.leaders && i === 0 && f.leader !== f.units[0];
      const type = leader ? f.leader : pick(f.units);
      const e = spawnUnit(o.dim, type, spot, side, leader);
      if (e) b[side].ids.add(e.id);
      particle(o.dim, 'bc:pillar', spot, { color: rgb(SIDE[side].color), scale: 0.6 });
    }
  }
  battles.set(id, b);
  const watchers = o.dim.getPlayers({ location: o.center, maxDistance: 64 });
  const fa = DATA.factions[o.fa];
  const fb = DATA.factions[o.fb];
  sound(o.dim, 'bc.horn', o.center, 2, 1);
  for (const p of watchers) {
    if (!o.quiet) safe(() => p.sendMessage(`§6⚔ §9${fa.name} §7vs §c${fb.name} §8(${o.size} a side)`));
    title(p, '§6§lBATTLE', `§9${fa.name} §7vs §c${fb.name}`, 30);
  }
  for (const [k, w] of [[25, '§e3'], [40, '§e2'], [55, '§e1']]) timer(/** @type {number} */ (k), () => {
    for (const p of o.dim.getPlayers({ location: o.center, maxDistance: 64 })) title(p, /** @type {string} */ (w), '', 12);
    sound(o.dim, 'random.click', o.center, 1.5, 1.4);
  });
  timer(70, () => {
    for (const p of o.dim.getPlayers({ location: o.center, maxDistance: 64 })) title(p, '§c§lFIGHT!', '', 20);
    sound(o.dim, 'bc.horn', o.center, 2, 1.2);
  });
  return id;
}

function finish(b, winner) {
  b.done = true;
  const dim = b.dim;
  const watchers = safe(() => dim.getPlayers({ location: b.center, maxDistance: 80 })) ?? [];
  const wf = winner ? DATA.factions[b[winner].f] : undefined;
  const head = winner ? `${SIDE[winner].mc}§l${SIDE[winner].word} VICTORY` : '§7§lDRAW';
  for (const p of watchers) title(p, head, wf ? `${wf.mc}${wf.name}§7 hold the field` : '§7Both sides withdraw', 60);
  sound(dim, 'bc.fanfare', b.center, 2, 1);
  particle(dim, 'bc:light_burst', V.add(b.center, { x: 0, y: 2, z: 0 }), { scale: 2 });
  particle(dim, 'bc:clover_leaves', V.add(b.center, { x: 0, y: 2, z: 0 }), { scale: 2 });
  if (b.bet) {
    const p = world.getEntity(b.bet.player);
    if (p instanceof Player) {
      if (winner && b.bet.side === winner) {
        giveCoins(p, b.bet.amount * 2);
        safe(() => p.sendMessage(`§e⛁ Your bet paid out: §6${b.bet.amount * 2} doubloons§e!`));
        sound(dim, 'bc.coins', p.location, 1, 1);
      } else if (!winner) {
        giveCoins(p, b.bet.amount);
        safe(() => p.sendMessage('§7A draw - your stake is returned.'));
      } else safe(() => p.sendMessage('§7Your side lost. The bookmaker keeps your stake.'));
    }
  }
  // survivors march off after a while
  timer(200, () => {
    for (const side of ['a', 'b']) {
      for (const id of b[side].ids) {
        const e = world.getEntity(id);
        if (!e) continue;
        particle(dim, 'bc:smoke_burst', e.location, { scale: 0.6 });
        safe(() => e.remove());
      }
    }
    battles.delete(b.id);
  });
}

function count(b, side) {
  let n = 0;
  for (const id of [...b[side].ids]) {
    const e = world.getEntity(id);
    if (!e || !alive(e)) {
      b[side].ids.delete(id);
      continue;
    }
    n++;
    // keep the fight in the arena
    if (V.dist(e.location, b.center) > 36) safe(() => e.teleport(V.add(b.center, { x: rand(-4, 4), y: 1, z: rand(-4, 4) })));
  }
  return n;
}

system.runInterval(() => {
  const t = system.currentTick;
  for (const b of battles.values()) {
    if (b.done) continue;
    safe(() => {
      const na = count(b, 'a');
      const nb = count(b, 'b');
      const fa = DATA.factions[b.a.f];
      const fb = DATA.factions[b.b.f];
      if (t > b.start) {
        for (const p of b.dim.getPlayers({ location: b.center, maxDistance: 64 })) {
          if (heldKind(p)) continue;
          safe(() => p.onScreenDisplay.setActionBar(`§9${fa.name} §f${na}  §8⚔  §f${nb} §c${fb.name}`));
        }
      }
      if (na === 0 || nb === 0) finish(b, na > 0 ? 'a' : nb > 0 ? 'b' : undefined);
      else if (t - b.start > 20 * 240) finish(b, undefined);
    }, 'battle');
  }
}, 20);

export function activeBattleNear(dim, loc, r = 40) {
  for (const b of battles.values()) if (!b.done && b.dim.id === dim.id && V.dist(b.center, loc) < r) return b;
  return undefined;
}
