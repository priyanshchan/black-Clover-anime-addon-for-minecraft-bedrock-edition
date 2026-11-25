// Armour (v0.8.0): set bonuses that are effects or reactions, damage reduction, materials dropped by the foes that suit
// them, and companions wearing armour. The plain numbers (mana, power, cooldowns) live in core/armor.js.
// * EFFECTS - Devilhide fire resistance, Abyssal water breathing, Shadowweave speed, Chitin poison immunity, Runeplate
//   resistance, Vitality runes (Health Boost), Swiftness runes (Speed) and the Shadowweave vanish.
// * DAMAGE - reinforcement cuts every hit; Warding runes and Runeplate cut magic. Magic is cut before it lands (a damage
//   mod on hurt()); other hits are healed back by the same share just after. Evasion, thorns, barbs, rune pulses, the
//   Royal Aegis and Devilhide lifesteal react to hits.
// * COMPANIONS - hand a companion a piece of armour to wear: it shows on them and its bonuses work for them too.
import { ActionFormData } from '@minecraft/server-ui';
import { ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { emit } from '../core/bus.js';
import { PIECES, armorCdMul, armorPowerMul, bonusLines, damageTakenMul, gearOf, pieceName, readUpgrades, setGearProvider, writeUpgrades } from '../core/armor.js';
import { addDamageMod, center, effect, hurt, knock, ownerOf, targetsAround } from '../core/combat.js';
import { anim, particle, rgb, sound } from '../core/fx.js';
import { V, alive, isCreative, safe } from '../core/util.js';
import { heal } from './engine.js';
import { addInfo, addMemberButtons, addProfileLines, addTalkHandler, giveItem, memberOf, onMemberTick, save } from './companions.js';

const A = DATA.armor;
const SLOT_CMD = { head: 'slot.armor.head', chest: 'slot.armor.chest', legs: 'slot.armor.legs', feet: 'slot.armor.feet' };
/** @type {Map<string, number>} target id -> tick of a hit dealt through hurt() (already reduced) */
const scripted = new Map();
/** @type {Map<string, number>} player id -> tick they began to crouch still */
const stillSince = new Map();
/** @type {Set<string>} Shadowweave wearers hidden in the shadows */
const hidden = new Set();
const vitality = new Set();
const fullSeen = new Set();
const aegisCd = new Map();

function say(p, m, text) {
  safe(() => p.sendMessage(`§b${m.name}§f: ${text}`));
}
function hpFrac(e) {
  const h = safe(() => e.getComponent('minecraft:health'));
  return h ? h.currentValue / Math.max(1, h.effectiveMax) : 1;
}

// ------------------------------------------------------------------------------- set effects
function keep(e, id, amp) {
  effect(e, id, 3, amp, false);
}
/** Effects from the armour an entity wears (players every half second, companions on their tick). */
export function wearerTick(e, isPlayer) {
  const g = gearOf(e);
  const has = (sid, n) => (g.sets[sid] ?? 0) >= n;
  if (has('devilhide', 2) || has('wyvernscale', 2)) keep(e, 'fire_resistance', 0);
  if (has('abyssal', 2)) {
    keep(e, 'water_breathing', 0);
    if (safe(() => e.isInWater)) keep(e, 'conduit_power', 0);
  }
  const swift = g.runes.swiftness ?? 0;
  const speed = Math.max(has('shadow', 2) ? 0 : -1, swift >= 4 ? 1 : swift >= 2 ? 0 : -1);
  if (speed >= 0) keep(e, 'speed', speed);
  if (has('chitin', 2)) safe(() => e.removeEffect('poison'));
  if (has('chitin', 4) && hpFrac(e) < 0.5) keep(e, 'regeneration', 0);
  if (has('runeplate', 4)) keep(e, 'resistance', 0);
  // Vitality runes: Health Boost, only re-applied when it changes or runs low (so health is not reset)
  const vit = g.runes.vitality ?? 0;
  const cur = safe(() => e.getEffect('health_boost'));
  if (vit > 0) {
    if (!cur || cur.amplifier !== vit - 1 || cur.duration < 200) safe(() => e.addEffect('health_boost', 2400, { amplifier: vit - 1, showParticles: false }));
    vitality.add(e.id);
  } else if (vitality.has(e.id)) {
    vitality.delete(e.id);
    if (cur) safe(() => e.removeEffect('health_boost'));
  }
  if (!isPlayer) return;
  const t = system.currentTick;
  // Shadowweave (4): crouch still for two seconds to vanish
  if (has('shadow', 4)) {
    const v = safe(() => e.getVelocity()) ?? { x: 0, y: 0, z: 0 };
    if (e.isSneaking && Math.abs(v.x) + Math.abs(v.z) < 0.03) {
      if (!stillSince.has(e.id)) stillSince.set(e.id, t);
      if (t - (stillSince.get(e.id) ?? t) >= 40 && !hidden.has(e.id)) {
        hidden.add(e.id);
        effect(e, 'invisibility', 30, 0, false);
        particle(e.dimension, 'bc:smoke_burst', center(e), { scale: 0.6 });
        safe(() => e.onScreenDisplay.setActionBar('§8You melt into the shadows... §7your next blow lands twice.'));
      }
    } else stillSince.delete(e.id);
    if (hidden.has(e.id) && !safe(() => e.getEffect('invisibility'))) hidden.delete(e.id);
  } else {
    hidden.delete(e.id);
    stillSince.delete(e.id);
  }
  // wearing a whole set (for the feats)
  for (const [sid, n] of Object.entries(g.sets)) {
    const key = `${e.id}:${sid}`;
    if (n < 4 || fullSeen.has(key)) continue;
    fullSeen.add(key);
    emit('armor_set', e, sid);
    safe(() => e.onScreenDisplay.setActionBar(`${A.sets[sid].mc}Full set: ${A.sets[sid].name} §7- ${A.sets[sid].b4}`));
  }
}
system.runInterval(() => {
  for (const p of world.getAllPlayers()) safe(() => wearerTick(p, true), 'armorTick');
}, 10);
world.afterEvents.playerLeave.subscribe((ev) => {
  for (const k of [...fullSeen]) if (k.startsWith(`${ev.playerId}:`)) fullSeen.delete(k);
});

function reveal(e) {
  hidden.delete(e.id);
  stillSince.delete(e.id);
  safe(() => e.removeEffect('invisibility'));
  particle(e.dimension, 'bc:burst_dark', center(e), { scale: 0.6 });
}

// ------------------------------------------------------------------------------- damage
// magic (anything dealt through hurt()) is cut before it lands
addDamageMod((target, attacker, amount) => {
  scripted.set(target.id, system.currentTick);
  let dmg = amount;
  if (gearOf(target).pieces.length) dmg *= damageTakenMul(target, true);
  if (attacker && hidden.has(attacker.id)) {
    dmg *= 2;
    reveal(attacker);
  }
  if (attacker && dmg > 0 && alive(attacker) && (gearOf(attacker).sets.devilhide ?? 0) >= 4) heal(attacker, dmg * 0.08);
  return dmg;
});

world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const e = ev.hurtEntity;
  const t = system.currentTick;
  const src = ev.damageSource.damagingEntity;
  const cause = ev.damageSource.cause;
  const viaHurt = scripted.get(e.id) === t;
  if (viaHurt) scripted.delete(e.id);
  // a hidden Shadowweave wearer's first blow lands twice
  if (!viaHurt && src && hidden.has(src.id) && cause === 'entityAttack') {
    reveal(src);
    hurt(e, ev.damage, src);
    sound(e.dimension, 'random.break', e.location, 0.6, 1.6);
  }
  if (!alive(e)) return;
  const g = gearOf(e);
  if (!g.pieces.length) return;
  const has = (sid, n) => (g.sets[sid] ?? 0) >= n;
  const melee = cause === 'entityAttack' && !!src && V.dist(src.location, e.location) < 6;
  if (!viaHurt) {
    // Shadowweave (4): evasion
    if (melee && has('shadow', 4) && Math.random() < 0.2) {
      heal(e, ev.damage);
      particle(e.dimension, 'bc:smoke_burst', center(e), { scale: 0.5 });
      if (e instanceof Player) safe(() => e.onScreenDisplay.setActionBar('§8Evaded!'));
      return;
    }
    let back = ev.damage * (1 - damageTakenMul(e, false));
    if (has('runeplate', 2) && ['fall', 'entityExplosion', 'blockExplosion'].includes(cause)) back += ev.damage * 0.4;
    // v1.1.0: Wyvernscale - no fall damage (2), and fire and lightning hurt 40% less (4)
    if (has('wyvernscale', 2) && cause === 'fall') back = ev.damage;
    else if (has('wyvernscale', 4) && ['fire', 'fire_tick', 'lava', 'lightning', 'magma'].includes(cause)) back += ev.damage * 0.4;
    if (back > 0) heal(e, back);
  }
  // Thorns runes and Chitin barbs
  if (melee && alive(src)) {
    const thorns = (g.runes.thorns ?? 0) + (has('chitin', 4) ? 3 : 0);
    if (thorns > 0) {
      hurt(src, thorns, e, 'thorns');
      if (has('chitin', 4)) effect(src, 'poison', 4, 0);
      particle(e.dimension, 'bc:shard_burst', center(src), { color: rgb('6ad040'), scale: 0.4 });
    }
  }
  // Runeplate (4): a rune pulse
  if (has('runeplate', 4) && src && Math.random() < 0.15) {
    particle(e.dimension, 'bc:shockwave', e.location, { color: rgb('60e0ff'), radius: 4 });
    sound(e.dimension, 'bc.golem.slam', e.location, 0.7, 1.3);
    for (const v of targetsAround(e.dimension, e.location, 4, e)) {
      hurt(v, 4, e);
      knock(v, V.sub(v.location, e.location), 1.4, 0.4);
    }
  }
  // Royal Knight (4): the Royal Aegis
  if (has('royal', 4) && hpFrac(e) < 0.3 && (aegisCd.get(e.id) ?? 0) < t) {
    aegisCd.set(e.id, t + 1200);
    effect(e, 'absorption', 6, 2, false);
    effect(e, 'resistance', 6, 1, false);
    particle(e.dimension, 'bc:light_burst', center(e), { color: rgb('ffe58a'), scale: 1 });
    sound(e.dimension, 'bc.light.shine', e.location, 1, 1.2);
    if (e instanceof Player) safe(() => e.onScreenDisplay.setActionBar('§eRoyal Aegis! §7The crown shields you.'));
  }
}, 'armorHurt'));

