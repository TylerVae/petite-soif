"""Appels Windows : inactivité clavier/souris, raccourci global, lancement au démarrage."""
import ctypes
import os
import re
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QAbstractNativeEventFilter

IS_WIN = sys.platform == "win32"
HAS_IDLE = True  # idle_seconds() est fiable (GetLastInputInfo)
HAS_HOTKEY = True
if IS_WIN:
    import ctypes.wintypes as wt


# --- inactivité -----------------------------------------------------------
def idle_seconds():
    """Secondes depuis la dernière saisie clavier OU souris (None hors Windows)."""
    if not IS_WIN:
        return None

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(lii)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        return None
    now = ctypes.windll.kernel32.GetTickCount() & 0xFFFFFFFF
    return ((now - lii.dwTime) & 0xFFFFFFFF) / 1000.0


# --- raccourci global -----------------------------------------------------
_MODS = {"ctrl": 0x2, "control": 0x2, "alt": 0x1, "shift": 0x4, "win": 0x8}
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312


def parse_hotkey(text):
    mods, vk = 0, None
    for part in [p.strip().lower() for p in text.split("+") if p.strip()]:
        if part in _MODS:
            mods |= _MODS[part]
        elif re.fullmatch(r"f([1-9]|1[0-9]|2[0-4])", part):
            vk = 0x6F + int(part[1:])
        elif len(part) == 1 and part.isalnum():
            vk = ord(part.upper())
        else:
            raise ValueError(f"Touche inconnue : {part}")
    if vk is None:
        raise ValueError("Aucune touche principale dans le raccourci")
    return mods, vk


def pretty_hotkey(text):
    return "+".join(p.strip().capitalize() if len(p.strip()) > 2 else p.strip().upper() for p in text.split("+"))


class GlobalHotkey(QAbstractNativeEventFilter):
    ID = 0x5A1F

    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.registered = False
        self.hwnd = None

    def register(self, text, hwnd):
        if not IS_WIN:
            return False
        self.unregister()
        try:
            mods, vk = parse_hotkey(text)
        except ValueError:
            return False
        self.hwnd = hwnd
        ok = ctypes.windll.user32.RegisterHotKey(wt.HWND(hwnd), self.ID, mods | MOD_NOREPEAT, vk)
        self.registered = bool(ok)
        return self.registered

    def unregister(self):
        if IS_WIN and self.registered:
            ctypes.windll.user32.UnregisterHotKey(wt.HWND(self.hwnd), self.ID)
        self.registered = False

    def nativeEventFilter(self, event_type, message):
        try:
            et = event_type.data() if hasattr(event_type, "data") else bytes(event_type)
            if et == b"windows_generic_MSG":
                msg = wt.MSG.from_address(int(message))
                if msg.message == WM_HOTKEY and msg.wParam == self.ID:
                    self.callback()
        except Exception:
            pass
        return False, 0


# --- premier plan ---------------------------------------------------------
_HWND_TOPMOST = -1
_SWP_FLAGS = 0x0001 | 0x0002 | 0x0010 | 0x0200 | 0x0400  # NOSIZE|NOMOVE|NOACTIVATE|NOOWNERZORDER|NOSENDCHANGING
_GWL_EXSTYLE = -20
_WS_EX_TOPMOST = 0x00000008
_WS_EX_TOOLWINDOW = 0x00000080
_WS_EX_NOACTIVATE = 0x08000000

if IS_WIN:
    _user32 = ctypes.windll.user32
    _user32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    _user32.SetWindowPos.restype = wt.BOOL
    _user32.GetWindowLongPtrW.argtypes = [wt.HWND, ctypes.c_int]
    _user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    _user32.SetWindowLongPtrW.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_ssize_t]
    _user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t


def make_overlay(hwnd):
    """Style natif : fenêtre outil, jamais activée, toujours au premier plan."""
    if not IS_WIN:
        return
    ex = _user32.GetWindowLongPtrW(wt.HWND(hwnd), _GWL_EXSTYLE)
    _user32.SetWindowLongPtrW(wt.HWND(hwnd), _GWL_EXSTYLE, ex | _WS_EX_TOOLWINDOW | _WS_EX_NOACTIVATE)
    force_topmost(hwnd)


def force_topmost(hwnd):
    """Remet la fenêtre en tête de la couche 'topmost', sans voler le focus."""
    if not IS_WIN:
        return
    _user32.SetWindowPos(wt.HWND(hwnd), wt.HWND(_HWND_TOPMOST), 0, 0, 0, 0, _SWP_FLAGS)


# --- démarrage de Windows -------------------------------------------------
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_RUN_NAME = "PetiteSoif"


def _command(script):
    if getattr(sys, "frozen", False):  # version .exe : on lance l'exe lui-même
        return f'"{Path(sys.executable).resolve()}"'
    exe = Path(sys.executable)
    pyw = exe.with_name("pythonw.exe")
    if pyw.exists():
        exe = pyw
    return f'"{exe}" "{script}"'


def set_autostart(enabled, script):
    if not IS_WIN:
        return False
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, _RUN_NAME, 0, winreg.REG_SZ, _command(script))
        else:
            try:
                winreg.DeleteValue(key, _RUN_NAME)
            except FileNotFoundError:
                pass
    return True


def open_path(path):
    if IS_WIN:
        os.startfile(str(path))
    else:
        subprocess.Popen(["xdg-open", str(path)])
