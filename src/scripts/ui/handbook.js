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
import { missionSummary } from '../living/missions.js';

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
  form.button('§lCompanions\n§r§8Your party, bonds and orders');
  actions.push(() => companionPage(p));
  form.button('§lMissions\n§r§8Today\'s missions and the Mission Board');
  actions.push(() => missionPage(p));
  form.button('§lBrooms & amulets\n§r§8Flight, off-hand charms, camps');
  actions.push(() => gearPage(p));
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
  const form = new ActionFormData().title('Attributes').body('§7Each grimoire holds four spells (levels 1, 3, 6 and 10), and every grimoire but Anti-Magic awakens a fifth at level 15.');
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
    '§l§eLevels§r\n§7Casting and defeating monsters grants magic XP. New spells unlock at levels 3, 6 and 10, and your grimoire §dawakens§7 a fifth spell at level 15. Spell power grows every level.',
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

async function companionPage(p) {
  const C = DATA.companion;
  const body = [
    '§l§6New in v0.5.0§r\n§7Personalities, specialisations, party tactics, combos, revives, mood, camps, personal trials, a reserve with expeditions, sparring, rival squads - and they fly brooms with you.',
    '§l§bPersonalities§r\n' + Object.values(C.personalities).map((x) => `§f${x.name}§7: ${x.desc}`).join('\n'),
    `§l§6Specialisations (level ${C.specLevel})§r\n` + Object.values(C.specs).map((x) => `§6${x.name}§7: ${x.desc} §8Mastery: ${x.mastery}`).join('\n'),
    '§l§bParty tactics (whistle)§r\n' + Object.values(C.tactics).map((x) => `§f${x.name}§7: ${x.desc}`).join('\n'),
    '§l§bFighting as a squad§r\n§7Foes caught in a prison or a time stop take +25% from the squad (Combo!). A Ranger\'s mark adds +20%. Companions step out of warning circles and spell fields, keep out of your line of fire, and a Vanguard stands between you and danger.',
    '§l§aRevives§r\n§7A fallen companion leaves a glowing clover for 60 seconds. Sneak beside it, or let a squadmate kneel there (a Warden is twice as fast), and they get up at half health. A §aClover Leaf of Return§7 revives everyone at once.',
    '§l§dMood§r\n§7Morale rises with victories, gifts, talks and a cheerful friend; weariness builds in long fights. Inspired: +10% power. Shaken: less nerve. Exhausted: slower casting. Make camp with the whistle, or hand them §6Field Rations§7.',
    '§l§dCamp & night watch§r\n§7"Make camp": they sit around a fire, recover fast and chat. At night one of them keeps watch and raises the alarm if something sneaks up.',
    '§l§dTrials§r\n§7At bond Friend a companion asks for help with a personal trial - finishing it awakens their fifth spell early and earns a title. At Sworn Ally a second trial grants their specialisation\'s mastery.',
    '§l§2Squad Banner§r\n§7Keep up to ' + C.reserveMax + ' more knights in reserve. Swap them into the party, and send reserve knights on expeditions (real-time, from 8 to 60 minutes) for loot and XP. Reserve knights train while they wait.',
    '§l§6Training & sparring§r\n§7Place a §6Training Dummy§7 (it shows your DPS) and switch training on: companions practise on it between fights. Pick two companions for a sparring match - non-lethal, and both learn.',
    '§l§bYour party§r\n§7Up to ' + DATA.companion.partyMax + ' Magic Knights travel with you. Recruit them with a §aKnight Contract§7, by talking to a wild knight (contract or doubloons), or by rescuing a wounded knight. Your party is saved with you: companions level up to 20, keep their robe and bond, and come back 60 seconds after they fall.',
    '§l§bThe Companion Whistle§r\n§7Hold it to see your party\'s health on screen. Use it to open your party: summon or dismiss, rename, give orders, change formation (wedge, line, circle) and stance (aggressive, defensive, passive), and switch loot gathering. §fSneak + use§7 while looking at a foe: everyone attacks it. Looking at nothing: regroup.',
    '§l§bHow they think§r\n§7Companions attack what you attack, rush whoever hurts you, heal you first when you are low, dodge spells, keep out of your line of fire, walk in formation, gather loot after a fight and sit down when you rest.',
    '§l§dBond§r\n' + DATA.companion.bond.map((b) => `§d${b.name}§7 (${b.at}): ${b.perk}`).join('\n') + '\n§7Bond grows with time together, victories, level-ups and gifts (hold a Mana Cookie, mana crystal or cooked food and talk to them).',
    '§l§6Robes§r\n§7Hand a companion a squad robe to dress them in it and give them its perk.',
  ].join('\n\n');
  await new MessageFormData().title('Companions').body(body).button1('Back').button2('Close').show(p).then((r) => {
    if (r.selection === 0) return openHandbook(p);
    return undefined;
  });
}

