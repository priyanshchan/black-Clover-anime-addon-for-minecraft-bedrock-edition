// Giant bosses: the Archdevil, the Stone Colossus, the Phantom Galleon, the Storm Kraken, the Fallen Captain,
// the Witch Sisters (the Frost Witch and the Ember Witch) and the Bone Dragon.
//
// One framework drives them all:
// * THREAT: every boss remembers who hurt it most (players, knights, companions) and turns on the biggest threat -
//   it only switches when someone out-does the current target by 10%. Brawler companions draw extra threat.
// * PHASES: below 50% health it enrages, below 25% it unleashes a once-only DESPERATION move.
// * TELEGRAPHS: big blows show a warning circle first - get out of it.
// * MOVEMENT: the Archdevil blinks away when surrounded, the Kraken dives and resurfaces elsewhere, the Colossus
//   stomps foes away, the Galleon keeps station above you and rams in its last phase, the Captain blinks behind you,
//   the Witches blink away from melee, the Bone Dragon circles above and dives.
// * TWINS: the Witch Sisters weave Twin Spells together; when one falls, the other goes straight to her desperation move.
// * ENRAGE TIMER: after six minutes any boss grows stronger and faster.
import { Player, WeatherType, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { center, effect, hurt, knock, launch, ownerOf, targetsAround } from '../core/combat.js';
import { anim, particle, rgb, shakeArea, shockwave, sound, title } from '../core/fx.js';
import { addXp } from '../core/progress.js';
import { addStars } from '../core/ranks.js';
import { emit } from '../core/bus.js';
import { V, alive, isCreative, pick, rand, repeat, safe, timer } from '../core/util.js';
import { castSpec } from './engine.js';
import { face, kitFor } from './knights.js';

/**
 * @typedef {{w: number, min?: number, max?: number, phase?: number, spec?: Record<string, any>, src?: string, anim?: string, fn?: string, tele?: number}} Attack
 * @typedef {{name: string, src: string, every: [number, number], rage: [string, string], intro: [string, string], last: [string, string],
 *            attacks: Attack[], range: number, stars: number, desperation: string, roar?: string}} BossDef
 */
/** @type {Record<string, BossDef>} */
const DEF = {
  'bc:archdevil': {
    name: '§4The Archdevil', src: 'a:blood', every: [45, 75], range: 40, stars: 8, desperation: 'hellgate', roar: 'animation.bc.archdevil.roar',
    intro: ['§4§lTHE ARCHDEVIL', '§7A king of the underworld steps through'],
    rage: ['§4§lThe Archdevil is enraged', '§7Its halo burns crimson'],
    last: ['§4§lHELLGATE', '§7The Archdevil tears the world open'],
    attacks: [
      { w: 3, max: 22, spec: { t: 'bolt', d: 9, n: 5, spread: 30, shape: 3, speed: 2.2, fx: 'dark' }, src: 'a:dark', anim: 'animation.bc.devil.cast' },
      { w: 3, spec: { t: 'rain', d: 10, n: 10, r: 6, every: 3, fire: 5, fx: 'flame' }, anim: 'animation.bc.devil.cast' },
      { w: 3, max: 8, tele: 16, spec: { t: 'nova', d: 14, r: 7, kb: [2.2, 0.8], fx: 'blood' }, anim: 'animation.bc.devil.attack' },
      { w: 2, phase: 2, spec: { t: 'vortex', d: 16, r: 8, dur: 2.5, fx: 'dark' }, src: 'a:dark', anim: 'animation.bc.devil.cast' },
      { w: 2, phase: 2, spec: { t: 'meteor', d: 16, n: 5, r: 8, aoe: 4, fire: 6, size: 2, fx: 'magma' }, src: 'a:magma', anim: 'animation.bc.devil.cast' },
      { w: 1, fn: 'imps', anim: 'animation.bc.devil.cast' },
    ],
  },
  'bc:stone_colossus': {
    name: '§6The Stone Colossus', src: 'a:earth', every: [40, 70], range: 40, stars: 7, desperation: 'avalanche', roar: 'animation.bc.stone_colossus.roar',
    intro: ['§6§lTHE STONE COLOSSUS', '§7The mountain stands up'],
    rage: ['§6§lThe Colossus cracks open', '§7Molten light pours from its core'],
    last: ['§6§lAVALANCHE', '§7The sky fills with stone'],
    attacks: [
      { w: 4, max: 7, fn: 'slam', anim: 'animation.bc.stone_colossus.slam' },
      { w: 3, min: 7, fn: 'boulders', anim: 'animation.bc.stone_colossus.throw' },
      { w: 2, tele: 18, spec: { t: 'wave', d: 12, len: 16, dirs: 8, fx: 'earth', kb: [0.3, 1.0] }, anim: 'animation.bc.stone_colossus.stomp' },
      { w: 2, phase: 2, spec: { t: 'meteor', d: 14, n: 6, r: 7, aoe: 3.5, fire: 5, size: 2, fx: 'magma' }, src: 'a:magma', anim: 'animation.bc.stone_colossus.throw' },
      { w: 1, phase: 2, spec: { t: 'prison', d: 12, r: 4, dur: 3, fx: 'sand' }, src: 'a:sand' },
    ],
  },
  'bc:phantom_galleon': {
    name: '§3The Phantom Galleon', src: 'a:crystal', every: [40, 65], range: 48, stars: 6, desperation: 'ram',
    intro: ['§3§lTHE PHANTOM GALLEON', '§7A ship of the drowned sails the sky'],
    rage: ['§3§lThe Galleon raises its black sails', '§7The dead crew stirs'],
    last: ['§3§lGHOST RAM', '§7The Galleon dives straight at you'],
    attacks: [
      { w: 4, fn: 'broadside', anim: 'animation.bc.phantom_galleon.broadside' },
      { w: 2, fn: 'crew' },
      { w: 2, spec: { t: 'meteor', d: 10, n: 6, r: 6, aoe: 3, size: 1, fx: 'crystal' } },
      { w: 2, phase: 2, spec: { t: 'strikes', d: 11, n: 5, r: 10, fx: 'mist', eff: [['blindness', 3, 0]] }, src: 'a:mist' },
    ],
  },
  'bc:storm_kraken': {
    name: '§9The Storm Kraken', src: 'a:lightning', every: [40, 65], range: 44, stars: 7, desperation: 'maelstrom',
    intro: ['§9§lTHE STORM KRAKEN', '§7The sea itself rises against you'],
    rage: ['§9§lThe Kraken calls the storm', '§7Thunder answers'],
    last: ['§9§lMAELSTROM', '§7The sea turns into a whirlpool'],
    attacks: [
      { w: 3, spec: { t: 'strikes', d: 12, n: 5, r: 10, fx: 'lightning' }, anim: 'animation.bc.storm_kraken.slam' },
      { w: 3, max: 14, tele: 16, spec: { t: 'wave', d: 14, len: 14, dirs: 4, fx: 'water', kb: [1.6, 0.9] }, src: 'a:water', anim: 'animation.bc.storm_kraken.slam' },
      { w: 2, spec: { t: 'vortex', d: 10, r: 7, dur: 3, fx: 'water' }, src: 'a:water' },
      { w: 2, spec: { t: 'prison', d: 8, r: 4, dur: 3, fx: 'bubble', eff: [['levitation', 2, 1]] }, src: 'a:bubble' },
      { w: 2, phase: 2, spec: { t: 'bolt', d: 9, n: 7, spread: 40, shape: 3, speed: 2.4, fx: 'lightning' } },
      { w: 2, fn: 'submerge' },
    ],
  },
  'bc:fallen_captain': {
    name: '§4The Fallen Captain', src: 'a:dark', every: [28, 46], range: 36, stars: 9, desperation: 'final_form', roar: 'animation.bc.fallen_captain.roar',
    intro: ['§4§lTHE FALLEN CAPTAIN', '§7A Magic Knight captain, devoured by a devil'],
    rage: ['§4§lThe Captain turns another page', '§7A second grimoire opens'],
    last: ['§4§lFINAL FORM', '§7Time itself bends to the Fallen Captain'],
    attacks: [
      { w: 4, max: 4, fn: 'combo', anim: 'animation.bc.fallen_captain.slash' },
      { w: 3, min: 5, fn: 'blink_strike' },
      { w: 4, fn: 'grimoire', anim: 'animation.bc.fallen_captain.cast' },
      { w: 1, phase: 2, fn: 'hounds', anim: 'animation.bc.fallen_captain.cast' },
    ],
  },
};
DEF['bc:frost_witch'] = {
  name: '§bThe Frost Witch', src: 'a:ice', every: [30, 50], range: 40, stars: 5, desperation: 'absolute_winter', roar: 'animation.bc.frost_witch.roar',
  intro: ['§b§lTHE WITCH SISTERS', '§7Frost and Ember, twin daughters of the long night'],
  rage: ['§b§lThe Frost Witch grows cold', '§7Her breath freezes the air'],
  last: ['§b§lABSOLUTE WINTER', '§7The world turns to ice'],
  attacks: [
    { w: 3, spec: { t: 'bolt', d: 8, n: 3, spread: 18, shape: 1, speed: 2.2, fx: 'ice', eff: [['slowness', 3, 1]] }, anim: 'animation.bc.frost_witch.cast' },
    { w: 2, spec: { t: 'prison', d: 8, r: 3, dur: 3, fx: 'ice' }, anim: 'animation.bc.frost_witch.cast' },
    { w: 2, max: 7, tele: 14, spec: { t: 'nova', d: 11, r: 6, kb: [1.6, 0.6], fx: 'ice', eff: [['slowness', 4, 2]] }, anim: 'animation.bc.frost_witch.sweep' },
    { w: 2, phase: 2, spec: { t: 'rain', d: 8, n: 12, r: 6, every: 3, fx: 'ice' }, anim: 'animation.bc.frost_witch.cast' },
    { w: 3, fn: 'twin', anim: 'animation.bc.frost_witch.cast' },
  ],
};
DEF['bc:ember_witch'] = {
  name: '§6The Ember Witch', src: 'a:flame', every: [30, 50], range: 40, stars: 5, desperation: 'inferno_requiem', roar: 'animation.bc.ember_witch.roar',
  intro: ['§6§lTHE WITCH SISTERS', '§7Frost and Ember, twin daughters of the long night'],
  rage: ['§6§lThe Ember Witch blazes', '§7Her hair becomes fire'],
  last: ['§6§lINFERNO REQUIEM', '§7The sky rains fire'],
  attacks: [
    { w: 3, spec: { t: 'bolt', d: 9, n: 3, spread: 22, shape: 2, speed: 2.0, fire: 4, fx: 'flame' }, anim: 'animation.bc.ember_witch.cast' },
    { w: 2, spec: { t: 'zone', d: 3, r: 4, dur: 4, fire: 3, fx: 'flame', at: 'aim' }, anim: 'animation.bc.ember_witch.cast' },
    { w: 2, max: 9, tele: 14, spec: { t: 'wave', d: 11, len: 12, dirs: 6, fire: 4, fx: 'flame', kb: [1.2, 0.5] }, anim: 'animation.bc.ember_witch.sweep' },
    { w: 2, phase: 2, spec: { t: 'meteor', d: 12, n: 4, r: 6, aoe: 3, fire: 5, size: 1, fx: 'flame' }, anim: 'animation.bc.ember_witch.cast' },
    { w: 3, fn: 'twin', anim: 'animation.bc.ember_witch.cast' },
  ],
};
DEF['bc:bone_dragon'] = {
  name: '§fThe Bone Dragon', src: 'a:bone', every: [30, 48], range: 52, stars: 8, desperation: 'deaths_wingbeat', roar: 'animation.bc.bone_dragon.roar',
  intro: ['§f§lTHE BONE DRAGON', '§7Death itself takes wing'],
  rage: ['§f§lThe Bone Dragon howls', '§7Green fire burns in its empty eyes'],
  last: ["§f§lDEATH'S WINGBEAT", '§7Every wingbeat is a grave'],
  attacks: [
    { w: 4, min: 4, fn: 'breath', anim: 'animation.bc.bone_dragon.breath' },
    { w: 2, max: 10, tele: 14, spec: { t: 'nova', d: 10, r: 8, kb: [2.4, 1.0], fx: 'wind' }, src: 'a:wind', anim: 'animation.bc.bone_dragon.roar' },
    { w: 3, spec: { t: 'rain', d: 9, n: 14, r: 7, every: 3, fx: 'bone' } },
    { w: 2, min: 8, fn: 'dive', anim: 'animation.bc.bone_dragon.dive' },
    { w: 3, max: 7, fn: 'tail', anim: 'animation.bc.bone_dragon.tail' },
    { w: 1, phase: 2, fn: 'bones', anim: 'animation.bc.bone_dragon.roar' },
  ],
};
const WITCHES = { 'bc:frost_witch': 'bc:ember_witch', 'bc:ember_witch': 'bc:frost_witch' };
const CAPTAIN_ATTRS = ['flame', 'lightning', 'dark', 'ice', 'blood', 'glass', 'rune', 'spirit', 'star', 'gold', 'smoke', 'magma'];

/** @type {Map<string, {next: number, phase: number, start: number, enraged: boolean, threat: Map<string, number>, target: string, moveAt: number, attrs?: string[], parryAt?: number, dodgeAt?: number, sister?: string}>} */
const bosses = new Map();

function track(e) {
  if (!DEF[e.typeId] || bosses.has(e.id)) return;
  const st = { next: system.currentTick + 60, phase: 1, start: 0, enraged: false, threat: new Map(), target: '', moveAt: system.currentTick + 400 };
  if (e.typeId === 'bc:fallen_captain') {
    const pool = [...CAPTAIN_ATTRS].sort(() => Math.random() - 0.5);
    st.attrs = [pool[0], pool[1], 'time'];
    st.parryAt = 0;
    st.dodgeAt = 0;
  }
  bosses.set(e.id, st);
}
world.afterEvents.entitySpawn.subscribe((ev) => safe(() => track(ev.entity)));
world.afterEvents.entityLoad.subscribe((ev) => safe(() => track(ev.entity)));

// ------------------------------------------------------------------------------- threat
world.afterEvents.entityHurt.subscribe((ev) => {
  const st = bosses.get(ev.hurtEntity.id);
  const src = ev.damageSource.damagingEntity;
  if (!st || !src) return;
  if (!st.start) st.start = system.currentTick;
  let amount = ev.damage;
  // brawler companions and knights in melee draw extra attention (they "tank")
  if (src.typeId === 'bc:magic_knight' && V.dist(src.location, ev.hurtEntity.location) < 5) amount *= 1.6;
  st.threat.set(src.id, (st.threat.get(src.id) ?? 0) + amount);
});

function valid(e, x, range) {
  if (!x || !alive(x) || x.dimension.id !== e.dimension.id || V.dist(x.location, e.location) > range) return false;
  if (x instanceof Player) {
    const gm = safe(() => x.getGameMode());
    return gm !== 'Creative' && gm !== 'Spectator';
  }
  return true;
}

function bossTarget(e, st, def) {
  const cur = world.getEntity(st.target);
  let best = valid(e, cur, def.range) ? cur : undefined;
  let bestThreat = best ? (st.threat.get(best.id) ?? 0) : -1;
  for (const [id, th] of st.threat) {
    const x = world.getEntity(id);
    if (!valid(e, x, def.range)) {
      if (!x) st.threat.delete(id);
      continue;
    }
    if (th > bestThreat * 1.1 + (best ? 0 : -1)) {
      best = x;
      bestThreat = th;
    }
  }
  if (!best) {
    let bd = def.range;
    for (const p of e.dimension.getPlayers({ location: e.location, maxDistance: def.range })) {
      if (!valid(e, p, def.range)) continue;
      const d = V.dist(p.location, e.location);
      if (d < bd) {
        bd = d;
        best = p;
      }
    }
    if (!best) best = safe(() => e.dimension.getEntities({ location: e.location, maxDistance: 24, families: ['bc_knight'] }))?.[0];
  }
  if (best && best.id !== st.target) {
    st.target = best.id;
    if (best instanceof Player && st.threat.size > 1) safe(() => best.onScreenDisplay.setActionBar(`${def.name}§c turns on you!`));
  }
  return best;
}

// ------------------------------------------------------------------------------- special moves
function telegraph(e, at, r, ticks) {
  particle(e.dimension, 'bc:warning_circle', V.add(at, { x: 0, y: 0.1, z: 0 }), { size: r, life: ticks / 20 + 0.2 });
  sound(e.dimension, 'random.click', at, 1.2, 0.6);
}

/** @type {Record<string, (e: any, target: any, st: any) => void>} */
const MOVES = {
  imps(e, target, st) {
    sound(e.dimension, 'bc.devil.roar', e.location, 2, 0.6);
    const n = st.phase > 1 ? 4 : 3;
    for (let i = 0; i < n; i++) {
      const type = st.phase > 1 && i === 0 ? 'bc:dark_disciple' : 'bc:imp';
      const at = V.add(e.location, { x: rand(-4, 4), y: 1, z: rand(-4, 4) });
      particle(e.dimension, 'bc:magic_circle_dark', at, { size: 2, life: 1 });
      safe(() => e.dimension.spawnEntity(type, at));
    }
  },
  slam(e, target, st) {
    telegraph(e, e.location, 7, 9);
    timer(9, () => {
      if (!alive(e)) return;
      const at = e.location;
      sound(e.dimension, 'bc.golem.slam', at, 2.5, 0.5);
      shockwave(e.dimension, at, 'earth', 7);
      particle(e.dimension, 'bc:rock_debris', at, { scale: 2 });
      shakeArea(e.dimension, at, 24, 0.7, 0.8);
      for (const v of targetsAround(e.dimension, at, 7, e)) {
        hurt(v, st.phase > 1 ? 24 : 18, e);
        knock(v, V.sub(v.location, at), 1.4, 0.9);
      }
    });
  },
  boulders(e, target, st) {
    const n = st.phase > 1 ? 3 : 2;
    for (let i = 0; i < n; i++) {
      timer(10 + i * 6, () => {
        if (!alive(e) || !alive(target)) return;
        const from = V.add(e.location, { x: 0, y: 8, z: 0 });
        launch(e, 'bc:boulder', from, V.sub(V.add(center(target), { x: rand(-1.5, 1.5), y: 0, z: rand(-1.5, 1.5) }), from), 1.5,
          { spell: 'colossus_rock', attr: 'earth', damage: 14, pierce: 0 });
      });
    }
  },
  broadside(e, target, st) {
    const n = st.phase > 1 ? 8 : 6;
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
    const count = safe(() => e.dimension.getEntities({ location: e.location, maxDistance: 48, type: 'bc:phantom_raider' }).length) ?? 0;
    if (count >= 8) return;
    sound(e.dimension, 'bc.portal', target.location, 1.5, 0.5);
    for (let i = 0; i < (st.phase > 1 ? 4 : 2); i++) {
      const at = V.add(target.location, { x: rand(-6, 6), y: 0.5, z: rand(-6, 6) });
      particle(e.dimension, 'bc:fog_cloud', at, { scale: 0.3 });
      safe(() => e.dimension.spawnEntity('bc:phantom_raider', at));
    }
  },
  submerge(e, target) {
    // dive under, become untouchable for a moment, and come up somewhere else near the prey
    anim(e, 'animation.bc.storm_kraken.submerge');
    effect(e, 'resistance', 2.5, 4, false);
    particle(e.dimension, 'bc:water_splash', e.location, { scale: 3 });
    sound(e.dimension, 'random.splash', e.location, 2, 0.5);
    timer(24, () => {
      if (!alive(e) || !alive(target)) return;
      for (let i = 0; i < 8; i++) {
        const a = Math.random() * Math.PI * 2;
        const spot = { x: target.location.x + Math.cos(a) * 9, y: target.location.y - 2, z: target.location.z + Math.sin(a) * 9 };
        const b = safe(() => e.dimension.getBlock({ x: Math.floor(spot.x), y: Math.floor(spot.y), z: Math.floor(spot.z) }));
        if (b?.typeId !== 'minecraft:water') continue;
        safe(() => e.teleport(spot));
        anim(e, 'animation.bc.storm_kraken.emerge');
        particle(e.dimension, 'bc:water_splash', V.add(spot, { x: 0, y: 2, z: 0 }), { scale: 3 });
        sound(e.dimension, 'bc.leviathan.roar', spot, 2, 0.8);
        return;
      }
    });
  },
  combo(e, target, st) {
    for (let i = 0; i < 3; i++) {
      timer(i * 7, () => {
        if (!alive(e) || !alive(target)) return;
        anim(e, 'animation.bc.fallen_captain.slash');
        const dir = V.flat(V.sub(target.location, e.location));
        safe(() => e.applyImpulse({ x: dir.x * 0.5, y: 0, z: dir.z * 0.5 }));
        particle(e.dimension, 'bc:slash_fx', V.add(e.location, { x: dir.x * 1.5, y: 1.2, z: dir.z * 1.5 }), { scale: 1 });
        sound(e.dimension, 'bc.anti.slash', e.location, 1, 0.8 + i * 0.1);
        for (const v of targetsAround(e.dimension, V.add(e.location, V.mul(dir, 1.6)), 2.4, e)) hurt(v, st.phase > 2 ? 12 : 9, e);
      });
    }
  },
  blink_strike(e, target, st) {
    const behind = V.add(target.location, V.mul(V.flat(target.getViewDirection()), -2));
    particle(e.dimension, 'bc:burst_dark', center(e), { scale: 1, color: rgb('2a0010') });
    sound(e.dimension, 'bc.portal', e.location, 1, 1.6);
    safe(() => e.teleport(behind));
    timer(6, () => {
      if (!alive(e) || !alive(target)) return;
      face(e, target);
      anim(e, 'animation.bc.fallen_captain.slash');
      particle(e.dimension, 'bc:burst_dark', center(e), { scale: 1, color: rgb('2a0010') });
      if (V.dist(e.location, target.location) < 3.5) {
        hurt(target, st.phase > 2 ? 16 : 13, e);
        knock(target, V.sub(target.location, e.location), 1.2, 0.4);
      }
    });
  },
  grimoire(e, target, st) {
    const attr = st.attrs[Math.min(st.phase, 3) - 1];
    const kit = kitFor(attr, 10);
    const spec = pick(kit.filter((s) => !['wall', 'heal', 'rewind', 'summon'].includes(s.t)));
    if (spec) castSpec(e, spec, `a:${attr}`, st.phase > 2 ? 1.5 : 1.25, target);
  },
  twin(e, target, st) {
    const sis = sisterOf(e, st);
    if (!sis) {
      // alone: a plain but furious volley
      castSpec(e, { t: 'bolt', d: 10, n: 5, spread: 30, shape: 1, speed: 2.3, fx: e.typeId === 'bc:frost_witch' ? 'ice' : 'flame' }, DEF[e.typeId].src, 1.2, target);
      return;
    }
    const frost = e.typeId === 'bc:frost_witch' ? e : sis;
    const ember = e.typeId === 'bc:ember_witch' ? e : sis;
    for (const p of e.dimension.getPlayers({ location: e.location, maxDistance: 48 })) safe(() => p.onScreenDisplay.setActionBar('§b§lTWIN SPELL §r§7- §bfrost§7 then §6fire§7. Move!'));
    anim(frost, 'animation.bc.frost_witch.cast');
    castSpec(frost, { t: 'prison', d: 8, r: 4, dur: 2.5, fx: 'ice' }, 'a:ice', 1.1, target);
    telegraph(e, target.location, 4.5, 30);
    timer(30, () => {
      if (!alive(ember) || !alive(target)) return;
      anim(ember, 'animation.bc.ember_witch.cast');
      castSpec(ember, { t: 'meteor', d: 16, n: 3, r: 2, aoe: 4, fire: 6, size: 2, fx: 'flame' }, 'a:flame', 1.25, target);
    });
  },
  breath(e, target, st) {
    face(e, target);
    sound(e.dimension, 'mob.enderdragon.growl', e.location, 2, 0.6);
    const n = st.phase > 1 ? 3 : 2;
    for (let i = 0; i < n; i++) {
      timer(8 + i * 10, () => {
        if (!alive(e) || !alive(target)) return;
        castSpec(e, { t: 'beam', d: 8, range: 26, width: 1.6, fx: 'bone', eff: [['wither', 4, 1]] }, 'a:bone', st.phase > 1 ? 1.25 : 1, target);
      });
    }
  },
  dive(e, target, st) {
    if (!alive(target)) return;
    const spot = { ...target.location };
    telegraph(e, spot, 4, 24);
    sound(e.dimension, 'mob.enderdragon.flap', e.location, 2, 0.7);
    timer(24, () => {
      if (!alive(e)) return;
      const from = { ...e.location };
      const dir = V.norm(V.sub(spot, from));
      const steps = Math.max(4, Math.min(14, Math.round(V.dist(spot, from) / 2)));
      repeat(steps, 1, (i) => {
        if (!alive(e)) return false;
        safe(() => e.teleport(V.add(from, V.mul(dir, ((i + 1) / steps) * V.dist(spot, from))), { facingLocation: spot }));
      }, () => {
        if (!alive(e)) return;
        shockwave(e.dimension, spot, 'bone', 5);
        particle(e.dimension, 'bc:rock_debris', spot, { scale: 1.6 });
        shakeArea(e.dimension, spot, 24, 0.7, 0.7);
        sound(e.dimension, 'bc.golem.slam', spot, 2, 0.7);
        for (const v of targetsAround(e.dimension, spot, 5, e)) {
          hurt(v, st.phase > 1 ? 20 : 16, e);
          knock(v, V.sub(v.location, spot), 1.6, 0.9);
        }
        safe(() => e.applyImpulse({ x: 0, y: 1.2, z: 0 }));
      });
    });
  },
  tail(e, target, st) {
    timer(8, () => {
      if (!alive(e)) return;
      sound(e.dimension, 'mob.enderdragon.flap', e.location, 2, 0.5);
      particle(e.dimension, 'bc:slash_fx', V.add(e.location, { x: 0, y: 1.5, z: 0 }), { scale: 3, color: rgb('e8e0c8') });
      for (const v of targetsAround(e.dimension, e.location, 7, e)) {
        hurt(v, st.phase > 1 ? 15 : 12, e);
        knock(v, V.sub(v.location, e.location), 2.2, 0.5);
      }
    });
  },
  bones(e, target, st) {
    const count = safe(() => e.dimension.getEntities({ location: e.location, maxDistance: 40, families: ['skeleton'] }).length) ?? 0;
    if (count >= 6) return;
    sound(e.dimension, 'mob.skeleton.say', e.location, 2, 0.6);
    for (let i = 0; i < (st.phase > 2 ? 4 : 3); i++) {
      const at = V.add(target.location, { x: rand(-6, 6), y: 0.5, z: rand(-6, 6) });
      const top = safe(() => e.dimension.getTopmostBlock({ x: at.x, z: at.z }));
      if (top && Math.abs(top.location.y + 1 - at.y) < 6) at.y = top.location.y + 1;
      particle(e.dimension, 'bc:magic_circle_dark', at, { size: 2, life: 1, color: rgb('e8e0c8') });
      timer(15, () => safe(() => e.dimension.spawnEntity(st.phase > 2 && i === 0 ? 'minecraft:wither_skeleton' : 'minecraft:skeleton', at)));
    }
  },
  hounds(e, target, st) {
    sound(e.dimension, 'bc.howl', e.location, 2, 0.6);
    for (let i = 0; i < 2; i++) {
      const at = V.add(e.location, { x: rand(-3, 3), y: 0.5, z: rand(-3, 3) });
      particle(e.dimension, 'bc:magic_circle_dark', at, { size: 2, life: 1 });
      safe(() => e.dimension.spawnEntity('bc:hellhound', at));
    }
  },
};

/** Once-only moves below 25% health. */
const DESPERATION = {
  hellgate(e, target) {
    for (let i = 0; i < 2; i++) {
      const a = Math.random() * Math.PI * 2;
      const at = V.add(e.location, { x: Math.cos(a) * 10, y: 0, z: Math.sin(a) * 10 });
      safe(() => e.dimension.spawnEntity('bc:devil_gate', at));
    }
    castSpec(e, { t: 'meteor', d: 14, n: 10, r: 12, aoe: 3.5, fire: 6, size: 2, fx: 'magma' }, 'a:magma', 1.3, target);
  },
  avalanche(e, target) {
    for (const v of targetsAround(e.dimension, e.location, 30, e).slice(0, 6)) {
      for (let i = 0; i < 3; i++) {
        timer(i * 12, () => {
          if (!alive(v)) return;
          const spot = V.add(v.location, { x: rand(-2, 2), y: 0, z: rand(-2, 2) });
          telegraph(e, spot, 2.5, 20);
          const from = V.add(spot, { x: rand(-3, 3), y: 22, z: rand(-3, 3) });
          timer(10, () => launch(e, 'bc:boulder', from, V.sub(spot, from), 1.6, { spell: 'avalanche', attr: 'earth', damage: 16, pierce: 0 }));
        });
      }
    }
    timer(40, () => alive(e) && castSpec(e, { t: 'wave', d: 14, len: 18, dirs: 12, fx: 'earth', kb: [0.3, 1.1] }, 'a:earth', 1.2, target));
  },
  ram(e, target) {
    if (!alive(target)) return;
    const from = { ...e.location };
    const to = V.add(target.location, { x: 0, y: 1, z: 0 });
    const dir = V.norm(V.sub(to, from));
    for (let s = 0; s < 28; s += 2) telegraph(e, V.add(target.location, V.mul(V.flat(dir), s - 6)), 3, 30);
    anim(e, 'animation.bc.phantom_galleon.ram');
    const hit = new Set();
    timer(30, () => {
      repeat(16, 2, (i) => {
        if (!alive(e)) return false;
        const at = V.add(from, V.mul(dir, (i + 1) * 2.2));
        safe(() => e.teleport(at));
        particle(e.dimension, 'bc:fog_cloud', at, { scale: 0.3 });
        for (const v of targetsAround(e.dimension, at, 3.5, e)) {
          if (hit.has(v.id)) continue;
          hit.add(v.id);
          hurt(v, 18, e);
          knock(v, dir, 2.0, 0.8);
        }
      });
    });
  },
  maelstrom(e, target) {
    castSpec(e, { t: 'vortex', d: 20, r: 12, dur: 5, fx: 'water' }, 'a:water', 1.2, target);
    timer(30, () => alive(e) && castSpec(e, { t: 'strikes', d: 12, n: 8, r: 14, fx: 'lightning' }, 'a:lightning', 1.2, target));
  },
  absolute_winter(e, target) {
    castSpec(e, { t: 'zone', d: 4, r: 10, dur: 6, fx: 'ice', eff: [['slowness', 3, 3]] }, 'a:ice', 1.3, target);
    for (const v of targetsAround(e.dimension, e.location, 22, e).slice(0, 6)) {
      timer(10, () => alive(v) && castSpec(e, { t: 'prison', d: 10, r: 2.5, dur: 3, fx: 'ice' }, 'a:ice', 1.2, v));
    }
    timer(50, () => alive(e) && castSpec(e, { t: 'rain', d: 10, n: 24, r: 10, every: 2, fx: 'ice' }, 'a:ice', 1.3, target));
  },
  inferno_requiem(e, target) {
    castSpec(e, { t: 'meteor', d: 16, n: 12, r: 10, aoe: 3.5, fire: 8, size: 2, fx: 'flame' }, 'a:flame', 1.3, target);
    timer(40, () => alive(e) && castSpec(e, { t: 'wave', d: 14, len: 16, dirs: 12, fire: 6, fx: 'flame', kb: [1.4, 0.6] }, 'a:flame', 1.3, target));
  },
  deaths_wingbeat(e, target) {
    if (!alive(target)) return;
    const spot = { ...target.location };
    safe(() => e.applyImpulse({ x: 0, y: 2.0, z: 0 }));
    telegraph(e, spot, 12, 40);
    for (const p of e.dimension.getPlayers({ location: spot, maxDistance: 48 })) safe(() => p.onScreenDisplay.setActionBar('§f§lThe Bone Dragon rises - get out of the circle!'));
    timer(40, () => {
      if (!alive(e)) return;
      shockwave(e.dimension, spot, 'bone', 12);
      shakeArea(e.dimension, spot, 40, 1, 1.2);
      sound(e.dimension, 'mob.enderdragon.growl', spot, 3, 0.4);
      for (const v of targetsAround(e.dimension, spot, 12, e)) {
        hurt(v, 22, e);
        effect(v, 'wither', 6, 1);
        knock(v, V.sub(v.location, spot), 2.6, 1.2);
      }
      MOVES.bones(e, target, { phase: 3 });
    });
  },
  final_form(e, target) {
    effect(e, 'strength', 600, 1, false);
    effect(e, 'speed', 600, 1, false);
    castSpec(e, { t: 'timestop', d: 12, r: 14, dur: 4 }, 'a:time', 1.3, target);
  },
};

// ------------------------------------------------------------------------------- the Witch Sisters
/** The other witch of the pair (linked once, then remembered). */
function sisterOf(e, st) {
  if (!WITCHES[e.typeId]) return undefined;
  let sis = st.sister ? world.getEntity(st.sister) : undefined;
  if (sis && alive(sis)) return sis;
  sis = safe(() => e.dimension.getEntities({ location: e.location, maxDistance: 48, type: WITCHES[e.typeId], closest: 1 }))?.[0];
  if (sis) {
    st.sister = sis.id;
    const other = bosses.get(sis.id);
    if (other) other.sister = e.id;
  }
  return sis;
}

world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const dead = ev.deadEntity;
  if (!WITCHES[dead.typeId]) return;
  const st = bosses.get(dead.id);
  const sis = st?.sister ? world.getEntity(st.sister) : undefined;
  if (!sis || !alive(sis)) return;
  const sst = bosses.get(sis.id);
  if (!sst) return;
  const def = DEF[sis.typeId];
  announce(sis, `${def.name}§c screams for her sister`, '§7Grief becomes power');
  anim(sis, def.roar);
  effect(sis, 'strength', 9999, 1, false);
  effect(sis, 'speed', 9999, 0, false);
  if (sst.phase < 3) {
    sst.phase = 3;
    timer(30, () => alive(sis) && safe(() => DESPERATION[def.desperation](sis, bossTarget(sis, sst, def))));
    sst.next = system.currentTick + 90;
  }
}, 'witchGrief'));

