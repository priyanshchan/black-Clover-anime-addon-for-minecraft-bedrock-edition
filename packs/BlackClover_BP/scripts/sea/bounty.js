// Bounty Board: daily captain bounties, a doubloon shop, tracking and rewards.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { ActionFormData, MessageFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { particle, sound, title } from '../core/fx.js';
import { V, pick, safe, yawOf } from '../core/util.js';
import { spawnCaptain } from './captains.js';
import { sea } from './state.js';
import { build, column, farFromOthers } from './structures.js';
import { addWillXp } from './will.js';

const G = DATA.glyphs;

/** Deterministic little PRNG so a player's board offers stay the same for a whole day. */
function rng(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

function hash(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) h = Math.imul(h ^ str.charCodeAt(i), 16777619);
  return h >>> 0;
}

function offers(p) {
  const day = world.getDay();
  const r = rng(hash(`${p.id}:${day}`));
  const out = [];
  for (let i = 0; i < 3; i++) {
    const fruit = DATA.fruitOrder[Math.floor(r() * DATA.fruitOrder.length)];
    const name = `Captain ${DATA.captainFirst[Math.floor(r() * DATA.captainFirst.length)]}${DATA.captainLast[Math.floor(r() * DATA.captainLast.length)]}`;
    const tier = i + 1;
    out.push({ name, fruit, reward: 60 + tier * 50 + Math.floor(r() * 40), dist: 150 + tier * 60 + Math.floor(r() * 60), angle: r() * 360 });
  }
  return out;
}

export function countCoins(p) {
  const inv = p.getComponent('minecraft:inventory')?.container;
  let n = 0;
  if (!inv) return 0;
  for (let i = 0; i < inv.size; i++) {
    const it = inv.getItem(i);
    if (it?.typeId === 'bc:doubloon') n += it.amount;
  }
  return n;
}

