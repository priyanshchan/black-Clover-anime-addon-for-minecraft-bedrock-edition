// Abyssal Seas expansion entry point: item routing and melee hooks.
import { system } from '@minecraft/server';
import { particle, sound } from '../core/fx.js';
import { V, isCreative, safe } from '../core/util.js';
import './bounty.js';
import './captains.js';
import { onFruitMelee, usePower } from './fruits.js';
import { useLure } from './leviathan.js';
import { fireCannon, placeShip } from './ship.js';
import './structures.js';
import { addWillXp, onWillMelee } from './will.js';

/** @returns {boolean} true when the item belonged to the expansion */
export function useSeaItem(p, item) {
  const id = item.typeId;
  if (id.startsWith('bc:power_')) usePower(p, item);
  else if (id === 'bc:ship_kit') placeShip(p);
  else if (id === 'bc:cannonball') fireCannon(p);
  else if (id === 'bc:leviathan_lure') useLure(p);
  else if (id === 'bc:leviathan_scale') {
    addWillXp(p, 40);
    particle(p.dimension, 'bc:will_spark', V.add(p.location, { x: 0, y: 1, z: 0 }), { scale: 1.2 });
    sound(p.dimension, 'bc.will.pulse', p.location, 0.8, 1.3);
    if (!isCreative(p)) {
      const inv = p.getComponent('minecraft:inventory')?.container;
      const it = inv?.getItem(p.selectedSlotIndex);
      if (it?.typeId === id) {
        if (it.amount > 1) {
          it.amount -= 1;
          inv.setItem(p.selectedSlotIndex, it);
        } else inv.setItem(p.selectedSlotIndex, undefined);
      }
    }
    safe(() => p.onScreenDisplay.setActionBar("§5You absorb the Leviathan's will (+40 Will XP)"));
  } else return false;
  return true;
}

export function onSeaMelee(p, target) {
  onWillMelee(p, target);
  onFruitMelee(p, target);
}

export { system };
