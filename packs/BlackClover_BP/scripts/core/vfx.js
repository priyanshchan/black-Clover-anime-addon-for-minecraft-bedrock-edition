// The VFX director (v0.9.0): layered spell effects built from the bc:fx_* particle library.
// A good hit is several layers at once - a white-hot flash and core, the element's own particles, sparks,
// smoke or mist, and on the ground a shock ring, a dust wave and cracks. Each element has a KIT saying which
// layers it uses. Everything here is one spawnParticle call per layer (the emitters spawn the many particles),
// and a per-tick budget drops the optional layers when a big battle fills the sky with spells.
import { MolangVariableMap, system } from '@minecraft/server';

/** @typedef {{x: number, y: number, z: number}} Vec */
/** @typedef {{red: number, green: number, blue: number}} RGB */

export function hex(h) {
  const s = h.replace('#', '');
  return { red: parseInt(s.slice(0, 2), 16) / 255, green: parseInt(s.slice(2, 4), 16) / 255, blue: parseInt(s.slice(4, 6), 16) / 255 };
}
const mix = (a, b, t) => ({ red: a.red + (b.red - a.red) * t, green: a.green + (b.green - a.green) * t, blue: a.blue + (b.blue - a.blue) * t });
const WHITE = { red: 1, green: 1, blue: 1 };
const SMOKE = hex('38363c');
const DUST = hex('8a7f70');

// ------------------------------------------------------------------------------- budget
const BUDGET = 260; // particle emitters per tick before optional layers are dropped
let tick = -1;
let used = 0;
/** Spawn one emitter. Optional layers are skipped when the tick's budget is spent. */
export function spawn(dim, id, loc, vars, optional = false) {
  const t = system.currentTick;
  if (t !== tick) {
    tick = t;
    used = 0;
  }
  if (optional && used >= BUDGET) return;
  used++;
  try {
    if (!vars) {
      dim.spawnParticle(id, loc);
      return;
    }
    const m = new MolangVariableMap();
    if (vars.color) m.setColorRGB('variable.color', vars.color);
    for (const k of ['size', 'scale', 'radius', 'life', 'rot', 'len']) if (vars[k] !== undefined) m.setFloat(`variable.${k}`, vars[k]);
    if (vars.dir) m.setVector3('variable.dir', vars.dir);
    dim.spawnParticle(id, loc, m);
  } catch {
    /* unloaded chunk, or the dimension went away */
  }
}
export function spentThisTick() {
  return system.currentTick === tick ? used : 0;
}

// ------------------------------------------------------------------------------- element kits
/**
 * el: element particles [id, scale]; sparks/smoke/embers/mist/debris: scale (0 = none);
 * crack: 'dark' | 'glow'; tint: fixed colour for the element particles; dust: a ground dust wave on big hits.
 * @typedef {{el: [string, number][], sparks?: number, smoke?: number, embers?: number, mist?: number, debris?: number,
 *   crack?: string, tint?: RGB, flash?: number, dust?: number, void?: number, ring?: boolean}} Kit
 */
