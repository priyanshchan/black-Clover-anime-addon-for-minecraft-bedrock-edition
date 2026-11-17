// Magic Brooms: fly on your own mana.
// Use a broom to mount it. Look where you want to go and hold forward to fly (look up to climb, down to dive),
// hold back to brake, let go to hover. Sneak to step off. Flying costs mana every second; when you run dry the
// broom can only glide gently down until your mana recovers (it does not regenerate while you fly).
// Without a grimoire the broom only glides, and Anti-Magic users can't fly.
// Step off and the broom flies back into your inventory a moment later.
import { ItemStack, Player, system, world } from '@minecraft/server';
import { DATA } from '../generated/data.js';
import { COLORS, particle, sound } from '../core/fx.js';
import { heldKind } from '../core/hud.js';
import { addMana, maxMana, state } from '../core/data.js';
import { effect } from '../core/combat.js';
import { V, isCreative, now, safe, yawOf } from '../core/util.js';

const TIERS = ['broom', 'swift_broom'];
/** @type {Map<string, {tier: number, speed: number, yaw: number, empty: number, rider: string, owner: string, warned: number, dry?: boolean}>} */
const brooms = new Map();

function tierOf(e) {
  const v = safe(() => e.getProperty('bc:tier'));
  return typeof v === 'number' ? v : 0;
}

function track(e) {
  if (e.typeId !== 'bc:broom' || brooms.has(e.id)) return;
  const owner = safe(() => e.getDynamicProperty('bc:owner'));
  brooms.set(e.id, { tier: tierOf(e), speed: 0, yaw: safe(() => e.getRotation().y) ?? 0, empty: 0, rider: '', owner: typeof owner === 'string' ? owner : '', warned: 0 });
}
world.afterEvents.entitySpawn.subscribe((ev) => safe(() => track(ev.entity)));
world.afterEvents.entityLoad.subscribe((ev) => safe(() => track(ev.entity)));

function give(p, item) {
  const left = p.getComponent('minecraft:inventory')?.container?.addItem(item);
  if (left) p.dimension.spawnItem(left, p.location);
}

/** Mount a broom from the item in hand. */
export function useBroom(p, id) {
  const tier = TIERS.indexOf(id.slice(3));
  if (tier < 0) return false;
  if (safe(() => p.getComponent('minecraft:riding')?.entityRidingOn)) {
    safe(() => p.onScreenDisplay.setActionBar('§7You are already riding something.'));
    return true;
  }
  const s = state(p);
  if (s.attr === 'anti') {
    safe(() => p.onScreenDisplay.setActionBar('§8Your anti-magic smothers the broom. It will not fly for you.'));
    sound(p.dimension, 'random.fizz', p.location, 0.8, 0.8);
    return true;
  }
  const at = V.add(p.location, { x: 0, y: 0.3, z: 0 });
  const e = safe(() => p.dimension.spawnEntity('bc:broom', at));
  if (!e) return true;
  const yaw = yawOf(p.getViewDirection());
  safe(() => {
    e.setProperty('bc:tier', tier);
    e.setDynamicProperty('bc:owner', p.id);
    e.setRotation({ x: 0, y: yaw });
  });
  brooms.set(e.id, { tier, speed: 0, yaw, empty: 0, rider: p.id, owner: p.id, warned: 0 });
  safe(() => e.getComponent('minecraft:rideable')?.addRider(p));
  if (!isCreative(p)) {
    const inv = p.getComponent('minecraft:inventory')?.container;
    const it = inv?.getItem(p.selectedSlotIndex);
    if (it?.typeId === id) {
      if (it.amount > 1) {
        it.amount -= 1;
        inv.setItem(p.selectedSlotIndex, it);
      } else inv.setItem(p.selectedSlotIndex, undefined);
    }
  }
  const color = COLORS[s.attr] ?? COLORS.wind;
  particle(p.dimension, 'bc:burst_spark', at, { color, scale: 0.7 });
  sound(p.dimension, 'bc.wind.gust', at, 0.8, 1.2);
  if (!s.attr) safe(() => p.sendMessage('§7Without a grimoire the broom can only §fglide§7. Find a §dGrimoire Altar§7 to truly fly.'));
  else safe(() => p.onScreenDisplay.setActionBar('§6Look to steer, hold forward to fly, back to brake. §7Sneak to step off.'));
  return true;
}

/** Put the broom back in its owner's pack (or drop it) and remove it. */
function stow(e, st) {
  const item = new ItemStack(`bc:${TIERS[st.tier] ?? 'broom'}`, 1);
  const owner = st.owner ? world.getEntity(st.owner) : undefined;
  if (owner instanceof Player && owner.dimension.id === e.dimension.id && V.dist(owner.location, e.location) < 24) {
    if (!isCreative(owner)) give(owner, item);
  } else safe(() => e.dimension.spawnItem(item, e.location));
  particle(e.dimension, 'bc:clover_leaves', e.location, { scale: 0.5 });
  safe(() => e.remove());
  brooms.delete(e.id);
}

