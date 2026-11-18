// Warbands: hostile NPCs run by the tactical brain fight as groups, not as a crowd of loners.
// Every second, enemies of one faction within 18 blocks of each other near a player form a warband. A warband:
// * shares a FOCUS - the most vulnerable foe around: hurt, alone, a healer, or whoever just hit one of its summoners;
// * SURROUNDS it - fighters take evenly spaced flank slots around the focus, casters and archers an arc behind them;
// * CALLS FOR HELP - when it is hurt, its kind within 32 blocks come running;
// * BREAKS - when it has lost more than half of its strongest number and is outnumbered, the faint-hearted flee
//   (and eventually leave) while the rest regroup around their leader.
import { Player, system, world } from '@minecraft/server';
import { HOSTILE_SIDES, factionOf, foesOf, ownerOf } from '../core/combat.js';
import { particle, rgb } from '../core/fx.js';
import { V, alive, safe } from '../core/util.js';
import { brainInfo, hasBrain, setBandProvider } from './ai.js';

/** @typedef {{ members: string[], focus: string, faction: string, leader: string, broken: boolean }} Band */
/** @type {Map<string, Band>} entity id -> its band */
const bandOf = new Map();
/** @type {Map<string, number>} entity id -> the most members its band has had */
const peak = new Map();
/** @type {Map<string, number>} entity id -> tick it may flee until */
const fleeing = new Map();
/** @type {Map<string, {at: number, by: string}>} entity id -> last time it was hurt, and by whom */
const hurtLog = new Map();
/** @type {Map<string, {target: string, until: number}>} rallied helpers */
const rallied = new Map();
const callCd = new Map();
const breakNote = new Map();
const NAMES = { devil: 'the devils', pirate: 'the raiders', rogue: 'the rogues', bandit: 'the bandits', hive: 'the swarm', witch: 'the witches', undead: 'the dead' };

function hpFrac(e) {
  const h = safe(() => e.getComponent('minecraft:health'));
  return h ? h.currentValue / Math.max(1, h.effectiveMax) : 1;
}

function isSupport(x) {
  if (x instanceof Player) return false;
  if (typeof safe(() => x.getDynamicProperty('bc:cid')) !== 'string') return false;
  return safe(() => brainInfo(x).role) === 'support';
}

/** How juicy a target is for a whole band. */
function preyScore(x, center, band) {
  let s = (1 - hpFrac(x)) * 10 - V.dist(x.location, center) * 0.3;
  const pals = safe(() => x.dimension.getEntities({ location: x.location, maxDistance: 5, families: ['bc_knight'] }).length) ?? 0;
  const near = safe(() => x.dimension.getPlayers({ location: x.location, maxDistance: 5 }).length) ?? 0;
  if (pals + near - (x instanceof Player ? 1 : 1) <= 0) s += 6; // alone
  if (isSupport(x)) s += 5;
  if (x.id === band.focus) s += 4;
  // whoever is hurting a summoner gets the band's attention
  for (const id of band.members) {
    const h = hurtLog.get(id);
    if (h && h.by === x.id && system.currentTick - h.at < 100) {
      const m = world.getEntity(id);
      s += m?.typeId === 'bc:cultist' ? 9 : 2;
    }
  }
  return s;
}

world.afterEvents.entityHurt.subscribe((ev) => {
  const e = ev.hurtEntity;
  if (!hasBrain(e)) return;
  hurtLog.set(e.id, { at: system.currentTick, by: ev.damageSource.damagingEntity?.id ?? '' });
});

