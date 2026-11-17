// Magic Knights: named NPC mages of every attribute. They roam, hunt monsters, pirates and devils, fight in
// War Table battles and grow stronger with every kill (levels 1-10 unlock more of their grimoire).
// Talk to a knight to see its profile, recruit it, and give your own knights orders.
// Their fighting is driven by the tactical brain in ai.js.
import { Player, system, world } from '@minecraft/server';
import { ActionFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { center, teamOf } from '../core/combat.js';
import { anim, particle, rgb, sound, title } from '../core/fx.js';
import { V, alive, pick, rand, safe, yawOf } from '../core/util.js';
import { countCoins } from '../sea/bounty.js';

const ATTRS = DATA.order.filter((a) => a !== 'anti');
/** knight XP needed for levels 1..10 */
const XP_AT = [0, 0, 20, 60, 120, 200, 320, 480, 700, 1000, 1400];
export const RANK = ['', 'Junior', 'Junior', 'Intermediate', 'Intermediate', 'Senior', 'Senior', 'First Class', 'First Class', 'Vice-Captain', 'Captain',
  'Captain', 'Captain', 'Captain', 'Captain', 'Champion', 'Champion', 'Champion', 'Champion', 'Champion', 'Royal Champion'];
const MAX_HIRED = DATA.companion.partyMax;

/** companions.js plugs in here (knights.js must not import it) */
const hooks = {
  /** @type {(e: any, p: any) => void} */ onEnlist: () => {},
  /** @type {(p: any) => number} */ partySize: (p) => hiredBy(p).length,
  /** @type {((p: any, e: any, item: any) => Promise<void> | void) | undefined} */ talk: undefined,
};
export function setCompanionHooks(h) {
  Object.assign(hooks, h);
}
function isCompanion(e) {
  return typeof safe(() => e.getDynamicProperty('bc:cid')) === 'string';
}

export function knightAttr(e) {
  const v = safe(() => e.getDynamicProperty('bc:attr'));
  return typeof v === 'string' && DATA.attributes[v] ? v : 'wind';
}
export function knightLevel(e) {
  const v = safe(() => e.getDynamicProperty('bc:klv'));
  return typeof v === 'number' ? v : 1;
}
function knightName(e) {
  const v = safe(() => e.getDynamicProperty('bc:kname'));
  return typeof v === 'string' ? v : 'Magic Knight';
}

/** Refresh the name shown above a knight: name, rank and attribute glyph. */
export function nameKnight(e) {
  safe(() => {
    const prefix = safe(() => e.getDynamicProperty('bc:prefix')) ?? '§a';
    const lv = knightLevel(e);
    e.nameTag = `${prefix}${knightName(e)} §7${RANK[lv]} §r${DATA.attributes[knightAttr(e)].glyph}`;
  });
}

/** Give a knight its attribute, name, level and (optionally) robe. */
export function setupKnight(e, opts = {}) {
  safe(() => {
    e.setDynamicProperty('bc:attr', opts.attr ?? pick(ATTRS));
    e.setDynamicProperty('bc:kname', opts.name ?? `${pick(DATA.knightFirst)} ${pick(DATA.knightLast)}`);
    e.setDynamicProperty('bc:prefix', opts.prefix ?? '§a');
    const lv = opts.level ?? (Math.random() < 0.25 ? 1 + Math.floor(Math.random() * 4) : 1);
    e.setDynamicProperty('bc:klv', lv);
    e.setDynamicProperty('bc:kxp', XP_AT[lv]);
    if (opts.robe !== undefined) e.setProperty('bc:robe', opts.robe);
    else if (opts.randomRobe) e.setProperty('bc:robe', Math.floor(Math.random() * DATA.knightRobes.length));
  }, 'setupKnight');
  nameKnight(e);
}

function track(e) {
  if (e.typeId !== 'bc:magic_knight') return;
  if (typeof safe(() => e.getDynamicProperty('bc:attr')) !== 'string') setupKnight(e);
}
world.afterEvents.entitySpawn.subscribe((ev) => safe(() => track(ev.entity)));
world.afterEvents.entityLoad.subscribe((ev) => safe(() => track(ev.entity)));

/**
 * The spells a knight of this attribute and level knows (engine recipes only).
 * Level 1: two spells, level 3: three, level 6: the grimoire's ultimate.
 */
export function kitFor(attr, level = 1) {
  if (DATA.npcKits[attr]) return DATA.npcKits[attr];
  const specs = DATA.spells[attr]?.map((sp) => sp.spec).filter(Boolean) ?? [];
  const n = level >= 6 ? 4 : level >= 3 ? 3 : 2;
  const kit = specs.slice(0, n).filter((s) => s.t !== 'wall');
  return kit.length ? kit : DATA.npcKits.wind;
}

export function face(e, target) {
  safe(() => e.setRotation({ x: 0, y: yawOf(V.sub(target.location, e.location)) }));
}

// ------------------------------------------------------------------------------- experience
/** @type {((e: any) => void)[]} */
const levelHooks = [];
export function onKnightLevel(fn) {
  levelHooks.push(fn);
}

export function giveKnightXp(e, amount) {
  if (!alive(e) || e.typeId !== 'bc:magic_knight') return;
  const xp = (safe(() => e.getDynamicProperty('bc:kxp')) ?? 0) + amount;
  safe(() => e.setDynamicProperty('bc:kxp', xp));
  const table = isCompanion(e) ? DATA.companion.xp : XP_AT;
  const cap = table.length - 1;
  let lv = knightLevel(e);
  const before = lv;
  while (lv < cap && xp >= table[lv + 1]) lv++;
  if (lv === before) return;
  safe(() => e.setDynamicProperty('bc:klv', lv));
  nameKnight(e);
  particle(e.dimension, 'bc:level_up', e.location);
  particle(e.dimension, 'bc:clover_leaves', center(e), { scale: 0.8 });
  sound(e.dimension, 'bc.levelup', e.location, 0.8, 1.2);
  for (const fn of levelHooks) safe(() => fn(e));
  const owner = world.getEntity(/** @type {string} */ (safe(() => e.getDynamicProperty('bc:owner')) ?? ''));
  if (owner instanceof Player) {
    const extra = lv === 3 ? ' and learned a third spell' : lv === 6 ? ' and mastered their grimoire' : '';
    safe(() => owner.sendMessage(`§b${knightName(e)}§f is now a §e${RANK[lv]}§f knight (level ${lv})${extra}!`));
  }
}

world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const k = ev.damageSource.damagingEntity;
  if (!k || k.typeId !== 'bc:magic_knight') return;
  const dead = ev.deadEntity;
  const big = safe(() => dead.matches({ families: ['boss'] }));
  const kills = (safe(() => k.getDynamicProperty('bc:kills')) ?? 0) + 1;
  safe(() => k.setDynamicProperty('bc:kills', kills));
  giveKnightXp(k, big ? 150 : dead.typeId.startsWith('bc:') ? 18 : 10);
}, 'knightKill'));

