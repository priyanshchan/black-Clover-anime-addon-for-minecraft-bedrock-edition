// The living world (v1.0.0): world events are INCIDENTS that happen at real places, out of sight - not in front of you.
//
// * They are placed far away (about 60-200 blocks) and reported by direction and distance: "Smoke rises to the
//   north-east, about 180 blocks away". Signs mark them on the horizon (smoke columns, pillars of light), and the
//   newest one is tracked on your HUD (choose another in the Handbook's World events page).
// * They are SIMULATED while nobody is there: a Devil Gate grows stronger, a ritual nears completion, a hive lays
//   eggs, two armies wear each other down, a wounded knight bleeds out, a bandit raid marches on your home, a caravan
//   crosses the land. Left alone they resolve on their own - with consequences: faction power, news, ruins, or a
//   boss let loose.
// * Their units only appear when a player comes close (when the place is really loaded and ticking), in whatever
//   state the incident has reached - and they fade back into the simulation if everyone leaves.
// Personal events (thieves, assassins, bounty hunters, rogue mages, rival squads) approach from out of sight instead.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { ActionFormData, MessageFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { emit } from '../core/bus.js';
import { addMana } from '../core/data.js';
import { particle, rgb, sound, title } from '../core/fx.js';
import { yawOf, V, alive, pick, rand, safe } from '../core/util.js';
import * as vfx from '../core/vfx.js';
import { forceTarget } from './ai.js';
import { startBattle, TACTICS } from './battle.js';
import { summonBoss } from './bosses.js';
import { boltFrom } from './engine.js';
import { EVENTS, eventLog, eventsOn, logEvent, night, reward, runEvent, scaled, setOutcome, tier, weightedFaction } from './events.js';
import { layEgg } from './foes.js';
import { joinParty } from './companions.js';
import { setupKnight } from './knights.js';
import { spawnMerchant } from './merchant.js';
import { setupRogue } from './rogues.js';
import { POWERS, RIVAL, news, onOffensive, powerMul, shift } from './worldsim.js';
import { spawnCaptain } from '../sea/captains.js';
import { setCompassProvider } from '../core/hud.js';

const KEY = 'bc:incidents';
const MAX_ACTIVE = 7;
const MAT_R = 52;          // a player this close makes an incident real (the place is loaded and ticking)
const UNMAT_R = 110;       // ...and if everyone is further than this for a while, it fades back into the simulation
const HEAR_R = 360;        // who hears about a new incident
const CYCLE = 5;           // seconds per simulation step

/**
 * @typedef {{id: string, kind: string, dim: string, x: number, y: number | null, z: number, dest?: {x: number, z: number}, speed?: number,
 *   age: number, life: number, power: number, mat: boolean, ents: string[], until?: number, away?: number, data: Record<string, any>,
 *   done?: string, label: string}} Incident
 */
/** @type {Incident[] | undefined} */
let cache;
function all() {
  if (cache) return cache;
  const raw = safe(() => world.getDynamicProperty(KEY));
  try {
    cache = typeof raw === 'string' ? JSON.parse(raw) : [];
  } catch {
    cache = [];
  }
  if (!Array.isArray(cache)) cache = [];
  return cache;
}
function save() {
  safe(() => world.setDynamicProperty(KEY, JSON.stringify(all().filter((i) => !i.done))));
}
/** Active incidents (for the Handbook, the HUD and tests). */
export function incidents() {
  return all().filter((i) => !i.done);
}

// ------------------------------------------------------------------------------- geography
const DIRS = ['north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west', 'north-west'];
/** "north-east" etc. from a point to another (Minecraft: -z is north, +x is east). */
export function compass(from, to) {
  const a = (Math.atan2(to.x - from.x, -(to.z - from.z)) * 180) / Math.PI;
  return DIRS[((Math.round(a / 45) % 8) + 8) % 8];
}
function flatDist(a, b) {
  return Math.hypot(a.x - b.x, a.z - b.z);
}
function dimOf(id) {
  return safe(() => world.getDimension(id));
}
/** The ground at x/z, if that chunk is loaded. */
function groundAt(dim, x, z) {
  const top = safe(() => dim.getTopmostBlock({ x, z }));
  if (!top) return undefined;
  return { y: top.location.y + 1, liquid: top.isLiquid, id: top.typeId };
}
/** A place out of sight: far if possible (the ground there is worked out when someone gets close). */
function placeFar(p, minD = 60, maxD = 200, water = false) {
  const tries = [[Math.max(minD, 110), maxD], [Math.max(minD, 75), 110], [minD, 75]];
  for (const [lo, hi] of tries) {
    if (lo > hi) continue;
    for (let i = 0; i < 7; i++) {
      const a = Math.random() * Math.PI * 2;
      const d = rand(lo, hi);
      const x = p.location.x + Math.sin(a) * d;
      const z = p.location.z - Math.cos(a) * d;
      if (world.getAllPlayers().some((q) => q.id !== p.id && flatDist(q.location, { x, z }) < 40)) continue;
      const g = groundAt(p.dimension, x, z);
      if (water) {
        if (g && g.id === 'minecraft:water') return { x, y: g.y - 2, z };
        continue;
      }
      if (!g) {
        if (d >= 90) return { x, y: null, z };
        continue;
      }
      if (g.liquid || g.id.endsWith('leaves') || Math.abs(g.y - p.location.y) > 30) continue;
      return { x, y: g.y, z };
    }
  }
  return undefined;
}

// ------------------------------------------------------------------------------- the kinds of incident
const C = (h) => vfx.hex(h);
/**
 * w: weight, f: faction (weights follow its power), ok(p): may it start now, life: seconds before it resolves alone,
 * sign: what marks it on the horizon, color, rumor: what you hear, moving: travels toward dest,
 * tick(inc, dt): the simulation, spawn(inc, p, at): make it real, won/lost: outcomes, end: resolved without anyone.
 * @type {Record<string, any>}
 */
