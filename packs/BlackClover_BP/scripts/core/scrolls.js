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
  // lore lines must stay within 50 characters, so the description is wrapped
  const lines = [`${a.mc}${choice.sp.name} §7(${a.name} magic)`.slice(0, 50), ...wrap(choice.sp.desc, 46).slice(0, 6).map((l) => `§7${l}`),
    `§8spell:${choice.attr}:${choice.sp.id}`];
  safe(() => item.setLore(lines));
  return item;
}

/** Word-wrap text into lines of at most `width` characters. */
export function wrap(text, width) {
  const out = [];
  let cur = '';
  for (const w of String(text).split(/\s+/)) {
    if (cur && cur.length + 1 + w.length > width) {
      out.push(cur);
      cur = w.slice(0, width);
    } else cur = cur ? `${cur} ${w}` : w.slice(0, width);
  }
  if (cur) out.push(cur);
  return out;
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
