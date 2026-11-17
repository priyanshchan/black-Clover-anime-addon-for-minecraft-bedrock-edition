// The War Table: a battle simulator. Pick two factions and an army size, bet on a side, and watch them fight.
import { Player, system } from '@minecraft/server';
import { ActionFormData, MessageFormData, ModalFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { sound } from '../core/fx.js';
import { V, isCreative, pick, safe } from '../core/util.js';
import { countCoins } from '../sea/bounty.js';
import { activeBattleNear, factionIds, startBattle } from './battle.js';
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

async function battleForm(p, tableLoc) {
  if (activeBattleNear(p.dimension, tableLoc, 48)) {
    safe(() => p.sendMessage('§7A battle is already raging here. Wait for it to end.'));
    return;
  }
  const ids = factionIds();
  const names = ids.map((k) => `${DATA.factions[k].mc}${DATA.factions[k].name}`);
  const purse = countCoins(p);
  const form = new ModalFormData().title('§lWar Table')
    .dropdown('§9Blue army', names, { defaultValueIndex: 0 })
    .dropdown('§cRed army', names, { defaultValueIndex: 1 })
    .slider('Soldiers per side', 2, 12, { valueStep: 1, defaultValue: 5 })
    .toggle('Leaders join the fight (captains, commodores)', { defaultValue: true })
    .dropdown('Bet on', ['No bet', '§9Blue', '§cRed'], { defaultValueIndex: 0 })
    .slider(`Stake (you have ${purse} doubloons)`, 0, Math.max(10, Math.min(500, purse - (purse % 10))), { valueStep: 10, defaultValue: 0 });
  const res = await form.show(p);
  if (res.canceled || !res.formValues) return;
  const [ia, ib, size, leaders, betSide, stake] = /** @type {[number, number, number, boolean, number, number]} */ (/** @type {unknown} */ (res.formValues));
  let bet;
  if (betSide > 0 && stake > 0) {
    if (!takeCoins(p, stake)) {
      safe(() => p.sendMessage('§7You do not have that many doubloons.'));
      return;
    }
    bet = { player: p.id, side: betSide === 1 ? 'a' : 'b', amount: stake };
    sound(p.dimension, 'bc.coins', p.location, 1, 1);
  }
  const { center, facing } = arenaFor(p, tableLoc);
  startBattle({ dim: p.dimension, center, facing, fa: ids[ia], fb: ids[ib], size: Math.round(size), leaders, bet });
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
  form.button('§l⚔ Start a battle\n§r§8Choose the armies');
  acts.push(() => battleForm(p, tableLoc));
  form.button('§l⚔ Random battle\n§r§8Two random armies, 5 a side');
  acts.push(() => {
    if (activeBattleNear(p.dimension, tableLoc, 48)) return safe(() => p.sendMessage('§7A battle is already raging here.'));
    const ids = factionIds();
    const fa = pick(ids);
    let fb = pick(ids);
    while (fb === fa) fb = pick(ids);
    const { center, facing } = arenaFor(p, tableLoc);
    startBattle({ dim: p.dimension, center, facing, fa, fb, size: 5, leaders: true });
    return undefined;
  });
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
    '§lThe arena§r\n§7Soldiers appear about 14 blocks beyond the table, Blue on the left and Red on the right. Units only fight the other army - unless you hit them.',
    '§lBets§r\n§7Stake doubloons on a side. If it wins, you get double back. A draw returns your stake.',
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
  startBattle({ dim: p.dimension, center: at, facing: dir, fa, fb, size: 4, leaders: Math.random() < 0.5 });
  return true;
}
