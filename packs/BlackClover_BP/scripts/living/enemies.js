// Small special rules for the v0.2.0 enemies (their fighting is in ai.js).
import { Player, world } from '@minecraft/server';
import { addMana, state } from '../core/data.js';
import { center } from '../core/combat.js';
import { particle, rgb } from '../core/fx.js';
import { safe } from '../core/util.js';

// Mana Wraiths feed on magic: every hit drains a player's mana
world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const src = ev.damageSource.damagingEntity;
  const p = ev.hurtEntity;
  if (!src || src.typeId !== 'bc:mana_wraith' || !(p instanceof Player)) return;
  const s = state(p);
  if (!s.attr || s.attr === 'anti') return;
  addMana(p, -12);
  particle(p.dimension, 'bc:burst', center(p), { color: rgb('90ffe8'), scale: 0.5 });
  safe(() => p.onScreenDisplay.setActionBar('§3The wraith drinks your mana (-12)'));
}, 'wraith'));
