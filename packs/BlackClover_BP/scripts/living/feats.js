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
/** @type {Map<string, {c: Record<string, number>, done: string[], kinds: string[], title: string}>} */
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
  f = { c: {}, done: [], kinds: [], title: '', ...(f ?? {}) };
  cache.set(p.id, f);
  return f;
}
function save(p) {
  safe(() => p.setDynamicProperty(KEY, JSON.stringify(feats(p))));
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

// slow checks: level, party, bonds, fruit, brooms
system.runInterval(() => {
  for (const p of world.getAllPlayers()) safe(() => {
    atLeast(p, 'level', state(p).level);
    const pt = party(p);
    atLeast(p, 'party', pt.m.length);
    if (pt.m.some((m) => bondRank(m.bond) >= 4) || pt.r.some((m) => bondRank(m.bond) >= 4)) atLeast(p, 'soulbound', 1);
    if (sea(p).fruit) atLeast(p, 'fruit', 1);
    if (safe(() => p.getComponent('minecraft:riding')?.entityRidingOn?.typeId) === 'bc:broom') atLeast(p, 'broom', 1);
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
