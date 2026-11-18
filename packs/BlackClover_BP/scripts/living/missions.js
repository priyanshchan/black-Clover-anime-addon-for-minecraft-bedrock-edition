// Magic Knight Missions: every in-game day each player gets three missions (one easy, one harder, one wild card).
// Progress counts anywhere - kills, bosses, sealed gates, spells cast, XP earned, your companions' victories - and
// finished missions are turned in at a Mission Board (crafted, or found in Magic Knight camps) for stars,
// doubloons and magic XP. Delivery missions take the items from your pack at the board.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { ActionFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { emit, on } from '../core/bus.js';
import { ownerOf } from '../core/combat.js';
import { particle, sound } from '../core/fx.js';
import { addXp } from '../core/progress.js';
import { addStars } from '../core/ranks.js';
import { safe } from '../core/util.js';
import { countCoins, giveCoins } from '../sea/bounty.js';

const KEY = 'bc:missions';
const REROLL_COST = 25;
const BY_ID = Object.fromEntries(DATA.missions.map((m) => [m.id, m]));

/** @typedef {{id: string, n: number, claimed: boolean}} Slot */
/** @typedef {{day: number, list: Slot[], rerolls: number, total: number}} Board */

/** @type {Map<string, Board>} */
const cache = new Map();

function hash(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) h = Math.imul(h ^ str.charCodeAt(i), 16777619);
  return h >>> 0;
}

function rng(seed) {
  let a = seed;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Today's three missions for a player: an easy one, a harder one and a wild card. */
function dealFor(p, day, salt = 0) {
  const r = rng(hash(`${p.id}:${day}:${salt}`));
  const pickFrom = (pool, taken) => {
    const left = pool.filter((m) => !taken.includes(m.id));
    return left[Math.floor(r() * left.length)]?.id;
  };
  const ids = [];
  ids.push(pickFrom(DATA.missions.filter((m) => m.tier === 1), ids));
  ids.push(pickFrom(DATA.missions.filter((m) => m.tier === 2), ids));
  ids.push(pickFrom(DATA.missions, ids));
  return ids.filter(Boolean).map((id) => ({ id, n: 0, claimed: false }));
}

/** @returns {Board} */
function board(p) {
  let b = cache.get(p.id);
  const day = world.getDay();
  if (!b) {
    const raw = safe(() => p.getDynamicProperty(KEY));
    try {
      b = typeof raw === 'string' ? JSON.parse(raw) : undefined;
    } catch {
      b = undefined;
    }
    if (!b || !Array.isArray(b.list)) b = { day: -1, list: [], rerolls: 0, total: 0 };
    b.list = b.list.filter((s) => BY_ID[s.id]);
    cache.set(p.id, b);
  }
  if (b.day !== day) {
    b.day = day;
    b.list = dealFor(p, day);
    b.rerolls = 0;
    store(p, b);
  }
  return b;
}

function store(p, b) {
  safe(() => p.setDynamicProperty(KEY, JSON.stringify(b)));
}

world.afterEvents.playerLeave.subscribe((ev) => cache.delete(ev.playerId));

function done(slot) {
  return slot.n >= BY_ID[slot.id].count;
}

/** Add progress to every matching mission of a player. */
function progress(p, test, amount = 1) {
  if (!(p instanceof Player)) return;
  const b = board(p);
  let changed = false;
  for (const slot of b.list) {
    const m = BY_ID[slot.id];
    if (slot.claimed || done(slot) || !test(m)) continue;
    slot.n = Math.min(m.count, slot.n + amount);
    changed = true;
    if (done(slot)) {
      safe(() => p.sendMessage(`§a✔ Mission complete: §f${m.title}§a - turn it in at a §6Mission Board§a.`));
      sound(p.dimension, 'random.levelup', p.location, 0.7, 1.4);
      particle(p.dimension, 'bc:clover_leaves', p.location, { scale: 0.8 });
    } else if (m.kind !== 'xp' || slot.n % 50 < amount) {
      safe(() => p.onScreenDisplay.setActionBar(`§6Mission §7${m.title}: §f${Math.floor(slot.n)}§7/${m.count}`));
    }
  }
  if (changed) store(p, b);
}

function matchesTarget(e, typeId, target) {
  if (typeId === target) return true;
  if (target.includes(':')) return false;
  return !!safe(() => e.matches({ families: [target] }));
}

// ------------------------------------------------------------------------------- progress hooks
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const dead = ev.deadEntity;
  const typeId = safe(() => dead.typeId) ?? '';
  const killer = ev.damageSource.damagingEntity;
  if (!killer) return;
  const ownerId = killer instanceof Player ? '' : ownerOf(killer);
  const p = killer instanceof Player ? killer : ownerId ? world.getEntity(ownerId) : undefined;
  if (!(p instanceof Player)) return;
  progress(p, (m) => m.kind === 'kill' && matchesTarget(dead, typeId, m.target));
  if (ownerId && typeof safe(() => killer.getDynamicProperty('bc:cid')) === 'string') progress(p, (m) => m.kind === 'companion');
}, 'missionKill'));

