"""inputs.py - keyboard + PlayStation controller input, and controls you can change.

How it works (like I'm 10): the game never asks "was the SPACE key pressed?".
It asks "did the player want to ATTACK?". This file connects the two. The keyboard keys and
controller buttons that mean "attack" are kept in a list, and you can change that list in the
Controls menu. Your choices are saved in a small file called controls.json."""
import json
import math
import os

import pygame

# Make the PS5 DualSense behave (rumble on, and keep working if the window isn't focused).
os.environ.setdefault("SDL_JOYSTICK_HIDAPI_PS5_RUMBLE", "1")
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")

V2 = pygame.Vector2

# ====================================================================== the list of things you can DO
GAME_ACTIONS = ['move_up', 'move_down', 'move_left', 'move_right', 'attack', 'ability1', 'ability2',
                'ability3', 'ultimate', 'dash', 'interact', 'stats', 'pause', 'mute']

ACTION_LABELS = {
    'move_up': 'Move Up', 'move_down': 'Move Down', 'move_left': 'Move Left', 'move_right': 'Move Right',
    'attack': 'Attack', 'ability1': 'Ability 1', 'ability2': 'Ability 2', 'ability3': 'Ability 3',
    'ultimate': 'Ultimate',
    'dash': 'Dash', 'interact': 'Stairs / Interact', 'stats': 'Hero Stats (hold)',
    'pause': 'Pause', 'mute': 'Mute Sound',
}
# on the controller the LEFT STICK always moves you (the D-Pad can too), so no stick rows are needed
PAD_ACTIONS = [a for a in GAME_ACTIONS if not a.startswith('move_')]

DEFAULT_KB = {
    'move_up': [pygame.K_w, pygame.K_UP], 'move_down': [pygame.K_s, pygame.K_DOWN],
    'move_left': [pygame.K_a, pygame.K_LEFT], 'move_right': [pygame.K_d, pygame.K_RIGHT],
    'attack': [pygame.K_SPACE], 'ability1': [pygame.K_1], 'ability2': [pygame.K_2], 'ability3': [pygame.K_3],
    'ultimate': [pygame.K_r], 'dash': [pygame.K_LSHIFT, pygame.K_RSHIFT], 'interact': [pygame.K_e],
    'stats': [pygame.K_TAB], 'pause': [pygame.K_ESCAPE, pygame.K_p], 'mute': [pygame.K_m],
}
# PLAYER 2's keys in Duo (the right-hand side of the keyboard: arrows + the keys next to them, or the numpad)
DEFAULT_KB2 = {
    'move_up': [pygame.K_UP], 'move_down': [pygame.K_DOWN], 'move_left': [pygame.K_LEFT], 'move_right': [pygame.K_RIGHT],
    'attack': [pygame.K_RCTRL, pygame.K_KP0], 'ability1': [pygame.K_COMMA, pygame.K_KP1],
    'ability2': [pygame.K_PERIOD, pygame.K_KP2], 'ability3': [pygame.K_SLASH, pygame.K_KP3],
    'ultimate': [pygame.K_SEMICOLON, pygame.K_KP4], 'dash': [pygame.K_RSHIFT, pygame.K_KP_ENTER],
    'interact': [pygame.K_RETURN, pygame.K_KP5], 'stats': [pygame.K_QUOTE, pygame.K_KP6], 'pause': [pygame.K_BACKSPACE],
    'mute': [],
}
# Controller names follow SDL: a=Cross, b=Circle, x=Square, y=Triangle, lt/rt = L2/R2, ...
DEFAULT_PAD = {
    'move_up': ['dpup'], 'move_down': ['dpdown'], 'move_left': ['dpleft'], 'move_right': ['dpright'],
    'attack': ['rt', 'x'], 'ability1': ['leftshoulder'], 'ability2': ['rightshoulder'], 'ability3': ['lt'],
    'ultimate': ['b'], 'dash': ['a'], 'interact': ['y'], 'stats': ['back', 'touchpad'],
    'pause': ['start'], 'mute': [],
}
DEFAULT_SETTINGS = {'deadzone': 0.22, 'vibration': True, 'stick_aims': True, 'stick_attack': True, 'aim_assist': True}

SDL_BUTTONS = ['a', 'b', 'x', 'y', 'back', 'guide', 'start', 'leftstick', 'rightstick', 'leftshoulder',
               'rightshoulder', 'dpup', 'dpdown', 'dpleft', 'dpright', 'misc1', 'paddle1', 'paddle2',
               'paddle3', 'paddle4', 'touchpad']
