"""Configuration : chemins, valeurs par défaut, lecture/écriture de config.json."""
import copy
import json
import os
import sys
from pathlib import Path

__version__ = "2.0.0"  # garder aligné avec le tag git (v2.0.0, posé à la fusion dans main)

FROZEN = getattr(sys, "frozen", False)  # True quand on tourne depuis le .exe
# Dossier du code (ou du .exe). Il ne contient JAMAIS de données personnelles.
APP_DIR = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent.parent
ENTRY_SCRIPT = APP_DIR / "petite_soif.pyw"
# Fichiers livrés avec l'appli (polices) : _internal/ dans le .exe, dossier du code sinon
RES_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
FONTS_DIR = RES_DIR / "assets" / "fonts"  # Baloo2.ttf (titres)
REPO_URL = "https://github.com/TylerVae/petite-soif"


def _user_dir():
    if sys.platform == "win32" and os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / "PetiteSoif"
    if sys.platform.startswith("linux"):  # XDG : ~/.config/PetiteSoif, jamais dans le dossier du code
        return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "PetiteSoif"
    return Path.home() / ".petite_soif"


# Polices : Segoe UI et son emoji sous Windows ; sous Linux, les polices courantes des distributions
WIN = sys.platform == "win32"
BODY_FONT = "Segoe UI" if WIN else "Noto Sans"
EMOJI_FONT = "Segoe UI Emoji" if WIN else "Noto Color Emoji"
FONT_FALLBACK = "'Segoe UI', 'Noto Sans', 'DejaVu Sans', 'Ubuntu', sans-serif"  # liste CSS (feuilles de style Qt)


# Toutes les données vivent dans %APPDATA%\PetiteSoif\ (Linux : ~/.config/PetiteSoif/) (hors du dossier du code / du repo)
USER_DIR = _user_dir()
CONFIG_PATH = USER_DIR / "config.json"
DATA_DIR = USER_DIR / "donnees"
SOUNDS_DIR = USER_DIR / "sons"
DB_PATH = DATA_DIR / "petite_soif.db"
LOG_PATH = DATA_DIR / "erreurs.log"

DEFAULTS = {
    "rappels_minutes": {"soif_1": 20, "soif_2": 30, "soif_3": 40, "repetition": 1},
    "insistance": "normale",
    "absence_minutes": 3,
    "poursuite_secondes": 5,
    "appui_long_ms": 800,
    "decalage_curseur_px": 40,
    "verre_cl": 50,
    "objectif_cl": 300,
    "heure_reset": 6,
    "reset_timer_au_lancement": True,
    "raccourci_recuperer": "ctrl+alt+f1",
    "volume": 0.6,
    "echelle": 1.0,
    "demarrage_windows": False,
    "ne_pas_deranger_minutes": [30, 60, 120],
    "langue": "fr",
    "plante": "classique",
    "tout_debloque": False,
}

HELP = {
    "rappels_minutes": "Minutes sans boire avant chaque niveau de soif. 'repetition' = intervalle entre les rappels après le niveau 3 (uniquement si tu as touché souris/clavier depuis le dernier).",
    "insistance": "Après le niveau 3 : 'douce' (un rappel toutes les 5 min, elle reste à sa place), 'normale' (rappel chaque 'repetition', poursuite de 'poursuite_secondes'), 'tenace' (poursuite deux fois plus longue, en tournant autour du curseur).",
    "absence_minutes": "Sans activité clavier/souris pendant ce temps, tu es considéré absent. Au niveau 3, la fleur vient alors t'attendre près du curseur.",
    "poursuite_secondes": "Durée pendant laquelle la fleur suit la souris avant de revenir.",
    "appui_long_ms": "Durée du clic long pour valider une gorgée.",
    "decalage_curseur_px": "Distance entre le curseur et la fleur quand elle te suit.",
    "verre_cl": "Volume ajouté par le bouton du popup.",
    "objectif_cl": "Objectif quotidien en cl (300 = 3 L).",
    "heure_reset": "Heure de début d'une 'journée' (compteur + timer remis à zéro).",
    "reset_timer_au_lancement": "true = le timer repart de zéro quand l'appli démarre (évite une fleur desséchée au boot).",
    "raccourci_recuperer": "Raccourci global pour ramener la fleur sur l'écran principal. Ex : ctrl+alt+f1, ctrl+shift+alt+h.",
    "volume": "0.0 à 1.0",
    "echelle": "Taille de la fleur (1.0 = normale, 1.5 = plus grande).",
    "demarrage_windows": "Lancer automatiquement au démarrage de Windows (aussi réglable dans le menu de l'icône).",
    "ne_pas_deranger_minutes": "Durées proposées dans le menu 'Ne pas déranger'.",
    "langue": "'fr' ou 'en' (aussi réglable dans Paramètres).",
    "plante": "'classique', ou 'plante_2' à 'plante_11' une fois débloquées ; le choix se fait dans Paramètres → Ma plante.",
    "tout_debloque": "true : toutes les plantes sont disponibles, sans XP (Paramètres → Ma plante).",
}


