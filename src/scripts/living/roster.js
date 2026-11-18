// The Squad Banner and the Training Dummy.
// * SQUAD BANNER: your reserve (up to 6 knights beyond the 4 at your side). Swap knights in and out, and send reserve
//   knights on timed EXPEDITIONS (they run in real time, even while you are offline) that bring back loot and
//   experience - the stronger and better suited the knight, the better the odds. Reserve knights also train while
//   they wait (a little XP for every real minute, collected at the banner).
// * TRAINING DUMMY: place it anywhere. It shows your damage per second; hitting it gives a little magic XP, and with
//   training switched on (whistle) your companions practise on it between fights.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { ActionFormData, MessageFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { addFoes, ownerOf } from '../core/combat.js';
import { particle, rgb, sound } from '../core/fx.js';
import { addXp } from '../core/progress.js';
import { V, alive, clamp, isCreative, pick, rand, safe } from '../core/util.js';
import { giveKnightXp } from './knights.js';
import { addWhistleButtons, entityOf, giveItem, memberOf, onPartyTick, party, save } from './companions.js';

const C = DATA.companion;
const EXP = Object.fromEntries(C.expeditions.map((x) => [x.id, x]));
const ROBES = Object.keys(DATA.robes);
const AMULETS = Object.keys(DATA.amulets);
const TRAIN_XP_PER_MIN = 3;

function levelFromXp(m) {
  while (m.level < 20 && m.xp >= C.xp[m.level + 1]) m.level++;
}

// ------------------------------------------------------------------------------- expeditions
/** The odds a member brings an expedition home in good shape. */
export function expeditionChance(m, x) {
  const fit = { escort: ['ranger', 'vanguard'], ruins: ['arcanist'], devil_hunt: ['vanguard', 'warden'], witch_woods: ['warden', 'arcanist'],
    graveyard: ['vanguard', 'ranger'], patrol: ['ranger'] }[x.id] ?? [];
  let c = 0.55 + (m.level - x.level) * 0.04 - (x.danger - 1) * 0.04;
  if (fit.includes(m.spec)) c += 0.1;
  if (m.mastery) c += 0.05;
  c += (m.morale - 50) / 500 - m.fatigue / 400;
  if (m.personality === 'cautious') c += 0.04;
  if (m.personality === 'hothead') c -= 0.03;
  return clamp(c, 0.15, 0.95);
}

function rollLoot(x, success) {
  const out = [];
  for (const [id, lo, hi, chance] of x.loot) {
    if (Math.random() > chance * (success ? 1 : 0.5)) continue;
    const n = Math.max(1, Math.round(rand(lo, hi + 0.99) * (success ? 1 : 0.5)));
    const item = id === 'robe' ? `bc:${pick(ROBES)}` : id === 'amulet' ? `bc:${pick(AMULETS)}` : id;
    out.push([item, id === 'robe' || id === 'amulet' ? 1 : n]);
  }
  return out;
}

function memberById(pt, cid) {
  return [...pt.m, ...pt.r].find((m) => m.cid === cid);
}

/** Bring finished expeditions home: loot to the player, XP and mood to the knight. */
function collect(p) {
  const pt = party(p);
  const now = Date.now();
  const lines = [];
  pt.ex = pt.ex.filter((ex) => {
    if (ex.end > now) return true;
    const m = memberById(pt, ex.cid);
    const x = EXP[ex.id];
    if (!m || !x) return false;
    const ok = Math.random() < ex.chance;
    const loot = rollLoot(x, ok);
    for (const [id, n] of loot) giveItem(p, new ItemStack(id, n));
    m.xp += ok ? x.xp : Math.round(x.xp / 2);
    levelFromXp(m);
    m.morale = clamp(m.morale + (ok ? 10 : -20), 0, 100);
    m.fatigue = clamp(m.fatigue + (ok ? 30 : 80), 0, 100);
    m.away = '';
    lines.push(`${ok ? '§a✔' : '§c✘'} §b${m.name}§7 - ${x.name}: ${ok ? 'success' : 'came back hurt'} (${loot.map(([id, n]) => `${n}× ${id.replace(/^(bc|minecraft):/, '').replace(/_/g, ' ')}`).join(', ') || 'nothing'}; +${ok ? x.xp : Math.round(x.xp / 2)} XP)`);
    return false;
  });
  if (lines.length) {
    save(p);
    sound(p.dimension, 'bc.fanfare', p.location, 0.8, 1.1);
    for (const l of lines) safe(() => p.sendMessage(l));
  }
  return lines.length;
}

