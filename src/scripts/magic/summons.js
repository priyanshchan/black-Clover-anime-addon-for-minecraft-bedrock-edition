// Long-lived spell entities driven by script: tornado, black hole, ice prison.
import { Player, system, world } from '@minecraft/server';
import { HOSTILE_PROJECTILES, center, effect, groundBelow, hurt, knock, knockFrom, projectiles, pull, targetsAround } from '../core/combat.js';
import { COLORS, burst, particle, rgb, shockwave, sound } from '../core/fx.js';
import { V, alive, safe } from '../core/util.js';

/** @type {Set<{tick:(t:number)=>boolean}>} */
const active = new Set();
/** ids of spell entities currently driven by a tracker */
const trackedIds = new Set();

function despawn(e) {
  trackedIds.delete(e.id);
  safe(() => e.triggerEvent('bc:expire'));
  safe(() => e.remove());
}

export function trackTornado(e, owner, dir, dmg, life) {
  trackedIds.add(e.id);
  let age = 0;
  const dim = e.dimension;
  active.add({
    tick() {
      if (!alive(e) || age++ > life) {
        if (alive(e)) {
          const l = e.location;
          particle(dim, 'bc:wind_burst', l, { scale: 1.2 });
          for (const t of targetsAround(dim, l, 5, owner)) knockFrom(t, l, 2.0, 0.9);
          despawn(e);
        }
        return false;
      }
      const loc = e.location;
      const next = groundBelow(dim, V.add(loc, { x: dir.x * 0.24, y: 2, z: dir.z * 0.24 }), 5);
      safe(() => e.teleport(next));
      if (age % 3 === 0) {
        for (const t of targetsAround(dim, V.add(next, { x: 0, y: 1.5, z: 0 }), 5.5, owner)) {
          pull(t, V.add(next, { x: 0, y: 2.5, z: 0 }), 1.2);
          if (t instanceof Player) knock(t, { x: 0, y: 0, z: 0 }, 0, 0.25);
          else safe(() => t.applyImpulse({ x: 0, y: 0.18, z: 0 }));
        }
      }
      if (age % 10 === 0) {
        for (const t of targetsAround(dim, V.add(next, { x: 0, y: 1.5, z: 0 }), 2.8, owner)) hurt(t, dmg * 0.5, owner, 'entityAttack');
        sound(dim, 'bc.wind.gust', next, 0.6, 0.8 + Math.random() * 0.4);
      }
      return true;
    },
  });
}

export function trackBlackHole(e, owner, dmg, life) {
  trackedIds.add(e.id);
  let age = 0;
  const dim = e.dimension;
  const core = V.add(e.location, { x: 0, y: 0.75, z: 0 });
  active.add({
    tick() {
      if (!alive(e) || age++ > life) {
        if (alive(e)) {
          burst(dim, core, 'dark', 2);
          shockwave(dim, core, 'dark', 6);
          sound(dim, 'bc.spell.impact', core, 1.4, 0.6);
          for (const t of targetsAround(dim, core, 4.5, owner)) {
            hurt(t, dmg * 2.2, owner, 'magic');
            knockFrom(t, core, 1.5, 0.6);
          }
          despawn(e);
        }
        return false;
      }
      for (const t of targetsAround(dim, core, 9, owner)) pull(t, core, 0.9);
      // devour hostile magic and projectiles
      safe(() => {
        for (const x of dim.getEntities({ location: core, maxDistance: 8 })) {
          const meta = projectiles.get(x.id);
          const mine = meta && meta.owner === owner.id;
          if ((x.matches({ families: ['bc_spell'] }) && !mine && x.id !== e.id && !['bc:black_hole', 'bc:tornado', 'bc:ice_prison'].includes(x.typeId))
            || HOSTILE_PROJECTILES.includes(x.typeId)) {
            particle(dim, 'bc:burst_dark', x.location, { scale: 0.5, color: rgb('2a1040') });
            x.remove();
          }
        }
      });
      if (age % 10 === 0) {
        for (const t of targetsAround(dim, core, 2.8, owner)) {
          hurt(t, dmg, owner, 'magic');
          effect(t, 'wither', 2, 0);
        }
        sound(dim, 'mob.endermen.portal', core, 0.5, 0.5);
      }
      return true;
    },
  });
}

export function trackPrison(e, victim, owner, dmg, life) {
  trackedIds.add(e.id);
  let age = 0;
  const dim = e.dimension;
  const hold = victim.location;
  active.add({
    tick() {
      if (!alive(e) || age++ > life || !alive(victim)) {
        if (alive(e)) {
          particle(dim, 'bc:ice_shatter', V.add(e.location, { x: 0, y: 1, z: 0 }), { scale: 1.2 });
          sound(dim, 'random.glass', e.location, 1, 0.8);
          if (alive(victim)) hurt(victim, dmg, owner, 'freezing');
          despawn(e);
        }
        return false;
      }
      if (!(victim instanceof Player)) safe(() => victim.teleport(hold, { keepVelocity: false }));
      safe(() => e.teleport(victim.location));
      return true;
    },
  });
}

system.runInterval(() => {
  for (const a of [...active]) {
    const ok = safe(() => a.tick(system.currentTick), 'summon');
    if (!ok) active.delete(a);
  }
}, 1);

/** Clean up orphaned static spell entities after a reload (their trackers are gone). */
world.afterEvents.playerSpawn.subscribe((ev) => {
  if (!ev.initialSpawn) return;
  system.runTimeout(() => safe(() => {
    for (const x of ev.player.dimension.getEntities({ location: ev.player.location, maxDistance: 96, families: ['bc_spell'] })) {
      if (['bc:black_hole', 'bc:tornado', 'bc:ice_prison'].includes(x.typeId) && !trackedIds.has(x.id)) x.remove();
    }
  }), 40);
});

export { COLORS, center };
