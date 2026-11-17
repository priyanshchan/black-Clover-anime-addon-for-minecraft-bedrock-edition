// The battle simulator: two or three armies spawn in formation and fight until one side holds the field.
// Each side has a TACTIC (charge, hold the line, flank, skirmish), MORALE that breaks when it takes losses
// (routed soldiers flee and may rally while their leader lives), a LEADER whose aura steadies nearby troops,
// and a shared FOCUS target. A live scoreboard, kill feed, battle report and a cinematic camera let you watch.
// Used by the War Table (with bets), the Skirmish Horn and world events.
import { DisplaySlotId, EasingType, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { center, effect, groundBelow } from '../core/combat.js';
import { particle, rgb, sound, title } from '../core/fx.js';
import { heldKind } from '../core/hud.js';
import { V, alive, pick, rand, safe, timer } from '../core/util.js';
import { spawnCaptain } from '../sea/captains.js';
import { giveCoins } from '../sea/bounty.js';
import { setupKnight } from './knights.js';

export const SIDE = {
  a: { mc: '§9', color: '4a80e0', word: 'Blue' },
  b: { mc: '§c', color: 'e04a3a', word: 'Red' },
  c: { mc: '§e', color: 'f0c040', word: 'Gold' },
};
export const TACTICS = {
  charge: 'Charge - rush the enemy',
  hold: 'Hold the line - let them come',
  flank: 'Flank - half the army swings around the side',
  skirmish: 'Skirmish - mages keep their distance',
};
const UNIT_NAME = {
  'bc:dark_disciple': 'Disciple', 'bc:imp': 'Imp', 'bc:sea_raider': 'Raider', 'bc:tidewatch_sentinel': 'Sentinel',
  'bc:tidewatch_commodore': 'Commodore', 'bc:construct': 'Construct',
};
const CASTERS = new Set(['bc:magic_knight', 'bc:dark_disciple']);
const OBJECTIVE = 'bc_battle';

/**
 * @typedef {{ f: string, label: string, ids: Set<string>, initial: number, morale: number, tactic: string, leader: string,
 *             lost: number, fled: number, focus: string, centroid: {x:number,y:number,z:number} }} Side
 * @typedef {{ id: number, dim: any, center: {x:number,y:number,z:number}, sides: Record<string, Side>, bet: any, start: number,
 *             done: boolean, morale: boolean, simulated: boolean, duel: boolean, quiet: boolean,
 *             kills: Map<string, number>, dmg: Map<string, number>, names: Map<string, string>, owner?: string }} Battle
 * @typedef {{ battle: Battle, side: string, leader: boolean, routing: boolean, anchor: {x:number,y:number,z:number},
 *             flank?: {x:number,y:number,z:number}, courage: number }} Unit
 */
/** @type {Map<number, Battle>} */
const battles = new Map();
/** @type {Map<string, Unit>} */
const units = new Map();
let nextId = 1;
/** @type {((b: Battle, winner: string | undefined) => void)[]} */
const endHooks = [];
/** @type {Map<string, string>} player id -> last battle report */
export const reports = new Map();
/** @type {Map<string, {battle: number, angle: number}>} */
const spectators = new Map();

export function factionIds() {
  return Object.keys(DATA.factions);
}
export function onBattleEnd(fn) {
  endHooks.push(fn);
}

/** What the AI needs to know about a soldier. */
export function unitInfo(id) {
  const u = units.get(id);
  if (!u || u.battle.done) return undefined;
  const s = u.battle.sides[u.side];
  let enemyLeader = '';
  for (const [k, o] of Object.entries(u.battle.sides)) if (k !== u.side && o.leader) enemyLeader = o.leader;
  return { routing: u.routing, focus: s.focus, enemyLeader, tactic: s.tactic };
}

function surface(dim, loc) {
  return groundBelow(dim, { x: loc.x, y: loc.y + 4, z: loc.z }, 14);
}

function displayName(e) {
  return (safe(() => e.nameTag) || UNIT_NAME[e.typeId] || 'Soldier').replace(/§./g, '').replace(/[-]/g, '').trim();
}

function spawnUnit(dim, spec, loc, side, leader) {
  const s = SIDE[side];
  const type = spec.type;
  let e;
  if (type === 'bc:raider_captain') {
    e = spawnCaptain(dim, loc, {});
    safe(() => e?.triggerEvent(`bc:team_${side}`));
  } else {
    e = safe(() => dim.spawnEntity(type, loc, { spawnEvent: `bc:team_${side}` }));
  }
  if (!e) return undefined;
  safe(() => e.setDynamicProperty('bc:team', side));
  if (type === 'bc:magic_knight') setupKnight(e, { randomRobe: true, prefix: s.mc, attr: spec.attr, level: spec.level });
  else if (type === 'bc:raider_captain') safe(() => { e.nameTag = `${s.mc}${e.nameTag.replace(/§./g, '')}`; });
  else {
    if (type === 'bc:construct') safe(() => e.setProperty('bc:variant', Math.floor(Math.random() * 4)));
    safe(() => { e.nameTag = `${s.mc}${leader ? '★ ' : ''}${UNIT_NAME[type] ?? 'Soldier'}`; });
  }
  effect(e, 'slowness', 3.4, 10, false);
  effect(e, 'weakness', 3.4, 4, false);
  return e;
}

/** Side anchor points: opposite each other, or a triangle for three armies. */
function basePoints(center, facing, n) {
  const right = V.flat({ x: -facing.z, y: 0, z: facing.x });
  if (n === 2) return [V.add(center, V.mul(right, -10)), V.add(center, V.mul(right, 10))];
  return [0, 120, 240].map((a) => V.add(center, V.mul(V.yaw(right, a - 180), 11)));
}

/**
 * Start a battle.
 * @param {{dim:any, center:{x:number,y:number,z:number}, facing:{x:number,y:number,z:number}, fa:string, fb:string, fc?:string, size:number,
 *          leaders?: boolean, bet?: {player: string, side: string, amount: number}, quiet?: boolean, tactics?: Record<string, string>,
 *          morale?: boolean, simulated?: boolean, owner?: string, roster?: Record<string, {type: string, attr?: string, level?: number, leader?: boolean}[]>, duel?: boolean}} o
 */
export function startBattle(o) {
  const id = nextId++;
  const keys = o.fc ? ['a', 'b', 'c'] : ['a', 'b'];
  const factions = { a: o.fa, b: o.fb, c: o.fc };
  const bases = basePoints(o.center, o.facing, keys.length);
  /** @type {Battle} */
  const b = {
    id, dim: o.dim, center: o.center, sides: {}, bet: o.bet, start: system.currentTick + 70, done: false,
    morale: o.morale !== false && !o.duel, simulated: !!o.simulated, duel: !!o.duel, quiet: !!o.quiet,
    kills: new Map(), dmg: new Map(), names: new Map(), owner: o.owner,
  };
  keys.forEach((side, si) => {
    const f = DATA.factions[factions[side]];
    const base = bases[si];
    const toC = V.flat(V.sub(o.center, base));
    const along = { x: -toC.z, y: 0, z: toC.x };
    const tactic = o.tactics?.[side] ?? 'charge';
    /** @type {Side} */
    const S = { f: factions[side], label: o.duel ? 'Duellist' : f.name, ids: new Set(), initial: 0, morale: 100, tactic, leader: '', lost: 0, fled: 0, focus: '', centroid: base };
    b.sides[side] = S;
    // muster: melee in front, casters behind, the leader in the middle of the second rank
    let roster = o.roster?.[side];
    if (!roster) {
      roster = [];
      for (let i = 0; i < o.size; i++) roster.push({ type: pick(f.units) });
      if (o.leaders && f.leader !== f.units[0]) roster[0] = { type: f.leader, leader: true };
    }
    const front = roster.filter((r) => !CASTERS.has(r.type) && !r.leader);
    const back = roster.filter((r) => CASTERS.has(r.type) || r.leader);
    const ranks = [front, back].filter((r) => r.length);
    particle(o.dim, 'bc:magic_circle_ground', V.add(surface(o.dim, base), { x: 0, y: 0.1, z: 0 }), { color: rgb(SIDE[side].color), size: 5, life: 3.5 });
    ranks.forEach((rank, ri) => {
      rank.forEach((r, i) => {
        const col = (i % 6) - (Math.min(6, rank.length) - 1) / 2;
        const row = ri * 1.8 + Math.floor(i / 6) * 1.6;
        const spot = surface(o.dim, V.add(V.add(base, V.mul(along, col * 1.7)), V.mul(toC, -row)));
        const e = spawnUnit(o.dim, r, spot, side, r.leader);
        if (!e) return;
        S.ids.add(e.id);
        const kname = safe(() => e.getDynamicProperty('bc:kname'));
        b.names.set(e.id, `${SIDE[side].mc}${typeof kname === 'string' ? kname : displayName(e)}`);
        if (r.leader) S.leader = e.id;
        const flankDir = i % 2 ? 60 : -60;
        units.set(e.id, {
          battle: b, side, leader: !!r.leader, routing: false, anchor: spot, courage: rand(0.2, 1),
          flank: tactic === 'flank' && i % 2 === 0 ? V.add(o.center, V.mul(V.yaw(V.sub(base, o.center), flankDir), 0.8)) : undefined,
        });
        particle(o.dim, 'bc:pillar', spot, { color: rgb(SIDE[side].color), scale: 0.6 });
      });
    });
    S.initial = S.ids.size;
  });
  battles.set(id, b);
  setupScoreboard(b);
  const names = keys.map((k) => `${SIDE[k].mc}${b.sides[k].label}`).join(' §7vs ');
  sound(o.dim, 'bc.horn', o.center, 2, 1);
  for (const p of o.dim.getPlayers({ location: o.center, maxDistance: 64 })) {
    if (!o.quiet) safe(() => p.sendMessage(`§6⚔ ${names} §8(${keys.map((k) => b.sides[k].initial).join(' v ')}) §7- tactics: ${keys.map((k) => `${SIDE[k].mc}${b.sides[k].tactic}`).join('§7, ')}`));
    title(p, o.duel ? '§6§lDUEL' : '§6§lBATTLE', names, 30);
  }
  for (const [k, w] of [[25, '§e3'], [40, '§e2'], [55, '§e1']]) timer(/** @type {number} */ (k), () => {
    for (const p of o.dim.getPlayers({ location: o.center, maxDistance: 64 })) title(p, /** @type {string} */ (w), '', 12);
    sound(o.dim, 'random.click', o.center, 1.5, 1.4);
  });
  timer(70, () => {
    for (const p of o.dim.getPlayers({ location: o.center, maxDistance: 64 })) title(p, '§c§lFIGHT!', '', 20);
    sound(o.dim, 'bc.horn', o.center, 2, 1.2);
    for (const k of keys) {
      if (b.sides[k].tactic !== 'charge') continue;
      for (const uid of b.sides[k].ids) {
        const e = world.getEntity(uid);
        if (e) effect(e, 'speed', 5, 1, false);
      }
    }
  });
  return id;
}

// ------------------------------------------------------------------------------- scoreboard
function setupScoreboard(b) {
  safe(() => {
    const sb = world.scoreboard;
    if (sb.getObjective(OBJECTIVE)) sb.removeObjective(OBJECTIVE);
    const obj = sb.addObjective(OBJECTIVE, b.duel ? '§6⚔ Duel' : '§6⚔ Battle');
    sb.setObjectiveAtDisplaySlot(DisplaySlotId.Sidebar, { objective: obj });
  }, 'scoreboard');
}
function updateScoreboard(b) {
  safe(() => {
    const obj = world.scoreboard.getObjective(OBJECTIVE);
    if (!obj) return;
    for (const [k, s] of Object.entries(b.sides)) {
      obj.setScore(`${SIDE[k].mc}${SIDE[k].word}: ${s.label}`, s.ids.size);
      if (b.morale) obj.setScore(`${SIDE[k].mc}${SIDE[k].word} morale`, Math.max(0, Math.round(s.morale)));
    }
  });
}

// ------------------------------------------------------------------------------- kill feed & stats
world.afterEvents.entityHurt.subscribe((ev) => {
  const src = ev.damageSource.damagingEntity;
  if (!src) return;
  const u = units.get(src.id);
  if (u && !u.battle.done) u.battle.dmg.set(src.id, (u.battle.dmg.get(src.id) ?? 0) + ev.damage);
});

world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const dead = ev.deadEntity;
  const u = units.get(dead.id);
  if (!u) return;
  const b = u.battle;
  units.delete(dead.id);
  const s = b.sides[u.side];
  if (!s || b.done) return;
  s.ids.delete(dead.id);
  s.lost += 1;
  const k = ev.damageSource.damagingEntity;
  let who = '§7the battlefield';
  if (k) {
    b.kills.set(k.id, (b.kills.get(k.id) ?? 0) + 1);
    who = b.names.get(k.id) ?? (k instanceof Player ? `§f${k.name}` : `§7${displayName(k)}`);
  }
  if (b.morale) {
    s.morale -= u.leader ? 30 : 75 / Math.max(1, s.initial);
    for (const [key, o] of Object.entries(b.sides)) if (key !== u.side) o.morale = Math.min(100, o.morale + 3);
  }
  if (u.leader) {
    s.leader = '';
    for (const p of b.dim.getPlayers({ location: b.center, maxDistance: 64 })) title(p, ' ', `${SIDE[u.side].mc}${b.names.get(dead.id)}§7, the ${s.label} leader, has fallen!`, 30);
  }
  if (!b.quiet) {
    for (const p of b.dim.getPlayers({ location: b.center, maxDistance: 64 })) safe(() => p.sendMessage(`§8⚔ ${who} §7defeated ${b.names.get(dead.id) ?? 'a soldier'}`));
  }
}, 'battleDie'));

