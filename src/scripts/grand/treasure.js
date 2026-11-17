// Treasure maps: each map points to its own buried chest. Hold it to follow the arrow; use it on the spot to dig.
import { BlockPermutation, system } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { particle, sound, title } from '../core/fx.js';
import { V, safe, yawOf } from '../core/util.js';
import { fill } from '../sea/structures.js';

function heldMap(p) {
  const inv = p.getComponent('minecraft:inventory')?.container;
  const it = inv?.getItem(p.selectedSlotIndex);
  return it?.typeId === 'bc:treasure_map' ? { inv, it } : undefined;
}

function target(p, it, inv) {
  let x = it.getDynamicProperty('bc:tx');
  let z = it.getDynamicProperty('bc:tz');
  if (typeof x !== 'number' || typeof z !== 'number') {
    const a = Math.random() * Math.PI * 2;
    const d = 140 + Math.random() * 160;
    x = Math.round(p.location.x + Math.cos(a) * d);
    z = Math.round(p.location.z + Math.sin(a) * d);
    it.setDynamicProperty('bc:tx', x);
    it.setDynamicProperty('bc:tz', z);
    safe(() => it.setLore(['§7X marks the spot...', `§8Somewhere near §f${x}, ${z}`]));
    inv.setItem(p.selectedSlotIndex, it);
    safe(() => p.sendMessage(`§6The map's ink shifts... §fthe treasure lies near §e${x}, ${z}§f.`));
  }
  return { x, z };
}

export function mapHud(p) {
  const h = heldMap(p);
  if (!h) return undefined;
  const x = h.it.getDynamicProperty('bc:tx');
  const z = h.it.getDynamicProperty('bc:tz');
  if (typeof x !== 'number' || typeof z !== 'number') return '§6Treasure Map §7- use it to read the map';
  const dx = x - p.location.x;
  const dz = z - p.location.z;
  const dist = Math.round(Math.sqrt(dx * dx + dz * dz));
  if (dist <= 4) return '§6§lX marks the spot! §r§7Use the map here to dig.';
  const rel = ((yawOf({ x: dx, y: 0, z: dz }) - yawOf(p.getViewDirection()) + 540) % 360) - 180;
  const arrow = DATA.glyphs.arrows[((Math.round(rel / 45) % 8) + 8) % 8];
  return `${arrow} §6Treasure §7${dist}m`;
}

export function useMap(p) {
  const h = heldMap(p);
  if (!h) return;
  const { x, z } = target(p, h.it, h.inv);
  const d = Math.hypot(x - p.location.x, z - p.location.z);
  if (d > 4) return;
  // dig: put a chest two blocks under the ground and open the pit
  const dim = p.dimension;
  let y = Math.floor(p.location.y) - 1;
  for (let k = 0; k < 6; k++) {
    const b = dim.getBlock({ x, y, z });
    if (b && !b.isAir && !b.isLiquid) break;
    y--;
  }
  const chestY = y - 1;
  const chest = dim.getBlock({ x, y: chestY, z });
  if (!chest) return;
  safe(() => dim.getBlock({ x, y, z })?.setType('minecraft:air'));
  safe(() => chest.setPermutation(BlockPermutation.resolve('minecraft:chest')));
  system.run(() => safe(() => fill(chest, 'treasure')));
  h.inv.setItem(p.selectedSlotIndex, undefined);
  particle(dim, 'bc:rock_debris', { x: x + 0.5, y: y + 1, z: z + 0.5 }, { scale: 0.8 });
  particle(dim, 'bc:level_up', { x: x + 0.5, y: chestY + 1, z: z + 0.5 });
  sound(dim, 'bc.coins', p.location, 1, 1);
  title(p, '§6§lTREASURE!', '§7You unearth a buried chest', 50);
}

export { V };
