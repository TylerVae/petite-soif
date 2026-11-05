"""Petite pop-up (clic droit) : total du jour, objectif, + 50 cl, historique 7 jours."""
from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout, QWidget)

DAYS = ["L", "M", "M", "J", "V", "S", "D"]


def fmt_l(cl):
    v = f"{cl / 100:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    return f"{v} L"


def fmt_ago(minutes):
    if minutes is None:
        return "aucune gorgée aujourd'hui"
    if minutes < 1:
        return "dernière à l'instant"
    if minutes < 60:
        return f"dernière il y a {minutes} min"
    return f"dernière il y a {minutes // 60} h {minutes % 60:02d}"


class WaterBar(QWidget):
    def __init__(self):
        super().__init__()
        self.ratio = 0.0
        self.setFixedHeight(12)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#E6EDF3"))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        k = max(0.0, min(1.0, self.ratio))
        if k > 0:
            f = QRectF(r.x(), r.y(), max(r.height(), r.width() * k), r.height())
            g = QLinearGradient(f.topLeft(), f.topRight())
            if self.ratio >= 1:
                g.setColorAt(0, QColor("#7BD88F"))
                g.setColorAt(1, QColor("#3FB36B"))
            else:
                g.setColorAt(0, QColor("#8FD6FF"))
                g.setColorAt(1, QColor("#3A95D8"))
            p.setBrush(g)
            p.drawRoundedRect(f, r.height() / 2, r.height() / 2)


class WeekChart(QWidget):
    def __init__(self):
        super().__init__()
        self.data = []  # [(label, cl, is_today)]
        self.goal = 300
        self.setFixedHeight(96)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        top, bottom = 14, 16
        area = h - top - bottom
        maxv = max([self.goal] + [d[1] for d in self.data]) * 1.08 or 1
        n = max(1, len(self.data))
        slot = w / n
        bw = slot * 0.56
        small = QFont(self.font())
        small.setPixelSize(10)
        p.setFont(small)

        gy = top + area * (1 - self.goal / maxv)
        p.setPen(QPen(QColor("#E0A45A"), 1, Qt.DashLine))
        p.drawLine(0, int(gy), w, int(gy))

        for i, (label, cl, today) in enumerate(self.data):
            x = i * slot + (slot - bw) / 2
            bh = area * cl / maxv
            p.setPen(Qt.NoPen)
            if cl > 0:
                p.setBrush(QColor("#3A95D8") if today else QColor("#A9D6F5"))
                p.drawRoundedRect(QRectF(x, top + area - bh, bw, bh), 3, 3)
                p.setPen(QColor("#6D5A4C"))
                p.drawText(QRectF(i * slot, top + area - bh - 13, slot, 12), Qt.AlignCenter,
                           fmt_l(cl).replace(" L", ""))
            else:
                p.setBrush(QColor("#E6E0D8"))
                p.drawRoundedRect(QRectF(x, top + area - 3, bw, 3), 1.5, 1.5)
            f = QFont(small)
            f.setBold(today)
            p.setFont(f)
            p.setPen(QColor("#3A2A20") if today else QColor("#A08A78"))
            p.drawText(QRectF(i * slot, h - bottom + 2, slot, bottom - 2), Qt.AlignCenter, label)
            p.setFont(small)


STYLE = """
#card { background:#FFF9F1; border:1px solid #EADBC8; border-radius:14px; }
QLabel { color:#3A2A20; }
QLabel#title { color:#9A806B; font-size:10px; font-weight:700; letter-spacing:1px; }
QLabel#big { font-size:26px; font-weight:800; }
QLabel#goal { color:#9A806B; font-size:13px; }
QLabel#pct { color:#3A95D8; font-size:12px; font-weight:700; }
QLabel#meta { color:#8A7361; font-size:11px; }
QLabel#dnd { color:#6F82A6; font-size:11px; }
QPushButton#plus { background:#3A95D8; color:white; border:none; border-radius:10px;
                   padding:8px; font-size:14px; font-weight:800; }
QPushButton#plus:hover { background:#2F86C7; }
QPushButton#plus:pressed { background:#2672AD; }
QPushButton#undo { background:transparent; color:#A08A78; border:none; font-size:11px;
                   text-decoration:underline; padding:0; }
QPushButton#undo:hover { color:#6D5A4C; }
"""


