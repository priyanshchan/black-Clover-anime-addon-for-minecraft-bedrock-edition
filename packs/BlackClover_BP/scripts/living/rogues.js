// Rogue Mages: mages who turned their grimoires against the kingdom. They roam the plains and forests at night,
// each with a real grimoire (any attribute) and a level from 2 to 8 - so they fight with the same tactical brain
// and spell kits as Magic Knights. They hunt players and knights alike, and the Rogue Mages are a War Table army.
import { system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { pick, safe } from '../core/util.js';
import { rethink } from './ai.js';

const ATTRS = Object.keys(DATA.attributes).filter((a) => a !== 'anti' && a !== 'time');
const TITLES = ['the Exile', 'the Traitor', 'the Hollow', 'the Outlaw', 'the Cursed', 'the Deserter', 'the Renegade'];

/** Give a Rogue Mage a grimoire, a level and a name (only once). */
export function setupRogue(e, opts = {}) {
  if (typeof safe(() => e.getDynamicProperty('bc:attr')) === 'string' && !opts.force) return;
  safe(() => {
    const attr = opts.attr ?? pick(ATTRS);
    const lv = opts.level ?? 2 + Math.floor(Math.random() * 7);
    e.setDynamicProperty('bc:attr', attr);
    e.setDynamicProperty('bc:klv', lv);
    e.setDynamicProperty('bc:kname', `${pick(DATA.knightFirst)} ${pick(TITLES)}`);
    e.nameTag = `§5${e.getDynamicProperty('bc:kname')} §7Lv ${lv} §r${DATA.attributes[attr].glyph}`;
  }, 'setupRogue');
  rethink(e);
}

function track(e) {
  if (e.typeId !== 'bc:rogue_mage') return;
  system.runTimeout(() => safe(() => e.isValid && setupRogue(e)), 1);
}
world.afterEvents.entitySpawn.subscribe((ev) => safe(() => track(ev.entity)));
world.afterEvents.entityLoad.subscribe((ev) => safe(() => track(ev.entity)));
