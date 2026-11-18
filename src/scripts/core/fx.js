// Visual & audio effect helpers (particles, sounds, camera, titles).
import { MolangVariableMap } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { V, safe } from './util.js';
import * as vfx from './vfx.js';

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

/** Magic circle in front of the caster, facing the cast direction (v0.9.0: the detailed sigil, glowing). */
export function castCircle(player, attr, size = 1.6, dist = 1.2) {
  const dir = player.getViewDirection();
  const at = V.add(player.getHeadLocation(), V.mul(dir, dist));
  at.y -= 0.25;
  const color = COLORS[attr] ?? COLORS.wind;
  if (attr === 'anti') {
    particle(player.dimension, 'bc:magic_circle', at, { color: rgb('b0202a'), size, dir });
    vfx.spawn(player.dimension, 'bc:fx_void', at, { scale: 0.5 });
  } else {
    vfx.sigil(player.dimension, at, dir, attr === 'dark' ? rgb('a066e0') : color, size * 1.05, 0.8);
    vfx.spawn(player.dimension, 'bc:fx_converge', at, { color, radius: size * 0.9, life: 0.25 }, true);
  }
}

export function groundCircle(dim, loc, attr, size = 3, life = 1.2) {
  const color = COLORS[attr] ?? COLORS.wind;
  if (attr === 'anti') particle(dim, 'bc:magic_circle_dark', loc, { size, life });
  else vfx.groundSigil(dim, loc, color, size, life);
}

/** A layered hit in the attribute's style (flash, core, element particles, sparks, smoke...). */
export function burst(dim, loc, attr, scale = 1) {
  const color = COLORS[attr] ?? COLORS.wind;
  if (attr === 'anti') {
    particle(dim, 'bc:anti_burst', loc, { scale });
    particle(dim, 'bc:anti_sparks', loc, { scale });
    vfx.impact(dim, loc, 'anti', rgb('e23a3a'), scale);
    return;
  }
  vfx.impact(dim, loc, attr, attr === 'dark' ? rgb('8a46c8') : color, scale);
}

export function shockwave(dim, loc, attr, radius) {
  if (attr === 'anti' || attr === 'dark') particle(dim, 'bc:shockwave_dark', loc, { radius });
  if (attr === 'anti') return;
  const color = COLORS[attr] ?? COLORS.wind;
  vfx.spawn(dim, 'bc:fx_ring', loc, { color, radius });
  vfx.spawn(dim, 'bc:fx_dust', loc, { scale: Math.max(0.5, radius / 3.5) }, true);
}

/** A continuous glowing beam between two points (v0.9.0: a solid bar with a white-hot core, not dots). */
export function beam(dim, a, b, attr, step = 0.45, size = 0.6, life = 0.35) {
  const color = attr === 'anti' ? rgb('e23a3a') : COLORS[attr] ?? COLORS.wind;
  const d = V.dist(a, b);
  if (d < 0.05) return;
  const dir = V.norm(V.sub(b, a));
  vfx.spawn(dim, 'bc:fx_beam', a, { color, dir, len: d, size: size * 1.1, life });
  vfx.spawn(dim, 'bc:fx_beam_core', a, { color, dir, len: d, size: size * 1.1, life: life * 0.9 });
  void step;
}

/** Jagged electric arc between two points. */
export function arc(dim, a, b, color = rgb('fff38c')) {
  vfx.lightning(dim, a, b, color, 0.55);
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
