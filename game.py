"""game.py - the BRAIN of the game: menus, heroes, abilities, allies, fighting, lighting, drawing the screen."""
import math
import os
import random
import sys

import pygame

from settings import *
from dungeon import Dungeon, FLOOR
from entities import (Player, Enemy, Minion, Corpse, Item, Particle, FloatText, Bolt, BOSS_KINDS, xp_for)
from sprites import Sprites, make_icon, ui_icon, shade, add
from sounds import Audio, MUSIC_TRACKS
from classes import CLASSES, CLASS_ORDER, ABILITIES, UNLOCK_LEVELS
from biomes import biome, floor_name
from inputs import (Input, ACTION_LABELS, GAME_ACTIONS, PAD_ACTIONS, PAD_LABELS, DEFAULT_SETTINGS, draw_pad_icon)

V2 = pygame.Vector2

# what a corpse becomes when a Necromancer raises it
CORPSE_TO_MINION = {'slime': 'skeleton', 'bat': 'skeleton', 'goblin': 'skeleton', 'imp': 'skeleton', 'spider': 'skeleton',
                    'skeleton': 'archer', 'cultist': 'archer', 'wraith': 'archer', 'brute': 'bonebrute'}
MINION_CAPS = {'undead': 8, 'army': 6, 'wolf': 4, 'hawk': 2, 'bear': 1}
KNOCK_RESIST = {'boss': 0.2, 'warlord': 0.15, 'brute': 0.3}
FLYERS = {'bat': 12, 'wraith': 8}                      # monsters that float above their shadow
FREEZE_TIME = 2.5                                      # Ghala's Frozen Heart: seconds a monster stays frozen
FLOWER_TIME, FLOWER_RADIUS, FLOWER_COUNT = 6.0, 76, 6  # Ghala's Flower Ring: how long, how wide, how many


