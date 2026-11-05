"""Contrôleur : timer de soif, escalade des rappels, absence, ne pas déranger, tray, raccourci."""
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QLockFile, QObject, QPoint, QPointF, QTimer
from PySide6.QtGui import QAction, QActionGroup, QCursor, QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QMenu, QMessageBox, QSystemTrayIcon

from . import config as cfgmod
from . import painter as art
from . import winapi
from .flower import FlowerWidget, MARGIN
from .popup import StatsPopup, fmt_l
from .sounds import SoundPlayer
from .storage import Storage


def _install_error_log():
    cfgmod.DATA_DIR.mkdir(parents=True, exist_ok=True)

    def hook(etype, value, tb):
        with open(cfgmod.LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n--- {datetime.now():%Y-%m-%d %H:%M:%S} ---\n")
            f.write("".join(traceback.format_exception(etype, value, tb)))

    sys.excepthook = hook


def _icon(thirst=0.0, sleeping=False):
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    sc = 60 / 142
    p.translate((64 - art.BODY_W * sc) / 2, 2 + 10 * sc)
    p.scale(sc, sc)
    art.draw_body(p, thirst, sleeping=sleeping)
    p.end()
    return QIcon(pm)


class Controller(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app
        first_run = cfgmod.is_first_run()
        self.cfg, err = cfgmod.load()
        self.storage = Storage(cfgmod.DB_PATH, self.cfg["heure_reset"])
        self.sounds = SoundPlayer(cfgmod.SOUNDS_DIR, self.cfg["volume"])

        self.flower = FlowerWidget(self.cfg["echelle"], self.cfg["appui_long_ms"], self.cfg["decalage_curseur_px"])
        home = self.storage.get_state("home")
        if home:
            x, y = (int(v) for v in home.split(","))
            self.flower.set_home(QPoint(x, y))
        else:
            self.flower.set_home(self._default_home())

        now = time.time()
        last = self.storage.last_event_ts(("gorgee", "verre")) or 0
        self.ref = max(last, self.storage.last_boundary(), now if self.cfg["reset_timer_au_lancement"] else 0)
        self.fired_level = 0
        self.last_repeat = 0.0
        self.next_boundary = self.storage.next_boundary()
        self.dnd_until = float(self.storage.get_state("ndp_jusqua", "0"))
        self._fallback_pos = QCursor.pos()
        self._fallback_t = now
        self._popup = None
        self._tooltip = ""
        self._icon_state = None

        self.flower.drink_started.connect(lambda: self.sounds.play("glouglou"))
        self.flower.drink_cancelled.connect(lambda: self.sounds.stop("glouglou"))
        self.flower.drank.connect(lambda: self.register_drink(glass=False))
        self.flower.menu_requested.connect(self.open_popup)
        self.flower.home_changed.connect(self._save_home)
        self.flower.poofed.connect(lambda: self.sounds.play("poof"))

        self._build_tray()
        self.flower.show()
        self._hwnd = int(self.flower.winId())
        winapi.make_overlay(self._hwnd)

        self.hotkey = winapi.GlobalHotkey(self.recall)
        app.installNativeEventFilter(self.hotkey)
        self._register_hotkey()

        if first_run and winapi.IS_WIN:
            answer = QMessageBox.question(
                None, "Petite Soif",
                "Lancer Petite Soif automatiquement au démarrage de Windows ?\n\n"
                "Modifiable à tout moment via l'icône près de l'horloge.",
            )
            self.cfg["demarrage_windows"] = answer == QMessageBox.Yes
            cfgmod.save_key("demarrage_windows", self.cfg["demarrage_windows"])
            self.act_autostart.setChecked(self.cfg["demarrage_windows"])
            self.tray.showMessage("Petite Soif", "Je suis là ! Clic droit sur moi pour voir ta journée, "
                                  "clic gauche maintenu quand tu bois.")
        try:
            # réécrit le chemin à chaque lancement : suit le .exe s'il a été déplacé
            winapi.set_autostart(bool(self.cfg["demarrage_windows"]), cfgmod.ENTRY_SCRIPT)
        except Exception:
            pass

        if err:
            self.tray.showMessage("Petite Soif", f"config.json illisible, valeurs par défaut utilisées.\n{err}")

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.tick()

    # --- utilitaires ------------------------------------------------------
    def _default_home(self):
        g = QGuiApplication.primaryScreen().availableGeometry()
        return QPoint(g.right() - self.flower.width() - 20, g.bottom() - self.flower.height() - 10)

    def _save_home(self, point):
        self.storage.set_state("home", f"{point.x()},{point.y()}")

    def _idle(self):
        idle = winapi.idle_seconds()
        if idle is not None:
            return idle
        pos = QCursor.pos()  # repli hors Windows : souris seulement
        if pos != self._fallback_pos:
            self._fallback_pos = pos
            self._fallback_t = time.time()
        return time.time() - self._fallback_t

    def _level(self, elapsed_min):
        r = self.cfg["rappels_minutes"]
        if elapsed_min >= r["soif_3"]:
            return 3
        if elapsed_min >= r["soif_2"]:
            return 2
        if elapsed_min >= r["soif_1"]:
            return 1
        return 0

    def _register_hotkey(self):
        key = self.cfg["raccourci_recuperer"]
        ok = self.hotkey.register(key, int(self.flower.winId()))
        if winapi.IS_WIN and not ok:
            self.tray.showMessage("Petite Soif", f"Le raccourci {winapi.pretty_hotkey(key)} est indisponible "
                                  "(déjà pris ou invalide). Change-le dans config.json.")
        self.act_recall.setText(f"Récupérer la fleur ({winapi.pretty_hotkey(key)})")

    # --- boucle principale -----------------------------------------------
    def _keep_on_top(self):
        popup_open = False
        if self._popup is not None:
            try:
                popup_open = self._popup.isVisible()
            except RuntimeError:
                popup_open = False
        if not popup_open and self.flower.isVisible():
            winapi.force_topmost(self._hwnd)

    def tick(self):
        now = time.time()
        self._keep_on_top()
        if now >= self.next_boundary:  # 6 h : nouvelle journée
            self.ref = max(self.ref, self.storage.last_boundary())
            self.fired_level = 0
            self.next_boundary = self.storage.next_boundary()
            if self.flower.mode != "home":
                self.flower.go_home()

        level = self._level((now - self.ref) / 60)
        idle = self._idle()
        absent = idle >= self.cfg["absence_minutes"] * 60
        dnd = now < self.dnd_until

        self.flower.set_thirst(level)
        self.flower.set_sleeping(dnd)
        self._update_tray(level, dnd)

        if dnd:
            if self.flower.mode in ("follow", "dock", "hold"):
                self.flower.go_home()
            return

        mode = self.flower.mode
        if level > self.fired_level:
            self._fire(level, absent)
        elif level == 3:
            rep = self.cfg["rappels_minutes"]["repetition"] * 60
            if mode == "dock":
                if not absent:  # retour à l'ordinateur
                    self._fire(3, False)
                else:
                    self.flower.wake()
            elif absent and mode == "home":
                self.flower.dock()
            elif mode == "home" and now - self.last_repeat >= rep and idle < rep:
                self._fire(3, False)

    def _fire(self, level, absent):
        self.fired_level = max(self.fired_level, level)
        self.last_repeat = time.time()
        self.storage.log("rappel", detail=str(level))
        if level == 1:
            self.sounds.play("soif_1")
        elif level == 2:
            self.sounds.play("soif_2")
            self.flower.agitate()
        elif level == 3:
            self.sounds.play("soif_3")
            if absent:
                self.flower.dock()
            else:
                self.flower.follow(self.cfg["poursuite_secondes"])

    # --- actions ----------------------------------------------------------
    def register_drink(self, glass):
        now = time.time()
        self.ref = now
        self.fired_level = 0
        self.last_repeat = now
        if glass:
            self.storage.log("verre", cl=self.cfg["verre_cl"])
            self.flower.celebrate()
        else:
            self.storage.log("gorgee")
        self.sounds.play("valide")
        self.flower.set_thirst(0)
        if self.flower.mode in ("follow", "dock", "hold"):
            self.flower.hold()
            QTimer.singleShot(1000, self.flower.go_home)
        self._tooltip = ""
        self._update_tray(0, time.time() < self.dnd_until)

    def add_glass(self):
        self.register_drink(glass=True)

    def undo_glass(self):
        self.storage.undo_last_glass()
        self._tooltip = ""
        self._update_tray(self.flower.thirst_target, time.time() < self.dnd_until)

    def recall(self):
        home = self._default_home()
        self._save_home(home)
        self.flower.recall(home)

    def set_dnd(self, minutes=None, until_reset=False):
        now = time.time()
        self.dnd_until = self.storage.next_boundary() if until_reset else now + minutes * 60
        self.storage.set_state("ndp_jusqua", self.dnd_until)
        self.storage.log("ndp", detail="sommeil" if until_reset else f"{minutes} min")
        self.tick()

    def resume(self):
        self.dnd_until = 0.0
        self.storage.set_state("ndp_jusqua", 0)
        self.tick()

    def stats(self):
        now = time.time()
        last = self.storage.last_event_ts(("gorgee", "verre"))
        last_today = last is not None and self.storage.day_key(last) == self.storage.day_key(now)
        dnd_text = ""
        if now < self.dnd_until:
            dnd_text = f"💤 Ne pas déranger jusqu'à {datetime.fromtimestamp(self.dnd_until):%H:%M}"
        return {
            "reset_hour": self.cfg["heure_reset"],
            "total_cl": self.storage.total_cl(),
            "goal_cl": self.cfg["objectif_cl"],
            "glass_cl": self.cfg["verre_cl"],
            "sips": self.storage.count("gorgee"),
            "glasses": self.storage.count("verre"),
            "last_min": int((now - last) / 60) if last_today else None,
            "week": self.storage.totals_by_day(7),
            "avg_cl": self.storage.average_cl(7),
            "dnd_text": dnd_text,
        }

    def open_popup(self, point=None):
        if self._popup is not None:
            try:
                self._popup.close()
            except RuntimeError:
                pass
        self._popup = StatsPopup(self)
        self._popup.destroyed.connect(lambda *_: setattr(self, "_popup", None))
        self._popup.show_near(point or QCursor.pos())

    def export_csv(self):
        default = str(Path.home() / f"petite_soif_{datetime.now():%Y%m%d}.csv")
        path, _ = QFileDialog.getSaveFileName(None, "Exporter l'historique", default, "CSV (*.csv)")
        if path:
            n = self.storage.export_csv(path)
            self.tray.showMessage("Petite Soif", f"{n} événements exportés.")

    def reload_config(self):
        self.cfg, err = cfgmod.load()
        self.storage.reset_hour = int(self.cfg["heure_reset"])
        self.next_boundary = self.storage.next_boundary()
        self.sounds.set_volume(self.cfg["volume"])
        self.flower.set_scale(self.cfg["echelle"])
        winapi.make_overlay(self._hwnd)
        self.flower.long_press_ms = int(self.cfg["appui_long_ms"])
        self.flower.cursor_offset = int(self.cfg["decalage_curseur_px"])
        self._register_hotkey()
        self._rebuild_dnd_menu()
        self.act_autostart.setChecked(bool(self.cfg["demarrage_windows"]))
        self.tray.showMessage("Petite Soif", f"config.json illisible : {err}" if err else "Configuration rechargée.")

    def toggle_autostart(self, checked):
        try:
            winapi.set_autostart(checked, cfgmod.ENTRY_SCRIPT)
        except Exception:
            pass
        self.cfg["demarrage_windows"] = checked
        cfgmod.save_key("demarrage_windows", checked)

    # --- zone de notification --------------------------------------------
    def _build_tray(self):
        self.tray = QSystemTrayIcon(_icon(0), self.app)
        menu = QMenu()
        menu.addAction("Voir ma journée", lambda: self.open_popup(QCursor.pos()))
        self.act_recall = menu.addAction("Récupérer la fleur", self.recall)
        menu.addSeparator()
        self.dnd_menu = menu.addMenu("Ne pas déranger")
        self._rebuild_dnd_menu()
        menu.addSeparator()
        menu.addAction("Exporter l'historique (CSV)…", self.export_csv)
        menu.addAction("Ouvrir config.json", lambda: winapi.open_path(cfgmod.CONFIG_PATH))
        menu.addAction("Ouvrir le dossier de mes données", lambda: winapi.open_path(cfgmod.USER_DIR))
        menu.addAction("Recharger la configuration", self.reload_config)
        self.act_autostart = QAction("Lancer au démarrage de Windows", menu, checkable=True)
        self.act_autostart.setChecked(bool(self.cfg["demarrage_windows"]))
        self.act_autostart.toggled.connect(self.toggle_autostart)
        menu.addAction(self.act_autostart)
        menu.addSeparator()
        about = menu.addAction(f"Petite Soif v{cfgmod.__version__}")
        about.setEnabled(False)
        menu.addAction("Quitter", self.app.quit)
        self.tray_menu = menu
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda reason: self.open_popup(QCursor.pos()) if reason == QSystemTrayIcon.Trigger else None
        )
        self.tray.show()

    def _rebuild_dnd_menu(self):
        m = self.dnd_menu
        m.clear()
        for minutes in self.cfg["ne_pas_deranger_minutes"]:
            label = f"{minutes} min" if minutes < 60 else (f"{minutes // 60} h" if minutes % 60 == 0 else f"{minutes // 60} h {minutes % 60:02d}")
            m.addAction(label, lambda mm=minutes: self.set_dnd(minutes=mm))
        m.addAction(f"Sommeil jusqu'à {self.cfg['heure_reset']} h", lambda: self.set_dnd(until_reset=True))
        m.addSeparator()
        self.act_resume = m.addAction("Reprendre maintenant", self.resume)

    def _update_tray(self, level, dnd):
        state = (level, dnd)
        if state != self._icon_state:
            self._icon_state = state
            self.tray.setIcon(_icon(level, dnd))
            self.act_resume.setEnabled(dnd)
        total = self.storage.total_cl()
        tip = f"Petite Soif — {fmt_l(total)} / {fmt_l(self.cfg['objectif_cl'])}"
        if dnd:
            tip += f"\nNe pas déranger jusqu'à {datetime.fromtimestamp(self.dnd_until):%H:%M}"
        if tip != self._tooltip:
            self._tooltip = tip
            self.tray.setToolTip(tip)


def run():
    _install_error_log()
    app = QApplication(sys.argv)
    app.setApplicationName("Petite Soif")
    app.setQuitOnLastWindowClosed(False)
    cfgmod.USER_DIR.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(cfgmod.USER_DIR / "instance.lock"))
    if not lock.tryLock(100):
        QMessageBox.information(None, "Petite Soif", "Petite Soif tourne déjà (icône près de l'horloge).")
        return
    ctrl = Controller(app)  # noqa: F841 (garder la référence)
    code = app.exec()
    ctrl.hotkey.unregister()
    lock.unlock()
    sys.exit(code)
