// Friendly fights.
// * SPARRING: pick two companions with the whistle and they duel with real spells - at reduced strength, and the
//   match stops as soon as one of them is down to a third of their health. Both learn from it; the winner gloats.
// * RIVAL SQUADS: a squad of knights from another company challenges your party (world event). Their spells only
//   sting, and a rival who is beaten yields. Beat them all for doubloons, experience and a big boost to morale.
import { Player, system, world } from '@minecraft/server';
import { ActionFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { addDamageMod, addFoes, addRelation, center, ownerOf } from '../core/combat.js';
import { anim, particle, rgb, sound, title } from '../core/fx.js';
import { V, alive, pick, rand, safe } from '../core/util.js';
import { giveKnightXp, nameKnight, setupKnight } from './knights.js';
import { addBond, addInfo, addWhistleButtons, bark, entityOf, memberOf, party, save } from './companions.js';
import { giveCoins } from '../sea/bounty.js';

const C = DATA.companion;
const COMPANIES = ['Silver Talon', 'Ember Fang', 'Azure Antler', 'Iron Heron', 'Scarlet Thorn', 'Golden Lynx'];

// ------------------------------------------------------------------------------- sparring
/** @type {Map<string, {a: string, b: string, until: number, owner: string}>} key = a's id */
const spars = new Map();

function sparOf(e) {
  for (const s of spars.values()) if (s.a === e.id || s.b === e.id) return s;
  return undefined;
}

export function startSpar(p, ma, mb) {
  const a = entityOf(ma);
  const b = entityOf(mb);
  if (!a || !b || sparOf(a) || sparOf(b)) return false;
  spars.set(a.id, { a: a.id, b: b.id, until: system.currentTick + 1800, owner: p.id });
  for (const [x, y] of [[a, b], [b, a]]) safe(() => x.setDynamicProperty('bc:spar', y.id));
  const mid = V.lerp(a.location, b.location, 0.5);
  particle(p.dimension, 'bc:magic_circle_ground', V.add(mid, { x: 0, y: 0.1, z: 0 }), { size: 6, life: 2, color: rgb('ffd040') });
  title(p, '§6§lSPARRING MATCH', `§b${ma.name}§7 vs §b${mb.name}`, 50);
  sound(p.dimension, 'bc.horn', p.location, 0.8, 1.2);
  anim(a, 'animation.bc.magic_knight.salute');
  anim(b, 'animation.bc.magic_knight.salute');
  return true;
}

function endSpar(s, loserId) {
  spars.delete(s.a);
  const a = world.getEntity(s.a);
  const b = world.getEntity(s.b);
  const p = world.getEntity(s.owner);
  for (const x of [a, b]) {
    if (!x) continue;
    safe(() => x.setDynamicProperty('bc:spar', undefined));
    const h = x.getComponent('minecraft:health');
    if (h) safe(() => h.setCurrentValue(h.effectiveMax));
  }
  if (!(p instanceof Player)) return;
  const winner = loserId ? (loserId === s.a ? b : a) : undefined;
  const loser = loserId ? world.getEntity(loserId) : undefined;
  if (!winner || !loser) {
    safe(() => p.sendMessage('§6Sparring: §7a draw! Both of them learned something.'));
    for (const x of [a, b]) if (x) giveKnightXp(x, 25);
    return;
  }
  const mw = memberOf(winner);
  const ml = memberOf(loser);
  giveKnightXp(winner, 40);
  giveKnightXp(loser, 25);
  anim(winner, 'animation.bc.magic_knight.victory');
  anim(loser, 'animation.bc.magic_knight.kneel');
  if (mw) {
    bark(mw.m, p, 'spar_win', true);
    mw.m.morale = Math.min(100, mw.m.morale + 6);
    addBond(p, mw.m, 4);
  }
  if (ml) {
    system.runTimeout(() => bark(ml.m, p, 'spar_lose', true), 40);
    ml.m.morale = Math.max(0, ml.m.morale - 2);
    addBond(p, ml.m, 4);
  }
  title(p, '§6§lMATCH OVER', `§b${mw?.m.name ?? 'Winner'}§7 wins!`, 50);
  save(p);
}

async function sparMenu(p) {
  const here = party(p).m.filter((m) => m.active && entityOf(m));
  if (here.length < 2) {
    safe(() => p.sendMessage('§7You need two companions at your side to hold a sparring match.'));
    return;
  }
  const pickOne = async (heading, list) => {
    const f = new ActionFormData().title(heading);
    for (const m of list) f.button(`${DATA.attributes[m.attr].glyph} §l${m.name}§r §8Lv ${m.level}`);
    const r = await f.show(p);
    return r.canceled || r.selection === undefined ? undefined : list[r.selection];
  };
  const a = await pickOne('Sparring: first fighter', here);
  if (!a) return;
  const b = await pickOne('Sparring: their opponent', here.filter((m) => m !== a));
  if (b) startSpar(p, a, b);
}

addWhistleButtons((p, pt) => (pt.m.filter((m) => m.active).length >= 2 ? [{ label: '§lSparring match\n§r§8Two companions duel for practice', act: () => sparMenu(p) }] : []));

// ------------------------------------------------------------------------------- rival squads
/** @type {Map<string, {ids: string[], until: number, company: string, yielded: number}>} player id -> the rivals */
const matches = new Map();

function rivalOwner(e) {
  const v = safe(() => e.getDynamicProperty('bc:rival'));
  return typeof v === 'string' ? v : '';
}

/** A rival squad challenges `p`'s party. */
export function startRivalMatch(p, at) {
  const pt = party(p);
  const here = pt.m.filter((m) => m.active && entityOf(m));
  if (!here.length || matches.has(p.id)) return false;
  const avg = Math.round(here.reduce((s, m) => s + m.level, 0) / here.length);
  const n = Math.min(4, Math.max(2, here.length + (Math.random() < 0.4 ? 1 : 0)));
  const company = pick(COMPANIES);
  const ids = [];
  for (let i = 0; i < n; i++) {
    const loc = V.add(at, { x: rand(-3, 3), y: 0.5, z: rand(-3, 3) });
    const e = safe(() => p.dimension.spawnEntity('bc:magic_knight', loc));
    if (!e) continue;
    setupKnight(e, { level: Math.max(1, Math.min(20, avg + Math.round(rand(-1, 1)))), prefix: '§6', randomRobe: true });
    safe(() => {
      e.setDynamicProperty('bc:rival', p.id);
      e.setDynamicProperty('bc:kname', `${pick(DATA.knightFirst)} of the ${company}`);
    });
    nameKnight(e);
    ids.push(e.id);
  }
  if (!ids.length) return false;
  matches.set(p.id, { ids, until: system.currentTick + 20 * 150, company, yielded: 0 });
  title(p, '§6§lA RIVAL SQUAD', `§7The ${company} challenge your party`, 60);
  safe(() => p.sendMessage(`§6⚔ The §f${company}§6 squad challenges your party to a friendly match! §7Their spells only sting. Make them yield!`));
  sound(p.dimension, 'bc.horn', p.location, 1, 1);
  return true;
}

function finishMatch(p, won) {
  const mt = matches.get(p.id);
  if (!mt) return;
  matches.delete(p.id);
  for (const id of mt.ids) {
    const e = world.getEntity(id);
    if (!e) continue;
    anim(e, won ? 'animation.bc.magic_knight.salute' : 'animation.bc.magic_knight.cheer');
    system.runTimeout(() => safe(() => {
      if (!alive(e)) return;
      particle(e.dimension, 'bc:clover_leaves', center(e), { scale: 0.8 });
      e.remove();
    }), 40);
  }
  const pt = party(p);
  if (won) {
    const coins = 40 + mt.ids.length * 20;
    giveCoins(p, coins);
    for (const m of pt.m) {
      const e = entityOf(m);
      if (!e) continue;
      giveKnightXp(e, 80);
      m.morale = Math.min(100, m.morale + 15);
      addBond(p, m, 10);
      anim(e, 'animation.bc.magic_knight.victory');
    }
    title(p, '§6§lVICTORY', `§7The ${mt.company} yield! §6+${coins} doubloons`, 70);
    sound(p.dimension, 'bc.fanfare', p.location, 1, 1);
  } else {
    for (const m of pt.m) m.morale = Math.max(0, m.morale - 8);
    title(p, '§7§lTHE MATCH IS OVER', `§7The ${mt.company} bow and leave`, 60);
  }
  save(p);
}

function yieldRival(e, ownerId) {
  safe(() => e.setDynamicProperty('bc:rival', undefined));
  const h = e.getComponent('minecraft:health');
  if (h) safe(() => h.setCurrentValue(Math.max(h.currentValue, h.effectiveMax * 0.5)));
  anim(e, 'animation.bc.magic_knight.kneel');
  particle(e.dimension, 'bc:burst_spark', center(e), { color: rgb('ffd040'), scale: 0.8 });
  const p = world.getEntity(ownerId);
  if (p instanceof Player) safe(() => p.onScreenDisplay.setActionBar(`§6${safe(() => e.getDynamicProperty('bc:kname')) ?? 'A rival'}§7 yields!`));
  const mt = matches.get(ownerId);
  if (mt) mt.yielded += 1;
}

// ------------------------------------------------------------------------------- the rules of friendly fights
function sameSide(x, ownerId) {
  return x.id === ownerId || ownerOf(x) === ownerId;
}

addRelation((attacker, target) => {
  const sa = safe(() => attacker.getDynamicProperty('bc:spar'));
  if (typeof sa === 'string') return sa === target.id ? true : undefined;
  const ra = rivalOwner(attacker);
  if (ra && sameSide(target, ra)) return true;
  const rt = rivalOwner(target);
  if (rt && sameSide(attacker, rt)) return true;
  return undefined;
});

addFoes((e) => {
  const sp = safe(() => e.getDynamicProperty('bc:spar'));
  if (typeof sp === 'string') {
    const o = world.getEntity(sp);
    return o ? [o] : [];
  }
  const r = rivalOwner(e);
  if (r) {
    const p = world.getEntity(r);
    if (!(p instanceof Player)) return [];
    return [p, ...party(p).m.map((m) => entityOf(m)).filter(Boolean)];
  }
  const owner = ownerOf(e);
  const mt = owner ? matches.get(owner) : undefined;
  if (!mt) return [];
  return mt.ids.map((id) => world.getEntity(id)).filter((x) => x && rivalOwner(x));
});

/** Friendly fights never kill: a blow can take someone down to 1 health, no further. */
function friendly(target, amount) {
  const hp = safe(() => target.getComponent('minecraft:health')?.currentValue) ?? amount + 1;
  return Math.max(0, Math.min(amount, hp - 1));
}
addDamageMod((target, attacker, amount) => {
  if (!attacker) return amount;
  const sp = safe(() => attacker.getDynamicProperty('bc:spar'));
  if (typeof sp === 'string' && sp === target.id) return friendly(target, amount * 0.6);
  const ra = rivalOwner(attacker);
  const rt = rivalOwner(target);
  if ((ra && sameSide(target, ra)) || (rt && sameSide(attacker, rt))) return friendly(target, amount * 0.5);
  return amount;
});

// sparring partners only have eyes for each other
addInfo((e, p, m, info) => {
  const sp = safe(() => e.getDynamicProperty('bc:spar'));
  if (typeof sp === 'string') {
    info.focus = sp;
    info.passive = false;
  } else if (matches.has(p.id) && !info.focus) {
    const r = matches.get(p.id).ids.map((id) => world.getEntity(id)).find((x) => x && rivalOwner(x));
    if (r) info.focus = r.id;
  }
});

world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const e = ev.hurtEntity;
  const h = e.getComponent('minecraft:health');
  if (!h) return;
  const frac = h.currentValue / Math.max(1, h.effectiveMax);
  const s = sparOf(e);
  if (s && frac < 0.35) return endSpar(s, e.id);
  const r = rivalOwner(e);
  if (r && frac < 0.3) return yieldRival(e, r);
  return undefined;
}, 'friendlyFights'));

system.runInterval(() => {
  const t = system.currentTick;
  for (const s of [...spars.values()]) {
    const a = world.getEntity(s.a);
    const b = world.getEntity(s.b);
    if (!a || !b || !alive(a) || !alive(b)) {
      spars.delete(s.a);
      for (const x of [a, b]) if (x) safe(() => x.setDynamicProperty('bc:spar', undefined));
    } else if (s.until < t) endSpar(s, '');
  }
  for (const [pid, mt] of [...matches]) {
    const p = world.getEntity(pid);
    if (!(p instanceof Player)) {
      matches.delete(pid);
      continue;
    }
    const standing = mt.ids.map((id) => world.getEntity(id)).filter((x) => x && alive(x) && rivalOwner(x));
    // a companion knocked down below a fifth of its health is out of the match
    const mine = party(p).m.filter((m) => {
      const e = m.active ? entityOf(m) : undefined;
      const h = e ? safe(() => e.getComponent('minecraft:health')) : undefined;
      return !!h && h.currentValue / Math.max(1, h.effectiveMax) >= 0.2;
    });
    if (!standing.length) finishMatch(p, true);
    else if (!mine.length || mt.until < t) finishMatch(p, false);
  }
}, 20);

