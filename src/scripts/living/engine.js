// The spell engine: every wave-4 grimoire spell, fruit ability, Magic Knight kit and boss attack is a
// small recipe ("spec") from tools/bc/data.py, run here by one of ~20 templates.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { eclipseMul, robe } from '../core/data.js';
import { aimEntity, aimPoint, blinkDestination, canHit, center, effect, groundBelow, hurt, knock, launch, ownerOf, factionOf, projectiles, pull, targetsAlong, targetsAround, teamOf } from '../core/combat.js';
import { particle, rgb, shakeArea, sound, title } from '../core/fx.js';
import { V, alive, rand, repeat, safe, timer } from '../core/util.js';
import { registerHandler } from '../magic/projectiles.js';
import { emit } from '../core/bus.js';
import * as vfx from '../core/vfx.js';
import { addDanger } from './danger.js';

/**
 * @typedef {Record<string, any>} Spec
 * @typedef {Object} ECtx
 * @property {any} c          caster
 * @property {any} dim
 * @property {string} src     tint key ('a:sand', 'f:lava', ...)
 * @property {number} pw      damage multiplier
 * @property {{x:number,y:number,z:number}} dir
 * @property {{x:number,y:number,z:number}} aim
 * @property {any} [target]
 * @property {{red:number,green:number,blue:number}} col
 */

const up = { x: 0, y: 1, z: 0 };

export function colorOf(src) {
  const [kind, id] = src.split(':');
  const hex = kind === 'f' ? DATA.fruits[id]?.color : DATA.attributes[id]?.color;
  return rgb(src === 'a:anti' ? 'e23a3a' : hex ?? 'ffffff');
}

// ------------------------------------------------------------------------------- visuals & sounds
// v0.9.0: every element's look lives in core/vfx.js (kits of layered particles); the engine says where and how big.
/** @type {Record<string, [string, number]>} */
const CAST_SOUND = {
  sand: ['bc.wind.gust', 0.7], earth: ['bc.stone.crack', 0.9], bubble: ['bc.bubble', 1], water: ['bc.water.surge', 1.1], leaf: ['bc.wind.gust', 1.3],
  poison: ['bc.bubble', 0.6], acid: ['bc.bubble', 0.8], blood: ['bc.devil.roar', 1.7], star: ['bc.light.shine', 1.2], light: ['bc.light.shine', 1],
  sound: ['bc.chord', 1], mist: ['bc.wind.gust', 0.6], ash: ['bc.wind.gust', 0.5], ink: ['bc.bubble', 0.5], crystal: ['bc.ice.form', 1.3],
  ice: ['bc.ice.form', 1], bone: ['bc.stone.crack', 1.4], magma: ['mob.blaze.shoot', 0.8], flame: ['mob.blaze.shoot', 1], lightning: ['bc.lightning.zap', 1],
  dark: ['bc.portal', 0.7], metal: ['bc.mirror', 0.6], steel: ['bc.mirror', 0.6], time: ['bc.clock', 1], spatial: ['bc.portal', 1], mirror: ['bc.mirror', 1],
  wind: ['bc.wind.gust', 1], cotton: ['bc.wind.gust', 1.4], paper: ['bc.grimoire.flip', 1.2], smoke: ['bc.wind.gust', 0.5], glass: ['random.glass', 1.2],
  gold: ['bc.coins', 1], beast: ['bc.howl', 1.3], spirit: ['bc.mirror', 0.8], rune: ['bc.portal', 1.3], gun: ['bc.pistol', 1.1],
};

function fx(x, spec, loc, scale = 1) {
  vfx.impact(x.dim, loc, spec.fx ?? x.src, x.col, scale);
}
/** Grimoire magic (not fruits) gets magic circles. */
function magic(x) {
  return x.src.startsWith('a:');
}
const UP = { x: 0, y: 1, z: 0 };
function castSound(x, spec, loc) {
  const [id, pitch] = CAST_SOUND[spec.fx] ?? ['bc.cast', 1];
  sound(x.dim, id, loc, 1, pitch * (0.92 + Math.random() * 0.16));
}

// ------------------------------------------------------------------------------- helpers
export function heal(e, amount) {
  safe(() => {
    const h = e.getComponent('minecraft:health');
    if (h && h.currentValue > 0) h.setCurrentValue(Math.min(h.effectiveMax, h.currentValue + amount));
  });
}

/** Allies of a caster: itself, its owner's other followers, other players (for players), its own side otherwise. */
export function friends(c, loc, r) {
  return safe(() => c.dimension.getEntities({ location: loc, maxDistance: r, excludeFamilies: ['bc_spell', 'inanimate'] }).filter((e) => {
    if (e.id === c.id) return true;
    if (!e.getComponent('minecraft:health')) return false;
    if (c instanceof Player) return e instanceof Player || ownerOf(e) === c.id;
    const tc = teamOf(c);
    if (tc) return teamOf(e) === tc;
    const o = ownerOf(c);
    if (o) return e.id === o || ownerOf(e) === o;
    const f = factionOf(c);
    return !!f && f === factionOf(e);
  })) ?? [];
}

function ground(dim, loc) {
  return groundBelow(dim, { x: loc.x, y: loc.y + 2, z: loc.z }, 12);
}

function from(x, dist = 1.1, down = 0.25) {
  const h = x.c.getHeadLocation();
  return { x: h.x + x.dir.x * dist, y: h.y + x.dir.y * dist - down, z: h.z + x.dir.z * dist };
}

function applyEffects(e, list) {
  for (const [id, sec, amp] of list ?? []) effect(e, id, sec, amp);
}

