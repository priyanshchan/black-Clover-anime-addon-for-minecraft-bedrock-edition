// Magic Knights: named NPC mages of every attribute. They roam, hunt monsters, pirates and devils,
// cast real spells through the engine, fight in War Table battles and can be hired with a contract.
import { Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { canHit, center, teamOf } from '../core/combat.js';
import { anim, particle, rgb, sound } from '../core/fx.js';
import { V, alive, pick, rand, safe, yawOf } from '../core/util.js';
import { castSpec } from './engine.js';

/** @type {Map<string, {next: number}>} */
const knights = new Map();
const ATTRS = DATA.order.filter((a) => a !== 'anti');

/** Give a knight its attribute, name and (optionally) robe. */
export function setupKnight(e, opts = {}) {
  safe(() => {
    const attr = opts.attr ?? pick(ATTRS);
    const name = opts.name ?? `${pick(DATA.knightFirst)} ${pick(DATA.knightLast)}`;
    e.setDynamicProperty('bc:attr', attr);
    e.setDynamicProperty('bc:kname', name);
    if (opts.robe !== undefined) e.setProperty('bc:robe', opts.robe);
    else if (opts.randomRobe) e.setProperty('bc:robe', Math.floor(Math.random() * DATA.knightRobes.length));
    e.nameTag = `${opts.prefix ?? '§a'}${name} §r${DATA.attributes[attr].glyph}`;
  }, 'setupKnight');
  knights.set(e.id, { next: system.currentTick + 40 });
}

export function knightAttr(e) {
  const v = safe(() => e.getDynamicProperty('bc:attr'));
  return typeof v === 'string' && DATA.attributes[v] ? v : 'wind';
}

function track(e) {
  if (e.typeId !== 'bc:magic_knight' || knights.has(e.id)) return;
  if (typeof safe(() => e.getDynamicProperty('bc:attr')) !== 'string') setupKnight(e);
  else knights.set(e.id, { next: system.currentTick + 40 });
}
world.afterEvents.entitySpawn.subscribe((ev) => safe(() => track(ev.entity)));
world.afterEvents.entityLoad.subscribe((ev) => safe(() => track(ev.entity)));

/** The spells a knight of this attribute knows (engine recipes only). */
export function kitFor(attr) {
  if (DATA.npcKits[attr]) return DATA.npcKits[attr];
  const specs = DATA.spells[attr]?.map((sp) => sp.spec).filter(Boolean) ?? [];
  const kit = specs.slice(0, 3);
  if (specs[3] && Math.random() < 0.2) kit.push(specs[3]);
  return kit.length ? kit : DATA.npcKits.wind;
}

/** Nearest enemy of an NPC (War Table side, or monsters / grudges in the wild). */
export function enemyOf(e, range = 18) {
  const tm = teamOf(e);
  let list = [];
  safe(() => {
    if (tm) list = e.dimension.getEntities({ location: e.location, maxDistance: range, families: [`bc_team_${tm === 'a' ? 'b' : 'a'}`] });
    else {
      list = e.dimension.getEntities({ location: e.location, maxDistance: range, families: ['monster'] }).filter((x) => canHit(e, x));
      if (!list.length) list = e.dimension.getPlayers({ location: e.location, maxDistance: range }).filter((p) => canHit(e, p));
    }
  });
  let best;
  let bd = Infinity;
  for (const x of list) {
    const d = V.dist(x.location, e.location);
    if (d < bd && alive(x)) {
      bd = d;
      best = x;
    }
  }
  return best;
}

export function face(e, target) {
  safe(() => e.setRotation({ x: 0, y: yawOf(V.sub(target.location, e.location)) }));
}

system.runInterval(() => {
  const t = system.currentTick;
  for (const [id, st] of knights) {
    if (st.next > t) continue;
    const e = world.getEntity(id);
    if (!e) {
      knights.delete(id);
      continue;
    }
    safe(() => {
      const target = enemyOf(e, 18);
      if (!target) {
        st.next = t + 20;
        return;
      }
      const attr = knightAttr(e);
      const hp = e.getComponent('minecraft:health');
      const hurtBad = hp ? hp.currentValue < hp.effectiveMax * 0.55 : false;
      const kit = kitFor(attr).filter((s) => s.t !== 'wall' && (s.t !== 'summon' || Math.random() < 0.2) && (!['heal', 'buff', 'rewind'].includes(s.t) || hurtBad || Math.random() < 0.15));
      if (!kit.length) {
        st.next = t + 30;
        return;
      }
      const spec = pick(kit);
      const d = V.dist(target.location, e.location);
      if (spec.t === 'nova' && spec.at !== 'aim' && d > (spec.r ?? 6) + 1) {
        st.next = t + 10;
        return;
      }
      face(e, target);
      anim(e, 'animation.bc.magic_knight.cast');
      castSpec(e, spec, `a:${attr}`, 0.85, target);
      st.next = t + 45 + Math.floor(rand(0, 45));
    }, 'knight');
  }
}, 10);

// ------------------------------------------------------------------------------- hiring
/** Use a Knight Contract: a Magic Knight joins you as a companion. */
export function hireKnight(p) {
  const dir = V.flat(p.getViewDirection());
  const loc = V.add(p.location, V.mul(dir, 2));
  const e = safe(() => p.dimension.spawnEntity('bc:magic_knight', loc, { spawnEvent: 'bc:hire' }));
  if (!e) return false;
  setupKnight(e, { randomRobe: true, prefix: '§b' });
  safe(() => {
    e.setDynamicProperty('bc:owner', p.id);
    e.getComponent('minecraft:tameable')?.tame(p);
  });
  const attr = knightAttr(e);
  const a = DATA.attributes[attr];
  particle(p.dimension, 'bc:magic_circle_ground', V.add(loc, { x: 0, y: 0.1, z: 0 }), { color: rgb(a.color), size: 2.5, life: 1.5 });
  particle(p.dimension, 'bc:clover_leaves', center(e), { scale: 1 });
  sound(p.dimension, 'bc.fanfare', loc, 0.8, 1.1);
  const name = safe(() => e.getDynamicProperty('bc:kname')) ?? 'A knight';
  safe(() => p.sendMessage(`${a.glyph} §b${name}§f, a ${a.mc}${a.name}§f mage, swears to fight at your side.`));
  return true;
}

// hired knights keep up with their captain
system.runInterval(() => {
  for (const [id] of knights) {
    const e = world.getEntity(id);
    if (!e) continue;
    safe(() => {
      const owner = e.getDynamicProperty('bc:owner');
      if (typeof owner !== 'string') return;
      const p = world.getEntity(owner);
      if (!(p instanceof Player) || p.dimension.id !== e.dimension.id) return;
      if (V.dist(p.location, e.location) > 24) e.teleport(V.add(p.location, { x: rand(-2, 2), y: 0.2, z: rand(-2, 2) }));
    });
  }
}, 40);

// knights swing visibly in melee
world.afterEvents.entityHitEntity.subscribe((ev) => {
  if (ev.damagingEntity.typeId === 'bc:magic_knight') anim(ev.damagingEntity, 'animation.bc.magic_knight.attack');
});
