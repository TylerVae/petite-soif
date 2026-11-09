"""Fenêtre de paramètres « Carnet » : onglets à gauche, application immédiate (écrit config.json)."""
import codecs
import math
import platform
import time
from urllib.parse import urlencode

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (QAbstractButton, QButtonGroup, QFrame, QGraphicsDropShadowEffect,
                               QHBoxLayout, QLabel, QMessageBox, QPushButton, QSlider, QStackedWidget,
                               QVBoxLayout, QWidget)

from . import config as cfgmod
from . import i18n
from .i18n import t
from . import painter as art
from . import plantes
from . import winapi
from .popup import fmt_hour, fmt_l

FAMILY = "Baloo 2"  # titres (remplacé par le nom réellement chargé, main.load_fonts)
BODY = "Segoe UI"  # petit texte : police de Windows, calée au pixel (DM Sans/Baloo restaient flous en petit)
CONTROL_W = 196
NDP_CHOICES = [15, 30, 60, 120, 240]
INSIST = [("douce", "Douce"), ("normale", "Normale"), ("tenace", "Tenace")]
INSIST_HELP = {
    "douce": "Un rappel toutes les 5 min, elle reste dans son coin.",
    "normale": "Un rappel par minute, elle te suit 5 s.",
    "tenace": "Un rappel par minute, elle te suit 10 s et tourne autour du curseur.",
}
TABS = [("🔔", "Rappels"), ("💧", "Hydratation"), ("🌱", "Fleur et son"), ("🌺", "Ma plante"), ("⚙️", "Système"),
        ("💛", "À propos")]
XP_TIER = 200  # une nouvelle plante tous les 200 XP
# Identifiants numérotés : les noms ne se lisent pas dans le code (ROT13, FR puis EN) ; ils s'affichent une fois la plante gagnée.
SKINS = ["classique"] + [f"plante_{n}" for n in range(2, 12)]
_NOMS = {"plante_2": ("Bepuvqér", "Bepuvq"),
          "plante_3": ("Qnuyvn", "Qnuyvn"),
          "plante_4": ("Zhthrg", "Yvyl bs gur inyyrl"),
          "plante_5": ("Gbhearfby", "Fhasybjre"),
          "plante_6": ("Pnpghf ra syrhe", "Sybjrevat pnpghf"),
          "plante_7": ("Ghyvcrf", "Ghyvcf"),
          "plante_8": ("Yninaqr", "Yniraqre"),
          "plante_9": ("Obafnï", "Obafnv"),
          "plante_10": ("Senvfvre", "Fgenjoreel cynag"),
          "plante_11": ("Ebfr", "Ebfr")}


def plant_name(pid):
    if pid not in _NOMS:
        return t("Classique")
    return codecs.decode(_NOMS[pid][i18n.lang == "en"], "rot13")


def plant_ready(pid):
    """La plante est dessinée dans l'appli (déploiement une par une)."""
    return pid == "classique" or pid in plantes.PLANTES


