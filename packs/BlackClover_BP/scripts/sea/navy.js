// Notoriety (your own bounty) and the Tidewatch: an original naval order that hunts infamous players.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { MessageFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { center, foeOf, hurt, knock, knockFrom, targetsAround } from '../core/combat.js';
import { anim, particle, shakeArea, sound, title } from '../core/fx.js';
import { V, rand, safe, timer } from '../core/util.js';

const GAIN = { 'bc:raider_captain': 80, 'bc:tidewatch_sentinel': 120, 'bc:tidewatch_commodore': 600, 'bc:devil': 500, 'bc:leviathan': 400, 'bc:sail_ship': 150 };
const nextHunt = new Map();
/** @type {Map<string, {next: number}>} */
const commodores = new Map();

export function notoriety(p) {
  const v = p.getDynamicProperty('bc:notoriety');
  return typeof v === 'number' ? v : 0;
}

function tier(n) {
  let t = -1;
  DATA.notoriety.forEach((x, i) => {
    if (n >= x.bounty) t = i;
  });
  return t;
}

export function notorietyTitle(p) {
  const t = tier(notoriety(p));
  return t < 0 ? 'Unknown' : DATA.notoriety[t].title;
}

export function addNotoriety(p, amount) {
  const before = tier(notoriety(p));
  const total = notoriety(p) + amount;
  p.setDynamicProperty('bc:notoriety', total);
  const after = tier(total);
  if (after > before) {
    const t = DATA.notoriety[after];
    title(p, `§c§lWANTED: ${total} DOUBLOONS`, `§7You are now known as a §c${t.title}§7. The Tidewatch is coming.`, 70);
    sound(p.dimension, 'bc.ship.bell', p.location, 1, 0.7);
    const poster = new ItemStack('bc:wanted_poster', 1);
    safe(() => poster.setLore([`§cWANTED: §f${p.name}`, `§7${t.title}`, `§e${total} doubloons`]));
    const left = p.getComponent('minecraft:inventory')?.container?.addItem(poster);
    if (left) p.dimension.spawnItem(left, p.location);
  }
}

world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const k = ev.damageSource.damagingEntity;
  if (!(k instanceof Player)) return;
  const g = GAIN[safe(() => ev.deadEntity.typeId) ?? ''];
  if (g) addNotoriety(k, g);
}, 'notoriety'));

export async function showPoster(p) {
  const n = notoriety(p);
  await new MessageFormData().title('§cWANTED')
    .body(`§f${p.name}\n§7${notorietyTitle(p)}\n\n§eBounty: ${n} doubloons\n\n§7Defeating captains, the Tidewatch, devils and the Leviathan raises your bounty. `
      + 'Above 300, Tidewatch squads start hunting you; higher bounties bring Commodores.')
    .button1('Close').button2('Close').show(p);
}

// ------------------------------------------------------------------------------- hunting squads
function surface(dim, x, z) {
  for (let y = 120; y > 40; y--) {
    const b = safe(() => dim.getBlock({ x, y, z }));
    if (!b) return undefined;
    if (b.isAir) continue;
    if (b.isLiquid || b.typeId.endsWith('_leaves')) return undefined;
    return y + 1;
  }
  return undefined;
}

function sendSquad(p, t) {
  const dim = p.dimension;
  const a = Math.random() * Math.PI * 2;
  const x = Math.floor(p.location.x + Math.cos(a) * rand(18, 26));
  const z = Math.floor(p.location.z + Math.sin(a) * rand(18, 26));
  const y = surface(dim, x, z);
  if (y === undefined) return false;
  const at = { x: x + 0.5, y, z: z + 0.5 };
  particle(dim, 'bc:smoke_burst', at, { scale: 1 });
  const sentinels = 2 + t;
  for (let i = 0; i < sentinels; i++) safe(() => dim.spawnEntity('bc:tidewatch_sentinel', V.add(at, { x: rand(-2, 2), y: 0, z: rand(-2, 2) })));
  const officers = t >= 3 ? 2 : t >= 1 ? 1 : 0;
  for (let i = 0; i < officers; i++) {
    const c = safe(() => dim.spawnEntity('bc:tidewatch_commodore', V.add(at, { x: rand(-1, 1), y: 0, z: rand(-1, 1) })));
    if (c) commodores.set(c.id, { next: system.currentTick + 100 });
  }
  safe(() => p.onScreenDisplay.setActionBar('§9§lThe Tidewatch has found you!'));
  sound(dim, 'bc.ship.bell', at, 1.4, 1.2);
  return true;
}

