"""Génère docs/demo.gif avec le vrai widget de la fleur, rendu hors écran sur une horloge simulée.

Outil de dev uniquement : nécessite Pillow (pip install pillow), qui n'est pas embarqué dans l'exe.
Usage : .venv\\Scripts\\python tools\\make_demo.py [en|fr]   (écrit docs/demo.gif, ou docs/demo_fr.gif)
"""
import io
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402
from PySide6.QtCore import QBuffer, QPoint, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from soif import flower as fl  # noqa: E402


class Clock:
    t = 1000.0

    def monotonic(self):
        return self.t


clock = Clock()
fl.time = clock  # la fleur lit l'heure via time.monotonic()
random.seed(3)

LANG = sys.argv[1] if len(sys.argv) > 1 else "en"
CAP = {"fr": ["Bien hydratée", "20 min sans boire…", "30 min : elle s'agite !", "40 min : très soif", "Clic long = une gorgée", "Merci !"],
       "en": ["Well hydrated", "20 min without drinking…", "30 min: she gets agitated!", "40 min: very thirsty", "Long click = a sip", "Thank you!"]}[LANG]
app = QApplication(sys.argv)
fl.art.set_skin("classique")  # la fleur de départ seulement : les autres plantes restent une surprise
w = fl.FlowerWidget(scale=1.5)
w.drank.connect(lambda: w.set_thirst(0))

FPS, W, H = 20, 360, 340
BG, INK = QColor("#FBF4EA"), QColor("#7A4A34")
frames = []


def shoot(caption, seconds, setup=None):
    if setup:
        setup()
    for _ in range(int(seconds * FPS)):
        clock.t += 1 / FPS
        w._tick()
        img = QImage(W, H, QImage.Format_RGB32)
        img.fill(BG)
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        w.render(p, QPoint((W - w.width()) // 2, 0))
        f = QFont("Segoe UI", 15)
        f.setBold(True)
        p.setFont(f)
        p.setPen(INK)
        p.drawText(QRectF(0, H - 60, W, 40), Qt.AlignCenter, caption)
        p.end()
        buf = QBuffer()
        buf.open(QBuffer.ReadWrite)
        img.save(buf, "PNG")
        frames.append(Image.open(io.BytesIO(bytes(buf.data()))).convert("RGB"))


def press():
    w._pressing, w._press_t0, w._drop_accum = True, clock.t, 0.0


shoot(CAP[0], 1.5)
shoot(CAP[1], 2.0, lambda: w.set_thirst(1))
shoot(CAP[2], 2.0, lambda: (w.set_thirst(2), w.agitate()))
shoot(CAP[3], 2.0, lambda: w.set_thirst(3))
shoot(CAP[4], 1.0, press)
shoot(CAP[5], 2.5)

out = ROOT / "docs" / ("demo.gif" if LANG == "en" else "demo_fr.gif")
frames[0].save(out, save_all=True, append_images=frames[1:], duration=1000 // FPS, loop=0, optimize=True)
print(out, f"{out.stat().st_size / 1024:.0f} Ko", len(frames), "images")