// ------------------------------------------------------------------------------- hiring & orders
function hiredBy(p) {
  return safe(() => p.dimension.getEntities({ type: 'bc:magic_knight', location: p.location, maxDistance: 128 })
    .filter((e) => e.getDynamicProperty('bc:owner') === p.id)) ?? [];
}

function enlist(e, p) {
  safe(() => {
    e.triggerEvent('bc:hire');
    e.setDynamicProperty('bc:owner', p.id);
    e.setDynamicProperty('bc:prefix', '§b');
    e.setDynamicProperty('bc:order', 'follow');
    e.getComponent('minecraft:tameable')?.tame(p);
  });
  nameKnight(e);
  safe(() => hooks.onEnlist(e, p));
}

/** Use a Knight Contract: a Magic Knight joins you as a companion. */
export function hireKnight(p) {
  if (hooks.partySize(p) >= MAX_HIRED) {
    safe(() => p.sendMessage(`§7You already lead ${MAX_HIRED} knights. Release one before hiring another.`));
    return false;
  }
  const dir = V.flat(p.getViewDirection());
  const loc = V.add(p.location, V.mul(dir, 2));
  const e = safe(() => p.dimension.spawnEntity('bc:magic_knight', loc, { spawnEvent: 'bc:hire' }));
  if (!e) return false;
  setupKnight(e, { randomRobe: true, prefix: '§b', level: 2 });
  enlist(e, p);
  const a = DATA.attributes[knightAttr(e)];
  particle(p.dimension, 'bc:magic_circle_ground', V.add(loc, { x: 0, y: 0.1, z: 0 }), { color: rgb(a.color), size: 2.5, life: 1.5 });
  particle(p.dimension, 'bc:clover_leaves', center(e), { scale: 1 });
  sound(p.dimension, 'bc.fanfare', loc, 0.8, 1.1);
  safe(() => p.sendMessage(`${a.glyph} §b${knightName(e)}§f, a ${a.mc}${a.name}§f mage, swears to fight at your side. §7(Talk to them to give orders.)`));
  return true;
}

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

function profile(e, roleInfo) {
  const a = DATA.attributes[knightAttr(e)];
  const lv = knightLevel(e);
  const xp = safe(() => e.getDynamicProperty('bc:kxp')) ?? 0;
  const table = isCompanion(e) ? DATA.companion.xp : XP_AT;
  const kills = safe(() => e.getDynamicProperty('bc:kills')) ?? 0;
  const stars = (v) => '★'.repeat(Math.max(1, Math.round(v * 5))).padEnd(5, '☆');
  const known = kitFor(knightAttr(e), lv).length;
  return `${a.glyph} ${a.mc}§l${knightName(e)}§r\n`
    + `§7${RANK[lv]} Magic Knight - level §e${lv}§7 (${xp}${lv < table.length - 1 ? `/${table[lv + 1]}` : ''} XP)\n`
    + `§7Magic: ${a.mc}${a.name}§7 - knows ${known} spell${known > 1 ? 's' : ''}\n`
    + `§7Fighting style: §f${roleInfo.role}§7   Kills: §f${kills}\n`
    + `§7Skill: §e${stars(roleInfo.skill)}§7   Courage: §e${stars(roleInfo.courage)}`;
}