system.runInterval(() => {
  const now = system.currentTick;
  for (const p of world.getAllPlayers()) {
    safe(() => {
      if (p.dimension.id !== 'minecraft:overworld') return;
      const gm = p.getGameMode();
      if (gm === 'Creative' || gm === 'Spectator') return;
      const t = tier(notoriety(p));
      if (t < 0 || (nextHunt.get(p.id) ?? 0) > now) return;
      if (Math.random() > 0.25 + t * 0.1) return;
      if (sendSquad(p, t)) nextHunt.set(p.id, now + 20 * 60 * 6);
    }, 'hunt');
  }
}, 1200);

// ------------------------------------------------------------------------------- the Commodore
world.afterEvents.entityLoad.subscribe((ev) => {
  if (ev.entity.typeId === 'bc:tidewatch_commodore' && !commodores.has(ev.entity.id)) commodores.set(ev.entity.id, { next: system.currentTick + 100 });
});

system.runInterval(() => {
  const now = system.currentTick;
  for (const [id, st] of commodores) {
    const e = world.getEntity(id);
    if (!e) {
      commodores.delete(id);
      continue;
    }
    if (st.next > now) continue;
    safe(() => {
      const target = foeOf(e, 24);
      if (!target) return;
      st.next = now + 140 + Math.floor(rand(0, 60));
      anim(e, 'animation.bc.tidewatch_commodore.cast');
      // call down a bombardment from the fleet
      for (let i = 0; i < 4; i++) {
        const spot = V.add(target.location, { x: rand(-4, 4), y: 0, z: rand(-4, 4) });
        particle(e.dimension, 'bc:warning_circle', spot, { size: 3, life: 1.2 });
        timer(24 + i * 5, () => {
          particle(e.dimension, 'bc:flame_burst', spot, { scale: 0.9 });
          particle(e.dimension, 'bc:smoke_burst', spot, { scale: 0.9 });
          sound(e.dimension, 'bc.cannon', spot, 1.2, 1.1);
          shakeArea(e.dimension, spot, 10, 0.3, 0.4);
          for (const v of targetsAround(e.dimension, spot, 2.8, e)) {
            if (v.typeId === 'bc:tidewatch_sentinel' || v.typeId === 'bc:tidewatch_commodore') continue;
            hurt(v, 10, e, 'entityExplosion');
            knockFrom(v, spot, 1.2, 0.5);
          }
        });
      }
    }, 'commodore');
  }
}, 10);

// officers trained in Will: they sometimes sidestep hits and their strikes land harder
world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const e = ev.hurtEntity;
  if (e.typeId !== 'bc:tidewatch_commodore' || Math.random() > 0.22) return;
  const hp = e.getComponent('minecraft:health');
  if (!hp || hp.currentValue <= 0) return;
  safe(() => hp.setCurrentValue(Math.min(hp.effectiveMax, hp.currentValue + ev.damage)));
  const att = ev.damageSource.damagingEntity;
  const away = att ? V.sub(e.location, att.location) : { x: 1, y: 0, z: 0 };
  knock(e, { x: -away.z, y: 0, z: away.x }, 0.9, 0.1);
  particle(e.dimension, 'bc:will_spark', center(e), { scale: 0.6 });
}, 'commodoreDodge'));

world.afterEvents.entityHitEntity.subscribe((ev) => safe(() => {
  const a = ev.damagingEntity;
  if (a.typeId === 'bc:tidewatch_sentinel' || a.typeId === 'bc:tidewatch_commodore') anim(a, `animation.bc.${a.typeId.slice(3)}.attack`);
  if (a.typeId === 'bc:tidewatch_commodore') {
    hurt(ev.hitEntity, 4, a);
    particle(a.dimension, 'bc:will_spark', center(ev.hitEntity), { scale: 0.5 });
  }
}, 'navyHit'));