function formBands() {
  const t = system.currentTick;
  const seen = new Set();
  const nextBand = new Map();
  for (const p of world.getAllPlayers()) {
    const list = (safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 56, families: ['monster'] })) ?? [])
      .filter((e) => hasBrain(e) && HOSTILE_SIDES.has(factionOf(e)) && !seen.has(e.id) && !safe(() => e.matches({ families: ['boss'] })) && !ownerOf(e));
    for (const e of list) {
      if (seen.has(e.id)) continue;
      const fac = factionOf(e);
      const members = list.filter((x) => !seen.has(x.id) && factionOf(x) === fac && V.dist(x.location, e.location) <= 18);
      for (const m of members) seen.add(m.id);
      const old = bandOf.get(e.id);
      /** @type {Band} */
      const band = { members: members.map((m) => m.id), focus: old?.focus ?? '', faction: fac, leader: '', broken: false };
      let best = -1;
      for (const m of members) {
        const h = safe(() => m.getComponent('minecraft:health')?.currentValue) ?? 0;
        if (h > best) {
          best = h;
          band.leader = m.id;
        }
        peak.set(m.id, Math.max(peak.get(m.id) ?? 0, members.length));
      }
      // the focus: the most vulnerable foe near the band
      const center = members.reduce((c, m) => V.add(c, V.mul(m.location, 1 / members.length)), { x: 0, y: 0, z: 0 });
      let prey;
      let ps = -Infinity;
      for (const x of safe(() => foesOf(members[0], 26)) ?? []) {
        const s = preyScore(x, center, band);
        if (s > ps) {
          ps = s;
          prey = x;
        }
      }
      band.focus = prey?.id ?? '';
      // morale: a band that has lost over half its number and is outnumbered breaks
      const most = Math.max(...members.map((m) => peak.get(m.id) ?? members.length));
      const foes = safe(() => foesOf(members[0], 20).length) ?? 0;
      band.broken = most >= 3 && members.length <= most / 2 && foes >= members.length;
      if (band.broken) {
        for (const m of members) {
          if ((fleeing.get(m.id) ?? 0) > t) continue;
          const courage = safe(() => brainInfo(m).courage) ?? 0.5;
          if (courage < 0.55 && !safe(() => m.hasTag('bc_event'))) {
            fleeing.set(m.id, t + 240);
            particle(m.dimension, 'bc:dust_burst', m.location, { color: rgb('a0a0a0'), scale: 0.6 });
          }
        }
        if ((breakNote.get(p.id) ?? 0) < t) {
          breakNote.set(p.id, t + 400);
          safe(() => p.onScreenDisplay.setActionBar(`§7${(NAMES[fac] ?? 'they').replace(/^\w/, (c) => c.toUpperCase())} are breaking - some of them run!`));
        }
      }
      // a hurt band calls for help
      const hurtRecently = members.some((m) => t - (hurtLog.get(m.id)?.at ?? -999) < 60);
      if (hurtRecently && members.length < 4 && prey && (callCd.get(band.leader) ?? 0) < t) {
        callCd.set(band.leader, t + 300);
        for (const x of safe(() => members[0].dimension.getEntities({ location: center, maxDistance: 32, families: ['monster'] })) ?? []) {
          if (members.some((m) => m.id === x.id) || !hasBrain(x) || factionOf(x) !== fac) continue;
          rallied.set(x.id, { target: prey.id, until: t + 300 });
        }
      }
      for (const m of members) nextBand.set(m.id, band);
    }
  }
  bandOf.clear();
  for (const [k, v] of nextBand) bandOf.set(k, v);
}

system.runInterval(() => safe(formBands, 'warband'), 20);

// fleeing enemies who got away simply leave
system.runInterval(() => {
  const t = system.currentTick;
  for (const [id, until] of fleeing) {
    if (until > t) continue;
    fleeing.delete(id);
    const e = world.getEntity(id);
    if (!e || !alive(e)) continue;
    const near = safe(() => e.dimension.getPlayers({ location: e.location, maxDistance: 20 }).length) ?? 1;
    if (!near && !safe(() => e.matches({ families: ['boss'] }))) {
      particle(e.dimension, 'bc:smoke_burst', e.location, { scale: 0.6 });
      safe(() => e.remove());
    }
  }
}, 100);

/** What the brain needs to know about an enemy's warband. */
setBandProvider((e) => {
  const t = system.currentTick;
  if ((fleeing.get(e.id) ?? 0) > t) return { flee: true };
  const r = rallied.get(e.id);
  const band = bandOf.get(e.id);
  if (!band && !(r && r.until > t)) return undefined;
  const focus = r && r.until > t ? r.target : band?.focus;
  const target = focus ? world.getEntity(focus) : undefined;
  let slot;
  if (band && target) {
    const melee = (safe(() => brainInfo(e).role) ?? 'striker') === 'brawler';
    const same = band.members.filter((id) => {
      const m = world.getEntity(id);
      return m && ((safe(() => brainInfo(m).role) ?? 'striker') === 'brawler') === melee;
    });
    const i = Math.max(0, same.indexOf(e.id));
    const n = Math.max(1, same.length);
    const base = (band.members.length * 37) % 360;
    if (melee) {
      // surround the prey
      slot = V.add(target.location, V.yaw({ x: 2.0, y: 0, z: 0 }, base + (360 / n) * i));
    } else {
      // an arc behind the fighters, facing the prey
      const leader = world.getEntity(band.leader) ?? e;
      const away = V.flat(V.sub(leader.location, target.location));
      const dir = V.len(away) > 0.1 ? away : { x: 1, y: 0, z: 0 };
      slot = V.add(target.location, V.yaw(V.mul(dir, 9), (i - (n - 1) / 2) * 25));
    }
  }
  return {
    focus,
    slot,
    bonus: (f) => (band && band.leader === e.id && f.id === focus ? 2 : 0),
  };
});

export { bandOf };
