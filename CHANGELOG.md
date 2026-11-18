# Changelog

## v0.5.0 – Early Access (2026-11-18)

**The companion update.** Your Magic Knights become a real squad: personalities, specialisations, party tactics, combos, revives, mood, camps, personal trials, a reserve with expeditions, sparring and rival squads - and they fly brooms beside you. Plus four new grimoires and a boss that turns your own companions against you.

> v0.2.0 and v0.3.0 were never published as releases, so this build also contains both: the saved companion party, smarter enemies and bosses, the Fallen Captain, 16 grimoires and 8 Abyss Fruits (v0.2.0), and magic brooms, daily missions, amulets, awakened spells, Rogue Mages, the Witch Sisters, the Bone Dragon and Magic Knight camps (v0.3.0). See [CHANGELOG.md](https://github.com/priyanshchan/black-Clover-anime-addon-for-minecraft-bedrock-edition/blob/ccr-62b3f23b-74ycbu/CHANGELOG.md) for everything.

### Download
* **`BlackClover_GrimoireAwakening_v0.5.0.mcaddon`** – open it and Minecraft imports both packs (it replaces earlier versions; your grimoire, levels and party are kept, and existing companions get a personality).
* `BlackClover_BP_v0.5.0.mcpack` / `BlackClover_RP_v0.5.0.mcpack` – the packs separately.

### Companions: who they are
* **Personalities** – Brave, Cautious, Loyal, Hothead, Cheerful, Scholar. They change courage, skill, spell power, casting pace, where a companion stands in a fight and what it says (Scholars learn 25% faster, Cheerful companions lift the party's morale, Loyal ones stay at your side).
* **Specialisations at level 10** – **Vanguard** (resistance, Taunt pulls every foe and boss onto itself, Shield Bash, stands between you and danger), **Arcanist** (+15% power, 15% shorter cooldowns, Arcane Barrage), **Warden** (Aegis shields the party, Cleanse removes curses, cuts down arrows and spells aimed at you, revives twice as fast), **Ranger** (fights from 10+ blocks, piercing Volley, Mark for +20% squad damage). **Mastery** at level 20 or through a trial: Bulwark, Spell Echo, Sanctuary, Hawk Eye. A **Companion Tome** retrains them.
* **Mood** – morale and weariness. Inspired companions hit 10% harder; shaken ones lose their nerve; exhausted ones cast slower. Victories, gifts, talks, rest and **Field Rations** keep them going.
* **Talk** – ask how they feel, about their hometown and dream, or for advice.
* **Personal trials** – at bond Friend a companion asks for help with a trial (hunt devils, rogues, the dead, face a giant...). Finishing it **awakens their grimoire** early and earns them a title; a second trial at Sworn Ally grants mastery.

### Companions: how they fight (AI)
* **Party tactics** on the whistle: Balanced, Focus fire, Protect me, Spread out, Hit and run.
* **Combos** – foes held by a prison or a time stop take +25% from the squad; strikers go for bound foes while controllers look for fresh ones. **Marks** add +20% (+35% at mastery).
* **Danger awareness** – boss warning circles, spell fields, meteor and rain targets are danger zones; companions step out of them (other NPCs do too, by skill).
* **Revives** – a fallen companion leaves a glowing clover for 60 s. Sneak beside it, or a squadmate kneels there (a Warden first, and twice as fast), and they get up at half health. **Clover Leaf of Return** revives everyone at once.
* **Smarter positioning** – Vanguards bodyguard you, Rangers and cautious companions keep their distance, Protect me keeps everyone close, Spread out keeps them apart.
* **Flying together** – mount a broom and your companions summon their own and fly in formation behind you; land and they land with you.
* The brain itself gained taunts (forced targets), extra skill actions, target preferences, spell echo and personality-driven courage and skill.

### Companions: squad life
* **Make camp** with the whistle: they sit around a fire, heal, shed weariness and tell stories. At night one keeps **watch** and raises the alarm when something creeps up. Between fights they **banter** with each other.
* **Squad Banner** block: a **reserve** of 6 more knights (new recruits wait there when your party of 4 is full), swap knights in and out, reserve knights train while they wait, and **expeditions** - 6 timed missions from 8 to 60 real minutes (they run even while you are offline) that bring back doubloons, pages, amulets, rare loot and XP. Odds depend on level, specialisation, mastery and mood.
* **Training Dummy** – shows your DPS; switch training on and your companions practise on it between fights.
* **Sparring matches** – two companions duel, non-lethally, for XP.
* **Rival squads** (world event) – another company's squad challenges your party to a friendly match: beaten rivals yield, nobody dies, the winner takes doubloons and glory.
* Hold the **Companion Whistle** to see your party's health and mood on screen. Hand a companion an **amulet** to wear.

### New boss: the Soul Puppeteer
* A floating marionette master with a porcelain mask (600 HP). String lashes, falling needles, marionette minions - and **the strings**: it takes control of your companions, who turn their magic on you. Strike them a few times or have a Warden Cleanse them to cut the strings. Desperation: **Grand Finale**.
* Summon it with a **Cursed Spool**, or meet it in the new night event.

### More content
* **4 new grimoires, 20 spells:** Gravity, Moon, Thorn and Ash, each with an awakened spell (36 grimoires and 179 spells in total).
* **New items:** Squad Banner, Training Dummy, Clover Leaf of Return, Field Rations, Companion Tome, Cursed Spool. The merchant sells rations, clover leaves and tomes.
* **New creature:** the Marionette.
* **New events:** rival squad, puppet show.

### Animations & models
* Companions: kneel (reviving), point (marking), guard, victory, wave, taunt, eat, sleep, and a riding pose for brooms.
* The Soul Puppeteer (float, cast, control, summon, roar), the Marionette (idle, jerky walk, attack), the Training Dummy (hit wobble), the Squad Banner block.

### Fixes & changes
* Friendly fights (sparring, rival squads) can never kill.
* The companion loop now runs on aligned ticks, so periodic checks (bond over time, saving) fire reliably.
* Knight Contracts and recruiting count the reserve: you can lead up to 10 knights.

### Known issues
* Companions on brooms are steered by script; in tight caves they may clip through leaves or ceilings until you land.
* Expedition timers use real time; changing your device clock changes them too.
* Balance is still a first pass: please report anything too strong or too weak.

## v0.3.0 – Early Access (2026-11-17)

A big content drop: take to the sky on **magic brooms**, earn rewards with **daily missions**, wear **amulets**, awaken a **fifth spell** in every grimoire, and face **Rogue Mages**, the **Witch Sisters** and the **Bone Dragon**.

> v0.2.0 was never published as a release, so this build also contains all of v0.2.0: the saved **companion party** with smart AI, smarter enemies and bosses (threat, three phases, desperation moves), the Fallen Captain, 8 more grimoires and 8 more Abyss Fruits. See the v0.2.0 section of [CHANGELOG.md](https://github.com/priyanshchan/black-Clover-anime-addon-for-minecraft-bedrock-edition/blob/ccr-62b3f23b-74ycbu/CHANGELOG.md) for the full list.

### Download
* **`BlackClover_GrimoireAwakening_v0.3.0.mcaddon`** – open it and Minecraft imports both packs (it replaces v0.1.0 / v0.2.0; your grimoire, levels and party are kept).
* `BlackClover_BP_v0.3.0.mcpack` / `BlackClover_RP_v0.3.0.mcpack` – the packs separately.

### New: magic brooms
* **Magic Broom** (stick, hay block, mana crystal) and **Swift Broom** (feathers, a diamond, a Magic Broom). Use one to mount it.
* **Look** to steer, **hold forward** to fly (look up to climb, down to dive), **hold back** to brake, let go to **hover**, **sneak** to step off – the broom flies back into your pack and you float down gently.
* Flying costs mana (1.5 / 2.5 per second, 40% while hovering) and your mana does not regenerate in the air. Run dry and the broom glides down until 15% of your mana is back.
* Without a grimoire a broom can only glide; Anti-Magic smothers it entirely. A small HUD shows speed, mana and altitude.

### New: daily missions
* **Three missions every in-game day** – an easy one, a harder one and a wild card – from 15 kinds: hunt Dark Disciples, Imps, Hellhounds, raiders, Mana Wraiths or Rogue Mages, patrol against monsters, defeat any boss, seal a Devil Gate, cast 40 spells, earn 600 XP, deliver crystals, pages or bones, or lead your companions to 10 victories.
* Progress counts anywhere (your companions' kills count too); everyone near a boss or a sealed gate gets credit.
* Claim rewards at the new **Mission Board** block (oak planks, paper, green dye, sticks): 1-3 stars, 30-150 doubloons and 120-500 magic XP; all three done gives 4 Mana Crystals. Swap an unstarted mission (free once a day). The Handbook shows today's missions.

### New: amulets
* Hold one in your **off hand**: **Mana Heart** (+30 max mana, +20% regen), **Swift Sigil** (cooldowns −12%), **Battle Charm** (+12% spell power), **Guardian Ward** (Resistance II below 40% health), **Vigor Band** (two extra hearts, faster healing).
* Craft them (gold nuggets, string, a mana crystal and a focus), buy a **Mystery Amulet** from the merchant, or find them in camps and boss loot.

### New: awakened spells
* At **magic level 15** every grimoire except Anti-Magic awakens a **fifth, strongest spell** – 31 in total (159 spells overall): Gale Emperor, Crown of Suns, Ocean Sovereign, Thousand Bolts and more.
* Magic Knights and companions learn their awakened spell at level 15 too.

### New foes
* **Rogue Mages** – outlaw mages with a real grimoire (any attribute) and a level from 2 to 8. They spawn at night in plains, forests, taiga and savanna, fight with the same tactical brain and spell kits as knights, hunt players, knights and the Tidewatch, and form a **Rogue Mages** army at the War Table.
* **The Witch Sisters** (twin boss, 450 HP each) – the Frost Witch and the Ember Witch fly, blink away from melee and weave **Twin Spells** (an ice prison, then falling fire on the same spot). Kill one and the other screams, gains strength and speed and unleashes her desperation move: **Absolute Winter** or **Inferno Requiem**. Summon them with a **Twin Moon Charm**.
* **The Bone Dragon** (1100 HP) – circles overhead, breathes withering bone-fire, blows you away with its wings, rains bones, dives onto a warning circle, sweeps its tail and raises skeletons. Desperation: **Death's Wingbeat**. Summon it with a **Bone Totem**.

### World
* **Magic Knight camps** appear on open grassland: tents and bedrolls around a campfire, a Mission Board, a supply chest and three knights on watch.
* New events: **Rogue ambush** (sometimes with a knight patrol coming to help), **Witch Sisters** (night) and **Bone Dragon** (night).
* The Travelling Merchant sells **Magic Brooms** and **Mystery Amulets**.

### Animations & models
* New 3D models: two brooms, the Mission Board, Rogue Mages (four robe colours), the Frost and Ember Witches, the Bone Dragon.
* Witches: float, cast, staff sweep, roar. Bone Dragon: wingbeat flight, breath, dive, tail sweep, roar. Brooms bob and sway in flight.

### Known issues
* Camps only appear on fairly flat grass or dirt, so they are rarer in hilly biomes.
* Balance is still a first pass: please report anything too strong or too weak.

## v0.2.0 – Early Access (2026-11-17)

A big content update with a full **companion system**, smarter **enemies** and **bosses**, and many new **animations**.

### Download
* **`BlackClover_GrimoireAwakening_v0.2.0.mcaddon`** – open it and Minecraft imports both packs (it replaces v0.1.0).
* `BlackClover_BP_v0.2.0.mcpack` / `BlackClover_RP_v0.2.0.mcpack` – the packs separately.

### New: companions
* Recruited Magic Knights become a **saved party of up to 4**: name, magic, level, robe and bond stay with your player across sessions, and a fallen companion **returns after 60 seconds**.
* **Companion Whistle:** open your party, summon or dismiss, rename, give orders, choose a **stance** (aggressive, defensive, passive) and a **formation** (wedge, line, circle), toggle loot gathering. **Sneak + use** at a foe: everyone attacks it; at nothing: regroup.
* **Smart support AI:** companions attack what you attack, rush whoever hurts you, heal you first when you are low, step out of your line of fire, walk in formation, gather loot, sit when you rest and talk to you.
* **Levels 1-20** with health tiers (40 → 130), more spells at 3 and 6, extra power above 10.
* **Bond:** grows with time, victories, level-ups and **gifts** (Mana Cookies and more). Ranks unlock **Mana Link**, **Guardian** and **Union Magic** (a combined ultimate spell).
* **Robes:** hand a companion a squad robe to dress them and give them its perk.
* Rescue a **wounded knight** (new event) and it joins you.

### Smarter enemies
* Dark Disciples, Imps, Sea Raiders, the new **Raider Gunners** and **Tidewatch Marksmen**, **Hellhounds** and **Mana Wraiths** now fight with the tactical brain: spell kits, aim leading, dodging, retreating.
* Gunners and marksmen aim before they fire and keep their distance; Hellhounds hunt in packs, circling their prey before lunging; hurt one enemy and its kind come running.

### Smarter bosses
* **Threat tables:** bosses turn on whoever hurts them most (melee knights and companions can tank).
* **Three phases** with a once-only **desperation** move: Hellgate, Avalanche, Ghost Ram, Maelstrom, Final Form.
* **Telegraphed** slams and waves, **signature movement** (Archdevil blinks, Kraken submerges, Colossus stomps, Galleon rams) and a six-minute **enrage timer**.
* New boss: **the Fallen Captain** - a corrupted Magic Knight captain who duels with a blade and three grimoires, blinks behind you, parries and dodges.

### New content
* **8 grimoires, 32 spells:** Cotton, Paper, Smoke, Glass, Gold, Beast, Spirit, Rune (32 grimoires and 128 spells in total).
* **8 Abyss Fruits, 24 abilities:** Spore, Thread, Slime, Chain, and the **Lion, Shark, Phoenix and Spider** beast forms (30 fruits and 90 abilities in total; the Shark Fruit is not drained by the sea).
* **New creatures:** Raider Gunner, Tidewatch Marksman, Hellhound, Mana Wraith (drains your mana), the Fallen Captain.
* **New items:** Companion Whistle, Mana Cookie (+30 mana), Seal of the Fallen Captain.
* **New events:** wounded knight, mana storm, bounty hunters, the Fallen Captain.

### Animations
* Knights and companions: cast animations per kind of spell (raise, channel, slam), dodge, flinch, salute, cheer, sit.
* Player: channel and slam casting animations for the new spell kinds.
* Bosses: Colossus throw, stomp and roar; Archdevil roar and blink; Kraken submerge and emerge; Galleon broadside and ram; Fallen Captain slash, cast, parry and roar.
* Enemies: gunner aim, shoot and throw; Hellhound bite and howl; Mana Wraith float and cast.

### Known issues
* Balance is still a first pass: please report anything too strong or too weak.
* Companions fall back to the vanilla follow behaviour on rough terrain; the whistle's regroup fixes stragglers.
* The Stone Colossus can get stuck on rough terrain; the Phantom Galleon is steered by script and may drift.

## v0.1.0 – Early Access (2026-11-17)

The first public build of **Black Clover: Grimoire Awakening**, an unofficial fan addon for Minecraft Bedrock (1.21.90+, no experimental toggles).
This release puts the focus on **AI behaviour and simulation**: NPCs that fight with tactics, battles you can stage and watch, and a world whose factions rise and fall on their own.

> Early access: everything works end to end in our automated checks, but balance (damage, morale, bets, boss health) is a first pass. Please report anything odd in the issue tracker.

### Download
* **`BlackClover_GrimoireAwakening_v0.1.0.mcaddon`** – open it and Minecraft imports both packs.
* `BlackClover_BP_v0.1.0.mcpack` / `BlackClover_RP_v0.1.0.mcpack` – the behavior and resource packs separately.
* If you tried a private test build before, remove those packs first (they used a higher internal version number).

### New: tactical AI for spellcasters
* Magic Knights and Raider Captains are run by a shared **tactical brain**. Each has a **fighting style** worked out from the spells it knows (striker, controller, brawler or support) and two traits: **skill** and **courage**.
* Every moment it scores each spell for the situation – range, how tightly enemies are bunched, hurt allies, cooldowns – and casts the best one, **leading moving targets** (better aim with more skill).
* NPCs **side-step spells and arrows** flying at them, **gang up** on their army's focus target, prefer foes that just hurt them, **heal and buff** hurt friends, and **fall back** to their allies when badly wounded (unless they are brave).
* Spellcasters **keep their distance** from foes that get too close while brawlers dive in.
* Team-aware targeting everywhere: commodore bombardments and captain powers in a battle only hit the other armies.

### New: battle simulation
* **Tactics** per army: *Charge* (speed burst), *Hold the line*, *Flank* (half the army swings around the side), *Skirmish* (mages kite).
* **Formations**: melee in front, mages behind, the leader in the middle.
* **Morale**: losses, a fallen leader or being outnumbered break an army; frightened soldiers **flee** and can **rally** while their leader lives. An army with no one left fighting loses.
* **Leaders** steady and strengthen the soldiers around them.
* **Three-army battles** (Blue, Red and Gold) and **knight duels** with any two magic attributes and a chosen level.
* A live **scoreboard** (soldiers and morale per army), a **kill feed**, a **battle report** with an MVP, bets that pay 2x (3x with three armies), and a slowly circling **cinematic camera** (sneak to leave).

### New: the world simulates itself
* The Clover Magic Knights, Devil Host, Sea Raiders and Tidewatch Navy each have a **power** that falls when their people die and rises when they win real battles. Off screen, rivals keep fighting and the **news** reaches you.
* Strong factions show up more often in world events; a dominant one launches an **offensive** – a large battle near a player.
* **State of the Kingdom** page (Handbook and War Table) with power bars and the latest news.

### New: knights you can lead
* Knights **level up** (1–10) from kills, with ranks shown over their heads, and learn more of their grimoire at levels 3 and 6.
* **Talk** to any knight to see its profile (magic, rank, style, skill, courage, kills). **Recruit** wild knights with a Knight Contract or doubloons (up to 4).
* Give your knights **orders**: follow, hold this position, guard you (defensive) or hunt freely (aggressive), or release them.
* New world event: a **knights' tournament** duel.

### Everything else in this first build
* 24 grimoires (96 spells) including the five-leaf Anti-Magic grimoire with three demon swords and Black Form; 22 Abyss Fruits (66 abilities) with Wolf, Hawk, Bear, Tiger and Wyvern beast forms; Will; nine squad robes and Magic Knight ranks.
* Sailing ships with cannons, raider outposts and wrecks, a Bounty Board, ancient dungeons, treasure maps and pirate weapons.
* Bosses: the Devil, the Abyssal Leviathan, the Dungeon Guardian, the Archdevil, the Stone Colossus, the Phantom Galleon and the Storm Kraken.
* Random world events, the Travelling Magic Merchant, the War Table and the Skirmish Horn.

### Known issues
* Not yet tuned in long play sessions: damage numbers, bet payouts, boss health and morale thresholds may change.
* The Stone Colossus is huge and can get stuck on rough terrain; the Phantom Galleon is steered by script and may drift.
* Spell trails behind the new mana bolts may appear white on some devices.
