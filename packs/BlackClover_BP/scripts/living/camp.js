// Life in the squad: mood, rest and camp, banter, talking, specialisations, personal trials and gear.
// * MOOD: morale (victories, gifts, a cheerful friend, rest) and weariness (long fights). Inspired companions hit
//   harder; shaken ones lose their nerve; exhausted ones cast slower. Rest, camp and Field Rations fix it.
// * CAMP: "Make camp" with the whistle - everyone sits around a fire, recovers quickly and chats. At night one of them
//   keeps watch and raises the alarm when something creeps up.
// * TALK: ask how they feel, about their past and dreams, or for advice (once a day it builds bond).
// * SPECIALISATION: at level 10 choose Vanguard, Arcanist, Warden or Ranger; mastery comes at level 20 or with the
//   second personal trial. A Companion Tome lets them retrain.
// * TRIALS: at bond Friend a companion asks you for help with a personal trial; finishing it awakens their fifth
//   spell early and earns them a title. At Sworn Ally a second trial grants their specialisation's mastery.
// * GEAR: hand them an amulet; Field Rations take the weariness away.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { ActionFormData, MessageFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { on } from '../core/bus.js';
import { anim, particle, rgb, sound, title } from '../core/fx.js';
import { center, foesOf } from '../core/combat.js';
import { V, clamp, isCreative, pick, safe } from '../core/util.js';
import { rethink } from './ai.js';
import { nameKnight } from './knights.js';
import { isBoss } from './bosses.js';
import { heal } from './engine.js';
import {
  addBond, addMemberButtons, addProfileLines, addTalkHandler, addWhistleButtons, bark, bondRank, consumeHeld, entityOf, giveItem, memberOf, onMemberFall,
  onMemberTick, onPartyTick, party, save,
} from './companions.js';

const C = DATA.companion;
const SPEC_IDS = Object.keys(C.specs);
/** @type {Map<string, {at: any, dim: string, since: number, watch: string, alarmAt: number}>} */
const camps = new Map();
const banterAt = new Map();
/** @type {Map<string, number>} companion id -> ticks spent fighting since the last mood update */
const fightTime = new Map();

const night = () => {
  const t = world.getTimeOfDay();
  return t > 13000 && t < 23000;
};
function hash(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) h = Math.imul(h ^ str.charCodeAt(i), 16777619);
  return h >>> 0;
}
function say(p, m, text) {
  safe(() => p.sendMessage(`§b${m.name}§f: ${text.replace(/\{p\}/g, p.name)}`));
}

// ------------------------------------------------------------------------------- mood
function moodShift(m, morale, fatigue = 0) {
  const pers = C.personalities[m.personality];
  const before = { inspired: m.morale >= C.mood.inspired, tired: m.fatigue >= C.mood.exhausted };
  m.morale = clamp(m.morale + morale * (morale > 0 ? pers.morale ?? 1 : 1), 0, 100);
  m.fatigue = clamp(m.fatigue + fatigue, 0, 100);
  return before;
}

world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const dead = ev.deadEntity;
  const k = ev.damageSource.damagingEntity;
  const mo = k && !(k instanceof Player) ? memberOf(k) : undefined;
  if (mo) moodShift(mo.m, 2);
  if (isBoss(dead)) {
    for (const p of dead.dimension.getPlayers({ location: dead.location, maxDistance: 64 })) {
      for (const m of party(p).m) if (m.active && entityOf(m)) moodShift(m, 15);
      const first = party(p).m.find((m) => m.active && entityOf(m));
      if (first) {
        const e = entityOf(first);
        if (e) anim(e, 'animation.bc.magic_knight.victory');
      }
    }
  }
}, 'campMood'));

onMemberFall((p, m) => {
  moodShift(m, -15);
  for (const o of party(p).m) if (o !== m && o.active) moodShift(o, -5);
});

// each companion tires from its own fighting (foes within 16 blocks of it)
onMemberTick((p, m, e, i, pt, t, fighting) => {
  if (t % 20 !== 0) return;
  if (fighting || (safe(() => foesOf(e, 16).length) ?? 0) > 0) fightTime.set(m.cid, (fightTime.get(m.cid) ?? 0) + 20);
});

