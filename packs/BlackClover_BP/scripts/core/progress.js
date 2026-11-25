// Magic XP, levels and unlock announcements.
import { DATA } from '../generated/data.js';
import { MAX_LEVEL, eclipseMul, maxMana, spellsOf, state, xpToNext } from './data.js';
import { emit } from './bus.js';
import { particle, sound, title } from './fx.js';
import { addStars } from './ranks.js';
import { safe } from './util.js';
import { mods } from './mods.js';

export function addXp(player, amount) {
  const s = state(player);
  if (s.attr) emit('xp', player, amount);
  if (!s.attr || s.level >= MAX_LEVEL) return;
  s.xp += (eclipseMul() > 1 ? amount * 1.5 : amount) * mods(player).xp;
  s.dirty = true;
  while (s.level < MAX_LEVEL && s.xp >= xpToNext(s.level)) {
    s.xp -= xpToNext(s.level);
    s.level++;
    levelUp(player, s.level);
    if (s.level % 5 === 0) addStars(player, 1, `reached level ${s.level}`);
  }
}

function levelUp(player, level) {
  const s = state(player);
  s.mana = maxMana(player, s);
  const a = DATA.attributes[s.attr];
  const unlockedNow = spellsOf(s.attr).filter((sp) => sp.level === level);
  const sub = unlockedNow.length ? `§fNew spell: ${a.mc}${unlockedNow.map((x) => x.name).join(', ')}` : `§7Max mana §b${maxMana(player, s)}`;
  title(player, `§e${DATA.glyphs.star} Level ${level}`, sub, 50);
  particle(player.dimension, 'bc:level_up', player.location);
  particle(player.dimension, 'bc:clover_leaves', { x: player.location.x, y: player.location.y + 1.2, z: player.location.z });
  sound(player.dimension, 'bc.levelup', player.location, 1, 1);
  if (unlockedNow.length) {
    safe(() => player.sendMessage(`§e${DATA.glyphs.star} §fYour grimoire's pages glow... ${a.mc}${unlockedNow[0].name}§f unlocked! §7(${unlockedNow[0].desc})`));
  }
}