// ------------------------------------------------------------------------------- the battle tick
function centroid(b, s) {
  let n = 0;
  const c = { x: 0, y: 0, z: 0 };
  for (const id of s.ids) {
    const e = world.getEntity(id);
    if (!e) continue;
    c.x += e.location.x;
    c.y += e.location.y;
    c.z += e.location.z;
    n++;
  }
  return n ? V.mul(c, 1 / n) : b.center;
}

function push(e, dir, strength) {
  const f = V.flat(dir);
  safe(() => e.applyImpulse({ x: f.x * strength, y: 0, z: f.z * strength }));
}

function rout(b, u, e, on) {
  u.routing = on;
  safe(() => {
    if (on) {
      e.nameTag = `${b.names.get(e.id)} §7(fleeing)`;
      effect(e, 'speed', 6, 1, false);
      particle(e.dimension, 'bc:dust_burst', e.location, { color: rgb('b0b0b0'), scale: 0.6 });
    } else {
      e.nameTag = b.names.get(e.id) ?? e.nameTag;
      particle(e.dimension, 'bc:shockwave', e.location, { color: rgb(SIDE[u.side].color), radius: 1.5 });
    }
  });
}

/** Movement orders and morale, every 5 ticks. */
system.runInterval(() => {
  const t = system.currentTick;
  for (const b of battles.values()) {
    if (b.done || t < b.start) continue;
    safe(() => {
      const enemyCentre = (side) => {
        const pts = Object.entries(b.sides).filter(([k]) => k !== side).map(([, o]) => o.centroid);
        return pts.length ? V.mul(pts.reduce((a, p) => V.add(a, p), { x: 0, y: 0, z: 0 }), 1 / pts.length) : b.center;
      };
      for (const [id, u] of units) {
        if (u.battle !== b) continue;
        const e = world.getEntity(id);
        if (!e) continue;
        const foeC = enemyCentre(u.side);
        if (u.routing) {
          push(e, V.sub(e.location, foeC), 0.32);
          if (V.dist(e.location, b.center) > 34) {
            const s = b.sides[u.side];
            s.ids.delete(id);
            s.fled += 1;
            units.delete(id);
            particle(e.dimension, 'bc:smoke_burst', e.location, { scale: 0.6 });
            if (!b.quiet) for (const p of b.dim.getPlayers({ location: b.center, maxDistance: 64 })) safe(() => p.sendMessage(`§8⚔ ${b.names.get(id)} §7fled the field`));
            safe(() => e.remove());
          }
          continue;
        }
        const tactic = b.sides[u.side].tactic;
        const close = V.dist(e.location, foeC) < 11;
        if (u.flank && t - b.start < 220) {
          if (V.dist(e.location, u.flank) < 4) u.flank = undefined;
          else push(e, V.sub(u.flank, e.location), 0.24);
        } else if (tactic === 'hold' && t - b.start < 500 && !close && V.dist(e.location, u.anchor) > 2.5) {
          push(e, V.sub(u.anchor, e.location), 0.2);
        }
        // keep everyone in the arena
        if (V.dist(e.location, b.center) > 36) safe(() => e.teleport(V.add(b.center, { x: rand(-4, 4), y: 1, z: rand(-4, 4) })));
      }
    }, 'battleMove');
  }
}, 5);