onPartyTick((p, pt, active, t, fighting) => {
  if (t % 200 !== 0) return;
  const camp = camps.get(p.id);
  const cheer = active.some((m) => m.personality === 'cheerful' && entityOf(m)) ? 1 : 0;
  for (const m of active) {
    const e = entityOf(m);
    if (!e) continue;
    const resting = !!camp || safe(() => p.isSneaking) === true;
    const fought = fightTime.get(m.cid) ?? 0;
    fightTime.set(m.cid, 0);
    // two points of weariness per 10 s of fighting; rest takes it away
    const weary = fought > 0 ? fought / 100 : camp ? -8 : resting ? -3 : -1.5;
    const before = moodShift(m, (fought ? 0 : 0.5) + cheer + (camp ? 3 : 0) + (m.morale < 60 ? 0.5 : -0.3), weary);
    if (!before.inspired && m.morale >= C.mood.inspired) bark(m, p, 'inspired');
    if (!before.tired && m.fatigue >= C.mood.exhausted) bark(m, p, 'tired', true);
    if (camp) heal(e, 2);
  }
});

// ------------------------------------------------------------------------------- camp & night watch
function campSpot(p) {
  const dir = V.flat(p.getViewDirection());
  const at = V.add(p.location, V.mul(dir, 3));
  const top = safe(() => p.dimension.getTopmostBlock({ x: at.x, z: at.z }));
  if (top && Math.abs(top.location.y + 1 - p.location.y) < 4) at.y = top.location.y + 1;
  else at.y = p.location.y;
  return at;
}

export function makeCamp(p) {
  const pt = party(p);
  const here = pt.m.filter((m) => m.active && entityOf(m));
  if (!here.length) {
    safe(() => p.sendMessage('§7Your companions need to be with you to make camp.'));
    return false;
  }
  if ((safe(() => p.dimension.getEntities({ location: p.location, maxDistance: 14, families: ['monster'] }).length) ?? 0) > 0) {
    safe(() => p.sendMessage('§7Not with monsters this close!'));
    return false;
  }
  const at = campSpot(p);
  const watcher = night() ? (here.find((m) => m.personality === 'loyal' || m.personality === 'cautious') ?? here[0]) : undefined;
  camps.set(p.id, { at, dim: p.dimension.id, since: system.currentTick, watch: watcher?.cid ?? '', alarmAt: 0 });
  here.forEach((m, i) => {
    const e = entityOf(m);
    const ang = (i / here.length) * Math.PI * 2;
    const seat = V.add(at, { x: Math.cos(ang) * 2.4, y: 0, z: Math.sin(ang) * 2.4 });
    safe(() => e.teleport(seat, { facingLocation: at }));
    if (m.cid === watcher?.cid) {
      bark(m, p, 'watch', true);
      anim(e, 'animation.bc.magic_knight.salute');
    } else safe(() => e.playAnimation('animation.bc.magic_knight.sit', { stopExpression: 'q.modified_move_speed > 0.02' }));
  });
  bark(here[0], p, 'camp', true);
  sound(p.dimension, 'fire.ignite', at, 1, 1);
  return true;
}

export function breakCamp(p, why = '') {
  const c = camps.get(p.id);
  if (!c) return;
  camps.delete(p.id);
  for (const m of party(p).m) {
    const e = entityOf(m);
    if (e) safe(() => e.playAnimation('animation.bc.magic_knight.idle', { blendOutTime: 0.1 }));
  }
  if (why) safe(() => p.onScreenDisplay.setActionBar(why));
}

export function campOf(p) {
  return camps.get(p.id);
}

