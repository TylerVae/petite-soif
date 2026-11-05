"""Petite Soif — double-clique ce fichier pour lancer l'appli (sans console)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from soif.main import run  # noqa: E402

if __name__ == "__main__":
    run()
