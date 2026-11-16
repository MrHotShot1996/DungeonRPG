"""sprites.py - draws EVERY picture in the game with code (no image files needed!).

How it works (like I'm 10): we first draw a small "pixel art" picture of each character.
Then a 'stylizer' blows it up, adds a dark outline, shading from top to bottom, and a shiny
rim-light on the edges. Floors and walls are drawn big and then shrunk down, which makes the
lines smooth. That's how the game gets its polished look."""
import math
import random

import pygame

from settings import TILE
from classes import CLASSES, CLASS_ORDER
from biomes import BIOMES

SKIN = (240, 200, 160)
BONE = (232, 228, 212)
OUTLINE = (14, 10, 20)


# ------------------------------------------------------------------ small helpers
def new(w=TILE, h=TILE):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def clamp(v, lo=0, hi=255):
    return max(lo, min(hi, int(v)))


def shade(c, f):
    return (clamp(c[0] * f), clamp(c[1] * f), clamp(c[2] * f))


def add(c, n):
    return (clamp(c[0] + n), clamp(c[1] + n), clamp(c[2] + n))


def jit(c, rng, a):
    n = rng.randint(-a, a)
    return add(c, n)


def gray_tint(surf, color):
    """Make a picture black-and-white, then colour it (used for undead allies)."""
    t = surf.copy()
    for y in range(t.get_height()):
        for x in range(t.get_width()):
            r, g, b, a = t.get_at((x, y))
            if a:
                v = int(r * 0.35 + g * 0.5 + b * 0.15)
                t.set_at((x, y), (clamp(v * color[0] / 200), clamp(v * color[1] / 200), clamp(v * color[2] / 200), a))
    return t


def tint(surf, color):
    t = surf.copy()
    t.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return t