onPartyTick((p, pt, active, t, fighting) => {
  const c = camps.get(p.id);
  if (!c) return;
  if (c.dim !== p.dimension.id || V.dist(p.location, c.at) > 16) return breakCamp(p, '§7You broke camp.');
  if (t % 20 === 0) {
    particle(p.dimension, 'bc:flame_burst', V.add(c.at, { x: 0, y: 0.3, z: 0 }), { scale: 0.25 });
    particle(p.dimension, 'bc:smoke_burst', V.add(c.at, { x: 0, y: 1.0, z: 0 }), { scale: 0.3 });
  }
  // the night watch
  if (c.watch) {
    const w = active.find((m) => m.cid === c.watch);
    const we = w ? entityOf(w) : undefined;
    const prowl = safe(() => p.dimension.getEntities({ location: c.at, maxDistance: 22, families: ['monster'] })) ?? [];
    if (we && (prowl.length || fighting) && c.alarmAt < t) {
      c.alarmAt = t + 400;
      bark(w, p, 'alarm', true);
      anim(we, 'animation.bc.magic_knight.point');
      title(p, '§c§lAMBUSH', `§7${w.name} spotted ${Math.max(1, prowl.length)} foe${prowl.length > 1 ? 's' : ''} in the dark`, 40);
      sound(p.dimension, 'bc.horn', p.location, 1, 0.8);
      breakCamp(p);
      return undefined;
    }
  }
  if (fighting) return breakCamp(p, '§cTo arms! §7Camp is broken.');
  // stories by the fire
  if (t % 200 === 0 && Math.random() < 0.3) banter(p, active);
});

function banter(p, active) {
  const here = active.filter((m) => {
    const e = entityOf(m);
    return e && V.dist(e.location, p.location) < 14;
  });
  if (here.length < 2) return;
  const a = pick(here);
  const b = pick(here.filter((x) => x !== a));
  const [l1, l2] = pick(C.banter);
  say(p, a, l1);
  system.runTimeout(() => say(p, b, l2), 50);
  banterAt.set(p.id, system.currentTick);
}

onPartyTick((p, pt, active, t, fighting) => {
  if (fighting || camps.has(p.id) || t % 600 !== 0) return;
  if (t - (banterAt.get(p.id) ?? -99999) < 2400 || Math.random() > 0.35) return;
  banter(p, active);
});

// ------------------------------------------------------------------------------- level milestones
onMemberTick((p, m, e, i, pt, t) => {
  if (t % 100 !== 0) return;
  if (m.level >= C.specLevel && !m.spec && !m.specNoted) {
    m.specNoted = true;
    title(p, `§b${m.name}`, '§6can choose a specialisation!', 50);
    safe(() => p.sendMessage(`§6${m.name} has reached level ${C.specLevel}! §7Open their profile with the §bCompanion Whistle§7 and choose: ${SPEC_IDS.map((s) => C.specs[s].name).join(', ')}.`));
    save(p);
  }
  if (m.spec && !m.mastery && m.level >= 20) grantMastery(p, m, 'level 20');
  if (safe(() => e.getDynamicProperty('bc:awake')) !== m.awakened) {
    safe(() => e.setDynamicProperty('bc:awake', m.awakened));
    rethink(e);
  }
});

function grantMastery(p, m, why) {
  if (!m.spec || m.mastery) return;
  m.mastery = true;
  const s = C.specs[m.spec];
  title(p, `§e${m.name}`, `§6${s.name} Mastery`, 60);
  safe(() => p.sendMessage(`§e★ ${m.name} masters the way of the ${s.name} (${why}). §7${s.mastery}`));
  sound(p.dimension, 'bc.fanfare', p.location, 1, 1.1);
  const e = entityOf(m);
  if (e) anim(e, 'animation.bc.magic_knight.victory');
  save(p);
}

