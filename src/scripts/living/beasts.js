// The creatures of the Untamed Kingdom (v1.1.0):
// * MANA WYVERNS (Ember, Frost and Storm) sleep on their hoards in the heights. Wake one - come close, hurt it, or touch its
//   gold - and it hunts you from the air: elemental breath, dives, tail sweeps, wing gusts, and a storm of its element.
//   They also cross the sky over Wyvern Territory (and on a Wyvern Migration day), and leave if nobody fights them.
// * the SPIRE WARDEN guards the roof of every Mage Spire: fist slams, a rune beam, rune storms, guards from the floors below.
// * MANA SPRITES are mischievous: one may snatch an item from your pack and flee - catch it before it vanishes.
// * ROOTWARDENS snare you with roots; HOLLOW KNIGHTS still cast from their broken grimoires.
// * WILL-O'-WISPS drift ahead of you at night in haunted and fae lands - follow one, and it leads you somewhere.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { emit } from '../core/bus.js';
import { center, effect, hurt, knock, targetsAround } from '../core/combat.js';
import { anim, particle, rgb, shakeArea, sound, title } from '../core/fx.js';
import { chestItems } from '../core/loot.js';
import { V, alive, pick, rand, safe, timer } from '../core/util.js';
import * as vfx from '../core/vfx.js';
import { announce, bossMove, registerBoss, telegraph } from './bosses.js';
import { castSpec } from './engine.js';
import { face } from './knights.js';
import { hasTrait } from './regions.js';
import { wakeWyvern } from './landmarks.js';

const W = DATA.world;

// ------------------------------------------------------------------------------- the Mana Wyverns
const BREATH = {
  ember_wyvern: { t: 'beam', d: 8, range: 24, width: 1.8, fire: 4, fx: 'flame' },
  frost_wyvern: { t: 'beam', d: 7, range: 24, width: 1.8, fx: 'ice', eff: [['slowness', 4, 2], ['mining_fatigue', 4, 1]] },
  storm_wyvern: { t: 'beam', d: 8, range: 26, width: 1.4, fx: 'lightning', eff: [['slowness', 2, 0]] },
};
const STORM = {
  ember_wyvern: { t: 'meteor', d: 10, n: 4, r: 6, aoe: 3, fire: 5, size: 1, fx: 'flame' },
  frost_wyvern: { t: 'rain', d: 8, n: 12, r: 6, every: 3, fx: 'ice', eff: [['slowness', 3, 1]] },
  storm_wyvern: { t: 'strikes', d: 10, n: 5, r: 9, fx: 'lightning' },
};
for (const [wid, w] of Object.entries(W.wyverns)) {
  const type = `bc:${wid}`;
  const src = `a:${w.attr}`;
  registerBoss(type, {
    name: `§l${w.name}`, src, every: [34, 52], range: 48, stars: 4, desperation: 'wyvern_fury', roar: 'animation.bc.wyvern.roar',
    intro: [`§l${w.name.toUpperCase()}`, '§7It wakes on its hoard'],
    rage: [`§l${w.name} is wounded`, '§7And now it is angry'],
    last: ['§l§cWYVERN\'S FURY', '§7It pours everything it has into one last storm'],
    attacks: [
      { w: 4, min: 3, spec: BREATH[wid], src, anim: 'animation.bc.wyvern.breath' },
      { w: 2, min: 7, fn: 'dive', anim: 'animation.bc.wyvern.bite' },
      { w: 2, max: 8, fn: 'tail' },
      { w: 2, max: 10, tele: 12, spec: { t: 'nova', d: 8, r: 7, kb: [2.4, 1.0], fx: 'wind' }, src: 'a:wind', anim: 'animation.bc.wyvern.roar' },
      { w: 2, phase: 2, spec: STORM[wid], src, anim: 'animation.bc.wyvern.roar' },
    ],
  }, {
    color: w.color, flyer: 6,
    asleep: (e) => safe(() => e.getProperty('bc:asleep')) === true,
    desperation: {
      wyvern_fury(e, target) {
        if (!alive(e) || !target) return;
        const kind = e.typeId.replace('bc:', '');
        anim(e, 'animation.bc.wyvern.roar');
        sound(e.dimension, 'mob.enderdragon.growl', e.location, 3, 0.6);
        shakeArea(e.dimension, e.location, 40, 0.6, 1.2);
        for (let i = 0; i < 4; i++) {
          timer(10 + i * 14, () => {
            if (!alive(e) || !alive(target)) return;
            face(e, target);
            anim(e, 'animation.bc.wyvern.breath');
            castSpec(e, BREATH[kind], `a:${W.wyverns[kind].attr}`, 1.3, target);
          });
        }
        timer(70, () => alive(e) && alive(target) && castSpec(e, STORM[kind], `a:${W.wyverns[kind].attr}`, 1.4, target));
      },
    },
    mover(e, target, st, t) {
      if (!target) return;
      // circle above the prey, low enough to bite
      const ang = (t / 110 + (e.id.length % 7)) % (Math.PI * 2);
      const want = V.add(target.location, { x: Math.cos(ang) * 10, y: 7, z: Math.sin(ang) * 10 });
      const d = V.sub(want, e.location);
      if (V.len(d) > 3) safe(() => e.applyImpulse(V.mul(V.norm(d), 0.11)));
    },
  });
}

