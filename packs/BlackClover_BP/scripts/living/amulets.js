// Amulets: hold one in your off hand. Mana Heart, Swift Sigil and Battle Charm work through the magic stats
// (core/data.js and the caster); Guardian Ward and Vigor Band are kept up here.
import { system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { amuletOf } from '../core/data.js';
import { effect } from '../core/combat.js';
import { particle, rgb } from '../core/fx.js';
import { safe } from '../core/util.js';

/** @type {Map<string, string>} */
const worn = new Map();

system.runInterval(() => {
  const t = system.currentTick;
  for (const p of world.getAllPlayers()) {
    safe(() => {
      const a = amuletOf(p);
      if (a !== (worn.get(p.id) ?? '')) {
        worn.set(p.id, a);
        const info = DATA.amulets[a];
        if (info) safe(() => p.onScreenDisplay.setActionBar(`${info.name}§r §7- ${info.perk}`));
      }
      if (!a) return;
      const hp = p.getComponent('minecraft:health');
      if (a === 'amulet_guard' && hp && hp.currentValue < hp.effectiveMax * 0.4) {
        effect(p, 'resistance', 2, 1, false);
        if (t % 40 === 0) particle(p.dimension, 'bc:mana_aura', p.location, { color: rgb('ffe066'), scale: 0.6 });
      }
      if (a === 'amulet_vigor') {
        effect(p, 'health_boost', 3, 0, false);
        if (hp && hp.currentValue < hp.effectiveMax && t % 60 === 0) hp.setCurrentValue(Math.min(hp.effectiveMax, hp.currentValue + 1));
      }
    }, 'amulet');
  }
}, 20);

world.afterEvents.playerLeave.subscribe((ev) => worn.delete(ev.playerId));
