"""Génère l'image d'aperçu social GitHub (1280 x 640) : docs/petite_soif_v<version>_cover.png.

Lit la version dans soif/config.py. À téléverser à la main : Settings > Social preview.
Usage : .venv\\Scripts\\python tools\\make_social.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QPointF, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QLinearGradient, QPainter  # noqa: E402

from soif import painter as art  # noqa: E402
from soif.config import __version__  # noqa: E402

app = QGuiApplication(sys.argv)
W, H = 1280, 640
img = QImage(W, H, QImage.Format_RGB32)
p = QPainter(img)
p.setRenderHint(QPainter.Antialiasing)
g = QLinearGradient(0, 0, 0, H)
g.setColorAt(0, QColor("#FDF8F1"))
g.setColorAt(1, QColor("#F6E9D9"))
p.fillRect(img.rect(), g)

# trois fleurs : assoiffée -> en train de boire -> heureuse
for x, thirst, kw, sc in ((70, 3.0, {}, 2.1), (300, 0.0, {"drinking": True}, 2.6), (560, 0.0, {}, 2.1)):
    p.save()
    p.translate(x, H - 70 - art.BODY_H * sc)
    p.scale(sc, sc)
    art.draw_body(p, thirst, **kw)
    if thirst >= 3:
        art.draw_thought_bubble(p)
    p.restore()

# gouttes au-dessus de la fleur du milieu
p.setPen(Qt.NoPen)
p.setBrush(QColor(90, 175, 235, 220))
for dx, dy in ((-25, 150), (5, 115), (30, 160)):
    p.drawEllipse(QPointF(300 + 50 * 2.6 + dx, dy + 40), 6, 11)


def text(s, rect, size, color, bold=True, family="Segoe UI", align=Qt.AlignLeft | Qt.TextWordWrap):
    f = QFont(family)
    f.setPixelSize(size)
    f.setBold(bold)
    p.setFont(f)
    p.setPen(QColor(color))
    p.drawText(rect, align, s)


text("Petite Soif", QRectF(820, 170, 440, 340), 84, "#4A2E24")
text("La petite fleur de ton bureau qui a soif quand tu oublies de boire.", QRectF(820, 290, 440, 130), 32, "#7A4A34", False)
text("Windows · gratuit · open source", QRectF(820, 460, 440, 100), 24, "#3A95D8")

# version en haut à droite
pill = QRectF(W - 186, 32, 146, 54)
p.setPen(Qt.NoPen)
p.setBrush(QColor(201, 101, 60, 38))
p.drawRoundedRect(pill, 27, 27)
text(f"v{__version__}", pill, 30, "#A9532F", align=Qt.AlignCenter)

# signature en bas à droite
text("\U0001F6E1️ Tyler / Ben", QRectF(W - 440, H - 86, 400, 50), 32, "#8A6450", False,
     "Segoe UI Emoji", Qt.AlignRight | Qt.AlignVCenter)
p.end()

out = ROOT / "docs" / f"petite_soif_v{__version__}_cover.png"
assert img.save(str(out)), "échec export"
print(out)