// ------------------------------------------------------------------------------- materials from the foes that suit them
function drop(dim, loc, item, [chance, lo, hi]) {
  if (Math.random() >= chance) return;
  safe(() => dim.spawnItem(new ItemStack(item, lo + Math.floor(Math.random() * (hi - lo + 1))), loc));
}
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const dead = ev.deadEntity;
  const k = ev.damageSource.damagingEntity;
  if (!(k instanceof Player) && !(k && ownerOf(k))) return;
  const id = dead.typeId;
  const loc = { ...dead.location };
  const dim = dead.dimension;
  for (const [mat, m] of Object.entries(A.materials)) if (m.drops[id]) drop(dim, loc, `bc:${mat}`, m.drops[id]);
  if (A.scaleDrops[id]) drop(dim, loc, 'bc:leviathan_scale', A.scaleDrops[id]);
  // elites carry the makings of armour
  if (typeof safe(() => dead.getDynamicProperty('bc:elite')) === 'string') {
    const mats = Object.keys(A.materials).filter((x) => x !== 'mana_steel_ingot');
    drop(dim, loc, `bc:${mats[Math.floor(Math.random() * mats.length)]}`, [0.3, 1, 2]);
  }
}, 'armorDrops'));

// ------------------------------------------------------------------------------- companions wear armour
/** @typedef {{id: string, plus: number, rune: string, mantle: string, dmg?: number}} Worn */
/** The armour a companion wears, as items to hand back. */
export function toItem(w) {
  const it = new ItemStack(w.id, 1);
  writeUpgrades(it, w);
  if (w.dmg) safe(() => (it.getComponent('minecraft:durability').damage = w.dmg));
  return it;
}
setGearProvider((e) => {
  if (e.typeId !== 'bc:magic_knight') return undefined;
  const mo = memberOf(e);
  if (!mo?.m.armor) return [];
  return Object.values(mo.m.armor).filter((w) => w && PIECES[w.id]).map((w) => ({ ...w, ...PIECES[w.id] }));
});

