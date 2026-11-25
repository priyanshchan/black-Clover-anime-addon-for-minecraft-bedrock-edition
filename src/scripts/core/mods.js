// Stat modifiers (v1.1.0): regions, omens and relics each register a provider; the mana, spell and loot maths read
// the combined numbers here. Providers return any of:
//   maxMana (added), regen / power / cd / xp / melee (multipliers), luck / fortune (added percentage points),
//   guard / ward (fractions of damage cut), thorns / leech (added).
import { system } from '@minecraft/server';

/** @typedef {{maxMana?: number, regen?: number, power?: number, cd?: number, xp?: number, melee?: number, luck?: number, fortune?: number,
 *   guard?: number, ward?: number, thorns?: number, leech?: number, wild?: boolean}} Mods */
/** @type {((p: any) => Mods | undefined)[]} */
const providers = [];
export function addMods(fn) {
  providers.push(fn);
}

/** @type {Map<string, {t: number, m: Required<Mods>}>} */
const cache = new Map();
/** The combined modifiers on a player this tick. @returns {Required<Mods>} */
export function mods(p) {
  const t = system.currentTick;
  const id = p?.id ?? '';
  const c = cache.get(id);
  if (c && c.t === t) return c.m;
  /** @type {Required<Mods>} */
  const m = { maxMana: 0, regen: 1, power: 1, cd: 1, xp: 1, melee: 1, luck: 0, fortune: 0, guard: 0, ward: 0, thorns: 0, leech: 0, wild: false };
  for (const fn of providers) {
    let r;
    try {
      r = fn(p);
    } catch {
      r = undefined;
    }
    if (!r) continue;
    m.maxMana += r.maxMana ?? 0;
    m.regen *= r.regen ?? 1;
    m.power *= r.power ?? 1;
    m.cd *= r.cd ?? 1;
    m.xp *= r.xp ?? 1;
    m.melee *= r.melee ?? 1;
    m.luck += r.luck ?? 0;
    m.fortune += r.fortune ?? 0;
    m.guard += r.guard ?? 0;
    m.ward += r.ward ?? 0;
    m.thorns += r.thorns ?? 0;
    m.leech += r.leech ?? 0;
    m.wild = m.wild || !!r.wild;
  }
  m.cd = Math.max(0.5, m.cd);
  m.guard = Math.min(0.5, m.guard);
  m.ward = Math.min(0.6, m.ward);
  cache.set(id, { t, m });
  if (cache.size > 64) cache.clear();
  return m;
}
