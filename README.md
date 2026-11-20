# Echoes of the Bone King - a Dungeon RPG

## How to play
1. Install Python 3.8+ (https://www.python.org).
2. Unzip this folder.
3. Run:  `python main.py`   (Mac/Linux: `python3 main.py`)
   - If pygame is missing, main.py installs it for you automatically.

## Solo or Duo
On the title screen pick **SOLO** (one player) or **DUO** (two players on the same PC). In Duo, Player 1 picks a
hero, then Player 2 (you can both pick the same one).
- **Joining:** after choosing DUO, each player presses a key or a controller button on the device they will
  play with. From then on each hero listens ONLY to their own device: keyboard + controller, two controllers, or
  one shared keyboard (Player 1 = WASD side, Player 2 = arrow side, keys below). A controller that is unplugged
  and plugged back in goes back to the same player. Esc / Circle on the join screen takes a player out again.
- **Separate settings:** Player 2 has their own keyboard keys and their own controller buttons
  (Controls > P2 KEYBOARD / P2 CONTROLLER); changing one player's never changes the other's.
- **One screen:** the camera stays between you, and you can't walk so far apart that one of you leaves the screen.
- **Shared:** both heroes get the XP for every kill (so you level up together) and every coin and chest counts
  for both. **Your own:** health, abilities, ability points, items and gold to spend. After the stairs, Player 1
  shops first, then Player 2. The pause menu has a shop for each player.
- **Going down:** a hero at 0 health goes DOWN instead of dying. Stand next to them for 2.5 seconds to revive them
  (they come back with 35% health). Going down the stairs also brings a downed partner back. The run only ends
  when BOTH of you are down.
- **Harder monsters:** there are about 35% more monsters, and they have more health (bosses even more) and hit
  harder, so a Duo run feels about as tough as a Solo run. XP and gold per kill are trimmed, so each hero levels
  and shops at the same pace as in Solo. The numbers are in settings.py (the DUO block).

| Player 2 key | What it does |
|---|---|
| Arrow keys | Walk |
| Right-Ctrl or Numpad 0 (hold) | Attack |
| `,` `.` `/` or Numpad 1 2 3 | Abilities 1 / 2 / 3 |
| `;` or Numpad 4 | Ultimate (Shadow Ninja, Vampire Lord) |
| Right-Shift or Numpad Enter | Dash |
| Enter or Numpad 5 | Go down the stairs |
| `'` or Numpad 6 (hold) | Show your stats |
| Backspace | Pause |

## Pick your hero (9 classes, 20 floors)
Knight, Ghala the Mage (pink!), Rogue, Necromancer (raises the dead), the Exiled Swordsman, the Vampire Lord,
the Shadow Ninja, the Arcane Explorer,
Monk (fast martial artist - throws an orb that sticks to a monster; press the ability again to launch yourself at it).
The Exiled Swordsman chains a Triple Slash (press the ability up to 3 times), stuns everything around him with a
War Cry, and grows his sword with Greatblade (more damage and reach - press it again to throw blade waves).
The Vampire Lord spends blood to gain blood (like Vladimir in League of Legends). Every ability but the first
COSTS a share of his current health (it can never kill him) and heals him back from what it hits:
1. **Blood Drain** (free): hurt one monster and drink its blood. The lower his health, the more he drains (up to
   3x the healing, and harder hits).
2. **Blood Pool** (15% health): sink into blood for 2.5s. Nothing can hurt him, and monsters on it are hurt
   and heal him.
3. **Tides of Blood** (7% health, 5s cooldown): throw blood at EVERY monster around him; each hit heals him.
4. **R - Blood Curse** (ULTIMATE at level 8, 10% health): curse every monster in a big splash. They take 25%
   more damage, then BURST and heal him.
His blood only comes from life a monster really had (no healing from overkill), and when one spell hits many
monsters at once, only the first heals fully (the others at a third).
The Arcane Explorer shoots quick golden bolts from his gauntlet. Essence Wave is a crescent that flies through
monsters and marks them (hit a marked monster again to burst the mark), Arcane Shift blinks you forward, blasts
monsters where you land and fires a bolt at the nearest one, and Trueshot Barrage is a HUGE crescent that crosses
the whole map through walls (each monster after the first takes 10% less, never under half).
The Shadow Ninja throws 3 Shadow Shurikens in a straight line that fly through monsters (the first hit is the hardest - every hit
after it does half), sends out a Living Shadow for 5 seconds that copies his other two abilities from where it
stands (press the ability again to swap places with it, once per shadow), and cuts everything around him with
Shadow Slash - the shadow's own slash also slows monsters, and a monster caught in both is only hurt once.
At level 8 he unlocks his ULTIMATE, Death Mark (R / Circle): he vanishes (you can't be hurt for a moment) and strikes
the monster you aim at from behind, leaving a shadow where he stood. The monster is MARKED for 3 seconds: half of
all the damage you deal it is stored, then the mark blows up for a big hit plus that stored damage. Press R again to
swap back to the shadow (once). The ultimate's shadow copies your abilities too, so you can have two shadows out.
If nobody is in range, nothing happens and there's no cooldown.
Ghala throws a Frozen Heart that freezes a monster solid, and spins a damaging Flower Ring around herself.
Each hero has 3 abilities that unlock at levels 1, 3 and 5 (the Shadow Ninja also gets an ultimate at level 8). Level-ups are automatic.
Hold the Stats button to see your numbers.

## The 20 floors and their bosses
Every 5th floor has a **mini-boss**, every 10th floor has a **major boss**. You must beat the boss to unlock the stairs.
| Floor | Boss | Type |
|---|---|---|
| 5 | Gorrak the Ogre Warlord (charges, slams, calls goblins) | Mini-boss |
| 10 | The Bone King (3 phases, bullet rings, spirals, summons) | MAJOR boss |
| 15 | Velgrim the Frost Lich (ice-bolt fans, blinks around, frost rings, raises skeletons) | Mini-boss |
| 20 | Malgor the Abyss Demon Lord (4 phases: charges, slams, fire rings, double spirals, summons) | FINAL boss - beat him to win! |

Each floor has its own look (frozen catacombs, drowned temple, fungal depths, blood cathedral...), and monsters get tougher the deeper you go.

## Ability levels
Every ability starts at rank 1 and can go up to **rank 5**. You get an **ability point** at hero level 4
and then every 3 levels (4, 7, 10, 13...). The game pauses and you choose which ability to upgrade:
use the arrows and Enter, press the ability's key (1, 2 or 3), or click it.
Each rank adds **+22% damage** and makes that ability's cooldown **10% shorter** (rank 5 = +88% damage and a
40% shorter cooldown). Allies you summon with an ability get stronger with its rank too. Shield Wall and
Living Shadow deal no damage, so ranking them up only shortens their cooldown.
You can max out all three abilities around level 37. The numbers are in settings.py (RANK_DAMAGE, RANK_COOLDOWN,
SKILL_POINT_FROM, SKILL_POINT_EVERY).

## The Shop: items (like League of Legends)
Every time you take the stairs to a new floor, the Shop opens. You can also open it from the Pause menu.
You carry up to **4 items** (one of each kind), and they make your hero stronger in 5 ways:
attack damage, ability damage, cooldown reduction, life steal (basic attacks heal you) and defense.

- **Small items** (100 gold): one small stat. Rusty Dagger, Apprentice Wand, Pocket Hourglass, Leech Fang, Leather Vest.
- **Components** (400 gold, or 300 if you carry its small item): one good stat.
  Warblade, Arcane Tome, Timekeeper's Clock, Vampire Fang, Iron Plate.
- **Mythic items** (2200 gold, or 1400 if you carry both components): two stats and a special power.

Pieces you already carry are used up and taken off the price. Selling gives back 60% (press twice).
Cooldown reduction stops at 35%, life steal at 25% and defense at 40%.

| Mythic | Stats | Power |
|---|---|---|
| Arcane Edge | +22% Attack damage, +25% Ability damage | After you use an ability, your next basic attack deals 60% more damage. |
| Tempo Blade | +22% Attack damage, +10% Cooldown reduction | Every basic attack that hits takes 0.25s off your ability cooldowns. |
| Crimson Reaver | +22% Attack damage, +8% Life steal | Your life steal is DOUBLED while you are below 40% health. |
| Titan's Maul | +22% Attack damage, +12% Defense | Basic attacks deal extra damage equal to 2% of your max health. |
| Echo Staff | +25% Ability damage, +10% Cooldown reduction | Every 6s, your next ability hit blasts every monster around the target. |
| Soul Drinker | +25% Ability damage, +8% Life steal | Your abilities heal you for 5% of the damage they deal (a third for extra targets and poison). |
| Frost Aegis | +25% Ability damage, +12% Defense | Your abilities SLOW the monsters they hit for 1.2s. |
| Reaper's Hourglass | +10% Cooldown reduction, +8% Life steal | Every kill takes 0.5s off your cooldowns and heals 2% of your health. |
| Guardian Clock | +10% Cooldown reduction, +12% Defense | Falling below 30% health gives you a shield that blocks everything for 2s (once every 60s). |
| Bramble Heart | +8% Life steal, +12% Defense | Monsters that hit you up close take a full basic attack of damage back. |

Want different prices or numbers? They are all at the top of `items.py`.

## Healing (there are no potions)
- **Every kill** heals 0.5% of your maximum health (it adds up while you fight).
- **Between floors**, the Shop has **Refill Health**: pay gold to heal back to full. You only pay for the
  health you are missing, and if you can't afford all of it you get as much as your gold buys.
  (This offer only shows up between floors, not in the Pause-menu shop.)
- You still get a little health back for free when you take the stairs and when you level up.
- **Life steal limits:** you can never steal more life than a monster had left (hitting a 10-HP monster for
  500 only counts 10). With abilities, only one hit at a time heals fully: the other monsters an area attack
  hits, and poison ticks, heal at a third. And all life stolen by abilities with the Soul Drinker item is
  capped at 2% of your max health per second, saved up to 12%. (The Vampire's own spells don't use this cap:
  they cost him health instead.) (The numbers are in items.py:
  ABILITY_LS_...)

## Difficulty and speed
- Want the game easier or harder? Open `settings.py` and change the numbers in the **DIFFICULTY** block
  (monster health, damage, speed, how many monsters per room, how much you heal for free).
- Leveling too fast or too slow? Change `XP_MULT`. Too much or too little gold? Change `GOLD_MULT`
  (and `GOLD_PER_FLOOR`, how much more coins are worth on deeper floors).
- The game draws in step with your monitor (60 FPS on a 60 Hz screen, up to 144 on a fast one).
  Press **F3** to show the FPS counter.

## Smarter monsters
Monsters find their way around walls and down hallways, spread out instead of piling up, and take
TURNS: only a few close in on you at once while the rest circle around, waiting for a gap. Only a few
can wind up a big attack (lunge, slam, explode) or shoot at the same moment, and they never shoot
from off-screen. A yellow "!" shows when a monster spots you (it pauses a moment before attacking).
If you get away and stay out of sight long enough, they give up.

They get cleverer the deeper you go. On floor 1 they simply walk at you. Further down they come at you
from the sides, aim some shots ahead of where you're running (change direction to dodge!), sometimes
sidestep your shots, and warn nearby friends when they spot you.
Too hard or too easy? In settings.py, AI_DIFFICULTY = 0.5 makes them half as clever (0 = no tricks),
and AI_SMARTS_FULL_FLOOR picks the floor where they reach full cleverness.

## Keyboard controls (default)
| Key | What it does |
|---|---|
| WASD / Arrow keys | Walk (in Duo the arrows are Player 2's) |
| SPACE (hold) | Attack |
| 1 / 2 / 3 | Use abilities |
| R | Ultimate (Shadow Ninja, Vampire Lord) |
| SHIFT | Dash (you can't be hurt for a moment) |
| E | Go down the stairs |
| TAB (hold) | Show your stats |
| P / ESC | Pause |
| M | Mute / unmute |
| F11 | Full screen |
| F3 | Show / hide the FPS counter |

## PS5 controller (DualSense) - how to connect it
**USB cable (easiest):** plug the controller into your computer with a USB-C cable. Done!
The game shows "Controller connected" at the top. You can plug it in before or after starting.

**Bluetooth (wireless):**
1. Turn Bluetooth on in your computer's settings.
2. On the controller, HOLD the **PS button + Create button** (small button left of the touchpad) for ~3 seconds, until the light bar flashes fast.
3. In your computer's Bluetooth list, pick **DualSense Wireless Controller** and press Pair.
4. Start (or look at) the game - it finds the controller by itself.

Works on Windows, Mac and Linux with no extra software. You do NOT need Steam or DS4Windows
(close Steam if it is open - it can steal the controller).

## PS5 controller - what the buttons do (default)
| Button | What it does |
|---|---|
| Left stick | Walk (push gently = walk slowly) |
| D-pad | Walk (and move in menus) |
| Right stick | Aim (push it all the way to auto-attack) |
| R2 or Square | Attack |
| L1 / R1 / L2 | Ability 1 / 2 / 3 |
| Circle | Ultimate (Shadow Ninja, Vampire Lord) |
| Cross (X) | Dash |
| Triangle | Stairs / interact |
| Create or Touchpad (hold) | Show stats |
| Options | Pause |
| Menus | Cross = choose, Circle = back, L1/R1 = switch tabs, Triangle = reset |

The pad vibrates when you get hit, dash, or use big attacks (you can turn this off).
On-screen hints switch between keyboard keys and PlayStation symbols automatically,
depending on which one you touched last.

## Changing the music and volume
Title screen -> **Music** (or Pause -> Music). Pick from 4 tunes (Catacombs, War March, Moonlit Keep,
Goblin's Jig) or **No Music** to turn the background music off while keeping sound effects on.
The same screen has a Music Volume and an SFX Volume slider (Left/Right to adjust).
Your choices are saved in `audio.json`.

## Changing the controls
Title screen -> **Controls** (or Pause -> Controls). Three tabs:
- **Keyboard** and **PS5 Controller**: pick an action, choose the MAIN or ALTERNATIVE slot
  (Left/Right), press Enter / Cross, then press the new key/button. Esc cancels, Backspace clears.
  If the key is already used for something else, it moves to the new action (you'll see a message).
  The controller tab also has: stick dead zone, vibration, right-stick aiming, auto-attack, aim assist.
- **Layout & Setup**: a picture of the controller with your current buttons and the connection steps.
The mouse works in the menus too. Your choices are saved in `controls.json` (delete it to reset everything).

## Controller troubleshooting
- Not detected? Unplug and replug, or hold PS for 10 seconds to turn it off and re-pair.
- Character drifts by itself? Raise "Stick dead zone" in Controls.
- Buttons feel wrong? Close Steam / other controller programs, then restart the game.
- No luck? The keyboard always works.

## Files
- main.py     - start here!
- settings.py - easy numbers to tweak
- inputs.py   - keyboard + controller handling and the saved bindings
- classes.py  - heroes, abilities and level-up stats (add your own here!)
- biomes.py   - the look of each floor
- dungeon.py  - builds random dungeons
- entities.py - hero, monsters and their brains, spells, loot
- ai.py       - the monsters' shared brain: pathfinding, taking turns, aiming, dodging
- items.py    - the shop items: prices, stats, recipes and mythic powers
- sprites.py  - draws all the pictures with code
- sounds.py   - makes all sounds and music with math
- game.py     - the game brain: menus, fighting, abilities, drawing