// hurting a sleeping wyvern is a mistake
world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const e = ev.hurtEntity;
  if (!W.wyverns[e.typeId.replace('bc:', '')]) return;
  const src = ev.damageSource.damagingEntity;
  if (safe(() => e.getProperty('bc:asleep')) === true) wakeWyvern(e, src instanceof Player ? src : undefined);
}, 'wyvernWake'));

/** A wyvern crossing the sky (Wyvern Territory, a Wyvern Migration) - it hunts whoever it sees, and leaves after a while. */
export function flyby(p, kind = '') {
  const wid = kind || pick(Object.keys(W.wyverns));
  const back = V.flat(p.getViewDirection());
  const at = V.add(p.location, { x: -back.x * 70 + rand(-20, 20), y: 30, z: -back.z * 70 + rand(-20, 20) });
  const e = safe(() => p.dimension.spawnEntity(`bc:${wid}`, at));
  if (!e) return undefined;
  safe(() => e.setDynamicProperty('bc:flyby', Date.now() + 180000));
  sound(p.dimension, 'mob.enderdragon.flap', p.location, 1, 0.6);
  safe(() => p.onScreenDisplay.setActionBar(`§2A shadow crosses the sun... §f${W.wyverns[wid].name}§2 on the wing!`));
  return e;
}
system.runInterval(() => {
  const t = Date.now();
  for (const wid of Object.keys(W.wyverns)) {
    for (const p of world.getAllPlayers()) {
      for (const e of safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 120, type: `bc:${wid}` })) ?? []) {
        const until = safe(() => e.getDynamicProperty('bc:flyby'));
        if (typeof until !== 'number' || until > t) continue;
        const hp = e.getComponent('minecraft:health');
        if (hp && hp.currentValue < hp.effectiveMax * 0.9) continue; // a fight is on - it stays
        particle(e.dimension, 'bc:smoke_burst', center(e), { scale: 1.2 });
        safe(() => e.remove());
      }
    }
  }
}, 200);