class StatsPopup(QWidget):
    def __init__(self, controller):
        super().__init__(None, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.ctrl = controller
        self.setStyleSheet(STYLE)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        card = QFrame(objectName="card")
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(80, 50, 30, 60))
        card.setGraphicsEffect(shadow)
        outer.addWidget(card)
        card.setFixedWidth(250)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(6)

        row = QHBoxLayout()
        row.addWidget(QLabel("AUJOURD'HUI", objectName="title"))
        row.addStretch()
        self.since = QLabel("", objectName="title")
        row.addWidget(self.since)
        lay.addLayout(row)

        row = QHBoxLayout()
        row.setSpacing(4)
        self.big = QLabel("", objectName="big")
        self.goal = QLabel("", objectName="goal")
        self.pct = QLabel("", objectName="pct")
        row.addWidget(self.big, 0, Qt.AlignBottom)
        row.addWidget(self.goal, 0, Qt.AlignBottom)
        row.addStretch()
        row.addWidget(self.pct, 0, Qt.AlignBottom)
        lay.addLayout(row)

        self.bar = WaterBar()
        lay.addWidget(self.bar)
        self.meta = QLabel("", objectName="meta")
        self.meta.setWordWrap(True)
        lay.addWidget(self.meta)

        lay.addSpacing(4)
        self.plus = QPushButton("", objectName="plus")
        self.plus.setCursor(Qt.PointingHandCursor)
        self.plus.clicked.connect(self._on_plus)
        lay.addWidget(self.plus)
        self.undo = QPushButton("annuler le dernier verre", objectName="undo")
        self.undo.setCursor(Qt.PointingHandCursor)
        self.undo.clicked.connect(self._on_undo)
        lay.addWidget(self.undo, 0, Qt.AlignHCenter)

        lay.addSpacing(6)
        row = QHBoxLayout()
        row.addWidget(QLabel("7 JOURS", objectName="title"))
        row.addStretch()
        self.avg = QLabel("", objectName="title")
        row.addWidget(self.avg)
        lay.addLayout(row)
        self.chart = WeekChart()
        lay.addWidget(self.chart)

        self.dnd = QLabel("", objectName="dnd")
        lay.addWidget(self.dnd)
        self.refresh()

    def refresh(self):
        st = self.ctrl.stats()
        self.since.setText(f"depuis {st['reset_hour']} h")
        self.big.setText(fmt_l(st["total_cl"]))
        self.goal.setText(f"/ {fmt_l(st['goal_cl'])}")
        ratio = st["total_cl"] / st["goal_cl"] if st["goal_cl"] else 0
        self.pct.setText(f"{round(ratio * 100)} %")
        self.bar.ratio = ratio
        self.bar.update()
        g = st["sips"]
        v = st["glasses"]
        self.meta.setText(f"{g} gorgée{'s' if g > 1 else ''} · {v} verre{'s' if v > 1 else ''} · {fmt_ago(st['last_min'])}")
        self.plus.setText(f"+ {st['glass_cl']} cl")
        self.undo.setVisible(v > 0)
        self.avg.setText(f"MOY. {fmt_l(round(st['avg_cl'] / 10) * 10)}" if st["avg_cl"] is not None else "")
        self.chart.goal = st["goal_cl"]
        self.chart.data = [(DAYS[d.weekday()], cl, i == len(st["week"]) - 1) for i, (d, cl) in enumerate(st["week"])]
        self.chart.update()
        self.dnd.setText(st["dnd_text"] or "")
        self.dnd.setVisible(bool(st["dnd_text"]))
        self.adjustSize()

    def _on_plus(self):
        self.ctrl.add_glass()
        self.refresh()

    def _on_undo(self):
        self.ctrl.undo_glass()
        self.refresh()

    def show_near(self, point):
        self.adjustSize()
        scr = QGuiApplication.screenAt(point) or QGuiApplication.primaryScreen()
        g = scr.availableGeometry()
        x = point.x() + 8
        y = point.y() - self.height() // 2
        if x + self.width() > g.right():
            x = point.x() - self.width() - 8
        x = max(g.left(), min(x, g.right() - self.width()))
        y = max(g.top(), min(y, g.bottom() - self.height()))
        self.move(QPoint(x, y))
        self.show()
