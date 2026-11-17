// Giant bosses: the Archdevil, the Stone Colossus, the Phantom Galleon and the Storm Kraken.
// One framework: each boss has a list of weighted attacks (engine recipes or special moves),
// a second phase below half health, and a summoning item.
import { Player, WeatherType, system, world } from '@minecraft/server';
import { center, effect, hurt, knock, launch, targetsAround } from '../core/combat.js';
import { anim, particle, rgb, shakeArea, shockwave, sound, title } from '../core/fx.js';
import { addXp } from '../core/progress.js';
import { addStars } from '../core/ranks.js';
import { V, alive, isCreative, pick, rand, repeat, safe, timer } from '../core/util.js';
import { castSpec } from './engine.js';
import { face } from './knights.js';

/**
 * @typedef {{w: number, min?: number, max?: number, phase?: number, spec?: Record<string, any>, src?: string, anim?: string, fn?: string}} Attack
 * @typedef {{name: string, src: string, every: [number, number], rage: [string, string], intro: [string, string], attacks: Attack[], range: number, stars: number}} BossDef
 */
/** @type {Record<string, BossDef>} */
const DEF = {
  'bc:archdevil': {
    name: '§4The Archdevil', src: 'a:blood', every: [45, 75], range: 40, stars: 8,
    intro: ['§4§lTHE ARCHDEVIL', '§7A king of the underworld steps through'],
    rage: ['§4§lThe Archdevil is enraged', '§7Its halo burns crimson'],
    attacks: [
      { w: 3, max: 22, spec: { t: 'bolt', d: 9, n: 5, spread: 30, shape: 3, speed: 2.2, fx: 'dark' }, src: 'a:dark', anim: 'animation.bc.devil.cast' },
      { w: 3, spec: { t: 'rain', d: 10, n: 10, r: 6, every: 3, fire: 5, fx: 'flame' }, anim: 'animation.bc.devil.cast' },
      { w: 3, max: 8, spec: { t: 'nova', d: 14, r: 7, kb: [2.2, 0.8], fx: 'blood' }, anim: 'animation.bc.devil.attack' },
      { w: 2, phase: 2, spec: { t: 'vortex', d: 16, r: 8, dur: 2.5, fx: 'dark' }, src: 'a:dark', anim: 'animation.bc.devil.cast' },
      { w: 2, phase: 2, spec: { t: 'meteor', d: 16, n: 5, r: 8, aoe: 4, fire: 6, size: 2, fx: 'magma' }, src: 'a:magma', anim: 'animation.bc.devil.cast' },
      { w: 1, fn: 'imps', anim: 'animation.bc.devil.cast' },
    ],
  },
  'bc:stone_colossus': {
    name: '§6The Stone Colossus', src: 'a:earth', every: [40, 70], range: 40, stars: 7,
    intro: ['§6§lTHE STONE COLOSSUS', '§7The mountain stands up'],
    rage: ['§6§lThe Colossus cracks open', '§7Molten light pours from its core'],
    attacks: [
      { w: 4, max: 7, fn: 'slam', anim: 'animation.bc.stone_colossus.slam' },
      { w: 3, min: 7, fn: 'boulders', anim: 'animation.bc.stone_colossus.slam' },
      { w: 2, spec: { t: 'wave', d: 12, len: 16, dirs: 8, fx: 'earth', kb: [0.3, 1.0] }, anim: 'animation.bc.stone_colossus.slam' },
      { w: 2, phase: 2, spec: { t: 'meteor', d: 14, n: 6, r: 7, aoe: 3.5, fire: 5, size: 2, fx: 'magma' }, src: 'a:magma' },
      { w: 1, phase: 2, spec: { t: 'prison', d: 12, r: 4, dur: 3, fx: 'sand' }, src: 'a:sand' },
    ],
  },
  'bc:phantom_galleon': {
    name: '§3The Phantom Galleon', src: 'a:crystal', every: [40, 65], range: 48, stars: 6,
    intro: ['§3§lTHE PHANTOM GALLEON', '§7A ship of the drowned sails the sky'],
    rage: ['§3§lThe Galleon raises its black sails', '§7The dead crew stirs'],
    attacks: [
      { w: 4, fn: 'broadside' },
      { w: 2, fn: 'crew' },
      { w: 2, spec: { t: 'meteor', d: 10, n: 6, r: 6, aoe: 3, size: 1, fx: 'crystal' } },
      { w: 2, phase: 2, spec: { t: 'strikes', d: 11, n: 5, r: 10, fx: 'mist', eff: [['blindness', 3, 0]] }, src: 'a:mist' },
    ],
  },
  'bc:storm_kraken': {
    name: '§9The Storm Kraken', src: 'a:lightning', every: [40, 65], range: 44, stars: 7,
    intro: ['§9§lTHE STORM KRAKEN', '§7The sea itself rises against you'],
    rage: ['§9§lThe Kraken calls the storm', '§7Thunder answers'],
    attacks: [
      { w: 3, spec: { t: 'strikes', d: 12, n: 5, r: 10, fx: 'lightning' }, anim: 'animation.bc.storm_kraken.slam' },
      { w: 3, max: 14, spec: { t: 'wave', d: 14, len: 14, dirs: 4, fx: 'water', kb: [1.6, 0.9] }, src: 'a:water', anim: 'animation.bc.storm_kraken.slam' },
      { w: 2, spec: { t: 'vortex', d: 10, r: 7, dur: 3, fx: 'water' }, src: 'a:water' },
      { w: 2, spec: { t: 'prison', d: 8, r: 4, dur: 3, fx: 'bubble', eff: [['levitation', 2, 1]] }, src: 'a:bubble' },
      { w: 2, phase: 2, spec: { t: 'bolt', d: 9, n: 7, spread: 40, shape: 3, speed: 2.4, fx: 'lightning' } },
    ],
  },
};

