// Relics and rolled weapons at work (v1.1.0). Relics count while they sit in your hotbar - up to three of them, the
// first three from the left. Rolled weapons work while held. Their affixes feed the mana and spell maths (core/mods.js),
// give effects (Swiftness, Night Vision...), cut damage you take, and add procs to your blows: burning, freezing,
// lightning, life drain, mana drain, executions, giant-felling and cleaving.
import { EquipmentSlot, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { emit } from '../core/bus.js';
import { center, effect, hurt, targetsAround } from '../core/combat.js';
import { addMana } from '../core/data.js';
import { particle, rgb, sound } from '../core/fx.js';
import { isLegend, readRoll } from '../core/loot.js';
import { addMods, mods } from '../core/mods.js';
import { V, alive, safe } from '../core/util.js';
import * as vfx from '../core/vfx.js';
import { heal } from './engine.js';
import { eliteOf } from './elites.js';

const SLOTS = DATA.loot.relicSlots;

/** @type {Map<string, {t: number, relics: Record<string, number>, names: string[]}>} */
const cache = new Map();
/** The summed affixes of a player's active relics (hotbar, first three). */
export function relicsOf(p) {
  const t = system.currentTick;
  const c = cache.get(p.id);
  if (c && t - c.t < 20) return c;
  /** @type {Record<string, number>} */
  const relics = {};
  const names = [];
  const inv = safe(() => p.getComponent('minecraft:inventory')?.container);
  for (let i = 0; inv && i < 9 && names.length < SLOTS; i++) {
    const it = safe(() => inv.getItem(i));
    if (!it || !it.typeId.startsWith('bc:relic_')) continue;
    const roll = readRoll(it);
    if (!roll) continue;
    names.push(roll.name);
    for (const [k, v] of Object.entries(roll.affixes)) relics[k] = (relics[k] ?? 0) + v;
  }
  const out = { t, relics, names };
  cache.set(p.id, out);
  return out;
}
/** The roll of the weapon a player is holding, or undefined. */
export function weaponOf(p) {
  const it = safe(() => p.getComponent('minecraft:equippable')?.getEquipment(EquipmentSlot.Mainhand));
  if (!it) return undefined;
  const roll = readRoll(it);
  return roll?.kind === 'weapon' ? roll : undefined;
}

addMods((p) => {
  if (!(p instanceof Player)) return undefined;
  const r = relicsOf(p).relics;
  if (!Object.keys(r).length) return undefined;
  return {
    maxMana: r.mana ?? 0, regen: 1 + (r.regen ?? 0) / 100, power: 1 + (r.power ?? 0) / 100, cd: 1 - (r.haste ?? 0) / 100, xp: 1 + (r.scholar ?? 0) / 100,
    melee: 1 + (r.might ?? 0) / 100, luck: r.luck ?? 0, fortune: r.fortune ?? 0, guard: (r.guard ?? 0) / 100, ward: (r.ward ?? 0) / 100,
    thorns: r.thorns ?? 0, leech: (r.leech ?? 0) / 100,
  };
});

// effects from relics (and Haste from a Quick weapon)
system.runInterval(() => {
  for (const p of world.getAllPlayers()) safe(() => {
    const r = relicsOf(p).relics;
    if (r.swift) effect(p, 'speed', 3, 0, false);
    if (r.leap) effect(p, 'jump_boost', 3, 0, false);
    if (r.sight) safe(() => p.addEffect('night_vision', 320, { amplifier: 0, showParticles: false }));
    if (r.gills) effect(p, 'water_breathing', 3, 0, false);
    if (r.ember) effect(p, 'fire_resistance', 3, 0, false);
    if ((r.vigor ?? 0) >= 4) {
      const lvl = Math.min(4, Math.floor(r.vigor / 4)) - 1;
      const cur = safe(() => p.getEffect('health_boost'));
      if (!cur || cur.amplifier !== lvl || cur.duration < 100) safe(() => p.addEffect('health_boost', 600, { amplifier: lvl, showParticles: false }));
    }
    if (weaponOf(p)?.affixes.quick) effect(p, 'haste', 3, 0, false);
  }, 'relicFx');
}, 40);

// ------------------------------------------------------------------------------- blows
let echo = false;
world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  if (echo) return;
  const e = ev.hurtEntity;
  const src = ev.damageSource.damagingEntity;
  const cause = ev.damageSource.cause;
  // the wearer is struck: guard (all damage), ward (spells), thorns
  if (e instanceof Player && alive(e)) {
    const m = mods(e);
    const cut = ev.damage * (m.guard + (cause === 'magic' ? m.ward : 0));
    if (cut > 0) heal(e, Math.min(ev.damage, cut));
    if (m.thorns > 0 && src && cause === 'entityAttack' && alive(src) && V.dist(src.location, e.location) < 6) {
      echo = true;
      safe(() => hurt(src, m.thorns, e, 'thorns'));
      echo = false;
    }
  }
  // a player's melee blow: might, weapon affixes, leech
  if (!(src instanceof Player) || cause !== 'entityAttack' || !alive(src)) return;
  const p = src;
  const m = mods(p);
  const w = weaponOf(p);
  const a = w?.affixes ?? {};
  let extra = ev.damage * (m.melee - 1) + ev.damage * (a.sharp ?? 0) / 100;
  const hp = safe(() => e.getComponent('minecraft:health'));
  if (a.executioner && hp && hp.currentValue < hp.effectiveMax * 0.3) extra += ev.damage * a.executioner / 100;
  if (a.giantslayer && (safe(() => e.matches({ families: ['boss'] })) || eliteOf(e))) extra += ev.damage * a.giantslayer / 100;
  echo = true;
  try {
    if (extra > 0.5 && alive(e)) hurt(e, extra, p, 'magic');
    if (a.burning && alive(e)) safe(() => e.setOnFire(a.burning, true));
    if (a.frost && Math.random() < a.frost / 100 && alive(e)) {
      effect(e, 'slowness', 3, 3);
      particle(e.dimension, 'bc:ice_shatter', center(e), { scale: 0.6 });
    }
    if (a.storm && Math.random() < a.storm / 100 && alive(e)) {
      const at = { ...e.location };
      vfx.lightning(e.dimension, V.add(at, { x: 0, y: 12, z: 0 }), at, vfx.hex('ffe03a'), 1);
      sound(e.dimension, 'ambient.weather.thunder', at, 0.8, 1.6);
      for (const v of targetsAround(e.dimension, at, 3, p)) hurt(v, 6, p, 'lightning');
    }
    if (a.cleave) {
      const next = targetsAround(e.dimension, e.location, 3, p).find((v) => v.id !== e.id);
      if (next) {
        hurt(next, ev.damage * a.cleave / 100, p);
        particle(e.dimension, 'bc:slash_fx', center(next), { scale: 0.8, color: rgb('ffffff') });
      }
    }
  } finally {
    echo = false;
  }
  const leech = m.leech + (a.vampiric ?? 0) / 100;
  if (leech > 0) heal(p, (ev.damage + extra) * leech);
  if (a.mana_thirst) addMana(p, a.mana_thirst);
}, 'relicHits'));

// a Legendary or Mythic in your hands: the world should know
const seen = new Set();
system.runInterval(() => {
  for (const p of world.getAllPlayers()) safe(() => {
    const inv = p.getComponent('minecraft:inventory')?.container;
    for (let i = 0; inv && i < inv.size; i++) {
      const it = inv.getItem(i);
      if (!it || (!it.typeId.startsWith('bc:relic_') && !it.typeId.startsWith('minecraft:'))) continue;
      const roll = readRoll(it);
      if (!roll || !isLegend(roll)) continue;
      const key = `${p.id}|${roll.name}`;
      if (seen.has(key)) continue;
      seen.add(key);
      safe(() => p.sendMessage(`§6§l${roll.rarity === 'mythic' ? 'MYTHIC' : 'LEGENDARY'}! §r§f${roll.name}§7 is yours.`));
      sound(p.dimension, 'bc.fanfare', p.location, 1, 1.2);
      emit('legendary', p, roll);
    }
  }, 'legendScan');
}, 60);
