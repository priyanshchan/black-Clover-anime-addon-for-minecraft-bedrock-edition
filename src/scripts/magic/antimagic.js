// Anti-magic: summoning demon swords, sword abilities, spell nullification and Black Form.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { HOSTILE_PROJECTILES, canHit, center, effect, hurt, knock, launch, muzzle, projectiles, targetsAlong } from '../core/combat.js';
import { state } from '../core/data.js';
import { anim, burst, particle, rgb, shake, shakeArea, shockwave, sound, title } from '../core/fx.js';
import { V, alive, clamp, isCreative, rand, repeat, safe } from '../core/util.js';

const SWORD_BY_SPELL = { demon_slayer: 'bc:demon_slayer_sword', demon_dweller: 'bc:demon_dweller_sword', demon_destroyer: 'bc:demon_destroyer_sword' };
const LORE = {
  'bc:demon_slayer_sword': ['§7A massive blade that cuts through magic.', '§8Use: §fBlack Meteorite §7(anti-magic slash)'],
  'bc:demon_dweller_sword': ['§7Absorbs magic and sends it back.', '§8Use: §fSpell Return'],
  'bc:demon_destroyer_sword': ['§7Its wounds cannot be healed by magic.', '§8Use: §fCurse-Breaker Thrust'],
};

function inBlackForm(p) {
  const t = p.getDynamicProperty('bc:black_form');
  return typeof t === 'number' && t > system.currentTick;
}

function inventory(p) {
  return p.getComponent('minecraft:inventory')?.container;
}

function hasItem(p, typeId) {
  const inv = inventory(p);
  if (!inv) return false;
  for (let i = 0; i < inv.size; i++) if (inv.getItem(i)?.typeId === typeId) return true;
  return false;
}

/** Grimoire "spells" of an anti-magic user. */
export const ANTI_SPELLS = {
  demon_slayer: (c) => drawSword(c.p, SWORD_BY_SPELL.demon_slayer),
  demon_dweller: (c) => drawSword(c.p, SWORD_BY_SPELL.demon_dweller),
  demon_destroyer: (c) => drawSword(c.p, SWORD_BY_SPELL.demon_destroyer),
  black_form(c) {
    const s = state(c.p);
    if (s.anti < 100 && !isCreative(c.p)) {
      safe(() => c.p.sendMessage(`§c${DATA.glyphs.clover5} The devil stirs, but your Anti-Magic gauge is only §f${Math.floor(s.anti)}%§c. Land sword hits to fill it.`));
      sound(c.dim, 'bc.mana.empty', c.p.location);
      return false;
    }
    s.anti = 0;
    s.dirty = true;
    const until = system.currentTick + 30 * 20;
    c.p.setDynamicProperty('bc:black_form', until);
    effect(c.p, 'strength', 30, 1, false);
    effect(c.p, 'speed', 30, 1, false);
    effect(c.p, 'resistance', 30, 0, false);
    effect(c.p, 'jump_boost', 30, 1, false);
    anim(c.p, 'animation.bc.player.cast_raise');
    title(c.p, '§0§lBLACK FORM', '§cThe devil lends you its power', 50);
    sound(c.dim, 'bc.blackform', c.p.location, 1.4, 1);
    shakeArea(c.dim, c.p.location, 24, 0.6, 1.2);
    shockwave(c.dim, c.p.location, 'anti', 7);
    particle(c.dim, 'bc:magic_circle_dark', c.p.location, { size: 6, life: 2 });
    for (let i = 0; i < 6; i++) particle(c.dim, 'bc:dark_lightning', V.add(c.p.location, { x: rand(-4, 4), y: 0, z: rand(-4, 4) }));
  },
};

function drawSword(p, typeId) {
  if (hasItem(p, typeId)) {
    safe(() => p.sendMessage(`§7Your ${DATA.swords[typeId.slice(3)]} is already with you.`));
    return false;
  }
  const item = new ItemStack(typeId, 1);
  safe(() => item.setLore([...(LORE[typeId] ?? []), `§8Bound to ${p.name}`]));
  const left = inventory(p)?.addItem(item);
  if (left) p.dimension.spawnItem(left, p.location);
  anim(p, 'animation.bc.player.cast_forward');
  const at = muzzle(p, 1.0, 0.2);
  particle(p.dimension, 'bc:anti_burst', at, { scale: 1 });
  particle(p.dimension, 'bc:slash_fx', at, { size: 2.5, rot: rand(-30, 30) });
  sound(p.dimension, 'bc.anti.slash', p.location, 1, 0.8);
  sound(p.dimension, 'random.anvil_land', p.location, 0.3, 0.6);
  return true;
}

