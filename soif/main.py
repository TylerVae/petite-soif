"""Contrôleur : timer de soif, escalade des rappels, absence, ne pas déranger, tray, raccourci."""
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QLocale, QLockFile, QObject, QPoint, QTimer, QUrl
from PySide6.QtGui import QCursor, QDesktopServices, QFontDatabase, QBitmap, QGuiApplication, QIcon, QPainter, QPixmap, QRegion
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QMenu, QMessageBox, QSystemTrayIcon

from . import config as cfgmod
from . import i18n
from .i18n import t
from . import settings as settings_mod
from . import painter as art
from . import osapi
from .flower import FlowerWidget
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
    """Plante actuelle, recadrée au plus près pour remplir l'icône (les marges du dessin en font perdre la moitié)."""
    big = QPixmap(256, 256)
    big.fill(Qt.transparent)
    p = QPainter(big)
    p.setRenderHint(QPainter.Antialiasing)
    sc = 240 / art.BODY_H
    p.translate((256 - art.BODY_W * sc) / 2, 8)
    p.scale(sc, sc)
    art.draw_body(p, thirst, sleeping=sleeping)
    p.end()
    box = QRegion(QBitmap.fromImage(big.toImage().createAlphaMask())).boundingRect()
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    if not box.isEmpty():
        crop = big.copy(box).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        p = QPainter(pm)
        p.drawPixmap((64 - crop.width()) // 2, (64 - crop.height()) // 2, crop)
        p.end()
    return QIcon(pm)


MAX_REPEATS_NO_IDLE = 5


class Controller(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app
        first_run = cfgmod.is_first_run()
        no_lang = first_run or not cfgmod.has_key("langue")  # 1er lancement, ou config d'une V1 (sans langue)
        self.cfg, err = cfgmod.load()
        if no_lang and not QLocale.system().name().lower().startswith("fr"):
            self.cfg["langue"] = "en"
            cfgmod.save_key("langue", "en")
        i18n.lang = self.cfg["langue"] if self.cfg["langue"] in ("fr", "en") else "fr"
        self.storage = Storage(cfgmod.DB_PATH, self.cfg["heure_reset"])
        self.sounds = SoundPlayer(cfgmod.SOUNDS_DIR, self.cfg["volume"])
        self._built_volume = self.cfg["volume"]

        art.set_skin(self.cfg.get("plante"))
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
        self.repeats = 0  # rappels répétés depuis la dernière gorgée (plafonnés si l'inactivité n'est pas mesurable)
        self.next_boundary = self.storage.next_boundary()
        self.dnd_until = float(self.storage.get_state("ndp_jusqua", "0"))
        self._fallback_pos = QCursor.pos()
        self._fallback_t = now
        self._popup = None
        self._settings = None
        self._hotkey_text = None
        self._tooltip = ""
        self._icon_state = None

        self.flower.drink_started.connect(lambda: self.sounds.play("glouglou"))
        self.flower.drink_cancelled.connect(lambda: self.sounds.stop("glouglou"))
        self.flower.drank.connect(lambda: self.register_drink(glass=False))
        self.flower.menu_requested.connect(self.open_popup)
        self.flower.home_changed.connect(self._save_home)
        self.flower.poofed.connect(lambda: self.sounds.play("poof"))
        self.flower.settings_requested.connect(self.open_settings)
        self.flower.dnd_requested.connect(self.toggle_dnd)
        self.flower.title_font = settings_mod.FAMILY
        self.flower.set_news(self.has_news())

        self._build_tray()
        self.flower.show()
        self._hwnd = int(self.flower.winId())
        osapi.make_overlay(self._hwnd)

        self.hotkey = osapi.GlobalHotkey(self.recall)
        app.installNativeEventFilter(self.hotkey)
        self.register_hotkey()

        # config.json modifié (par la fenêtre de paramètres ou à la main) : rechargé tout seul
        self._reload_timer = QTimer(self, singleShot=True, interval=250, timeout=self.reload_config)
        self._watcher = QFileSystemWatcher([str(cfgmod.CONFIG_PATH)], self)
        self._watcher.fileChanged.connect(self._on_config_file)

        if first_run:
            answer = QMessageBox.question(
                None, "Petite Soif",
                t("Lancer Petite Soif automatiquement au démarrage de Windows ?\n\n"
                  "Modifiable à tout moment via l'icône près de l'horloge.") if osapi.IS_WIN else
                t("Lancer Petite Soif automatiquement à l'ouverture de session ?\n\n"
                  "Modifiable à tout moment via l'icône de la zone de notification."),
            )
            self.cfg["demarrage_windows"] = answer == QMessageBox.Yes
            cfgmod.save_key("demarrage_windows", self.cfg["demarrage_windows"])
            self.tray.showMessage("Petite Soif", t("Je suis là ! Clic droit sur moi pour voir ta journée, "
                                                   "clic gauche maintenu quand tu bois."))
        try:
            # réécrit le chemin à chaque lancement : suit le .exe s'il a été déplacé
            osapi.set_autostart(bool(self.cfg["demarrage_windows"]), cfgmod.ENTRY_SCRIPT)
        except Exception:
            pass

        if err:
            self.tray.showMessage("Petite Soif", t("config.json illisible, valeurs par défaut utilisées.") + f"\n{err}")

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
        idle = osapi.idle_seconds()
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

    def _insist(self):
        """(répétition en min, poursuite en s, tourne autour du curseur) selon l'insistance."""
        r = self.cfg["rappels_minutes"]["repetition"]
        chase = self.cfg["poursuite_secondes"]
        kind = self.cfg.get("insistance", "normale")
        if kind == "douce":
            return 5, 0, False
        if kind == "tenace":
            return r, chase * 2, True
        return r, chase, False

    def register_hotkey(self, key=None, quiet=False):
        """Enregistre le raccourci global (celui de la config par défaut). Retourne True si OK."""
        key = key or self.cfg["raccourci_recuperer"]
        ok = self.hotkey.register(key, int(self.flower.winId()))
        self._hotkey_text = key if ok else None
        if osapi.HAS_HOTKEY and not ok and not quiet:
            self.tray.showMessage("Petite Soif", t("Le raccourci {k} est indisponible (déjà pris ou invalide). "
                                                   "Change-le dans les paramètres.", k=osapi.pretty_hotkey(key)))
        self._set_recall_label(key)
        return ok

    def _set_recall_label(self, key):
        if osapi.HAS_HOTKEY:
            self.act_recall.setText(t("Récupérer la fleur ({k})", k=osapi.pretty_hotkey(key)))
        else:
            self.act_recall.setText(t("Récupérer la fleur"))

    # --- boucle principale -----------------------------------------------
    def _keep_on_top(self):
        popup_open = False
        if self._popup is not None:
            try:
                popup_open = self._popup.isVisible()
            except RuntimeError:
                popup_open = False
        if not popup_open and self.flower.isVisible():
            osapi.force_topmost(self._hwnd)

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
            rep_min, _, _ = self._insist()
            rep = rep_min * 60
            douce = self.cfg.get("insistance") == "douce"
            if mode == "dock":
                if not absent:  # retour à l'ordinateur
                    self._fire(3, False)
                else:
                    self.flower.wake()
            elif absent and mode == "home" and not douce:
                self.flower.dock()
            elif mode == "home" and now - self.last_repeat >= rep and idle < rep and self._may_repeat():
                self.repeats += 1
                self._fire(3, False)

    def _may_repeat(self):
        # Sans mesure fiable de l'inactivité (Linux sans libXss, Wayland), "idle < rep" ne prouve rien : on plafonne
        return osapi.HAS_IDLE or self.repeats < MAX_REPEATS_NO_IDLE

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
            _, chase, orbit = self._insist()
            if not chase:  # douce : elle reste à sa place et s'agite
                self.flower.agitate()
            elif absent:
                self.flower.dock()
            else:
                self.flower.follow(chase, orbit=orbit)

    # --- actions ----------------------------------------------------------
    def register_drink(self, glass):
        now = time.time()
        self.ref = now
        self.fired_level = 0
        self.last_repeat = now
        self.repeats = 0
        xp_before = self.storage.xp()
        if glass:
            gain = 3
            self.storage.log("verre", cl=self.cfg["verre_cl"])
            self.flower.celebrate()
        else:
            gain = 5 if self.storage.count("gorgee") == 0 else 1  # 1re gorgée de la journée
            self.storage.log("gorgee")
        if not self.cfg.get("tout_debloque"):  # mode collection : plus de XP à l'écran
            self.flower.show_xp(t("+{n} XP", n=gain))
            if settings_mod.plant_level(xp_before + gain) > settings_mod.plant_level(xp_before):
                self.flower.celebrate()
                self.flower.set_news(True)
        if self._settings is not None:
            self._settings.on_xp_changed()
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
        if self._settings is not None:
            self._settings.on_xp_changed()
        self._tooltip = ""
        self._update_tray(self.flower.thirst_target, time.time() < self.dnd_until)

    def report_bug(self):
        QDesktopServices.openUrl(QUrl(settings_mod.report_bug_url()))  # ouvert par le navigateur

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

    def toggle_dnd(self):
        """Bouton 💤 / 🔔 : reprend si « Ne pas déranger » est actif, sinon 30 min (les autres durées sont dans le menu de l'icône)."""
        if time.time() < self.dnd_until:
            self.resume()
        else:
            self.set_dnd(minutes=30)

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
            dnd_text = t("💤 Ne pas déranger jusqu'à {t}", t=f"{datetime.fromtimestamp(self.dnd_until):%H:%M}")
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

    def xp(self):
        return self.storage.xp()

    def has_news(self):
        """Une plante débloquée que l'utilisateur n'a pas encore vue dans « Ma plante »."""
        if self.cfg.get("tout_debloque"):
            return False
        return settings_mod.plant_level(self.storage.xp()) > int(self.storage.get_state("plante_vue", "0"))

    def mark_plants_seen(self):
        self.storage.set_state("plante_vue", str(settings_mod.plant_level(self.storage.xp())))
        self.flower.set_news(False)

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
        path, _ = QFileDialog.getSaveFileName(None, t("Exporter l'historique"), default, "CSV (*.csv)")
        if path:
            n = self.storage.export_csv(path)
            self.tray.showMessage("Petite Soif", t("{n} événements exportés.", n=n))

    def schedule_reload(self):
        self._reload_timer.start()

    def _on_config_file(self, path):
        if path not in self._watcher.files():  # certains éditeurs remplacent le fichier : on le resurveille
            self._watcher.addPath(path)
        self.schedule_reload()

    def reload_config(self):
        cfg, err = cfgmod.load()
        if err:
            self.tray.showMessage("Petite Soif", t("config.json illisible : {err}", err=err))
            return
        self.cfg = cfg
        self.storage.reset_hour = int(cfg["heure_reset"])
        self.next_boundary = self.storage.next_boundary()
        if self._built_volume != cfg["volume"]:
            self._built_volume = cfg["volume"]
            self.sounds.set_volume(cfg["volume"])
        if float(cfg["echelle"]) != self.flower.scale_:
            self.flower.set_scale(cfg["echelle"])
            osapi.make_overlay(self._hwnd)
        if cfg.get("plante") != art.SKIN:
            art.set_skin(cfg.get("plante"))
            self.flower.update()
        self.flower.long_press_ms = int(cfg["appui_long_ms"])
        self.flower.cursor_offset = int(cfg["decalage_curseur_px"])
        if cfg["raccourci_recuperer"] != self._hotkey_text and not (self._settings and self._settings.key.capturing):
            self.register_hotkey()
        if cfg["langue"] in ("fr", "en") and cfg["langue"] != i18n.lang:
            self.set_language(cfg["langue"])
        self._rebuild_dnd_menu()
        self._tooltip = ""
        self._update_tray(self.flower.thirst_target, time.time() < self.dnd_until)
        if self._popup is not None:
            try:
                self._popup.refresh()
            except RuntimeError:
                pass

    def open_settings(self):
        if self._popup is not None:
            try:
                self._popup.close()
            except RuntimeError:
                pass
        if self._settings is None:
            win = self._settings = settings_mod.SettingsWindow(self)
            # seulement si c'est encore la fenêtre courante (changement de langue = nouvelle fenêtre)
            win.destroyed.connect(lambda *_, w=win: setattr(self, "_settings", None) if self._settings is w else None)
            g = QGuiApplication.primaryScreen().availableGeometry()
            self._settings.move(g.center() - self._settings.rect().center())
        self._settings.show()
        self._settings.raise_()
        self._settings.activateWindow()

    def set_language(self, lang):
        """Change la langue : menu de l'icône refait, fenêtre de paramètres rouverte au même endroit."""
        if self.cfg.get("langue") != lang:
            self.cfg["langue"] = lang
            cfgmod.save_key("langue", lang)
        if lang == i18n.lang:
            return
        i18n.lang = lang
        self._build_menu()
        self._tooltip = ""
        self._update_tray(self.flower.thirst_target, time.time() < self.dnd_until)
        self._set_recall_label(self._hotkey_text or self.cfg["raccourci_recuperer"])
        win = self._settings
        if win is not None:
            pos, tab = win.pos(), win.stack.currentIndex()
            win.close()
            self._settings = None
            self.open_settings()
            self._settings.move(pos)
            self._settings.nav.button(tab).setChecked(True)
            self._settings._show_tab(tab)

    def toggle_autostart(self, checked):
        try:
            osapi.set_autostart(checked, cfgmod.ENTRY_SCRIPT)
        except Exception:
            pass
        self.cfg["demarrage_windows"] = checked
        cfgmod.save_key("demarrage_windows", checked)

    # --- zone de notification --------------------------------------------
    def _build_tray(self):
        self.tray = QSystemTrayIcon(_icon(0), self.app)
        self._build_menu()
        self.tray.activated.connect(
            lambda reason: self.open_popup(QCursor.pos()) if reason == QSystemTrayIcon.Trigger else None
        )
        self.tray.show()

    def _build_menu(self):
        menu = QMenu()
        menu.addAction(t("Voir ma journée"), lambda: self.open_popup(QCursor.pos()))
        self.act_recall = menu.addAction(t("Récupérer la fleur"), self.recall)
        menu.addSeparator()
        self.dnd_menu = menu.addMenu(t("Ne pas déranger"))
        self._rebuild_dnd_menu()
        menu.addSeparator()
        menu.addAction(t("Paramètres…"), self.open_settings)
        menu.addAction(t("Exporter l'historique (CSV)…"), self.export_csv)
        menu.addSeparator()
        menu.addAction("🐞 " + t("Signaler un bug"), self.report_bug)
        about = menu.addAction(f"Petite Soif v{cfgmod.__version__}")
        about.setEnabled(False)
        menu.addAction(t("Quitter"), self.app.quit)
        self.tray_menu = menu
        self.tray.setContextMenu(menu)
        self._icon_state = None  # le prochain _update_tray réactive « Reprendre » dans le nouveau menu

    def _rebuild_dnd_menu(self):
        m = self.dnd_menu
        m.clear()
        for minutes in self.cfg["ne_pas_deranger_minutes"]:
            label = f"{minutes} min" if minutes < 60 else (f"{minutes // 60} h" if minutes % 60 == 0 else f"{minutes // 60} h {minutes % 60:02d}")
            m.addAction(label, lambda mm=minutes: self.set_dnd(minutes=mm))
        m.addAction(t("Sommeil jusqu'à {h}", h=settings_mod.fmt_hour(self.cfg['heure_reset'])), lambda: self.set_dnd(until_reset=True))
        m.addSeparator()
        self.act_resume = m.addAction(t("Reprendre maintenant"), self.resume)

    def refresh_icons(self):
        self._icon_state = None
        self._update_tray(self.flower.thirst_target, time.time() < self.dnd_until)

    def _update_tray(self, level, dnd):
        state = (level, dnd, art.SKIN)
        if state != self._icon_state:
            self._icon_state = state
            icon = _icon(level, dnd)
            self.tray.setIcon(icon)
            self.app.setWindowIcon(icon)  # barre des tâches et fenêtres ouvertes ensuite
            if self._settings is not None:
                self._settings.setWindowIcon(icon)  # la fenêtre déjà ouverte ne suit pas l'icône de l'appli
            self.act_resume.setEnabled(dnd)
        total = self.storage.total_cl()
        tip = f"Petite Soif — {fmt_l(total)} / {fmt_l(self.cfg['objectif_cl'])}"
        if dnd:
            tip += "\n" + t("Ne pas déranger jusqu'à {t}", t=f"{datetime.fromtimestamp(self.dnd_until):%H:%M}")
        if tip != self._tooltip:
            self._tooltip = tip
            self.tray.setToolTip(tip)


def load_fonts():
    """Baloo 2 (titres, OFL) livrée avec l'appli ; le petit texte est en Segoe UI, la police de Windows."""
    for name, attr in (("Baloo2.ttf", "FAMILY"),):
        fid = QFontDatabase.addApplicationFont(str(cfgmod.FONTS_DIR / name))
        families = QFontDatabase.applicationFontFamilies(fid) if fid >= 0 else []
        if families:
            setattr(settings_mod, attr, families[0])


def run():
    _install_error_log()
    if sys.platform.startswith("linux"):
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")  # X11, ou XWayland ; Wayland pur non géré (fleur non épinglée)
    app = QApplication(sys.argv)
    load_fonts()
    app.setApplicationName("Petite Soif")
    app.setQuitOnLastWindowClosed(False)
    cfgmod.USER_DIR.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(cfgmod.USER_DIR / "instance.lock"))
    if not lock.tryLock(100):
        QMessageBox.information(None, "Petite Soif", t("Petite Soif tourne déjà (icône près de l'horloge)."))
        return
    ctrl = Controller(app)  # noqa: F841 (garder la référence)
    code = app.exec()
    ctrl.hotkey.unregister()
    lock.unlock()
    sys.exit(code)