/** @type {Map<string, string>} companion entity id -> the armour it is shown wearing */
const shown = new Map();
function dress(e, m) {
  const sig = A.slots.map((s) => m.armor?.[s]?.id ?? '').join(',');
  if (shown.get(e.id) === sig) return;
  shown.set(e.id, sig);
  for (const s of A.slots) safe(() => e.runCommand(`replaceitem entity @s ${SLOT_CMD[s]} 0 ${m.armor?.[s]?.id ?? 'air'}`));
}
onMemberTick((p, m, e) => {
  if (!m.armor || !Object.values(m.armor).some(Boolean)) return;
  dress(e, m);
  wearerTick(e, false);
});
addInfo((e, p, m, info) => {
  info.pwMul *= armorPowerMul(e, hpFrac(e));
  info.cdMul *= armorCdMul(e);
  // Royal Knight (4): companions near you fight harder
  if ((gearOf(p).sets.royal ?? 0) >= 4 && V.dist(p.location, e.location) <= 16) info.pwMul *= 1.1;
});

addTalkHandler((p, e, m, id) => {
  const pc = PIECES[id];
  if (!pc) return false;
  const inv = p.getComponent('minecraft:inventory')?.container;
  const held = inv?.getItem(p.selectedSlotIndex);
  if (!inv || held?.typeId !== id) return false;
  m.armor = m.armor ?? {};
  const old = m.armor[pc.slot];
  if (old) giveItem(p, toItem(old));
  const dmg = safe(() => held.getComponent('minecraft:durability')?.damage) ?? 0;
  m.armor[pc.slot] = { id, ...readUpgrades(held), dmg };
  if (!isCreative(p)) inv.setItem(p.selectedSlotIndex, undefined);
  shown.delete(e.id);
  dress(e, m);
  save(p);
  anim(e, 'animation.bc.magic_knight.salute');
  sound(e.dimension, 'armor.equip_iron', e.location, 1, 1);
  const n = Object.values(m.armor).filter((w) => w && PIECES[w.id]?.set === pc.set).length;
  say(p, m, `${pieceName(id)}§f? It fits${n >= 4 ? ' - and with the whole set, I feel unstoppable!' : '.'}`);
  return true;
});