/** @type {Record<string, Kit>} */
const KIT = {
  flame: { el: [['bc:fx_fire', 1.1]], sparks: 0.6, smoke: 0.7, embers: 1, crack: 'glow', dust: 0.5 },
  magma: { el: [['bc:fx_fire', 1.2]], sparks: 0.5, smoke: 1, embers: 1.2, debris: 0.8, crack: 'glow', dust: 1, tint: hex('ff6a1a') },
  ash: { el: [['bc:fx_fire', 0.5]], smoke: 1.3, embers: 1.3, dust: 1, tint: hex('ff8a3a') },
  water: { el: [['bc:fx_water', 1.2]], mist: 0.8, sparks: 0.3, dust: 0.3 },
  bubble: { el: [['bc:fx_bubble', 1.3], ['bc:fx_water', 0.5]], mist: 0.4 },
  acid: { el: [['bc:fx_bubble', 1], ['bc:fx_water', 0.6]], mist: 1, smoke: 0.3, crack: 'glow' },
  poison: { el: [['bc:fx_bubble', 0.8]], mist: 1.3, smoke: 0.4 },
  mist: { el: [], mist: 1.8, smoke: 0.6 },
  ice: { el: [['bc:fx_ice', 1.2], ['bc:fx_flake', 1]], mist: 0.6, sparks: 0.3, crack: 'dark' },
  crystal: { el: [['bc:fx_ice', 1.2], ['bc:fx_star', 0.7]], sparks: 0.5 },
  glass: { el: [['bc:fx_ice', 1.3], ['bc:fx_star', 0.5]], sparks: 0.6, tint: hex('d8f4ff') },
  mirror: { el: [['bc:fx_ice', 0.8], ['bc:fx_star', 1]], sparks: 0.5 },
  lightning: { el: [], sparks: 1.6, flash: 1.3, crack: 'glow' },
  light: { el: [['bc:fx_star', 1.3]], sparks: 0.8, flash: 1.4, embers: 0.4 },
  star: { el: [['bc:fx_star', 1.5]], sparks: 0.7, flash: 1.2 },
  moon: { el: [['bc:fx_star', 1.2]], mist: 0.5, flash: 1.1, tint: hex('dfe8ff') },
  gold: { el: [['bc:fx_star', 1.2]], sparks: 1.1, tint: hex('ffd860') },
  dark: { el: [], void: 1.3, sparks: 0.6, flash: 0.8 },
  gravity: { el: [], void: 1, dust: 1, debris: 0.8, crack: 'dark', ring: true },
  ink: { el: [], void: 1.2, smoke: 0.5, tint: hex('1a1430') },
  spatial: { el: [['bc:fx_glyph', 0.8]], void: 0.6, sparks: 0.5, ring: true },
  time: { el: [['bc:fx_glyph', 1.1]], sparks: 0.4, ring: true },
  rune: { el: [['bc:fx_glyph', 1.2]], sparks: 0.6, ring: true },
  paper: { el: [['bc:fx_glyph', 0.8], ['bc:fx_leaf', 0.6]], tint: hex('f2ead0') },
  earth: { el: [], debris: 1.3, dust: 1.4, smoke: 0.4, crack: 'dark' },
  sand: { el: [], dust: 1.6, debris: 0.4, mist: 0.6, tint: hex('d8c08a') },
  bone: { el: [['bc:fx_ice', 0.8]], debris: 0.8, dust: 0.6, tint: hex('ece4cc') },
  steel: { el: [['bc:fx_ice', 0.6]], sparks: 1.5, tint: hex('d0d8e4') },
  metal: { el: [['bc:fx_ice', 0.6]], sparks: 1.5, tint: hex('d0d8e4') },
  leaf: { el: [['bc:fx_leaf', 1.4]], sparks: 0.3, mist: 0.3 },
  thorn: { el: [['bc:fx_leaf', 1], ['bc:fx_ice', 0.5]], sparks: 0.4, tint: hex('6ad040') },
  cotton: { el: [], mist: 1.6, tint: hex('fff8f0') },
  smoke: { el: [], smoke: 1.6, mist: 0.6 },
  sound: { el: [['bc:fx_note', 1.3]], ring: true, sparks: 0.3 },
  blood: { el: [['bc:fx_water', 1.2]], sparks: 0.4, tint: hex('b0101a') },
  spirit: { el: [['bc:fx_star', 0.8]], mist: 0.9, embers: 0.5 },
  beast: { el: [], sparks: 1.1, dust: 0.6 },
  wind: { el: [], sparks: 0.8, mist: 0.6, dust: 0.6, ring: true },
  gun: { el: [], sparks: 1.2, smoke: 0.6 },
  anti: { el: [], void: 1.5, sparks: 1, flash: 0.6, tint: hex('ff2a2a') },
  devil: { el: [['bc:fx_fire', 0.6]], void: 1.2, sparks: 0.6, tint: hex('ff3a2a') },
};
/** Fruits map onto an element kit. */
const FRUIT_KIT = {
  ember: 'flame', stone: 'earth', gravity: 'gravity', shadow: 'dark', bloom: 'leaf', quicksilver: 'metal', frost: 'ice', barrier: 'crystal',
  wolf: 'beast', hawk: 'wind', lava: 'magma', ash: 'ash', prism: 'light', bounce: 'bubble', blast: 'flame', acid: 'acid', lodestone: 'metal',
  cloud: 'cotton', ink: 'ink', bear: 'beast', tiger: 'beast', wyvern: 'flame', spore: 'poison', thread: 'paper', slime: 'bubble', chain: 'steel',
  lion: 'flame', shark: 'water', phoenix: 'flame', spider: 'dark', spark: 'lightning', echo: 'sound', sand: 'sand', gale: 'wind',
};
const ATTR_KIT = { plant: 'leaf', storm: 'lightning', blossom: 'leaf', coral: 'crystal', dream: 'spirit' };

