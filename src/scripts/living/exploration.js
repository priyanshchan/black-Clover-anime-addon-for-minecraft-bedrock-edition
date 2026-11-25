// Exploration (v1.1.0): Explorer's Maps lead to landmarks nobody has found; Torn Journal Pages tell the land's story (and
// some mark a buried cache); the Handbook's ATLAS keeps the regions and landmarks you have found, today's omen and your
// relics - and tracks the nearest unknown landmark on your HUD.
import { BlockPermutation, ItemStack, system, world } from '@minecraft/server';
import { ActionFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { emit, on } from '../core/bus.js';
import { addCompassProvider, addHeldHud } from '../core/hud.js';
import { affixLine, fillChest, readRoll, setLootMakers } from '../core/loot.js';
import { particle, sound, title } from '../core/fx.js';
import { wrap } from '../core/scrolls.js';
import { pick, rand, safe, yawOf } from '../core/util.js';
import { foundBy, nameOf, nearestUnfound, slotsNear } from './landmarks.js';
import { compassWord, currentRegion, regions, stars as starText, traitText } from './regions.js';
import { omenInfo } from './omens.js';
import { relicsOf } from './relics.js';

const W = DATA.world;
const G = DATA.glyphs;

function arrowTo(p, x, z) {
  const dx = x - p.location.x;
  const dz = z - p.location.z;
  const rel = ((yawOf({ x: dx, y: 0, z: dz }) - yawOf(p.getViewDirection()) + 540) % 360) - 180;
  return { arrow: G.arrows[((Math.round(rel / 45) % 8) + 8) % 8], dist: Math.round(Math.hypot(dx, dz)) };
}
function held(p) {
  const inv = p.getComponent('minecraft:inventory')?.container;
  const it = inv?.getItem(p.selectedSlotIndex);
  return { inv, it };
}

// ------------------------------------------------------------------------------- Explorer's Maps
/** An Explorer's Map (pointing at the nearest unknown landmark around `p`, of `kind` when given). */
export function makeExplorerMap(p = undefined, kind = '') {
  const it = new ItemStack('bc:explorer_map', 1);
  if (p) aimMap(it, p, kind);
  else safe(() => it.setLore(['§7Use it to unroll the map.', '§8It shows a place nobody has found.']));
  return it;
}
function aimMap(it, p, kind = '') {
  const s = nearestUnfound(p, kind, 1200) ?? nearestUnfound(p, '', 1200);
  if (!s) return false;
  safe(() => {
    it.setDynamicProperty('bc:tx', s.x);
    it.setDynamicProperty('bc:tz', s.z);
    it.setDynamicProperty('bc:tid', s.id);
    it.setLore([`§7Leads to: §6${nameOf(s.kind)}`, `§8${compassWord(s.x - p.location.x, s.z - p.location.z)} of where it was drawn`]);
    it.nameTag = `§6Explorer's Map: ${nameOf(s.kind)}`;
  });
  return true;
}
export function useExplorerMap(p) {
  const { inv, it } = held(p);
  if (!inv || it?.typeId !== 'bc:explorer_map') return;
  let x = safe(() => it.getDynamicProperty('bc:tx'));
  if (typeof x !== 'number') {
    if (!aimMap(it, p)) {
      safe(() => p.sendMessage('§7The map is blank - there is nothing undiscovered near here. Explore further and try again.'));
      return;
    }
    inv.setItem(p.selectedSlotIndex, it);
    x = safe(() => it.getDynamicProperty('bc:tx'));
  }
  const z = Number(safe(() => it.getDynamicProperty('bc:tz')));
  const d = Math.round(Math.hypot(Number(x) - p.location.x, z - p.location.z));
  safe(() => p.sendMessage(`§6The map shows ${String(safe(() => it.nameTag) ?? '').replace(/^.*: /, 'a ')} §f${compassWord(Number(x) - p.location.x, z - p.location.z)}§6, about §f${d}§6 blocks away.`));
  sound(p.dimension, 'bc.grimoire.flip', p.location, 0.8, 1.3);
}
addHeldHud('bc:explorer_map', (p, it) => {
  const x = safe(() => it.getDynamicProperty('bc:tx'));
  const z = safe(() => it.getDynamicProperty('bc:tz'));
  if (typeof x !== 'number' || typeof z !== 'number') return '§6Explorer\'s Map §7- use it to unroll the map';
  const { arrow, dist } = arrowTo(p, x, z);
  if (dist < 24) {
    const { inv } = held(p);
    safe(() => inv?.setItem(p.selectedSlotIndex, undefined));
    title(p, '§6§lYOU FOUND IT', '§7The map crumbles - its secret is yours', 50);
    sound(p.dimension, 'bc.chord', p.location, 1, 1.3);
    return '§6The map\'s secret is found.';
  }
  return `${arrow} §6${String(safe(() => it.nameTag) ?? 'Explorer\'s Map').replace(/§./g, '').replace('Explorer\'s Map: ', '')} §7${dist}m`;
});

// ------------------------------------------------------------------------------- journals
/** A torn journal page. Its words are written the first time someone reads it, from the land around them. */
export function makeJournal(stars = 1, cache = Math.random() < 0.25 + 0.04 * stars) {
  const it = new ItemStack('bc:journal_page', 1);
  safe(() => {
    if (cache) it.setDynamicProperty('bc:cache', true);
    it.setLore(['§7A page torn from someone\'s journal.', cache ? '§8Something is scrawled in the margin...' : '§8Use it to read.']);
  });
  return it;
}
setLootMakers({ journal: (stars, treasure) => makeJournal(stars, Math.random() < (treasure ? 0.6 : 0.25 + 0.04 * stars)), map: () => makeExplorerMap() });

function journalText(p, cache) {
  const reg = currentRegion(p);
  const slot = nearestUnfound(p, '', 900) ?? slotsNear(p.location.x, p.location.z, 1)[0];
  const others = Object.values(regions()).filter((r) => r.k !== reg?.k);
  const vars = {
    region: reg?.name ?? 'these lands', other: others.length ? pick(others).name : 'the Capital', what: slot ? nameOf(slot.kind) : 'old ruin',
    dir: slot ? compassWord(slot.x - p.location.x, slot.z - p.location.z) : 'north', dist: slot ? String(Math.round(Math.hypot(slot.x - p.location.x, slot.z - p.location.z) / 10) * 10) : '200',
    name: pick(W.wandererFirst), day: String(3 + Math.floor(Math.random() * 80)),
  };
  if (cache) {
    vars.dir = pick(['north', 'south', 'east', 'west', 'north-east', 'south-west', 'north-west', 'south-east']);
    vars.dist = String(40 + Math.floor(Math.random() * 6) * 10);
  }
  const tpl = cache ? pick(W.cacheJournals) : pick(W.journals);
  return { text: tpl.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? k), dir: vars.dir, dist: Number(vars.dist) };
}
const DIRS = { north: [0, -1], south: [0, 1], east: [1, 0], west: [-1, 0], 'north-east': [0.71, -0.71], 'north-west': [-0.71, -0.71], 'south-east': [0.71, 0.71], 'south-west': [-0.71, 0.71] };

