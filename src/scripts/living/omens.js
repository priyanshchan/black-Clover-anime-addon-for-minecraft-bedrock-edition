// Omens (v1.1.0): most mornings the sky shows an omen that colours the whole day - a Mana Tide, a Wild Surge, a Starfall
// night, a Hollow Night, a Wyvern Migration, a Merchants' Fair, a Bandit Moon, a Fae Revel, Calm Skies or Lucky Stars.
// The Handbook's Atlas shows today's omen.   Cheat: /scriptevent bc:omen [id]
import { Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { emit } from '../core/bus.js';
import { effect } from '../core/combat.js';
import { particle, rgb, sound, title } from '../core/fx.js';
import { setOmenLuck } from '../core/loot.js';
import { addMods } from '../core/mods.js';
import { V, pick, rand, safe } from '../core/util.js';
import * as vfx from '../core/vfx.js';
import { addExtraSlot } from './landmarks.js';
import { compassWord } from './regions.js';

const O = DATA.world.omens;
const KEY = 'bc:omen';

/** @returns {{id: string, day: number}} */
function read() {
  const v = safe(() => world.getDynamicProperty(KEY));
  try {
    return typeof v === 'string' ? JSON.parse(v) : { id: '', day: -1 };
  } catch {
    return { id: '', day: -1 };
  }
}
/** Today's omen id ('' when the sky is plain). */
export function omen() {
  const o = read();
  const day = safe(() => world.getDay()) ?? 0;
  return o.day === day ? o.id : '';
}
export function omenInfo() {
  const id = omen();
  return id ? { id, ...O[id] } : undefined;
}

/** Start an omen for today (a random one, unless named). */
export function setOmen(id = '') {
  const day = safe(() => world.getDay()) ?? 0;
  const pickId = id || (Math.random() < DATA.world.omenChance ? pick(Object.keys(O)) : '');
  safe(() => world.setDynamicProperty(KEY, JSON.stringify({ id: pickId, day })));
  if (!pickId) return '';
  const o = O[pickId];
  for (const p of world.getAllPlayers()) {
    title(p, `${o.mc}§l${o.name}`, '§7An omen in the morning sky', 70);
    safe(() => p.sendMessage(`§7Omen of the day: ${o.mc}${o.name}§7 - ${o.desc}`));
    sound(p.dimension, 'bc.chord', p.location, 0.8, 0.9);
  }
  emit('omen', pickId);
  return pickId;
}

// a new day, a new omen
let lastDay = -1;
system.runInterval(() => {
  const day = safe(() => world.getDay()) ?? 0;
  if (lastDay < 0) {
    lastDay = day;
    if (read().day < 0) setOmen();
    return;
  }
  if (day === lastDay) return;
  lastDay = day;
  setOmen();
}, 200);

// ------------------------------------------------------------------------------- what the omens do
addMods(() => {
  const id = omen();
  if (id === 'mana_tide') return { regen: 1.25 };
  if (id === 'wild_surge') return { wild: true };
  return undefined;
});
setOmenLuck(() => (omen() === 'lucky_stars' ? 0.6 : 0));

/** Is this kind of ambush allowed today? (Calm Skies: none.) */
export function calm() {
  return omen() === 'calm';
}

const night = () => {
  const t = safe(() => world.getTimeOfDay()) ?? 6000;
  return t > 13000 && t < 23000;
};

/** A star falls somewhere 80-200 blocks from a player: a streak in the sky, and a crater with a Star Fragment. */
export function starfall(p) {
  const a = Math.random() * Math.PI * 2;
  const d = rand(80, 200);
  const x = p.location.x + Math.cos(a) * d;
  const z = p.location.z + Math.sin(a) * d;
  addExtraSlot('starfall', x, z, 1);
  const sky = { x, y: p.location.y + 60, z };
  vfx.spawn(p.dimension, 'bc:fx_signal_beam', { x, y: p.location.y, z }, { color: vfx.hex('ffe58a'), size: 1.4, life: 6 });
  particle(p.dimension, 'bc:light_burst', sky, { scale: 2 });
  sound(p.dimension, 'random.explode', p.location, 0.4, 0.5);
  safe(() => p.sendMessage(`§eA star falls to the §f${compassWord(x - p.location.x, z - p.location.z)}§e, about §f${Math.round(d)}§e blocks away.`));
  return { x, z };
}

// the omens' doings, a few times a minute
system.runInterval(() => {
  const id = omen();
  if (!id) return;
  for (const p of world.getAllPlayers()) safe(() => {
    if (p.dimension.id !== 'minecraft:overworld') return;
    if (id === 'starfall' && night() && Math.random() < 0.12) starfall(p);
    if (id === 'calm') effect(p, 'regeneration', 4, 0, false);
    if (id === 'mana_tide' && Math.random() < 0.3) particle(p.dimension, 'bc:mana_aura', V.add(p.location, { x: rand(-6, 6), y: 1, z: rand(-6, 6) }), { color: rgb('60c8ff') });
  }, 'omen');
}, 300);

system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (ev.id !== 'bc:omen') return;
  const want = ev.message.trim();
  const id = setOmen(O[want] ? want : pick(Object.keys(O)));
  const p = ev.sourceEntity instanceof Player ? ev.sourceEntity : undefined;
  if (p && !id) safe(() => p.sendMessage('§7The sky is plain today.'));
});