PAD_LABELS = {'a': 'Cross', 'b': 'Circle', 'x': 'Square', 'y': 'Triangle', 'back': 'Create', 'guide': 'PS Button',
              'start': 'Options', 'leftstick': 'L3', 'rightstick': 'R3', 'leftshoulder': 'L1',
              'rightshoulder': 'R1', 'lt': 'L2', 'rt': 'R2', 'dpup': 'D-Pad Up', 'dpdown': 'D-Pad Down',
              'dpleft': 'D-Pad Left', 'dpright': 'D-Pad Right', 'misc1': 'Mic', 'touchpad': 'Touchpad'}

# fixed keys / buttons used to move around the MENUS
KEY_NAV = {pygame.K_UP: 'up', pygame.K_w: 'up', pygame.K_DOWN: 'down', pygame.K_s: 'down',
           pygame.K_LEFT: 'left', pygame.K_a: 'left', pygame.K_RIGHT: 'right', pygame.K_d: 'right',
           pygame.K_RETURN: 'confirm', pygame.K_KP_ENTER: 'confirm', pygame.K_SPACE: 'confirm',
           pygame.K_ESCAPE: 'back', pygame.K_TAB: 'tab_next', pygame.K_q: 'tab_prev', pygame.K_e: 'tab_next',
           pygame.K_r: 'reset'}
PAD_NAV = {'a': 'confirm', 'b': 'back', 'leftshoulder': 'tab_prev', 'rightshoulder': 'tab_next', 'y': 'reset'}

_ADD = {getattr(pygame, n) for n in ('CONTROLLERDEVICEADDED', 'JOYDEVICEADDED') if hasattr(pygame, n)}
_REM = {getattr(pygame, n) for n in ('CONTROLLERDEVICEREMOVED', 'JOYDEVICEREMOVED') if hasattr(pygame, n)}

_KEY_PRETTY = {'left shift': 'L-Shift', 'right shift': 'R-Shift', 'left ctrl': 'L-Ctrl', 'right ctrl': 'R-Ctrl',
               'left alt': 'L-Alt', 'right alt': 'R-Alt', 'return': 'Enter', 'escape': 'Esc', 'space': 'Space',
               'backspace': 'Backspace', 'keypad enter': 'Num Enter', 'enter': 'Num Enter', 'up': 'Up', 'down': 'Down', 'left': 'Left',
               'right': 'Right', 'tab': 'Tab'}


def key_label(code):
    try:
        n = pygame.key.name(code)
    except Exception:
        n = str(code)
    if n in _KEY_PRETTY:
        return _KEY_PRETTY[n]
    if len(n) == 3 and n[0] == '[' and n[2] == ']':          # numpad keys: "[0]" -> "Num 0"
        return 'Num ' + n[1]
    return n.upper() if len(n) <= 1 else n.title()


def pad_label(name):
    return PAD_LABELS.get(name, name)


