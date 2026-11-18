// Potions, elixirs, smoke bombs and spell scrolls.
import { Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { emit } from '../core/bus.js';
import { center, effect, targetsAround } from '../core/combat.js';
import { addMana, maxMana, spellPower, state } from '../core/data.js';
import { particle, rgb, sound, title } from '../core/fx.js';
import { readScroll, scrollSpells } from '../core/scrolls.js';
import { V, isCreative, pick, safe } from '../core/util.js';
import { castSpec } from './engine.js';

world.afterEvents.itemCompleteUse.subscribe((ev) => safe(() => {
  const id = ev.itemStack.typeId;
  const p = ev.source;
  if (!(p instanceof Player)) return;
  const s = state(p);
  if (id === 'bc:mana_potion') {
    if (s.attr === 'anti') {
      s.anti = Math.min(100, s.anti + 30);
      s.dirty = true;
    } else addMana(p, 60);
    particle(p.dimension, 'bc:burst', center(p), { color: rgb('3ca8ff'), scale: 0.7 });
    safe(() => p.onScreenDisplay.setActionBar(s.attr === 'anti' ? '§c+30% Anti-Magic' : '§b+60 mana'));
  } else if (id === 'bc:greater_mana_potion') {
    if (s.attr === 'anti') {
      s.anti = 100;
      s.dirty = true;
    } else addMana(p, maxMana(p, s));
    effect(p, 'regeneration', 10, 0);
    particle(p.dimension, 'bc:level_up', p.location);
    safe(() => p.onScreenDisplay.setActionBar('§9Your mana surges back!'));
  } else if (id === 'bc:elixir_iron') {
    effect(p, 'resistance', 60, 1);
    effect(p, 'absorption', 60, 1);
    particle(p.dimension, 'bc:shockwave', p.location, { color: rgb('c8d0dc'), radius: 2 });
  } else if (id === 'bc:elixir_haste') {
    effect(p, 'speed', 60, 0);
    safe(() => p.setDynamicProperty('bc:haste_until', system.currentTick + 1200));
    particle(p.dimension, 'bc:burst_spark', center(p), { color: rgb('60e070'), scale: 0.8 });
    safe(() => p.onScreenDisplay.setActionBar('§aYour spells come faster (60 s)'));
  }
}, 'potion'));

function consume(p, id) {
  if (isCreative(p)) return;
  const inv = p.getComponent('minecraft:inventory')?.container;
  const it = inv?.getItem(p.selectedSlotIndex);
  if (it?.typeId !== id) return;
  if (it.amount > 1) {
    it.amount -= 1;
    inv.setItem(p.selectedSlotIndex, it);
  } else inv.setItem(p.selectedSlotIndex, undefined);
}

/** Smoke Bomb: blind everything around you and slip away. */
export function useSmokeBomb(p) {
  particle(p.dimension, 'bc:smoke_burst', center(p), { scale: 1.8 });
  particle(p.dimension, 'bc:fog_cloud', p.location, { scale: 0.5 });
  sound(p.dimension, 'random.fizz', p.location, 1.2, 0.6);
  for (const v of targetsAround(p.dimension, p.location, 6, p)) effect(v, 'blindness', 4, 0);
  effect(p, 'invisibility', 4, 0, false);
  effect(p, 'speed', 4, 1, false);
  consume(p, 'bc:smoke_bomb');
  return true;
}

/** Spell Scroll: cast the spell written on it (blank scrolls settle on a random spell). */
export function useScroll(p, item) {
  let w = readScroll(item);
  if (!w) {
    const c = pick(scrollSpells());
    w = { attr: c.attr, sp: c.sp };
  }
  const a = DATA.attributes[w.attr];
  const s = state(p);
  const pw = s.attr && s.attr !== 'anti' ? spellPower(p, s) : 1;
  title(p, ' ', `${a.mc}${w.sp.name}§7 - read from a scroll`, 30);
  particle(p.dimension, 'bc:magic_circle', V.add(center(p), V.mul(p.getViewDirection(), 1.2)), { color: rgb(a.color), size: 1.8, life: 0.6 });
  sound(p.dimension, 'bc.grimoire.flip', p.location, 1, 0.8);
  castSpec(p, w.sp.spec, `a:${w.attr}`, pw);
  consume(p, 'bc:spell_scroll');
  emit('scroll', p, w.sp.id);
  return true;
}

