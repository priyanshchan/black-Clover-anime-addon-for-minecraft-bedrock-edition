// Abyss Fruits: eating, the bound power item, 18 abilities, passives, the sea's curse and anti-magic sealing.
// Abilities work for any caster entity, so Raider Captains use the very same powers as players.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { state } from '../core/data.js';
import {
  aimEntity, aimPoint, canHit, center, effect, groundBelow, hurt, knock, knockFrom, launch, pull, targetsAlong, targetsAround,
} from '../core/combat.js';
import { anim, beam, burst, particle, rgb, shakeArea, shockwave, sound, title } from '../core/fx.js';
import { V, alive, isCreative, rand, repeat, safe, timer } from '../core/util.js';
import { registerHandler } from '../magic/projectiles.js';
import { addWill, sea } from './state.js';
import { castSpec } from '../living/engine.js';
import { emit } from '../core/bus.js';

const F = DATA.fruits;
export const FRUIT_IDS = DATA.fruitOrder;
const up = { x: 0, y: 1, z: 0 };
const col = (fid) => rgb(F[fid].color);

// ------------------------------------------------------------------------------- sealing
/** Anti-magic (or seawater) shuts a fruit user's powers off for a while. */
export function sealFruit(e, ticks = 120) {
  safe(() => e.setDynamicProperty('bc:sealed', system.currentTick + ticks));
  particle(e.dimension, 'bc:anti_burst', center(e), { scale: 0.6 });
}
export function isSealed(e) {
  const v = safe(() => e.getDynamicProperty('bc:sealed'));
  return typeof v === 'number' && v > system.currentTick;
}
export function fruitOf(e) {
  if (e instanceof Player) return sea(e).fruit;
  const v = safe(() => e.getDynamicProperty('bc:fruit'));
  return typeof v === 'string' ? v : '';
}

// ------------------------------------------------------------------------------- casting context
/**
 * @typedef {Object} FCtx
 * @property {any} c        caster entity
 * @property {any} dim
 * @property {number} pw    damage multiplier
 * @property {{x:number,y:number,z:number}} dir
 * @property {{x:number,y:number,z:number}} aim
 * @property {any} [target]
 * @property {string} fid
 */

/** @returns {FCtx} */
export function ctxFor(c, fid, target) {
  const head = c.getHeadLocation();
  if (c instanceof Player) {
    const t = aimEntity(c, 32);
    const aim = t ? center(t) : aimPoint(c, 26).point;
    const s = sea(c);
    return { c, dim: c.dimension, fid, dir: c.getViewDirection(), aim, target: t, pw: 1 + state(c).level * 0.03 + s.willLv * 0.04 };
  }
  const aim = target ? center(target) : V.add(head, V.mul(c.getViewDirection(), 10));
  return { c, dim: c.dimension, fid, dir: V.norm(V.sub(aim, head)), aim, target, pw: 0.8 };
}

export function from(x, dist = 1.1, down = 0.25) {
  const h = x.c.getHeadLocation();
  return { x: h.x + x.dir.x * dist, y: h.y + x.dir.y * dist - down, z: h.z + x.dir.z * dist };
}

export function dash(c, dir, strength, lift = 0.2) {
  const f = V.flat(dir);
  if (c instanceof Player) knock(c, f, strength, lift);
  else safe(() => c.applyImpulse({ x: f.x * strength * 0.45, y: lift, z: f.z * strength * 0.45 }));
}

/** Friendly entities of the caster (for heals). */
export function allies(c, loc, r) {
  return safe(() => c.dimension.getEntities({ location: loc, maxDistance: r }).filter((e) => {
    if (e.id === c.id) return true;
    if (c instanceof Player) {
      if (e instanceof Player) return true;
      const tame = e.getComponent('minecraft:tameable');
      return (!!tame && tame.tamedToPlayerId === c.id) || e.getDynamicProperty('bc:owner') === c.id;
    }
    return e.matches({ families: ['bc_pirate'] });
  })) ?? [];
}