const KINDS = {
  devil_gate: {
    name: 'Devil Gate', mc: '§4', w: 8, f: 'devils', life: 720, sign: 'beam', color: '9a1018',
    rumor: 'A crimson light splits the sky',
    tick(inc, dt) {
      inc.power = Math.min(10, inc.power + dt / 60);
    },
    spawn(inc, p, at) {
      const dim = p.dimension;
      const gate = safe(() => dim.spawnEntity('bc:devil_gate', V.add(at, { x: 0, y: 0.5, z: 0 })));
      if (!gate) return false;
      const n = Math.min(10, 2 + Math.floor(inc.power));
      for (let i = 0; i < n; i++) safe(() => dim.spawnEntity(i % 3 === 2 ? 'bc:dark_disciple' : 'bc:imp', V.add(at, { x: rand(-4, 4), y: 1, z: rand(-4, 4) })));
      arrive(inc, at, '§4§lA DEVIL GATE', `§7${n > 6 ? 'It has been open too long - the devils pour out' : 'Destroy it before it grows'}`);
      inc.ents = [gate.id];
      inc.until = inc.age + Math.max(120, inc.life - inc.age);
      return true;
    },
    won(inc) {
      shift('devils', -3);
      shift('knights', 2);
      news(`A Devil Gate ${inc.data.where} was sealed.`);
    },
    end(inc, dim, at) {
      shift('devils', 5);
      shift('knights', -3);
      news(`A Devil Gate ${inc.data.where} erupted - the Devil Host grows stronger.`);
      if (Math.random() < 0.5) startIncident('boss', undefined, { at, dim: dim?.id ?? inc.dim, boss: 'bc:archdevil', label: 'The Archdevil', where: inc.data.where });
      else ruins(inc, 'devils');
      return 'erupted';
    },
  },
  skirmish: {
    name: 'Skirmish', mc: '§6', w: 10, life: 300, sign: 'smoke', color: '6a5a4a',
    rumor: 'Battle cries echo and smoke rises',
    init(inc) {
      const fa = weightedFaction();
      const fb = Math.random() < 0.6 && RIVAL[fa] ? RIVAL[fa] : weightedFaction(fa);
      inc.data.fa = fa;
      inc.data.fb = fb;
      inc.data.sa = 5 + Math.floor(Math.random() * 4);
      inc.data.sb = 5 + Math.floor(Math.random() * 4);
      inc.label = `${DATA.factions[fa].name} vs ${DATA.factions[fb].name}`;
    },
    tick(inc, dt) {
      // the armies wear each other down (each side loses in proportion to the other's numbers)
      const d = inc.data;
      const la = d.sb * 0.005 * dt * (powerMul(d.fb) || 1) * rand(0.6, 1.4);
      const lb = d.sa * 0.005 * dt * (powerMul(d.fa) || 1) * rand(0.6, 1.4);
      d.sa = Math.max(0, d.sa - la);
      d.sb = Math.max(0, d.sb - lb);
      if (d.sa < 1 || d.sb < 1) inc.life = inc.age; // decided
    },
    spawn(inc, p, at) {
      const d = inc.data;
      const sa = Math.max(1, Math.round(d.sa));
      const sb = Math.max(1, Math.round(d.sb));
      const tactics = Object.keys(TACTICS);
      arrive(inc, at, '§6§lA SKIRMISH', `§7${DATA.factions[d.fa].name} (${sa}) against ${DATA.factions[d.fb].name} (${sb})`);
      startBattle({ dim: p.dimension, center: at, facing: V.flat(V.sub(at, p.location)), fa: d.fa, fb: d.fb, size: Math.min(9, Math.max(sa, sb)),
        leaders: true, quiet: true, tactics: { a: pick(tactics), b: pick(tactics) } });
      return 'witnessed';
    },
    end(inc) {
      const d = inc.data;
      const win = d.sa >= d.sb ? d.fa : d.fb;
      const lose = win === d.fa ? d.fb : d.fa;
      if (POWERS.includes(win)) shift(win, 3);
      if (POWERS.includes(lose)) shift(lose, -3);
      news(`${DATA.factions[win].name} won a skirmish against the ${DATA.factions[lose].name} ${inc.data.where}.`);
      return `${DATA.factions[win].name} won`;
    },
  },
  bandit_raid: {
    name: 'Bandit raid', mc: '§6', w: 8, f: 'bandits', life: 600, sign: 'smoke', color: '5a4630', moving: 0.55, far: [130, 210],
    rumor: 'Horns sound and dust rises - a bandit raid is on the march',
    init(inc, p) {
      inc.dest = { x: p.location.x + rand(-6, 6), z: p.location.z + rand(-6, 6) };
      inc.power = scaled(p, 4);
      inc.data.king = tier(p) >= 2 && Math.random() < 0.3;
      if (inc.data.king) inc.label = 'Bandit raid (the Bandit King)';
    },
    spawn(inc, p, at) {
      const dim = p.dimension;
      const ids = [];
      const n = Math.max(2, Math.round(inc.power));
      for (let i = 0; i < n; i++) {
        const type = i === 0 ? 'bc:bandit_thief' : i % 3 === 0 ? 'bc:bandit_archer' : 'bc:bandit';
        const e = safe(() => dim.spawnEntity(type, V.add(at, { x: rand(-3, 3), y: 0.5, z: rand(-3, 3) })));
        if (!e) continue;
        ids.push(e.id);
        safe(() => e.addTag('bc_event'));
        forceTarget(e, p, 20 * 60);
      }
      if (inc.data.king) system.runTimeout(() => summonBoss('bc:bandit_king', dim, at, [p]), 60);
      sound(dim, 'bc.horn', at, 2, 0.7);
      arrive(inc, at, '§6§lBANDIT RAID', inc.data.king ? '§7The Bandit King rides with them!' : '§7They have seen you - break the raid!');
      inc.ents = ids;
      inc.until = inc.age + 240;
      return true;
    },
    won(inc, dim, at) {
      const coins = 30 + Math.round(inc.power) * 8;
      for (const q of near(dim, at, 64)) title(q, '§6§lRAID REPELLED', `§7The bandits are beaten §6+${coins} doubloons`, 50);
      reward(dim, at, coins, 1, 80, 'repelled a bandit raid');
    },
    lost(inc, dim, at) {
      for (const q of near(dim, at, 64)) safe(() => q.sendMessage('§6The bandits withdraw with whatever they could carry.'));
    },
    end(inc) {
      news(`A bandit raid sacked the land ${inc.data.where}.`);
      ruins(inc, 'bandits');
      return 'sacked the land';
    },
  },
  devil_ritual: {
    name: 'Devil ritual', mc: '§4', w: 5, f: 'devils', ok: () => night(), life: 300, sign: 'beam', color: '7a0a3a',
    rumor: 'Chanting carries on the wind, and a dark pillar rises',
    spawn(inc, p, at) {
      const dim = p.dimension;
      const ids = [];
      const n = scaled(p, 3);
      for (let i = 0; i < n; i++) {
        const a = (i / n) * Math.PI * 2;
        const e = safe(() => dim.spawnEntity('bc:cultist', V.add(at, { x: Math.cos(a) * 3, y: 0.5, z: Math.sin(a) * 3 })));
        if (e) {
          ids.push(e.id);
          safe(() => e.addTag('bc_event'));
        }
      }
      for (let i = 0; i < 2; i++) safe(() => dim.spawnEntity('bc:imp', V.add(at, { x: rand(-4, 4), y: 1, z: rand(-4, 4) })));
      const left = Math.max(30, Math.round(inc.life - inc.age));
      arrive(inc, at, '§4§lA DEVIL RITUAL', `§7${left}s until it completes - kill the cultists!`);
      inc.ents = ids;
      inc.until = inc.age + left;
      return true;
    },
    live(inc, dim, at) {
      vfx.groundSigil(dim, at, C('8a1010'), 10, 1.4);
      vfx.spawn(dim, 'bc:fx_pillar', at, { color: C('8a1010'), size: 1.2, radius: 1 }, true);
      const left = Math.round((inc.until ?? 0) - inc.age);
      for (const q of near(dim, at, 48)) safe(() => q.onScreenDisplay.setActionBar(`§4Ritual: §f${left}s§4 left - kill the cultists!`));
    },
    won(inc, dim, at) {
      for (const q of near(dim, at, 64)) title(q, '§a§lRITUAL STOPPED', '§7The circle fades', 50);
      reward(dim, at, 0, 1, 150, 'stopped a devil ritual');
      safe(() => dim.spawnItem(new ItemStack('bc:mana_crystal', 4), at));
    },
    lost(inc, dim, at) {
      for (const q of near(dim, at, 64)) title(q, '§4§lTHE RITUAL IS COMPLETE', '§7Something hungry wakes up', 60);
      summonBoss('bc:grimoire_devourer', dim, at, near(dim, at, 64));
    },
    end(inc, dim, at) {
      news(`A devil ritual was completed ${inc.data.where}. Something hungry roams there now.`);
      startIncident('boss', undefined, { at, dim: inc.dim, boss: 'bc:grimoire_devourer', label: 'The Grimoire Devourer', where: inc.data.where });
      return 'completed';
    },
  },
  hive: {
    name: 'Hive infestation', mc: '§e', w: 5, life: 480, sign: 'smoke', color: '8a7a20',
    rumor: 'A swarm buzzes over the trees',
    tick(inc, dt) {
      inc.power = Math.min(12, inc.power + dt / 40);
    },
    spawn(inc, p, at) {
      const dim = p.dimension;
      const ids = [];
      const eggs = Math.min(12, scaled(p, 3) + Math.floor(inc.power));
      for (let i = 0; i < eggs; i++) {
        const egg = layEgg(dim, V.add(at, { x: rand(-6, 6), y: 0.2, z: rand(-6, 6) }), 20 * (50 + Math.floor(Math.random() * 40)));
        if (egg) ids.push(egg.id);
      }
      for (let i = 0; i < scaled(p, 2) + Math.floor(inc.power / 4); i++) safe(() => dim.spawnEntity('bc:hive_drone', V.add(at, { x: rand(-3, 3), y: 0.5, z: rand(-3, 3) })));
      arrive(inc, at, '§e§lHIVE INFESTATION', `§7${eggs} eggs pulse in the grass - smash them!`);
      inc.ents = ids;
      inc.until = inc.age + 120;
      return true;
    },
    won(inc, dim, at) {
      for (const q of near(dim, at, 64)) title(q, '§a§lHIVE DESTROYED', '§7Not a single egg survived', 50);
      reward(dim, at, 40, 1, 120, 'destroyed a hive');
    },
    lost(inc, dim, at) {
      if (inc.power >= 6) summonBoss('bc:hive_queen', dim, at, near(dim, at, 64));
    },
    end(inc, dim, at) {
      news(`A hive ${inc.data.where} has grown a queen.`);
      startIncident('boss', undefined, { at, dim: inc.dim, boss: 'bc:hive_queen', label: 'The Hive Queen', where: inc.data.where });
      return 'grew a queen';
    },
  },
  wounded_knight: {
    name: 'Knight in trouble', mc: '§e', w: 5, life: 360, sign: 'beam', color: 'e0c040',
    rumor: 'A Magic Knight\'s distress flare climbs into the sky',
    spawn(inc, p, at) {
      const dim = p.dimension;
      const k = safe(() => dim.spawnEntity('bc:magic_knight', at));
      if (!k) return false;
      setupKnight(k, { level: 3 + Math.floor(Math.random() * 4), randomRobe: true });
      const frac = Math.max(0.12, 0.4 * (1 - inc.age / inc.life));
      safe(() => {
        const h = k.getComponent('minecraft:health');
        h.setCurrentValue(Math.max(4, h.effectiveMax * frac));
        k.addTag('bc_wounded');
      });
      const ids = [];
      for (let i = 0; i < 3; i++) {
        const f = safe(() => dim.spawnEntity(i === 0 && Math.random() < 0.5 ? 'bc:hellhound' : 'bc:dark_disciple', V.add(at, { x: rand(-6, 6), y: 0.5, z: rand(-6, 6) })));
        if (f) ids.push(f.id);
      }
      inc.data.knight = k.id;
      inc.data.name = safe(() => k.getDynamicProperty('bc:kname')) ?? 'A knight';
      arrive(inc, at, '§e§lA KNIGHT IN TROUBLE', `§7Save ${inc.data.name} from the devils!`);
      inc.ents = ids;
      inc.until = inc.age + 180;
      return true;
    },
    won(inc, dim) {
      const k = world.getEntity(inc.data.knight ?? '');
      const p = near(dim, k?.location ?? { x: inc.x, y: inc.y ?? 64, z: inc.z }, 48)[0];
      if (!k || !alive(k)) return;
      particle(dim, 'bc:heal', k.location, { scale: 1 });
      safe(() => k.removeTag('bc_wounded'));
      if (p && joinParty(k, p, 150)) safe(() => p.sendMessage(`§b${inc.data.name}§f: You saved my life. My grimoire is yours!`));
      else if (p) safe(() => p.sendMessage(`§b${inc.data.name}§f: Thank you, friend!`));
    },
    end(inc) {
      news(`A Magic Knight fell ${inc.data.where}, alone.`);
      shift('knights', -1);
      return 'the knight fell';
    },
  },
  sky_treasure: {
    name: 'Sky treasure', mc: '§e', w: 6, life: 900, sign: 'beam', color: 'ffd36a',
    rumor: 'A golden light falls from the sky',
    spawn(inc, p, at) {
      const dim = p.dimension;
      const blk = { x: Math.floor(at.x), y: Math.floor(at.y), z: Math.floor(at.z) };
      const b = safe(() => dim.getBlock(blk));
      if (!b) return false;
      safe(() => b.setType('minecraft:chest'));
      const inv = safe(() => b.getComponent('minecraft:inventory')?.container);
      const loot = [new ItemStack('bc:doubloon', 20 + Math.floor(Math.random() * 40)), new ItemStack('bc:mana_crystal', 3 + Math.floor(Math.random() * 4)),
        new ItemStack('bc:ancient_page', 1 + Math.floor(Math.random() * 2)), new ItemStack('minecraft:diamond', 1 + Math.floor(Math.random() * 3))];
      if (Math.random() < 0.15) loot.push(new ItemStack(`bc:fruit_${pick(DATA.fruitOrder)}`, 1));
      if (Math.random() < 0.3) loot.push(new ItemStack(pick(['bc:knight_contract', 'bc:treasure_map', 'bc:spell_scroll', 'bc:rune_shard']), 1));
      loot.forEach((it, i) => safe(() => inv?.setItem(i * 3 + 1, it)));
      vfx.impact(dim, V.add(blk, { x: 0.5, y: 1, z: 0.5 }), 'gold', C('ffd36a'), 1.4);
      for (let i = 0; i < 3; i++) safe(() => dim.spawnEntity('bc:sea_raider', V.add(blk, { x: rand(-6, 6), y: 1, z: rand(-6, 6) })));
      arrive(inc, at, '§e§lSKY TREASURE', '§7Pirates got here first - take it from them!');
      return 'found';
    },
    end(inc) {
      news(`Pirates carried off a fallen treasure ${inc.data.where}.`);
      shift('raiders', 1);
      return 'taken by pirates';
    },
  },
  merchant_camp: {
    name: 'Travelling merchant', mc: '§b', w: 6, life: 600, sign: 'smoke', color: 'c0b080',
    rumor: 'A merchant\'s campfire smokes on the horizon',
    spawn(inc, p, at) {
      spawnMerchant(p.dimension, at, Math.max(2, Math.round((inc.life - inc.age) / 60)));
      arrive(inc, at, '§b§lA MERCHANT\'S CAMP', '§7Rare wares, while they last');
      return 'visited';
    },
    end() {
      return 'moved on';
    },
  },
  meteor_shower: {
    name: 'Meteor shower', mc: '§b', w: 7, life: 300, sign: 'beam', color: '9ae8ff',
    rumor: 'Shooting stars are falling',
    spawn(inc, p, at) {
      arrive(inc, at, '§b§lMANA METEOR SHOWER', '§7Catch the mana crystals the stars leave behind!');
      inc.until = inc.age + Math.max(60, inc.life - inc.age);
      inc.ents = [];
      return true;
    },
    live(inc, dim, at) {
      const owner = near(dim, at, 80)[0];
      if (!owner) return;
      for (let i = 0; i < 2; i++) {
        const a = Math.random() * Math.PI * 2;
        const r = rand(4, 22);
        const target = { x: at.x + Math.cos(a) * r, y: at.y, z: at.z + Math.sin(a) * r };
        const g = groundAt(dim, target.x, target.z);
        if (g) target.y = g.y;
        const from = V.add(target, { x: rand(-10, 10), y: 30, z: rand(-10, 10) });
        boltFrom(owner, 'a:star', { t: 'bolt', d: 6, aoe: 2.5, shape: 0, size: 2, fx: 'star' }, from, V.sub(target, from), 1.6, { drop: 'bc:mana_crystal', pw: 1 });
      }
    },
    end() {
      return 'the stars stopped falling';
    },
  },
  tournament: {
    name: 'Knights\' tournament', mc: '§a', w: 4, ok: () => !night(), life: 420, sign: 'beam', color: '60e070',
    rumor: 'Banners and cheers - Magic Knights are holding a tournament',
    spawn(inc, p, at) {
      const attrs = DATA.order.filter((a) => a !== 'anti');
      const level = 3 + Math.floor(Math.random() * 6);
      arrive(inc, at, '§a§lA KNIGHTS\' TOURNAMENT', '§7Two Magic Knights cross grimoires');
      startBattle({ dim: p.dimension, center: at, facing: V.flat(V.sub(at, p.location)), fa: 'knights', fb: 'knights', size: 1, duel: true,
        roster: { a: [{ type: 'bc:magic_knight', attr: pick(attrs), level }], b: [{ type: 'bc:magic_knight', attr: pick(attrs), level }] } });
      return 'watched';
    },
    end() {
      return 'over';
    },
  },
  patrol: {
    name: 'Knight patrol', mc: '§a', w: 5, f: 'knights', ok: () => !night(), life: 420, sign: 'smoke', color: 'a0a0a0', moving: 0.6, far: [100, 150], cross: true,
    rumor: 'A Magic Knight patrol is passing through',
    spawn(inc, p, at) {
      for (let i = 0; i < 3; i++) {
        const e = safe(() => p.dimension.spawnEntity('bc:magic_knight', V.add(at, { x: rand(-2, 2), y: 0.5, z: rand(-2, 2) })));
        if (e) setupKnight(e, {});
      }
      safe(() => p.sendMessage('§a♣ You meet a patrol of Magic Knights.'));
      return 'met';
    },
    end() {
      return 'passed by';
    },
  },
  pirates: {
    name: 'Pirate landing', mc: '§c', w: 6, f: 'raiders', life: 480, sign: 'smoke', color: '402020', water: true,
    rumor: 'A ship\'s bell rings - pirates are coming ashore',
    spawn(inc, p, at) {
      const land = groundAt(p.dimension, at.x, at.z);
      const spot = land && !land.liquid ? { x: at.x, y: land.y, z: at.z } : at;
      spawnCaptain(p.dimension, spot, {});
      for (let i = 0; i < scaled(p, 4); i++) safe(() => p.dimension.spawnEntity('bc:sea_raider', V.add(spot, { x: rand(-3, 3), y: 0.5, z: rand(-3, 3) })));
      sound(p.dimension, 'bc.ship.bell', spot, 2, 0.8);
      arrive(inc, spot, '§c§lPIRATES HAVE LANDED', '§7A raiding party comes ashore');
      return 'fought';
    },
    end(inc) {
      shift('raiders', 2);
      news(`Pirates raided the coast ${inc.data.where}.`);
      return 'raided the coast';
    },
  },
  // a boss abroad: it appears when you get there
  boss: {
    name: 'Something terrible', mc: '§4', w: 0, life: 600, sign: 'beam', color: 'ff3030',
    rumor: 'Something terrible stirs',
    spawn(inc, p, at) {
      summonBoss(inc.data.boss, p.dimension, at, [p]);
      arrive(inc, at, `§4§l${inc.label.toUpperCase()}`, '§7It has found you');
      return 'confronted';
    },
    end(inc) {
      news(`${inc.label} roams ${inc.data.where}... then moves on.`);
      return 'moved on';
    },
  },
  // ---------------------------------------------------------------- new in v1.0.0
  caravan: {
    name: 'Merchant caravan', mc: '§b', w: 5, ok: () => !night(), life: 600, sign: 'smoke', color: 'b09060', moving: 0.5, far: [100, 150], cross: true,
    rumor: 'A merchant caravan is on the road',
    spawn(inc, p, at) {
      const dim = p.dimension;
      const m = spawnMerchant(dim, at, 4);
      const ids = [];
      for (let i = 0; i < 2; i++) {
        const k = safe(() => dim.spawnEntity('bc:magic_knight', V.add(at, { x: rand(-3, 3), y: 0.5, z: rand(-3, 3) })));
        if (k) setupKnight(k, { level: 2 + Math.floor(Math.random() * 3) });
      }
      if (Math.random() < 0.5) {
        const side = V.add(at, V.mul(V.norm({ x: rand(-1, 1), y: 0, z: rand(-1, 1) }), 14));
        for (let i = 0; i < scaled(p, 3); i++) {
          const e = safe(() => dim.spawnEntity(i ? 'bc:bandit' : 'bc:bandit_archer', V.add(side, { x: rand(-2, 2), y: 0.5, z: rand(-2, 2) })));
          if (e) {
            ids.push(e.id);
            safe(() => e.addTag('bc_event'));
          }
        }
        arrive(inc, at, '§b§lAN AMBUSHED CARAVAN', '§7Bandits strike the caravan - protect it!');
        inc.ents = ids;
        inc.until = inc.age + 120;
        inc.data.merchant = m?.id;
        return true;
      }
      arrive(inc, at, '§b§lA MERCHANT CARAVAN', '§7Trade with them before they move on');
      return 'met';
    },
    won(inc, dim, at) {
      const m = world.getEntity(inc.data.merchant ?? '');
      if (m && alive(m)) {
        for (const q of near(dim, at, 64)) title(q, '§b§lCARAVAN SAVED', '§7The merchant pays you for the escort §6+60 doubloons', 50);
        reward(dim, at, 60, 1, 60, 'saved a caravan');
      }
    },
    end(inc) {
      news(`A merchant caravan crossed the land ${inc.data.where} safely.`);
      return 'arrived safely';
    },
  },
  mana_spring: {
    name: 'Mana spring', mc: '§b', w: 5, life: 360, sign: 'beam', color: '50c8ff',
    rumor: 'A geyser of raw mana erupts',
    spawn(inc, p, at) {
      arrive(inc, at, '§b§lA MANA SPRING', '§7Stand in the geyser to drink in its mana');
      inc.until = inc.age + Math.max(90, inc.life - inc.age);
      inc.ents = [];
      return true;
    },
    live(inc, dim, at) {
      vfx.pillar(dim, at, C('50c8ff'), 8, 1.3);
      vfx.spawn(dim, 'bc:fx_mist', V.add(at, { x: 0, y: 1, z: 0 }), { color: C('50c8ff'), scale: 1.5 }, true);
      for (const q of near(dim, at, 3.5)) {
        addMana(q, 25);
        safe(() => q.onScreenDisplay.setActionBar('§bThe spring floods you with mana!'));
      }
      if (Math.random() < 0.35) safe(() => dim.spawnItem(new ItemStack('bc:mana_crystal', 1), V.add(at, { x: rand(-2, 2), y: 1.5, z: rand(-2, 2) })));
    },
    end() {
      return 'ran dry';
    },
  },
  camp_siege: {
    name: 'Camp under siege', mc: '§c', w: 4, life: 420, sign: 'smoke', color: '402018',
    rumor: 'A Magic Knight camp is under attack - signal fires burn',
    init(inc) {
      inc.data.foe = pick(['devils', 'bandits', 'rogues']);
    },
    spawn(inc, p, at) {
      const dim = p.dimension;
      for (let i = 0; i < 3; i++) {
        const k = safe(() => dim.spawnEntity('bc:magic_knight', V.add(at, { x: rand(-3, 3), y: 0.5, z: rand(-3, 3) })));
        if (k) setupKnight(k, { level: 3 + Math.floor(Math.random() * 4) });
      }
      const types = { devils: ['bc:imp', 'bc:dark_disciple', 'bc:hellhound'], bandits: ['bc:bandit', 'bc:bandit_archer', 'bc:bandit'], rogues: ['bc:rogue_mage'] }[inc.data.foe];
      const ids = [];
      const off = V.add(at, V.mul(V.norm(V.flat(V.sub(at, p.location))), 9));
      for (let i = 0; i < scaled(p, 5); i++) {
        const e = safe(() => dim.spawnEntity(types[i % types.length], V.add(off, { x: rand(-3, 3), y: 0.5, z: rand(-3, 3) })));
        if (!e) continue;
        if (e.typeId === 'bc:rogue_mage') setupRogue(e, { level: 3 + Math.floor(Math.random() * 4) });
        ids.push(e.id);
        safe(() => e.addTag('bc_event'));
      }
      arrive(inc, at, '§c§lA CAMP UNDER SIEGE', '§7Help the knights hold the line!');
      inc.ents = ids;
      inc.until = inc.age + 200;
      return true;
    },
    won(inc, dim, at) {
      for (const q of near(dim, at, 64)) title(q, '§a§lTHE CAMP HOLDS', '§7The knights salute you', 50);
      reward(dim, at, 50, 2, 120, 'defended a knight camp');
      shift('knights', 2);
    },
    end(inc) {
      shift('knights', -3);
      news(`A Magic Knight camp ${inc.data.where} was overrun.`);
      ruins(inc, inc.data.foe);
      return 'overrun';
    },
  },
  refugees: {
    name: 'Refugees', mc: '§f', w: 3, life: 360, sign: 'smoke', color: '909090', moving: 0.45, far: [90, 130],
    rumor: 'Refugees are fleeing something',
    init(inc, p) {
      inc.dest = { x: p.location.x + rand(-8, 8), z: p.location.z + rand(-8, 8) };
      // they flee a gate further out, the way they came
      const back = V.norm(V.flat({ x: inc.x - p.location.x, y: 0, z: inc.z - p.location.z }));
      inc.data.gate = startIncident('devil_gate', undefined, { at: { x: inc.x + back.x * 80, y: null, z: inc.z + back.z * 80 }, dim: inc.dim, quiet: true })?.id;
    },
    spawn(inc, p, at) {
      for (let i = 0; i < 3; i++) safe(() => p.dimension.spawnEntity('minecraft:villager_v2', V.add(at, { x: rand(-2, 2), y: 0.5, z: rand(-2, 2) })));
      const gate = all().find((x) => x.id === inc.data.gate && !x.done);
      const where = gate ? `${compass(at, gate)}, about ${Math.round(flatDist(at, gate))} blocks` : 'somewhere behind them';
      safe(() => p.sendMessage(`§fA villager§7: Devils! A gate opened ${where} - run!`));
      if (gate) track(p, gate.id);
      reward(p.dimension, at, 0, 0, 40, '');
      return 'met';
    },
    end() {
      return 'found shelter';
    },
  },
  ruins: {
    name: 'Ruins', mc: '§7', w: 0, life: 1200, sign: 'smoke', color: '303030',
    rumor: 'Smoke rises from fresh ruins',
    spawn(inc, p, at) {
      const dim = p.dimension;
      const blk = { x: Math.floor(at.x), y: Math.floor(at.y), z: Math.floor(at.z) };
      safe(() => dim.getBlock(blk)?.setType('minecraft:chest'));
      const inv = safe(() => dim.getBlock(blk)?.getComponent('minecraft:inventory')?.container);
      const loot = [new ItemStack('bc:doubloon', 15 + Math.floor(Math.random() * 30)), new ItemStack('bc:mana_crystal', 2 + Math.floor(Math.random() * 3))];
      if (Math.random() < 0.5) loot.push(new ItemStack(pick(['bc:devil_hide', 'bc:shadow_silk', 'bc:rune_shard', 'bc:arcane_thread', 'bc:spell_scroll']), 1 + Math.floor(Math.random() * 2)));
      loot.forEach((it, i) => safe(() => inv?.setItem(i * 4 + 2, it)));
      vfx.spawn(dim, 'bc:fx_smoke', V.add(at, { x: 0, y: 1, z: 0 }), { scale: 2 });
      const types = { devils: ['bc:imp', 'bc:dark_disciple'], bandits: ['bc:bandit', 'bc:bandit_archer'], rogues: ['bc:rogue_mage'] }[inc.data.foe ?? 'bandits'] ?? ['bc:bandit'];
      for (let i = 0; i < 3; i++) {
        const e = safe(() => dim.spawnEntity(types[i % types.length], V.add(at, { x: rand(-6, 6), y: 0.5, z: rand(-6, 6) })));
        if (e?.typeId === 'bc:rogue_mage') setupRogue(e, { level: 3 });
      }
      arrive(inc, at, '§7§lRUINS', '§7Something is left to salvage - and someone is guarding it');
      return 'searched';
    },
    end() {
      return 'scavenged';
    },
  },
};
// the giant bosses walk the world too (by night, day or sea)
/** @type {[string, string, () => boolean, string][]} */
const BOSSES = [
  ['bc:fallen_captain', 'The Fallen Captain', () => night(), 'Something in a Magic Knight\'s robe walks in the dark'],
  ['bc:soul_puppeteer', 'The Soul Puppeteer', () => night(), 'A music box plays somewhere out there'],
  ['twins', 'The Witch Sisters', () => night(), 'Two witches laugh on the night wind'],
  ['bc:bone_dragon', 'The Bone Dragon', () => night(), 'Bones rattle in the sky'],
  ['bc:stone_colossus', 'A Stone Colossus', () => !night(), 'The ground trembles - something enormous is waking'],
  ['bc:phantom_galleon', 'The Phantom Galleon', () => night(), 'A ghostly fog rolls in, and a ship\'s bell rings in the sky'],
];
for (const [boss, label, ok, rumor] of BOSSES) {
  KINDS[`boss_${boss.replace('bc:', '')}`] = { ...KINDS.boss, w: 2, ok, rumor, init(inc) {
    inc.data.boss = boss;
    inc.label = label;
  } };
}
KINDS.boss_kraken = { ...KINDS.boss, w: 2, water: true, rumor: 'The sea darkens and thunder rolls over the water', init(inc) {
  inc.data.boss = 'bc:storm_kraken';
  inc.label = 'The Storm Kraken';
} };
export { KINDS };

