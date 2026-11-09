"""Petite pop-up (clic droit) : total du jour, objectif, + 50 cl, historique 7 jours."""
from PySide6.QtCore import QPoint, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QGuiApplication, QLinearGradient, QPainter, QPen
from . import i18n
from .i18n import t
from PySide6.QtWidgets import (QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout, QWidget)



def fmt_hour(h):
    """Heure ronde : « 6 h » en français, « 6 AM » en anglais (minuit = 12 AM)."""
    if i18n.lang == "en":
        return f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}"
    return f"{h} h"


def fmt_l(cl):
    v = f"{cl / 100:.2f}".rstrip("0").rstrip(".")
    if i18n.lang == "fr":  # virgule décimale en français
        v = v.replace(".", ",")
    return f"{v} L"


def fmt_ago(minutes):
    if minutes is None:
        return t("aucune gorgée aujourd'hui")
    if minutes < 1:
        return t("dernière à l'instant")
    if minutes < 60:
        return t("dernière il y a {m} min", m=minutes)
    return t("dernière il y a {h} h {m}", h=minutes // 60, m=f"{minutes % 60:02d}")


class WaterBar(QWidget):
    def __init__(self):
        super().__init__()
        self.ratio = 0.0
        self.setFixedHeight(10)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#F3E6D7"))
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
        self.setFixedHeight(104)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        top, bottom = 16, 20
        area = h - top - bottom
        maxv = max([self.goal] + [d[1] for d in self.data]) * 1.08 or 1
        n = max(1, len(self.data))
        slot = w / n
        bw = slot * 0.56
        small = QFont(_body())
        small.setPixelSize(11)
        p.setFont(small)

        gy = top + area * (1 - self.goal / maxv)
        p.setPen(QPen(QColor(201, 101, 60, 140), 1, Qt.DashLine))
        p.drawLine(0, int(gy), w, int(gy))

        for i, (label, cl, today) in enumerate(self.data):
            x = i * slot + (slot - bw) / 2
            bh = area * cl / maxv
            p.setPen(Qt.NoPen)
            if cl > 0:
                p.setBrush(QColor("#3A95D8") if today else QColor("#A9D6F5"))
                p.drawRoundedRect(QRectF(x, top + area - bh, bw, bh), 4, 4)
                p.setPen(QColor("#2F7DBA") if today else QColor("#7A5C4A"))
                p.drawText(QRectF(i * slot, top + area - bh - 15, slot, 14), Qt.AlignCenter,
                           fmt_l(cl).replace(" L", ""))
            else:
                p.setBrush(QColor("#F3E6D7"))
                p.drawRoundedRect(QRectF(x, top + area - 3, bw, 3), 1.5, 1.5)
            f = QFont(_title()) if today else QFont(small)
            f.setPixelSize(14 if today else 12)
            f.setWeight(QFont.DemiBold if today else QFont.Normal)
            p.setFont(f)
            p.setPen(QColor("#A9532F") if today else QColor("#7A5C4A"))
            p.drawText(QRectF(i * slot, h - bottom + 2, slot, bottom - 2), Qt.AlignCenter, label)
            p.setFont(small)


def _title():
    from . import settings  # import tardif : settings importe popup
    return settings.FAMILY


def _body():
    from . import settings
    return settings.BODY


def style():
    t, b = _title(), _body()
    return f"""
#card {{ background:#FFF9F1; border:1px solid #EAD8C3; border-radius:16px; }}
QWidget {{ font-family:'{b}', 'Segoe UI'; color:#4A2E24; font-size:14px; }}
QLabel#head {{ font-family:'{t}'; font-size:18px; font-weight:600; }}
QLabel#sub {{ font-size:13px; color:#7A5C4A; }}
QLabel#big {{ font-family:'{t}'; font-size:34px; font-weight:700; }}
QLabel#goal {{ font-size:15px; color:#7A5C4A; padding-bottom:7px; }}
QLabel#pct {{ background:#E7F2FB; color:#2F7DBA; border-radius:11px; padding:0 9px;
              font-size:13px; font-weight:700; }}
QLabel#pct[done="true"] {{ background:#E3F4E7; color:#2E8A50; }}
QLabel#meta {{ font-size:13px; color:#7A5C4A; }}
QLabel#dnd {{ background:#EEF1F7; color:#5A6C90; border-radius:10px; padding:4px 10px; font-size:13px; }}
QFrame#sep {{ border:none; border-top:1px solid #F1E5D7; }}
QPushButton#plus {{ background:#3A95D8; color:white; border:none; border-radius:10px; padding:6px;
                    font-family:'{t}'; font-size:18px; font-weight:700; }}
QPushButton#plus:hover {{ background:#2F86C7; }}
QPushButton#plus:pressed {{ background:#2672AD; }}
QPushButton#undo {{ background:transparent; border:none; color:#7A5C4A; text-decoration:underline;
                    font-size:13px; padding:0; }}
QPushButton#undo:hover {{ color:#A9532F; }}
QPushButton#sleep {{ background:#EEF1F7; border:1px solid #D5DCEC; border-radius:10px; font-size:18px; padding:0; }}
QPushButton#sleep:hover {{ background:#E0E6F3; border-color:#B8C4DE; }}
QPushButton#gear {{ background:#E3F1E4; border:1px solid #CBE2CE; border-radius:10px; font-size:18px; padding:0; }}
QPushButton#gear:hover {{ background:#D2E9D5; border-color:#A9D3AF; }}
QLabel#dot {{ background:#E0533A; border-radius:4px; }}
"""


class StatsPopup(QWidget):
    def __init__(self, controller):
        super().__init__(None, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.ctrl = controller
        self.setStyleSheet(style())

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        card = QFrame(objectName="card")
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(90, 50, 30, 55))
        card.setGraphicsEffect(shadow)
        outer.addWidget(card)
        card.setFixedWidth(284)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 16)
        lay.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(QLabel(t("Aujourd'hui"), objectName="head"))
        self.since = QLabel("", objectName="sub")
        row.addStretch()
        row.addWidget(self.since)
        gear = QPushButton("⚙️", objectName="gear")
        gear.setToolTip(t("Paramètres"))
        gear.setCursor(Qt.PointingHandCursor)
        gear.setFixedSize(34, 34)
        gear.clicked.connect(self.ctrl.open_settings)
        self.news_dot = QLabel(gear, objectName="dot")  # une plante débloquée pas encore vue
        self.news_dot.setFixedSize(8, 8)
        self.news_dot.move(24, 2)
        row.addWidget(gear)
        self.sleep = sleep = QPushButton("💤", objectName="sleep")
        sleep.setToolTip(t("Ne pas déranger"))
        sleep.setCursor(Qt.PointingHandCursor)
        sleep.setFixedSize(34, 34)
        sleep.clicked.connect(lambda: (self.close(), QTimer.singleShot(0, self.ctrl.toggle_dnd)))
        row.addWidget(sleep)
        lay.addLayout(row)

        row = QHBoxLayout()
        row.setSpacing(4)
        self.big = QLabel("", objectName="big")
        self.goal = QLabel("", objectName="goal")
        self.pct = QLabel("", objectName="pct")
        row.addWidget(self.big, 0, Qt.AlignBottom)
        row.addWidget(self.goal, 0, Qt.AlignBottom)
        row.addStretch()
        self.pct.setFixedHeight(22)
        row.addWidget(self.pct, 0, Qt.AlignVCenter)
        lay.addLayout(row)

        self.bar = WaterBar()
        lay.addWidget(self.bar)
        self.meta = QLabel("", objectName="meta")
        self.meta.setWordWrap(True)
        lay.addWidget(self.meta)

        lay.addSpacing(2)
        self.plus = QPushButton("", objectName="plus")
        self.plus.setCursor(Qt.PointingHandCursor)
        self.plus.clicked.connect(self._on_plus)
        lay.addWidget(self.plus)
        self.undo = QPushButton(t("annuler le dernier verre"), objectName="undo")
        self.undo.setCursor(Qt.PointingHandCursor)
        self.undo.clicked.connect(self._on_undo)
        lay.addWidget(self.undo, 0, Qt.AlignHCenter)

        sep = QFrame(objectName="sep")
        sep.setFixedHeight(1)
        lay.addSpacing(2)
        lay.addWidget(sep)
        row = QHBoxLayout()
        row.addWidget(QLabel(t("7 jours"), objectName="head"))
        row.addStretch()
        self.avg = QLabel("", objectName="sub")
        row.addWidget(self.avg)
        lay.addLayout(row)
        self.chart = WeekChart()
        lay.addWidget(self.chart)

        self.dnd = QLabel("", objectName="dnd")
        lay.addWidget(self.dnd)
        self.refresh()

    def refresh(self):
        st = self.ctrl.stats()
        self.since.setText(t("depuis {h}", h=fmt_hour(st['reset_hour'])))
        self.big.setText(fmt_l(st["total_cl"]))
        self.goal.setText(f"/ {fmt_l(st['goal_cl'])}")
        ratio = st["total_cl"] / st["goal_cl"] if st["goal_cl"] else 0
        self.pct.setText(f"{round(ratio * 100)} %")
        self.pct.setProperty("done", ratio >= 1)
        self.pct.style().unpolish(self.pct)
        self.pct.style().polish(self.pct)
        self.bar.ratio = ratio
        self.bar.update()
        g = st["sips"]
        v = st["glasses"]
        self.meta.setText(t("{g} gorgée{s} · {v} verre{s2}", g=g, s="s" if g > 1 else "", v=v,
                             s2=("s" if i18n.lang == "fr" else "es") if v > 1 else "")
                           + "\n" + fmt_ago(st['last_min']))
        self.plus.setText(f"+ {st['glass_cl']} cl")
        self.undo.setVisible(v > 0)
        self.avg.setText(t("moy. {v}", v=fmt_l(round(st['avg_cl'] / 10) * 10)) if st["avg_cl"] is not None else "")
        self.chart.goal = st["goal_cl"]
        self.chart.data = [(t("LMMJVSD")[d.weekday()], cl, i == len(st["week"]) - 1) for i, (d, cl) in enumerate(st["week"])]
        self.chart.update()
        self.news_dot.setVisible(self.ctrl.has_news())
        self.dnd.setText(st["dnd_text"] or "")
        self.dnd.setVisible(bool(st["dnd_text"]))
        self.sleep.setText("🔔" if st["dnd_text"] else "💤")  # comme sur le pot : 🔔 reprend, 💤 endort
        self.sleep.setToolTip(t("Reprendre maintenant") if st["dnd_text"] else t("Ne pas déranger"))
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