// ------------------------------------------------------------------------------- the Spire Warden
registerBoss('bc:spire_warden', {
  name: '§b§lThe Spire Warden', src: 'a:rune', every: [30, 50], range: 28, stars: 5, desperation: 'spire_collapse', roar: 'animation.bc.spire_warden.cast',
  intro: ['§b§lTHE SPIRE WARDEN', '§7The guardian of the old kingdom\'s magic'],
  rage: ['§b§lThe Warden\'s runes blaze', '§7The ring turns faster'],
  last: ['§b§lSPIRE COLLAPSE', '§7The roof itself turns on you'],
  attacks: [
    { w: 3, max: 5, fn: 'warden_slam', anim: 'animation.bc.spire_warden.slam' },
    { w: 3, min: 3, spec: { t: 'beam', d: 9, range: 22, width: 1.2, fx: 'spatial' }, src: 'a:rune', anim: 'animation.bc.spire_warden.cast' },
    { w: 2, spec: { t: 'strikes', d: 8, n: 4, r: 7, fx: 'spatial' }, src: 'a:rune', anim: 'animation.bc.spire_warden.cast' },
    { w: 2, max: 9, tele: 14, spec: { t: 'nova', d: 10, r: 6, kb: [2.0, 0.8], fx: 'spatial' }, src: 'a:rune', anim: 'animation.bc.spire_warden.slam' },
    { w: 1, phase: 2, fn: 'warden_guards', anim: 'animation.bc.spire_warden.cast' },
  ],
}, {
  color: '60e0ff',
  moves: {
    warden_slam(e, target, st) {
      telegraph(e, e.location, 4.5, 14);
      timer(14, () => {
        if (!alive(e)) return;
        vfx.ground(e.dimension, e.location, 'spatial', vfx.hex('60e0ff'), 4.5, 1.0);
        shakeArea(e.dimension, e.location, 20, 0.5, 0.6);
        sound(e.dimension, 'bc.golem.slam', e.location, 2, 0.9);
        for (const v of targetsAround(e.dimension, e.location, 4.5, e)) {
          hurt(v, st.phase > 1 ? 14 : 11, e);
          knock(v, V.sub(v.location, e.location), 1.6, 0.7);
        }
      });
    },
    warden_guards(e, target) {
      const n = safe(() => e.dimension.getEntities({ location: e.location, maxDistance: 20, type: 'bc:rogue_mage' }).length) ?? 0;
      if (n >= 3) return;
      announce(e, '§bThe Warden calls the spire\'s guards', '');
      for (let i = 0; i < 2; i++) {
        const at = V.add(e.location, { x: rand(-4, 4), y: 0.5, z: rand(-4, 4) });
        particle(e.dimension, 'bc:magic_circle_ground', at, { color: rgb('60e0ff'), size: 2, life: 1 });
        timer(16, () => safe(() => e.dimension.spawnEntity(i === 0 ? 'bc:rogue_mage' : 'bc:mana_wraith', at)));
      }
    },
  },
  desperation: {
    spire_collapse(e, target) {
      if (!alive(e)) return;
      shakeArea(e.dimension, e.location, 30, 0.8, 2.0);
      for (let i = 0; i < 6; i++) {
        timer(i * 12, () => {
          if (!alive(e)) return;
          const at = target && alive(target) ? V.add(target.location, { x: rand(-3, 3), y: 0, z: rand(-3, 3) }) : V.add(e.location, { x: rand(-6, 6), y: 0, z: rand(-6, 6) });
          telegraph(e, at, 2.5, 14);
          timer(14, () => {
            vfx.pillar(e.dimension, at, vfx.hex('60e0ff'), 8, 1.2);
            for (const v of targetsAround(e.dimension, at, 2.6, e)) hurt(v, 10, e, 'magic');
          });
        });
      }
      bossMove('warden_guards', e, target, {});
    },
  },
});

