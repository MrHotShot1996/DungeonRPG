"""classes.py - the hero classes and their abilities.
Want a new class? Copy one of the entries below and change the numbers!

growth = (health, damage) the hero gets AUTOMATICALLY every time they level up."""

UNLOCK_LEVELS = [1, 3, 5]          # ability slot 1, 2, 3 unlock at these levels
NO_DAMAGE = ('shield_wall', 'living_shadow')   # ranking these up only shortens their cooldown
ULT_UNLOCK = 8                     # a hero's ULTIMATE (4th ability, the 'ultimate' key) unlocks at this level
ULT_MAX_RANK = 3                   # ...and can be ranked up to this


def slot_names(cls):
    """A hero's ability names, in key order: abilities 1-3, then the ultimate if the hero has one."""
    c = CLASSES[cls]
    return c['abilities'] + ([c['ult']] if c.get('ult') else [])


def unlock_level(slot):
    return UNLOCK_LEVELS[slot] if slot < 3 else ULT_UNLOCK


def slot_key(slot):
    """The input action that uses ability `slot`."""
    return f'ability{slot + 1}' if slot < 3 else 'ultimate'
CLASS_ORDER = ['knight', 'mage', 'rogue', 'necromancer', 'monk', 'swordsman', 'vampire', 'ninja', 'explorer', 'wanderer']

