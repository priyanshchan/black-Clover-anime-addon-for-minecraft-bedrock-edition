// Companions: your party of Magic Knights (up to 4 at your side, 6 more in reserve at a Squad Banner).
//
// * The party is saved with you: companions keep their name, magic, level (up to 20), robe, bond, personality,
//   specialisation, mood and trials across sessions, come back 60 seconds after they fall (or sooner, if someone
//   revives them), and can be dismissed and summoned again with the Companion Whistle.
// * They fight with the tactical brain (ai.js) plus what this module tells it: your focus target ("attack what I'm
//   looking at"), whoever is hurting you, whether you are in danger (healers prioritise you), their stance and robe perks.
// * Out of combat they walk in formation, keep out of your line of fire, gather loot, sit down when you rest, and talk.
// * Bond grows with time together, victories and gifts, and unlocks Mana Link, Guardian and Union Magic.
// * This module is the core (saving, spawning, the whistle). squad.js (fighting as a squad), camp.js (mood, camp,
//   talk, trials), roster.js (reserve, expeditions, training) and rivals.js (sparring, rival squads) plug in through
//   the hooks below.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { ActionFormData, MessageFormData, ModalFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { addMana, maxMana, state } from '../core/data.js';
import { aimEntity, canHit, center, effect, foesOf, ownerOf } from '../core/combat.js';
import { anim, particle, rgb, sound, title } from '../core/fx.js';
import { heldKind } from '../core/hud.js';
import { V, alive, isCreative, pick, rand, safe } from '../core/util.js';
import { setCompanionProvider } from './ai.js';
import { castSpec, colorOf, heal } from './engine.js';
import { RANK, kitFor, knightAttr, knightLevel, nameKnight, onKnightLevel, setCompanionHooks, setupKnight } from './knights.js';

const C = DATA.companion;
const RESPAWN_MS = 60000;
const GIFTS = { 'bc:mana_cookie': 40, 'bc:mana_crystal': 15, 'minecraft:cake': 30, 'minecraft:cooked_beef': 8, 'minecraft:cooked_porkchop': 8,
  'minecraft:cooked_chicken': 6, 'minecraft:bread': 5, 'minecraft:cookie': 5, 'minecraft:golden_apple': 25, 'bc:hearty_roast': 20 };
const FORMATIONS = ['wedge', 'line', 'circle'];
const STANCES = ['aggressive', 'defensive', 'passive'];
const ROBE_PERK = {
  black_bull_robe: (e, m, hp) => ({ pw: hp < 0.4 ? 1.25 : 1 }),
  golden_dawn_robe: () => ({ pw: 1.1 }),
  crimson_lion_robe: (e, m) => ({ pw: ['flame', 'magma'].includes(m.attr) ? 1.2 : 1.05 }),
  silver_eagle_robe: (e, m, hp) => ({ pw: hp > 0.75 ? 1.2 : 1 }),
  blue_rose_robe: () => ({ pw: 1.15 }),
  green_mantis_robe: () => ({ cd: 0.8 }),
  coral_peacock_robe: () => ({ cd: 0.9, pw: 1.05 }),
  purple_orca_robe: (e, m) => ({ pw: ['water', 'ice', 'bubble'].includes(m.attr) ? 1.2 : 1 }),
  aqua_deer_robe: () => ({ pw: 1.05 }),
};

/**
 * @typedef {{cid: string, name: string, attr: string, robe: number, gear: string, level: number, xp: number, kills: number, skill: number,
 *            courage: number, bond: number, active: boolean, fallenAt: number, eid: string, personality: string, spec: string,
 *            mastery: boolean, awakened: boolean, morale: number, fatigue: number, amulet: string, trial: any, trialStage: number,
 *            title: string, fallenLoc: any, talkDay: number, home: string, dream: string, xpDay: number, xpToday: number, away: string,
 *            specNoted?: boolean, fruit: string}} Member
 * @typedef {{formation: string, stance: string, loot: boolean, unionAt: number, tactic: string, train: boolean, trainAt?: number}} Cfg
 * @typedef {{m: Member[], r: Member[], ex: any[], cfg: Cfg}} Party
 */
/** @type {Map<string, Party>} */
const parties = new Map();
/** @type {Map<string, {id: string, until: number}>} */
const orderFocus = new Map();
/** @type {Map<string, {id: string, until: number}>} */
const ownerTarget = new Map();
/** @type {Map<string, {id: string, until: number}>} */
const ownerThreat = new Map();
/** @type {Map<string, {loc: any, at: number, joined: number}>} */
const presence = new Map();
/** @type {Map<string, number>} cid -> next tick a chatty line is allowed */
const barkCd = new Map();
const perkCd = new Map();
const bossesSeen = new Set();

// ------------------------------------------------------------------------------- hooks for the other companion modules
/** @type {((p: any, pt: Party, active: Member[], t: number, fighting: boolean) => void)[]} */
const partyHooks = [];
/** @type {((p: any, m: Member, e: any, i: number, pt: Party, t: number, fighting: boolean) => void)[]} */
const memberHooks = [];
/** @type {((p: any, pt: Party) => {label: string, act: () => any}[])[]} */
const whistleHooks = [];
/** @type {((p: any, m: Member) => {label: string, act: () => any}[])[]} */
const memberMenuHooks = [];
/** @type {((e: any, p: any, m: Member, info: any) => void)[]} */
const infoHooks = [];
/** @type {((p: any, e: any, m: Member, id: string) => boolean | Promise<boolean>)[]} */
const talkHooks = [];
/** @type {((p: any, m: Member) => void)[]} */
const fallHooks = [];
/** @type {((m: Member) => string[])[]} */
const profileHooks = [];
export const onPartyTick = (fn) => partyHooks.push(fn);
export const onMemberTick = (fn) => memberHooks.push(fn);
export const addWhistleButtons = (fn) => whistleHooks.push(fn);
export const addMemberButtons = (fn) => memberMenuHooks.push(fn);
export const addInfo = (fn) => infoHooks.push(fn);
export const addTalkHandler = (fn) => talkHooks.push(fn);
export const onMemberFall = (fn) => fallHooks.push(fn);
export const addProfileLines = (fn) => profileHooks.push(fn);