addMemberButtons((p, m) => {
  const worn = A.slots.filter((s) => m.armor?.[s]);
  if (!worn.length) return [];
  return [{ label: `§lArmour\n§r§8${worn.length} piece${worn.length > 1 ? 's' : ''} - take some back`, act: async () => {
    const f = new ActionFormData().title(`${m.name}'s armour`).body(['§7Hand them a piece of armour to wear it.', ...bonusLinesOf(m)].join('\n'));
    for (const s of worn) f.button(`§l${pieceName(m.armor[s].id)}\n§r§8take it back`);
    f.button('§lTake back everything');
    f.button('§8Close');
    const r = await f.show(p);
    if (r.canceled || r.selection === undefined) return;
    const pick = r.selection < worn.length ? [worn[r.selection]] : r.selection === worn.length ? worn : [];
    for (const s of pick) {
      giveItem(p, toItem(m.armor[s]));
      delete m.armor[s];
    }
    if (pick.length) {
      save(p);
      const e = world.getEntity(m.eid ?? '');
      if (e) {
        shown.delete(e.id);
        dress(e, m);
      }
    }
  } }];
});

function bonusLinesOf(m) {
  const sets = {};
  for (const w of Object.values(m.armor ?? {})) if (w && PIECES[w.id]) sets[PIECES[w.id].set] = (sets[PIECES[w.id].set] ?? 0) + 1;
  const out = [];
  for (const [sid, n] of Object.entries(sets)) {
    const s = A.sets[sid];
    if (n >= 2) out.push(`${s.mc}${s.name} (2): §7${s.b2}`);
    if (n >= 4) out.push(`${s.mc}${s.name} (4): §7${s.b4}`);
  }
  return out;
}
addProfileLines((m) => {
  const worn = A.slots.map((s) => m.armor?.[s]).filter(Boolean);
  if (!worn.length) return [];
  return [`§7Armour: §f${worn.map((w) => `${pieceName(w.id).replace(/§./g, '')}${w.plus ? ` +${w.plus}` : ''}`).join(', ')}`, ...bonusLinesOf(m)];
});

export { bonusLines, hidden };
