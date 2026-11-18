// Mana Waygates (v1.0.0): place a Waygate and it joins the network every player shares. Use one to travel to any other
// gate - it costs mana (more for longer trips), or a mana crystal if your mana is low. Name your gates; break one to
// take it out of the network. Handy for answering the world's incidents before they play out without you.
import { Player, system, world } from '@minecraft/server';
import { ActionFormData, ModalFormData } from '@minecraft/server-ui';
import { emit } from '../core/bus.js';
import { state } from '../core/data.js';
import { sound } from '../core/fx.js';
import { isCreative, safe } from '../core/util.js';
import * as vfx from '../core/vfx.js';

const KEY = 'bc:waygates';
const BASE = 20;
const PER_100 = 15;
const COOLDOWN = 30 * 20;
const CYAN = vfx.hex('60c8ff');
/** @typedef {{id: string, dim: string, x: number, y: number, z: number, name: string, by: string}} Gate */

/** @returns {Gate[]} */
export function gates() {
  const raw = safe(() => world.getDynamicProperty(KEY));
  try {
    const v = typeof raw === 'string' ? JSON.parse(raw) : [];
    return Array.isArray(v) ? v : [];
  } catch {
    return [];
  }
}
function store(list) {
  safe(() => world.setDynamicProperty(KEY, JSON.stringify(list.slice(-64))));
}
const keyOf = (dim, l) => `${dim}:${Math.floor(l.x)},${Math.floor(l.y)},${Math.floor(l.z)}`;

export function addGate(p, loc) {
  const list = gates();
  const id = keyOf(p.dimension.id, loc);
  if (list.some((g) => g.id === id)) return;
  list.push({ id, dim: p.dimension.id, x: Math.floor(loc.x), y: Math.floor(loc.y), z: Math.floor(loc.z), name: `Waygate ${list.length + 1}`, by: p.name });
  store(list);
  vfx.pillar(p.dimension, { x: Math.floor(loc.x) + 0.5, y: Math.floor(loc.y), z: Math.floor(loc.z) + 0.5 }, CYAN, 6, 1);
  safe(() => p.sendMessage(`§bThe Waygate joins the network (§f${list.length}§b gates). §7Use it to travel; rename it from its menu.`));
}
export function removeGate(dim, loc) {
  const id = keyOf(dim, loc);
  store(gates().filter((g) => g.id !== id));
}

world.afterEvents.playerPlaceBlock.subscribe((ev) => safe(() => {
  if (ev.block.typeId === 'bc:waygate') addGate(ev.player, ev.block.location);
}, 'waygatePlace'));
world.afterEvents.playerBreakBlock.subscribe((ev) => safe(() => {
  if (ev.brokenBlockPermutation.type.id === 'bc:waygate') removeGate(ev.dimension.id, ev.block.location);
}, 'waygateBreak'));

/** Mana a trip costs. */
export function tripCost(from, to) {
  const d = Math.hypot(from.x - to.x, from.z - to.z);
  return Math.round(BASE + (d / 100) * PER_100);
}
const cooldown = new Map();

/** Travel from one gate to another. */
export function travel(p, from, to) {
  const t = system.currentTick;
  if ((cooldown.get(p.id) ?? 0) > t && !isCreative(p)) {
    safe(() => p.sendMessage(`§7The Waygate is still humming - wait §f${Math.ceil(((cooldown.get(p.id) ?? 0) - t) / 20)}s§7.`));
    return false;
  }
  const cost = tripCost(from, to);
  const s = state(p);
  if (!isCreative(p)) {
    if (s.attr !== 'anti' && s.mana >= cost) {
      s.mana -= cost;
      s.dirty = true;
    } else if (!payCrystal(p)) {
      safe(() => p.sendMessage(`§7You need §b${cost} mana§7 or a §bMana Crystal§7 to travel.`));
      return false;
    }
  }
  const dim = safe(() => world.getDimension(to.dim));
  if (!dim) return false;
  const dest = { x: to.x + 0.5, y: to.y + 0.2, z: to.z + 1.6 };
  vfx.pillar(p.dimension, p.location, CYAN, 7, 1.2);
  vfx.spawn(p.dimension, 'bc:fx_flash', { x: p.location.x, y: p.location.y + 1, z: p.location.z }, { color: CYAN, size: 1.6 });
  sound(p.dimension, 'bc.portal', p.location, 1, 1.2);
  safe(() => p.teleport(dest, { dimension: dim }));
  system.runTimeout(() => {
    vfx.pillar(dim, dest, CYAN, 7, 1.2);
    vfx.groundSigil(dim, dest, CYAN, 4, 1.2);
    sound(dim, 'bc.portal', dest, 1, 1.4);
  }, 2);
  cooldown.set(p.id, t + COOLDOWN);
  emit('waygate', p);
  safe(() => p.onScreenDisplay.setActionBar(`§bYou step through to §f${to.name}§b.`));
  return true;
}
function payCrystal(p) {
  const inv = p.getComponent('minecraft:inventory')?.container;
  for (let i = 0; inv && i < inv.size; i++) {
    const it = inv.getItem(i);
    if (it?.typeId !== 'bc:mana_crystal') continue;
    if (it.amount > 1) {
      it.amount -= 1;
      inv.setItem(i, it);
    } else inv.setItem(i, undefined);
    return true;
  }
  return false;
}

export async function openGate(p, loc) {
  const here = gates().find((g) => g.id === keyOf(p.dimension.id, loc));
  if (!here) {
    addGate(p, loc);
    return;
  }
  const others = gates().filter((g) => g.id !== here.id).sort((a, b) => (a.dim === b.dim ? 0 : a.dim === here.dim ? -1 : 1));
  const f = new ActionFormData().title(`§l${here.name}`)
    .body(others.length ? '§7Travel to another Waygate. It costs mana (more for longer trips) - or a Mana Crystal if your mana is low.' : '§7No other Waygates yet. Build another one somewhere else to travel between them.');
  for (const g of others) {
    const far = g.dim === here.dim ? `${Math.round(Math.hypot(g.x - here.x, g.z - here.z))}m, ${tripCost(here, g)} mana` : 'another dimension';
    f.button(`§b§l${g.name}\n§r§8${far}`);
  }
  f.button('§lRename this gate');
  f.button('§8Close');
  const r = await f.show(p);
  if (r.canceled || r.selection === undefined) return;
  if (r.selection < others.length) {
    travel(p, here, others[r.selection]);
    return;
  }
  if (r.selection === others.length) {
    const m = await new ModalFormData().title('Rename the Waygate').textField('Name', here.name, { defaultValue: here.name }).show(p);
    const name = String(m.formValues?.[0] ?? '').trim().slice(0, 24);
    if (!m.canceled && name) {
      const list = gates();
      const g = list.find((x) => x.id === here.id);
      if (g) g.name = name;
      store(list);
      safe(() => p.sendMessage(`§bWaygate renamed: §f${name}`));
    }
  }
}

system.beforeEvents.startup.subscribe((ev) => {
  ev.blockComponentRegistry.registerCustomComponent('bc:waygate', {
    onPlayerInteract(e) {
      const p = e.player;
      if (!(p instanceof Player)) return;
      const loc = { ...e.block.location };
      system.run(() => openGate(p, loc).catch(() => {}));
    },
  });
});

