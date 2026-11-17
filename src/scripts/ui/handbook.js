// Magic Knight's Handbook: status page, spell picker and guide (server-ui forms).
import { ActionFormData, MessageFormData } from '@minecraft/server-ui';
import { DATA } from '../generated/data.js';
import { maxMana, regenPerSecond, robe, spellPower, spellsOf, state, xpToNext } from '../core/data.js';
import { sound } from '../core/fx.js';
import { isCreative, safe } from '../core/util.js';
import { sea, willToNext } from '../sea/state.js';
import { countCoins } from '../sea/bounty.js';
import { rankTitle, stars } from '../core/ranks.js';
import { notoriety, notorietyTitle } from '../sea/navy.js';
import { kingdomPage } from '../living/worldsim.js';

const G = DATA.glyphs;

function statusBody(p) {
  const s = state(p);
  if (!s.attr) {
    return '§7You have not received a grimoire yet.\n\n§fPlace a §dGrimoire Altar§f and interact with it. '
      + `The altar chooses one of ${DATA.order.length} attributes for you - from Wind, Flame and Sand to the rare Star and Time, `
      + 'or - very rarely - a five-leaf grimoire of §0§lAnti-Magic§r§f.';
  }
  const a = DATA.attributes[s.attr];
  const leaves = { 3: 'Three-Leaf', 4: 'Four-Leaf', 5: 'Five-Leaf' }[a.leaves];
  const r = robe(p);
  let body = `${a.glyph} ${a.mc}§l${a.name} Magic§r  §7(${leaves} Grimoire)\n`;
  body += `§e${G.star} Level ${s.level}§7  -  XP ${Math.floor(s.xp)}/${xpToNext(s.level)}\n`;
  if (s.attr === 'anti') body += `§cAnti-Magic gauge: ${Math.floor(s.anti)}%%\n`.replace('%%', '%');
  else body += `§bMana ${Math.floor(s.mana)}/${maxMana(p, s)}§7  (+${regenPerSecond(p, s).toFixed(1)}/s)\n`;
  body += `§7Spell power: §fx${spellPower(p, s).toFixed(2)}\n`;
  body += `§7Robe: §f${r ? DATA.robes[r] : 'none'}\n\n`;
  body += '§8Use your grimoire to cast. Sneak + use to flip to the next spell.';
  return body;
}

export async function openHandbook(p) {
  const s = state(p);
  const form = new ActionFormData().title('§lMagic Knight\'s Handbook').body(statusBody(p));
  const actions = [];
  if (s.attr) {
    form.button('§lChoose spell\n§r§8Pick the active page of your grimoire');
    actions.push(() => spellPicker(p));
  }
  form.button('§lAll attributes & spells\n§r§8Browse every grimoire');
  actions.push(() => attributeList(p));
  form.button('§lAbyss Fruit & Will\n§r§8Your fruit power and fighting spirit');
  actions.push(() => fruitPage(p));
  form.button('§lThe Abyssal Seas\n§r§8Ships, bounties, the Leviathan');
  actions.push(() => seaGuide(p));
  form.button('§lRank, robes & renown\n§r§8Stars, squad robes, your bounty');
  actions.push(() => rankPage(p));
  form.button('§lBosses & world events\n§r§8Giants, gates, raids, the merchant');
  actions.push(() => livingPage(p));
  form.button('§lKnights & the War Table\n§r§8Factions, battles, bets');
  actions.push(() => warPage(p));
  form.button('§lState of the Kingdom\n§r§8Faction power and world news');
  actions.push(() => kingdomPage(p));
  form.button('§lHow to play\n§r§8Altar, mana, robes, the Devil');
  actions.push(() => guide(p));
  sound(p.dimension, 'bc.grimoire.flip', p.location, 0.8, 1);
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return;
  await actions[res.selection]?.();
}

async function spellPicker(p) {
  const s = state(p);
  const spells = spellsOf(s.attr);
  const lvl = isCreative(p) ? 20 : s.level;
  const form = new ActionFormData().title(`${DATA.attributes[s.attr].mc}${DATA.attributes[s.attr].name} Grimoire`).body('§7Select the spell your grimoire will cast.');
  for (const sp of spells) {
    const locked = lvl < sp.level;
    const cost = s.attr === 'anti' ? (sp.id === 'black_form' ? '100% gauge' : 'free') : `${sp.mana} mana`;
    form.button(locked ? `${G.lock} §8${sp.name}\n§8Unlocks at level ${sp.level}` : `§l${sp.name}§r\n§8${cost} - ${sp.cooldown}s`);
  }
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return;
  const sp = spells[res.selection];
  if (lvl < sp.level) {
    safe(() => p.sendMessage(`${G.lock} §7${sp.name} unlocks at level ${sp.level}.`));
    return;
  }
  s.spell = res.selection;
  s.dirty = true;
  safe(() => p.sendMessage(`${DATA.attributes[s.attr].mc}${sp.name}§7 - ${sp.desc}`));
}

