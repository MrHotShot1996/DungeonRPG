"""settings.py - the game's 'control panel'. Change numbers here to change the game!"""

WIDTH, HEIGHT = 1280, 720     # window size in pixels (you can also resize the window or press F11)
TILE = 40                     # every floor/wall square is 40x40 pixels
FPS = 60                      # frames per second
MAP_W, MAP_H = 56, 40         # dungeon size (in tiles)
TITLE = "Echoes of the Bone King - Dungeon RPG"
MAX_FLOOR = 10                # floor 10 has the final boss
BOSS_FLOORS = {5: 'warlord', 10: 'boss'}   # which floors have a boss (floor 5 = mini-boss)
MINIMAP_SCALE = 4             # pixels per tile on the minimap
