// The Travelling Magic Merchant: appears during world events (or from a spawn egg) and trades for doubloons.
import { ItemStack, system, world } from '@minecraft/server';
import { ActionFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { particle, sound } from '../core/fx.js';
import { pick, safe } from '../core/util.js';
import { countCoins, giveCoins } from '../sea/bounty.js';

const GREETINGS = [
  'Wares from every corner of the kingdom - and a few from beyond the sea!',
  'Grimoire pages, Abyss Fruits, rare sigils... if you have the coin.',
  'Careful with that sigil, friend. What it calls does not leave quietly.',
  'A contract for a knight? Wise. The roads are not safe these days.',
];

function takeCoins(p, amount) {
  if (countCoins(p) < amount) return false;
  const inv = p.getComponent('minecraft:inventory')?.container;
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

async function openShop(p, merchant) {
  const coins = countCoins(p);
  const form = new ActionFormData().title('§lTravelling Magic Merchant').body(`§7"${pick(GREETINGS)}"\n\n§eYour purse: ${DATA.glyphs.coin} ${coins} doubloons`);
  for (const o of DATA.merchant) form.button(`${coins >= o.price ? '§0' : '§8'}§l${o.label}\n§r${coins >= o.price ? '§6' : '§c'}${o.price} doubloons`);
  form.button('§8Leave');
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined || res.selection >= DATA.merchant.length) return;
  const o = DATA.merchant[res.selection];
  if (!takeCoins(p, o.price)) {
    safe(() => p.sendMessage(`§7"Come back with §6${o.price}§7 doubloons, friend."`));
    return;
  }
  const id = o.item === 'random_fruit' ? `bc:fruit_${pick(DATA.fruitOrder)}` : o.item;
  give(p, new ItemStack(id, o.count));
  sound(p.dimension, 'bc.coins', p.location, 1, 1);
  if (merchant) particle(p.dimension, 'bc:burst_spark', merchant.location, { scale: 0.6 });
  safe(() => p.sendMessage(`§a"A fine choice!" §7(${o.label})`));
}

world.afterEvents.playerInteractWithEntity.subscribe((ev) => {
  if (ev.target.typeId !== 'bc:magic_merchant') return;
  const p = ev.player;
  const m = ev.target;
  system.run(() => openShop(p, m).catch(() => {}));
});

/** Spawn a merchant who leaves after `minutes`. */
export function spawnMerchant(dim, loc, minutes = 6) {
  const e = safe(() => dim.spawnEntity('bc:magic_merchant', loc));
  if (!e) return undefined;
  safe(() => {
    e.setDynamicProperty('bc:leave_at', system.currentTick + minutes * 1200);
    e.nameTag = '§bTravelling Magic Merchant';
  });
  particle(dim, 'bc:clover_leaves', loc, { scale: 1.2 });
  return e;
}

system.runInterval(() => {
  const t = system.currentTick;
  for (const p of world.getAllPlayers()) {
    safe(() => {
      for (const e of p.dimension.getEntities({ location: p.location, maxDistance: 96, type: 'bc:magic_merchant' })) {
        const at = e.getDynamicProperty('bc:leave_at');
        if (typeof at === 'number' && at < t) {
          particle(e.dimension, 'bc:smoke_burst', e.location, { scale: 1 });
          e.triggerEvent('bc:leave');
        }
      }
    });
  }
}, 200);

export { giveCoins };
