// Lairs: bandit hideouts on dry, open ground; hive nests in mossy, muddy lowlands; cultist shrines in the woods.
// They appear out of sight near explorers, never close to another structure. Their chests are worth the fight -
// and the first time you open a lair's chest it counts towards the Lair Raider feat.
import { Player, system, world } from '@minecraft/server';
import { emit } from '../core/bus.js';
import { rand, safe, yawOf } from '../core/util.js';
import { build, farFromOthers } from '../sea/structures.js';

const KEY = 'bc:lairs';
const DRY = new Set(['minecraft:sand', 'minecraft:red_sand', 'minecraft:terracotta', 'minecraft:coarse_dirt']);
const WET = new Set(['minecraft:mud', 'minecraft:moss_block', 'minecraft:podzol', 'minecraft:clay', 'minecraft:mycelium']);
const GRASS = new Set(['minecraft:grass_block', 'minecraft:dirt']);

function surface(dim, x, z) {
  const top = safe(() => dim.getTopmostBlock({ x, z }));
  if (!top || top.isLiquid) return undefined;
  return { y: top.location.y, id: top.typeId };
}

function lairs() {
  const v = world.getDynamicProperty(KEY);
  try {
    return typeof v === 'string' ? JSON.parse(v) : [];
  } catch {
    return [];
  }
}

/** Which lair suits this ground? */
function kindFor(ground) {
  if (DRY.has(ground)) return 'hideout';
  if (WET.has(ground)) return 'nest';
  if (!GRASS.has(ground)) return undefined;
  const r = Math.random();
  return r < 0.4 ? 'hideout' : r < 0.75 ? 'shrine' : 'nest';
}

export function trySpawnLair(p, force = undefined) {
  if (p.dimension.id !== 'minecraft:overworld') return false;
  const yaw = yawOf(p.getViewDirection()) + 180 + rand(-70, 70);
  const r = (yaw * Math.PI) / 180;
  const dist = force ? 24 : rand(60, 85);
  const x = Math.floor(p.location.x - Math.sin(r) * dist);
  const z = Math.floor(p.location.z + Math.cos(r) * dist);
  if (!force && !farFromOthers(x, z, 360)) return false;
  const s = surface(p.dimension, x, z);
  if (!s || s.y < 50 || s.y > 120) return false;
  const kind = force ?? kindFor(s.id);
  if (!kind) return false;
  for (const [dx, dz] of [[-8, 0], [8, 0], [0, -8], [0, 8], [-6, -6], [6, 6]]) {
    const o = surface(p.dimension, x + dx, z + dz);
    if (!o || Math.abs(o.y - s.y) > 3) return false;
  }
  build(p.dimension, kind, { x, y: s.y, z });
  // remember its chests so looting it counts
  const chests = { hideout: [[-5, 1, -4], [4, 1, -5]], nest: [[0, 1, -2]], shrine: [[0, 1, -4]] }[kind] ?? [];
  const list = lairs();
  list.push({ kind, chests: chests.map(([dx, dy, dz]) => [x + dx, s.y + dy, z + dz]), by: [] });
  world.setDynamicProperty(KEY, JSON.stringify(list.slice(-60)));
  return true;
}

system.runInterval(() => {
  for (const p of world.getAllPlayers()) if (Math.random() < 0.12) safe(() => trySpawnLair(p), 'lairSpawn');
}, 400);

world.afterEvents.playerInteractWithBlock.subscribe((ev) => safe(() => {
  const b = ev.block;
  if (b.typeId !== 'minecraft:chest') return;
  const p = ev.player;
  const list = lairs();
  const l = b.location;
  const lair = list.find((x) => x.chests.some(([cx, cy, cz]) => cx === l.x && cy === l.y && cz === l.z));
  if (!lair || lair.by.includes(p.id)) return;
  lair.by.push(p.id);
  world.setDynamicProperty(KEY, JSON.stringify(list));
  safe(() => p.onScreenDisplay.setActionBar(`§6You raid the ${lair.kind === 'hideout' ? 'bandit hideout' : lair.kind === 'nest' ? 'hive nest' : 'cultist shrine'}!`));
  if (p instanceof Player) emit('lair', p, lair.kind);
}, 'lairLoot'));

// cheat: /scriptevent bc:lair [hideout|nest|shrine] builds one about 24 blocks behind you
system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (ev.id !== 'bc:lair') return;
  const p = ev.sourceEntity instanceof Player ? ev.sourceEntity : world.getAllPlayers()[0];
  if (!p) return;
  const want = ev.message.trim();
  const kind = ['hideout', 'nest', 'shrine'].includes(want) ? want : ['hideout', 'nest', 'shrine'][Math.floor(Math.random() * 3)];
  const ok = safe(() => trySpawnLair(p, kind), 'lairCheat');
  safe(() => p.sendMessage(ok ? `§6A ${kind} appears behind you.` : '§7No room for a lair here - try flatter ground.'));
});
