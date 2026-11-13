"""
main.py - DOUBLE-CLICK or run this file to play!

    python main.py

If the 'pygame' toolbox is missing, this file will try to install it for you.
"""
import os
import subprocess
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())


def ensure_pygame():
    try:
        import pygame  # noqa: F401
        return
    except ImportError:
        pass
    print("pygame (the game toolbox) is missing. Installing it now, please wait...")
    pip = [sys.executable, "-m", "pip", "install"]
    names = ["pygame-ce", "pygame"] if sys.version_info >= (3, 13) else ["pygame", "pygame-ce"]
    attempts = []
    for name in names:                          # newest Pythons need 'pygame-ce'
        attempts += [pip + [name], pip + ["--user", name], pip + ["--break-system-packages", name]]
    for cmd in attempts:
        try:
            subprocess.check_call(cmd)
            import importlib
            importlib.invalidate_caches()
            import pygame  # noqa: F401
            return
        except Exception:
            continue
    print("\nCould not install pygame automatically.")
    print("Please open a terminal and type:   pip install pygame")
    input("Press ENTER to close...")
    sys.exit(1)


if __name__ == "__main__":
    ensure_pygame()
    from game import Game
    Game().run()
