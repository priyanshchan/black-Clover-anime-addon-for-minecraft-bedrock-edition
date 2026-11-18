// Ancient magic dungeons: they appear underground near explorers, with flame traps, treasure and a Guardian.
import { Player, system, world } from '@minecraft/server';
import { center, hurt, knock, knockFrom, launch, targetsAround } from '../core/combat.js';
import { anim, particle, shakeArea, shockwave, sound, title } from '../core/fx.js';
import { addXp } from '../core/progress.js';
import { V, isCreative, rand, safe, timer, yawOf } from '../core/util.js';
import { build, farFromOthers } from '../sea/structures.js';
import { addWillXp } from '../sea/will.js';

const trapCd = new Map();
/** @type {Map<string, {slam: number, rock: number, enraged: boolean}>} */
const golems = new Map();

// ------------------------------------------------------------------------------- spawning
function landSurface(dim, x, z) {
  for (let y = 130; y > 40; y--) {
    const b = safe(() => dim.getBlock({ x, y, z }));
    if (!b) return undefined;
    if (b.isAir) continue;
    const id = b.typeId;
    if (b.isLiquid || id.endsWith('_leaves') || id.endsWith('_log') || id === 'minecraft:snow_layer') return undefined;
    return y;
  }
  return undefined;
}

function trySpawn(p) {
  if (p.dimension.id !== 'minecraft:overworld') return;
  const yaw = yawOf(p.getViewDirection()) + 180 + rand(-60, 60);
  const r = (yaw * Math.PI) / 180;
  const dist = rand(60, 90);
  const x = Math.floor(p.location.x - Math.sin(r) * dist);
  const z = Math.floor(p.location.z + Math.cos(r) * dist);
  if (!farFromOthers(x, z, 400)) return;
  const y = landSurface(p.dimension, x, z);
  if (y === undefined || y < 52 || y > 120) return;
  // the whole footprint must be solid ground (no cliffs or lakes)
  for (const [dx, dz] of [[-3, -3], [3, -3], [-3, 3], [3, 3], [0, 20], [0, 40]]) {
    const yy = landSurface(p.dimension, x + dx, z + dz);
    if (yy === undefined || Math.abs(yy - y) > 6) return;
  }
  build(p.dimension, 'dungeon', { x, y, z });
}

system.runInterval(() => {
  for (const p of world.getAllPlayers()) if (Math.random() < 0.22) safe(() => trySpawn(p), 'dungeonSpawn');
}, 300);

// ------------------------------------------------------------------------------- flame traps
system.runInterval(() => {
  const v = world.getDynamicProperty('bc:traps');
  if (typeof v !== 'string' || v.length < 3) return;
  let traps;
  try {
    traps = JSON.parse(v);
  } catch {
    return;
  }
  const t = system.currentTick;
  for (const p of world.getAllPlayers()) {
    if (isCreative(p)) continue;
    const l = p.location;
    for (const [x, y, z, dim] of traps) {
      if (dim !== p.dimension.id || Math.abs(l.x - (x + 0.5)) > 1.6 || Math.abs(l.z - (z + 0.5)) > 1.2 || Math.abs(l.y - y) > 1.5) continue;
      const key = `${x},${y},${z}`;
      if ((trapCd.get(key) ?? 0) > t) continue;
      trapCd.set(key, t + 30);
      for (const sx of [-2, 2]) particle(p.dimension, 'bc:flame_burst', { x: x + 0.5 + sx, y: y + 1, z: z + 0.5 }, { scale: 0.6 });
      sound(p.dimension, 'mob.blaze.shoot', l, 1, 0.8);
      hurt(p, 5, undefined, 'fire');
      safe(() => p.setOnFire(3, true));
    }
  }
}, 5);

// ------------------------------------------------------------------------------- the Guardian
function track(e) {
  if (e.typeId === 'bc:dungeon_golem' && !golems.has(e.id)) golems.set(e.id, { slam: 0, rock: system.currentTick + 60, enraged: false });
}
world.afterEvents.entitySpawn.subscribe((ev) => safe(() => track(ev.entity)));
world.afterEvents.entityLoad.subscribe((ev) => safe(() => track(ev.entity)));

