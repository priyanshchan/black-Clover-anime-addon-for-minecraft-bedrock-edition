// What every spell projectile does when it hits something.
import { system, world } from '@minecraft/server';
import { HOSTILE_PROJECTILES, canHit, center, effect, hurt, knock, launch, projectiles, targetsAround } from '../core/combat.js';
import { COLORS, arc, burst, particle, rgb, shakeArea, shockwave, sound } from '../core/fx.js';
import { V, alive, safe } from '../core/util.js';

/**
 * @typedef {import('../core/combat.js').ProjMeta} ProjMeta
 * @typedef {{ entity?: (m: ProjMeta, owner: any, target: any, loc: any) => void, block?: (m: ProjMeta, owner: any, loc: any, dim: any) => void, fx: string }} Handler
 */

function boom(dim, loc, attr, owner, radius, dmg, cause = 'entityExplosion', fire = 0) {
  burst(dim, loc, attr, radius / 2.5);
  shockwave(dim, loc, attr, radius);
  if (attr === 'flame') {
    particle(dim, 'bc:flame_burst', loc, { scale: radius / 2.5 });
    particle(dim, 'bc:smoke_burst', loc, { scale: radius / 3 });
  }
  sound(dim, 'random.explode', loc, 1, 1.1);
  sound(dim, 'bc.spell.impact', loc, 1, 1);
  shakeArea(dim, loc, radius * 3, 0.35, 0.5);
  for (const t of targetsAround(dim, loc, radius, owner)) {
    hurt(t, dmg * (1 - Math.min(0.6, V.dist(t.location, loc) / radius * 0.5)), owner, cause);
    if (fire) safe(() => t.setOnFire(fire, true));
    knock(t, V.sub(t.location, loc), 1.3, 0.55);
  }
}

/** @type {Record<string, Handler>} */
const HANDLERS = {
  'bc:wind_blade': {
    fx: 'wind',
    entity(m, o, t) {
      hurt(t, m.damage, o);
      knock(t, m.vel, 1.1, 0.35);
    },
  },
  'bc:fireball': {
    fx: 'flame',
    entity(m, o, t, loc) {
      hurt(t, m.damage, o, 'fire');
      safe(() => t.setOnFire(5, true));
      particle(t.dimension, 'bc:flame_burst', loc, { scale: 0.6 });
    },
    block(m, o, loc, dim) {
      particle(dim, 'bc:flame_burst', loc, { scale: 0.6 });
    },
  },
  'bc:flame_lion': {
    fx: 'flame',
    entity(m, o, t, loc) {
      boom(t.dimension, loc, 'flame', o, 4.8, m.damage, 'fire', 7);
    },
    block(m, o, loc, dim) {
      boom(dim, loc, 'flame', o, 4.8, m.damage, 'fire', 7);
    },
  },
  'bc:water_orb': {
    fx: 'water',
    entity(m, o, t, loc) {
      hurt(t, m.damage, o, 'drowning');
      effect(t, 'slowness', 2, 0);
      safe(() => t.extinguishFire(true));
      particle(t.dimension, 'bc:water_splash', loc, { scale: 0.5 });
    },
    block(m, o, loc, dim) {
      particle(dim, 'bc:water_splash', loc, { scale: 0.5 });
    },
  },
  'bc:water_dragon': {
    fx: 'water',
    entity(m, o, t, loc) {
      hurt(t, m.damage, o, 'drowning');
      knock(t, m.vel, 1.8, 0.6);
      particle(t.dimension, 'bc:water_splash', loc, { scale: 1 });
      sound(t.dimension, 'random.splash', loc, 1, 0.8);
    },
    block(m, o, loc, dim) {
      particle(dim, 'bc:water_splash', loc, { scale: 1.6 });
      shockwave(dim, loc, 'water', 4);
      sound(dim, 'bc.water.surge', loc, 1, 1);
    },
  },
  'bc:thunder_spear': {
    fx: 'lightning',
    entity(m, o, t, loc) {
      hurt(t, m.damage, o, 'lightning');
      sound(t.dimension, 'bc.lightning.zap', loc, 1, 1);
      let from = center(t);
      const done = new Set([t.id]);
      for (let i = 0; i < 2; i++) {
        const next = targetsAround(t.dimension, from, 6.5, o).find((e) => !done.has(e.id));
        if (!next) break;
        done.add(next.id);
        const to = center(next);
        arc(t.dimension, from, to);
        hurt(next, m.damage * 0.55, o, 'lightning');
        from = to;
      }
    },
  },
  'bc:light_sword': {
    fx: 'light',
    entity(m, o, t, loc) {
      hurt(t, m.damage, o, 'magic');
      particle(t.dimension, 'bc:light_burst', loc, { scale: 0.5 });
    },
    block(m, o, loc, dim) {
      particle(dim, 'bc:light_burst', loc, { scale: 0.5 });
      if (m.spell === 'radiant_rain') for (const t of targetsAround(dim, loc, 1.6, o)) hurt(t, m.damage * 0.6, o, 'magic');
    },
  },
  'bc:dark_crescent': {
    fx: 'dark',
    entity(m, o, t) {
      hurt(t, m.damage, o, 'magic');
      effect(t, 'wither', 3, 0);
      knock(t, m.vel, 0.7, 0.2);
    },
  },
  'bc:ice_spear': {
    fx: 'ice',
    entity(m, o, t, loc) {
      hurt(t, m.damage, o, 'freezing');
      effect(t, 'slowness', 3, 1);
      particle(t.dimension, 'bc:ice_shatter', loc, { scale: 0.6 });
      sound(t.dimension, 'random.glass', loc, 0.6, 1.4);
    },
    block(m, o, loc, dim) {
      particle(dim, 'bc:ice_shatter', loc, { scale: 0.6 });
      sound(dim, 'random.glass', loc, 0.5, 1.6);
    },
  },
  'bc:anti_magic_slash': {
    fx: 'anti',
    entity(m, o, t, loc) {
      hurt(t, m.damage * (t.matches({ families: ['bc_magic'] }) ? 1.5 : 1), o, 'entityAttack');
      // anti-magic strips magical buffs
      for (const ef of safe(() => t.getEffects()) ?? []) safe(() => t.removeEffect(ef.typeId));
      knock(t, m.vel, 1.2, 0.3);
      particle(t.dimension, 'bc:slash_fx', loc, { size: 3 });
    },
  },
  // ---------------------------------------------------------- enemy projectiles
  'bc:dark_bolt': {
    fx: 'dark',
    entity(m, o, t) {
      effect(t, 'weakness', 3, 0);
    },
  },
  'bc:devil_orb': {
    fx: 'anti',
    entity(m, o, t) {
      effect(t, 'wither', 3, 1);
      effect(t, 'darkness', 3, 0);
    },
    block(m, o, loc, dim) {
      for (const x of targetsAround(dim, loc, 2.5, o)) hurt(x, 5, o, 'magic');
    },
  },
};