export function explode(dim, loc, owner, radius, dmg, fire) {
  burst(dim, loc, 'flame', radius / 2.5);
  particle(dim, 'bc:flame_burst', loc, { scale: radius / 2.5 });
  particle(dim, 'bc:smoke_burst', loc, { scale: radius / 3 });
  particle(dim, 'bc:rock_debris', loc, { scale: radius / 3 });
  shockwave(dim, loc, 'flame', radius);
  sound(dim, 'random.explode', loc, 1.2, 0.8);
  shakeArea(dim, loc, radius * 4, 0.45, 0.6);
  for (const t of targetsAround(dim, loc, radius, owner)) {
    hurt(t, dmg * (1 - Math.min(0.5, V.dist(t.location, loc) / radius * 0.5)), owner, 'entityExplosion');
    if (fire) safe(() => t.setOnFire(fire, true));
    knockFrom(t, loc, 1.4, 0.6);
  }
}

// ------------------------------------------------------------------------------- the abilities
/** @type {Record<string, (x: FCtx) => boolean | void>} */
export const ABILITIES = {
  // ------------------------------------------------ Ember
  ember_fist(x) {
    sound(x.dim, 'mob.blaze.shoot', x.c.location, 1, 0.9);
    launch(x.c, 'bc:fireball', from(x), x.dir, 2.0, { spell: 'ember_fist', attr: 'flame', damage: 8 * x.pw, pierce: 0 });
  },
  blaze_step(x) {
    const dir = V.flat(x.dir);
    dash(x.c, dir, 2.8);
    sound(x.dim, 'mob.ghast.fireball', x.c.location, 0.8, 1.3);
    const hit = new Set();
    repeat(9, 1, () => {
      if (!alive(x.c)) return false;
      const l = x.c.location;
      particle(x.dim, 'bc:flame_burst', V.add(l, { x: 0, y: 0.4, z: 0 }), { scale: 0.35 });
      for (const t of targetsAround(x.dim, l, 2.0, x.c)) {
        if (hit.has(t.id)) continue;
        hit.add(t.id);
        hurt(t, 7 * x.pw, x.c, 'fire');
        safe(() => t.setOnFire(5, true));
      }
    });
  },
  cinder_nova(x) {
    const at = x.c.location;
    effect(x.c, 'fire_resistance', 5, 0, false);
    sound(x.dim, 'bc.spell.impact', at, 1.2, 1.2);
    shakeArea(x.dim, at, 14, 0.35, 0.6);
    const hit = new Set();
    repeat(7, 2, (i) => {
      const r = 1 + i;
      for (let k = 0; k < 8 + i * 3; k++) {
        const a = (k / (8 + i * 3)) * Math.PI * 2;
        particle(x.dim, 'bc:flame_burst', { x: at.x + Math.cos(a) * r, y: at.y + 0.4, z: at.z + Math.sin(a) * r }, { scale: 0.4 });
      }
      for (const t of targetsAround(x.dim, at, r + 0.6, x.c)) {
        if (hit.has(t.id)) continue;
        hit.add(t.id);
        hurt(t, 14 * x.pw, x.c, 'fire');
        safe(() => t.setOnFire(6, true));
        knockFrom(t, at, 1.3, 0.4);
      }
    });
  },
  // ------------------------------------------------ Stone
  boulder_fist(x) {
    sound(x.dim, 'bc.stone.crack', x.c.location, 0.8, 1.2);
    launch(x.c, 'bc:boulder', from(x, 1.4, 0.4), x.dir, 1.6, { spell: 'boulder_fist', attr: 'stone', damage: 10 * x.pw, pierce: 0 });
  },
  earth_spikes(x) {
    const dir = V.flat(x.dir);
    const start = x.c.location;
    const hit = new Set();
    for (let i = 1; i <= 12; i++) {
      timer(i, () => {
        const p = groundBelow(x.dim, V.add(start, V.add(V.mul(dir, i * 1.1), { x: 0, y: 2, z: 0 })), 5);
        particle(x.dim, 'bc:rock_debris', V.add(p, { x: 0, y: 0.3, z: 0 }), { scale: 0.7 });
        particle(x.dim, 'bc:smoke_burst', p, { scale: 0.3 });
        if (i % 3 === 0) sound(x.dim, 'bc.stone.crack', p, 0.7, 0.9 + Math.random() * 0.3);
        for (const t of targetsAround(x.dim, V.add(p, { x: 0, y: 1, z: 0 }), 1.6, x.c)) {
          if (hit.has(t.id)) continue;
          hit.add(t.id);
          hurt(t, 9 * x.pw, x.c);
          knock(t, up, 0, 0.9);
        }
      });
    }
  },
  fortress_skin(x) {
    effect(x.c, 'resistance', 8, 2, false);
    effect(x.c, 'slowness', 8, 0, false);
    particle(x.dim, 'bc:rock_debris', V.add(x.c.location, { x: 0, y: 1, z: 0 }), { scale: 1 });
    sound(x.dim, 'bc.stone.crack', x.c.location, 1, 0.6);
    x.c.setDynamicProperty('bc:fortress_until', system.currentTick + 160);
  },
  // ------------------------------------------------ Gravity
  gravity_crush(x) {
    const at = groundBelow(x.dim, V.add(x.aim, { x: 0, y: 1, z: 0 }), 8);
    sound(x.dim, 'bc.gravity.hum', at, 1, 0.8);
    particle(x.dim, 'bc:shockwave', at, { radius: 4.5, color: col('gravity') });
    particle(x.dim, 'bc:magic_circle_ground', at, { color: col('gravity'), size: 6, life: 0.8 });
    for (const t of targetsAround(x.dim, V.add(at, { x: 0, y: 1, z: 0 }), 4.8, x.c)) {
      hurt(t, 9 * x.pw, x.c, 'magic');
      effect(t, 'slowness', 2.5, 4);
      knock(t, up, 0, -1.4);
      particle(x.dim, 'bc:rock_debris', t.location, { scale: 0.4 });
    }
  },
  repulse(x) {
    const at = x.c.location;
    sound(x.dim, 'bc.gravity.hum', at, 1.2, 1.4);
    particle(x.dim, 'bc:shockwave', at, { radius: 7, color: col('gravity') });
    for (const t of targetsAround(x.dim, at, 7, x.c)) {
      hurt(t, 6 * x.pw, x.c, 'magic');
      knockFrom(t, at, 3.0, 0.7);
    }
  },
  falling_star(x) {
    const at = groundBelow(x.dim, V.add(x.aim, { x: 0, y: 1, z: 0 }), 10);
    particle(x.dim, 'bc:warning_circle', at, { size: 7, life: 1.4 });
    sound(x.dim, 'bc.gravity.hum', at, 1.5, 0.5);
    timer(14, () => {
      if (!alive(x.c)) return;
      const sky = V.add(at, { x: rand(-6, 6), y: 26, z: rand(-6, 6) });
      launch(x.c, 'bc:meteor', sky, V.sub(at, sky), 1.5, { spell: 'falling_star', attr: 'gravity', damage: 22 * x.pw, pierce: 0 });
    });
  },
  // ------------------------------------------------ Shadow
  shadow_bind(x) {
    const at = x.aim;
    particle(x.dim, 'bc:magic_circle_dark', groundBelow(x.dim, V.add(at, up), 6), { size: 7, life: 1.2 });
    sound(x.dim, 'mob.endermen.portal', at, 1, 0.5);
    for (const t of targetsAround(x.dim, at, 5, x.c)) {
      hurt(t, 4 * x.pw, x.c, 'magic');
      effect(t, 'slowness', 4, 9, false);
      effect(t, 'weakness', 4, 1);
      particle(x.dim, 'bc:dark_mist', t.location, { scale: 0.4 });
    }
  },
  shade_step(x) {
    const t = x.target;
    particle(x.dim, 'bc:burst_dark', center(x.c), { scale: 0.8, color: rgb('2a1040') });
    if (t && alive(t)) {
      const behind = V.sub(t.location, V.mul(V.flat(safe(() => t.getViewDirection()) ?? x.dir), 1.6));
      safe(() => x.c.teleport(behind, { facingLocation: center(t), keepVelocity: false }));
      hurt(t, 8 * x.pw, x.c, 'magic');
      effect(t, 'blindness', 2, 0);
    } else {
      const to = V.add(x.c.location, V.mul(V.flat(x.dir), 8));
      safe(() => x.c.teleport(to, { checkForBlocks: true, keepVelocity: false }));
    }
    particle(x.dim, 'bc:burst_dark', center(x.c), { scale: 0.8, color: rgb('2a1040') });
    sound(x.dim, 'mob.endermen.portal', x.c.location, 1, 0.8);
  },
  umbral_legion(x) {
    if (!(x.c instanceof Player)) return ABILITIES.shadow_bind(x);
    sound(x.dim, 'mob.evocation_illager.prepare_summon', x.c.location, 1, 0.7);
    for (let i = 0; i < 3; i++) {
      const a = (i / 3) * Math.PI * 2;
      const at = groundBelow(x.dim, V.add(x.c.location, { x: Math.cos(a) * 2, y: 2, z: Math.sin(a) * 2 }), 5);
      particle(x.dim, 'bc:dark_mist', at, { scale: 0.5 });
      timer(6 + i * 3, () => {
        const e = safe(() => x.dim.spawnEntity('bc:shade_soldier', at));
        if (e) {
          safe(() => e.setDynamicProperty('bc:owner', x.c.id));
          e.nameTag = `§8${x.c.name}'s Shade`;
        }
      });
    }
  },
  // ------------------------------------------------ Bloom
  thorn_lash(x) {
    const a = V.add(x.c.getHeadLocation(), V.mul(x.dir, 0.8));
    const b = V.add(a, V.mul(x.dir, 9));
    beam(x.dim, a, b, 'wind', 0.5, 0.35, 0.4);
    for (let t = 0; t < 9; t += 1.5) particle(x.dim, 'bc:leaf_burst', V.add(a, V.mul(x.dir, t)), { scale: 0.25 });
    sound(x.dim, 'bc.wind.gust', x.c.location, 0.6, 1.8);
    for (const t of targetsAlong(x.dim, a, b, 1.3, x.c)) {
      hurt(t, 7 * x.pw, x.c);
      effect(t, 'poison', 3, 0);
      knock(t, V.mul(x.dir, -1), 0.6, 0.2);
    }
  },
  healing_pollen(x) {
    const at = x.c.location;
    particle(x.dim, 'bc:leaf_burst', V.add(at, up), { scale: 1.2 });
    particle(x.dim, 'bc:magic_circle_ground', at, { color: col('bloom'), size: 6, life: 1.2 });
    sound(x.dim, 'bc.light.shine', at, 0.8, 1.4);
    for (const a of allies(x.c, at, 6)) {
      const hp = a.getComponent('minecraft:health');
      if (hp) safe(() => hp.setCurrentValue(Math.min(hp.effectiveMax, hp.currentValue + 7 * x.pw)));
      effect(a, 'regeneration', 6, 0);
      particle(x.dim, 'bc:heal', center(a));
    }
  },
  rooting_grove(x) {
    const at = x.c.location;
    particle(x.dim, 'bc:magic_circle_ground', at, { color: col('bloom'), size: 14, life: 4 });
    sound(x.dim, 'bc.stone.crack', at, 1, 1.4);
    const caught = targetsAround(x.dim, at, 8, x.c);
    for (const t of caught) effect(t, 'slowness', 4, 9, false);
    repeat(4, 20, () => {
      for (const t of caught) {
        if (!alive(t)) continue;
        hurt(t, 4 * x.pw, x.c);
        particle(x.dim, 'bc:leaf_burst', t.location, { scale: 0.4 });
      }
    });
  },
  // ------------------------------------------------ Quicksilver
  mercury_blades(x) {
    sound(x.dim, 'random.glass', x.c.location, 0.6, 1.8);
    for (const off of [-16, -8, 0, 8, 16]) {
      launch(x.c, 'bc:metal_blade', from(x), V.yaw(x.dir, off), 2.4, { spell: 'mercury_blades', attr: 'quicksilver', damage: 5 * x.pw, pierce: 0 });
    }
  },
  flow_dash(x) {
    const dir = V.flat(x.dir);
    const a = V.add(x.c.location, up);
    const b = V.add(a, V.mul(dir, 7));
    dash(x.c, dir, 3.0, 0.1);
    sound(x.dim, 'bc.water.surge', x.c.location, 0.7, 1.8);
    const hit = new Set();
    repeat(7, 1, () => {
      if (!alive(x.c)) return false;
      particle(x.dim, 'bc:shard_burst', V.add(x.c.location, up), { color: col('quicksilver'), scale: 0.3 });
      for (const t of targetsAlong(x.dim, a, b, 1.6, x.c)) {
        if (hit.has(t.id)) continue;
        hit.add(t.id);
        hurt(t, 9 * x.pw, x.c);
        knock(t, dir, 0.6, 0.2);
      }
    });
  },
  silver_storm(x) {
    sound(x.dim, 'random.glass', x.c.location, 1, 0.7);
    repeat(20, 4, (i) => {
      if (!alive(x.c)) return false;
      const at = x.c.location;
      for (let k = 0; k < 4; k++) {
        const a = i * 0.7 + (k * Math.PI) / 2;
        particle(x.dim, 'bc:shard_burst', { x: at.x + Math.cos(a) * 2.6, y: at.y + 1, z: at.z + Math.sin(a) * 2.6 }, { color: col('quicksilver'), scale: 0.25 });
      }
      for (const t of targetsAround(x.dim, V.add(at, up), 3.6, x.c)) hurt(t, 3 * x.pw, x.c);
    });
  },
};

