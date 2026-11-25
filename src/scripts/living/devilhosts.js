// Devil hosts (v1.3.0). A devil cannot walk this world without a body - so it borrows one.
// * HOSTS of the mid-rank devils (Vharog, Sileth, Morvane, Ghorza) walk the Forsaken Realm and the Marches at night, haunt
//   Devil-Scarred regions, and march with Spade patrols. They cast their devil's magic.
// * UNION: the harder you push a host, the deeper its devil digs in. Below 60% health it reaches 50% union - horns, a devil's
//   arm, glowing marks; it heals and grows stronger. Below 30% it reaches FULL union - wings and a tail, and its devil's
//   greatest spell. Only a host beaten at full union leaves its devil's PACT SIGIL behind (and a Host Horn).
// * POSSESSION: at night a lesser devil may seize a Magic Knight near you. Beat it down - but do not kill it: below 35% health
//   the devil is driven out and the knight is free. A blow that kills the host kills the knight with it.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { emit } from '../core/bus.js';
import { center, effect, ownerOf, targetsAround } from '../core/combat.js';
import { anim, particle, rgb, shakeArea, sound, title } from '../core/fx.js';
import { addXp } from '../core/progress.js';
import * as vfx from '../core/vfx.js';
import { V, alive, pick, rand, safe, timer } from '../core/util.js';
import { giveCoins } from '../sea/bounty.js';
import { castSpec, heal } from './engine.js';
import { EVENTS, behind, night } from './events.js';
import { omen } from './omens.js';
import { realmAt, traitsAt } from './regions.js';
import { inCapital } from './capital.js';
import { kingdomAt } from './kingdoms.js';

const H = DATA.host;
const LOOKS = DATA.hostLooks;   // bc:devil property -> devil id

// ------------------------------------------------------------------------------- who is who
/** The devil inside a host ('' for anything else). */
export function devilOf(e) {
  const d = safe(() => e.getDynamicProperty('bc:devil'));
  return typeof d === 'string' ? d : '';
}
/** How deep the union goes: 0, 1 (50%) or 2 (100%). */
export function unionOf(e) {
  return Number(safe(() => e.getDynamicProperty('bc:union')) ?? 0);
}
export function possessedName(e) {
  const n = safe(() => e.getDynamicProperty('bc:possessed'));
  return typeof n === 'string' ? n : '';
}
const PCT = ['0%', '50%', '100%'];
function label(e) {
  const D = DATA.devils[devilOf(e)];
  if (!D) return;
  const who = possessedName(e);
  const u = unionOf(e);
  const name = who ? `§c${who} §7(possessed)` : `${D.mc}Host of ${D.name}`;
  safe(() => (e.nameTag = `${name} §8[${u ? D.mc : '§7'}${PCT[u]}§8]`));
}

/** Make an entity a host of a devil (exported for tests and other modules). */
export function makeHost(e, devil, opts = {}) {
  safe(() => e.setDynamicProperty('bc:devil', devil));
  safe(() => e.setDynamicProperty('bc:union', 0));
  safe(() => e.setProperty('bc:devil', Math.max(0, LOOKS.indexOf(devil))));
  safe(() => e.setProperty('bc:union', 0));
  if (opts.possessed) safe(() => e.setDynamicProperty('bc:possessed', opts.possessed));
  label(e);
  return e;
}
/** Spawn a devil host (a random mid-rank devil unless one is named). */
export function spawnHost(dim, at, devil = '', opts = {}) {
  const d = devil || pick(DATA.hostDevils);
  const e = safe(() => dim.spawnEntity('bc:devil_host', at));
  if (!e) return undefined;
  return makeHost(e, d, opts);
}