function fly(e, st) {
  const riders = e.getComponent('minecraft:rideable')?.getRiders() ?? [];
  const p = riders.find((r) => r instanceof Player);
  if (!p) {
    // the rider stepped off mid-air: a soft landing, then the broom flies home
    if (st.rider) {
      const was = world.getEntity(st.rider);
      if (was) effect(was, 'slow_falling', 4, 0, false);
      st.rider = '';
    }
    const v = e.getVelocity();
    safe(() => e.applyImpulse({ x: -v.x * 0.3, y: -v.y * 0.3, z: -v.z * 0.3 }));
    if (++st.empty > 40) stow(e, st);
    return;
  }
  st.empty = 0;
  st.rider = p.id;
  if (!st.owner) st.owner = p.id;
  const s = state(p);
  const cfg = DATA.brooms[TIERS[st.tier]] ?? DATA.brooms.broom;
  const creative = isCreative(p);
  if (s.attr === 'anti') {
    safe(() => e.getComponent('minecraft:rideable')?.ejectRider(p));
    safe(() => p.onScreenDisplay.setActionBar('§8Your anti-magic smothers the broom.'));
    return;
  }
  const look = p.getViewDirection();
  const mv = safe(() => p.inputInfo.getMovementVector()) ?? { x: 0, y: 0 };
  const thrust = mv.y;
  const glideOnly = !s.attr && !creative;
  // running dry: glide until 15% of your mana has come back
  if (!creative && !glideOnly) {
    if (s.mana < 1) st.dry = true;
    else if (st.dry && s.mana >= maxMana(p, s) * 0.15) {
      st.dry = false;
      safe(() => p.onScreenDisplay.setActionBar('§bMana restored - the broom answers again.'));
    }
  }
  const dry = !!st.dry && !creative && !glideOnly;
  // steering: the broom turns smoothly towards where you look
  const want = yawOf(look);
  const diff = ((want - st.yaw + 540) % 360) - 180;
  st.yaw += Math.max(-9, Math.min(9, diff));
  const top = glideOnly ? cfg.speed * 0.45 : cfg.speed;
  const target = thrust > 0.1 ? top * thrust : thrust < -0.1 ? 0 : st.speed * 0.6;
  st.speed += (target - st.speed) * (thrust > 0.1 ? 0.06 : 0.12);
  let dir = V.norm(look);
  if (glideOnly || dry) dir = V.norm({ x: look.x, y: Math.min(look.y, -0.25), z: look.z });
  const vel = V.mul(dir, st.speed);
  if (st.speed < 0.04) vel.y = glideOnly || dry ? -0.12 : 0; // hover
  else if (glideOnly || dry) vel.y = Math.min(vel.y, -0.08);
  const v = e.getVelocity();
  safe(() => e.applyImpulse({ x: (vel.x - v.x) * 0.3, y: (vel.y - v.y) * 0.3, z: (vel.z - v.z) * 0.3 }));
  safe(() => e.setRotation({ x: 0, y: st.yaw }));
  // mana upkeep (every tick, in small sips; hovering costs less) - and no regeneration while you fly
  if (!creative && !glideOnly && !dry) {
    const perSec = cfg.mana * (st.speed > 0.06 ? 1 : 0.4);
    addMana(p, -perSec / 20);
    s.noRegen = system.currentTick + 5;
  }
  const t = system.currentTick;
  if (dry && t > st.warned) {
    st.warned = t + 100;
    safe(() => p.onScreenDisplay.setActionBar('§cOut of mana - the broom is gliding down!'));
  }
  // a trail of the rider's mana colour
  if (st.speed > 0.15 && t % 3 === 0) {
    const back = V.add(e.location, V.add(V.mul(dir, -1.1), { x: 0, y: 0.3, z: 0 }));
    particle(e.dimension, 'bc:beam_dot', back, { color: COLORS[s.attr] ?? COLORS.wind, size: 0.35, life: 0.6 });
  }
  if (st.speed > top * 0.8 && t % 30 === 0) sound(e.dimension, 'bc.wind.gust', e.location, 0.4, 1.4);
  // a little HUD while nothing else is shown
  if (t % 8 === 0 && !heldKind(p) && now() - s.lastCast > 60) {
    const mx = maxMana(p, s);
    const speed = Math.round(V.len(e.getVelocity()) * 20);
    const fuel = glideOnly ? '§7gliding' : creative ? '§7creative' : `§b${Math.floor(s.mana)}§7/${mx} mana`;
    safe(() => p.onScreenDisplay.setActionBar(`${cfg.name} §7| §f${speed} m/s §7| ${fuel} §7| alt §f${Math.floor(e.location.y)}`));
  }
}

system.runInterval(() => {
  for (const [id, st] of brooms) {
    const e = world.getEntity(id);
    if (!e) {
      brooms.delete(id);
      continue;
    }
    safe(() => fly(e, st), 'broom');
  }
}, 1);
