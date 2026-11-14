"""settings.py - the game's 'control panel'. Change numbers here to change the game!"""

WIDTH, HEIGHT = 1280, 720     # window size in pixels (you can also resize the window or press F11)
TILE = 40                     # every floor/wall square is 40x40 pixels
FPS = 60                      # frames per second
MAP_W, MAP_H = 56, 40         # dungeon size (in tiles)
TITLE = "Echoes of the Bone King - Dungeon RPG"
MAX_FLOOR = 20                # floor 20 has the FINAL boss
# Every 5th floor has a MINI-boss (5, 15). Every 10th floor has a MAJOR boss (10, 20).
BOSS_FLOORS = {5: 'warlord', 10: 'boss', 15: 'lich', 20: 'demon'}
MAJOR_BOSS_KINDS = ('boss', 'demon')
MINIMAP_SCALE = 4             # pixels per tile on the minimap