/** Damage + effects + fire + knockback + lifesteal on one target. */
function strike(x, spec, t, mul = 1, origin) {
  if (!alive(t)) return;
  const dmg = (spec.d ?? 0) * x.pw * mul;
  if (dmg > 0) hurt(t, dmg, x.c, spec.fire ? 'fire' : 'entityAttack');
  if (spec.fire) safe(() => t.setOnFire(spec.fire, true));
  applyEffects(t, spec.eff);
  if (spec.kb) knock(t, origin ? V.sub(t.location, origin) : x.dir, spec.kb[0], spec.kb[1]);
  if (spec.ls && dmg > 0 && alive(x.c)) heal(x.c, dmg * spec.ls);
}

function area(x, spec, at, r, mul = 1, hit) {
  for (const t of targetsAround(x.dim, at, r, x.c)) {
    if (hit) {
      if (hit.has(t.id)) continue;
      hit.add(t.id);
    }
    strike(x, spec, t, mul, at);
  }
}

// ------------------------------------------------------------------------------- the mana bolt
const SHAPES = { orb: 0, shard: 1, blade: 2, needle: 3, comet: 4 };

function shoot(x, spec, origin, dir, speed = spec.speed ?? 1.6) {
  const tint = DATA.tints[x.src] ?? 0;
  const shape = typeof spec.shape === 'string' ? SHAPES[spec.shape] ?? 0 : spec.shape ?? 0;
  const size = spec.size ?? 0;
  return launch(x.c, 'bc:mana_bolt', origin, dir, speed, {
    spell: 'engine', attr: x.src, damage: (spec.d ?? 0) * x.pw, pierce: spec.pierce ?? 0,
    extra: {
      spec, src: x.src, pw: x.pw,
      spawnEvent: spec.grav ? 'bc:heavy' : undefined,
      paint: (e) => {
        e.setProperty('bc:tint', tint);
        e.setProperty('bc:shape', shape);
        e.setProperty('bc:size', size);
      },
    },
  });
}

function boltCtx(m, owner, dim) {
  const src = m.extra?.src ?? 'a:wind';
  return /** @type {ECtx} */ ({ c: owner, dim, src, pw: m.extra?.pw ?? 1, dir: V.norm(m.vel), aim: { x: 0, y: 0, z: 0 }, col: colorOf(src) });
}

function boltImpact(m, owner, loc, dim, target) {
  const spec = m.extra?.spec ?? {};
  const x = boltCtx(m, owner, dim);
  fx(x, spec, loc, spec.aoe ? Math.min(2.6, spec.aoe / 2.2) : 0.65);
  if (spec.aoe) {
    sound(dim, 'bc.spell.impact', loc, 0.8, 1.1);
    if (spec.aoe >= 3) {
      shakeArea(dim, loc, spec.aoe * 3, 0.25, 0.3);
      const g = vfx.groundNear(dim, loc, 2.5);
      if (g) vfx.ground(dim, g, spec.fx ?? x.src, x.col, spec.aoe, 0.6, false);
    }
    area(x, spec, loc, spec.aoe, 1, new Set(m.hit));
    if (m.extra?.drop && Math.random() < 0.5) safe(() => dim.spawnItem(new ItemStack(m.extra.drop, 1), loc));
  } else if (target) {
    strike(x, spec, target, 1);
  }
}

registerHandler('bc:mana_bolt', {
  fx: '',
  entity(m, o, t, loc) {
    boltImpact(m, o, loc, t.dimension, t);
  },
  block(m, o, loc, dim) {
    if (m.extra?.spec?.aoe) boltImpact(m, o, loc, dim, undefined);
    else fx(boltCtx(m, o, dim), m.extra?.spec ?? {}, loc, 0.4);
  },
}, true);

// ------------------------------------------------------------------------------- position history (Rewind)
/** @type {Map<string, {x:number,y:number,z:number}[]>} */
const history = new Map();
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    let h = history.get(p.id);
    if (!h) history.set(p.id, (h = []));
    h.push({ ...p.location });
    if (h.length > 8) h.shift();
  }
}, 10);

function kitVoid(s) {
  return !!vfx.kitOf(s.fx ?? '').void;
}