/** @type {(e: any) => {role: string, skill: number, courage: number}} */
let roleOfKnight = () => ({ role: 'striker', skill: 0.6, courage: 0.6 });
export function setRoleProvider(fn) {
  roleOfKnight = fn;
}

async function talk(p, e) {
  const owner = safe(() => e.getDynamicProperty('bc:owner'));
  const body = profile(e, roleOfKnight(e));
  const form = new ActionFormData().title('Magic Knight').body(body);
  const acts = [];
  if (owner === p.id) {
    const order = safe(() => e.getDynamicProperty('bc:order')) ?? 'follow';
    const stance = safe(() => e.getDynamicProperty('bc:stance')) ?? 'aggressive';
    form.button(`${order === 'follow' ? '§2> ' : ''}§lFollow me`);
    acts.push(() => {
      e.setDynamicProperty('bc:order', 'follow');
      e.triggerEvent('bc:order_follow');
      return 'falls in behind you';
    });
    form.button(`${order === 'hold' ? '§2> ' : ''}§lHold this position`);
    acts.push(() => {
      e.setDynamicProperty('bc:order', 'hold');
      e.setDynamicProperty('bc:anchor', JSON.stringify({ x: e.location.x, y: e.location.y, z: e.location.z }));
      e.triggerEvent('bc:order_hold');
      return 'will hold this ground';
    });
    form.button(`§lStance: ${stance === 'aggressive' ? '§cAggressive' : '§9Defensive'}\n§r§8Switch: ${stance === 'aggressive' ? 'only guard you' : 'hunt any foe'}`);
    acts.push(() => {
      e.setDynamicProperty('bc:stance', stance === 'aggressive' ? 'defensive' : 'aggressive');
      return stance === 'aggressive' ? 'will stay close and guard you' : 'will hunt down any foe';
    });
    form.button('§8Release from service');
    acts.push(() => {
      e.triggerEvent('bc:release');
      e.setDynamicProperty('bc:owner', undefined);
      e.setDynamicProperty('bc:order', undefined);
      e.setDynamicProperty('bc:prefix', '§a');
      nameKnight(e);
      return 'salutes and goes their own way';
    });
  } else if (!owner && !teamOf(e)) {
    const price = 100 + knightLevel(e) * 25;
    form.button(`§lRecruit\n§r§8A Knight Contract, or ${price} doubloons`);
    acts.push(() => {
      if (hooks.partySize(p) >= MAX_HIRED) return `cannot join - you already lead ${MAX_HIRED} companions`;
      const inv = p.getComponent('minecraft:inventory')?.container;
      let paid = false;
      for (let i = 0; inv && i < inv.size && !paid; i++) {
        const it = inv.getItem(i);
        if (it?.typeId !== 'bc:knight_contract') continue;
        if (it.amount > 1) {
          it.amount -= 1;
          inv.setItem(i, it);
        } else inv.setItem(i, undefined);
        paid = true;
      }
      if (!paid && !takeCoins(p, price)) return `asks for a Knight Contract or ${price} doubloons`;
      enlist(e, p);
      sound(e.dimension, 'bc.fanfare', e.location, 0.8, 1.1);
      return 'joins your company';
    });
  }
  form.button('Goodbye');
  acts.push(() => undefined);
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return;
  const msg = safe(() => acts[res.selection]?.());
  if (msg) safe(() => p.sendMessage(`§b${knightName(e)}§7 ${msg}.`));
}

world.afterEvents.playerInteractWithEntity.subscribe((ev) => {
  if (ev.target.typeId !== 'bc:magic_knight') return;
  const p = ev.player;
  const e = ev.target;
  const item = ev.beforeItemStack;
  face(e, p);
  if (hooks.talk && safe(() => e.getDynamicProperty('bc:owner')) === p.id && isCompanion(e)) {
    system.run(() => Promise.resolve(hooks.talk(p, e, item)).catch(() => {}));
    return;
  }
  system.run(() => talk(p, e).catch(() => {}));
});

// hired knights keep up with their captain (and come when called from far away)
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    for (const e of hiredBy(p)) {
      if (isCompanion(e)) continue; // companions.js handles its party
      safe(() => {
        if (e.getDynamicProperty('bc:order') === 'hold') return;
        if (V.dist(p.location, e.location) > 24) e.teleport(V.add(p.location, { x: rand(-2, 2), y: 0.2, z: rand(-2, 2) }));
      });
    }
  }
}, 40);

// knights swing visibly in melee
world.afterEvents.entityHitEntity.subscribe((ev) => {
  if (ev.damagingEntity.typeId === 'bc:magic_knight') anim(ev.damagingEntity, 'animation.bc.magic_knight.attack');
});

export { title, hiredBy, enlist };