export async function readJournal(p) {
  const { inv, it } = held(p);
  if (!inv || it?.typeId !== 'bc:journal_page') return;
  let text = safe(() => it.getDynamicProperty('bc:text'));
  const cache = safe(() => it.getDynamicProperty('bc:cache')) === true;
  if (typeof text !== 'string') {
    const j = journalText(p, cache);
    text = j.text;
    safe(() => {
      it.setDynamicProperty('bc:text', text);
      if (cache) {
        const [dx, dz] = DIRS[j.dir] ?? [0, -1];
        it.setDynamicProperty('bc:tx', Math.round(p.location.x + dx * j.dist));
        it.setDynamicProperty('bc:tz', Math.round(p.location.z + dz * j.dist));
      }
      it.setLore(wrap(`§7"${String(text).slice(0, 120)}..."`, 46).slice(0, 4));
    });
    inv.setItem(p.selectedSlotIndex, it);
    emit('journal', p);
  }
  const tx = safe(() => it.getDynamicProperty('bc:tx'));
  if (cache && typeof tx === 'number') {
    const tz = Number(safe(() => it.getDynamicProperty('bc:tz')));
    if (Math.hypot(tx - p.location.x, tz - p.location.z) <= 4) {
      digCache(p, tx, tz);
      inv.setItem(p.selectedSlotIndex, undefined);
      return;
    }
  }
  sound(p.dimension, 'bc.grimoire.flip', p.location, 0.8, 1);
  const f = new ActionFormData().title('§lTorn Journal Page').body(`§f${text}${cache ? '\n\n§6(Hold the page to follow the arrow to the cache, and use it on the spot to dig.)' : ''}`);
  f.button('Close');
  await f.show(p);
}
addHeldHud('bc:journal_page', (p, it) => {
  const x = safe(() => it.getDynamicProperty('bc:tx'));
  const z = safe(() => it.getDynamicProperty('bc:tz'));
  if (typeof x !== 'number' || typeof z !== 'number') return undefined;
  const { arrow, dist } = arrowTo(p, x, z);
  return dist <= 4 ? '§6§lThe cache is here! §r§7Use the page to dig.' : `${arrow} §6Buried cache §7${dist}m`;
});