/** Morale, leaders, focus fire, scoreboard and the end of the battle, every second. */
system.runInterval(() => {
  const t = system.currentTick;
  for (const b of battles.values()) {
    if (b.done) continue;
    safe(() => {
      for (const [k, s] of Object.entries(b.sides)) {
        for (const id of [...s.ids]) {
          const e = world.getEntity(id);
          if (!e || !alive(e)) {
            s.ids.delete(id);
            units.delete(id);
          }
        }
        s.centroid = centroid(b, s);
        const leader = s.leader ? world.getEntity(s.leader) : undefined;
        if (t < b.start) continue;
        // leader aura
        if (leader && t % 40 < 20) {
          particle(b.dim, 'bc:shockwave', leader.location, { color: rgb(SIDE[k].color), radius: 6 });
          for (const id of s.ids) {
            const e = world.getEntity(id);
            if (e && id !== leader.id && V.dist(e.location, leader.location) < 10) effect(e, 'strength', 2.5, 0, false);
          }
        }
        // focus fire: the weakest foe near the army's centre
        let best;
        let bs = -Infinity;
        for (const [ok, o] of Object.entries(b.sides)) {
          if (ok === k) continue;
          for (const id of o.ids) {
            const e = world.getEntity(id);
            if (!e) continue;
            const h = safe(() => e.getComponent('minecraft:health'));
            const frac = h ? h.currentValue / h.effectiveMax : 1;
            const sc = -V.dist(e.location, s.centroid) * 0.6 + (1 - frac) * 10 + (o.leader === id ? 3 : 0);
            if (sc > bs) {
              bs = sc;
              best = id;
            }
          }
        }
        s.focus = best ?? '';
        // morale: losing badly drains it, a living leader restores it
        if (b.morale) {
          const mine = s.ids.size;
          let theirs = 0; // the strongest single enemy army
          for (const [ok, o] of Object.entries(b.sides)) if (ok !== k) theirs = Math.max(theirs, o.ids.size);
          if (mine && theirs / mine >= 2) s.morale -= 4;
          else if (mine && theirs / mine >= 1.5) s.morale -= 2;
          s.morale = Math.min(100, s.morale + (leader ? 1.5 : 0.4));
          for (const id of s.ids) {
            const u = units.get(id);
            const e = world.getEntity(id);
            if (!u || !e) continue;
            if (!u.routing && s.morale < 30 && Math.random() < ((30 - s.morale) / 30) * (1.2 - u.courage) * 0.6) rout(b, u, e, true);
            else if (u.routing && s.morale > 55) {
              rout(b, u, e, false);
              if (!b.quiet && leader) for (const p of b.dim.getPlayers({ location: b.center, maxDistance: 64 })) safe(() => p.sendMessage(`§8⚔ ${b.names.get(id)} §7rallies to ${b.names.get(leader.id)}!`));
            }
          }
        }
      }
      updateScoreboard(b);
      const fighting = Object.entries(b.sides).filter(([, s]) => [...s.ids].some((id) => !units.get(id)?.routing));
      const counts = Object.entries(b.sides).map(([k, s]) => `${SIDE[k].mc}${s.label} §f${s.ids.size}`).join('  §8⚔  ');
      if (t > b.start) {
        for (const p of b.dim.getPlayers({ location: b.center, maxDistance: 64 })) {
          if (!heldKind(p)) safe(() => p.onScreenDisplay.setActionBar(counts));
        }
      }
      if (t > b.start && fighting.length <= 1) finish(b, fighting[0]?.[0]);
      else if (t - b.start > 20 * 240) finish(b, undefined);
    }, 'battle');
  }
}, 20);