CLASSES = {
    'knight': dict(
        name='Knight', short='Knight', title='The Knight', color=(90, 140, 230),
        blurb='Tough and steady. Fights up close with a big sword.',
        hp=75, dmg=12, speed=170, crit=0.08, atk='melee', atk_cd=0.38, reach=34, hitsize=66,
        growth=(12, 2), role='Melee tank',
        palette=dict(armor=(70, 120, 210), trim=(55, 100, 190), legs=(70, 60, 95), helm=(150, 155, 172),
                     plume=(200, 40, 50), head='helmet', weapon='sword'),
        abilities=['whirlwind', 'shield_wall', 'ground_slam']),
    'mage': dict(
        name='Ghala the Mage', short='Ghala', title='Ghala the Mage', color=(255, 125, 195),
        blurb='Fragile but deadly. Shoots pink magic from far away.',
        hp=45, dmg=11, speed=165, crit=0.10, atk='ranged', atk_cd=0.42, reach=0, hitsize=0,
        growth=(7, 2), role='Ranged caster',
        bolt=(255, 140, 210), bolt_kind='magic',
        palette=dict(armor=(240, 100, 170), trim=(212, 70, 145), legs=(125, 50, 95), helm=(255, 130, 190),
                     plume=None, head='hat', weapon='staff', orb=(255, 185, 235)),
        abilities=['frozen_heart', 'flower_ring', 'chain_lightning']),
    'rogue': dict(
        name='Rogue', short='Rogue', title='The Rogue', color=(90, 200, 120),
        blurb='Super fast with sneaky tricks and lots of critical hits.',
        hp=55, dmg=8, speed=200, crit=0.22, atk='melee', atk_cd=0.22, reach=30, hitsize=56,
        growth=(9, 2), role='Fast assassin',
        palette=dict(armor=(50, 95, 62), trim=(40, 72, 50), legs=(40, 40, 48), helm=(45, 78, 58),
                     plume=None, head='hood', weapon='dagger'),
        abilities=['knives', 'shadow_strike', 'poison_bomb']),
    'necromancer': dict(
        name='Necromancer', short='Necro', title='The Necromancer', color=(150, 120, 235),
        blurb='Raises the DEAD to fight for you. Every kill heals a little.',
        hp=50, dmg=10, speed=165, crit=0.08, atk='ranged', atk_cd=0.45, reach=0, hitsize=0,
        growth=(7, 2), role='Summoner (undead)',
        bolt=(130, 255, 160), bolt_kind='magic', kill_heal=3,
        palette=dict(armor=(62, 42, 92), trim=(110, 240, 150), legs=(40, 28, 60), helm=(46, 32, 70),
                     plume=None, head='hood', weapon='skullstaff', face='dark', robe=True, orb=(130, 255, 160)),
        abilities=['raise_dead', 'corpse_explosion', 'army_of_dead']),
    'monk': dict(
        name='Monk', short='Monk', title='The Monk', color=(255, 150, 70),
        blurb='A fast martial artist. Throws an orb that sticks to a foe, then launches in to finish them.',
        hp=62, dmg=10, speed=190, crit=0.14, atk='melee', atk_cd=0.3, reach=28, hitsize=58,
        growth=(9, 2), role='Mobile brawler',
        palette=dict(armor=(222, 142, 58), trim=(150, 90, 40), legs=(70, 55, 40), helm=(90, 60, 40),
                     plume=(205, 55, 45), head='hood', weapon='fists', robe=True, wraps=(235, 225, 205)),
        abilities=['sky_strike', 'tempest_kick', 'dragons_kick']),
    'swordsman': dict(
        name='Swordsman', short='Swordsman', title='The Exiled Swordsman', color=(150, 230, 245),
        blurb='An exile with a growing blade. Chains 3 swipes and stuns with a shout.',
        hp=66, dmg=11, speed=180, crit=0.12, atk='melee', atk_cd=0.34, reach=34, hitsize=66,
        growth=(10, 2), role='Combo fighter',
        palette=dict(armor=(88, 96, 116), trim=(60, 66, 84), legs=(52, 50, 64), helm=(58, 44, 40),
                     plume=None, head='helmet', weapon='sword', collar=(200, 55, 60)),
        abilities=['triple_slash', 'war_cry', 'greatblade']),
    'vampire': dict(
        name='Vampire Lord', short='Vampire', title='The Vampire Lord', color=(235, 70, 95),
        blurb='Spends blood to gain blood. Drains foes, then floods them with blood',
        hp=54, dmg=10, speed=170, crit=0.08, atk='ranged', atk_cd=0.42, reach=0, hitsize=0,
        growth=(8, 2), role='Blood caster',
        bolt=(225, 40, 65), bolt_kind='magic',
        palette=dict(armor=(74, 18, 32), trim=(190, 30, 55), legs=(34, 22, 30), helm=(30, 24, 34),
                     plume=None, head='helmet', weapon='orb', robe=True, orb=(235, 45, 70),
                     collar=(150, 20, 40), skin=(226, 222, 234)),
        abilities=['blood_drain', 'blood_pool', 'tides_of_blood'], ult='blood_curse'),
    'ninja': dict(
        name='Shadow Ninja', short='Ninja', title='The Shadow Ninja', color=(200, 208, 235),
        blurb='A silent assassin with a living SHADOW that copies his moves.',
        hp=52, dmg=9, speed=205, crit=0.20, atk='melee', atk_cd=0.24, reach=30, hitsize=58,
        growth=(8, 2), role='Shadow assassin',
        palette=dict(armor=(38, 38, 52), trim=(78, 80, 104), legs=(28, 28, 40), helm=(32, 32, 46),
                     plume=None, head='hood', weapon='dagger', face='dark', orb=(255, 70, 80),
                     collar=(190, 40, 55)),
        abilities=['shadow_shuriken', 'living_shadow', 'shadow_slash'], ult='death_mark'),
    'explorer': dict(
        name='Arcane Explorer', short='Explorer', title='The Arcane Explorer', color=(255, 214, 90),
        blurb='A daring treasure hunter whose golden gauntlet shoots arcane bolts.',
        hp=48, dmg=10, speed=190, crit=0.12, atk='ranged', atk_cd=0.34, reach=0, hitsize=0,
        growth=(7, 2), role='Ranged marksman',
        bolt=(255, 225, 110), bolt_kind='mystic',
        palette=dict(armor=(52, 92, 168), trim=(214, 170, 70), legs=(92, 70, 52), helm=(246, 214, 120),
                     plume=None, head='hair', weapon='gauntlet', orb=(255, 228, 120)),
        abilities=['essence_wave', 'arcane_shift', 'trueshot']),
    'wanderer': dict(
        name='Wanderer', short='Wanderer', title='The Wanderer', color=(150, 215, 255),
        blurb='A wind swordsman. Throws tornados, blocks arrows, and keeps foes up in the air.',
        hp=56, dmg=10, speed=195, crit=0.15, atk='melee', atk_cd=0.3, reach=34, hitsize=62,
        growth=(9, 2), role='Wind swordsman',
        palette=dict(armor=(54, 92, 150), trim=(225, 232, 242), legs=(40, 44, 62), helm=(46, 34, 30),
                     plume=None, head='topknot', weapon='katana', collar=(150, 190, 230)),
        abilities=['wind_thrust', 'gale_wall', 'cyclone_spin'], ult='storm_breaker'),
}

