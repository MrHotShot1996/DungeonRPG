"""ai.py - the monsters' shared BRAIN.

Every floor gets one Brain. It helps each monster:
  * find its way around walls (a 'flow map' that points every floor tile toward the hero),
  * spread out and come at you from the sides instead of queuing up in a line,
  * not pile on top of each other or get stuck on corners,
  * aim a little ahead of where you are running (on deeper floors),
  * sidestep your arrows and spells now and then (on deeper floors),
  * and take TURNS: only a few melee monsters press in at once (the rest circle around, waiting for a gap),
    and only a few may wind up a big attack or shoot at the same moment.

How clever monsters are depends on the floor ('smarts', from 0.0 on floor 1 to 1.0 deep down).
The knobs for that are AI_SMARTS_FULL_FLOOR and AI_DIFFICULTY in settings.py.
"""
import math
import random
from collections import deque

import pygame
from settings import TILE, MAP_W, MAP_H, WIDTH, HEIGHT, AI_SMARTS_FULL_FLOOR, AI_DIFFICULTY

BOSS_KINDS = ('boss', 'warlord', 'lich', 'demon')
TOKEN_KINDS = ('goblin', 'brute', 'imp')       # their big attacks have to take turns
SHOOTER_KINDS = ('skeleton', 'spider', 'cultist')
DODGER_KINDS = ('goblin', 'skeleton', 'spider', 'cultist', 'bat')
PRESSER_KINDS = ('slime', 'bat', 'goblin', 'imp', 'brute', 'wraith')   # melee monsters that take turns to close in
CIRCLE_RANGE = 260                              # melee monsters this close to you join the 'take turns' circle
TURN_TIME, REST_TIME = 3.5, 2.0                 # a melee monster's turn lasts this long; then it backs off for a bit
SHOT_WINDOW = 0.7                               # seconds: 'how many monsters may shoot in this long'
NEIGHBOURS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def smarts_for(floor, elite=False):
    """0.0 (floor 1, simple monsters) .. 1.0 (fully clever). Elites are a bit cleverer than the rest."""
    s = (floor - 1) / max(1, AI_SMARTS_FULL_FLOOR - 1) * AI_DIFFICULTY
    if elite:
        s += 0.15 * AI_DIFFICULTY
    return max(0.0, min(1.0, s))


# ---- everything that grows with 'smarts' lives here, so it's easy to read and tweak
def lead_chance(s):        # the chance a shot is aimed AHEAD of a running hero (the rest aim right at you)
    return 0.0 if s < 0.12 else min(0.7, 0.8 * (s - 0.12) / 0.88)


def dodge_chance(s):       # the chance to sidestep ONE of your shots that is about to hit
    return 0.0 if s < 0.35 else 0.25 * (s - 0.35) / 0.65


def max_windups(s):        # how many monsters may be winding up a big attack at the same time
    return 1 if s < 0.5 else 2 if s < 0.9 else 3


def max_shots(s):          # how many monsters may shoot in one SHOT_WINDOW
    return 1 if s < 0.4 else 2 if s < 0.8 else 3


def react_time(s):         # the pause after a monster first spots you before it may attack
    return 0.65 - 0.35 * s


def memory_time(s):        # how long a monster keeps hunting you after it loses sight of you
    return 3.5 + 6.5 * s


def alert_radius(s):       # a monster that spots you warns friends this close to it (who can see it)
    return 50 + 190 * s * s           # (grows slowly at first, faster on deep floors)


def flank_amount(s):       # how hard melee monsters try to come at you from the sides
    return 0.0 if s < 0.2 else 0.3 + 0.45 * s


def max_attackers(s):      # how many melee monsters may close in on you at once (the rest circle and wait)
    return 2 if s < 0.35 else 3 if s < 0.75 else 4


def lunge_lead(s):         # goblins aim their lunge partly toward where you are running (never all the way)
    return 0.0 if s < 0.12 else 0.5 * (s - 0.12) / 0.88