async function chooseSpec(p, m) {
  const form = new ActionFormData().title(`${m.name}: specialisation`).body(`§7Choose how §b${m.name}§7 will fight from now on. ${C.personalities[m.personality].name} companions suit any path.\n`);
  for (const id of SPEC_IDS) {
    const s = C.specs[id];
    form.button(`§l${s.name}§r\n§8${s.desc.slice(0, 60)}${s.desc.length > 60 ? '...' : ''}`);
  }
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return false;
  const id = SPEC_IDS[res.selection];
  const s = C.specs[id];
  const ok = await new MessageFormData().title(s.name).body(`${s.desc}\n\n§6Skills:§r ${s.skills}\n§eMastery (level 20 or second trial):§r ${s.mastery}`)
    .button1('§aChoose').button2('Back').show(p);
  if (ok.selection !== 0) return chooseSpec(p, m);
  m.spec = id;
  m.mastery = m.level >= 20 || m.trialStage >= 2;
  save(p);
  const e = entityOf(m);
  if (e) {
    anim(e, 'animation.bc.magic_knight.salute');
    rethink(e);
  }
  title(p, `§b${m.name}`, `§6${s.name}`, 50);
  safe(() => p.sendMessage(`§b${m.name}§7 is now a §6${s.name}§7. ${s.skills}.`));
  return true;
}

// ------------------------------------------------------------------------------- personal trials
function offerTrial(p, m, stage) {
  const list = C.trials;
  const tr = list[(hash(m.cid) + stage * 3) % list.length];
  const count = stage === 2 ? tr.count * 2 : tr.count;
  m.trial = { stage, kind: tr.kind, target: tr.target, count, n: 0, text: tr.text.replace(/\d+/, String(count)) };
  bark(m, p, 'trial', true);
  safe(() => p.sendMessage(`§d✦ Personal trial (${stage === 1 ? 'Awakening' : 'Mastery'}): §f"${m.trial.text}" §7(track it in ${m.name}'s profile)`));
  sound(p.dimension, 'bc.chord', p.location, 0.8, 0.9);
  save(p);
}

function progressTrial(p, test, amount = 1) {
  let changed = false;
  for (const m of party(p).m) {
    const tr = m.trial;
    if (!tr || !m.active || !test(tr, m)) continue;
    const e = entityOf(m);
    if (!e || V.dist(e.location, p.location) > 32) continue;
    tr.n = Math.min(tr.count, tr.n + amount);
    changed = true;
    if (tr.n >= tr.count) completeTrial(p, m);
    else if (tr.n % Math.max(1, Math.floor(tr.count / 5)) === 0) safe(() => p.onScreenDisplay.setActionBar(`§d${m.name}'s trial: §f${tr.n}/${tr.count}`));
  }
  if (changed) save(p);
}

function completeTrial(p, m) {
  const stage = m.trial.stage;
  m.trial = null;
  m.trialStage = stage;
  bark(m, p, 'trial_done', true);
  const e = entityOf(m);
  if (e) {
    anim(e, 'animation.bc.magic_knight.victory');
    particle(e.dimension, 'bc:level_up', e.location);
    particle(e.dimension, 'bc:pillar', e.location, { color: rgb('ff9aff'), scale: 1.4 });
  }
  if (stage === 1) {
    m.awakened = true;
    m.title = C.trialTitles[hash(m.cid) % C.trialTitles.length];
    addBond(p, m, 100, 'trial');
    m.morale = 100;
    title(p, `§d${m.name} ${m.title}`, '§7Their grimoire awakens!', 70);
    if (e) {
      safe(() => e.setDynamicProperty('bc:awake', true));
      rethink(e);
    }
  } else {
    addBond(p, m, 150, 'trial');
    if (m.spec) grantMastery(p, m, 'their second trial');
    else safe(() => p.sendMessage(`§7${m.name} will master their specialisation the moment they choose one.`));
  }
  sound(p.dimension, 'bc.fanfare', p.location, 1, 1);
  save(p);
}

world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const dead = ev.deadEntity;
  const k = ev.damageSource.damagingEntity;
  if (!k) return;
  const p = k instanceof Player ? k : memberOf(k)?.p;
  if (!(p instanceof Player)) return;
  const typeId = safe(() => dead.typeId) ?? '';
  progressTrial(p, (tr) => tr.kind === 'kill' && (tr.target === typeId || (!tr.target.includes(':') && !!safe(() => dead.matches({ families: [tr.target] })))));
}, 'trialKill'));
on('boss', (p) => progressTrial(p, (tr) => tr.kind === 'boss'));
on('cast', (p) => progressTrial(p, (tr) => tr.kind === 'cast'));

