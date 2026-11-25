// Wild magic (v1.1.0): in Wild Magic regions, and everywhere on a Wild Surge day, a spell sometimes surges - it costs
// nothing, or it echoes a second time - and sometimes it misfires and fizzles in your hands.
import { state } from './data.js';
import { particle, rgb, sound } from './fx.js';
import { safe } from './util.js';

export const SURGE = 0.08;
export const MISFIRE = 0.04;

/** @returns {'' | 'free' | 'twice' | 'misfire'} */
export function wildMagic(p, cost, roll = Math.random()) {
  const at = { x: p.location.x, y: p.location.y + 1.2, z: p.location.z };
  if (roll < MISFIRE) {
    particle(p.dimension, 'bc:smoke_burst', at, { scale: 0.6 });
    particle(p.dimension, 'bc:burst_spark', at, { color: rgb('c040ff'), scale: 0.5 });
    sound(p.dimension, 'random.fizz', p.location, 1, 0.8);
    safe(() => p.onScreenDisplay.setActionBar('§5Wild magic! §7Your spell fizzles in your hands.'));
    return 'misfire';
  }
  if (roll < MISFIRE + SURGE) {
    particle(p.dimension, 'bc:burst_spark', at, { color: rgb('ff70e0'), scale: 1.0 });
    sound(p.dimension, 'random.orb', p.location, 1, 1.6);
    if (roll < MISFIRE + SURGE / 2 && cost > 0) {
      const s = state(p);
      s.mana += cost;
      s.dirty = true;
      safe(() => p.onScreenDisplay.setActionBar('§dWild magic! §7The spell surges - it cost you nothing.'));
      return 'free';
    }
    safe(() => p.onScreenDisplay.setActionBar('§dWild magic! §7The spell surges and echoes a second time.'));
    return 'twice';
  }
  return '';
}
