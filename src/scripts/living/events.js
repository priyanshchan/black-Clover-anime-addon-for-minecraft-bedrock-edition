// Random world events: every few minutes something happens near a player - meteor showers, devil gates,
// bandit raids, devil rituals, hive infestations, assassins, thieves, a Mana Eclipse,
// pirate landings, faction skirmishes, a travelling merchant, sky treasure, a crimson night, a Rogue Mage ambush,
// a rival squad's challenge, or a giant boss (the Witch Sisters, the Bone Dragon and the Soul Puppeteer walk at night).
// Toggle them at a War Table, or trigger one with:  /scriptevent bc:event <name>
//
// The EVENT DIRECTOR (v0.7.0): events scale with the player's level and party (more enemies, nastier leaders), never
// repeat the last two events, come sooner after quiet stretches and later after hard fights, and many of them have an
// OBJECTIVE (break the raid, stop the ritual, smash the eggs) with a reward - or a consequence. Every event is written
// to a log you can read in the Handbook.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { center } from '../core/combat.js';
import { particle, rgb, shakeArea, sound, title } from '../core/fx.js';
import { addXp } from '../core/progress.js';
import { addStars } from '../core/ranks.js';
import { V, alive, pick, rand, repeat, safe, timer } from '../core/util.js';
import { spawnCaptain } from '../sea/captains.js';
import { TACTICS, startBattle } from './battle.js';
import { POWERS, RIVAL, onOffensive, powerMul } from './worldsim.js';
import { summonBoss } from './bosses.js';
import { boltFrom } from './engine.js';
import { setupKnight } from './knights.js';
import { setupRogue } from './rogues.js';
import { emit } from '../core/bus.js';
import { startRivalMatch } from './rivals.js';
import { partySize } from './companions.js';
import { spawnMerchant } from './merchant.js';
import { joinParty } from './companions.js';
import { addMana } from '../core/data.js';
import { hurt, targetsAround } from '../core/combat.js';
import { notoriety } from '../sea/navy.js';
import { eclipseMul, state } from '../core/data.js';
import { layEgg } from './foes.js';
import { giveCoins } from '../sea/bounty.js';

const night = () => {
  const t = world.getTimeOfDay();
  return t > 13000 && t < 23000;
};

export function eventsOn() {
  return world.getDynamicProperty('bc:events') !== 'off';
}
export function setEvents(on) {
  world.setDynamicProperty('bc:events', on ? 'on' : 'off');
}

function announce(p, main, sub, msg) {
  for (const q of p.dimension.getPlayers({ location: p.location, maxDistance: 96 })) {
    title(q, main, sub, 60);
    if (msg) safe(() => q.sendMessage(msg));
  }
  sound(p.dimension, 'bc.gong', p.location, 1.2, 1);
}

/** Solid, dry ground about `dist` blocks from a player (random direction). */
function spotNear(p, dist, tries = 8) {
  for (let i = 0; i < tries; i++) {
    const a = Math.random() * Math.PI * 2;
    const x = p.location.x + Math.cos(a) * dist;
    const z = p.location.z + Math.sin(a) * dist;
    const top = safe(() => p.dimension.getTopmostBlock({ x, z }));
    if (!top || top.isLiquid || top.typeId.endsWith('leaves')) continue;
    const y = top.location.y + 1;
    if (Math.abs(y - p.location.y) > 12) continue;
    return { x, y, z };
  }
  return undefined;
}

function waterNear(p, dist) {
  for (let i = 0; i < 10; i++) {
    const a = Math.random() * Math.PI * 2;
    const x = p.location.x + Math.cos(a) * dist;
    const z = p.location.z + Math.sin(a) * dist;
    const top = safe(() => p.dimension.getTopmostBlock({ x, z }));
    if (top?.typeId !== 'minecraft:water') continue;
    const deep = safe(() => p.dimension.getBlock({ x, y: top.location.y - 4, z }));
    if (deep?.typeId === 'minecraft:water') return { x, y: top.location.y - 2, z };
  }
  return undefined;
}

// ------------------------------------------------------------------------------- the director
/** How tough this player's events should be: 1 (new), 2 (seasoned), 3 (veteran). */
export function tier(p) {
  const lv = safe(() => state(p).level) ?? 1;
  const pals = safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 32, type: 'bc:magic_knight' })
    .filter((e) => e.getDynamicProperty('bc:owner') === p.id).length) ?? 0;
  const score = lv + pals * 3;
  return score >= 16 ? 3 : score >= 7 ? 2 : 1;
}
/** Scale an enemy count by tier. */
function scaled(p, base) {
  return Math.round(base * [1, 1, 1.4, 1.8][tier(p)]);
}

/** The event log (newest first), shown in the Handbook. */
export function eventLog() {
  const v = world.getDynamicProperty('bc:event_log');
  try {
    return typeof v === 'string' ? JSON.parse(v) : [];
  } catch {
    return [];
  }
}
function logEvent(label, outcome) {
  const log = eventLog();
  log.unshift({ label, outcome, day: world.getDay() });
  safe(() => world.setDynamicProperty('bc:event_log', JSON.stringify(log.slice(0, 12))));
}
function setOutcome(label, outcome) {
  const log = eventLog();
  const e = log.find((x) => x.label === label && x.outcome === 'under way');
  if (e) e.outcome = outcome;
  safe(() => world.setDynamicProperty('bc:event_log', JSON.stringify(log)));
}

