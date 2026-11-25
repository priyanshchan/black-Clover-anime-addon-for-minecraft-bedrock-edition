// Devil Union (v1.3.0): a pact with a devil of your own.
// * THE PACT: a Pact Sigil (left by a host beaten at full union, or by the Crowned Vessel) lets you hear its devil's offer.
//   Accept and you are bound: the devil's BOON and its PRICE are with you from then on (one devil at a time).
// * THE GAUGE: fighting fills your union gauge - landing blows, taking them, and above all killing (devils most of all).
// * UNION: use the sigil with the gauge at 50% to join with your devil - horns break through and your blows and spells
//   grow stronger; its first two moves are yours (use: cast, sneak-use: switch). With the gauge full and a BOND of 3 or
//   more you join at 100% - wings, far greater power, and the devil's third move. The gauge drains while you are joined,
//   and a 50% union deepens to 100% by itself if you fill the gauge again in battle.
// * BOND grows with every second joined and every kill made joined. At bond 5 your devil no longer fights you at 50%.
// * THE DEVIL'S HOLD: while you are joined the devil pushes to take over (faster at 100%; Will and bond push back). Let its
//   hold fill and it TAKES OVER for ten seconds: it lashes out at anything near you, friend or foe, then leaves you weak.
//   A Binding Chain breaks its hold and keeps it quiet for two minutes.
import { Player, system, world } from '@minecraft/server';
import { ActionFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { emit } from '../core/bus.js';
import { canHit, center, effect, hurt, knock, ownerOf } from '../core/combat.js';
import { anim, particle, shakeArea, shockwave, sound, title } from '../core/fx.js';
import { addHeldHud, addHudSuffix, gaugeBar } from '../core/hud.js';
import { addMods } from '../core/mods.js';
import * as vfx from '../core/vfx.js';
import { V, alive, clamp, isCreative, pick, rand, safe } from '../core/util.js';
import { sea } from '../sea/state.js';
import { castSpec } from './engine.js';
import { omen } from './omens.js';

const U = DATA.union;
const KEY = 'bc:pact';

/**
 * @typedef {{devil: string, bond: number, gauge: number, hold: number, move: number}} Pact
 * @typedef {{mode: number, taken: number, chain: number, cds: Map<string, number>, ready: boolean, bondLv: number, since: number}} Live
 */
/** @type {Map<string, Pact>} */
const pacts = new Map();
/** @type {Map<string, Live>} */
const live = new Map();
const dirty = new Set();

/** A player's pact (devil '' when they have none). @returns {Pact} */
export function pactOf(p) {
  let s = pacts.get(p.id);
  if (s) return s;
  let raw;
  try {
    const v = safe(() => p.getDynamicProperty(KEY));
    raw = typeof v === 'string' ? JSON.parse(v) : undefined;
  } catch {
    raw = undefined;
  }
  s = { devil: '', bond: 0, gauge: 0, hold: 0, move: 0, ...(raw ?? {}) };
  if (!DATA.devils[s.devil]) s.devil = '';
  pacts.set(p.id, s);
  return s;
}
/** @returns {Live} */
function liveOf(p) {
  let l = live.get(p.id);
  if (!l) live.set(p.id, (l = { mode: 0, taken: 0, chain: 0, cds: new Map(), ready: false, bondLv: 0, since: 0 }));
  return l;
}
function save(p) {
  dirty.add(p.id);
}
system.runInterval(() => {
  for (const id of dirty) {
    const p = world.getEntity(id);
    const s = pacts.get(id);
    if (p && s) safe(() => p.setDynamicProperty(KEY, JSON.stringify(s)));
  }
  dirty.clear();
}, 40);

/** Bond level 1-5 from bond points. */
export function bondLevel(points) {
  let lv = 0;
  for (const at of U.bond) if (points >= at) lv++;
  return Math.max(1, lv);
}
/** 0 apart, 1 at 50%, 2 at 100%. */
export function unionMode(p) {
  return live.get(p.id)?.mode ?? 0;
}
export function takenOver(p) {
  return (live.get(p.id)?.taken ?? 0) > system.currentTick;
}
const devilOf = (p) => DATA.devils[pactOf(p).devil];

// ------------------------------------------------------------------------------- the pact
/** Bind a player to a devil (a new pact replaces the old one). */
export function bind(p, devil) {
  const D = DATA.devils[devil];
  if (!D || !DATA.pactDevils.includes(devil)) return false;
  const s = pactOf(p);
  if (unionMode(p)) leave(p, 'quiet');
  Object.assign(s, { devil, bond: 0, gauge: 0, hold: 0, move: 0 });
  const l = liveOf(p);
  l.ready = false;
  l.bondLv = 1;
  save(p);
  title(p, `${D.mc}§lPACT SEALED`, `§7${D.name}, ${D.title}, is bound to you`, 60);
  sound(p.dimension, 'bc.devil.roar', p.location, 1, 0.8);
  vfx.ground(p.dimension, p.location, 'devil', vfx.hex(D.color), 3);
  safe(() => p.sendMessage(`${D.mc}${D.name}§7: "${D.offer}"\n§7Boon: §a${D.boon_text}§7. Price: §c${D.price_text}§7. Fight to fill your union gauge, then use the sigil.`));
  emit('pact', p, devil);
  return true;
}

/** Hear a devil's offer (the Pact Sigil's first use). */
export async function offerPact(p, devil) {
  const D = DATA.devils[devil];
  if (!D) return false;
  const cur = pactOf(p).devil;
  const moves = D.moves.map((m, i) => `§f${m.name}§7${i === 2 ? ' §8(100% union only)' : ''} - ${m.desc}`).join('\n');
  const body = [`§8${DATA.devilRanks[D.rank]} devil of ${D.vice}`, `§7${D.name} is ${D.desc}.`, '', `${D.mc}"${D.offer}"`, '',
    `§aBoon: §f${D.boon_text}`, `§cPrice: §f${D.price_text}`, '', '§7Its magic:', moves,
    ...(cur && cur !== devil ? ['', `§c§lYour pact with ${DATA.devils[cur].name} will be broken.`] : [])].join('\n');
  const f = new ActionFormData().title(`${D.mc}§l${D.name}, ${D.title}`).body(body);
  f.button('§4§lAccept the pact');
  f.button('Refuse');
  const r = await f.show(p);
  if (r.canceled || r.selection !== 0) {
    safe(() => p.onScreenDisplay.setActionBar(`${D.mc}${D.name}§7: "You will come back. They always do."`));
    return false;
  }
  return bind(p, devil);
}

// ------------------------------------------------------------------------------- joining
/** Join with your devil at 50% or 100% union. */
export function join(p, mode) {
  const D = devilOf(p);
  if (!D) return false;
  const l = liveOf(p);
  const first = l.mode === 0;
  l.mode = mode;
  if (first) l.since = system.currentTick;
  const col = vfx.hex(D.color);
  anim(p, 'animation.bc.player.cast_raise');
  sound(p.dimension, mode === 2 ? 'bc.blackform' : 'bc.devil.roar', p.location, 1.3, mode === 2 ? 0.8 : 1.1);
  shockwave(p.dimension, p.location, 'anti', mode === 2 ? 7 : 4);
  vfx.ground(p.dimension, p.location, 'devil', col, mode === 2 ? 6 : 3.5);
  vfx.swirl(p.dimension, p.location, col, 1.4, 1.2, mode === 2 ? 1.8 : 1.1);
  if (mode === 2) {
    shakeArea(p.dimension, p.location, 24, 0.6, 1.0);
    title(p, `${D.mc}§lFULL UNION`, `§7You and ${D.name} are one`, 50);
  } else title(p, `${D.mc}§l50% UNION`, `§7${D.name} lends you its power`, 40);
  emit('union', p, mode);
  return true;
}
/** Use the sigil apart from your devil: join if you can. */
export function tryJoin(p) {
  const s = pactOf(p);
  const D = devilOf(p);
  if (!D) return false;
  if (takenOver(p)) return false;
  const lv = bondLevel(s.bond);
  if (s.gauge >= U.full && lv >= U.full_bond) return join(p, 2);
  if (s.gauge >= U.half || isCreative(p)) return join(p, s.gauge >= U.full && lv >= U.full_bond ? 2 : 1);
  safe(() => p.onScreenDisplay.setActionBar(`${D.mc}${D.name}§7 stirs... union gauge §c${Math.floor(s.gauge)}%§7 - fight to fill it (§f50%§7 to join)`));
  sound(p.dimension, 'bc.mana.empty', p.location);
  return false;
}
/** The union ends: the gauge ran dry, the devil let go, or a chain broke it. */
export function leave(p, why = 'spent') {
  const l = liveOf(p);
  if (!l.mode) return false;
  const D = devilOf(p);
  l.mode = 0;
  l.taken = 0;
  safe(() => p.removeEffect('slow_falling'));
  safe(() => p.removeEffect('jump_boost'));
  if (D && why === 'spent') safe(() => p.onScreenDisplay.setActionBar(`§7The union fades. §8(${D.name} withdraws, for now)`));
  if (D) particle(p.dimension, 'bc:smoke_burst', center(p), { scale: 0.8 });
  save(p);
  return true;
}

// ------------------------------------------------------------------------------- the devil's moves
/** The moves open to you now (two at 50%, all three at 100%; all three to look at while apart). */
function openMoves(p) {
  const D = devilOf(p);
  if (!D) return [];
  const m = unionMode(p);
  return m === 1 ? D.moves.slice(0, 2) : D.moves;
}
export function switchMove(p) {
  const s = pactOf(p);
  const list = openMoves(p);
  if (!list.length) return;
  s.move = (s.move + 1) % list.length;
  save(p);
  const mv = list[s.move];
  safe(() => p.onScreenDisplay.setActionBar(`${devilOf(p).mc}§l${mv.name}§r §7- ${mv.desc} §8(costs ${mv.cost}% union)`));
}
/** Cast the chosen devil move (costs union gauge, not mana). */
export function castMove(p) {
  const s = pactOf(p);
  const D = devilOf(p);
  const l = liveOf(p);
  if (!D || !l.mode) return false;
  if (takenOver(p)) {
    safe(() => p.onScreenDisplay.setActionBar(`§4${D.name} has the reins!`));
    return false;
  }
  const list = openMoves(p);
  if (s.move >= list.length) s.move = 0;
  const mv = list[s.move];
  const t = system.currentTick;
  const ready = l.cds.get(mv.id) ?? 0;
  if (ready > t && !isCreative(p)) {
    safe(() => p.onScreenDisplay.setActionBar(`§7${mv.name} §c${((ready - t) / 20).toFixed(1)}s`));
    return false;
  }
  if (s.gauge < mv.cost && !isCreative(p)) {
    safe(() => p.onScreenDisplay.setActionBar(`§c${mv.name} needs ${mv.cost}% union §7(you have ${Math.floor(s.gauge)}%)`));
    return false;
  }
  const pw = (1 + 0.08 * (bondLevel(s.bond) - 1)) * (D.rank === 'higher' ? U.higher.power : 1);
  if (!castSpec(p, mv.spec, `a:${D.attr}`, pw)) return false;
  if (!isCreative(p)) s.gauge = Math.max(0, s.gauge - mv.cost);
  s.hold = Math.min(100, s.hold + 3);
  l.cds.set(mv.id, t + Math.round(mv.cd * 20));
  save(p);
  emit('devil_cast', p, mv.id);
  return true;
}

/** The Pact Sigil in your hand. */
export function useSigil(p, itemId) {
  const devil = itemId.replace('bc:pact_', '');
  const s = pactOf(p);
  if (s.devil !== devil) {
    system.run(() => offerPact(p, devil).catch(() => {}));
    return true;
  }
  if (p.isSneaking) switchMove(p);
  else if (unionMode(p)) castMove(p);
  else tryJoin(p);
  return true;
}

/** A Binding Chain: the devil's hold breaks, and it stays quiet for a while. */
export function useChain(p) {
  const s = pactOf(p);
  const D = devilOf(p);
  if (!D) {
    safe(() => p.onScreenDisplay.setActionBar('§7You have no devil to bind.'));
    return false;
  }
  const l = liveOf(p);
  s.hold = 0;
  l.chain = system.currentTick + U.chain_seconds * 20;
  if (l.taken) {
    l.taken = 0;
    leave(p, 'chain');
    safe(() => p.sendMessage(`§7The chain bites. §8${D.name} howls and lets you go.`));
  }
  particle(p.dimension, 'bc:anti_burst', center(p), { scale: 0.8 });
  sound(p.dimension, 'random.anvil_land', p.location, 0.5, 1.6);
  safe(() => p.onScreenDisplay.setActionBar(`§7The Binding Chain holds ${D.name} §8(no takeover for ${U.chain_seconds / 60} minutes)`));
  save(p);
  return true;
}

// ------------------------------------------------------------------------------- the gauge fills in battle
function gain(p, n) {
  const s = pactOf(p);
  if (!s.devil || n <= 0) return;
  const mul = (omen() === 'underworld_stirs' ? 1.5 : 1) * (unionMode(p) ? 0.5 : 1);
  s.gauge = clamp(s.gauge + n * mul, 0, 100);
  const l = liveOf(p);
  if (!l.mode && !l.ready && s.gauge >= U.half) {
    l.ready = true;
    const D = devilOf(p);
    safe(() => p.onScreenDisplay.setActionBar(`${D.mc}${D.name}§7: "${pick(D.whispers)}" §8(union ready - use the sigil)`));
  }
  if (s.gauge < U.half) l.ready = false;
  // a 50% union deepens by itself when the gauge fills in battle (and the bond is strong enough)
  if (l.mode === 1 && !takenOver(p) && s.gauge >= U.full && bondLevel(s.bond) >= U.full_bond) join(p, 2);
  save(p);
}
/** Add to a player's union gauge (exported for tests and events). */
export function addGauge(p, n) {
  gain(p, n / ((omen() === 'underworld_stirs' ? 1.5 : 1) * (unionMode(p) ? 0.5 : 1)));
}
const playerOf = (e) => (e instanceof Player ? e : e && ownerOf(e) ? world.getEntity(ownerOf(e)) : undefined);
world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const by = ev.damageSource.damagingEntity;
  const hit = ev.hurtEntity;
  if (by instanceof Player && hit !== by && pactOf(by).devil) gain(by, ev.damage * U.hit);
  if (hit instanceof Player && pactOf(hit).devil && ev.damage > 0) gain(hit, ev.damage * U.hurt);
}, 'unionHurt'));
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const dead = ev.deadEntity;
  if (dead instanceof Player) {
    leave(dead, 'fell');
    return;
  }
  const p = playerOf(ev.damageSource.damagingEntity);
  if (!(p instanceof Player) || !pactOf(p).devil) return;
  const devil = safe(() => dead.matches({ families: ['bc_devil'] }));
  gain(p, devil ? U.devil_kill : U.kill);
  if (unionMode(p)) pactOf(p).bond += 6;
}, 'unionKill'));

