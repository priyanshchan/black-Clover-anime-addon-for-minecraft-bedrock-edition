// Elite enemies: now and then a hostile spellcaster spawns as an ELITE with a trait (an affix), more health and better
// loot. Its name says what it does - Vampiric, Shielded, Swift, Explosive, Summoner, Arcane or Frenzied.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { emit } from '../core/bus.js';
import { HOSTILE_SIDES, addDamageMod, center, effect, factionOf, hurt, knock, ownerOf, targetsAround } from '../core/combat.js';
import { eclipseMul } from '../core/data.js';
import { particle, rgb, sound } from '../core/fx.js';
import { makeScroll } from '../core/scrolls.js';
import { V, alive, pick, rand, safe } from '../core/util.js';
import { castSpec, heal } from './engine.js';

const AFFIXES = Object.keys(DATA.elites);
/** @type {Map<string, {affix: string, next: number, shield: number, frenzy: boolean}>} */
const elites = new Map();
const COLOR = { vampiric: 'b0101a', shielded: '60c0ff', swift: '60e070', explosive: 'ff6020', summoner: 'a040ff', arcane: 'ff70e0', frenzied: 'ffa020' };

export function eliteOf(e) {
  return elites.get(e?.id)?.affix ?? '';
}

/** Turn an enemy into an elite (a random affix unless one is given). */
export function makeElite(e, affix = pick(AFFIXES)) {
  if (!alive(e) || elites.has(e.id)) return;
  const info = DATA.elites[affix];
  safe(() => {
    e.setDynamicProperty('bc:elite', affix);
    if (affix === 'swift') e.setDynamicProperty('bc:skill', 0.95);
    const name = e.nameTag || e.typeId.slice(3).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    e.nameTag = `§6Elite ${name.replace(/§./g, '')} ${info.mc}(${info.name})`;
  });
  effect(e, 'health_boost', 9999, 2, false);
  effect(e, 'resistance', 9999, 0, false);
  if (affix === 'swift') effect(e, 'speed', 9999, 1, false);
  system.runTimeout(() => safe(() => {
    const h = e.getComponent('minecraft:health');
    if (h) h.setCurrentValue(h.effectiveMax);
  }), 2);
  elites.set(e.id, { affix, next: system.currentTick + 100, shield: affix === 'shielded' ? 3 : 0, frenzy: false });
  particle(e.dimension, 'bc:pillar', e.location, { color: rgb(COLOR[affix]), scale: 0.8 });
}

function track(e) {
  if (elites.has(e.id)) return;
  const saved = safe(() => e.getDynamicProperty('bc:elite'));
  if (typeof saved === 'string' && DATA.elites[saved]) {
    elites.set(e.id, { affix: saved, next: system.currentTick + 100, shield: saved === 'shielded' ? 3 : 0, frenzy: false });
    return;
  }
  if (typeof saved === 'string' || !HOSTILE_SIDES.has(factionOf(e)) || ownerOf(e)) return;
  if (safe(() => e.matches({ families: ['boss'] })) || e.typeId === 'bc:hive_egg' || e.typeId === 'bc:devil_gate') return;
  if (safe(() => e.getDynamicProperty('bc:minion')) === true) return;
  if (Math.random() < DATA.eliteChance * (eclipseMul() > 1 ? 1.5 : 1)) makeElite(e);
}
world.afterEvents.entitySpawn.subscribe((ev) => system.runTimeout(() => safe(() => alive(ev.entity) && track(ev.entity)), 3));
world.afterEvents.entityLoad.subscribe((ev) => safe(() => track(ev.entity)));

// Shielded: spells are halved until three blows break the shield
addDamageMod((target, attacker, amount) => {
  const st = elites.get(target.id);
  if (!st || st.affix !== 'shielded' || st.shield <= 0) return amount;
  return amount * 0.5;
});

