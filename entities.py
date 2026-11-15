"""entities.py - the living (and flying) things: the hero, monsters, ALLIES, spells, loot, sparkles."""
import math
import random
import pygame
from settings import (TILE, ENEMY_HP_MULT, ENEMY_DMG_MULT, ENEMY_SPEED_MULT, BOSS_HP_MULT, BOSS_DMG_MULT,
                      HURT_INVULN, XP_MULT)
from classes import CLASSES
from ai import smarts_for, memory_time, lunge_lead
import items as IT

V2 = pygame.Vector2
BOSS_KINDS = ('boss', 'warlord', 'lich', 'demon')


def xp_for(level):
    """How much XP you need to get from `level` to the next one."""
    return 25 + level * 18 + level * level * 2


class Entity:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = float(x), float(y), int(w), int(h)

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2), self.w, self.h)

    def move(self, dx, dy, dungeon):
        """Move one direction at a time so we can slide along walls."""
        if dx:
            self.x += dx
            if dungeon.hits_wall(self.rect):
                self.x -= dx
        if dy:
            self.y += dy
            if dungeon.hits_wall(self.rect):
                self.y -= dy


# ====================================================================== PLAYER
class Player(Entity):
    def __init__(self, cls='knight'):
        super().__init__(0, 0, 22, 22)
        c = CLASSES[cls]
        self.cls = cls
        self.max_hp = self.hp = c['hp']
        self.dmg, self.speed, self.crit = c['dmg'], c['speed'], c['crit']
        self.dash_cd_base = c['dash_cd']
        self.kill_heal = c.get('kill_heal', 0)
        self.heal_bank = 0.0         # every kill adds a sliver of health here; whole points get paid out
        self.cd_mult, self.ap = 1.0, 1.0
        self.level, self.xp = 1, 0
        self.xp_next = xp_for(1)
        self.face = V2(0, 1)
        self.attack_cd = self.swing = self.invuln = 0.0
        self.dash_t = self.dash_cd = 0.0
        self.dash_vec = V2(0, 0)
        self.kx = self.ky = 0.0
        self.gold, self.kills = 0, 0
        self.combo = 0               # Swordsman: how many Triple Slash swipes have been done so far
        self.blade_wave = False      # Swordsman: True while the Greatblade recast (blade waves) is unused
        self.pool_tick = 0.0         # Vampire Lord: time until the Blood Pool hurts monsters again
        self.pooled = False          # ...and whether we were in the pool last frame (to pop back out)
        self.ability_cd = [0.0, 0.0, 0.0]
        self.ability_max = [1.0, 1.0, 1.0]
        self.buffs = {}
        self.items = []              # the shop items you carry (ids from items.py), at most 4
        self.istat = IT.total_stats(self.items)      # ...their stats added up, in percent
        self.ipow = set()            # ...and the mythic powers they give
        self.ls_bank = 0.0           # life steal smaller than 1 HP is saved up here
        self.echo_cd = self.guard_cd = self.tempo_cd = 0.0     # mythic power timers
        self.sky_mark_enemy = None   # Monk's Sky Strike mark: the monster the orb is stuck to
        self.launch, self.launch_t = None, 0.0   # ...and the monster we are FLYING at after the recast
        self.slow_t = 0.0
        self.spin = 0.0
        self.hurt_flash = 0.0
        self.anim = 0.0
        self.moving = False

    def refresh_items(self):
        """Call after `self.items` changes: adds up the stats and powers again."""
        self.istat = IT.total_stats(self.items)
        self.ipow = IT.powers(self.items)

    @property
    def dir_name(self):
        if abs(self.face.x) > abs(self.face.y):
            return 'right' if self.face.x > 0 else 'left'
        return 'down' if self.face.y > 0 else 'up'

    def update(self, dt, inp, game):
        """`inp` is the Input object (keyboard + controller). It tells us where to walk, aim and what's held."""
        for name in ('attack_cd', 'swing', 'invuln', 'dash_cd', 'slow_t', 'spin', 'hurt_flash',
                     'echo_cd', 'guard_cd', 'tempo_cd'):
            setattr(self, name, max(0.0, getattr(self, name) - dt))
        for i in range(3):
            self.ability_cd[i] = max(0.0, self.ability_cd[i] - dt)
        for k in list(self.buffs):
            self.buffs[k] -= dt
            if self.buffs[k] <= 0:
                del self.buffs[k]

        if self.launch_t > 0:                        # Monk mid-flight: nothing else until we land
            self.fly_to_mark(dt, game)
            return

        pooled = self.buffs.get('pool', 0) > 0       # Vampire Lord sunk into the Blood Pool: can't be hurt,
        if pooled:                                   # but can't attack or dash either (walking is fine)
            self.invuln = max(self.invuln, 0.12)
        sp = self.speed * (0.5 if self.slow_t > 0 else 1.0)
        vec = inp.move_vector()                      # length 0..1  (a gentle stick push = a slow walk)
        self.moving = vec.length_squared() > 0.0004
        if self.moving:
            self.face = V2(vec).normalize()
            self.anim += dt * max(0.5, min(1.0, vec.length()))
        aim = inp.aim_vector()                       # right stick: face where you point it
        if aim is not None:
            self.face = V2(aim)

        if inp.held('dash') and self.dash_cd <= 0 and self.dash_t <= 0 and not pooled:
            self.dash_t, self.dash_cd = 0.16, self.dash_cd_base
            self.dash_vec = V2(vec).normalize() if self.moving else V2(self.face)
            self.invuln = max(self.invuln, 0.22)
            game.audio.play('dash')

        if self.dash_t > 0:
            self.dash_t -= dt
            v = self.dash_vec * self.speed * 3.3
            if random.random() < game.fx:
                game.burst(self.x, self.y + 6, (170, 190, 255), 2, 40, glow=True)
        else:
            v = vec * sp
        self.move(v.x * dt, v.y * dt, game.dungeon)

        if abs(self.kx) > 5 or abs(self.ky) > 5:
            self.move(self.kx * dt, self.ky * dt, game.dungeon)
            f = 0.001 ** dt
            self.kx *= f; self.ky *= f
        else:
            self.kx = self.ky = 0.0

        if (inp.held('attack') or inp.stick_attacking()) and self.attack_cd <= 0 and not pooled:
            game.player_attack()

    def fly_to_mark(self, dt, game):
        """Sky Strike recast: rocket toward the marked monster and hit it when we arrive."""
        e = self.launch
        self.launch_t -= dt
        if e is None or e not in game.enemies:       # it died while we were in the air
            self.launch, self.launch_t = None, 0.0
            return
        dx, dy = e.x - self.x, e.y - self.y
        dist = math.hypot(dx, dy) or 1.0
        reach = (e.w + self.w) / 2 + 6
        self.face = V2(dx / dist, dy / dist)
        self.invuln = max(self.invuln, 0.15)
        self.kx = self.ky = 0.0
        self.moving = False
        step = min(950 * dt, max(0.0, dist - reach))
        self.move(dx / dist * step, dy / dist * step, game.dungeon)
        if random.random() < game.fx:
            game.burst(self.x, self.y + 4, (255, 235, 150), 3, 60, glow=True)
        if math.hypot(e.x - self.x, e.y - self.y) <= reach + 4:
            self.launch, self.launch_t = None, 0.0
            game.sky_strike_land(e)
        elif self.launch_t <= 0:                     # a wall was in the way for too long
            self.launch, self.launch_t = None, 0.0
            game.float_text(self.x, self.y - 30, "Blocked!", (200, 200, 200))

    def hurt(self, dmg, sx, sy, game):
        if self.invuln > 0 or self.hp <= 0:
            return
        if self.buffs.get('shield', 0) > 0:
            game.audio.play('deflect')
            game.burst(self.x, self.y, (120, 180, 255), 8, 120, glow=True)
            return
        dmg = max(1, int(dmg * (1 - self.istat['df'] / 100)))       # (defense from items)
        guard = 'guard' in self.ipow and self.guard_cd <= 0
        self.hp -= dmg
        if guard and self.hp < self.max_hp * IT.MYTHIC_GUARD_HP:      # Guardian Clock: a shield pops up,
            self.hp = max(1, self.hp)                                 # and this hit can't kill you
            self.guard_cd = IT.MYTHIC_GUARD_CD
            self.buffs['shield'] = max(self.buffs.get('shield', 0), IT.MYTHIC_GUARD_TIME)
            game.audio.play('shield')
            game.float_text(self.x, self.y - 46, "Guardian Clock!", (120, 200, 255), big=True)
        if 'thorns' in self.ipow:                                     # Bramble Heart: hurt whoever hit us up close
            game.thorns_from(sx, sy)
        self.invuln = HURT_INVULN
        self.hurt_flash = 0.45
        d = V2(self.x - sx, self.y - sy)
        d = d.normalize() if d.length_squared() else V2(0, 1)
        self.kx, self.ky = d.x * 260, d.y * 260
        game.audio.play('hurt')
        game.rumble(0.9, 220)
        game.shake = max(game.shake, 0.25)
        game.float_text(self.x, self.y - 22, f"-{dmg}", (255, 90, 90), big=True)
        game.burst(self.x, self.y, (220, 40, 50), 10, 120)
        if self.hp <= 0:
            self.hp = 0
            game.on_player_death()