// ------------------------------------------------------------------------------- templates
const walls = [];
/** @type {Record<string, (x: ECtx, s: Spec) => boolean | void>} */
const T = {
  bolt(x, s) {
    const n = s.n ?? 1;
    const spread = s.spread ?? 0;
    castSound(x, s, x.c.location);
    const o = from(x, 1.2, 0.3);
    vfx.muzzle(x.dim, o, x.dir, s.fx ?? x.src, x.col, 0.6 + (s.size ?? 0) * 0.35 + (n > 1 ? 0.25 : 0));
    for (let i = 0; i < n; i++) {
      const off = n === 1 ? 0 : -spread / 2 + (spread * i) / (n - 1);
      shoot(x, s, o, V.yaw(x.dir, off));
    }
  },
  radial(x, s) {
    const n = s.n ?? 12;
    const rings = s.rings ?? 1;
    castSound(x, s, x.c.location);
    for (let r = 0; r < rings; r++) {
      timer(r * 6, () => {
        if (!alive(x.c)) return;
        const o = V.add(x.c.location, { x: 0, y: 1.2, z: 0 });
        for (let i = 0; i < n; i++) {
          const a = ((i + r * 0.5) / n) * Math.PI * 2;
          const dir = { x: Math.cos(a), y: 0.02, z: Math.sin(a) };
          shoot(x, s, V.add(o, V.mul(dir, 0.8)), dir);
        }
        vfx.spawn(x.dim, 'bc:fx_flash', o, { color: x.col, size: 1.2 });
        vfx.ground(x.dim, x.c.location, s.fx ?? x.src, x.col, 4 + r, 0.7, magic(x) && r === 0);
      });
    }
  },
  beam(x, s) {
    const range = s.range ?? 20;
    const width = s.width ?? 1.0;
    const a = from(x, 1.0, 0.25);
    const hit = safe(() => x.dim.getBlockFromRay(a, x.dir, { maxDistance: range, includePassableBlocks: false, includeLiquidBlocks: false }));
    const len = hit ? Math.max(1, V.dist(a, V.add(hit.block.location, hit.faceLocation))) : range;
    const b = V.add(a, V.mul(x.dir, len));
    castSound(x, s, a);
    vfx.beam(x.dim, a, b, s.fx ?? x.src, x.col, width, { life: 0.42 });
    if (width >= 1.5) shakeArea(x.dim, a, 12, 0.2, 0.35);
    for (const t of targetsAlong(x.dim, a, b, width, x.c)) strike(x, s, t, 1, a);
  },
  wave(x, s) {
    const len = s.len ?? 12;
    const dirs = s.dirs ?? 1;
    const lanes = s.lanes ?? 1;
    const hit = new Set();
    castSound(x, s, x.c.location);
    shakeArea(x.dim, x.c.location, 16, 0.25, 0.6);
    const base = x.c.location;
    vfx.slash(x.dim, from(x, 1.6, 0.4), x.col, 3.2, 0);
    vfx.ground(x.dim, base, s.fx ?? x.src, x.col, 2.5, 0.6, magic(x));
    for (let d = 0; d < dirs; d++) {
      const dir = dirs === 1 ? V.flat(x.dir) : V.yaw(V.flat(x.dir), (360 / dirs) * d);
      const side = { x: -dir.z, y: 0, z: dir.x };
      for (let k = 1; k * 1.5 <= len; k++) {
        timer(k * 2, () => {
          for (let l = 0; l < lanes; l++) {
            const off = lanes === 1 ? 0 : (l - (lanes - 1) / 2) * 2.2;
            const p = ground(x.dim, V.add(V.add(base, V.mul(dir, k * 1.5)), V.mul(side, off)));
            vfx.spawn(x.dim, 'bc:fx_pillar', p, { color: x.col, size: 0.7, radius: 0.7 });
            vfx.spawn(x.dim, 'bc:fx_dust', p, { scale: 0.55 }, true);
            if (k % 2 === 0) fx(x, s, V.add(p, { x: 0, y: 0.6, z: 0 }), 0.6);
            if (k % 3 === 0) vfx.spawn(x.dim, 'bc:fx_crack', p, { size: 1.3 }, true);
            area(x, s, p, 1.8, 1, hit);
          }
        });
      }
    }
  },
  zone(x, s) {
    const self = s.at === 'self';
    const r = s.r ?? 4;
    const at0 = self ? x.c.location : ground(x.dim, x.aim);
    castSound(x, s, at0);
    const ticks = Math.round((s.dur ?? 5) * 2);
    if (!self && (s.d || s.eff)) addDanger(x.dim, at0, r, ticks * 10, x.c);
    if (!self) {
      vfx.ground(x.dim, at0, s.fx ?? x.src, x.col, r, (s.dur ?? 5) + 0.3, magic(x));
      vfx.swirl(x.dim, at0, x.col, r * 0.6, Math.min(3, s.dur ?? 5), 1.2);
    }
    repeat(ticks, 10, (i) => {
      if (self && !alive(x.c)) return false;
      const at = self ? x.c.location : at0;
      if (self) {
        if (magic(x)) vfx.groundSigil(x.dim, at, x.col, r * 2, 0.6);
        vfx.aura(x.dim, at, x.col, 0.5);
      }
      for (let k = 0; k < 2; k++) {
        const a = Math.random() * Math.PI * 2;
        const rr = Math.sqrt(Math.random()) * r;
        fx(x, s, V.add(at, { x: Math.cos(a) * rr, y: 0.6, z: Math.sin(a) * rr }), 0.45);
      }
      if (i % 2 === 0) vfx.spawn(x.dim, 'bc:fx_mist', V.add(at, { x: 0, y: 0.5, z: 0 }), { color: x.col, scale: r / 2.5 }, true);
      for (const t of targetsAround(x.dim, at, r, x.c)) {
        if (s.d) hurt(t, s.d * x.pw * 0.5, x.c, s.fire ? 'fire' : 'magic');
        if (s.fire && i % 4 === 0) safe(() => t.setOnFire(Math.min(s.fire, 3), true));
        applyEffects(t, s.eff);
        if (s.pull) pull(t, at, s.pull);
      }
    });
  },
  nova(x, s) {
    const at = s.at === 'aim' ? ground(x.dim, x.aim) : s.at === 'front' ? V.add(x.c.location, V.mul(V.flat(x.dir), 2)) : x.c.location;
    const r = s.r ?? 6;
    castSound(x, s, at);
    const g = vfx.groundNear(x.dim, V.add(at, { x: 0, y: 0.5, z: 0 }), 3) ?? at;
    vfx.ground(x.dim, g, s.fx ?? x.src, x.col, r, 0.9, magic(x));
    vfx.spawn(x.dim, 'bc:fx_flash', V.add(at, { x: 0, y: 1, z: 0 }), { color: x.col, size: 1.2 + r * 0.25 });
    fx(x, s, V.add(at, { x: 0, y: 1, z: 0 }), Math.min(2.4, r / 3));
    timer(3, () => vfx.spawn(x.dim, 'bc:fx_ring', V.add(g, { x: 0, y: 0.2, z: 0 }), { color: x.col, radius: r * 1.25, life: 0.5 }, true));
    const ringN = Math.min(8, Math.round(r));
    for (let k = 0; k < ringN; k++) {
      const a = (k / ringN) * Math.PI * 2;
      timer(1 + (k % 2), () => fx(x, s, V.add(at, { x: Math.cos(a) * r * 0.7, y: 0.5, z: Math.sin(a) * r * 0.7 }), 0.45));
    }
    if (r >= 5) shakeArea(x.dim, at, r * 2.5, 0.3, 0.5);
    if (r >= 8 && x.c instanceof Player) vfx.screenFlash([x.c], x.col, 0.3);
    const spec = s.kb ? s : { ...s, kb: [1.2, 0.4] };
    area(x, spec, at, r, 1);
  },
  rain(x, s) {
    const n = s.n ?? 8;
    const r = s.r ?? 4;
    const at = ground(x.dim, x.aim);
    castSound(x, s, at);
    addDanger(x.dim, at, r + 1, n * (s.every ?? 3) + 4, x.c);
    particle(x.dim, 'bc:warning_circle', V.add(at, { x: 0, y: 0.1, z: 0 }), { size: r + 1, life: (n * (s.every ?? 3)) / 20 + 0.4 });
    if (magic(x)) vfx.groundSigil(x.dim, at, x.col, (r + 1) * 2, (n * (s.every ?? 3)) / 20 + 0.5);
    vfx.sigil(x.dim, V.add(at, { x: 0, y: 10, z: 0 }), { x: 0, y: -1, z: 0 }, x.col, (r + 1) * 1.6, (n * (s.every ?? 3)) / 20 + 0.5);
    repeat(n, s.every ?? 3, () => {
      const a = Math.random() * Math.PI * 2;
      const rr = Math.sqrt(Math.random()) * r;
      const p = ground(x.dim, V.add(at, { x: Math.cos(a) * rr, y: 0, z: Math.sin(a) * rr }));
      const sky = V.add(p, { x: rand(-0.6, 0.6), y: 9, z: rand(-0.6, 0.6) });
      if (s.fx === 'lightning') vfx.lightning(x.dim, sky, p, x.col, 0.9);
      else vfx.beam(x.dim, sky, p, s.fx ?? x.src, x.col, 0.45, { life: 0.2, muzzle: false, impact: false });
      fx(x, s, V.add(p, { x: 0, y: 0.5, z: 0 }), 0.85);
      area(x, s, p, s.ar ?? 2.0, 1);
    });
  },
  meteor(x, s) {
    const n = s.n ?? 1;
    const r = s.r ?? 0;
    const at = ground(x.dim, x.aim);
    castSound(x, s, x.c.location);
    sound(x.dim, 'mob.blaze.shoot', at, 1, 0.5);
    repeat(n, 3, () => {
      const a = Math.random() * Math.PI * 2;
      const rr = Math.sqrt(Math.random()) * r;
      const p = ground(x.dim, V.add(at, { x: Math.cos(a) * rr, y: 0, z: Math.sin(a) * rr }));
      particle(x.dim, 'bc:warning_circle', V.add(p, { x: 0, y: 0.1, z: 0 }), { size: s.aoe ?? 3, life: 1.0 });
      vfx.groundSigil(x.dim, p, x.col, (s.aoe ?? 3) * 2, 1.0);
      addDanger(x.dim, p, (s.aoe ?? 3) + 0.5, 24, x.c);
      const o = V.add(p, { x: rand(-5, 5), y: 20, z: rand(-5, 5) });
      vfx.spawn(x.dim, 'bc:fx_flash', o, { color: x.col, size: 2 });
      if (alive(x.c)) shoot(x, { ...s, shape: 'comet', size: s.size ?? 2 }, o, V.sub(p, o), 1.8);
    });
  },
  buff(x, s) {
    castSound(x, s, x.c.location);
    if (magic(x)) vfx.groundSigil(x.dim, x.c.location, x.col, (s.allies ?? 1.6) * 2, 1.1);
    vfx.pillar(x.dim, x.c.location, x.col, 5, 0.9);
    vfx.spawn(x.dim, 'bc:fx_flash', center(x.c), { color: x.col, size: 1.1 });
    const list = s.allies ? friends(x.c, x.c.location, s.allies) : [x.c];
    for (const e of list) {
      applyEffects(e, s.self);
      vfx.aura(x.dim, e.location, x.col, 1.2);
      vfx.swirl(x.dim, e.location, x.col, 0.9, 0.9, 0.8);
      fx(x, s, center(e), 0.4);
    }
    return true;
  },
  heal(x, s) {
    const r = s.r ?? 6;
    const mul = x.c instanceof Player && robe(x.c) === 'blue_rose_robe' ? 1.3 : 1;
    castSound(x, s, x.c.location);
    if (magic(x)) vfx.groundSigil(x.dim, x.c.location, x.col, r * 2, 1.4);
    vfx.spawn(x.dim, 'bc:fx_ring', V.add(x.c.location, { x: 0, y: 0.15, z: 0 }), { color: x.col, radius: r, life: 0.7 });
    vfx.spawn(x.dim, 'bc:fx_flash', center(x.c), { color: x.col, size: 1.0 });
    vfx.pillar(x.dim, x.c.location, x.col, 4, 0.7);
    for (const e of friends(x.c, x.c.location, r)) {
      vfx.aura(x.dim, e.location, x.col, 1.2);
      vfx.spawn(x.dim, 'bc:fx_glyph', center(e), { color: x.col, scale: 0.7 }, true);
      vfx.spawn(x.dim, 'bc:fx_glow', center(e), { color: x.col, size: 1.4, life: 0.8 });
      heal(e, (s.heal ?? 6) * mul * Math.max(1, x.pw * 0.8));
      if (s.regen) effect(e, 'regeneration', s.regen, 0);
      for (const bad of ['poison', 'wither', 'slowness', 'weakness', 'blindness', 'nausea']) safe(() => e.removeEffect(bad));
      particle(x.dim, 'bc:heal', center(e), { scale: 1 });
      fx(x, s, center(e), 0.4);
    }
    return true;
  },
  prison(x, s) {
    const at = ground(x.dim, x.aim);
    const r = s.r ?? 3;
    const victims = targetsAround(x.dim, at, r, x.c);
    castSound(x, s, at);
    fx(x, s, V.add(at, { x: 0, y: 1, z: 0 }), r / 2);
    if (!victims.length) {
      particle(x.dim, 'bc:magic_circle_ground', V.add(at, { x: 0, y: 0.1, z: 0 }), { color: x.col, size: r, life: 0.8 });
      return true;
    }
    const dur = s.dur ?? 3;
    for (const v of victims) emit('cc', v, Math.round(dur * 20), x.c);
    for (const v of victims) {
      if (magic(x)) vfx.groundSigil(x.dim, v.location, x.col, 2.6, dur);
      vfx.swirl(x.dim, v.location, x.col, 0.9, Math.min(dur, 3), 0.9);
      vfx.spawn(x.dim, 'bc:fx_flash', center(v), { color: x.col, size: 0.9 });
      effect(v, 'slowness', dur, 8, false);
      effect(v, 'weakness', dur, 2, false);
      effect(v, 'mining_fatigue', dur, 2, false);
      applyEffects(v, s.eff);
    }
    repeat(Math.round(dur * 2), 10, () => {
      for (const v of victims) if (alive(v)) {
        vfx.spawn(x.dim, 'bc:fx_ring', V.add(v.location, { x: 0, y: 0.1, z: 0 }), { color: x.col, radius: 1.2, life: 0.4 }, true);
        vfx.spawn(x.dim, 'bc:fx_sparks', center(v), { color: x.col, scale: 0.35 }, true);
      }
    }, () => {
      for (const v of victims) if (alive(v)) {
        strike(x, { ...s, eff: undefined }, v, 1);
        fx(x, s, center(v), 0.9);
      }
      sound(x.dim, 'bc.spell.impact', at, 1, 0.8);
    });
  },
  summon(x, s) {
    castSound(x, s, x.c.location);
    const n = s.n ?? 1;
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2 + 0.6;
      const p = ground(x.dim, V.add(x.c.location, { x: Math.cos(a) * 2, y: 0, z: Math.sin(a) * 2 }));
      const e = safe(() => x.dim.spawnEntity(s.id ?? 'bc:construct', p, { spawnEvent: 'bc:summoned' }));
      if (!e) continue;
      safe(() => {
        if (s.variant !== undefined) e.setProperty('bc:variant', s.variant);
        e.setDynamicProperty('bc:owner', ownerOf(x.c) || x.c.id);
        const tm = teamOf(x.c);
        if (tm) {
          e.setDynamicProperty('bc:team', tm);
          e.triggerEvent(`bc:team_${tm}`);
        }
      });
      vfx.groundSigil(x.dim, p, x.col, 3, 1.3);
      vfx.pillar(x.dim, p, x.col, 4, 0.8);
      fx(x, s, V.add(p, { x: 0, y: 1, z: 0 }), 0.9);
    }
  },
  wall(x, s) {
    const dir = V.flat(x.dir);
    const side = { x: -dir.z, y: 0, z: dir.x };
    const base = V.add(x.c.location, V.mul(dir, 2.6));
    const w = s.w ?? 5;
    const placed = [];
    for (let k = -Math.floor(w / 2); k <= Math.floor(w / 2); k++) {
      for (let h = 0; h < (s.h ?? 3); h++) {
        const loc = { x: Math.floor(base.x + side.x * k), y: Math.floor(base.y) + h, z: Math.floor(base.z + side.z * k) };
        const b = safe(() => x.dim.getBlock(loc));
        if (b && b.isAir) {
          safe(() => b.setType(s.block));
          placed.push(loc);
          if (h === 0) {
            fx(x, s, V.add(loc, { x: 0.5, y: 0.5, z: 0.5 }), 0.4);
            vfx.spawn(x.dim, 'bc:fx_dust', V.add(loc, { x: 0.5, y: 0.05, z: 0.5 }), { scale: 0.4 }, true);
          }
        }
      }
    }
    if (!placed.length) return false;
    castSound(x, s, base);
    walls.push({ dim: x.dim, placed, block: s.block, until: system.currentTick + Math.round((s.dur ?? 8) * 20) });
  },
  timestop(x, s) {
    const r = s.r ?? 10;
    const at = x.c.location;
    const victims = targetsAround(x.dim, at, r, x.c).map((v) => ({ v, loc: { ...v.location } }));
    sound(x.dim, 'bc.clock', at, 1.5, 0.7);
    sound(x.dim, 'bc.gong', at, 1, 1.4);
    vfx.groundSigil(x.dim, at, x.col, r * 2, (s.dur ?? 4) + 0.3);
    vfx.spawn(x.dim, 'bc:fx_ring', V.add(at, { x: 0, y: 1, z: 0 }), { color: x.col, radius: r * 1.2, life: 0.6 });
    vfx.spawn(x.dim, 'bc:fx_flash', V.add(at, { x: 0, y: 1.2, z: 0 }), { color: x.col, size: 3 });
    vfx.spawn(x.dim, 'bc:fx_glyph', V.add(at, { x: 0, y: 1, z: 0 }), { color: x.col, scale: 2 });
    vfx.screenFlash([...(x.c instanceof Player ? [x.c] : []), ...victims.map((o) => o.v).filter((v) => v instanceof Player)], x.col, 0.5);
    for (const { v } of victims) if (v instanceof Player) title(v, '§e§lTIME STOPS', '§7...', 30);
    // hostile spells in the field simply vanish
    safe(() => {
      for (const e of x.dim.getEntities({ location: at, maxDistance: r, families: ['bc_spell'] })) {
        const m = projectiles.get(e.id);
        if (m && m.owner !== x.c.id) e.remove();
      }
    });
    const ticks = Math.round((s.dur ?? 4) * 10);
    for (const { v } of victims) emit('cc', v, ticks * 2, x.c);
    repeat(ticks, 2, (i) => {
      for (const { v, loc } of victims) {
        if (!alive(v)) continue;
        safe(() => v.teleport(loc, { keepVelocity: false }));
        if (i % 10 === 0) {
          effect(v, 'slowness', 1.2, 10, false);
          effect(v, 'weakness', 1.2, 3, false);
          effect(v, 'mining_fatigue', 1.2, 3, false);
          vfx.spawn(x.dim, 'bc:fx_glyph', center(v), { color: x.col, scale: 0.4 }, true);
        }
      }
      if (i % 10 === 0) sound(x.dim, 'bc.clock', at, 0.6, 1.2);
    }, () => {
      sound(x.dim, 'bc.spell.impact', at, 1.4, 0.6);
      for (const { v } of victims) if (alive(v)) {
        strike(x, s, v, 1, at);
        fx(x, s, center(v), 1);
      }
    });
  },
  leap(x, s) {
    const start = { ...x.c.location };
    if (s.mode === 'blink') {
      let dest;
      if (x.c instanceof Player) dest = blinkDestination(x.c, s.dist ?? 8);
      else dest = V.add(start, V.mul(V.flat(V.sub(x.aim, start)), Math.min(s.dist ?? 8, V.dist(x.aim, start) - 1.5)));
      fx(x, s, V.add(start, { x: 0, y: 1, z: 0 }), 0.8);
      vfx.spawn(x.dim, 'bc:fx_smoke', V.add(start, { x: 0, y: 0.8, z: 0 }), { scale: 0.6 }, true);
      safe(() => x.c.teleport(dest, { keepVelocity: false }));
      fx(x, s, V.add(dest, { x: 0, y: 1, z: 0 }), 0.9);
      vfx.spawn(x.dim, 'bc:fx_ring', V.add(dest, { x: 0, y: 0.15, z: 0 }), { color: x.col, radius: 2.2 });
      castSound(x, s, dest);
      const a = V.add(start, { x: 0, y: 1, z: 0 });
      const b = V.add(dest, { x: 0, y: 1, z: 0 });
      vfx.beam(x.dim, a, b, s.fx ?? x.src, x.col, 0.35, { life: 0.35, muzzle: false, impact: false });
      for (const t of targetsAlong(x.dim, a, b, 1.5, x.c)) strike(x, s, t, 1, a);
      return true;
    }
    const dir = V.flat(x.dir);
    castSound(x, s, start);
    if (x.c instanceof Player) knock(x.c, dir, (s.dist ?? 8) * 0.38, 0.25);
    else safe(() => x.c.applyImpulse({ x: dir.x * 1.6, y: 0.3, z: dir.z * 1.6 }));
    const hit = new Set();
    vfx.spawn(x.dim, 'bc:fx_ring', V.add(start, { x: 0, y: 0.15, z: 0 }), { color: x.col, radius: 1.8 });
    vfx.spawn(x.dim, 'bc:fx_dust', start, { scale: 0.7 }, true);
    repeat(8, 1, (i) => {
      if (!alive(x.c)) return false;
      if (i % 2 === 0) fx(x, s, V.add(x.c.location, { x: 0, y: 1, z: 0 }), 0.35);
      vfx.spawn(x.dim, 'bc:fx_spray', V.add(x.c.location, { x: 0, y: 1, z: 0 }), { color: x.col, dir: V.mul(dir, -1), scale: 0.4 }, true);
      area(x, { ...s, kb: s.kb ?? [1.0, 0.3] }, x.c.location, 2.2, 1, hit);
    });
  },
  vortex(x, s) {
    const at = V.add(ground(x.dim, x.aim), { x: 0, y: 1, z: 0 });
    const r = s.r ?? 6;
    castSound(x, s, at);
    const ticks = Math.max(2, Math.round(((s.dur ?? 2) * 20) / 3));
    addDanger(x.dim, at, r, ticks * 3 + 4, x.c);
    const g0 = vfx.groundNear(x.dim, at, 3) ?? at;
    if (magic(x)) vfx.groundSigil(x.dim, g0, x.col, r * 2, (s.dur ?? 2) + 0.4);
    vfx.swirl(x.dim, g0, x.col, r * 0.8, (s.dur ?? 2), 1.4);
    repeat(ticks, 3, (i) => {
      if (i % 2 === 0) vfx.spawn(x.dim, 'bc:fx_converge', at, { color: x.col, radius: r, life: 0.3 }, true);
      if (i % 3 === 0) vfx.spawn(x.dim, kitVoid(s) ? 'bc:fx_void' : 'bc:fx_glow', at, { color: x.col, scale: 0.8, size: 1.2, life: 0.3 }, true);
      if (i % 2 === 0) fx(x, s, V.add(at, { x: rand(-r, r) * 0.5, y: rand(0, 2), z: rand(-r, r) * 0.5 }), 0.4);
      for (const t of targetsAround(x.dim, at, r, x.c)) pull(t, at, 1.1);
    }, () => {
      fx(x, s, at, Math.min(2.4, r / 3));
      vfx.spawn(x.dim, 'bc:fx_flash', at, { color: x.col, size: 2.2 });
      vfx.spawn(x.dim, 'bc:fx_ring', g0, { color: x.col, radius: r * 1.1 });
      sound(x.dim, 'bc.spell.impact', at, 1.2, 0.8);
      area(x, { ...s, kb: s.kb ?? [1.4, 0.6] }, at, r * 0.65, 1);
    });
  },
  strikes(x, s) {
    const at = x.aim;
    const r = s.r ?? 8;
    const list = targetsAround(x.dim, at, r, x.c).sort((a, b) => V.dist(a.location, at) - V.dist(b.location, at)).slice(0, s.n ?? 4);
    castSound(x, s, x.c.location);
    if (!list.length) {
      const g = ground(x.dim, at);
      if (s.fx === 'lightning') vfx.lightning(x.dim, V.add(g, { x: 0, y: 11, z: 0 }), g, x.col, 1.1);
      else vfx.pillar(x.dim, g, x.col, 8, 1);
      fx(x, s, V.add(g, { x: 0, y: 0.5, z: 0 }), 0.8);
      return true;
    }
    list.forEach((t, i) => {
      timer(i * 3, () => {
        if (!alive(t)) return;
        const c = center(t);
        const top = V.add(c, { x: rand(-1, 1), y: 11, z: rand(-1, 1) });
        if (s.fx === 'lightning') vfx.lightning(x.dim, top, c, x.col, 1.1);
        else vfx.beam(x.dim, top, c, s.fx ?? x.src, x.col, 0.6, { life: 0.3, muzzle: false, impact: false });
        vfx.spawn(x.dim, 'bc:fx_ring', V.add(t.location, { x: 0, y: 0.1, z: 0 }), { color: x.col, radius: 1.8 }, true);
        fx(x, s, c, 0.9);
        sound(x.dim, s.fx === 'lightning' ? 'bc.lightning.zap' : 'bc.spell.impact', c, 0.9, 1.1);
        strike(x, s, t, 1, x.c.location);
      });
    });
  },
  dive(x, s) {
    const target = ground(x.dim, x.aim);
    castSound(x, s, x.c.location);
    fx(x, s, x.c.location, 0.8);
    vfx.spawn(x.dim, 'bc:fx_ring', V.add(x.c.location, { x: 0, y: 0.15, z: 0 }), { color: x.col, radius: 2.4 });
    vfx.spawn(x.dim, 'bc:fx_dust', x.c.location, { scale: 0.9 }, true);
    vfx.spawn(x.dim, 'bc:fx_spray', x.c.location, { color: x.col, dir: UP, scale: 0.8 }, true);
    if (magic(x)) vfx.groundSigil(x.dim, target, x.col, (s.r ?? 4) * 2, 1.4);
    if (x.c instanceof Player) {
      knock(x.c, up, 0, 1.25);
      effect(x.c, 'resistance', 2.5, 4, false);
    } else safe(() => x.c.applyImpulse({ x: 0, y: 1.2, z: 0 }));
    timer(10, () => {
      if (!alive(x.c)) return;
      const d = V.sub(target, x.c.location);
      const flat = V.flat(d);
      const dist = Math.min(14, Math.sqrt(d.x * d.x + d.z * d.z));
      if (x.c instanceof Player) knock(x.c, flat, dist * 0.32, -1.4);
      else safe(() => x.c.applyImpulse({ x: flat.x * dist * 0.12, y: -1.2, z: flat.z * dist * 0.12 }));
      let landed = false;
      repeat(20, 2, (i) => {
        if (!alive(x.c)) return false;
        if (i % 2 === 0) fx(x, s, V.add(x.c.location, { x: 0, y: 1, z: 0 }), 0.3);
        vfx.spawn(x.dim, 'bc:fx_spray', V.add(x.c.location, { x: 0, y: 1.6, z: 0 }), { color: x.col, dir: UP, scale: 0.3 }, true);
        if ((i > 1 && safe(() => x.c.isOnGround)) || i === 19) {
          landed = true;
          return false;
        }
      }, () => {
        if (!landed || !alive(x.c)) return;
        const at = x.c.location;
        vfx.ground(x.dim, V.add(at, { x: 0, y: 0.05, z: 0 }), s.fx ?? x.src, x.col, s.r ?? 4, 0.8, false);
        vfx.spawn(x.dim, 'bc:fx_crack', V.add(at, { x: 0, y: 0.05, z: 0 }), { size: (s.r ?? 4) * 0.9 });
        vfx.spawn(x.dim, 'bc:fx_debris', at, { scale: 1.2 }, true);
        vfx.spawn(x.dim, 'bc:fx_flash', V.add(at, { x: 0, y: 0.8, z: 0 }), { color: x.col, size: 2.4 });
        fx(x, s, V.add(at, { x: 0, y: 0.5, z: 0 }), 1.3);
        if (x.c instanceof Player && (s.r ?? 4) >= 5) vfx.screenFlash([x.c], x.col, 0.25);
        sound(x.dim, 'bc.golem.slam', at, 1.2, 1.1);
        shakeArea(x.dim, at, 14, 0.45, 0.5);
        area(x, { ...s, kb: s.kb ?? [1.0, 0.7] }, at, s.r ?? 4, 1);
      });
    });
  },
  rewind(x, s) {
    if (!(x.c instanceof Player)) return T.heal(x, { ...s, r: 1 });
    const h = history.get(x.c.id);
    if (!h || h.length < 2) return false;
    const back = h[Math.max(0, h.length - 7)];
    const was = center(x.c);
    fx(x, s, was, 0.8);
    vfx.spawn(x.dim, 'bc:fx_glyph', was, { color: x.col, scale: 1.2 });
    safe(() => x.c.teleport(back, { keepVelocity: false }));
    heal(x.c, (s.heal ?? 6) * Math.max(1, x.pw * 0.8));
    fx(x, s, V.add(back, { x: 0, y: 1, z: 0 }), 1.1);
    vfx.beam(x.dim, was, V.add(back, { x: 0, y: 1, z: 0 }), s.fx ?? x.src, x.col, 0.3, { life: 0.4, muzzle: false, impact: false });
    vfx.groundSigil(x.dim, back, x.col, 3.2, 1.3);
    vfx.swirl(x.dim, back, x.col, 1.0, 1.0, 1);
    sound(x.dim, 'bc.clock', back, 1, 1.4);
    return true;
  },
  repeat(x, s) {
    const sub = s.spec ?? {};
    repeat(s.n ?? 3, s.every ?? 4, () => {
      if (!alive(x.c)) return false;
      run(refresh(x), sub);
    });
  },
};

