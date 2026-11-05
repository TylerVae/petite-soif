"""Génère assets/icon.ico (icône de l'exe) à partir du dessin vectoriel de la fleur."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QGuiApplication, QImage, QPainter  # noqa: E402

from soif import painter as art  # noqa: E402

app = QGuiApplication(sys.argv)
img = QImage(256, 256, QImage.Format_ARGB32)
img.fill(Qt.transparent)
p = QPainter(img)
p.setRenderHint(QPainter.Antialiasing)
sc = 248 / 142
p.translate((256 - art.BODY_W * sc) / 2, 4 + 10 * sc)
p.scale(sc, sc)
art.draw_body(p, 0.0)
p.end()
out = ROOT / "assets" / "icon.ico"
out.parent.mkdir(exist_ok=True)
assert img.save(str(out)), "échec export .ico"
img.save(str(ROOT / "assets" / "icon.png"))
print(out)