// ------------------------------------------------------------------------------- starting incidents
let seq = 0;
/**
 * Start an incident near a player (out of sight), or at a given place.
 * @param {string} kind @param {Player | undefined} p @param {{at?: any, dim?: string, boss?: string, label?: string, quiet?: boolean, near?: boolean, where?: string}} [opts]
 */
export function startIncident(kind, p, opts = {}) {
  const K = KINDS[kind];
  if (!K) return undefined;
  if (incidents().length >= MAX_ACTIVE && !opts.at) return undefined;
  let at = opts.at;
  if (!at && p) {
    const [lo, hi] = opts.near ? [56, 64] : K.far ?? [60, 200];
    at = placeFar(p, lo, hi, !!K.water);
  }
  if (!at) return undefined;
  /** @type {Incident} */
  const inc = { id: `i${Date.now().toString(36)}${(seq++).toString(36)}`, kind, dim: opts.dim ?? p?.dimension.id ?? 'minecraft:overworld',
    x: at.x, y: at.y ?? null, z: at.z, age: 0, life: K.life, power: 0, mat: false, ents: [], data: {}, label: opts.label ?? K.name };
  if (opts.boss) inc.data.boss = opts.boss;
  if (K.moving) {
    inc.speed = K.moving;
    if (K.cross && p) inc.dest = { x: p.location.x * 2 - at.x + rand(-10, 10), z: p.location.z * 2 - at.z + rand(-10, 10) };
  }
  safe(() => K.init?.(inc, p));
  inc.data.where = opts.where ?? (p ? `${compass(p.location, inc)} of ${landmark(p)}` : 'in the wilds');
  all().push(inc);
  save();
  logEvent(`${inc.label} (${p ? compass(p.location, inc) : 'far away'})`, 'under way');
  if (!opts.quiet) rumor(inc);
  return inc;
}
function landmark(p) {
  const sp = safe(() => p.getSpawnPoint?.());
  return sp && flatDist(sp, p.location) < 120 ? 'your home' : 'where you were';
}