// ------------------------------------------------------------------------------- the devil's turn
/** The devil takes over (exported for tests). */
export function takeover(p) {
  const D = devilOf(p);
  const l = liveOf(p);
  if (!D || !l.mode) return false;
  l.taken = system.currentTick + U.takeover * 20;
  title(p, '§4§lTAKEN', `§7${D.name} has the reins!`, 50);
  sound(p.dimension, 'bc.devil.roar', p.location, 2, 0.5);
  effect(p, 'nausea', U.takeover + 2, 0, false);
  safe(() => p.sendMessage(`${D.mc}${D.name}§7: "${pick(D.whispers)}" §4(The devil has taken over! It will let go in ${U.takeover} seconds - or break its hold with a Binding Chain.)`));
  emit('takeover', p);
  return true;
}
function devilActs(p, D) {
  // it lashes out at whatever is close - foe or friend
  const near = (safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 10, excludeFamilies: ['inanimate', 'bc_spell'] })) ?? [])
    .filter((e) => e.id !== p.id && e.getComponent('minecraft:health'));
  const t = pick(near);
  if (t && canHit(p, t)) castSpec(p, pick(D.moves.slice(0, unionMode(p) === 2 ? 3 : 2)).spec, `a:${D.attr}`, 1.1, t);
  else if (t) {
    hurt(t, 4, undefined, 'magic');
    particle(p.dimension, 'bc:burst_dark', center(t), { scale: 0.7, color: vfx.hex(D.color) });
  }
  knock(p, { x: rand(-1, 1), y: 0, z: rand(-1, 1) }, 0.7, 0.25);
}