/** Dig a buried cache: a chest two blocks down, full of whatever someone hid. */
export function digCache(p, x, z) {
  const dim = p.dimension;
  let y = Math.floor(p.location.y) - 1;
  for (let k = 0; k < 6; k++) {
    const b = safe(() => dim.getBlock({ x, y, z }));
    if (b && !b.isAir && !b.isLiquid) break;
    y--;
  }
  const chest = safe(() => dim.getBlock({ x, y: y - 1, z }));
  if (!chest) return false;
  safe(() => dim.getBlock({ x, y, z })?.setType('minecraft:air'));
  safe(() => chest.setPermutation(BlockPermutation.resolve('minecraft:chest')));
  system.run(() => safe(() => fillChest(chest, 'cache', 2)));
  particle(dim, 'bc:rock_debris', { x: x + 0.5, y: y + 1, z: z + 0.5 }, { scale: 0.8 });
  sound(dim, 'bc.coins', p.location, 1, 1);
  title(p, '§6§lA BURIED CACHE', '§7Someone never came back for it', 50);
  emit('cache', p);
  return true;
}

// ------------------------------------------------------------------------------- tracking a landmark from the Atlas
addCompassProvider((p) => {
  const id = safe(() => p.getDynamicProperty('bc:track_lm'));
  if (typeof id !== 'string') return undefined;
  const s = slotsNear(p.location.x, p.location.z, 2).find((x) => x.id === id);
  if (!s || s.rec?.found.includes(p.id)) {
    safe(() => p.setDynamicProperty('bc:track_lm', undefined));
    return undefined;
  }
  const { arrow, dist } = arrowTo(p, s.x, s.z);
  return `${arrow} §6${nameOf(s.kind)} §7${dist}m`;
});

