// Raider Captains: named pirates who each carry an Abyss Fruit power and use it in battle.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { anim, particle, rgb, sound } from '../core/fx.js';
import { V, alive, pick, safe } from '../core/util.js';
import { castAbility, isSealed } from './fruits.js';

/** @type {Map<string, number>} captain id -> tick of next ability */
const captains = new Map();

export function captainName() {
  return `Captain ${pick(DATA.captainFirst)}${pick(DATA.captainLast)}`;
}

/**
 * @param {import('@minecraft/server').Dimension} dim
 * @param {{x:number,y:number,z:number}} loc
 * @param {{name?: string, fruit?: string, bountyFor?: string}} [opts]
 */
export function spawnCaptain(dim, loc, opts = {}) {
  const e = safe(() => dim.spawnEntity('bc:raider_captain', loc));
  if (!e) return undefined;
  const fruit = opts.fruit ?? pick(DATA.fruitOrder);
  const name = opts.name ?? captainName();
  const f = DATA.fruits[fruit];
  safe(() => {
    e.setDynamicProperty('bc:fruit', fruit);
    e.nameTag = `§c${name} ${f.glyph}`;
    if (opts.bountyFor) e.addTag(`bc_bounty:${opts.bountyFor}`);
  });
  captains.set(e.id, system.currentTick + 60);
  particle(dim, 'bc:magic_circle_ground', loc, { color: rgb(f.color), size: 3, life: 1.2 });
  return e;
}

function nearestTarget(e) {
  let best;
  let bd = 18;
  for (const p of e.dimension.getPlayers({ location: e.location, maxDistance: 18 })) {
    const gm = safe(() => p.getGameMode());
    if (gm === 'Creative' || gm === 'Spectator') continue;
    const d = V.dist(p.location, e.location);
    if (d < bd) {
      bd = d;
      best = p;
    }
  }
  return best;
}

world.afterEvents.entityLoad.subscribe((ev) => {
  if (ev.entity.typeId === 'bc:raider_captain' && !captains.has(ev.entity.id)) captains.set(ev.entity.id, system.currentTick + 60);
});

system.runInterval(() => {
  const t = system.currentTick;
  for (const [id, next] of captains) {
    const e = world.getEntity(id);
    if (!e) {
      captains.delete(id);
      continue;
    }
    if (next > t) continue;
    safe(() => {
      const fruit = e.getDynamicProperty('bc:fruit');
      if (typeof fruit !== 'string' || isSealed(e)) return;
      const target = nearestTarget(e);
      if (!target) return;
      const abilities = DATA.fruits[fruit].abilities.map((a) => a.id).filter((a) => a !== 'healing_pollen' || Math.random() < 0.3);
      const ab = pick(abilities);
      anim(e, 'animation.bc.raider_captain.cast');
      safe(() => e.setRotation({ x: 0, y: (Math.atan2(-(target.location.x - e.location.x), target.location.z - e.location.z) * 180) / Math.PI }));
      castAbility(e, fruit, ab, target);
      captains.set(id, t + 70 + Math.floor(Math.random() * 50));
    }, 'captain');
  }
}, 10);

// melee swing animation for pirates
world.afterEvents.entityHitEntity.subscribe((ev) => {
  const a = ev.damagingEntity;
  if (a.typeId === 'bc:sea_raider') anim(a, 'animation.bc.sea_raider.attack');
  else if (a.typeId === 'bc:raider_captain') anim(a, 'animation.bc.raider_captain.attack');
});

// captains sometimes drop the fruit they ate
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const e = ev.deadEntity;
  if (e.typeId !== 'bc:raider_captain') return;
  const fruit = e.getDynamicProperty('bc:fruit');
  if (typeof fruit === 'string' && Math.random() < 0.35) {
    e.dimension.spawnItem(new ItemStack(`bc:fruit_${fruit}`, 1), e.location);
    particle(e.dimension, 'bc:burst', e.location, { color: rgb(DATA.fruits[fruit].color), scale: 1 });
    const k = ev.damageSource.damagingEntity;
    if (k instanceof Player) safe(() => k.sendMessage(`${DATA.fruits[fruit].glyph} §fThe captain's ${DATA.fruits[fruit].mc}${DATA.fruits[fruit].name}§f rolls free!`));
  }
  sound(e.dimension, 'bc.coins', e.location, 1, 1);
}, 'captainDie'));

export { alive };