def _merge(base, over):
    out = copy.deepcopy(base)
    for key, value in over.items():
        if key.startswith("_"):
            continue
        if isinstance(out.get(key), dict) and isinstance(value, dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def _num(lo, hi, kind=float):
    def ok(v, default):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return default
        return kind(min(hi, max(lo, v)))
    return ok


_BOUNDS = {  # clé -> (min, max, type) : une valeur hors limites est ramenée dans les limites, un type faux revient au défaut
    "absence_minutes": (1, 120, int), "poursuite_secondes": (0, 60, int), "appui_long_ms": (200, 3000, int),
    "decalage_curseur_px": (0, 300, int), "verre_cl": (5, 200, int), "objectif_cl": (50, 2000, int),
    "heure_reset": (0, 23, int), "volume": (0.0, 1.0, float), "echelle": (0.5, 3.0, float),
}
_CHOICES = {"insistance": ("douce", "normale", "tenace"), "langue": ("fr", "en")}


def sanitize(cfg):
    """Remet au défaut (ou dans les limites) toute valeur de config.json qui ferait planter ou dérailler l'appli."""
    out = cfg
    for key, (lo, hi, kind) in _BOUNDS.items():
        out[key] = _num(lo, hi, kind)(out.get(key), DEFAULTS[key])
    for key, allowed in _CHOICES.items():
        if out.get(key) not in allowed:
            out[key] = DEFAULTS[key]
    for key in ("reset_timer_au_lancement", "demarrage_windows", "tout_debloque"):
        if not isinstance(out.get(key), bool):
            out[key] = DEFAULTS[key]
    for key in ("raccourci_recuperer", "plante"):
        if not isinstance(out.get(key), str) or not out[key].strip():
            out[key] = DEFAULTS[key]
    r, d = out.get("rappels_minutes"), DEFAULTS["rappels_minutes"]
    if (not isinstance(r, dict) or any(isinstance(r.get(k), bool) or not isinstance(r.get(k), (int, float)) or r[k] < 1 for k in d)
            or not r["soif_1"] < r["soif_2"] < r["soif_3"]):
        out["rappels_minutes"] = copy.deepcopy(d)
    n = out.get("ne_pas_deranger_minutes")
    if not isinstance(n, list) or not n or any(isinstance(m, bool) or not isinstance(m, int) or m < 1 for m in n):
        out["ne_pas_deranger_minutes"] = list(DEFAULTS["ne_pas_deranger_minutes"])
    return out


def _write(data):
    CONFIG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def is_first_run():
    return not CONFIG_PATH.exists()


def has_key(key):
    """La clé est-elle écrite dans config.json ? (absente = fichier d'une version plus ancienne)"""
    try:
        return key in json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return False


def load():
    """Retourne (config, erreur_ou_None)."""
    USER_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        data = {"_aide": HELP}
        data.update(copy.deepcopy(DEFAULTS))
        _write(data)
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
        return sanitize(_merge(DEFAULTS, raw)), None
    except Exception as exc:  # JSON invalide : on garde les défauts
        return copy.deepcopy(DEFAULTS), str(exc)


def save(values):
    """Écrit seulement les clés données dans config.json (le reste du fichier est conservé)."""
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        raw = {}
    raw.update(values)
    _write(raw)


def save_key(key, value):
    save({key: value})


def reset_defaults(keep=("demarrage_windows",)):
    save({k: copy.deepcopy(v) for k, v in DEFAULTS.items() if k not in keep})