// ------------------------------------------------------------------------------- the Fallen Captain: parry & dodge
world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const e = ev.hurtEntity;
  if (e.typeId !== 'bc:fallen_captain') return;
  const st = bosses.get(e.id);
  const src = ev.damageSource.damagingEntity;
  if (!st || !src || ev.damageSource.cause !== 'entityAttack' || V.dist(src.location, e.location) > 4) return;
  const t = system.currentTick;
  if ((st.parryAt ?? 0) > t || Math.random() > 0.3) return;
  st.parryAt = t + 80;
  const hp = e.getComponent('minecraft:health');
  if (hp) hp.setCurrentValue(Math.min(hp.effectiveMax, hp.currentValue + ev.damage));
  anim(e, 'animation.bc.fallen_captain.parry');
  sound(e.dimension, 'random.anvil_land', e.location, 0.8, 1.8);
  particle(e.dimension, 'bc:burst_spark', center(e), { color: rgb('ffffff'), scale: 0.8 });
  hurt(src, 6, e);
  knock(src, V.sub(src.location, e.location), 1.4, 0.4);
  if (src instanceof Player) safe(() => src.onScreenDisplay.setActionBar('§cParried!'));
}, 'parry'));

function captainDodge(e, st, t) {
  if ((st.dodgeAt ?? 0) > t) return;
  const near = safe(() => e.dimension.getEntities({ location: e.location, maxDistance: 7, families: ['bc_spell'] })) ?? [];
  for (const p of near) {
    const v = safe(() => p.getVelocity());
    if (!v || V.len(v) < 0.3) continue;
    const to = V.sub(center(e), p.location);
    if (V.dot(to, v) <= 0) continue;
    if (Math.random() > 0.6) {
      st.dodgeAt = t + 20;
      return;
    }
    const side = V.flat({ x: -v.z, y: 0, z: v.x });
    const dest = V.add(e.location, V.mul(side, Math.random() < 0.5 ? 3 : -3));
    particle(e.dimension, 'bc:burst_dark', center(e), { scale: 0.6, color: rgb('2a0010') });
    safe(() => e.teleport(dest));
    st.dodgeAt = t + 50;
    return;
  }
}