/** The kit for a spec fx key, an attribute, a fruit ('f:id' / 'a:id') or an element name. */
export function kitOf(key) {
  if (!key) return KIT.wind;
  if (key.startsWith('f:')) return KIT[FRUIT_KIT[key.slice(2)] ?? ''] ?? KIT.wind;
  if (key.startsWith('a:')) key = key.slice(2);
  return KIT[key] ?? KIT[ATTR_KIT[key] ?? ''] ?? KIT[FRUIT_KIT[key] ?? ''] ?? KIT.wind;
}
export function kitName(key) {
  if (!key) return 'wind';
  if (key.startsWith('f:')) return FRUIT_KIT[key.slice(2)] ?? 'wind';
  const k = key.startsWith('a:') ? key.slice(2) : key;
  return KIT[k] ? k : ATTR_KIT[k] ?? FRUIT_KIT[k] ?? 'wind';
}

// ------------------------------------------------------------------------------- ground
/** The ground a little below a point, or undefined in mid-air. */
export function groundNear(dim, loc, maxDown = 2.5) {
  for (let i = 0; i <= Math.ceil(maxDown); i++) {
    let b;
    try {
      b = dim.getBlock({ x: Math.floor(loc.x), y: Math.floor(loc.y) - i, z: Math.floor(loc.z) });
    } catch {
      return undefined;
    }
    if (b && !b.isAir && !b.isLiquid) return { x: loc.x, y: Math.floor(loc.y) - i + 1.02, z: loc.z };
  }
  return undefined;
}

// ------------------------------------------------------------------------------- the layers
/**
 * A hit: flash, core, the element's particles, sparks, smoke/mist/embers; on the ground a ring, dust and cracks.
 * @param {any} dim @param {Vec} loc @param {string} key fx key / element / 'a:attr' / 'f:fruit' @param {RGB} col @param {number} size
 */
