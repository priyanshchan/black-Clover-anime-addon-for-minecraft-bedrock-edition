// The Crowned Vessel (v1.3.0): a captain of Magic Knights who gave his body to Vaelgrim, the Crowned Abyss - a higher-rank
// devil. It waits in Underworld Breaches in the far, dangerous lands, or answers an Abyssal Crown raised at night.
// Its union deepens with the fight: at half health Vaelgrim's horns break through the crown and both arms turn (50%);
// at a quarter it spreads its wings and the halo burns (100%) - and the underworld falls on you. Beat it and Vaelgrim's
// own Pact Sigil is yours.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { emit } from '../core/bus.js';
import { center, effect, hurt, knock, targetsAround } from '../core/combat.js';
import { anim, particle, shakeArea, sound, title } from '../core/fx.js';
import * as vfx from '../core/vfx.js';
import { V, alive, isCreative, rand, safe, timer } from '../core/util.js';
import { castSpec } from './engine.js';
import { face } from './knights.js';
import { registerBoss, summonBoss, telegraph } from './bosses.js';
import { night } from './events.js';
import { inCapital } from './capital.js';
import { spawnHost } from './devilhosts.js';

const D = DATA.devils.vaelgrim;
const COL = 'ff2a4a';
const [LANCE, DOMINION, ABYSS] = D.moves.map((m) => m.spec);
const SRC = `a:${D.attr}`;

registerBoss('bc:crowned_vessel', {
  name: '§4§lThe Crowned Vessel', src: SRC, every: [26, 44], range: 40, stars: 9, desperation: 'crowned_abyss', roar: 'animation.bc.crowned_vessel.roar',
  intro: ['§4§lTHE CROWNED VESSEL', '§7A knight-captain who gave himself to a lord of the underworld'],
  rage: ['§4§l50% UNION', '§7Vaelgrim\'s horns break through the crown'],
  last: ['§4§lFULL UNION', '§7Vaelgrim, the Crowned Abyss, walks the world'],
  attacks: [
    { w: 4, max: 5, fn: 'vessel_slash', anim: 'animation.bc.crowned_vessel.slash' },
    { w: 3, min: 4, spec: LANCE, anim: 'animation.bc.crowned_vessel.cast' },
    { w: 2, max: 10, tele: 14, spec: DOMINION, anim: 'animation.bc.crowned_vessel.roar' },
    { w: 2, min: 6, fn: 'vessel_blink' },
    { w: 2, phase: 2, fn: 'vessel_hosts', anim: 'animation.bc.crowned_vessel.cast' },
    { w: 2, phase: 2, spec: { t: 'vortex', d: 12, r: 7, dur: 2.5, fx: 'devil' }, anim: 'animation.bc.crowned_vessel.cast' },
    { w: 2, phase: 3, spec: ABYSS, anim: 'animation.bc.crowned_vessel.roar' },
  ],
}, {
  color: COL,
  moves: {
    vessel_slash(e, target) {
      timer(6, () => {
        if (!alive(e)) return;
        const fwd = V.flat(e.getViewDirection());
        const at = V.add(e.location, V.mul(fwd, 2.2));
        vfx.slash(e.dimension, V.add(at, { x: 0, y: 1.6, z: 0 }), vfx.hex(COL), 3.4);
        sound(e.dimension, 'bc.anti.slash', at, 1.2, 0.6);
        for (const v of targetsAround(e.dimension, at, 3.4, e)) {
          hurt(v, 14, e);
          knock(v, V.sub(v.location, e.location), 1.4, 0.4);
        }
      });
    },
    vessel_blink(e, target) {
      if (!target) return;
      const back = V.flat(target.getViewDirection());
      const at = V.add(target.location, V.mul(back, -2.5));
      particle(e.dimension, 'bc:burst_dark', center(e), { scale: 1.4, color: vfx.hex(COL) });
      sound(e.dimension, 'bc.portal', e.location, 1, 0.8);
      safe(() => e.teleport(at));
      face(e, target);
      anim(e, 'animation.bc.crowned_vessel.slash');
      timer(8, () => {
        if (!alive(e) || !alive(target)) return;
        vfx.slash(e.dimension, V.add(target.location, { x: 0, y: 1.2, z: 0 }), vfx.hex(COL), 2.6);
        if (V.dist(target.location, e.location) < 4) hurt(target, 12, e);
      });
    },
    vessel_hosts(e) {
      // lesser devils answer their lord - in borrowed bodies
      sound(e.dimension, 'bc.devil.roar', e.location, 2, 1.2);
      for (let i = 0; i < 2; i++) {
        const a = Math.random() * Math.PI * 2;
        const at = V.add(e.location, { x: Math.cos(a) * 4, y: 0.3, z: Math.sin(a) * 4 });
        particle(e.dimension, 'bc:magic_circle_dark', at, { size: 2, life: 1, color: vfx.hex(COL) });
        timer(14, () => alive(e) && spawnHost(e.dimension, at, 'lesser'));
      }
    },
  },
  desperation: {
    crowned_abyss(e, target) {
      if (!alive(e)) return;
      shakeArea(e.dimension, e.location, 48, 0.8, 1.6);
      for (let i = 0; i < 3; i++) {
        timer(12 + i * 26, () => {
          if (!alive(e)) return;
          const t = target && alive(target) ? target : undefined;
          if (t) face(e, t);
          anim(e, 'animation.bc.crowned_vessel.roar');
          castSpec(e, ABYSS, SRC, 1.1 + i * 0.15, t);
        });
      }
    },
  },
});