/** @type {{label: string, ids: string[], until: number, dim: any, at: any, success: () => void, fail: () => void, warn?: (left: number) => void}[]} */
const objectives = [];
/** Track an event with an objective: everyone in `ids` must fall before `ticks` run out. */
function objective(label, ids, ticks, dim, at, success, fail, warn) {
  // an event's enemies are committed to it: they never break and run (warband.js)
  for (const id of ids) safe(() => world.getEntity(id)?.addTag('bc_event'));
  objectives.push({ label, ids, until: system.currentTick + ticks, dim, at, success, fail, warn });
  logEvent(label, 'under way');
}
system.runInterval(() => {
  const t = system.currentTick;
  for (let i = objectives.length - 1; i >= 0; i--) {
    const o = objectives[i];
    const left = o.ids.filter((id) => {
      const e = world.getEntity(id);
      return e && alive(e);
    });
    if (!left.length) {
      objectives.splice(i, 1);
      setOutcome(o.label, 'success');
      for (const q of playersNear(o.dim, o.at, 64)) emit('event_win', q, o.label);
      safe(o.success, 'eventWin');
    } else if (o.until <= t) {
      objectives.splice(i, 1);
      setOutcome(o.label, 'failed');
      safe(o.fail, 'eventFail');
    } else if (o.warn) safe(() => o.warn(Math.ceil((o.until - t) / 20)), 'eventWarn');
  }
}, 20);

function playersNear(dim, at, r) {
  return safe(() => dim.getPlayers({ location: at, maxDistance: r })) ?? [];
}
function reward(dim, at, coins, stars, xp, why) {
  for (const q of playersNear(dim, at, 64)) {
    if (coins) giveCoins(q, coins);
    if (xp) addXp(q, xp);
    if (stars) safe(() => addStars(q, stars, why));
  }
}


// ------------------------------------------------------------------------------- the events
/** Pick a faction, the stronger ones more often. */
function weightedFaction(exclude) {
  const pool = Object.keys(DATA.factions).filter((f) => f !== exclude);
  const w = pool.map((f) => (POWERS.includes(f) ? powerMul(f) : 0.6));
  let r = Math.random() * w.reduce((a, b) => a + b, 0);
  for (let i = 0; i < pool.length; i++) {
    r -= w[i];
    if (r <= 0) return pool[i];
  }
  return pool[0];
}

function battleSpot(p, dist = 20) {
  const dir = V.flat(p.getViewDirection());
  const c = V.add(p.location, V.mul(dir, dist));
  const top = safe(() => p.dimension.getTopmostBlock({ x: c.x, z: c.z }));
  if (!top || top.isLiquid) return undefined;
  c.y = top.location.y + 1;
  return { c, dir };
}