// ------------------------------------------------------------------------------- every second
system.runInterval(() => {
  const t = system.currentTick;
  for (const p of world.getAllPlayers()) safe(() => {
    const s = pactOf(p);
    const D = devilOf(p);
    if (!D) return;
    const l = liveOf(p);
    const lv = bondLevel(s.bond);
    if (l.bondLv && lv > l.bondLv) {
      safe(() => p.sendMessage(`${D.mc}Bond ${lv} with ${D.name}.${lv === U.full_bond ? ' §7You can now join at §c100%§7 union.' : ''}${lv === U.steady_bond ? ' §7It no longer fights you at 50%.' : ''}`));
      emit('bond', p, lv);
    }
    l.bondLv = lv;
    if (!l.mode) {
      s.hold = Math.max(0, s.hold - U.hold_decay);
      return;
    }
    // joined: a full gauge deepens a 50% union; the gauge drains, the bond grows, the devil pushes
    if (l.mode === 1 && !takenOver(p) && s.gauge >= U.full && lv >= U.full_bond) join(p, 2);
    const higher = D.rank === 'higher';
    if (!isCreative(p)) s.gauge = Math.max(0, s.gauge - U.drain[l.mode - 1]);
    s.bond += 1;
    const will = sea(p).willLv ?? 0;
    let push = U.hold[l.mode - 1] * (higher ? U.higher.hold : 1) * Math.max(0.4, 1 - 0.08 * will) * Math.max(0.5, 1 - 0.08 * (lv - 1));
    if (l.mode === 1 && lv >= U.steady_bond) push = 0;
    if (l.chain > t) push = 0;
    if (!l.taken || l.taken <= t) s.hold = Math.min(100, s.hold + push);
    if (Math.random() < 0.04) safe(() => p.sendMessage(`§8${D.name}: §7"${pick(D.whispers)}"`));
    if (l.mode === 2) {
      effect(p, 'slow_falling', 2, 0, false);
      effect(p, 'jump_boost', 2, 1, false);
    }
    if (l.taken && l.taken <= t) {
      // the devil lets go - and leaves you spent
      l.taken = 0;
      s.gauge = 0;
      s.hold = 0;
      effect(p, 'weakness', 20, 0, false);
      leave(p, 'taken');
      safe(() => p.sendMessage(`§7You claw your way back. §8(${D.name} lets go... for now)`));
    } else if (!l.taken && s.hold >= 100) takeover(p);
    else if (s.gauge <= 0) leave(p, 'spent');
    save(p);
  }, 'union');
}, 20);

