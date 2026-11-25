// Wanderers (v1.1.0): travellers on the roads of the kingdom - pilgrims, cartographers, peddlers, hermit mages, bards and
// lost Magic Knights - each with a name of their own. Talk to one: they tell rumours that point at real landmarks nearby,
// trade odd things (Explorer's Maps, rolled relics and weapons, scrolls, tales), and sometimes ask a favour - bring them
// something, or deal with a landmark - for a reward. A lost knight may join your squad. They come more often to
// Sanctuaries, the Noble Realm and on a Merchants' Fair day, and move on after a while.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { ActionFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { emit, on } from '../core/bus.js';
import { effect } from '../core/combat.js';
import { particle, rgb, sound } from '../core/fx.js';
import { makeRelic, makeWeapon } from '../core/loot.js';
import { mods } from '../core/mods.js';
import { makeScroll } from '../core/scrolls.js';
import { V, alive, pick, rand, safe } from '../core/util.js';
import { countCoins, giveCoins, takeCoins } from '../sea/bounty.js';
import { joinParty } from './companions.js';
import { behind } from './events.js';
import { makeExplorerMap, makeJournal } from './exploration.js';
import { setupKnight } from './knights.js';
import { nameOf, nearestUnfound, setResidentMaker, slotsNear } from './landmarks.js';
import { omen } from './omens.js';
import { compassWord, currentRegion, starsAt, traitsAt } from './regions.js';

const W = DATA.world;
const KINDS = Object.keys(W.wanderers);
const LIFE = 12 * 60 * 1000; // twelve minutes (real time, so it survives a reload)

/** @typedef {{label: string, price: number, give: string}} Offer */

/** Bring a wanderer into the world. */
export function spawnWanderer(dim, loc, kind = '', opts = {}) {
  const k = kind || pick(KINDS);
  const info = W.wanderers[k];
  const e = safe(() => dim.spawnEntity('bc:wanderer', loc, { spawnEvent: `bc:look_${info.look}` }));
  if (!e) return undefined;
  const name = `${pick(W.wandererFirst)} ${pick(W.wandererEpithet)}`;
  const titleText = opts.title ?? info.title;
  safe(() => {
    e.setDynamicProperty('bc:wkind', k);
    e.setDynamicProperty('bc:wname', name);
    e.setDynamicProperty('bc:wtitle', titleText);
    e.setDynamicProperty('bc:wborn', Date.now());
    if (opts.stay) e.setDynamicProperty('bc:wstay', true);
    e.nameTag = `§e${name}\n§7${titleText}`;
  });
  return e;
}
setResidentMaker((dim, loc, kind, opts) => spawnWanderer(dim, loc, kind, opts));

// ------------------------------------------------------------------------------- arriving and leaving
function chanceFor(p) {
  let c = 0.08;
  const traits = traitsAt(p.location);
  if (traits.includes('sanctuary')) c *= 2.5;
  if (omen() === 'merchants_fair') c *= 3;
  if (currentRegion(p)?.realm === 'noble') c *= 1.5;
  const t = safe(() => world.getTimeOfDay()) ?? 6000;
  if (t > 13000 && t < 23000) c *= 0.4;
  return c;
}
system.runInterval(() => {
  for (const p of world.getAllPlayers()) safe(() => {
    if (p.dimension.id !== 'minecraft:overworld' || Math.random() >= chanceFor(p)) return;
    const near = safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 96, type: 'bc:wanderer' }).length) ?? 0;
    if (near >= 2) return;
    const at = behind(p, 28, 40);
    if (!at) return;
    const e = spawnWanderer(p.dimension, at);
    if (e) safe(() => p.onScreenDisplay.setActionBar('§eA traveller is on the road nearby.'));
  }, 'wandererArrive');
  const t = Date.now();
  for (const p of world.getAllPlayers()) {
    for (const e of safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 128, type: 'bc:wanderer' })) ?? []) safe(() => {
      if (e.getDynamicProperty('bc:wstay') === true) return;
      const born = e.getDynamicProperty('bc:wborn');
      if (typeof born !== 'number' || t - born < LIFE) return;
      if (e.dimension.getPlayers({ location: e.location, maxDistance: 20 }).length) return;
      particle(e.dimension, 'bc:smoke_burst', e.location, { scale: 0.5 });
      e.remove();
    });
  }
}, 1800);