// ------------------------------------------------------------------------------- the loop
function announce(e, main, sub) {
  for (const p of e.dimension.getPlayers({ location: e.location, maxDistance: 56 })) title(p, main, sub, 50);
}

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
      const target = bossTarget(e, st, def);
      // movement
      if (e.typeId === 'bc:phantom_galleon' && target) {
        const want = V.add(target.location, V.mul(V.flat(V.sub(e.location, target.location)), 14));
        want.y = target.location.y + 11;
        const d = V.sub(want, e.location);
        if (V.len(d) > 3) safe(() => e.applyImpulse(V.mul(V.norm(d), 0.12)));
      }
      if (e.typeId === 'bc:bone_dragon' && target) {
        // circle above the prey
        const ang = (t / 120) % (Math.PI * 2);
        const want = V.add(target.location, { x: Math.cos(ang) * 12, y: 9, z: Math.sin(ang) * 12 });
        const d = V.sub(want, e.location);
        if (V.len(d) > 3) safe(() => e.applyImpulse(V.mul(V.norm(d), 0.1)));
      }
      if (e.typeId === 'bc:fallen_captain') captainDodge(e, st, t);
      if (target && t > st.moveAt) {
        const crowd = targetsAround(e.dimension, e.location, 5, e).length;
        if (WITCHES[e.typeId] && crowd >= 1) {
          st.moveAt = t + 200;
          particle(e.dimension, 'bc:burst_dark', center(e), { scale: 1.2, color: rgb(COLORS[e.typeId]) });
          sound(e.dimension, 'bc.portal', e.location, 1, 1.4);
          const a = Math.random() * Math.PI * 2;
          safe(() => e.teleport(V.add(target.location, { x: Math.cos(a) * 9, y: 3, z: Math.sin(a) * 9 })));
        } else if (e.typeId === 'bc:archdevil' && crowd >= 2) {
          st.moveAt = t + 300;
          anim(e, 'animation.bc.archdevil.blink');
          particle(e.dimension, 'bc:burst_dark', center(e), { scale: 2, color: rgb('2a0010') });
          const a = Math.random() * Math.PI * 2;
          timer(8, () => alive(e) && safe(() => e.teleport(V.add(target.location, { x: Math.cos(a) * 11, y: 4, z: Math.sin(a) * 11 }))));
        } else if (e.typeId === 'bc:stone_colossus' && crowd >= 2) {
          st.moveAt = t + 240;
          anim(e, 'animation.bc.stone_colossus.stomp');
          telegraph(e, e.location, 6, 10);
          timer(10, () => {
            if (!alive(e)) return;
            shockwave(e.dimension, e.location, 'earth', 6);
            for (const v of targetsAround(e.dimension, e.location, 6, e)) knock(v, V.sub(v.location, e.location), 2.4, 0.6);
          });
        }
      }
      // phases
      const hp = e.getComponent('minecraft:health');
      const frac = hp ? hp.currentValue / hp.effectiveMax : 1;
      if (st.phase === 1 && frac < 0.5) {
        st.phase = 2;
        if (def.roar) anim(e, def.roar);
        sound(e.dimension, e.typeId === 'bc:storm_kraken' ? 'ambient.weather.thunder' : 'bc.devil.roar', e.location, 3, 0.5);
        shakeArea(e.dimension, e.location, 40, 0.6, 1.2);
        announce(e, def.rage[0], def.rage[1]);
        effect(e, 'strength', 600, 1, false);
        effect(e, 'resistance', 600, 0, false);
        if (e.typeId === 'bc:storm_kraken') safe(() => e.dimension.setWeather(WeatherType.Thunder, 6000));
      } else if (st.phase === 2 && frac < 0.25) {
        st.phase = 3;
        if (def.roar) anim(e, def.roar);
        announce(e, def.last[0], def.last[1]);
        sound(e.dimension, 'bc.gong', e.location, 3, 0.6);
        shakeArea(e.dimension, e.location, 40, 0.8, 1.4);
        timer(20, () => alive(e) && safe(() => DESPERATION[def.desperation](e, target ?? bossTarget(e, st, def))));
        st.next = t + 80;
      }
      // the enrage timer
      if (!st.enraged && st.start && t - st.start > 20 * 360) {
        st.enraged = true;
        announce(e, `${def.name}§c grows furious`, '§7You took too long');
        effect(e, 'strength', 9999, 2, false);
        effect(e, 'speed', 9999, 1, false);
      }
      if (!target || st.next > t) return;
      const d = V.dist(target.location, e.location);
      const pool = def.attacks.filter((a) => (a.phase ?? 1) <= st.phase && d >= (a.min ?? 0) && d <= (a.max ?? 99));
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
      const pw = (st.phase > 1 ? 1.25 : 1.0) * (st.phase > 2 ? 1.15 : 1) * (st.enraged ? 1.4 : 1);
      const go = () => {
        if (!alive(e)) return;
        if (atk.fn) MOVES[atk.fn](e, target, st);
        else castSpec(e, atk.spec, atk.src ?? def.src, pw, target);
      };
      if (atk.tele) {
        telegraph(e, atk.spec?.at === 'aim' ? target.location : e.location, atk.spec?.r ?? 6, atk.tele);
        timer(atk.tele, go);
      } else go();
      const [lo, hi] = def.every;
      st.next = t + Math.round(rand(lo, hi) * (st.phase > 1 ? 0.75 : 1) * (st.phase > 2 ? 0.85 : 1) * (st.enraged ? 0.7 : 1));
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
  const killerOwner = killer ? world.getEntity(ownerOf(killer)) : undefined;
  for (const p of dim.getPlayers({ location: loc, maxDistance: 64 })) {
    title(p, '§6§lBOSS DEFEATED', `${def.name}§7 has fallen`, 70);
    const mine = p === killer || p === killerOwner;
    addXp(p, mine ? 400 : 200);
    emit('boss', p, e.typeId);
    safe(() => addStars(p, mine ? def.stars : Math.ceil(def.stars / 2), `${def.name.replace(/§./g, '')} defeated`));
  }
  if (e.typeId === 'bc:storm_kraken') safe(() => dim.setWeather(WeatherType.Clear, 6000));
  bosses.delete(e.id);
}, 'bossDie'));

