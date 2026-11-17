// Consumables, first-join welcome kit and kill rewards.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { addMana, hasJoined, markJoined, save, state } from '../core/data.js';
import { aimPoint, groundBelow } from '../core/combat.js';
import { COLORS, particle, sound, title } from '../core/fx.js';
import { addXp } from '../core/progress.js';
import { V, isCreative, safe } from '../core/util.js';
import { gainAnti } from '../magic/antimagic.js';
import { confirmCharm, openHandbook } from '../ui/handbook.js';
import { summonDevil } from './mobs.js';

function consumeHeld(p, typeId) {
  if (isCreative(p)) return;
  const inv = p.getComponent('minecraft:inventory')?.container;
  if (!inv) return;
  const slot = p.selectedSlotIndex;
  const it = inv.getItem(slot);
  if (!it || it.typeId !== typeId) return;
  if (it.amount > 1) {
    it.amount -= 1;
    inv.setItem(slot, it);
  } else inv.setItem(slot, undefined);
}

export function useMisc(p, typeId) {
  if (typeId === 'bc:mana_crystal') {
    const s = state(p);
    if (!s.attr) {
      safe(() => p.sendMessage('§7The crystal hums, but you have no grimoire to channel it.'));
      return;
    }
    if (s.attr === 'anti') gainAnti(p, 20);
    else addMana(p, 45);
    consumeHeld(p, typeId);
    particle(p.dimension, 'bc:mana_aura', p.location, { color: COLORS[s.attr] ?? COLORS.water, scale: 2 });
    sound(p.dimension, 'random.orb', p.location, 0.8, 1.3);
    sound(p.dimension, 'bc.light.shine', p.location, 0.5, 1.6);
  } else if (typeId === 'bc:handbook') {
    system.run(() => openHandbook(p).catch(() => {}));
  } else if (typeId === 'bc:devil_contract') {
    const { point } = aimPoint(p, 10);
    const spot = groundBelow(p.dimension, V.add(point, { x: 0, y: 1, z: 0 }), 8);
    safe(() => p.sendMessage('§4You sign the contract in blood... §cSomething answers.'));
    consumeHeld(p, typeId);
    summonDevil(p.dimension, spot, p);
  } else if (typeId === 'bc:clover_charm') {
    system.run(async () => {
      const ok = await confirmCharm(p).catch(() => false);
      if (!ok) return;
      const s = state(p);
      const inv = p.getComponent('minecraft:inventory')?.container;
      if (inv) {
        for (let i = 0; i < inv.size; i++) {
          const it = inv.getItem(i);
          if (it && (it.typeId.startsWith('bc:grimoire_') || it.typeId.startsWith('bc:demon_'))) inv.setItem(i, undefined);
        }
      }
      s.attr = '';
      s.level = 1;
      s.xp = 0;
      s.spell = 0;
      s.anti = 0;
      s.cd.clear();
      save(p);
      consumeHeld(p, 'bc:clover_charm');
      particle(p.dimension, 'bc:clover_leaves', V.add(p.location, { x: 0, y: 1, z: 0 }), { scale: 1.5 });
      sound(p.dimension, 'bc.levelup', p.location, 1, 0.7);
      title(p, '§aA wish is made', '§7Visit a Grimoire Altar to receive a new grimoire', 60);
    });
  }
}

// ------------------------------------------------------------------------ welcome kit
world.afterEvents.playerSpawn.subscribe((ev) => {
  if (!ev.initialSpawn) return;
  const p = ev.player;
  system.runTimeout(() => safe(() => {
    if (hasJoined(p)) {
      const s = state(p);
      if (s.attr) {
        const a = DATA.attributes[s.attr];
        p.sendMessage(`${a.glyph} §7Welcome back, ${a.mc}${a.name}§7 mage. Level §e${s.level}§7.`);
      }
      return;
    }
    markJoined(p);
    const inv = p.getComponent('minecraft:inventory')?.container;
    inv?.addItem(new ItemStack('bc:handbook', 1));
    inv?.addItem(new ItemStack('bc:grimoire_altar', 1));
    title(p, '§l§2Black Clover', '§fGrimoire Awakening', 70);
    p.sendMessage(`${DATA.glyphs.clover4} §2§lBlack Clover: Grimoire Awakening§r\n§fPlace your §dGrimoire Altar§f and interact with it to receive your grimoire.\n§7Read the §eMagic Knight's Handbook§7 for everything else.`);
    sound(p.dimension, 'bc.grimoire.awaken', p.location, 0.6, 1.2);
  }, 'welcome'), 60);
});

// ------------------------------------------------------------------------ xp from kills
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const killer = ev.damageSource.damagingEntity;
  if (!(killer instanceof Player)) return;
  const e = ev.deadEntity;
  let xp = 1;
  const typeId = safe(() => e.typeId) ?? '';
  if (typeId === 'bc:devil') xp = 260;
  else if (typeId === 'bc:dark_disciple') xp = 16;
  else if (safe(() => e.matches({ families: ['monster'] }))) xp = 6;
  addXp(killer, xp);
  if (typeId === 'bc:dark_disciple' || typeId === 'bc:devil') gainAnti(killer, 15);
}, 'killXp'));

world.afterEvents.playerLeave.subscribe(() => {});

export { particle };