// ------------------------------------------------------------------------------- the end
function report(b, winner) {
  const secs = Math.max(0, Math.round((system.currentTick - b.start) / 20));
  const lines = [`§6§lBattle report§r §7(${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')})`];
  for (const [k, s] of Object.entries(b.sides)) {
    const routed = [...s.ids].filter((id) => units.get(id)?.routing).length;
    lines.push(`${SIDE[k].mc}${s.label}§7: ${s.initial} fought, ${s.lost} fell${s.fled ? `, ${s.fled} fled` : ''}, ${s.ids.size - routed} stand${routed ? `, ${routed} running` : ''} - tactic ${s.tactic}${k === winner ? ' §6(victors)' : ''}`);
  }
  let mvp = '';
  let ms = -1;
  for (const [id, name] of b.names) {
    const sc = (b.kills.get(id) ?? 0) * 25 + (b.dmg.get(id) ?? 0);
    if (sc > ms) {
      ms = sc;
      mvp = `§7Most valuable: ${name}§7 - ${b.kills.get(id) ?? 0} defeated, ${Math.round(b.dmg.get(id) ?? 0)} damage`;
    }
  }
  if (ms > 0) lines.push(mvp);
  return lines.join('\n');
}

function finish(b, winner) {
  b.done = true;
  const dim = b.dim;
  const watchers = safe(() => dim.getPlayers({ location: b.center, maxDistance: 80 })) ?? [];
  const ws = winner ? b.sides[winner] : undefined;
  const head = winner ? `${SIDE[winner].mc}§l${SIDE[winner].word.toUpperCase()} VICTORY` : '§7§lDRAW';
  const rep = report(b, winner);
  for (const p of watchers) {
    title(p, head, ws ? `${SIDE[winner].mc}${ws.label}§7 hold the field` : '§7No one holds the field', 60);
    if (!b.quiet || p.id === b.owner) safe(() => p.sendMessage(rep));
    reports.set(p.id, rep);
  }
  sound(dim, 'bc.fanfare', b.center, 2, 1);
  particle(dim, 'bc:light_burst', V.add(b.center, { x: 0, y: 2, z: 0 }), { scale: 2 });
  particle(dim, 'bc:clover_leaves', V.add(b.center, { x: 0, y: 2, z: 0 }), { scale: 2 });
  if (b.bet) {
    const p = world.getEntity(b.bet.player);
    if (p instanceof Player) {
      if (winner && b.bet.side === winner) {
        const odds = Object.keys(b.sides).length;
        giveCoins(p, b.bet.amount * odds);
        safe(() => p.sendMessage(`§e⛁ Your bet paid out: §6${b.bet.amount * odds} doubloons§e!`));
        sound(dim, 'bc.coins', p.location, 1, 1);
      } else if (!winner) {
        giveCoins(p, b.bet.amount);
        safe(() => p.sendMessage('§7A draw - your stake is returned.'));
      } else safe(() => p.sendMessage('§7Your side lost. The bookmaker keeps your stake.'));
    }
  }
  for (const fn of endHooks) safe(() => fn(b, winner));
  timer(60, () => {
    for (const [pid, sp] of spectators) {
      if (sp.battle !== b.id) continue;
      const p = world.getEntity(pid);
      if (p instanceof Player) safe(() => p.camera.clear());
      spectators.delete(pid);
    }
  });
  // survivors march off after a while
  timer(200, () => {
    for (const s of Object.values(b.sides)) {
      for (const id of s.ids) {
        const e = world.getEntity(id);
        units.delete(id);
        if (!e) continue;
        particle(dim, 'bc:smoke_burst', e.location, { scale: 0.6 });
        safe(() => e.remove());
      }
    }
    safe(() => {
      if (![...battles.values()].some((o) => !o.done)) world.scoreboard.removeObjective(OBJECTIVE);
    });
    battles.delete(b.id);
  });
}

