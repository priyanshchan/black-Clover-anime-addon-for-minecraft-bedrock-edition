// The Grimoire Altar block: grants each player their grimoire in a short ceremony.
import { ItemStack, system } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { maxMana, save, state } from '../core/data.js';
import { COLORS, burst, groundCircle, particle, shakeArea, sound, title } from '../core/fx.js';
import { V, rand, repeat, safe } from '../core/util.js';

const WEIGHTS = DATA.altarWeights;
const ceremonies = new Set();

function roll() {
  const total = Object.values(WEIGHTS).reduce((a, b) => a + b, 0);
  let r = Math.random() * total;
  for (const [k, w] of Object.entries(WEIGHTS)) {
    r -= w;
    if (r <= 0) return k;
  }
  return 'wind';
}

export function grimoireItem(player, attr) {
  const a = DATA.attributes[attr];
  const item = new ItemStack(`bc:grimoire_${attr}`, 1);
  const leaves = { 3: 'three', 4: 'four', 5: 'five' }[a.leaves];
  safe(() => item.setLore([
    `§7A ${leaves}-leaf grimoire of ${a.mc}${a.name}§7 magic.`,
    `§8Owner: §f${player.name}`,
    '§8Use: §7cast   §8Sneak + Use: §7change spell',
  ]));
  return item;
}

function hasGrimoire(player, attr) {
  const inv = player.getComponent('minecraft:inventory')?.container;
  if (!inv) return false;
  for (let i = 0; i < inv.size; i++) if (inv.getItem(i)?.typeId === `bc:grimoire_${attr}`) return true;
  return false;
}

function give(player, item) {
  const left = player.getComponent('minecraft:inventory')?.container?.addItem(item);
  if (left) player.dimension.spawnItem(left, player.location);
}

/** @param {import('@minecraft/server').Player} player @param {import('@minecraft/server').Block} block */
export function interact(player, block) {
  const s = state(player);
  const dim = block.dimension;
  const top = V.add(block.location, { x: 0.5, y: 1.2, z: 0.5 });
  if (s.attr) {
    if (!hasGrimoire(player, s.attr)) {
      give(player, grimoireItem(player, s.attr));
      particle(dim, 'bc:clover_leaves', top);
      sound(dim, 'bc.grimoire.flip', top, 1, 1);
      safe(() => player.sendMessage(`§dThe altar glows... §fyour ${DATA.attributes[s.attr].mc}${DATA.attributes[s.attr].name} grimoire§f returns to you.`));
    } else {
      safe(() => player.sendMessage('§7Your grimoire is already with you. §8(A Wishing Clover Charm lets you seek a new one.)'));
    }
    return;
  }
  if (ceremonies.has(player.id)) return;
  ceremonies.add(player.id);
  title(player, '§dThe altar awakens...', '§7A grimoire is searching for its master', 60);
  sound(dim, 'bc.grimoire.awaken', top, 1.4, 1);
  groundCircle(dim, V.add(block.location, { x: 0.5, y: 0.05, z: 0.5 }), 'light', 6, 3.2);
  repeat(15, 4, (i) => {
    particle(dim, 'bc:clover_leaves', top, { scale: 0.6 + i * 0.05 });
    particle(dim, 'bc:mana_aura', V.add(block.location, { x: 0.5, y: 0.2, z: 0.5 }), { color: COLORS.light, scale: 2 });
    const ang = i * 0.8;
    particle(dim, 'bc:beam_dot', { x: top.x + Math.cos(ang) * 1.4, y: top.y + i * 0.15, z: top.z + Math.sin(ang) * 1.4 }, { color: COLORS[Object.keys(WEIGHTS)[i % 8]], size: 0.5, life: 0.8 });
  }, () => {
    ceremonies.delete(player.id);
    const attr = roll();
    const a = DATA.attributes[attr];
    s.attr = attr;
    s.level = 1;
    s.xp = 0;
    s.spell = 0;
    s.anti = 0;
    s.mana = maxMana(player, s);
    s.dirty = true;
    safe(() => save(player));
    give(player, grimoireItem(player, attr));
    const leaves = { 3: 'Three-Leaf', 4: 'Four-Leaf', 5: '§cFive-Leaf' }[a.leaves];
    title(player, `${a.mc}§l${a.name} Magic`, `§f${leaves} Grimoire §7has chosen you`, 80);
    burst(dim, top, attr, 2);
    particle(dim, 'bc:level_up', block.location);
    shakeArea(dim, top, 12, 0.25, 0.6);
    sound(dim, attr === 'anti' ? 'bc.blackform' : 'bc.levelup', top, 1.2, 1);
    if (attr === 'anti') {
      for (let i = 0; i < 4; i++) particle(dim, 'bc:dark_lightning', V.add(block.location, { x: rand(-3, 3), y: 0, z: rand(-3, 3) }));
      safe(() => player.sendMessage(`§c${DATA.glyphs.clover5} A tattered five-leaf grimoire... §fIt holds no magic at all - only §0§lAnti-Magic§r§f. Draw its demon swords!`));
    } else {
      safe(() => player.sendMessage(`${a.mc}${DATA.glyphs.clover3} ${a.name} Magic! §fUse your grimoire to cast, sneak + use to change spells. Level up to unlock more pages.`));
    }
  });
}

system.beforeEvents.startup.subscribe((ev) => {
  ev.blockComponentRegistry.registerCustomComponent('bc:altar_logic', {
    onPlayerInteract(e) {
      if (e.player) safe(() => interact(e.player, e.block), 'altar');
    },
    onTick(e) {
      safe(() => {
        const b = e.block;
        const top = V.add(b.location, { x: 0.5, y: 1.1, z: 0.5 });
        const nearby = e.dimension.getPlayers({ location: top, maxDistance: 24 });
        if (!nearby.length) return;
        particle(e.dimension, 'bc:mana_aura', V.add(b.location, { x: 0.5, y: 0.6, z: 0.5 }), { color: COLORS.wind });
        if (Math.random() < 0.25) particle(e.dimension, 'bc:clover_leaves', top, { scale: 0.3 });
      }, 'altarTick');
    },
  });
});
