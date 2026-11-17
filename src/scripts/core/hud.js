// Action-bar HUD: attribute icon, selected spell, cooldown and a glyph mana bar.
import { system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { maxMana, spellsOf, state } from './data.js';
import { isCreative, now, safe } from './util.js';

const G = DATA.glyphs;
const PIPS = 12;

function bar(value, max, anti = false) {
  const frac = max > 0 ? value / max : 0;
  const total = frac * PIPS;
  let s = G.capL;
  for (let i = 0; i < PIPS; i++) {
    const v = total - i;
    if (anti) s += v >= 0.75 ? G.antiFull : v >= 0.25 ? G.antiHalf : G.antiEmpty;
    else s += v >= 0.75 ? G.full : v >= 0.25 ? G.half : G.empty;
  }
  return s + G.capR;
}

function heldId(player) {
  return safe(() => player.getComponent('minecraft:inventory')?.container?.getItem(player.selectedSlotIndex)?.typeId) ?? '';
}

export function heldKind(player) {
  const item = { typeId: heldId(player) };
  if (!item.typeId) return '';
  if (item.typeId.startsWith('bc:grimoire_')) return 'grimoire';
  if (item.typeId.endsWith('_sword') && item.typeId.startsWith('bc:demon_')) return 'sword';
  return '';
}

/** Build the HUD text for a player. */
export function hudText(player) {
  const s = state(player);
  let attr = s.attr;
  let level = s.level;
  const held = heldId(player);
  if (isCreative(player) && held.startsWith('bc:grimoire_')) {
    attr = held.slice('bc:grimoire_'.length);
    level = 20;
  }
  if (!attr) return `${G.clover3} §7No grimoire yet - visit a §dGrimoire Altar§7.`;
  const a = DATA.attributes[attr];
  const spells = spellsOf(attr);
  const sp = spells[s.spell] ?? spells[0];
  const t = now();
  let spellPart;
  if (!sp) spellPart = '';
  else if (level < sp.level) spellPart = `${G.lock} §8${sp.name} §7(Lv ${sp.level})`;
  else {
    const ready = s.cd.get(sp.id) ?? 0;
    if (ready > t) spellPart = `§7${sp.name} §c${((ready - t) / 20).toFixed(1)}s`;
    else spellPart = `${a.mc}§l${sp.name}§r`;
  }
  const idx = `§8[${s.spell + 1}/${spells.length}]`;
  if (attr === 'anti') {
    const g = Math.floor(s.anti);
    return `${a.glyph} ${spellPart} ${idx}  ${bar(s.anti, 100, true)} §c${g}§7%  §e${G.star}${level}`;
  }
  const mx = maxMana(player, s);
  return `${a.glyph} ${spellPart} ${idx}  ${bar(s.mana, mx)} §b${Math.floor(s.mana)}§7/${mx}  §e${G.star}${level}`;
}

export function showHud(player) {
  safe(() => player.onScreenDisplay.setActionBar(hudText(player)), 'hud');
}

system.runInterval(() => {
  const t = now();
  for (const p of world.getAllPlayers()) {
    const kind = heldKind(p);
    const s = state(p);
    if (kind || t - s.lastCast < 60) showHud(p);
  }
}, 4);
