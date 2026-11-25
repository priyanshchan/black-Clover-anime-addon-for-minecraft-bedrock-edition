// Elite enemies: now and then a hostile creature spawns as an ELITE with a trait (an affix), more health and better
// loot. v1.1.0 adds two higher tiers - CHAMPIONS (two traits) and INFERNALS (three) - and ten more traits; the
// farther you are from home (danger stars), the likelier they get, and Untamed regions breed twice as many.
// Traits: Vampiric, Shielded, Swift, Explosive, Summoner, Arcane, Frenzied, Blinking, Frostbound, Stormcaller, Gravitic,
// Regenerating, Reflective, Webbing, Splitting, Ghostly and Juggernaut.
import { BlockPermutation, ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { emit } from '../core/bus.js';
import { HOSTILE_SIDES, addDamageMod, center, effect, factionOf, hurt, knock, ownerOf, targetsAround } from '../core/combat.js';
import { eclipseMul } from '../core/data.js';
import { particle, rgb, sound } from '../core/fx.js';
import { makeRolled } from '../core/loot.js';
import { makeScroll } from '../core/scrolls.js';
import { V, alive, pick, rand, safe } from '../core/util.js';
import * as vfx from '../core/vfx.js';
import { castSpec, heal } from './engine.js';
import { hasTrait, starsAt } from './regions.js';

const AFFIXES = Object.keys(DATA.elites);
const TIERS = Object.fromEntries(DATA.eliteTiers.map((t) => [t.id, t]));
/** @typedef {{affix: string, affixes: string[], tier: string, next: number, shield: number, frenzy: boolean, blink: number, storm: number, pull: number, ghost: number}} EliteState */
/** @type {Map<string, EliteState>} */
const elites = new Map();
const COLOR = { vampiric: 'b0101a', shielded: '60c0ff', swift: '60e070', explosive: 'ff6020', summoner: 'a040ff', arcane: 'ff70e0', frenzied: 'ffa020',
  blinking: 'a040ff', frostbound: '8ae6ff', stormcaller: 'ffe03a', gravitic: 'c08cff', regenerating: '60e070', reflective: 'f0f0ff', webbing: 'c8c8c8',
  splitting: 'ffb040', ghostly: '3a3a4a', juggernaut: 'b0101a' };

/** The elite's first trait ('' when it is not an elite). */
export function eliteOf(e) {
  return elites.get(e?.id)?.affix ?? '';
}
/** All of its traits. */
export function traitsOf(e) {
  return elites.get(e?.id)?.affixes ?? [];
}
export function tierOf(e) {
  return elites.get(e?.id)?.tier ?? '';
}
const has = (st, a) => st.affixes.includes(a);

function fresh(affixes, tier) {
  return { affix: affixes[0], affixes, tier, next: system.currentTick + 100, shield: affixes.includes('shielded') ? 3 : 0, frenzy: false,
    blink: system.currentTick + 100, storm: system.currentTick + 120, pull: system.currentTick + 80, ghost: system.currentTick + 100 };
}

/** Which tier an elite here should be. */
export function rollTier(stars = 1) {
  const s = Math.max(0, stars - 1);
  const r = Math.random();
  const inf = DATA.eliteTierChance.infernal * (1 + 0.4 * s);
  if (r < inf) return 'infernal';
  if (r < inf + DATA.eliteTierChance.champion * (1 + 0.25 * s)) return 'champion';
  return 'elite';
}

/** Turn an enemy into an elite (random traits unless given; a Champion or Infernal when `tier` says so). */
export function makeElite(e, affix = undefined, tier = 'elite') {
  if (!alive(e) || elites.has(e.id)) return;
  const T = TIERS[tier] ?? TIERS.elite;
  const pool = AFFIXES.filter((a) => a !== affix).sort(() => Math.random() - 0.5);
  const affixes = [...(affix ? [affix] : []), ...pool].slice(0, T.affixes);
  safe(() => {
    e.setDynamicProperty('bc:elite', affixes[0]);
    e.setDynamicProperty('bc:elites', affixes.join(','));
    e.setDynamicProperty('bc:etier', T.id);
    if (affixes.includes('swift')) e.setDynamicProperty('bc:skill', 0.95);
    const name = e.nameTag || e.typeId.slice(3).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    const traits = affixes.map((a) => `${DATA.elites[a].mc}${DATA.elites[a].name}`).join('§7, ');
    e.nameTag = `${T.mc}${T.name} ${name.replace(/§./g, '')} §7(${traits}§7)`;
  });
  effect(e, 'health_boost', 9999, T.boost, false);
  effect(e, 'resistance', 9999, T.id === 'infernal' ? 1 : 0, false);
  if (affixes.includes('swift')) effect(e, 'speed', 9999, 1, false);
  if (affixes.includes('juggernaut')) {
    effect(e, 'strength', 9999, 1, false);
    effect(e, 'slowness', 9999, 0, false);
  }
  if (T.id === 'infernal') effect(e, 'fire_resistance', 9999, 0, false);
  system.runTimeout(() => safe(() => {
    const h = e.getComponent('minecraft:health');
    if (h) h.setCurrentValue(h.effectiveMax);
  }), 2);
  elites.set(e.id, fresh(affixes, T.id));
  particle(e.dimension, 'bc:pillar', e.location, { color: rgb(COLOR[affixes[0]] ?? 'ffffff'), scale: T.id === 'infernal' ? 1.4 : 0.8 });
  if (T.id === 'infernal') sound(e.dimension, 'bc.devil.roar', e.location, 1, 0.7);
}

/** The chance that a hostile spawn here turns elite. */
export function eliteChanceAt(loc) {
  const stars = starsAt(loc);
  let c = DATA.eliteChance + DATA.eliteStarBonus * Math.max(0, stars - 1);
  if (hasTrait(loc, 'untamed')) c *= 2;
  if (eclipseMul() > 1) c *= 1.5;
  return c;
}

function track(e) {
  if (elites.has(e.id)) return;
  const saved = safe(() => e.getDynamicProperty('bc:elite'));
  if (typeof saved === 'string' && DATA.elites[saved]) {
    const all = String(safe(() => e.getDynamicProperty('bc:elites')) ?? saved).split(',').filter((a) => DATA.elites[a]);
    const tier = String(safe(() => e.getDynamicProperty('bc:etier')) ?? 'elite');
    elites.set(e.id, fresh(all.length ? all : [saved], TIERS[tier] ? tier : 'elite'));
    return;
  }
  if (typeof saved === 'string' || !HOSTILE_SIDES.has(factionOf(e)) || ownerOf(e)) return;
  if (safe(() => e.matches({ families: ['boss'] })) || e.typeId === 'bc:hive_egg' || e.typeId === 'bc:devil_gate' || e.typeId === 'bc:mimic') return;
  if (safe(() => e.getDynamicProperty('bc:minion')) === true) return;
  if (DATA.eliteChance <= 0) return;
  if (Math.random() < eliteChanceAt(e.location)) makeElite(e, undefined, rollTier(starsAt(e.location)));
}
world.afterEvents.entitySpawn.subscribe((ev) => system.runTimeout(() => safe(() => alive(ev.entity) && track(ev.entity)), 3));
world.afterEvents.entityLoad.subscribe((ev) => safe(() => track(ev.entity)));

// Shielded: spells are halved until three blows break it.  Reflective: a quarter of a spell goes back to its caster.
let reflecting = false;
addDamageMod((target, attacker, amount) => {
  const st = elites.get(target.id);
  if (!st) return amount;
  let dmg = amount;
  if (has(st, 'shielded') && st.shield > 0) dmg *= 0.5;
  if (has(st, 'reflective') && attacker && !reflecting && alive(attacker) && attacker.id !== target.id) {
    reflecting = true;
    safe(() => hurt(attacker, amount * 0.25, target, 'magic'));
    reflecting = false;
    particle(target.dimension, 'bc:shard_burst', center(target), { color: rgb('f0f0ff'), scale: 0.5 });
  }
  return dmg;
});

world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const e = ev.hurtEntity;
  const src = ev.damageSource.damagingEntity;
  const sst = src ? elites.get(src.id) : undefined;
  if (sst && alive(src)) {
    // Vampiric: heal on hit
    if (has(sst, 'vampiric')) {
      heal(src, ev.damage * 0.3);
      particle(src.dimension, 'bc:heal', center(src), { scale: 0.5 });
    }
    // Frostbound: frozen limbs
    if (has(sst, 'frostbound') && alive(e)) {
      effect(e, 'slowness', 3, 2);
      effect(e, 'mining_fatigue', 3, 1);
      particle(e.dimension, 'bc:ice_shatter', center(e), { scale: 0.5 });
    }
    // Webbing: tangled in cobwebs
    if (has(sst, 'webbing') && alive(e) && Math.random() < 0.35) {
      const b = safe(() => e.dimension.getBlock({ x: Math.floor(e.location.x), y: Math.floor(e.location.y), z: Math.floor(e.location.z) }));
      if (b?.isAir) {
        safe(() => b.setPermutation(BlockPermutation.resolve('minecraft:web')));
        system.runTimeout(() => safe(() => b.typeId === 'minecraft:web' && b.setPermutation(BlockPermutation.resolve('minecraft:air'))), 80);
      }
    }
  }
  const st = elites.get(e.id);
  if (!st) return;
  if (has(st, 'shielded') && st.shield > 0 && ev.damageSource.cause === 'entityAttack' && src && V.dist(src.location, e.location) < 5) {
    st.shield -= 1;
    particle(e.dimension, 'bc:shard_burst', center(e), { color: rgb('60c0ff'), scale: 0.7 });
    if (st.shield <= 0) {
      sound(e.dimension, 'random.glass', e.location, 1, 0.8);
      if (src instanceof Player) safe(() => src.onScreenDisplay.setActionBar('§bThe elite\'s mana shield shatters!'));
    }
  }
  if (has(st, 'juggernaut')) system.run(() => safe(() => e.clearVelocity()));
  const h = e.getComponent('minecraft:health');
  if (has(st, 'frenzied') && !st.frenzy && h && h.currentValue < h.effectiveMax * 0.5) {
    st.frenzy = true;
    effect(e, 'strength', 9999, 1, false);
    effect(e, 'speed', 9999, 1, false);
    particle(e.dimension, 'bc:burst', center(e), { color: rgb('ffa020'), scale: 1 });
    sound(e.dimension, 'bc.devil.roar', e.location, 0.8, 1.4);
  }
}, 'eliteHurt'));

