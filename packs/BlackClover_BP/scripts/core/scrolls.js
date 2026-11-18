// Spell Scrolls: a single spell from any grimoire, written on paper. The spell is kept in the item's lore
// (crafted scrolls are blank until read - then their runes settle on a random spell).
import { ItemStack } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { pick, safe } from './util.js';

/** Every spell a scroll can hold: engine recipes up to level 10 (no awakened spells, no anti-magic). */
export function scrollSpells() {
  const out = [];
  for (const a of DATA.order) {
    if (a === 'anti') continue;
    for (const sp of DATA.spells[a]) if (sp.spec && sp.level <= 10) out.push({ attr: a, sp });
  }
  return out;
}

/** A written scroll (a random spell unless one is given). */
export function makeScroll(attr, id) {
  const all = scrollSpells();
  const choice = (attr && all.find((x) => x.attr === attr && x.sp.id === id)) || pick(all);
  const item = new ItemStack('bc:spell_scroll', 1);
  const a = DATA.attributes[choice.attr];
  safe(() => item.setLore([`${a.mc}${choice.sp.name} §7(${a.name} magic)`, `§7${choice.sp.desc}`, `§8spell:${choice.attr}:${choice.sp.id}`]));
  return item;
}

/** The spell written on a scroll, or undefined for a blank one. */
export function readScroll(item) {
  const lore = safe(() => item?.getLore?.()) ?? [];
  const line = lore.find((l) => l.includes('spell:'));
  if (!line) return undefined;
  const [, attr, id] = line.replace(/§./g, '').split(':');
  const sp = DATA.spells[attr]?.find((x) => x.id === id);
  return sp?.spec ? { attr, sp } : undefined;
}
