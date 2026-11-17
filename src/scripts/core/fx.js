// Visual & audio effect helpers (particles, sounds, camera, titles).
import { MolangVariableMap } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { V, safe } from './util.js';

/** @param {string} hex */
export function rgb(hex) {
  const h = hex.replace('#', '');
  return { red: parseInt(h.slice(0, 2), 16) / 255, green: parseInt(h.slice(2, 4), 16) / 255, blue: parseInt(h.slice(4, 6), 16) / 255 };
}

export const COLORS = Object.fromEntries(Object.entries(DATA.attributes).map(([k, v]) => [k, rgb(v.color)]));

/**
 * @param {import('@minecraft/server').Dimension} dim
 * @param {string} id
 * @param {{x:number,y:number,z:number}} loc
 * @param {{color?: {red:number,green:number,blue:number}, size?: number, scale?: number, radius?: number, life?: number, dir?: {x:number,y:number,z:number}, rot?: number}} [vars]
 */
export function particle(dim, id, loc, vars) {
  safe(() => {
    if (!vars) {
      dim.spawnParticle(id, loc);
      return;
    }
    const m = new MolangVariableMap();
    if (vars.color) m.setColorRGB('variable.color', vars.color);
    if (vars.size !== undefined) m.setFloat('variable.size', vars.size);
    if (vars.scale !== undefined) m.setFloat('variable.scale', vars.scale);
    if (vars.radius !== undefined) m.setFloat('variable.radius', vars.radius);
    if (vars.life !== undefined) m.setFloat('variable.life', vars.life);
    if (vars.rot !== undefined) m.setFloat('variable.rot', vars.rot);
    if (vars.dir) m.setVector3('variable.dir', vars.dir);
    dim.spawnParticle(id, loc, m);
  }, 'particle');
}

export function sound(dim, id, loc, volume = 1, pitch = 1) {
  safe(() => dim.playSound(id, loc, { volume, pitch }), 'sound');
}

/** Magic circle in front of the caster, facing the cast direction. */
export function castCircle(player, attr, size = 1.6, dist = 1.2) {
  const dir = player.getViewDirection();
  const at = V.add(player.getHeadLocation(), V.mul(dir, dist));
  at.y -= 0.25;
  const color = COLORS[attr] ?? COLORS.wind;
  if (attr === 'anti' || attr === 'dark') {
    particle(player.dimension, 'bc:magic_circle', at, { color: attr === 'anti' ? rgb('b0202a') : rgb('a066e0'), size, dir });
  } else {
    particle(player.dimension, 'bc:magic_circle', at, { color, size, dir });
  }
}

export function groundCircle(dim, loc, attr, size = 3, life = 1.2) {
  const color = COLORS[attr] ?? COLORS.wind;
  if (attr === 'anti') particle(dim, 'bc:magic_circle_dark', loc, { size, life });
  else particle(dim, 'bc:magic_circle_ground', loc, { color, size, life });
}

export function burst(dim, loc, attr, scale = 1) {
  const color = COLORS[attr] ?? COLORS.wind;
  if (attr === 'anti') {
    particle(dim, 'bc:anti_burst', loc, { scale });
    particle(dim, 'bc:anti_sparks', loc, { scale });
  } else if (attr === 'dark') {
    particle(dim, 'bc:burst_dark', loc, { scale, color: rgb('2a1040') });
    particle(dim, 'bc:burst_spark', loc, { scale, color });
  } else {
    particle(dim, 'bc:burst', loc, { color, scale });
    particle(dim, 'bc:burst_spark', loc, { color, scale });
  }
}

export function shockwave(dim, loc, attr, radius) {
  if (attr === 'anti' || attr === 'dark') particle(dim, 'bc:shockwave_dark', loc, { radius });
  if (attr !== 'anti') particle(dim, 'bc:shockwave', loc, { radius, color: COLORS[attr] ?? COLORS.wind });
}

/** Dotted beam of glowing particles between two points. */
export function beam(dim, a, b, attr, step = 0.45, size = 0.6, life = 0.35) {
  const d = V.dist(a, b);
  const dir = V.norm(V.sub(b, a));
  const color = COLORS[attr] ?? COLORS.wind;
  for (let t = 0; t <= d; t += step) particle(dim, 'bc:beam_dot', V.add(a, V.mul(dir, t)), { color, size, life });
}

/** Jagged electric arc between two points. */
export function arc(dim, a, b, color = rgb('fff38c')) {
  const d = V.dist(a, b);
  const n = Math.max(2, Math.ceil(d / 0.6));
  for (let i = 0; i <= n; i++) {
    const p = V.lerp(a, b, i / n);
    const j = i === 0 || i === n ? 0 : 0.35;
    particle(dim, 'bc:beam_dot', { x: p.x + (Math.random() - 0.5) * j, y: p.y + (Math.random() - 0.5) * j, z: p.z + (Math.random() - 0.5) * j },
      { color, size: 0.35, life: 0.25 });
  }
  particle(dim, 'bc:spark', b, { color });
}

export function shake(player, intensity = 0.3, seconds = 0.4) {
  safe(() => player.runCommand(`camerashake add @s ${intensity.toFixed(2)} ${seconds.toFixed(2)} positional`), 'shake');
}

export function shakeArea(dim, loc, radius, intensity, seconds) {
  for (const p of dim.getPlayers({ location: loc, maxDistance: radius })) shake(p, intensity, seconds);
}

export function anim(entity, name, blend = 0.1) {
  safe(() => entity.playAnimation(name, { blendOutTime: blend }), 'anim');
}

export function title(player, main, sub = '', stay = 40) {
  safe(() => player.onScreenDisplay.setTitle(main, { fadeInDuration: 5, stayDuration: stay, fadeOutDuration: 15, subtitle: sub }), 'title');
}