world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const e = ev.deadEntity;
  const st = elites.get(e.id);
  if (!st) return;
  elites.delete(e.id);
  const loc = { ...e.location };
  const dim = e.dimension;
  const stars = starsAt(loc);
  const mul = st.tier === 'infernal' ? 3 : st.tier === 'champion' ? 2 : 1;
  const untamed = hasTrait(loc, 'untamed');
  // better loot - and the higher the tier, the better
  safe(() => dim.spawnItem(new ItemStack('bc:doubloon', (10 + Math.floor(Math.random() * 16)) * mul), loc));
  if (Math.random() < 0.4) safe(() => dim.spawnItem(makeScroll(), loc));
  if (Math.random() < 0.25) safe(() => dim.spawnItem(new ItemStack('bc:mana_potion', 1), loc));
  if (Math.random() < 0.08) safe(() => dim.spawnItem(new ItemStack(`bc:${pick(Object.keys(DATA.amulets))}`, 1), loc));
  const rolled = st.tier === 'infernal' ? 1 : st.tier === 'champion' ? 0.5 : untamed ? 0.25 : 0.1;
  if (Math.random() < rolled) safe(() => dim.spawnItem(makeRolled(stars, { min: st.tier === 'infernal' ? 'rare' : st.tier === 'champion' ? 'uncommon' : 'common' }), loc));
  if (st.tier === 'infernal' && Math.random() < 0.3) safe(() => dim.spawnItem(new ItemStack('bc:star_fragment', 1), loc));
  const k = ev.damageSource.damagingEntity;
  const killer = k instanceof Player ? k : k ? world.getEntity(ownerOf(k)) : undefined;
  if (killer instanceof Player) {
    emit('elite', killer, st.affix);
    if (st.tier === 'infernal') emit('infernal', killer);
  }
  // Explosive: a last burst
  if (has(st, 'explosive')) {
    particle(dim, 'bc:warning_circle', V.add(loc, { x: 0, y: 0.1, z: 0 }), { size: 4, life: 1.1 });
    sound(dim, 'random.fuse', loc, 1, 1);
    system.runTimeout(() => {
      particle(dim, 'bc:flame_burst', loc, { scale: 1.4 });
      particle(dim, 'bc:smoke_burst', loc, { scale: 1.2 });
      sound(dim, 'random.explode', loc, 1, 1.1);
      for (const v of targetsAround(dim, loc, 4, undefined)) {
        if (safe(() => v.matches({ families: ['monster'] }))) continue;
        hurt(v, 10, undefined, 'entityExplosion');
        knock(v, V.sub(v.location, loc), 1.2, 0.5);
      }
    }, 20);
  }
  // Splitting: two lesser copies
  if (has(st, 'splitting')) {
    particle(dim, 'bc:burst', V.add(loc, { x: 0, y: 1, z: 0 }), { color: rgb('ffb040'), scale: 1 });
    for (let i = 0; i < 2; i++) {
      const m = safe(() => dim.spawnEntity(e.typeId, V.add(loc, { x: rand(-1.5, 1.5), y: 0.3, z: rand(-1.5, 1.5) })));
      if (m) safe(() => m.setDynamicProperty('bc:minion', true));
    }
  }
}, 'eliteDie'));