// the devil drives
system.runInterval(() => {
  const t = system.currentTick;
  for (const p of world.getAllPlayers()) {
    const l = live.get(p.id);
    if (!l || !l.taken || l.taken <= t) continue;
    const D = devilOf(p);
    if (D) safe(() => devilActs(p, D), 'devilActs');
  }
}, 30);

// horns, wings and an aura in the devil's colour (particles that keep up with you)
system.runInterval(() => {
  const t = system.currentTick;
  for (const p of world.getAllPlayers()) {
    const l = live.get(p.id);
    if (!l || !l.mode) continue;
    const D = devilOf(p);
    if (!D) continue;
    safe(() => {
      const col = vfx.hex(l.taken > t ? 'ff1010' : D.color);
      const v = safe(() => p.getVelocity()) ?? { x: 0, y: 0, z: 0 };
      const at = V.add(p.location, { x: v.x * 2, y: v.y * 2, z: v.z * 2 });
      const dir = V.flat(p.getViewDirection());
      const crouch = p.isSneaking ? -0.3 : 0;
      vfx.spawn(p.dimension, 'bc:union_horns', V.add(at, { x: 0, y: 2.0 + crouch, z: 0 }), { color: col, scale: l.mode === 2 ? 1.3 : 1 });
      if (l.mode === 2) vfx.spawn(p.dimension, 'bc:union_wings', V.add(at, { x: -dir.x * 0.34, y: 1.2 + crouch, z: -dir.z * 0.34 }), { color: col, dir, scale: 1 + Math.sin(t / 3) * 0.06 });
      if (t % 6 === 0) vfx.aura(p.dimension, p.location, col, 0.6);
    });
  }
}, 2);

