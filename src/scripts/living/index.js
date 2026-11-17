// Living world entry point: spell engine, tactical AI, knights, battles, world simulation, bosses, events, merchant, War Table.
import { safe } from '../core/util.js';
import './engine.js';
import './passives.js';
import './knights.js';
import './battle.js';
import './ai.js';
import './worldsim.js';
import './merchant.js';
import './events.js';
import { useBossItem } from './bosses.js';
import { hireKnight } from './knights.js';
import { blowHorn } from './wartable.js';
import { isCreative } from '../core/util.js';

function consume(p, id) {
  if (isCreative(p)) return;
  const inv = p.getComponent('minecraft:inventory')?.container;
  const it = inv?.getItem(p.selectedSlotIndex);
  if (it?.typeId !== id) return;
  if (it.amount > 1) {
    it.amount -= 1;
    inv.setItem(p.selectedSlotIndex, it);
  } else inv.setItem(p.selectedSlotIndex, undefined);
}

/** @returns {boolean} true when the item belongs to wave 4 */
export function useLivingItem(p, item) {
  const id = item.typeId;
  if (useBossItem(p, id)) return true;
  if (id === 'bc:knight_contract') {
    if (safe(() => hireKnight(p))) consume(p, id);
  } else if (id === 'bc:skirmish_horn') {
    if (safe(() => blowHorn(p))) consume(p, id);
  } else return false;
  return true;
}
