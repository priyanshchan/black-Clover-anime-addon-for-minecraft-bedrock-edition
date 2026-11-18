// World simulation: the four great factions - the Clover Magic Knights, the Devil Host, the Sea Raiders and the
// Tidewatch Navy - each have a POWER (0-100). It falls when their people die and rises when they win real
// battles (not War Table games). Off screen, rivals keep fighting, and the news reaches you. Strong factions
// show up more often in world events, and a dominant one launches an offensive near a player.
import { Player, system, world } from '@minecraft/server';
import { MessageFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { factionOf, teamOf } from '../core/combat.js';
import { title } from '../core/fx.js';
import { pick, rand, safe } from '../core/util.js';
import { onBattleEnd } from './battle.js';

/** natural faction (combat.js) -> War Table faction id */
const KEY = { clover: 'knights', devil: 'devils', pirate: 'raiders', navy: 'navy' };
export const POWERS = ['knights', 'devils', 'raiders', 'navy'];
export const RIVAL = { knights: 'devils', devils: 'knights', raiders: 'navy', navy: 'raiders' };
const OFFSCREEN = {
  knights: ['Magic Knights sealed a devil nest in the far hills.', 'A Magic Knight squad drove the devils from a border village.'],
  devils: ['A Magic Knight outpost fell to the Devil Host.', 'Dark Disciples burned a chapel of the Clover Kingdom.'],
  navy: ['The Tidewatch sank a raider ship off the coast.', 'A Tidewatch commodore hanged a dozen pirates at the harbour.'],
  raiders: ['Sea Raiders plundered a Tidewatch supply ship.', 'Pirates raided a fishing town and vanished with the tide.'],
};

/** @type {{power: Record<string, number>, news: {day: number, text: string}[], offensiveAt: number}} */
let S;
function load() {
  if (S) return S;
  const raw = safe(() => world.getDynamicProperty('bc:world'));
  try {
    S = typeof raw === 'string' ? JSON.parse(raw) : undefined;
  } catch {
    S = undefined;
  }
  S = S ?? { power: {}, news: [], offensiveAt: 0 };
  for (const f of POWERS) if (typeof S.power[f] !== 'number') S.power[f] = 50;
  return S;
}
let dirty = false;
function save() {
  dirty = true;
}
system.runInterval(() => {
  if (!dirty) return;
  dirty = false;
  safe(() => world.setDynamicProperty('bc:world', JSON.stringify(load())));
}, 100);

export function power(f) {
  return load().power[f] ?? 50;
}
/** Event weight multiplier from a faction's power (1.0 at 50, about 1.5 at 90, 0.5 at 10). */
export function powerMul(f) {
  return 0.4 + (power(f) / 100) * 1.2;
}
export function shift(f, amount) {
  if (!(f in load().power)) return;
  S.power[f] = Math.max(5, Math.min(95, S.power[f] + amount));
  save();
}
export function news(text) {
  const day = safe(() => world.getDay()) ?? 0;
  load().news.unshift({ day, text });
  S.news = S.news.slice(0, 10);
  save();
}

// ------------------------------------------------------------------------------- what moves the balance
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const dead = ev.deadEntity;
  if (teamOf(dead)) return; // battles are settled in onBattleEnd
  const f = KEY[factionOf(dead)];
  const k = ev.damageSource.damagingEntity;
  if (dead.typeId === 'bc:devil_gate') {
    shift('devils', -5);
    news(k instanceof Player ? `${k.name} sealed a Devil Gate.` : 'A Devil Gate collapsed.');
  } else if (dead.typeId === 'bc:archdevil') {
    shift('devils', -15);
    news(`The Archdevil was slain${k instanceof Player ? ` by ${k.name}` : ''}! The Devil Host reels.`);
  } else if (dead.typeId === 'bc:phantom_galleon') {
    shift('raiders', -10);
    news('The Phantom Galleon was sent to the bottom of the sky.');
  } else if (dead.typeId === 'bc:stone_colossus') news('A Stone Colossus crumbled back into the mountains.');
  else if (dead.typeId === 'bc:storm_kraken') news('The Storm Kraken sank beneath the waves.');
  if (!f) return;
  shift(f, k instanceof Player ? -0.5 : -0.3);
  const kf = k ? KEY[factionOf(k)] : undefined;
  if (kf && kf !== f) shift(kf, 0.3);
}, 'worldsim'));

onBattleEnd((b, winner) => {
  if (b.simulated || b.duel || !winner) return;
  const wf = b.sides[winner].f;
  if (!POWERS.includes(wf)) return;
  shift(wf, 6);
  for (const [k, s] of Object.entries(b.sides)) if (k !== winner) shift(s.f, -6);
  const losers = Object.entries(b.sides).filter(([k]) => k !== winner).map(([, s]) => DATA.factions[s.f].name).join(' and ');
  news(`${DATA.factions[wf].name} defeated the ${losers} near ${Math.round(b.center.x)}, ${Math.round(b.center.z)}.`);
});

// ------------------------------------------------------------------------------- the world turns (every 5 minutes)
/** @type {((attacker: string, defender: string) => boolean)[]} */
const offensiveHandlers = [];
export function onOffensive(fn) {
  offensiveHandlers.push(fn);
}

system.runInterval(() => {
  const st = load();
  for (const f of POWERS) shift(f, (50 - st.power[f]) * 0.04 + rand(-1.5, 1.5));
  if (Math.random() < 0.35) {
    const a = pick(POWERS);
    const d = RIVAL[a];
    const winner = Math.random() < power(a) / (power(a) + power(d)) ? a : d;
    shift(winner, 3);
    shift(RIVAL[winner], -3);
    news(pick(OFFSCREEN[winner]));
  }
  const strongest = POWERS.reduce((x, y) => (power(y) > power(x) ? y : x));
  const t = system.currentTick;
  if (power(strongest) >= 80 && t > st.offensiveAt && world.getDynamicProperty('bc:events') !== 'off') {
    for (const fn of offensiveHandlers) {
      if (safe(() => fn(strongest, RIVAL[strongest]))) {
        st.offensiveAt = t + 20 * 60 * 20;
        news(`${DATA.factions[strongest].name} launched an offensive against the ${DATA.factions[RIVAL[strongest]].name}!`);
        break;
      }
    }
  }
}, 6000);

// ------------------------------------------------------------------------------- the Handbook / War Table page
function bar(v) {
  const n = Math.round(v / 10);
  return `§a${'|'.repeat(n)}§8${'|'.repeat(10 - n)}`;
}

export async function kingdomPage(p) {
  const st = load();
  let body = '§7The great powers of the world rise and fall with every battle - including the ones you fight.\n\n';
  for (const f of POWERS) {
    const v = st.power[f];
    const mood = v >= 80 ? '§6dominant' : v >= 60 ? '§aon the rise' : v >= 40 ? '§7holding' : v >= 20 ? '§cweakened' : '§4broken';
    body += `${DATA.factions[f].mc}§l${DATA.factions[f].name}§r\n${bar(v)} §f${Math.round(v)} §7- ${mood}\n`;
  }
  body += '\n§lNews§r\n';
  body += st.news.length ? st.news.map((n) => `§8Day ${n.day}: §7${n.text}`).join('\n') : '§8No news yet.';
  body += '\n\n§8Strong factions appear more often in world events. A dominant one launches offensives.';
  await new MessageFormData().title('State of the Kingdom').body(body).button1('OK').button2('Close').show(p);
}

export { title };