/** Tell everyone close enough to hear about it - by direction and distance. */
function rumor(inc) {
  const K = KINDS[inc.kind];
  const dim = dimOf(inc.dim);
  if (!dim) return;
  for (const q of world.getAllPlayers()) {
    if (q.dimension.id !== inc.dim) continue;
    const d = flatDist(q.location, inc);
    if (d > HEAR_R) continue;
    safe(() => q.sendMessage(`${K.mc}⚑ ${K.rumor}§7 - to the §f${compass(q.location, inc)}§7, about §f${Math.round(d / 10) * 10}§7 blocks away. §8(${tracked.get(q.id) ? 'Track it from the Handbook' : 'Tracking it on your HUD'})`));
    // a sound from that direction
    const dir = V.norm(V.flat({ x: inc.x - q.location.x, y: 0, z: inc.z - q.location.z }));
    const cue = { beam: 'bc.gong', smoke: 'bc.horn' }[K.sign] ?? 'bc.gong';
    sound(q.dimension, cue, V.add(q.location, V.mul(dir, 14)), 0.6, 0.7);
    if (!tracked.get(q.id) || !all().some((x) => x.id === tracked.get(q.id) && !x.done)) tracked.set(q.id, inc.id);
  }
}

// ------------------------------------------------------------------------------- tracking (HUD compass)
/** @type {Map<string, string>} player id -> incident id */
const tracked = new Map();
export function track(p, id) {
  tracked.set(p.id, id);
}
export function trackedBy(p) {
  return tracked.get(p.id);
}
setCompassProvider((p) => {
  const id = tracked.get(p.id);
  if (!id) return undefined;
  const inc = all().find((x) => x.id === id && !x.done);
  if (!inc) {
    tracked.delete(p.id);
    return undefined;
  }
  if (inc.dim !== p.dimension.id) return undefined;
  const dx = inc.x - p.location.x;
  const dz = inc.z - p.location.z;
  const dist = Math.round(Math.hypot(dx, dz));
  if (dist < 24) return undefined;
  const rel = ((yawOf({ x: dx, y: 0, z: dz }) - yawOf(p.getViewDirection()) + 540) % 360) - 180;
  const arrow = DATA.glyphs.arrows[((Math.round(rel / 45) % 8) + 8) % 8];
  const K = KINDS[inc.kind];
  return `${arrow} ${K.mc}${inc.label} §7${dist}m ${stateText(inc)}`;
});
function stateText(inc) {
  const left = Math.max(0, Math.round(inc.life - inc.age));
  const t = left > 90 ? `${Math.round(left / 60)} min` : `${left}s`;
  if (inc.kind === 'devil_gate') return `§8(gate strength ${Math.floor(inc.power)}/10, erupts in ${t})`;
  if (inc.kind === 'skirmish') return `§8(${Math.round(inc.data.sa)} vs ${Math.round(inc.data.sb)})`;
  if (inc.kind === 'hive') return `§8(${3 + Math.floor(inc.power)} eggs, a queen in ${t})`;
  if (inc.kind === 'devil_ritual') return `§8(completes in ${t})`;
  if (inc.kind === 'wounded_knight') return `§8(bleeding out: ${t})`;
  if (inc.dest) return `§8(on the move)`;
  return `§8(${t} left)`;
}