/** @type {Record<string, {w: number, f?: string, label?: string, ok?: (p: Player) => boolean, run: (p: Player) => boolean | void}>} */
export const EVENTS = {
  meteor_shower: {
    w: 10,
    run(p) {
      announce(p, '§b§lMANA METEOR SHOWER', '§7Stars are falling - catch the mana crystals!', '§b✦ A mana meteor shower lights up the sky. Fallen stars may leave §dMana Crystals§b behind.');
      repeat(40, 15, () => {
        if (!alive(p)) return false;
        const a = Math.random() * Math.PI * 2;
        const r = rand(7, 30);
        const target = { x: p.location.x + Math.cos(a) * r, y: p.location.y, z: p.location.z + Math.sin(a) * r };
        const top = safe(() => p.dimension.getTopmostBlock({ x: target.x, z: target.z }));
        if (top) target.y = top.location.y + 1;
        const from = V.add(target, { x: rand(-10, 10), y: 30, z: rand(-10, 10) });
        boltFrom(p, 'a:star', { t: 'bolt', d: 6, aoe: 2.5, shape: 0, size: 2, fx: 'star' }, from, V.sub(target, from), 1.6, { drop: 'bc:mana_crystal', pw: 1 });
      });
    },
  },
  devil_gate: {
    w: 8,
    f: 'devils',
    run(p) {
      const at = spotNear(p, rand(18, 26));
      if (!at) return false;
      const gate = safe(() => p.dimension.spawnEntity('bc:devil_gate', V.add(at, { x: 0, y: 0.5, z: 0 })));
      if (!gate) return false;
      announce(p, '§4§lA DEVIL GATE OPENS', '§7Destroy it before something worse comes through', `§4☠ A Devil Gate has torn open near §f${Math.floor(at.x)}, ${Math.floor(at.y)}, ${Math.floor(at.z)}§4. Destroy it!`);
      sound(p.dimension, 'bc.devil.roar', at, 3, 0.6);
      repeat(12, 160, (i) => {
        if (!alive(gate)) return false;
        const count = safe(() => gate.dimension.getEntities({ location: at, maxDistance: 32, families: ['bc_devil'] }).length) ?? 0;
        if (count > 12) return;
        for (const type of ['bc:imp', 'bc:imp', i % 2 ? 'bc:dark_disciple' : 'bc:imp']) {
          safe(() => gate.dimension.spawnEntity(type, V.add(at, { x: rand(-2, 2), y: 1, z: rand(-2, 2) })));
        }
        particle(gate.dimension, 'bc:magic_circle_dark', V.add(at, { x: 0, y: 0.1, z: 0 }), { size: 4, life: 1 });
      }, () => {
        if (!alive(gate)) return;
        const loc = gate.location;
        safe(() => gate.remove());
        if (Math.random() < 0.3 && !safe(() => p.dimension.getEntities({ location: loc, maxDistance: 96, type: 'bc:archdevil' }).length)) {
          summonBoss('bc:archdevil', p.dimension, loc);
        } else {
          particle(p.dimension, 'bc:burst_dark', loc, { scale: 2, color: rgb('2a0010') });
          for (const q of p.dimension.getPlayers({ location: loc, maxDistance: 64 })) title(q, '§8The gate closes', '§7...for now', 40);
        }
      });
    },
  },
  pirate_landing: {
    w: 8,
    f: 'raiders',
    run(p) {
      const at = spotNear(p, rand(18, 24));
      if (!at) return false;
      announce(p, '§c§lPIRATES HAVE LANDED', '§7A raiding party comes ashore', '§c⚓ A raiding party has landed nearby!');
      sound(p.dimension, 'bc.ship.bell', at, 2, 0.8);
      spawnCaptain(p.dimension, at, {});
      for (let i = 0; i < scaled(p, 4 + Math.floor(Math.random() * 3)); i++) safe(() => p.dimension.spawnEntity('bc:sea_raider', V.add(at, { x: rand(-3, 3), y: 0.5, z: rand(-3, 3) })));
    },
  },
  skirmish: {
    w: 10,
    run(p) {
      const spot = battleSpot(p);
      if (!spot) return false;
      const fa = weightedFaction();
      const fb = Math.random() < 0.6 && RIVAL[fa] ? RIVAL[fa] : weightedFaction(fa);
      const tactics = Object.keys(TACTICS);
      announce(p, '§6§lA SKIRMISH BREAKS OUT', `§7${DATA.factions[fa].name} clash with ${DATA.factions[fb].name}`);
      startBattle({ dim: p.dimension, center: spot.c, facing: spot.dir, fa, fb, size: 4 + Math.floor(Math.random() * 3), leaders: true, quiet: true,
        tactics: { a: pick(tactics), b: pick(tactics) } });
    },
  },
  knight_tournament: {
    w: 4,
    ok: () => !night(),
    run(p) {
      const spot = battleSpot(p, 14);
      if (!spot) return false;
      const attrs = DATA.order.filter((a) => a !== 'anti');
      const level = 3 + Math.floor(Math.random() * 5);
      announce(p, '§a§lA KNIGHTS\' TOURNAMENT', '§7Two Magic Knights cross grimoires', '§a♣ Two Magic Knights are holding a duel nearby - come and watch!');
      startBattle({ dim: p.dimension, center: spot.c, facing: spot.dir, fa: 'knights', fb: 'knights', size: 1, duel: true,
        roster: { a: [{ type: 'bc:magic_knight', attr: pick(attrs), level }], b: [{ type: 'bc:magic_knight', attr: pick(attrs), level }] } });
    },
  },
  knight_patrol: {
    w: 6,
    f: 'knights',
    ok: () => !night(),
    run(p) {
      const at = spotNear(p, rand(14, 20));
      if (!at) return false;
      for (let i = 0; i < 3; i++) {
        const e = safe(() => p.dimension.spawnEntity('bc:magic_knight', V.add(at, { x: rand(-2, 2), y: 0.5, z: rand(-2, 2) })));
        if (e) setupKnight(e, {});
      }
      safe(() => p.sendMessage('§a♣ A patrol of Magic Knights passes nearby.'));
    },
  },
  merchant: {
    w: 7,
    run(p) {
      const at = spotNear(p, 7);
      if (!at) return false;
      spawnMerchant(p.dimension, at, 6);
      announce(p, '§b§lA TRAVELLING MERCHANT', '§7Rare wares, for a short while only', '§b⛁ A Travelling Magic Merchant has arrived. Talk to them before they leave!');
    },
  },
  sky_treasure: {
    w: 6,
    run(p) {
      const at = spotNear(p, rand(24, 36));
      if (!at) return false;
      const blk = { x: Math.floor(at.x), y: Math.floor(at.y), z: Math.floor(at.z) };
      announce(p, '§e§lSKY TREASURE', '§7Follow the golden beam', `§e✦ A treasure chest is falling from the sky near §f${blk.x}, ${blk.y}, ${blk.z}§e - pirates have seen it too!`);
      repeat(10, 10, () => particle(p.dimension, 'bc:sky_beam', V.add(blk, { x: 0.5, y: 0, z: 0.5 }), { color: rgb('ffd36a') }), () => {
        const b = safe(() => p.dimension.getBlock(blk));
        if (!b) return;
        safe(() => b.setType('minecraft:chest'));
        const inv = safe(() => b.getComponent('minecraft:inventory')?.container);
        const loot = [new ItemStack('bc:doubloon', 20 + Math.floor(Math.random() * 40)), new ItemStack('bc:mana_crystal', 3 + Math.floor(Math.random() * 4)),
          new ItemStack('bc:ancient_page', 1 + Math.floor(Math.random() * 2)), new ItemStack('minecraft:diamond', 1 + Math.floor(Math.random() * 3))];
        if (Math.random() < 0.15) loot.push(new ItemStack(`bc:fruit_${pick(DATA.fruitOrder)}`, 1));
        if (Math.random() < 0.25) loot.push(new ItemStack(pick(['bc:knight_contract', 'bc:skirmish_horn', 'bc:treasure_map']), 1));
        loot.forEach((it, i) => safe(() => inv?.setItem(i * 3 + 1, it)));
        particle(p.dimension, 'bc:light_burst', V.add(blk, { x: 0.5, y: 1, z: 0.5 }), { scale: 1.5 });
        shakeArea(p.dimension, blk, 20, 0.3, 0.4);
        sound(p.dimension, 'random.anvil_land', blk, 1.5, 0.8);
        for (let i = 0; i < 3; i++) safe(() => p.dimension.spawnEntity('bc:sea_raider', V.add(blk, { x: rand(-5, 5), y: 1, z: rand(-5, 5) })));
      });
    },
  },
  crimson_night: {
    w: 4,
    f: 'devils',
    ok: () => night(),
    run(p) {
      announce(p, '§4§lCRIMSON NIGHT', '§7The devils are bold tonight', '§4☾ A crimson moon rises. Devils swarm for the next two minutes - each one slain is worth extra magic XP!');
      repeat(12, 200, () => {
        for (const q of world.getAllPlayers()) {
          if (q.dimension.id !== 'minecraft:overworld') continue;
          particle(q.dimension, 'bc:blood_moon', V.add(q.location, { x: 0, y: 14, z: 0 }), { scale: 1 });
          const at = spotNear(q, rand(10, 16), 4);
          if (!at) continue;
          for (const type of ['bc:imp', 'bc:dark_disciple']) {
            const e = safe(() => q.dimension.spawnEntity(type, V.add(at, { x: rand(-2, 2), y: 0.5, z: rand(-2, 2) })));
            safe(() => e?.addTag('bc_crimson'));
          }
        }
      }, () => {
        for (const q of world.getAllPlayers()) title(q, '§7The crimson moon sets', '', 40);
      });
    },
  },
  wounded_knight: {
    w: 5,
    run(p) {
      const at = spotNear(p, rand(14, 20));
      if (!at) return false;
      const k = safe(() => p.dimension.spawnEntity('bc:magic_knight', at));
      if (!k) return false;
      setupKnight(k, { level: 3 + Math.floor(Math.random() * 4), randomRobe: true });
      safe(() => {
        const h = k.getComponent('minecraft:health');
        h.setCurrentValue(Math.max(6, h.effectiveMax * 0.3));
        k.addTag('bc_wounded');
      });
      const foes = [];
      for (let i = 0; i < 3; i++) {
        const type = i === 0 && Math.random() < 0.5 ? 'bc:hellhound' : 'bc:dark_disciple';
        const f = safe(() => p.dimension.spawnEntity(type, V.add(at, { x: rand(-6, 6), y: 0.5, z: rand(-6, 6) })));
        if (f) foes.push(f);
      }
      const name = safe(() => k.getDynamicProperty('bc:kname')) ?? 'A knight';
      announce(p, '§e§lA KNIGHT IN TROUBLE', '§7Help them before the devils finish them off', `§e♣ §f${name}§e is hurt and surrounded by devils nearby - save them!`);
      repeat(60, 40, () => {
        if (!alive(k)) {
          safe(() => p.sendMessage(`§7${name} has fallen...`));
          return false;
        }
        if (foes.some((f) => alive(f))) return undefined;
        particle(k.dimension, 'bc:heal', center(k), { scale: 1 });
        safe(() => k.removeTag('bc_wounded'));
        if (alive(p) && joinParty(k, p, 150)) safe(() => p.sendMessage(`§b${name}§f: You saved my life. My grimoire is yours!`));
        else safe(() => p.sendMessage(`§b${name}§f: Thank you, friend! §7(Your party is full - talk to them to recruit later.)`));
        return false;
      });
    },
  },
  mana_storm: {
    w: 5,
    run(p) {
      announce(p, '§b§lMANA STORM', '§7The air crackles with free mana', '§b⚡ A mana storm rolls in: everyone regains mana fast, and wild lightning strikes monsters!');
      repeat(45, 20, (i) => {
        for (const q of world.getAllPlayers()) {
          if (q.dimension.id !== 'minecraft:overworld') continue;
          addMana(q, 4);
          if (i % 3) continue;
          const a = Math.random() * Math.PI * 2;
          const spot = V.add(q.location, { x: Math.cos(a) * rand(6, 20), y: 0, z: Math.sin(a) * rand(6, 20) });
          const top = safe(() => q.dimension.getTopmostBlock({ x: spot.x, z: spot.z }));
          if (top) spot.y = top.location.y + 1;
          particle(q.dimension, 'bc:pillar', spot, { color: rgb('9ae8ff'), scale: 1.4 });
          particle(q.dimension, 'bc:burst_spark', spot, { color: rgb('9ae8ff'), scale: 1 });
          sound(q.dimension, 'bc.lightning.zap', spot, 1, 1.2);
          for (const m of targetsAround(q.dimension, spot, 3, undefined)) if (safe(() => m.matches({ families: ['monster'] }))) hurt(m, 8, undefined, 'lightning');
        }
      });
    },
  },
  bounty_hunters: {
    w: 4,
    ok: (p) => notoriety(p) >= 300,
    run(p) {
      const at = spotNear(p, rand(14, 18));
      if (!at) return false;
      announce(p, '§9§lBOUNTY HUNTERS', '§7The Tidewatch have found you', '§9⚓ Tidewatch bounty hunters have tracked you down!');
      const squad = ['bc:tidewatch_marksman', 'bc:tidewatch_marksman', 'bc:tidewatch_sentinel', 'bc:tidewatch_sentinel'];
      if (notoriety(p) >= 1500) squad.push('bc:tidewatch_commodore');
      for (const type of squad) {
        const e = safe(() => p.dimension.spawnEntity(type, V.add(at, { x: rand(-3, 3), y: 0.5, z: rand(-3, 3) })));
        safe(() => { if (e) e.nameTag = '§9Bounty Hunter'; });
      }
    },
  },
  fallen_captain: {
    w: 2,
    ok: () => night(),
    run(p) {
      const at = spotNear(p, rand(20, 26));
      if (!at) return false;
      announce(p, '§4§lA CAPTAIN FALLEN', '§7Something wearing a Magic Knight\'s robe walks in the dark', '§4☠ The Fallen Captain hunts tonight...');
      summonBoss('bc:fallen_captain', p.dimension, at);
    },
  },
  rogue_ambush: {
    w: 6,
    f: 'rogues',
    run(p) {
      const at = spotNear(p, rand(14, 20));
      if (!at) return false;
      const n = 3 + Math.floor(Math.random() * 2);
      // sometimes a knight patrol was already on their trail
      const patrol = Math.random() < 0.35;
      announce(p, '§5§lROGUE MAGES', patrol ? '§7A knight patrol is hunting them - join the fight' : '§7Outlaw mages are lying in wait',
        `§5☠ Rogue Mages ambush you${patrol ? ' - and a Magic Knight patrol arrives to help!' : '!'}`);
      for (let i = 0; i < n; i++) {
        const e = safe(() => p.dimension.spawnEntity('bc:rogue_mage', V.add(at, { x: rand(-3, 3), y: 0.5, z: rand(-3, 3) })));
        if (e) setupRogue(e, { level: 2 + Math.floor(Math.random() * 5) + (i === 0 ? 3 : 0) });
      }
      if (patrol) {
        const back = V.add(p.location, V.mul(V.flat(V.sub(p.location, at)), 8));
        for (let i = 0; i < 2; i++) {
          const k = safe(() => p.dimension.spawnEntity('bc:magic_knight', V.add(back, { x: rand(-2, 2), y: 0.5, z: rand(-2, 2) })));
          if (k) setupKnight(k, { level: 3 + Math.floor(Math.random() * 4) });
        }
      }
    },
  },
  bandit_raid: {
    w: 8,
    f: 'bandits',
    label: 'Bandit raid',
    run(p) {
      const at = spotNear(p, rand(18, 24));
      if (!at) return false;
      const king = tier(p) >= 2 && Math.random() < 0.3;
      announce(p, '§6§lBANDIT RAID', king ? '§7The Bandit King rides with them!' : '§7Bandits come over the hill', `§6⚔ A bandit raid${king ? ' - led by the Bandit King himself -' : ''} is coming your way!`);
      sound(p.dimension, 'bc.horn', at, 2, 0.7);
      const ids = [];
      const band = [...Array(scaled(p, 3)).fill('bc:bandit'), ...Array(scaled(p, 1)).fill('bc:bandit_archer'), 'bc:bandit_thief'];
      for (const type of band) {
        const e = safe(() => p.dimension.spawnEntity(type, V.add(at, { x: rand(-3, 3), y: 0.5, z: rand(-3, 3) })));
        if (e) ids.push(e.id);
      }
      if (king) timer(40, () => summonBoss('bc:bandit_king', p.dimension, at, [p]));
      const coins = 30 + ids.length * 8;
      objective('Bandit raid', ids, 20 * 240, p.dimension, at,
        () => {
          for (const q of playersNear(p.dimension, at, 64)) title(q, '§6§lRAID REPELLED', `§7The bandits are beaten §6+${coins} doubloons`, 50);
          reward(p.dimension, at, coins, 1, 80, 'repelled a bandit raid');
        },
        () => {
          for (const q of playersNear(p.dimension, at, 64)) safe(() => q.sendMessage('§6The bandits withdraw with whatever they could carry.'));
        });
      return true;
    },
  },
  devil_ritual: {
    w: 5,
    f: 'devils',
    label: 'Devil ritual',
    ok: () => night(),
    run(p) {
      const at = spotNear(p, rand(20, 26));
      if (!at) return false;
      announce(p, '§4§lA DEVIL RITUAL', '§7Cultists chant in the dark - stop them!', `§4☠ Cultists are performing a ritual near §f${Math.floor(at.x)}, ${Math.floor(at.z)}§4. Kill them before it completes!`);
      const ids = [];
      for (let i = 0; i < scaled(p, 3); i++) {
        const a = (i / scaled(p, 3)) * Math.PI * 2;
        const e = safe(() => p.dimension.spawnEntity('bc:cultist', V.add(at, { x: Math.cos(a) * 3, y: 0.5, z: Math.sin(a) * 3 })));
        if (e) ids.push(e.id);
      }
      for (let i = 0; i < 2; i++) safe(() => p.dimension.spawnEntity('bc:imp', V.add(at, { x: rand(-4, 4), y: 1, z: rand(-4, 4) })));
      const ritual = system.runInterval(() => {
        particle(p.dimension, 'bc:magic_circle_dark', V.add(at, { x: 0, y: 0.1, z: 0 }), { size: 5, life: 1.2, color: rgb('8a1010') });
        particle(p.dimension, 'bc:pillar', at, { color: rgb('8a1010'), scale: 0.8 });
      }, 20);
      objective('Devil ritual', ids, 20 * 90, p.dimension, at,
        () => {
          system.clearRun(ritual);
          for (const q of playersNear(p.dimension, at, 64)) title(q, '§a§lRITUAL STOPPED', '§7The circle fades', 50);
          reward(p.dimension, at, 0, 1, 150, 'stopped a devil ritual');
          safe(() => p.dimension.spawnItem(new ItemStack('bc:mana_crystal', 4), at));
        },
        () => {
          system.clearRun(ritual);
          for (const q of playersNear(p.dimension, at, 64)) title(q, '§4§lTHE RITUAL IS COMPLETE', tier(p) >= 2 ? '§7Something hungry wakes up' : '§7A gate tears open', 60);
          if (tier(p) >= 2) summonBoss('bc:grimoire_devourer', p.dimension, at, [p]);
          else safe(() => p.dimension.spawnEntity('bc:devil_gate', V.add(at, { x: 0, y: 0.5, z: 0 })));
        },
        (left) => {
          if (left % 15 === 0 || left <= 10) for (const q of playersNear(p.dimension, at, 48)) safe(() => q.onScreenDisplay.setActionBar(`§4Ritual: §f${left}s§4 left - kill the cultists!`));
        });
      return true;
    },
  },
  hive_infestation: {
    w: 5,
    label: 'Hive infestation',
    run(p) {
      const at = spotNear(p, rand(18, 24));
      if (!at) return false;
      announce(p, '§e§lHIVE INFESTATION', '§7Eggs pulse in the grass - smash them!', '§e☣ A hive has taken root nearby. Destroy every egg before they all hatch!');
      const ids = [];
      for (let i = 0; i < scaled(p, 5); i++) {
        const egg = layEgg(p.dimension, V.add(at, { x: rand(-5, 5), y: 0.2, z: rand(-5, 5) }), 20 * (60 + Math.floor(Math.random() * 40)));
        if (egg) ids.push(egg.id);
      }
      for (let i = 0; i < scaled(p, 3); i++) safe(() => p.dimension.spawnEntity('bc:hive_drone', V.add(at, { x: rand(-3, 3), y: 0.5, z: rand(-3, 3) })));
      objective('Hive infestation', ids, 20 * 120, p.dimension, at,
        () => {
          for (const q of playersNear(p.dimension, at, 64)) title(q, '§a§lHIVE DESTROYED', '§7Not a single egg survived', 50);
          reward(p.dimension, at, 40, 1, 120, 'destroyed a hive');
        },
        () => {
          if (tier(p) >= 2) {
            for (const q of playersNear(p.dimension, at, 64)) title(q, '§e§lTHE QUEEN AWAKENS', '§7The hive protects its mother', 60);
            summonBoss('bc:hive_queen', p.dimension, at, [p]);
          }
        });
      return true;
    },
  },
  assassins: {
    w: 3,
    label: 'Assassins',
    ok: (p) => night() && ((safe(() => p.getDynamicProperty('bc:stars')) ?? 0) >= 5 || (safe(() => state(p).level) ?? 1) >= 8),
    run(p) {
      const at = spotNear(p, rand(18, 22));
      if (!at) return false;
      safe(() => p.sendMessage('§5You feel watched... §7(Shadow Assassins hunt you tonight. Look for faint shadows.)'));
      sound(p.dimension, 'bc.portal', p.location, 0.4, 0.5);
      const ids = [];
      for (let i = 0; i < Math.min(4, scaled(p, 2)); i++) {
        const e = safe(() => p.dimension.spawnEntity('bc:shadow_assassin', V.add(at, { x: rand(-4, 4), y: 0.5, z: rand(-4, 4) })));
        if (e) {
          ids.push(e.id);
          safe(() => e.addEffect('invisibility', 200, { amplifier: 0, showParticles: false }));
        }
      }
      objective('Assassins', ids, 20 * 300, p.dimension, at, () => reward(p.dimension, at, 25, 1, 100, 'survived the assassins'), () => {});
      return true;
    },
  },
  thief: {
    w: 4,
    label: 'A thief',
    ok: (p) => {
      const inv = p.getComponent('minecraft:inventory')?.container;
      let n = 0;
      for (let i = 0; inv && i < inv.size; i++) if (inv.getItem(i)?.typeId === 'bc:doubloon') n += inv.getItem(i).amount;
      return n >= 20;
    },
    run(p) {
      const behind = V.add(p.location, V.mul(V.flat(p.getViewDirection()), -9));
      const top = safe(() => p.dimension.getTopmostBlock({ x: behind.x, z: behind.z }));
      if (top && Math.abs(top.location.y + 1 - p.location.y) < 5) behind.y = top.location.y + 1;
      const e = safe(() => p.dimension.spawnEntity('bc:bandit_thief', behind));
      if (!e) return false;
      safe(() => e.addEffect('invisibility', 160, { amplifier: 0, showParticles: false }));
      safe(() => p.sendMessage('§6Watch your purse... §7(a thief is close)'));
      logEvent('A thief', 'happened');
      return true;
    },
  },
  mana_eclipse: {
    w: 4,
    label: 'Mana Eclipse',
    run(p) {
      const until = system.currentTick + 20 * 180;
      world.setDynamicProperty('bc:eclipse_until', until);
      for (const q of world.getAllPlayers()) title(q, '§d§lMANA ECLIPSE', '§7Spells strike 25% harder and magic XP flows faster - but monsters grow bold', 70);
      safe(() => p.sendMessage('§d☾ A Mana Eclipse darkens the sky for 3 minutes: +25% spell power, x1.5 magic XP, stronger monsters.'));
      logEvent('Mana Eclipse', 'happened');
      return true;
    },
  },
  rival_squad: {
    w: 5,
    ok: (p) => !night() && partySize(p) > 0,
    run(p) {
      const at = spotNear(p, rand(14, 18));
      if (!at) return false;
      return startRivalMatch(p, at);
    },
  },
  puppet_show: {
    w: 2,
    ok: () => night(),
    run(p) {
      const at = spotNear(p, rand(20, 26));
      if (!at) return false;
      announce(p, '§5§lTHE CURTAIN RISES', '§7Somewhere in the dark, strings are pulled taut', '§5☠ You hear a music box... §dthe Soul Puppeteer§5 has come to play.');
      timer(40, () => summonBoss('bc:soul_puppeteer', p.dimension, at));
    },
  },
  witch_sisters: {
    w: 2,
    ok: () => night(),
    run(p) {
      const at = spotNear(p, rand(20, 26));
      if (!at) return false;
      announce(p, '§b§lTWIN MOONS', '§7Frost and fire ride the night wind', '§b☾ §6☽ §7Two witches laugh somewhere in the dark... §bThe Witch Sisters§7 are coming.');
      repeat(6, 10, () => particle(p.dimension, 'bc:fog_cloud', V.add(p.location, { x: rand(-4, 4), y: 1, z: rand(-4, 4) }), { scale: 0.6 }));
      timer(40, () => summonBoss('twins', p.dimension, at));
    },
  },
  bone_dragon: {
    w: 2,
    ok: (p) => night() && p.location.y > 55,
    run(p) {
      const at = spotNear(p, rand(26, 32));
      if (!at) return false;
      announce(p, '§f§lBONES IN THE SKY', '§7Something vast blots out the stars', '§f☠ Bones rattle in the sky... §fthe Bone Dragon§7 has woken.');
      sound(p.dimension, 'mob.enderdragon.growl', p.location, 1, 0.5);
      timer(40, () => summonBoss('bc:bone_dragon', p.dimension, at));
    },
  },
  colossus: {
    w: 3,
    ok: (p) => !night() && p.location.y > 55,
    run(p) {
      const at = spotNear(p, rand(26, 32));
      if (!at) return false;
      announce(p, '§6§lTHE GROUND TREMBLES', '§7Something enormous is waking up', '§6⛰ The earth shakes... a Stone Colossus is rising nearby!');
      summonBoss('bc:stone_colossus', p.dimension, at);
    },
  },
  phantom_galleon: {
    w: 3,
    ok: () => night(),
    run(p) {
      const at = spotNear(p, rand(24, 30)) ?? V.add(p.location, { x: 24, y: 0, z: 0 });
      announce(p, '§3§lA GHOSTLY FOG ROLLS IN', '§7You hear a ship\'s bell... in the sky', '§3☠ A ghostly fog rolls in. The Phantom Galleon is coming!');
      repeat(8, 10, () => particle(p.dimension, 'bc:fog_cloud', p.location, { scale: 1 }));
      timer(40, () => summonBoss('bc:phantom_galleon', p.dimension, at));
    },
  },
  kraken: {
    w: 3,
    ok: (p) => !!waterNear(p, 20),
    run(p) {
      const at = waterNear(p, 20);
      if (!at) return false;
      announce(p, '§9§lTHE SEA DARKENS', '§7Thunder rolls over the water', '§9⚡ The sea darkens... the Storm Kraken rises!');
      summonBoss('bc:storm_kraken', p.dimension, at);
    },
  },
};