/** Reserve knights train while they wait. */
function trainReserve(p) {
  const pt = party(p);
  const now = Date.now();
  const last = typeof pt.cfg.trainAt === 'number' ? pt.cfg.trainAt : now;
  const minutes = Math.min(200, Math.floor((now - last) / 60000));
  if (minutes < 1) {
    if (typeof pt.cfg.trainAt !== 'number') pt.cfg.trainAt = now;
    return;
  }
  pt.cfg.trainAt = last + minutes * 60000;
  for (const m of pt.r) {
    if (m.away) continue;
    m.xp += minutes * TRAIN_XP_PER_MIN;
    levelFromXp(m);
    m.fatigue = Math.max(0, m.fatigue - minutes * 2);
  }
  save(p);
}

onPartyTick((p, pt, active, t) => {
  if (t % 400 !== 0 || !pt.ex.length) return;
  const now = Date.now();
  for (const ex of pt.ex) {
    if (ex.end > now || ex.told) continue;
    ex.told = true;
    const m = memberById(pt, ex.cid);
    if (m) safe(() => p.sendMessage(`§2⚑ §b${m.name}§2 is back from the ${EXP[ex.id]?.name ?? 'expedition'}! §7Collect the spoils at a §2Squad Banner§7.`));
    save(p);
  }
});

function timeLeft(ms) {
  const s = Math.max(0, Math.ceil(ms / 1000));
  return s >= 60 ? `${Math.floor(s / 60)}m ${s % 60}s` : `${s}s`;
}

async function pickMember(p, list, heading) {
  if (!list.length) return undefined;
  const form = new ActionFormData().title(heading);
  for (const m of list) form.button(`${DATA.attributes[m.attr].glyph} §l${m.name}§r §8Lv ${m.level}\n§8${C.personalities[m.personality].name}${m.spec ? ` · ${C.specs[m.spec].name}` : ''}`);
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return undefined;
  return list[res.selection];
}

async function swapIn(p) {
  const pt = party(p);
  const incoming = await pickMember(p, pt.r.filter((m) => !m.away), 'Bring into the party');
  if (!incoming) return;
  if (pt.m.length >= C.partyMax) {
    const out = await pickMember(p, pt.m, `Who goes to the reserve for ${incoming.name}?`);
    if (!out) return;
    toReserve(p, out);
  }
  pt.r = pt.r.filter((m) => m !== incoming);
  incoming.active = true;
  incoming.fallenAt = 0;
  incoming.eid = '';
  pt.m.push(incoming);
  save(p);
  safe(() => p.sendMessage(`§b${incoming.name}§7 joins the party. (Whistle them over if they don't appear.)`));
}

function toReserve(p, m) {
  const pt = party(p);
  const e = entityOf(m);
  if (e) {
    particle(e.dimension, 'bc:clover_leaves', e.location, { scale: 0.8 });
    safe(() => e.remove());
  }
  pt.m = pt.m.filter((x) => x !== m);
  m.active = false;
  m.eid = '';
  pt.r.push(m);
  save(p);
}