def plant_level(xp):
    """Nombre de plantes débloquées en plus de la Classique."""
    return min(xp // XP_TIER, len(SKINS) - 1)


def report_bug_url():
    """Page « nouvelle issue » préremplie (version, Windows). Ouverte par le navigateur : l'appli ne se connecte à rien."""
    fields = {"template": "bug.yml", "version": cfgmod.__version__, "windows": f"{platform.release()} ({platform.version()})"}
    return f"{cfgmod.REPO_URL}/issues/new?" + urlencode(fields)


def fmt_min(m):
    if m < 60:
        return f"{m} min"
    return f"{m // 60} h" if m % 60 == 0 else f"{m // 60} h {m % 60:02d}"


def style():
    return f"""
#card {{ background:#FFF9F1; border:1px solid #EAD8C3; border-radius:16px; }}
#side {{ background:#F6E9D9; border-top-left-radius:16px; border-bottom-left-radius:16px; }}
QWidget {{ font-family:'{BODY}', 'Segoe UI'; color:#4A2E24; font-size:14px; }}
QLabel#brand {{ font-family:'{FAMILY}'; font-size:20px; font-weight:700; }}
QLabel#title {{ font-family:'{FAMILY}'; font-size:28px; font-weight:700; }}
QLabel#lbl {{ font-family:'{FAMILY}'; font-size:18px; font-weight:600; }}
QLabel#hlp, QLabel#sub {{ font-size:14px; color:#7A5C4A; }}
QLabel#foot {{ font-size:13px; color:#7A5C4A; }}
QFrame#row {{ border:none; border-bottom:1px solid #F1E5D7; }}
QPushButton#nav {{ text-align:left; padding:6px 10px; border:none; border-radius:10px; font-family:'{FAMILY}'; font-size:18px; font-weight:400; color:#6E4F3E; }}
QPushButton#nav:hover {{ background:rgba(201,101,60,18); }}
QPushButton#nav:checked {{ background:rgba(201,101,60,36); color:#A9532F; font-weight:600; }}
QPushButton#close {{ border:none; border-radius:10px; font-size:17px; color:#8A6450; }}
QPushButton#close:hover {{ background:#F3E6D7; color:#A9532F; }}
QFrame#step {{ background:white; border:1px solid #EAD8C3; border-radius:10px; }}
QFrame#step QPushButton {{ border:none; border-radius:9px; font-size:18px; color:#C9653C; }}
QFrame#step QPushButton:hover {{ background:#F6E9D9; }}
QFrame#step[water="true"] QPushButton {{ color:#3A95D8; }}
QFrame#step[water="true"] QPushButton:hover {{ background:#E7F2FB; }}
QFrame#seg {{ background:#F3E6D7; border-radius:10px; }}
QFrame#lang {{ background:#EAD8C3; border-radius:9px; }}
QFrame#lang QPushButton {{ border:none; border-radius:7px; font-size:12px; font-weight:700; color:#7A5C4A; }}
QFrame#lang QPushButton:checked {{ background:#FFF9F1; color:#A9532F; }}
QFrame#seg QPushButton {{ border:none; border-radius:8px; padding:4px 0; font-size:13px; }}
QFrame#seg QPushButton:checked {{ background:#C9653C; color:white; font-weight:700; }}
QPushButton#chip {{ background:white; border:1px solid #EAD8C3; border-radius:13px; padding:2px 11px; font-size:13px; }}
QPushButton#chip:checked {{ background:rgba(201,101,60,36); border-color:transparent; color:#A9532F; font-weight:700; }}
QPushButton#key {{ background:white; border:1px solid #EAD8C3; border-radius:10px; }}
QPushButton#key[capture="true"] {{ border:2px solid #C9653C; background:#FFF3EA; }}
QPushButton#key[capture="true"] QLabel {{ color:#A9532F; }}
QLabel#keyicon {{ font-size:18px; }}
QLabel#fine {{ font-size:12px; color:#9A806B; font-style:italic; }}
QPushButton#key[bad="true"] {{ border:2px solid #D2553E; }}
QPushButton#link {{ border:none; color:#A9532F; text-decoration:underline; font-size:13px; padding:0; }}
QPushButton#link:hover {{ color:#7A3A1F; }}
QPushButton#muted {{ border:none; color:#7A5C4A; text-decoration:underline; font-size:13px; padding:0; }}
QLabel#pill {{ background:rgba(201,101,60,36); color:#A9532F; border-radius:10px; padding:0 10px; font-size:12px; font-weight:700; }}
QSlider::groove:horizontal {{ height:6px; background:#F3E6D7; border-radius:3px; }}
QSlider::sub-page:horizontal {{ height:6px; background:#C9653C; border-radius:3px; }}
QSlider {{ min-height:24px; }}
QLabel#dot {{ background:#E0533A; border-radius:4px; }}
QLabel#level {{ font-family:'{FAMILY}'; font-size:24px; font-weight:700; }}
QLabel#next {{ font-size:14px; color:#4A2E24; }}
QFrame#stage {{ background:#F6E8D8; border-radius:12px; }}
QMessageBox {{ background:#FFF9F1; }}
QMessageBox QLabel {{ color:#4A2E24; font-size:14px; }}
QMessageBox QPushButton {{ background:white; color:#4A2E24; border:1px solid #EAD8C3; border-radius:8px; padding:6px 14px; min-width:90px; }}
QMessageBox QPushButton:hover, QMessageBox QPushButton:default {{ border-color:#C9653C; }}
QFrame#skin {{ background:white; border:1px solid #EAD8C3; border-radius:10px; }}
QFrame#skin[locked="true"] {{ background:#F6EFE6; border:1px dashed #E3D3C1; }}
QFrame#skin[locked="true"] QLabel {{ color:#A08A78; }}
QFrame#skin[current="true"] {{ border:2px solid #C9653C; }}
QLabel#skinicon {{ font-size:22px; }}
QLabel#skinname {{ font-size:13px; font-weight:700; }}
QLabel#skinstate {{ font-size:12px; color:#7A5C4A; }}
QSlider::handle:horizontal {{ background:white; border:2px solid #C9653C; width:14px; height:14px; margin:-6px 0; border-radius:9px; }}
"""


# --- petits contrôles --------------------------------------------------------
class Stepper(QFrame):
    changed = Signal(int)

    def __init__(self, value, step, lo, hi, fmt, water=False, on_click=None):
        super().__init__(objectName="step")
        self.setProperty("water", water)
        self.value, self.step, self.lo, self.hi, self.fmt = value, step, lo, hi, fmt
        self.setFixedSize(CONTROL_W, 34)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(1, 1, 1, 1)
        lay.setSpacing(0)
        self.label = QLabel(alignment=Qt.AlignCenter)
        self.label.setStyleSheet("font-size:15px; font-weight:600;")
        for sign, d in (("–", -1), ("+", 1)):
            b = QPushButton(sign)
            b.setFixedSize(32, 32)
            b.setCursor(Qt.PointingHandCursor)
            b.setAutoRepeat(True)
            b.setAutoRepeatDelay(400)
            b.setAutoRepeatInterval(90)
            b.clicked.connect(lambda _=False, d=d: self._bump(d))
            if d < 0:
                lay.addWidget(b)
                lay.addWidget(self.label, 1)
            else:
                lay.addWidget(b)
        self.on_click = on_click
        self._show()

    def _show(self):
        self.label.setText(self.fmt(self.value))

    def set_value(self, v):
        self.value = v
        self._show()

    def _bump(self, d):
        v = max(self.lo, min(self.hi, self.value + d * self.step))
        if v != self.value:
            self.value = v
            self._show()
            if self.on_click:
                self.on_click()
            self.changed.emit(v)


class Segment(QFrame):
    changed = Signal(str)

    def __init__(self, items, current):
        super().__init__(objectName="seg")
        self.setFixedSize(CONTROL_W, 34)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(0)
        self.group = QButtonGroup(self)
        self.buttons = {}
        for key, text in items:
            b = QPushButton(text, checkable=True)
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(30)
            self.group.addButton(b)
            self.buttons[key] = b
            lay.addWidget(b)
            b.clicked.connect(lambda _=False, k=key: self.changed.emit(k))
        self.set_value(current)

    def set_value(self, key):
        (self.buttons.get(key) or next(iter(self.buttons.values()))).setChecked(True)


class Toggle(QAbstractButton):
    def __init__(self, checked):
        super().__init__(checkable=True, checked=checked)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(40, 22)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#C9653C" if self.isChecked() else "#E3D3C1"))
        p.drawRoundedRect(QRectF(0, 0, 40, 22), 11, 11)
        p.setBrush(QColor("white"))
        p.drawEllipse(QRectF(20 if self.isChecked() else 2, 2, 18, 18))


class KeyField(QPushButton):
    """Capture d'un raccourci : seulement après un clic dessus, et seulement dans cette fenêtre."""
    captured = Signal(str)
    started = Signal()
    cancelled = Signal()

    def __init__(self, text):
        super().__init__(objectName="key")
        self.setFixedSize(CONTROL_W, 34)
        self.setCursor(Qt.PointingHandCursor)
        self.capturing = False
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(6)
        icon = QLabel("⌨️", objectName="keyicon", alignment=Qt.AlignCenter)
        icon.setFixedSize(26, 32)
        self._txt = QLabel(alignment=Qt.AlignCenter)
        for w in (icon, self._txt):
            w.setAttribute(Qt.WA_TransparentForMouseEvents)
        lay.addWidget(icon)
        lay.addWidget(self._txt, 1)
        lay.addSpacing(22)  # contrepoids de l'icône : le texte reste centré dans le champ
        self.set_hotkey(text)
        self.clicked.connect(self._start)

    def _restyle(self, **props):
        for k, v in props.items():
            self.setProperty(k, v)
        for w in (self, self._txt):
            w.style().unpolish(w)
            w.style().polish(w)

    def setText(self, text):
        self._txt.setText(text)

    def set_hotkey(self, text, bad=False):
        self.hotkey = text
        self.setText(winapi.pretty_hotkey(text).replace("+", " + "))
        self._restyle(capture=False, bad=bad)

    def _start(self):
        if self.capturing:
            return
        self.capturing = True
        self.setText(t("Appuie sur tes touches…"))
        self._restyle(capture=True, bad=False)
        self.started.emit()
        self.grabKeyboard()

    def _stop(self):
        self.capturing = False
        self.releaseKeyboard()

    def keyPressEvent(self, e):
        if not self.capturing:
            return super().keyPressEvent(e)
        k = e.key()
        if k == Qt.Key_Escape:
            self._stop()
            self.set_hotkey(self.hotkey)
            self.cancelled.emit()
            return
        if Qt.Key_F1 <= k <= Qt.Key_F24:
            main = f"f{k - Qt.Key_F1 + 1}"
        elif Qt.Key_A <= k <= Qt.Key_Z or Qt.Key_0 <= k <= Qt.Key_9:
            main = chr(k).lower()
        else:
            return  # modificateur seul ou touche non gérée : on attend la suite
        m = e.modifiers()
        mods = [n for n, f in (("ctrl", Qt.ControlModifier), ("alt", Qt.AltModifier),
                               ("shift", Qt.ShiftModifier), ("win", Qt.MetaModifier)) if m & f]
        if not {"ctrl", "alt", "win"} & set(mods):
            self.setText(t("Ajoute Ctrl, Alt ou Win"))
            return
        self._stop()
        self.captured.emit("+".join(mods + [main]))

    def focusOutEvent(self, e):
        if self.capturing:
            self._stop()
            self.set_hotkey(self.hotkey)
            self.cancelled.emit()
        super().focusOutEvent(e)


class XpBar(QWidget):
    def __init__(self):
        super().__init__()
        self.ratio = 0.0
        self.setFixedHeight(12)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#F3E6D7"))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        if self.ratio > 0:
            f = QRectF(r.x(), r.y(), max(r.height(), r.width() * min(1.0, self.ratio)), r.height())
            g = QLinearGradient(f.topLeft(), f.topRight())
            g.setColorAt(0, QColor("#E8A27C"))
            g.setColorAt(1, QColor("#C9653C"))
            p.setBrush(g)
            p.drawRoundedRect(f, r.height() / 2, r.height() / 2)


class Slot(QPushButton):
    """Une case de l'étagère : plante débloquée (cliquable), la prochaine en silhouette « ??? », ou un point."""

    def __init__(self, pid):
        super().__init__()
        self.pid = pid
        self.state, self.ready, self.current = "hidden", False, False
        self.setFixedSize(44, 54)

    def set_state(self, state, ready, current, tip):
        self.state, self.ready, self.current = state, ready, current
        self.setToolTip(tip)
        self.setCursor(Qt.PointingHandCursor if state == "open" and ready else Qt.ArrowCursor)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        locked = self.state != "open"
        pen = QPen(QColor("#C9653C") if self.current else QColor("#D9C3AB" if locked else "#EAD8C3"), 2 if self.current else 1)
        if locked:
            pen.setStyle(Qt.DashLine)
        p.setPen(pen)
        p.setBrush(QColor("#F6EDE2") if locked else QColor("white"))
        p.drawRoundedRect(QRectF(1, 1, self.width() - 2, self.height() - 2), 10, 10)
        if self.state == "hidden":
            p.setPen(QColor("#B8A28E"))
            p.drawText(self.rect(), Qt.AlignCenter, "·")
        elif self.state == "next":
            f = QFont(FAMILY)  # pas de silhouette : le « ? » ne dévoile rien de la prochaine plante
            f.setPixelSize(22)
            f.setWeight(QFont.Bold)
            p.setFont(f)
            p.setPen(QColor("#B8A28E"))
            p.drawText(self.rect(), Qt.AlignCenter, "?")
        elif self.ready:
            k = 0.34
            p.translate((self.width() - art.BODY_W * k) / 2, (self.height() - art.BODY_H * k) / 2)
            p.scale(k, k)
            art.draw_preview(p, self.pid)
        else:  # débloquée mais pas encore dessinée
            f = QFont("Segoe UI Emoji")
            f.setPixelSize(22)
            p.setFont(f)
            p.setOpacity(0.6)
            p.drawText(self.rect(), Qt.AlignCenter, self.icon_)
        p.end()


class Badge(QWidget):
    """Petite fleur dessinée par painter, qui sait se balancer / s'agiter / tourner."""

    def __init__(self, size):
        super().__init__()
        self.sc = size / art.BODY_H
        self.setFixedSize(int(art.BODY_W * self.sc) + 16, size + 8)
        self.kind, self.t0 = None, 0.0
        self.timer = QTimer(self, interval=16, timeout=self.update)

    def play(self, kind):
        self.kind, self.t0 = kind, time.monotonic()
        self.timer.start()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        t = time.monotonic() - self.t0
        dur = {"douce": 1.4, "normale": 0.9, "tenace": 1.3}.get(self.kind, 0)
        rot = dx = dy = 0.0
        if self.kind and t < dur:
            k = 1 - t / dur
            if self.kind == "douce":
                rot = math.sin(t / dur * 2 * math.pi) * 6
            elif self.kind == "normale":
                rot = math.sin(t * 40) * 12 * k
            else:
                a = t / dur * 4 * math.pi
                dx, dy = math.cos(a) * 5, math.sin(a) * 3
                rot = math.sin(t * 45) * 9 * k
        elif self.kind:
            self.kind = None
            self.timer.stop()
        w = art.BODY_W * self.sc
        p.translate((self.width() - w) / 2 + dx, 4 + dy)
        p.scale(self.sc, self.sc)
        p.translate(50, 129)
        p.rotate(rot)
        p.translate(-50, -129)
        art.draw_body(p, 0)
        p.end()


# --- fenêtre -----------------------------------------------------------------
class SettingsWindow(QWidget):
    def __init__(self, controller):
        super().__init__(None, Qt.Window | Qt.FramelessWindowHint)
        self.setWindowTitle(t("Paramètres · Petite Soif"))
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.ctrl = controller
        self.setStyleSheet(style())
        self._last_bubble = 0.0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        card = QFrame(objectName="card")
        shadow = QGraphicsDropShadowEffect(card, blurRadius=24, offset=QPointF(0, 4), color=QColor(80, 50, 30, 70))
        card.setGraphicsEffect(shadow)
        outer.addWidget(card)
        root = QHBoxLayout(card)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        side = QFrame(objectName="side")
        side.setFixedWidth(204)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(10, 14, 10, 14)
        sl.setSpacing(2)
        head = QHBoxLayout()
        self.side_badge = Badge(52)  # (self.badge est la grande plante de « Ma plante »)
        head.addWidget(self.side_badge)
        txt = QVBoxLayout()
        txt.setSpacing(0)
        txt.addWidget(QLabel("Petite Soif", objectName="brand"))
        txt.addWidget(QLabel(t("Paramètres"), objectName="sub"))
        head.addLayout(txt, 1)
        sl.addLayout(head)
        sl.addSpacing(10)
        self.nav = QButtonGroup(self)
        for i, (icon, name) in enumerate(TABS):
            b = QPushButton(f"{icon}  {t(name)}".replace("&", "&&"), objectName="nav", checkable=True)
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(36)
            self.nav.addButton(b, i)
            if name == "Ma plante":  # pastille quand une plante vient d'être débloquée
                bl = QHBoxLayout(b)
                bl.setContentsMargins(0, 0, 12, 0)
                bl.addStretch()
                self.news_dot = QLabel(objectName="dot")
                self.news_dot.setFixedSize(9, 9)
                self.news_dot.setVisible(self.ctrl.has_news())
                bl.addWidget(self.news_dot)
            sl.addWidget(b)
        sl.addStretch()
        bug = self._link("🐞 " + t("Signaler un bug"), lambda: self._open_url(report_bug_url()))
        bug.setToolTip(t("Ouvre une page GitHub préremplie avec ta version de l'appli et de Windows."))
        sl.addWidget(bug, 0, Qt.AlignLeft)
        sl.addSpacing(6)
        bottom = QHBoxLayout()
        bottom.setContentsMargins(4, 0, 4, 0)
        lang = QFrame(objectName="lang")
        ll = QHBoxLayout(lang)
        ll.setContentsMargins(2, 2, 2, 2)
        ll.setSpacing(0)
        group = QButtonGroup(lang)
        for code in ("fr", "en"):
            b = QPushButton(code.upper(), checkable=True, checked=i18n.lang == code)
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedSize(38, 26)
            b.setToolTip("Français" if code == "fr" else "English")
            b.clicked.connect(lambda _=False, c=code: QTimer.singleShot(0, lambda: self.ctrl.set_language(c)))
            group.addButton(b)
            ll.addWidget(b)
        bottom.addWidget(lang)
        bottom.addStretch()
        bottom.addWidget(QLabel(f"v{cfgmod.__version__}", objectName="foot"))
        sl.addLayout(bottom)
        root.addWidget(side)

        main = QVBoxLayout()
        main.setContentsMargins(22, 10, 12, 12)
        top = QHBoxLayout()
        self.title = QLabel("", objectName="title")
        top.addWidget(self.title, 1)
        close = QPushButton("✕", objectName="close")
        close.setFixedSize(34, 34)
        close.setCursor(Qt.PointingHandCursor)
        close.clicked.connect(self.close)
        top.addWidget(close, 0, Qt.AlignTop)
        main.addLayout(top)
        self.stack = QStackedWidget()
        main.addWidget(self.stack, 1)
        foot = QHBoxLayout()
        self.saved = QLabel(t("✓ Enregistré automatiquement"), objectName="foot")
        foot.addWidget(self.saved)
        foot.addStretch()
        reset = QPushButton(t("Valeurs par défaut"), objectName="muted")
        reset.setCursor(Qt.PointingHandCursor)
        reset.clicked.connect(self._reset)
        foot.addWidget(reset)
        main.addLayout(foot)
        root.addLayout(main, 1)

        self._build_pages()
        self.nav.idClicked.connect(self._show_tab)
        self.nav.button(0).setChecked(True)
        self._show_tab(0)
        self.resize(772, 470)

    # --- construction --------------------------------------------------------
    def _row(self, lay, label, help_text, control, last=False, help_lines=1):
        row = QFrame(objectName="row")
        if last:
            row.setStyleSheet("QFrame#row { border:none; }")
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 7, 0, 7)
        h.setSpacing(14)
        v = QVBoxLayout()
        v.setSpacing(0)
        v.addWidget(QLabel(label, objectName="lbl"))
        hl = QLabel(help_text, objectName="hlp", wordWrap=True)
        if help_lines > 1:
            hl.setMinimumHeight(hl.fontMetrics().lineSpacing() * help_lines + 2)
            hl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        v.addWidget(hl)
        h.addLayout(v, 1)
        if control is not None:
            h.addWidget(control, 0, Qt.AlignVCenter)
        lay.addWidget(row)
        return hl

    def _page(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.stack.addWidget(w)
        return lay

    def _build_pages(self):
        c = self.ctrl.cfg
        r = c["rappels_minutes"]
        drop = lambda: self.ctrl.sounds.play("goutte")  # noqa: E731

        # Rappels
        lay = self._page()
        self.s_first = Stepper(r["soif_1"], 5, 5, 180, lambda v: f"{v} min", on_click=drop)
        self.s_first.changed.connect(lambda _: self._save_reminders())
        self._row(lay, t("Premier rappel"), t("Minutes sans boire avant que la fleur ait soif."), self.s_first)
        self.s_gap = Stepper(max(5, r["soif_2"] - r["soif_1"]), 5, 5, 60, lambda v: f"{v} min", on_click=drop)
        self.s_gap.changed.connect(lambda _: self._save_reminders())
        self._row(lay, t("Puis toutes les"), t("Écart entre chaque niveau de soif."), self.s_gap)
        self.seg = Segment([(k, t(v)) for k, v in INSIST], c["insistance"])
        self.ins_help = self._row(lay, t("Insistance"), t(INSIST_HELP.get(c["insistance"], "")), self.seg, help_lines=2)
        self.seg.changed.connect(self._on_insist)
        box = QFrame(objectName="row")
        box.setStyleSheet("QFrame#row { border:none; }")
        bl = QVBoxLayout(box)
        bl.setContentsMargins(0, 7, 0, 7)
        bl.setSpacing(0)
        bl.addWidget(QLabel(t("Ne pas déranger"), objectName="lbl"))
        bl.addWidget(QLabel(t("Durées proposées dans le menu."), objectName="hlp"))
        chips = QHBoxLayout()
        chips.setContentsMargins(0, 6, 0, 0)
        chips.setSpacing(6)
        self.chips = {}
        for m in NDP_CHOICES:
            b = QPushButton(fmt_min(m), objectName="chip", checkable=True)
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(28)
            b.ensurePolished()
            b.setMinimumWidth(b.fontMetrics().horizontalAdvance(b.text()) + 34)  # sinon « 30 min » est rogné
            b.clicked.connect(self._save_ndp)
            self.chips[m] = b
            chips.addWidget(b)
        chips.addStretch()
        bl.addLayout(chips)
        lay.addWidget(box)
        lay.addStretch()

        # Hydratation
        lay = self._page()
        self.s_goal = Stepper(c["objectif_cl"], 25, 50, 800, fmt_l, water=True, on_click=drop)
        self.goal_help = self._row(lay, t("Objectif du jour"), "", self.s_goal)
        self.s_goal.changed.connect(lambda v: self._save("objectif_cl", v))
        self.s_glass = Stepper(c["verre_cl"], 5, 5, 150, lambda v: f"{v} cl", water=True, on_click=drop)
        self._row(lay, t("Bouton « + verre »"), t("Volume ajouté depuis la pop-up."), self.s_glass)
        self.s_glass.changed.connect(lambda v: self._save("verre_cl", v))
        self.s_reset = Stepper(c["heure_reset"], 1, 0, 23, fmt_hour, on_click=drop)
        self._row(lay, t("Nouvelle journée"), t("Le compteur repart à zéro à cette heure."), self.s_reset, last=True)
        self.s_reset.changed.connect(lambda v: self._save("heure_reset", v))
        lay.addStretch()

        # Fleur et son
        lay = self._page()
        self.sl_size = QSlider(Qt.Horizontal, minimum=60, maximum=200, singleStep=10, pageStep=10)
        self.sl_size.setFixedWidth(CONTROL_W)
        self.size_help = self._row(lay, t("Taille de la fleur"), "", self.sl_size)
        self.sl_size.valueChanged.connect(self._on_size)
        vol = QWidget()
        vol.setFixedWidth(CONTROL_W)
        vl = QHBoxLayout(vol)
        vl.setContentsMargins(0, 0, 0, 0)
        self.sl_vol = QSlider(Qt.Horizontal, minimum=0, maximum=100, singleStep=5, pageStep=10)
        vl.addWidget(self.sl_vol, 1)
        test = QPushButton("▶", objectName="chip")
        test.setToolTip(t("Tester"))
        test.setCursor(Qt.PointingHandCursor)
        test.setFixedSize(36, 28)
        test.clicked.connect(lambda: self.ctrl.sounds.play("soif_1"))
        vl.addWidget(test)
        self.vol_help = self._row(lay, t("Volume"), "", vol, last=True)
        self.sl_vol.valueChanged.connect(self._on_volume)
        lay.addStretch()

        # Ma plante : la plante en grand, l'avancée en XP, puis l'étagère de la collection
        lay = self._page()
        top = QHBoxLayout()
        top.setSpacing(16)
        stage = QFrame(objectName="stage")
        sl = QVBoxLayout(stage)
        sl.setContentsMargins(10, 8, 10, 8)
        self.badge = Badge(112)
        sl.addWidget(self.badge, 0, Qt.AlignCenter)
        top.addWidget(stage, 0)
        info = QVBoxLayout()
        info.setSpacing(0)
        info.addStretch()
        self.plant_name = QLabel("", objectName="level")
        self.xp_level = QLabel("", objectName="hlp")
        info.addWidget(self.plant_name)
        info.addWidget(self.xp_level)
        self.xp_box = QWidget()  # barre d'XP : cachée en mode collection
        xl = QVBoxLayout(self.xp_box)
        xl.setContentsMargins(0, 0, 0, 0)
        xl.setSpacing(0)
        xl.addSpacing(8)
        self.xp_bar = XpBar()
        xl.addWidget(self.xp_bar)
        xl.addSpacing(6)
        self.xp_next = QLabel("", objectName="next")
        xl.addWidget(self.xp_next)
        info.addWidget(self.xp_box)
        info.addStretch()
        top.addLayout(info, 1)
        lay.addLayout(top)
        lay.addSpacing(12)
        shelf = QHBoxLayout()
        shelf.setSpacing(4)
        self.slots = {}
        for pid in SKINS:
            slot = Slot(pid)
            slot.clicked.connect(lambda _=False, pid=pid: self._on_plant(pid))
            shelf.addWidget(slot)
            self.slots[pid] = slot
        shelf.addStretch()
        lay.addLayout(shelf)
        lay.addSpacing(4)
        lay.addWidget(QLabel(t("Clique une plante pour la mettre en pot"), objectName="hlp"))
        self.rules = QWidget()
        rl = QVBoxLayout(self.rules)
        rl.setContentsMargins(0, 6, 0, 0)
        rl.setSpacing(0)
        rl.addWidget(QLabel(t("1re gorgée du jour +5 · chaque gorgée +1 · chaque verre +3"), objectName="hlp"))
        rl.addWidget(QLabel(t("Joue le jeu : clique seulement quand tu bois vraiment, sinon c'est dommage."), objectName="fine"))
        lay.addWidget(self.rules)
        lay.addStretch()
        self.tg_all = Toggle(bool(c.get("tout_debloque")))
        self._row(lay, t("Tout débloquer"), t("Désactive l'XP : toutes les plantes sont disponibles."), self.tg_all, last=True)
        self.tg_all.toggled.connect(self._on_all)

        # Système
        lay = self._page()
        self.key = KeyField(c["raccourci_recuperer"])
        self.key_help = self._row(lay, t("Ramener la fleur"), t("Clique, puis appuie sur ta combinaison."), self.key)
        self.key.started.connect(self.ctrl.hotkey.unregister)  # sinon Windows avale le raccourci actuel
        self.key.cancelled.connect(self.ctrl.register_hotkey)
        self.key.captured.connect(self._on_hotkey)
        self.tg_auto = Toggle(bool(c["demarrage_windows"]))
        self.tg_auto.toggled.connect(self.ctrl.toggle_autostart)
        self._row(lay, t("Lancer au démarrage"), t("Petite Soif démarre avec Windows."), self.tg_auto, last=True)
        links = QHBoxLayout()
        links.setContentsMargins(0, 10, 0, 0)
        links.setSpacing(18)
        for text, path in ((t("Ouvrir le dossier de mes données"), cfgmod.USER_DIR),
                           (t("Réglages avancés (config.json)"), cfgmod.CONFIG_PATH)):
            links.addWidget(self._link(text, lambda p=path: winapi.open_path(p)))
        links.addStretch()
        lay.addLayout(links)
        lay.addStretch()

        # À propos
        lay = self._page()
        lay.addStretch()
        self.big_badge = Badge(120)
        lay.addWidget(self.big_badge, 0, Qt.AlignHCenter)
        lay.addWidget(QLabel("Petite Soif", objectName="title"), 0, Qt.AlignHCenter)
        pill = QLabel(f"v{cfgmod.__version__}", objectName="pill")
        pill.setFixedHeight(22)
        lay.addWidget(pill, 0, Qt.AlignHCenter)
        lay.addSpacing(4)
        lay.addWidget(QLabel(t("La petite fleur de ton bureau qui a soif quand tu oublies de boire."),
                             objectName="hlp"), 0, Qt.AlignHCenter)
        lay.addSpacing(6)
        lay.addWidget(QLabel("🛡️ Tyler / Ben", objectName="lbl"), 0, Qt.AlignHCenter)
        row = QHBoxLayout()
        row.setSpacing(18)
        row.addStretch()
        row.addWidget(self._link(t("Code source sur GitHub"), lambda: self._open_url(cfgmod.REPO_URL)))
        row.addWidget(self._link(t("Signaler un bug"), self._report_bug))
        row.addWidget(self._link(t("Vérifier les mises à jour"), lambda: self._open_url(f"{cfgmod.REPO_URL}/releases/latest")))
        row.addWidget(self._link(t("Journal d'erreurs"), self._open_log))
        row.addStretch()
        lay.addSpacing(4)
        lay.addLayout(row)
        lay.addSpacing(4)
        lay.addWidget(QLabel(t("Licence MIT · tes données restent sur ton PC"), objectName="hlp"), 0, Qt.AlignHCenter)
        lay.addStretch()

        self.refresh()

    def _link(self, text, slot):
        b = QPushButton(text, objectName="link")
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(slot)
        return b

    # --- état ----------------------------------------------------------------
    def refresh(self):
        """Recopie la config courante dans les contrôles (sans rien réécrire)."""
        c = self.ctrl.cfg
        r = c["rappels_minutes"]
        self.s_first.set_value(r["soif_1"])
        self.s_gap.set_value(max(5, r["soif_2"] - r["soif_1"]))
        self.seg.set_value(c["insistance"])
        self.ins_help.setText(t(INSIST_HELP.get(c["insistance"], "")))
        for m, b in self.chips.items():
            b.setChecked(m in c["ne_pas_deranger_minutes"])
        self.s_goal.set_value(c["objectif_cl"])
        self.s_glass.set_value(c["verre_cl"])
        self.s_reset.set_value(c["heure_reset"])
        self._goal_text()
        for sl, v in ((self.sl_size, round(c["echelle"] * 100)), (self.sl_vol, round(c["volume"] * 100))):
            sl.blockSignals(True)
            sl.setValue(v)
            sl.blockSignals(False)
        self.size_help.setText(f"{self.sl_size.value()} %")
        self.vol_help.setText(t("Rappels et gorgées · {v} %", v=self.sl_vol.value()))
        self.key.set_hotkey(c["raccourci_recuperer"])
        self.tg_auto.blockSignals(True)
        self.tg_auto.setChecked(bool(c["demarrage_windows"]))
        self.tg_auto.blockSignals(False)
        self._refresh_xp()

    def _refresh_xp(self):
        xp = self.ctrl.xp()
        allu = bool(self.ctrl.cfg.get("tout_debloque"))
        level = len(SKINS) - 1 if allu else plant_level(xp)
        cur = self.ctrl.cfg.get("plante") or "classique"
        self.tg_all.blockSignals(True)
        self.tg_all.setChecked(allu)
        self.tg_all.blockSignals(False)
        self.xp_box.setVisible(not allu)
        self.rules.setVisible(not allu)
        self.plant_name.setText(plant_name(cur))
        if allu:
            self.xp_level.setText(t("Mode collection · toutes les plantes sont débloquées"))
        else:
            self.xp_level.setText(t("Niveau {n} · {xp} XP gagnés", n=level + 1, xp=xp))
            if level + 1 < len(SKINS):
                goal = (level + 1) * XP_TIER
                self.xp_bar.ratio = (xp - level * XP_TIER) / XP_TIER
                self.xp_next.setText(t("{left} XP avant la prochaine plante", left=goal - xp))
            else:
                self.xp_bar.ratio = 1.0
                self.xp_next.setText(t("Toutes les plantes sont débloquées 🎉"))
            self.xp_bar.update()
        for i, pid in enumerate(SKINS):
            ready = plant_ready(pid)
            if i <= level:
                state, tip = "open", plant_name(pid) if ready else t("{name} (bientôt)", name=plant_name(pid))
            elif i == level + 1:
                state, tip = "next", t("??? · à {xp} XP", xp=i * XP_TIER)
            else:
                state, tip = "hidden", t("à {xp} XP", xp=i * XP_TIER)
            self.slots[pid].set_state(state, ready, pid == cur, tip)

    def _on_plant(self, pid):
        slot = self.slots[pid]
        if slot.state != "open" or not slot.ready or pid == self.ctrl.cfg.get("plante"):
            return
        self._save("plante", pid)
        art.set_skin(pid)
        self.badge.update()
        self.side_badge.update()
        self.big_badge.update()
        self.ctrl.refresh_icons()
        self.ctrl.flower.update()
        self.ctrl.flower.celebrate()
        self._refresh_xp()

    def _confirm_box(self):
        """Confirmation du mode collection ; chaque bouton est élargi à son texte (sinon il le rogne)."""
        box = QMessageBox(self)
        box.setWindowTitle("Petite Soif")
        box.setText(t("Tout débloquer ?"))
        box.setInformativeText(t("Gagner les plantes une à une, c'est une partie du fun.\nTu es sûr de vouloir sauter l'étape ?"))
        no = box.addButton(t("Non, je garde le suspense"), QMessageBox.RejectRole)
        yes = box.addButton(t("Oui, tout débloquer"), QMessageBox.AcceptRole)
        box.setDefaultButton(no)
        for b in (no, yes):
            b.ensurePolished()
            b.setMinimumWidth(b.fontMetrics().horizontalAdvance(b.text()) + 44)
        return box, no, yes

    def _on_all(self, on):
        if on:
            box, no, yes = self._confirm_box()
            box.exec()
            if box.clickedButton() is not yes:
                self.tg_all.blockSignals(True)
                self.tg_all.setChecked(False)
                self.tg_all.blockSignals(False)
                return
        self._save("tout_debloque", bool(on))
        self.ctrl.flower.set_news(self.ctrl.has_news())
        self.news_dot.setVisible(self.ctrl.has_news())
        self._refresh_xp()

    def on_xp_changed(self):
        """Appelé par le contrôleur après une gorgée / un verre : l'onglet suit en direct."""
        self._refresh_xp()
        if self.isVisible() and TABS[self.stack.currentIndex()][1] == "Ma plante":
            self.ctrl.mark_plants_seen()
            self.news_dot.hide()
        else:
            self.news_dot.setVisible(self.ctrl.has_news())

    def _goal_text(self):
        n = self.s_goal.value / max(1, self.s_glass.value)
        self.goal_help.setText(t("≈ {n} verre{s} de {cl} cl", n=round(n), s="s" if round(n) > 1 else "",
                                es="es" if round(n) > 1 else "", cl=self.s_glass.value))

    def _show_tab(self, i):
        if TABS[i][1] == "Ma plante":
            self._refresh_xp()
            self.ctrl.mark_plants_seen()
            self.news_dot.hide()
        self.stack.setCurrentIndex(i)
        self.title.setText("" if i == len(TABS) - 1 else t(TABS[i][1]))

    # --- enregistrement --------------------------------------------------------
    def _save(self, key, value):
        self.ctrl.cfg[key] = value
        cfgmod.save_key(key, value)
        self.ctrl.schedule_reload()
        if key in ("objectif_cl", "verre_cl"):
            self._goal_text()

    def _save_reminders(self):
        r = dict(self.ctrl.cfg["rappels_minutes"])
        a, g = self.s_first.value, self.s_gap.value
        r.update(soif_1=a, soif_2=a + g, soif_3=a + 2 * g)
        self._save("rappels_minutes", r)

    def _save_ndp(self):
        others = [m for m in self.ctrl.cfg["ne_pas_deranger_minutes"] if m not in NDP_CHOICES]  # valeurs perso du JSON
        self._save("ne_pas_deranger_minutes", sorted(others + [m for m, b in self.chips.items() if b.isChecked()]))

    def _on_insist(self, key):
        self.ins_help.setText(t(INSIST_HELP[key]))
        self.badge.play(key)
        self._save("insistance", key)

    def _bubble(self, value, lo, hi):
        now = time.monotonic()
        if now - self._last_bubble > 0.08:  # un petit "plic" à chaque cran, pas une rafale
            self._last_bubble = now
            i = min(4, int((value - lo) / (hi - lo + 1e-9) * 5))
            self.ctrl.sounds.play(f"eau_{i}")

    def _on_size(self, v):
        v = round(v / 10) * 10
        self.size_help.setText(f"{v} %")
        self._bubble(v, 60, 200)
        self._save("echelle", v / 100)

    def _on_volume(self, v):
        v = round(v / 5) * 5
        self.vol_help.setText(t("Rappels et gorgées · {v} %", v=v))
        self.ctrl.sounds.volume = v / 100  # le "plic" suit le volume choisi
        self._bubble(v, 0, 100)
        self._save("volume", v / 100)

    def _on_hotkey(self, text):
        ok = self.ctrl.register_hotkey(text, quiet=True)
        if ok:
            self.key.set_hotkey(text)
            self.key_help.setText(t("Clique, puis appuie sur ta combinaison."))
            self._save("raccourci_recuperer", text)
        else:
            self.key.set_hotkey(self.key.hotkey, bad=True)
            self.key_help.setText(t("{k} est déjà pris, essaies-en une autre.", k=winapi.pretty_hotkey(text)))
            self.ctrl.register_hotkey()

    def _reset(self):
        answer = QMessageBox.question(self, "Petite Soif", t("Tout remettre par défaut ?\n\n"
                                      "(Le lancement au démarrage de Windows ne change pas.)"))
        if answer != QMessageBox.Yes:
            return
        cfgmod.reset_defaults()
        self.ctrl.reload_config()
        self.refresh()

    # --- liens -----------------------------------------------------------------
    def _open_url(self, url):
        QDesktopServices.openUrl(QUrl(url))  # ouvert par le navigateur, l'appli ne se connecte à rien

    def _report_bug(self):
        self._open_url(report_bug_url())

    def _open_log(self):
        if cfgmod.LOG_PATH.exists():
            winapi.open_path(cfgmod.LOG_PATH)
        else:
            QMessageBox.information(self, "Petite Soif", t("Aucune erreur enregistrée pour l'instant."))

    # --- fenêtre sans barre : déplacement, Échap ----------------------------------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self.windowHandle():
            self.windowHandle().startSystemMove()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(e)

    def sizeHint(self):
        return QSize(772, 470)
