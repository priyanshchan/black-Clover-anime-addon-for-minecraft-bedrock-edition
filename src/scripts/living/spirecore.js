// The Spire Core (v1.1.0): the heart of a Spire Warden. Use it and a Mana Waygate rises in front of you, already part
// of the network - a way back to wherever you are, from anywhere.
import { BlockPermutation } from '@minecraft/server';
import { particle, rgb, sound } from '../core/fx.js';
import { V, safe } from '../core/util.js';
import { addGate } from './waygate.js';
import { regionAt } from './regions.js';

/** @returns {boolean} true when a gate was raised (and the core is spent) */
export function useSpireCore(p) {
  const dir = V.flat(p.getViewDirection());
  const at = { x: Math.floor(p.location.x + dir.x * 2), y: Math.floor(p.location.y), z: Math.floor(p.location.z + dir.z * 2) };
  const b = safe(() => p.dimension.getBlock(at));
  if (!b || !b.isAir) {
    safe(() => p.onScreenDisplay.setActionBar('§7The core needs an open space in front of you.'));
    return false;
  }
  safe(() => b.setPermutation(BlockPermutation.resolve('bc:waygate')));
  const reg = regionAt(at.x, at.z);
  addGate(p, at, `Spire Gate${reg ? ` of ${reg.base}` : ''}`.slice(0, 24));
  particle(p.dimension, 'bc:pillar', at, { color: rgb('60e0ff'), scale: 1.4 });
  sound(p.dimension, 'bc.portal', at, 1, 1.2);
  return true;
}