export function impact(dim, loc, key, col, size = 1) {
  const k = kitOf(key);
  const s = Math.max(0.25, size);
  const c = col ?? WHITE;
  const tint = k.tint ?? c;
  spawn(dim, 'bc:fx_flash', loc, { color: c, size: 0.75 * s * (k.flash ?? 1) });
  spawn(dim, 'bc:fx_core', loc, { color: mix(c, WHITE, 0.4), size: 0.7 * s });
  for (const [id, m] of k.el) spawn(dim, id, loc, { color: tint, scale: s * m });
  if (k.void) spawn(dim, 'bc:fx_void', loc, { color: c, scale: s * k.void });
  if (k.sparks) spawn(dim, 'bc:fx_sparks', loc, { color: tint, scale: s * k.sparks }, true);
  if (k.smoke) spawn(dim, 'bc:fx_smoke', loc, { color: SMOKE, scale: s * k.smoke }, true);
  if (k.embers) spawn(dim, 'bc:fx_embers', loc, { color: tint, scale: s * k.embers }, true);
  if (k.mist) spawn(dim, 'bc:fx_mist', loc, { color: tint, scale: s * k.mist }, true);
  if (s >= 0.7) {
    const g = groundNear(dim, loc, 1.6 + s);
    if (g) {
      if (k.ring || s >= 1.2) spawn(dim, 'bc:fx_ring', g, { color: c, radius: 1.6 * s + 0.6 }, true);
      if (k.dust) spawn(dim, 'bc:fx_dust', g, { color: k.tint && k.dust >= 1.4 ? k.tint : DUST, scale: s * k.dust }, true);
      if (k.debris) spawn(dim, 'bc:fx_debris', g, { color: DUST, scale: s * k.debris }, true);
      if (k.crack && s >= 1) spawn(dim, k.crack === 'glow' ? 'bc:fx_crack_glow' : 'bc:fx_crack', g, { color: c, size: 1.2 * s + 0.6 }, true);
      if (k.crack === 'glow' && s >= 1) spawn(dim, 'bc:fx_crack', g, { size: 1.2 * s + 0.6 }, true);
    }
  }
}

/** The release at the caster's hand: a flash, a shock ring facing the cast, and a spray along it. */
export function muzzle(dim, at, dir, key, col, size = 1) {
  const c = col ?? WHITE;
  const k = kitOf(key);
  spawn(dim, 'bc:fx_flash', at, { color: c, size: 0.5 * size });
  spawn(dim, 'bc:fx_shock', at, { color: c, dir, radius: 1.3 * size });
  spawn(dim, 'bc:fx_spray', at, { color: k.tint ?? c, dir, scale: 0.7 * size }, true);
  if (k.el.length) spawn(dim, k.el[0][0], at, { color: k.tint ?? c, scale: 0.35 * size }, true);
}

/** A magic circle facing a direction (grimoire magic). */
export function sigil(dim, at, dir, col, size = 1.6, life = 0.9) {
  spawn(dim, 'bc:fx_sigil', at, { color: col ?? WHITE, dir, size, life });
  spawn(dim, 'bc:fx_glow', at, { color: col ?? WHITE, size: size * 0.35, life: life * 0.6 }, true);
}
export function groundSigil(dim, at, col, size = 3, life = 1.2) {
  spawn(dim, 'bc:fx_sigil_ground', { x: at.x, y: at.y + 0.06, z: at.z }, { color: col ?? WHITE, size, life });
}

/** Gathering power: streaks converge on a growing orb. */
export function charge(dim, at, col, size = 1, life = 0.45) {
  spawn(dim, 'bc:fx_converge', at, { color: col ?? WHITE, radius: 1.6 * size + 0.4, life });
  spawn(dim, 'bc:fx_charge', at, { color: col ?? WHITE, size: 0.9 * size, life: life + 0.1 });
}

/** A continuous beam with a white-hot core, the element along it, a muzzle and an impact. */
export function beam(dim, a, b, key, col, width = 1, opts = {}) {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const dz = b.z - a.z;
  const len = Math.max(0.1, Math.hypot(dx, dy, dz));
  const dir = { x: dx / len, y: dy / len, z: dz / len };
  const c = col ?? WHITE;
  spawn(dim, 'bc:fx_beam', a, { color: c, dir, len, size: 0.55 * width + 0.25, life: opts.life ?? 0.35 });
  spawn(dim, 'bc:fx_beam_core', a, { color: c, dir, len, size: 0.55 * width + 0.25, life: opts.life ?? 0.35 });
  const k = kitOf(key);
  if (k.el.length && len > 3) {
    for (let i = 1; i <= Math.min(3, Math.floor(len / 4)); i++) {
      const t = i / (Math.min(3, Math.floor(len / 4)) + 1);
      spawn(dim, k.el[0][0], { x: a.x + dx * t, y: a.y + dy * t, z: a.z + dz * t }, { color: k.tint ?? c, scale: 0.4 * width }, true);
    }
  }
  if (opts.muzzle !== false) muzzle(dim, a, dir, key, c, 0.8 * width + 0.2);
  if (opts.impact !== false) impact(dim, b, key, c, 0.6 * width + 0.3);
}