async function livingPage(p) {
  const body = [
    '§l§4The Archdevil§r\n§7Craft an §4Archdevil Sigil§7 (crying obsidian, mana crystals, a devil heart). Dark lances, hellfire, a crushing nova, and imps. Enrages at half health.',
    '§l§4The Fallen Captain§r\n§7Use a §4Seal of the Fallen Captain§7 (crying obsidian, devil hearts, knight contracts, a diamond) or meet it on a dark night. It duels with a blade and three grimoires, blinks behind you, parries blows and dodges spells.',
    '§l§6The Stone Colossus§r\n§7A §6Colossus Core§7 (mossy cobblestone, ancient pages, a diamond block) wakes a walking mountain that slams, hurls boulders and splits the earth.',
    '§l§3The Phantom Galleon§r\n§7Ring a §3Phantom Galleon Bell§7 (phantom membranes, doubloons, a bell). A ghost ship sails the sky, fires broadsides and drops its drowned crew.',
    '§l§bThe Witch Sisters§r\n§7Raise a §bTwin Moon Charm§7 (packed ice, magma blocks, mana crystals, an amethyst block) or meet them on a dark night. The Frost Witch and the Ember Witch blink away from melee and weave §fTwin Spells§7 - an ice prison, then falling fire. Kill one and the other goes berserk: §bAbsolute Winter§7 or §6Inferno Requiem§7.',
    '§l§fThe Bone Dragon§r\n§7Plant a §fBone Totem§7 (bone blocks, a wither skeleton skull, a mana crystal) or look up on a dark night. It circles overhead, breathes withering bone-fire, dives, sweeps its tail, calls skeletons, and ends with §fDeath\'s Wingbeat§7.',
    '§l§5The Soul Puppeteer§r\n§7Weave a §5Cursed Spool§7 (string, devil hearts, phantom membranes, an ender pearl) or hear its music box on a dark night. It lashes with strings, sends marionettes, and §ftakes control of your companions§7 - strike them a few times or have a Warden Cleanse them to cut the strings. Desperation: §5Grand Finale§7.',
    '§l§9The Storm Kraken§r\n§7Throw a §9Storm Kraken Lure§7 (Leviathan scales, lightning rods, a heart of the sea) into deep water. Lightning, whirlpools and tentacle slams.',
    '§l§eWorld events§r\n§7Every few minutes something happens near a player: mana meteor showers (catch the crystals), Devil Gates (break them!), pirate landings, faction skirmishes, Rogue Mage ambushes, rival squad challenges, Magic Knight patrols, the Travelling Merchant, sky treasure, a Crimson Night, or a giant boss rising. Toggle events at a War Table.',
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
    '§l§7Factions in the wild§r\n§7Knights fight devils and pirates; the Tidewatch hunt pirates and devils; pirates and devils fight knights and the navy. §5Rogue Mages§7 - outlaws with real grimoires and levels 2-8 - prowl at night and attack players and knights alike.',
  ].join('\n\n');
  await new MessageFormData().title('Knights & the War Table').body(body).button1('Back').button2('Close').show(p).then((r) => {
    if (r.selection === 0) return openHandbook(p);
    return undefined;
  });
}

async function missionPage(p) {
  const r = DATA.missionRewards;
  const body = [
    '§l§6Today\'s missions§r\n' + missionSummary(p),
    '§l§6How missions work§r\n§7Each in-game day brings three missions: an easy one, a harder one and a wild card. Progress counts anywhere - kills, bosses, Devil Gates, spells and fruit powers, magic XP, your companions\' victories. Delivery missions take the items from your pack at the board.',
    `§l§6The Mission Board§r\n§7Craft one (oak planks, paper, green dye, sticks) or find one in a §aMagic Knight camp§7. Use it to claim rewards and swap a mission (free once a day). Rewards: §e${r[1].stars} star, ${r[1].coins} doubloons§7 / §e${r[2].stars} stars, ${r[2].coins}§7 / §e${r[3].stars} stars, ${r[3].coins}§7 plus magic XP. Finish all three for a bonus.`,
  ].join('\n\n');
  await new MessageFormData().title('Missions').body(body).button1('Back').button2('Close').show(p).then((res) => {
    if (res.selection === 0) return openHandbook(p);
    return undefined;
  });
}

async function gearPage(p) {
  const brooms = Object.values(DATA.brooms).map((b) => `${b.name}§7: top speed ${Math.round(b.speed * 20)} m/s, ${b.mana} mana/s`).join('\n');
  const amulets = Object.values(DATA.amulets).map((a) => `${a.name}§7: ${a.perk}`).join('\n');
  const body = [
    '§l§6Magic Brooms§r\n' + brooms + '\n§7Use a broom to mount it. Look where you want to go and hold forward (look up to climb), hold back to brake, let go to hover, sneak to step off - the broom returns to your pack. Flying drains mana; when you run dry it only glides. Without a grimoire a broom can only glide, and Anti-Magic smothers it entirely.',
    '§l§dAmulets§r\n' + amulets + '\n§7Hold an amulet in your §foff hand§7. Craft them from gold nuggets, string, a mana crystal and a focus (lapis block, emerald, redstone block, iron block or golden apple), buy a Mystery Amulet from the merchant, or find one in camp chests.',
    '§l§aMagic Knight camps§r\n§7Tents around a campfire on open grassland, with knights on watch, a supply chest and a Mission Board.',
    '§l§5Awakening§r\n§7At magic level 15 every grimoire (except Anti-Magic) awakens a fifth spell - its strongest. Knights and companions learn theirs at level 15 too.',
  ].join('\n\n');
  await new MessageFormData().title('Brooms & amulets').body(body).button1('Back').button2('Close').show(p).then((res) => {
    if (res.selection === 0) return openHandbook(p);
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