/** The devil digs deeper: union 50% or 100%. */
export function deepen(e, stage) {
  if (!alive(e) || unionOf(e) >= stage) return false;
  const D = DATA.devils[devilOf(e)];
  if (!D) return false;
  safe(() => e.setDynamicProperty('bc:union', stage));
  safe(() => e.setProperty('bc:union', stage));
  label(e);
  anim(e, 'animation.bc.devil_host.roar');
  sound(e.dimension, 'bc.devil.roar', e.location, stage === 2 ? 2.2 : 1.4, stage === 2 ? 0.6 : 0.9);
  const col = vfx.hex(D.color);
  vfx.ground(e.dimension, e.location, 'devil', col, stage === 2 ? 6 : 3.5);
  vfx.swirl(e.dimension, e.location, col, 1.4, 1.0, stage === 2 ? 1.6 : 1);
  particle(e.dimension, 'bc:burst_dark', center(e), { scale: stage === 2 ? 1.8 : 1.1, color: col });
  const hp = e.getComponent('minecraft:health');
  if (hp) heal(e, hp.effectiveMax * H.heal);
  effect(e, 'strength', 600, stage - 1, false);
  if (stage === 2) {
    effect(e, 'speed', 600, 0, false);
    effect(e, 'resistance', 600, 0, false);
    shakeArea(e.dimension, e.location, 24, 0.5, 0.8);
  }
  const who = possessedName(e);
  for (const p of e.dimension.getPlayers({ location: e.location, maxDistance: 40 })) {
    if (stage === 2) title(p, `${D.mc}§lFULL UNION`, `§7${D.name} takes the host completely`, 40);
    else safe(() => p.onScreenDisplay.setActionBar(`${D.mc}§l50% UNION §r§7- ${who ? `the devil digs into ${who}` : `${D.name}'s horns break through`}!`));
  }
  emit('host_union', e, stage);
  return true;
}

// ------------------------------------------------------------------------------- the hosts fight
const castAt = new Map();
const seen = new Set();
function foeOf(e) {
  const list = targetsAround(e.dimension, e.location, 20, e);
  // players and those who fight for them (knights, companions, wyverns), the Tidewatch and the kingdoms' soldiers - never the cattle
  const prey = list.filter((x) => x instanceof Player || x.typeId === 'bc:tamed_wyvern' || safe(() => x.matches({ families: ['bc_knight', 'bc_navy', 'bc_kingdom'] })) ||
    x.typeId === 'bc:magic_knight');
  prey.sort((a, b) => V.dist(a.location, e.location) - V.dist(b.location, e.location));
  return prey[0];
}
function think(e, t) {
  const D = DATA.devils[devilOf(e)];
  if (!D) return;
  const hp = e.getComponent('minecraft:health');
  const frac = hp ? hp.currentValue / hp.effectiveMax : 1;
  const who = possessedName(e);
  // the union deepens as the host is hurt (a possessed knight never goes past 50% - you free them first)
  if (frac < H.half && unionOf(e) < 1) deepen(e, 1);
  if (!who && frac < H.full && unionOf(e) < 2) deepen(e, 2);
  const u = unionOf(e);
  if (u >= 2 && t % 20 === 0) vfx.spawn(e.dimension, 'bc:fx_glow', center(e), { color: vfx.hex(D.color), size: 1.8, life: 0.6 }, true);
  if ((castAt.get(e.id) ?? 0) > t) return;
  const foe = foeOf(e);
  if (!foe) return;
  const moves = D.moves.slice(0, u + 1);
  const mv = u >= 2 && Math.random() < 0.4 ? moves[2] : pick(moves);
  castAt.set(e.id, t + Math.round((90 - u * 20) * (0.8 + Math.random() * 0.4)));
  anim(e, 'animation.bc.devil_host.cast');
  castSpec(e, mv.spec, `a:${D.attr}`, 0.65 + u * 0.25, foe);
  // at full union it flies at its prey
  if (u >= 2 && V.dist(foe.location, e.location) > 6 && Math.random() < 0.5) {
    const d = V.flat(V.sub(foe.location, e.location));
    safe(() => e.applyImpulse({ x: d.x * 1.1, y: 0.45, z: d.z * 1.1 }));
    particle(e.dimension, 'bc:burst_dark', center(e), { scale: 0.7, color: vfx.hex(D.color) });
  }
}
system.runInterval(() => {
  const t = system.currentTick;
  seen.clear();
  for (const p of world.getAllPlayers()) {
    for (const e of safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 48, type: 'bc:devil_host' })) ?? []) {
      if (seen.has(e.id)) continue;
      seen.add(e.id);
      safe(() => think(e, t), 'host');
    }
  }
  if (castAt.size > 256) castAt.clear();
}, 10);