// ------------------------------------------------------------------------------- what they say
function rumor(p) {
  const s = nearestUnfound(p, '', 700);
  const reg = currentRegion(p);
  if (!s) return reg ? reg.lore : 'The roads are quiet these days.';
  const d = Math.round(Math.hypot(s.x - p.location.x, s.z - p.location.z) / 10) * 10;
  const what = nameOf(s.kind);
  const article = /s$/.test(what) ? 'the' : /^[AEIOU]/i.test(what) ? 'an' : 'a';
  return pick(W.rumors).replace('a {what}', `${article} ${what}`).replace('the {what}', `the ${what}`).replace('{what}', what).replace('{dir}', compassWord(s.x - p.location.x, s.z - p.location.z))
    .replace('{dist}', String(d)).replace('{region}', reg?.name ?? 'these parts');
}

// ------------------------------------------------------------------------------- trades
/** @returns {Offer[]} */
function stockFor(kind) {
  if (kind === 'cartographer') {
    return [{ label: 'Explorer\'s Map (a Mage Spire)', price: 80, give: 'map:spire' }, { label: 'Explorer\'s Map (a Wyvern Roost)', price: 80, give: 'map:roost' },
      { label: 'Explorer\'s Map (anything unknown)', price: 50, give: 'map:' }, { label: 'Treasure Map', price: 120, give: 'tmap' }];
  }
  if (kind === 'peddler') {
    return [{ label: 'A mysterious relic', price: 90 + Math.floor(Math.random() * 6) * 20, give: 'relic' }, { label: 'A well-made weapon', price: 80 + Math.floor(Math.random() * 6) * 20, give: 'weapon' },
      { label: 'Mana Potions x2', price: 40, give: 'item:bc:mana_potion:2' }, { label: 'Smoke Bombs x3', price: 30, give: 'item:bc:smoke_bomb:3' }];
  }
  if (kind === 'hermit') {
    return [{ label: 'Spell Scroll', price: 70, give: 'scroll' }, { label: 'Greater Mana Potion', price: 90, give: 'item:bc:greater_mana_potion:1' },
      { label: 'Sprite Dust x3', price: 45, give: 'item:bc:sprite_dust:3' }, { label: 'A relic of the old magic', price: 160, give: 'relic:rare' }];
  }
  if (kind === 'bard') {
    return [{ label: 'A tale (a journal page)', price: 10, give: 'journal' }, { label: 'A TRUE tale (a buried cache)', price: 60, give: 'journal:cache' },
      { label: 'A song of a famous blade', price: 400, give: 'weapon:epic' }];
  }
  if (kind === 'pilgrim') {
    return [{ label: 'Mana Cookies x4', price: 20, give: 'item:bc:mana_cookie:4' }, { label: 'Bread x6', price: 10, give: 'item:minecraft:bread:6' },
      { label: 'A pilgrim\'s blessing', price: 25, give: 'blessing' }, { label: 'Explorer\'s Map', price: 60, give: 'map:' }];
  }
  return [];
}
function priceOf(o) {
  return Math.max(1, Math.round(o.price * (omen() === 'merchants_fair' ? 0.8 : 1)));
}
function give(p, it) {
  const left = p.getComponent('minecraft:inventory')?.container?.addItem(it);
  if (left) p.dimension.spawnItem(left, p.location);
}
function deliver(p, o) {
  const stars = starsAt(p.location);
  const luck = mods(p).luck;
  const [what, a, b, c] = o.give.split(':');
  if (what === 'map') give(p, makeExplorerMap(p, a ?? ''));
  else if (what === 'tmap') give(p, new ItemStack('bc:treasure_map', 1));
  else if (what === 'relic') give(p, makeRelic(stars, { min: a || 'uncommon', luck }));
  else if (what === 'weapon') give(p, makeWeapon(stars, { min: a || 'uncommon', luck }));
  else if (what === 'scroll') give(p, makeScroll());
  else if (what === 'journal') give(p, makeJournal(stars, a === 'cache'));
  else if (what === 'blessing') {
    effect(p, 'regeneration', 180, 0, false);
    effect(p, 'speed', 180, 0, false);
    particle(p.dimension, 'bc:heal', p.location, { scale: 0.8 });
  } else if (what === 'item') give(p, new ItemStack(`${a}:${b}`, Number(c) || 1));
}