/** Is this ability open to the player yet? (A fruit's fourth move needs Will.) */
export function abilityOpen(p, ab) {
  if (!ab?.will || isCreative(p)) return true;
  return sea(p).willLv >= ab.will;
}

/** Cast an ability with any entity (used by players, Raider Captains and companions). */
export function castAbility(caster, fid, abilityId, target, pwMul = 1) {
  if (isSealed(caster)) return false;
  const fn = ABILITIES[abilityId];
  const x = ctxFor(caster, fid, target);
  x.pw *= pwMul;
  if (!fn) {
    // wave 4 fruits are recipes for the spell engine
    const spec = F[fid]?.abilities.find((a) => a.id === abilityId)?.spec;
    if (!spec) return false;
    return safe(() => castSpec(caster, spec, `f:${fid}`, x.pw, x.target), `fruit:${abilityId}`);
  }
  return safe(() => fn(x), `fruit:${abilityId}`);
}

// ------------------------------------------------------------------------------- projectile hits
registerHandler('bc:boulder', {
  fx: 'wind',
  entity(m, o, t, loc) {
    hurt(t, m.damage, o);
    knock(t, m.vel, 1.4, 0.4);
    particle(t.dimension, 'bc:rock_debris', loc, { scale: 0.8 });
    sound(t.dimension, 'bc.stone.crack', loc, 1, 1);
  },
  block(m, o, loc, dim) {
    particle(dim, 'bc:rock_debris', loc, { scale: 0.8 });
    sound(dim, 'bc.stone.crack', loc, 0.8, 1.1);
    for (const t of targetsAround(dim, loc, 2, o)) hurt(t, m.damage * 0.5, o);
  },
});
registerHandler('bc:meteor', {
  fx: 'flame',
  entity(m, o, t, loc) {
    explode(t.dimension, loc, o, 5.5, m.damage, 6);
  },
  block(m, o, loc, dim) {
    explode(dim, loc, o, 5.5, m.damage, 6);
  },
});
registerHandler('bc:metal_blade', {
  fx: 'light',
  entity(m, o, t, loc) {
    hurt(t, m.damage, o);
    particle(t.dimension, 'bc:shard_burst', loc, { color: col('quicksilver'), scale: 0.4 });
  },
  block(m, o, loc, dim) {
    particle(dim, 'bc:shard_burst', loc, { color: col('quicksilver'), scale: 0.4 });
  },
});