def spawn_weights(floor):
    """Which monsters can appear on which floor (and how often)."""
    return {
        'slime': max(1, 6 - floor // 2),
        'bat': 3,
        'goblin': 2 if floor == 1 else 3,
        'skeleton': min(6, (floor - 1) * 2),
        'imp': 3 if floor >= 2 else 0,
        'spider': 3 if floor >= 2 else 0,
        'brute': (2 + floor // 4) if floor >= 3 else 0,
        'wraith': 2 if floor >= 3 else 0,
        'cultist': 3 if floor >= 4 else 0,
    }


class Game:
    def __init__(self):
        pygame.display.init()
        pygame.font.init()
        try:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
        except Exception:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        # when bundled into an .exe (PyInstaller), __file__ lives in a throwaway temp
        # folder, so settings must be saved next to the real .exe instead
        base_dir = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, 'frozen', False) \
            else os.path.dirname(os.path.abspath(__file__))
        self.audio = Audio(os.path.join(base_dir, 'audio.json'))
        self.sprites = Sprites()
        pygame.display.set_icon(pygame.transform.smoothscale(self.sprites.player[('knight', 'down', 0)], (32, 32)))
        self.fonts, self._text_cache, self._panels, self._masks = {}, {}, {}, {}
        self.icons = {n: make_icon(a['icon'], a['color']) for n, a in ABILITIES.items()}
        self.ui = {'coin': ui_icon('coin', 26), 'potion': ui_icon('potion', 26), 'dash': ui_icon('dash', 26),
                   'potion_big': ui_icon('potion', 40), 'dash_big': ui_icon('dash', 40)}
        self.overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.glow_layer = pygame.Surface((WIDTH // 4, HEIGHT // 4))
        self.vignette = self.make_vignette((0, 0, 0), 215)
        self.vignette_red = self.make_vignette((150, 0, 10), 235)
        self.mote_img = self.sprites.glow(5, (255, 255, 255), 1.0)
        self.motes = [[random.uniform(0, WIDTH), random.uniform(0, HEIGHT), random.uniform(-6, 6),
                       random.uniform(-14, -3), random.random() * 6.28, random.choice((1, 1, 2))] for _ in range(70)]
        self.fog_img = None
        self.state = 'title'
        self.t = 0.0
        self.running = True
        self.player = Player('knight')
        self.dungeon = None
        self.reset_lists()
        self.minions = []
        self.shake = 0.0
        self.hitstop = 0.0
        self.fade = 0.0
        self.banner_text, self.banner_sub, self.banner_t = "", "", 0.0
        self.levelup_t = 0.0
        self.boss_dead_timer = 0.0
        self.floor = 1
        self.run_time = 0.0
        self.stairs = None
        self.torches, self.static_lights = [], []
        self.pal = biome(1)
        self.sel = 0
        self.input = Input(os.path.join(base_dir, 'controls.json'))
        self.toasts = []                      # little pop-up notes ("Controller connected")
        self.menu_sel = 0
        self.return_state = 'title'           # where the Controls screen goes back to
        self.ctl_tab, self.ctl_row, self.ctl_col = 0, 0, 0
        self._hits = []                       # clickable areas, recorded while drawing (for the mouse)
        self._badges = {}
        self.show_stats = False
        self.cam = V2(0, 0)
        self.hp_trail = 0.0
        self.trail = []
        self.level_surf = None
        self.backdrop = self.build_backdrop()

    def reset_lists(self):
        self.enemies, self.items, self.projectiles, self.bolts = [], [], [], []
        self.particles, self.texts, self.rings, self.zaps, self.corpses, self.flashes = [], [], [], [], [], []

    # ------------------------------------------------------------ pretty-picture helpers
    def make_vignette(self, color, strength):
        sw, sh = 160, 90
        s = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for y in range(sh):
            for x in range(sw):
                nx, ny = (x / sw - 0.5) * 2, (y / sh - 0.5) * 2
                d = math.hypot(nx, ny * 1.05)
                a = max(0.0, min(1.0, (d - 0.55) / 0.8)) ** 1.6 * strength
                s.set_at((x, y), (*color, int(a)))
        return pygame.transform.smoothscale(s, (WIDTH, HEIGHT))

    def make_fog(self, color):
        s = pygame.Surface((560, 360), pygame.SRCALPHA)
        for i in range(12):
            f = i / 12
            pygame.draw.ellipse(s, (*color, int(26 * f)), (int((1 - f) * 250), int((1 - f) * 160),
                                                         int(560 - (1 - f) * 500), int(360 - (1 - f) * 320)))
        return s

    def mask(self, r, strength):
        """A soft hole of light for cutting through the darkness."""
        key = (int(round(r / 10)) * 10, int(strength * 10))
        if key not in self._masks:
            rr = max(10, key[0])
            m = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
            for i in range(rr, 0, -3):
                a = int(255 * strength * min(1.0, 1.6 * (1 - i / rr)) ** 0.8)
                pygame.draw.circle(m, (0, 0, 0, a), (rr, rr), i)
            self._masks[key] = m
        return self._masks[key]

    def add_glow(self, sx, sy, radius, color, intensity=1.0):
        """Bright additive glow (bloom + coloured light). Drawn small, then blown up soft."""
        r4 = max(2, int(radius / 4))
        img = self.sprites.glow(r4, color, intensity)
        self.glow_layer.blit(img, (int(sx / 4) - img.get_width() // 2, int(sy / 4) - img.get_height() // 2),
                             special_flags=pygame.BLEND_RGB_ADD)

    # ------------------------------------------------------------ text & panels
    def font(self, size):
        if size not in self.fonts:
            self.fonts[size] = pygame.font.Font(None, size)
        return self.fonts[size]

    def text_img(self, s, size, color, outline=False):
        key = (s, size, color, outline)
        img = self._text_cache.get(key)
        if img is None:
            if len(self._text_cache) > 900:
                self._text_cache.clear()
            f = self.font(size)
            base = f.render(s, True, color)
            w, h = base.get_size()
            if outline:
                dark = f.render(s, True, (12, 8, 16))
                img = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
                for dx in (0, 2, 4):
                    for dy in (0, 2, 4):
                        if (dx, dy) != (2, 2):
                            img.blit(dark, (dx, dy))
                img.blit(base, (3, 3))
            else:
                img = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
                img.blit(f.render(s, True, (0, 0, 0)), (2, 2))
                img.blit(base, (0, 0))
            self._text_cache[key] = img
        return img

    def text(self, s, size, color, pos, center=False, shadow=True, outline=False, surface=None, alpha=255, right=False):
        surface = surface or self.screen
        img = self.text_img(s, size, color, outline)
        if alpha < 255:
            img = img.copy()
            img.set_alpha(alpha)
        r = img.get_rect()
        if center:
            r.center = pos
        elif right:
            r.topright = pos
        else:
            r.topleft = pos
        surface.blit(img, r)
        return r

    def wrap(self, text, size, width):
        f = self.font(size)
        lines, cur = [], ""
        for w in text.split():
            t = (cur + " " + w).strip()
            if f.size(t)[0] <= width:
                cur = t
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def panel(self, rect, alpha=215, border=(176, 140, 78), radius=10, glow=None):
        """A fancy dark panel with a golden frame (used all over the HUD)."""
        rect = pygame.Rect(rect)
        key = (rect.w, rect.h, alpha, border, radius, glow)
        img = self._panels.get(key)
        if img is None:
            img = pygame.Surface((rect.w + 12, rect.h + 12), pygame.SRCALPHA)
            sh = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(sh, (0, 0, 0, 90), sh.get_rect(), border_radius=radius)
            img.blit(sh, (8, 9))
            body = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            for y in range(rect.h):
                t = y / max(1, rect.h - 1)
                pygame.draw.line(body, (int(34 - 14 * t), int(28 - 12 * t), int(46 - 16 * t), alpha), (0, y), (rect.w, y))
            mask = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
            body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            img.blit(body, (4, 4))
            pygame.draw.rect(img, border, (4, 4, rect.w, rect.h), 2, border_radius=radius)
            pygame.draw.rect(img, add(border, -70), (6, 6, rect.w - 4, rect.h - 4), 1, border_radius=max(2, radius - 2))
            if glow:
                pygame.draw.rect(img, (*glow, 90), (2, 2, rect.w + 4, rect.h + 4), 3, border_radius=radius + 2)
            for cx, cy in ((4, 4), (rect.w + 4, 4), (4, rect.h + 4), (rect.w + 4, rect.h + 4)):
                pygame.draw.circle(img, border, (cx, cy), 3)
            self._panels[key] = img
        self.screen.blit(img, (rect.x - 4, rect.y - 4))

    def bar(self, x, y, w, h, frac, c1, c2, trail=None):
        scr = self.screen
        pygame.draw.rect(scr, (14, 10, 20), (x, y, w, h), border_radius=h // 2)
        if trail is not None and trail > frac:
            pygame.draw.rect(scr, (235, 210, 200), (x, y, max(h, int(w * min(1, trail))), h), border_radius=h // 2)
        if frac > 0:
            fw = max(h, int(w * min(1, frac)))
            pygame.draw.rect(scr, c2, (x, y, fw, h), border_radius=h // 2)
            pygame.draw.rect(scr, c1, (x + 2, y + 1, max(2, fw - 4), max(2, h // 2 - 1)), border_radius=h // 3)
        pygame.draw.rect(scr, (230, 220, 200), (x, y, w, h), 2, border_radius=h // 2)

    def dim(self, color, alpha):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((*color, alpha))
        self.screen.blit(s, (0, 0))

    # ------------------------------------------------------------ run setup
    def new_run(self, cls):
        self.player = Player(cls)
        self.minions = []
        self.floor = 1
        self.run_time = 0.0
        self.boss_dead_timer = 0.0
        self.hp_trail = self.player.hp
        self.build_floor()
        self.state = 'playing'

    def build_floor(self):
        self.reset_lists()
        self.pal = biome(self.floor)
        self.fog_img = self.make_fog(self.pal['mote'])
        self.dungeon = Dungeon(self.floor)
        rooms = self.dungeon.rooms
        p = self.player
        cx, cy = rooms[0].center
        p.x, p.y = (cx + 0.5) * TILE, (cy + 0.5) * TILE
        p.kx = p.ky = 0
        boss_kind = BOSS_FLOORS.get(self.floor)

        w = spawn_weights(self.floor)
        kinds, weights = list(w.keys()), list(w.values())
        elite_chance = 0 if self.floor == 1 else min(0.28, 0.05 + 0.03 * (self.floor - 1))
        for i, room in enumerate(rooms[1:], start=1):
            is_last = (i == len(rooms) - 1)
            if boss_kind and is_last:
                bx, by = (room.x + room.w - 3.5) * TILE, (room.y + room.h / 2) * TILE
                self.enemies.append(Enemy(boss_kind, bx, by, self.floor))
                guards = ('goblin', 'goblin') if boss_kind == 'warlord' else ('skeleton', 'cultist', 'skeleton', 'cultist')
                for kind in guards:
                    x, y = self.dungeon.random_spot(room)
                    self.enemies.append(Enemy(kind, x, y, self.floor))
                continue
            count = min(6, random.randint(1, 2) + self.floor // 2 + (1 if self.floor >= 8 else 0))
            for _ in range(count):
                kind = random.choices(kinds, weights)[0]
                x, y = self.dungeon.random_spot(room)
                self.enemies.append(Enemy(kind, x, y, self.floor, elite=random.random() < elite_chance))

        for i, room in enumerate(rooms[1:], start=1):
            if random.random() < 0.65:
                for _ in range(random.randint(2, 5)):
                    x, y = self.dungeon.random_spot(room)
                    self.items.append(Item('coin', x, y, random.randint(2, 5) * self.floor))
            if random.random() < 0.4:
                self.items.append(Item('chest', *self.dungeon.random_spot(room)))
            if random.random() < 0.25:
                self.items.append(Item('potion', *self.dungeon.random_spot(room)))
        mid = rooms[len(rooms) // 2]
        self.items.append(Item('potion', *self.dungeon.random_spot(mid)))

        self.stairs = None
        if self.floor < MAX_FLOOR:
            room = rooms[-1]
            if boss_kind:
                self.stairs = ((room.x + 2.5) * TILE, (room.y + room.h / 2 + 0.5) * TILE)
            else:
                sx, sy = room.center
                self.stairs = ((sx + 0.5) * TILE, (sy + 0.5) * TILE)

        for m in self.minions:                       # your allies come with you!
            a = random.random() * 6.28
            m.x, m.y = p.x + math.cos(a) * 36, p.y + math.sin(a) * 36
            m.target = None
            m.spawn = 0.4

        self.render_level()
        self.explored = [[False] * MAP_W for _ in range(MAP_H)]
        self.mini = pygame.Surface((MAP_W * MINIMAP_SCALE, MAP_H * MINIMAP_SCALE), pygame.SRCALPHA)
        self.last_tile = None
        self.reveal()
        self.cam = V2(p.x - WIDTH / 2, p.y - HEIGHT / 2)
        self.fade = 1.0
        self.trail = []
        self.show_banner(f"Floor {self.floor}", floor_name(self.floor))

    def render_level(self):
        """Paint the whole dungeon onto one big picture ONE time (so the game stays fast)."""
        d, sp, pal = self.dungeon, self.sprites, self.pal
        ts = sp.tiles(self.floor)
        rng = random.Random(random.randint(0, 10 ** 6))
        grid = d.grid
        surf = pygame.Surface((MAP_W * TILE, MAP_H * TILE))
        surf.fill(shade(pal['top'], 0.55))
        self.torches, self.static_lights = [], []

        def fl(tx, ty):
            return 0 <= tx < MAP_W and 0 <= ty < MAP_H and grid[ty][tx] == FLOOR

        for ty in range(MAP_H):
            for tx in range(MAP_W):
                x, y = tx * TILE, ty * TILE
                if grid[ty][tx] == FLOOR:
                    surf.blit(ts.floor[(tx * 7 + ty * 13 + (tx * ty) % 5) % 8], (x, y))
                    if not fl(tx, ty - 1):
                        surf.blit(ts.ao_n, (x, y))
                    if not fl(tx - 1, ty):
                        surf.blit(ts.ao_w, (x, y))
                    if not fl(tx + 1, ty):
                        surf.blit(ts.ao_e, (x + TILE - ts.ao_e.get_width(), y))
                    continue
                if fl(tx, ty + 1):                                    # the front face of a wall
                    surf.blit(ts.wall_front[(tx * 5 + ty * 3) % 4], (x, y))
                    h = (tx * 31 + ty * 17) % 11
                    if h == 0:
                        sp.torch_bracket(surf, x, y)
                        self.torches.append((x + TILE // 2, y + 12, random.random() * 6.28))
                    elif h == 5:
                        sp.banner(surf, x, y, pal['banner'])
                    edge = add(pal['wall'], 30)
                    if fl(tx - 1, ty):
                        pygame.draw.line(surf, edge, (x, y), (x, y + TILE), 2)
                    if fl(tx + 1, ty):
                        pygame.draw.line(surf, shade(pal['wall'], 0.5), (x + TILE - 2, y), (x + TILE - 2, y + TILE), 2)
                elif any(fl(tx + ox, ty + oy) for ox in (-1, 0, 1) for oy in (-1, 0, 1)):
                    surf.blit(ts.wall_top[(tx + ty) % 2], (x, y))
                    edge = add(pal['top'], 34)
                    if fl(tx, ty - 1):
                        pygame.draw.line(surf, edge, (x, y), (x + TILE, y), 3)
                    if fl(tx - 1, ty):
                        pygame.draw.line(surf, edge, (x, y), (x, y + TILE), 2)
                    if fl(tx + 1, ty):
                        pygame.draw.line(surf, add(pal['top'], 16), (x + TILE - 2, y), (x + TILE - 2, y + TILE), 2)

        boss_floor = self.floor in BOSS_FLOORS
        for ri, room in enumerate(d.rooms):
            n = rng.randint(1, 2 + room.w * room.h // 45)
            for _ in range(n):
                kind = rng.choice(pal['decor'])
                if kind == 'web':
                    cx = room.x if rng.random() < 0.5 else room.x + room.w - 1
                    cy = room.y if rng.random() < 0.5 else room.y + room.h - 1
                    self.static_lights += sp.decor(surf, 'web', cx * TILE, cy * TILE, rng, pal,
                                                   flip=(cx != room.x, cy != room.y))
                else:
                    tx, ty = rng.randint(room.x, room.x + room.w - 1), rng.randint(room.y, room.y + room.h - 1)
                    self.static_lights += sp.decor(surf, kind, tx * TILE, ty * TILE, rng, pal)
            if boss_floor and ri == len(d.rooms) - 1:
                cxp, cyp = int((room.x + room.w / 2) * TILE), int((room.y + room.h / 2) * TILE)
                rad = min(room.w, room.h) * TILE // 2 - 18
                sp.big_rune(surf, cxp, cyp, rad, pal['light'])
                self.static_lights.append((cxp, cyp, rad + 60, pal['light'], 0.3))
        if self.stairs:
            sp.big_rune(surf, int(self.stairs[0]), int(self.stairs[1]), 34, (110, 190, 255))
        self.level_surf = surf

    def reveal(self):
        p = self.player
        tx, ty = int(p.x // TILE), int(p.y // TILE)
        if (tx, ty) == self.last_tile:
            return
        self.last_tile = (tx, ty)
        ms = MINIMAP_SCALE
        for yy in range(ty - 9, ty + 10):
            for xx in range(tx - 9, tx + 10):
                if 0 <= xx < MAP_W and 0 <= yy < MAP_H and not self.explored[yy][xx]:
                    if math.hypot(xx - tx, yy - ty) <= 9:
                        self.explored[yy][xx] = True
                        if self.dungeon.grid[yy][xx] == FLOOR:
                            col = (210, 175, 70) if self.is_stairs_tile(xx, yy) else (118, 108, 150)
                            pygame.draw.rect(self.mini, col, (xx * ms, yy * ms, ms, ms))

    def is_stairs_tile(self, tx, ty):
        return self.stairs is not None and int(self.stairs[0] // TILE) == tx and int(self.stairs[1] // TILE) == ty

    def boss_alive(self):
        return any(e.kind in BOSS_KINDS for e in self.enemies)

    # ------------------------------------------------------------ effect helpers
    def show_banner(self, text, sub=""):
        self.banner_text, self.banner_sub, self.banner_t = text, sub, 3.4

    def float_text(self, x, y, text, color, big=False):
        self.texts.append(FloatText(x, y, text, color, big))

    def burst(self, x, y, color, n, speed, glow=False):
        for _ in range(n):
            a = random.random() * 6.283
            s = random.random() * speed
            self.particles.append(Particle(x, y, math.cos(a) * s, math.sin(a) * s,
                                           random.uniform(0.25, 0.6), color, random.randint(2, 4), glow))

    def flash_light(self, x, y, r, color, strength, life):
        self.flashes.append([x, y, r, color, strength, life, life])

    def shockwave(self, x, y, radius, color):
        self.rings.append([x, y, radius, 0.0, 0.35, color])
        self.flash_light(x, y, radius * 1.5, color, 0.7, 0.3)

    def rumble(self, strength, ms):
        """Make the PS5 controller buzz (if one is connected and vibration is on)."""
        self.input.rumble(strength * 0.6, strength, ms)

    def toast(self, msg, color=(235, 235, 245)):
        self.toasts.append([msg, color, 4.0])
        del self.toasts[:-4]

    def decal(self, x, y, color, size=14):
        if self.level_surf is not None:
            self.sprites.splat(self.level_surf, x, y, color, random, size)

    # ------------------------------------------------------------ fighting basics
    def aim_dir(self):
        """Ranged attacks aim where you face, with a little help toward monsters in front of you."""
        p = self.player
        if not self.input.settings['aim_assist']:
            return V2(p.face)
        best, score = None, 1e9
        for e in self.enemies:
            dx, dy = e.x - p.x, e.y - p.y
            dist = math.hypot(dx, dy)
            if dist < 1 or dist > 500:
                continue
            ang = abs((p.face.angle_to(V2(dx, dy)) + 180) % 360 - 180)
            if ang > 38 or not self.dungeon.line_clear(p.x, p.y, e.x, e.y):
                continue
            sc = ang * 4 + dist * 0.2
            if sc < score:
                best, score = V2(dx, dy).normalize(), sc
        return best if best else V2(p.face)

    def player_attack(self):
        p = self.player
        c = CLASSES[p.cls]
        p.attack_cd = c['atk_cd']
        if c['atk'] == 'ranged':
            d = self.aim_dir()
            p.face = V2(d)
            kind = c.get('bolt_kind', 'magic')
            self.audio.play('cast' if kind == 'magic' else 'knife')
            speed = 560 if kind == 'arrow' else 400
            self.bolts.append(Bolt(p.x + d.x * 16, p.y + d.y * 16, d.x * speed, d.y * speed,
                                   p.dmg + random.randint(-1, 1), c.get('bolt', (205, 130, 255)),
                                   4 if kind == 'arrow' else 6, 1.1, kind=kind, crit=None))
            self.burst(p.x + d.x * 18, p.y + d.y * 18, c.get('bolt', (255, 255, 255)), 4, 80, glow=True)
            return
        p.swing = 0.16
        self.audio.play('swing')
        f = p.face
        hs = c['hitsize']
        hit = pygame.Rect(0, 0, hs, hs)
        hit.center = (p.x + f.x * c['reach'], p.y + f.y * c['reach'])
        for e in self.enemies[:]:
            if hit.colliderect(e.rect):
                self.damage_enemy(e, p.dmg + random.randint(-2, 2))
        for pr in self.projectiles:   # slash can swat away arrows!
            if hit.collidepoint(pr.x, pr.y):
                pr.alive = False
                self.audio.play('deflect')
                self.burst(pr.x, pr.y, (255, 255, 200), 5, 80, glow=True)

    def damage_enemy(self, e, dmg, crit=None, knock=True, origin=None, leech=False, dot=False, push=None):
        p = self.player
        if crit is None:
            crit = random.random() < p.crit
        if crit:
            dmg *= 2
        dmg = int(dmg)
        e.hp -= dmg
        e.awake = True
        if dot:
            self.float_text(e.x, e.y - 18, str(dmg), (120, 230, 100))
        else:
            e.flash = 0.12
            self.audio.play('hit')
            self.float_text(e.x, e.y - 22, f"{dmg}!" if crit else str(dmg),
                            (255, 225, 70) if crit else (255, 255, 255), big=crit)
            self.burst(e.x, e.y, (255, 220, 160), 6, 130, glow=True)
            if crit:
                self.hitstop = max(self.hitstop, 0.045)
        if knock:
            ox, oy = origin if origin else (p.x, p.y)
            d = V2(e.x - ox, e.y - oy)
            d = d.normalize() if d.length_squared() else V2(0, 1)
            amount = (300 if push is None else push) * KNOCK_RESIST.get(e.kind, 1.0)
            e.kx, e.ky = d.x * amount, d.y * amount
        if e.hp <= 0:
            self.kill_enemy(e)

    def aoe(self, x, y, radius, dmg, knock=250, stun=0.0, slow=0.0, poison=0.0, poison_t=0.0,
            color=(255, 255, 255), crit=False, ring=True, exclude=None):
        """Hurt (and maybe stun/slow/poison) every monster inside a circle."""
        if ring:
            self.shockwave(x, y, radius, color)
        n = 0
        for e in self.enemies[:]:
            if exclude and e in exclude:
                continue
            if math.hypot(e.x - x, e.y - y) <= radius + e.w / 2:
                n += 1
                e.awake = True
                if stun and e.kind not in BOSS_KINDS:
                    e.stun_t = max(e.stun_t, stun)
                if slow:
                    e.slow_t = max(e.slow_t, slow)
                if poison:
                    e.poison_dps, e.poison_t, e.poison_tick = poison, poison_t, 0.5
                if dmg > 0:
                    self.damage_enemy(e, dmg, crit=crit, origin=(x, y), push=knock)
        return n

    def freeze_enemy(self, e, secs):
        """Freeze a monster solid. Bosses are too mighty to freeze - they get chilled (slowed) instead."""
        if e.kind in BOSS_KINDS:
            e.slow_t = max(e.slow_t, secs)
            self.float_text(e.x, e.y - 40, "Chilled!", (170, 225, 255), big=True)
        else:
            e.freeze_t = max(e.freeze_t, secs)
            self.float_text(e.x, e.y - 40, "FROZEN!", (170, 225, 255), big=True)
        self.audio.play('frost')
        self.shockwave(e.x, e.y, 46, (170, 225, 255))
        self.burst(e.x, e.y, (200, 235, 255), 16, 150, glow=True)

    def hurt_around(self, x, y, radius, dmg):
        """Damage the player AND the player's allies inside a circle (used by bombs and slams)."""
        p = self.player
        if math.hypot(p.x - x, p.y - y) < radius + 11:
            p.hurt(dmg, x, y, self)
        for m in self.minions[:]:
            if math.hypot(m.x - x, m.y - y) < radius + m.w / 2:
                m.hurt(dmg, self)

    def explosion(self, x, y, radius, dmg):
        self.shockwave(x, y, radius, (255, 140, 40))
        self.burst(x, y, (255, 170, 50), 30, 260, glow=True)
        self.burst(x, y, (90, 80, 80), 14, 140)
        self.audio.play('boom')
        self.shake = max(self.shake, 0.35)
        self.rumble(0.7, 260)
        self.hurt_around(x, y, radius, dmg)

    def slam(self, x, y, radius, dmg):
        self.shockwave(x, y, radius, (255, 160, 60))
        self.burst(x, y + 10, (160, 130, 100), 18, 200)
        self.audio.play('slam')
        self.shake = max(self.shake, 0.4)
        self.rumble(0.7, 260)
        self.hurt_around(x, y, radius, dmg)

    def kill_enemy(self, e):
        if e in self.enemies:
            self.enemies.remove(e)
        p = self.player
        if p.sky_mark_enemy is e:
            p.sky_mark_enemy = None
            p.buffs.pop('sky_mark', None)
        if p.launch is e:
            p.launch, p.launch_t = None, 0.0
        p.kills += 1
        p.xp += e.xp
        self.audio.play('die')
        col = {'skeleton': (200, 200, 220), 'wraith': (190, 210, 255), 'imp': (255, 150, 50),
               'cultist': (200, 80, 255), 'spider': (120, 80, 150), 'goblin': (110, 170, 60),
               'brute': (110, 130, 70)}.get(e.kind, (80, 210, 100))
        self.burst(e.x, e.y, col, 18, 200, glow=True)
        self.decal(e.x, e.y, (60, 150, 70) if e.kind in ('slime', 'goblin', 'brute') else (110, 20, 30), 12 if e.kind not in BOSS_KINDS else 30)
        self.shake = max(self.shake, 0.15)
        if e.elite:
            self.hitstop = max(self.hitstop, 0.07)
            self.float_text(e.x, e.y - 50, "ELITE DOWN!", (255, 220, 90), big=True)
        if p.cls == 'necromancer' and e.kind not in BOSS_KINDS:
            self.corpses.append(Corpse(e.kind, e.x, e.y))
            if len(self.corpses) > 24:
                self.corpses.pop(0)
        if p.kill_heal and p.hp < p.max_hp:
            p.hp = min(p.max_hp, p.hp + p.kill_heal)
            self.float_text(p.x, p.y - 30, f"+{p.kill_heal}", (130, 255, 160))
        if random.random() < (0.5 if not e.elite else 1.0) or e.kind in ('boss', 'brute', 'warlord'):
            n = random.randint(1, 3) if e.kind not in BOSS_KINDS else 10
            for _ in range(n + (3 if e.elite else 0)):
                self.items.append(Item('coin', e.x + random.randint(-18, 18), e.y + random.randint(-18, 18),
                                       random.randint(3, 8) * self.floor))
        if random.random() < (0.12 if not e.elite else 0.45) or e.kind == 'warlord':
            self.items.append(Item('potion', e.x, e.y))
        self.float_text(e.x, e.y - 36, f"+{e.xp} XP", (140, 195, 255))
        while p.xp >= p.xp_next:
            p.xp -= p.xp_next
            self.level_up()
        if e.kind == 'boss':
            self.projectiles.clear()
            self.boss_dead_timer = 3.0
            self.hitstop = 0.2
            self.rumble(1.0, 700)
            self.shake = 0.9
            self.show_banner("The Bone King has fallen!")
            for en in self.enemies[:]:
                self.enemies.remove(en)
                self.burst(en.x, en.y, (200, 200, 220), 12, 150, glow=True)
        elif e.kind == 'warlord':
            self.projectiles.clear()
            self.hitstop = 0.15
            self.shake = 0.7
            self.show_banner("Gorrak has fallen!", "The stairs are open")
            self.audio.play('levelup')

    def level_up(self):
        """Leveling up is AUTOMATIC: every hero grows a little stronger each level."""
        p = self.player
        c = CLASSES[p.cls]
        p.level += 1
        p.xp_next = xp_for(p.level)
        ghp, gdmg = c['growth']
        p.max_hp += ghp
        p.dmg += gdmg
        p.crit = min(0.6, p.crit + 0.003)
        lines = [f"+{ghp} HP", f"+{gdmg} DMG"]
        if p.level % 5 == 0:
            p.cd_mult = max(0.5, p.cd_mult * 0.92)
            p.ap += 0.1
            lines.append("Abilities stronger!")
        p.hp = min(p.max_hp, p.hp + int(p.max_hp * 0.3))
        self.audio.play('levelup2')
        self.rumble(0.5, 350)
        self.float_text(p.x, p.y - 46, "LEVEL UP!", (255, 235, 110), big=True)
        self.float_text(p.x, p.y - 22, "  ".join(lines), (200, 255, 200))
        self.shockwave(p.x, p.y, 120, (255, 225, 110))
        self.burst(p.x, p.y, (255, 235, 120), 30, 240, glow=True)
        self.levelup_t = 1.3
        if p.level in UNLOCK_LEVELS:
            slot = UNLOCK_LEVELS.index(p.level)
            name = ABILITIES[c['abilities'][slot]]['name']
            self.show_banner(f"New ability: {name}", f"Press {slot + 1} to use it")
            self.audio.play('unlock')

    def on_player_death(self):
        self.state = 'dead'
        self.audio.play('gameover')

    def drink_potion(self):
        p = self.player
        if p.potions > 0 and p.hp < p.max_hp:
            p.potions -= 1
            h = p.potion_heal
            p.hp = min(p.max_hp, p.hp + h)
            self.audio.play('potion')
            self.float_text(p.x, p.y - 26, f"+{h} HP", (110, 255, 130))
            self.burst(p.x, p.y, (255, 100, 130), 14, 100, glow=True)

    def try_descend(self):
        p = self.player
        if self.stairs and math.hypot(p.x - self.stairs[0], p.y - self.stairs[1]) < 40:
            if self.boss_alive():
                self.float_text(p.x, p.y - 40, "Defeat the boss first!", (255, 120, 120), big=True)
                self.audio.play('deflect')
                return
            self.audio.play('stairs')
            self.floor += 1
            p.hp = min(p.max_hp, p.hp + int(p.max_hp * 0.2))
            self.build_floor()
            self.open_shop('playing')

    # ------------------------------------------------------------ ALLIES (minions)
    def count_group(self, g):
        return sum(1 for m in self.minions if m.group == g)

    def summon(self, kind, x, y, group, life=None):
        p = self.player
        cap = MINION_CAPS.get(group, 6)
        while self.count_group(group) >= cap:
            old = next(m for m in self.minions if m.group == group)
            self.minions.remove(old)
            self.burst(old.x, old.y, (180, 255, 200), 8, 90, glow=True)
        m = Minion(kind, x, y, p.level, life, group)
        if self.dungeon.hits_wall(m.rect):
            m.x, m.y = p.x, p.y
        self.minions.append(m)
        col = {'skeleton': (130, 255, 170), 'archer': (140, 190, 255), 'bonebrute': (190, 255, 190)}.get(kind, (255, 220, 150))
        self.burst(m.x, m.y, col, 16, 150, glow=True)
        self.shockwave(m.x, m.y, 40, col)
        return m

    def minion_hit(self, m, e, dmg):
        self.damage_enemy(e, dmg, crit=False, origin=(m.x, m.y), push=130)
        if random.random() < 0.3:
            self.audio.play('bite')

    def minion_died(self, m):
        if m in self.minions:
            self.minions.remove(m)
        self.burst(m.x, m.y, (200, 210, 230), 14, 150, glow=True)
        self.float_text(m.x, m.y - 24, "fallen", (200, 200, 220))
        self.audio.play('die')

    def minion_expire(self, m):
        if m in self.minions:
            self.minions.remove(m)
        self.burst(m.x, m.y, (150, 255, 190), 14, 110, glow=True)

    def nearest_enemy(self, x, y, max_d, p):
        best, bd = None, max_d
        for e in self.enemies:
            d = math.hypot(e.x - x, e.y - y)
            if d >= bd:
                continue
            if not (e.awake or math.hypot(e.x - p.x, e.y - p.y) < 260):
                continue
            if math.hypot(e.x - p.x, e.y - p.y) > 460 or not self.dungeon.line_clear(x, y, e.x, e.y):
                continue
            best, bd = e, d
        return best

    # ------------------------------------------------------------ ABILITIES
    def use_ability(self, slot):
        p = self.player
        name = CLASSES[p.cls]['abilities'][slot]
        ab = ABILITIES[name]
        if p.level < UNLOCK_LEVELS[slot]:
            self.float_text(p.x, p.y - 34, f"Unlocks at level {UNLOCK_LEVELS[slot]}", (210, 210, 210))
            return
        if p.launch_t > 0:                # already flying at the mark
            return
        if name == 'sky_strike' and self.sky_recast_ready():
            self.ab_sky_strike_recast()   # free follow-up, doesn't touch the cooldown
            return
        if p.ability_cd[slot] > 0:
            return
        if getattr(self, 'ab_' + name)() is False:
            return
        cd = ab['cd'] * p.cd_mult
        p.ability_cd[slot] = p.ability_max[slot] = cd

    def sky_recast_ready(self):
        """True while the Monk's orb is stuck to a living monster (so ability 1 will launch you at it)."""
        p = self.player
        return p.buffs.get('sky_mark', 0) > 0 and p.sky_mark_enemy in self.enemies

    def power(self, mult):
        p = self.player
        return p.dmg * mult * p.ap

    def nearest_enemies(self, x, y, max_dist, count, need_los=True):
        out = []
        for e in self.enemies:
            d = math.hypot(e.x - x, e.y - y)
            if d <= max_dist and (not need_los or self.dungeon.line_clear(x, y, e.x, e.y)):
                out.append((d, e))
        out.sort(key=lambda t: t[0])
        return [e for _, e in out[:count]]

    # -- Knight
    def ab_whirlwind(self):
        p = self.player
        p.spin = 0.45
        self.audio.play('whirl')
        self.aoe(p.x, p.y, 100, self.power(1.7), knock=270, color=(220, 230, 255))
        for pr in self.projectiles:
            if math.hypot(pr.x - p.x, pr.y - p.y) < 100:
                pr.alive = False

    def ab_shield_wall(self):
        p = self.player
        p.buffs['shield'] = 2.5
        self.audio.play('shield')
        self.burst(p.x, p.y, (120, 180, 255), 20, 150, glow=True)

    def ab_ground_slam(self):
        p = self.player
        self.audio.play('slam')
        self.shake = max(self.shake, 0.4)
        self.aoe(p.x, p.y, 150, self.power(2.0), knock=220, stun=1.5, color=(255, 170, 80))
        self.burst(p.x, p.y, (180, 150, 120), 25, 220)

    # -- Mage
    def ab_frozen_heart(self):
        """Throw a heart. The first monster it hits is hurt and frozen solid for a few seconds."""
        p = self.player
        d = self.aim_dir()
        p.face = V2(d)
        self.audio.play('cast')
        self.bolts.append(Bolt(p.x + d.x * 16, p.y + d.y * 16, d.x * 380, d.y * 380, self.power(1.8),
                               (255, 120, 185), 11, 1.3, kind='heart', freeze=FREEZE_TIME))
        self.burst(p.x + d.x * 18, p.y + d.y * 18, (255, 170, 215), 8, 100, glow=True)

    def ab_flower_ring(self):
        """A ring of flowers spins around you. update_flowers() below does the hurting."""
        p = self.player
        p.buffs['flowers'] = FLOWER_TIME
        self.audio.play('nova')
        self.shockwave(p.x, p.y, FLOWER_RADIUS, (255, 150, 200))
        self.burst(p.x, p.y, (255, 170, 215), 24, 190, glow=True)
        self.float_text(p.x, p.y - 34, "Bloom!", (255, 170, 215), big=True)

    def flower_spots(self):
        """Where each flower of the ring is right now (world x, y). Empty when the ring isn't up."""
        p = self.player
        left = p.buffs.get('flowers', 0)
        if left <= 0:
            return []
        grow = min(1.0, (FLOWER_TIME - left) / 0.25, left / 0.25)      # blooms out, then folds back in
        r = FLOWER_RADIUS * (0.3 + 0.7 * grow)
        return [(p.x + math.cos(self.t * 3.4 + k * 6.2832 / FLOWER_COUNT) * r,
                 p.y + math.sin(self.t * 3.4 + k * 6.2832 / FLOWER_COUNT) * r) for k in range(FLOWER_COUNT)]

    def update_flowers(self):
        p = self.player
        spots = self.flower_spots()
        if not spots:
            return
        dmg = self.power(0.45)
        for e in self.enemies[:]:
            if e.petal_cd > 0:
                continue
            for fx, fy in spots:
                if math.hypot(e.x - fx, e.y - fy) < e.w / 2 + 15:
                    e.petal_cd = 0.5
                    self.burst(fx, fy, (255, 170, 215), 5, 110, glow=True)
                    self.damage_enemy(e, dmg, origin=(p.x, p.y), push=150)
                    break

    def ab_chain_lightning(self):
        p = self.player
        pts, hit, cur = [(p.x, p.y)], [], (p.x, p.y)
        for i in range(5):
            reach = 330 if i == 0 else 200
            cands = [e for e in self.enemies if e not in hit and math.hypot(e.x - cur[0], e.y - cur[1]) < reach
                     and self.dungeon.line_clear(cur[0], cur[1], e.x, e.y)]
            if not cands:
                break
            e = min(cands, key=lambda q: math.hypot(q.x - cur[0], q.y - cur[1]))
            hit.append(e)
            pts.append((e.x, e.y))
            cur = (e.x, e.y)
        if not hit:
            self.float_text(p.x, p.y - 30, "No targets!", (200, 200, 200))
            return False
        self.audio.play('zap')
        self.zaps.append([pts, 0.3, 0.3, (170, 210, 255)])
        for e in hit:
            e.stun_t = 0 if e.kind in BOSS_KINDS else max(e.stun_t, 0.4)
            self.damage_enemy(e, self.power(2.0), crit=False, origin=pts[0], push=120)

    # -- Rogue
    def ab_knives(self):
        p = self.player
        base = self.aim_dir()
        p.face = V2(base)
        self.audio.play('knife')
        for a in (-24, -12, 0, 12, 24):
            d = base.rotate(a)
            self.bolts.append(Bolt(p.x + d.x * 14, p.y + d.y * 14, d.x * 440, d.y * 440, self.power(0.9),
                                   (215, 220, 230), 4, 0.9, kind='knife'))

    def ab_shadow_strike(self):
        p = self.player
        targets = self.nearest_enemies(p.x, p.y, 280, 1)
        if not targets:
            self.float_text(p.x, p.y - 30, "No target!", (200, 200, 200))
            return False
        e = targets[0]
        back = V2(p.x - e.x, p.y - e.y)
        back = back.normalize() if back.length_squared() else V2(0, 1)
        spot = None
        for ang in (0, 90, -90, 180):
            v = back.rotate(ang) * (e.w / 2 + 22)
            tx, ty = e.x + v.x, e.y + v.y
            rc = pygame.Rect(int(tx - p.w / 2), int(ty - p.h / 2), p.w, p.h)
            if not self.dungeon.hits_wall(rc):
                spot = (tx, ty)
                break
        if not spot:
            return False
        self.audio.play('warp')
        self.burst(p.x, p.y, (150, 100, 220), 16, 150, glow=True)
        p.x, p.y = spot
        p.invuln = max(p.invuln, 0.5)
        p.face = V2(e.x - p.x, e.y - p.y).normalize()
        self.burst(p.x, p.y, (150, 100, 220), 16, 150, glow=True)
        self.damage_enemy(e, self.power(3.0), crit=True, origin=(p.x, p.y))

    def ab_poison_bomb(self):
        p = self.player
        d = self.aim_dir()
        cx, cy = p.x + d.x * 110, p.y + d.y * 110
        if self.dungeon.is_wall(int(cx // TILE), int(cy // TILE)):
            cx, cy = p.x, p.y
        self.audio.play('nova')
        self.aoe(cx, cy, 110, self.power(0.5), knock=60, poison=self.power(0.6), poison_t=6.0, color=(110, 220, 90))
        self.burst(cx, cy, (110, 220, 90), 35, 150, glow=True)

    # -- Cleric
    def ab_smite(self):
        p = self.player
        targets = self.nearest_enemies(p.x, p.y, 380, 3, need_los=False)
        if not targets:
            self.float_text(p.x, p.y - 30, "No targets!", (200, 200, 200))
            return False
        self.audio.play('zap')
        for e in targets:
            self.zaps.append([[(e.x - 8, e.y - 320), (e.x + 6, e.y - 160), (e.x, e.y)], 0.3, 0.3, (255, 235, 140)])
            self.aoe(e.x, e.y, 45, self.power(2.2), knock=100, stun=0.6, color=(255, 225, 110))

    def ab_heal(self):
        p = self.player
        amt = int(p.max_hp * 0.35)
        p.hp = min(p.max_hp, p.hp + amt)
        self.audio.play('heal')
        self.float_text(p.x, p.y - 28, f"+{amt} HP", (110, 255, 130), big=True)
        self.burst(p.x, p.y, (120, 255, 160), 18, 120, glow=True)
        self.burst(p.x, p.y, (255, 235, 150), 10, 90, glow=True)
        self.flash_light(p.x, p.y, 180, (120, 255, 160), 0.7, 0.5)

    def ab_holy_nova(self):
        p = self.player
        self.audio.play('nova')
        self.aoe(p.x, p.y, 150, self.power(1.5), knock=340, color=(255, 240, 170))
        p.hp = min(p.max_hp, p.hp + 8)
        self.burst(p.x, p.y, (255, 240, 170), 25, 200, glow=True)

    # -- Necromancer
    def ab_raise_dead(self):
        p = self.player
        near = sorted((c for c in self.corpses if math.hypot(c.x - p.x, c.y - p.y) < 340),
                      key=lambda c: math.hypot(c.x - p.x, c.y - p.y))[:3]
        self.audio.play('raise')
        if not near:                               # no corpses? bones still rise from the floor
            self.summon('skeleton', p.x + p.face.x * 46, p.y + p.face.y * 46, 'undead')
            self.float_text(p.x, p.y - 34, "Bones rise!", (150, 255, 180))
            return
        for c in near:
            self.corpses.remove(c)
            self.summon(CORPSE_TO_MINION.get(c.kind, 'skeleton'), c.x, c.y, 'undead')
        self.float_text(p.x, p.y - 34, "Rise!", (150, 255, 180), big=True)

    def ab_corpse_explosion(self):
        p = self.player
        near = [c for c in self.corpses if math.hypot(c.x - p.x, c.y - p.y) < 420]
        if not near:
            self.float_text(p.x, p.y - 30, "No corpses!", (200, 200, 200))
            return False
        self.audio.play('boom')
        for c in near:
            self.corpses.remove(c)
            self.aoe(c.x, c.y, 95, self.power(2.2), knock=200, color=(140, 255, 120))
            self.burst(c.x, c.y, (160, 255, 120), 20, 200, glow=True)
        self.shake = max(self.shake, 0.3)

    def ab_army_of_dead(self):
        p = self.player
        self.audio.play('raise')
        self.shockwave(p.x, p.y, 110, (150, 140, 255))
        for i in range(5):
            a = i * 6.2832 / 5
            self.summon('skeleton', p.x + math.cos(a) * 70, p.y + math.sin(a) * 70, 'army', life=18.0)
        self.float_text(p.x, p.y - 36, "ARISE!", (170, 160, 255), big=True)

    # -- Beastmaster
    def _spawn_beasts(self, kind, group, n, cap, full_msg, sound):
        p = self.player
        have = self.count_group(group)
        if have >= cap:
            self.float_text(p.x, p.y - 34, full_msg, (210, 210, 210))
            return False
        self.audio.play(sound)
        for i in range(min(n, cap - have)):
            a = random.random() * 6.28
            self.summon(kind, p.x + math.cos(a) * 44, p.y + math.sin(a) * 44, group)

    def ab_summon_wolves(self):
        return self._spawn_beasts('wolf', 'wolf', 2, 4, "The pack is full!", 'howl')

    def ab_summon_hawk(self):
        return self._spawn_beasts('hawk', 'hawk', 1, 2, "Two hawks is enough!", 'screech')

    def ab_summon_bear(self):
        p = self.player
        if self._spawn_beasts('bear', 'bear', 1, 1, "Your bear is already here!", 'roar') is False:
            return False
        self.shake = max(self.shake, 0.3)
        self.aoe(p.x, p.y, 170, 0, knock=190, stun=1.2, color=(235, 190, 120))

    # -- Monk
    def ab_sky_strike(self):
        """The first half of Sky Strike: throw a ball of force. It marks (and lightly hurts) the first
        monster it hits, but doesn't move you - that's what the recast below is for."""
        p = self.player
        d = self.aim_dir()
        p.face = V2(d)
        self.audio.play('shoot')
        self.bolts.append(Bolt(p.x + d.x * 16, p.y + d.y * 16, d.x * 540, d.y * 540, self.power(0.8),
                               (255, 235, 150), 9, 0.75, kind='orb', mark=True))
        self.burst(p.x + d.x * 18, p.y + d.y * 18, (255, 235, 150), 6, 90, glow=True)

    def ab_sky_strike_recast(self):
        """The follow-up: LAUNCH yourself at the marked monster. Player.fly_to_mark() does the flying and
        calls sky_strike_land() below when you arrive. Costs no extra cooldown."""
        p = self.player
        e = p.sky_mark_enemy
        p.sky_mark_enemy = None
        p.buffs.pop('sky_mark', None)
        if e is None or e not in self.enemies:
            self.float_text(p.x, p.y - 30, "Target lost!", (200, 200, 200))
            return
        p.launch, p.launch_t = e, 0.8
        p.dash_t = 0.0
        p.invuln = max(p.invuln, 0.2)
        self.audio.play('dash')
        self.audio.play('warp')
        self.shockwave(p.x, p.y, 40, (255, 235, 150))
        self.burst(p.x, p.y, (255, 235, 150), 16, 150, glow=True)

    def sky_strike_land(self, e):
        p = self.player
        p.invuln = max(p.invuln, 0.4)
        p.swing = 0.16
        self.audio.play('slam')
        self.shake = max(self.shake, 0.3)
        self.rumble(0.7, 220)
        self.shockwave(e.x, e.y, 60, (255, 235, 150))
        self.burst(e.x, e.y, (255, 235, 150), 20, 220, glow=True)
        self.damage_enemy(e, self.power(2.2), crit=True, origin=(p.x, p.y))

    def ab_tempest_kick(self):
        p = self.player
        p.spin = 0.4
        self.audio.play('whirl')
        self.aoe(p.x, p.y, 130, self.power(1.8), knock=430, stun=0.3, color=(255, 170, 90))
        self.burst(p.x, p.y, (255, 190, 110), 22, 220, glow=True)

    def ab_dragons_kick(self):
        p = self.player
        targets = self.nearest_enemies(p.x, p.y, 130, 1)
        if not targets:
            self.float_text(p.x, p.y - 30, "No target!", (200, 200, 200))
            return False
        e = targets[0]
        self.audio.play('slam')
        self.shake = max(self.shake, 0.5)
        self.rumble(0.8, 300)
        self.damage_enemy(e, self.power(2.6), crit=True, origin=(p.x, p.y), push=620)
        self.burst(e.x, e.y, (255, 140, 60), 20, 220, glow=True)
        # the kicked monster bowls into anything else nearby, like a wrecking ball
        self.aoe(e.x, e.y, 90, self.power(1.0), knock=320, ring=False, color=(255, 150, 70), exclude=(e,))

    # ------------------------------------------------------------ updating
    def update_items(self, dt):
        p = self.player
        pr = p.rect
        for it in self.items[:]:
            it.t += dt
            if it.kind == 'coin':
                d = math.hypot(p.x - it.x, p.y - it.y)
                if 1 < d < 90:
                    it.x += (p.x - it.x) / d * 260 * dt
                    it.y += (p.y - it.y) / d * 260 * dt
            if not pr.colliderect(it.rect):
                continue
            if it.kind == 'coin':
                p.gold += it.value
                self.audio.play('coin')
                self.float_text(it.x, it.y - 10, f"+{it.value}", (255, 215, 70))
                self.items.remove(it)
            elif it.kind == 'potion' and p.potions < 9:
                p.potions += 1
                self.audio.play('potion')
                self.float_text(it.x, it.y - 10, "Potion!", (255, 120, 150))
                self.items.remove(it)
            elif it.kind == 'chest' and not it.opened:
                it.opened = True
                g = random.randint(15, 35) * self.floor
                p.gold += g
                self.audio.play('chest')
                self.float_text(it.x, it.y - 20, f"+{g} gold!", (255, 215, 70), big=True)
                self.burst(it.x, it.y, (255, 230, 120), 20, 160, glow=True)
                self.flash_light(it.x, it.y, 120, (255, 220, 100), 0.6, 0.4)
                if random.random() < 0.5 and p.potions < 9:
                    p.potions += 1
                    self.float_text(it.x, it.y - 40, "Potion!", (255, 120, 150))

    def update_fx(self, dt):
        for pa in self.particles[:]:
            pa.life -= dt
            pa.x += pa.vx * dt
            pa.y += pa.vy * dt
            pa.vx *= 0.92; pa.vy *= 0.92
            if pa.life <= 0:
                self.particles.remove(pa)
        for tx in self.texts[:]:
            tx.life -= dt
            tx.y -= 30 * dt
            if tx.life <= 0:
                self.texts.remove(tx)
        for r in self.rings[:]:
            r[3] += dt
            if r[3] >= r[4]:
                self.rings.remove(r)
        for z in self.zaps[:]:
            z[1] -= dt
            if z[1] <= 0:
                self.zaps.remove(z)
        for f in self.flashes[:]:
            f[5] -= dt
            if f[5] <= 0:
                self.flashes.remove(f)
        self.levelup_t = max(0.0, self.levelup_t - dt)
        necro = self.player.cls == 'necromancer'
        for c in self.corpses[:]:
            c.life -= dt
            if c.life <= 0:
                self.corpses.remove(c)
            elif necro and random.random() < 0.03:
                self.particles.append(Particle(c.x + random.uniform(-8, 8), c.y, 0, -26, 0.9, (130, 255, 170), 3, True))

    def update_motes(self, dt):
        for m in self.motes:
            m[4] += dt
            m[0] += (m[2] + math.sin(m[4]) * 6) * dt
            m[1] += m[3] * dt
            if m[1] < -10: m[1] = HEIGHT + 10
            if m[0] < -10: m[0] = WIDTH + 10
            if m[0] > WIDTH + 10: m[0] = -10

    def update_camera(self, dt):
        p = self.player
        target = V2(p.x - WIDTH / 2 + p.face.x * 24, p.y - HEIGHT / 2 + p.face.y * 16)
        self.cam += (target - self.cam) * min(1.0, dt * 7)

    def update(self, dt):
        self.t += dt
        self.audio.update()
        self.fade = max(0.0, self.fade - dt * 1.5)
        self.banner_t = max(0.0, self.banner_t - dt)
        self.shake = max(0.0, self.shake - dt)
        self.update_motes(dt)
        self.show_stats = self.input.held('stats') and self.state == 'playing'
        for t in self.toasts[:]:
            t[2] -= dt
            if t[2] <= 0:
                self.toasts.remove(t)
        if self.state == 'playing':
            if self.hitstop > 0:                        # tiny freeze on big hits (feels crunchy!)
                self.hitstop -= dt
                return
            p = self.player
            self.run_time += dt
            if p.dash_t > 0 or p.launch_t > 0:
                self.trail.append([p.x, p.y, p.dir_name, 0.22])
            for tr in self.trail[:]:
                tr[3] -= dt
                if tr[3] <= 0:
                    self.trail.remove(tr)
            p.update(dt, self.input, self)
            self.update_flowers()
            for e in self.enemies[:]:
                if e in self.enemies:
                    e.update(dt, self)
            for m in self.minions[:]:
                if m in self.minions:
                    m.update(dt, self)
            for pr in self.projectiles[:]:
                pr.update(dt, self)
                if not pr.alive:
                    self.projectiles.remove(pr)
            for b in self.bolts[:]:
                b.update(dt, self)
                if not b.alive:
                    self.bolts.remove(b)
            self.update_items(dt)
            self.update_fx(dt)
            self.reveal()
            self.update_camera(dt)
            if self.hp_trail > p.hp:
                self.hp_trail = max(p.hp, self.hp_trail - p.max_hp * 0.35 * dt)
            else:
                self.hp_trail = p.hp
            if self.boss_dead_timer > 0:
                self.boss_dead_timer -= dt
                if self.boss_dead_timer <= 0:
                    self.state = 'victory'
                    self.audio.play('victory')
        elif self.state == 'dead':
            self.update_fx(dt)

    # ------------------------------------------------------------ menus
    SETTING_LABELS = {'deadzone': 'Stick dead zone', 'vibration': 'Vibration', 'stick_aims': 'Right stick aims',
                      'stick_attack': 'Right stick auto-attacks', 'aim_assist': 'Aim assist'}

    def title_items(self):
        return [("START GAME", self.go_select), ("MUSIC", lambda: self.open_music('title')),
                ("CONTROLS", lambda: self.open_controls('title')), ("QUIT", self.quit_game)]

    def pause_items(self):
        return [("RESUME", self.resume), ("SHOP", lambda: self.open_shop('paused')),
                ("MUSIC", lambda: self.open_music('paused')), ("CONTROLS", lambda: self.open_controls('paused')),
                ("QUIT TO TITLE", self.go_title)]

    def menu_items(self):
        if self.state == 'title':
            return self.title_items()
        if self.state == 'paused':
            return self.pause_items()
        if self.state == 'music':
            return self.music_items()
        if self.state == 'shop':
            return self.shop_items()
        return []

    def select_item_index(self, items, label):
        """Finds `label`'s position in `items` (0 if missing) - avoids hardcoding menu-row numbers that shift
        whenever an entry is added or reordered."""
        return next((i for i, (lab, _) in enumerate(items) if lab == label), 0)

    def go_select(self):
        self.audio.play('select')
        self.sel = 0
        self.state = 'select'

    def go_title(self):
        self.audio.play('select')
        self.state = 'title'
        self.menu_sel = 0

    def resume(self):
        self.state = 'playing'

    def quit_game(self):
        self.running = False

    def open_controls(self, back_to):
        self.audio.play('select')
        self.return_state = back_to
        self.state = 'controls'
        self.ctl_tab = 1 if self.input.device == 'gamepad' else 0
        self.ctl_row = self.ctl_col = 0

    def close_controls(self):
        self.audio.play('select')
        self.state = self.return_state
        self.menu_sel = self.select_item_index(self.menu_items(), "CONTROLS")

    # ------------------------------------------------------------ the MUSIC screen (tracks + volume)
    def music_items(self):
        items = [(rec['name'], (lambda k=rec['key']: self.choose_track(k))) for rec in MUSIC_TRACKS]
        items.append(("Music Volume", lambda: None))   # sliders: left/right adjust, click just selects
        items.append(("SFX Volume", lambda: None))
        items.append(("BACK", self.close_music))
        return items

    def open_music(self, back_to):
        self.audio.play('select')
        self.return_state = back_to
        self.state = 'music'
        self.menu_sel = next((i for i, rec in enumerate(MUSIC_TRACKS) if rec['key'] == self.audio.track_key), 0)

    def close_music(self):
        self.audio.play('select')
        self.state = self.return_state
        self.menu_sel = self.select_item_index(self.menu_items(), "MUSIC")

    def choose_track(self, key):
        self.audio.set_track(key)
        name = next(rec['name'] for rec in MUSIC_TRACKS if rec['key'] == key)
        self.audio.play('select')
        self.toast(f"Music: {name}", (170, 230, 255))

    def music_input(self):
        inp = self.input
        if inp.nav('back'):
            self.close_music()
            return
        n_tracks = len(MUSIC_TRACKS)
        if inp.nav('left') or inp.nav('right'):
            d = -1 if inp.nav('left') else 1
            if self.menu_sel == n_tracks:
                self.audio.set_music_vol(self.audio.music_vol + 0.1 * d)
            elif self.menu_sel == n_tracks + 1:
                self.audio.set_sfx_vol(self.audio.sfx_vol + 0.1 * d)
                self.audio.play('select')
        self.menu_input(self.music_items())

    # ------------------------------------------------------------ the SHOP screen
    def shop_offers(self):
        f = self.floor
        return [
            ('potion', 'Potion', 'Carry one more healing potion', 15 + f * 2),
            ('hp', 'Vitality Elixir', '+15 max HP, heals it now', 35 + f * 5),
            ('dmg', 'Whetstone', '+2 damage, forever', 35 + f * 5),
            ('speed', 'Swift Boots', '+8 speed, forever', 30 + f * 4),
        ]

    def shop_items(self):
        items = [(f"{name}  -  {cost}g", (lambda k=key, c=cost: self.buy_shop_item(k, c)))
                 for key, name, desc, cost in self.shop_offers()]
        items.append(("LEAVE SHOP", self.close_shop))
        return items

    def open_shop(self, back_to):
        self.audio.play('select')
        self.return_state = back_to
        self.state = 'shop'
        self.menu_sel = 0

    def close_shop(self):
        self.audio.play('select')
        self.state = self.return_state
        self.menu_sel = self.select_item_index(self.menu_items(), "SHOP")

    def buy_shop_item(self, key, cost):
        p = self.player
        if p.gold < cost:
            self.audio.play('deflect')
            self.toast("Not enough gold!", (255, 160, 140))
            return
        p.gold -= cost
        self.audio.play('coin')
        if key == 'potion':
            p.potions += 1
            self.toast("+1 Potion", (255, 180, 200))
        elif key == 'hp':
            p.max_hp += 15
            p.hp = min(p.max_hp, p.hp + 15)
            self.toast("+15 Max HP", (255, 120, 140))
        elif key == 'dmg':
            p.dmg += 2
            self.toast("+2 Damage", (255, 190, 110))
        elif key == 'speed':
            p.speed += 8
            self.toast("+8 Speed", (150, 220, 255))

    def shop_input(self):
        if self.input.nav('back'):
            self.close_shop()
        else:
            self.menu_input(self.shop_items())

    def menu_input(self, items):
        inp = self.input
        if inp.nav('up'):
            self.menu_sel = (self.menu_sel - 1) % len(items)
            self.audio.play('select')
        if inp.nav('down'):
            self.menu_sel = (self.menu_sel + 1) % len(items)
            self.audio.play('select')
        if inp.nav('confirm'):
            items[self.menu_sel][1]()

    # ------------------------------------------------------------ the Controls screen
    def ctl_rows(self):
        if self.ctl_tab == 0:
            rows = [('bind', a) for a in GAME_ACTIONS] + [('reset', None)]
        elif self.ctl_tab == 1:
            rows = ([('bind', a) for a in PAD_ACTIONS] + [('slider', 'deadzone'), ('toggle', 'vibration'),
                    ('toggle', 'stick_aims'), ('toggle', 'stick_attack'), ('toggle', 'aim_assist'), ('reset', None)])
        else:
            rows = []
        return rows + [('back', None)]

    def set_tab(self, i):
        self.ctl_tab, self.ctl_row, self.ctl_col = i % 3, 0, 0
        self.audio.play('select')

    def ctl_reset(self):
        if self.ctl_tab in (0, 1):
            self.input.reset('keyboard' if self.ctl_tab == 0 else 'gamepad')
            self.toast("Controls reset to the defaults", (170, 230, 255))
            self.audio.play('select')

    def ctl_activate(self):
        rows = self.ctl_rows()
        kind, key = rows[min(self.ctl_row, len(rows) - 1)]
        inp = self.input
        if kind == 'bind':
            device = 'keyboard' if self.ctl_tab == 0 else 'gamepad'
            if device == 'gamepad' and not inp.backend.connected:
                self.toast("No controller found. Connect one first (see the LAYOUT & SETUP tab).", (255, 170, 140))
                self.audio.play('deflect')
                return
            inp.start_capture(device, key, self.ctl_col)
            self.audio.play('select')
        elif kind == 'toggle':
            inp.settings[key] = not inp.settings[key]
            inp.save()
            self.audio.play('select')
            if key == 'vibration' and inp.settings[key]:
                self.rumble(0.8, 300)
        elif kind == 'reset':
            self.ctl_reset()
        elif kind == 'back':
            self.close_controls()

    def controls_input(self):
        inp = self.input
        if inp.nav('tab_next'):
            self.set_tab(self.ctl_tab + 1)
        if inp.nav('tab_prev'):
            self.set_tab(self.ctl_tab - 1)
        if inp.nav('back'):
            self.close_controls()
            return
        rows = self.ctl_rows()
        n = len(rows)
        self.ctl_row = min(self.ctl_row, n - 1)
        if inp.nav('up'):
            self.ctl_row = (self.ctl_row - 1) % n
        if inp.nav('down'):
            self.ctl_row = (self.ctl_row + 1) % n
        kind, key = rows[self.ctl_row]
        if inp.nav('left') or inp.nav('right'):
            d = -1 if inp.nav('left') else 1
            if kind == 'bind':
                self.ctl_col = 0 if d < 0 else 1
            elif kind == 'slider':
                inp.settings[key] = round(max(0.05, min(0.5, inp.settings[key] + 0.03 * d)), 2)
                inp.save()
            elif kind == 'toggle':
                inp.settings[key] = not inp.settings[key]
                inp.save()
        if inp.nav('confirm'):
            self.ctl_activate()
        if inp.nav('reset'):
            self.ctl_reset()

    # ------------------------------------------------------------ turning input into game actions
    def process_input(self):
        inp = self.input
        for msg, col in inp.messages:
            self.toast(msg, col)
        inp.messages.clear()
        if inp.capture is not None:                  # the Controls screen is waiting for a new key/button
            return
        if inp.pressed('mute'):
            self.audio.toggle_mute()
            self.toast("Sound OFF" if self.audio.muted else "Sound ON")
        st = self.state
        n = len(CLASS_ORDER)
        if st == 'title':
            self.menu_input(self.title_items())
        elif st == 'select':
            if inp.nav('left'):
                self.sel = (self.sel - 1) % n
            if inp.nav('right'):
                self.sel = (self.sel + 1) % n
            if inp.nav('confirm'):
                self.audio.play('select')
                self.new_run(CLASS_ORDER[self.sel])
            elif inp.nav('back'):
                self.go_title()
        elif st == 'playing':
            if inp.pressed('pause'):
                self.state = 'paused'
                self.menu_sel = 0
                return
            if inp.pressed('potion'):
                self.drink_potion()
            if inp.pressed('interact'):
                self.try_descend()
            for i in range(3):
                if inp.pressed(f'ability{i + 1}'):
                    self.use_ability(i)
        elif st == 'paused':
            if inp.pressed('pause') or inp.nav('back'):
                self.resume()
            else:
                self.menu_input(self.pause_items())
        elif st == 'controls':
            self.controls_input()
        elif st == 'music':
            self.music_input()
        elif st == 'shop':
            self.shop_input()
        elif st in ('dead', 'victory'):
            if inp.nav('confirm'):
                self.go_title()

    # ------------------------------------------------------------ mouse & window events
    def select_rects(self):
        n = len(CLASS_ORDER)
        margin, gap = 14, 10
        spacing = (WIDTH - 2 * margin) // n
        card_w = spacing - gap
        return [pygame.Rect(margin + i * spacing, 92, card_w, 392) for i in range(n)]

    def mouse_hover(self, pos):
        if self.state == 'select':
            for i, r in enumerate(self.select_rects()):
                if r.collidepoint(pos):
                    self.sel = i
            return
        if self.input.capture is not None:
            return
        for h in self._hits:
            if h[0].collidepoint(pos):
                if h[1] == 'menu':
                    self.menu_sel = h[2]
                elif h[1] == 'cell':
                    self.ctl_row, self.ctl_col = h[2], h[3]
                elif h[1] == 'btn':
                    self.ctl_row = h[2]
                break

    def mouse_click(self, pos):
        if self.state == 'select':
            for i, r in enumerate(self.select_rects()):
                if r.collidepoint(pos):
                    self.audio.play('select')
                    self.new_run(CLASS_ORDER[i])
            return
        if self.input.capture is not None:
            return
        for h in self._hits:
            if h[0].collidepoint(pos):
                if h[1] == 'menu':
                    self.menu_sel = h[2]
                    self.menu_items()[h[2]][1]()
                elif h[1] == 'tab':
                    self.set_tab(h[2])
                elif h[1] == 'cell':
                    self.ctl_row, self.ctl_col = h[2], h[3]
                    self.ctl_activate()
                elif h[1] == 'btn':
                    self.ctl_row = h[2]
                    self.ctl_activate()
                break

    def handle_event(self, e):
        n = len(CLASS_ORDER)
        if e.type == pygame.QUIT:
            self.running = False
        elif e.type == pygame.MOUSEMOTION:
            self.mouse_hover(e.pos)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.mouse_click(e.pos)
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            elif self.state == 'select' and pygame.K_1 <= e.key <= pygame.K_1 + n - 1:
                self.sel = e.key - pygame.K_1

    # ------------------------------------------------------------ drawing the world
    def camera_pos(self):
        cx, cy = self.cam.x, self.cam.y
        if self.shake > 0:
            cx += random.uniform(-1, 1) * self.shake * 16
            cy += random.uniform(-1, 1) * self.shake * 16
        return (int(max(0, min(MAP_W * TILE - WIDTH, cx))), int(max(0, min(MAP_H * TILE - HEIGHT, cy))))

    def blit_feet(self, img, sx, feet_y, pad, alpha=None):
        if alpha is not None:
            img = img.copy()
            img.set_alpha(alpha)
        self.screen.blit(img, (int(sx - img.get_width() // 2), int(feet_y + pad - img.get_height())))

    def draw_enemy(self, o, cx, cy):
        sp, scr = self.sprites, self.screen
        sx, sy = int(o.x - cx), int(o.y - cy)
        frame = int(o.anim * (10 if o.kind == 'bat' else 4)) % 2
        if o.elite:
            frames, pad = sp.big_enemy(o.kind)
            img = frames[frame]
        else:
            img, pad = sp.enemy[o.kind][frame], sp.foot[('e', o.kind)]
        tint = None
        if o.flash > 0:
            tint = (170, 170, 170)
        elif o.warn and int(self.t * 14) % 2 == 0:
            tint = (210, 40, 40)
        elif o.freeze_t > 0:
            tint = (70, 130, 190)
        elif o.slow_t > 0:
            tint = (0, 50, 120)
        elif o.poison_t > 0:
            tint = (0, 85, 0)
        if tint or o.kind == 'wraith':
            img = img.copy()
            if tint:
                img.fill((*tint, 0), special_flags=pygame.BLEND_RGB_ADD)
            if o.kind == 'wraith':
                img.set_alpha(150 + int(40 * math.sin(self.t * 4 + o.anim)))
        lift = FLYERS.get(o.kind, 0)
        if lift:
            lift += int(3 * math.sin(o.anim * 6))
        feet = sy + o.h / 2 + 2 - lift
        scr.blit(img, (int(sx - img.get_width() // 2), int(feet + pad - img.get_height())))
        top = feet + pad - img.get_height()
        if o.awake and o.kind not in BOSS_KINDS and o.hp < o.max_hp:
            bw = max(30, int(o.w * 1.2))
            pygame.draw.rect(scr, (12, 6, 14), (sx - bw // 2 - 1, top - 1, bw + 2, 7), border_radius=3)
            pygame.draw.rect(scr, (210, 40, 50), (sx - bw // 2, top, int(bw * max(0, o.hp) / o.max_hp), 5), border_radius=2)
            pygame.draw.rect(scr, (255, 130, 130), (sx - bw // 2, top, int(bw * max(0, o.hp) / o.max_hp), 2), border_radius=1)
        if o.elite:
            self.text("ELITE", 18, (255, 220, 90), (sx, top - 12), center=True, outline=True)
        if o.warn:
            self.text("!", 44, (255, 70, 70), (sx, top - 8), center=True, outline=True)
        if o.freeze_t > 0:                                   # a block of ice with a little heart on it
            iw, ih = img.get_width() + 8, img.get_height() + 6
            ice = pygame.Surface((iw, ih), pygame.SRCALPHA)
            pygame.draw.rect(ice, (150, 215, 255, 95), (0, 0, iw, ih), border_radius=8)
            pygame.draw.rect(ice, (225, 245, 255, 220), (0, 0, iw, ih), 2, border_radius=8)
            pygame.draw.line(ice, (255, 255, 255, 200), (6, ih - 8), (iw // 3, 6), 2)
            if o.freeze_t < 0.6 and int(self.t * 16) % 2:    # flickers just before it thaws
                ice.set_alpha(110)
            scr.blit(ice, (int(sx - iw // 2), int(top - 3)))
            self.draw_heart(sx, int(top - 12), 6, (255, 150, 200))
            self.add_glow(sx, sy, 60, (150, 215, 255), 0.7)
        if self.player.sky_mark_enemy is o and self.sky_recast_ready():   # the Monk's orb, stuck to it
            for k in range(2):
                a = self.t * 5 + k * math.pi
                ox, oy = int(sx + math.cos(a) * (o.w * 0.5 + 12)), int(sy - 4 + math.sin(a) * (o.w * 0.25 + 6))
                pygame.draw.circle(scr, (255, 235, 150), (ox, oy), 5)
                pygame.draw.circle(scr, (255, 255, 235), (ox, oy), 2)
                self.add_glow(ox, oy, 26, (255, 235, 150), 0.9)
            pygame.draw.circle(scr, (255, 235, 150), (sx, int(top - 14)), 7)
            pygame.draw.circle(scr, (255, 255, 235), (sx, int(top - 14)), 4)
            self.add_glow(sx, int(top - 14), 34, (255, 235, 150), 1.0)
        if o.stun_t > 0:
            for k in range(3):
                a = self.t * 6 + k * 2.1
                pygame.draw.circle(scr, (255, 235, 90), (int(sx + math.cos(a) * 12), int(top + 6 + math.sin(a) * 4)), 3)

    def draw_heart(self, sx, sy, r, color):
        """A little heart centred on (sx, sy); r is roughly half its width."""
        scr = self.screen
        k = max(2, int(r * 0.58))
        for col, g in (((255, 255, 255), 2), (color, 0)):
            pygame.draw.circle(scr, col, (sx - k, sy - k // 2), k + g)
            pygame.draw.circle(scr, col, (sx + k, sy - k // 2), k + g)
            pygame.draw.polygon(scr, col, [(sx - 2 * k - g, sy), (sx, sy + int(r * 1.25) + g * 2), (sx + 2 * k + g, sy)])

    def draw_minion(self, m, cx, cy):
        sp, scr = self.sprites, self.screen
        sx, sy = int(m.x - cx), int(m.y - cy)
        key = m.kind + ('_flip' if m.face_left else '')
        img = sp.minion[key][int(m.anim * (10 if m.kind == 'hawk' else 6)) % 2]
        pad = sp.foot[('m', m.kind)]
        if m.spawn > 0:
            k = 0.6 + 0.4 * (1 - m.spawn / 0.4)
            img = pygame.transform.smoothscale(img, (max(2, int(img.get_width() * k)), max(2, int(img.get_height() * k))))
        if m.flash > 0:
            img = img.copy()
            img.fill((170, 170, 170, 0), special_flags=pygame.BLEND_RGB_ADD)
        lift = 0
        if m.kind == 'hawk':
            lift = 16 + int(3 * math.sin(m.anim * 5))
        ox = oy = 0
        if m.lunge > 0:
            k = math.sin(math.pi * m.lunge / 0.14) * 9
            ox, oy = m.vec[0] * k, m.vec[1] * k
        feet = sy + m.h / 2 + 2 - lift + oy
        scr.blit(img, (int(sx + ox - img.get_width() // 2), int(feet + pad - img.get_height())))
        top = feet + pad - img.get_height()
        bw = max(26, int(m.w * 1.2))
        pygame.draw.rect(scr, (10, 14, 12), (sx - bw // 2 - 1, top - 1, bw + 2, 6), border_radius=3)
        pygame.draw.rect(scr, (80, 220, 120), (sx - bw // 2, top, int(bw * max(0, m.hp) / m.max_hp), 4), border_radius=2)
        if m.life is not None and m.life < 4:
            self.text(f"{m.life:.0f}", 18, (200, 220, 255), (sx, top - 10), center=True, outline=True)

    def draw_world(self):
        scr, sp, p, pal = self.screen, self.sprites, self.player, self.pal
        cx, cy = self.camera_pos()
        t = self.t
        scr.blit(self.level_surf, (0, 0), pygame.Rect(cx, cy, WIDTH, HEIGHT))
        gl = self.glow_layer
        gl.fill((0, 0, 0))
        lights = []                    # (world x, world y, radius, colour, darkness-cut strength, colour-glow strength)

        # --- wall torches
        for tx, ty, ph in self.torches:
            sx, sy = tx - cx, ty - cy
            if -160 < sx < WIDTH + 160 and -160 < sy < HEIGHT + 160:
                fl = 7 + 2.5 * math.sin(t * 13 + ph * 3) + 1.5 * math.sin(t * 7.3 + ph)
                pygame.draw.ellipse(scr, (255, 110, 30), (sx - 6, sy - fl - 4, 12, fl + 10))
                pygame.draw.ellipse(scr, (255, 190, 70), (sx - 4, sy - fl, 8, fl + 5))
                pygame.draw.ellipse(scr, (255, 245, 180), (sx - 2, sy - fl + 3, 4, fl))
                self.add_glow(sx, sy - 4, 34, (255, 170, 70), 1.4)
                lights.append((tx, ty, 160 + 10 * math.sin(t * 9 + ph), pal['light'], 0.92, 0.5))
        for (lx, ly, lr, lc, ls) in self.static_lights:
            lights.append((lx, ly, lr, lc, ls * 0.8, ls))
        for f in self.flashes:
            k = f[5] / f[6]
            lights.append((f[0], f[1], f[2], f[3], f[4] * k, f[4] * k))

        # --- stairs
        if self.stairs:
            sx, sy = int(self.stairs[0] - cx), int(self.stairs[1] - cy)
            scr.blit(sp.stairs, (sx - TILE // 2, sy - TILE // 2))
            locked = self.boss_alive()
            lights.append((self.stairs[0], self.stairs[1], 130, (230, 70, 70) if locked else (110, 190, 255), 0.6, 0.45))
            if not locked:
                a = t * 2
                for k in range(3):
                    ang = a + k * 2.094
                    pygame.draw.circle(scr, (170, 220, 255), (int(sx + math.cos(ang) * 22), int(sy + math.sin(ang) * 22)), 2)

        # --- corpses (necromancers see their raisable dead glowing)
        for c in self.corpses:
            img = sp.corpse(c.kind)
            scr.blit(img, (int(c.x - cx - img.get_width() / 2), int(c.y - cy - img.get_height() / 2)))
            if p.cls == 'necromancer':
                self.add_glow(c.x - cx, c.y - cy, 40, (90, 255, 150), 0.7 + 0.2 * math.sin(t * 4))

        # --- shadows, then everything standing on the floor sorted by depth
        things = self.items + self.enemies + self.minions + [p]
        things.sort(key=lambda o: o.y)
        for o in things:
            sx, sy = int(o.x - cx), int(o.y - cy)
            if sx < -90 or sx > WIDTH + 90 or sy < -90 or sy > HEIGHT + 90:
                continue
            if isinstance(o, Item):
                w = 22
            else:
                w = o.w * 1.7
            sh = sp.shadow(w, w * 0.45)
            fy = sy + (6 if isinstance(o, Item) else o.h / 2 + 2)
            scr.blit(sh, (int(sx - sh.get_width() / 2), int(fy - sh.get_height() / 2)))
        for tr in self.trail:                                                # dash after-images
            img = sp.player[(p.cls, tr[2], 0)]
            self.blit_feet(img, tr[0] - cx, tr[1] - cy + p.h / 2 + 2, sp.foot[('p', p.cls)], int(130 * tr[3] / 0.22))
        for o in things:
            sx, sy = int(o.x - cx), int(o.y - cy)
            if sx < -90 or sx > WIDTH + 90 or sy < -90 or sy > HEIGHT + 90:
                continue
            if o is p:
                if p.invuln > 0 and int(t * 20) % 2 == 0 and p.dash_t <= 0 and p.launch_t <= 0:
                    continue
                img = sp.player[(p.cls, p.dir_name, int(p.anim * 8) % 2 if p.moving else 0)]
                bob = int(1.6 * math.sin(p.anim * 16)) if p.moving else int(1.2 * math.sin(t * 2.5))
                self.blit_feet(img, sx, sy + p.h / 2 + 2 + bob * 0.5, sp.foot[('p', p.cls)])
                if p.buffs.get('shield', 0) > 0:
                    bub = pygame.Surface((84, 84), pygame.SRCALPHA)
                    pygame.draw.circle(bub, (90, 160, 255, 60), (42, 42), 38)
                    pygame.draw.circle(bub, (170, 215, 255, 210), (42, 42), 38, 3)
                    scr.blit(bub, (sx - 42, sy - 44))
                    self.add_glow(sx, sy, 80, (90, 150, 255), 0.7)
            elif isinstance(o, Enemy):
                self.draw_enemy(o, cx, cy)
                if o.elite:
                    self.add_glow(sx, sy, 70, (255, 200, 60), 0.55)
                if o.kind in BOSS_KINDS and o.awake:
                    lights.append((o.x, o.y, 220, (200, 80, 255) if o.kind == 'boss' else (255, 120, 60), 0.4, 0.4))
            elif isinstance(o, Item):
                bob = int(2 * math.sin(o.t * 4)) if o.kind == 'potion' else 0
                if o.kind == 'coin':
                    img, g = sp.coin[int(o.t * 8) % 4], (255, 210, 80)
                elif o.kind == 'potion':
                    img, g = sp.potion, (255, 80, 110)
                else:
                    img, g = sp.chest[1 if o.opened else 0], (255, 220, 100)
                scr.blit(img, (sx - img.get_width() // 2, sy - img.get_height() + 12 + bob))
                if not (o.kind == 'chest' and o.opened):
                    self.add_glow(sx, sy, 34, g, 0.7)
            else:
                self.draw_minion(o, cx, cy)
                if o.group in ('undead', 'army'):
                    self.add_glow(sx, sy, 46, (90, 255, 160), 0.6)
                    lights.append((o.x, o.y, 70, (90, 255, 160), 0.2, 0.25))

        # --- attack effects
        c = CLASSES[p.cls]
        if p.swing > 0 and c['atk'] == 'melee':
            ang = math.degrees(math.atan2(-p.face.y, p.face.x))
            img = sp.slash(ang).copy()
            img.set_alpha(int(255 * p.swing / 0.16))
            scr.blit(img, img.get_rect(center=(int(p.x + p.face.x * c['reach'] - cx), int(p.y + p.face.y * c['reach'] - cy))))
        if p.spin > 0:
            for k in range(4):
                a = t * 18 + k * math.pi / 2
                img = sp.slash(-math.degrees(a)).copy()
                img.set_alpha(int(255 * p.spin / 0.45))
                scr.blit(img, img.get_rect(center=(int(p.x - cx + math.cos(a) * 54), int(p.y - cy + math.sin(a) * 54))))
            self.add_glow(p.x - cx, p.y - cy, 90, (150, 190, 255), 0.5)
        for r in self.rings:
            k = r[3] / r[4]
            rad = int(r[2] * (k ** 0.55))
            col = tuple(int(v * (1 - k * 0.8)) for v in r[5])
            pygame.draw.circle(scr, col, (int(r[0] - cx), int(r[1] - cy)), max(2, rad), max(2, int(5 * (1 - k))))
            pygame.draw.circle(gl, col, (int((r[0] - cx) / 4), int((r[1] - cy) / 4)), max(1, rad // 4), 2)
        for z in self.zaps:
            pts = z[0]
            col = z[3] if int(t * 40) % 2 else (255, 255, 255)
            for a, b in zip(pts, pts[1:]):
                last = (a[0] - cx, a[1] - cy)
                for s in range(1, 5):
                    u = s / 4
                    nx = a[0] + (b[0] - a[0]) * u - cx + (random.uniform(-9, 9) if s < 4 else 0)
                    ny = a[1] + (b[1] - a[1]) * u - cy + (random.uniform(-9, 9) if s < 4 else 0)
                    pygame.draw.line(scr, col, last, (nx, ny), 3)
                    pygame.draw.line(gl, col, (last[0] / 4, last[1] / 4), (nx / 4, ny / 4), 2)
                    last = (nx, ny)
            lights.append((pts[-1][0], pts[-1][1], 120, z[3], 0.5, 0.6))
        for pr in self.projectiles:
            sx, sy = int(pr.x - cx), int(pr.y - cy)
            pygame.draw.circle(scr, pr.color, (sx, sy), pr.radius)
            pygame.draw.circle(scr, (255, 255, 255), (sx, sy), max(1, pr.radius - 3))
            self.add_glow(sx, sy, 38, pr.color, 1.0)
        for b in self.bolts:
            sx, sy = int(b.x - cx), int(b.y - cy)
            if b.kind in ('knife', 'arrow'):
                n = math.hypot(b.vx, b.vy) or 1
                ux, uy = b.vx / n, b.vy / n
                ln = 20 if b.kind == 'arrow' else 14
                pygame.draw.line(scr, b.color, (sx, sy), (sx - ux * ln, sy - uy * ln), 3)
                pygame.draw.circle(scr, (255, 255, 255), (sx, sy), 2)
                self.add_glow(sx, sy, 26, b.color, 0.6)
            elif b.kind == 'heart':
                self.draw_heart(sx, sy - 3, b.radius + int(1.5 * math.sin(t * 22)), b.color)
                self.add_glow(sx, sy, 56, (170, 225, 255), 1.0)
                lights.append((b.x, b.y, 100, b.color, 0.6, 0.55))
            elif b.kind == 'orb':
                pygame.draw.circle(scr, b.color, (sx, sy), b.radius)
                pygame.draw.circle(scr, (255, 255, 240), (sx, sy), b.radius - 4)
                a = t * 16
                pygame.draw.circle(scr, (255, 255, 255), (int(sx + math.cos(a) * (b.radius + 4)),
                                                          int(sy + math.sin(a) * (b.radius + 4))), 2)
                pygame.draw.circle(scr, (255, 200, 110), (sx, sy), b.radius + 4, 2)
                self.add_glow(sx, sy, 60, b.color, 1.2)
                lights.append((b.x, b.y, 110, b.color, 0.6, 0.55))
            else:
                rad = b.radius + (int(2 * math.sin(t * 30)) if b.kind == 'fire' else 0)
                pygame.draw.circle(scr, b.color, (sx, sy), rad)
                pygame.draw.circle(scr, (255, 255, 230), (sx, sy), max(1, rad - 3))
                self.add_glow(sx, sy, 60 if b.kind == 'fire' else 40, b.color, 1.1)
                lights.append((b.x, b.y, 110 if b.kind == 'fire' else 70, b.color, 0.6, 0.55))
        for i, (fx, fy) in enumerate(self.flower_spots()):                   # Ghala's Flower Ring
            sx, sy = int(fx - cx), int(fy - cy)
            spin = -t * 5 + i
            for j in range(5):
                a = spin + j * 1.2566
                px, py = int(sx + math.cos(a) * 7), int(sy + math.sin(a) * 7)
                pygame.draw.circle(scr, (255, 255, 255), (px, py), 6)
                pygame.draw.circle(scr, (255, 130, 195) if i % 2 else (255, 175, 220), (px, py), 5)
            pygame.draw.circle(scr, (255, 225, 100), (sx, sy), 4)
            self.add_glow(sx, sy, 34, (255, 150, 200), 0.9)
            if random.random() < 0.25:
                self.particles.append(Particle(fx, fy, random.uniform(-25, 25), random.uniform(-25, 25),
                                               0.4, (255, 190, 225), 3, glow=True))
        if p.buffs.get('flowers', 0) > 0:
            lights.append((p.x, p.y, 150, (255, 150, 200), 0.3, 0.35))
        for pa in self.particles:
            sx, sy = int(pa.x - cx), int(pa.y - cy)
            k = max(0.0, pa.life / pa.max_life)
            col = tuple(int(v * (0.35 + 0.65 * k)) for v in pa.color)
            pygame.draw.rect(scr, col, (sx, sy, pa.size, pa.size))
            if pa.glow:
                self.add_glow(sx, sy, 16 + pa.size * 4, pa.color, 0.8 * k)

        # --- fog drifting through the dungeon (lit by the lights, so drawn BEFORE the darkness)
        if self.fog_img:
            for i in range(3):
                fx = ((i * 520 + t * (12 + i * 5) - cx * 0.45) % (WIDTH + 560)) - 560
                fy = 90 + i * 210 + math.sin(t * 0.25 + i * 2) * 26 - cy * 0.25 % 200
                scr.blit(self.fog_img, (int(fx), int(fy)))

        # --- darkness with holes of light
        ov = self.overlay
        ov.fill((*pal['ambient'], pal['dark'] - 14))
        glow = 340 + 5 * math.sin(t * 9)
        lights.append((p.x, p.y, glow, (255, 232, 200), 1.0, 0.1))
        if self.levelup_t > 0:
            k = self.levelup_t / 1.3
            lights.append((p.x, p.y, 220, (255, 225, 110), 0.8 * k, 0.9 * k))
            bx = int((p.x - cx) / 4)
            pygame.draw.rect(gl, (int(255 * k), int(220 * k), int(110 * k)), (bx - 3, 0, 6, int((p.y - cy) / 4)))
        for (wx, wy, r, col, sub, addi) in lights:
            sx, sy = int(wx - cx), int(wy - cy)
            if sx < -r or sx > WIDTH + r or sy < -r or sy > HEIGHT + r:
                continue
            if sub > 0:
                m = self.mask(r, min(1.0, sub))
                ov.blit(m, (sx - m.get_width() // 2, sy - m.get_height() // 2), special_flags=pygame.BLEND_RGBA_SUB)
            if addi > 0:
                self.add_glow(sx, sy, r * 1.05, col, addi)
        scr.blit(ov, (0, 0))
        scr.blit(pygame.transform.smoothscale(gl, (WIDTH, HEIGHT)), (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        # --- floating dust, damage numbers, prompts
        for m in self.motes:
            a = 0.35 + 0.35 * math.sin(m[4] * 1.7)
            img = self.sprites.glow(3 + m[5] * 2, pal['mote'], max(0.05, a))
            scr.blit(img, (int(m[0]), int(m[1])), special_flags=pygame.BLEND_RGB_ADD)
        for ft in self.texts:
            age = ft.max_life - ft.life
            base = 40 if ft.big else 26
            size = int(base * (1.0 + 0.5 * max(0.0, 1 - age / 0.14)))
            self.text(ft.text, size, ft.color, (int(ft.x - cx), int(ft.y - cy)), center=True, outline=True,
                      alpha=255 if ft.life > 0.3 else int(255 * ft.life / 0.3))
        if self.stairs and math.hypot(p.x - self.stairs[0], p.y - self.stairs[1]) < 40:
            if self.boss_alive():
                self.text("Defeat the boss to unlock the stairs", 28, (255, 130, 120),
                          (int(p.x - cx), int(p.y - cy) - 56), center=True, outline=True)
            else:
                self.draw_inline(["Press ", ('action', 'interact'), " to go down the stairs"],
                                 int(p.x - cx), int(p.y - cy) - 56, 28, (255, 240, 150))

        scr.blit(self.vignette, (0, 0))
        danger = max(p.hurt_flash * 1.6, (0.35 + 0.25 * math.sin(t * 6)) if p.hp < p.max_hp * 0.3 else 0)
        if danger > 0:
            self.vignette_red.set_alpha(int(255 * min(1.0, danger)))
            scr.blit(self.vignette_red, (0, 0))

    def build_backdrop(self):
        """A moody dungeon hall for the title and hero-select screens."""
        sp = self.sprites
        ts = sp.tiles(1)
        s = pygame.Surface((WIDTH, HEIGHT))
        self.title_torches = []
        for ty in range(HEIGHT // TILE + 1):
            for tx in range(WIDTH // TILE + 1):
                x, y = tx * TILE, ty * TILE
                if ty <= 9:
                    s.blit(ts.wall_front[(tx * 5 + ty * 3) % 4], (x, y))
                else:
                    s.blit(ts.floor[(tx * 7 + ty * 13) % 8], (x, y))
                    if ty == 10:
                        s.blit(ts.ao_n, (x, y))
        for tx in (2, 8, 23, 29):
            sp.torch_bracket(s, tx * TILE, 7 * TILE)
            self.title_torches.append((tx * TILE + 20, 7 * TILE + 12, tx))
        for tx in (5, 12, 19, 26):
            sp.banner(s, tx * TILE, 2 * TILE, biome(1)['banner'])
        return s

    # ------------------------------------------------------------ button pictures & small UI helpers
    def key_surface(self, text, size=22):
        f = self.font(max(15, size - 4))
        img = f.render(text, True, (240, 225, 190))
        w = max(size, img.get_width() + 14)
        s = pygame.Surface((w + 2, size + 4), pygame.SRCALPHA)
        r = pygame.Rect(1, 2, w, size)
        pygame.draw.rect(s, (14, 10, 20), r, border_radius=5)
        pygame.draw.rect(s, (190, 160, 100), r, 1, border_radius=5)
        s.blit(img, img.get_rect(center=r.center))
        return s

    def pad_icon_surface(self, ctrl, size=22):
        tmp = pygame.Surface((size * 5, size + 6), pygame.SRCALPHA)
        w = draw_pad_icon(tmp, ctrl, size * 5 // 2, (size + 6) // 2, size, self.font(max(14, size - 8)))
        return tmp.subsurface((size * 5 // 2 - w // 2 - 2, 0, w + 4, size + 6)).copy()

    def badge_surface(self, kind, value, size=22):
        """A little picture of the key (keyboard) or the PlayStation button (controller) for an action."""
        inp = self.input
        use_pad = inp.device == 'gamepad'
        if kind == 'action':
            ctrl = inp.pad_primary(value) if use_pad else None
            labels = inp.labels(value, 'keyboard')
            text = '-' if use_pad else (labels[0] if labels else '-')
        else:                                           # menu buttons that never change
            ctrl = {'confirm': 'a', 'back': 'b'}.get(value) if use_pad else None
            text = {'confirm': 'Enter', 'back': 'Esc'}.get(value, value)
        key = (ctrl, text, size)
        s = self._badges.get(key)
        if s is None:
            if len(self._badges) > 300:
                self._badges.clear()
            s = self.pad_icon_surface(ctrl, size) if ctrl else self.key_surface(text, size)
            self._badges[key] = s
        return s

    def draw_inline(self, parts, cx, cy, size=28, color=(235, 230, 215)):
        """Draw a line made of words and button pictures, e.g. ["Press ", ('action','interact'), " to descend"]."""
        imgs = []
        for p in parts:
            imgs.append(self.text_img(p, size, color, True) if isinstance(p, str)
                        else self.badge_surface(p[0], p[1], int(size * 0.85)))
        x = cx - sum(i.get_width() for i in imgs) // 2
        for img in imgs:
            self.screen.blit(img, (x, cy - img.get_height() // 2))
            x += img.get_width()

    def draw_toasts(self):
        ctl = self.state == 'controls'
        shown = list(self.toasts)[-2:] if ctl else list(self.toasts)
        for i, (msg, col, life) in enumerate(shown):
            img = self.text_img(msg, 22 if ctl else 26, col, True)
            r = pygame.Rect(0, 0, img.get_width() + 40, 30 if ctl else 34)
            r.center = (WIDTH - 40 - r.w // 2, 30 + i * 36) if ctl else (WIDTH // 2, 150 + i * 40)
            self.panel(r, alpha=225, border=(150, 130, 90), radius=9)
            img = img if life > 0.5 else img.copy()
            if life <= 0.5:
                img.set_alpha(int(255 * life / 0.5))
            self.screen.blit(img, img.get_rect(center=r.center))

    def draw_pad_status(self, x, y):
        inp = self.input
        ok = inp.backend.connected
        text = f"Controller: {inp.backend.name}" if ok else "No controller detected"
        img = self.text_img(text, 22, (150, 235, 175) if ok else (190, 190, 210), True)
        r = pygame.Rect(x, y, img.get_width() + 52, 34)
        self.panel(r, alpha=200, border=(110, 200, 150) if ok else (100, 95, 120), radius=9)
        pygame.draw.circle(self.screen, (90, 240, 140) if ok else (130, 130, 150), (x + 20, y + 17), 7)
        self.screen.blit(img, (x + 36, y + 17 - img.get_height() // 2))

    def draw_menu(self, items, cx, y0, w=330, h=52, gap=10):
        for i, (label, _) in enumerate(items):
            r = pygame.Rect(cx - w // 2, y0 + i * (h + gap), w, h)
            sel = i == self.menu_sel
            self.panel(r, alpha=235 if sel else 200, border=(255, 214, 90) if sel else (110, 100, 130), radius=12,
                       glow=(255, 214, 90) if sel else None)
            self.text(label, 40, (255, 255, 255) if sel else (170, 170, 195), r.center, center=True, outline=sel)
            self._hits.append((r, 'menu', i))

    # ------------------------------------------------------------ HUD
    def pie(self, cx, cy, radius, frac, alpha=175):
        frac = max(0.0, min(1.0, frac))
        n = max(2, int(48 * frac))
        pts = [(radius, radius)]
        for i in range(n + 1):
            a = -math.pi / 2 + 2 * math.pi * frac * i / n
            pts.append((radius + math.cos(a) * radius * 1.5, radius + math.sin(a) * radius * 1.5))
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.polygon(s, (0, 0, 0, alpha), pts)
        self.screen.blit(s, (cx - radius, cy - radius))

    def draw_slot(self, x, y, size, icon, color, cd, cd_max, action, locked=None, dim=False, count=None):
        scr = self.screen
        ready = cd <= 0 and not locked and not dim
        self.panel((x, y, size, size), alpha=235, border=color if ready else (110, 104, 122), radius=9,
                   glow=color if ready else None)
        if locked:
            self.text(f"Lv {locked}", 26, (150, 150, 165), (x + size // 2, y + size // 2), center=True)
        else:
            scr.blit(icon, (x + (size - icon.get_width()) // 2, y + (size - icon.get_height()) // 2))
            if dim:
                self.dim_rect(x, y, size, size, 130)
            if cd > 0:
                clip = pygame.Rect(x, y, size, size)
                old = scr.get_clip()
                scr.set_clip(clip)
                self.pie(x + size // 2, y + size // 2, size // 2 + 2, cd / max(0.1, cd_max))
                scr.set_clip(old)
                self.text(f"{cd:.0f}" if cd >= 1 else f"{cd:.1f}", 30, (255, 255, 255), (x + size // 2, y + size // 2), center=True, outline=True)
        if count is not None:
            self.text(str(count), 24, (255, 255, 255), (x + size - 6, y + size - 22), right=True, outline=True)
        scr.blit(self.badge_surface('action', action, 20), (x + 2, y + size - 26))

    def dim_rect(self, x, y, w, h, alpha):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((0, 0, 0, alpha))
        self.screen.blit(s, (x, y))

    def draw_hud(self):
        p, scr = self.player, self.screen
        c = CLASSES[p.cls]
        # ---- portrait + bars (top-left)
        self.panel((14, 14, 360, 120))
        pc = (70, 72)
        pygame.draw.circle(scr, (22, 17, 32), pc, 42)
        img = self.sprites.player[(p.cls, 'down', 0)]
        scr.blit(img, (pc[0] - img.get_width() // 2, pc[1] - img.get_height() // 2 + 6))
        pygame.draw.circle(scr, c['color'], pc, 42, 4)
        pygame.draw.circle(scr, (255, 255, 255), pc, 45, 1)
        pygame.draw.circle(scr, (22, 17, 32), (104, 108), 17)
        pygame.draw.circle(scr, (230, 190, 80), (104, 108), 17, 3)
        self.text(str(p.level), 26, (255, 240, 190), (104, 108), center=True)
        self.text(c['title'], 26, c['color'], (130, 20), outline=False)
        self.bar(130, 46, 232, 24, p.hp / p.max_hp, (236, 90, 100), (190, 30, 48), trail=self.hp_trail / p.max_hp)
        self.text(f"{p.hp} / {p.max_hp}", 22, (255, 255, 255), (246, 58), center=True)
        self.bar(130, 78, 232, 10, p.xp / p.xp_next, (170, 200, 255), (90, 120, 230))
        self.text(f"XP {p.xp}/{p.xp_next}", 18, (190, 205, 240), (130, 91), shadow=True)
        scr.blit(self.ui['coin'], (230, 92))
        self.text(str(p.gold), 22, (255, 220, 100), (258, 96))
        scr.blit(self.ui['potion'], (306, 92))
        self.text(f"x{p.potions}", 22, (255, 140, 165), (334, 96))

        # ---- floor title (top-centre)
        self.text(f"FLOOR {self.floor}", 34, (245, 235, 210), (WIDTH // 2, 24), center=True, outline=True)
        self.text(floor_name(self.floor), 22, (205, 190, 150), (WIDTH // 2, 50), center=True)
        pygame.draw.line(scr, (176, 140, 78), (WIDTH // 2 - 130, 64), (WIDTH // 2 - 20, 64), 2)
        pygame.draw.line(scr, (176, 140, 78), (WIDTH // 2 + 20, 64), (WIDTH // 2 + 130, 64), 2)
        pygame.draw.polygon(scr, (230, 190, 80), [(WIDTH // 2, 59), (WIDTH // 2 + 6, 64), (WIDTH // 2, 69), (WIDTH // 2 - 6, 64)])

        # ---- minimap (top-right)
        mw, mh = MAP_W * MINIMAP_SCALE, MAP_H * MINIMAP_SCALE
        mx, my = WIDTH - mw - 28, 22
        self.panel((mx - 8, my - 8, mw + 16, mh + 16), alpha=200)
        scr.blit(self.mini, (mx, my))
        ms = MINIMAP_SCALE
        for m in self.minions:
            pygame.draw.rect(scr, (90, 255, 150), (mx + int(m.x // TILE) * ms, my + int(m.y // TILE) * ms, ms, ms))
        for e in self.enemies:
            if e.kind in BOSS_KINDS and self.explored[int(e.y // TILE)][int(e.x // TILE)]:
                pygame.draw.circle(scr, (255, 70, 90), (mx + int(e.x // TILE) * ms + 2, my + int(e.y // TILE) * ms + 2), 4)
        pygame.draw.rect(scr, (255, 255, 255), (mx + int(p.x // TILE) * ms - 1, my + int(p.y // TILE) * ms - 1, ms + 2, ms + 2))

        # ---- boss bar
        for e in self.enemies:
            if e.kind in BOSS_KINDS and e.awake:
                bx = WIDTH // 2 - 240
                self.panel((bx - 10, 82, 500, 56), alpha=200, border=(200, 70, 110))
                self.text(e.name, 26, (255, 230, 230), (WIDTH // 2, 98), center=True, outline=True)
                self.bar(bx, 114, 480, 16, e.hp / e.max_hp, (230, 140, 255), (150, 50, 190))

        # ---- ability bar (bottom-centre)
        names = c['abilities']
        x0 = WIDTH // 2 - 196
        y0 = HEIGHT - 92
        self.panel((x0 - 16, y0 - 12, 424, 92), alpha=190)
        for i in range(3):
            ab = ABILITIES[names[i]]
            locked = UNLOCK_LEVELS[i] if p.level < UNLOCK_LEVELS[i] else None
            recast = names[i] == 'sky_strike' and self.sky_recast_ready()      # orb is stuck: press again!
            self.draw_slot(x0 + i * 76, y0, 66, self.icons[names[i]], ab['color'],
                           0 if recast else p.ability_cd[i], p.ability_max[i], f'ability{i + 1}', locked)
            if recast and int(self.t * 6) % 2:
                pygame.draw.rect(scr, (255, 255, 255), (x0 + i * 76 - 2, y0 - 2, 70, 70), 3, border_radius=10)
        sx = x0 + 3 * 76 + 14
        pygame.draw.line(scr, (110, 96, 70), (sx - 10, y0 + 6), (sx - 10, y0 + 60), 2)
        self.draw_slot(sx, y0, 66, self.ui['potion_big'], (255, 120, 150), 0, 1, "potion", dim=(p.potions == 0 or p.hp >= p.max_hp), count=p.potions)
        self.draw_slot(sx + 76, y0, 66, self.ui['dash_big'], (150, 200, 255), p.dash_cd, p.dash_cd_base, "dash")

        # ---- allies (bottom-left)
        if self.minions:
            kinds = {}
            for m in self.minions:
                kinds[m.kind] = kinds.get(m.kind, 0) + 1
            wd = 24 + 64 * len(kinds)
            self.panel((14, HEIGHT - 82, wd, 66), alpha=190, border=(110, 200, 150))
            for i, (k, n) in enumerate(kinds.items()):
                img = self.sprites.minion[k][0]
                s = pygame.transform.smoothscale(img, (int(img.get_width() * 0.62), int(img.get_height() * 0.62)))
                scr.blit(s, (30 + i * 64 - s.get_width() // 2 + 18, HEIGHT - 76))
                self.text(f"x{n}", 22, (190, 255, 210), (30 + i * 64 + 26, HEIGHT - 44), outline=True)
            self.text("ALLIES", 16, (150, 220, 180), (24, HEIGHT - 94))

        if self.show_stats:
            self.draw_stats_panel()
        if self.run_time < 16 and self.state == 'playing':
            move = "Left Stick" if self.input.device == 'gamepad' else "WASD"
            parts = [f"Move: {move}    "]
            for act, lab in (('attack', 'Attack'), ('ability1', 'Skill 1'), ('ability2', 'Skill 2'),
                             ('ability3', 'Skill 3'), ('dash', 'Dash'), ('potion', 'Potion'), ('interact', 'Stairs')):
                parts += [('action', act), f" {lab}   "]
            self.draw_inline(parts, WIDTH // 2, HEIGHT - 116, 24)

        if self.banner_t > 0:
            a = min(1.0, self.banner_t, (3.4 - self.banner_t) * 4)
            band = pygame.Surface((WIDTH, 110), pygame.SRCALPHA)
            for yy in range(110):
                k = 1 - abs(yy - 55) / 55
                pygame.draw.line(band, (0, 0, 0, int(165 * k * a)), (0, yy), (WIDTH, yy))
            scr.blit(band, (0, 200))
            self.text(self.banner_text, 64, (255, 232, 160), (WIDTH // 2, 238), center=True, outline=True, alpha=int(255 * a))
            if self.banner_sub:
                self.text(self.banner_sub, 32, (225, 215, 195), (WIDTH // 2, 280), center=True, outline=True, alpha=int(255 * a))

    def draw_stats_panel(self):
        p = self.player
        c = CLASSES[p.cls]
        r = pygame.Rect(WIDTH // 2 - 200, 130, 400, 450)
        self.panel(r, alpha=240, border=c['color'])
        self.text("YOUR HERO", 38, (255, 240, 200), (WIDTH // 2, r.y + 28), center=True, outline=True)
        rows = [("Hero", c['title']), ("Level", str(p.level)), ("Health", f"{p.hp} / {p.max_hp}"),
                ("Damage", str(p.dmg)), ("Speed", str(int(p.speed))), ("Crit chance", f"{p.crit * 100:.1f}%"),
                ("Ability cooldowns", f"{int(p.cd_mult * 100)}%"), ("Ability power", f"{int(p.ap * 100)}%"),
                ("Potion heals", str(p.potion_heal)), ("Allies", str(len(self.minions))),
                ("Monsters beaten", str(p.kills)), ("Gold", str(p.gold)),
                ("Each level gives", f"+{c['growth'][0]} HP, +{c['growth'][1]} DMG")]
        for i, (a, b) in enumerate(rows):
            y = r.y + 64 + i * 28
            self.text(a, 24, (180, 180, 205), (r.x + 26, y))
            self.text(b, 24, (255, 232, 160), (r.right - 26, y), right=True)

    # ------------------------------------------------------------ menu screens
    def lit_backdrop(self, lights_extra=()):
        """The dungeon hall behind the menus, with flickering torch light."""
        scr = self.screen
        scr.blit(self.backdrop, (0, 0))
        gl = self.glow_layer
        gl.fill((0, 0, 0))
        ov = self.overlay
        ov.fill((6, 6, 16, 205))
        for tx, ty, ph in self.title_torches:
            fl = 8 + 3 * math.sin(self.t * 13 + ph * 3)
            pygame.draw.ellipse(scr, (255, 110, 30), (tx - 7, ty - fl - 5, 14, fl + 12))
            pygame.draw.ellipse(scr, (255, 190, 70), (tx - 5, ty - fl - 1, 10, fl + 7))
            pygame.draw.ellipse(scr, (255, 245, 180), (tx - 2, ty - fl + 3, 5, fl))
            m = self.mask(260 + 10 * math.sin(self.t * 9 + ph), 0.95)
            ov.blit(m, (tx - m.get_width() // 2, ty - m.get_height() // 2), special_flags=pygame.BLEND_RGBA_SUB)
            self.add_glow(tx, ty - 4, 40, (255, 170, 70), 1.4)
            self.add_glow(tx, ty, 200, (255, 150, 60), 0.5)
        for (lx, ly, lr, sub) in lights_extra:
            m = self.mask(lr, sub)
            ov.blit(m, (lx - m.get_width() // 2, ly - m.get_height() // 2), special_flags=pygame.BLEND_RGBA_SUB)
        scr.blit(ov, (0, 0))
        scr.blit(pygame.transform.smoothscale(gl, (WIDTH, HEIGHT)), (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        for m in self.motes:
            a = 0.35 + 0.35 * math.sin(m[4] * 1.7)
            scr.blit(self.sprites.glow(3 + m[5] * 2, (255, 190, 110), max(0.05, a)), (int(m[0]), int(m[1])),
                     special_flags=pygame.BLEND_RGB_ADD)

    def draw_title(self):
        scr = self.screen
        self.lit_backdrop([(WIDTH // 2, 300, 500, 0.5)])
        for i, cls in enumerate(CLASS_ORDER):
            f = int(self.t * 3 + i) % 2
            img = self.sprites.player[(cls, 'down', f)]
            big = pygame.transform.scale(img, (img.get_width() * 2, img.get_height() * 2))
            x = WIDTH // 2 + (i - (len(CLASS_ORDER) - 1) / 2) * 158
            fy = 695 + int(2 * math.sin(self.t * 2 + i))
            sh = self.sprites.shadow(110, 34)
            scr.blit(sh, (int(x - sh.get_width() / 2), fy - 16))
            scr.blit(big, (int(x - big.get_width() / 2), fy + self.sprites.foot[('p', cls)] * 2 - big.get_height()))
        bob = int(5 * math.sin(self.t * 1.6))
        self.add_glow_screen(WIDTH // 2, 190 + bob, 360, (255, 190, 80), 0.28)
        self.text("ECHOES OF THE", 62, (205, 195, 240), (WIDTH // 2, 92 + bob), center=True, outline=True)
        self.text("BONE KING", 168, (255, 214, 90), (WIDTH // 2, 190 + bob), center=True, outline=True)
        self.text(f"A DUNGEON RPG  -  10 FLOORS  -  {len(CLASS_ORDER)} HEROES", 30, (190, 190, 220), (WIDTH // 2, 284), center=True, outline=True)
        items = self.title_items()
        self.draw_menu(items, WIDTH // 2, 322)
        menu_bottom = 322 + (len(items) - 1) * 62 + 52   # draw_menu's default row height(52) + gap(10)
        how = "D-Pad / Left Stick + " if self.input.device == 'gamepad' else "Arrows / mouse + "
        self.draw_inline([how, ('nav', 'confirm'), " to choose"], WIDTH // 2, menu_bottom + 26, 24)
        self.draw_pad_status(18, 16)

    def add_glow_screen(self, x, y, r, color, intensity):
        img = self.sprites.glow(r, color, intensity)
        self.screen.blit(img, (int(x - img.get_width() / 2), int(y - img.get_height() / 2)), special_flags=pygame.BLEND_RGB_ADD)

    def draw_select(self):
        scr = self.screen
        self.lit_backdrop([(WIDTH // 2, 300, 700, 0.55)])
        self.dim((0, 0, 10), 70)
        self.text("CHOOSE YOUR HERO", 66, (255, 214, 90), (WIDTH // 2, 48), center=True, outline=True)
        maxes = dict(hp=80, dmg=12, speed=205)
        for i, (key, r0) in enumerate(zip(CLASS_ORDER, self.select_rects())):
            c = CLASSES[key]
            sel = i == self.sel
            r = r0.move(0, -10 if sel else 0)
            self.panel(r, alpha=235 if sel else 205, border=c['color'] if sel else (100, 92, 116), radius=12,
                       glow=c['color'] if sel else None)
            self.text(c['name'], 30 if len(c['name']) <= 11 else 24, c['color'], (r.centerx, r.y + 26), center=True, outline=True)
            self.text(c['role'], 20, (180, 180, 205), (r.centerx, r.y + 50), center=True)
            if sel:
                self.add_glow_screen(r.centerx, r.y + 118, 80, c['color'], 0.5)
            img = self.sprites.player[(key, 'down', int(self.t * 3) % 2 if sel else 0)]
            big = pygame.transform.scale(img, (img.get_width() * 2, img.get_height() * 2))
            scr.blit(big, (r.centerx - big.get_width() // 2, r.y + 62))
            for j, (lab, stat, col) in enumerate((("HP", 'hp', (220, 70, 80)), ("DMG", 'dmg', (255, 170, 70)),
                                                  ("SPD", 'speed', (110, 215, 255)))):
                yy = r.y + 188 + j * 25
                self.text(lab, 21, (205, 205, 225), (r.x + 12, yy))
                pygame.draw.rect(scr, (30, 24, 40), (r.x + 58, yy + 3, r.w - 72, 12), border_radius=5)
                pygame.draw.rect(scr, col, (r.x + 58, yy + 3, int((r.w - 72) * min(1, c[stat] / maxes[stat])), 12), border_radius=5)
                pygame.draw.rect(scr, (230, 225, 210), (r.x + 58, yy + 3, r.w - 72, 12), 1, border_radius=5)
            self.text(f"Crit {int(c['crit'] * 100)}%  -  {'Ranged' if c['atk'] == 'ranged' else 'Melee'}", 20,
                      (255, 235, 160), (r.centerx, r.y + 272), center=True)
            for j, line in enumerate(self.wrap(c['blurb'], 20, r.w - 24)[:5]):
                self.text(line, 20, (200, 200, 225), (r.x + 12, r.y + 292 + j * 18), shadow=False)
        key = CLASS_ORDER[self.sel]
        c = CLASSES[key]
        self.panel((29, 500, 1222, 186), alpha=225, border=c['color'])
        for i, name in enumerate(c['abilities']):
            ab = ABILITIES[name]
            x = 52 + i * 400
            scr.blit(self.icons[name], (x, 520))
            self.text(ab['name'], 32, ab['color'], (x + 72, 520), outline=True)
            self.text(f"Unlocks at level {UNLOCK_LEVELS[i]}  -  {(self.input.labels('ability%d' % (i + 1)) or ['-'])[0]}  -  {ab['cd']}s cooldown", 20, (175, 175, 200), (x + 72, 550))
            for j, line in enumerate(self.wrap(ab['desc'], 24, 330)[:3]):
                self.text(line, 24, (225, 225, 240), (x, 592 + j * 26), shadow=True)
        how = "D-Pad / Left Stick: choose     " if self.input.device == 'gamepad' else "LEFT / RIGHT or click: choose     "
        self.draw_inline([how, ('nav', 'confirm'), " start     ", ('nav', 'back'), " back"], WIDTH // 2, 704, 26)

    # ------------------------------------------------------------ the main draw
    # ------------------------------------------------------------ the CONTROLS screen
    TAB_NAMES = ["KEYBOARD", "PS5 CONTROLLER", "LAYOUT & SETUP"]

    def draw_ps5_diagram(self, cx, cy):
        """A picture of the DualSense with every button labelled by what it does in this game."""
        scr, P, inp = self.screen, pygame.draw, self.input
        body = (44, 46, 66)
        P.ellipse(scr, body, (cx - 150, cy - 60, 300, 150))
        P.ellipse(scr, body, (cx - 205, cy - 10, 120, 170))
        P.ellipse(scr, body, (cx + 85, cy - 10, 120, 170))
        P.rect(scr, (60, 64, 92), (cx - 150, cy - 60, 300, 70), border_radius=30)
        for sx in (-1, 1):                                              # shoulder + trigger buttons
            P.rect(scr, (70, 74, 104), (cx + sx * 118 - 34, cy - 82, 68, 18), border_radius=8)
            P.rect(scr, (58, 62, 90), (cx + sx * 118 - 28, cy - 100, 56, 16), border_radius=8)
        P.rect(scr, (30, 32, 50), (cx - 52, cy - 28, 104, 62), border_radius=10)   # touchpad
        P.circle(scr, (30, 32, 50), (cx - 62, cy + 62), 28); P.circle(scr, (30, 32, 50), (cx + 62, cy + 62), 28)
        P.circle(scr, (90, 96, 130), (cx - 62, cy + 62), 20); P.circle(scr, (90, 96, 130), (cx + 62, cy + 62), 20)
        font = self.font(18)
        ic = lambda name, x, y, s=26: draw_pad_icon(scr, name, x, y, s, font)
        ic('dpup', cx - 132, cy - 4); ic('dpleft', cx - 156, cy + 20); ic('dpright', cx - 108, cy + 20); ic('dpdown', cx - 132, cy + 44)
        ic('y', cx + 132, cy - 4); ic('b', cx + 156, cy + 20); ic('a', cx + 132, cy + 44); ic('x', cx + 108, cy + 20)
        ic('leftshoulder', cx - 118, cy - 73, 30); ic('rightshoulder', cx + 118, cy - 73, 30)
        ic('lt', cx - 118, cy - 92, 24); ic('rt', cx + 118, cy - 92, 24)
        ic('back', cx - 88, cy - 20, 22); ic('start', cx + 88, cy - 20, 22)
        # legend under the picture, taken from YOUR current bindings
        def who(btn):
            names = [ACTION_LABELS[a] for a, l in inp.pad.items() if btn in l]
            return ", ".join(names) if names else "-"
        order = ['lt', 'leftshoulder', 'back', 'dpup', 'dpleft', 'dpdown', 'dpright',
                 'rt', 'rightshoulder', 'start', 'y', 'b', 'a', 'x', 'touchpad']
        items = [(PAD_LABELS[b], who(b)) for b in order if b in PAD_LABELS and who(b) != "-"]
        items += [("Left stick", "Walk (gentle = slow)"), ("Right stick", "Aim + auto-attack")]
        half = (len(items) + 1) // 2
        for i, (lab, what) in enumerate(items):
            col, row = divmod(i, half)
            x = cx - 205 + col * 215
            self.text(lab, 19, (255, 214, 90), (x, cy + 190 + row * 22), shadow=False)
            self.text(what, 19, (215, 215, 232), (x + 92, cy + 190 + row * 22), shadow=False)

    SETUP_STEPS = [
        ("USB cable (easiest, works everywhere)", "Plug the DualSense into your computer with a USB-C cable. That's it! "
         "The game says \"Controller connected\" at the top of the screen. You can plug it in before or after starting."),
        ("Bluetooth (wireless)", "Turn Bluetooth on in your computer's settings. On the controller, HOLD the PS button and the "
         "Create button (the little button left of the touchpad) together for 3 seconds, until the light bar flashes quickly. "
         "Then choose \"DualSense Wireless Controller\" in your Bluetooth list and press Pair."),
        ("Windows / Mac / Linux", "All three work with no extra software. On Windows you do NOT need to install DS4Windows or Steam. "
         "If you also have Steam open, close it, because Steam can grab the controller and change the buttons."),
        ("Not working?", "Unplug it and plug it in again, or turn it off (hold PS for 10 seconds) and re-pair it. "
         "Make sure only ONE program is using the controller. Still stuck? You can always play with the keyboard."),
    ]

    def draw_setup_tab(self, r):
        self.draw_ps5_diagram(r.x + 305, r.y + 120)
        x, y = r.x + 640, r.y + 30
        self.text("HOW TO CONNECT YOUR PS5 CONTROLLER", 26, (255, 214, 90), (x, y), outline=True)
        y += 40
        for title, body in self.SETUP_STEPS:
            self.text(title, 23, (150, 235, 175), (x, y), outline=True)
            y += 27
            for line in self.wrap(body, 20, r.right - x - 24):
                self.text(line, 20, (205, 205, 225), (x, y), shadow=False)
                y += 22
            y += 12

    def draw_controls(self):
        scr, inp = self.screen, self.input
        self.lit_backdrop([(WIDTH // 2, 330, 700, 0.5)])
        self.dim((0, 0, 14), 110)
        self.text("CONTROLS", 60, (255, 214, 90), (WIDTH // 2, 40), center=True, outline=True)
        self.draw_pad_status(18, 16)
        # --- tabs
        tw = 270
        for i, name in enumerate(self.TAB_NAMES):
            r = pygame.Rect(WIDTH // 2 - tw * 3 // 2 - 10 + i * (tw + 10), 78, tw, 40)
            on = i == self.ctl_tab
            self.panel(r, alpha=240 if on else 190, border=(255, 214, 90) if on else (100, 94, 120), radius=10,
                       glow=(255, 214, 90) if on else None)
            self.text(name, 26, (255, 255, 255) if on else (165, 165, 190), r.center, center=True, outline=on)
            self._hits.append((r, 'tab', i))
        for side, act in ((-1, 'tab_prev'), (1, 'tab_next')):
            self.screen.blit(self.badge_surface('nav', 'L1' if side < 0 else 'R1', 22) if False else
                             self.text_img("<" if side < 0 else ">", 34, (200, 190, 150), True),
                             (WIDTH // 2 + side * (tw * 3 // 2 + 40) - 8, 84))
        panel = pygame.Rect(60, 124, WIDTH - 120, 548)
        self.panel(panel, alpha=232)
        if self.ctl_tab == 2:
            self.draw_setup_tab(panel)
        else:
            self.draw_binding_table(panel)
        # --- footer hint
        if inp.capture:
            cap = inp.capture
            what = "a KEY" if cap['device'] == 'keyboard' else "a BUTTON on your controller"
            ov = pygame.Rect(WIDTH // 2 - 330, 300, 660, 140)
            self.dim((0, 0, 0), 150)
            self.panel(ov, alpha=250, border=(255, 214, 90), glow=(255, 214, 90))
            self.text(f"Press {what} for", 30, (230, 230, 245), (WIDTH // 2, 330), center=True, outline=True)
            self.text(ACTION_LABELS[cap['action']].upper(), 48, (255, 214, 90), (WIDTH // 2, 376), center=True, outline=True)
            self.text(f"Esc = cancel     Backspace = clear this slot     ({cap['t']:.0f}s)", 20, (180, 180, 205), (WIDTH // 2, 420), center=True)
        else:
            if self.ctl_tab == 2:
                self.draw_inline([('nav', 'back'), " back     ", "L1 / R1 or Tab: switch tab"], WIDTH // 2, 698, 24)
            else:
                self.draw_inline(["Up/Down: pick     Left/Right: slot     ", ('nav', 'confirm'), " change     ",
                                  ('nav', 'back'), " back     Y / R: reset"], WIDTH // 2, 698, 22)

    def draw_binding_table(self, panel):
        scr, inp = self.screen, self.input
        rows = self.ctl_rows()
        pad = self.ctl_tab == 1
        device = 'gamepad' if pad else 'keyboard'
        n_bind = sum(1 for k, _ in rows if k == 'bind')
        rh = 28 if len(rows) > 14 else 34
        x0, y0 = panel.x + 24, panel.y + 40
        self.text("ACTION", 20, (170, 170, 200), (x0 + 6, panel.y + 14))
        self.text("MAIN", 20, (170, 170, 200), (x0 + 430, panel.y + 14))
        self.text("ALTERNATIVE", 20, (170, 170, 200), (x0 + 640, panel.y + 14))
        if pad and not inp.connected:
            self.text("No controller connected - see the LAYOUT & SETUP tab", 22, (255, 160, 140), (panel.right - 24, panel.y + 12), right=True)
        for i, (kind, key) in enumerate(rows):
            y = y0 + i * rh
            r = pygame.Rect(x0, y, panel.w - 48, rh - 3)
            sel = i == self.ctl_row
            if sel:
                pygame.draw.rect(scr, (60, 52, 84), r, border_radius=8)
                pygame.draw.rect(scr, (255, 214, 90), r, 2, border_radius=8)
            if kind == 'bind':
                self.text(ACTION_LABELS[key], 24, (255, 255, 255) if sel else (205, 205, 225), (x0 + 12, y + 4), outline=sel)
                for col in (0, 1):
                    cell = pygame.Rect(x0 + 400 + col * 210, y + 2, 190, rh - 7)
                    lst = inp.kb[key] if not pad else inp.pad[key]
                    here = sel and self.ctl_col == col
                    waiting = inp.capture and inp.capture['action'] == key and inp.capture['slot'] == col and inp.capture['device'] == device
                    pygame.draw.rect(scr, (30, 26, 44) if not here else (84, 70, 40), cell, border_radius=6)
                    pygame.draw.rect(scr, (255, 214, 90) if here else (92, 86, 112), cell, 2 if here else 1, border_radius=6)
                    if waiting:
                        self.text("press a button..." if pad else "press a key...", 20, (255, 214, 90), cell.center, center=True)
                    elif col < len(lst):
                        if pad:
                            img = self.pad_icon_surface(lst[col], 22)
                            scr.blit(img, (cell.x + 8, cell.centery - img.get_height() // 2))
                            self.text(PAD_LABELS.get(lst[col], lst[col]), 20, (235, 235, 250), (cell.x + 14 + img.get_width(), cell.centery - 9))
                        else:
                            self.text(self.key_label(lst[col]), 22, (235, 235, 250), cell.center, center=True)
                    else:
                        self.text("-", 22, (110, 108, 130), cell.center, center=True)
                    self._hits.append((cell, 'cell', i, col))
            elif kind == 'slider':
                v = inp.settings[key]
                self.text(self.SETTING_LABELS[key], 24, (255, 255, 255) if sel else (205, 205, 225), (x0 + 12, y + 4))
                bar = pygame.Rect(x0 + 400, y + 9, 300, 12)
                pygame.draw.rect(scr, (30, 26, 44), bar, border_radius=6)
                pygame.draw.rect(scr, (110, 215, 255), (bar.x, bar.y, int(bar.w * (v - 0.05) / 0.45), bar.h), border_radius=6)
                pygame.draw.rect(scr, (235, 230, 215), bar, 1, border_radius=6)
                self.text(f"{int(v * 100)}%   (raise it if your character drifts)", 20, (200, 200, 225), (bar.right + 14, y + 5))
                self._hits.append((r, 'btn', i))
            elif kind == 'toggle':
                on = inp.settings[key]
                self.text(self.SETTING_LABELS[key], 24, (255, 255, 255) if sel else (205, 205, 225), (x0 + 12, y + 4))
                tg = pygame.Rect(x0 + 400, y + 3, 64, rh - 9)
                pygame.draw.rect(scr, (70, 190, 120) if on else (70, 66, 90), tg, border_radius=12)
                pygame.draw.circle(scr, (255, 255, 255), (tg.right - 13 if on else tg.x + 13, tg.centery), 9)
                self.text("ON" if on else "OFF", 22, (190, 255, 210) if on else (160, 160, 185), (tg.right + 14, y + 4))
                self._hits.append((r, 'btn', i))
            elif kind in ('reset', 'back'):
                label = "Reset to defaults" if kind == 'reset' else "Back"
                self.text(label, 26, (255, 190, 150) if kind == 'reset' else (255, 255, 255), r.center, center=True, outline=sel)
                self._hits.append((r, 'btn', i))

    @staticmethod
    def key_label(code):
        from inputs import key_label
        return key_label(code)

    # ------------------------------------------------------------ the MUSIC screen
    def draw_music(self):
        self.lit_backdrop([(WIDTH // 2, 300, 500, 0.5)])
        self.dim((0, 0, 10), 70)
        self.text("BACKGROUND MUSIC", 56, (255, 214, 90), (WIDTH // 2, 68), center=True, outline=True)
        self.text("Pick a tune, or adjust the volume", 22, (190, 190, 220), (WIDTH // 2, 112), center=True)
        items = self.music_items()
        n_tracks = len(MUSIC_TRACKS)
        y0, rh, gap = 148, 54, 8
        for i, (label, _) in enumerate(items):
            r = pygame.Rect(WIDTH // 2 - 240, y0 + i * (rh + gap), 480, rh)
            sel = i == self.menu_sel
            self.panel(r, alpha=235 if sel else 200, border=(255, 214, 90) if sel else (110, 100, 130), radius=12,
                       glow=(255, 214, 90) if sel else None)
            if i < n_tracks:
                playing = MUSIC_TRACKS[i]['key'] == self.audio.track_key
                shown = ("NOW PLAYING: " if playing else "") + label
                self.text(shown, 28, (255, 255, 255) if sel else (170, 170, 195), r.center, center=True, outline=sel)
            elif i in (n_tracks, n_tracks + 1):
                v = self.audio.music_vol if i == n_tracks else self.audio.sfx_vol
                self.text(label, 24, (255, 255, 255) if sel else (205, 205, 225), (r.x + 16, r.y + 7), outline=sel)
                bar = pygame.Rect(r.x + 220, r.y + 20, r.w - 250, 14)
                pygame.draw.rect(self.screen, (30, 26, 44), bar, border_radius=7)
                pygame.draw.rect(self.screen, (110, 215, 255), (bar.x, bar.y, int(bar.w * v), bar.h), border_radius=7)
                pygame.draw.rect(self.screen, (235, 230, 215), bar, 1, border_radius=7)
                self.text(f"{round(v * 100)}%", 22, (230, 230, 245), (bar.right + 14, r.y + 12))
            else:
                self.text(label, 28, (255, 255, 255) if sel else (170, 170, 195), r.center, center=True, outline=sel)
            self._hits.append((r, 'menu', i))
        how = "D-Pad / Left Stick + " if self.input.device == 'gamepad' else "Arrows / mouse + "
        self.draw_inline([how, ('nav', 'confirm'), " pick track     Left/Right: volume     ", ('nav', 'back'), " back"],
                          WIDTH // 2, y0 + len(items) * (rh + gap) + 20, 22)

    # ------------------------------------------------------------ the SHOP screen
    def draw_shop(self):
        p = self.player
        self.lit_backdrop([(WIDTH // 2, 300, 500, 0.5)])
        self.dim((0, 0, 10), 70)
        self.text("SHOP", 56, (255, 214, 90), (WIDTH // 2, 60), center=True, outline=True)
        self.text(f"Gold: {p.gold}", 26, (255, 220, 100), (WIDTH // 2, 104), center=True)
        offers = self.shop_offers()
        items = self.shop_items()
        y0, rh, gap = 140, 56, 8
        for i, (label, _) in enumerate(items):
            r = pygame.Rect(WIDTH // 2 - 280, y0 + i * (rh + gap), 560, rh)
            sel = i == self.menu_sel
            is_offer = i < len(offers)
            afford = (not is_offer) or p.gold >= offers[i][3]
            self.panel(r, alpha=235 if sel else 200, border=(255, 214, 90) if sel else (110, 100, 130), radius=12,
                       glow=(255, 214, 90) if sel else None)
            col = (255, 255, 255) if sel else ((170, 170, 195) if afford else (170, 95, 95))
            if is_offer:
                self.text(label, 26, col, (r.x + 16, r.y + 6), outline=sel)
                self.text(offers[i][2], 18, (190, 190, 215), (r.x + 16, r.y + 32))
            else:
                self.text(label, 28, col, r.center, center=True, outline=sel)
            self._hits.append((r, 'menu', i))
        how = "D-Pad / Left Stick + " if self.input.device == 'gamepad' else "Arrows / mouse + "
        self.draw_inline([how, ('nav', 'confirm'), " to buy     ", ('nav', 'back'), " leave"],
                          WIDTH // 2, y0 + len(items) * (rh + gap) + 20, 22)

    # ------------------------------------------------------------ the main draw
    def draw(self):
        scr = self.screen
        self._hits = []
        st = self.state
        if st == 'title':
            self.draw_title()
        elif st == 'select':
            self.draw_select()
        elif st == 'controls':
            self.draw_controls()
        elif st == 'music':
            self.draw_music()
        elif st == 'shop':
            self.draw_shop()
        else:
            scr.fill((0, 0, 0))
            self.draw_world()
            self.draw_hud()
            if self.fade > 0:
                self.dim((0, 0, 0), int(255 * self.fade))
            mins, secs = divmod(int(self.run_time), 60)
            p = self.player
            c = CLASSES[p.cls]
            if st == 'paused':
                self.dim((0, 0, 20), 175)
                pause_items = self.pause_items()
                panel_h = 246 + (len(pause_items) - 1) * 62   # grows to fit however many rows the menu has
                self.panel((WIDTH // 2 - 230, 150, 460, panel_h), alpha=240)
                self.text("PAUSED", 84, (255, 255, 255), (WIDTH // 2, 205), center=True, outline=True)
                self.draw_menu(pause_items, WIDTH // 2, 270)
            elif st == 'dead':
                self.dim((90, 0, 0), 190)
                self.panel((WIDTH // 2 - 340, 170, 680, 340), alpha=235, border=(220, 70, 70))
                self.text("YOU DIED", 130, (255, 80, 80), (WIDTH // 2, 250), center=True, outline=True)
                self.text(f"{c['title']} fell on floor {self.floor} at level {p.level}", 36, (255, 255, 255), (WIDTH // 2, 340), center=True)
                self.text(f"Monsters beaten: {p.kills}     Gold: {p.gold}     Time: {mins}:{secs:02d}", 30, (235, 205, 205), (WIDTH // 2, 385), center=True)
                self.draw_inline(["Press ", ('nav', 'confirm'), " to try again"], WIDTH // 2, 455, 40)
            elif st == 'victory':
                self.dim((30, 20, 0), 190)
                self.panel((WIDTH // 2 - 380, 150, 760, 380), alpha=235, border=(255, 210, 90))
                self.text("VICTORY!", 150, (255, 222, 90), (WIDTH // 2, 235), center=True, outline=True)
                self.text(f"{c['title']} defeated the Bone King and saved the kingdom!", 36, (255, 255, 255), (WIDTH // 2, 335), center=True)
                self.text(f"Level {p.level}     Monsters beaten: {p.kills}     Gold: {p.gold}     Time: {mins}:{secs:02d}", 30, (255, 238, 175), (WIDTH // 2, 385), center=True)
                self.draw_inline(["Press ", ('nav', 'confirm'), " to play again"], WIDTH // 2, 465, 44)
        self.draw_toasts()

    def step(self, dt, keys=None):
        """One tick of the game: read input, act on it, update the world. (Tests call this too.)"""
        self.input.update(dt, keys)
        self.process_input()
        self.update(dt)

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.input.begin_frame()
            for e in pygame.event.get():
                if self.input.handle_event(e):          # eaten while you are choosing a new key/button
                    continue
                self.handle_event(e)
            self.step(dt)
            self.draw()
            pygame.display.flip()
        self.audio.stop()
        pygame.quit()
