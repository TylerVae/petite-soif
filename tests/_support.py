"""Environnement commun des tests : Qt hors écran, données dans un dossier temporaire (jamais les vraies données)."""
import os
import sys
import tempfile
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["APPDATA"] = tempfile.mkdtemp(prefix="petite_soif_test_")  # doit précéder tout import de soif.config
os.environ["XDG_CONFIG_HOME"] = os.environ["APPDATA"]  # idem sous Linux
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication.instance() or QApplication([])