// ------------------------------------------------------------------------------- eating
function powerItem(p, fid) {
  const f = F[fid];
  const item = new ItemStack(`bc:power_${fid}`, 1);
  safe(() => item.setLore([`§7${f.passive}`, `§8Owner: §f${p.name}`, '§8Use: §7ability   §8Sneak + Use: §7switch']));
  return item;
}

function hasItem(p, typeId) {
  const inv = p.getComponent('minecraft:inventory')?.container;
  if (!inv) return false;
  for (let i = 0; i < inv.size; i++) if (inv.getItem(i)?.typeId === typeId) return true;
  return false;
}

export function givePower(p) {
  const s = sea(p);
  if (!s.fruit || hasItem(p, `bc:power_${s.fruit}`)) return;
  const left = p.getComponent('minecraft:inventory')?.container?.addItem(powerItem(p, s.fruit));
  if (left) p.dimension.spawnItem(left, p.location);
}

world.afterEvents.itemCompleteUse.subscribe((ev) => safe(() => {
  const id = ev.itemStack.typeId;
  if (!id.startsWith('bc:fruit_')) return;
  const p = ev.source;
  const fid = id.slice('bc:fruit_'.length);
  const s = sea(p);
  const dim = p.dimension;
  if (s.fruit) {
    title(p, '§4Your body rejects it!', '§cNo one can hold two Abyss Fruits', 50);
    hurt(p, 14, undefined, 'magic');
    effect(p, 'nausea', 8, 0);
    effect(p, 'wither', 4, 1);
    particle(dim, 'bc:burst_dark', center(p), { scale: 1, color: rgb('2a0010') });
    return;
  }
  s.fruit = fid;
  s.ability = 0;
  s.dirty = true;
  const f = F[fid];
  title(p, `${f.mc}§l${f.name}`, `§7${f.passive} §8- §9the sea now rejects you`, 80);
  sound(dim, 'bc.fruit.eat', p.location, 1, 1);
  particle(dim, 'bc:burst', center(p), { color: col(fid), scale: 1.2 });
  particle(dim, 'bc:magic_circle_ground', p.location, { color: col(fid), size: 4, life: 1.5 });
  safe(() => p.sendMessage(`${f.glyph} ${f.mc}${f.name}§f: you gained the ${f.mc}${f.power}§f. Hold it to use your powers. §7Deep water will drain you, and anti-magic can seal you.`));
  givePower(p);
}, 'eat'));

