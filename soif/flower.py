"""Fenêtre de la fleur : toujours au premier plan, transparente, ne prend jamais le focus.

Modes : home (à sa place), follow (suit la souris N s), dock (attend près du curseur),
hold (immobile hors de sa place), poof_out / poof_in (téléportation avec fumée).
L'animation (≈30 fps) ne tourne que lorsqu'il se passe quelque chose.
"""
import math
import random
import time

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QWidget

from . import painter as art

MARGIN = 48.0
POOF = 0.28
AGITATE = 1.6


class _Particle:
    __slots__ = ("kind", "x", "y", "vx", "vy", "life", "age", "size", "rot", "vr", "color")

    def __init__(self, kind, x, y, vx, vy, life, size, color=None, vr=0.0):
        self.kind, self.x, self.y, self.vx, self.vy = kind, x, y, vx, vy
        self.life, self.age, self.size, self.color = life, 0.0, size, color
        self.rot, self.vr = random.uniform(0, 360), vr


class FlowerWidget(QWidget):
    drink_started = Signal()
    drink_cancelled = Signal()
    drank = Signal()
    menu_requested = Signal(QPoint)
    home_changed = Signal(QPoint)
    poofed = Signal()

    def __init__(self, scale=1.0, long_press_ms=800, cursor_offset=40):
        super().__init__(
            None,
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus | Qt.NoDropShadowWindowHint,
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.NoFocus)

        self.scale_ = float(scale)
        self.long_press_ms = int(long_press_ms)
        self.cursor_offset = int(cursor_offset)

        self.thirst_target = 0
        self.thirst = 0.0
        self.sleeping = False
        self.mode = "home"
        self.home = QPoint(0, 0)
        self._fpos = QPointF(0, 0)
        self._follow_until = 0.0
        self._poof_t0 = 0.0

        self._pressing = False
        self._press_t0 = 0.0
        self._press_origin = QPoint()
        self._drag_offset = None

        self._agitate_until = 0.0
        self._blink_until = 0.0
        self._walking = False
        self._walk_phase = 0.0
        self._particles = []
        self._drop_accum = 0.0
        self._t = 0.0
        self._last = time.monotonic()

        self._anim = QTimer(self)
        self._anim.setInterval(33)
        self._anim.timeout.connect(self._tick)
        self._apply_size()
        self._schedule_blink()

    # --- géométrie --------------------------------------------------------
    def _apply_size(self):
        s = self.scale_
        self.setFixedSize(int((art.BODY_W + 2 * MARGIN) * s), int((art.BODY_H + 2 * MARGIN) * s))

    def set_scale(self, s):
        self.scale_ = float(s)
        self._apply_size()
        self.update()

    def _body_rect_local(self):
        s = self.scale_
        return QRectF(MARGIN * s, (MARGIN - 10) * s, art.BODY_W * s, (art.BODY_H + 14) * s)

    def _cursor_over_body(self):
        r = self._body_rect_local().translated(QPointF(self.pos()))
        return r.contains(QPointF(QCursor.pos()))

    def _target_for_cursor(self):
        c = QCursor.pos()
        scr = QGuiApplication.screenAt(c) or QGuiApplication.primaryScreen()
        g = scr.availableGeometry()
        s = self.scale_
        bw, bh, off = art.BODY_W * s, art.BODY_H * s, self.cursor_offset
        bx, by = c.x() + off, c.y() + off
        if bx + bw > g.right():
            bx = c.x() - off - bw
        if by + bh > g.bottom():
            by = c.y() - off - bh
        return QPointF(bx - MARGIN * s, by - MARGIN * s)

    # --- API --------------------------------------------------------------
    def set_home(self, point, move=True):
        self.home = QPoint(point)
        if move:
            self.move(self.home)
            self._fpos = QPointF(self.home)
            self.mode = "home"

    def set_thirst(self, level):
        level = max(0, min(3, int(level)))
        if level != self.thirst_target:
            self.thirst_target = level
            self._ensure_anim()

    def set_sleeping(self, value):
        if value != self.sleeping:
            self.sleeping = value
            self.update()

    def agitate(self):
        self._agitate_until = time.monotonic() + AGITATE
        self._ensure_anim()

    def follow(self, seconds):
        if self.mode in ("poof_out", "poof_in"):
            return
        self.mode = "follow"
        self._fpos = QPointF(self.pos())
        self._follow_until = time.monotonic() + seconds
        self._ensure_anim()

    def dock(self):
        if self.mode in ("poof_out", "poof_in"):
            return
        self.mode = "dock"
        self._fpos = QPointF(self.pos())
        self._ensure_anim()

    def wake(self):
        """Appelé chaque seconde par le contrôleur quand la fleur est dockée."""
        if self.mode == "dock":
            d = self._target_for_cursor() - self._fpos
            if math.hypot(d.x(), d.y()) > 0.5:
                self._ensure_anim()

    def hold(self):
        if self.mode in ("follow", "dock"):
            self.mode = "hold"

    def go_home(self):
        if self.mode in ("poof_out", "poof_in"):
            return
        if self.pos() == self.home:
            self.mode = "home"
            return
        self.mode = "poof_out"
        self._poof_t0 = time.monotonic()
        self._spawn_smoke()
        self.poofed.emit()
        self._ensure_anim()

    def recall(self, point):
        self.home = QPoint(point)
        self.mode = "hold"
        self.go_home()

    def celebrate(self):
        self._spawn_stars()
        self._ensure_anim()

    # --- animation --------------------------------------------------------
    def _ensure_anim(self):
        if not self._anim.isActive():
            self._last = time.monotonic()
            self._anim.start()

    def _needs_anim(self):
        now = time.monotonic()
        if self._pressing or self._particles or self.mode in ("follow", "poof_out", "poof_in"):
            return True
        if self.mode == "dock" and self._walking:
            return True
        if now < self._agitate_until or now < self._blink_until:
            return True
        return abs(self.thirst - self.thirst_target) > 0.001

    def _schedule_blink(self):
        QTimer.singleShot(random.randint(2500, 6500), self._blink)

    def _blink(self):
        if not self.sleeping and round(self.thirst) >= 1 and self.isVisible():
            self._blink_until = time.monotonic() + 0.13
            self._ensure_anim()
        self._schedule_blink()

    def _tick(self):
        now = time.monotonic()
        dt = min(0.1, now - self._last)
        self._last = now
        self._t += dt

        diff = self.thirst_target - self.thirst
        self.thirst = float(self.thirst_target) if abs(diff) < 0.005 else self.thirst + diff * min(1.0, dt * 3.5)

        self._walking = False
        if self.mode == "follow" and now >= self._follow_until and not self._pressing:
            self.go_home()
        elif self.mode in ("follow", "dock"):
            if not self._pressing and self._drag_offset is None and not self._cursor_over_body():
                tgt = self._target_for_cursor()
                d = tgt - self._fpos
                dist = math.hypot(d.x(), d.y())
                if dist > 0.5:
                    step = min(dist * min(1.0, dt * 5.0), 1600 * dt)
                    self._fpos += d * (step / dist)
                    self.move(round(self._fpos.x()), round(self._fpos.y()))
                    if step > 0.4:
                        self._walking = True
                        self._walk_phase += step * 0.09
        elif self.mode == "poof_out" and now - self._poof_t0 >= POOF:
            self._particles.clear()
            self.move(self.home)
            self._fpos = QPointF(self.home)
            self.mode = "poof_in"
            self._poof_t0 = now
            self._spawn_smoke()
        elif self.mode == "poof_in" and now - self._poof_t0 >= POOF:
            self.mode = "home"

        if self._pressing:
            if (now - self._press_t0) * 1000 >= self.long_press_ms:
                self._pressing = False
                self._spawn_stars()
                self.drank.emit()
            else:
                self._drop_accum += dt
                while self._drop_accum > 0.09:
                    self._drop_accum -= 0.09
                    self._spawn_drop()

        self._update_particles(dt)
        self.update()
        if not self._needs_anim():
            self._anim.stop()
            self.update()

    # --- particules -------------------------------------------------------
    def _center_local(self, bx, by):
        s = self.scale_
        return (MARGIN + bx) * s, (MARGIN + by) * s

    def _spawn_stars(self):
        cx, cy = self._center_local(50, 60)
        s = self.scale_
        for i in range(10):
            a = i / 10 * 2 * math.pi + random.uniform(-0.2, 0.2)
            sp = random.uniform(70, 150) * s
            col = random.choice([QColor("#FFD54A"), QColor("#FFE98A"), QColor("#FFFFFF"), QColor("#9ADBFF")])
            self._particles.append(_Particle("star", cx, cy, math.cos(a) * sp, math.sin(a) * sp,
                                             random.uniform(0.7, 1.0), random.uniform(4, 8) * s, col,
                                             random.uniform(-300, 300)))

    def _spawn_smoke(self):
        cx, cy = self._center_local(50, 112)
        s = self.scale_
        for _ in range(12):
            a = random.uniform(math.pi, 2 * math.pi) if random.random() < 0.7 else random.uniform(0, math.pi)
            sp = random.uniform(30, 90) * s
            self._particles.append(_Particle("smoke", cx + random.uniform(-25, 25) * s, cy + random.uniform(-10, 12) * s,
                                             math.cos(a) * sp, math.sin(a) * sp - 20 * s,
                                             random.uniform(0.45, 0.6), random.uniform(7, 12) * s))

    def _spawn_drop(self):
        hp = art.head_position(self.thirst, self.sleeping)
        cx, _ = self._center_local(hp.x() + random.uniform(-12, 12), 0)
        _, top = self._center_local(0, -34)
        _, hy = self._center_local(0, hp.y() - 8)
        s = self.scale_
        vy = 260 * s
        self._particles.append(_Particle("drop", cx, top, 0, vy, max(0.05, (hy - top) / vy), 4.5 * s))

    def _update_particles(self, dt):
        alive = []
        for pt in self._particles:
            pt.age += dt
            if pt.age >= pt.life:
                continue
            pt.x += pt.vx * dt
            pt.y += pt.vy * dt
            pt.rot += pt.vr * dt
            if pt.kind == "star":
                pt.vy += 120 * self.scale_ * dt
                pt.vx *= 0.97
            elif pt.kind == "smoke":
                pt.vx *= 0.92
                pt.vy *= 0.92
            alive.append(pt)
        self._particles = alive

    # --- rendu ------------------------------------------------------------
    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        now = time.monotonic()
        s = self.scale_

        p.save()
        p.translate(MARGIN * s, MARGIN * s)
        p.scale(s, s)
        if self._pressing:
            art.draw_ring(p, (now - self._press_t0) * 1000 / self.long_press_ms)

        shrink = 1.0
        if self.mode == "poof_out":
            k = min(1.0, (now - self._poof_t0) / POOF)
            shrink = 1.0 - k * k
        elif self.mode == "poof_in":
            k = min(1.0, (now - self._poof_t0) / POOF)
            shrink = 1.0 - (1.0 - k) ** 2
        shake_x = tilt = 0.0
        agitating = now < self._agitate_until
        if agitating:
            k = (self._agitate_until - now) / AGITATE
            shake_x = math.sin(self._t * 45) * 3.5 * k
            tilt = math.sin(self._t * 30) * 6 * k

        if shrink > 0.01:
            p.save()
            pivot = QPointF(50, 129)
            p.translate(pivot.x() + shake_x, pivot.y())
            p.rotate(tilt)
            p.scale(shrink, shrink)
            p.translate(-pivot)
            sway = math.sin(self._t * 9) * 4 if self._walking else 0.0
            art.draw_body(p, self.thirst, sleeping=self.sleeping, drinking=self._pressing,
                          blink=now < self._blink_until, walking=self._walking,
                          walk_phase=self._walk_phase, sway=sway)
            if self.sleeping:
                art.draw_zz(p, self._t)
            elif agitating:
                art.draw_exclaim(p)
            elif self.thirst_target >= 3 and not self._pressing:
                art.draw_thought_bubble(p)
            p.restore()
        p.restore()

        for pt in self._particles:
            k = pt.age / pt.life
            if pt.kind == "star":
                c = QColor(pt.color)
                c.setAlphaF(max(0.0, 1.0 - k))
                p.save()
                p.translate(pt.x, pt.y)
                p.rotate(pt.rot)
                p.setPen(Qt.NoPen)
                p.setBrush(c)
                p.drawPath(art.star_path(pt.size * (1.0 - 0.4 * k)))
                p.restore()
            elif pt.kind == "smoke":
                a = max(0.0, 1.0 - k)
                r = pt.size * (1.0 + 1.2 * k)
                p.setPen(QPen(QColor(200, 192, 182, int(160 * a)), 1.2))
                p.setBrush(QColor(246, 243, 238, int(230 * a)))
                p.drawEllipse(QPointF(pt.x, pt.y), r, r)
            elif pt.kind == "drop":
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(90, 175, 235, 220))
                sz = pt.size
                p.drawEllipse(QPointF(pt.x, pt.y), sz * 0.55, sz)
        p.end()

    # --- souris -----------------------------------------------------------
    def mousePressEvent(self, e):
        if not self._body_rect_local().contains(e.position()):
            e.ignore()
            return
        if e.button() == Qt.RightButton:
            self.menu_requested.emit(e.globalPosition().toPoint())
            return
        if e.button() != Qt.LeftButton:
            return
        if e.modifiers() & Qt.ShiftModifier:
            self._drag_offset = e.globalPosition().toPoint() - self.pos()
            return
        if self.mode in ("poof_out", "poof_in"):
            return
        self._pressing = True
        self._press_t0 = time.monotonic()
        self._press_origin = e.globalPosition().toPoint()
        self._drop_accum = 0.0
        self.drink_started.emit()
        self._ensure_anim()

    def mouseMoveEvent(self, e):
        g = e.globalPosition().toPoint()
        if self._drag_offset is not None:
            np = g - self._drag_offset
            self.move(np)
            self._fpos = QPointF(np)
            return
        if self._pressing and (g - self._press_origin).manhattanLength() > 8:
            self._cancel_press()

    def mouseReleaseEvent(self, e):
        if self._drag_offset is not None and e.button() == Qt.LeftButton:
            self._drag_offset = None
            self.home = self.pos()
            self.mode = "home"
            self.home_changed.emit(self.home)
            return
        if self._pressing:
            self._cancel_press()

    def _cancel_press(self):
        self._pressing = False
        self._particles = [pt for pt in self._particles if pt.kind != "drop"]
        self.drink_cancelled.emit()
        self.update()
