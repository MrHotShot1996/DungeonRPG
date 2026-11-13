# Echoes of the Bone King - a Dungeon RPG

## How to play
1. Install Python 3.8+ (https://www.python.org).
2. Unzip this folder.
3. Run:  `python main.py`   (Mac/Linux: `python3 main.py`)
   - If pygame is missing, main.py installs it for you automatically.

## Pick your hero (7 classes, 10 floors)
Knight, Ghala the Mage (pink!), Rogue, Cleric, Necromancer (raises the dead), Beastmaster (calls beasts),
Monk (fast martial artist - throws an orb that sticks to a monster; press the ability again to launch yourself at it).
Ghala throws a Frozen Heart that freezes a monster solid, and spins a damaging Flower Ring around herself.
Each hero has 3 abilities that unlock at levels 1, 3 and 5. Level-ups are automatic.
Floors 5 and 10 have bosses. Hold the Stats button to see your numbers.

## The Shop
Every time you take the stairs to a new floor, the Shop opens so you can spend the gold you picked up:
more potions, permanent +HP/+damage/+speed upgrades. Prices go up a little each floor. You can also open
it anytime from the Pause menu, and leave empty-handed if you'd rather save your gold.

## Keyboard controls (default)
| Key | What it does |
|---|---|
| WASD / Arrow keys | Walk |
| SPACE (hold) | Attack |
| 1 / 2 / 3 | Use abilities |
| SHIFT | Dash (you can't be hurt for a moment) |
| Q | Drink a potion |
| E | Go down the stairs |
| TAB (hold) | Show your stats |
| P / ESC | Pause |
| M | Mute / unmute |
| F11 | Full screen |

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
| Circle | Drink potion |
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
- sprites.py  - draws all the pictures with code
- sounds.py   - makes all sounds and music with math
- game.py     - the game brain: menus, fighting, abilities, drawing