// give the power back after death (fruit powers stay with you)
world.afterEvents.playerSpawn.subscribe((ev) => {
  system.runTimeout(() => safe(() => givePower(ev.player), 'regive'), 20);
});

// ------------------------------------------------------------------------------- using the power item
export function usePower(p, item) {
  const s = sea(p);
  const fid = item.typeId.slice('bc:power_'.length);
  const creative = isCreative(p);
  if (s.fruit !== fid && !creative) {
    safe(() => p.sendMessage('§7Nothing happens. This power belongs to another body.'));
    return;
  }
  const f = F[fid];
  if (!f) return;
  if (p.isSneaking) {
    for (let k = 1; k <= f.abilities.length; k++) {
      s.ability = (s.ability + 1) % f.abilities.length;
      if (abilityOpen(p, f.abilities[s.ability])) break;
    }
    s.dirty = true;
    s.lastUse = system.currentTick;
    const ab = f.abilities[s.ability];
    sound(p.dimension, 'bc.grimoire.flip', p.location, 0.6, 1.3);
    safe(() => p.onScreenDisplay.setTitle(' ', { fadeInDuration: 0, stayDuration: 30, fadeOutDuration: 8, subtitle: `${f.mc}${ab.name} §7- ${ab.desc}` }));
    return;
  }
  if (isSealed(p)) {
    safe(() => p.onScreenDisplay.setActionBar('§8Your power is sealed by anti-magic...'));
    return;
  }
  if (drained(p) && !creative) {
    safe(() => p.onScreenDisplay.setActionBar('§9The sea drains your power. Get out of the water!'));
    return;
  }
  const ab = f.abilities[s.ability] ?? f.abilities[0];
  const t = system.currentTick;
  if (!abilityOpen(p, ab)) {
    safe(() => p.onScreenDisplay.setActionBar(`${DATA.glyphs.lock} §8${ab.name} §7awakens at §5Will ${ab.will}`));
    return;
  }
  if ((s.cd.get(ab.id) ?? 0) > t) {
    s.lastUse = t;
    return;
  }
  s.cd.set(ab.id, t + Math.round(ab.cooldown * 20));
  s.lastUse = t;
  anim(p, s.ability >= 2 ? 'animation.bc.player.cast_raise' : 'animation.bc.player.cast_forward');
  const ok = castAbility(p, fid, ab.id);
  if (ok === false) s.cd.delete(ab.id);
  else {
    addWill(p, 0);
    emit('cast', p, ab.id);
  }
}