/** A ground effect: a magic circle, a ring, a dust wave and cracks. */
export function ground(dim, at, key, col, r = 3, life = 1.2, magic = true) {
  const c = col ?? WHITE;
  const k = kitOf(key);
  if (magic) groundSigil(dim, at, c, r * 2, life);
  spawn(dim, 'bc:fx_ring', { x: at.x, y: at.y + 0.1, z: at.z }, { color: c, radius: r });
  spawn(dim, 'bc:fx_dust', at, { color: k.tint && (k.dust ?? 0) >= 1.4 ? k.tint : DUST, scale: Math.max(0.6, r / 3) }, true);
  if (r >= 3 && k.crack) spawn(dim, k.crack === 'glow' ? 'bc:fx_crack_glow' : 'bc:fx_crack', at, { color: c, size: r * 0.8 }, true);
}

/** A column of light rising from the ground. */
export function pillar(dim, at, col, height = 6, size = 1) {
  const c = col ?? WHITE;
  spawn(dim, 'bc:fx_pillar', at, { color: c, size, radius: 0.6 * size });
  spawn(dim, 'bc:fx_beam', at, { color: c, dir: { x: 0, y: 1, z: 0 }, len: height, size: 0.7 * size, life: 0.5 });
  spawn(dim, 'bc:fx_beam_core', at, { color: c, dir: { x: 0, y: 1, z: 0 }, len: height, size: 0.7 * size, life: 0.45 }, true);
  spawn(dim, 'bc:fx_ring', { x: at.x, y: at.y + 0.1, z: at.z }, { color: c, radius: 1.4 * size }, true);
}

/** A jagged lightning bolt between two points. */
export function lightning(dim, a, b, col, width = 1) {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const dz = b.z - a.z;
  const len = Math.max(0.1, Math.hypot(dx, dy, dz));
  const dir = { x: dx / len, y: dy / len, z: dz / len };
  const mid = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, z: (a.z + b.z) / 2 };
  const c = col ?? hex('fff38c');
  spawn(dim, 'bc:fx_bolt', mid, { color: c, dir, len, size: width });
  spawn(dim, 'bc:fx_bolt', mid, { color: c, dir, len, size: width * 0.7, life: 0.16 }, true);
  spawn(dim, 'bc:fx_beam', a, { color: c, dir, len, size: 0.5 * width, life: 0.18 }, true);
  spawn(dim, 'bc:fx_flash', b, { color: c, size: 0.8 * width });
  spawn(dim, 'bc:fx_sparks', b, { color: c, scale: 0.8 * width }, true);
}

/** A crescent slash (blades, claws, sweeping waves). */
export function slash(dim, at, col, size = 2, rot) {
  spawn(dim, 'bc:fx_slash', at, { color: col ?? WHITE, size, rot: rot ?? Math.random() * 80 - 40 });
}

/** Wisps spiralling up around a point (tornadoes, buffs, prisons). */
export function swirl(dim, at, col, radius = 1.2, life = 0.9, size = 1) {
  spawn(dim, 'bc:fx_swirl', at, { color: col ?? WHITE, radius, life, size });
}

/** Rising motes around an entity's feet (buffs, healing). */
export function aura(dim, at, col, life = 1.0) {
  spawn(dim, 'bc:fx_aura', at, { color: col ?? WHITE, life });
}

/** A short full-screen flash for the biggest moments (only the given players). */
export function screenFlash(players, col, out = 0.35) {
  const c = col ?? WHITE;
  for (const p of players) {
    try {
      p.camera.fade({ fadeColor: mix(c, WHITE, 0.55), fadeTime: { fadeInTime: 0.01, holdTime: 0.02, fadeOutTime: out } });
    } catch {
      /* not supported here */
    }
  }
}

export { KIT, FRUIT_KIT, mix };