// sealing a Devil Gate counts for everyone who was there
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  if (ev.deadEntity.typeId !== 'bc:devil_gate') return;
  for (const q of ev.deadEntity.dimension.getPlayers({ location: ev.deadEntity.location, maxDistance: 48 })) progress(q, (m) => m.kind === 'gate');
}, 'missionGate'));

on('boss', (p) => progress(p, (m) => m.kind === 'boss'));
on('cast', (p) => progress(p, (m) => m.kind === 'cast'));
on('event_win', (p) => progress(p, (m) => m.kind === 'event'));
on('xp', (p, amount) => progress(p, (m) => m.kind === 'xp', Math.max(0, Math.floor(amount))));

// ------------------------------------------------------------------------------- the board
function count(p, id) {
  const inv = p.getComponent('minecraft:inventory')?.container;
  let n = 0;
  if (!inv) return 0;
  for (let i = 0; i < inv.size; i++) {
    const it = inv.getItem(i);
    if (it?.typeId === id) n += it.amount;
  }
  return n;
}

function take(p, id, amount) {
  const inv = p.getComponent('minecraft:inventory')?.container;
  if (!inv) return 0;
  let left = amount;
  for (let i = 0; i < inv.size && left > 0; i++) {
    const it = inv.getItem(i);
    if (it?.typeId !== id) continue;
    const k = Math.min(left, it.amount);
    left -= k;
    if (it.amount - k > 0) {
      it.amount -= k;
      inv.setItem(i, it);
    } else inv.setItem(i, undefined);
  }
  return amount - left;
}

function line(slot) {
  const m = BY_ID[slot.id];
  const stars = DATA.glyphs.star.repeat(m.tier);
  if (slot.claimed) return `§8${m.title}\n§8Reward claimed`;
  if (done(slot)) return `§2§l${m.title}\n§r§aClaim reward §6${stars}`;
  const bar = m.kind === 'deliver' ? '§9deliver here' : `§7${Math.floor(slot.n)}/${m.count}`;
  return `§0${m.title}\n${bar} §6${stars}`;
}

function claim(p, b, slot) {
  const m = BY_ID[slot.id];
  const r = DATA.missionRewards[m.tier] ?? DATA.missionRewards[1];
  slot.claimed = true;
  b.total += 1;
  store(p, b);
  emit('mission', p, m.id);
  sound(p.dimension, 'bc.fanfare', p.location, 0.9, 1.1);
  particle(p.dimension, 'bc:level_up', p.location);
  giveCoins(p, r.coins);
  addXp(p, r.xp);
  safe(() => addStars(p, r.stars, `mission: ${m.title}`));
  safe(() => p.sendMessage(`§6Mission reward: §e${r.coins} doubloons§6, §b${r.xp} magic XP§6. §7(${b.total} missions completed)`));
  if (b.list.every((s) => s.claimed)) {
    safe(() => p.sendMessage('§a§lAll of today\'s missions done! §r§7A bonus from the Magic Knight HQ: §dMana Crystals x4'));
    const left = p.getComponent('minecraft:inventory')?.container?.addItem(new ItemStack('bc:mana_crystal', 4));
    if (left) p.dimension.spawnItem(left, p.location);
  }
}