// ------------------------------------------------------------------------------- Mana Sprites: little thieves
/** Let a sprite snatch something from a player's pack (never the held item or armour). Returns the stolen stack. */
export function snatch(sprite, p) {
  const inv = p.getComponent('minecraft:inventory')?.container;
  if (!inv) return undefined;
  const slots = [];
  for (let i = 0; i < inv.size; i++) {
    if (i === p.selectedSlotIndex) continue;
    const it = inv.getItem(i);
    if (it && !it.typeId.startsWith('bc:grimoire_')) slots.push(i);
  }
  if (!slots.length) return undefined;
  const i = pick(slots);
  const it = inv.getItem(i);
  if (!it) return undefined;
  const one = it.clone ? it.clone() : new ItemStack(it.typeId, 1);
  one.amount = 1;
  if (it.amount > 1) {
    it.amount -= 1;
    inv.setItem(i, it);
  } else inv.setItem(i, undefined);
  safe(() => sprite.setDynamicProperty('bc:stolen', JSON.stringify({ id: one.typeId, name: safe(() => one.nameTag) ?? '', lore: safe(() => one.getLore()) ?? [] })));
  safe(() => sprite.setDynamicProperty('bc:flee_until', Date.now() + 60000));
  const name = String(safe(() => one.nameTag) || one.typeId.replace(/^.*:/, '').replace(/_/g, ' ')).replace(/§./g, '');
  safe(() => p.sendMessage(`§aA Mana Sprite snatches your §f${name}§a and flies off giggling! §7Catch it within a minute...`));
  sound(p.dimension, 'random.orb', p.location, 1, 2);
  emit('sprite_theft', p);
  return one;
}
function stolenOf(e) {
  const v = safe(() => e.getDynamicProperty('bc:stolen'));
  if (typeof v !== 'string') return undefined;
  try {
    const o = JSON.parse(v);
    const it = new ItemStack(o.id, 1);
    if (o.name) safe(() => (it.nameTag = o.name));
    if (o.lore?.length) safe(() => it.setLore(o.lore));
    return it;
  } catch {
    return undefined;
  }
}
system.runInterval(() => {
  const now = Date.now();
  for (const p of world.getAllPlayers()) {
    for (const e of safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 32, type: 'bc:mana_sprite' })) ?? []) safe(() => {
      const until = e.getDynamicProperty('bc:flee_until');
      if (typeof until === 'number') {
        if (until < now) {
          // gone, with its prize
          particle(e.dimension, 'bc:burst_spark', center(e), { color: rgb('a8ffd0'), scale: 0.8 });
          e.remove();
          return;
        }
        const away = V.norm(V.flat(V.sub(e.location, p.location)));
        safe(() => e.applyImpulse({ x: away.x * 0.12, y: 0.02, z: away.z * 0.12 }));
        if (system.currentTick % 40 === 0) particle(e.dimension, 'bc:burst_spark', e.location, { color: rgb('a8ffd0'), scale: 0.3 });
        return;
      }
      if (V.dist(e.location, p.location) < 2.6 && Math.random() < (hasTrait(e.location, 'fae_wilds') ? 0.12 : 0.06)) snatch(e, p);
    });
  }
}, 20);
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const e = ev.deadEntity;
  if (e.typeId !== 'bc:mana_sprite') return;
  const it = stolenOf(e);
  if (it) safe(() => e.dimension.spawnItem(it, e.location));
}, 'spriteDie'));

// ------------------------------------------------------------------------------- Rootwardens and the Hollow
const snareAt = new Map();
const castAt = new Map();
system.runInterval(() => {
  const t = system.currentTick;
  for (const p of world.getAllPlayers()) {
    for (const e of safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 18, type: 'bc:rootwarden' })) ?? []) safe(() => {
      if ((snareAt.get(e.id) ?? 0) > t) return;
      snareAt.set(e.id, t + 120);
      anim(e, 'animation.bc.rootwarden.attack');
      const at = { ...p.location };
      particle(e.dimension, 'bc:leaf_burst', at, { scale: 0.9 });
      vfx.ground(e.dimension, at, 'plant', vfx.hex('3fae4a'), 2, 0.8, false);
      sound(e.dimension, 'dig.grass', at, 1, 0.6);
      for (const v of targetsAround(e.dimension, at, 2.2, e)) {
        effect(v, 'slowness', 2, 4);
        hurt(v, 4, e);
      }
    });
    for (const e of safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 16, type: 'bc:hollow_knight' })) ?? []) safe(() => {
      if ((castAt.get(e.id) ?? 0) > t) return;
      castAt.set(e.id, t + 120 + Math.floor(Math.random() * 80));
      anim(e, 'animation.bc.hollow_knight.cast');
      const kit = DATA.npcKits[Math.random() < 0.5 ? 'dark' : 'ice'];
      castSpec(e, { ...kit[0], d: Math.max(3, (kit[0].d ?? 5) - 1) }, Math.random() < 0.5 ? 'a:dark' : 'a:ice', 0.8, p);
    });
  }
}, 20);

