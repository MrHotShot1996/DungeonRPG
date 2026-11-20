"""items.py - the SHOP items (a bit like League of Legends).

You carry up to 4 items. There are three sizes:
  * SMALL items      - cheap, one little stat.
  * COMPONENTS       - built from a small item + gold. One good stat.
  * MYTHIC items     - built from TWO components + gold. Two stats AND a special power.

There are 5 stats, so there are 5 small items, 5 components and 10 mythics (one for every pair of stats).
If you already carry the pieces, you only pay the difference - exactly like building an item in LoL.

Want to rebalance? Every number is in this file:
  PRICE_SMALL / PRICE_COMPONENT / PRICE_MYTHIC, the stat tables just below, and the MYTHIC_* numbers.
"""

MAX_SLOTS = 4
SELL_BACK = 0.6                 # selling gives back this much of what the item is worth

# ---- prices (the TOTAL worth of an item; you pay less if you already carry its pieces)
PRICE_SMALL = 100
PRICE_COMPONENT = 400           # = its small item (100) + 300
PRICE_MYTHIC = 2200             # = two components (800) + 1400

# ---- the 5 stats. Numbers are PERCENT.
#   atk = basic attack damage     ap  = ability damage      cdr = shorter ability cooldowns
#   ls  = life steal (basic attacks heal you for this much of their damage)
#   df  = defense (you take this much less damage)
STATS = ('atk', 'ap', 'cdr', 'ls', 'df')
STAT_NAME = {'atk': 'Attack damage', 'ap': 'Ability damage', 'cdr': 'Cooldown reduction', 'ls': 'Life steal',
             'df': 'Defense'}
STAT_COLOR = {'atk': (255, 150, 80), 'ap': (150, 140, 255), 'cdr': (110, 220, 235), 'ls': (240, 80, 110),
              'df': (150, 205, 130)}
SMALL_STAT = {'atk': 6, 'ap': 6, 'cdr': 4, 'ls': 3, 'df': 5}
COMPONENT_STAT = {'atk': 15, 'ap': 16, 'cdr': 8, 'ls': 6, 'df': 10}
MYTHIC_STAT = {'atk': 22, 'ap': 25, 'cdr': 10, 'ls': 8, 'df': 12}
STAT_CAP = {'cdr': 35, 'ls': 25, 'df': 40}      # you can never go above these, whatever you carry

# ---- the mythic powers' numbers
MYTHIC_SPELLBLADE_BONUS = 0.60      # Arcane Edge: the empowered attack does this much MORE damage
MYTHIC_SPELLBLADE_TIME = 4.0        # ...if you attack within this many seconds of using an ability
MYTHIC_TEMPO_REFUND = 0.25          # Tempo Blade: seconds taken off your cooldowns per attack that hits
MYTHIC_REAVER_HP = 0.40             # Crimson Reaver: life steal is doubled below this much health
MYTHIC_TITAN_HP = 0.02              # Titan's Maul: attacks do extra damage = this much of your MAX health
MYTHIC_ECHO_POWER = 0.8             # Echo Staff: the blast is this strong (1.0 = one basic attack)
MYTHIC_ECHO_RADIUS = 90
MYTHIC_ECHO_CD = 6.0                # ...and can happen once every this many seconds
MYTHIC_SOUL_HEAL = 0.05             # Soul Drinker: abilities heal you for this much of their damage
ABILITY_LS_SPLASH = 1 / 3           # ...but only ONE ability hit every ABILITY_LS_WINDOW s heals fully: the rest of an
ABILITY_LS_WINDOW = 0.2             #    area attack / volley heals at a third (like League's 'area' life steal)
ABILITY_LS_DOT = 1 / 3              # ...and poison / damage over time heals at a third too
ABILITY_LS_RATE = 0.02              # ALL life stolen by abilities (Soul Drinker, Blood Drain, Blood Curse) is capped:
ABILITY_LS_STORE = 0.12             #    2% of your max health per second, saved up to 12% (so a big hit after a pause
                                    #    still heals well, but nonstop fights can't refill you over and over)
MYTHIC_FROST_SLOW = 1.2             # Frost Aegis: seconds your abilities slow monsters
MYTHIC_REAPER_REFUND = 0.5          # Reaper's Hourglass: seconds off your cooldowns per kill
MYTHIC_REAPER_HEAL = 0.02           # ...and this much of your max health healed per kill
MYTHIC_GUARD_HP = 0.30              # Guardian Clock: the shield pops when you fall below this much health
MYTHIC_GUARD_TIME = 2.0             # ...blocks everything for this many seconds
MYTHIC_GUARD_CD = 60.0              # ...and needs this long to recharge
MYTHIC_THORNS = 1.0                 # Bramble Heart: monsters that hit you up close take this many basic attacks back

_SMALL = {'atk': ('rusty_dagger', 'Rusty Dagger'), 'ap': ('apprentice_wand', 'Apprentice Wand'),
          'cdr': ('pocket_sand', 'Pocket Hourglass'), 'ls': ('leech_fang', 'Leech Fang'),
          'df': ('leather_vest', 'Leather Vest')}
_COMPONENT = {'atk': ('warblade', 'Warblade'), 'ap': ('arcane_tome', 'Arcane Tome'),
              'cdr': ('timekeeper', "Timekeeper's Clock"), 'ls': ('vampire_fang', 'Vampire Fang'),
              'df': ('iron_plate', 'Iron Plate')}
