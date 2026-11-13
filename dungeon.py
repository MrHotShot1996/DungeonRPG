"""dungeon.py - builds a brand new random dungeon every time (rooms + hallways)."""
import math
import random
from settings import MAP_W, MAP_H, TILE

WALL = 0
FLOOR = 1


class Room:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def center(self):
        return (self.x + self.w // 2, self.y + self.h // 2)

    def intersects(self, o, pad=2):
        return not (self.x + self.w + pad <= o.x or o.x + o.w + pad <= self.x or
                    self.y + self.h + pad <= o.y or o.y + o.h + pad <= self.y)


class Dungeon:
    def __init__(self, floor):
        self.floor = floor
        self.grid = []
        self.rooms = []
        self._generate()

    def _generate(self):
        # keep trying until we get at least 6 rooms
        target = min(11, 8 + self.floor // 3)
        boss_floor = self.floor in (5, 10)
        while len(self.rooms) < 6:
            self.grid = [[WALL] * MAP_W for _ in range(MAP_H)]
            self.rooms = []
            for _ in range(200):
                w, h = random.randint(6, 12), random.randint(5, 9)
                x = random.randint(1, MAP_W - w - 2)
                y = random.randint(1, MAP_H - h - 2)
                room = Room(x, y, w, h)
                if any(room.intersects(o) for o in self.rooms):
                    continue
                self._carve_room(room)
                if self.rooms:  # connect to the previous room with a hallway
                    (x1, y1), (x2, y2) = self.rooms[-1].center, room.center
                    if random.random() < 0.5:
                        self._h(x1, x2, y1); self._v(y1, y2, x2)
                    else:
                        self._v(y1, y2, x1); self._h(x1, x2, y2)
                self.rooms.append(room)
                if len(self.rooms) >= target:
                    break
        if boss_floor:
            self._make_boss_arena()

    def _make_boss_arena(self):
        """Take the biggest room (not the start room), grow it, and make it the LAST room."""
        cands = self.rooms[1:]
        big = max(cands, key=lambda r: r.w * r.h)
        others = [r for r in self.rooms if r is not big]
        for g in (4, 3, 2, 1):
            nr = Room(big.x - g, big.y - g, big.w + 2 * g, big.h + 2 * g)
            if nr.x < 1 or nr.y < 1 or nr.x + nr.w > MAP_W - 1 or nr.y + nr.h > MAP_H - 1:
                continue
            if any(nr.intersects(o, 1) for o in others):
                continue
            self._carve_room(nr)
            big = nr
            break
        self.rooms = others + [big]

    def _set(self, x, y):
        if 1 <= x < MAP_W - 1 and 1 <= y < MAP_H - 1:
            self.grid[y][x] = FLOOR

    def _carve_room(self, r):
        for yy in range(r.y, r.y + r.h):
            for xx in range(r.x, r.x + r.w):
                self.grid[yy][xx] = FLOOR

    def _h(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self._set(x, y); self._set(x, y + 1)

    def _v(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self._set(x, y); self._set(x + 1, y)

    # ---- helpers the rest of the game uses ----
    def is_wall(self, tx, ty):
        if tx < 0 or ty < 0 or tx >= MAP_W or ty >= MAP_H:
            return True
        return self.grid[ty][tx] == WALL

    def hits_wall(self, rect):
        x0, x1 = rect.left // TILE, (rect.right - 1) // TILE
        y0, y1 = rect.top // TILE, (rect.bottom - 1) // TILE
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if self.is_wall(tx, ty):
                    return True
        return False

    def line_clear(self, x1, y1, x2, y2):
        """Can something at (x1,y1) 'see' (x2,y2) without a wall in between?"""
        steps = int(math.hypot(x2 - x1, y2 - y1) // 12) + 1
        for i in range(1, steps):
            t = i / steps
            if self.is_wall(int((x1 + (x2 - x1) * t) // TILE), int((y1 + (y2 - y1) * t) // TILE)):
                return False
        return True

    def random_spot(self, room):
        tx = random.randint(room.x + 1, room.x + room.w - 2)
        ty = random.randint(room.y + 1, room.y + room.h - 2)
        return (tx + 0.5) * TILE, (ty + 0.5) * TILE