class Brain:
    def __init__(self, game):
        self.game = game
        self.dungeon = game.dungeon
        self.smarts = smarts_for(game.floor)
        self.field = None             # the flow map: steps from every floor tile to the hero (None = can't reach)
        self.field_tile = None
        self.pv = pygame.Vector2(0, 0)  # the hero's running speed and direction (smoothed)
        self.last_p = None
        self.shots = deque()          # times of recent monster shots
        self.windups = 0              # monsters winding up a big attack right now
        self.circle_t = 0.0           # when to re-pick which melee monsters may close in
        self.t = 0.0
        self.dt = 0.0

    # ------------------------------------------------------------------ every frame
    def update(self, dt, lead=True):
        """`lead` is False for Duo's second brain (each hero has one): the shared jobs run only once."""
        g = self.game
        p = g.player
        self.t += dt
        self.dt = dt
        if self.last_p is not None and dt > 0:
            vx, vy = (p.x - self.last_p[0]) / dt, (p.y - self.last_p[1]) / dt
            if vx * vx + vy * vy > 520 ** 2:          # a blink or a swap, not running: don't 'predict' that
                vx = vy = 0.0
            a = min(1.0, dt * 10)
            self.pv.x += (vx - self.pv.x) * a
            self.pv.y += (vy - self.pv.y) * a
        self.last_p = (p.x, p.y)
        tile = (int(p.x // TILE), int(p.y // TILE))
        if tile != self.field_tile and not self.dungeon.is_wall(*tile):
            self.build_field(tile)
        while self.shots and self.t - self.shots[0] > SHOT_WINDOW:
            self.shots.popleft()
        self.windups = sum(1 for e in g.enemies if e.warn and e.kind in TOKEN_KINDS)
        self.circle_t -= dt
        for e in g.enemies:
            if e.rest_t > 0 and lead:
                e.rest_t -= dt
        if self.circle_t <= 0:
            self.circle_t = 0.25
            self.pick_attackers(0.25)
        if lead:
            self.separate(dt)

    def pick_attackers(self, dt):
        """The closest few melee monsters may close in and hit you; the others circle around at a distance
        until a spot is free. Monsters already attacking keep their spot for a while (so they don't flip-flop),
        but when others are waiting, a monster whose turn has lasted TURN_TIME backs off and lets one in."""
        p = self.game.player
        near = []
        for e in self.game.enemies:
            if e.kind not in PRESSER_KINDS or not e.awake:
                continue
            if getattr(e, 'tgt', p) is not p:       # (Duo: the other hero's brain looks after this one)
                continue
            d = math.hypot(e.x - p.x, e.y - p.y)
            if d > CIRCLE_RANGE or (e.state == 'chase' and not e.sees):
                e.attacker, e.turn_t = True, 0.0  # far away (or round a corner): free to come closer
                continue
            if e.warn or e.state != 'chase':
                d -= 1000                       # in the middle of an attack: always keeps its spot
            elif e.rest_t > 0:
                d += 1000                       # just had a turn: goes to the back of the queue
            elif e.attacker:
                d -= 45
            near.append((d, e))
        near.sort(key=lambda t: t[0])
        n = max_attackers(self.smarts)
        waiting = len(near) > n
        for i, (d, e) in enumerate(near):
            if i < n:
                if e.attacker:
                    e.turn_t += dt
                e.attacker = True
                if waiting and e.turn_t > TURN_TIME and not e.warn and e.state == 'chase':
                    e.attacker, e.turn_t, e.rest_t = False, 0.0, REST_TIME   # turn over: step back
            else:
                e.attacker, e.turn_t = False, 0.0

    def ring_point(self, e):
        """Where a waiting melee monster should stand: on a circle around the hero, slowly walking round it."""
        p = self.game.player
        dx, dy = e.x - p.x, e.y - p.y
        L = math.hypot(dx, dy)
        if L < 1:
            dx, dy, L = 1.0, 0.0, 1.0
        a = math.atan2(dy, dx) + 0.35 * e.strafe
        r = 130 + e.w / 2
        return p.x + math.cos(a) * r, p.y + math.sin(a) * r

    def build_field(self, start):
        """Breadth-first 'flood' out from the hero's tile: every tile learns how many steps away the hero is."""
        d = self.dungeon
        field = [[None] * MAP_W for _ in range(MAP_H)]
        sx, sy = start
        field[sy][sx] = 0
        q = deque([start])
        grid = d.grid
        while q:
            x, y = q.popleft()
            n = field[y][x] + 1
            for ox, oy in NEIGHBOURS:
                nx, ny = x + ox, y + oy
                if 0 <= nx < MAP_W and 0 <= ny < MAP_H and field[ny][nx] is None and grid[ny][nx]:
                    field[ny][nx] = n
                    q.append((nx, ny))
        self.field, self.field_tile = field, start

    def steps_from(self, x, y):
        """How many tiles a monster at (x, y) must walk to reach the hero (None = no way there)."""
        tx, ty = int(x // TILE), int(y // TILE)
        if self.field is None or not (0 <= tx < MAP_W and 0 <= ty < MAP_H):
            return None
        return self.field[ty][tx]

    def separate(self, dt):
        """Monsters gently push apart so they don't stand inside each other. Bosses push but are not pushed."""
        es = [e for e in self.game.enemies if e.awake and e.freeze_t <= 0]
        n = len(es)
        k = min(1.0, dt * 9)
        for i in range(n):
            a = es[i]
            for j in range(i + 1, n):
                b = es[j]
                dx, dy = b.x - a.x, b.y - a.y
                want = (a.w + b.w) * 0.5 + 4
                if abs(dx) >= want or abs(dy) >= want:
                    continue
                dd = dx * dx + dy * dy
                if dd >= want * want:
                    continue
                dist = math.sqrt(dd)
                if dist < 0.01:
                    ang = random.random() * 6.2832
                    dx, dy, dist = math.cos(ang), math.sin(ang), 1.0
                push = (want - dist) * k
                ux, uy = dx / dist, dy / dist
                ab, bb = a.kind in BOSS_KINDS, b.kind in BOSS_KINDS
                if ab and bb:
                    continue
                sa = 0.0 if ab else (1.0 if bb else 0.5)
                sb = 0.0 if bb else (1.0 if ab else 0.5)
                if sa:
                    a.move(-ux * push * sa, -uy * push * sa, self.dungeon)
                if sb:
                    b.move(ux * push * sb, uy * push * sb, self.dungeon)

    # ------------------------------------------------------------------ seeing
    def wide_clear(self, x1, y1, x2, y2, half):
        """Like line_clear, but for a body `half` pixels wide on each side - so big monsters don't clip corners."""
        d = self.dungeon
        if not d.line_clear(x1, y1, x2, y2):
            return False
        L = math.hypot(x2 - x1, y2 - y1)
        if L < 1 or half < 2:
            return True
        px, py = -(y2 - y1) / L * half, (x2 - x1) / L * half
        return d.line_clear(x1 + px, y1 + py, x2 + px, y2 + py) and d.line_clear(x1 - px, y1 - py, x2 - px, y2 - py)

    def clear_run(self, e, tx, ty):
        """Can monster `e` CHARGE straight at (tx, ty) without hitting a wall?"""
        return self.wide_clear(e.x, e.y, tx, ty, e.w / 2 - 3)

    def on_screen(self, x, y, margin=24):
        c = self.game.cam
        return c.x + margin < x < c.x + WIDTH - margin and c.y + margin < y < c.y + HEIGHT - margin

    def sees_player(self, e):
        p = self.game.player
        return e.kind == 'wraith' or self.dungeon.line_clear(e.x, e.y, p.x, p.y)

    # ------------------------------------------------------------------ moving
    def waypoint(self, e):
        """The furthest spot along the flow map that the monster can walk to in a straight line."""
        f = self.field
        tx, ty = int(e.x // TILE), int(e.y // TILE)
        if f is None or not (0 <= tx < MAP_W and 0 <= ty < MAP_H) or f[ty][tx] is None:
            return None
        p = self.game.player
        path = []
        x, y = tx, ty
        for _ in range(7):                              # walk 'downhill' toward the hero a few tiles
            cur = f[y][x]
            if cur == 0:
                break
            best, bd = None, 1e9
            for ox, oy in NEIGHBOURS:
                nx, ny = x + ox, y + oy
                if 0 <= nx < MAP_W and 0 <= ny < MAP_H and f[ny][nx] is not None and f[ny][nx] < cur:
                    dd = ((nx + 0.5) * TILE - p.x) ** 2 + ((ny + 0.5) * TILE - p.y) ** 2
                    if dd < bd:
                        best, bd = (nx, ny), dd
            if best is None:
                break
            x, y = best
            path.append(best)
        if not path:
            return None
        half = e.w / 2 - 3
        for (cx, cy) in reversed(path):                 # 'string-pull': skip tiles we can cut straight to
            wx, wy = (cx + 0.5) * TILE, (cy + 0.5) * TILE
            if self.wide_clear(e.x, e.y, wx, wy, half):
                return wx, wy
        return (path[0][0] + 0.5) * TILE, (path[0][1] + 0.5) * TILE

    def steer(self, e, tx, ty, flank=True):
        """Which way (a unit vector) should monster `e` walk to reach (tx, ty)?"""
        if e.unstick_t > 0:
            return e.unstick_dir
        e.nav_t -= self.dt
        if e.nav_pt is not None and math.hypot(e.nav_pt[0] - e.x, e.nav_pt[1] - e.y) < 8:
            e.nav_t = 0.0
        if e.nav_t <= 0:
            e.nav_t = 0.12 + random.random() * 0.06
            if e.kind == 'wraith' or self.wide_clear(e.x, e.y, tx, ty, e.w / 2 - 3):
                e.nav_pt = None
            else:
                e.nav_pt = self.waypoint(e)
                if e.nav_pt is None and not self.dungeon.line_clear(e.x, e.y, tx, ty):
                    e.nav_pt = None                     # (cut off from the hero: just try straight)
            e.flank = self.flank_dir(e, tx, ty) if (flank and e.nav_pt is None) else (0.0, 0.0)
        gx, gy = e.nav_pt if e.nav_pt is not None else (tx, ty)
        dx, dy = gx - e.x, gy - e.y
        L = math.hypot(dx, dy)
        if L < 0.01:
            return 0.0, 0.0
        dx, dy = dx / L + e.flank[0], dy / L + e.flank[1]
        L = math.hypot(dx, dy) or 1.0
        return dx / L, dy / L

    def flank_dir(self, e, tx, ty):
        """If a friend is already standing between this monster and its target, step around to the side."""
        amt = flank_amount(e.smarts)
        if amt <= 0:
            return 0.0, 0.0
        dx, dy = tx - e.x, ty - e.y
        dist = math.hypot(dx, dy)
        if dist < 70 or dist > 300:
            return 0.0, 0.0
        my_ang = math.atan2(-dy, -dx)                   # where I stand, seen from the target
        side = 0.0
        for o in self.game.enemies:
            if o is e or not o.awake or o.kind in ('wraith',) + BOSS_KINDS + SHOOTER_KINDS:
                continue
            od = math.hypot(o.x - tx, o.y - ty)
            if od >= dist - 8 or math.hypot(o.x - e.x, o.y - e.y) > 170:
                continue
            da = (math.atan2(o.y - ty, o.x - tx) - my_ang + math.pi) % 6.2832 - math.pi
            if abs(da) < 0.5:
                side += -1.0 if da > 0 else 1.0         # go round the side AWAY from that friend
        if side == 0.0:
            return 0.0, 0.0
        sgn = 1.0 if side > 0 else -1.0
        nx, ny = dx / dist, dy / dist
        return -ny * sgn * amt * 1.3, nx * sgn * amt * 1.3

    def track(self, e, ox, oy, want, dx, dy, dt):
        """Notice when a monster keeps walking into a wall, and send it sideways for a moment."""
        if e.unstick_t > 0:
            e.unstick_t -= dt
            return
        if want < 0.2:
            e.stuck_t = 0.0
            return
        moved = math.hypot(e.x - ox, e.y - oy)
        if moved < want * 0.3:
            e.stuck_t += dt
        else:
            e.stuck_t = max(0.0, e.stuck_t - dt * 2)
        if e.stuck_t > 0.35:
            e.stuck_t = 0.0
            e.nav_t = 0.0
            opts = [(-dy, dx), (dy, -dx)]
            random.shuffle(opts)
            for sx, sy in opts:
                probe = pygame.Rect(int(e.x + sx * 18 - e.w / 2), int(e.y + sy * 18 - e.h / 2), e.w, e.h)
                if not self.dungeon.hits_wall(probe):
                    break
            else:
                sx, sy = -dx, -dy
            e.unstick_dir = (sx, sy)
            e.unstick_t = 0.3

    def kite(self, e, far, near, strafe):
        """Ranged monsters: keep between `near` and `far` from the hero, in the open, where they can see him.
        Re-decides a few times a second. Returns a unit direction."""
        p = self.game.player
        if math.hypot(p.x - e.x, p.y - e.y) > far * 1.25 or not self.sees_player(e):
            return self.steer(e, p.x, p.y, flank=False)  # too far, or can't see him: walk closer (around walls)
        e.nav_t -= self.dt
        if e.nav_t > 0 and e.unstick_t <= 0:
            return e.kite_dir
        if e.unstick_t > 0:
            return e.unstick_dir
        e.nav_t = 0.18 + random.random() * 0.08
        d = self.dungeon
        s = e.smarts
        dist = math.hypot(p.x - e.x, p.y - e.y) or 1.0
        tnx, tny = (p.x - e.x) / dist, (p.y - e.y) / dist
        best, bs = None, -1e9
        L = 36
        for i in range(8):
            a = i * 0.7854
            cx, cy = math.cos(a), math.sin(a)
            px, py = e.x + cx * L, e.y + cy * L
            if d.hits_wall(pygame.Rect(int(px - e.w / 2), int(py - e.h / 2), e.w, e.h)):
                continue
            nd = math.hypot(p.x - px, p.y - py)
            if nd < near:
                sc = -(near - nd) / near * 3.0
            elif nd > far:
                sc = -(nd - far) / far * 2.0
            else:
                sc = 0.0
            sc += (-ny_dot(cx, cy, tnx, tny) * e.strafe) * 0.35 * strafe   # circle around the hero
            sc += (cx * e.kite_dir[0] + cy * e.kite_dir[1]) * 0.3            # don't jitter
            if not d.line_clear(px, py, p.x, p.y):
                sc -= 0.6 + 0.8 * s                     # keep a clear shot
            if s > 0.2 and d.hits_wall(pygame.Rect(int(px + cx * L - e.w / 2), int(py + cy * L - e.h / 2), e.w, e.h)):
                sc -= 0.5 * s                           # don't back into corners
            sc += random.random() * 0.08
            if sc > bs:
                best, bs = (cx, cy), sc
        if best is None:                                # boxed in: flip the circling direction
            e.strafe *= -1
            best = (-tnx, -tny)
        e.kite_dir = best
        return best

    # ------------------------------------------------------------------ attacking
    def can_windup(self, e):
        if e.react_t > 0 or not e.attacker:
            return False
        return self.windups < max_windups(e.smarts)

    def start_windup(self, e):
        self.windups += 1

    def can_shoot(self, e):
        if e.react_t > 0 or not self.on_screen(e.x, e.y):
            return False
        return len(self.shots) < max_shots(e.smarts)

    def shot_fired(self):
        self.shots.append(self.t)

    def aim(self, e, speed, ox=None, oy=None, lead=None):
        """Where should a shot (that flies at `speed`) aim? On deeper floors, a little ahead of a running hero.
        Returns a unit direction."""
        p = self.game.player
        ox = e.x if ox is None else ox
        oy = e.y if oy is None else oy
        tx, ty = p.x, p.y
        if lead is None:                                # shots: some aim ahead of you, the rest right at you
            lead = 1.0 if random.random() < lead_chance(e.smarts) else 0.0
        if lead > 0 and self.pv.length_squared() > 400:
            t = intercept_time(p.x - ox, p.y - oy, self.pv.x, self.pv.y, speed)
            px, py = self.pv.x * t * lead, self.pv.y * t * lead
            L = math.hypot(px, py)
            if L > 280:
                px, py = px / L * 280, py / L * 280
            if self.dungeon.line_clear(ox, oy, p.x + px, p.y + py):
                tx, ty = p.x + px, p.y + py
        dx, dy = tx - ox, ty - oy
        L = math.hypot(dx, dy) or 1.0
        return dx / L, dy / L

    # ------------------------------------------------------------------ dodging
    def try_dodge(self, e):
        """Sidestep a hero shot that is about to hit. Each shot gets ONE roll per monster, and then the
        monster needs a rest before it can dodge again - so most of your shots still land."""
        ch = dodge_chance(e.smarts)
        if ch <= 0 or e.dodge_cd > 0 or e.kind not in DODGER_KINDS:
            return
        for b in self.game.bolts:
            if not b.alive:
                continue
            key = id(b)
            if key in e.seen:
                continue
            rx, ry = e.x - b.x, e.y - b.y
            vv = b.vx * b.vx + b.vy * b.vy
            if vv < 1 or rx * rx + ry * ry > 230 * 230:
                continue
            t = (rx * b.vx + ry * b.vy) / vv              # when it passes closest to me
            if t < 0.05 or t > 0.45:
                continue
            mx, my = b.x + b.vx * t - e.x, b.y + b.vy * t - e.y
            if mx * mx + my * my > (e.w / 2 + b.radius + 8) ** 2:
                continue
            if len(e.seen) > 60:
                e.seen.clear()
            e.seen.add(key)
            if random.random() >= ch:
                continue
            sp = math.sqrt(vv)
            px, py = -b.vy / sp, b.vx / sp                  # sideways to the shot...
            if px * mx + py * my > 0:                       # ...on the side away from where it will pass
                px, py = -px, -py
            for sx, sy in ((px, py), (-px, -py)):
                probe = pygame.Rect(int(e.x + sx * 30 - e.w / 2), int(e.y + sy * 30 - e.h / 2), e.w, e.h)
                if not self.dungeon.hits_wall(probe):
                    e.dodge_dir, e.dodge_t, e.dodge_cd = (sx, sy), 0.22, 2.4 - 0.8 * e.smarts
                    self.game.burst(e.x, e.y + e.h / 2, (170, 160, 150), 5, 90)
                    return
            return

    # ------------------------------------------------------------------ waking up
    def on_wake(self, e, alerted=False):
        """A monster just noticed the hero."""
        e.react_t = react_time(e.smarts) + (0.25 if alerted else 0.0)
        e.lost_t = 0.0
        if e.kind in BOSS_KINDS:
            return
        self.game.float_text(e.x, e.y - e.h / 2 - 14, "!", (255, 220, 90))
        if alerted:
            return
        r = alert_radius(e.smarts)
        for o in self.game.enemies:
            if o.awake or o is e or o.kind in BOSS_KINDS:
                continue
            if math.hypot(o.x - e.x, o.y - e.y) < r and self.dungeon.line_clear(e.x, e.y, o.x, o.y):
                o.awake = True
                self.on_wake(o, alerted=True)


def intercept_time(rx, ry, vx, vy, speed, longest=1.6):
    """How long until a shot fired at `speed` can meet a target that is at (rx, ry) from us, running at (vx, vy)?
    (Solves |r + v*t| = speed*t.) If it can't catch the target, just use the straight-line time."""
    a = vx * vx + vy * vy - speed * speed
    b = 2 * (rx * vx + ry * vy)
    c = rx * rx + ry * ry
    t = None
    if abs(a) < 1e-6:
        if b < 0:
            t = -c / b
    else:
        disc = b * b - 4 * a * c
        if disc >= 0:
            r = math.sqrt(disc)
            ts = [x for x in ((-b - r) / (2 * a), (-b + r) / (2 * a)) if x > 0]
            if ts:
                t = min(ts)
    if t is None:
        t = math.sqrt(c) / max(1.0, speed)
    return min(t, longest)


def ny_dot(cx, cy, tnx, tny):
    """How much (cx, cy) points sideways (anticlockwise) relative to the direction (tnx, tny)."""
    return cx * tny - cy * tnx