# ====================================================================== talking to the real controller
class PadBackend:
    """A thin layer over SDL's game-controller API. It gives every controller the SAME button names,
    so a PS5 DualSense works the same on Windows, Mac and Linux. (Falls back to the raw joystick API.)"""

    def __init__(self, index=0):
        self.index = index            # 0 = the first controller plugged in, 1 = the second (Duo's Player 2)
        self.ctrl = None
        self.joy = None
        self.name = ''
        self._sdlc = None
        try:
            pygame.joystick.init()
        except Exception:
            pass
        try:
            from pygame._sdl2 import controller as sdlc
            sdlc.init()
            self._sdlc = sdlc
        except Exception:
            self._sdlc = None
        self.refresh()

    @property
    def connected(self):
        return self.ctrl is not None or self.joy is not None

    def refresh(self):
        """(Re)connect to the first controller we can find. Called on start and on plug/unplug."""
        if self.ctrl is not None:
            try:
                if not self.ctrl.attached():
                    self.ctrl, self.name = None, ''
            except Exception:
                self.ctrl, self.name = None, ''
        if self.joy is not None and pygame.joystick.get_count() <= self.index:
            self.joy, self.name = None, ''
        if self.connected:
            return
        if self._sdlc is not None:
            try:
                found = [i for i in range(self._sdlc.get_count()) if self._sdlc.is_controller(i)]
                if len(found) > self.index:
                    i = found[self.index]
                    self.ctrl = self._sdlc.Controller(i)
                    nm = getattr(self.ctrl, 'name', None) or self._sdlc.name_forindex(i) or 'Controller'
                    self.name = nm.decode() if isinstance(nm, bytes) else str(nm)
                    return
                if found:
                    return                    # (controllers exist, just not this many)
            except Exception:
                self.ctrl = None
        try:
            if pygame.joystick.get_count() > self.index:
                j = pygame.joystick.Joystick(self.index)
                j.init()
                self.joy, self.name = j, j.get_name()
                return
        except Exception:
            self.joy = None

    @staticmethod
    def _norm(v):
        return v / 32768.0 if isinstance(v, int) else float(v)

    def poll(self):
        """Returns (set of pressed button names, dict of stick/trigger values from -1 to 1)."""
        buttons = set()
        axes = dict(lx=0.0, ly=0.0, rx=0.0, ry=0.0, lt=0.0, rt=0.0)
        try:
            if self.ctrl is not None:
                c = self.ctrl
                if not c.attached():
                    self.ctrl, self.name = None, ''
                    return buttons, axes
                for idx, name in enumerate(SDL_BUTTONS):
                    try:
                        if c.get_button(idx):
                            buttons.add(name)
                    except Exception:
                        pass
                axes['lx'], axes['ly'] = self._norm(c.get_axis(0)), self._norm(c.get_axis(1))
                axes['rx'], axes['ry'] = self._norm(c.get_axis(2)), self._norm(c.get_axis(3))
                axes['lt'], axes['rt'] = max(0.0, self._norm(c.get_axis(4))), max(0.0, self._norm(c.get_axis(5)))
            elif self.joy is not None:
                j = self.joy
                for i in range(min(j.get_numbuttons(), len(SDL_BUTTONS))):
                    if j.get_button(i):
                        buttons.add(SDL_BUTTONS[i])
                if j.get_numhats() > 0:
                    hx, hy = j.get_hat(0)
                    if hy > 0: buttons.add('dpup')
                    if hy < 0: buttons.add('dpdown')
                    if hx < 0: buttons.add('dpleft')
                    if hx > 0: buttons.add('dpright')
                n = j.get_numaxes()
                if n >= 2:
                    axes['lx'], axes['ly'] = j.get_axis(0), j.get_axis(1)
                if n >= 4:
                    axes['rx'], axes['ry'] = j.get_axis(2), j.get_axis(3)
                if n >= 6:
                    axes['lt'], axes['rt'] = (j.get_axis(4) + 1) / 2, (j.get_axis(5) + 1) / 2
        except Exception:
            pass
        return buttons, axes

    def rumble(self, low, high, ms):
        try:
            if self.ctrl is not None:
                self.ctrl.rumble(low, high, ms)
            elif self.joy is not None:
                self.joy.rumble(low, high, ms)
        except Exception:
            pass


def pad_count():
    """How many controllers are plugged in right now."""
    try:
        from pygame._sdl2 import controller as sdlc
        sdlc.init()
        n = sum(1 for i in range(sdlc.get_count()) if sdlc.is_controller(i))
        if n:
            return n
    except Exception:
        pass
    try:
        return pygame.joystick.get_count()
    except Exception:
        return 0


