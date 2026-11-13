"""entities.py - the living (and flying) things: the hero, monsters, ALLIES, spells, loot, sparkles."""
import math
import random
import pygame
from settings import TILE
from classes import CLASSES

V2 = pygame.Vector2
BOSS_KINDS = ('boss', 'warlord')


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
        self.dash_cd_base, self.potion_frac = c['dash_cd'], c['potion_frac']
        self.kill_heal = c.get('kill_heal', 0)
        self.cd_mult, self.ap = 1.0, 1.0
        self.level, self.xp = 1, 0
        self.xp_next = xp_for(1)
        self.face = V2(0, 1)
        self.attack_cd = self.swing = self.invuln = 0.0
        self.dash_t = self.dash_cd = 0.0
        self.dash_vec = V2(0, 0)
        self.kx = self.ky = 0.0
        self.potions, self.gold, self.kills = 1, 0, 0
        self.ability_cd = [0.0, 0.0, 0.0]
        self.ability_max = [1.0, 1.0, 1.0]
        self.buffs = {}
        self.sky_mark_enemy = None   # Monk's Sky Strike mark, used for the teleport recast
        self.slow_t = 0.0
        self.spin = 0.0
        self.hurt_flash = 0.0
        self.anim = 0.0
        self.moving = False

    @property
    def potion_heal(self):
        return int(self.max_hp * self.potion_frac)

    @property
    def dir_name(self):
        if abs(self.face.x) > abs(self.face.y):
            return 'right' if self.face.x > 0 else 'left'
        return 'down' if self.face.y > 0 else 'up'

    def update(self, dt, inp, game):
        """`inp` is the Input object (keyboard + controller). It tells us where to walk, aim and what's held."""
        for name in ('attack_cd', 'swing', 'invuln', 'dash_cd', 'slow_t', 'spin', 'hurt_flash'):
            setattr(self, name, max(0.0, getattr(self, name) - dt))
        for i in range(3):
            self.ability_cd[i] = max(0.0, self.ability_cd[i] - dt)
        for k in list(self.buffs):
            self.buffs[k] -= dt
            if self.buffs[k] <= 0:
                del self.buffs[k]

        sp = self.speed * (0.5 if self.slow_t > 0 else 1.0)
        vec = inp.move_vector()                      # length 0..1  (a gentle stick push = a slow walk)
        self.moving = vec.length_squared() > 0.0004
        if self.moving:
            self.face = V2(vec).normalize()
            self.anim += dt * max(0.5, min(1.0, vec.length()))
        aim = inp.aim_vector()                       # right stick: face where you point it
        if aim is not None:
            self.face = V2(aim)

        if inp.held('dash') and self.dash_cd <= 0 and self.dash_t <= 0:
            self.dash_t, self.dash_cd = 0.16, self.dash_cd_base
            self.dash_vec = V2(vec).normalize() if self.moving else V2(self.face)
            self.invuln = max(self.invuln, 0.22)
            game.audio.play('dash')

        if self.dash_t > 0:
            self.dash_t -= dt
            v = self.dash_vec * self.speed * 3.3
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

        if (inp.held('attack') or inp.stick_attacking()) and self.attack_cd <= 0:
            game.player_attack()

    def hurt(self, dmg, sx, sy, game):
        if self.invuln > 0 or self.hp <= 0:
            return
        if self.buffs.get('shield', 0) > 0:
            game.audio.play('deflect')
            game.burst(self.x, self.y, (120, 180, 255), 8, 120, glow=True)
            return
        dmg = max(1, int(dmg))
        self.hp -= dmg
        self.invuln = 0.9
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
    'boss':     dict(hp=1000, speed=75, dmg=20, xp=600, size=52, sight=600),   # floor 10 final boss
}
MELEE_KINDS = ('slime', 'bat', 'goblin', 'imp', 'brute', 'wraith', 'warlord', 'boss')
BOSS_NAMES = {'warlord': 'GORRAK THE OGRE WARLORD', 'boss': 'THE BONE KING'}


