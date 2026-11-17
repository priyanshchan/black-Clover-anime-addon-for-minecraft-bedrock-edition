// Magic Knight field camps: tents around a campfire on open grassland, with a Mission Board, a supply chest
// and a few knights on watch. They appear out of sight near explorers (never too close to another structure).
import { system, world } from '@minecraft/server';
import { rand, safe, yawOf } from '../core/util.js';
import { build, farFromOthers } from '../sea/structures.js';

const GROUND = new Set(['minecraft:grass_block', 'minecraft:dirt', 'minecraft:coarse_dirt', 'minecraft:podzol']);

/** The y of the grass/dirt surface at a column, or undefined (water, trees, cliffs...). */
function grassY(dim, x, z) {
  const top = safe(() => dim.getTopmostBlock({ x, z }));
  if (!top || !GROUND.has(top.typeId)) return undefined;
  return top.location.y;
}

export function trySpawnCamp(p, force = false) {
  if (p.dimension.id !== 'minecraft:overworld') return false;
  const yaw = yawOf(p.getViewDirection()) + 180 + rand(-70, 70);
  const r = (yaw * Math.PI) / 180;
  const dist = force ? 24 : rand(56, 80);
  const x = Math.floor(p.location.x - Math.sin(r) * dist);
  const z = Math.floor(p.location.z + Math.cos(r) * dist);
  if (!force && !farFromOthers(x, z, 320)) return false;
  const y = grassY(p.dimension, x, z);
  if (y === undefined || y < 55 || y > 110) return false;
  // the footprint must be fairly flat, open ground
  for (const [dx, dz] of [[-7, 0], [7, 0], [0, -7], [0, 7], [-5, -5], [5, 5], [-5, 5], [5, -5]]) {
    const yy = grassY(p.dimension, x + dx, z + dz);
    if (yy === undefined || Math.abs(yy - y) > 2) return false;
  }
  build(p.dimension, 'camp', { x, y, z });
  return true;
}

system.runInterval(() => {
  for (const p of world.getAllPlayers()) if (Math.random() < 0.18) safe(() => trySpawnCamp(p), 'campSpawn');
}, 400);