/** @type {Map<string, {next: number, enraged: boolean}>} */
const bosses = new Map();

function track(e) {
  if (!DEF[e.typeId] || bosses.has(e.id)) return;
  bosses.set(e.id, { next: system.currentTick + 60, enraged: false });
}
world.afterEvents.entitySpawn.subscribe((ev) => safe(() => track(ev.entity)));
world.afterEvents.entityLoad.subscribe((ev) => safe(() => track(ev.entity)));

function bossTarget(e, range) {
  let best;
  let bd = range;
  for (const p of e.dimension.getPlayers({ location: e.location, maxDistance: range })) {
    const gm = safe(() => p.getGameMode());
    if (gm === 'Creative' || gm === 'Spectator') continue;
    const d = V.dist(p.location, e.location);
    if (d < bd) {
      bd = d;
      best = p;
    }
  }
  if (best) return best;
  const near = safe(() => e.dimension.getEntities({ location: e.location, maxDistance: 24, families: ['bc_knight'] })) ?? [];
  return near[0];
}

// ------------------------------------------------------------------------------- special moves
/** @type {Record<string, (e: any, target: any, st: {enraged: boolean}) => void>} */
const MOVES = {
  imps(e, target, st) {
    sound(e.dimension, 'bc.devil.roar', e.location, 2, 0.6);
    const n = st.enraged ? 4 : 3;
    for (let i = 0; i < n; i++) {
      const type = st.enraged && i === 0 ? 'bc:dark_disciple' : 'bc:imp';
      const at = V.add(e.location, { x: rand(-4, 4), y: 1, z: rand(-4, 4) });
      particle(e.dimension, 'bc:magic_circle_dark', at, { size: 2, life: 1 });
      safe(() => e.dimension.spawnEntity(type, at));
    }
  },
  slam(e, target, st) {
    timer(9, () => {
      if (!alive(e)) return;
      const at = e.location;
      sound(e.dimension, 'bc.golem.slam', at, 2.5, 0.5);
      shockwave(e.dimension, at, 'earth', 7);
      particle(e.dimension, 'bc:rock_debris', at, { scale: 2 });
      shakeArea(e.dimension, at, 24, 0.7, 0.8);
      for (const v of targetsAround(e.dimension, at, 7, e)) {
        hurt(v, st.enraged ? 24 : 18, e);
        knock(v, V.sub(v.location, at), 1.4, 0.9);
      }
    });
  },
  boulders(e, target, st) {
    const n = st.enraged ? 3 : 2;
    for (let i = 0; i < n; i++) {
      timer(8 + i * 6, () => {
        if (!alive(e) || !alive(target)) return;
        const from = V.add(e.location, { x: 0, y: 8, z: 0 });
        launch(e, 'bc:boulder', from, V.sub(V.add(center(target), { x: rand(-1.5, 1.5), y: 0, z: rand(-1.5, 1.5) }), from), 1.5,
          { spell: 'colossus_rock', attr: 'earth', damage: 14, pierce: 0 });
      });
    }
  },
  broadside(e, target, st) {
    const n = st.enraged ? 8 : 6;
    sound(e.dimension, 'bc.ship.bell', e.location, 2, 0.6);
    for (let i = 0; i < n; i++) {
      timer(i * 4, () => {
        if (!alive(e) || !alive(target)) return;
        const side = i % 2 ? 1 : -1;
        const from = V.add(e.location, { x: side * 2.5, y: 1.5, z: rand(-3, 3) });
        const to = V.add(target.location, { x: rand(-3, 3), y: 0, z: rand(-3, 3) });
        sound(e.dimension, 'bc.cannon', from, 1.6, 0.8 + Math.random() * 0.2);
        particle(e.dimension, 'bc:smoke_burst', from, { scale: 0.8 });
        launch(e, 'bc:cannonball', from, V.sub(to, from), 1.6, { spell: 'galleon_cannon', attr: 'flame', damage: 11, pierce: 0 });
      });
    }
  },
  crew(e, target, st) {
    const alive_ = safe(() => e.dimension.getEntities({ location: e.location, maxDistance: 48, type: 'bc:phantom_raider' }).length) ?? 0;
    if (alive_ >= 8) return;
    sound(e.dimension, 'bc.portal', target.location, 1.5, 0.5);
    for (let i = 0; i < (st.enraged ? 4 : 2); i++) {
      const at = V.add(target.location, { x: rand(-6, 6), y: 0.5, z: rand(-6, 6) });
      particle(e.dimension, 'bc:fog_cloud', at, { scale: 0.3 });
      safe(() => e.dimension.spawnEntity('bc:phantom_raider', at));
    }
  },
};