// ------------------------------------------------------------------------------- the Atlas
function regionBlock(p) {
  const r = currentRegion(p);
  if (!r) return '§7You stand somewhere nobody has named.';
  const traits = r.traits.map((t) => `${W.traits[t].mc}${W.traits[t].name}§7: ${W.traits[t].desc}`).join('\n');
  return `§6§l${r.name}§r\n${r.mc}${r.realmName} §7· danger ${starText(r.stars)}\n${traits}\n§8§o${r.lore}`;
}
function relicBlock(p) {
  const inv = p.getComponent('minecraft:inventory')?.container;
  const lines = [];
  for (let i = 0; inv && i < 9 && lines.length < DATA.loot.relicSlots; i++) {
    const it = inv.getItem(i);
    if (!it || !it.typeId.startsWith('bc:relic_')) continue;
    const roll = readRoll(it);
    if (!roll) continue;
    lines.push(`§d${roll.name}§7: ${Object.entries(roll.affixes).map(([k, v]) => affixLine('relic', k, v).replace('§7', '')).join(', ')}`);
  }
  void relicsOf;
  return lines.length ? lines.join('\n') : '§8No relics in your hotbar.';
}

export async function atlasPage(p, back) {
  const mine = Object.values(regions()).filter((r) => r.by.includes(p.id));
  const found = foundBy(p);
  const o = omenInfo();
  const body = [regionBlock(p), '', o ? `§7Omen of the day: ${o.mc}${o.name}§7 - ${o.desc}` : '§7No omen today.', '',
    `§eRegions found: §f${mine.length}   §eLandmarks found: §f${found.length}`, '', '§dRelics at work:', relicBlock(p)].join('\n');
  const f = new ActionFormData().title('§lThe Atlas').body(body);
  f.button('§lRegions you have found\n§r§8Nearest first');
  f.button('§lLandmarks you have found\n§r§8Spires, roosts, crypts...');
  f.button('§lTrack an unknown landmark\n§r§8Follow the arrow on your HUD');
  f.button('Back');
  const r = await f.show(p);
  if (r.canceled || r.selection === undefined) return;
  if (r.selection === 0) {
    const list = mine.map((x) => ({ x, d: Math.hypot(x.rx * 320 + 160 - p.location.x, x.rz * 320 + 160 - p.location.z) })).sort((a, b) => a.d - b.d).slice(0, 30);
    const lines = list.map(({ x, d }) => `§6${x.name} §7${starText(x.stars)} ${x.mc}${x.realmName}§7 - ${traitText(x)} §8(${compassWord(x.rx * 320 + 160 - p.location.x, x.rz * 320 + 160 - p.location.z)}, ${Math.round(d)}m)`);
    await new ActionFormData().title('Regions').body(lines.join('\n') || '§7None yet - go and look!').button('Back').show(p);
    return atlasPage(p, back);
  }
  if (r.selection === 1) {
    const lines = found.map((x) => ({ x, d: Math.hypot(x.x - p.location.x, x.z - p.location.z) })).sort((a, b) => a.d - b.d).slice(0, 30)
      .map(({ x, d }) => `§6${nameOf(x.kind)}${x.cleared ? ' §a(cleared)' : ''} §7- ${regions()[x.region]?.name ?? '?'} §8(${compassWord(x.x - p.location.x, x.z - p.location.z)}, ${Math.round(d)}m)`);
    await new ActionFormData().title('Landmarks').body(lines.join('\n') || '§7None yet.').button('Back').show(p);
    return atlasPage(p, back);
  }
  if (r.selection === 2) {
    const s = nearestUnfound(p, '', 900);
    if (!s) safe(() => p.sendMessage('§7No unknown landmark near here - explore new regions first.'));
    else {
      safe(() => p.setDynamicProperty('bc:track_lm', s.id));
      safe(() => p.sendMessage(`§7Now tracking: §6${nameOf(s.kind)}§7 (${compassWord(s.x - p.location.x, s.z - p.location.z)}, ${Math.round(Math.hypot(s.x - p.location.x, s.z - p.location.z))} blocks).`));
    }
    return;
  }
  return back?.();
}

on('landmark', (p, rec) => {
  if (safe(() => p.getDynamicProperty('bc:track_lm')) === rec.id) safe(() => p.setDynamicProperty('bc:track_lm', undefined));
});
export { rand, world };