// ------------------------------------------------------------------------------- requests
/** @typedef {{kind: 'fetch' | 'landmark', who: string, item?: string, n?: number, slot?: string, what?: string, x?: number, z?: number}} Request */
function requestsOf(p) {
  try {
    const v = p.getDynamicProperty('bc:requests');
    return /** @type {Request[]} */ (typeof v === 'string' ? JSON.parse(v) : []);
  } catch {
    return [];
  }
}
function saveRequests(p, list) {
  safe(() => p.setDynamicProperty('bc:requests', JSON.stringify(list.slice(-4))));
}
function rewardRequest(p, req) {
  const coins = 30 + Math.floor(Math.random() * 50);
  giveCoins(p, coins);
  if (Math.random() < 0.6) give(p, makeRelic(starsAt(p.location) + 1, { min: 'uncommon', luck: mods(p).luck }));
  sound(p.dimension, 'bc.coins', p.location, 1, 1.1);
  safe(() => p.sendMessage(`§a${req.who}'s request is done! §7+§6${coins} doubloons§7 and their thanks.`));
  emit('request', p);
}
/** A wanderer's request, rolled (or undefined when they need nothing). */
function rollRequest(p, who) {
  if (Math.random() < 0.55) {
    const [item, lo, hi] = pick(W.fetch);
    return { kind: 'fetch', who, item, n: lo + Math.floor(Math.random() * (hi - lo + 1)) };
  }
  const s = nearestUnfound(p, '', 600);
  if (!s) return undefined;
  return { kind: 'landmark', who, slot: s.id, what: nameOf(s.kind), x: s.x, z: s.z };
}
function countItem(p, id) {
  const inv = p.getComponent('minecraft:inventory')?.container;
  let n = 0;
  for (let i = 0; inv && i < inv.size; i++) {
    const it = inv.getItem(i);
    if (it?.typeId === id) n += it.amount;
  }
  return n;
}
function takeItem(p, id, n) {
  if (id === 'bc:doubloon') return takeCoins(p, n);
  const inv = p.getComponent('minecraft:inventory')?.container;
  if (!inv || countItem(p, id) < n) return false;
  let left = n;
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
  return true;
}
const itemName = (id) => (id.startsWith('bc:') ? (DATA.world.items[id.slice(3)]?.name ?? id.slice(3).replace(/_/g, ' ')) : id.replace('minecraft:', '').replace(/_/g, ' ')).replace(/§./g, '');

// a landmark request is done when the landmark's master falls, or its chest is opened
function landmarkDone(p, rec) {
  const list = requestsOf(p);
  const k = list.findIndex((r) => r.kind === 'landmark' && r.slot === rec.id);
  if (k < 0) return;
  const [req] = list.splice(k, 1);
  saveRequests(p, list);
  rewardRequest(p, req);
}
on('landmark_clear', landmarkDone);
on('landmark_loot', landmarkDone);

