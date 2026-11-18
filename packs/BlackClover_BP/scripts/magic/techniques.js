// Advanced mana techniques and robe passives.
//   Level 12  Mana Skin  - a coat of mana soaks up part of every hit (costs mana)
//   Level 15  Mana Zone  - hold your grimoire, Sneak + Jump: 20 s zone of faster, stronger casting
import { ButtonState, InputButton, Player, system, world } from '@minecraft/server';
import { maxMana, robe, state } from '../core/data.js';
import { COLORS, particle, shockwave, sound, title } from '../core/fx.js';
import { V, safe } from '../core/util.js';

/** @type {Map<string, {center: {x:number,y:number,z:number}, dim: string, until: number}>} */
const zones = new Map();
const zoneCd = new Map();
const lastHurt = new Map();

/** Bonus for casting inside your own Mana Zone. */
export function zoneBonus(p) {
  const z = zones.get(p.id);
  if (!z || z.until < system.currentTick || z.dim !== p.dimension.id) return { cd: 1, pw: 1, regen: 1 };
  if (V.dist(z.center, p.location) > 12) return { cd: 1, pw: 1, regen: 1 };
  return { cd: 0.5, pw: 1.2, regen: 2 };
}

world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const p = ev.hurtEntity;
  if (!(p instanceof Player)) return;
  lastHurt.set(p.id, system.currentTick);
  const s = state(p);
  if (!s.attr || s.attr === 'anti' || s.level < 12) return;
  const mx = maxMana(p, s);
  const soak = ev.damage * 0.25;
  const cost = soak * 3;
  if (s.mana < mx * 0.2 + cost) return;
  const hp = p.getComponent('minecraft:health');
  if (!hp || hp.currentValue <= 0) return;
  safe(() => hp.setCurrentValue(Math.min(hp.effectiveMax, hp.currentValue + soak)));
  s.mana -= cost;
  s.dirty = true;
  particle(p.dimension, 'bc:mana_aura', p.location, { color: COLORS[s.attr] ?? COLORS.water, scale: 1.2 });
}, 'manaSkin'));

system.runInterval(() => {
  const t = system.currentTick;
  for (const p of world.getAllPlayers()) {
    safe(() => {
      const s = state(p);
      // Mana Zone activation
      if (s.attr && s.attr !== 'anti' && s.level >= 15 && p.isSneaking) {
        const held = p.getComponent('minecraft:inventory')?.container?.getItem(p.selectedSlotIndex)?.typeId;
        if (held === `bc:grimoire_${s.attr}` && (zoneCd.get(p.id) ?? 0) <= t
          && p.inputInfo.getButtonState(InputButton.Jump) === ButtonState.Pressed) {
          zoneCd.set(p.id, t + 1200);
          zones.set(p.id, { center: { ...p.location }, dim: p.dimension.id, until: t + 400 });
          title(p, `§b§lMANA ZONE`, '§7Your mana bends the world around you', 30);
          sound(p.dimension, 'bc.cast', p.location, 1.4, 0.6);
          shockwave(p.dimension, p.location, s.attr, 12);
        }
      }
      const z = zones.get(p.id);
      if (z && z.until >= t && t % 30 === 0) {
        particle(p.dimension, 'bc:magic_circle_ground', z.center, { color: COLORS[s.attr] ?? COLORS.water, size: 24, life: 1.6 });
      }
      // robe passives
      const r = robe(p);
      if (r === 'purple_orca_robe') safe(() => p.addEffect('water_breathing', 60, { amplifier: 0, showParticles: false }));
      if (r === 'aqua_deer_robe' && t - (lastHurt.get(p.id) ?? -1000) > 100) safe(() => p.addEffect('speed', 60, { amplifier: 0, showParticles: false }));
    });
  }
}, 4);

export function wasRecentlyHurt(p, ticks = 100) {
  return system.currentTick - (lastHurt.get(p.id) ?? -1000) < ticks;
}