async function attributeList(p) {
  const form = new ActionFormData().title('Attributes').body('§7Each grimoire holds four spells. The fourth is unlocked at level 10.');
  for (const k of DATA.order) {
    const a = DATA.attributes[k];
    form.button(`${a.glyph} ${a.mc}§l${a.name}§r\n§8${{ 3: 'Three', 4: 'Four', 5: 'Five' }[a.leaves]}-leaf grimoire`);
  }
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return;
  const k = DATA.order[res.selection];
  const a = DATA.attributes[k];
  const lines = spellsOf(k).map((sp) => `§l${a.mc}${sp.name}§r §8(Lv ${sp.level}${k === 'anti' ? '' : `, ${sp.mana} mana`})\n§7${sp.desc}`).join('\n\n');
  await new MessageFormData().title(`${a.name} Magic`).body(lines).button1('Back').button2('Close').show(p).then((r) => {
    if (r.selection === 0) return attributeList(p);
    return undefined;
  });
}

async function guide(p) {
  const body = [
    '§l§dGrimoire Altar§r\n§7Craft one (or use the one you received on your first day). Interact with it to receive your grimoire. Lost it? The altar returns it.',
    '§l§bMana§r\n§7Spells cost mana, which regenerates over time. Mana Crystals restore it instantly (craft: amethyst + lapis + glowstone).',
    '§l§eLevels§r\n§7Casting and defeating monsters grants magic XP. New spells unlock at levels 3, 6 and 10. Spell power grows every level.',
    '§l§0Anti-Magic§r\n§7Five-leaf grimoires hold demon swords instead of spells. Sword hits fill the gauge; at 100% unleash Black Form. Sneak with a sword to cut down incoming spells.',
    '§l§6Robes§r\n§7Black Bull: faster mana, stronger when near death. Golden Dawn: +40 mana, +10% power. Crimson Lion: cheaper and stronger flame spells.',
    '§l§4The Devil§r\n§7Dark Disciples roam at night. A Devil Summoning Contract (crying obsidian, mana crystals, book) calls the Devil itself. Its heart crafts a Wishing Clover Charm, which lets you seek a new grimoire.',
  ].join('\n\n');
  await new MessageFormData().title('How to play').body(body).button1('Back').button2('Close').show(p).then((r) => {
    if (r.selection === 0) return openHandbook(p);
    return undefined;
  });
}

async function fruitPage(p) {
  const w = sea(p);
  let body = '';
  if (w.fruit) {
    const f = DATA.fruits[w.fruit];
    body += `${f.glyph} ${f.mc}§l${f.name}§r\n§7Passive: §f${f.passive}\n\n`;
    for (const [i, a] of f.abilities.entries()) body += `${i === w.ability ? '§e> ' : '§8- '}§f${a.name} §8(${a.cooldown}s)\n§7${a.desc}\n`;
    body += '\n§9Weakness: §7deep water drains you, and anti-magic seals your power for a while.';
  } else {
    body += '§7You have not eaten an Abyss Fruit. Raider Captains, sunken wrecks, the Leviathan and the Bounty Board shop can give you one.\n§cYou can only ever hold one fruit.';
  }
  body += `\n\n§5${G.will} Will level ${w.willLv}§7 - ${Math.floor(w.willXp)}/${willToNext(w.willLv)} XP, gauge ${Math.floor(w.will)}%%\n`.replace('%%', '%');
  body += `${w.willLv >= 1 ? '§d' : '§8'}Lv 1 Iron Will: melee hits spend Will for extra damage\n`;
  body += `${w.willLv >= 3 ? '§d' : '§8'}Lv 3 Keen Will: a chance to sidestep blows and arrows\n`;
  body += `${w.willLv >= 8 ? '§d' : '§8'}Lv 8 Sovereign Will: Sneak + Jump at full Will to floor weak foes\n`;
  body += '§7Train Will by fighting. Leviathan Scales strengthen it.';
  const form = new ActionFormData().title('Abyss Fruit & Will').body(body);
  const acts = [];
  if (w.fruit) {
    for (const [i, a] of DATA.fruits[w.fruit].abilities.entries()) {
      form.button(`Use §l${a.name}`);
      acts.push(() => {
        w.ability = i;
        w.dirty = true;
      });
    }
  }
  form.button('Back');
  acts.push(() => openHandbook(p));
  const res = await form.show(p);
  if (res.canceled || res.selection === undefined) return;
  await acts[res.selection]?.();
}

async function rankPage(p) {
  const s = state(p);
  let body = `§6${G.star} ${rankTitle(p)}§7 - ${stars(p)} stars\n`;
  const next = DATA.ranks.find((r) => r.stars > stars(p));
  body += next ? `§7Next: §f${next.title} §7at ${next.stars} stars\n` : '§7You have reached the highest rank.\n';
  body += '§8Stars: Devil +5, Leviathan +5, dungeon Guardian +3, Commodore +2, captain +1, every 5 levels +1. Each rank adds +5 max mana.\n\n';
  body += `§c${G.coin} Bounty on your head: §e${notoriety(p)} §7(${notorietyTitle(p)})\n\n`;
  body += '§lSquad robes§r\n';
  for (const [id, name] of Object.entries(DATA.robes)) body += `§6${name}§7: ${DATA.robePerks[id] ?? ''}\n`;
  body += '\n§lTechniques§r\n§7Lv 12 Mana Skin: a coat of mana soaks a quarter of every hit (costs mana).\n§7Lv 15 Mana Zone: hold your grimoire, Sneak + Jump.';
  if (s.level < 12) body += '\n§8(locked)';
  await new MessageFormData().title('Rank, robes & renown').body(body).button1('Back').button2('Close').show(p).then((r) => {
    if (r.selection === 0) return openHandbook(p);
    return undefined;
  });
}