// a dominant faction marches on its rival, near a player
onOffensive((attacker, defender) => {
  const players = world.getAllPlayers().filter((p) => p.dimension.id === 'minecraft:overworld');
  if (!players.length) return false;
  const p = pick(players);
  const spot = battleSpot(p, 24);
  if (!spot) return false;
  announce(p, `${DATA.factions[attacker].mc}§lAN OFFENSIVE`, `§7The ${DATA.factions[attacker].name} march on the ${DATA.factions[defender].name}`);
  startBattle({ dim: p.dimension, center: spot.c, facing: spot.dir, fa: attacker, fb: defender, size: 7 + Math.floor(Math.random() * 3), leaders: true, quiet: true,
    tactics: { a: Math.random() < 0.5 ? 'charge' : 'flank', b: 'hold' } });
  return true;
});

// crimson-night devils give extra XP
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  if (!ev.deadEntity.hasTag('bc_crimson')) return;
  const k = ev.damageSource.damagingEntity;
  if (k instanceof Player) addXp(k, 25);
}, 'crimson'));

// devil gates reward whoever breaks them
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  if (ev.deadEntity.typeId !== 'bc:devil_gate') return;
  const loc = ev.deadEntity.location;
  particle(ev.deadEntity.dimension, 'bc:light_burst', loc, { scale: 2 });
  for (const q of ev.deadEntity.dimension.getPlayers({ location: loc, maxDistance: 48 })) {
    title(q, '§a§lGATE SEALED', '§7The devils are cut off', 50);
    addXp(q, 120);
    safe(() => addStars(q, 1, 'sealed a Devil Gate'));
  }
}, 'gateDie'));

