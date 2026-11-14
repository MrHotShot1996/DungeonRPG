"""settings.py - the game's 'control panel'. Change numbers here to change the game!"""

WIDTH, HEIGHT = 1280, 720     # window size in pixels (you can also resize the window or press F11)
TILE = 40                     # every floor/wall square is 40x40 pixels
FPS = 144                     # the MOST frames per second the game will draw. It follows your monitor
                              # (60 on a 60 Hz screen, up to 144 on a fast one) and never draws more than that.
MAP_W, MAP_H = 56, 40         # dungeon size (in tiles)
TITLE = "Echoes of the Bone King - Dungeon RPG"
MAX_FLOOR = 20                # floor 20 has the FINAL boss
# Every 5th floor has a MINI-boss (5, 15). Every 10th floor has a MAJOR boss (10, 20).
BOSS_FLOORS = {5: 'warlord', 10: 'boss', 15: 'lich', 20: 'demon'}
MAJOR_BOSS_KINDS = ('boss', 'demon')
MINIMAP_SCALE = 4             # pixels per tile on the minimap

# ---- DIFFICULTY: bigger numbers = a harder game. (1.0 = how the game used to be.)
ENEMY_HP_MULT = 1.15          # normal monsters have this much more health
ENEMY_DMG_MULT = 1.15         # ...and hit this much harder
ENEMY_SPEED_MULT = 1.05       # ...and move this much faster
BOSS_HP_MULT = 1.2            # bosses have this much more health
BOSS_DMG_MULT = 1.1           # ...and hit this much harder
EXTRA_MONSTERS_FROM_FLOOR = 3 # from this floor on, every room has one more monster
MAX_MONSTERS_PER_ROOM = 8
ELITE_CHANCE_MAX = 0.32       # the most often a monster can be an ELITE (deep floors)
HURT_INVULN = 0.8             # seconds you can't be hurt again after taking a hit (was 0.9)
STAIRS_HEAL = 0.10            # free heal when you take the stairs (part of your max health; was 0.20)
LEVELUP_HEAL = 0.20           # free heal when you level up (was 0.30)