async function sendExpedition(p) {
  const pt = party(p);
  const m = await pickMember(p, pt.r.filter((x) => !x.away), 'Who goes on the expedition?');
  if (!m) return;
  const list = C.expeditions;
  const form = new ActionFormData().title(`${m.name}: expeditions`).body(`§7Level ${m.level} · ${C.personalities[m.personality].name}${m.spec ? ` · ${C.specs[m.spec].name}` : ''}\n§7Morale ${Math.round(m.morale)} · weariness ${Math.round(m.fatigue)}`);
  for (const x of list) {
    const ok = m.level >= x.level;
    form.button(ok ? `§l${x.name}§r §8${x.minutes} min\n§2${Math.round(expeditionChance(m, x) * 100)}% §8· danger ${'!'.repeat(x.danger)}` : `§8${x.name}\n§8needs level ${x.level}`);
  }
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return;
  const x = list[res.selection];
  if (m.level < x.level) {
    safe(() => p.sendMessage(`§7${m.name} needs level ${x.level} for the ${x.name}.`));
    return;
  }
  const chance = expeditionChance(m, x);
  const ok = await new MessageFormData().title(x.name).body(`${x.desc}\n\n§7Duration: §f${x.minutes} real minutes§7\nOdds for §b${m.name}§7: §f${Math.round(chance * 100)}%§7\nRewards: XP §f${x.xp}§7 and the spoils of the road.\n§8A failed expedition still returns - hurt, with half the spoils.`)
    .button1('§aSend them').button2('Not now').show(p);
  if (ok.selection !== 0) return;
  m.away = x.id;
  pt.ex.push({ cid: m.cid, id: x.id, start: Date.now(), end: Date.now() + x.minutes * 60000, chance, told: false });
  save(p);
  safe(() => p.sendMessage(`§2⚑ §b${m.name}§2 sets out on the ${x.name}. §7Back in ${x.minutes} minutes.`));
}

export async function openBanner(p) {
  const back = collect(p);
  trainReserve(p);
  const pt = party(p);
  const now = Date.now();
  const away = pt.ex.map((ex) => {
    const m = memberById(pt, ex.cid);
    return `§2⚑ §b${m?.name ?? '?'}§7 - ${EXP[ex.id]?.name ?? ex.id}: back in §f${timeLeft(ex.end - now)}`;
  });
  const body = [
    `§7Party §f${pt.m.length}/${C.partyMax}§7 · reserve §f${pt.r.length}/${C.reserveMax}§7${back ? ` · §a${back} expedition(s) returned!` : ''}`,
    pt.r.length ? `§7Reserve: ${pt.r.map((m) => `§b${m.name}§8 Lv${m.level}${m.away ? ' (away)' : ''}`).join('§7, ')}` : '§8No one in reserve. Recruit more knights - when your party is full they wait here.',
    ...away,
    `§8Reserve knights train while they wait (+${TRAIN_XP_PER_MIN} XP per real minute).`,
  ].join('\n');
  const form = new ActionFormData().title('§2§lSquad Banner').body(body);
  const acts = [];
  if (pt.r.some((m) => !m.away)) {
    form.button('§lBring a reserve knight into the party');
    acts.push(() => swapIn(p));
    form.button('§lSend a reserve knight on an expedition');
    acts.push(() => sendExpedition(p));
  }
  if (pt.m.length && pt.r.length < C.reserveMax) {
    form.button('§lSend a party member to the reserve');
    acts.push(async () => {
      const m = await pickMember(p, pt.m, 'Send to the reserve');
      if (m) toReserve(p, m);
    });
  }
  form.button('§8Close');
  acts.push(() => {});
  sound(p.dimension, 'bc.horn', p.location, 0.5, 1.4);
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return;
  await acts[res.selection]?.();
}

system.beforeEvents.startup.subscribe((ev) => {
  ev.blockComponentRegistry.registerCustomComponent('bc:squad_banner', {
    onPlayerInteract(e) {
      const p = e.player;
      if (!(p instanceof Player)) return;
      system.run(() => openBanner(p).catch(() => {}));
    },
  });
});

// ------------------------------------------------------------------------------- the Training Dummy
/** @type {Map<string, {total: number, first: number, last: number, lastHit: number}>} */
const dummies = new Map();
/** @type {Map<string, {day: number, n: number}>} player XP from dummies today */
const playerXp = new Map();

