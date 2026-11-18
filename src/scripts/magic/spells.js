// Elemental spell implementations. Each spell receives a cast context and returns
// false when it could not be cast (mana / cooldown are then refunded).
import { Player, system, world } from '@minecraft/server';
import {
  aimEntity, aimPoint, blinkDestination, canHit, center, effect, groundBelow, hurt, knock, knockFrom, launch, muzzle, pull,
  targetsAlong, targetsAround, HOSTILE_PROJECTILES,
} from '../core/combat.js';
import { COLORS, anim, arc, beam, burst, groundCircle, particle, rgb, shake, shakeArea, shockwave, sound } from '../core/fx.js';
import { V, alive, rand, repeat, safe, timer } from '../core/util.js';
import { robe } from '../core/data.js';
import { trackTornado, trackBlackHole, trackPrison } from './summons.js';

/**
 * @typedef {Object} CastCtx
 * @property {import('@minecraft/server').Player} p
 * @property {import('@minecraft/server').Dimension} dim
 * @property {string} attr
 * @property {number} pw   damage multiplier
 */

const up = { x: 0, y: 1, z: 0 };
const right = (dir) => V.norm({ x: -dir.z, y: 0, z: dir.x });

/** @type {Record<string, (c: CastCtx) => boolean | void>} */
export const SPELLS = {
  // ================================================================= WIND
  gale_blades(c) {
    const dir = c.p.getViewDirection();
    anim(c.p, 'animation.bc.player.cast_sweep');
    sound(c.dim, 'bc.wind.gust', c.p.location, 0.8, 1.4);
    for (const off of [-11, 0, 11]) {
      const d = V.yaw(dir, off);
      launch(c.p, 'bc:wind_blade', muzzle(c.p, 1.2, 0.5), d, 2.3, { spell: 'gale_blades', attr: 'wind', damage: 6 * c.pw, pierce: 0 });
    }
  },
  cyclone_step(c) {
    const dir = V.flat(c.p.getViewDirection());
    anim(c.p, 'animation.bc.player.cast_forward');
    particle(c.dim, 'bc:wind_burst', c.p.location, { scale: 0.7 });
    sound(c.dim, 'bc.wind.gust', c.p.location, 1, 1.1);
    knock(c.p, dir, 3.2, 0.35);
    effect(c.p, 'slow_falling', 2.5, 0, false);
    effect(c.p, 'resistance', 1, 1, false);
    const hit = new Set();
    repeat(10, 1, () => {
      if (!alive(c.p)) return false;
      particle(c.dim, 'bc:wind_burst', c.p.location, { scale: 0.25 });
      particle(c.dim, 'bc:burst', V.add(c.p.location, { x: 0, y: 1, z: 0 }), { color: COLORS.wind, scale: 0.4 });
      for (const t of targetsAround(c.dim, c.p.location, 2.6, c.p)) {
        if (hit.has(t.id)) continue;
        hit.add(t.id);
        hurt(t, 6 * c.pw, c.p);
        knockFrom(t, c.p.location, 1.4, 0.8);
      }
    });
  },
  tempest_tornado(c) {
    const dir = V.flat(c.p.getViewDirection());
    const start = groundBelow(c.dim, V.add(c.p.location, V.add(V.mul(dir, 3), { x: 0, y: 1.5, z: 0 })), 6);
    const e = safe(() => c.dim.spawnEntity('bc:tornado', start));
    if (!e) return false;
    anim(c.p, 'animation.bc.player.cast_raise');
    groundCircle(c.dim, start, 'wind', 4);
    sound(c.dim, 'bc.wind.gust', start, 1.2, 0.7);
    trackTornado(e, c.p, dir, 6 * c.pw, 110);
  },
  storm_ascension(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    const at = c.p.location;
    groundCircle(c.dim, at, 'wind', 7, 1.5);
    shockwave(c.dim, at, 'wind', 8);
    particle(c.dim, 'bc:wind_burst', at, { scale: 1.6 });
    sound(c.dim, 'bc.wind.gust', at, 1.5, 0.6);
    shakeArea(c.dim, at, 16, 0.4, 0.6);
    knock(c.p, { x: 0, y: 0, z: 0 }, 0, 2.2);
    effect(c.p, 'slow_falling', 7, 0, false);
    effect(c.p, 'speed', 8, 1, false);
    effect(c.p, 'jump_boost', 8, 1, false);
    for (const t of targetsAround(c.dim, at, 8, c.p)) {
      hurt(t, 16 * c.pw, c.p);
      knockFrom(t, at, 2.6, 1.0);
      particle(c.dim, 'bc:burst', center(t), { color: COLORS.wind, scale: 0.8 });
    }
  },

  // ================================================================= FLAME
  flame_bullet(c) {
    anim(c.p, 'animation.bc.player.cast_forward');
    sound(c.dim, 'mob.blaze.shoot', c.p.location, 0.8, 1.1);
    launch(c.p, 'bc:fireball', muzzle(c.p), c.p.getViewDirection(), 1.9, { spell: 'flame_bullet', attr: 'flame', damage: 7 * c.pw, pierce: 0 });
  },
  blazing_pillar(c) {
    const { point } = aimPoint(c.p, 26);
    const base = groundBelow(c.dim, V.add(point, { x: 0, y: 0.5, z: 0 }), 10);
    anim(c.p, 'animation.bc.player.cast_forward');
    const spots = [base, V.add(base, { x: rand(-2.2, 2.2), y: 0, z: rand(-2.2, 2.2) }), V.add(base, { x: rand(-2.2, 2.2), y: 0, z: rand(-2.2, 2.2) })];
    for (const s of spots) particle(c.dim, 'bc:warning_circle', s, { size: 2.6, life: 0.7 });
    sound(c.dim, 'mob.blaze.breathe', base, 1, 0.8);
    spots.forEach((s, i) => timer(12 + i * 4, () => {
      particle(c.dim, 'bc:flame_pillar', s, { scale: 1 });
      particle(c.dim, 'bc:flame_burst', V.add(s, up), { scale: 0.8 });
      sound(c.dim, 'mob.ghast.fireball', s, 1, 0.7);
      for (const t of targetsAround(c.dim, V.add(s, { x: 0, y: 1.5, z: 0 }), 2.4, c.p)) {
        if (t.location.y > s.y + 5) continue;
        hurt(t, 11 * c.pw, c.p, 'fire');
        safe(() => t.setOnFire(6, true));
        knock(t, up, 0, 0.7);
      }
    }));
  },
  inferno_lion(c) {
    anim(c.p, 'animation.bc.player.cast_forward');
    sound(c.dim, 'mob.blaze.shoot', c.p.location, 1.2, 0.6);
    sound(c.dim, 'bc.devil.roar', c.p.location, 0.6, 1.6);
    launch(c.p, 'bc:flame_lion', muzzle(c.p, 1.6, 0.6), c.p.getViewDirection(), 1.25, { spell: 'inferno_lion', attr: 'flame', damage: 17 * c.pw, pierce: 0 });
  },
  solar_nova(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    const at = c.p.location;
    effect(c.p, 'fire_resistance', 6, 0, false);
    groundCircle(c.dim, at, 'flame', 10, 1.6);
    sound(c.dim, 'bc.spell.impact', at, 1.5, 0.7);
    shakeArea(c.dim, at, 20, 0.5, 0.8);
    const hit = new Set();
    repeat(10, 2, (i) => {
      const r = 1.2 + i * 1.05;
      const n = 10 + i * 3;
      for (let k = 0; k < n; k++) {
        const a = (k / n) * Math.PI * 2;
        particle(c.dim, 'bc:flame_burst', { x: at.x + Math.cos(a) * r, y: at.y + 0.4, z: at.z + Math.sin(a) * r }, { scale: 0.5 });
      }
      for (const t of targetsAround(c.dim, at, r + 0.8, c.p)) {
        if (hit.has(t.id)) continue;
        hit.add(t.id);
        hurt(t, 18 * c.pw, c.p, 'fire');
        safe(() => t.setOnFire(8, true));
        knockFrom(t, at, 1.6, 0.5);
      }
    });
  },

  // ================================================================= WATER
  water_bullet(c) {
    anim(c.p, 'animation.bc.player.cast_forward');
    sound(c.dim, 'bucket.empty_water', c.p.location, 0.7, 1.6);
    const dir = c.p.getViewDirection();
    launch(c.p, 'bc:water_orb', muzzle(c.p), dir, 2.5, { spell: 'water_bullet', attr: 'water', damage: 5 * c.pw, pierce: 0 });
    timer(3, () => alive(c.p) && launch(c.p, 'bc:water_orb', muzzle(c.p), c.p.getViewDirection(), 2.5, { spell: 'water_bullet', attr: 'water', damage: 4 * c.pw, pierce: 0 }));
  },
  healing_spring(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    const at = c.p.location;
    groundCircle(c.dim, at, 'water', 6, 1.5);
    particle(c.dim, 'bc:water_splash', V.add(at, up), { scale: 1 });
    sound(c.dim, 'bc.water.surge', at, 1, 1.2);
    const allies = c.dim.getEntities({ location: at, maxDistance: 6 }).filter((e) => {
      if (e.id === c.p.id) return true;
      if (e instanceof Player) return true;
      const tame = e.getComponent('minecraft:tameable');
      return !!tame && tame.tamedToPlayerId === c.p.id;
    });
    for (const a of allies) {
      const hp = a.getComponent('minecraft:health');
      const rose = robe(c.p) === 'blue_rose_robe' ? 1.3 : 1;
      if (hp) safe(() => hp.setCurrentValue(Math.min(hp.effectiveMax, hp.currentValue + 8 * c.pw * rose)));
      effect(a, 'regeneration', 6, 1);
      safe(() => a.extinguishFire(true));
      particle(c.dim, 'bc:heal', center(a));
    }
  },
  sea_dragon(c) {
    anim(c.p, 'animation.bc.player.cast_forward');
    sound(c.dim, 'bc.water.surge', c.p.location, 1.3, 0.8);
    launch(c.p, 'bc:water_dragon', muzzle(c.p, 1.8, 0.6), c.p.getViewDirection(), 1.5, { spell: 'sea_dragon', attr: 'water', damage: 13 * c.pw, pierce: 8 });
  },
  tidal_prison(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    const at = c.p.location;
    groundCircle(c.dim, at, 'water', 8, 1.5);
    sound(c.dim, 'bc.water.surge', at, 1.5, 0.6);
    const caught = targetsAround(c.dim, at, 8, c.p);
    for (const t of caught) {
      effect(t, 'slowness', 6, 4);
      effect(t, 'weakness', 6, 1);
      effect(t, 'mining_fatigue', 6, 2);
    }
    repeat(6, 20, () => {
      for (const t of caught) {
        if (!alive(t)) continue;
        particle(c.dim, 'bc:water_splash', center(t), { scale: 0.6 });
        particle(c.dim, 'bc:burst', center(t), { color: COLORS.water, scale: 0.5 });
        hurt(t, 3.5 * c.pw, c.p, 'drowning');
      }
    });
  },

  // ================================================================= LIGHTNING
  thunder_spear(c) {
    anim(c.p, 'animation.bc.player.cast_forward');
    sound(c.dim, 'bc.lightning.zap', c.p.location, 0.9, 1.2);
    launch(c.p, 'bc:thunder_spear', muzzle(c.p), c.p.getViewDirection(), 3.4, { spell: 'thunder_spear', attr: 'lightning', damage: 8 * c.pw, pierce: 0 });
  },
  flash_step(c) {
    const from = c.p.location;
    const to = blinkDestination(c.p, 12);
    anim(c.p, 'animation.bc.player.cast_forward');
    const a = V.add(from, { x: 0, y: 1, z: 0 });
    const b = V.add(to, { x: 0, y: 1, z: 0 });
    for (const t of targetsAlong(c.dim, a, b, 1.6, c.p)) {
      hurt(t, 7 * c.pw, c.p, 'lightning');
      particle(c.dim, 'bc:spark', center(t));
    }
    safe(() => c.p.teleport(to, { keepVelocity: false, checkForBlocks: true }));
    arc(c.dim, a, b);
    beam(c.dim, a, b, 'lightning', 0.6, 0.45, 0.4);
    sound(c.dim, 'bc.lightning.zap', to, 1, 1.5);
  },
  thunder_armor(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    effect(c.p, 'speed', 20, 2);
    effect(c.p, 'haste', 20, 1);
    effect(c.p, 'strength', 20, 0);
    c.p.setDynamicProperty('bc:thunder_until', system.currentTick + 400);
    groundCircle(c.dim, c.p.location, 'lightning', 3);
    particle(c.dim, 'bc:lightning_bolt', c.p.location, { color: rgb('fff38c') });
    sound(c.dim, 'ambient.weather.thunder', c.p.location, 0.6, 1.5);
  },
  heavens_judgment(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    const at = c.p.location;
    let targets = targetsAround(c.dim, at, 16, c.p).sort((x, y) => V.dist(x.location, at) - V.dist(y.location, at)).slice(0, 8);
    const spots = targets.length ? targets.map((t) => t.location) : Array.from({ length: 5 }, () => V.add(at, { x: rand(-7, 7), y: 0, z: rand(-7, 7) }));
    groundCircle(c.dim, at, 'lightning', 6, 1.4);
    spots.forEach((s, i) => {
      particle(c.dim, 'bc:warning_circle', groundBelow(c.dim, V.add(s, { x: 0, y: 1, z: 0 })), { size: 2.4, life: 0.4 + i * 0.15 });
      timer(8 + i * 3, () => {
        const t = targets[i];
        const loc = t && alive(t) ? t.location : s;
        particle(c.dim, 'bc:lightning_bolt', loc, { color: rgb('fff38c') });
        particle(c.dim, 'bc:burst_spark', V.add(loc, { x: 0, y: 0.5, z: 0 }), { color: COLORS.lightning, scale: 1.3 });
        sound(c.dim, 'ambient.weather.thunder', loc, 0.5, 1.3);
        for (const v of targetsAround(c.dim, loc, 2.6, c.p)) {
          hurt(v, 17 * c.pw, c.p, 'lightning');
          effect(v, 'slowness', 2, 2);
        }
      });
    });
    shakeArea(c.dim, at, 20, 0.35, 1.2);
  },

  // ================================================================= LIGHT
  light_swords(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    const target = aimEntity(c.p, 40);
    const dir = c.p.getViewDirection();
    const r = right(dir);
    const offsets = [V.add(V.mul(r, 1.4), { x: 0, y: 1.0, z: 0 }), { x: 0, y: 1.8, z: 0 }, V.add(V.mul(r, -1.4), { x: 0, y: 1.0, z: 0 })];
    sound(c.dim, 'bc.light.shine', c.p.location, 1, 1.2);
    offsets.forEach((o, i) => {
      const start = V.add(c.p.getHeadLocation(), o);
      particle(c.dim, 'bc:light_burst', start, { scale: 0.4 });
      timer(4 + i * 3, () => {
        if (!alive(c.p)) return;
        const goal = target && alive(target) ? center(target) : aimPoint(c.p, 40).point;
        const from = V.add(c.p.getHeadLocation(), o);
        launch(c.p, 'bc:light_sword', from, V.sub(goal, from), 2.7, { spell: 'light_swords', attr: 'light', damage: 7 * c.pw, pierce: 0 });
      });
    });
  },
  light_speed(c) {
    const from = c.p.location;
    const to = blinkDestination(c.p, 22);
    particle(c.dim, 'bc:light_burst', V.add(from, up), { scale: 1 });
    safe(() => c.p.teleport(to, { keepVelocity: false, checkForBlocks: true }));
    beam(c.dim, V.add(from, up), V.add(to, up), 'light', 0.5, 0.7, 0.5);
    particle(c.dim, 'bc:light_burst', V.add(to, up), { scale: 1 });
    effect(c.p, 'speed', 4, 3, false);
    sound(c.dim, 'bc.light.shine', to, 1, 1.6);
  },
  holy_ray(c) {
    anim(c.p, 'animation.bc.player.cast_forward');
    const head = c.p.getHeadLocation();
    const dir = c.p.getViewDirection();
    const { point } = aimPoint(c.p, 36);
    const a = V.add(head, V.mul(dir, 0.8));
    sound(c.dim, 'bc.light.shine', head, 1.4, 0.9);
    sound(c.dim, 'beacon.activate', head, 1, 1.4);
    repeat(4, 2, () => beam(c.dim, a, point, 'light', 0.4, 0.95, 0.45));
    for (const t of targetsAlong(c.dim, a, point, 1.3, c.p)) {
      hurt(t, 16 * c.pw, c.p, 'magic');
      particle(c.dim, 'bc:light_burst', center(t), { scale: 0.8 });
      knock(t, dir, 0.8, 0.2);
    }
    particle(c.dim, 'bc:light_burst', point, { scale: 1.2 });
  },
  radiant_rain(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    const { point } = aimPoint(c.p, 30);
    const base = groundBelow(c.dim, V.add(point, { x: 0, y: 1, z: 0 }), 10);
    groundCircle(c.dim, base, 'light', 12, 3.2);
    groundCircle(c.dim, V.add(base, { x: 0, y: 13, z: 0 }), 'light', 10, 3.2);
    sound(c.dim, 'bc.light.shine', base, 1.5, 0.7);
    repeat(24, 3, () => {
      if (!alive(c.p)) return false;
      for (let k = 0; k < 2; k++) {
        const ang = Math.random() * Math.PI * 2;
        const rr = Math.sqrt(Math.random()) * 7;
        const from = { x: base.x + Math.cos(ang) * rr, y: base.y + 13, z: base.z + Math.sin(ang) * rr };
        launch(c.p, 'bc:light_sword', from, { x: rand(-0.05, 0.05), y: -1, z: rand(-0.05, 0.05) }, 2.4, { spell: 'radiant_rain', attr: 'light', damage: 8 * c.pw, pierce: 0 });
      }
    });
  },

  // ================================================================= DARK
  dark_crescent(c) {
    anim(c.p, 'animation.bc.player.cast_sweep');
    sound(c.dim, 'mob.wither.shoot', c.p.location, 0.7, 1.4);
    launch(c.p, 'bc:dark_crescent', muzzle(c.p, 1.4, 0.4), c.p.getViewDirection(), 1.9, { spell: 'dark_crescent', attr: 'dark', damage: 10 * c.pw, pierce: 6 });
  },
  abyssal_hole(c) {
    const { point } = aimPoint(c.p, 20);
    const at = V.add(groundBelow(c.dim, V.add(point, { x: 0, y: 1, z: 0 }), 6), { x: 0, y: 1.0, z: 0 });
    const e = safe(() => c.dim.spawnEntity('bc:black_hole', at));
    if (!e) return false;
    anim(c.p, 'animation.bc.player.cast_forward');
    sound(c.dim, 'mob.wither.spawn', at, 0.6, 1.8);
    trackBlackHole(e, c.p, 4 * c.pw, 100);
  },
  shadow_cloak(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    particle(c.dim, 'bc:dark_mist', c.p.location, { scale: 1 });
    particle(c.dim, 'bc:burst_dark', V.add(c.p.location, up), { scale: 1.2 });
    sound(c.dim, 'mob.endermen.portal', c.p.location, 1, 0.6);
    effect(c.p, 'invisibility', 15, 0, false);
    effect(c.p, 'speed', 15, 1, false);
    effect(c.p, 'night_vision', 15, 0, false);
    c.p.setDynamicProperty('bc:shadow_strike', system.currentTick + 300);
  },
  rift_slash(c) {
    anim(c.p, 'animation.bc.player.cast_sweep');
    const head = c.p.getHeadLocation();
    const dir = c.p.getViewDirection();
    const a = V.add(head, V.mul(dir, 1));
    const b = V.add(head, V.mul(dir, 42));
    sound(c.dim, 'bc.anti.slash', head, 1, 0.6);
    repeat(5, 2, () => beam(c.dim, a, b, 'dark', 0.8, 0.3, 0.3));
    timer(11, () => {
      for (let t = 0; t <= 42; t += 1.4) {
        const p = V.add(a, V.mul(dir, t));
        particle(c.dim, 'bc:burst_dark', p, { scale: 0.5, color: rgb('2a1040') });
        if (t % 4.2 < 1.4) particle(c.dim, 'bc:slash_fx', p, { size: 4, rot: rand(-20, 20) });
      }
      beam(c.dim, a, b, 'dark', 0.35, 1.0, 0.5);
      sound(c.dim, 'mob.warden.sonic_boom', head, 1.2, 0.7);
      shakeArea(c.dim, head, 30, 0.5, 0.6);
      for (const t of targetsAlong(c.dim, a, b, 2.2, c.p)) {
        hurt(t, 32 * c.pw, c.p, 'magic');
        effect(t, 'wither', 4, 1);
        particle(c.dim, 'bc:burst_dark', center(t), { scale: 1 });
      }
    });
  },

  // ================================================================= ICE
  ice_spear(c) {
    anim(c.p, 'animation.bc.player.cast_forward');
    sound(c.dim, 'bc.ice.form', c.p.location, 0.7, 1.5);
    launch(c.p, 'bc:ice_spear', muzzle(c.p), c.p.getViewDirection(), 2.5, { spell: 'ice_spear', attr: 'ice', damage: 7 * c.pw, pierce: 0 });
  },
  frost_prison(c) {
    const tgt = aimEntity(c.p, 24);
    const center0 = tgt ? tgt.location : aimPoint(c.p, 20).point;
    const victims = targetsAround(c.dim, center0, 4.5, c.p).slice(0, 6);
    if (!victims.length) {
      safe(() => c.p.sendMessage('§bFrost Prison: §7no enemies near your aim.'));
      return false;
    }
    anim(c.p, 'animation.bc.player.cast_forward');
    sound(c.dim, 'bc.ice.form', center0, 1.4, 0.9);
    for (const v of victims) {
      const e = safe(() => c.dim.spawnEntity('bc:ice_prison', v.location));
      hurt(v, 7 * c.pw, c.p, 'freezing');
      effect(v, 'slowness', 4, 9, false);
      effect(v, 'mining_fatigue', 4, 3, false);
      effect(v, 'weakness', 4, 2, false);
      particle(c.dim, 'bc:ice_shatter', center(v), { scale: 0.7 });
      if (e) trackPrison(e, v, c.p, 5 * c.pw, 80);
    }
  },
  glacier_wall(c) {
    const dir = V.flat(c.p.getViewDirection());
    const r = right(dir);
    const base = V.add(c.p.location, V.mul(dir, 3.2));
    const placed = [];
    anim(c.p, 'animation.bc.player.cast_raise');
    for (let w = -3; w <= 3; w++) {
      for (let h = 0; h < 4; h++) {
        const loc = { x: Math.floor(base.x + r.x * w), y: Math.floor(base.y) + h, z: Math.floor(base.z + r.z * w) };
        const b = safe(() => c.dim.getBlock(loc));
        if (b && b.isAir) {
          safe(() => b.setType('minecraft:packed_ice'));
          placed.push(loc);
          if (h === 0 || Math.random() < 0.3) particle(c.dim, 'bc:ice_shatter', { x: loc.x + 0.5, y: loc.y + 0.5, z: loc.z + 0.5 }, { scale: 0.4 });
        }
      }
    }
    if (!placed.length) return false;
    sound(c.dim, 'bc.ice.form', base, 1.5, 0.7);
    sound(c.dim, 'random.glass', base, 0.8, 0.6);
    timer(220, () => {
      for (const loc of placed) {
        const b = safe(() => c.dim.getBlock(loc));
        if (b && b.typeId === 'minecraft:packed_ice') {
          safe(() => b.setType('minecraft:air'));
          particle(c.dim, 'bc:ice_shatter', { x: loc.x + 0.5, y: loc.y + 0.5, z: loc.z + 0.5 }, { scale: 0.4 });
        }
      }
      sound(c.dim, 'random.glass', base, 0.7, 1.2);
    });
  },
  absolute_zero(c) {
    anim(c.p, 'animation.bc.player.cast_raise');
    const at = c.p.location;
    groundCircle(c.dim, at, 'ice', 12, 5);
    sound(c.dim, 'bc.ice.form', at, 1.6, 0.6);
    repeat(10, 10, () => {
      if (!alive(c.p)) return false;
      const here = c.p.location;
      particle(c.dim, 'bc:snowstorm', here, { radius: 10 });
      for (const t of targetsAround(c.dim, here, 10, c.p)) {
        effect(t, 'slowness', 1.2, 2, false);
        hurt(t, 3 * c.pw, c.p, 'freezing');
      }
    }, () => {
      if (!alive(c.p)) return;
      const here = c.p.location;
      shockwave(c.dim, here, 'ice', 10);
      sound(c.dim, 'random.glass', here, 1.5, 0.5);
      for (const t of targetsAround(c.dim, here, 10, c.p)) {
        hurt(t, 10 * c.pw, c.p, 'freezing');
        effect(t, 'slowness', 3, 6, false);
        particle(c.dim, 'bc:ice_shatter', center(t), { scale: 1 });
      }
    });
  },
};

