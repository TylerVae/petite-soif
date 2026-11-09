"""Génère l'image d'aperçu social GitHub (1280 x 640) : docs/petite_soif_v<version>_cover.png.

Design V2 : grand fond bleu, la fleur de départ et des cartes « ? » pour annoncer de nouvelles plantes sans les montrer.
Lit la version dans soif/config.py. À téléverser à la main : Settings > Social preview.
Usage : .venv\\Scripts\\python tools\\make_social.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QPointF, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QLinearGradient, QPainter, QPen  # noqa: E402

from soif import painter as art  # noqa: E402
from soif.config import __version__  # noqa: E402

app = QGuiApplication(sys.argv)
art.set_skin("classique")
W, H = 1280, 640
img = QImage(W, H, QImage.Format_RGB32)
p = QPainter(img)
p.setRenderHint(QPainter.Antialiasing)

# fond : gros bleu, avec de grands disques plus clairs pour le relief
g = QLinearGradient(0, 0, W, H)
g.setColorAt(0, QColor("#1F5FC4"))
g.setColorAt(1, QColor("#123F94"))
p.fillRect(img.rect(), g)
p.setPen(Qt.NoPen)
for cx, cy, r, a in ((180, 120, 300, 22), (1120, 560, 380, 18), (640, 700, 260, 14)):
    p.setBrush(QColor(255, 255, 255, a))
    p.drawEllipse(QPointF(cx, cy), r, r)

# cartes mystère : de nouvelles plantes, sans rien montrer
for x, y, s, rot, a in ((70, 120, 150, -9, 70), (520, 90, 190, 8, 85), (590, 360, 150, -7, 60), (120, 400, 120, 11, 50)):
    p.save()
    p.translate(x + s / 2, y + s / 2)
    p.rotate(rot)
    r = QRectF(-s / 2, -s / 2, s, s)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(255, 255, 255, int(a * 0.55)))
    p.drawRoundedRect(r, s * 0.18, s * 0.18)
    pen = QPen(QColor(255, 255, 255, 170), 3)
    pen.setStyle(Qt.DashLine)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(r.adjusted(5, 5, -5, -5), s * 0.15, s * 0.15)
    f = QFont("Segoe UI")
    f.setPixelSize(int(s * 0.62))
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor(255, 255, 255, 235))
    p.drawText(r, Qt.AlignCenter, "?")
    p.restore()

# la fleur de départ, bien hydratée, avec son ombre
sc = 3.0
fx = 330 - art.BODY_W * sc / 2
base = H - 62
p.setPen(Qt.NoPen)
p.setBrush(QColor(8, 28, 80, 90))
p.drawEllipse(QPointF(330, base + 6), 150, 20)
p.save()
p.translate(fx, base - art.BODY_H * sc)
p.scale(sc, sc)
art.draw_body(p, 0.0)
p.restore()


def text(s, rect, size, color, bold=True, family="Segoe UI", align=Qt.AlignLeft | Qt.TextWordWrap):
    f = QFont(family)
    f.setPixelSize(size)
    f.setBold(bold)
    p.setFont(f)
    p.setPen(QColor(color))
    p.drawText(rect, align, s)


text("Petite Soif", QRectF(800, 105, 460, 120), 88, "#FFFFFF")
# étiquette jaune pour mettre la nouveauté en valeur
label = QRectF(790, 238, 462, 156)
p.setPen(Qt.NoPen)
p.setBrush(QColor(8, 28, 80, 80))
p.drawRoundedRect(label.translated(0, 8), 30, 30)
p.setBrush(QColor("#FFD86B"))
p.drawRoundedRect(label, 30, 30)
text("New plants\nto unlock!", label.adjusted(28, 0, -20, 0), 54, "#123F94", align=Qt.AlignVCenter | Qt.AlignLeft)
text("The little desktop flower that gets thirsty when you forget to drink.", QRectF(800, 420, 440, 100), 26, "#D8E8FF", False)
text("Windows · free · open source", QRectF(800, 520, 440, 50), 24, "#8FD0FA")

# version en haut à droite
pill = QRectF(W - 196, 30, 156, 58)
p.setPen(Qt.NoPen)
p.setBrush(QColor(255, 255, 255, 235))
p.drawRoundedRect(pill, 29, 29)
text(f"v{__version__}", pill, 30, "#123F94", align=Qt.AlignCenter)

# signature en bas à droite
text("\U0001F6E1️ Tyler / Ben", QRectF(W - 440, H - 80, 400, 50), 30, "#BFD6FF", False,
     "Segoe UI Emoji", Qt.AlignRight | Qt.AlignVCenter)
p.end()

out = ROOT / "docs" / f"petite_soif_v{__version__}_cover.png"
assert img.save(str(out)), "échec export"
print(out)