// ------------------------------------------------------------------------------- the saved party
function hash(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) h = Math.imul(h ^ str.charCodeAt(i), 16777619);
  return h >>> 0;
}
const PERSONALITY_IDS = Object.keys(C.personalities);
/** Fill in fields added by newer versions (companions recruited in v0.2/v0.3 get a personality, a hometown and a dream). */
export function ensure(m) {
  const h = hash(m.cid);
  m.personality = C.personalities[m.personality] ? m.personality : PERSONALITY_IDS[h % PERSONALITY_IDS.length];
  m.spec = C.specs[m.spec] ? m.spec : '';
  m.mastery = !!m.mastery;
  m.awakened = !!m.awakened;
  m.morale = typeof m.morale === 'number' ? m.morale : C.mood.start_morale;
  m.fatigue = typeof m.fatigue === 'number' ? m.fatigue : 0;
  m.amulet = typeof m.amulet === 'string' ? m.amulet : '';
  m.trialStage = typeof m.trialStage === 'number' ? m.trialStage : 0;
  m.trial = m.trial ?? null;
  m.title = typeof m.title === 'string' ? m.title : '';
  m.talkDay = typeof m.talkDay === 'number' ? m.talkDay : -1;
  m.home = m.home || C.hometowns[(h >>> 3) % C.hometowns.length];
  m.dream = m.dream || C.dreams[(h >>> 7) % C.dreams.length];
  m.xpDay = typeof m.xpDay === 'number' ? m.xpDay : -1;
  m.xpToday = typeof m.xpToday === 'number' ? m.xpToday : 0;
  m.away = typeof m.away === 'string' ? m.away : '';
  // v0.6.0: every companion fights with a grimoire and an Abyss Fruit
  if (!DATA.fruits[m.fruit]) m.fruit = DATA.fruitOrder[(h >>> 11) % DATA.fruitOrder.length];
  return m;
}
export function party(p) {
  let pt = parties.get(p.id);
  if (pt) return pt;
  const raw = safe(() => p.getDynamicProperty('bc:party'));
  try {
    pt = typeof raw === 'string' ? JSON.parse(raw) : undefined;
  } catch {
    pt = undefined;
  }
  pt = pt ?? /** @type {Party} */ (/** @type {any} */ ({ m: [], r: [], ex: [], cfg: {} }));
  pt.m = Array.isArray(pt.m) ? pt.m : [];
  pt.r = Array.isArray(pt.r) ? pt.r : [];
  pt.ex = Array.isArray(pt.ex) ? pt.ex : [];
  pt.cfg = { formation: 'wedge', stance: 'aggressive', loot: true, unionAt: 0, tactic: 'balanced', train: false, ...pt.cfg };
  if (!C.tactics[pt.cfg.tactic]) pt.cfg.tactic = 'balanced';
  for (const m of [...pt.m, ...pt.r]) ensure(m);
  while (pt.m.length > C.partyMax) {
    const extra = pt.m.pop();
    extra.active = false;
    pt.r.push(extra);
  }
  parties.set(p.id, pt);
  return pt;
}
export function save(p) {
  safe(() => p.setDynamicProperty('bc:party', JSON.stringify(party(p))));
}
export function partySize(p) {
  return party(p).m.length;
}
/** Everyone you lead, the reserve included. */
export function rosterSize(p) {
  return party(p).m.length + party(p).r.length;
}
export function bondRank(bond) {
  let r = 0;
  C.bond.forEach((b, i) => {
    if (bond >= b.at) r = i;
  });
  return r;
}
function hpTier(level) {
  let tier = 1;
  C.hp.forEach(([from], i) => {
    if (level >= from) tier = i + 1;
  });
  return tier;
}
export function memberOf(e) {
  const cid = safe(() => e.getDynamicProperty('bc:cid'));
  const owner = world.getEntity(ownerOf(e));
  if (typeof cid !== 'string' || !(owner instanceof Player)) return undefined;
  const m = party(owner).m.find((x) => x.cid === cid);
  return m ? { p: owner, m } : undefined;
}
export function hpFrac(e) {
  const h = safe(() => e.getComponent('minecraft:health'));
  return h ? h.currentValue / Math.max(1, h.effectiveMax) : 1;
}

// ------------------------------------------------------------------------------- talking
export function bark(m, p, kind, force = false) {
  const t = system.currentTick;
  if (!force && (barkCd.get(m.cid) ?? 0) > t) return;
  const chatty = m.personality === 'cheerful' ? 0.6 : m.personality === 'cautious' ? 1.3 : 1;
  barkCd.set(m.cid, t + Math.round((400 + rand(0, 400)) * chatty));
  const own = C.personalities[m.personality]?.lines?.[kind];
  const lines = own && Math.random() < 0.6 ? own : C.lines[kind];
  if (!lines) return;
  safe(() => p.sendMessage(`§b${m.name}§f: ${pick(lines).replace(/\{p\}/g, p.name)}`));
}
export { bark as say };

// ------------------------------------------------------------------------------- entity <-> member
function applyTo(e, m, p) {
  safe(() => {
    e.setDynamicProperty('bc:cid', m.cid);
    e.setDynamicProperty('bc:attr', m.attr);
    e.setDynamicProperty('bc:kname', m.name);
    e.setDynamicProperty('bc:klv', m.level);
    e.setDynamicProperty('bc:kxp', m.xp);
    e.setDynamicProperty('bc:kills', m.kills);
    e.setDynamicProperty('bc:skill', m.skill);
    e.setDynamicProperty('bc:courage', m.courage);
    e.setDynamicProperty('bc:owner', p.id);
    e.setDynamicProperty('bc:prefix', '§b');
    e.setDynamicProperty('bc:awake', !!m.awakened);
    e.setDynamicProperty('bc:fruit', m.fruit);
    if (typeof e.getDynamicProperty('bc:order') !== 'string') e.setDynamicProperty('bc:order', 'follow');
    e.setProperty('bc:robe', m.robe);
    e.getComponent('minecraft:tameable')?.tame(p);
    e.triggerEvent(`bc:hp_${hpTier(m.level)}`);
    const st = party(p).cfg.stance;
    e.setDynamicProperty('bc:stance', st === 'defensive' ? 'defensive' : 'aggressive');
    e.triggerEvent(st === 'passive' ? 'bc:passive_on' : 'bc:passive_off');
  }, 'applyTo');
  nameKnight(e);
}