class Enemy(Entity):
    def __init__(self, kind, x, y, floor, elite=False):
        d = ENEMY_TYPES[kind]
        self.kind = kind
        self.elite = elite and kind not in BOSS_KINDS
        size = d['size'] * (1.18 if self.elite else 1.0)
        super().__init__(x, y, size, size)
        self.floor = floor
        boss = kind in BOSS_KINDS
        hp_scale = 1.0 if boss else 1 + 0.33 * (floor - 1)       # monsters get tougher every floor!
        dmg_scale = 1.0 if boss else 1 + 0.16 * (floor - 1)
        self.max_hp = self.hp = int(d['hp'] * hp_scale * (2.2 if self.elite else 1.0))
        self.dmg = int(d['dmg'] * dmg_scale * (1.25 if self.elite else 1.0))
        self.speed = d['speed'] * min(1.3, 1 + 0.03 * (floor - 1))
        self.xp = int(d['xp'] * (1 + 0.22 * (floor - 1)) * (2.5 if self.elite else 1.0))
        self.sight = d['sight']
        self.awake = False
        self.flash = 0.0
        self.anim = random.random() * 5
        self.kx = self.ky = 0.0
        self.shoot_t = random.uniform(1.0, 2.5)
        self.strafe = random.choice((-1, 1))
        self.phase = 1
        self.stun_t = self.slow_t = self.poison_t = 0.0
        self.poison_dps, self.poison_tick = 0.0, 0.5
        self.state = 'chase'
        self.state_t = random.uniform(1.0, 2.5)
        self.warn = False
        self.vec = (0.0, 0.0)
        self.tele_t = random.uniform(3, 6)
        self.summon_t = 10.0
        self.spiral_t, self.spiral_on, self.spiral_ang, self.spiral_shot = 5.0, 0.0, 0.0, 0.0
        self.name = BOSS_NAMES.get(kind, '')

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
                game.damage_enemy(self, max(1, int(self.poison_dps * 0.5)), crit=False, knock=False, dot=True)
                if self.hp <= 0:
                    return
        self.slow_t = max(0.0, self.slow_t - dt)

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
        if not self.awake:
            see = d.line_clear(self.x, self.y, p.x, p.y) or self.kind == 'wraith'
            if dpl < self.sight and see:
                self.awake = True
                if self.kind in BOSS_KINDS:
                    game.audio.play('boss'); game.shake = 0.6
                    game.show_banner(f"{self.name.title()} awakens!")
            else:
                return

        tx, ty = self.target_pos(game)
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy) or 1.0
        nx, ny = dx / dist, dy / dist
        pnx, pny = (p.x - self.x) / dpl, (p.y - self.y) / dpl      # direction to the PLAYER (for shooters)

        self.state_t -= dt
        sp = self.speed * (0.45 if self.slow_t > 0 else 1.0)
        k = self.kind

        if k == 'slime':
            hop = 0.25 + 0.75 * max(0.0, math.sin(self.anim * 4))
            self.move(nx * sp * hop * dt, ny * sp * hop * dt, d)

        elif k == 'bat':
            w = math.sin(self.anim * 5)
            vx, vy = nx - ny * w * 0.9, ny + nx * w * 0.9
            l = math.hypot(vx, vy) or 1
            self.move(vx / l * sp * dt, vy / l * sp * dt, d)

        elif k == 'skeleton':
            self.keep_distance(pnx, pny, dpl, sp, dt, d, 230, 140)
            self.shoot_t -= dt
            if self.shoot_t <= 0 and dpl < 400 and d.line_clear(self.x, self.y, p.x, p.y):
                self.shoot_t = 2.3
                game.projectiles.append(Projectile(self.x, self.y, pnx * 210, pny * 210, self.dmg, (240, 240, 220)))
                game.audio.play('shoot')

        elif k == 'goblin':      # runs at you, then does a sneaky LUNGE
            if self.state == 'chase':
                self.move(nx * sp * dt, ny * sp * dt, d)
                if self.state_t <= 0 and 90 < dist < 260 and d.line_clear(self.x, self.y, tx, ty):
                    self.state, self.state_t, self.warn = 'wind', 0.4, True
                    game.audio.play('warn')
            elif self.state == 'wind':
                if self.state_t <= 0:
                    self.state, self.state_t, self.warn = 'lunge', 0.35, False
                    self.vec = (nx, ny)
            else:
                self.move(self.vec[0] * sp * 4.2 * dt, self.vec[1] * sp * 4.2 * dt, d)
                if self.state_t <= 0:
                    self.state, self.state_t = 'chase', random.uniform(2.5, 4.0)

        elif k == 'imp':         # runs up and EXPLODES
            if self.state == 'chase':
                self.move(nx * sp * dt, ny * sp * dt, d)
                if dist < 60:
                    self.state, self.state_t, self.warn = 'fuse', 0.7, True
                    game.audio.play('warn')
            else:
                self.move(nx * sp * 0.3 * dt, ny * sp * 0.3 * dt, d)
                if self.state_t <= 0:
                    game.explosion(self.x, self.y, 85, int(self.dmg * 1.6))
                    if self in game.enemies:
                        game.enemies.remove(self)
                    return

        elif k == 'spider':      # keeps away and spits slowing webs
            self.keep_distance(pnx, pny, dpl, sp, dt, d, 240, 150, strafe=0.9)
            self.shoot_t -= dt
            if self.shoot_t <= 0 and dpl < 380 and d.line_clear(self.x, self.y, p.x, p.y):
                self.shoot_t = 2.6
                game.projectiles.append(Projectile(self.x, self.y, pnx * 230, pny * 230, max(1, self.dmg // 2),
                                                   (235, 235, 245), 6, effect='slow'))
                game.audio.play('shoot')

        elif k == 'brute':       # slow, but SLAMS the ground (watch for the "!")
            if self.state == 'chase':
                self.move(nx * sp * dt, ny * sp * dt, d)
                if dist < 125 and self.state_t <= 0:
                    self.state, self.state_t, self.warn = 'wind', 0.75, True
                    game.audio.play('warn')
            elif self.state_t <= 0:
                game.slam(self.x, self.y, 100, int(self.dmg * 1.3))
                self.state, self.state_t, self.warn = 'chase', 2.6, False

        elif k == 'wraith':      # floats THROUGH walls
            f = 0.6 + 0.4 * math.sin(self.anim * 2)
            self.x += nx * sp * f * dt
            self.y += ny * sp * f * dt

        elif k == 'cultist':     # blinks around and fires 3 dark bolts
            self.keep_distance(pnx, pny, dpl, sp, dt, d, 260, 170)
            self.shoot_t -= dt
            if self.shoot_t <= 0 and dpl < 420 and d.line_clear(self.x, self.y, p.x, p.y):
                self.shoot_t = 3.0
                base = math.atan2(pny, pnx)
                for da in (-0.28, 0, 0.28):
                    game.projectiles.append(Projectile(self.x, self.y, math.cos(base + da) * 190,
                                                       math.sin(base + da) * 190, self.dmg, (210, 70, 255), 6))
                game.audio.play('shoot')
            self.tele_t -= dt
            if self.tele_t <= 0:
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
                self.move(nx * sp * dt, ny * sp * dt, d)
                if self.state_t <= 0:
                    if dist < 160:
                        self.state, self.state_t, self.warn = 'slamwind', 0.9, True
                    else:
                        self.state, self.state_t, self.warn = 'wind', 0.8, True
                    game.audio.play('warn')
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
                self.move(nx * sp * dt, ny * sp * dt, d)
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

        # touching the player or an ally hurts them
        if k != 'imp':
            r = self.rect
            if r.colliderect(p.rect):
                p.hurt(self.dmg, self.x, self.y, game)
            for m in game.minions:
                if r.colliderect(m.rect):
                    m.hurt(self.dmg, game)

    def keep_distance(self, nx, ny, dist, sp, dt, d, far, near, strafe=0.6):
        if dist > far:
            mx, my = nx, ny
        elif dist < near:
            mx, my = -nx, -ny
        else:
            mx, my = -ny * self.strafe * strafe, nx * self.strafe * strafe
        self.move(mx * sp * dt, my * sp * dt, d)


# ====================================================================== ALLIES
MINION_TYPES = {
    'skeleton':  dict(hp=45,  speed=110, mult=0.9, size=22, role='melee',  cd=0.7),
    'archer':    dict(hp=30,  speed=95,  mult=0.75, size=22, role='ranged', cd=1.3),
    'bonebrute': dict(hp=130, speed=72,  mult=1.5, size=30, role='melee',  cd=1.0),
    'wolf':      dict(hp=70,  speed=165, mult=0.8, size=22, role='melee',  cd=0.55),
    'hawk':      dict(hp=38,  speed=190, mult=1.1, size=18, role='swoop',  cd=1.6),
    'bear':      dict(hp=280, speed=95,  mult=1.6, size=34, role='cleave', cd=1.0),
}


class Minion(Entity):
    """A friend that fights FOR you: raised undead or summoned beasts."""
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
        dmg = max(2, int(p.dmg * self.mult))
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
            if self.role in ('melee', 'cleave'):
                if dist > touch - 4:
                    mx, my = nx * sp, ny * sp
                if self.cd <= 0 and dist < touch + (26 if self.role == 'cleave' else 4):
                    self.cd = self.cd_base
                    self.lunge = 0.14
                    self.vec = (nx, ny)
                    if self.role == 'cleave':
                        game.audio.play('roar') if random.random() < 0.3 else None
                        game.aoe(self.x, self.y, 62, dmg, knock=170, color=(235, 190, 120), ring=False)
                        game.burst(self.x + nx * 20, self.y + ny * 20, (240, 210, 160), 8, 140)
                    else:
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
                    game.bolts.append(Bolt(self.x, self.y, nx * 380, ny * 380, dmg, (225, 235, 255), 4, 1.2, kind='arrow'))
                    game.audio.play('shoot')
            elif self.role == 'swoop':                  # hawk: circle, dive, retreat
                if self.state == 'circle':
                    self.orbit += dt * 3.2
                    gx, gy = t.x + math.cos(self.orbit) * 95, t.y + math.sin(self.orbit) * 95
                    gd = math.hypot(gx - self.x, gy - self.y) or 1
                    mx, my = (gx - self.x) / gd * sp, (gy - self.y) / gd * sp
                    if self.state_t <= 0 and self.cd <= 0:
                        self.state, self.state_t, self.vec = 'dive', 0.5, (nx, ny)
                        game.audio.play('screech') if random.random() < 0.5 else None
                elif self.state == 'dive':
                    mx, my = self.vec[0] * sp * 2.4, self.vec[1] * sp * 2.4
                    if self.rect.colliderect(t.rect):
                        self.cd = self.cd_base
                        game.minion_hit(self, t, dmg)
                        self.state, self.state_t = 'retreat', 0.6
                    elif self.state_t <= 0:
                        self.state, self.state_t = 'retreat', 0.5
                else:
                    mx, my = -nx * sp, -ny * sp
                    if self.state_t <= 0:
                        self.state, self.state_t = 'circle', random.uniform(0.6, 1.4)
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
        if random.random() < 0.5:
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
                 kind='magic', crit=False, leech=False):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.dmg, self.color, self.radius, self.life = dmg, color, radius, life
        self.aoe, self.pierce, self.kind, self.crit, self.leech = aoe, pierce, kind, crit, leech
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
        if random.random() < 0.8:
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
                self.hit.add(id(e))
                if self.aoe:
                    self.explode(game)
                    return
                game.damage_enemy(e, int(self.dmg), crit=self.crit, origin=(self.x - self.vx, self.y - self.vy),
                                  leech=self.leech)
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