async function openBoard(p) {
  const b = board(p);
  const time = world.getTimeOfDay();
  const hours = Math.ceil(((24000 - time) % 24000) / 1000);
  const form = new ActionFormData()
    .title('§lMagic Knight Missions')
    .body(`§7Day ${b.day}. New missions in about §f${hours}§7 in-game hours.\n§7Completed so far: §f${b.total}\n\n§7Finish a mission anywhere, then claim it here.`);
  for (const slot of b.list) form.button(line(slot));
  const canReroll = b.list.some((s) => !s.claimed && s.n === 0);
  const rerollCost = b.rerolls === 0 ? 0 : REROLL_COST;
  if (canReroll) form.button(`§5Swap a mission\n§7${rerollCost ? `${rerollCost} doubloons` : 'free once a day'}`);
  form.button('§8Close');
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return;
  const sel = res.selection;
  if (sel < b.list.length) {
    const slot = b.list[sel];
    const m = BY_ID[slot.id];
    if (slot.claimed) return;
    if (!done(slot) && m.kind === 'deliver') {
      const have = count(p, m.target);
      if (!have) {
        safe(() => p.sendMessage(`§7You have nothing to deliver for §f${m.title}§7.`));
        return;
      }
      slot.n += take(p, m.target, Math.min(have, m.count - slot.n));
      store(p, b);
      sound(p.dimension, 'random.pop', p.location, 0.8, 1);
      safe(() => p.sendMessage(`§6Delivered: §f${slot.n}/${m.count}`));
    }
    if (done(slot)) claim(p, b, slot);
    else if (m.kind !== 'deliver') safe(() => p.sendMessage(`§7${m.title}: §f${Math.floor(slot.n)}/${m.count}§7 - keep going.`));
    return;
  }
  if (canReroll && sel === b.list.length) {
    const idx = b.list.findIndex((s) => !s.claimed && s.n === 0);
    if (rerollCost && countCoins(p) < rerollCost) {
      safe(() => p.sendMessage(`§7Swapping a mission costs §6${rerollCost} doubloons§7.`));
      return;
    }
    if (rerollCost) payCoins(p, rerollCost);
    const taken = b.list.map((s) => s.id);
    const same = DATA.missions.filter((m) => !taken.includes(m.id) && m.tier === BY_ID[b.list[idx].id].tier);
    const pool = same.length ? same : DATA.missions.filter((m) => !taken.includes(m.id));
    const fresh = pool[Math.floor(Math.random() * pool.length)];
    if (!fresh) return;
    b.list[idx] = { id: fresh.id, n: 0, claimed: false };
    b.rerolls += 1;
    store(p, b);
    safe(() => p.sendMessage(`§5New mission: §f${fresh.title}`));
  }
}

function payCoins(p, amount) {
  take(p, 'bc:doubloon', amount);
}

/** A short summary for the handbook. */
export function missionSummary(p) {
  const b = board(p);
  return b.list.map((s) => {
    const m = BY_ID[s.id];
    const st = s.claimed ? '§8claimed' : done(s) ? '§adone - claim it' : `§f${Math.floor(s.n)}/${m.count}`;
    return `§6${DATA.glyphs.star.repeat(m.tier)} §f${m.title}: ${st}`;
  }).join('\n');
}

system.beforeEvents.startup.subscribe((ev) => {
  ev.blockComponentRegistry.registerCustomComponent('bc:mission_board', {
    onPlayerInteract(e) {
      const p = e.player;
      if (!(p instanceof Player)) return;
      system.run(() => openBoard(p).catch(() => {}));
    },
  });
});