# ====================================================================== the Input manager
class Input:
    def __init__(self, path=None, backend=None, owner=None):
        """`owner` is Player 1's Input when this one is Duo's PLAYER 2: it then uses Player 1's saved
        Player-2 keys, controller layout and settings (one controls.json for both)."""
        self.path = path
        self.kb = {a: list(v) for a, v in DEFAULT_KB.items()}
        self.kb2 = {a: list(v) for a, v in DEFAULT_KB2.items()}      # Duo: Player 2's keys (saved with ours)
        self.pad = {a: list(v) for a, v in DEFAULT_PAD.items()}
        self.settings = dict(DEFAULT_SETTINGS)
        self.load()
        if owner is not None:
            self.kb, self.pad, self.settings = owner.kb2, owner.pad, owner.settings
        self.blocked = set()                # keys this player must ignore (Duo: the other player's keys)
        self.pad_on = True                  # False = this player doesn't use a controller right now
        self.who = ''                       # 'P1' / 'P2' in Duo (for the 'controller connected' notes)
        self._nav_pad = []                  # menu moves that came from THIS player's controller
        self.backend = backend if backend is not None else PadBackend()
        self.device = 'keyboard'            # which one you touched last (used for on-screen button hints)
        self.axes = dict(lx=0.0, ly=0.0, rx=0.0, ry=0.0, lt=0.0, rt=0.0)
        self.capture = None                 # set while we are waiting for you to press a new key/button
        self.messages = []                  # little notes for the game to show ("Controller connected")
        self._pressed, self._held, self._nav = set(), set(), []
        self._pad_now = set()
        self._rep = {}
        self._was_connected = False

    # ---------------------------------------------------------------- saving & loading
    def load(self):
        if not self.path or not os.path.exists(self.path):
            return
        try:
            with open(self.path, 'r') as f:
                data = json.load(f)
            for a, v in data.get('keyboard', {}).items():
                if a in self.kb and isinstance(v, list):
                    self.kb[a] = [int(k) for k in v][:2]
            for a, v in data.get('keyboard2', {}).items():
                if a in self.kb2 and isinstance(v, list):
                    self.kb2[a] = [int(k) for k in v][:2]
            for a, v in data.get('gamepad', {}).items():
                if a in self.pad and isinstance(v, list):
                    self.pad[a] = [str(k) for k in v][:2]
            for k, v in data.get('settings', {}).items():
                if k in self.settings:
                    self.settings[k] = type(DEFAULT_SETTINGS[k])(v)
        except Exception:
            pass          # a broken file just means "use the defaults"

    def save(self):
        if not self.path:
            return
        try:
            with open(self.path, 'w') as f:
                json.dump({'keyboard': self.kb, 'keyboard2': self.kb2, 'gamepad': self.pad, 'settings': self.settings},
                          f, indent=1)
        except Exception:
            pass

    def reset(self, device):
        if device == 'keyboard':
            self.kb = {a: list(v) for a, v in DEFAULT_KB.items()}
        elif device == 'keyboard2':
            self.kb2.clear()
            self.kb2.update({a: list(v) for a, v in DEFAULT_KB2.items()})
        else:
            self.pad = {a: list(v) for a, v in DEFAULT_PAD.items()}
            self.settings = dict(DEFAULT_SETTINGS)
        self.save()

    # ---------------------------------------------------------------- asking "what does the player want?"
    def begin_frame(self):
        self._pressed, self._nav, self._nav_pad = set(), [], []

    def pressed(self, action):
        return action in self._pressed

    def held(self, action):
        return action in self._held

    def nav(self, name):
        return name in self._nav

    @property
    def connected(self):
        return self.pad_on and self.backend.connected

    @property
    def pad_name(self):
        return self.backend.name

    def _stick(self, x, y):
        dz = self.settings['deadzone']
        mag = math.hypot(x, y)
        if mag < dz:
            return V2(0, 0)
        scaled = min(1.0, (mag - dz) / (1 - dz))
        return V2(x / mag * scaled, y / mag * scaled)

    def move_vector(self):
        """Walking direction. Keys/D-Pad give full speed; the left stick is ANALOG (push gently to walk slowly)."""
        v = V2(0, 0)
        if 'move_left' in self._held: v.x -= 1
        if 'move_right' in self._held: v.x += 1
        if 'move_up' in self._held: v.y -= 1
        if 'move_down' in self._held: v.y += 1
        if v.length_squared() > 0:
            v = v.normalize()
        v += self._stick(self.axes['lx'], self.axes['ly'])
        if v.length() > 1:
            v = v.normalize()
        return v

    def aim_vector(self):
        """Direction of the RIGHT stick (or None when it is resting)."""
        if not self.settings['stick_aims']:
            return None
        v = self._stick(self.axes['rx'], self.axes['ry'])
        return v.normalize() if v.length() > 0.35 else None

    def stick_attacking(self):
        if not (self.settings['stick_aims'] and self.settings['stick_attack']):
            return False
        return self._stick(self.axes['rx'], self.axes['ry']).length() > 0.65

    def rumble(self, low, high, ms):
        if self.settings['vibration'] and self.connected:
            self.backend.rumble(low, high, ms)

    # ---------------------------------------------------------------- showing button names on screen
    def labels(self, action, device=None):
        device = device or self.device
        if device == 'keyboard':
            return [key_label(k) for k in self.kb.get(action, [])]
        if device == 'keyboard2':
            return [key_label(k) for k in self.kb2.get(action, [])]
        return [pad_label(c) for c in self.pad.get(action, [])]

    def pad_primary(self, action):
        lst = self.pad.get(action, [])
        return lst[0] if lst else None

    def key_primary(self, action):
        lst = self.kb.get(action, [])
        return key_label(lst[0]) if lst else None

    # ---------------------------------------------------------------- changing the controls
    def start_capture(self, device, action, slot):
        if device == 'gamepad' and not self.connected:
            self.messages.append(("No controller found. See the SETUP tab to connect one.", (255, 140, 120)))
            return False
        self.capture = dict(device=device, action=action, slot=slot, t=7.0, arm=0.25)
        return True

    def cancel_capture(self, note=None):
        self.capture = None
        if note:
            self.messages.append((note, (220, 220, 230)))

    def _table(self, device):
        return {'keyboard': self.kb, 'keyboard2': self.kb2}.get(device, self.pad)

    def _assign(self, device, action, slot, code):
        table = self._table(device)
        shown = pad_label if device == 'gamepad' else key_label
        moved = None
        for a, lst in table.items():                 # a key/button can only do ONE thing
            if a != action and code in lst:
                lst.remove(code)
                moved = a
        lst = table[action]
        if code in lst:
            lst.remove(code)
        slot = min(slot, len(lst))
        lst.insert(slot, code) if slot >= len(lst) else lst.__setitem__(slot, code)
        del lst[2:]
        self.capture = None
        self.save()
        msg = f"{ACTION_LABELS[action]} = {shown(code)}"
        if moved:
            msg += f"   ({shown(code)} was taken from {ACTION_LABELS[moved]})"
        self.messages.append((msg, (170, 255, 190)))

    def _clear_slot(self, device, action, slot):
        table = self._table(device)
        if slot < len(table[action]):
            del table[action][slot]
        self.capture = None
        self.save()
        self.messages.append((f"Cleared {ACTION_LABELS[action]}", (220, 220, 230)))

    # ---------------------------------------------------------------- events from pygame
    def handle_event(self, e):
        """Returns True if this event was 'eaten' (used for rebinding) and the game should ignore it."""
        t = e.type
        if t == pygame.KEYDOWN:
            self.device = 'keyboard'
            cap = self.capture
            if cap:
                if e.key == pygame.K_ESCAPE:
                    self.cancel_capture("Rebinding cancelled")
                elif e.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                    self._clear_slot(cap['device'], cap['action'], cap['slot'])
                elif cap['device'] in ('keyboard', 'keyboard2') and e.key != pygame.K_F11:
                    self._assign(cap['device'], cap['action'], cap['slot'], e.key)
                return True
            if e.key not in self.blocked:
                for act, keys in self.kb.items():
                    if e.key in keys:
                        self._pressed.add(act)
            n = KEY_NAV.get(e.key)
            if n:
                self._nav.append(n)
        elif t == pygame.MOUSEBUTTONDOWN:
            self.device = 'keyboard'
        elif t in _ADD or t in _REM:
            self.backend.refresh()
            self._check_connection()
        return False

    def _check_connection(self):
        c = self.backend.connected
        if c != self._was_connected:
            self._was_connected = c
            who = self.who + " " if self.who else ""
            if c:
                self.messages.append((f"{who}Controller connected: {self.backend.name}", (150, 255, 190)))
            else:
                self.messages.append((f"{who}Controller disconnected", (255, 170, 150)))
                self.device = 'keyboard'

    # ---------------------------------------------------------------- every frame
    def update(self, dt, keys=None):
        keys = keys if keys is not None else pygame.key.get_pressed()
        held = set()
        for act, ks in self.kb.items():
            if any(keys[k] for k in ks if k not in self.blocked):
                held.add(act)

        prev = self._pad_now
        if self.pad_on:
            buttons, axes = self.backend.poll()
        else:
            buttons, axes = set(), dict(lx=0.0, ly=0.0, rx=0.0, ry=0.0, lt=0.0, rt=0.0)
        for name in ('lt', 'rt'):                                    # triggers count as buttons
            v = axes[name]
            if v > 0.55 or (name in prev and v > 0.3):
                buttons.add(name)
        self.axes = axes
        self._pad_now = buttons
        new = buttons - prev
        if new or max(abs(axes['lx']), abs(axes['ly']), abs(axes['rx']), abs(axes['ry'])) > 0.6:
            self.device = 'gamepad'

        cap = self.capture
        if cap:
            cap['t'] -= dt
            cap['arm'] = max(0.0, cap['arm'] - dt)
            if cap['t'] <= 0:
                self.cancel_capture("Rebinding cancelled (nothing was pressed)")
            elif cap['device'] == 'gamepad' and cap['arm'] <= 0 and new:
                self._assign('gamepad', cap['action'], cap['slot'], sorted(new)[0])
        else:
            for act, cs in self.pad.items():
                if any(c in buttons for c in cs):
                    held.add(act)
                if any(c in new for c in cs):
                    self._pressed.add(act)
            for name in new:
                n = PAD_NAV.get(name)
                if n:
                    self._nav.append(n)
                    self._nav_pad.append(n)
            # D-Pad / left stick moving through menus (with key-repeat when held)
            dirs = set()
            if 'dpup' in buttons or axes['ly'] < -0.55: dirs.add('up')
            if 'dpdown' in buttons or axes['ly'] > 0.55: dirs.add('down')
            if 'dpleft' in buttons or axes['lx'] < -0.55: dirs.add('left')
            if 'dpright' in buttons or axes['lx'] > 0.55: dirs.add('right')
            for d in ('up', 'down', 'left', 'right'):
                if d in dirs:
                    t = self._rep.get(d)
                    if t is None:
                        self._nav.append(d)
                        self._nav_pad.append(d)
                        self._rep[d] = 0.4
                    else:
                        t -= dt
                        if t <= 0:
                            self._nav.append(d)
                            self._nav_pad.append(d)
                            t = 0.13
                        self._rep[d] = t
                else:
                    self._rep.pop(d, None)
        self._held = held
        self._check_connection()


