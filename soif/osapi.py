"""Choisit l'implémentation du système : winapi (Windows) ou x11api (Linux, expérimental)."""
import sys

if sys.platform == "win32":
    from .winapi import *  # noqa: F401,F403
    from .winapi import HAS_HOTKEY, HAS_IDLE, IS_WIN  # noqa: F401
else:
    from .x11api import *  # noqa: F401,F403
    from .x11api import HAS_HOTKEY, HAS_IDLE, IS_WIN  # noqa: F401
