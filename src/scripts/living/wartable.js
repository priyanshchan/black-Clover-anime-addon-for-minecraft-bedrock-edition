// The War Table: a battle simulator. Pick two factions and an army size, bet on a side, and watch them fight.
import { Player, system } from '@minecraft/server';
import { ActionFormData, MessageFormData, ModalFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { sound } from '../core/fx.js';
import { V, isCreative, pick, safe } from '../core/util.js';
import { countCoins } from '../sea/bounty.js';
import { TACTICS, activeBattleNear, factionIds, reports, spectate, startBattle } from './battle.js';
import { kingdomPage } from './worldsim.js';
import { EVENTS, eventsOn, runEvent, setEvents } from './events.js';

function takeCoins(p, amount) {
  const inv = p.getComponent('minecraft:inventory')?.container;
  if (!inv || countCoins(p) < amount) return false;
  let left = amount;
  for (let i = 0; i < inv.size && left > 0; i++) {
    const it = inv.getItem(i);
    if (it?.typeId !== 'bc:doubloon') continue;
    const take = Math.min(left, it.amount);
    left -= take;
    if (it.amount - take > 0) {
      it.amount -= take;
      inv.setItem(i, it);
    } else inv.setItem(i, undefined);
  }
  return true;
}

function arenaFor(p, tableLoc) {
  const dir = V.flat(V.sub(V.add(tableLoc, { x: 0.5, y: 0, z: 0.5 }), p.location));
  const center = V.add(tableLoc, V.mul(dir, 14));
  const top = safe(() => p.dimension.getTopmostBlock({ x: center.x, z: center.z }));
  if (top && Math.abs(top.location.y - tableLoc.y) < 10) center.y = top.location.y + 1;
  else center.y = tableLoc.y + 1;
  return { center, facing: dir };
}

const TACTIC_IDS = Object.keys(TACTICS);
const ATTRS = DATA.order.filter((a) => a !== 'anti');

function busy(p, tableLoc) {
  if (!activeBattleNear(p.dimension, tableLoc, 48)) return false;
  safe(() => p.sendMessage('§7A battle is already raging here. Wait for it to end (or watch it).'));
  return true;
}

function stake(p, side, amount) {
  if (!side || amount <= 0) return undefined;
  if (!takeCoins(p, amount)) {
    safe(() => p.sendMessage('§7You do not have that many doubloons.'));
    return null;
  }
  sound(p.dimension, 'bc.coins', p.location, 1, 1);
  return { player: p.id, side, amount };
}

async function battleForm(p, tableLoc) {
  if (busy(p, tableLoc)) return;
  const ids = factionIds();
  const names = ids.map((k) => `${DATA.factions[k].mc}${DATA.factions[k].name}`);
  const tactics = TACTIC_IDS.map((k) => TACTICS[k]);
  const purse = countCoins(p);
  const form = new ModalFormData().title('§lWar Table - muster the armies')
    .dropdown('§9Blue army', names, { defaultValueIndex: 0 })
    .dropdown('§9Blue tactic', tactics, { defaultValueIndex: 0 })
    .dropdown('§cRed army', names, { defaultValueIndex: 1 })
    .dropdown('§cRed tactic', tactics, { defaultValueIndex: 0 })
    .dropdown('§eGold army (optional third side)', ['None', ...names], { defaultValueIndex: 0 })
    .dropdown('§eGold tactic', tactics, { defaultValueIndex: 0 })
    .slider('Soldiers per side', 2, 12, { valueStep: 1, defaultValue: 5 })
    .toggle('Leaders join (captains, commodores) and steady their troops', { defaultValue: true })
    .toggle('Morale: losing armies can break and flee', { defaultValue: true })
    .toggle('Watch with the cinematic camera (sneak to stop)', { defaultValue: false })
    .dropdown('Bet on', ['No bet', '§9Blue', '§cRed', '§eGold'], { defaultValueIndex: 0 })
    .slider(`Stake (you have ${purse} doubloons; pays 2x, or 3x with three armies)`, 0, Math.max(10, Math.min(500, purse - (purse % 10))), { valueStep: 10, defaultValue: 0 });
  const res = await form.show(p);
  if (res.canceled || !res.formValues) return;
  const v = /** @type {any[]} */ (res.formValues);
  const [ia, ta, ib, tb, ic, tc, size, leaders, morale, watch, betSide, amount] = v;
  const fc = ic > 0 ? ids[ic - 1] : undefined;
  const sideKey = ['', 'a', 'b', 'c'][betSide];
  if (sideKey === 'c' && !fc) {
    safe(() => p.sendMessage('§7There is no Gold army to bet on.'));
    return;
  }
  const bet = stake(p, sideKey, amount);
  if (bet === null) return;
  const { center, facing } = arenaFor(p, tableLoc);
  const id = startBattle({ dim: p.dimension, center, facing, fa: ids[ia], fb: ids[ib], fc, size: Math.round(size), leaders, morale, bet,
    tactics: { a: TACTIC_IDS[ta], b: TACTIC_IDS[tb], c: TACTIC_IDS[tc] }, simulated: true, owner: p.id });
  if (watch) spectate(p, id);
}

async function duelForm(p, tableLoc) {
  if (busy(p, tableLoc)) return;
  const names = ATTRS.map((a) => `${DATA.attributes[a].mc}${DATA.attributes[a].name}`);
  const purse = countCoins(p);
  const form = new ModalFormData().title('§lWar Table - knight duel')
    .dropdown('§9Blue knight\'s magic', names, { defaultValueIndex: Math.floor(Math.random() * names.length) })
    .dropdown('§cRed knight\'s magic', names, { defaultValueIndex: Math.floor(Math.random() * names.length) })
    .slider('Knight level (more spells at 3 and 6)', 1, 10, { valueStep: 1, defaultValue: 6 })
    .toggle('Watch with the cinematic camera (sneak to stop)', { defaultValue: true })
    .dropdown('Bet on', ['No bet', '§9Blue', '§cRed'], { defaultValueIndex: 0 })
    .slider(`Stake (you have ${purse} doubloons)`, 0, Math.max(10, Math.min(500, purse - (purse % 10))), { valueStep: 10, defaultValue: 0 });
  const res = await form.show(p);
  if (res.canceled || !res.formValues) return;
  const [ia, ib, level, watch, betSide, amount] = /** @type {any[]} */ (res.formValues);
  const bet = stake(p, ['', 'a', 'b'][betSide], amount);
  if (bet === null) return;
  const { center, facing } = arenaFor(p, tableLoc);
  const id = startBattle({ dim: p.dimension, center, facing, fa: 'knights', fb: 'knights', size: 1, duel: true, bet, simulated: true, owner: p.id,
    roster: { a: [{ type: 'bc:magic_knight', attr: ATTRS[ia], level }], b: [{ type: 'bc:magic_knight', attr: ATTRS[ib], level }] } });
  if (watch) spectate(p, id);
}

async function eventsForm(p) {
  const names = Object.keys(EVENTS);
  const form = new ActionFormData().title('World events').body('§7Pick an event to start it here and now.');
  for (const n of names) form.button(`§l${n.replace(/_/g, ' ')}`);
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return;
  if (!runEvent(p, names[res.selection])) safe(() => p.sendMessage('§7That event cannot happen here right now.'));
}

async function openTable(p, tableLoc) {
  sound(p.dimension, 'bc.grimoire.flip', p.location, 0.8, 0.8);
  const on = eventsOn();
  const form = new ActionFormData().title('§lWar Table').body(
    '§7Muster two armies and watch them fight. Bet doubloons on the winner to double them.\n\n'
    + `§7Random world events are ${on ? '§aON' : '§cOFF'}§7.`);
  const acts = [];
  const live = activeBattleNear(p.dimension, tableLoc, 48);
  if (live) {
    form.button('§l>> Watch the battle\n§r§8Cinematic camera - sneak to stop');
    acts.push(() => spectate(p, live.id));
  }
  form.button('§l⚔ Start a battle\n§r§8Armies, tactics, a third side, bets');
  acts.push(() => battleForm(p, tableLoc));
  form.button('§l⚔ Knight duel\n§r§8Two knights, any magic, one winner');
  acts.push(() => duelForm(p, tableLoc));
  form.button('§l⚔ Random battle\n§r§8Two random armies with random tactics');
  acts.push(() => {
    if (busy(p, tableLoc)) return undefined;
    const ids = factionIds();
    const fa = pick(ids);
    let fb = pick(ids);
    while (fb === fa) fb = pick(ids);
    const { center, facing } = arenaFor(p, tableLoc);
    startBattle({ dim: p.dimension, center, facing, fa, fb, size: 5 + Math.floor(Math.random() * 4), leaders: true, simulated: true, owner: p.id,
      tactics: { a: pick(TACTIC_IDS), b: pick(TACTIC_IDS) } });
    return undefined;
  });
  if (reports.has(p.id)) {
    form.button('§lLast battle report');
    acts.push(() => new MessageFormData().title('Battle report').body(reports.get(p.id) ?? '').button1('OK').button2('Close').show(p));
  }
  form.button('§lState of the Kingdom\n§r§8Faction power and world news');
  acts.push(() => kingdomPage(p));
  form.button(`§lWorld events: ${on ? '§aON' : '§cOFF'}\n§r§8Toggle meteor showers, bosses, raids...`);
  acts.push(() => {
    setEvents(!on);
    safe(() => p.sendMessage(`§7Random world events are now ${!on ? '§aON' : '§cOFF'}§7.`));
  });
  if (isCreative(p)) {
    form.button('§lTrigger an event\n§r§8(creative)');
    acts.push(() => eventsForm(p));
  }
  form.button('§lHow it works');
  acts.push(() => new MessageFormData().title('War Table').body([
    '§lArmies§r\n§7' + Object.values(DATA.factions).map((f) => `${f.mc}${f.name}`).join('§7, ') + '§7.',
    '§lThe arena§r\n§7Soldiers appear about 14 blocks beyond the table in formation (melee in front, mages behind). Units only fight the other armies - unless you hit them.',
    '§lTactics§r\n§7Charge rushes in with a burst of speed. Hold the line waits for the enemy. Flank sends half the army around the side. Skirmish keeps mages at range.',
    '§lMorale§r\n§7Losses, a fallen leader or being badly outnumbered break an army\'s morale. Frightened soldiers flee; a living leader can rally them. Armies with no one left fighting lose.',
    '§lThe brain§r\n§7Knights and captains pick the best spell for the moment, lead moving targets, dodge spells, gang up on the weakest foe, protect hurt friends and fall back when wounded.',
    '§lBets§r\n§7Stake doubloons on a side: a win pays 2x (3x with three armies). A draw returns your stake.',
    '§lWorld events§r\n§7Every few minutes something may happen near a player: meteor showers, devil gates, pirate landings, skirmishes, a travelling merchant, sky treasure, a crimson night, or a giant boss.',
  ].join('\n\n')).button1('OK').button2('Close').show(p));
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return;
  await acts[res.selection]?.();
}

system.beforeEvents.startup.subscribe((ev) => {
  ev.blockComponentRegistry.registerCustomComponent('bc:war_table', {
    onPlayerInteract(e) {
      const p = e.player;
      if (!(p instanceof Player)) return;
      const loc = e.block.location;
      system.run(() => openTable(p, loc).catch(() => {}));
    },
  });
});

/** Skirmish Horn: two random armies clash in front of you. */
export function blowHorn(p) {
  const dir = V.flat(p.getViewDirection());
  const at = V.add(p.location, V.mul(dir, 16));
  if (activeBattleNear(p.dimension, at, 40)) {
    safe(() => p.sendMessage('§7A battle is already raging nearby.'));
    return false;
  }
  const top = safe(() => p.dimension.getTopmostBlock({ x: at.x, z: at.z }));
  at.y = top && Math.abs(top.location.y - p.location.y) < 10 ? top.location.y + 1 : p.location.y;
  const ids = factionIds();
  const fa = pick(ids);
  let fb = pick(ids);
  while (fb === fa) fb = pick(ids);
  startBattle({ dim: p.dimension, center: at, facing: dir, fa, fb, size: 4, leaders: Math.random() < 0.5, simulated: true,
    tactics: { a: pick(TACTIC_IDS), b: pick(TACTIC_IDS) } });
  return true;
}