const recent = [];
/** Run a named event (or a random one) at a player. */
export function runEvent(p, name) {
  const pool = name ? [[name, EVENTS[name]]] : Object.entries(EVENTS).filter(([k, e]) => !recent.includes(k) && (!e.ok || e.ok(p)));
  if (!pool.length || !pool[0][1]) return false;
  const weight = (e) => e.w * (e.f && POWERS.includes(e.f) ? powerMul(e.f) : 1);
  let r = Math.random() * pool.reduce((s, [, e]) => s + weight(e), 0);
  let chosen = pool[0];
  for (const entry of pool) {
    r -= weight(entry[1]);
    if (r <= 0) {
      chosen = entry;
      break;
    }
  }
  const ok = safe(() => chosen[1].run(p), `event:${chosen[0]}`) !== false;
  if (ok) {
    recent.unshift(chosen[0]);
    recent.length = Math.min(recent.length, 2);
    // events without an objective are logged as they happen
    if (!chosen[1].label) logEvent(chosen[0].replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase()), 'happened');
  }
  return ok;
}

// pacing: hard fights push the next event back, quiet stretches bring it forward
const fights = new Map();
world.afterEvents.entityDie.subscribe((ev) => {
  const k = ev.damageSource.damagingEntity;
  const p = k instanceof Player ? k : undefined;
  if (p) fights.set(p.id, (fights.get(p.id) ?? 0) + 1);
});
function pace() {
  let kills = 0;
  for (const v of fights.values()) kills += v;
  fights.clear();
  return kills >= 25 ? 1.5 : kills <= 2 ? 0.7 : 1;
}