// ------------------------------------------------------------------------------- summoning
const COLORS = { 'bc:archdevil': 'd01a34', 'bc:stone_colossus': 'ff8a2a', 'bc:phantom_galleon': '96ffdc', 'bc:storm_kraken': '9ae8ff', 'bc:fallen_captain': 'b0101a',
  'bc:frost_witch': '9ae8ff', 'bc:ember_witch': 'ff7a2a', 'bc:bone_dragon': 'e8e0c8' };
const FLYERS = { 'bc:phantom_galleon': 10, 'bc:bone_dragon': 7, 'bc:frost_witch': 2, 'bc:ember_witch': 2 };

/** Raise a boss in front of a location with a short ceremony. */
export function summonBoss(type, dim, loc, players = [], opts = {}) {
  if (type === 'twins') {
    // the Witch Sisters arrive together, side by side
    const side = { x: 3, y: 0, z: 0 };
    summonBoss('bc:frost_witch', dim, V.sub(loc, side), players);
    summonBoss('bc:ember_witch', dim, V.add(loc, side), players, { quiet: true });
    return;
  }
  const def = DEF[type];
  if (!def) return;
  const color = COLORS[type];
  sound(dim, type === 'bc:phantom_galleon' ? 'bc.ship.bell' : 'bc.gong', loc, 3, 0.6);
  repeat(10, 10, (i) => {
    particle(dim, type === 'bc:archdevil' || type === 'bc:fallen_captain' ? 'bc:magic_circle_dark' : 'bc:magic_circle_ground', V.add(loc, { x: 0, y: 0.1, z: 0 }),
      { color: rgb(color), size: 4 + i * 0.6, life: 0.7 });
    if (type === 'bc:stone_colossus') {
      particle(dim, 'bc:rock_debris', V.add(loc, { x: rand(-3, 3), y: 0.5, z: rand(-3, 3) }), { scale: 1.2 });
      shakeArea(dim, loc, 30, 0.4, 0.5);
    } else if (type === 'bc:phantom_galleon') particle(dim, 'bc:fog_cloud', loc, { scale: 0.6 });
    else particle(dim, 'bc:pillar', loc, { color: rgb(color), scale: 1.5 });
  }, () => {
    const at = V.add(loc, { x: 0, y: FLYERS[type] ?? 0, z: 0 });
    const e = safe(() => dim.spawnEntity(type, at));
    if (!e) return;
    track(e);
    shockwave(dim, loc, 'flame', 8);
    if (def.roar) anim(e, def.roar);
    const roar = { 'bc:storm_kraken': 'bc.leviathan.roar', 'bc:stone_colossus': 'bc.golem.slam', 'bc:bone_dragon': 'mob.enderdragon.growl', 'bc:frost_witch': 'bc.ice.form', 'bc:ember_witch': 'bc.chord' };
    sound(dim, roar[type] ?? 'bc.devil.roar', loc, 3, 0.5);
    if (!opts.quiet) for (const p of dim.getPlayers({ location: loc, maxDistance: 64 })) title(p, def.intro[0], def.intro[1], 60);
    if (type === 'bc:archdevil' || type === 'bc:fallen_captain') for (const p of players) effect(p, 'darkness', 4, 0, false);
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
  'bc:fallen_seal': 'bc:fallen_captain',
  'bc:twin_moon_charm': 'twins',
  'bc:bone_totem': 'bc:bone_dragon',
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
    loc = V.add(p.location, V.mul(dir, type === 'bc:stone_colossus' || type === 'bc:bone_dragon' ? 12 : 9));
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
  const who = type === 'twins' ? '§bThe Witch §6Sisters§7 are' : `${DEF[type].name}§7 is`;
  safe(() => p.sendMessage(`§7Something answers the call... ${who} coming.`));
  summonBoss(type, p.dimension, loc, [p]);
  return true;
}

export { DATA };