ABILITIES = {
    # --- Knight
    'whirlwind': dict(name='Whirlwind', cd=6, color=(220, 230, 255), icon='swirl',
                      desc='Spin your sword and hit every monster around you.'),
    'shield_wall': dict(name='Shield Wall', cd=14, color=(90, 160, 255), icon='shield',
                        desc='A magic shield blocks ALL damage for 2.5 seconds.'),
    'ground_slam': dict(name='Ground Slam', cd=12, color=(255, 170, 80), icon='slam',
                        desc='Smash the floor! Hurts and STUNS monsters nearby.'),
    # --- Mage
    'frozen_heart': dict(name='Frozen Heart', cd=5, color=(255, 120, 185), icon='heart',
                         desc='Throw a heart that hurts the first monster it hits and FREEZES it solid.'),
    'flower_ring': dict(name='Flower Ring', cd=11, color=(255, 150, 200), icon='flower',
                        desc='A ring of flowers spins around you for 6 seconds, hurting monsters it touches.'),
    'chain_lightning': dict(name='Chain Lightning', cd=9, color=(255, 240, 120), icon='bolt',
                            desc='Lightning that jumps between up to 5 monsters.'),
    # --- Rogue
    'knives': dict(name='Throwing Knives', cd=1, color=(205, 215, 225), icon='knives',
                   desc='Throw a fan of 5 sharp knives.'),
    'shadow_strike': dict(name='Shadow Strike', cd=2, color=(160, 110, 230), icon='step',
                          desc='Zip to a monster and stab it for triple damage!'),
    'poison_bomb': dict(name='Poison Bomb', cd=11, color=(110, 220, 90), icon='poison',
                        desc='A green cloud that poisons monsters for 6 seconds.'),
    # --- Necromancer
    'raise_dead': dict(name='Raise Dead', cd=7, color=(130, 255, 160), icon='raise',
                       desc='Raise up to 3 fallen monsters near you as undead allies.'),
    'corpse_explosion': dict(name='Corpse Explosion', cd=8, color=(180, 255, 120), icon='corpse',
                             desc='Blow up every corpse nearby. Big damage to monsters around them!'),
    'army_of_dead': dict(name='Army of the Dead', cd=26, color=(150, 140, 255), icon='army',
                         desc='Call 5 skeleton warriors out of the ground for 18 seconds.'),
    # --- Monk
    'sky_strike': dict(name='Sky Strike', cd=6, color=(255, 235, 150), icon='fist',
                       desc='Throw an orb that sticks to the first monster it hits (light damage). '
                            'Use again within 4 seconds to LAUNCH yourself at it and strike hard - '
                            'landing the jump cuts the cooldown in half!'),
    'tempest_kick': dict(name='Tempest Kick', cd=9, color=(255, 170, 90), icon='tempest',
                         desc='A spinning kick that hits and knocks back every monster around you.'),
    'dragons_kick': dict(name="Dragon's Kick", cd=13, color=(255, 120, 60), icon='kick',
                        desc='Kick the nearest monster FAR away. It flies in a straight line and damages every monster it crashes into on the way!'),
    # --- Swordsman
    'triple_slash': dict(name='Triple Slash', cd=7, color=(235, 240, 255), icon='trislash',
                         desc='Swipe the monsters in FRONT of you. Press again for 2 more swipes - '
                              'the third hits hardest!'),
    'war_cry': dict(name='War Cry', cd=9, color=(255, 225, 140), icon='warcry',
                    desc='A mighty shout that hurts and STUNS every monster around you for 1 second.'),
    'greatblade': dict(name='Greatblade', cd=24, color=(150, 235, 255), icon='blade',
                       desc='Bigger sword for 10 seconds: more damage and reach. '
                            'Press again to throw 3 blade waves where you point!'),
    # --- Vampire Lord
    'blood_drain': dict(name='Blood Drain', cd=4, color=(235, 60, 85), icon='drain',
                        desc='FREE. Suck blood from a monster in front of you: it is hurt and the blood heals you. '
                             'The lower your health, the more you drain (up to 3x the healing).'),
    'blood_pool': dict(name='Blood Pool', cd=16, color=(200, 40, 70), icon='pool',
                       desc='Costs 15% of your health. Sink into a pool of blood for 2.5s: you cannot be hurt, '
                            'monsters on it are hurt, and the blood flows back to heal you.'),
    'tides_of_blood': dict(name='Tides of Blood', cd=5, color=(240, 50, 80), icon='tides',
                           desc='Costs 7% of your health. Throw blood at EVERY monster around you. '
                                'Each one it hits gives blood back to heal you. Short cooldown!'),
    'blood_curse': dict(name='Blood Curse', cd=30, color=(255, 100, 100), icon='curse',
                        desc='ULTIMATE. Costs 10% of your health. Curse every monster in a big splash: they take 25% '
                             'more damage, then BURST after 4 seconds and heal you.'),
    # --- Wanderer
    'wind_thrust': dict(name='Wind Thrust', cd=2.5, color=(170, 225, 255), icon='thrust',
                        desc='A quick stab in front of you. Hit with 2 stabs and the NEXT one throws a TORNADO '
                             'that flies forward and knocks monsters into the air.'),
    'gale_wall': dict(name='Gale Wall', cd=18, color=(200, 240, 255), icon='windwall',
                      desc='Raise a wall of wind in front of you for 4 seconds. It blows away every monster shot '
                           'that tries to cross it.'),
    'cyclone_spin': dict(name='Cyclone Spin', cd=8, color=(140, 210, 255), icon='cyclone',
                         desc='Spin in place in a circle of wind: hurts every monster around you and knocks them '
                              'into the air.'),
    'storm_breaker': dict(name='Storm Breaker', cd=35, color=(120, 200, 255), icon='storm',
                          desc='ULTIMATE. Blink to a monster that is in the AIR and keep it - and every airborne '
                               'monster near it - up there while you slash them. You cannot be hurt meanwhile.'),
    # --- Shadow Ninja
    'shadow_shuriken': dict(name='Shadow Shuriken', cd=5, color=(185, 150, 255), icon='shuriken',
                            desc='Throw 3 spinning shurikens that fly THROUGH monsters. '
                                 'The first hit is the hardest - every hit after it does less.'),
    'living_shadow': dict(name='Living Shadow', cd=14, color=(150, 110, 235), icon='shadow',
                          desc='Throw your shadow forward for 5 seconds. It COPIES your other abilities! '
                               'Press again to swap places with it.'),
    'shadow_slash': dict(name='Shadow Slash', cd=6, color=(215, 190, 255), icon='swipe',
                         desc='Swipe your blades at every monster around you. '
                              'Your shadow swipes too, and SLOWS what it hits.'),
    'death_mark': dict(name='Death Mark', cd=32, color=(230, 60, 80), icon='deathmark',
                       desc='ULTIMATE: Vanish and strike the monster you aim at, leaving a shadow behind. '
                            'It is MARKED: damage you deal is stored, then it blows up. Press again to swap with the shadow.'),
    # --- Arcane Explorer
    'essence_wave': dict(name='Essence Wave', cd=6, color=(255, 214, 90), icon='crescent',
                         desc='A golden crescent that flies through monsters and MARKS them. '
                              'Hit a marked monster again to burst the mark.'),
    'arcane_shift': dict(name='Arcane Shift', cd=9, color=(120, 210, 255), icon='blink',
                         desc='Blink forward the way you face. Blasts monsters where you land '
                              'and fires a bolt at the nearest one.'),
    'trueshot': dict(name='Trueshot Barrage', cd=24, color=(255, 190, 70), icon='barrage',
                     desc='A HUGE crescent that flies through walls across the whole map. '
                          'Each monster after the first takes a bit less.'),
}