// temporary walls melt back
system.runInterval(() => {
  const t = system.currentTick;
  for (let i = walls.length - 1; i >= 0; i--) {
    const w = walls[i];
    if (w.until > t) continue;
    for (const loc of w.placed) {
      const b = safe(() => w.dim.getBlock(loc));
      if (b && b.typeId === w.block) safe(() => b.setType('minecraft:air'));
    }
    walls.splice(i, 1);
  }
}, 10);

/** Which player animation goes with each template (v0.9.0: full-body animations; fruit users fight like brawlers). */
const PLAYER_ANIM = {
  bolt: 'cast_forward', beam: 'cast_channel', zone: 'cast_channel', vortex: 'cast_channel', nova: 'cast_slam', dive: 'cast_slam', wave: 'cast_sweep',
  rain: 'cast_raise', meteor: 'cast_raise', strikes: 'cast_raise', buff: 'cast_buff', heal: 'cast_heal', summon: 'cast_summon',
  timestop: 'cast_summon', radial: 'cast_spin', leap: 'cast_dash', prison: 'cast_push', wall: 'cast_slam', rewind: 'cast_raise',
};
const FRUIT_ANIM = { bolt: 'fruit_punch', beam: 'cast_push', wave: 'fruit_stomp', nova: 'fruit_stomp', buff: 'fruit_roar', prison: 'cast_push' };
function animFor(spec, src) {
  const kind = spec.t === 'repeat' ? spec.spec?.t : spec.t;
  if (kind === 'bolt' && (spec.n ?? 1) >= 3 && !src.startsWith('f:')) return 'cast_push';
  if (kind === 'wave' && (spec.dirs ?? 1) > 1) return 'cast_slam';
  if (kind === 'zone' && spec.at === 'self') return src.startsWith('f:') ? 'fruit_roar' : 'cast_buff';
  return (src.startsWith('f:') ? FRUIT_ANIM[kind] : undefined) ?? PLAYER_ANIM[kind] ?? 'cast_forward';
}