// ------------------------------------------------------------------------------- talking
export async function talk(p, e) {
  const kind = String(safe(() => e.getDynamicProperty('bc:wkind')) ?? 'pilgrim');
  const name = String(safe(() => e.getDynamicProperty('bc:wname')) ?? 'Traveller');
  const titleText = String(safe(() => e.getDynamicProperty('bc:wtitle')) ?? W.wanderers[kind]?.title ?? 'Wanderer');
  safe(() => e.teleport(e.location, { facingLocation: p.location }));
  // the favour they want of you (rolled once per wanderer)
  let reqRaw = safe(() => e.getDynamicProperty('bc:wreq'));
  if (reqRaw === undefined && kind !== 'lost_knight') {
    const r = Math.random() < 0.5 ? rollRequest(p, name) : undefined;
    reqRaw = r ? JSON.stringify(r) : 'none';
    safe(() => e.setDynamicProperty('bc:wreq', reqRaw));
  }
  /** @type {Request | undefined} */
  const req = typeof reqRaw === 'string' && reqRaw !== 'none' ? JSON.parse(reqRaw) : undefined;
  const stock = stockFor(kind);
  const coins = countCoins(p);
  const f = new ActionFormData().title(`§l${name}`).body(`§7${titleText}\n\n§f"${pick(W.greetings[kind] ?? ['Well met.'])}"\n\n§7"${rumor(p)}"\n\n§ePurse: ${DATA.glyphs.coin} ${coins}`);
  /** @type {(() => any)[]} */
  const acts = [];
  for (const o of stock) {
    const price = priceOf(o);
    f.button(`${coins >= price ? '§0' : '§8'}§l${o.label}\n§r${coins >= price ? '§6' : '§c'}${price} doubloons`);
    acts.push(() => {
      if (!takeCoins(p, price)) {
        safe(() => p.sendMessage(`§7"That's §6${price}§7, friend. Come back when your purse is heavier."`));
        return;
      }
      deliver(p, o);
      sound(p.dimension, 'bc.coins', p.location, 1, 1);
      safe(() => p.sendMessage(`§a"A fine choice!" §7(${o.label})`));
    });
  }
  if (req && req.kind === 'fetch' && req.item && req.n) {
    const have = countItem(p, req.item);
    f.button(`§l${have >= req.n ? '§2Hand over' : 'A favour:'} ${req.n} ${itemName(req.item)}\n§r§8${have >= req.n ? 'you have them' : `you have ${have}`}`);
    acts.push(() => {
      if (!takeItem(p, req.item, req.n)) {
        safe(() => p.sendMessage(`§7"${name}: I need §f${req.n} ${itemName(req.item)}§7. Would you find them for me?"`));
        return;
      }
      safe(() => e.setDynamicProperty('bc:wreq', 'none'));
      rewardRequest(p, req);
    });
  } else if (req && req.kind === 'landmark') {
    f.button(`§lA favour: the ${req.what}\n§r§8${compassWord((req.x ?? 0) - p.location.x, (req.z ?? 0) - p.location.z)}, ${Math.round(Math.hypot((req.x ?? 0) - p.location.x, (req.z ?? 0) - p.location.z))} blocks`);
    acts.push(() => {
      const list = requestsOf(p);
      if (!list.some((r) => r.slot === req.slot)) list.push(req);
      saveRequests(p, list);
      safe(() => e.setDynamicProperty('bc:wreq', 'none'));
      safe(() => p.sendMessage(`§7"${name}: Find the §6${req.what}§7 ${compassWord((req.x ?? 0) - p.location.x, (req.z ?? 0) - p.location.z)} of here - defeat whatever guards it, or bring back its treasure. I'll know." §8(The reward comes when it is done.)`));
      safe(() => p.setDynamicProperty('bc:track_lm', req.slot));
    });
  }
  if (kind === 'lost_knight') {
    f.button('§l§2"Join my squad"\n§r§8A Magic Knight with nowhere to go');
    acts.push(() => {
      const k = safe(() => e.dimension.spawnEntity('bc:magic_knight', e.location));
      if (!k) return;
      setupKnight(k, { name, level: 2 + Math.floor(Math.random() * 5), randomRobe: true });
      if (joinParty(k, p, 80)) {
        safe(() => p.sendMessage(`§b${name}§f: A squad again... Thank you. I won't let you down.`));
        safe(() => e.remove());
      } else {
        safe(() => k.remove());
        safe(() => p.sendMessage('§7Your squad and reserve are full.'));
      }
    });
  }
  f.button('§8Farewell');
  sound(p.dimension, 'random.orb', p.location, 0.5, 1.2);
  const r = await f.show(p);
  if (r.canceled || r.selection === undefined) return;
  await acts[r.selection]?.();
}

world.afterEvents.playerInteractWithEntity.subscribe((ev) => {
  if (ev.target.typeId !== 'bc:wanderer') return;
  const p = ev.player;
  const e = ev.target;
  system.run(() => talk(p, e).catch(() => {}));
});

// cheat: /scriptevent bc:wanderer [kind]
system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (ev.id !== 'bc:wanderer') return;
  const p = ev.sourceEntity instanceof Player ? ev.sourceEntity : world.getAllPlayers()[0];
  if (!p) return;
  const want = ev.message.trim();
  const dir = V.flat(p.getViewDirection());
  spawnWanderer(p.dimension, V.add(p.location, { x: dir.x * 4, y: 0, z: dir.z * 4 }), KINDS.includes(want) ? want : '');
});

export { alive, rand, rgb, slotsNear };