function readFrom(e, m) {
  const lv = knightLevel(e);
  const xp = safe(() => e.getDynamicProperty('bc:kxp'));
  const kills = safe(() => e.getDynamicProperty('bc:kills'));
  let changed = lv !== m.level;
  m.level = lv;
  if (typeof xp === 'number' && xp !== m.xp) {
    m.xp = xp;
    changed = true;
  }
  if (typeof kills === 'number' && kills !== m.kills) {
    m.kills = kills;
    changed = true;
  }
  return changed;
}

function slotFor(p, index, formation) {
  const f = V.flat(p.getViewDirection());
  const r = { x: -f.z, y: 0, z: f.x };
  let off;
  if (formation === 'line') off = V.add(V.mul(r, (index % 2 ? 1 : -1) * (2 + Math.floor(index / 2) * 2)), V.mul(f, -0.5));
  else if (formation === 'circle') off = V.yaw({ x: 3, y: 0, z: 0 }, 45 + index * 90);
  else off = V.add(V.mul(r, (index % 2 ? 1 : -1) * (1.5 + Math.floor(index / 2) * 1.5)), V.mul(f, -2 - Math.floor(index / 2) * 1.5));
  return V.add(p.location, off);
}

/**
 * Bring a member into the world beside you (or at `opts.at`, with `opts.hp` of its health when revived).
 * @param {{at?: any, hp?: number, quiet?: boolean}} [opts]
 */
export function spawnMember(p, m, returning, opts = {}) {
  const idx = party(p).m.filter((x) => x.active).indexOf(m);
  const loc = opts.at ? { ...opts.at } : slotFor(p, Math.max(0, idx), party(p).cfg.formation);
  if (!opts.at) loc.y = p.location.y + 0.2;
  const e = safe(() => p.dimension.spawnEntity('bc:magic_knight', loc, { spawnEvent: 'bc:hire' }));
  if (!e) return undefined;
  applyTo(e, m, p);
  m.eid = e.id;
  m.fallenAt = 0;
  particle(p.dimension, 'bc:magic_circle_ground', V.add(loc, { x: 0, y: 0.1, z: 0 }), { color: colorOf(`a:${m.attr}`), size: 2.2, life: 1.2 });
  particle(p.dimension, 'bc:pillar', loc, { color: colorOf(`a:${m.attr}`), scale: 0.8 });
  sound(p.dimension, 'bc.portal', loc, 0.7, 1.4);
  system.runTimeout(() => alive(e) && anim(e, 'animation.bc.magic_knight.salute'), 10);
  if (opts.hp !== undefined) {
    system.runTimeout(() => safe(() => {
      const h = e.getComponent('minecraft:health');
      if (h) h.setCurrentValue(Math.max(1, h.effectiveMax * opts.hp));
    }), 2);
  }
  if (!opts.quiet) bark(m, p, returning ? 'return' : 'summon', true);
  save(p);
  return e;
}

export function entityOf(m) {
  if (!m.eid) return undefined;
  const e = world.getEntity(m.eid);
  return e && alive(e) ? e : undefined;
}

/** A knight just joined you (Knight Contract, recruiting, a rescue): add it to the saved party. */
function adopt(e, p) {
  if (typeof safe(() => e.getDynamicProperty('bc:cid')) === 'string') return;
  const pt = party(p);
  const bond0 = safe(() => e.getDynamicProperty('bc:bond0'));
  /** @type {any} */
  const m = {
    cid: `${Date.now().toString(36)}${Math.floor(Math.random() * 1e6).toString(36)}`,
    name: /** @type {string} */ (safe(() => e.getDynamicProperty('bc:kname')) ?? 'Knight'),
    attr: knightAttr(e), robe: /** @type {number} */ (safe(() => e.getProperty('bc:robe')) ?? 0), gear: '',
    level: knightLevel(e), xp: /** @type {number} */ (safe(() => e.getDynamicProperty('bc:kxp')) ?? 0),
    kills: /** @type {number} */ (safe(() => e.getDynamicProperty('bc:kills')) ?? 0),
    skill: /** @type {number} */ (safe(() => e.getDynamicProperty('bc:skill')) ?? rand(0.45, 0.95)),
    courage: /** @type {number} */ (safe(() => e.getDynamicProperty('bc:courage')) ?? rand(0.3, 1)),
    bond: typeof bond0 === 'number' ? bond0 : 0, active: true, fallenAt: 0, eid: e.id,
  };
  ensure(m);
  if (pt.m.length >= C.partyMax) {
    // the party is full: the new knight waits at your Squad Banner
    m.active = false;
    m.eid = '';
    pt.r.push(m);
    save(p);
    particle(e.dimension, 'bc:clover_leaves', center(e), { scale: 0.8 });
    safe(() => e.remove());
    safe(() => p.sendMessage(`§b${m.name}§7 (${C.personalities[m.personality].name}) joins your §2reserve§7 - ${pt.r.length}/${C.reserveMax}. Swap them in at a §2Squad Banner§7.`));
    return;
  }
  pt.m.push(m);
  applyTo(e, m, p);
  save(p);
  bark(m, p, 'join', true);
  safe(() => p.sendMessage(`§7(${m.name} joined your party - ${pt.m.length}/${C.partyMax}. ${C.personalities[m.personality].name}: ${C.personalities[m.personality].desc} Use a §bCompanion Whistle§7 to command your party.)`));
}