// ------------------------------------------------------------------------------- the simulation
function near(dim, at, r) {
  return safe(() => dim.getPlayers({ location: at, maxDistance: r })) ?? [];
}
function arrive(inc, at, main, sub) {
  const dim = dimOf(inc.dim);
  for (const q of near(dim, at, 96)) title(q, main, sub, 50);
  emit('incident', inc.kind, at);
}
function ruins(inc, foe) {
  const r = startIncident('ruins', undefined, { at: { x: inc.x, y: inc.y, z: inc.z }, dim: inc.dim, quiet: true, where: inc.data.where });
  if (r) r.data.foe = foe;
}
function finish(inc, outcome) {
  inc.done = outcome;
  setOutcome(`${inc.label} (`, outcome, true);
  for (const [pid, id] of tracked) if (id === inc.id) tracked.delete(pid);
}

/** Make an incident real: a player is close, the place is loaded. */
function materialize(inc, p) {
  const K = KINDS[inc.kind];
  const g = groundAt(p.dimension, inc.x, inc.z);
  if (!g) return;
  const at = { x: inc.x, y: K.water && g.liquid ? g.y : g.y, z: inc.z };
  inc.y = at.y;
  const r = safe(() => K.spawn(inc, p, at), `incident:${inc.kind}`);
  if (r === false || r === undefined) {
    finish(inc, 'gone');
    return;
  }
  inc.mat = true;
  if (r !== true) {
    // a one-off: it happened in front of whoever came
    finish(inc, r);
    for (const q of near(p.dimension, at, 64)) emit('event_win', q, inc.kind);
  }
}