// ------------------------------------------------------------------------------- entry points
/** @returns {ECtx} */
export function makeCtx(c, src, pw, target, aimAt) {
  const head = c.getHeadLocation();
  let aim;
  if (c instanceof Player) {
    target = target ?? aimEntity(c, 32);
    aim = target ? center(target) : aimPoint(c, 26).point;
    return { c, dim: c.dimension, src, pw, dir: c.getViewDirection(), aim, target, col: colorOf(src) };
  }
  aim = aimAt ?? (target && alive(target) ? center(target) : V.add(head, V.mul(c.getViewDirection(), 10)));
  return { c, dim: c.dimension, src, pw, dir: V.norm(V.sub(aim, head)), aim, target, col: colorOf(src) };
}

function refresh(x) {
  return makeCtx(x.c, x.src, x.pw, x.c instanceof Player ? undefined : x.target);
}

function run(x, spec) {
  const fn = T[spec.t];
  if (!fn) return false;
  return fn(x, spec);
}

/**
 * Cast one spell recipe.
 * @param {any} caster  player or NPC
 * @param {Spec} spec
 * @param {string} src  tint/colour source ('a:<attribute>' or 'f:<fruit>')
 * @param {number} [pw] damage multiplier
 * @param {any} [target] NPC casters: who to aim at
 * @param {{aim?: {x:number,y:number,z:number}}} [opts] NPC casters: a precise aim point (leading a moving target)
 * @returns {boolean} false when nothing was cast (refund)
 */