// ------------------------------------------------------------------------------- spectating
/** Watch the nearest battle from a slowly circling camera. Sneak to stop. */
export function spectate(p, battleId) {
  spectators.set(p.id, { battle: battleId, angle: Math.random() * 360 });
  safe(() => p.onScreenDisplay.setActionBar('§7Cinematic camera - §fsneak§7 to return'));
}

system.runInterval(() => {
  for (const [pid, sp] of spectators) {
    const p = world.getEntity(pid);
    const b = battles.get(sp.battle);
    if (!(p instanceof Player) || !b) {
      spectators.delete(pid);
      continue;
    }
    if (p.isSneaking) {
      safe(() => p.camera.clear());
      spectators.delete(pid);
      continue;
    }
    safe(() => {
      const pts = Object.values(b.sides).map((s) => s.centroid);
      const focus = V.mul(pts.reduce((a, q) => V.add(a, q), { x: 0, y: 0, z: 0 }), 1 / Math.max(1, pts.length));
      sp.angle += 4;
      const r = (sp.angle * Math.PI) / 180;
      const eye = { x: focus.x + Math.cos(r) * 20, y: focus.y + 11, z: focus.z + Math.sin(r) * 20 };
      p.camera.setCamera('minecraft:free', { location: eye, facingLocation: V.add(focus, { x: 0, y: 1, z: 0 }), easeOptions: { easeTime: 0.5, easeType: EasingType.Linear } });
    }, 'camera');
  }
}, 10);

export function activeBattleNear(dim, loc, r = 40) {
  for (const b of battles.values()) if (!b.done && b.dim.id === dim.id && V.dist(b.center, loc) < r) return b;
  return undefined;
}

export { center };