/** Everyone left: the incident fades back into the simulation (its survivors are remembered). */
function dematerialize(inc) {
  let n = 0;
  for (const id of inc.ents) {
    const e = world.getEntity(id);
    if (e && alive(e)) {
      n++;
      safe(() => e.remove());
    }
  }
  if (inc.kind === 'bandit_raid' || inc.kind === 'camp_siege') inc.power = n;
  inc.ents = [];
  inc.mat = false;
}

function step(dt) {
  const list = all();
  for (const inc of list) {
    if (inc.done) continue;
    const K = KINDS[inc.kind];
    const dim = dimOf(inc.dim);
    if (!K || !dim) {
      inc.done = 'gone';
      continue;
    }
    inc.age += dt;
    const at = { x: inc.x, y: inc.y ?? 64, z: inc.z };
    if (!inc.mat) {
      // the simulation
      safe(() => K.tick?.(inc, dt), `incTick:${inc.kind}`);
      if (inc.dest && inc.speed) {
        const d = flatDist(inc, inc.dest);
        const stepLen = Math.min(d, inc.speed * dt);
        if (d > 1) {
          inc.x += ((inc.dest.x - inc.x) / d) * stepLen;
          inc.z += ((inc.dest.z - inc.z) / d) * stepLen;
          inc.y = null;
        } else if (inc.kind === 'bandit_raid' || inc.kind === 'refugees') inc.life = inc.age;
      }
      if (inc.age >= inc.life) {
        const out = safe(() => K.end?.(inc, dim, at), `incEnd:${inc.kind}`) ?? 'over';
        finish(inc, out);
      }
      continue;
    }
    // it is real: watch it play out
    safe(() => K.live?.(inc, dim, at), `incLive:${inc.kind}`);
    if (inc.ents.length) {
      const left = inc.ents.filter((id) => {
        const e = world.getEntity(id);
        return e && alive(e);
      });
      if (!left.length) {
        safe(() => K.won?.(inc, dim, at));
        for (const q of near(dim, at, 64)) emit('event_win', q, inc.kind);
        finish(inc, 'success');
        continue;
      }
    }
    if (inc.until !== undefined && inc.age >= inc.until) {
      if (inc.ents.length) safe(() => K.lost?.(inc, dim, at));
      finish(inc, inc.ents.length ? 'failed' : 'over');
      continue;
    }
    const someone = world.getAllPlayers().some((q) => q.dimension.id === inc.dim && flatDist(q.location, inc) < UNMAT_R);
    inc.away = someone ? 0 : (inc.away ?? 0) + dt;
    if (inc.away >= 60) dematerialize(inc);
  }
  cache = list.filter((i) => !i.done);
  save();
}
system.runInterval(() => safe(() => step(CYCLE), 'world'), 20 * CYCLE);