// ------------------------------------------------------------------------------- the loop
system.runInterval(() => {
  const t = system.currentTick;
  for (const [id, st] of bosses) {
    const e = world.getEntity(id);
    if (!e) {
      bosses.delete(id);
      continue;
    }
    const def = DEF[e.typeId];
    safe(() => {
      const target = bossTarget(e, def.range);
      // the galleon keeps station above its prey
      if (e.typeId === 'bc:phantom_galleon' && target) {
        const want = V.add(target.location, V.mul(V.flat(V.sub(e.location, target.location)), 14));
        want.y = target.location.y + 11;
        const d = V.sub(want, e.location);
        if (V.len(d) > 3) safe(() => e.applyImpulse(V.mul(V.norm(d), 0.12)));
      }
      const hp = e.getComponent('minecraft:health');
      if (hp && !st.enraged && hp.currentValue < hp.effectiveMax * 0.5) {
        st.enraged = true;
        sound(e.dimension, e.typeId === 'bc:storm_kraken' ? 'ambient.weather.thunder' : 'bc.devil.roar', e.location, 3, 0.5);
        shakeArea(e.dimension, e.location, 40, 0.6, 1.2);
        for (const p of e.dimension.getPlayers({ location: e.location, maxDistance: 56 })) title(p, def.rage[0], def.rage[1], 50);
        effect(e, 'strength', 600, 1, false);
        effect(e, 'resistance', 600, 0, false);
        if (e.typeId === 'bc:storm_kraken') safe(() => e.dimension.setWeather(WeatherType.Thunder, 6000));
      }
      if (!target || st.next > t) return;
      const d = V.dist(target.location, e.location);
      const pool = def.attacks.filter((a) => (a.phase ?? 1) <= (st.enraged ? 2 : 1) && d >= (a.min ?? 0) && d <= (a.max ?? 99));
      if (!pool.length) return;
      let r = Math.random() * pool.reduce((s, a) => s + a.w, 0);
      let atk = pool[0];
      for (const a of pool) {
        r -= a.w;
        if (r <= 0) {
          atk = a;
          break;
        }
      }
      face(e, target);
      if (atk.anim) anim(e, atk.anim);
      if (atk.fn) MOVES[atk.fn](e, target, st);
      else castSpec(e, atk.spec, atk.src ?? def.src, st.enraged ? 1.25 : 1.0, target);
      const [lo, hi] = def.every;
      st.next = t + Math.round(rand(lo, hi) * (st.enraged ? 0.7 : 1));
    }, 'boss');
  }
}, 10);

world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const e = ev.deadEntity;
  const def = DEF[e.typeId];
  if (!def) return;
  const loc = e.location;
  const dim = e.dimension;
  particle(dim, 'bc:light_burst', V.add(loc, { x: 0, y: 2, z: 0 }), { scale: 3 });
  particle(dim, 'bc:clover_leaves', V.add(loc, { x: 0, y: 2, z: 0 }), { scale: 2.5 });
  sound(dim, 'bc.fanfare', loc, 2, 0.9);
  const killer = ev.damageSource.damagingEntity;
  for (const p of dim.getPlayers({ location: loc, maxDistance: 64 })) {
    title(p, '§6§lBOSS DEFEATED', `${def.name}§7 has fallen`, 70);
    addXp(p, p === killer ? 400 : 200);
    safe(() => addStars(p, p === killer ? def.stars : Math.ceil(def.stars / 2), `${def.name.replace(/§./g, '')} defeated`));
  }
  if (e.typeId === 'bc:storm_kraken') safe(() => dim.setWeather(WeatherType.Clear, 6000));
}, 'bossDie'));

