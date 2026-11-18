// Passive powers of the wave-4 Abyss Fruits.
import { InputButton, ButtonState, Player, system, world } from '@minecraft/server';
import { effect, hurt, targetsAround } from '../core/combat.js';
import { particle, rgb } from '../core/fx.js';
import { safe } from '../core/util.js';
import { drained, isSealed } from '../sea/fruits.js';
import { sea } from '../sea/state.js';
import { heal } from './engine.js';

function active(p) {
  const fid = sea(p).fruit;
  if (!fid || isSealed(p) || drained(p)) return '';
  return fid;
}

system.runInterval(() => {
  const t = system.currentTick;
  for (const p of world.getAllPlayers()) {
    const fid = active(p);
    if (!fid) continue;
    safe(() => {
      const v = p.getVelocity();
      if (fid === 'lava' || fid === 'wyvern' || fid === 'phoenix') effect(p, 'fire_resistance', 2, 0, false);
      if ((fid === 'thread' || fid === 'slime') && p.isFalling && v.y < -0.5) effect(p, 'slow_falling', 1, 0, false);
      if (fid === 'lion') effect(p, 'strength', 2, 0, false);
      if (fid === 'spider' && t % 40 === 0) effect(p, 'night_vision', 12, 0, false);
      if (fid === 'shark' && p.isInWater) {
        effect(p, 'water_breathing', 2, 0, false);
        effect(p, 'conduit_power', 2, 0, false);
        effect(p, 'speed', 2, 1, false);
      }
      if (fid === 'phoenix' && p.isFalling && v.y < -0.4 && p.inputInfo.getButtonState(InputButton.Jump) === ButtonState.Pressed) effect(p, 'slow_falling', 1, 0, false);
      if (fid === 'prism' && t % 40 === 0) effect(p, 'night_vision', 12, 0, false);
      if (fid === 'bounce') {
        effect(p, 'jump_boost', 2, 1, false);
        if (p.isFalling && v.y < -0.5) effect(p, 'slow_falling', 1, 0, false);
      }
      if (fid === 'acid') safe(() => p.removeEffect('poison'));
      if (fid === 'cloud' && p.isFalling && p.isSneaking) effect(p, 'slow_falling', 1, 0, false);
      if (fid === 'bear') effect(p, 'resistance', 2, 0, false);
      if (fid === 'tiger') {
        effect(p, 'speed', 2, 1, false);
        if (t % 40 === 0) effect(p, 'night_vision', 12, 0, false);
      }
      if (fid === 'wyvern') {
        if (p.isFalling && v.y < -0.4 && p.inputInfo.getButtonState(InputButton.Jump) === ButtonState.Pressed) {
          effect(p, 'slow_falling', 1, 0, false);
        }
      }
    });
  }
}, 5);

world.afterEvents.entityHurt.subscribe((ev) => {
  const p = ev.hurtEntity;
  if (!(p instanceof Player)) return;
  const fid = active(p);
  if (!fid) return;
  safe(() => {
    const src = ev.damageSource;
    if (fid === 'ash' && Math.random() < 0.25 && src.cause !== 'fall') {
      heal(p, ev.damage);
      particle(p.dimension, 'bc:dust_burst', p.location, { color: rgb('8a8a94'), scale: 1 });
    } else if (fid === 'lodestone' && src.cause === 'projectile' && Math.random() < 0.4) {
      heal(p, ev.damage);
      particle(p.dimension, 'bc:shard_burst', p.location, { color: rgb('c8d0dc'), scale: 0.6 });
    } else if (fid === 'spore' && src.damagingEntity && src.damagingEntity.id !== p.id) {
      effect(src.damagingEntity, 'poison', 3, 0);
      particle(p.dimension, 'bc:dust_burst', p.location, { color: rgb('c8a070'), scale: 0.6 });
    } else if (fid === 'ink' && src.damagingEntity && src.damagingEntity.id !== p.id) {
      effect(src.damagingEntity, 'blindness', 3, 0);
      particle(p.dimension, 'bc:dust_burst', p.location, { color: rgb('1a1430'), scale: 0.8 });
    }
  });
});

// Blast Fruit: punches go off with a small blast; Chain Fruit: punches hit like a hammer
world.afterEvents.entityHitEntity.subscribe((ev) => {
  const p = ev.damagingEntity;
  if (!(p instanceof Player)) return;
  if (active(p) === 'chain') {
    hurt(ev.hitEntity, 3, p);
    particle(p.dimension, 'bc:burst_spark', ev.hitEntity.location, { color: rgb('c8d0dc'), scale: 0.4 });
    return;
  }
  if (active(p) !== 'blast') return;
  safe(() => {
    const at = ev.hitEntity.location;
    particle(p.dimension, 'bc:flame_burst', at, { scale: 0.4 });
    for (const t of targetsAround(p.dimension, at, 1.8, p)) hurt(t, 3, p, 'entityExplosion');
  });
});