// ----------------------------------------------------------------------- sword abilities
const swordCd = new Map(); // `${playerId}:${typeId}` -> tick

/** @param {import('@minecraft/server').Player} p */
export function useSword(p, typeId) {
  const s = state(p);
  if (s.attr !== 'anti' && !isCreative(p)) {
    safe(() => p.sendMessage('§8The blade is just cold, heavy steel to you. Only anti-magic awakens it.'));
    return;
  }
  const key = `${p.id}:${typeId}`;
  const t = system.currentTick;
  if ((swordCd.get(key) ?? 0) > t) return;
  const bf = inBlackForm(p);
  const dim = p.dimension;
  const mult = (bf ? 1.6 : 1) * (1 + (s.level - 1) * 0.05);
  let cd = 0;
  if (typeId === 'bc:demon_slayer_sword') {
    anim(p, 'animation.bc.player.sword_slash');
    sound(dim, 'bc.anti.slash', p.location, 1.2, bf ? 0.7 : 1);
    timer3(() => launch(p, 'bc:anti_magic_slash', muzzle(p, 1.6, 0.6), p.getViewDirection(), bf ? 2.1 : 1.7,
      { spell: 'black_meteorite', attr: 'anti', damage: 14 * mult, pierce: bf ? 10 : 5 }));
    cd = bf ? 30 : 60;
  } else if (typeId === 'bc:demon_dweller_sword') {
    anim(p, 'animation.bc.player.guard');
    let absorbed = 0;
    safe(() => {
      for (const x of dim.getEntities({ location: p.location, maxDistance: 8 })) {
        const xm = projectiles.get(x.id);
        const hostile = (x.matches({ families: ['bc_spell'] }) && (!xm || xm.owner !== p.id) && !['bc:tornado', 'bc:black_hole', 'bc:ice_prison'].includes(x.typeId))
          || HOSTILE_PROJECTILES.includes(x.typeId);
        if (!hostile) continue;
        particle(dim, 'bc:anti_burst', x.location, { scale: 0.7 });
        x.remove();
        absorbed++;
      }
    });
    effect(p, 'resistance', 1.5, 2, false);
    if (absorbed) {
      sound(dim, 'bc.anti.nullify', p.location, 1.2, 0.9);
      const dir = p.getViewDirection();
      for (let i = 0; i < Math.min(absorbed, 5); i++) {
        timerN(4 + i * 3, () => launch(p, 'bc:anti_magic_slash', muzzle(p, 1.4, 0.5), V.yaw(dir, (i - (Math.min(absorbed, 5) - 1) / 2) * 9), 2.0,
          { spell: 'spell_return', attr: 'anti', damage: 12 * mult, pierce: 3 }));
      }
      safe(() => p.onScreenDisplay.setActionBar(`§8${DATA.glyphs.clover5} §fSpell Return! §7(${absorbed} absorbed)`));
    } else {
      // nothing to absorb: quick flash slash forward
      dash(p, 5.5, 9 * mult, 'bc:slash_fx');
    }
    cd = bf ? 40 : 80;
  } else if (typeId === 'bc:demon_destroyer_sword') {
    anim(p, 'animation.bc.player.sword_thrust');
    for (const ef of safe(() => p.getEffects()) ?? []) {
      if (['poison', 'wither', 'slowness', 'weakness', 'blindness', 'darkness', 'mining_fatigue', 'nausea', 'hunger', 'levitation'].includes(ef.typeId)) safe(() => p.removeEffect(ef.typeId));
    }
    dash(p, 6.5, 12 * mult, 'bc:anti_burst', (t) => {
      for (const ef of safe(() => t.getEffects()) ?? []) safe(() => t.removeEffect(ef.typeId));
      effect(t, 'weakness', 6, 1);
      effect(t, 'slowness', 2, 1);
    });
    cd = bf ? 50 : 100;
  }
  swordCd.set(key, t + cd);
}

function timer3(fn) {
  system.runTimeout(() => safe(fn, 'sword'), 3);
}
function timerN(n, fn) {
  system.runTimeout(() => safe(fn, 'sword'), n);
}

function dash(p, dist, dmg, fx, onHit) {
  const dim = p.dimension;
  const dir = V.flat(p.getViewDirection());
  const a = V.add(p.location, { x: 0, y: 1, z: 0 });
  const b = V.add(a, V.mul(dir, dist));
  knock(p, dir, 2.6, 0.15);
  sound(dim, 'bc.anti.slash', p.location, 1, 1.3);
  const hit = new Set();
  repeat(7, 1, () => {
    if (!alive(p)) return false;
    particle(dim, 'bc:anti_crackle', V.add(p.location, { x: 0, y: 1, z: 0 }), { radius: 0.6 });
    for (const t of targetsAlong(dim, a, b, 1.6, p)) {
      if (hit.has(t.id)) continue;
      hit.add(t.id);
      hurt(t, dmg * (t.matches({ families: ['bc_magic'] }) ? 1.5 : 1), p);
      particle(dim, fx, center(t), { size: 3, scale: 0.8 });
      knock(t, dir, 0.8, 0.3);
      if (onHit) safe(() => onHit(t));
      gainAnti(p, 4);
    }
  });
}

