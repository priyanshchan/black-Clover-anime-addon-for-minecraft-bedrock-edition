// Danger zones: telegraphed boss blows, spell fields, meteor and rain targets.
// Smart fighters (companions above all) read them and step out before the blow lands.
import { system, world } from '@minecraft/server';
import { canHit } from '../core/combat.js';
import { V, safe } from '../core/util.js';

/** @type {{dim: string, x: number, y: number, z: number, r: number, until: number, src: string}[]} */
const zones = [];

/** Mark an area as dangerous for `ticks` (src = the caster; only its enemies avoid it). */
export function addDanger(dim, loc, r, ticks, src) {
  const t = system.currentTick;
  for (let i = zones.length - 1; i >= 0; i--) if (zones[i].until < t) zones.splice(i, 1);
  if (zones.length > 120) zones.shift();
  zones.push({ dim: dim.id, x: loc.x, y: loc.y, z: loc.z, r, until: t + Math.max(1, Math.round(ticks)), src: src?.id ?? '' });
}

/** The zone `e` is standing in that is hostile to it, if any. */
export function dangerAt(e, margin = 0.8) {
  const t = system.currentTick;
  const l = e.location;
  for (const z of zones) {
    if (z.until < t || z.dim !== e.dimension.id || z.src === e.id) continue;
    if (Math.abs(l.y - z.y) > 5 || Math.hypot(l.x - z.x, l.z - z.z) > z.r + margin) continue;
    const src = z.src ? world.getEntity(z.src) : undefined;
    if (src && !safe(() => canHit(src, e))) continue;
    return z;
  }
  return undefined;
}

/** Step out of danger. Returns true when the entity had to move. */
export function escape(e, strength = 0.45) {
  const z = dangerAt(e);
  if (!z) return false;
  let dir = V.flat({ x: e.location.x - z.x, y: 0, z: e.location.z - z.z });
  if (V.len(dir) < 0.05) {
    const a = Math.random() * Math.PI * 2;
    dir = { x: Math.cos(a), y: 0, z: Math.sin(a) };
  }
  safe(() => e.applyImpulse({ x: dir.x * strength, y: 0.08, z: dir.z * strength }));
  return true;
}

/** How many live danger zones there are (for tests and the debug HUD). */
export function dangerCount() {
  const t = system.currentTick;
  return zones.filter((z) => z.until >= t).length;
}
