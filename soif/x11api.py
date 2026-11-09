"""Équivalent Linux (X11) de winapi.py. EXPÉRIMENTAL : jamais testé sous Windows, voir docs/LINUX.md.

Même interface que winapi.py. Aucune dépendance Python en plus : libX11 et libXss sont chargées
avec ctypes si elles sont présentes ; sinon l'appli se rabat sur la souris seule (HAS_IDLE = False).
"""
import ctypes
import ctypes.util
import os
import subprocess
import sys
from pathlib import Path

IS_WIN = False
HAS_HOTKEY = False  # raccourci global : pas encore implémenté sous Linux (le menu de l'icône fait le travail)
_LINUX = sys.platform.startswith("linux")


# --- inactivité (libXss) ----------------------------------------------------
class _XssInfo(ctypes.Structure):
    _fields_ = [("window", ctypes.c_ulong), ("state", ctypes.c_int), ("kind", ctypes.c_int),
                ("til_or_since", ctypes.c_ulong), ("idle", ctypes.c_ulong), ("event_mask", ctypes.c_ulong)]


_x11 = _xss = _dpy = _root = _info = None


def _init_idle():
    """Charge libX11/libXss et ouvre une connexion X. Retourne False si quelque chose manque."""
    global _x11, _xss, _dpy, _root, _info
    if not _LINUX or not os.environ.get("DISPLAY"):
        return False
    if os.environ.get("XDG_SESSION_TYPE") == "wayland":
        return False  # sous XWayland, libXss ne voit que les saisies faites dans les fenêtres X : valeur trompeuse
    try:
        _x11 = ctypes.CDLL(ctypes.util.find_library("X11") or "libX11.so.6")
        _xss = ctypes.CDLL(ctypes.util.find_library("Xss") or "libXss.so.1")
        _x11.XOpenDisplay.restype = ctypes.c_void_p
        _x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        _x11.XDefaultRootWindow.restype = ctypes.c_ulong
        _x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        _xss.XScreenSaverAllocInfo.restype = ctypes.POINTER(_XssInfo)
        _xss.XScreenSaverQueryInfo.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(_XssInfo)]
        _xss.XScreenSaverQueryInfo.restype = ctypes.c_int
        _dpy = _x11.XOpenDisplay(None)
        if not _dpy:
            return False
        _root = _x11.XDefaultRootWindow(_dpy)
        _info = _xss.XScreenSaverAllocInfo()
        return bool(_info) and idle_seconds() is not None
    except Exception:
        return False


def idle_seconds():
    """Secondes depuis la dernière saisie clavier OU souris (None si libXss est indisponible)."""
    if not _dpy or not _info:
        return None
    try:
        if not _xss.XScreenSaverQueryInfo(_dpy, _root, _info):
            return None
        return _info.contents.idle / 1000.0
    except Exception:
        return None


HAS_IDLE = _init_idle()


# --- raccourci global (non implémenté) --------------------------------------
def pretty_hotkey(text):
    return "+".join(p.strip().capitalize() if len(p.strip()) > 2 else p.strip().upper() for p in text.split("+"))


class GlobalHotkey:
    """Coquille vide : register() renvoie toujours False."""

    def __init__(self, callback):
        self.callback = callback
        self.registered = False

    def register(self, text, hwnd):
        return False

    def unregister(self):
        pass


# --- premier plan -----------------------------------------------------------
# Le flag Qt WindowStaysOnTopHint (flower.py) suffit sous X11 (_NET_WM_STATE_ABOVE) ; rien à répéter chaque seconde.
def make_overlay(hwnd):
    pass


def force_topmost(hwnd):
    pass


# --- démarrage de la session ------------------------------------------------
def _autostart_file():
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "autostart" / "petite-soif.desktop"


def _quote(arg):
    """Guillemets du champ Exec= (spécification Desktop Entry : doubles guillemets, \ " ` $ échappés ; % doublé)."""
    for ch in ("\\", '"', "`", "$"):
        arg = arg.replace(ch, "\\" + ch)
    return '"' + arg.replace("%", "%%") + '"'


def _exec_line(script):
    if getattr(sys, "frozen", False):
        args = [str(Path(sys.executable).resolve())]
    else:
        args = [sys.executable, str(script)]
    return " ".join(_quote(a) for a in args)


def desktop_entry(script):
    return ("[Desktop Entry]\nType=Application\nName=Petite Soif\n"
            "Comment=Rappel pour boire de l'eau\n"
            f"Exec={_exec_line(script)}\nTerminal=false\nX-GNOME-Autostart-enabled=true\n")


def set_autostart(enabled, script):
    path = _autostart_file()
    if enabled:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(desktop_entry(script), encoding="utf-8")
    else:
        path.unlink(missing_ok=True)
    return True


# --- divers -----------------------------------------------------------------
def clean_env():
    """Environnement pour lancer un programme du système (paplay, xdg-open…) depuis l'appli PyInstaller :
    sans LD_LIBRARY_PATH de l'appli, qui ferait charger nos bibliothèques à la place de celles du système."""
    env = dict(os.environ)
    if getattr(sys, "frozen", False):
        orig = env.pop("LD_LIBRARY_PATH_ORIG", None)
        env.pop("LD_LIBRARY_PATH", None)
        if orig is not None:
            env["LD_LIBRARY_PATH"] = orig
    return env


def open_path(path):
    subprocess.Popen(["xdg-open", str(path)], env=clean_env())