// ------------------------------------------------------------------ passive hooks (melee)
/** Extra on-hit effects from active buffs. */
export function onMeleeHit(player, target) {
  const t = system.currentTick;
  const thunder = player.getDynamicProperty('bc:thunder_until');
  if (typeof thunder === 'number' && thunder > t && canHit(player, target)) {
    hurt(target, 4, player, 'lightning');
    arc(player.dimension, player.getHeadLocation(), center(target));
    const next = targetsAround(player.dimension, target.location, 5, player).find((e) => e.id !== target.id);
    if (next) {
      hurt(next, 3, player, 'lightning');
      arc(player.dimension, center(target), center(next));
    }
  }
  const shadow = player.getDynamicProperty('bc:shadow_strike');
  if (typeof shadow === 'number' && shadow > t && canHit(player, target)) {
    player.setDynamicProperty('bc:shadow_strike', 0);
    hurt(target, 10, player, 'magic');
    effect(target, 'blindness', 4, 0);
    particle(player.dimension, 'bc:burst_dark', center(target), { scale: 1, color: rgb('2a1040') });
    sound(player.dimension, 'mob.endermen.portal', target.location, 1, 0.5);
    safe(() => player.removeEffect('invisibility'));
  }
}

/** Thunder armour sparkle loop. */
system.runInterval(() => {
  const t = system.currentTick;
  for (const p of world.getAllPlayers()) {
    const thunder = p.getDynamicProperty('bc:thunder_until');
    if (typeof thunder === 'number' && thunder > t) particle(p.dimension, 'bc:spark', V.add(p.location, { x: rand(-0.4, 0.4), y: rand(0.2, 1.8), z: rand(-0.4, 0.4) }));
  }
}, 3);

export { HOSTILE_PROJECTILES };