// the Mana Eclipse makes monsters near players bolder
system.runInterval(() => {
  if (eclipseMul() === 1) return;
  for (const p of world.getAllPlayers()) {
    particle(p.dimension, 'bc:burst_spark', V.add(p.location, { x: rand(-6, 6), y: rand(3, 6), z: rand(-6, 6) }), { color: rgb('c060ff'), scale: 0.5 });
    for (const m of safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 32, families: ['monster'] })) ?? []) {
      safe(() => m.addEffect('strength', 120, { amplifier: 0, showParticles: false }));
    }
  }
}, 100);

let nextAt = 20 * 60 * 3;
system.runInterval(() => {
  const t = system.currentTick;
  if (t < nextAt || !eventsOn()) return;
  const players = world.getAllPlayers().filter((p) => p.dimension.id === 'minecraft:overworld');
  if (!players.length) return;
  const p = pick(players);
  if (runEvent(p)) nextAt = t + Math.round(rand(20 * 60 * 4, 20 * 60 * 7) * pace());
  else nextAt = t + 20 * 30;
}, 100);

system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (ev.id !== 'bc:event') return;
  const src = ev.sourceEntity;
  const p = src instanceof Player ? src : world.getAllPlayers()[0];
  if (!p) return;
  const name = ev.message.trim();
  if (name && !EVENTS[name]) {
    safe(() => p.sendMessage(`§7Events: ${Object.keys(EVENTS).join(', ')}`));
    return;
  }
  runEvent(p, name || undefined);
});

export { center };