export function addBond(p, m, n, why) {
  const before = bondRank(m.bond);
  m.bond = Math.min(99999, m.bond + n);
  const after = bondRank(m.bond);
  if (after > before) {
    const b = C.bond[after];
    title(p, `§b${m.name}`, `§dBond: ${b.name}`, 50);
    safe(() => p.sendMessage(`§d♥ ${m.name} is now your ${b.name}! §7${b.perk}`));
    sound(p.dimension, 'bc.chord', p.location, 0.8, 1.2);
    const e = entityOf(m);
    if (e) {
      anim(e, 'animation.bc.magic_knight.cheer');
      particle(e.dimension, 'bc:heal', center(e), { scale: 1.2 });
    }
  }
  if (why) save(p);
}

// ------------------------------------------------------------------------------- what the brain needs to know
setCompanionProvider((e) => {
  const mo = memberOf(e);
  if (!mo) return undefined;
  const { p, m } = mo;
  const cfg = party(p).cfg;
  const t = system.currentTick;
  const pick_ = (map) => {
    const v = map.get(p.id);
    return v && v.until > t && world.getEntity(v.id) ? v.id : undefined;
  };
  const focus = pick_(orderFocus) ?? pick_(ownerThreat) ?? (cfg.stance === 'aggressive' ? pick_(ownerTarget) : undefined);
  const hp = hpFrac(e);
  const perk = m.gear ? ROBE_PERK[m.gear.slice(3)]?.(e, m, hp) ?? {} : {};
  const info = {
    focus,
    passive: cfg.stance === 'passive',
    ownerLow: hpFrac(p) < 0.4,
    pwMul: (bondRank(m.bond) >= 1 ? 1.1 : 1) * (perk.pw ?? 1) * (1 + Math.max(0, m.level - 10) * 0.03),
    cdMul: perk.cd ?? 1,
  };
  for (const fn of infoHooks) safe(() => fn(e, p, m, info), 'companionInfo');
  return info;
});

setCompanionHooks({ onEnlist: adopt, partySize: rosterSize, talk: companionTalk });

onKnightLevel((e) => {
  const mo = memberOf(e);
  if (!mo) return;
  mo.m.level = knightLevel(e);
  safe(() => e.triggerEvent(`bc:hp_${hpTier(mo.m.level)}`));
  anim(e, 'animation.bc.magic_knight.cheer');
  bark(mo.m, mo.p, 'level', true);
  addBond(mo.p, mo.m, 10, 'level');
});

// ------------------------------------------------------------------------------- events
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const dead = ev.deadEntity;
  const k = ev.damageSource.damagingEntity;
  if (dead.typeId === 'bc:magic_knight') {
    const cid = safe(() => dead.getDynamicProperty('bc:cid'));
    const owner = world.getEntity(/** @type {string} */ (safe(() => dead.getDynamicProperty('bc:owner')) ?? ''));
    if (typeof cid === 'string' && owner instanceof Player) {
      const m = party(owner).m.find((x) => x.cid === cid);
      if (m) {
        readFrom(dead, m);
        m.eid = '';
        m.fallenAt = Date.now();
        m.fallenLoc = { x: dead.location.x, y: dead.location.y, z: dead.location.z, dim: dead.dimension.id };
        save(owner);
        safe(() => owner.sendMessage(`§c✝ §b${m.name}§c has fallen! §7They rejoin you in 60 seconds - or stand by their glowing clover to revive them sooner.`));
        sound(owner.dimension, 'bc.mana.empty', owner.location, 1, 0.6);
        for (const fn of fallHooks) safe(() => fn(owner, m), 'companionFall');
      }
    }
  }
  // victories build bonds
  if (k instanceof Player) {
    for (const m of party(k).m) if (m.active && entityOf(m) && V.dist(entityOf(m).location, k.location) < 16) addBond(k, m, 1);
  } else if (k && k.typeId === 'bc:magic_knight') {
    const mo = memberOf(k);
    if (mo) {
      addBond(mo.p, mo.m, 2);
      if (Math.random() < 0.15) bark(mo.m, mo.p, 'kill');
    }
  }
}, 'companionDie'));

world.afterEvents.entityHurt.subscribe((ev) => {
  const src = ev.damageSource.damagingEntity;
  const hurt = ev.hurtEntity;
  const t = system.currentTick;
  if (src instanceof Player && !(hurt instanceof Player) && parties.has(src.id) && ownerOf(hurt) !== src.id) {
    ownerTarget.set(src.id, { id: hurt.id, until: t + 200 });
  } else if (hurt instanceof Player && src && !(src instanceof Player) && parties.has(hurt.id) && ownerOf(src) !== hurt.id) {
    ownerThreat.set(hurt.id, { id: src.id, until: t + 120 });
  }
});

/** Keep the one true copy of each companion when chunks load. */
world.afterEvents.entityLoad.subscribe((ev) => safe(() => {
  const e = ev.entity;
  if (e.typeId !== 'bc:magic_knight') return;
  const mo = memberOf(e);
  if (mo) {
    const other = entityOf(mo.m);
    if (!mo.m.active || (other && other.id !== e.id)) {
      e.remove();
      return;
    }
    mo.m.eid = e.id;
    return;
  }
  // knights hired before companions existed join the party
  const owner = world.getEntity(ownerOf(e));
  if (owner instanceof Player && typeof safe(() => e.getDynamicProperty('bc:cid')) !== 'string' && partySize(owner) < C.partyMax) adopt(e, owner);
}, 'companionLoad'));

world.afterEvents.playerSpawn.subscribe((ev) => {
  presence.set(ev.player.id, { loc: { ...ev.player.location }, at: system.currentTick, joined: system.currentTick });
});

world.afterEvents.itemCompleteUse.subscribe((ev) => safe(() => {
  if (ev.itemStack.typeId !== 'bc:mana_cookie') return;
  const p = ev.source;
  addMana(p, 30);
  particle(p.dimension, 'bc:burst', center(p), { color: rgb('78c8ff'), scale: 0.6 });
  safe(() => p.onScreenDisplay.setActionBar('§b+30 mana'));
}, 'cookie'));

