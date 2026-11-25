// Feats: lifetime achievements. Each one pays stars and doubloons and unlocks a title you can wear above your head
// (choose it in the Handbook). Progress is saved with the player.
import { Player, system, world } from '@minecraft/server';
import { ActionFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { on } from '../core/bus.js';
import { state } from '../core/data.js';
import { particle, sound, title } from '../core/fx.js';
import { addStars } from '../core/ranks.js';
import { safe } from '../core/util.js';
import { giveCoins } from '../sea/bounty.js';
import { sea } from '../sea/state.js';
import { bondRank, party } from './companions.js';

const KEY = 'bc:feats';
/** @type {Map<string, {c: Record<string, number>, done: string[], kinds: string[], sets: string[], title: string}>} */
const cache = new Map();

function feats(p) {
  let f = cache.get(p.id);
  if (f) return f;
  const raw = safe(() => p.getDynamicProperty(KEY));
  try {
    f = typeof raw === 'string' ? JSON.parse(raw) : undefined;
  } catch {
    f = undefined;
  }
  f = { c: {}, done: [], kinds: [], sets: [], title: '', ...(f ?? {}) };
  cache.set(p.id, f);
  return f;
}
/** @type {Set<string>} players with counts not yet written down */
const dirty = new Set();
function save(p) {
  dirty.delete(p.id);
  safe(() => p.setDynamicProperty(KEY, JSON.stringify(feats(p))));
}
/** A feat counter's value (v1.2.0: also for the Handbook and tests). */
export function featCount(p, counter) {
  return feats(p).c[counter] ?? 0;
}
world.afterEvents.playerLeave.subscribe((ev) => cache.delete(ev.playerId));

function check(p) {
  const f = feats(p);
  let changed = false;
  for (const ft of DATA.feats) {
    if (f.done.includes(ft.id) || (f.c[ft.counter] ?? 0) < ft.goal) continue;
    f.done.push(ft.id);
    changed = true;
    title(p, `§6§l${ft.name}`, `§7Feat complete - title unlocked: §6${ft.title}`, 60);
    safe(() => p.sendMessage(`§6★ Feat: §f${ft.name}§6 - ${ft.desc} §7(+${ft.coins} doubloons${ft.stars ? `, +${ft.stars} star${ft.stars > 1 ? 's' : ''}` : ''}; title "${ft.title}" in the Handbook)`));
    sound(p.dimension, 'bc.fanfare', p.location, 0.9, 1.2);
    particle(p.dimension, 'bc:level_up', p.location);
    if (ft.coins) giveCoins(p, ft.coins);
    if (ft.stars) safe(() => addStars(p, ft.stars, `feat: ${ft.name}`));
  }
  if (changed) save(p);
}

/** Count something towards the feats. */
export function bump(p, counter, n = 1) {
  if (!(p instanceof Player)) return;
  const f = feats(p);
  f.c[counter] = (f.c[counter] ?? 0) + n;
  check(p);
  dirty.add(p.id);
  if (system.currentTick % 20 === 0) save(p);
}
/** Set a counter to at least `n` (levels, party size...). */
function atLeast(p, counter, n) {
  const f = feats(p);
  if ((f.c[counter] ?? 0) >= n) return;
  f.c[counter] = n;
  check(p);
  save(p);
}

world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const k = ev.damageSource.damagingEntity;
  if (!(k instanceof Player)) return;
  const dead = ev.deadEntity;
  if (dead.typeId === 'bc:hive_egg') bump(k, 'eggs');
  if (safe(() => dead.matches({ families: ['monster'] }))) bump(k, 'kills');
}, 'featKills'));
on('boss', (p, typeId) => {
  bump(p, 'bosses');
  const f = feats(p);
  if (!f.kinds.includes(typeId)) {
    f.kinds.push(typeId);
    atLeast(p, 'boss_kinds', f.kinds.length);
  }
});
on('cast', (p) => bump(p, 'casts'));
on('mission', (p) => bump(p, 'missions'));
on('event_win', (p) => bump(p, 'events'));
on('elite', (p) => bump(p, 'elites'));
on('thief', (p) => bump(p, 'thieves'));
on('scroll', (p) => bump(p, 'scrolls'));
on('lair', (p) => bump(p, 'lairs'));
// v1.0.0
on('gate', (p) => bump(p, 'gates'));
// v1.1.0: the Untamed Kingdom
on('region', (p) => bump(p, 'regions'));
on('landmark', (p) => bump(p, 'landmarks'));
on('warden', (p) => bump(p, 'wardens'));
on('wyvern', (p) => bump(p, 'wyverns'));
on('legendary', (p) => atLeast(p, 'legendaries', 1));
on('mimic', (p) => bump(p, 'mimics'));
on('infernal', (p) => bump(p, 'infernals'));
on('request', (p) => bump(p, 'requests'));
// v1.2.0: Dragonbound & Kingdoms
on('hatch', (p) => bump(p, 'hatched'));
on('wyvern_adult', (p) => atLeast(p, 'adult_wyverns', 1));
on('wyvern_ride', (p) => atLeast(p, 'wyvern_rides', 1));
on('kingdom_kill', (p) => bump(p, 'kingdom_kills'));
on('commander', (p) => bump(p, 'commanders'));
on('heart_trade', (p) => bump(p, 'heart_trades'));
on('capital', (p) => atLeast(p, 'capital', 1));
on('waygate', (p) => bump(p, 'waygate'));
// v0.8.0: armour
on('forge', (p) => bump(p, 'forged'));
on('rune', (p) => bump(p, 'runes'));
on('reinforce', (p, level) => {
  if (level >= 5) atLeast(p, 'reinforce5', 1);
});
on('armor_set', (p, sid) => {
  const f = feats(p);
  atLeast(p, 'fullset', 1);
  if (!f.sets.includes(sid)) {
    f.sets.push(sid);
    atLeast(p, 'set_kinds', f.sets.length);
  }
});