# ====================================================================== PlayStation button pictures
def draw_pad_icon(surf, name, cx, cy, size, font):
    """Draw a PlayStation-style button picture centred at (cx, cy). Returns its width."""
    P = pygame.draw
    r = size // 2
    if name in ('a', 'b', 'x', 'y'):
        col = {'a': (110, 165, 255), 'b': (255, 105, 115), 'x': (255, 145, 215), 'y': (110, 235, 165)}[name]
        P.circle(surf, (22, 26, 46), (cx, cy), r)
        P.circle(surf, (125, 135, 175), (cx, cy), r, 2)
        s = max(3, int(r * 0.48))
        if name == 'a':
            P.line(surf, col, (cx - s, cy - s), (cx + s, cy + s), 3)
            P.line(surf, col, (cx - s, cy + s), (cx + s, cy - s), 3)
        elif name == 'b':
            P.circle(surf, col, (cx, cy), s + 1, 3)
        elif name == 'x':
            P.rect(surf, col, (cx - s, cy - s, 2 * s, 2 * s), 3)
        else:
            P.polygon(surf, col, [(cx, cy - s - 1), (cx + s + 1, cy + s), (cx - s - 1, cy + s)], 3)
        return size
    if name.startswith('dp'):
        P.circle(surf, (22, 26, 46), (cx, cy), r)
        arm = max(3, r // 3)
        P.rect(surf, (150, 160, 195), (cx - arm // 2 - 1, cy - r + 3, arm + 2, 2 * r - 6), border_radius=2)
        P.rect(surf, (150, 160, 195), (cx - r + 3, cy - arm // 2 - 1, 2 * r - 6, arm + 2), border_radius=2)
        hot = {'dpup': (cx - arm // 2, cy - r + 3, arm, r - 3), 'dpdown': (cx - arm // 2, cy, arm, r - 3),
               'dpleft': (cx - r + 3, cy - arm // 2, r - 3, arm), 'dpright': (cx, cy - arm // 2, r - 3, arm)}[name]
        P.rect(surf, (255, 215, 90), hot, border_radius=2)
        return size
    text = {'leftshoulder': 'L1', 'rightshoulder': 'R1', 'lt': 'L2', 'rt': 'R2', 'leftstick': 'L3',
            'rightstick': 'R3', 'start': 'OPTIONS', 'back': 'CREATE', 'guide': 'PS', 'touchpad': 'PAD',
            'misc1': 'MIC'}.get(name, name.upper())
    img = font.render(text, True, (235, 238, 255))
    w = max(size, img.get_width() + 14)
    h = int(size * 0.82)
    rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    if name in ('leftstick', 'rightstick'):
        P.circle(surf, (22, 26, 46), (cx, cy), r)
        P.circle(surf, (125, 135, 175), (cx, cy), r, 2)
        w = size
    else:
        P.rect(surf, (22, 26, 46), rect, border_radius=h // 2 if name in ('start', 'back', 'touchpad') else 6)
        P.rect(surf, (125, 135, 175), rect, 2, border_radius=h // 2 if name in ('start', 'back', 'touchpad') else 6)
    surf.blit(img, (cx - img.get_width() // 2, cy - img.get_height() // 2))
    return w