// ------------------------------------------------------------------------------- the party loop
function inCombat(p) {
  return (safe(() => foesOf(p, 12).length) ?? 0) > 0;
}

function careFor(p, m, e, i, cfg, t, fighting) {
  const dist = V.dist(e.location, p.location);
  if (e.dimension.id !== p.dimension.id || dist > 48) {
    safe(() => e.teleport(slotFor(p, i, cfg.formation), { dimension: p.dimension }));
    return;
  }
  const order = safe(() => e.getDynamicProperty('bc:order'));
  // formation when nothing is happening
  if (!fighting && order !== 'hold') {
    const slot = slotFor(p, i, cfg.formation);
    const d = V.dist(e.location, slot);
    if (d > 2.5 && d < 14) {
      const dir = V.flat(V.sub(slot, e.location));
      safe(() => e.applyImpulse({ x: dir.x * 0.16, y: 0, z: dir.z * 0.16 }));
    }
  }
  // stay out of the line of fire
  if (heldKind(p)) {
    const head = p.getHeadLocation();
    const dir = p.getViewDirection();
    const to = V.sub(center(e), head);
    const along = V.dot(to, dir);
    if (along > 1 && along < 14) {
      const off = V.sub(to, V.mul(dir, along));
      if (V.len(off) < 1.3) {
        const side = V.len(off) > 0.05 ? V.flat(off) : V.flat({ x: -dir.z, y: 0, z: dir.x });
        safe(() => e.applyImpulse({ x: side.x * 0.45, y: 0.05, z: side.z * 0.45 }));
      }
    }
  }
  const rank = bondRank(m.bond);
  const key = `${m.cid}`;
  const cd = perkCd.get(key) ?? { mana: 0, guard: 0 };
  perkCd.set(key, cd);
  // Friend: Mana Link
  if (rank >= 2 && t > cd.mana) {
    const s = state(p);
    if (s.attr && s.attr !== 'anti' && s.mana < maxMana(p, s) * 0.2) {
      addMana(p, 30 + m.level * 2);
      cd.mana = t + 1200;
      line(e, p, colorOf(`a:${m.attr}`));
      safe(() => p.onScreenDisplay.setActionBar(`§b${m.name}§7 shares their mana with you (+${30 + m.level * 2})`));
    }
  }
  // Sworn Ally: Guardian
  const php = hpFrac(p);
  if (php < 0.3) bark(m, p, 'low');
  if (rank >= 3 && t > cd.guard && php < 0.25) {
    effect(p, 'resistance', 6, 1, false);
    effect(p, 'absorption', 10, 1, false);
    heal(p, 4);
    cd.guard = t + 1800;
    line(e, p, rgb('ffe080'));
    particle(p.dimension, 'bc:shockwave', p.location, { color: rgb('ffe080'), radius: 2 });
    anim(e, 'animation.bc.magic_knight.cast_raise');
    safe(() => p.onScreenDisplay.setActionBar(`§e${m.name}§7 shields you!`));
  }
  // robe perks that are effects
  if (m.gear === 'bc:aqua_deer_robe' && !fighting) effect(e, 'speed', 1, 0, false);
  if (m.gear === 'bc:purple_orca_robe') effect(e, 'water_breathing', 1, 0, false);
  if (m.gear === 'bc:black_bull_robe' && hpFrac(e) < 0.4) effect(e, 'strength', 1, 0, false);
}

function line(a, b, color) {
  const p0 = center(a);
  const p1 = center(b);
  const d = V.dist(p0, p1);
  for (let s = 0; s <= d; s += 0.6) particle(a.dimension, 'bc:beam_dot', V.lerp(p0, p1, s / Math.max(0.1, d)), { color, size: 0.35, life: 0.5 });
}

function partyLoop() {
  const t = system.currentTick;
  for (const p of world.getAllPlayers()) {
    const pt = party(p);
    if (!pt.m.length) continue;
    let pres = presence.get(p.id);
    if (!pres) presence.set(p.id, (pres = { loc: { ...p.location }, at: t, joined: t }));
    if (V.dist(pres.loc, p.location) > 0.3) {
      pres.loc = { ...p.location };
      pres.at = t;
    }
    const fighting = inCombat(p);
    const active = pt.m.filter((m) => m.active);
    active.forEach((m, i) => safe(() => {
      const e = entityOf(m);
      if (!e) {
        if (t - pres.joined < 100) return; // let chunks load first
        if (m.fallenAt && Date.now() - m.fallenAt < RESPAWN_MS) return;
        const found = p.dimension.getEntities({ type: 'bc:magic_knight', location: p.location, maxDistance: 128 })
          .find((x) => x.getDynamicProperty('bc:cid') === m.cid);
        if (found) m.eid = found.id;
        else spawnMember(p, m, !!m.fallenAt);
        return;
      }
      careFor(p, m, e, i, pt.cfg, t, fighting);
      for (const fn of memberHooks) safe(() => fn(p, m, e, i, pt, t, fighting), 'memberTick');
      // a rest: companions sit down when you stand still for a while
      if (!fighting && t - pres.at > 600 && t % 200 === 0) safe(() => e.playAnimation('animation.bc.magic_knight.sit', { stopExpression: 'q.modified_move_speed > 0.02' }));
      if (!fighting && t % 2400 === 0 && Math.random() < 0.25) bark(m, p, 'idle');
    }, 'companion'));
    // loot gathering after a fight
    if (pt.cfg.loot && !fighting && t % 40 === 0) {
      for (const m of active) {
        const e = entityOf(m);
        if (!e) continue;
        const items = safe(() => e.dimension.getEntities({ type: 'minecraft:item', location: e.location, maxDistance: 10 })
          .filter((x) => V.dist(x.location, p.location) > 3)) ?? [];
        if (!items.length) continue;
        for (const it of items) safe(() => it.teleport(V.add(p.location, { x: 0, y: 0.5, z: 0 })));
        if (Math.random() < 0.2) bark(m, p, 'loot');
      }
    }
    // a big foe appears
    for (const b of safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 32, families: ['boss'] })) ?? []) {
      if (bossesSeen.has(b.id)) continue;
      bossesSeen.add(b.id);
      const m = active.find((x) => entityOf(x));
      if (m) bark(m, p, 'boss', true);
    }
    for (const fn of partyHooks) safe(() => fn(p, pt, active, t, fighting), 'partyTick');
    if (t % 20 === 0 && heldId(p) === 'bc:companion_whistle') safe(() => p.onScreenDisplay.setActionBar(partyHud(pt)));
    // time together
    if (t % 1200 === 0) {
      for (const m of active) {
        const e = entityOf(m);
        if (e && V.dist(e.location, p.location) < 16) addBond(p, m, 1);
      }
      save(p);
    }
    if (t % 100 === 0) {
      let changed = false;
      for (const m of active) {
        const e = entityOf(m);
        if (e && readFrom(e, m)) changed = true;
      }
      if (changed) save(p);
    }
  }
}
// run on ticks that are multiples of 10, so the "every N ticks" checks in here and in the hooks line up
system.runTimeout(() => system.runInterval(partyLoop, 10), 10 - (system.currentTick % 10));