export function placeDummy(p) {
  const hit = safe(() => p.getBlockFromViewDirection({ maxDistance: 6 }));
  const b = hit?.block;
  const at = b ? { x: b.location.x + 0.5, y: b.location.y + 1, z: b.location.z + 0.5 } : V.add(p.location, V.mul(V.flat(p.getViewDirection()), 2));
  const e = safe(() => p.dimension.spawnEntity('bc:training_dummy', at));
  if (!e) return false;
  safe(() => {
    e.setDynamicProperty('bc:dummy_owner', p.id);
    e.nameTag = '§eTraining Dummy §7- hit me!';
  });
  if (!isCreative(p)) {
    const inv = p.getComponent('minecraft:inventory')?.container;
    const it = inv?.getItem(p.selectedSlotIndex);
    if (it?.typeId === 'bc:training_dummy') {
      if (it.amount > 1) {
        it.amount -= 1;
        inv.setItem(p.selectedSlotIndex, it);
      } else inv.setItem(p.selectedSlotIndex, undefined);
    }
  }
  sound(p.dimension, 'dig.wood', at, 1, 1);
  return true;
}

world.afterEvents.entityHurt.subscribe((ev) => safe(() => {
  const d = ev.hurtEntity;
  if (d.typeId !== 'bc:training_dummy') return;
  const t = system.currentTick;
  const h = d.getComponent('minecraft:health');
  if (h) h.setCurrentValue(h.effectiveMax);
  let st = dummies.get(d.id);
  if (!st || t - st.last > 100) st = { total: 0, first: t, last: t, lastHit: 0 };
  st.total += ev.damage;
  st.last = t;
  st.lastHit = ev.damage;
  dummies.set(d.id, st);
  const secs = Math.max(1, (t - st.first) / 20);
  d.nameTag = `§eDPS §f${(st.total / secs).toFixed(1)} §7| last §f${ev.damage.toFixed(1)} §7| total §f${Math.round(st.total)}`;
  safe(() => d.playAnimation('animation.bc.training_dummy.hit'));
  particle(d.dimension, 'bc:dust_burst', V.add(d.location, { x: 0, y: 1.2, z: 0 }), { color: rgb('c8a044'), scale: 0.4 });
  const src = ev.damageSource.damagingEntity;
  if (src instanceof Player) {
    const day = world.getDay();
    const px = playerXp.get(src.id);
    const rec = px && px.day === day ? px : { day, n: 0 };
    if (rec.n < 200) {
      rec.n += 1;
      addXp(src, 1);
    }
    playerXp.set(src.id, rec);
  } else if (src) {
    const mo = memberOf(src);
    if (mo) {
      const day = world.getDay();
      if (mo.m.xpDay !== day) {
        mo.m.xpDay = day;
        mo.m.xpToday = 0;
      }
      if (mo.m.xpToday < 400) {
        mo.m.xpToday += 2;
        giveKnightXp(src, 2);
      }
    }
  }
}, 'dummy'));

world.afterEvents.playerInteractWithEntity.subscribe((ev) => {
  if (ev.target.typeId !== 'bc:training_dummy' || !ev.player.isSneaking) return;
  const d = ev.target;
  const p = ev.player;
  system.run(() => safe(() => {
    if (!alive(d)) return;
    particle(d.dimension, 'bc:dust_burst', d.location, { color: rgb('c8a044'), scale: 0.8 });
    d.remove();
    if (!isCreative(p)) giveItem(p, new ItemStack('bc:training_dummy', 1));
  }, 'dummyPickup'));
});

// companions practise on dummies near you when training is on
addFoes((e, range) => {
  const owner = ownerOf(e);
  if (!owner || e.typeId !== 'bc:magic_knight') return [];
  const p = world.getEntity(owner);
  if (!(p instanceof Player) || !party(p).cfg.train) return [];
  return safe(() => e.dimension.getEntities({ location: e.location, maxDistance: Math.min(range, 16), type: 'bc:training_dummy' })) ?? [];
});

addWhistleButtons((p, pt) => [{
  label: `§lTraining: ${pt.cfg.train ? '§aon' : '§coff'}\n§r§8Practise on Training Dummies between fights`,
  act: () => {
    pt.cfg.train = !pt.cfg.train;
    save(p);
    if (pt.cfg.train) {
      const near = safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 16, type: 'bc:training_dummy' }).length) ?? 0;
      safe(() => p.sendMessage(near ? '§aTraining on: your companions will practise on the dummy.' : '§7Training on - place a §6Training Dummy§7 near you.'));
    }
  },
}]);

