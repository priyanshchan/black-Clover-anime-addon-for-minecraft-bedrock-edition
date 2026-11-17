// Grimoire use: spell selection, mana / cooldown checks, casting and regeneration.
import { system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { addMana, maxMana, regenPerSecond, robe, spellPower, spellsOf, state } from '../core/data.js';
import { castCircle, particle, sound } from '../core/fx.js';
import { showHud } from '../core/hud.js';
import { addXp } from '../core/progress.js';
import { isCreative, safe } from '../core/util.js';
import { ANTI_SPELLS } from './antimagic.js';
import { SPELLS } from './spells.js';
import { SPELLS2 } from './spells2.js';
import { zoneBonus } from './techniques.js';

const IMPL = { ...SPELLS, ...SPELLS2, ...ANTI_SPELLS };

/** @param {import('@minecraft/server').Player} p @param {import('@minecraft/server').ItemStack} item */
export function useGrimoire(p, item) {
  const s = state(p);
  const itemAttr = item.typeId.slice('bc:grimoire_'.length);
  const creative = isCreative(p);
  if (!s.attr && !creative) {
    safe(() => p.sendMessage('§7The grimoire stays shut. §fReceive your own grimoire at a §dGrimoire Altar§f first.'));
    return;
  }
  if (s.attr !== itemAttr && !creative) {
    safe(() => p.sendMessage(`§7This ${DATA.attributes[itemAttr]?.name ?? ''} grimoire does not answer to you.`));
    sound(p.dimension, 'bc.mana.empty', p.location, 0.6, 1);
    return;
  }
  // creative players may borrow any grimoire for testing
  const attr = itemAttr;
  const level = creative ? 20 : s.level;
  const spells = spellsOf(attr);
  if (s.spell >= spells.length) s.spell = 0;

  if (p.isSneaking) {
    cycle(p, spells, level, attr);
    return;
  }
  const sp = spells[s.spell];
  if (!sp) return;
  if (level < sp.level) {
    safe(() => p.onScreenDisplay.setActionBar(`${DATA.glyphs.lock} §8${sp.name} §7unlocks at level §e${sp.level}`));
    return;
  }
  const t = system.currentTick;
  const ready = s.cd.get(sp.id) ?? 0;
  if (ready > t) {
    s.lastCast = t;
    showHud(p);
    return;
  }
  let cost = sp.mana;
  if (attr === 'flame' && robe(p) === 'crimson_lion_robe') cost = Math.round(cost * 0.85);
  if (!creative && s.mana < cost) {
    sound(p.dimension, 'bc.mana.empty', p.location, 0.8, 1);
    safe(() => p.onScreenDisplay.setActionBar(`§9Not enough mana §7(${Math.floor(s.mana)}/${cost})`));
    s.lastCast = t;
    return;
  }
  const impl = IMPL[sp.id];
  if (!impl) return;
  if (!creative) s.mana -= cost;
  const zone = zoneBonus(p);
  const cdMul = (robe(p) === 'green_mantis_robe' ? 0.85 : 1) * zone.cd;
  s.cd.set(sp.id, t + Math.round(sp.cooldown * 20 * cdMul));
  if (!creative && cost > 0 && robe(p) === 'coral_peacock_robe' && Math.random() < 0.2) {
    s.mana += cost;
    safe(() => p.onScreenDisplay.setActionBar('§dCoral Peacock: §7mana refunded!'));
  }
  s.lastCast = t;
  s.dirty = true;
  const ctx = { p, dim: p.dimension, attr, pw: (creative ? 1 + 19 * 0.05 : spellPower(p, s)) * zone.pw };
  if (attr !== 'anti') {
    castCircle(p, attr, sp.level >= 10 ? 2.6 : sp.level >= 6 ? 2.0 : 1.5);
    sound(p.dimension, 'bc.cast', p.location, 0.7, 0.9 + Math.random() * 0.2);
  }
  const ok = safe(() => impl(ctx), `spell:${sp.id}`);
  if (ok === false) {
    if (!creative) s.mana += cost;
    s.cd.delete(sp.id);
  } else if (!creative && s.attr === attr) {
    addXp(p, 2 + Math.round(cost / 10));
  }
  showHud(p);
}

function cycle(p, spells, level, attr) {
  const s = state(p);
  for (let k = 1; k <= spells.length; k++) {
    const idx = (s.spell + k) % spells.length;
    if (spells[idx].level <= level) {
      s.spell = idx;
      break;
    }
  }
  s.lastCast = system.currentTick;
  s.dirty = true;
  sound(p.dimension, 'bc.grimoire.flip', p.location, 0.8, 1 + Math.random() * 0.2);
  const sp = spells[s.spell];
  const a = DATA.attributes[attr] ?? DATA.attributes.wind;
  safe(() => p.onScreenDisplay.setTitle(' ', { fadeInDuration: 0, stayDuration: 30, fadeOutDuration: 8, subtitle: `${a.mc}${sp.name} §7- ${sp.desc}` }));
  showHud(p);
}

// ------------------------------------------------------------------------- regeneration
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    const s = state(p);
    if (!s.attr || s.attr === 'anti') continue;
    const mx = maxMana(p, s);
    if (s.mana < mx) addMana(p, (regenPerSecond(p, s) * zoneBonus(p).regen) / 5);
    else if (s.mana > mx) s.mana = mx;
  }
}, 4);

/** Gentle mana aura while holding your grimoire. */
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    const s = state(p);
    if (!s.attr) continue;
    const held = safe(() => p.getComponent('minecraft:inventory')?.container?.getItem(p.selectedSlotIndex)?.typeId);
    if (held === `bc:grimoire_${s.attr}`) {
      const color = DATA.attributes[s.attr].color;
      particle(p.dimension, 'bc:mana_aura', p.location, {
        color: { red: parseInt(color.slice(0, 2), 16) / 255, green: parseInt(color.slice(2, 4), 16) / 255, blue: parseInt(color.slice(4, 6), 16) / 255 },
      });
    }
  }
}, 16);