function heldId(p) {
  return safe(() => p.getComponent('minecraft:inventory')?.container?.getItem(p.selectedSlotIndex)?.typeId) ?? '';
}

/** A compact party frame for the actionbar while you hold the whistle. */
export function partyHud(pt) {
  const parts = [];
  for (const m of pt.m.filter((x) => x.active)) {
    const e = entityOf(m);
    if (!e) {
      const left = m.fallenAt ? Math.max(0, Math.ceil((RESPAWN_MS - (Date.now() - m.fallenAt)) / 1000)) : 0;
      parts.push(`§8${m.name.split(' ')[0]} ${m.fallenAt ? `§c✝${left}s` : '§7...'}`);
      continue;
    }
    const f = hpFrac(e);
    const n = Math.max(0, Math.min(5, Math.round(f * 5)));
    const col = f > 0.6 ? '§a' : f > 0.3 ? '§e' : '§c';
    const mood = m.fatigue >= C.mood.exhausted ? '§8z' : m.morale >= C.mood.inspired ? '§d+' : m.morale <= C.mood.shaken ? '§9-' : '';
    parts.push(`§b${m.name.split(' ')[0]} ${col}${'|'.repeat(n)}§8${'|'.repeat(5 - n)}${mood}`);
  }
  return `${parts.join(' §7· ')}  §8[${C.tactics[pt.cfg.tactic].name}]`;
}

// ------------------------------------------------------------------------------- the whistle
export function statusOf(m) {
  if (!m.active) return '§8resting';
  if (m.fallenAt && !entityOf(m)) return `§creturning in ${Math.max(0, Math.ceil((RESPAWN_MS - (Date.now() - m.fallenAt)) / 1000))}s`;
  const e = entityOf(m);
  if (!e) return '§7on the way';
  const h = safe(() => e.getComponent('minecraft:health'));
  return h ? `§a${Math.ceil(h.currentValue)}/${h.effectiveMax} HP` : '§a';
}

function fruitLine(m) {
  const f = DATA.fruits[m.fruit];
  if (!f) return '§7Fruit: §8none';
  const open = m.level >= C.fruitLevel || m.awakened;
  const moves = f.abilities.map((ab) => (ab.will && !open ? `§8${ab.name} (Lv ${C.fruitLevel})` : `§f${ab.name}`)).join('§7, ');
  return `§7Fruit: ${f.glyph} ${f.mc}${f.name}§7 - ${moves}`;
}

export function profile(m) {
  const a = DATA.attributes[m.attr];
  const b = C.bond[bondRank(m.bond)];
  const next = C.bond[bondRank(m.bond) + 1];
  const spells = kitFor(m.attr, m.level).length;
  const pers = C.personalities[m.personality];
  const spec = C.specs[m.spec];
  const lines = [
    `${a.glyph} ${a.mc}§l${m.name}${m.title ? ` ${m.title}` : ''}§r - ${RANK[m.level] ?? ''} Magic Knight, level §e${m.level}§r`,
    `§7Magic: ${a.mc}${a.name}§7 (${spells} spell${spells > 1 ? 's' : ''}${m.awakened ? ', §dawakened§7' : ''})   Kills: §f${m.kills}`,
    fruitLine(m),
    `§7Personality: §f${pers.name}§7 - ${pers.desc}`,
    `§7Specialisation: ${spec ? `§6${spec.name}${m.mastery ? ' §e(Mastery)' : ''}§7 - ${spec.desc}` : m.level >= C.specLevel ? '§ehas not chosen one yet - choose it below!' : `§8chosen at level ${C.specLevel}`}`,
    `§7Bond: §d${b.name}§7 (${m.bond}${next ? `/${next.at}` : ''}) - ${b.perk}`,
    `§7Robe: §f${m.gear ? DATA.robes[m.gear.slice(3)] : 'their own'}${m.gear ? `§7 - ${DATA.robePerks[m.gear.slice(3)]}` : ''}`,
    `§7Status: ${statusOf(m)}`,
    ...profileHooks.flatMap((fn) => safe(() => fn(m)) ?? []),
    '',
    '§8Gifts (hold them and talk): Mana Cookies, mana crystals, cooked food. Hand them a squad robe to dress them.',
  ];
  return lines.join('\n');
}