// slow checks: level, party, bonds, fruit, brooms
system.runInterval(() => {
  for (const p of world.getAllPlayers()) safe(() => {
    atLeast(p, 'level', state(p).level);
    const pt = party(p);
    atLeast(p, 'party', pt.m.length);
    if (pt.m.some((m) => bondRank(m.bond) >= 4) || pt.r.some((m) => bondRank(m.bond) >= 4)) atLeast(p, 'soulbound', 1);
    if (sea(p).fruit) atLeast(p, 'fruit', 1);
    if (['storm', 'blossom', 'coral', 'dream'].includes(state(p).attr)) atLeast(p, 'new_grimoire', 1);
    if (safe(() => p.getComponent('minecraft:riding')?.entityRidingOn?.typeId) === 'bc:broom') atLeast(p, 'broom', 1);
    if (dirty.has(p.id)) save(p);   // counts are written down at least every two seconds
    const f = feats(p);
    const want = f.title ? `${p.name}\n§6${f.title}` : p.name;
    if (p.nameTag !== want) p.nameTag = want;
  }, 'feats');
}, 40);

/** The Handbook's Feats page. */
export async function featsPage(p, back) {
  const f = feats(p);
  const lines = DATA.feats.map((ft) => {
    const n = Math.min(ft.goal, f.c[ft.counter] ?? 0);
    return f.done.includes(ft.id) ? `§a✔ §f${ft.name} §8- ${ft.desc}` : `§8□ §7${ft.name} §8- ${ft.desc} §f${n}/${ft.goal}`;
  });
  const form = new ActionFormData().title(`Feats (${f.done.length}/${DATA.feats.length})`)
    .body(`§7Title: ${f.title ? `§6${f.title}` : '§8none'}\n\n${lines.join('\n')}`);
  form.button('§lChoose a title');
  form.button('Back');
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return;
  if (res.selection === 1) return back?.();
  const titles = DATA.feats.filter((ft) => f.done.includes(ft.id)).map((ft) => ft.title);
  const pickForm = new ActionFormData().title('Choose a title').body(titles.length ? '§7Shown under your name.' : '§7Complete feats to unlock titles.');
  pickForm.button('§8No title');
  for (const t of titles) pickForm.button(`§6${t}`);
  const r2 = await pickForm.show(p);
  if (r2.canceled || r2.selection === undefined) return;
  f.title = r2.selection === 0 ? '' : titles[r2.selection - 1];
  save(p);
  safe(() => p.sendMessage(f.title ? `§6You now go by "${f.title}".` : '§7Title removed.'));
}