// ------------------------------------------------------------------------------- Will-o'-Wisps
/** @type {Map<string, {player: string, to: {x: number, z: number}, until: number}>} */
const wisps = new Map();
/** A wisp appears ahead of a player and drifts toward somewhere 60-120 blocks away. */
export function spawnWisp(p) {
  const dir = V.flat(p.getViewDirection());
  const at = V.add(p.location, { x: dir.x * 10, y: 1.5, z: dir.z * 10 });
  const e = safe(() => p.dimension.spawnEntity('bc:wisp', at));
  if (!e) return undefined;
  const a = Math.atan2(dir.z, dir.x) + rand(-0.8, 0.8);
  const d = rand(60, 120);
  wisps.set(e.id, { player: p.id, to: { x: p.location.x + Math.cos(a) * d, z: p.location.z + Math.sin(a) * d }, until: system.currentTick + 20 * 180 });
  safe(() => p.onScreenDisplay.setActionBar('§bA pale light drifts ahead of you... §7follow it?'));
  sound(p.dimension, 'random.orb', p.location, 0.6, 0.6);
  return e;
}
/** The wisp reaches its end: a buried cache, or a trap. */
export function wispEnd(e, p) {
  const dim = e.dimension;
  const at = { ...e.location };
  particle(dim, 'bc:light_burst', at, { scale: 1.2 });
  safe(() => e.remove());
  if (Math.random() < 0.7) {
    const top = safe(() => dim.getTopmostBlock({ x: Math.floor(at.x), z: Math.floor(at.z) }));
    const y = top ? top.location.y + 1 : Math.floor(at.y);
    const b = safe(() => dim.getBlock({ x: Math.floor(at.x), y, z: Math.floor(at.z) }));
    if (b) {
      safe(() => b.setType('minecraft:chest'));
      system.run(() => safe(() => {
        const inv = b.getComponent('minecraft:inventory')?.container;
        chestItems('cache', 2).forEach((it, i) => inv?.setItem(i, it));
      }));
    }
    title(p, '§b§lA HIDDEN CACHE', '§7The wisp led you true', 50);
    emit('wisp_cache', p);
  } else {
    for (let i = 0; i < 3; i++) safe(() => dim.spawnEntity('bc:hollow_knight', V.add(at, { x: rand(-4, 4), y: 0.5, z: rand(-4, 4) })));
    title(p, '§8§lA TRAP', '§7The light was bait', 40);
  }
}
system.runInterval(() => {
  const t = system.currentTick;
  for (const [id, w] of wisps) {
    const e = world.getEntity(id);
    const p = world.getEntity(w.player);
    if (!e || !p || w.until < t) {
      if (e) safe(() => e.remove());
      wisps.delete(id);
      continue;
    }
    safe(() => {
      const gap = V.dist(e.location, p.location);
      if (gap > 40) {
        safe(() => e.remove());
        wisps.delete(id);
        return;
      }
      const left = Math.hypot(w.to.x - e.location.x, w.to.z - e.location.z);
      if (left < 3) {
        wisps.delete(id);
        wispEnd(e, p);
        return;
      }
      if (gap < 12) {
        const step = V.norm({ x: w.to.x - e.location.x, y: 0, z: w.to.z - e.location.z });
        const next = V.add(e.location, V.mul(step, 1.2));
        const top = safe(() => e.dimension.getTopmostBlock({ x: Math.floor(next.x), z: Math.floor(next.z) }));
        if (top) next.y = top.location.y + 2;
        safe(() => e.teleport(next));
      }
      particle(e.dimension, 'bc:burst_spark', e.location, { color: rgb('8acaff'), scale: 0.3 });
    });
  }
}, 5);

export { flyby as wyvernFlyby };
