"""Configuration : chemins, valeurs par défaut, lecture/écriture de config.json."""
import copy
import json
import os
import sys
from pathlib import Path

__version__ = "1.0.0"  # garder aligné avec le tag git (v1.0.0)

FROZEN = getattr(sys, "frozen", False)  # True quand on tourne depuis le .exe
# Dossier du code (ou du .exe). Il ne contient JAMAIS de données personnelles.
APP_DIR = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent.parent
ENTRY_SCRIPT = APP_DIR / "petite_soif.pyw"


def _user_dir():
    if sys.platform == "win32" and os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / "PetiteSoif"
    return Path.home() / ".petite_soif"


# Toutes les données vivent dans %APPDATA%\PetiteSoif\ (hors du dossier du code / du repo)
USER_DIR = _user_dir()
CONFIG_PATH = USER_DIR / "config.json"
DATA_DIR = USER_DIR / "donnees"
SOUNDS_DIR = USER_DIR / "sons"
DB_PATH = DATA_DIR / "petite_soif.db"
LOG_PATH = DATA_DIR / "erreurs.log"



DEFAULTS = {
    "rappels_minutes": {"soif_1": 20, "soif_2": 30, "soif_3": 40, "repetition": 1},
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
}

HELP = {
    "rappels_minutes": "Minutes sans boire avant chaque niveau de soif. 'repetition' = intervalle entre les rappels après le niveau 3 (uniquement si tu as touché souris/clavier depuis le dernier).",
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


def _write(data):
    CONFIG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def is_first_run():
    return not CONFIG_PATH.exists()


def load():
    """Retourne (config, erreur_ou_None)."""
    USER_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        data = {"_aide": HELP}
        data.update(copy.deepcopy(DEFAULTS))
        _write(data)
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
        return _merge(DEFAULTS, raw), None
    except Exception as exc:  # JSON invalide : on garde les défauts
        return copy.deepcopy(DEFAULTS), str(exc)


def save_key(key, value):
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        raw = {}
    raw[key] = value
    _write(raw)