export async function memberMenu(p, m) {
  const form = new ActionFormData().title(m.name).body(profile(m));
  const acts = [];
  if (m.active) {
    form.button('§lDismiss\n§r§8They rest until you call them');
    acts.push(() => {
      const e = entityOf(m);
      if (e) {
        particle(e.dimension, 'bc:clover_leaves', center(e), { scale: 0.8 });
        safe(() => e.remove());
      }
      m.active = false;
      m.eid = '';
      save(p);
    });
    form.button('§lHold this position');
    acts.push(() => {
      const e = entityOf(m);
      if (!e) return;
      e.setDynamicProperty('bc:order', 'hold');
      e.setDynamicProperty('bc:anchor', JSON.stringify({ x: e.location.x, y: e.location.y, z: e.location.z }));
      e.triggerEvent('bc:order_hold');
    });
    form.button('§lFollow me');
    acts.push(() => {
      const e = entityOf(m);
      if (!e) return;
      e.setDynamicProperty('bc:order', 'follow');
      e.triggerEvent('bc:order_follow');
    });
  } else {
    form.button('§lSummon\n§r§8Call them to your side');
    acts.push(() => {
      m.active = true;
      m.fallenAt = 0;
      spawnMember(p, m, false);
    });
  }
  for (const fn of memberMenuHooks) {
    for (const b of safe(() => fn(p, m)) ?? []) {
      form.button(b.label);
      acts.push(b.act);
    }
  }
  form.button('§lRename');
  acts.push(async () => {
    const r = await new ModalFormData().title('Rename').textField('Name', 'A new name', { defaultValue: m.name }).show(p);
    const v = r.formValues?.[0];
    if (typeof v === 'string' && v.trim()) {
      m.name = v.trim().slice(0, 24);
      const e = entityOf(m);
      if (e) {
        e.setDynamicProperty('bc:kname', m.name);
        nameKnight(e);
      }
      save(p);
    }
  });
  form.button('§cRelease from the party');
  acts.push(async () => {
    const r = await new MessageFormData().title('Release').body(`Let §b${m.name}§r go their own way? Their level and bond will be lost.`).button1('§cRelease').button2('Keep them').show(p);
    if (r.selection !== 0) return;
    const e = entityOf(m);
    if (e) {
      safe(() => {
        e.triggerEvent('bc:release');
        e.setDynamicProperty('bc:owner', undefined);
        e.setDynamicProperty('bc:cid', undefined);
        e.setDynamicProperty('bc:prefix', '§a');
        nameKnight(e);
      });
    }
    party(p).m = party(p).m.filter((x) => x !== m);
    save(p);
    safe(() => p.sendMessage(`§b${m.name}§7 salutes and goes their own way.`));
  });
  form.button('Back');
  acts.push(() => openWhistle(p));
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return;
  await acts[res.selection]?.();
}

function orderAll(p, order) {
  for (const m of party(p).m) {
    const e = entityOf(m);
    if (!e) continue;
    safe(() => {
      if (order === 'hold') {
        e.setDynamicProperty('bc:order', 'hold');
        e.setDynamicProperty('bc:anchor', JSON.stringify({ x: e.location.x, y: e.location.y, z: e.location.z }));
        e.triggerEvent('bc:order_hold');
      } else {
        e.setDynamicProperty('bc:order', 'follow');
        e.triggerEvent('bc:order_follow');
      }
    });
  }
}

export function regroup(p) {
  const pt = party(p);
  pt.m.filter((m) => m.active).forEach((m, i) => {
    const e = entityOf(m);
    if (!e) return;
    const slot = slotFor(p, i, pt.cfg.formation);
    slot.y = p.location.y + 0.2;
    particle(e.dimension, 'bc:dust_burst', e.location, { color: rgb('c8c8c8'), scale: 0.5 });
    safe(() => e.teleport(slot));
    anim(e, 'animation.bc.magic_knight.salute');
  });
}

function setStance(p, st) {
  party(p).cfg.stance = st;
  for (const m of party(p).m) {
    const e = entityOf(m);
    if (!e) continue;
    safe(() => {
      e.setDynamicProperty('bc:stance', st === 'defensive' ? 'defensive' : 'aggressive');
      e.triggerEvent(st === 'passive' ? 'bc:passive_on' : 'bc:passive_off');
    });
  }
  save(p);
}

function unionMagic(p) {
  const pt = party(p);
  const t = system.currentTick;
  const souls = pt.m.filter((m) => m.active && entityOf(m) && bondRank(m.bond) >= 4).sort((a, b) => b.level - a.level);
  if (!souls.length) return safe(() => p.sendMessage('§7Union Magic needs a Soulbound companion at your side.'));
  if (t < pt.cfg.unionAt) return safe(() => p.sendMessage(`§7Union Magic is ready again in ${Math.ceil((pt.cfg.unionAt - t) / 20)}s.`));
  const m = souls[0];
  const e = entityOf(m);
  const target = aimEntity(p, 40) ?? foesOf(p, 24)[0];
  const kit = kitFor(m.attr, Math.max(6, m.level));
  const spec = kit[kit.length - 1];
  const sp = DATA.spells[m.attr]?.find((x) => JSON.stringify(x.spec) === JSON.stringify(spec));
  pt.cfg.unionAt = t + 2400;
  save(p);
  title(p, '§d§lUNION MAGIC', `§b${m.name}§7 & §f${p.name}§7: ${sp?.name ?? 'combined spell'}`, 50);
  bark(m, p, 'union', true);
  const pc = colorOf(`a:${state(p).attr || m.attr}`);
  particle(p.dimension, 'bc:magic_circle_ground', V.add(p.location, { x: 0, y: 0.1, z: 0 }), { color: pc, size: 5, life: 2 });
  particle(e.dimension, 'bc:magic_circle_ground', V.add(e.location, { x: 0, y: 0.1, z: 0 }), { color: colorOf(`a:${m.attr}`), size: 5, life: 2 });
  line(p, e, rgb('ff9aff'));
  sound(p.dimension, 'bc.chord', p.location, 1.2, 0.8);
  anim(e, 'animation.bc.magic_knight.cast_raise');
  safe(() => p.playAnimation('animation.bc.player.cast_raise'));
  system.runTimeout(() => {
    if (alive(e)) castSpec(e, spec, `a:${m.attr}`, (0.8 + m.level * 0.05) * 2.2, target);
  }, 12);
  return undefined;
}