async function seaGuide(p) {
  const body = [
    `§l§6Sailing§r\n§7Craft a Sailing Ship (wool, planks, iron) and use it on water. The first aboard is the captain: look where you want to go and hold forward. Use Cannonballs aboard to fire.`,
    `§l§cRaiders & bounties§r\n§7Pirate outposts and sunken wrecks appear out at sea. Raider Captains each wield an Abyss Fruit. Take a bounty at a Bounty Board and follow the arrow on your HUD. Purse: §e${countCoins(p)} doubloons`,
    '§l§3The Leviathan§r\n§7A Leviathan Lure (heart of the sea, prismarine crystals, mana crystals) calls the Abyssal Leviathan from deep water. It drops a fruit, scales and treasure.',
    '§l§0Anti-Magic vs fruits§r\n§7Demon-sword hits and anti-magic slashes seal a fruit user\'s powers for a few seconds.',
  ].join('\n\n');
  await new MessageFormData().title('The Abyssal Seas').body(body).button1('Back').button2('Close').show(p).then((r) => {
    if (r.selection === 0) return openHandbook(p);
    return undefined;
  });
}

async function livingPage(p) {
  const body = [
    '§l§4The Archdevil§r\n§7Craft an §4Archdevil Sigil§7 (crying obsidian, mana crystals, a devil heart). Dark lances, hellfire, a crushing nova, and imps. Enrages at half health.',
    '§l§6The Stone Colossus§r\n§7A §6Colossus Core§7 (mossy cobblestone, ancient pages, a diamond block) wakes a walking mountain that slams, hurls boulders and splits the earth.',
    '§l§3The Phantom Galleon§r\n§7Ring a §3Phantom Galleon Bell§7 (phantom membranes, doubloons, a bell). A ghost ship sails the sky, fires broadsides and drops its drowned crew.',
    '§l§9The Storm Kraken§r\n§7Throw a §9Storm Kraken Lure§7 (Leviathan scales, lightning rods, a heart of the sea) into deep water. Lightning, whirlpools and tentacle slams.',
    '§l§eWorld events§r\n§7Every few minutes something happens near a player: mana meteor showers (catch the crystals), Devil Gates (break them!), pirate landings, faction skirmishes, Magic Knight patrols, the Travelling Merchant, sky treasure, a Crimson Night, or a giant boss rising. Toggle events at a War Table.',
  ].join('\n\n');
  await new MessageFormData().title('Bosses & world events').body(body).button1('Back').button2('Close').show(p).then((r) => {
    if (r.selection === 0) return openHandbook(p);
    return undefined;
  });
}

async function warPage(p) {
  const body = [
    '§l§aMagic Knights§r\n§7Named knights of every attribute roam plains and forests. They hunt monsters, pirates and devils with real spells, and only fight you if you strike first. Each has a fighting style, skill and courage, and levels up with every kill (more spells at levels 3 and 6).',
    '§l§bYour own knights§r\n§7Talk to a knight to see its profile. Recruit wild knights with a §aKnight Contract§7 or doubloons (up to 4). Talk to your knights to order them to follow, hold a position, guard you or hunt freely.',
    '§l§6The War Table§r\n§7Craft one (map, iron sword, feather, planks, sticks) and use it: pick two or three armies - ' + Object.values(DATA.factions).map((f) => `${f.mc}${f.name}§7`).join(', ') + ' - their tactics and size, or stage a knight duel, and bet doubloons on the winner. Watch with the cinematic camera.',
    '§l§eSkirmish Horn§r\n§7Blow it (gold and a bone) and two random armies clash in front of you.',
    '§l§7Factions in the wild§r\n§7Knights fight devils and pirates; the Tidewatch hunt pirates and devils; pirates and devils fight knights and the navy.',
  ].join('\n\n');
  await new MessageFormData().title('Knights & the War Table').body(body).button1('Back').button2('Close').show(p).then((r) => {
    if (r.selection === 0) return openHandbook(p);
    return undefined;
  });
}

export async function confirmCharm(p) {
  const s = state(p);
  if (!s.attr) {
    safe(() => p.sendMessage('§7You have no grimoire to give up.'));
    return false;
  }
  const res = await new MessageFormData()
    .title('Wishing Clover Charm')
    .body(`§fGive up your ${DATA.attributes[s.attr].mc}${DATA.attributes[s.attr].name}§f grimoire and seek a new one at a Grimoire Altar?\n\n§cYour level and spells will be reset.`)
    .button1('§cYes, make a wish')
    .button2('Keep my grimoire')
    .show(p);
  return res.selection === 0;
}