_MYTHIC = [   # (id, name, stat A, stat B, power id, what the power does)
    ('arcane_edge', 'Arcane Edge', 'atk', 'ap', 'spellblade',
     f'After you use an ability, your next basic attack deals {int(MYTHIC_SPELLBLADE_BONUS * 100)}% more damage.'),
    ('tempo_blade', 'Tempo Blade', 'atk', 'cdr', 'tempo',
     f'Every basic attack that hits takes {MYTHIC_TEMPO_REFUND:g}s off your ability cooldowns.'),
    ('crimson_reaver', 'Crimson Reaver', 'atk', 'ls', 'reaver',
     f'Your life steal is DOUBLED while you are below {int(MYTHIC_REAVER_HP * 100)}% health.'),
    ('titans_maul', "Titan's Maul", 'atk', 'df', 'titan',
     f'Basic attacks deal extra damage equal to {int(MYTHIC_TITAN_HP * 100)}% of your max health.'),
    ('echo_staff', 'Echo Staff', 'ap', 'cdr', 'echo',
     f'Every {MYTHIC_ECHO_CD:g}s, your next ability hit blasts every monster around the target.'),
    ('soul_drinker', 'Soul Drinker', 'ap', 'ls', 'soul',
     f'Your abilities heal you for {int(MYTHIC_SOUL_HEAL * 100)}% of the damage they deal '
     f'(a third for extra targets and poison).'),
    ('frost_aegis', 'Frost Aegis', 'ap', 'df', 'frost',
     f'Your abilities SLOW the monsters they hit for {MYTHIC_FROST_SLOW:g}s.'),
    ('reapers_hourglass', "Reaper's Hourglass", 'cdr', 'ls', 'reaper',
     f'Every kill takes {MYTHIC_REAPER_REFUND:g}s off your cooldowns and heals {int(MYTHIC_REAPER_HEAL * 100)}% of your health.'),
    ('guardian_clock', 'Guardian Clock', 'cdr', 'df', 'guard',
     f'Falling below {int(MYTHIC_GUARD_HP * 100)}% health gives you a shield that blocks everything for '
     f'{MYTHIC_GUARD_TIME:g}s (once every {MYTHIC_GUARD_CD:g}s).'),
    ('bramble_heart', 'Bramble Heart', 'ls', 'df', 'thorns',
     'Monsters that hit you up close take a full basic attack of damage back.'),
]

ITEMS = {}          # id -> dict(name, tier, stats, recipe, price, power, desc)
SMALLS, COMPONENTS, MYTHICS = [], [], []
for _s in STATS:
    _id, _name = _SMALL[_s]
    ITEMS[_id] = dict(id=_id, name=_name, tier=1, stats={_s: SMALL_STAT[_s]}, recipe=(), price=PRICE_SMALL,
                      power=None, desc='')
    SMALLS.append(_id)
for _s in STATS:
    _id, _name = _COMPONENT[_s]
    ITEMS[_id] = dict(id=_id, name=_name, tier=2, stats={_s: COMPONENT_STAT[_s]}, recipe=(_SMALL[_s][0],),
                      price=PRICE_COMPONENT, power=None, desc='')
    COMPONENTS.append(_id)
for _id, _name, _a, _b, _power, _desc in _MYTHIC:
    ITEMS[_id] = dict(id=_id, name=_name, tier=3, stats={_a: MYTHIC_STAT[_a], _b: MYTHIC_STAT[_b]},
                      recipe=(_COMPONENT[_a][0], _COMPONENT[_b][0]), price=PRICE_MYTHIC, power=_power, desc=_desc)
    MYTHICS.append(_id)
SHOP_ROWS = [SMALLS, COMPONENTS, MYTHICS[:5], MYTHICS[5:]]      # how the shop screen lays them out
TIER_NAME = {1: 'Small item', 2: 'Component', 3: 'MYTHIC'}


def combine_cost(item_id):
    """The gold you add on top of an item's pieces to build it."""
    it = ITEMS[item_id]
    return it['price'] - sum(ITEMS[r]['price'] for r in it['recipe'])


def _use_pieces(item_id, pool):
    """Take the pieces of `item_id` out of `pool` (a list of carried item ids). Returns the gold they are worth.
    If a component is missing but its small item is carried, the small item is used instead."""
    credit = 0
    for part in ITEMS[item_id]['recipe']:
        if part in pool:
            pool.remove(part)
            credit += ITEMS[part]['price']
        else:
            credit += _use_pieces(part, pool)
    return credit


def plan(owned, item_id):
    """What buying `item_id` would do. Returns (cost, items_after, problem).
    `problem` is None if you may buy it, or a short message saying why not (cost is still filled in)."""
    pool = list(owned)
    cost = ITEMS[item_id]['price'] - _use_pieces(item_id, pool)
    after = pool + [item_id]
    if item_id in owned:
        return cost, after, "You already carry this"
    if len(after) > MAX_SLOTS:
        return cost, after, "No free slot - sell something first"
    return cost, after, None


def sell_value(item_id):
    return int(ITEMS[item_id]['price'] * SELL_BACK)


def total_stats(owned):
    """Add up the stats of everything carried (with the caps). Returns {'atk': %, 'ap': %, ...}."""
    out = dict.fromkeys(STATS, 0)
    for i in owned:
        for k, v in ITEMS[i]['stats'].items():
            out[k] += v
    for k, cap in STAT_CAP.items():
        out[k] = min(out[k], cap)
    return out


def powers(owned):
    """The set of mythic powers the carried items give."""
    return {ITEMS[i]['power'] for i in owned if ITEMS[i]['power']}


def builds_into(item_id):
    """The items that use `item_id` as a piece."""
    return [k for k, it in ITEMS.items() if item_id in it['recipe']]


def stat_line(item_id):
    """'+22% Attack damage, +12% Defense'"""
    return ',  '.join(f"+{v}% {STAT_NAME[k]}" for k, v in ITEMS[item_id]['stats'].items())