export function takeCoins(p, amount) {
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

function give(p, item) {
  const left = p.getComponent('minecraft:inventory')?.container?.addItem(item);
  if (left) p.dimension.spawnItem(left, p.location);
}

export function giveCoins(p, n) {
  while (n > 0) {
    const k = Math.min(64, n);
    give(p, new ItemStack('bc:doubloon', k));
    n -= k;
  }
}

export function bountyHud(p) {
  const b = sea(p).bounty;
  if (!b) return undefined;
  const dx = b.x - p.location.x;
  const dz = b.z - p.location.z;
  const dist = Math.round(Math.sqrt(dx * dx + dz * dz));
  const rel = ((yawOf({ x: dx, y: 0, z: dz }) - yawOf(p.getViewDirection()) + 540) % 360) - 180;
  const arrow = G.arrows[((Math.round(rel / 45) % 8) + 8) % 8];
  return `${arrow} §cBounty: §f${b.name} ${DATA.fruits[b.fruit].glyph} §7${dist}m  §e${G.coin}${b.reward}`;
}

async function openBoard(p, boardLoc) {
  const s = sea(p);
  const form = new ActionFormData().title('§lBounty Board');
  const acts = [];
  let body = `§7Purse: §e${G.coin} ${countCoins(p)} doubloons\n\n`;
  if (s.bounty) {
    const b = s.bounty;
    body += `§fActive bounty: §c${b.name} §7(${DATA.fruits[b.fruit].mc}${DATA.fruits[b.fruit].name}§7)\n§7Reward: §e${b.reward} doubloons\n§7Follow the arrow on your HUD. Defeat the captain to claim it.`;
    form.button('§cAbandon bounty');
    acts.push(async () => {
      const r = await new MessageFormData().title('Abandon bounty?').body('The captain will keep sailing free.').button1('Abandon').button2('Keep hunting').show(p);
      if (r.selection === 0) {
        s.bounty = null;
        s.dirty = true;
      }
    });
  } else {
    body += '§fWanted posters (refreshed every day):';
    for (const o of offers(p)) {
      const f = DATA.fruits[o.fruit];
      form.button(`§l${o.name}§r ${f.glyph}\n§8${f.name} user - §6${o.reward} doubloons`);
      acts.push(() => accept(p, o, boardLoc));
    }
  }
  form.button('§6Trade doubloons');
  acts.push(() => shop(p));
  form.body(body);
  sound(p.dimension, 'bc.grimoire.flip', p.location, 0.7, 0.8);
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return;
  await acts[res.selection]?.();
}

function accept(p, o, from) {
  const s = sea(p);
  const r = (o.angle * Math.PI) / 180;
  s.bounty = { name: o.name, fruit: o.fruit, reward: o.reward, x: Math.round(from.x - Math.sin(r) * o.dist), z: Math.round(from.z + Math.cos(r) * o.dist), built: false };
  s.dirty = true;
  title(p, '§cWANTED', `§f${o.name} §7- ${o.reward} doubloons`, 50);
  sound(p.dimension, 'bc.ship.bell', p.location, 0.8, 1.2);
}

async function shop(p) {
  const form = new ActionFormData().title('§lTrade').body(`§7Purse: §e${G.coin} ${countCoins(p)} doubloons`);
  for (const s of DATA.shop) form.button(`§l${s.label}§r\n§6${s.price} doubloons`);
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return;
  const s = DATA.shop[res.selection];
  if (!takeCoins(p, s.price)) {
    safe(() => p.sendMessage(`§cYou need ${s.price} doubloons for that.`));
    return;
  }
  const id = s.item === 'random_fruit' ? `bc:fruit_${pick(DATA.fruitOrder)}` : s.item;
  give(p, new ItemStack(id, s.count));
  sound(p.dimension, 'bc.coins', p.location, 1, 1);
  safe(() => p.sendMessage(`§aBought: §f${s.label}`));
}

// the board block
system.beforeEvents.startup.subscribe((ev) => {
  ev.blockComponentRegistry.registerCustomComponent('bc:bounty_logic', {
    onPlayerInteract(e) {
      const p = e.player;
      if (!p) return;
      const loc = e.block.location;
      system.run(() => openBoard(p, loc).catch(() => {}));
    },
  });
});

// raise the bounty target when the hunter gets close
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    safe(() => {
      const s = sea(p);
      const b = s.bounty;
      if (!b || b.built || p.dimension.id !== 'minecraft:overworld') return;
      if (V.dist({ x: b.x, y: 0, z: b.z }, { x: p.location.x, y: 0, z: p.location.z }) > 64) return;
      const col = column(p.dimension, b.x, b.z);
      if (col && col.surface - col.floor >= 4 && col.surface - col.floor <= 30) {
        build(p.dimension, 'outpost', { x: b.x, y: col.surface, z: b.z }, { bountyFor: p.id, captainName: b.name, captainFruit: b.fruit });
      } else {
        // on land: the crew makes camp on the highest ground
        let y = 120;
        for (; y > 40; y--) {
          const blk = p.dimension.getBlock({ x: b.x, y, z: b.z });
          if (!blk) return;
          if (!blk.isAir && !blk.isLiquid) break;
        }
        const at = { x: b.x + 0.5, y: y + 1, z: b.z + 0.5 };
        spawnCaptain(p.dimension, at, { name: b.name, fruit: b.fruit, bountyFor: p.id });
        for (let i = 0; i < 3; i++) safe(() => p.dimension.spawnEntity('bc:sea_raider', V.add(at, { x: i - 1, y: 0, z: 2 })));
      }
      b.built = true;
      s.dirty = true;
      safe(() => p.onScreenDisplay.setActionBar(`§c${b.name}§7's crew is close...`));
    }, 'bountyBuild');
  }
}, 40);

// pay out
world.afterEvents.entityDie.subscribe((ev) => safe(() => {
  const e = ev.deadEntity;
  if (e.typeId !== 'bc:raider_captain') return;
  for (const tag of e.getTags()) {
    if (!tag.startsWith('bc_bounty:')) continue;
    const owner = world.getEntity(tag.slice('bc_bounty:'.length));
    if (!(owner instanceof Player)) continue;
    const s = sea(owner);
    if (!s.bounty) continue;
    const reward = s.bounty.reward;
    giveCoins(owner, reward);
    addWillXp(owner, 15);
    title(owner, '§6§lBOUNTY CLAIMED', `§e+${reward} doubloons`, 60);
    sound(owner.dimension, 'bc.coins', owner.location, 1, 1);
    sound(owner.dimension, 'bc.levelup', owner.location, 0.7, 1.2);
    particle(owner.dimension, 'bc:level_up', owner.location);
    s.bounty = null;
    s.dirty = true;
  }
}, 'bountyPay'));

export { farFromOthers };
