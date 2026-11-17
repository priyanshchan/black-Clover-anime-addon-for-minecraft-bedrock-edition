# Changelog

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
