// Encounters your own actions wake (v1.1.0), and the dangers of the land itself.
// * Chop a tree and now and then a ROOTWARDEN tears itself free of the bark; dig deep stone and a MANA WRAITH may seep
//   out; cut grass and a MANA SPRITE pops up; lie down in a bed at night and you may wake to a HOLLOW KNIGHT.
// * In HAUNTED lands the slain sometimes rise as wraiths, and the Hollow walk at night; BANDIT COUNTRY has ambushes on
//   the road; DEVIL-SCARRED land has imps; WYVERN TERRITORY has wyverns overhead; the FAE WILDS have sprites by day and
//   Will-o'-Wisps by night. Danger stars bring bigger parties. Sanctuaries - and Calm Skies - stay quiet.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { emit } from '../core/bus.js';
import { particle, rgb, sound, title } from '../core/fx.js';
import { V, pick, rand, safe } from '../core/util.js';
import { behind } from './events.js';
import { flyby, spawnWisp } from './beasts.js';
import { calm, omen } from './omens.js';
import { hasTrait, starsAt, traitsAt } from './regions.js';
import { inCapital } from './capital.js';

const E = DATA.world.encounters;
const cool = new Map();
const isNight = () => {
  const t = safe(() => world.getTimeOfDay()) ?? 6000;
  return t > 13000 && t < 23000;
};
function ready(p, key, ticks) {
  const k = `${p.id}|${key}`;
  const t = system.currentTick;
  if ((cool.get(k) ?? -1e9) > t) return false;
  cool.set(k, t + ticks);
  return true;
}

/** Wake an encounter next to a spot. */
export function encounter(p, kind, at) {
  const enc = E[kind];
  if (!enc) return undefined;
  const dim = p.dimension;
  particle(dim, kind === 'grass' ? 'bc:leaf_burst' : kind === 'chop' ? 'bc:leaf_burst' : 'bc:rock_debris', at, { scale: 0.9 });
  const e = safe(() => dim.spawnEntity(enc.id, at));
  safe(() => p.onScreenDisplay.setActionBar(enc.msg));
  sound(dim, kind === 'chop' ? 'dig.wood' : kind === 'mine' ? 'dig.stone' : 'random.orb', at, 1, 0.6);
  emit('encounter', p, kind);
  return e;
}

const LOG = (id) => id.endsWith('_log') || id.endsWith('_stem') || id === 'minecraft:log' || id === 'minecraft:log2' || id.endsWith('_wood');
const STONE = (id) => id === 'minecraft:stone' || id.includes('deepslate') || id.endsWith('_ore') || id === 'minecraft:tuff' || id === 'minecraft:andesite'
  || id === 'minecraft:diorite' || id === 'minecraft:granite';
const GRASS = (id) => (id.includes('grass') && id !== 'minecraft:grass_block' && id !== 'minecraft:grass_path') || id.includes('fern') || id.includes('flower')
  || ['minecraft:poppy', 'minecraft:dandelion', 'minecraft:azure_bluet', 'minecraft:oxeye_daisy', 'minecraft:allium', 'minecraft:cornflower'].includes(id);

/** What breaking a block may wake (exported for tests: `roll` replaces the dice). */
export function onBreak(p, id, loc, roll = Math.random()) {
  if (calm()) return undefined;
  const fae = hasTrait(loc, 'fae_wilds');
  const at = { x: loc.x + 0.5, y: loc.y + 0.5, z: loc.z + 0.5 };
  if (LOG(id) && roll < E.chop.chance * (fae ? 2 : 1) && ready(p, 'chop', 1200)) return encounter(p, 'chop', V.add(at, { x: rand(-2, 2), y: 0, z: rand(-2, 2) }));
  if (STONE(id) && loc.y < 50 && roll < E.mine.chance && ready(p, 'mine', 1200)) return encounter(p, 'mine', at);
  if (GRASS(id) && roll < E.grass.chance * (fae ? 3 : 1) && ready(p, 'grass', 600)) return encounter(p, 'grass', V.add(at, { x: 0, y: 0.5, z: 0 }));
  return undefined;
}
world.afterEvents.playerBreakBlock.subscribe((ev) => safe(() => onBreak(ev.player, ev.brokenBlockPermutation.type.id, ev.block.location), 'breakEncounter'));