// ------------------------------------------------------------------------------- possession and exorcism
/** A lesser devil seizes a Magic Knight near a player (one is found nearby, or a lone knight walks up). */
export function possess(p, knight = undefined) {
  if (p.dimension.id !== 'minecraft:overworld' || inCapital(p.location)) return undefined;
  let k = knight;
  if (!k) {
    const near = (safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 40, type: 'bc:magic_knight' })) ?? []).filter((x) => !ownerOf(x));
    k = near[0];
  }
  if (!k) {
    const at = behind(p, 16, 24);
    if (!at) return undefined;
    k = safe(() => p.dimension.spawnEntity('bc:magic_knight', at));
    if (!k) return undefined;
  }
  const name = String(k.nameTag || 'A Magic Knight').split('\n')[0].replace(/§./g, '').trim() || 'A Magic Knight';
  const loc = { ...k.location };
  const dim = k.dimension;
  particle(dim, 'bc:magic_circle_dark', V.add(loc, { x: 0, y: 0.05, z: 0 }), { size: 2.4, life: 1.2, color: rgb('ff3a2a') });
  sound(dim, 'bc.devil.roar', loc, 1.6, 1.3);
  safe(() => k.remove());
  const e = spawnHost(dim, loc, 'lesser', { possessed: name });
  if (!e) return undefined;
  title(p, '§4§lPOSSESSED', `§7A devil has seized ${name}!`, 50);
  safe(() => p.sendMessage(`§4☠ A lesser devil has taken §f${name}§4. §7Beat it out of them - but a killing blow kills the knight too.`));
  emit('possession', p, e);
  return e;
}

/** Drive the devil out of a possessed knight: the knight stands up free, and the devil flees as an imp. */
export function exorcise(e, by = undefined) {
  const name = possessedName(e);
  if (!name || !alive(e)) return undefined;
  const loc = { ...e.location };
  const dim = e.dimension;
  safe(() => e.remove());
  particle(dim, 'bc:light_burst', V.add(loc, { x: 0, y: 1, z: 0 }), { scale: 1.6 });
  sound(dim, 'bc.chord', loc, 1.2, 1.3);
  const k = safe(() => dim.spawnEntity('bc:magic_knight', loc));
  if (k) system.runTimeout(() => safe(() => (k.nameTag = `§a${name}`)), 3);
  const imp = safe(() => dim.spawnEntity('bc:imp', V.add(loc, { x: rand(-2, 2), y: 1, z: rand(-2, 2) })));
  if (imp) safe(() => imp.nameTag = '§cthe devil, cast out');
  for (const p of dim.getPlayers({ location: loc, maxDistance: 32 })) {
    title(p, '§a§lCAST OUT', `§7${name} is free`, 40);
    safe(() => p.sendMessage(`§a${name}§7: "I... I could hear it in my head. Thank you, ${p.name}."`));
  }
  const p = by instanceof Player ? by : by && ownerOf(by) ? world.getEntity(ownerOf(by)) : undefined;
  if (p instanceof Player) {
    addXp(p, 80);
    giveCoins(p, 25);
    emit('exorcism', p, name);
  }
  return k;
}

world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const e = ev.hurtEntity;
  if (e.typeId !== 'bc:devil_host' || !possessedName(e)) return;
  const hp = e.getComponent('minecraft:health');
  if (!hp || hp.currentValue <= 0 || hp.currentValue / hp.effectiveMax >= H.possessed_free) return;
  exorcise(e, ev.damageSource.damagingEntity);
}, 'exorcise'));