// arrivals and signs are checked more often
system.runInterval(() => safe(() => {
  const players = world.getAllPlayers();
  for (const inc of incidents()) {
    if (inc.mat) continue;
    const p = players.find((q) => q.dimension.id === inc.dim && flatDist(q.location, inc) <= MAT_R);
    if (p) materialize(inc, p);
  }
}, 'worldArrive'), 20);
system.runInterval(() => safe(signs, 'worldSigns'), 40);

/** Signs on the horizon: smoke columns and pillars of light that show where each incident is. */
function signs() {
  for (const q of world.getAllPlayers()) {
    for (const inc of incidents()) {
      if (inc.dim !== q.dimension.id) continue;
      const K = KINDS[inc.kind];
      const d = flatDist(q.location, inc);
      if (d > HEAR_R || (inc.mat && d < 40)) continue;
      const dir = V.norm({ x: inc.x - q.location.x, y: 0, z: inc.z - q.location.z });
      const at = d <= 72 ? { x: inc.x, y: (inc.y ?? q.location.y) + 2, z: inc.z } : V.add(q.location, { x: dir.x * 64, y: 4 + Math.min(20, (d - 72) / 10), z: dir.z * 64 });
      vfx.spawn(q.dimension, K.sign === 'beam' ? 'bc:fx_signal_beam' : 'bc:fx_signal_smoke', at, { color: C(K.color) }, true);
    }
  }
}