// ------------------------------------------------------------------------------- stats, HUD
const ADD = ['maxMana', 'luck', 'fortune', 'guard', 'ward', 'thorns', 'leech'];
function merge(into, m) {
  for (const [k, v] of Object.entries(m ?? {})) {
    if (ADD.includes(k)) into[k] = (into[k] ?? 0) + v;
    else into[k] = (into[k] ?? 1) * v;
  }
  return into;
}
addMods((p) => {
  if (!(p instanceof Player)) return undefined;
  const D = devilOf(p);
  if (!D) return undefined;
  const m = merge(merge({}, D.boon), D.price);
  const mode = unionMode(p);
  if (mode) {
    merge(m, mode === 2 ? U.full_mods : U.half_mods);
    if (D.rank === 'higher') merge(m, { power: U.higher.power });
  }
  return m;
});

const MODE = ['§7apart', '§c50% union', '§4§l100% union§r'];
/** The union line: gauge, mode, the devil's hold. */
export function unionText(p) {
  const s = pactOf(p);
  const D = devilOf(p);
  if (!D) return '';
  const l = liveOf(p);
  if (takenOver(p)) return `§4§l${D.name} HAS THE REINS§r §8${Math.ceil((l.taken - system.currentTick) / 20)}s`;
  return `${D.mc}${D.name} ${gaugeBar(s.gauge, 100)} §c${Math.floor(s.gauge)}%§7 ${MODE[l.mode]} §8hold ${Math.floor(s.hold)}%`;
}
for (const d of DATA.pactDevils) {
  addHeldHud(`bc:pact_${d}`, (p) => {
    const s = pactOf(p);
    const D = DATA.devils[d];
    if (s.devil !== d) return `${D.mc}${D.name}'s Pact Sigil §7- use it to hear its offer.`;
    const list = openMoves(p);
    const mv = list[s.move] ?? list[0];
    const t = system.currentTick;
    const cd = liveOf(p).cds.get(mv.id) ?? 0;
    const mvText = cd > t ? `§7${mv.name} §c${((cd - t) / 20).toFixed(1)}s` : `${D.mc}§l${mv.name}§r`;
    return `${unionText(p)} §8| ${mvText} §8[${s.move + 1}/${list.length}] §7bond ${bondLevel(s.bond)}`;
  });
}
addHudSuffix((p) => (unionMode(p) ? `  §4${DATA.glyphs.clover5 ?? '♣'}${unionMode(p) === 2 ? '100' : '50'}% §c${Math.floor(pactOf(p).gauge)}` : undefined));

