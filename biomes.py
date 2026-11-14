"""biomes.py - every floor of the dungeon has its own colours, lights and decorations."""

FLOOR_NAMES = ["The Damp Cellar", "Forgotten Sewers", "Slime Caverns", "The Spider Nest",
               "The Ogre Pit", "The Bone Halls", "Crypt of Whispers", "Cultist Sanctum",
               "The Burning Depths", "Throne of the Bone King",
               "Frostbitten Catacombs", "The Drowned Temple", "Fungal Depths", "The Rotting Gardens",
               "Sanctum of the Frost Lich", "The Obsidian Forge", "Blood Cathedral", "Hall of Shadows",
               "The Gates of Ruin", "The Abyssal Throne"]

# floor/wall/top = tile colours.  light = torch colour.  ambient = colour of the darkness.
# decor = list of decorations that can appear in rooms.  moss = green patches on the floor.
BIOMES = [
    dict(floor=(66, 64, 80),  wall=(98, 92, 112),  top=(26, 24, 36), light=(255, 175, 90),  ambient=(6, 6, 16),
         dark=212, mote=(200, 200, 230), decor=['bones', 'rubble', 'web', 'puddle'], puddle=(60, 90, 140), moss=False,
         banner=(150, 40, 50)),
    dict(floor=(54, 70, 74),  wall=(76, 108, 106), top=(18, 30, 32), light=(255, 205, 120), ambient=(3, 12, 16),
         dark=214, mote=(160, 230, 220), decor=['puddle', 'puddle', 'rubble', 'bones'], puddle=(50, 130, 140), moss=True,
         banner=(40, 100, 110)),
    dict(floor=(56, 74, 52),  wall=(84, 112, 70),  top=(16, 30, 18), light=(190, 255, 130), ambient=(3, 14, 6),
         dark=214, mote=(190, 255, 150), decor=['puddle', 'puddle', 'rubble'], puddle=(90, 200, 70), moss=True,
         banner=(70, 130, 50)),
    dict(floor=(72, 60, 76),  wall=(106, 84, 112), top=(30, 20, 36), light=(235, 150, 255), ambient=(12, 4, 18),
         dark=216, mote=(230, 190, 255), decor=['web', 'web', 'bones', 'rubble'], puddle=(120, 70, 150), moss=False,
         banner=(110, 50, 130)),
    dict(floor=(88, 68, 50),  wall=(128, 96, 68),  top=(36, 26, 18), light=(255, 150, 60),  ambient=(14, 6, 2),
         dark=210, mote=(255, 200, 140), decor=['bones', 'rubble', 'bones', 'blood'], puddle=(120, 40, 30), moss=False,
         banner=(160, 70, 30)),
    dict(floor=(96, 92, 80),  wall=(146, 136, 114), top=(42, 40, 34), light=(255, 225, 150), ambient=(10, 8, 6),
         dark=214, mote=(240, 230, 200), decor=['bones', 'bones', 'bones', 'rubble', 'web'], puddle=(90, 90, 80), moss=False,
         banner=(190, 170, 120)),
    dict(floor=(54, 60, 90),  wall=(84, 96, 140),  top=(18, 20, 42), light=(150, 190, 255), ambient=(4, 6, 20),
         dark=218, mote=(170, 200, 255), decor=['bones', 'rune', 'rubble', 'web'], puddle=(70, 100, 190), moss=False,
         banner=(70, 90, 190)),
    dict(floor=(72, 44, 80),  wall=(114, 62, 116), top=(32, 14, 38), light=(255, 100, 220), ambient=(14, 2, 18),
         dark=218, mote=(255, 150, 240), decor=['rune', 'rune', 'blood', 'bones'], puddle=(150, 30, 90), moss=False,
         banner=(170, 40, 140)),
    dict(floor=(76, 46, 42),  wall=(124, 64, 50),  top=(36, 16, 14), light=(255, 110, 40),  ambient=(18, 4, 2),
         dark=214, mote=(255, 150, 70), decor=['lava', 'lava', 'rubble', 'bones'], puddle=(255, 110, 30), moss=False,
         banner=(200, 60, 20)),
    dict(floor=(52, 48, 62),  wall=(124, 106, 74), top=(26, 22, 20), light=(255, 210, 100), ambient=(12, 4, 18),
         dark=220, mote=(255, 230, 160), decor=['rune', 'bones', 'blood', 'rubble'], puddle=(120, 40, 160), moss=False,
         banner=(200, 160, 50)),
    dict(floor=(78, 92, 110), wall=(150, 190, 220), top=(36, 48, 66), light=(170, 225, 255), ambient=(4, 10, 22),
         dark=212, mote=(220, 240, 255), decor=['bones', 'puddle', 'rubble', 'web'], puddle=(150, 210, 245), moss=False,
         banner=(90, 150, 210)),
    dict(floor=(40, 76, 80),  wall=(60, 130, 130), top=(10, 34, 36), light=(110, 255, 230), ambient=(2, 14, 16),
         dark=218, mote=(130, 255, 235), decor=['puddle', 'puddle', 'puddle', 'rune', 'rubble'], puddle=(40, 190, 190), moss=True,
         banner=(30, 140, 140)),
    dict(floor=(62, 52, 86),  wall=(100, 70, 130), top=(24, 16, 40), light=(120, 255, 170), ambient=(6, 8, 20),
         dark=218, mote=(150, 255, 190), decor=['puddle', 'web', 'rubble', 'bones'], puddle=(90, 230, 130), moss=True,
         banner=(80, 170, 110)),
    dict(floor=(70, 74, 44),  wall=(112, 120, 62), top=(30, 32, 16), light=(215, 245, 110), ambient=(8, 12, 2),
         dark=216, mote=(220, 240, 130), decor=['bones', 'blood', 'rubble', 'web', 'puddle'], puddle=(140, 170, 40), moss=True,
         banner=(150, 160, 50)),
    dict(floor=(60, 70, 108), wall=(118, 140, 200), top=(22, 26, 56), light=(140, 230, 255), ambient=(4, 8, 26),
         dark=220, mote=(190, 235, 255), decor=['rune', 'rune', 'bones', 'puddle'], puddle=(110, 190, 255), moss=False,
         banner=(110, 170, 240)),
    dict(floor=(52, 46, 48),  wall=(88, 72, 72),  top=(22, 18, 20), light=(255, 120, 40), ambient=(14, 4, 2),
         dark=216, mote=(255, 160, 70), decor=['lava', 'lava', 'rubble', 'rubble'], puddle=(255, 130, 30), moss=False,
         banner=(220, 90, 20)),
    dict(floor=(80, 36, 46),  wall=(140, 54, 66), top=(38, 12, 18), light=(255, 80, 90), ambient=(16, 2, 6),
         dark=218, mote=(255, 120, 130), decor=['blood', 'blood', 'rune', 'bones'], puddle=(190, 20, 40), moss=False,
         banner=(190, 30, 50)),
    dict(floor=(38, 34, 54),  wall=(66, 56, 90),  top=(14, 10, 24), light=(190, 140, 255), ambient=(6, 2, 14),
         dark=226, mote=(190, 160, 255), decor=['web', 'rune', 'bones', 'rubble'], puddle=(90, 60, 150), moss=False,
         banner=(100, 70, 170)),
    dict(floor=(70, 66, 66),  wall=(110, 102, 98), top=(30, 26, 26), light=(255, 150, 90), ambient=(12, 6, 4),
         dark=218, mote=(255, 190, 130), decor=['rubble', 'rubble', 'bones', 'lava', 'blood'], puddle=(210, 90, 40), moss=False,
         banner=(190, 100, 50)),
    dict(floor=(44, 30, 40),  wall=(150, 60, 40), top=(20, 10, 14), light=(255, 90, 40), ambient=(16, 2, 4),
         dark=222, mote=(255, 140, 60), decor=['lava', 'rune', 'blood', 'bones', 'lava'], puddle=(255, 70, 20), moss=False,
         banner=(230, 50, 30)),
]


def biome(floor):
    return BIOMES[min(max(floor, 1), len(BIOMES)) - 1]


def floor_name(floor):
    return FLOOR_NAMES[min(max(floor, 1), len(FLOOR_NAMES)) - 1]