# ====================================================================== MONSTERS
ENEMY_TYPES = {
    'slime':    dict(hp=22,  speed=55,  dmg=7,  xp=8,   size=26, sight=280),
    'bat':      dict(hp=12,  speed=125, dmg=5,  xp=6,   size=22, sight=340),
    'skeleton': dict(hp=30,  speed=70,  dmg=8,  xp=14,  size=26, sight=360),
    'goblin':   dict(hp=20,  speed=100, dmg=7,  xp=9,   size=24, sight=300),
    'imp':      dict(hp=14,  speed=100, dmg=10, xp=7,   size=22, sight=320),
    'spider':   dict(hp=24,  speed=90,  dmg=6,  xp=12,  size=24, sight=340),
    'brute':    dict(hp=85,  speed=50,  dmg=14, xp=28,  size=34, sight=300),
    'wraith':   dict(hp=30,  speed=72,  dmg=9,  xp=18,  size=22, sight=320),
    'cultist':  dict(hp=28,  speed=62,  dmg=8,  xp=20,  size=24, sight=380),
    'warlord':  dict(hp=620, speed=70,  dmg=24, xp=300, size=54, sight=560),   # floor 5 mini-boss
    'boss':     dict(hp=1200, speed=75, dmg=20, xp=600, size=52, sight=600),   # floor 10 MAJOR boss
    'lich':     dict(hp=1700, speed=62, dmg=30, xp=900, size=48, sight=620),   # floor 15 mini-boss
    'demon':    dict(hp=3600, speed=80, dmg=38, xp=2000, size=60, sight=640),  # floor 20 FINAL boss
}
MELEE_KINDS = ('slime', 'bat', 'goblin', 'imp', 'brute', 'wraith', 'warlord', 'boss', 'demon')
BOSS_NAMES = {'warlord': 'GORRAK THE OGRE WARLORD', 'boss': 'THE BONE KING',
              'lich': 'VELGRIM THE FROST LICH', 'demon': 'MALGOR THE ABYSS DEMON LORD'}


