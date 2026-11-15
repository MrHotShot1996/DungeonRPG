# Echoes of the Bone King - a Dungeon RPG

## How to play
1. Install Python 3.8+ (https://www.python.org).
2. Unzip this folder.
3. Run:  `python main.py`   (Mac/Linux: `python3 main.py`)
   - If pygame is missing, main.py installs it for you automatically.

## Pick your hero (8 classes, 20 floors)
Knight, Ghala the Mage (pink!), Rogue, Necromancer (raises the dead), the Exiled Swordsman, the Vampire Lord,
the Shadow Ninja,
Monk (fast martial artist - throws an orb that sticks to a monster; press the ability again to launch yourself at it).
The Exiled Swordsman chains a Triple Slash (press the ability up to 3 times), stuns everything around him with a
War Cry, and grows his sword with Greatblade (more damage and reach - press it again to throw blade waves).
The Vampire Lord drains blood from monsters to heal a little (Blood Drain), sinks into a Blood Pool where nothing
can hurt him while monsters standing on it take damage, and throws a Blood Curse: cursed monsters take 25% more
damage from you, then burst after 4 seconds - the more you hurt them, the bigger the burst - and the burst heals you.
The Shadow Ninja throws 3 Shadow Shurikens that fly through monsters (the first hit is the hardest - every hit
after it does half), sends out a Living Shadow for 5 seconds that copies his other two abilities from where it
stands (press the ability again to swap places with it, once per shadow), and cuts everything around him with
Shadow Slash - the shadow's own slash also slows monsters, and a monster caught in both is only hurt once.
Ghala throws a Frozen Heart that freezes a monster solid, and spins a damaging Flower Ring around herself.
Each hero has 3 abilities that unlock at levels 1, 3 and 5. Level-ups are automatic.
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

## The Shop
Every time you take the stairs to a new floor, the Shop opens so you can spend the gold you picked up:
permanent +HP/+damage/+speed upgrades. Prices go up a little each floor. You can also open
it anytime from the Pause menu, and leave empty-handed if you'd rather save your gold.

## Healing (there are no potions)
- **Every kill** heals 0.5% of your maximum health (it adds up while you fight).
- **Between floors**, the Shop has **Refill Health**: pay gold to heal back to full. You only pay for the
  health you are missing, and if you can't afford all of it you get as much as your gold buys.
  (This offer only shows up between floors, not in the Pause-menu shop.)
- You still get a little health back for free when you take the stairs and when you level up.

## Difficulty and speed
- Want the game easier or harder? Open `settings.py` and change the numbers in the **DIFFICULTY** block
  (monster health, damage, speed, how many monsters per room, how much you heal for free).
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
| WASD / Arrow keys | Walk |
| SPACE (hold) | Attack |
| 1 / 2 / 3 | Use abilities |
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
- sprites.py  - draws all the pictures with code
- sounds.py   - makes all sounds and music with math
- game.py     - the game brain: menus, fighting, abilities, drawing