export function gainAnti(p, amount) {
  const s = state(p);
  if (s.attr !== 'anti' || inBlackForm(p)) return;
  s.anti = clamp(s.anti + amount, 0, 100);
  s.dirty = true;
  if (s.anti >= 100 && amount > 0) {
    safe(() => p.onScreenDisplay.setActionBar(`§c${DATA.glyphs.clover5} §lANTI-MAGIC OVERFLOWING§r §7- Black Form is ready!`));
  }
}

// ----------------------------------------------------------------------- passives
/** Melee hit with a demon sword. */
export function onSwordHit(p, target, typeId) {
  if (!canHit(p, target)) return;
  const s = state(p);
  const dim = p.dimension;
  const magical = target.matches({ families: ['bc_magic'] });
  particle(dim, 'bc:slash_fx', center(target), { size: typeId === 'bc:demon_slayer_sword' ? 3.2 : 2.4, rot: rand(-40, 40) });
  if (s.attr !== 'anti' && !isCreative(p)) return;
  particle(dim, 'bc:anti_sparks', center(target), { scale: 0.6 });
  if (magical) hurt(target, 6, p);
  if (inBlackForm(p)) {
    hurt(target, 5, p);
    particle(dim, 'bc:anti_crackle', center(target), { radius: 0.8 });
  }
  for (const ef of safe(() => target.getEffects()) ?? []) {
    if (['regeneration', 'strength', 'speed', 'resistance', 'absorption', 'invisibility', 'fire_resistance'].includes(ef.typeId)) safe(() => target.removeEffect(ef.typeId));
  }
  gainAnti(p, 7);
}

/** Black Form aura, parrying projectiles while sneaking with a demon sword. */
system.runInterval(() => {
  const t = system.currentTick;
  for (const p of world.getAllPlayers()) {
    const s = state(p);
    if (s.attr !== 'anti') continue;
    const bf = inBlackForm(p);
    if (bf) {
      particle(p.dimension, 'bc:anti_crackle', V.add(p.location, { x: 0, y: 1.1, z: 0 }), { radius: 0.9 });
      if (t % 8 === 0) particle(p.dimension, 'bc:black_aura', p.location, { scale: 1 });
    }
    const held = safe(() => inventory(p)?.getItem(p.selectedSlotIndex)?.typeId) ?? '';
    if (!held.startsWith('bc:demon_')) continue;
    if (t % 10 === 0 && !bf) particle(p.dimension, 'bc:anti_crackle', V.add(p.location, { x: 0, y: 1.0, z: 0 }), { radius: 0.7 });
    if (p.isSneaking || bf) {
      safe(() => {
        for (const x of p.dimension.getEntities({ location: p.location, maxDistance: bf ? 3.5 : 2.6 })) {
          const xm = projectiles.get(x.id);
          const hostile = (x.matches({ families: ['bc_spell'] }) && (!xm || xm.owner !== p.id) && !['bc:tornado', 'bc:black_hole', 'bc:ice_prison'].includes(x.typeId))
            || HOSTILE_PROJECTILES.includes(x.typeId);
          if (!hostile) continue;
          particle(p.dimension, 'bc:slash_fx', x.location, { size: 2, rot: rand(-60, 60) });
          particle(p.dimension, 'bc:anti_burst', x.location, { scale: 0.5 });
          sound(p.dimension, 'bc.anti.nullify', x.location, 0.8, 1.4);
          x.remove();
          gainAnti(p, 5);
        }
      });
    }
  }
}, 2);

/** Black Form ending. */
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    const until = p.getDynamicProperty('bc:black_form');
    if (typeof until === 'number' && until > 0 && until <= system.currentTick) {
      p.setDynamicProperty('bc:black_form', 0);
      title(p, '§7Black Form fades', '', 25);
      particle(p.dimension, 'bc:burst_dark', V.add(p.location, { x: 0, y: 1, z: 0 }), { scale: 1, color: rgb('100008') });
    }
  }
}, 10);

/** Taking hits fills the gauge a little. */
world.afterEvents.entityHurt.subscribe((ev) => {
  if (ev.hurtEntity instanceof Player) safe(() => gainAnti(/** @type {Player} */ (ev.hurtEntity), 2));
});

export { inBlackForm, burst, shake };
