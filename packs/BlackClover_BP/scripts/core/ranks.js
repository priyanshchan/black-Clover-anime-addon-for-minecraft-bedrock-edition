// Magic Knight ranks: stars are earned for great deeds and raise your rank.
import { Player, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { particle, sound, title } from './fx.js';
import { safe } from './util.js';

export function stars(p) {
  const v = p.getDynamicProperty('bc:stars');
  return typeof v === 'number' ? v : 0;
}

export function rankIndex(n) {
  let idx = 0;
  DATA.ranks.forEach((r, i) => {
    if (n >= r.stars) idx = i;
  });
  return idx;
}

export function rankTitle(p) {
  return DATA.ranks[rankIndex(stars(p))].title;
}

export function addStars(p, n, why) {
  const before = rankIndex(stars(p));
  const total = stars(p) + n;
  p.setDynamicProperty('bc:stars', total);
  safe(() => p.sendMessage(`§6${DATA.glyphs.star.repeat(Math.min(n, 5))} §e+${n} star${n > 1 ? 's' : ''} §7(${why}) - ${total} total`));
  const after = rankIndex(total);
  if (after > before) {
    const r = DATA.ranks[after];
    title(p, `§6§l${r.title}`, '§eThe Magic Knights recognise your deeds (+5 max mana)', 70);
    sound(p.dimension, 'bc.fanfare', p.location, 1, 1);
    particle(p.dimension, 'bc:level_up', p.location);
    particle(p.dimension, 'bc:clover_leaves', p.location, { scale: 1.4 });
  }
}

const BOUNTIES = { 'bc:devil': [5, 'defeated a Devil'], 'bc:leviathan': [5, 'slew the Abyssal Leviathan'], 'bc:dungeon_golem': [3, 'cleared a dungeon'],
  'bc:tidewatch_commodore': [2, 'bested a Commodore'], 'bc:raider_captain': [1, 'defeated a Raider Captain'] };

world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const k = ev.damageSource.damagingEntity;
  if (!(k instanceof Player)) return;
  const id = safe(() => ev.deadEntity.typeId) ?? '';
  const b = BOUNTIES[id];
  if (b) addStars(k, b[0], b[1]);
}, 'stars'));
