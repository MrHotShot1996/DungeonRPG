"""sounds.py - makes ALL the sound effects and music with math! No sound files needed.
A sound is just a list of numbers that wiggle up and down really fast (a 'wave')."""
import array
import math
import random
import threading

import pygame

RATE = 22050


def _wave(kind, p):
    if kind == 'square':
        return 1.0 if p < 0.5 else -1.0
    if kind == 'saw':
        return 2 * p - 1
    if kind == 'tri':
        return 4 * abs(p - 0.5) - 1
    if kind == 'sine':
        return math.sin(2 * math.pi * p)
    return random.uniform(-1, 1)  # noise (crashes, swooshes)


def tone(freq, dur, kind='square', vol=0.5, slide=0.0, attack=0.004, decay=1.5):
    n = int(RATE * dur)
    out = [0.0] * n
    phase = 0.0
    for i in range(n):
        t = i / RATE
        phase += max(20.0, freq + slide * t) / RATE
        env = min(1.0, t / attack) * (1.0 - i / n) ** decay
        out[i] = _wave(kind, phase % 1.0) * env * vol
    return out


def concat(*parts):
    r = []
    for p in parts:
        r.extend(p)
    return r


def layer(*parts):
    n = max(len(p) for p in parts)
    out = [0.0] * n
    for p in parts:
        for i, v in enumerate(p):
            out[i] += v
    return out


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