def stylize(raw, scale=1.25, strip=140):
    """Pixel-art in -> polished sprite out (outline + shading + rim light + smooth edges).
    Returns (surface, foot_pad) where foot_pad = empty pixels under the feet."""
    w, h = raw.get_size()
    src = raw.copy()
    if strip:                                   # remove faint baked-in shadows (we draw soft ones live)
        for y in range(h):
            for x in range(w):
                a = src.get_at((x, y)).a
                if 0 < a < strip:
                    src.set_at((x, y), (0, 0, 0, 0))
    K = 4
    big = pygame.transform.scale(src, (w * K, h * K))
    m = pygame.mask.from_surface(big, 100)
    # top-to-bottom shading
    g = pygame.Surface((2, 2))
    g.fill((255, 255, 255))
    g.set_at((0, 1), (178, 178, 198)); g.set_at((1, 1), (178, 178, 198))
    g = pygame.transform.smoothscale(g, (w * K, h * K))
    big.blit(g, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    # rim light on the top-left edges
    shifted = pygame.mask.Mask(big.get_size())
    shifted.draw(m, (5, 5))
    edge = m.copy()
    edge.erase(shifted, (0, 0))
    big.blit(edge.to_surface(setcolor=(80, 80, 100, 255), unsetcolor=(0, 0, 0, 255)), (0, 0),
             special_flags=pygame.BLEND_RGB_ADD)
    # dark outline
    pad = 10
    ol = m.to_surface(setcolor=(*OUTLINE, 255), unsetcolor=(0, 0, 0, 0))
    canvas = pygame.Surface((w * K + 2 * pad, h * K + 2 * pad), pygame.SRCALPHA)
    for dx, dy in ((-5, 0), (5, 0), (0, -5), (0, 5), (-4, -4), (4, -4), (-4, 4), (4, 4), (-5, -2), (5, 2), (0, 7)):
        canvas.blit(ol, (pad + dx, pad + dy))
    canvas.blit(big, (pad, pad))
    fw, fh = max(2, int(round(canvas.get_width() * scale / K))), max(2, int(round(canvas.get_height() * scale / K)))
    out = pygame.transform.smoothscale(canvas, (fw, fh))
    rects = pygame.mask.from_surface(out, 60).get_bounding_rects()
    bottom = rects[0].unionall(rects[1:]).bottom if rects else fh
    return out, fh - bottom


class Sprites:
    def __init__(self):
        rng = random.Random(3)
        self._tilesets = {}
        self._glows = {}
        self._shadows = {}
        self._corpses = {}
        self._bigs = {}
        self._shadow_copies = {}
        self.foot = {}
        # ---- heroes
        self.player = {}
        for cls in CLASS_ORDER:
            for d in ('down', 'up', 'right'):
                for f in (0, 1):
                    self.player[(cls, d, f)], self.foot[('p', cls)] = stylize(self._player(d, f, cls), 1.25)
            for f in (0, 1):
                self.player[(cls, 'left', f)] = pygame.transform.flip(self.player[(cls, 'right', f)], True, False)
        # ---- monsters
        self.raw = {
            'slime': [self._slime(f) for f in (0, 1)], 'bat': [self._bat(f) for f in (0, 1)],
            'skeleton': [self._skeleton(f) for f in (0, 1)], 'goblin': [self._goblin(f) for f in (0, 1)],
            'imp': [self._imp(f) for f in (0, 1)], 'spider': [self._spider(f) for f in (0, 1)],
            'brute': [self._brute(f) for f in (0, 1)], 'wraith': [self._wraith(f) for f in (0, 1)],
            'cultist': [self._cultist(f) for f in (0, 1)], 'boss': [self._boss(f) for f in (0, 1)],
            'warlord': [self._warlord(f) for f in (0, 1)],
            'lich': [self._lich(f) for f in (0, 1)], 'demon': [self._demon(f) for f in (0, 1)],
        }
        self.enemy = {}
        for k, frames in self.raw.items():
            outs = [stylize(fr, 1.25) for fr in frames]
            self.enemy[k] = [o[0] for o in outs]
            self.foot[('e', k)] = outs[0][1]
        # ---- allies
        sk = [self._skeleton(f, 'sword') for f in (0, 1)]
        ar = [self._skeleton(f, 'bow') for f in (0, 1)]
        bb = self.raw['brute']
        self.minion_raw = {
            'skeleton': [tint(x, (150, 255, 200)) for x in sk],
            'archer': [tint(x, (170, 200, 255)) for x in ar],
            'bonebrute': [gray_tint(x, (235, 235, 215)) for x in bb],
        }
        self.minion = {}
        for k, frames in self.minion_raw.items():
            outs = [stylize(fr, 1.25) for fr in frames]
            self.minion[k] = [o[0] for o in outs]
            self.minion[k + '_flip'] = [pygame.transform.flip(o[0], True, False) for o in outs]
            self.foot[('m', k)] = outs[0][1]
        # ---- items & misc
        self.coin = [stylize(self._coin(f), 1.1)[0] for f in range(4)]
        self.chest = [stylize(self._chest(o), 1.2)[0] for o in (False, True)]
        self.stairs = self._stairs()
        self._slash_base = self._make_slash()
        self._slash = {}

    # ------------------------------------------------------------------ cached soft sprites
    def glow(self, radius, color, intensity=1.0):
        """A soft round glow (use with additive blending)."""
        key = (int(radius // 6) * 6, color, int(intensity * 20))
        if key not in self._glows:
            r = max(4, key[0])
            s = pygame.Surface((r * 2, r * 2))
            s.fill((0, 0, 0))
            for i in range(r, 0, -2):
                f = (1 - i / r) ** 2 * intensity
                pygame.draw.circle(s, (clamp(color[0] * f), clamp(color[1] * f), clamp(color[2] * f)), (r, r), i)
            self._glows[key] = s
        return self._glows[key]

    def shadow(self, w, h):
        key = (int(w // 4) * 4, int(h // 2) * 2)
        if key not in self._shadows:
            s = new(key[0] + 4, key[1] + 4)
            for i in range(10, 0, -1):
                f = i / 10
                pygame.draw.ellipse(s, (0, 0, 0, int(95 * (1 - f) + 12)),
                                    (2 + (1 - f) * key[0] / 2, 2 + (1 - f) * key[1] / 2, key[0] * f, key[1] * f))
            self._shadows[key] = s
        return self._shadows[key]

    def big_enemy(self, kind, scale=1.6):
        """Bigger gold-ish copies for ELITE monsters."""
        if kind not in self._bigs:
            outs = [stylize(fr, scale) for fr in self.raw[kind]]
            frames = [o[0] for o in outs]
            for fr in frames:                                  # golden glow for elites
                fr.fill((48, 34, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
            self._bigs[kind] = (frames, outs[0][1])
        return self._bigs[kind]

    def corpse(self, kind):
        if kind not in self._corpses:
            img = self.enemy[kind][0]
            c = pygame.transform.rotate(img, 90)
            c = pygame.transform.smoothscale(c, (c.get_width(), max(6, int(c.get_height() * 0.7))))
            c.fill((115, 105, 125, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self._corpses[kind] = c
        return self._corpses[kind]

    def shadow_copy(self, cls, d):
        """A dark, see-through copy of a hero - the Shadow Ninja's Living Shadow."""
        key = (cls, d)
        if key not in self._shadow_copies:
            img = self.player[(cls, d, 0)].copy()
            img.fill((70, 50, 120, 255), special_flags=pygame.BLEND_RGBA_MULT)     # darken it...
            img.fill((26, 12, 58, 0), special_flags=pygame.BLEND_RGB_ADD)          # ...and tint it violet
            self._shadow_copies[key] = img
        return self._shadow_copies[key]

    def slash(self, angle):
        key = (int(round(angle / 45.0)) * 45) % 360
        if key not in self._slash:
            self._slash[key] = pygame.transform.rotate(self._slash_base, key)
        return self._slash[key]

    def _make_slash(self):
        s = new(110, 110)
        for width, col, rect in ((16, (120, 170, 255, 70), (4, 4, 102, 102)),
                                 (10, (190, 220, 255, 150), (8, 8, 94, 94)),
                                 (6, (255, 255, 255, 235), (12, 12, 86, 86)),
                                 (3, (255, 255, 255, 255), (16, 16, 78, 78))):
            pygame.draw.arc(s, col, pygame.Rect(rect), -1.05, 1.05, width)
        return pygame.transform.smoothscale(s, (82, 82))

    # ------------------------------------------------------------------ HEROES
    def _player(self, d, f, cls):
        pal = CLASSES[cls]['palette']
        s = new()
        l_off, r_off = (0, -2) if f == 0 else (-2, 0)
        if pal.get('robe'):
            sway = 1 if f else -1
            pygame.draw.polygon(s, pal['armor'], [(10, 35), (30 + sway, 35), (28, 22), (12, 22)])
            pygame.draw.line(s, pal['trim'], (10, 35), (30 + sway, 35), 2)
            pygame.draw.line(s, shade(pal['armor'], 0.7), (20, 24), (20 + sway, 35), 1)
        else:
            pygame.draw.rect(s, pal['legs'], (13, 27 + l_off, 6, 8))
            pygame.draw.rect(s, pal['legs'], (21, 27 + r_off, 6, 8))
            pygame.draw.rect(s, (40, 30, 30), (12, 33 + l_off, 8, 3))
            pygame.draw.rect(s, (40, 30, 30), (20, 33 + r_off, 8, 3))
        pygame.draw.rect(s, pal['armor'], (11, 15, 18, 14), border_radius=3)
        pygame.draw.rect(s, (120, 80, 40), (11, 25, 18, 3))
        pygame.draw.rect(s, (230, 200, 60), (18, 25, 4, 3))
        pygame.draw.rect(s, pal['trim'], (7, 16, 5, 11), border_radius=2)
        pygame.draw.rect(s, pal['trim'], (28, 16, 5, 11), border_radius=2)
        skin = pal.get('skin', SKIN)
        pygame.draw.circle(s, skin, (9, 28), 3)
        pygame.draw.circle(s, skin, (31, 28), 3)
        if pal.get('collar'):
            pygame.draw.ellipse(s, pal['collar'], (10, 13, 20, 7))
        dark_face = pal.get('face') == 'dark'
        face = (12, 8, 18) if dark_face else skin
        eye = pal.get('orb', (130, 255, 160)) if dark_face else (30, 30, 40)
        head = pal['head']
        if head == 'hood':
            pygame.draw.circle(s, pal['helm'], (20, 10), 10)
            pygame.draw.polygon(s, pal['helm'], [(11, 9), (29, 9), (20, 0)])
        else:
            pygame.draw.circle(s, pal['helm'], (20, 10), 9)
        if d == 'down':
            pygame.draw.rect(s, face, (14, 9 if head == 'hood' else 10, 12, 8), border_radius=2)
            s.fill(eye, (16, 12, 2, 3)); s.fill(eye, (22, 12, 2, 3))
        elif d == 'right':
            pygame.draw.rect(s, face, (19, 9 if head == 'hood' else 10, 8, 8), border_radius=2)
            s.fill(eye, (23, 12, 2, 3))
        if head == 'hair':                                 # messy hair: a few spikes on top
            for hx, hy in ((12, 3), (17, 0), (23, 0), (28, 4)):
                pygame.draw.polygon(s, pal['helm'], [(hx - 4, 7), (hx, hy), (hx + 4, 7)])
            if d == 'down':
                pygame.draw.rect(s, pal['helm'], (11, 6, 18, 4), border_radius=2)
        if head == 'hat':
            pygame.draw.polygon(s, pal['helm'], [(10, 9), (30, 9), (24, -1)])
            pygame.draw.rect(s, pal['trim'], (8, 8, 24, 3), border_radius=1)
        if pal['plume']:
            px = 16 if d == 'right' else 18
            pygame.draw.rect(s, pal['plume'], (px, 0, 4, 4))
        if pal.get('feather'):
            pygame.draw.polygon(s, pal['feather'], [(26, 7), (32, 1), (30, 9)])
        self._weapon(s, pal, d)
        return s

    def _weapon(self, s, pal, d):
        w = pal['weapon']
        orb = pal.get('orb', (150, 230, 255))
        vertical = d in ('down', 'up')
        if w == 'sword':
            if vertical:
                pygame.draw.rect(s, (205, 208, 220), (32, 14, 3, 14)); pygame.draw.rect(s, (210, 165, 45), (30, 24, 7, 2))
            else:
                pygame.draw.rect(s, (205, 208, 220), (28, 19, 11, 3)); pygame.draw.rect(s, (210, 165, 45), (27, 17, 2, 7))
        elif w in ('staff', 'skullstaff'):
            if vertical:
                pygame.draw.rect(s, (120, 80, 40), (33, 6, 3, 28))
                cx, cy = 34, 6
            else:
                pygame.draw.rect(s, (120, 80, 40), (26, 20, 13, 3))
                cx, cy = 38, 21
            if w == 'staff':
                pygame.draw.circle(s, orb, (cx, cy), 4)
            else:
                pygame.draw.circle(s, (*orb, 90), (cx, cy), 6)
                pygame.draw.circle(s, BONE, (cx, cy), 4)
                s.fill((20, 20, 30), (cx - 2, cy - 1, 1, 2)); s.fill((20, 20, 30), (cx + 1, cy - 1, 1, 2))
        elif w == 'dagger':
            if vertical:
                pygame.draw.rect(s, (210, 215, 225), (32, 19, 2, 8)); pygame.draw.rect(s, (120, 80, 40), (30, 26, 6, 2))
            else:
                pygame.draw.rect(s, (210, 215, 225), (30, 20, 7, 2)); pygame.draw.rect(s, (120, 80, 40), (28, 18, 2, 6))
        elif w == 'orb':                                  # a little ball of blood floating by the hand
            ox, oy = (33, 22) if vertical else (35, 20)
            pygame.draw.circle(s, shade(orb, 0.55), (ox, oy), 5)
            pygame.draw.circle(s, orb, (ox, oy), 4)
            s.fill((255, 200, 210), (ox - 2, oy - 2, 2, 2))
        elif w == 'gauntlet':                             # a golden gauntlet with a glowing gem
            gx, gy = (31, 25) if vertical else (31, 21)
            pygame.draw.rect(s, (150, 112, 40), (gx - 4, gy - 4, 9, 9), border_radius=2)
            pygame.draw.rect(s, (222, 182, 76), (gx - 3, gy - 3, 7, 7), border_radius=2)
            pygame.draw.circle(s, (*orb, 110), (gx + 1, gy), 5)
            pygame.draw.circle(s, orb, (gx + 1, gy), 2)
            s.fill((255, 255, 240), (gx, gy - 1, 1, 1))
        elif w == 'bow':
            pygame.draw.arc(s, (140, 92, 48), pygame.Rect(26, 8, 14, 26), -1.25, 1.25, 3)
            pygame.draw.line(s, (235, 235, 225), (33, 9), (33, 33), 1)
        elif w == 'fists':
            wrap = pal.get('wraps', (230, 220, 200))
            if vertical:
                pygame.draw.circle(s, wrap, (32, 26), 4)
                pygame.draw.circle(s, shade(wrap, 0.7), (32, 26), 4, 1)
            else:
                pygame.draw.circle(s, wrap, (30, 21), 4)
                pygame.draw.circle(s, shade(wrap, 0.7), (30, 21), 4, 1)
        else:  # mace
            if vertical:
                pygame.draw.rect(s, (120, 80, 40), (33, 14, 3, 18)); pygame.draw.circle(s, (240, 210, 90), (34, 12), 5)
            else:
                pygame.draw.rect(s, (120, 80, 40), (27, 20, 10, 3)); pygame.draw.circle(s, (240, 210, 90), (38, 21), 5)

    # ------------------------------------------------------------------ MONSTERS
    def _slime(self, f):
        s = new()
        r = pygame.Rect(6, 16, 28, 19) if f == 0 else pygame.Rect(4, 20, 32, 15)
        pygame.draw.ellipse(s, (70, 200, 95), r)
        pygame.draw.ellipse(s, (35, 130, 60), r, 2)
        pygame.draw.ellipse(s, (120, 235, 140), (r.x + 4, r.y + 7, r.w - 8, r.h - 10))
        pygame.draw.ellipse(s, (200, 255, 210), (r.x + 6, r.y + 3, 8, 5))
        for ex in (r.centerx - 5, r.centerx + 5):
            pygame.draw.circle(s, (255, 255, 255), (ex, r.centery + 2), 3)
            pygame.draw.circle(s, (0, 0, 0), (ex, r.centery + 3), 1)
        return s

    def _bat(self, f):
        s = new()
        wing, body = (80, 40, 110), (115, 65, 145)
        lw = [(16, 18), (1, 6), (6, 16), (10, 22)] if f == 0 else [(16, 18), (1, 25), (8, 28), (12, 22)]
        rw = [(TILE - x, y) for x, y in lw]
        pygame.draw.polygon(s, wing, lw); pygame.draw.polygon(s, wing, rw)
        pygame.draw.ellipse(s, body, (14, 13, 12, 16))
        pygame.draw.polygon(s, body, [(15, 15), (16, 8), (19, 14)])
        pygame.draw.polygon(s, body, [(25, 15), (24, 8), (21, 14)])
        s.fill((255, 60, 60), (17, 19, 2, 2)); s.fill((255, 60, 60), (22, 19, 2, 2))
        s.fill((255, 255, 255), (18, 25, 1, 2)); s.fill((255, 255, 255), (22, 25, 1, 2))
        return s

    def _skeleton(self, f, mode='plain'):
        s = new()
        lo = 2 if f else 0
        pygame.draw.line(s, BONE, (16, 26), (15, 34 - lo), 3)
        pygame.draw.line(s, BONE, (24, 26), (25, 34 - (2 - lo)), 3)
        pygame.draw.line(s, BONE, (20, 17), (20, 27), 3)
        for y in (18, 21, 24):
            pygame.draw.line(s, BONE, (13, y), (27, y), 2)
        pygame.draw.line(s, BONE, (13, 18), (8, 27), 2)
        pygame.draw.line(s, BONE, (27, 18), (32, 27), 2)
        if mode == 'sword':
            pygame.draw.rect(s, (200, 205, 220), (31, 12, 3, 16)); pygame.draw.rect(s, (200, 160, 50), (29, 26, 7, 2))
        elif mode == 'bow':
            pygame.draw.arc(s, (150, 100, 55), pygame.Rect(28, 8, 12, 24), -1.25, 1.25, 3)
            pygame.draw.line(s, (235, 235, 225), (34, 9), (34, 31), 1)
        pygame.draw.circle(s, BONE, (20, 10), 8)
        pygame.draw.rect(s, BONE, (15, 14, 10, 5))
        pygame.draw.circle(s, (20, 10, 20), (17, 10), 2); pygame.draw.circle(s, (20, 10, 20), (23, 10), 2)
        s.fill((255, 60, 60), (17, 10, 1, 1)); s.fill((255, 60, 60), (23, 10, 1, 1))
        for x in (17, 20, 23):
            pygame.draw.line(s, (60, 50, 60), (x, 15), (x, 18))
        return s

    def _goblin(self, f):
        s = new()
        lo = 2 if f else 0
        pygame.draw.rect(s, (90, 60, 40), (14, 27, 5, 8 - lo))
        pygame.draw.rect(s, (90, 60, 40), (22, 27, 5, 8 - (2 - lo)))
        pygame.draw.ellipse(s, (100, 165, 55), (11, 16, 18, 14))
        pygame.draw.rect(s, (110, 75, 40), (13, 25, 14, 5))
        pygame.draw.line(s, (100, 165, 55), (11, 18), (6, 27), 4)
        pygame.draw.line(s, (100, 165, 55), (29, 18), (34, 25), 4)
        pygame.draw.rect(s, (215, 215, 225), (33, 17, 2, 9))
        pygame.draw.circle(s, (100, 165, 55), (20, 11), 8)
        pygame.draw.polygon(s, (100, 165, 55), [(12, 10), (2, 5), (12, 14)])
        pygame.draw.polygon(s, (100, 165, 55), [(28, 10), (38, 5), (28, 14)])
        s.fill((255, 50, 50), (16, 9, 3, 3)); s.fill((255, 50, 50), (22, 9, 3, 3))
        pygame.draw.line(s, (40, 30, 20), (16, 15), (24, 15), 1)
        s.fill((255, 255, 255), (17, 15, 2, 2)); s.fill((255, 255, 255), (22, 15, 2, 2))
        return s

    def _imp(self, f):
        s = new()
        pygame.draw.rect(s, (30, 25, 30), (12, 32, 6, 3)); pygame.draw.rect(s, (30, 25, 30), (22, 32, 6, 3))
        pygame.draw.circle(s, (55, 55, 68), (20, 23), 11)
        pygame.draw.circle(s, (95, 95, 112), (16, 19), 4)
        pygame.draw.line(s, (130, 90, 50), (20, 13), (24, 7), 2)
        pygame.draw.circle(s, (255, 200, 60) if f == 0 else (255, 110, 30), (24, 6), 3 if f == 0 else 2)
        s.fill((255, 255, 255), (14, 21, 5, 4)); s.fill((255, 255, 255), (22, 21, 5, 4))
        s.fill((230, 30, 30), (16, 22, 2, 3)); s.fill((230, 30, 30), (23, 22, 2, 3))
        pygame.draw.line(s, (255, 255, 255), (13, 19), (19, 21), 2); pygame.draw.line(s, (255, 255, 255), (27, 19), (21, 21), 2)
        return s

    def _spider(self, f):
        s = new()
        for i in range(4):
            ya = 17 + i * 3
            dy = -2 if (i + f) % 2 else 2
            pygame.draw.lines(s, (35, 25, 45), False, [(15, ya), (7, ya - 6), (3, ya + 6 + dy)], 2)
            pygame.draw.lines(s, (35, 25, 45), False, [(25, ya), (33, ya - 6), (37, ya + 6 + dy)], 2)
        pygame.draw.ellipse(s, (55, 38, 68), (12, 19, 16, 13))
        pygame.draw.circle(s, (75, 52, 90), (20, 17), 6)
        pygame.draw.circle(s, (220, 40, 50), (20, 27), 2)
        for ex, ey in ((17, 15), (23, 15), (18, 18), (22, 18)):
            s.fill((255, 60, 60), (ex, ey, 2, 2))
        return s

    def _brute(self, f):
        base = new(48, 48)
        pygame.draw.rect(base, (80, 60, 45), (14, 32, 8, 12)); pygame.draw.rect(base, (80, 60, 45), (26, 32, 8, 12))
        pygame.draw.ellipse(base, (110, 125, 80), (7, 14, 34, 24))
        pygame.draw.rect(base, (110, 75, 40), (9, 29, 30, 5))
        pygame.draw.rect(base, (105, 120, 75), (1, 17, 9, 16), border_radius=3)
        pygame.draw.rect(base, (105, 120, 75), (38, 17, 9, 16), border_radius=3)
        pygame.draw.rect(base, (95, 65, 35), (42, 5, 5, 28)); pygame.draw.circle(base, (95, 65, 35), (44, 7), 6)
        for sx_, sy_ in ((40, 4), (47, 3), (44, 0)):
            pygame.draw.circle(base, (190, 190, 200), (sx_, sy_), 2)
        pygame.draw.circle(base, (125, 140, 88), (24, 11), 9)
        pygame.draw.line(base, (50, 40, 30), (17, 7), (23, 9), 3); pygame.draw.line(base, (50, 40, 30), (31, 7), (25, 9), 3)
        base.fill((255, 220, 60), (19, 10, 3, 3)); base.fill((255, 220, 60), (26, 10, 3, 3))
        pygame.draw.polygon(base, (240, 240, 225), [(18, 15), (21, 15), (19, 21)])
        pygame.draw.polygon(base, (240, 240, 225), [(27, 15), (30, 15), (29, 21)])
        s = new(48, 48)
        s.blit(base, (0, f))
        return s

    def _wraith(self, f):
        s = new()
        w = 3 if f else -3
        pts = [(12, 12), (28, 12), (32, 24), (30, 36), (26, 32 + w), (22, 38), (18, 32 - w), (14, 36), (10, 24)]
        pygame.draw.polygon(s, (190, 210, 255, 200), pts)
        pygame.draw.circle(s, (205, 222, 255, 215), (20, 12), 9)
        pygame.draw.ellipse(s, (15, 15, 40, 255), (14, 9, 5, 7)); pygame.draw.ellipse(s, (15, 15, 40, 255), (22, 9, 5, 7))
        pygame.draw.ellipse(s, (15, 15, 40, 255), (17, 20, 7, 6))
        pygame.draw.line(s, (190, 210, 255, 200), (11, 20), (5, 28 + w), 3)
        pygame.draw.line(s, (190, 210, 255, 200), (29, 20), (35, 28 - w), 3)
        return s

    def _cultist(self, f):
        s = new()
        pygame.draw.polygon(s, (95, 30, 115), [(9, 36), (31, 36), (27, 15 + f), (13, 15 + f)])
        pygame.draw.polygon(s, (60, 15, 80), [(9, 36), (31, 36), (27, 15 + f), (13, 15 + f)], 2)
        pygame.draw.circle(s, (72, 20, 92), (20, 11 + f), 8)
        pygame.draw.ellipse(s, (8, 4, 12), (15, 8 + f, 10, 8))
        s.fill((255, 90, 255), (16, 11 + f, 3, 2)); s.fill((255, 90, 255), (22, 11 + f, 3, 2))
        pygame.draw.line(s, (110, 75, 40), (33, 6), (33, 36), 3)
        pygame.draw.circle(s, (255, 100, 255), (33, 6), 4)
        pygame.draw.circle(s, (255, 220, 255), (33, 6), 2)
        return s

    def _boss(self, f):
        base = new(64, 64)
        pygame.draw.polygon(base, (90, 30, 120), [(10, 60), (54, 60), (48, 26), (16, 26)])
        pygame.draw.polygon(base, (60, 15, 90), [(10, 60), (54, 60), (48, 26), (16, 26)], 3)
        pygame.draw.polygon(base, (130, 60, 170), [(14, 58), (22, 58), (24, 30), (18, 30)])
        pygame.draw.rect(base, BONE, (30, 34, 4, 22))
        for y in (36, 41, 46):
            pygame.draw.line(base, BONE, (22, y), (42, y), 3)
        pygame.draw.circle(base, BONE, (32, 22), 15)
        pygame.draw.rect(base, BONE, (23, 30, 18, 8))
        for x in (26, 32, 38):
            pygame.draw.line(base, (70, 60, 70), (x, 31), (x, 37), 2)
        for ex in (26, 38):
            pygame.draw.circle(base, (15, 5, 15), (ex, 21), 5)
            pygame.draw.circle(base, (255, 40, 40), (ex, 21), 2)
        pygame.draw.polygon(base, (240, 190, 40), [(17, 12), (18, -1), (25, 7), (32, -2), (39, 7), (46, -1), (47, 12)])
        pygame.draw.circle(base, (220, 40, 60), (32, 7), 2)
        pygame.draw.line(base, BONE, (16, 32), (8, 46), 4)
        pygame.draw.line(base, BONE, (48, 32), (56, 46), 4)
        s = new(64, 64)
        s.blit(base, (0, f * 2))
        return s

    def _warlord(self, f):
        b = new(64, 64)
        skin, dk = (160, 72, 62), (112, 48, 42)
        pygame.draw.rect(b, (72, 46, 36), (18, 46, 11, 16)); pygame.draw.rect(b, (72, 46, 36), (35, 46, 11, 16))
        pygame.draw.rect(b, (50, 34, 28), (16, 58, 15, 5)); pygame.draw.rect(b, (50, 34, 28), (33, 58, 15, 5))
        pygame.draw.ellipse(b, skin, (10, 22, 44, 32))
        pygame.draw.ellipse(b, dk, (14, 40, 36, 12))
        pygame.draw.rect(b, (80, 52, 38), (12, 43, 40, 7))
        pygame.draw.rect(b, (225, 195, 75), (28, 43, 8, 7))
        pygame.draw.rect(b, skin, (1, 28, 11, 22), border_radius=4); pygame.draw.rect(b, skin, (52, 28, 11, 22), border_radius=4)
        for cx in (11, 53):
            pygame.draw.circle(b, (95, 95, 108), (cx, 27), 9)
            pygame.draw.polygon(b, (200, 200, 215), [(cx - 4, 21), (cx, 9), (cx + 4, 21)])
        pygame.draw.rect(b, (100, 66, 38), (57, 4, 4, 52))                        # axe handle
        pygame.draw.polygon(b, (190, 195, 210), [(59, 6), (45, 0), (45, 24), (59, 18)])
        pygame.draw.polygon(b, (235, 238, 248), [(46, 2), (45, 0), (45, 24), (47, 22)])
        pygame.draw.circle(b, skin, (32, 21), 12)
        pygame.draw.polygon(b, (105, 108, 120), [(19, 20), (45, 20), (41, 7), (23, 7)])
        pygame.draw.polygon(b, BONE, [(22, 12), (8, 8), (4, 18), (14, 12)])
        pygame.draw.polygon(b, BONE, [(42, 12), (56, 8), (60, 18), (50, 12)])
        b.fill((255, 225, 60), (26, 22, 4, 3)); b.fill((255, 225, 60), (35, 22, 4, 3))
        pygame.draw.line(b, (40, 25, 20), (24, 19), (30, 22), 3); pygame.draw.line(b, (40, 25, 20), (41, 19), (35, 22), 3)
        pygame.draw.polygon(b, (245, 245, 230), [(25, 28), (28, 28), (26, 35)])
        pygame.draw.polygon(b, (245, 245, 230), [(36, 28), (39, 28), (38, 35)])
        s = new(64, 64)
        s.blit(b, (0, f))
        return s

    def _lich(self, f):
        b = new(64, 64)
        robe, dk, hi = (46, 70, 120), (26, 40, 80), (96, 140, 200)
        ice = (150, 230, 255)
        pygame.draw.polygon(b, robe, [(10, 62), (54, 62), (47, 24), (17, 24)])
        pygame.draw.polygon(b, dk, [(10, 62), (54, 62), (47, 24), (17, 24)], 3)
        pygame.draw.polygon(b, hi, [(15, 60), (23, 60), (25, 30), (20, 30)])
        for x in range(10, 54, 8):
            pygame.draw.polygon(b, dk, [(x, 62), (x + 4, 56), (x + 8, 62)])
        pygame.draw.rect(b, (24, 26, 48), (19, 42, 26, 4))
        pygame.draw.circle(b, ice, (32, 44), 3)
        pygame.draw.circle(b, dk, (32, 22), 15)
        pygame.draw.polygon(b, dk, [(17, 22), (32, 5), (47, 22)])
        pygame.draw.circle(b, (10, 8, 20), (32, 24), 10)
        pygame.draw.ellipse(b, BONE, (25, 16, 14, 16))
        for ex in (28, 36):
            pygame.draw.circle(b, (10, 8, 20), (ex, 22), 3)
            pygame.draw.circle(b, ice, (ex, 22), 2)
        for x in (28, 32, 36):
            pygame.draw.line(b, (70, 60, 80), (x, 28), (x, 31), 1)
        for x, h in ((21, 7), (26, 12), (32, 16), (38, 12), (43, 7)):          # crown of ice
            pygame.draw.polygon(b, ice, [(x - 2, 12), (x, 12 - h + 4), (x + 2, 12)])
        pygame.draw.polygon(b, (235, 250, 255), [(31, 12), (32, 0), (33, 12)])
        pygame.draw.circle(b, BONE, (14, 38), 4); pygame.draw.circle(b, BONE, (50, 36), 4)
        pygame.draw.line(b, dk, (14, 36), (22, 30), 5); pygame.draw.line(b, dk, (50, 34), (42, 30), 5)
        pygame.draw.rect(b, (110, 90, 70), (55, 8, 3, 54))                       # ice staff
        pygame.draw.polygon(b, ice, [(56, 0), (50, 9), (56, 19), (62, 9)])
        pygame.draw.polygon(b, (235, 250, 255), [(56, 2), (53, 9), (56, 14)])
        s = new(64, 64)
        s.blit(b, (0, f * 2))
        return s

    def _demon(self, f):
        b = new(64, 64)
        skin, dk, hi = (176, 34, 42), (112, 18, 30), (232, 78, 62)
        for sx in (-1, 1):                                                      # leathery wings
            pts = [(32, 30), (32 + sx * 30, 2 + f * 3), (32 + sx * 33, 22), (32 + sx * 24, 24),
                   (32 + sx * 27, 40), (32 + sx * 14, 34)]
            pygame.draw.polygon(b, (72, 12, 32), pts)
            pygame.draw.polygon(b, (40, 6, 20), pts, 2)
        pygame.draw.rect(b, dk, (19, 46, 11, 16)); pygame.draw.rect(b, dk, (34, 46, 11, 16))
        pygame.draw.rect(b, (36, 18, 20), (17, 58, 15, 5)); pygame.draw.rect(b, (36, 18, 20), (33, 58, 15, 5))
        pygame.draw.ellipse(b, skin, (13, 24, 38, 34))
        pygame.draw.ellipse(b, hi, (22, 32, 20, 18))
        pygame.draw.circle(b, (255, 190, 60), (32, 41), 5)                       # glowing rune on chest
        pygame.draw.circle(b, (255, 245, 170), (32, 41), 2)
        pygame.draw.rect(b, skin, (5, 30, 10, 22), border_radius=4); pygame.draw.rect(b, skin, (49, 30, 10, 22), border_radius=4)
        for cx in (7, 57):
            for dx in (-3, 0, 3):
                pygame.draw.polygon(b, (240, 230, 210), [(cx + dx - 2, 50), (cx + dx, 58), (cx + dx + 2, 50)])
        pygame.draw.circle(b, skin, (32, 19), 13)
        for hx in (1, -1):                                                       # horns
            ox = 32 + hx * 1
            pts = [(32 + hx * 9, 12), (32 + hx * 22, 6), (32 + hx * 24, 0), (32 + hx * 16, 12), (32 + hx * 11, 18)]
            pygame.draw.polygon(b, (236, 224, 196), pts)
            pygame.draw.polygon(b, (150, 130, 100), pts, 1)
        for x, h in ((24, 8), (28, 12), (32, 14), (36, 12), (40, 8)):            # flame mane
            pygame.draw.polygon(b, (255, 140, 40), [(x - 3, 9), (x, 9 - h), (x + 3, 9)])
        pygame.draw.polygon(b, (255, 220, 90), [(30, 9), (32, 1), (34, 9)])
        for ex in (26, 38):
            b.fill((255, 220, 60), (ex - 2, 17, 5, 4))
        pygame.draw.line(b, (30, 6, 12), (23, 14), (29, 18), 3); pygame.draw.line(b, (30, 6, 12), (41, 14), (35, 18), 3)
        pygame.draw.rect(b, (40, 8, 14), (26, 26, 12, 5))
        for x in (27, 33):
            pygame.draw.polygon(b, (245, 245, 230), [(x, 26), (x + 3, 26), (x + 1, 31)])
        s = new(64, 64)
        s.blit(b, (0, f))
        return s

    # ------------------------------------------------------------------ ITEMS
    def _coin(self, f):
        s = new()
        w = (12, 8, 3, 8)[f]
        pygame.draw.ellipse(s, (250, 205, 50), (20 - w // 2, 14, w, 14))
        pygame.draw.ellipse(s, (180, 130, 20), (20 - w // 2, 14, w, 14), 2)
        if w > 6:
            pygame.draw.ellipse(s, (255, 240, 150), (20 - w // 2 + 3, 17, max(2, w - 6), 7))
        return s

    def _chest(self, opened):
        s = new()
        pygame.draw.rect(s, (140, 90, 40), (7, 20, 26, 14), border_radius=2)
        pygame.draw.rect(s, (90, 55, 25), (7, 20, 26, 14), 2, border_radius=2)
        pygame.draw.rect(s, (240, 200, 60), (7, 25, 26, 3))
        if not opened:
            pygame.draw.rect(s, (160, 105, 48), (7, 12, 26, 10), border_radius=4)
            pygame.draw.rect(s, (90, 55, 25), (7, 12, 26, 10), 2, border_radius=4)
            pygame.draw.rect(s, (240, 200, 60), (18, 21, 4, 5))
        else:
            pygame.draw.rect(s, (30, 15, 10), (9, 20, 22, 5))
            pygame.draw.rect(s, (160, 105, 48), (7, 7, 26, 8), border_radius=3)
            pygame.draw.rect(s, (90, 55, 25), (7, 7, 26, 8), 2, border_radius=3)
            pygame.draw.circle(s, (255, 230, 120), (20, 22), 2)
        return s

    def _stairs(self):
        S = 80
        s = pygame.Surface((S, S), pygame.SRCALPHA)
        pygame.draw.rect(s, (120, 110, 135), (0, 0, S, S), border_radius=6)
        pygame.draw.rect(s, (60, 54, 72), (0, 0, S, S), 4, border_radius=6)
        for i in range(7):
            c = clamp(128 - i * 17)
            r = pygame.Rect(8 + i * 5, 8 + i * 5, S - 16 - i * 10, S - 16 - i * 10)
            pygame.draw.rect(s, (c, clamp(c - 8), clamp(c + 12)), r, border_radius=3)
            pygame.draw.line(s, (clamp(c + 40),) * 3, r.topleft, (r.right, r.top), 2)
        pygame.draw.rect(s, (8, 6, 14), (30, 30, 20, 20), border_radius=2)
        return pygame.transform.smoothscale(s, (TILE, TILE))

    # ------------------------------------------------------------------ TILES (one set per biome)
    def tiles(self, floor):
        bi = min(max(floor, 1), len(BIOMES)) - 1
        if bi not in self._tilesets:
            pal, rng = BIOMES[bi], random.Random(500 + bi)
            ts = TileSet()
            ts.floor = [self._floor_tile(pal, rng, v) for v in range(8)]
            ts.wall_front = [self._wall_front(pal, rng) for _ in range(4)]
            ts.wall_top = [self._wall_top(pal, rng) for _ in range(2)]
            ts.ao_n = self._vgrad(TILE, 16, 150, 0)
            ts.ao_w = pygame.transform.rotate(self._vgrad(TILE, 11, 105, 0), 90)
            ts.ao_e = pygame.transform.flip(ts.ao_w, True, False)
            self._tilesets[bi] = ts
        return self._tilesets[bi]

    @staticmethod
    def _vgrad(w, h, a0, a1, color=(0, 0, 0)):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            t = y / max(1, h - 1)
            pygame.draw.line(s, (*color, int(a0 + (a1 - a0) * t)), (0, y), (w, y))
        return s

    def _floor_tile(self, pal, rng, v):
        S = 80
        base = pal['floor']
        s = pygame.Surface((S, S))
        s.fill(shade(base, 0.46))
        rows = (1, 2, 2, 3)[v % 4]
        rh = S // rows
        for r in range(rows):
            x = -rng.randint(0, 26) if rows > 1 else 0
            while x < S:
                wd = rng.randint(32, 58) if rows > 1 else S
                rect = pygame.Rect(x + 2, r * rh + 2, wd - 4, rh - 4)
                col = jit(base, rng, 8)
                pygame.draw.rect(s, col, rect, border_radius=6)
                pygame.draw.line(s, add(col, 20), (rect.left + 4, rect.top + 1), (rect.right - 5, rect.top + 1), 2)
                pygame.draw.line(s, add(col, 11), (rect.left + 1, rect.top + 4), (rect.left + 1, rect.bottom - 5), 2)
                pygame.draw.line(s, shade(col, 0.66), (rect.left + 4, rect.bottom - 2), (rect.right - 4, rect.bottom - 2), 2)
                pygame.draw.line(s, shade(col, 0.76), (rect.right - 2, rect.top + 4), (rect.right - 2, rect.bottom - 4), 2)
                for _ in range(rng.randint(8, 16)):
                    px, py = rng.randint(rect.left + 4, max(rect.left + 5, rect.right - 5)), rng.randint(rect.top + 4, max(rect.top + 5, rect.bottom - 5))
                    pygame.draw.circle(s, add(col, rng.choice((-14, 12))), (px, py), rng.randint(1, 2))
                x += wd
        ov = pygame.Surface((S, S), pygame.SRCALPHA)
        if pal['moss'] and rng.random() < 0.5:
            for _ in range(rng.randint(2, 4)):
                mx, my = rng.randint(6, 74), rng.randint(6, 74)
                pygame.draw.ellipse(ov, (70, 130, 60, 70), (mx, my, rng.randint(10, 24), rng.randint(8, 16)))
        if rng.random() < 0.45:
            x, y = rng.randint(10, 60), rng.randint(10, 60)
            pts = [(x, y)]
            for _ in range(4):
                x += rng.randint(-8, 12); y += rng.randint(5, 12)
                pts.append((x, y))
            pygame.draw.lines(ov, (*shade(base, 0.35), 200), False, pts, 2)
        s.blit(ov, (0, 0))
        return pygame.transform.smoothscale(s, (TILE, TILE))

    def _wall_front(self, pal, rng):
        S = 80
        base = pal['wall']
        s = pygame.Surface((S, S))
        s.fill(shade(base, 0.38))
        for r in range(2):
            x = 0 if r == 0 else -rng.randint(14, 26)
            while x < S:
                wd = rng.randint(34, 46)
                rect = pygame.Rect(x + 2, r * 40 + 2, wd - 4, 36)
                col = jit(base, rng, 9)
                pygame.draw.rect(s, col, rect, border_radius=5)
                pygame.draw.line(s, add(col, 30), (rect.left + 4, rect.top + 1), (rect.right - 5, rect.top + 1), 3)
                pygame.draw.line(s, add(col, 14), (rect.left + 1, rect.top + 4), (rect.left + 1, rect.bottom - 5), 2)
                pygame.draw.line(s, shade(col, 0.6), (rect.left + 4, rect.bottom - 2), (rect.right - 4, rect.bottom - 2), 3)
                pygame.draw.line(s, shade(col, 0.74), (rect.right - 2, rect.top + 4), (rect.right - 2, rect.bottom - 4), 2)
                for _ in range(rng.randint(6, 12)):
                    pygame.draw.circle(s, add(col, rng.choice((-16, 14))),
                                       (rng.randint(rect.left + 3, rect.right - 3), rng.randint(rect.top + 4, rect.bottom - 4)), rng.randint(1, 2))
                x += wd
        ov = pygame.Surface((S, S), pygame.SRCALPHA)
        pygame.draw.rect(ov, (*add(base, 60), 90), (0, 0, S, 5))                  # sunlit top edge
        ov.blit(self._vgrad(S, 34, 0, 170), (0, S - 34))                           # dark where it meets the floor
        for _ in range(rng.randint(1, 3)):                                          # stains
            x = rng.randint(4, 72)
            ov.blit(self._vgrad(rng.randint(4, 9), rng.randint(22, 50), 60, 0), (x, 6))
        if pal['moss'] and rng.random() < 0.7:
            for _ in range(3):
                pygame.draw.ellipse(ov, (70, 140, 60, 110), (rng.randint(0, 66), rng.randint(0, 8), rng.randint(10, 20), rng.randint(6, 14)))
        s.blit(ov, (0, 0))
        return pygame.transform.smoothscale(s, (TILE, TILE))

    def _wall_top(self, pal, rng):
        S = 80
        s = pygame.Surface((S, S))
        s.fill(pal['top'])
        for i in range(0, S, 20):
            pygame.draw.line(s, add(pal['top'], 7), (0, i), (S, i), 2)
        for _ in range(26):
            pygame.draw.circle(s, add(pal['top'], rng.choice((-6, 8))), (rng.randint(0, S), rng.randint(0, S)), rng.randint(1, 3))
        return pygame.transform.smoothscale(s, (TILE, TILE))

    # ------------------------------------------------------------------ decorations baked into the level picture
    def torch_bracket(self, surf, x, y):
        pygame.draw.rect(surf, (36, 30, 34), (x + 17, y + 14, 6, 14), border_radius=2)
        pygame.draw.rect(surf, (70, 62, 66), (x + 15, y + 12, 10, 4), border_radius=2)
        pygame.draw.rect(surf, (20, 16, 20), (x + 13, y + 24, 14, 3), border_radius=1)

    def banner(self, surf, x, y, color):
        c = pygame.Surface((16, 30), pygame.SRCALPHA)
        pygame.draw.polygon(c, color, [(0, 0), (16, 0), (16, 26), (8, 21), (0, 26)])
        pygame.draw.polygon(c, shade(color, 0.6), [(0, 0), (16, 0), (16, 26), (8, 21), (0, 26)], 2)
        pygame.draw.rect(c, (225, 190, 70), (0, 0, 16, 3))
        pygame.draw.circle(c, (225, 190, 70), (8, 11), 3)
        pygame.draw.circle(c, shade(color, 0.5), (8, 11), 1)
        surf.blit(c, (x + 12, y + 2))

    def splat(self, surf, x, y, color, rng, size=14):
        t = new(size * 4, size * 4)
        cx = size * 2
        for _ in range(rng.randint(4, 7)):
            ox, oy = rng.randint(-size, size), rng.randint(-size // 2, size // 2)
            rw, rh = rng.randint(size // 2, size), rng.randint(size // 3, size // 2 + 2)
            pygame.draw.ellipse(t, (*color, rng.randint(50, 95)), (cx + ox - rw // 2, cx + oy - rh // 2, rw, rh))
        surf.blit(t, (int(x - cx), int(y - cx)))

    def decor(self, surf, kind, x, y, rng, pal, flip=None):
        """Draw one decoration on the 40x40 tile whose corner is (x, y). Returns [(cx,cy,radius,color,strength)] lights."""
        t = new(64, 64)
        lights = []
        if kind == 'bones':
            c = (214, 208, 190, 255)
            for a, b in (((14, 40), (46, 46)), ((18, 48), (50, 38))):
                pygame.draw.line(t, c, a, b, 4)
                pygame.draw.circle(t, c, a, 3); pygame.draw.circle(t, c, b, 3)
            pygame.draw.circle(t, c, (34, 26), 9)
            pygame.draw.rect(t, c, (29, 32, 10, 6), border_radius=2)
            pygame.draw.circle(t, (30, 24, 30, 255), (31, 26), 2); pygame.draw.circle(t, (30, 24, 30, 255), (37, 26), 2)
            t = pygame.transform.rotate(t, rng.randint(0, 359))
        elif kind == 'rubble':
            for _ in range(rng.randint(4, 7)):
                g = rng.randint(70, 120)
                px, py, r = rng.randint(14, 50), rng.randint(14, 50), rng.randint(3, 7)
                pygame.draw.ellipse(t, (g, g - 4, g + 6, 255), (px, py, r * 2, r * 2 - 2))
                pygame.draw.ellipse(t, (g + 40, g + 36, g + 46, 255), (px + 1, py, r, r - 1))
        elif kind in ('puddle', 'lava'):
            w, h = rng.randint(30, 48), rng.randint(20, 34)
            col = pal['puddle']
            if kind == 'lava':
                pygame.draw.ellipse(t, (60, 18, 10, 255), (32 - w // 2 - 3, 32 - h // 2 - 3, w + 6, h + 6))
                pygame.draw.ellipse(t, (230, 80, 20, 255), (32 - w // 2, 32 - h // 2, w, h))
                pygame.draw.ellipse(t, (255, 190, 60, 255), (32 - w // 3, 32 - h // 3, w * 2 // 3, h * 2 // 3))
                lights.append((x + 20, y + 20, 100, (255, 120, 40), 0.5))
            else:
                pygame.draw.ellipse(t, (*shade(col, 0.5), 200), (32 - w // 2 - 2, 32 - h // 2 - 2, w + 4, h + 4))
                pygame.draw.ellipse(t, (*col, 190), (32 - w // 2, 32 - h // 2, w, h))
                pygame.draw.ellipse(t, (*add(col, 60), 120), (32 - w // 3, 32 - h // 3, w // 2, h // 3))
        elif kind == 'web':
            c = (225, 225, 240, 120)
            for ex, ey in ((60, 2), (56, 24), (40, 44), (24, 56), (2, 60)):
                pygame.draw.line(t, c, (2, 2), (ex, ey), 1)
            for r in (14, 26, 38, 50):
                pygame.draw.arc(t, c, (-r, -r, r * 2, r * 2), -1.57, 0, 1)
            fx, fy = flip if flip else (rng.random() < 0.5, rng.random() < 0.5)
            t = pygame.transform.flip(t, fx, fy)
        elif kind == 'blood':
            for _ in range(rng.randint(4, 8)):
                px, py = rng.randint(10, 54), rng.randint(10, 54)
                pygame.draw.ellipse(t, (118, 18, 28, rng.randint(110, 170)), (px, py, rng.randint(5, 14), rng.randint(4, 9)))
        elif kind == 'rune':
            col = (*pal['light'], 120)
            pygame.draw.circle(t, col, (32, 32), 18, 2)
            pts = [(32 + 13 * math.cos(math.radians(a)), 32 + 13 * math.sin(math.radians(a))) for a in (-90, 30, 150)]
            pygame.draw.polygon(t, col, pts, 2)
            for a in range(0, 360, 45):
                pygame.draw.line(t, col, (32 + 18 * math.cos(math.radians(a)), 32 + 18 * math.sin(math.radians(a))),
                                 (32 + 22 * math.cos(math.radians(a)), 32 + 22 * math.sin(math.radians(a))), 2)
            lights.append((x + 20, y + 20, 70, pal['light'], 0.22))
        surf.blit(t, (x + 20 - t.get_width() // 2, y + 20 - t.get_height() // 2))
        return lights

    def big_rune(self, surf, cx, cy, r, color):
        """A huge glowing summoning circle for boss rooms."""
        t = new(r * 2 + 20, r * 2 + 20)
        c = r + 10
        for rad, a, w in ((r, 130, 3), (r - 10, 90, 2), (r * 2 // 3, 110, 2)):
            pygame.draw.circle(t, (*color, a), (c, c), rad, w)
        for k in (0, 1):
            pts = [(c + (r * 0.66) * math.cos(math.radians(a + k * 60)), c + (r * 0.66) * math.sin(math.radians(a + k * 60))) for a in (-90, 30, 150)]
            pygame.draw.polygon(t, (*color, 120), pts, 2)
        for a in range(0, 360, 15):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            pygame.draw.line(t, (*color, 110), (c + (r - 10) * ca, c + (r - 10) * sa), (c + r * ca, c + r * sa), 2)
        surf.blit(t, (cx - c, cy - c))

# ====================================================================== module-level helpers


class TileSet:
    pass


def _skull(s, cx, cy, r, col=(235, 232, 218), eye=(26, 20, 32)):
    pygame.draw.circle(s, col, (cx, cy - r // 6), r)
    pygame.draw.rect(s, col, (cx - r * 2 // 3, cy + r // 3, r * 4 // 3, r * 2 // 3), border_radius=max(1, r // 4))
    pygame.draw.circle(s, eye, (cx - r // 3, cy - r // 6), max(1, r // 4))
    pygame.draw.circle(s, eye, (cx + r // 3, cy - r // 6), max(1, r // 4))
    for k in (-1, 0, 1):
        pygame.draw.line(s, eye, (cx + k * r // 3, cy + r // 2), (cx + k * r // 3, cy + r), max(1, r // 6))


def make_icon(icon, color, size=56):
    """Ability pictures. Drawn twice as big, then shrunk, so the lines look smooth."""
    S = size * 2
    u = S / 56.0
    s = pygame.Surface((S, S), pygame.SRCALPHA)
    cx = cy = S // 2
    r = int(S / 2 - 9 * u)
    L = lambda n: max(1, int(n * u))
    c, w = color, (255, 255, 255)
    P = pygame.draw
    if icon == 'swirl':
        P.circle(s, c, (cx, cy), r, L(3))
        P.arc(s, w, (cx - r + L(4), cy - r + L(4), 2 * r - L(8), 2 * r - L(8)), 0.5, 4.2, L(3))
    elif icon == 'shield':
        pts = [(cx - r, cy - r + L(2)), (cx + r, cy - r + L(2)), (cx + r, cy), (cx, cy + r + L(2)), (cx - r, cy)]
        P.polygon(s, c, pts); P.polygon(s, w, pts, L(2))
    elif icon == 'slam':
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            P.line(s, c, (cx + dx * L(3), cy + dy * L(3)), (cx + dx * r, cy + dy * r), L(3))
        P.circle(s, w, (cx, cy), L(4))
    elif icon == 'fire':
        P.circle(s, c, (cx, cy + L(3)), r - L(2))
        P.polygon(s, (255, 220, 90), [(cx - r // 2, cy), (cx, cy - r - L(2)), (cx + r // 2, cy)])
    elif icon == 'snow':
        for ang in (0, 60, 120):
            dx, dy = math.cos(math.radians(ang)) * r, math.sin(math.radians(ang)) * r
            P.line(s, c, (cx - dx, cy - dy), (cx + dx, cy + dy), L(3))
        P.circle(s, w, (cx, cy), L(3))
    elif icon == 'heart':
        k = r * 0.56
        pts = [(cx - r, cy - L(2)), (cx, cy + r + L(2)), (cx + r, cy - L(2))]
        for col, grow in ((w, L(3)), (c, 0)):
            P.circle(s, col, (int(cx - k), int(cy - k * 0.55)), int(k + grow))
            P.circle(s, col, (int(cx + k), int(cy - k * 0.55)), int(k + grow))
            P.polygon(s, col, [(pts[0][0] - grow, pts[0][1]), (pts[1][0], pts[1][1] + grow * 1.4),
                               (pts[2][0] + grow, pts[2][1])])
        for ang in (0, 60, 120):                       # a little snowflake in the middle
            dx, dy = math.cos(math.radians(ang)) * L(7), math.sin(math.radians(ang)) * L(7)
            P.line(s, (200, 240, 255), (cx - dx, cy - dy), (cx + dx, cy + dy), L(2))
    elif icon == 'flower':
        for i in range(6):
            a = i * math.pi / 3
            fx, fy = cx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78
            for j in range(5):
                b = a + j * 2 * math.pi / 5
                P.circle(s, c, (int(fx + math.cos(b) * L(4)), int(fy + math.sin(b) * L(4))), L(3))
            P.circle(s, (255, 230, 110), (int(fx), int(fy)), L(2))
        P.circle(s, w, (cx, cy), L(3))
    elif icon == 'bolt':
        pts = [(cx + L(3), cy - r - L(2)), (cx - r // 2 - L(1), cy + L(2)), (cx, cy + L(2)), (cx - L(3), cy + r + L(2)),
               (cx + r // 2 + L(1), cy - L(3)), (cx, cy - L(3))]
        P.polygon(s, c, pts); P.polygon(s, w, pts, L(1))
    elif icon == 'knives':
        for off in (-7, 0, 7):
            P.line(s, c, (cx + L(off) - L(4), cy + r), (cx + L(off) + L(4), cy - r), L(3))
            P.circle(s, w, (cx + L(off) + L(4), cy - r), L(2))
    elif icon == 'step':
        P.line(s, c, (cx - r, cy), (cx + r - L(4), cy), L(4))
        P.polygon(s, w, [(cx + r + L(1), cy), (cx + r - L(7), cy - L(7)), (cx + r - L(7), cy + L(7))])
        P.circle(s, c, (cx - r, cy), L(3))
    elif icon == 'poison':
        P.circle(s, c, (cx, cy), r)
        for dx, dy in ((-5, -3), (4, 2), (-1, 6)):
            P.circle(s, (20, 60, 20), (cx + L(dx), cy + L(dy)), L(3))
    elif icon == 'nova':
        for k in (r, r - L(5), r - L(10)):
            if k > 1:
                P.circle(s, c if k != r - L(10) else w, (cx, cy), k, L(2))
    elif icon == 'raise':
        for dx in (-9, 0, 9):
            P.arc(s, c, (cx + L(dx) - L(5), cy + L(6), L(10), L(20)), 0.2, 3.0, L(2))
        _skull(s, cx, cy - L(6), L(13), w)
    elif icon == 'corpse':
        pts = []
        for i in range(16):
            a = i * math.pi / 8
            rr = r if i % 2 == 0 else r * 0.55
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        P.polygon(s, c, pts)
        _skull(s, cx, cy, L(10), (40, 40, 50), c)
    elif icon == 'army':
        for dx, dy, rr in ((0, -8, 9), (-11, 7, 8), (11, 7, 8)):
            _skull(s, cx + L(dx), cy + L(dy), L(rr), c)
    elif icon == 'fist':
        P.circle(s, c, (cx, cy + L(3)), r - L(4))
        for dx in (-10, -3, 4, 11):
            P.rect(s, w, (cx + L(dx) - L(2), cy - r + L(2), L(4), L(6)))
        P.line(s, w, (cx - r - L(2), cy - r), (cx - r // 2, cy - r // 2), L(3))
    elif icon == 'tempest':
        for k in (r, r - L(6), r - L(12)):
            if k > 1:
                P.circle(s, c, (cx, cy), k, L(2))
        for ang in (0, 90, 180, 270):
            dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            x0, y0 = cx + dx * (r + L(2)), cy + dy * (r + L(2))
            x1, y1 = cx + dx * (r + L(10)), cy + dy * (r + L(10))
            P.line(s, w, (x0, y0), (x1, y1), L(3))
    elif icon == 'kick':
        P.polygon(s, c, [(cx - r, cy - L(4)), (cx + L(2), cy - L(10)), (cx + r, cy + L(2)),
                         (cx + L(4), cy + L(10)), (cx - r // 2, cy + L(6))])
        P.line(s, w, (cx + r, cy + L(2)), (cx + r + L(14), cy + L(2)), L(4))
        P.polygon(s, w, [(cx + r + L(16), cy + L(2)), (cx + r + L(8), cy - L(5)), (cx + r + L(8), cy + L(9))])
    elif icon in ('drain', 'curse'):                    # a drop of blood
        k = r - L(5)
        if icon == 'curse':                               # ...bursting
            for ang in range(0, 360, 45):
                a = math.radians(ang)
                P.line(s, w, (cx + math.cos(a) * (r - L(2)), cy + L(3) + math.sin(a) * (r - L(2))),
                       (cx + math.cos(a) * (r + L(7)), cy + L(3) + math.sin(a) * (r + L(7))), L(2))
        P.circle(s, c, (cx, cy + L(5)), k)
        P.polygon(s, c, [(cx - k + L(1), cy + L(1)), (cx, cy - r - L(4)), (cx + k - L(1), cy + L(1))])
        P.circle(s, w, (cx - k // 3, cy + L(4)), max(2, k // 4))
        if icon == 'drain':                               # ...with fangs
            for dx in (-5, 5):
                P.polygon(s, w, [(cx + L(dx) - L(3), cy - r - L(6)), (cx + L(dx) + L(3), cy - r - L(6)),
                                 (cx + L(dx), cy - r + L(4))])
    elif icon == 'pool':
        P.ellipse(s, c, (cx - r - L(4), cy - L(4), 2 * r + L(8), r + L(8)))
        P.ellipse(s, w, (cx - r - L(4), cy - L(4), 2 * r + L(8), r + L(8)), L(2))
        for dx, dy, rr in ((-9, 6, 4), (6, 9, 3), (2, 2, 2)):
            P.circle(s, w, (cx + L(dx), cy + L(dy)), L(rr), L(1))
        P.circle(s, c, (cx, cy - L(12)), L(5))
        P.polygon(s, c, [(cx - L(4), cy - L(14)), (cx, cy - r - L(6)), (cx + L(4), cy - L(14))])
    elif icon == 'crescent':                            # a golden crescent flying right
        for k, (rr, wd, col) in enumerate(((r, L(7), c), (r - L(5), L(3), w))):
            P.arc(s, col, (cx - rr - L(8), cy - rr, 2 * rr, 2 * rr), -1.15, 1.15, wd)
        P.circle(s, w, (cx - L(14), cy), L(3))
    elif icon == 'blink':                               # a figure's outline, a dotted path, and a flash
        for k in range(4):
            P.circle(s, c, (cx - r + L(4) + k * L(9), cy + L(6) - k * L(3)), L(3))
        P.circle(s, w, (cx + r - L(10), cy - L(6)), L(10), L(3))
        for a in range(0, 360, 45):
            ra = math.radians(a)
            P.line(s, c, (cx + r - L(10) + math.cos(ra) * L(13), cy - L(6) + math.sin(ra) * L(13)),
                   (cx + r - L(10) + math.cos(ra) * L(19), cy - L(6) + math.sin(ra) * L(19)), L(2))
    elif icon == 'barrage':                             # a HUGE crescent with speed lines
        P.arc(s, c, (cx - r - L(2), cy - r, 2 * r, 2 * r), -1.3, 1.3, L(11))
        P.arc(s, w, (cx - r + L(3), cy - r + L(5), 2 * r - L(10), 2 * r - L(10)), -1.1, 1.1, L(4))
        for k in (-1, 0, 1):
            P.line(s, c, (cx - r, cy + k * L(12)), (cx - r + L(14), cy + k * L(12)), L(3))
    elif icon == 'shuriken':                            # a 4-point throwing star
        pts = []
        for i in range(8):
            a = math.radians(i * 45 + 20)
            k = r + L(4) if i % 2 == 0 else r * 0.34
            pts.append((cx + math.cos(a) * k, cy + math.sin(a) * k))
        P.polygon(s, c, pts)
        P.polygon(s, w, pts, L(2))
        P.circle(s, (30, 24, 46), (cx, cy), L(4))
        P.circle(s, w, (cx, cy), L(4), L(1))
    elif icon == 'shadow':                              # a figure, and its darker twin stepping out of it
        for dx, col in ((L(7), shade(c, 0.45)), (-L(6), c)):
            P.circle(s, col, (cx + dx, cy - r + L(6)), L(7))
            P.polygon(s, col, [(cx + dx - L(10), cy + r + L(2)), (cx + dx - L(7), cy - L(3)), (cx + dx + L(7), cy - L(3)),
                               (cx + dx + L(10), cy + r + L(2))])
        P.circle(s, w, (cx - L(6), cy - r + L(6)), L(7), L(1))
        P.line(s, w, (cx - L(9), cy - r + L(6)), (cx - L(3), cy - r + L(6)), L(2))
    elif icon == 'swipe':                               # blades whirling all the way round
        for k in range(3):
            a0 = k * 2.0944
            P.arc(s, c, (cx - r, cy - r, 2 * r, 2 * r), a0, a0 + 1.6, L(5))
            P.arc(s, w, (cx - r + L(6), cy - r + L(6), 2 * r - L(12), 2 * r - L(12)), a0 + 0.3, a0 + 1.4, L(2))
        P.circle(s, w, (cx, cy), L(4))
    elif icon == 'trislash':
        for i, col in enumerate((c, c, w)):
            off = L(-9 + i * 9)
            P.arc(s, col, (cx - r + off, cy - r, 2 * r, 2 * r), -0.9, 0.9, L(4))
    elif icon == 'warcry':
        P.circle(s, c, (cx, cy), r, L(3))
        P.circle(s, c, (cx, cy), r - L(8), L(2))
        for ang in range(0, 360, 72):
            a = math.radians(ang - 90)
            P.circle(s, w, (int(cx + math.cos(a) * (r - L(4))), int(cy + math.sin(a) * (r - L(4)))), L(3))
        P.circle(s, w, (cx, cy), L(4))
    elif icon == 'blade':
        P.line(s, c, (cx - r + L(6), cy + r - L(6)), (cx + r, cy - r), L(7))
        P.line(s, w, (cx - r + L(8), cy + r - L(8)), (cx + r - L(1), cy - r + L(1)), L(2))
        P.line(s, (210, 165, 45), (cx - r + L(1), cy + L(3)), (cx - L(3), cy + r - L(1)), L(4))
        P.line(s, (150, 100, 50), (cx - r + L(6), cy + r - L(6)), (cx - r, cy + r), L(5))
    return pygame.transform.smoothscale(s, (size, size))


def ui_icon(kind, size=24):
    """Tiny icons for the HUD: coin, dash."""
    S = size * 3
    s = pygame.Surface((S, S), pygame.SRCALPHA)
    P = pygame.draw
    m = S // 2
    if kind == 'coin':
        P.circle(s, (120, 80, 10), (m, m), S // 2 - 2)
        P.circle(s, (250, 205, 50), (m, m), S // 2 - 6)
        P.circle(s, (255, 240, 150), (m - S // 12, m - S // 12), S // 6)
        P.circle(s, (200, 150, 30), (m, m), S // 4, 3)
    elif kind == 'dash':
        for i, a in enumerate((255, 170, 90)):
            P.polygon(s, (170, 200, 255, a), [(S // 10 + i * S // 4, S // 4), (S // 3 + i * S // 4, m), (S // 10 + i * S // 4, S * 3 // 4), (S // 5 + i * S // 4, m)])
    return pygame.transform.smoothscale(s, (size, size))


# ====================================================================== SHOP ITEM ICONS
def _stat_symbol(s, stat, cx, cy, r, col):
    """Draw the little picture for one stat (sword, star, hourglass, drop, shield) centred on (cx, cy)."""
    P = pygame.draw
    lite = tuple(min(255, c + 70) for c in col)
    dark = (24, 18, 30)
    w = max(2, int(r * 0.12))
    if stat == 'atk':                                   # a sword pointing up-right
        d = r * 0.9
        tip, hilt = (cx + d * 0.7, cy - d * 0.7), (cx - d * 0.35, cy + d * 0.35)
        nx, ny = 0.7071 * r * 0.2, 0.7071 * r * 0.2
        blade = [tip, (hilt[0] + nx, hilt[1] + ny), (hilt[0] - nx, hilt[1] - ny)]
        P.polygon(s, lite, blade)
        P.polygon(s, dark, blade, w)
        P.line(s, col, (hilt[0] - r * 0.38, hilt[1] - r * 0.38), (hilt[0] + r * 0.38, hilt[1] + r * 0.38), max(3, int(r * 0.22)))
        P.line(s, (120, 84, 50), hilt, (cx - d * 0.75, cy + d * 0.75), max(3, int(r * 0.2)))
        P.circle(s, col, (int(cx - d * 0.75), int(cy + d * 0.75)), max(2, int(r * 0.14)))
    elif stat == 'ap':                                  # a four-point magic star
        pts = []
        for i in range(8):
            a = math.radians(i * 45 - 90)
            k = r if i % 2 == 0 else r * 0.34
            pts.append((cx + math.cos(a) * k, cy + math.sin(a) * k))
        P.polygon(s, col, pts)
        P.polygon(s, dark, pts, w)
        P.circle(s, lite, (int(cx), int(cy)), max(2, int(r * 0.22)))
    elif stat == 'cdr':                                 # an hourglass
        t, b, hw = cy - r * 0.85, cy + r * 0.85, r * 0.62
        top = [(cx - hw, t), (cx + hw, t), (cx, cy)]
        bot = [(cx - hw, b), (cx + hw, b), (cx, cy)]
        P.polygon(s, (40, 60, 70), top)
        P.polygon(s, col, bot)
        P.polygon(s, lite, [(cx - hw * 0.5, t + r * 0.25), (cx + hw * 0.5, t + r * 0.25), (cx, cy)])
        P.polygon(s, dark, top, w)
        P.polygon(s, dark, bot, w)
        for yy in (t, b):
            P.line(s, (190, 150, 80), (cx - hw - r * 0.1, yy), (cx + hw + r * 0.1, yy), max(3, int(r * 0.2)))
    elif stat == 'ls':                                  # a drop of blood
        cy2 = cy + r * 0.25
        P.polygon(s, col, [(cx, cy - r * 0.95), (cx - r * 0.56, cy2 - r * 0.1), (cx + r * 0.56, cy2 - r * 0.1)])
        P.circle(s, col, (int(cx), int(cy2)), int(r * 0.6))
        P.circle(s, lite, (int(cx - r * 0.2), int(cy2 - r * 0.05)), max(2, int(r * 0.18)))
        P.circle(s, dark, (int(cx), int(cy2)), int(r * 0.6), w, draw_bottom_left=True, draw_bottom_right=True)
    else:                                               # 'df': a shield
        pts = [(cx - r * 0.78, cy - r * 0.8), (cx + r * 0.78, cy - r * 0.8), (cx + r * 0.78, cy + r * 0.1),
               (cx, cy + r * 0.95), (cx - r * 0.78, cy + r * 0.1)]
        P.polygon(s, col, pts)
        P.polygon(s, lite, [(cx, cy - r * 0.8), (cx + r * 0.78, cy - r * 0.8), (cx + r * 0.78, cy + r * 0.1), (cx, cy + r * 0.95)])
        P.polygon(s, dark, pts, w)
        P.line(s, dark, (cx, cy - r * 0.8), (cx, cy + r * 0.95), max(1, w // 2))


def item_icon(item, colors, size=64):
    """The picture for a shop item. `item` is its entry from items.ITEMS, `colors` is items.STAT_COLOR.
    Small items: a small symbol on grey.  Components: a big symbol with a bronze frame.
    Mythics: both of its stats' symbols on a split background with a gold frame."""
    S = size * 3
    s = pygame.Surface((S, S), pygame.SRCALPHA)
    P = pygame.draw
    stats = list(item['stats'])
    tier = item['tier']
    rad = S // 6
    box = pygame.Rect(0, 0, S, S)
    if tier == 3:
        a, b = (tuple(int(c * 0.34) for c in colors[k]) for k in stats)
        P.rect(s, a, box, border_radius=rad)
        clip = pygame.Surface((S, S), pygame.SRCALPHA)
        P.rect(clip, b, box, border_radius=rad)
        P.polygon(clip, (0, 0, 0, 0), [(0, 0), (S, 0), (0, S)])
        s.blit(clip, (0, 0))
        P.line(s, (255, 230, 150), (S * 0.1, S * 0.9), (S * 0.9, S * 0.1), max(2, S // 60))
        _stat_symbol(s, stats[0], S * 0.33, S * 0.34, S * 0.21, colors[stats[0]])
        _stat_symbol(s, stats[1], S * 0.67, S * 0.67, S * 0.21, colors[stats[1]])
        P.rect(s, (120, 84, 20), box, max(4, S // 16), border_radius=rad)
        P.rect(s, (255, 214, 90), box.inflate(-S // 22, -S // 22), max(3, S // 30), border_radius=rad)
    else:
        P.rect(s, (38, 34, 50) if tier == 1 else (46, 36, 34), box, border_radius=rad)
        _stat_symbol(s, stats[0], S * 0.5, S * 0.5, S * (0.22 if tier == 1 else 0.33), colors[stats[0]])
        P.rect(s, (120, 120, 140) if tier == 1 else (205, 140, 80), box, max(3, S // (26 if tier == 1 else 16)),
               border_radius=rad)
    return pygame.transform.smoothscale(s, (size, size))
