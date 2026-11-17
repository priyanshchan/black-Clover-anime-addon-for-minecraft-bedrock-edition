// Black Clover: Grimoire Awakening - script entry point.
// Unofficial fan-made addon. Requires @minecraft/server 2.0.0 (Minecraft 1.21.90+).
import { Player, system, world } from '@minecraft/server';
import { forget, save, state } from './core/data.js';
import './core/hud.js';
import { safe } from './core/util.js';
import { onSwordHit, useSword } from './magic/antimagic.js';
import { useGrimoire } from './magic/caster.js';
import './magic/projectiles.js';
import { onMeleeHit } from './magic/spells.js';
import './world/altar.js';
import { useMisc } from './world/items.js';
import './world/mobs.js';
import { onSeaMelee, useSeaItem } from './sea/index.js';
import { useGrandItem } from './grand/index.js';
import { forgetSea, saveSea } from './sea/state.js';

const lastUse = new Map();

world.afterEvents.itemUse.subscribe((ev) => {
  const p = ev.source;
  const item = ev.itemStack;
  if (!item || !item.typeId.startsWith('bc:')) return;
  const t = system.currentTick;
  if ((lastUse.get(p.id) ?? -10) >= t - 2) return; // debounce double events
  lastUse.set(p.id, t);
  const id = item.typeId;
  if (safe(() => useGrandItem(p, item), 'grand')) return;
  if (safe(() => useSeaItem(p, item), 'sea')) return;
  if (id.startsWith('bc:grimoire_')) safe(() => useGrimoire(p, item), 'grimoire');
  else if (id.startsWith('bc:demon_') && id.endsWith('_sword')) safe(() => useSword(p, id), 'sword');
  else safe(() => useMisc(p, id), 'item');
});

world.afterEvents.entityHitEntity.subscribe((ev) => {
  const p = ev.damagingEntity;
  if (!(p instanceof Player)) return;
  safe(() => {
    const held = p.getComponent('minecraft:inventory')?.container?.getItem(p.selectedSlotIndex)?.typeId ?? '';
    if (held.startsWith('bc:demon_') && held.endsWith('_sword')) onSwordHit(p, ev.hitEntity, held);
    onMeleeHit(p, ev.hitEntity);
    onSeaMelee(p, ev.hitEntity);
  }, 'melee');
});

world.beforeEvents.playerLeave.subscribe((ev) => {
  const p = ev.player;
  const id = p.id;
  safe(() => save(p), 'leave-save');
  safe(() => saveSea(p), 'leave-save-sea');
  system.run(() => {
    forget(id);
    forgetSea(id);
  });
});

world.afterEvents.worldLoad.subscribe(() => {
  for (const p of world.getAllPlayers()) safe(() => state(p));
  console.log('[Black Clover] Grimoire Awakening loaded.');
});