// the traits that act on their own clock
system.runInterval(() => {
  const t = system.currentTick;
  for (const [id, st] of elites) {
    const e = world.getEntity(id);
    if (!e || !alive(e)) {
      elites.delete(id);
      continue;
    }
    if (t % 40 === 0) particle(e.dimension, 'bc:burst_spark', V.add(e.location, { x: 0, y: 2.2, z: 0 }), { color: rgb(COLOR[st.affix] ?? 'ffffff'), scale: st.tier === 'infernal' ? 0.6 : 0.3 });
    if (has(st, 'regenerating')) safe(() => {
      const h = e.getComponent('minecraft:health');
      if (h && h.currentValue < h.effectiveMax) h.setCurrentValue(Math.min(h.effectiveMax, h.currentValue + h.effectiveMax * 0.02));
    });
    const foe = targetsAround(e.dimension, e.location, 16, e).find((x) => x instanceof Player || x.typeId === 'bc:magic_knight');
    if (!foe) continue;
    if (has(st, 'blinking') && t >= st.blink && V.dist(foe.location, e.location) > 3) {
      st.blink = t + 100;
      const behind = V.add(foe.location, V.mul(V.flat(foe.getViewDirection()), -2));
      particle(e.dimension, 'bc:burst_dark', center(e), { scale: 0.6, color: rgb('2a1040') });
      safe(() => e.teleport(behind, { facingLocation: foe.location }));
      sound(e.dimension, 'mob.endermen.portal', behind, 1, 1.2);
    }
    if (has(st, 'stormcaller') && t >= st.storm) {
      st.storm = t + 120;
      const at = { ...foe.location };
      particle(e.dimension, 'bc:warning_circle', V.add(at, { x: 0, y: 0.1, z: 0 }), { size: 2.5, life: 0.8 });
      system.runTimeout(() => {
        vfx.lightning(e.dimension, V.add(at, { x: 0, y: 14, z: 0 }), at, vfx.hex('ffe03a'), 1.2);
        sound(e.dimension, 'ambient.weather.thunder', at, 1, 1.4);
        for (const v of targetsAround(e.dimension, at, 2.5, e)) hurt(v, 6, e, 'lightning');
      }, 16);
    }
    if (has(st, 'gravitic') && t >= st.pull && V.dist(foe.location, e.location) < 10) {
      st.pull = t + 80;
      particle(e.dimension, 'bc:shockwave_dark', e.location, { scale: 0.8 });
      for (const v of targetsAround(e.dimension, e.location, 9, e)) knock(v, V.sub(e.location, v.location), 1.2, 0.2);
    }
    if (has(st, 'ghostly') && t >= st.ghost) {
      st.ghost = t + 120;
      effect(e, 'invisibility', 2, 0, false);
      particle(e.dimension, 'bc:smoke_burst', center(e), { scale: 0.4 });
    }
    if (st.next > t) continue;
    if (has(st, 'summoner')) {
      st.next = t + 300;
      const n = safe(() => e.dimension.getEntities({ location: e.location, maxDistance: 16, type: e.typeId }).length) ?? 0;
      if (n >= 5) continue;
      for (let i = 0; i < 2; i++) {
        const at = V.add(e.location, { x: rand(-2, 2), y: 0.5, z: rand(-2, 2) });
        particle(e.dimension, 'bc:magic_circle_dark', at, { size: 1.5, life: 0.8, color: rgb('a040ff') });
        const m = safe(() => e.dimension.spawnEntity(e.typeId, at));
        if (m) safe(() => m.setDynamicProperty('bc:minion', true));
      }
    } else if (has(st, 'arcane')) {
      st.next = t + 160;
      const a = pick(DATA.order.filter((x) => x !== 'anti'));
      const sp = DATA.spells[a].find((x) => x.spec && x.level <= 6 && !['wall', 'heal', 'buff', 'summon', 'leap'].includes(x.spec.t));
      if (sp) castSpec(e, sp.spec, `a:${a}`, 0.8, foe);
    } else st.next = t + 9999;
  }
}, 20);
