// Living world entry point: spell engine, tactical AI, knights, battles, world simulation, bosses, events, merchant, War Table,
// the v0.3.0 systems (brooms, missions, amulets, Rogue Mages, Magic Knight camps) and the v0.5.0 companion update
// (squad.js, camp.js, roster.js, rivals.js, puppeteer.js), and the v0.7.0 warbands (warband.js) and new foes (foes.js).
import { safe } from '../core/util.js';
import './engine.js';
import './passives.js';
import './knights.js';
import './battle.js';
import './ai.js';
import './worldsim.js';
import './enemies.js';
import { useWhistle } from './companions.js';
import './merchant.js';
import './events.js';
import './rogues.js';
import './missions.js';
import './amulets.js';
import './camps.js';
import './squad.js';
import './camp.js';
import './roster.js';
import './rivals.js';
import './warband.js';
import './foes.js';
import './lairs.js';
import './elites.js';
import './feats.js';
import './armor.js';
import './forge.js';
import './world.js';
import './waygate.js';
import { useScroll, useSmokeBomb } from './consumables.js';
import { useCloverLeaf } from './squad.js';
import { placeDummy } from './roster.js';
import { useBroom } from './brooms.js';
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
  } else if (id === 'bc:companion_whistle') {
    safe(() => useWhistle(p));
  } else if (id === 'bc:broom' || id === 'bc:swift_broom') {
    safe(() => useBroom(p, id));
  } else if (id === 'bc:training_dummy') {
    safe(() => placeDummy(p));
  } else if (id === 'bc:clover_leaf') {
    safe(() => useCloverLeaf(p));
  } else if (id === 'bc:smoke_bomb') {
    safe(() => useSmokeBomb(p));
  } else if (id === 'bc:spell_scroll') {
    safe(() => useScroll(p, item));
  } else if (id === 'bc:companion_tome') {
    safe(() => p.onScreenDisplay.setActionBar('§bTalk to a companion (level 10+) while holding the tome to retrain their specialisation.'));
  } else return false;
  return true;
}