// ------------------------------------------------------------------------------- the director
const PERSONAL = ['thief', 'assassins', 'bounty_hunters', 'rogue_ambush', 'rival_squad', 'crimson_night', 'mana_storm', 'mana_eclipse'];
/** Pick something to happen around a player: usually an incident out in the world, sometimes something that comes for them. */
export function direct(p) {
  if (Math.random() < 0.3) {
    const pool = PERSONAL.filter((k) => EVENTS[k] && (!EVENTS[k].ok || EVENTS[k].ok(p)));
    if (pool.length && runEvent(p, pick(pool))) return true;
  }
  const kinds = Object.entries(KINDS).filter(([k, K]) => K.w > 0 && (!K.ok || K.ok(p)) && !incidents().some((i) => i.kind === k));
  const weight = ([, K]) => K.w * (K.f && POWERS.includes(K.f) ? powerMul(K.f) : 1);
  let r = Math.random() * kinds.reduce((s, e) => s + weight(e), 0);
  for (const e of kinds) {
    r -= weight(e);
    if (r <= 0) return !!startIncident(e[0], p);
  }
  return false;
}

let nextAt = 20 * 60 * 2;
system.runInterval(() => {
  const t = system.currentTick;
  if (t < nextAt || !eventsOn()) return;
  const players = world.getAllPlayers().filter((p) => p.dimension.id === 'minecraft:overworld');
  if (!players.length) return;
  if (direct(pick(players))) nextAt = t + Math.round(rand(20 * 60 * 3, 20 * 60 * 6));
  else nextAt = t + 20 * 30;
}, 100);

// a dominant faction's offensive is a great battle somewhere out there
onOffensive((attacker, defender) => {
  const players = world.getAllPlayers().filter((p) => p.dimension.id === 'minecraft:overworld');
  if (!players.length) return false;
  const inc = startIncident('skirmish', pick(players));
  if (!inc) return false;
  inc.data.fa = attacker;
  inc.data.fb = defender;
  inc.data.sa = 8 + Math.floor(Math.random() * 3);
  inc.data.sb = 6 + Math.floor(Math.random() * 3);
  inc.label = `${DATA.factions[attacker].name}' offensive`;
  inc.life = 420;
  save();
  return true;
});

// cheats: /scriptevent bc:incident [kind] - an incident out in the world (add "near" to place it just out of sight)
system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (ev.id !== 'bc:incident') return;
  const p = ev.sourceEntity instanceof Player ? ev.sourceEntity : world.getAllPlayers()[0];
  if (!p) return;
  const [kind, flag] = ev.message.trim().split(/\s+/);
  if (kind && !KINDS[kind]) {
    safe(() => p.sendMessage(`§7Incidents: ${Object.keys(KINDS).filter((k) => KINDS[k].w > 0).join(', ')}`));
    return;
  }
  const inc = kind ? startIncident(kind, p, { near: flag === 'near' }) : (direct(p), undefined);
  if (kind && !inc) safe(() => p.sendMessage('§7No room for that here (or too many incidents are already under way).'));
});

// ------------------------------------------------------------------------------- the Handbook page
/** World events: what is happening out there (nearest first), which one you are tracking, and what happened lately. */
export async function worldPage(p, back) {
  const list = incidents().filter((i) => i.dim === p.dimension.id).sort((a, b) => flatDist(p.location, a) - flatDist(p.location, b));
  const mine = tracked.get(p.id);
  const body = list.length
    ? `§7Out in the world right now (nearest first). Choose one to track it on your HUD.\n\n${list.map((i) => `${KINDS[i.kind].mc}${i.label}§7 - §f${compass(p.location, i)}, ${Math.round(flatDist(p.location, i))}m §8${stateText(i)}${i.id === mine ? ' §e(tracking)' : ''}`).join('\n')}`
    : '§7All quiet for now. Something happens out in the world every few minutes - you will hear about it, and see its sign on the horizon.';
  const f = new ActionFormData().title('World events').body(`${body}\n\n§8Left alone, incidents play out without you - gates erupt, raids sack the land, armies decide their battles.`);
  for (const i of list) f.button(`${KINDS[i.kind].mc}§l${i.label}\n§r§8${compass(p.location, i)}, ${Math.round(flatDist(p.location, i))}m - ${i.id === mine ? 'tracking' : 'track it'}`);
  f.button('§lRecent events\n§r§8What happened, and how it ended');
  f.button(back ? '§8Back' : '§8Close');
  const r = await f.show(p);
  if (r.canceled || r.selection === undefined) return;
  if (r.selection < list.length) {
    track(p, list[r.selection].id);
    safe(() => p.sendMessage(`§7Now tracking: ${KINDS[list[r.selection].kind].mc}${list[r.selection].label}§7 (follow the arrow on your HUD).`));
    return;
  }
  if (r.selection === list.length) {
    const log = eventLog();
    const col = { success: '§a', failed: '§c', 'under way': '§e', happened: '§7' };
    const txt = log.length ? log.map((e) => `§8Day ${e.day} §f${e.label}§8 - ${col[e.outcome] ?? '§7'}${e.outcome}`).join('\n') : '§7Nothing yet.';
    const m = await new MessageFormData().title('Recent events').body(txt).button1('Back').button2('Close').show(p);
    if (m.selection === 0) return worldPage(p, back);
    return;
  }
  if (back) await back();
}

export { compass as directionWord, stateText };