const PIERCING = new Set(['bc:water_dragon', 'bc:dark_crescent', 'bc:anti_magic_slash']);
const DEFAULT_META = { 'bc:dark_bolt': 0, 'bc:devil_orb': 0 };

function metaFor(proj, typeId) {
  const m = projectiles.get(proj.id);
  if (m) return m;
  if (typeId in DEFAULT_META) return /** @type {ProjMeta} */ ({ owner: '', spell: typeId, attr: 'dark', damage: 0, pierce: 0, vel: { x: 0, y: 0, z: 0 }, hit: new Set() });
  return undefined;
}

world.afterEvents.projectileHitEntity.subscribe((ev) => safe(() => {
  const typeId = safe(() => ev.projectile.typeId) ?? '';
  const h = HANDLERS[typeId];
  if (!h) return;
  const m = metaFor(ev.projectile, typeId);
  if (!m) return;
  const target = ev.getEntityHit()?.entity;
  const owner = m.owner ? world.getEntity(m.owner) : ev.source;
  const loc = ev.location;
  burst(ev.dimension, loc, h.fx, 0.7);
  if (target && !m.hit.has(target.id) && (!owner || canHit(owner, target))) {
    m.hit.add(target.id);
    h.entity?.(m, owner, target, loc);
  }
  if (PIERCING.has(typeId) && m.pierce > 0 && owner && alive(owner)) {
    // keep flying: relaunch just past the target
    const dir = V.norm(m.vel);
    const from = V.add(loc, V.mul(dir, 1.8));
    const speed = V.len(m.vel);
    system.run(() => launch(owner, typeId, from, dir, speed, { spell: m.spell, attr: m.attr, damage: m.damage, pierce: m.pierce - 1, hit: m.hit, extra: m.extra }));
  }
  projectiles.delete(ev.projectile.id);
}, 'hitEntity'));

world.afterEvents.projectileHitBlock.subscribe((ev) => safe(() => {
  const typeId = safe(() => ev.projectile.typeId) ?? '';
  const h = HANDLERS[typeId];
  if (!h) return;
  const m = metaFor(ev.projectile, typeId);
  if (!m) return;
  const owner = m.owner ? world.getEntity(m.owner) : ev.source;
  burst(ev.dimension, ev.location, h.fx, 0.6);
  h.block?.(m, owner, ev.location, ev.dimension);
  projectiles.delete(ev.projectile.id);
}, 'hitBlock'));

/** Anti-magic slashes cut through hostile spells & projectiles in flight. */
system.runInterval(() => {
  for (const [id, m] of projectiles) {
    if (m.spell !== 'black_meteorite' && m.spell !== 'spell_return') continue;
    const e = world.getEntity(id);
    if (!e) {
      projectiles.delete(id);
      continue;
    }
    safe(() => {
      for (const x of e.dimension.getEntities({ location: e.location, maxDistance: 2.8 })) {
        if (x.id === id) continue;
        const xm = projectiles.get(x.id);
        const hostileSpell = x.matches({ families: ['bc_spell'] }) && (!xm || xm.owner !== m.owner) && !['bc:tornado', 'bc:black_hole', 'bc:ice_prison'].includes(x.typeId);
        if (hostileSpell || HOSTILE_PROJECTILES.includes(x.typeId)) {
          particle(e.dimension, 'bc:anti_burst', x.location, { scale: 0.6 });
          sound(e.dimension, 'bc.anti.nullify', x.location, 0.7, 1.3);
          x.remove();
        }
      }
    });
  }
}, 2);

/** Forget metadata of projectiles that expired without hitting anything. */
system.runInterval(() => {
  for (const id of [...projectiles.keys()]) if (!world.getEntity(id)) projectiles.delete(id);
}, 200);

export { HANDLERS, COLORS, rgb };