class Audio:
    def __init__(self):
        global RATE
        self.enabled = False
        self.muted = False
        self.sfx = {}
        self.music = None
        self.channel = None
        self._music_ready = False
        try:
            pygame.mixer.quit()
            pygame.mixer.init(RATE, -16, 1, 512)
            RATE, _, self.channels = pygame.mixer.get_init()
            pygame.mixer.set_num_channels(16)
            self.enabled = True
        except Exception as e:  # no speakers? the game still works
            print("Sound could not start (game will be silent):", e)
            return
        threading.Thread(target=self._build_all, daemon=True).start()

    def _build_all(self):
        self._build_sfx()
        self._build_music()

    def _to_sound(self, samples, vol=0.8):
        buf = array.array('h')
        for s in samples:
            v = int(max(-1.0, min(1.0, s)) * 32767 * vol)
            for _ in range(self.channels):
                buf.append(v)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _build_sfx(self):
        T = tone
        d = {
            'swing': layer(T(0, .12, 'noise', .22), T(500, .12, 'saw', .12, slide=-2500)),
            'hit': layer(T(0, .12, 'noise', .4), T(180, .12, 'square', .3, slide=-900)),
            'hurt': T(300, .3, 'saw', .45, slide=-700),
            'coin': concat(T(988, .07, 'square', .25), T(1319, .2, 'square', .25)),
            'potion': T(300, .35, 'sine', .5, slide=900),
            'levelup': concat(*[T(f, .1, 'square', .28) for f in (523, 659, 784)], T(1047, .4, 'square', .28)),
            'stairs': T(500, .6, 'tri', .5, slide=-700),
            'die': layer(T(0, .35, 'noise', .3), T(400, .35, 'square', .25, slide=-1000)),
            'shoot': T(700, .18, 'square', .18, slide=-2500),
            'dash': T(0, .18, 'noise', .18),
            'deflect': T(1500, .06, 'square', .18),
            'select': T(800, .06, 'square', .22),
            'chest': concat(*[T(f, .09, 'sine', .4) for f in (523, 659, 784, 1047)], T(1319, .3, 'sine', .4)),
            'gameover': concat(T(392, .3, 'saw', .4), T(330, .3, 'saw', .4), T(262, .3, 'saw', .4),
                               T(196, .9, 'saw', .4, slide=-40)),
            'victory': concat(*[T(f, .16, 'square', .3) for f in (523, 523, 523, 659, 784)],
                              T(1047, .7, 'square', .3)),
            'whirl': layer(T(0, .3, 'noise', .25), T(300, .3, 'saw', .12, slide=900)),
            'shield': T(400, .4, 'sine', .4, slide=600),
            'slam': layer(T(0, .35, 'noise', .45), T(90, .35, 'saw', .5, slide=-150)),
            'boom': layer(T(0, .5, 'noise', .55, decay=2.0), T(120, .5, 'saw', .4, slide=-180)),
            'frost': concat(*[T(f, .06, 'sine', .3) for f in (1800, 2200, 2600, 3000)]),
            'zap': concat(*[T(random.choice(range(600, 2400, 100)), .025, 'square', .25) for _ in range(8)]),
            'knife': layer(T(0, .1, 'noise', .2), T(1200, .1, 'saw', .1, slide=-5000)),
            'warp': T(200, .3, 'sine', .4, slide=1500),
            'warn': concat(T(900, .06, 'square', .2), [0.0] * int(RATE * .03), T(900, .06, 'square', .2)),
            'heal': concat(*[T(f, .1, 'sine', .35) for f in (523, 659, 784, 1047)]),
            'nova': layer(T(300, .4, 'sine', .4, slide=900), T(0, .3, 'noise', .15)),
            'unlock': concat(*[T(f, .09, 'square', .25) for f in (392, 523, 659, 784, 1047)]),
            'cast': T(500, .15, 'sine', .3, slide=700),
            'raise': layer(T(80, .7, 'saw', .35, slide=260), T(0, .6, 'noise', .18), T(200, .7, 'sine', .3, slide=500)),
            'howl': layer(T(320, .8, 'sine', .35, slide=260), T(330, .8, 'sine', .2, slide=240)),
            'roar': layer(T(110, .7, 'saw', .5, slide=-70), T(0, .7, 'noise', .3, decay=1.0)),
            'screech': T(1900, .3, 'square', .16, slide=-2800),
            'bite': layer(T(0, .08, 'noise', .3), T(260, .08, 'square', .22, slide=-1500)),
            'summon': concat(T(300, .35, 'tri', .35, slide=800), *[T(f, .05, 'sine', .25) for f in (1300, 1700, 2100)]),
            'drain': T(600, .4, 'sine', .3, slide=-400),
            'levelup2': concat(*[T(f, .12, 'square', .22) for f in (392, 494, 587, 784)], T(988, .25, 'square', .22),
                               T(1175, .5, 'sine', .3)),
            'boss': layer(T(60, 1.0, 'saw', .5, slide=20), T(0, 1.0, 'noise', .15)),
        }
        for k, v in d.items():
            self.sfx[k] = self._to_sound(v)

    def _build_music(self):
        """A spooky little looping tune in A minor, built from 3 'instruments'."""
        try:
            beat = 0.28
            bars = 8
            step = int(RATE * beat)
            total = step * 8 * bars
            buf = [0.0] * total
            cache = {}

            def note(m, dur, kind, vol, decay=1.5):
                key = (m, dur, kind, vol)
                if key not in cache:
                    cache[key] = tone(midi(m), dur, kind, vol, decay=decay)
                return cache[key]

            def add(samples, start):
                end = min(total, start + len(samples))
                for i in range(end - start):
                    buf[start + i] += samples[i]

            bass = [45, 41, 48, 43]
            chords = [[57, 60, 64], [53, 57, 60], [60, 64, 67], [55, 59, 62]]
            pent = [69, 72, 74, 76, 79, 81]
            rng = random.Random(11)
            for bar in range(bars):
                ch, b = chords[bar % 4], bass[bar % 4]
                for k in range(8):
                    start = (bar * 8 + k) * step
                    if k % 2 == 0:
                        add(note(b, beat * 1.8, 'tri', .45, 1.0), start)
                    add(note(ch[[0, 1, 2, 1, 0, 1, 2, 1][k]] + 12, beat * .9, 'square', .06), start)
                    if k % 2 == 1:
                        add(tone(0, .04, 'noise', .04), start)
                for q in range(4):
                    if bar >= 2 and rng.random() < 0.6:
                        add(note(rng.choice(pent), beat * 1.8, 'sine', .15, 1.0), (bar * 8 + q * 2) * step)
            self.music = self._to_sound(buf, 0.7)
            self._music_ready = True
        except Exception as e:
            print("Music failed:", e)

    def update(self):
        if self.enabled and self._music_ready and self.channel is None:
            self.channel = self.music.play(loops=-1)
            if self.channel:
                self.channel.set_volume(0.0 if self.muted else 0.35)

    def play(self, name):
        if self.enabled and not self.muted and name in self.sfx:
            self.sfx[name].play()

    def toggle_mute(self):
        self.muted = not self.muted
        if self.channel:
            self.channel.set_volume(0.0 if self.muted else 0.35)

    def stop(self):
        if self.enabled:
            pygame.mixer.stop()