class Enemy(Entity):
    def __init__(self, kind, x, y, floor, elite=False):
        d = ENEMY_TYPES[kind]
        self.kind = kind
        self.elite = elite and kind not in BOSS_KINDS
        size = d['size'] * (1.18 if self.elite else 1.0)
        super().__init__(x, y, size, size)
        self.floor = floor
        boss = kind in BOSS_KINDS
        deep = max(0, floor - 10)                                 # after floor 10 they grow a little slower
        hp_scale = 1.0 if boss else 1 + 0.33 * (min(floor, 10) - 1) + 0.20 * deep       # monsters get tougher every floor!
        dmg_scale = 1.0 if boss else 1 + 0.16 * (min(floor, 10) - 1) + 0.09 * deep
        hp_scale *= BOSS_HP_MULT if boss else ENEMY_HP_MULT       # the difficulty knobs from settings.py
        dmg_scale *= BOSS_DMG_MULT if boss else ENEMY_DMG_MULT
        self.max_hp = self.hp = int(d['hp'] * hp_scale * (2.2 if self.elite else 1.0))
        self.dmg = int(d['dmg'] * dmg_scale * (1.25 if self.elite else 1.0))
        self.speed = d['speed'] * min(1.3, 1 + 0.03 * (floor - 1)) * (1.0 if boss else ENEMY_SPEED_MULT)
        self.xp = max(1, int(d['xp'] * (1 + 0.22 * (floor - 1)) * (2.5 if self.elite else 1.0) * XP_MULT))
        self.sight = d['sight']
        self.awake = False
        self.flash = 0.0
        self.anim = random.random() * 5
        self.kx = self.ky = 0.0
        self.shoot_t = random.uniform(1.0, 2.5)
        self.strafe = random.choice((-1, 1))
        self.phase = 1
        self.stun_t = self.slow_t = self.poison_t = 0.0
        self.freeze_t = 0.0        # frozen solid (Ghala's Frozen Heart)
        self.petal_cd = 0.0        # how soon Ghala's flower ring may hit this monster again
        self.curse_t = 0.0         # Vampire Lord's Blood Curse: seconds until this monster BURSTS
        self.curse_dmg = 0.0       # ...and how much damage it has taken while cursed (makes the burst bigger)
        self.poison_dps, self.poison_tick = 0.0, 0.5
        self.state = 'chase'
        self.state_t = random.uniform(1.0, 2.5)
        self.warn = False
        self.vec = (0.0, 0.0)
        self.tele_t = random.uniform(3, 6)
        self.summon_t = 10.0
        self.spiral_t, self.spiral_on, self.spiral_ang, self.spiral_shot = 5.0, 0.0, 0.0, 0.0
        self.name = BOSS_NAMES.get(kind, '')
        # ---- brain stuff (see ai.py)
        self.smarts = smarts_for(floor, self.elite)   # 0 = simple, 1 = fully clever (grows with the floor)
        self.react_t = 0.0         # just spotted you: a short pause before it may attack
        self.lost_t = 0.0          # how long it has NOT seen you (it gives up after a while)
        self.sees, self.see_t = True, 0.0
        self.nav_t, self.nav_pt = 0.0, None           # the next spot it walks to when a wall is in the way
        self.flank = (0.0, 0.0)    # a sideways nudge so the pack spreads around you
        self.stuck_t, self.unstick_t, self.unstick_dir = 0.0, 0.0, (0.0, 0.0)
        self.kite_dir = (0.0, 0.0)
        self.dodge_t, self.dodge_cd, self.dodge_dir = 0.0, 0.0, (0.0, 0.0)
        self.seen = set()          # hero shots it has already decided whether to dodge
        self.attacker = True       # melee: may it close in right now? (or wait its turn, circling)
        self.turn_t = self.rest_t = 0.0                 # how long its turn has lasted / rest after a turn

    # ---- who do we chase? the player, or a nearby ally that is closer
    def target_pos(self, game):
        p = game.player
        if self.kind in MELEE_KINDS and game.minions:
            best, bd = None, min(math.hypot(p.x - self.x, p.y - self.y), 240) - 25
            for m in game.minions:
                d = math.hypot(m.x - self.x, m.y - self.y)
                if d < bd:
                    best, bd = m, d
            if best:
                return best.x, best.y
        return p.x, p.y

    def update(self, dt, game):
        p, d = game.player, game.dungeon
        self.anim += dt
        self.flash = max(0.0, self.flash - dt)

        if self.poison_t > 0:
            self.poison_t -= dt
            self.poison_tick -= dt
            if self.poison_tick <= 0:
                self.poison_tick = 0.5
                game.damage_enemy(self, max(1, int(self.poison_dps * 0.5)), crit=False, knock=False, dot=True, src='dot')
                if self.hp <= 0:
                    return
        self.slow_t = max(0.0, self.slow_t - dt)
        self.petal_cd = max(0.0, self.petal_cd - dt)

        if self.freeze_t > 0:                        # frozen solid: can't move, slide or attack
            self.freeze_t -= dt
            self.kx = self.ky = 0.0
            self.warn = False
            return

        if abs(self.kx) > 5 or abs(self.ky) > 5:
            self.move(self.kx * dt, self.ky * dt, d)
            f = 0.0005 ** dt
            self.kx *= f; self.ky *= f
        else:
            self.kx = self.ky = 0.0

        if self.stun_t > 0:
            self.stun_t -= dt
            self.warn = False
            return

        dpl = math.hypot(p.x - self.x, p.y - self.y) or 1.0
        brain = game.ai
        if not self.awake:
            if dpl < self.sight and (self.kind == 'wraith' or d.line_clear(self.x, self.y, p.x, p.y)):
                self.awake = True
                brain.on_wake(self)
                if self.kind in BOSS_KINDS:
                    game.audio.play('boss'); game.shake = 0.6
                    game.show_banner(f"{self.name.title()} awakens!")
            else:
                return

        self.react_t = max(0.0, self.react_t - dt)
        self.dodge_cd = max(0.0, self.dodge_cd - dt)
        self.see_t -= dt
        if self.see_t <= 0:                          # (looking costs a little, so only ~7 times a second)
            self.see_t = 0.15
            self.sees = dpl < self.sight * 1.6 and brain.sees_player(self)
        if self.sees:
            self.lost_t = 0.0
        elif (self.kind not in BOSS_KINDS and self.state == 'chase' and not self.warn
              and not any(abs(m.x - self.x) < 220 and abs(m.y - self.y) < 220 for m in game.minions)):
            self.lost_t += dt                        # (busy fighting your summons? then it isn't 'lost')
            if self.lost_t > memory_time(self.smarts):   # lost you for too long: gives up and goes back to sleep
                self.awake, self.lost_t, self.nav_pt = False, 0.0, None
                return

        tx, ty = self.target_pos(game)
        if not self.attacker and (tx, ty) == (p.x, p.y) and self.state == 'chase':
            tx, ty = brain.ring_point(self)          # not its turn: circle around you, waiting for a gap
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy) or 1.0
        nx, ny = dx / dist, dy / dist
        pnx, pny = (p.x - self.x) / dpl, (p.y - self.y) / dpl      # direction to the PLAYER (for shooters)

        self.state_t -= dt
        sp = self.speed * (0.45 if self.slow_t > 0 else 1.0)
        k = self.kind

        dodging = False                              # a quick sidestep away from one of your shots
        if self.dodge_t > 0:
            self.dodge_t -= dt
            self.move(self.dodge_dir[0] * max(sp, 80) * 2.6 * dt, self.dodge_dir[1] * max(sp, 80) * 2.6 * dt, d)
            dodging = True
        elif self.state == 'chase' and not self.warn:
            brain.try_dodge(self)

        if dodging:
            pass

        elif k == 'slime':
            hop = 0.25 + 0.75 * max(0.0, math.sin(self.anim * 4))
            self.chase_move(game, tx, ty, sp * hop, dt)

        elif k == 'bat':
            self.chase_move(game, tx, ty, sp, dt, wobble=math.sin(self.anim * 5) * 0.9)

        elif k == 'skeleton':
            self.kite_move(game, sp, dt, 230, 140, 0.6)
            self.shoot_t -= dt
            if self.shoot_t <= 0 and dpl < 400 and d.line_clear(self.x, self.y, p.x, p.y):
                if brain.can_shoot(self):
                    self.shoot_t = 2.3
                    ax, ay = brain.aim(self, 210)
                    game.projectiles.append(Projectile(self.x, self.y, ax * 210, ay * 210, self.dmg, (240, 240, 220)))
                    game.audio.play('shoot')
                    brain.shot_fired()
                else:                                # someone else is shooting right now: wait a moment
                    self.shoot_t = random.uniform(0.2, 0.5)

        elif k == 'goblin':      # runs at you, then does a sneaky LUNGE
            if self.state == 'chase':
                self.chase_move(game, tx, ty, sp, dt)
                if (self.state_t <= 0 and 90 < dist < 260 and d.line_clear(self.x, self.y, tx, ty)
                        and brain.can_windup(self)):
                    self.state, self.state_t, self.warn = 'wind', 0.4, True
                    brain.start_windup(self)
                    game.audio.play('warn')
            elif self.state == 'wind':
                if self.state_t <= 0:
                    self.state, self.state_t, self.warn = 'lunge', 0.35, False
                    if (tx, ty) == (p.x, p.y):       # deeper down, it lunges a bit toward where you are RUNNING
                        self.vec = brain.aim(self, sp * 4.2, lead=lunge_lead(self.smarts))
                    else:
                        self.vec = (nx, ny)
            else:
                self.move(self.vec[0] * sp * 4.2 * dt, self.vec[1] * sp * 4.2 * dt, d)
                if self.state_t <= 0:
                    self.state, self.state_t = 'chase', random.uniform(2.5, 4.0)

        elif k == 'imp':         # runs up and EXPLODES
            if self.state == 'chase':
                self.chase_move(game, tx, ty, sp, dt)
                if dist < 60 and brain.can_windup(self):
                    self.state, self.state_t, self.warn = 'fuse', 0.7, True
                    brain.start_windup(self)
                    game.audio.play('warn')
            else:
                self.chase_move(game, tx, ty, sp * 0.3, dt)
                if self.state_t <= 0:
                    game.explosion(self.x, self.y, 85, int(self.dmg * 1.6))
                    if self in game.enemies:
                        game.enemies.remove(self)
                    return

        elif k == 'spider':      # keeps away and spits slowing webs
            self.kite_move(game, sp, dt, 240, 150, 0.9)
            self.shoot_t -= dt
            if self.shoot_t <= 0 and dpl < 380 and d.line_clear(self.x, self.y, p.x, p.y):
                if brain.can_shoot(self):
                    self.shoot_t = 2.6
                    ax, ay = brain.aim(self, 230)
                    game.projectiles.append(Projectile(self.x, self.y, ax * 230, ay * 230, max(1, self.dmg // 2),
                                                       (235, 235, 245), 6, effect='slow'))
                    game.audio.play('shoot')
                    brain.shot_fired()
                else:
                    self.shoot_t = random.uniform(0.2, 0.5)

        elif k == 'brute':       # slow, but SLAMS the ground (watch for the "!")
            if self.state == 'chase':
                self.chase_move(game, tx, ty, sp, dt)
                if dist < 125 and self.state_t <= 0 and brain.can_windup(self):
                    self.state, self.state_t, self.warn = 'wind', 0.75, True
                    brain.start_windup(self)
                    game.audio.play('warn')
            elif self.state_t <= 0:
                game.slam(self.x, self.y, 100, int(self.dmg * 1.3))
                self.state, self.state_t, self.warn = 'chase', 2.6, False

        elif k == 'wraith':      # floats THROUGH walls
            f = 0.6 + 0.4 * math.sin(self.anim * 2)
            wx, wy = brain.steer(self, tx, ty)
            self.x += wx * sp * f * dt
            self.y += wy * sp * f * dt

        elif k == 'cultist':     # blinks around and fires 3 dark bolts
            self.kite_move(game, sp, dt, 260, 170, 0.6)
            self.shoot_t -= dt
            if self.shoot_t <= 0 and dpl < 420 and d.line_clear(self.x, self.y, p.x, p.y):
                if brain.can_shoot(self):
                    self.shoot_t = 3.0
                    ax, ay = brain.aim(self, 190)
                    base = math.atan2(ay, ax)
                    for da in (-0.28, 0, 0.28):
                        game.projectiles.append(Projectile(self.x, self.y, math.cos(base + da) * 190,
                                                           math.sin(base + da) * 190, self.dmg, (210, 70, 255), 6))
                    game.audio.play('shoot')
                    brain.shot_fired()
                else:
                    self.shoot_t = random.uniform(0.2, 0.5)
            self.tele_t -= dt
            if self.tele_t <= 0 and self.lost_t < 1.5:   # (only blinks to you if it has just seen you)
                self.tele_t = random.uniform(5, 7)
                for _ in range(12):
                    a, r = random.random() * 6.283, random.uniform(170, 240)
                    bx, by = p.x + math.cos(a) * r, p.y + math.sin(a) * r
                    rc = pygame.Rect(int(bx - self.w / 2), int(by - self.h / 2), self.w, self.h)
                    if not d.hits_wall(rc) and d.line_clear(bx, by, p.x, p.y):
                        game.burst(self.x, self.y, (200, 80, 255), 12, 120, glow=True)
                        self.x, self.y = bx, by
                        game.burst(bx, by, (200, 80, 255), 12, 120, glow=True)
                        game.audio.play('warp')
                        break

        elif k == 'warlord':     # MINI-BOSS: charges, slams, and calls goblins when hurt
            if self.state == 'chase':
                self.chase_move(game, tx, ty, sp, dt)
                if self.state_t <= 0:
                    if dist < 160:
                        self.state, self.state_t, self.warn = 'slamwind', 0.9, True
                        game.audio.play('warn')
                    elif brain.clear_run(self, tx, ty):      # (only charges if no wall is in the way)
                        self.state, self.state_t, self.warn = 'wind', 0.8, True
                        game.audio.play('warn')
                    else:
                        self.state_t = 0.3
            elif self.state == 'wind':
                if self.state_t <= 0:
                    self.state, self.state_t, self.warn = 'charge', 0.6, False
                    self.vec = (nx, ny)
                    game.audio.play('roar')
            elif self.state == 'charge':
                self.move(self.vec[0] * sp * 4.6 * dt, self.vec[1] * sp * 4.6 * dt, d)
                game.burst(self.x, self.y + 14, (150, 120, 90), 1, 60)
                if self.state_t <= 0:
                    self.state, self.state_t = 'chase', random.uniform(1.8, 2.8)
            elif self.state == 'slamwind':
                if self.state_t <= 0:
                    game.slam(self.x, self.y, 150, int(self.dmg * 1.1))
                    self.state, self.state_t, self.warn = 'chase', random.uniform(2.0, 3.0), False
            if self.phase == 1 and self.hp < self.max_hp * 0.5:
                self.phase = 2
                self.speed *= 1.25
                game.show_banner("Gorrak is ENRAGED!")
                game.audio.play('roar'); game.shake = 0.6
                for ox in (-70, 70):
                    game.enemies.append(Enemy('goblin', self.x + ox, self.y, self.floor))
                    game.enemies[-1].awake = True

        elif k == 'boss':        # FINAL BOSS: three phases
            if dist > 80:
                self.chase_move(game, tx, ty, sp, dt)
            frac = self.hp / self.max_hp
            want = 1 if frac > 0.66 else 2 if frac > 0.33 else 3
            if want > self.phase:
                self.phase = want
                self.speed *= 1.2
                game.show_banner("The Bone King is ANGRY!" if want == 2 else "THE BONE KING UNLEASHES HIS POWER!")
                game.audio.play('boss'); game.shake = 0.6
                for ox in (-60, 60):
                    game.enemies.append(Enemy('bat', self.x + ox, self.y, 8))
                    game.enemies[-1].awake = True
            self.shoot_t -= dt
            if self.shoot_t <= 0:
                self.shoot_t = (2.2, 1.7, 1.3)[self.phase - 1]
                n = 12 + 4 * (self.phase - 1)
                off = random.random() * 6.28
                for i in range(n):
                    a = off + i * 6.2832 / n
                    game.projectiles.append(Projectile(self.x, self.y, math.cos(a) * 170, math.sin(a) * 170,
                                                       int(self.dmg * 0.6), (200, 70, 255), 7))
                game.audio.play('shoot')
            self.summon_t -= dt
            if self.summon_t <= 0:
                self.summon_t = (14, 10, 8)[self.phase - 1]
                if len(game.enemies) < 12:
                    for ox in (-90, 90):
                        game.enemies.append(Enemy(random.choice(('skeleton', 'cultist')), self.x + ox, self.y + 20, 9))
                        game.enemies[-1].awake = True
                        game.burst(self.x + ox, self.y + 20, (200, 80, 255), 14, 140, glow=True)
                    game.audio.play('warp')
            if self.phase >= 3:
                self.spiral_t -= dt
                if self.spiral_on <= 0 and self.spiral_t <= 0:
                    self.spiral_on, self.spiral_t = 2.6, 5.5
                if self.spiral_on > 0:
                    self.spiral_on -= dt
                    self.spiral_shot -= dt
                    if self.spiral_shot <= 0:
                        self.spiral_shot = 0.07
                        self.spiral_ang += 0.55
                        game.projectiles.append(Projectile(self.x, self.y, math.cos(self.spiral_ang) * 200,
                                                           math.sin(self.spiral_ang) * 200, int(self.dmg * 0.5),
                                                           (255, 90, 160), 6))

        elif k == 'lich':        # MINI-BOSS (floor 15): keeps away, fans of ice bolts, blinks, raises skeletons
            self.kite_move(game, sp, dt, 270, 180, 0.6)
            if self.phase == 1 and self.hp < self.max_hp * 0.5:
                self.phase = 2
                self.speed *= 1.2
                game.show_banner("Velgrim is FURIOUS!", "Ice storm incoming")
                game.audio.play('boss'); game.shake = 0.6
                for ox in (-80, 80):
                    game.enemies.append(Enemy('skeleton', self.x + ox, self.y + 10, self.floor))
                    game.enemies[-1].awake = True
            self.shoot_t -= dt
            if self.shoot_t <= 0 and d.line_clear(self.x, self.y, p.x, p.y):
                self.shoot_t = (1.9, 1.3)[self.phase - 1]
                base, n = math.atan2(pny, pnx), (5, 7)[self.phase - 1]
                for i in range(n):
                    da = (i - (n - 1) / 2) * 0.2
                    game.projectiles.append(Projectile(self.x, self.y, math.cos(base + da) * 235, math.sin(base + da) * 235,
                                                       int(self.dmg * 0.7), (150, 225, 255), 7,
                                                       effect='slow' if i == n // 2 else None))
                game.audio.play('shoot')
            self.tele_t -= dt
            if self.tele_t <= 0:
                self.tele_t = random.uniform(4.0, 5.5)
                for _ in range(14):
                    a, r = random.random() * 6.283, random.uniform(180, 250)
                    bx, by = p.x + math.cos(a) * r, p.y + math.sin(a) * r
                    rc = pygame.Rect(int(bx - self.w / 2), int(by - self.h / 2), self.w, self.h)
                    if not d.hits_wall(rc) and d.line_clear(bx, by, p.x, p.y):
                        game.burst(self.x, self.y, (150, 225, 255), 14, 130, glow=True)
                        self.x, self.y = bx, by
                        game.burst(bx, by, (150, 225, 255), 14, 130, glow=True)
                        game.audio.play('warp')
                        for i in range(10):                         # frost ring after every blink
                            ang = i * 6.2832 / 10
                            game.projectiles.append(Projectile(bx, by, math.cos(ang) * 170, math.sin(ang) * 170,
                                                               int(self.dmg * 0.5), (190, 240, 255), 6))
                        break
            self.summon_t -= dt
            if self.summon_t <= 0:
                self.summon_t = (13, 9)[self.phase - 1]
                if len(game.enemies) < 10:
                    for ox in (-90, 90):
                        game.enemies.append(Enemy(random.choice(('skeleton', 'cultist')), self.x + ox, self.y + 20, self.floor))
                        game.enemies[-1].awake = True
                        game.burst(self.x + ox, self.y + 20, (150, 225, 255), 14, 140, glow=True)
                    game.audio.play('warp')

        elif k == 'demon':       # FINAL BOSS (floor 20): four phases - charges, slams, fire rings, spirals
            frac = self.hp / self.max_hp
            want = 1 if frac > 0.75 else 2 if frac > 0.5 else 3 if frac > 0.25 else 4
            if want > self.phase:
                self.phase = want
                self.speed *= 1.1
                game.show_banner(("", "Malgor is ENRAGED!", "MALGOR TEARS OPEN THE ABYSS!", "MALGOR'S FINAL FURY!")[want - 1])
                game.audio.play('boss'); game.shake = 0.8
                game.rumble(0.9, 500)
                if want >= 2 and len(game.enemies) < 12:
                    for ox in (-80, 80):
                        game.enemies.append(Enemy('imp' if want == 2 else 'wraith', self.x + ox, self.y, self.floor))
                        game.enemies[-1].awake = True
            if self.state == 'chase':
                if dist > 70:
                    self.chase_move(game, tx, ty, sp, dt)
                if self.state_t <= 0:
                    if dist < 180:
                        self.state, self.state_t, self.warn = 'slamwind', 0.8, True
                        game.audio.play('warn')
                    elif brain.clear_run(self, tx, ty):
                        self.state, self.state_t, self.warn = 'wind', 0.7, True
                        game.audio.play('warn')
                    else:
                        self.state_t = 0.3
            elif self.state == 'wind':
                if self.state_t <= 0:
                    self.state, self.state_t, self.warn = 'charge', 0.55, False
                    self.vec = (nx, ny)
                    game.audio.play('roar')
            elif self.state == 'charge':
                self.move(self.vec[0] * sp * 4.4 * dt, self.vec[1] * sp * 4.4 * dt, d)
                game.burst(self.x, self.y + 16, (255, 120, 50), 1, 70, glow=True)
                if self.state_t <= 0:
                    self.state, self.state_t = 'chase', random.uniform(1.6, 2.6) / (1 + 0.15 * (self.phase - 1))
            elif self.state == 'slamwind':
                if self.state_t <= 0:
                    game.slam(self.x, self.y, 175, int(self.dmg * 1.1))
                    if self.phase >= 2:                              # the slam throws out a ring of fire
                        for i in range(14):
                            ang = i * 6.2832 / 14
                            game.projectiles.append(Projectile(self.x, self.y, math.cos(ang) * 190, math.sin(ang) * 190,
                                                               int(self.dmg * 0.45), (255, 120, 40), 7))
                    self.state, self.state_t, self.warn = 'chase', random.uniform(1.8, 2.8), False
            self.shoot_t -= dt
            if self.shoot_t <= 0:
                self.shoot_t = (3.2, 2.6, 2.1, 1.7)[self.phase - 1]
                n, off = 14 + 3 * (self.phase - 1), random.random() * 6.28
                for i in range(n):
                    a = off + i * 6.2832 / n
                    game.projectiles.append(Projectile(self.x, self.y, math.cos(a) * 175, math.sin(a) * 175,
                                                       int(self.dmg * 0.5), (255, 90, 40), 7))
                game.audio.play('shoot')
            if self.phase >= 2:
                self.spiral_t -= dt
                if self.spiral_on <= 0 and self.spiral_t <= 0:
                    self.spiral_on, self.spiral_t = 2.4, (0, 6.5, 5.5, 4.5)[self.phase - 1]
                if self.spiral_on > 0:
                    self.spiral_on -= dt
                    self.spiral_shot -= dt
                    if self.spiral_shot <= 0:
                        self.spiral_shot = 0.08
                        self.spiral_ang += 0.55
                        arms = 2 if self.phase >= 4 else 1
                        for arm in range(arms):
                            ang = self.spiral_ang + arm * math.pi
                            game.projectiles.append(Projectile(self.x, self.y, math.cos(ang) * 200, math.sin(ang) * 200,
                                                               int(self.dmg * 0.4), (255, 60, 120), 6))
            if self.phase >= 3:
                self.summon_t -= dt
                if self.summon_t <= 0:
                    self.summon_t = 11 if self.phase == 3 else 8
                    if len(game.enemies) < 12:
                        for ox in (-100, 100):
                            game.enemies.append(Enemy(random.choice(('imp', 'brute', 'cultist')), self.x + ox, self.y + 20, self.floor))
                            game.enemies[-1].awake = True
                            game.burst(self.x + ox, self.y + 20, (255, 100, 40), 14, 140, glow=True)
                        game.audio.play('warp')

        # touching the player or an ally hurts them
        if k != 'imp':
            r = self.rect
            if r.colliderect(p.rect):
                p.hurt(self.dmg, self.x, self.y, game)
            for m in game.minions:
                if r.colliderect(m.rect):
                    m.hurt(self.dmg, game)

    def chase_move(self, game, tx, ty, sp, dt, wobble=0.0):
        """Walk toward (tx, ty) - around walls, and spreading out from friends (see ai.py)."""
        brain = game.ai
        mx, my = brain.steer(self, tx, ty)
        if wobble:                                   # (bats flutter from side to side)
            mx, my = mx - my * wobble, my + mx * wobble
            l = math.hypot(mx, my) or 1.0
            mx, my = mx / l, my / l
        ox, oy = self.x, self.y
        self.move(mx * sp * dt, my * sp * dt, game.dungeon)
        brain.track(self, ox, oy, sp * dt, mx, my, dt)

    def kite_move(self, game, sp, dt, far, near, strafe):
        """Ranged monsters: stay at shooting distance, in the open, with a clear shot (see ai.py)."""
        brain = game.ai
        mx, my = brain.kite(self, far, near, strafe)
        ox, oy = self.x, self.y
        self.move(mx * sp * dt, my * sp * dt, game.dungeon)
        brain.track(self, ox, oy, sp * dt, mx, my, dt)


# ====================================================================== ALLIES
MINION_TYPES = {
    'skeleton':  dict(hp=45,  speed=110, mult=0.9, size=22, role='melee',  cd=0.7),
    'archer':    dict(hp=30,  speed=95,  mult=0.75, size=22, role='ranged', cd=1.3),
    'bonebrute': dict(hp=130, speed=72,  mult=1.5, size=30, role='melee',  cd=1.0),
}


class Minion(Entity):
    """A friend that fights FOR you: the undead a Necromancer raises."""
    def __init__(self, kind, x, y, level, life=None, group='undead'):
        d = MINION_TYPES[kind]
        super().__init__(x, y, d['size'], d['size'])
        self.kind, self.role, self.group, self.life = kind, d['role'], group, life
        self.mult, self.speed, self.cd_base = d['mult'], d['speed'], d['cd']
        self.max_hp = self.hp = int(d['hp'] * (1 + 0.12 * (level - 1)))
        self.cd, self.invuln, self.flash = 0.3, 0.0, 0.0
        self.anim = random.random() * 4
        self.kx = self.ky = 0.0
        self.face_left = False
        self.target = None
        self.state, self.state_t, self.vec = 'circle', random.uniform(0.3, 1.0), (0.0, 0.0)
        self.orbit = random.random() * 6.28
        self.lunge = 0.0
        self.spawn = 0.4          # little "pop in" animation timer

    def hurt(self, dmg, game):
        if self.invuln > 0:
            return
        self.hp -= int(dmg)
        self.invuln, self.flash = 0.45, 0.12
        game.float_text(self.x, self.y - 18, f"-{int(dmg)}", (255, 140, 140))
        game.burst(self.x, self.y, (230, 60, 60), 5, 90)
        if self.hp <= 0:
            game.minion_died(self)

    def update(self, dt, game):
        p, d = game.player, game.dungeon
        self.anim += dt
        self.cd -= dt
        self.state_t -= dt
        self.invuln = max(0.0, self.invuln - dt)
        self.flash = max(0.0, self.flash - dt)
        self.lunge = max(0.0, self.lunge - dt)
        self.spawn = max(0.0, self.spawn - dt)
        if self.life is not None:
            self.life -= dt
            if self.life <= 0:
                game.minion_expire(self)
                return
        if abs(self.kx) > 5 or abs(self.ky) > 5:
            self.move(self.kx * dt, self.ky * dt, d)
            f = 0.0005 ** dt
            self.kx *= f; self.ky *= f
        else:
            self.kx = self.ky = 0.0

        dpl = math.hypot(p.x - self.x, p.y - self.y) or 1.0
        if dpl > 480:                                   # got lost? hop back to the hero
            game.burst(self.x, self.y, (180, 200, 255), 8, 100, glow=True)
            a = random.random() * 6.28
            self.x, self.y = p.x + math.cos(a) * 40, p.y + math.sin(a) * 40
            if d.hits_wall(self.rect):
                self.x, self.y = p.x, p.y

        t = self.target
        if (t is None or t not in game.enemies or math.hypot(t.x - self.x, t.y - self.y) > 400
                or not d.line_clear(self.x, self.y, t.x, t.y)):
            self.target = t = game.nearest_enemy(self.x, self.y, 320, p)
        sp = self.speed
        dmg = max(2, int(p.dmg * self.mult * (1 + p.istat['ap'] / 100)))   # (ability damage items help allies too)
        mx = my = 0.0

        if t is None:
            self.state = 'circle'
            self.hp = min(self.max_hp, self.hp + self.max_hp * 0.03 * dt)      # allies heal up between fights
            if dpl > 80:
                run = 1.0 + min(1.0, (dpl - 80) / 160)
                mx, my = (p.x - self.x) / dpl * sp * run, (p.y - self.y) / dpl * sp * run
            else:
                a = self.orbit + self.anim * 0.8
                mx, my = math.cos(a) * 14, math.sin(a) * 14
        else:
            dx, dy = t.x - self.x, t.y - self.y
            dist = math.hypot(dx, dy) or 1.0
            nx, ny = dx / dist, dy / dist
            touch = (t.w + self.w) / 2 + 6
            if self.role == 'melee':
                if dist > touch - 4:
                    mx, my = nx * sp, ny * sp
                if self.cd <= 0 and dist < touch + 4:
                    self.cd = self.cd_base
                    self.lunge = 0.14
                    self.vec = (nx, ny)
                    game.minion_hit(self, t, dmg)
            elif self.role == 'ranged':
                if dist > 230:
                    mx, my = nx * sp, ny * sp
                elif dist < 150:
                    mx, my = -nx * sp, -ny * sp
                if self.cd <= 0 and dist < 360:
                    self.cd = self.cd_base
                    self.lunge = 0.1
                    self.vec = (nx, ny)
                    game.bolts.append(Bolt(self.x, self.y, nx * 380, ny * 380, dmg, (225, 235, 255), 4, 1.2, kind='arrow',
                                           src='ally'))
                    game.audio.play('shoot')
            if abs(nx) > 0.2:
                self.face_left = nx < 0
        if t is None and abs(mx) > 6:
            self.face_left = mx < 0
        self.move(mx * dt, my * dt, d)


class Corpse:
    """What a monster leaves behind. Necromancers can raise or blow these up."""
    def __init__(self, kind, x, y):
        self.kind, self.x, self.y, self.life = kind, x, y, 40.0


# ====================================================================== SHOTS, LOOT, SPARKLES
class Projectile:
    """Bad guys' shots (they hurt YOU)."""
    def __init__(self, x, y, vx, vy, dmg, color, radius=5, life=4.0, effect=None):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.dmg, self.color, self.radius, self.life, self.effect = dmg, color, radius, life, effect
        self.alive = True

    def update(self, dt, game):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        if random.random() < 0.5 * game.fx:
            game.particles.append(Particle(self.x, self.y, 0, 0, 0.3, self.color, 3, glow=True))
        if self.life <= 0 or game.dungeon.is_wall(int(self.x // TILE), int(self.y // TILE)):
            self.alive = False
            return
        p = game.player
        if math.hypot(p.x - self.x, p.y - self.y) < self.radius + 10:
            p.hurt(self.dmg, self.x - self.vx, self.y - self.vy, game)
            if self.effect == 'slow' and p.buffs.get('shield', 0) <= 0:
                p.slow_t = 2.5
                game.float_text(p.x, p.y - 38, "Slowed!", (220, 220, 255))
            self.alive = False


class Bolt:
    """YOUR shots (and your allies'): magic bolts, fireballs, knives, arrows."""
    def __init__(self, x, y, vx, vy, dmg, color, radius=6, life=1.2, aoe=0, pierce=False,
                 kind='magic', crit=False, leech=False, mark=False, freeze=0.0, falloff=1.0, volley=None,
                 src='ability'):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.dmg, self.color, self.radius, self.life = dmg, color, radius, life
        self.aoe, self.pierce, self.kind, self.crit, self.leech = aoe, pierce, kind, crit, leech
        self.src = src         # 'basic' (a basic attack), 'ability' or 'ally' - shop items care which
        self.mark = mark       # Monk's Sky Strike: the orb sticks to the first monster it hits
        self.freeze = freeze   # Ghala's Frozen Heart: seconds the monster it hits stays frozen
        self.falloff = falloff # Shadow Ninja's shurikens: every hit after the FIRST does this much of the damage
        self.volley = volley   # ...a set shared by all shurikens of one throw: the monsters that throw already hit
        self.alive = True
        self.hit = set()

    def explode(self, game):
        if self.aoe:
            game.audio.play('boom')
            game.aoe(self.x, self.y, self.aoe, self.dmg, knock=220, color=self.color)
            game.burst(self.x, self.y, (255, 190, 80), 26, 230, glow=True)
            game.shake = max(game.shake, 0.12)
        self.alive = False

    def update(self, dt, game):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        if self.kind == 'shuriken':                      # shurikens leave a thin, dark trail (not a bright one)
            if random.random() < 0.5 * game.fx:
                game.particles.append(Particle(self.x, self.y, 0, 0, 0.22, (70, 45, 130), 3))
        elif random.random() < 0.8 * game.fx:
            game.particles.append(Particle(self.x, self.y, random.uniform(-20, 20), random.uniform(-20, 20),
                                           0.3, self.color, 3, glow=True))
        if self.life <= 0 or game.dungeon.is_wall(int(self.x // TILE), int(self.y // TILE)):
            if self.aoe:
                self.explode(game)
            self.alive = False
            return
        for e in game.enemies[:]:
            if id(e) in self.hit:
                continue
            if math.hypot(e.x - self.x, e.y - self.y) < e.w / 2 + self.radius + 2:
                first = len(self.hit) == 0 and (self.volley is None or id(e) not in self.volley)
                self.hit.add(id(e))
                if self.volley is not None:
                    self.volley.add(id(e))
                if self.aoe:
                    self.explode(game)
                    return
                dmg = self.dmg if first else self.dmg * self.falloff     # (falloff is 1.0 for everything but shurikens)
                game.damage_enemy(e, int(dmg), crit=self.crit, origin=(self.x - self.vx, self.y - self.vy),
                                  leech=self.leech, src=self.src)
                if self.mark and e in game.enemies:   # only mark it if the hit didn't kill it outright
                    p = game.player
                    p.sky_mark_enemy = e
                    p.buffs['sky_mark'] = 4.0
                    game.float_text(e.x, e.y - 40, "MARKED!", (255, 210, 90), big=True)
                if self.freeze and e in game.enemies:
                    game.freeze_enemy(e, self.freeze)
                if not self.pierce:
                    self.alive = False
                    return


class Item:
    def __init__(self, kind, x, y, value=0):
        self.kind, self.x, self.y, self.value = kind, float(x), float(y), value
        self.t = random.random() * 6
        self.opened = False

    @property
    def rect(self):
        return pygame.Rect(int(self.x - 12), int(self.y - 12), 24, 24)


class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size', 'glow')

    def __init__(self, x, y, vx, vy, life, color, size, glow=False):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.color, self.size, self.glow = color, size, glow


class FloatText:
    def __init__(self, x, y, text, color, big=False):
        self.x, self.y, self.text, self.color, self.big = x, y, text, color, big
        self.life = self.max_life = 1.1
