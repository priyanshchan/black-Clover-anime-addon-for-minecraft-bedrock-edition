// Kingdoms of the Marches (v1.2.0). Past the Forsaken Realm the land belongs to the neighbouring kingdoms:
// * the DIAMOND KINGDOM (the western Marches): crystal-armoured Legionnaires who fight with crystal and steel magic;
// * the SPADE KINGDOM (the northern Marches): hooded Zealots who fight with dark and gravity magic;
// * the HEART KINGDOM (the eastern Marches): spirit Guardians who are friendly - they fight monsters beside you, and the
//   priestess of each Heart Sanctum trades spirit relics and draughts.
// Diamond and Spade patrol their Marches, hold border forts under a Commander or Inquisitor, and carry spoils of war
// (Diamond Shards, Spade Sigils) that the Royal Capital's quartermaster buys.
import { Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { emit } from '../core/bus.js';
import { effect, targetsAround } from '../core/combat.js';
import { particle, rgb, sound } from '../core/fx.js';
import { addMods } from '../core/mods.js';
import { V, alive, pick, rand, safe } from '../core/util.js';
import { castSpec } from './engine.js';
import { makeElite } from './elites.js';
import { behind } from './events.js';
import { calm } from './omens.js';
import { realmAt, regionAt } from './regions.js';
import { inCapital } from './capital.js';

const K = DATA.kingdoms;
const SOLDIERS = Object.fromEntries(Object.entries(K).map(([k, v]) => [`bc:${v.soldier}`, k]));

/** Which kingdom holds this point ('' outside the Marches, and in the Southern Wilds). */
export function kingdomAt(loc) {
  const r = regionAt(loc.x, loc.z);
  if (r && r.kingdom !== undefined) return r.kingdom;
  return realmAt(loc.x, loc.z).kingdom ?? '';
}
export function kingdomOf(e) {
  return SOLDIERS[safe(() => e.typeId) ?? ''] ?? '';
}

// ------------------------------------------------------------------------------- soldiers cast their kingdom's magic
const castAt = new Map();
const OFFENSIVE = (sp) => sp.spec && sp.level <= 10 && !['wall', 'heal', 'buff', 'summon', 'leap', 'zone'].includes(sp.spec.t);
/** A spell from the kingdom's grimoires (crystal and steel, dark and gravity, plant and spirit). */
export function spellFor(attr) {
  const list = (DATA.spells[attr] ?? []).filter(OFFENSIVE);
  return list.length ? pick(list) : undefined;
}
system.runInterval(() => {
  const t = system.currentTick;
  for (const p of world.getAllPlayers()) {
    for (const [type, kid] of Object.entries(SOLDIERS)) {
      for (const e of safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 40, type })) ?? []) safe(() => {
        if ((castAt.get(e.id) ?? 0) > t) return;
        const kin = K[kid];
        const foe = kin.hostile
          ? targetsAround(e.dimension, e.location, 16, e).find((x) => x instanceof Player || x.typeId === 'bc:magic_knight')
          : targetsAround(e.dimension, e.location, 14, e).find((x) => safe(() => x.matches({ families: ['monster'] })) && !SOLDIERS[x.typeId]);
        if (!foe) return;
        const order = [...kin.kits].sort(() => Math.random() - 0.5);
        const attr = order.find((a) => spellFor(a));
        const sp = attr ? spellFor(attr) : undefined;
        if (!sp) return;
        castAt.set(e.id, t + 120 + Math.floor(Math.random() * 60));
        safe(() => e.playAnimation(`animation.bc.${kin.soldier}.cast`));
        castSpec(e, sp.spec, `a:${attr}`, 0.8, foe);
      });
    }
  }
}, 20);

// ------------------------------------------------------------------------------- patrols in the Marches
/** @type {((dim: any, at: any, devil: string) => any) | undefined} v1.3.0: the Spade Kingdom's devil hosts march with its patrols */
let patrolHost;
export function setPatrolHost(fn) {
  patrolHost = fn;
}
/** One roll of a border patrol for a player (exported for tests). */
export function patrol(p, roll = Math.random) {
  if (p.dimension.id !== 'minecraft:overworld' || calm() || inCapital(p.location)) return '';
  const kid = kingdomAt(p.location);
  if (!kid) return '';
  const kin = K[kid];
  const at = behind(p, 22, 32);
  if (!at) return '';
  if (kin.hostile) {
    if (roll() >= 0.14) return '';
    const n = 3 + Math.floor(roll() * 2);
    for (let i = 0; i < n; i++) {
      const e = safe(() => p.dimension.spawnEntity(`bc:${kin.soldier}`, V.add(at, { x: rand(-3, 3), y: 0.2, z: rand(-3, 3) })));
      if (e && i === 0 && roll() < 0.35) makeElite(e, undefined, 'champion');
    }
    if (kid === 'spade' && patrolHost && roll() < 0.3) safe(() => patrolHost?.(p.dimension, V.add(at, { x: 0, y: 0.2, z: -3 }), 'morvane'));
    safe(() => p.onScreenDisplay.setActionBar(`${kin.mc}A ${kin.name} patrol! §7They have seen you.`));
    return kid;
  }
  if (roll() >= 0.08) return '';
  for (let i = 0; i < 2; i++) safe(() => p.dimension.spawnEntity(`bc:${kin.soldier}`, V.add(at, { x: rand(-3, 3), y: 0.2, z: rand(-3, 3) })));
  safe(() => p.onScreenDisplay.setActionBar(`${kin.mc}Heart Guardians walk these woods. §7They nod to you as they pass.`));
  return kid;
}
system.runInterval(() => {
  for (const p of world.getAllPlayers()) safe(() => patrol(p), 'patrol');
}, 1200);

// a kingdom soldier falls
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const e = ev.deadEntity;
  const kid = kingdomOf(e);
  if (!kid) return;
  const k = ev.damageSource.damagingEntity;
  if (!(k instanceof Player)) return;
  if (K[kid].hostile) emit('kingdom_kill', k, kid);
  else safe(() => k.sendMessage('§dThe Heart Kingdom will remember this. §7(A Heart Guardian was a friend.)'));
}, 'kingdomDie'));

// ------------------------------------------------------------------------------- the Spirit Draught
/** @type {Map<string, number>} player id -> when the draught wears off (real time) */
const draught = new Map();
addMods((p) => ((draught.get(p?.id) ?? 0) > Date.now() ? { regen: 1.5 } : undefined));
export function drinkDraught(p) {
  draught.set(p.id, Date.now() + 180000);
  effect(p, 'regeneration', 180, 0, false);
  particle(p.dimension, 'bc:heal', p.location, { scale: 0.8 });
  particle(p.dimension, 'bc:burst_spark', V.add(p.location, { x: 0, y: 1, z: 0 }), { color: rgb('f8a0c0'), scale: 0.6 });
  sound(p.dimension, 'random.burp', p.location, 0.7, 1.3);
  safe(() => p.onScreenDisplay.setActionBar('§dThe Spirit Draught warms you: §7Regeneration and +50% mana regeneration for 3 minutes.'));
  return true;
}

export { alive };