onPartyTick((p, pt, active, t) => {
  if (t % 600 !== 0) return;
  for (const m of active) {
    if (m.trial || !entityOf(m)) continue;
    const rank = bondRank(m.bond);
    if (m.trialStage === 0 && rank >= 2) return offerTrial(p, m, 1);
    if (m.trialStage === 1 && rank >= 3) return offerTrial(p, m, 2);
  }
  return undefined;
});

// ------------------------------------------------------------------------------- talking
function feeling(m) {
  const pers = m.personality;
  if (m.fatigue >= C.mood.exhausted) return pick(['I\'m worn out. A camp and a hot meal would do wonders.', 'My mana feels like lead. Can we rest?']);
  if (m.morale >= C.mood.inspired) return pers === 'hothead' ? 'I feel unstoppable! Point me at something big!' : pick(['Never better! I feel like I could fly.', 'Honestly? This is the best squad I\'ve ever been in.']);
  if (m.morale <= C.mood.shaken) return pers === 'brave' ? 'I\'m fine. I\'m FINE. ...Maybe not fine.' : pick(['That last fight shook me. I\'ll be all right.', 'I keep seeing it when I close my eyes...']);
  return pick(['Steady. Ready for whatever comes next.', 'Not bad! A little hungry, maybe.', 'Good. Glad to be here with you, {p}.']);
}

async function talk(p, m) {
  const form = new ActionFormData().title(`Talk: ${m.name}`).body(`§7${C.personalities[m.personality].name} · ${DATA.attributes[m.attr].name} magic · from ${m.home}`);
  const acts = [];
  form.button('§lHow are you feeling?');
  acts.push(() => say(p, m, feeling(m)));
  form.button('§lTell me about yourself.');
  acts.push(() => {
    say(p, m, `I grew up in ${m.home}. My grimoire chose ${DATA.attributes[m.attr].name} magic when I was fifteen.`);
    system.runTimeout(() => say(p, m, `My dream? ${m.dream.charAt(0).toUpperCase()}${m.dream.slice(1)}.`), 40);
  });
  form.button('§lAny advice?');
  acts.push(() => say(p, m, pick(C.tips)));
  if (m.trial) {
    form.button(`§d§lYour trial\n§r§8${m.trial.n}/${m.trial.count}`);
    acts.push(() => say(p, m, `${m.trial.text} We're at ${m.trial.n} of ${m.trial.count}.`));
  }
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return;
  acts[res.selection]?.();
  const e = entityOf(m);
  if (e) anim(e, 'animation.bc.magic_knight.wave');
  const day = world.getDay();
  if (m.talkDay !== day) {
    m.talkDay = day;
    addBond(p, m, 3, 'talk');
    moodShift(m, 5);
    save(p);
  }
}

addMemberButtons((p, m) => {
  /** @type {{label: string, act: () => any}[]} */
  const out = [{ label: '§lTalk\n§r§8How they feel, their story, advice', act: () => talk(p, m) }];
  if (m.level >= C.specLevel && !m.spec) out.push({ label: '§6§lChoose a specialisation', act: () => chooseSpec(p, m) });
  if (m.amulet) {
    out.push({ label: `§lTake back the amulet\n§r§8${DATA.amulets[m.amulet]?.name ?? ''}`, act: () => {
      giveItem(p, new ItemStack(`bc:${m.amulet}`, 1));
      m.amulet = '';
      save(p);
    } });
  }
  return out;
});

addProfileLines((m) => {
  const out = [];
  if (m.trial) out.push(`§dTrial (${m.trial.stage === 1 ? 'Awakening' : 'Mastery'}): §f${m.trial.n}/${m.trial.count} §7- ${m.trial.text}`);
  else if (m.trialStage >= 2) out.push('§dTrials: §fall complete');
  out.push(`§7From §f${m.home}§7 - dreams ${m.dream}.`);
  return out;
});