export function castSpec(caster, spec, src, pw = 1, target, opts = {}) {
  emit('spellcast', caster, spec, src);
  if (!alive(caster) || !spec) return false;
  if (spec.hp) {
    const h = caster.getComponent('minecraft:health');
    if (h && h.currentValue <= spec.hp + 1) {
      if (caster instanceof Player) safe(() => caster.onScreenDisplay.setActionBar('§4Not enough blood to pay for this spell...'));
      return false;
    }
    hurt(caster, spec.hp, undefined, 'magic');
    particle(caster.dimension, 'bc:shard_burst', center(caster), { color: rgb('d01a34'), scale: 0.5 });
  }
  const x = makeCtx(caster, src, caster instanceof Player ? pw : pw * eclipseMul(), target, opts.aim);
  // knights and enemies cast grimoire magic through a magic circle too (players get theirs from the grimoire)
  const kind0 = spec.t === 'repeat' ? spec.spec?.t : spec.t;
  if (!(caster instanceof Player) && src.startsWith('a:') && src !== 'a:anti' && ['bolt', 'beam', 'radial', 'wave', 'strikes', 'rain', 'meteor'].includes(kind0)) {
    vfx.sigil(x.dim, from(x, 1.1, 0.35), x.dir, x.col, 1.4, 0.6);
  }
  // fruit users call the power up from their own body
  if (src.startsWith('f:')) vfx.spawn(x.dim, 'bc:fx_glow', from(x, 0.7, 0.45), { color: x.col, size: 0.9, life: 0.35 }, true);
  if (caster instanceof Player) {
    safe(() => caster.playAnimation(`animation.bc.player.${animFor(spec, src)}`, { blendOutTime: 0.18 }));
  }
  const ok = safe(() => run(x, spec), `engine:${spec.t}`);
  if (ok === false) return false;
  if (spec.self && spec.t !== 'buff') applyEffects(caster, spec.self);
  if (spec.then) timer(4, () => run(refresh(x), spec.then));
  return true;
}

/** Launch a bare mana bolt (events, bosses). */
export function boltFrom(owner, src, spec, origin, dir, speed, extra = {}) {
  const x = /** @type {ECtx} */ ({ c: owner, dim: owner.dimension, src, pw: 1, dir: V.norm(dir), aim: origin, col: colorOf(src) });
  const e = shoot(x, spec, origin, dir, speed);
  if (e) {
    const m = projectiles.get(e.id);
    if (m) m.extra = { ...m.extra, ...extra };
  }
  return e;
}

export { canHit };
