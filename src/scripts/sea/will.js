// Will: an original fighting-spirit system trained by combat.
//   Lv 1  Iron Will      - melee hits spend Will for bonus damage
//   Lv 3  Keen Will      - chance to sidestep a hit (the damage is undone)
//   Lv 8  Sovereign Will - Sneak + Jump at full Will: a pulse that floors weak enemies
import { ButtonState, InputButton, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { canHit, center, effect, hurt, knock, knockFrom, targetsAround } from '../core/combat.js';
import { particle, rgb, shakeArea, shockwave, sound, title } from '../core/fx.js';
import { V, safe } from '../core/util.js';
import { addWill, sea, willToNext } from './state.js';

const MAX = DATA.willMax;
const sovereignCd = new Map();

export function addWillXp(p, amount) {
  const s = sea(p);
  if (s.willLv >= MAX) return;
  s.willXp += amount;
  s.dirty = true;
  while (s.willLv < MAX && s.willXp >= willToNext(s.willLv)) {
    s.willXp -= willToNext(s.willLv);
    s.willLv++;
    const unlocks = { 1: 'Iron Will - your strikes carry your spirit', 3: 'Keen Will - you sense blows before they land', 8: 'Sovereign Will - Sneak + Jump at full Will' };
    const fourth = s.fruit ? DATA.fruits[s.fruit]?.abilities.find((a) => a.will === s.willLv) : undefined;
    if (fourth) unlocks[s.willLv] = `Fruit awakening - ${fourth.name} (your fruit's fourth move)`;
    title(p, `§5${DATA.glyphs.will} Will ${s.willLv}`, unlocks[s.willLv] ? `§d${unlocks[s.willLv]}` : '§7Your spirit hardens', 50);
    sound(p.dimension, 'bc.will.pulse', p.location, 0.8, 1.2);
    particle(p.dimension, 'bc:will_spark', V.add(p.location, { x: 0, y: 1, z: 0 }), { scale: 1 });
  }
}

/** Iron Will: called on every melee hit by a player. */
export function onWillMelee(p, target) {
  if (!canHit(p, target)) return;
  const s = sea(p);
  addWillXp(p, 1);
  if (s.willLv < 1 || s.will < 6) return;
  s.will -= 6;
  s.dirty = true;
  hurt(target, 2 + s.willLv, p);
  particle(p.dimension, 'bc:will_spark', center(target), { scale: 0.6 });
  if (s.willLv >= 5) particle(p.dimension, 'bc:anti_crackle', center(target), { radius: 0.6 });
}

/** Keen Will: undo a hit and sidestep. */
world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const p = ev.hurtEntity;
  if (!(p instanceof Player)) return;
  const cause = ev.damageSource.cause;
  if (cause !== 'entityAttack' && cause !== 'projectile') return;
  const s = sea(p);
  addWillXp(p, 1);
  if (s.willLv < 3 || s.will < 12) return;
  const chance = 0.05 + s.willLv * 0.02 + (s.fruit === 'quicksilver' ? 0.1 : 0);
  if (Math.random() > chance) return;
  const hp = p.getComponent('minecraft:health');
  if (!hp || hp.currentValue <= 0) return;
  safe(() => hp.setCurrentValue(Math.min(hp.effectiveMax, hp.currentValue + ev.damage)));
  s.will -= 12;
  s.dirty = true;
  const att = ev.damageSource.damagingEntity;
  const away = att ? V.sub(p.location, att.location) : p.getViewDirection();
  const side = V.norm({ x: -away.z, y: 0, z: away.x });
  knock(p, Math.random() < 0.5 ? side : V.mul(side, -1), 0.9, 0.1);
  particle(p.dimension, 'bc:will_spark', V.add(p.location, { x: 0, y: 1, z: 0 }), { scale: 0.8 });
  sound(p.dimension, 'mob.endermen.portal', p.location, 0.4, 2);
  safe(() => p.onScreenDisplay.setActionBar('§d§lKeen Will §r§7- dodged!'));
  addWillXp(p, 2);
}, 'keen'));

/** Sovereign Will: Sneak + Jump at full Will. */
function sovereign(p) {
  const s = sea(p);
  const t = system.currentTick;
  if ((sovereignCd.get(p.id) ?? 0) > t) return;
  sovereignCd.set(p.id, t + 1200);
  s.will = 0;
  s.dirty = true;
  const at = p.location;
  sound(p.dimension, 'bc.will.pulse', at, 1.6, 0.7);
  shockwave(p.dimension, at, 'dark', 14);
  particle(p.dimension, 'bc:shockwave', at, { radius: 14, color: rgb('8a46ff') });
  particle(p.dimension, 'bc:will_spark', V.add(at, { x: 0, y: 1, z: 0 }), { scale: 2 });
  shakeArea(p.dimension, at, 24, 0.6, 1.0);
  title(p, '§5§lSOVEREIGN WILL', '', 30);
  for (const e of targetsAround(p.dimension, at, 14, p)) {
    const hp = e.getComponent('minecraft:health');
    if (!hp) continue;
    if (hp.effectiveMax <= 30) {
      effect(e, 'slowness', 6, 9, false);
      effect(e, 'weakness', 6, 3, false);
      effect(e, 'mining_fatigue', 6, 3, false);
      effect(e, 'nausea', 6, 0, false);
      hurt(e, hp.currentValue * 0.5, p, 'magic');
      particle(p.dimension, 'bc:will_spark', center(e), { scale: 0.5 });
    } else {
      effect(e, 'slowness', 3, 1, false);
      knockFrom(e, at, 1.6, 0.4);
    }
  }
}

system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    const s = sea(p);
    if (s.will < 100) addWill(p, 1);
    const heldId = safe(() => p.getComponent('minecraft:inventory')?.container?.getItem(p.selectedSlotIndex)?.typeId) ?? '';
    if (s.willLv >= 8 && s.will >= 100 && p.isSneaking && !heldId.startsWith('bc:grimoire_')) {
      const jump = safe(() => p.inputInfo.getButtonState(InputButton.Jump));
      if (jump === ButtonState.Pressed) safe(() => sovereign(p), 'sovereign');
    }
  }
}, 10);

world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const k = ev.damageSource.damagingEntity;
  if (!(k instanceof Player)) return;
  const id = safe(() => ev.deadEntity.typeId) ?? '';
  if (id === 'bc:leviathan') addWillXp(k, 60);
  else if (id === 'bc:raider_captain' || id === 'bc:devil') addWillXp(k, 15);
  else if (safe(() => ev.deadEntity.matches({ families: ['monster'] }))) addWillXp(k, 4);
}, 'willKill'));