/** The Handbook's Devil Union page. */
export async function devilPage(p, back) {
  const s = pactOf(p);
  const D = devilOf(p);
  const head = D
    ? [`${D.mc}§l${D.name}, ${D.title}§r §8(${DATA.devilRanks[D.rank]}, ${D.vice})`, unionText(p),
      `§7Bond §f${bondLevel(s.bond)}§7/5 §8(${s.bond} points)  §aBoon: §f${D.boon_text}  §cPrice: §f${D.price_text}`,
      ...D.moves.map((m, i) => `§f${m.name}§7 - ${m.desc} §8(${m.cost}% union${i === 2 ? ', 100% only' : ''})`)]
    : ['§7You have made no pact. Beat a devil host at §cfull union§7 and it may leave its §cPact Sigil§7 behind.'];
  const how = [
    '§l§4Devil hosts§r §7walk the Forsaken Realm and the Marches at night, haunt Devil-Scarred land and march with Spade patrols. Hurt one and its devil digs in: §c50% union§7 below 60% health (horns, a devil\'s arm), §4full union§7 below 30% (wings, its greatest spell). Only a host beaten at full union leaves its §cPact Sigil§7 (and a Host Horn).',
    '§l§4Your pact§r §7Use a Pact Sigil to hear its devil\'s offer. Fighting fills your union gauge; at 50% use the sigil to join. At 100% with bond 3 you join fully: wings, far more power, a third move. Sigil: use to cast, sneak-use to switch.',
    '§l§4The devil\'s hold§r §7While joined it pushes to take over. If its hold fills it lashes out at anything near you for 10 seconds. A §7Binding Chain§7 breaks its hold. Bond and Will push back; at bond 5 it never fights you at 50%.',
    '§l§4Possession§r §7At night a lesser devil may seize a Magic Knight. Beat it below a third of its health to cast the devil out - a killing blow kills the knight too.',
    '§l§4The Crowned Vessel§r §7waits in Underworld Breaches far from home, or answers an Abyssal Crown raised at night. Beat it for Vaelgrim\'s own sigil.',
  ];
  const r = await new ActionFormData().title('§4§lDevil Union').body([...head, '', ...how].join('\n\n')).button('Back').show(p);
  if (!r.canceled && back) await back();
}

// cheat: /scriptevent bc:union [devil] - bind, fill the gauge and bond 3; /scriptevent bc:union off - break the pact
system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (ev.id !== 'bc:union') return;
  const p = ev.sourceEntity instanceof Player ? ev.sourceEntity : world.getAllPlayers()[0];
  if (!p) return;
  const want = ev.message.trim();
  if (want === 'off') {
    leave(p, 'quiet');
    Object.assign(pactOf(p), { devil: '', bond: 0, gauge: 0, hold: 0, move: 0 });
    save(p);
    return;
  }
  const s = pactOf(p);
  if (DATA.pactDevils.includes(want) && s.devil !== want) bind(p, want);
  if (!s.devil) bind(p, 'vharog');
  s.gauge = 100;
  s.bond = Math.max(s.bond, U.bond[U.full_bond - 1]);
  save(p);
});

export { alive };
