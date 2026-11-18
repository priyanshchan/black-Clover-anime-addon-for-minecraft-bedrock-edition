// Wave 3 entry point: routes the new items.
import { system } from '@minecraft/server';
import '../core/ranks.js';
import '../magic/techniques.js';
import '../sea/fruits2.js';
import { showPoster } from '../sea/navy.js';
import { readPage } from './dungeon.js';
import { useMap } from './treasure.js';
import { useWeapon } from './weapons.js';

/** @returns {boolean} true when the item belongs to wave 3 */
export function useGrandItem(p, item) {
  const id = item.typeId;
  if (id === 'bc:cutlass' || id === 'bc:flintlock' || id === 'bc:harpoon') useWeapon(p, id);
  else if (id === 'bc:treasure_map') useMap(p);
  else if (id === 'bc:ancient_page') readPage(p);
  else if (id === 'bc:wanted_poster') system.run(() => showPoster(p).catch(() => {}));
  else return false;
  return true;
}
