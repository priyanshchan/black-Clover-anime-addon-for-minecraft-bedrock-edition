// The Magic Forge (v0.8.0): forge the eight armour sets from the spoils of your battles, and upgrade the piece in your
// hand - reinforce it (+1 to +5), inscribe a rune, sew a squad robe onto a chestplate as a mantle (its perk comes along),
// or salvage it for half its materials. The Armoury (also in the Handbook) explains every set and where its makings drop.
import { ItemStack, Player, system } from '@minecraft/server';
import { ActionFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { emit } from '../core/bus.js';
import { PIECES, bonusLines, damageTakenMul, gearOf, pieceId, pieceName, readUpgrades, writeUpgrades } from '../core/armor.js';
import { particle, rgb, sound } from '../core/fx.js';
import { isCreative, safe } from '../core/util.js';
import { EquipmentSlot } from '@minecraft/server';
import { affixLine, readRoll, reforge } from '../core/loot.js';

const A = DATA.armor;
const SLOT_NAME = { head: 'Helmet', chest: 'Chestplate', legs: 'Leggings', feet: 'Boots' };
const NAMES = { 'bc:mana_crystal': 'Mana Crystal', 'bc:leviathan_scale': 'Leviathan Scale', 'minecraft:gold_ingot': 'Gold Ingot', 'minecraft:diamond': 'Diamond' };

export function itemName(id) {
  const key = id.replace(/^bc:/, '');
  const n = A.materials[key]?.name ?? (key.startsWith('rune_') ? A.runes[key.slice(5)]?.name : undefined) ?? NAMES[id] ?? id;
  return String(n).replace(/§./g, '');
}
function mobName(id) {
  return id.replace(/^bc:/, '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}
function stars(p) {
  const v = safe(() => p.getDynamicProperty('bc:stars'));
  return typeof v === 'number' ? v : 0;
}
function rankAt(n) {
  return DATA.ranks.find((r) => r.stars === n)?.title ?? `${n} stars`;
}

// ------------------------------------------------------------------------------- the pack
function inv(p) {
  return safe(() => p.getComponent('minecraft:inventory')?.container);
}
export function count(p, id) {
  const c = inv(p);
  let n = 0;
  if (!c) return 0;
  for (let i = 0; i < c.size; i++) {
    const it = c.getItem(i);
    if (it?.typeId === id) n += it.amount;
  }
  return n;
}
function take(p, id, amount) {
  const c = inv(p);
  let left = amount;
  for (let i = 0; c && i < c.size && left > 0; i++) {
    const it = c.getItem(i);
    if (it?.typeId !== id) continue;
    const k = Math.min(left, it.amount);
    left -= k;
    if (it.amount > k) {
      it.amount -= k;
      c.setItem(i, it);
    } else c.setItem(i, undefined);
  }
}
function give(p, item) {
  const left = inv(p)?.addItem(item);
  if (left) safe(() => p.dimension.spawnItem(left, p.location));
}
/** Pay a list of [item, count]; false (and nothing taken) if the pack is short. Creative players pay nothing. */
function pay(p, list) {
  if (isCreative(p)) return true;
  const short = list.filter(([id, n]) => count(p, id) < n);
  if (short.length) {
    safe(() => p.sendMessage(`§cYou need: §f${short.map(([id, n]) => `${n - count(p, id)} more ${itemName(id)}`).join(', ')}`));
    return false;
  }
  for (const [id, n] of list) if (n > 0) take(p, id, n);
  return true;
}
function costText(list) {
  return list.filter(([, n]) => n > 0).map(([id, n]) => `${n} ${itemName(id)}`).join(', ');
}

/** What one piece costs: the set material, mana-steel ingots and mana crystals (and gold and diamonds for the Royal set). */
export function costOf(sid, slot) {
  const [mat, ingots, crystals] = A.cost[slot];
  const s = A.sets[sid];
  const list = s.material === 'mana_steel_ingot' ? [['bc:mana_steel_ingot', mat + ingots]] : [[`bc:${s.material}`, mat], ['bc:mana_steel_ingot', ingots]];
  list.push(['bc:mana_crystal', crystals]);
  for (const [id, n] of A.extra[sid]?.[slot] ?? []) list.push([id, n]);
  return list;
}
export function reinforceCost(level) {
  const [ingots, crystals, diamonds] = A.reinforceCost[String(level)];
  return [['bc:mana_steel_ingot', ingots], ['bc:mana_crystal', crystals], ['minecraft:diamond', diamonds]];
}

function fx(p, color = 'ffb040') {
  sound(p.dimension, 'random.anvil_use', p.location, 0.8, 1.1);
  particle(p.dimension, 'bc:flame_burst', p.location, { scale: 0.5 });
  particle(p.dimension, 'bc:burst_spark', p.location, { color: rgb(color), scale: 0.6 });
}

/** The armour piece in the main hand, with its upgrades. */
function heldPiece(p) {
  const c = inv(p);
  const item = c?.getItem(p.selectedSlotIndex);
  const pc = item ? PIECES[item.typeId] : undefined;
  return pc ? { item, pc, up: readUpgrades(item), slot: p.selectedSlotIndex } : undefined;
}
function putBack(p, h) {
  inv(p)?.setItem(h.slot, h.item);
}

// ------------------------------------------------------------------------------- forging
export function forgePiece(p, sid, slot) {
  const s = A.sets[sid];
  if (stars(p) < s.stars && !isCreative(p)) {
    safe(() => p.sendMessage(`§7The ${s.mc}${s.name}§7 set is forged only for knights of rank §f${rankAt(s.stars)}§7 (${s.stars} stars) and above.`));
    return false;
  }
  if (!pay(p, costOf(sid, slot))) return false;
  give(p, new ItemStack(pieceId(sid, slot), 1));
  fx(p, s.glow);
  emit('forge', p, sid);
  safe(() => p.sendMessage(`§6Forged: ${s.mc}${s.pieces[A.slots.indexOf(slot)]}§6.`));
  return true;
}

export function reinforce(p) {
  const h = heldPiece(p);
  if (!h) return false;
  if (h.up.plus >= A.reinforceMax) {
    safe(() => p.sendMessage('§7That piece cannot be reinforced any further.'));
    return false;
  }
  const next = h.up.plus + 1;
  if (!pay(p, reinforceCost(next))) return false;
  h.up.plus = next;
  writeUpgrades(h.item, h.up);
  putBack(p, h);
  fx(p, '9ad0ff');
  emit('reinforce', p, next);
  safe(() => p.sendMessage(`§6${pieceName(h.item.typeId)}§6 reinforced to §f+${next}§6 (-${(next * A.reinforcePct).toFixed(1)}% damage taken).`));
  return true;
}

export function inscribe(p, rid) {
  const h = heldPiece(p);
  if (!h || !A.runes[rid]) return false;
  if (!isCreative(p) && count(p, `bc:rune_${rid}`) < 1) return false;
  if (!isCreative(p)) take(p, `bc:rune_${rid}`, 1);
  const old = h.up.rune;
  h.up.rune = rid;
  writeUpgrades(h.item, h.up);
  putBack(p, h);
  fx(p, A.runes[rid].color);
  emit('rune', p, rid);
  safe(() => p.sendMessage(`§d${A.runes[rid].name}§7 inscribed: ${A.runes[rid].desc}.${old ? ` §8(the ${A.runes[old].name} it replaced is gone)` : ''}`));
  return true;
}

export function sewMantle(p, robeId) {
  const h = heldPiece(p);
  if (!h || h.pc.slot !== 'chest' || !DATA.robes[robeId]) return false;
  if (!isCreative(p) && count(p, `bc:${robeId}`) < 1) return false;
  if (!isCreative(p)) take(p, `bc:${robeId}`, 1);
  if (h.up.mantle) give(p, new ItemStack(`bc:${h.up.mantle}`, 1));
  h.up.mantle = robeId;
  writeUpgrades(h.item, h.up);
  putBack(p, h);
  fx(p, 'ffd060');
  safe(() => p.sendMessage(`§6The ${DATA.robes[robeId]}§6 is sewn on as a mantle: §7${DATA.robePerks[robeId]}.`));
  return true;
}

/** Break a piece down: half its materials back (at least one of the set material), and its mantle robe. */
export function salvage(p) {
  const h = heldPiece(p);
  if (!h) return false;
  inv(p)?.setItem(h.slot, undefined);
  const back = costOf(h.pc.set, h.pc.slot).map(([id, n]) => [id, Math.floor(n / 2)]);
  back[0][1] = Math.max(1, back[0][1]);
  for (const [id, n] of back) if (n > 0) give(p, new ItemStack(id, n));
  if (h.up.mantle) give(p, new ItemStack(`bc:${h.up.mantle}`, 1));
  sound(p.dimension, 'random.break', p.location, 0.8, 0.8);
  safe(() => p.sendMessage(`§7Salvaged: §f${costText(back)}${h.up.mantle ? ` and the ${DATA.robes[h.up.mantle]}` : ''}§7.`));
  return true;
}

// ------------------------------------------------------------------------------- the forge's menus
export async function openForge(p) {
  const h = heldPiece(p);
  const body = ['§7Forge armour from the spoils of your battles. Hold a piece of armour to reinforce it, inscribe a rune, sew on a squad mantle or salvage it.'];
  if (h) {
    body.push(`\n§fIn your hand: ${pieceName(h.item.typeId)}${h.up.plus ? ` §f+${h.up.plus}` : ''}`);
    if (h.up.rune) body.push(`§d${A.runes[h.up.rune].name}`);
    if (h.up.mantle) body.push(`§6Mantle: ${DATA.robes[h.up.mantle]}`);
  }
  const f = new ActionFormData().title('§lMagic Forge').body(body.join('\n'));
  /** @type {(() => any)[]} */
  const acts = [];
  const btn = (label, act) => {
    f.button(label);
    acts.push(act);
  };
  btn('§lForge armour\n§r§8Eight sets, four pieces each', () => forgeMenu(p));
  if (h) {
    if (h.up.plus < A.reinforceMax) btn(`§lReinforce to +${h.up.plus + 1}\n§r§8${costText(reinforceCost(h.up.plus + 1))}`, () => reinforce(p));
    btn('§lInscribe a rune\n§r§8One rune per piece', () => runeMenu(p));
    if (h.pc.slot === 'chest') btn('§lSew a squad mantle\n§r§8A squad robe\'s perk, on your armour', () => mantleMenu(p));
    btn('§lSalvage\n§r§8Half its materials back', () => salvageMenu(p));
  }
  const rolled = heldRoll(p);
  if (rolled) btn(`§lReforge ${rolled.roll.name}\n§r§8Reroll its affixes: ${costText(reforgeCost(rolled.roll.rarity))}`, () => reforgeHeld(p));
  btn('§lThe Armoury\n§r§8Sets, bonuses, materials', () => armoryPage(p, () => openForge(p)));
  f.button('§8Close');
  const r = await f.show(p);
  if (r.canceled || r.selection === undefined || r.selection >= acts.length) return;
  await acts[r.selection]();
}

// ------------------------------------------------------------------------------- v1.1.0: reforging relics and weapons
function heldRoll(p) {
  const item = safe(() => p.getComponent('minecraft:equippable')?.getEquipment(EquipmentSlot.Mainhand));
  const roll = item ? readRoll(item) : undefined;
  return roll ? { item, roll } : undefined;
}
/** What a reroll costs: mana crystals, sprite dust and star fragments, by rarity. */
export function reforgeCost(rarity) {
  const [c, d, s] = DATA.loot.reforge[rarity] ?? [2, 0, 0];
  return [['bc:mana_crystal', c], ['bc:sprite_dust', d], ['bc:star_fragment', s]];
}
NAMES['bc:sprite_dust'] = 'Sprite Dust';
NAMES['bc:star_fragment'] = 'Star Fragment';
/** Reroll the affixes of the relic or weapon in the hand (keeping its rarity). */
export function reforgeHeld(p) {
  const h = heldRoll(p);
  if (!h || !pay(p, reforgeCost(h.roll.rarity))) return false;
  const before = Object.entries(h.roll.affixes).map(([k, v]) => affixLine(h.roll.kind, k, v)).join('§7, ');
  const roll = reforge(h.item);
  if (!roll) return false;
  safe(() => p.getComponent('minecraft:equippable')?.setEquipment(EquipmentSlot.Mainhand, h.item));
  const after = Object.entries(roll.affixes).map(([k, v]) => affixLine(roll.kind, k, v)).join('§7, ');
  particle(p.dimension, 'bc:burst_spark', p.location, { color: rgb('ff70e0'), scale: 1 });
  sound(p.dimension, 'random.anvil_use', p.location, 0.8, 1.3);
  safe(() => p.sendMessage(`§dReforged: §8${before.replace(/§./g, '')} §7-> §f${after}`));
  emit('reforge', p);
  return true;
}

async function forgeMenu(p) {
  const sets = Object.keys(A.sets);
  const f = new ActionFormData().title('Forge armour').body('§7Choose a set. Its materials drop from the foes that suit it - see the Armoury.');
  for (const sid of sets) {
    const s = A.sets[sid];
    const locked = stars(p) < s.stars && !isCreative(p);
    const mat = `bc:${s.material}`;
    f.button(`${s.mc}§l${s.name}\n§r§8${locked ? `§cneeds ${rankAt(s.stars)}` : `${itemName(mat)}: ${count(p, mat)}`}`);
  }
  f.button('§8Back');
  const r = await f.show(p);
  if (r.canceled || r.selection === undefined) return;
  if (r.selection >= sets.length) return openForge(p);
  await pieceMenu(p, sets[r.selection]);
}

async function pieceMenu(p, sid) {
  const s = A.sets[sid];
  const f = new ActionFormData().title(`${s.name}`).body(`§7Set bonus (2 pieces): §f${s.b2}\n§7Set bonus (4 pieces): §f${s.b4}`);
  A.slots.forEach((slot, i) => {
    const cost = costOf(sid, slot);
    const ok = isCreative(p) || cost.every(([id, n]) => count(p, id) >= n);
    f.button(`${ok ? '§2' : '§0'}§l${s.pieces[i]}§r §8(${s.prot[i]} armour)\n§8${costText(cost)}`);
  });
  f.button('§8Back');
  const r = await f.show(p);
  if (r.canceled || r.selection === undefined) return;
  if (r.selection >= A.slots.length) return forgeMenu(p);
  forgePiece(p, sid, A.slots[r.selection]);
}

async function runeMenu(p) {
  const have = Object.keys(A.runes).filter((rid) => isCreative(p) || count(p, `bc:rune_${rid}`) > 0);
  if (!have.length) {
    safe(() => p.sendMessage('§7You have no runes. §fCraft one: two Rune Shards, a Mana Crystal and the rune\'s ingredient §7(see the Armoury).'));
    return;
  }
  const f = new ActionFormData().title('Inscribe a rune').body('§7One rune per piece; a new rune replaces the old one.');
  for (const rid of have) f.button(`§d§l${A.runes[rid].name}\n§r§8${A.runes[rid].desc}`);
  f.button('§8Back');
  const r = await f.show(p);
  if (r.canceled || r.selection === undefined) return;
  if (r.selection >= have.length) return openForge(p);
  inscribe(p, have[r.selection]);
}

async function mantleMenu(p) {
  const have = Object.keys(DATA.robes).filter((rid) => isCreative(p) || count(p, `bc:${rid}`) > 0);
  if (!have.length) {
    safe(() => p.sendMessage('§7Bring a squad robe to sew onto your chestplate.'));
    return;
  }
  const f = new ActionFormData().title('Sew a squad mantle').body('§7The robe is sewn onto the chestplate: you keep its perk while wearing the armour.');
  for (const rid of have) f.button(`§6§l${DATA.robes[rid]}\n§r§8${DATA.robePerks[rid]}`);
  f.button('§8Back');
  const r = await f.show(p);
  if (r.canceled || r.selection === undefined) return;
  if (r.selection >= have.length) return openForge(p);
  sewMantle(p, have[r.selection]);
}

async function salvageMenu(p) {
  const h = heldPiece(p);
  if (!h) return;
  const back = costOf(h.pc.set, h.pc.slot).map(([id, n]) => [id, Math.floor(n / 2)]);
  back[0][1] = Math.max(1, back[0][1]);
  const f = new ActionFormData().title('Salvage').body(`§7Break down ${pieceName(h.item.typeId)}§7?\n§fYou get back: ${costText(back)}${h.up.mantle ? ' and its mantle robe' : ''}.\n§cReinforcement and runes are lost.`);
  f.button('§c§lSalvage it');
  f.button('§8Keep it');
  const r = await f.show(p);
  if (!r.canceled && r.selection === 0) salvage(p);
}

// ------------------------------------------------------------------------------- the Armoury
export async function armoryPage(p, back) {
  const g = gearOf(p);
  const lines = ['§lWorn:'];
  for (const slot of A.slots) {
    const pc = g.pieces.find((x) => x.slot === slot);
    lines.push(pc ? `§f${pieceName(pc.id)}${pc.plus ? ` §f+${pc.plus}` : ''}${pc.rune ? ` §d(${A.runes[pc.rune].name})` : ''}` : `§8${SLOT_NAME[slot]}: none`);
  }
  const bonus = bonusLines(p);
  lines.push('', bonus.length ? `§lSet bonuses:\n${bonus.join('\n')}` : '§7Wear two pieces of a set for its first bonus, four for the second.');
  if (g.mantle) lines.push(`§6Mantle: ${DATA.robes[g.mantle]} §7- ${DATA.robePerks[g.mantle]}`);
  const all = 100 - damageTakenMul(p, false) * 100;
  const magic = 100 - damageTakenMul(p, true) * 100;
  if (all > 0 || magic > 0) lines.push(`§7Damage cut: §f${all.toFixed(1)}%§7 from every hit, §f${magic.toFixed(1)}%§7 from magic.`);
  lines.push('', '§7Craft a §bMagic Forge§7: mana crystals, an anvil, iron blocks, a blast furnace and stone bricks.');
  const sets = Object.keys(A.sets);
  const f = new ActionFormData().title('The Armoury').body(lines.join('\n'));
  for (const sid of sets) f.button(`${A.sets[sid].mc}§l${A.sets[sid].name}\n§r§8${itemName(`bc:${A.sets[sid].material}`)}`);
  f.button('§d§lRunes');
  f.button(back ? '§8Back' : '§8Close');
  const r = await f.show(p);
  if (r.canceled || r.selection === undefined) return;
  if (r.selection < sets.length) return setPage(p, sets[r.selection], () => armoryPage(p, back));
  if (r.selection === sets.length) return runesPage(p, () => armoryPage(p, back));
  if (back) await back();
}

async function setPage(p, sid, back) {
  const s = A.sets[sid];
  const mat = A.materials[s.material];
  const drops = s.material === 'leviathan_scale'
    ? ['the Abyssal Leviathan and the Storm Kraken', ...Object.keys(A.scaleDrops).map(mobName)].join(', ')
    : mat && Object.keys(mat.drops).length ? Object.entries(mat.drops).map(([id, [c, lo, hi]]) => `${mobName(id)} (${c >= 1 ? `${lo}-${hi}` : `${Math.round(c * 100)}%`})`).join(', ') : '';
  const lines = [
    ...s.pieces.map((n, i) => `§f${n} §8- ${s.prot[i]} armour - ${costText(costOf(sid, A.slots[i]))}`),
    '', `§7(2): §f${s.b2}`, `§7(4): §f${s.b4}`, '',
    `§7Material: §f${itemName(`bc:${s.material}`)}${mat ? ` §8- ${mat.desc}` : ''}`,
  ];
  if (drops) lines.push(`§7Dropped by: §f${drops}`);
  if (s.stars) lines.push(`§7Forged only for §f${rankAt(s.stars)}§7 (${s.stars} stars) and above.`);
  const f = new ActionFormData().title(s.name).body(lines.join('\n')).button('§8Back');
  await f.show(p);
  await back();
}

async function runesPage(p, back) {
  const lines = ['§7Craft a rune from two Rune Shards, a Mana Crystal and its ingredient, then inscribe it at a Magic Forge. One rune per piece; they stack across your armour.', ''];
  for (const r of Object.values(A.runes)) lines.push(`§d${r.name}: §f${r.desc} §8(ingredient: ${mobName(r.item.replace('minecraft:', ''))})`);
  lines.push('', `§7Reinforcement: up to §f+${A.reinforceMax}§7 per piece, each level cuts all damage by §f${A.reinforcePct}%§7.`);
  const f = new ActionFormData().title('Runes').body(lines.join('\n')).button('§8Back');
  await f.show(p);
  await back();
}

system.beforeEvents.startup.subscribe((ev) => {
  ev.blockComponentRegistry.registerCustomComponent('bc:magic_forge', {
    onPlayerInteract(e) {
      const p = e.player;
      if (!(p instanceof Player)) return;
      system.run(() => openForge(p).catch(() => {}));
    },
  });
});