// ------------------------------------------------------------------------------- passives & the sea's curse
export function drained(p) {
  if (!p.isInWater) return false;
  if (sea(p).fruit === 'shark') return false; // the Shark Fruit belongs to the sea
  const h = p.getHeadLocation();
  const b = safe(() => p.dimension.getBlock({ x: Math.floor(h.x), y: Math.floor(h.y), z: Math.floor(h.z) }));
  return !!b && (b.typeId === 'minecraft:water' || b.typeId === 'minecraft:flowing_water');
}

const warned = new Set();
system.runInterval(() => {
  const night = (() => {
    const t = world.getTimeOfDay();
    return t > 13000 && t < 23000;
  })();
  for (const p of world.getAllPlayers()) {
    const fid = sea(p).fruit;
    if (!fid) continue;
    safe(() => {
      if (drained(p)) {
        effect(p, 'slowness', 1, 1, false);
        effect(p, 'weakness', 1, 1, false);
        effect(p, 'mining_fatigue', 1, 1, false);
        knock(p, { x: 0, y: 0, z: 0 }, 0, -0.08);
        if (!warned.has(p.id)) {
          warned.add(p.id);
          safe(() => p.onScreenDisplay.setActionBar('§9The sea rejects your fruit... your strength drains away!'));
        }
        return;
      }
      warned.delete(p.id);
      if (isSealed(p)) return;
      if (fid === 'ember') effect(p, 'fire_resistance', 2, 0, false);
      else if (fid === 'stone') effect(p, 'resistance', 2, 0, false);
      else if (fid === 'gravity') {
        if (p.isFalling && p.getVelocity().y < -0.5) effect(p, 'slow_falling', 1, 0, false);
      } else if (fid === 'shadow') {
        effect(p, 'night_vision', 12, 0, false);
        if (night && p.isSneaking) effect(p, 'invisibility', 1, 0, false);
      } else if (fid === 'bloom') {
        const below = p.dimension.getBlock({ x: Math.floor(p.location.x), y: Math.floor(p.location.y) - 1, z: Math.floor(p.location.z) });
        if (below && (below.typeId === 'minecraft:grass_block' || below.typeId.endsWith('_leaves'))) effect(p, 'regeneration', 2, 0, false);
      }
    });
  }
}, 10);

/** Ember punches ignite; called from the melee hook. */
export function onFruitMelee(p, target) {
  const fid = sea(p).fruit;
  if (!fid || isSealed(p) || drained(p) || !canHit(p, target)) return;
  if (fid === 'ember') safe(() => target.setOnFire(4, true));
  else if (fid === 'stone') knock(target, V.sub(target.location, p.location), 0.8, 0.2);
}

// shade soldiers stay with their owner and vanish when the owner leaves
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    safe(() => {
      for (const e of p.dimension.getEntities({ location: p.location, maxDistance: 64, type: 'bc:shade_soldier' })) {
        if (e.getDynamicProperty('bc:owner') !== p.id) continue;
        if (V.dist(e.location, p.location) > 16) safe(() => e.teleport(V.add(p.location, { x: rand(-2, 2), y: 0.5, z: rand(-2, 2) })));
      }
    });
  }
}, 40);