/** Set the Vessel's union (0, 1, 2) - its horns, arms, wings and halo show by property. */
function setUnion(e, stage) {
  const cur = Number(safe(() => e.getDynamicProperty('bc:union')) ?? 0);
  if (cur >= stage) return false;
  safe(() => e.setDynamicProperty('bc:union', stage));
  safe(() => e.setProperty('bc:union', stage));
  const col = vfx.hex(COL);
  vfx.ground(e.dimension, e.location, 'devil', col, stage === 2 ? 8 : 5);
  vfx.swirl(e.dimension, e.location, col, 2, 1.4, stage === 2 ? 2.2 : 1.5);
  particle(e.dimension, 'bc:burst_dark', center(e), { scale: 2.2, color: col });
  if (stage === 2) {
    effect(e, 'slow_falling', 9999, 0, false);
    for (const p of e.dimension.getPlayers({ location: e.location, maxDistance: 56 })) effect(p, 'darkness', 3, 0, false);
  }
  return true;
}
system.runInterval(() => {
  const t = system.currentTick;
  for (const p of world.getAllPlayers()) {
    for (const e of safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 64, type: 'bc:crowned_vessel' })) ?? []) safe(() => {
      const hp = e.getComponent('minecraft:health');
      const frac = hp ? hp.currentValue / hp.effectiveMax : 1;
      if (frac < 0.5) setUnion(e, 1);
      if (frac < 0.25) setUnion(e, 2);
      if (Number(safe(() => e.getDynamicProperty('bc:union')) ?? 0) >= 2 && t % 20 === 0) vfx.aura(e.dimension, e.location, vfx.hex(COL), 0.8);
    });
  }
}, 10);

// it falls: Vaelgrim lets go, and leaves its sigil for whoever was strong enough
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const e = ev.deadEntity;
  if (e.typeId !== 'bc:crowned_vessel') return;
  const loc = e.location;
  safe(() => e.dimension.spawnItem(new ItemStack('bc:pact_vaelgrim', 1), loc));
  for (const p of e.dimension.getPlayers({ location: loc, maxDistance: 48 })) {
    emit('vessel', p);
    safe(() => p.sendMessage(`${D.mc}${D.name}§7: "You broke my vessel. Good." §8(Its Pact Sigil lies where the Vessel fell.)`));
  }
}, 'vesselDie'));

/** Raise the Abyssal Crown: at night, the Crowned Vessel answers. */
export function raiseCrown(p) {
  if (!night() && !isCreative(p)) {
    safe(() => p.onScreenDisplay.setActionBar('§4The crown is cold. §7Raise it at night.'));
    return false;
  }
  if (inCapital(p.location)) {
    safe(() => p.onScreenDisplay.setActionBar('§7Not inside the Capital\'s walls.'));
    return false;
  }
  const at = V.add(p.location, V.mul(V.flat(p.getViewDirection()), 10));
  at.y = p.location.y;
  summonBoss('bc:crowned_vessel', p.dimension, at, [p]);
  safe(() => p.sendMessage('§4The crown grows heavy in your hands... §7and something answers.'));
  return true;
}

export { rand, Player };