export async function openWhistle(p) {
  const pt = party(p);
  const cfg = pt.cfg;
  sound(p.dimension, 'bc.ship.bell', p.location, 0.5, 2);
  const form = new ActionFormData().title('§lCompanions').body(pt.m.length
    ? `§7Party ${pt.m.length}/${C.partyMax} (reserve ${pt.r.length}/${C.reserveMax}) · tactic §f${C.tactics[cfg.tactic].name}§7 · formation §f${cfg.formation}§7 · stance §f${cfg.stance}§7 · loot ${cfg.loot ? '§aon' : '§coff'}\n§8Sneak + use the whistle: attack what you look at (or regroup).`
    : '§7You have no companions yet.\n\n§fRecruit a Magic Knight: talk to one in the wild (a Knight Contract or doubloons), use a §aKnight Contract§f, or rescue a wounded knight.');
  const acts = [];
  for (const m of pt.m) {
    const a = DATA.attributes[m.attr];
    form.button(`${a.glyph} §l${m.name}§r §8Lv ${m.level}\n${statusOf(m)} §8· ${C.bond[bondRank(m.bond)].name}`);
    acts.push(() => memberMenu(p, m));
  }
  if (pt.m.length) {
    form.button('§lEveryone: follow me');
    acts.push(() => orderAll(p, 'follow'));
    form.button('§lEveryone: hold here');
    acts.push(() => orderAll(p, 'hold'));
    form.button('§lRegroup\n§r§8Back into formation now');
    acts.push(() => regroup(p));
    form.button(`§lStance: ${cfg.stance}\n§r§8${cfg.stance === 'aggressive' ? 'next: defensive (guard you)' : cfg.stance === 'defensive' ? 'next: passive (no fighting)' : 'next: aggressive (hunt foes)'}`);
    acts.push(() => setStance(p, STANCES[(STANCES.indexOf(cfg.stance) + 1) % STANCES.length]));
    form.button(`§lFormation: ${cfg.formation}`);
    acts.push(() => {
      cfg.formation = FORMATIONS[(FORMATIONS.indexOf(cfg.formation) + 1) % FORMATIONS.length];
      save(p);
    });
    form.button(`§lGather loot: ${cfg.loot ? '§aon' : '§coff'}`);
    acts.push(() => {
      cfg.loot = !cfg.loot;
      save(p);
    });
    for (const fn of whistleHooks) {
      for (const b of safe(() => fn(p, pt)) ?? []) {
        form.button(b.label);
        acts.push(b.act);
      }
    }
    if (pt.m.some((m) => bondRank(m.bond) >= 4)) {
      form.button('§d§lUnion Magic\n§r§8A combined spell with your Soulbound companion');
      acts.push(() => unionMagic(p));
    }
  }
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return;
  await acts[res.selection]?.();
}

/** Use the Companion Whistle. Sneak: attack what you look at, or regroup. */
export function useWhistle(p) {
  if (!p.isSneaking) {
    system.run(() => openWhistle(p).catch(() => {}));
    return;
  }
  const pt = party(p);
  const target = aimEntity(p, 48);
  if (target && canHit(p, target)) {
    orderFocus.set(p.id, { id: target.id, until: system.currentTick + 400 });
    particle(p.dimension, 'bc:warning_circle', target.location, { size: 2.5, life: 1.2 });
    sound(p.dimension, 'bc.horn', p.location, 0.6, 1.6);
    const m = pt.m.find((x) => x.active && entityOf(x));
    if (m) safe(() => p.sendMessage(`§b${m.name}§f: ${pick(['On it!', 'Target sighted!', 'Leave it to us!'])}`));
  } else {
    regroup(p);
    sound(p.dimension, 'bc.ship.bell', p.location, 0.6, 1.6);
  }
}

// ------------------------------------------------------------------------------- talking to your own companion
async function companionTalk(p, e, item) {
  const mo = memberOf(e);
  if (!mo) return;
  const { m } = mo;
  const id = item?.typeId ?? '';
  for (const fn of talkHooks) {
    if (await fn(p, e, m, id)) return;
  }
  if (GIFTS[id]) {
    m.morale = Math.min(100, (m.morale ?? 70) + 5);
    addBond(p, m, GIFTS[id], 'gift');
    heal(e, 6);
    particle(e.dimension, 'bc:heal', center(e), { scale: 1 });
    sound(e.dimension, 'random.burp', e.location, 0.6, 1.2);
    bark(m, p, 'gift', true);
    if (!isCreative(p)) consumeHeld(p, id);
    return;
  }
  if (id.startsWith('bc:') && id.endsWith('_robe')) {
    const idx = DATA.knightRobes.indexOf(id.slice(3));
    if (idx < 0) return;
    if (m.gear) giveItem(p, new ItemStack(m.gear, 1));
    m.gear = id;
    m.robe = idx;
    safe(() => e.setProperty('bc:robe', idx));
    if (!isCreative(p)) consumeHeld(p, id);
    save(p);
    anim(e, 'animation.bc.magic_knight.salute');
    safe(() => p.sendMessage(`§b${m.name}§f now wears the ${DATA.robes[id.slice(3)]}. §7(${DATA.robePerks[id.slice(3)]})`));
    return;
  }
  await memberMenu(p, m);
}

export function consumeHeld(p, id) {
  const inv = p.getComponent('minecraft:inventory')?.container;
  const it = inv?.getItem(p.selectedSlotIndex);
  if (it?.typeId !== id) return;
  if (it.amount > 1) {
    it.amount -= 1;
    inv.setItem(p.selectedSlotIndex, it);
  } else inv.setItem(p.selectedSlotIndex, undefined);
}
export function giveItem(p, item) {
  const left = p.getComponent('minecraft:inventory')?.container?.addItem(item);
  if (left) p.dimension.spawnItem(left, p.location);
}

/** Wounded-knight rescue and other sources: hand a knight to a player as a companion. */
export function joinParty(e, p, bond = 0) {
  if (rosterSize(p) >= C.partyMax + C.reserveMax) return false;
  safe(() => e.setDynamicProperty('bc:bond0', bond));
  safe(() => {
    e.triggerEvent('bc:hire');
    e.setDynamicProperty('bc:owner', p.id);
  });
  adopt(e, p);
  return true;
}

export { setupKnight, line, slotFor, readFrom, applyTo, RESPAWN_MS, GIFTS };