system.runInterval(() => {
  const t = system.currentTick;
  for (const [id, st] of golems) {
    const e = world.getEntity(id);
    if (!e) {
      golems.delete(id);
      continue;
    }
    safe(() => {
      const target = e.dimension.getPlayers({ location: e.location, maxDistance: 18 }).find((p) => {
        const gm = p.getGameMode();
        return gm !== 'Creative' && gm !== 'Spectator';
      });
      if (!target) return;
      const hp = e.getComponent('minecraft:health');
      if (hp && !st.enraged && hp.currentValue < hp.effectiveMax * 0.5) {
        st.enraged = true;
        sound(e.dimension, 'bc.golem.slam', e.location, 2, 0.5);
        for (let i = 0; i < 2; i++) safe(() => e.dimension.spawnEntity('bc:imp', V.add(e.location, { x: rand(-3, 3), y: 2, z: rand(-3, 3) })));
        title(target, '§bThe Guardian awakens fully', '§7Its runes blaze with stolen mana', 40);
      }
      const d = V.dist(target.location, e.location);
      if (d < 4.8 && st.slam <= t) {
        st.slam = t + (st.enraged ? 50 : 70);
        anim(e, 'animation.bc.dungeon_golem.slam');
        timer(9, () => {
          const at = e.location;
          sound(e.dimension, 'bc.golem.slam', at, 1.6, 0.8);
          shockwave(e.dimension, at, 'earth', 4.5);
          particle(e.dimension, 'bc:rock_debris', at, { scale: 1.2 });
          shakeArea(e.dimension, at, 14, 0.5, 0.5);
          for (const v of targetsAround(e.dimension, at, 4.5, e)) {
            if (v.typeId === 'bc:imp') continue;
            hurt(v, st.enraged ? 16 : 12, e);
            knock(v, { x: 0, y: 0, z: 0 }, 0, 0.8);
          }
        });
      } else if (d > 6 && st.rock <= t) {
        st.rock = t + (st.enraged ? 60 : 90);
        anim(e, 'animation.bc.dungeon_golem.slam');
        const from = V.add(e.location, { x: 0, y: 4.2, z: 0 });
        timer(8, () => launch(e, 'bc:boulder', from, V.sub(center(target), from), 1.4, { spell: 'golem_rock', attr: 'earth', damage: 10, pierce: 0 }));
      }
    }, 'golem');
  }
}, 10);

world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  if (ev.deadEntity.typeId !== 'bc:dungeon_golem') return;
  const loc = ev.deadEntity.location;
  const dim = ev.deadEntity.dimension;
  shockwave(dim, loc, 'earth', 8);
  particle(dim, 'bc:rock_debris', loc, { scale: 2 });
  for (const p of dim.getPlayers({ location: loc, maxDistance: 32 })) title(p, '§b§lDUNGEON CLEARED', '§7The Guardian crumbles to dust', 60);
}, 'golemDie'));

// ------------------------------------------------------------------------------- ancient pages
export function readPage(p) {
  addXp(p, 60);
  addWillXp(p, 10);
  sound(p.dimension, 'bc.grimoire.flip', p.location, 1, 0.8);
  particle(p.dimension, 'bc:clover_leaves', V.add(p.location, { x: 0, y: 1, z: 0 }), { scale: 0.8 });
  safe(() => p.onScreenDisplay.setActionBar('§eThe ancient page crumbles into your grimoire (+60 magic XP)'));
  if (!isCreative(p)) {
    const inv = p.getComponent('minecraft:inventory')?.container;
    const it = inv?.getItem(p.selectedSlotIndex);
    if (it?.typeId === 'bc:ancient_page') {
      if (it.amount > 1) {
        it.amount -= 1;
        inv.setItem(p.selectedSlotIndex, it);
      } else inv.setItem(p.selectedSlotIndex, undefined);
    }
  }
}

export { Player, knockFrom };
