"""Génère docs/etats.png : les états de la fleur classique (hydratée, soif 1 à 3, sommeil, boit, marche).

Outil de dev uniquement. Rend le vrai widget (QApplication) sur une horloge simulée. Légendes bilingues.
Usage : .venv\\Scripts\\python tools\\make_etats.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QPoint, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from soif import flower as fl  # noqa: E402
from soif import painter as art  # noqa: E402


class Clock:
    t = 1000.0

    def monotonic(self):
        return self.t


clock = Clock()
fl.time = clock
app = QApplication(sys.argv)
art.set_skin("classique")  # on ne montre que la fleur de départ : les autres plantes restent une surprise
w = fl.FlowerWidget(scale=2.0)

STATES = [("Watered · Hydratée", {}), ("Thirst 1 · Soif 1", {"thirst": 1}), ("Thirst 2 · Soif 2", {"thirst": 2, "agitate": True}),
          ("Thirst 3 · Soif 3", {"thirst": 3}), ("Asleep · Sommeil", {"sleep": True}),
          ("Drinking · Boit", {"press": True}), ("Walking · Marche", {"thirst": 3, "walk": True})]
BG, INK = QColor("#F4F0EA"), QColor("#4A2E24")
cw, ch = w.width(), w.height()
img = QImage(cw * len(STATES), ch + 30, QImage.Format_RGB32)
img.fill(BG)
p = QPainter(img)
p.setRenderHint(QPainter.Antialiasing)
f = QFont("Segoe UI", 12)
p.setFont(f)
for i, (label, o) in enumerate(STATES):
    w.thirst = w.thirst_target = float(o.get("thirst", 0))
    w.sleeping, w.sl = bool(o.get("sleep")), 1.0 if o.get("sleep") else 0.0
    w._pressing, w._press_t0 = bool(o.get("press")), clock.t - 0.55
    w._agitate_until = clock.t + 5 if o.get("agitate") else 0.0
    w._walking, w._walk_phase = bool(o.get("walk")), 1.0
    w._t = 0.5 if o.get("sleep") else 0.0
    w.render(p, QPoint(i * cw, 0))
    p.setPen(INK)
    p.drawText(QRectF(i * cw, ch - 8, cw, 36), Qt.AlignHCenter | Qt.AlignVCenter, label)
p.end()
out = ROOT / "docs" / "etats.png"
assert img.save(str(out)), "échec export"
print(out, img.width(), "x", img.height())