world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const e = ev.hurtEntity;
  const src = ev.damageSource.damagingEntity;
  // Vampiric: heal on hit
  const sst = src ? elites.get(src.id) : undefined;
  if (sst?.affix === 'vampiric' && alive(src)) {
    heal(src, ev.damage * 0.3);
    particle(src.dimension, 'bc:heal', center(src), { scale: 0.5 });
  }
  const st = elites.get(e.id);
  if (!st) return;
  if (st.affix === 'shielded' && st.shield > 0 && ev.damageSource.cause === 'entityAttack' && src && V.dist(src.location, e.location) < 5) {
    st.shield -= 1;
    particle(e.dimension, 'bc:shard_burst', center(e), { color: rgb('60c0ff'), scale: 0.7 });
    if (st.shield <= 0) {
      sound(e.dimension, 'random.glass', e.location, 1, 0.8);
      if (src instanceof Player) safe(() => src.onScreenDisplay.setActionBar('§bThe elite\'s mana shield shatters!'));
    }
  }
  const h = e.getComponent('minecraft:health');
  if (st.affix === 'frenzied' && !st.frenzy && h && h.currentValue < h.effectiveMax * 0.5) {
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
  // better loot
  safe(() => dim.spawnItem(new ItemStack('bc:doubloon', 10 + Math.floor(Math.random() * 16)), loc));
  if (Math.random() < 0.4) safe(() => dim.spawnItem(makeScroll(), loc));
  if (Math.random() < 0.25) safe(() => dim.spawnItem(new ItemStack('bc:mana_potion', 1), loc));
  if (Math.random() < 0.08) safe(() => dim.spawnItem(new ItemStack(`bc:${pick(Object.keys(DATA.amulets))}`, 1), loc));
  const k = ev.damageSource.damagingEntity;
  const killer = k instanceof Player ? k : k ? world.getEntity(ownerOf(k)) : undefined;
  if (killer instanceof Player) emit('elite', killer, st.affix);
  // Explosive: a last burst
  if (st.affix === 'explosive') {
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
}, 'eliteDie'));

// Summoner and Arcane act on their own clock
system.runInterval(() => {
  const t = system.currentTick;
  for (const [id, st] of elites) {
    const e = world.getEntity(id);
    if (!e || !alive(e)) {
      elites.delete(id);
      continue;
    }
    if (t % 40 === 0) particle(e.dimension, 'bc:burst_spark', V.add(e.location, { x: 0, y: 2.2, z: 0 }), { color: rgb(COLOR[st.affix]), scale: 0.3 });
    if (st.next > t) continue;
    const foe = targetsAround(e.dimension, e.location, 16, e).find((x) => x instanceof Player || x.typeId === 'bc:magic_knight');
    if (!foe) continue;
    if (st.affix === 'summoner') {
      st.next = t + 300;
      const n = safe(() => e.dimension.getEntities({ location: e.location, maxDistance: 16, type: e.typeId }).length) ?? 0;
      if (n >= 5) continue;
      for (let i = 0; i < 2; i++) {
        const at = V.add(e.location, { x: rand(-2, 2), y: 0.5, z: rand(-2, 2) });
        particle(e.dimension, 'bc:magic_circle_dark', at, { size: 1.5, life: 0.8, color: rgb('a040ff') });
        const m = safe(() => e.dimension.spawnEntity(e.typeId, at));
        if (m) safe(() => m.setDynamicProperty('bc:minion', true));
      }
    } else if (st.affix === 'arcane') {
      st.next = t + 160;
      const a = pick(DATA.order.filter((x) => x !== 'anti'));
      const sp = DATA.spells[a].find((x) => x.spec && x.level <= 6 && !['wall', 'heal', 'buff', 'summon', 'leap'].includes(x.spec.t));
      if (sp) castSpec(e, sp.spec, `a:${a}`, 0.8, foe);
    } else st.next = t + 9999;
  }
}, 20);
