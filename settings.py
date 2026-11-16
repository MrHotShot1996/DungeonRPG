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
XP_MULT = 0.85                # how much XP monsters give (1.0 = how it used to be; lower = level up slower)
GOLD_MULT = 0.6               # how much gold coins and chests are worth (bigger = richer)
GOLD_PER_FLOOR = 0.05         # gold is worth this much more on every floor deeper (0.05 = +5% per floor)

# ---- ABILITY LEVELS: every ability starts at rank 1 and can go up to ABILITY_MAX_RANK.
# You earn an ability point at hero level SKILL_POINT_FROM and then every SKILL_POINT_EVERY levels,
# and choose which ability gets it. Each rank above 1 adds RANK_DAMAGE damage and cuts RANK_COOLDOWN off
# the ability's cooldown (0.22 and 0.10: rank 5 = +88% damage and a 40% shorter cooldown).
ABILITY_MAX_RANK = 5
SKILL_POINT_FROM, SKILL_POINT_EVERY = 4, 3
RANK_DAMAGE = 0.22
RANK_COOLDOWN = 0.10
# ---- Arcane Explorer
ESSENCE_TIME = 4.0            # Essence Wave: seconds a mark lasts
ESSENCE_BURST = 1.2           # ...how hard the mark bursts (x your damage) when you hit the marked monster
SHIFT_RANGE = 170             # Arcane Shift: how far you blink (pixels)
SHIFT_RADIUS = 95             # ...the blast where you land
TRUESHOT_DECAY = 0.10         # Trueshot Barrage: each monster after the first takes 10% less (never under half)
SKILL_LOCK = 1.0              # seconds the ability-point screen ignores every button when it opens (so a held
                              # attack button can't pick something by accident)
SKILL_LOCK_NEXT = 0.4         # ...and between picks, when you have more than one point to spend

# ---- MONSTER BRAINS (see ai.py). Monsters get cleverer the deeper you go: on floor 1 they just walk at you,
# and by AI_SMARTS_FULL_FLOOR they aim ahead of you, sidestep some of your shots and come at you from the sides.
AI_SMARTS_FULL_FLOOR = 16     # the floor where monsters reach full cleverness
AI_DIFFICULTY = 1.0           # 0.5 = monsters only get half as clever, 0 = no clever tricks at all