// a bed at night
world.afterEvents.playerInteractWithBlock.subscribe((ev) => safe(() => {
  const b = ev.block;
  if (!b.typeId.endsWith('bed') || !isNight() || calm()) return;
  const p = ev.player;
  const chance = E.bed.chance * (hasTrait(b.location, 'haunted') ? 3 : 1);
  if (Math.random() >= chance || !ready(p, 'bed', 20 * 600)) return;
  system.runTimeout(() => {
    const at = V.add(b.location, { x: rand(-2, 2) + 0.5, y: 0.2, z: rand(-2, 2) + 0.5 });
    encounter(p, 'bed', at);
    title(p, '§8...', '§7Something is in the room', 40);
  }, 60);
}, 'bedEncounter'));

// the slain of haunted lands sometimes rise
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const e = ev.deadEntity;
  if (e.typeId === 'bc:mana_wraith' || !safe(() => e.matches({ families: ['monster'] }))) return;
  const loc = { ...e.location };
  if (omen() === 'bandit_moon' && e.typeId.startsWith('bc:bandit')) safe(() => e.dimension.spawnItem(new ItemStack('bc:doubloon', 5 + Math.floor(Math.random() * 6)), loc));
  if (!isNight() || !hasTrait(loc, 'haunted') || Math.random() >= E.wraith.chance) return;
  const dim = e.dimension;
  system.runTimeout(() => {
    particle(dim, 'bc:dark_mist', loc, { scale: 0.6 });
    safe(() => dim.spawnEntity('bc:mana_wraith', V.add(loc, { x: 0, y: 0.5, z: 0 })));
  }, 30);
}, 'wraithRise'));

// ------------------------------------------------------------------------------- the land's own dangers
function party(p, ids, n, msg) {
  const dim = p.dimension;
  const at = behind(p, 20, 30);
  if (!at) return 0;
  for (let i = 0; i < n; i++) safe(() => dim.spawnEntity(typeof ids === 'string' ? ids : pick(ids), V.add(at, { x: rand(-3, 3), y: 0.2, z: rand(-3, 3) })));
  safe(() => p.onScreenDisplay.setActionBar(msg));
  return n;
}

/** One roll of the land's dangers for a player (exported for tests). Returns what happened. */
export function landRoll(p, roll = Math.random) {
  if (p.dimension.id !== 'minecraft:overworld' || calm() || inCapital(p.location)) return '';
  const loc = p.location;
  const traits = traitsAt(loc);
  if (traits.includes('sanctuary')) return '';
  const stars = starsAt(loc);
  const extra = Math.floor((stars - 1) / 2);
  const night = isNight();
  const o = omen();
  if (traits.includes('bandit_country') && !night && roll() < 0.12 * (o === 'bandit_moon' ? 2 : 1)) {
    party(p, ['bc:bandit', 'bc:bandit', 'bc:bandit_archer'], 2 + extra + Math.floor(roll() * 2), '§cBandits! §7An ambush on the road!');
    return 'bandits';
  }
  if ((traits.includes('haunted') || o === 'hollow_night') && night && roll() < (o === 'hollow_night' ? 0.25 : 0.15)) {
    party(p, 'bc:hollow_knight', 1 + extra + Math.floor(roll() * 2), '§8The Hollow walk tonight...');
    return 'hollow';
  }
  if (traits.includes('devil_scarred') && roll() < 0.08) {
    party(p, 'bc:imp', 2 + extra, '§4Imps crawl out of a crack in the earth!');
    return 'imps';
  }
  if ((traits.includes('wyvern_lands') && roll() < 0.03) || (o === 'wyvern_migration' && roll() < 0.08)) {
    if (flyby(p)) return 'wyvern';
  }
  if (traits.includes('fae_wilds') || traits.includes('haunted')) {
    if (night && roll() < (traits.includes('fae_wilds') ? 0.12 : 0.08)) {
      if (spawnWisp(p)) return 'wisp';
    } else if (!night && traits.includes('fae_wilds') && roll() < 0.1) {
      for (let i = 0; i < 2; i++) safe(() => p.dimension.spawnEntity('bc:mana_sprite', V.add(p.location, { x: rand(-6, 6), y: 1.5, z: rand(-6, 6) })));
      return 'sprites';
    }
  }
  if (o === 'bandit_moon' && !night && roll() < 0.06) {
    party(p, ['bc:bandit', 'bc:bandit_thief'], 2 + extra, '§cBandits under the Bandit Moon!');
    return 'bandits';
  }
  return '';
}
system.runInterval(() => {
  for (const p of world.getAllPlayers()) safe(() => landRoll(p), 'landRoll');
}, 1200);

export { rgb };