// ------------------------------------------------------------------------------- a host falls
/** @param {any} p */
function sigilPity(p, add) {
  const n = Number(safe(() => p.getDynamicProperty('bc:sigil_pity')) ?? 0) + add;
  safe(() => p.setDynamicProperty('bc:sigil_pity', add ? n : 0));
  return n;
}
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const e = ev.deadEntity;
  if (e.typeId !== 'bc:devil_host') return;
  const devil = devilOf(e);
  const D = DATA.devils[devil];
  const k = ev.damageSource.damagingEntity;
  const p = k instanceof Player ? k : k && ownerOf(k) ? world.getEntity(ownerOf(k)) : undefined;
  const loc = e.location;
  const dim = e.dimension;
  const who = possessedName(e);
  if (who) {
    for (const q of dim.getPlayers({ location: loc, maxDistance: 32 })) safe(() => q.sendMessage(`§c${who} is gone. §7The devil took them with it.`));
  }
  particle(dim, 'bc:smoke_burst', V.add(loc, { x: 0, y: 1, z: 0 }), { scale: 1.2 });
  if (!(p instanceof Player) || !D) return;
  emit('host_kill', p, devil);
  // only a host beaten at full union leaves its devil behind
  if (unionOf(e) < 2 || !DATA.hostDevils.includes(devil)) return;
  if (Math.random() < H.horn) safe(() => dim.spawnItem(new ItemStack('bc:host_horn', 1), loc));
  const misses = sigilPity(p, 1);
  if (Math.random() < H.sigil || misses >= H.sigil_pity) {
    sigilPity(p, 0);
    safe(() => dim.spawnItem(new ItemStack(`bc:pact_${devil}`, 1), loc));
    sound(dim, 'bc.devil.roar', loc, 1, 1.6);
    safe(() => p.sendMessage(`${D.mc}${D.name}§7 laughs as its host falls... §8"You are strong. I like strong." §7(It left its §cPact Sigil§7 behind.)`));
  }
}, 'hostDie'));

// ------------------------------------------------------------------------------- where hosts walk
/** How likely a host is to come for a player right now (exported for tests). */
export function hostChance(p) {
  if (p.dimension.id !== 'minecraft:overworld' || inCapital(p.location)) return 0;
  const realm = realmAt(p.location.x, p.location.z);
  const dark = night();
  let c = 0;
  if (dark && (realm.id === 'forsaken' || realm.id === 'marches')) c += 0.1;
  if (traitsAt(p.location).includes('devil_scarred')) c += dark ? 0.14 : 0.05;
  if (kingdomAt(p.location) === 'spade') c += 0.05;
  if (dark && omen() === 'underworld_stirs') c += 0.2;
  return Math.min(0.45, c);
}
/** One roll for a host to come for a player (exported for tests). */
export function hostRoll(p, roll = Math.random) {
  const c = hostChance(p);
  if (!c || roll() >= c) return undefined;
  if ((safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 48, type: 'bc:devil_host' }).length) ?? 0) >= 2) return undefined;
  const at = behind(p, 22, 32);
  if (!at) return undefined;
  const devil = kingdomAt(p.location) === 'spade' && roll() < 0.5 ? 'morvane' : pick(DATA.hostDevils);
  const e = spawnHost(p.dimension, at, devil);
  if (!e) return undefined;
  const n = 1 + Math.floor(roll() * 2);
  for (let i = 0; i < n; i++) safe(() => p.dimension.spawnEntity(roll() < 0.5 ? 'bc:cultist' : 'bc:imp', V.add(at, { x: rand(-3, 3), y: 0.2, z: rand(-3, 3) })));
  const D = DATA.devils[devil];
  safe(() => p.onScreenDisplay.setActionBar(`${D.mc}A devil walks in a borrowed body... §7(${D.name}, ${D.title})`));
  return e;
}
system.runInterval(() => {
  for (const p of world.getAllPlayers()) safe(() => hostRoll(p), 'hostRoll');
}, 600);

// possession: a few times a night, near someone
system.runInterval(() => {
  if (!night()) return;
  const odds = omen() === 'underworld_stirs' ? 0.3 : 0.12;
  for (const p of world.getAllPlayers()) {
    if (Math.random() < odds) safe(() => possess(p), 'possess');
  }
}, 2400);
EVENTS.possession = { w: 4, f: 'devils', ok: () => night(), run: (p) => !!possess(p) };

// a host raised by a landmark, a spawn egg or a command gets a devil of its own
world.afterEvents.entitySpawn.subscribe((ev) => safe(() => {
  const e = ev.entity;
  if (e.typeId === 'bc:devil_host' && !devilOf(e)) makeHost(e, pick(DATA.hostDevils));
}, 'hostSpawn'));

// cheat: /scriptevent bc:host [devil] - a host beside you; /scriptevent bc:host possess
system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (ev.id !== 'bc:host') return;
  const p = ev.sourceEntity instanceof Player ? ev.sourceEntity : world.getAllPlayers()[0];
  if (!p) return;
  const want = ev.message.trim();
  if (want === 'possess') {
    possess(p);
    return;
  }
  const at = V.add(p.location, V.mul(V.flat(p.getViewDirection()), 6));
  spawnHost(p.dimension, at, DATA.devils[want] ? want : '');
});

export { timer };
