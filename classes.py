"""classes.py - the hero classes and their abilities.
Want a new class? Copy one of the entries below and change the numbers!

growth = (health, damage) the hero gets AUTOMATICALLY every time they level up."""

UNLOCK_LEVELS = [1, 3, 5]          # ability slot 1, 2, 3 unlock at these levels
CLASS_ORDER = ['knight', 'mage', 'rogue', 'cleric', 'necromancer', 'beastmaster', 'monk']

CLASSES = {
    'knight': dict(
        name='Knight', short='Knight', title='The Knight', color=(90, 140, 230),
        blurb='Tough and steady. Fights up close with a big sword.',
        hp=75, dmg=12, speed=170, crit=0.08, atk='melee', atk_cd=0.38, reach=34, hitsize=66,
        dash_cd=0.9, potion_frac=0.40, growth=(12, 2), role='Melee tank',
        palette=dict(armor=(70, 120, 210), trim=(55, 100, 190), legs=(70, 60, 95), helm=(150, 155, 172),
                     plume=(200, 40, 50), head='helmet', weapon='sword'),
        abilities=['whirlwind', 'shield_wall', 'ground_slam']),
    'mage': dict(
        name='Ghala the Mage', short='Ghala', title='Ghala the Mage', color=(255, 125, 195),
        blurb='Fragile but deadly. Shoots pink magic from far away.',
        hp=45, dmg=11, speed=165, crit=0.10, atk='ranged', atk_cd=0.42, reach=0, hitsize=0,
        dash_cd=0.9, potion_frac=0.40, growth=(7, 2), role='Ranged caster',
        bolt=(255, 140, 210), bolt_kind='magic',
        palette=dict(armor=(240, 100, 170), trim=(212, 70, 145), legs=(125, 50, 95), helm=(255, 130, 190),
                     plume=None, head='hat', weapon='staff', orb=(255, 185, 235)),
        abilities=['frozen_heart', 'flower_ring', 'chain_lightning']),
    'rogue': dict(
        name='Rogue', short='Rogue', title='The Rogue', color=(90, 200, 120),
        blurb='Super fast with sneaky tricks and lots of critical hits.',
        hp=55, dmg=8, speed=200, crit=0.22, atk='melee', atk_cd=0.22, reach=30, hitsize=56,
        dash_cd=0.55, potion_frac=0.40, growth=(9, 2), role='Fast assassin',
        palette=dict(armor=(50, 95, 62), trim=(40, 72, 50), legs=(40, 40, 48), helm=(45, 78, 58),
                     plume=None, head='hood', weapon='dagger'),
        abilities=['knives', 'shadow_strike', 'poison_bomb']),
    'cleric': dict(
        name='Cleric', short='Cleric', title='The Cleric', color=(250, 220, 110),
        blurb='A holy healer. Smashes foes with a mace and can heal herself.',
        hp=65, dmg=10, speed=170, crit=0.08, atk='melee', atk_cd=0.46, reach=38, hitsize=80,
        dash_cd=0.9, potion_frac=0.50, growth=(10, 2), role='Melee healer',
        palette=dict(armor=(235, 235, 242), trim=(240, 210, 90), legs=(200, 190, 170), helm=(240, 210, 90),
                     plume=None, head='helmet', weapon='mace'),
        abilities=['smite', 'heal', 'holy_nova']),
    'necromancer': dict(
        name='Necromancer', short='Necro', title='The Necromancer', color=(150, 120, 235),
        blurb='Raises the DEAD to fight for you. Every kill heals a little.',
        hp=50, dmg=10, speed=165, crit=0.08, atk='ranged', atk_cd=0.45, reach=0, hitsize=0,
        dash_cd=0.9, potion_frac=0.40, growth=(7, 2), role='Summoner (undead)',
        bolt=(130, 255, 160), bolt_kind='magic', kill_heal=3,
        palette=dict(armor=(62, 42, 92), trim=(110, 240, 150), legs=(40, 28, 60), helm=(46, 32, 70),
                     plume=None, head='hood', weapon='skullstaff', face='dark', robe=True, orb=(130, 255, 160)),
        abilities=['raise_dead', 'corpse_explosion', 'army_of_dead']),
    'beastmaster': dict(
        name='Beastmaster', short='Beastmaster', title='The Beastmaster', color=(235, 150, 70),
        blurb='Calls wild BEASTS to fight beside you: wolves, a hawk and a bear!',
        hp=60, dmg=9, speed=175, crit=0.08, atk='ranged', atk_cd=0.38, reach=0, hitsize=0,
        dash_cd=0.9, potion_frac=0.40, growth=(9, 2), role='Summoner (beasts)',
        bolt=(235, 205, 150), bolt_kind='arrow',
        palette=dict(armor=(150, 100, 60), trim=(115, 78, 46), legs=(85, 64, 48), helm=(96, 134, 72),
                     plume=None, head='hood', weapon='bow', collar=(235, 225, 200), feather=(220, 70, 60)),
        abilities=['summon_wolves', 'summon_hawk', 'summon_bear']),
    'monk': dict(
        name='Monk', short='Monk', title='The Monk', color=(255, 150, 70),
        blurb='A fast martial artist. Throws an orb that sticks to a foe, then launches in to finish them.',
        hp=62, dmg=10, speed=190, crit=0.14, atk='melee', atk_cd=0.3, reach=28, hitsize=58,
        dash_cd=0.75, potion_frac=0.40, growth=(9, 2), role='Mobile brawler',
        palette=dict(armor=(222, 142, 58), trim=(150, 90, 40), legs=(70, 55, 40), helm=(90, 60, 40),
                     plume=(205, 55, 45), head='hood', weapon='fists', robe=True, wraps=(235, 225, 205)),
        abilities=['sky_strike', 'tempest_kick', 'dragons_kick']),
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
    # --- Cleric
    'smite': dict(name='Smite', cd=6, color=(255, 225, 110), icon='smite',
                  desc='Holy lightning strikes the 3 nearest monsters.'),
    'heal': dict(name='Heal', cd=12, color=(110, 255, 150), icon='heal',
                 desc='Heal 35% of your maximum health.'),
    'holy_nova': dict(name='Holy Nova', cd=10, color=(255, 240, 170), icon='nova',
                      desc='A burst of light that blasts monsters away.'),
    # --- Necromancer
    'raise_dead': dict(name='Raise Dead', cd=7, color=(130, 255, 160), icon='raise',
                       desc='Raise up to 3 fallen monsters near you as undead allies.'),
    'corpse_explosion': dict(name='Corpse Explosion', cd=8, color=(180, 255, 120), icon='corpse',
                             desc='Blow up every corpse nearby. Big damage to monsters around them!'),
    'army_of_dead': dict(name='Army of the Dead', cd=26, color=(150, 140, 255), icon='army',
                         desc='Call 5 skeleton warriors out of the ground for 18 seconds.'),
    # --- Beastmaster
    'summon_wolves': dict(name='Summon Wolves', cd=9, color=(190, 195, 215), icon='wolf',
                          desc='Call 2 fast wolves. They stay until they fall (max 4).'),
    'summon_hawk': dict(name='Summon Hawk', cd=12, color=(225, 170, 90), icon='hawk',
                        desc='A hawk that dive-bombs monsters from above (max 2).'),
    'summon_bear': dict(name='Summon Bear', cd=22, color=(205, 140, 80), icon='bear',
                        desc='A huge bear that stuns nearby monsters with a roar (max 1).'),
    # --- Monk
    'sky_strike': dict(name='Sky Strike', cd=6, color=(255, 235, 150), icon='fist',
                       desc='Throw an orb that sticks to the first monster it hits (light damage). '
                            'Use again within 4 seconds to LAUNCH yourself at it and strike hard - '
                            'landing the jump cuts the cooldown in half!'),
    'tempest_kick': dict(name='Tempest Kick', cd=9, color=(255, 170, 90), icon='tempest',
                         desc='A spinning kick that hits and knocks back every monster around you.'),
    'dragons_kick': dict(name="Dragon's Kick", cd=13, color=(255, 120, 60), icon='kick',
                        desc='Grab the nearest monster and kick it away hard, blasting anything it crashes into.'),
}