// ------------------------------------------------------------------------------- gifts and gear
addTalkHandler(async (p, e, m, id) => {
  if (id === 'bc:field_rations') {
    m.fatigue = Math.max(0, m.fatigue - 50);
    moodShift(m, 10);
    heal(e, 10);
    anim(e, 'animation.bc.magic_knight.eat');
    sound(e.dimension, 'random.burp', e.location, 0.6, 1.1);
    say(p, m, pick(['Ahh, that hits the spot.', 'Real food! Thank you, {p}.', 'I feel brand new.']));
    if (!isCreative(p)) consumeHeld(p, id);
    save(p);
    return true;
  }
  if (id === 'bc:companion_tome') {
    if (m.level < C.specLevel) {
      say(p, m, `I'm not ready to specialise yet. Level ${C.specLevel}, then we'll talk.`);
      return true;
    }
    const old = m.spec;
    m.spec = '';
    m.mastery = false;
    if (await chooseSpec(p, m)) {
      if (!isCreative(p)) consumeHeld(p, id);
    } else {
      m.spec = old;
      m.mastery = !!old && (m.level >= 20 || m.trialStage >= 2);
    }
    save(p);
    return true;
  }
  if (id.startsWith('bc:fruit_') && DATA.fruits[id.slice(9)]) {
    // v0.6.0: feed them an Abyss Fruit - its power replaces the one they had
    const fid = id.slice(9);
    if (fid === m.fruit) {
      say(p, m, 'I already carry that power!');
      return true;
    }
    const old = DATA.fruits[m.fruit];
    m.fruit = fid;
    if (!isCreative(p)) consumeHeld(p, id);
    const f = DATA.fruits[fid];
    safe(() => e.setDynamicProperty('bc:fruit', fid));
    nameKnight(e);
    rethink(e);
    anim(e, 'animation.bc.magic_knight.eat');
    particle(e.dimension, 'bc:burst', center(e), { color: rgb(f.color), scale: 1 });
    particle(e.dimension, 'bc:magic_circle_ground', e.location, { color: rgb(f.color), size: 2.5, life: 1.2 });
    sound(e.dimension, 'bc.fruit.eat', e.location, 1, 1);
    say(p, m, `${f.mc}${f.name}§f... ${old ? `the ${old.name} fades, and ` : ''}a new power answers me!`);
    safe(() => p.sendMessage(`§7${m.name} now fights with the ${f.mc}${f.power}§7: ${f.abilities.map((a) => a.name).join(', ')}.`));
    save(p);
    return true;
  }
  if (id.startsWith('bc:') && id.slice(3).startsWith('amulet_')) {
    if (m.amulet) giveItem(p, new ItemStack(`bc:${m.amulet}`, 1));
    m.amulet = id.slice(3);
    if (!isCreative(p)) consumeHeld(p, id);
    anim(e, 'animation.bc.magic_knight.salute');
    say(p, m, `${DATA.amulets[m.amulet].name}§f? I'll wear it with pride.`);
    save(p);
    return true;
  }
  if (id === 'bc:mana_cookie' || id.startsWith('minecraft:cooked') || id === 'minecraft:bread' || id === 'minecraft:cake') {
    anim(e, 'animation.bc.magic_knight.eat');
    moodShift(m, 5, -5);
  }
  return false;
});

// the whistle: tactics and camp
addWhistleButtons((p, pt) => {
  const ids = Object.keys(C.tactics);
  const cur = pt.cfg.tactic;
  const next = ids[(ids.indexOf(cur) + 1) % ids.length];
  /** @type {{label: string, act: () => any}[]} */
  const out = [{
    label: `§lTactic: ${C.tactics[cur].name}\n§r§8next: ${C.tactics[next].name}`,
    act: () => {
      pt.cfg.tactic = next;
      save(p);
      safe(() => p.sendMessage(`§bParty tactic: §f${C.tactics[next].name}§7 - ${C.tactics[next].desc}`));
    },
  }];
  if (camps.has(p.id)) out.push({ label: '§lBreak camp', act: () => breakCamp(p, '§7You broke camp.') });
  else out.push({ label: '§lMake camp\n§r§8Rest, recover, talk - with a night watch', act: () => makeCamp(p) });
  return out;
});