// ------------------------------------------------------------------------------- summoning
/** Raise a boss in front of a location with a short ceremony. */
export function summonBoss(type, dim, loc, players = []) {
  const def = DEF[type];
  if (!def) return;
  const color = { 'bc:archdevil': 'd01a34', 'bc:stone_colossus': 'ff8a2a', 'bc:phantom_galleon': '96ffdc', 'bc:storm_kraken': '9ae8ff' }[type];
  sound(dim, type === 'bc:phantom_galleon' ? 'bc.ship.bell' : 'bc.gong', loc, 3, 0.6);
  repeat(10, 10, (i) => {
    particle(dim, type === 'bc:archdevil' ? 'bc:magic_circle_dark' : 'bc:magic_circle_ground', V.add(loc, { x: 0, y: 0.1, z: 0 }), { color: rgb(color), size: 4 + i * 0.6, life: 0.7 });
    if (type === 'bc:stone_colossus') {
      particle(dim, 'bc:rock_debris', V.add(loc, { x: rand(-3, 3), y: 0.5, z: rand(-3, 3) }), { scale: 1.2 });
      shakeArea(dim, loc, 30, 0.4, 0.5);
    } else if (type === 'bc:phantom_galleon') particle(dim, 'bc:fog_cloud', loc, { scale: 0.6 });
    else particle(dim, 'bc:pillar', loc, { color: rgb(color), scale: 1.5 });
  }, () => {
    const at = type === 'bc:phantom_galleon' ? V.add(loc, { x: 0, y: 10, z: 0 }) : loc;
    const e = safe(() => dim.spawnEntity(type, at));
    if (!e) return;
    track(e);
    shockwave(dim, loc, 'flame', 8);
    sound(dim, type === 'bc:storm_kraken' ? 'bc.leviathan.roar' : type === 'bc:stone_colossus' ? 'bc.golem.slam' : 'bc.devil.roar', loc, 3, 0.5);
    for (const p of dim.getPlayers({ location: loc, maxDistance: 64 })) title(p, def.intro[0], def.intro[1], 60);
    if (type === 'bc:archdevil') for (const p of players) effect(p, 'darkness', 4, 0, false);
  });
}

function waterSpot(p) {
  const dir = V.flat(p.getViewDirection());
  for (const dist of [10, 14, 18, 6, 22]) {
    const at = V.add(p.location, V.mul(dir, dist));
    for (let dy = 3; dy >= -6; dy--) {
      const b = safe(() => p.dimension.getBlock({ x: Math.floor(at.x), y: Math.floor(p.location.y) + dy, z: Math.floor(at.z) }));
      if (b?.typeId === 'minecraft:water') {
        const below = safe(() => p.dimension.getBlock({ x: Math.floor(at.x), y: Math.floor(p.location.y) + dy - 3, z: Math.floor(at.z) }));
        if (below?.typeId === 'minecraft:water') return { x: at.x, y: Math.floor(p.location.y) + dy - 2, z: at.z };
      }
    }
  }
  return undefined;
}

const ITEMS = {
  'bc:archdevil_sigil': 'bc:archdevil',
  'bc:colossus_core': 'bc:stone_colossus',
  'bc:galleon_bell': 'bc:phantom_galleon',
  'bc:kraken_lure': 'bc:storm_kraken',
};

/** @returns {boolean} true when the item was a boss summon */
export function useBossItem(p, id) {
  const type = ITEMS[id];
  if (!type) return false;
  let loc;
  if (type === 'bc:storm_kraken') {
    loc = waterSpot(p);
    if (!loc) {
      safe(() => p.sendMessage('§9The lure needs deep water nearby. Stand at the shore of an ocean or a deep lake.'));
      return true;
    }
  } else {
    const dir = V.flat(p.getViewDirection());
    loc = V.add(p.location, V.mul(dir, type === 'bc:stone_colossus' ? 12 : 9));
    loc.y = p.location.y;
  }
  if (!isCreative(p)) {
    const inv = p.getComponent('minecraft:inventory')?.container;
    const it = inv?.getItem(p.selectedSlotIndex);
    if (it?.typeId === id) {
      if (it.amount > 1) {
        it.amount -= 1;
        inv.setItem(p.selectedSlotIndex, it);
      } else inv.setItem(p.selectedSlotIndex, undefined);
    }
  }
  safe(() => p.sendMessage(`§7Something answers the call... ${DEF[type].name}§7 is coming.`));
  summonBoss(type, p.dimension, loc, [p]);
  return true;
}

export { Player, pick };
