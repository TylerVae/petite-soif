"""Dessin de la fleur en pot (vectoriel, QPainter).

Repère : boîte de 100 x 130 unités. Le pot occupe le bas, la tige part de (50, 88).
`thirst` est un float 0..3 pour des transitions fluides entre les 4 états.
Pour passer à des sprites PNG plus tard, il suffit de remplacer draw_body().
"""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainterPath, QPen, QRadialGradient

BODY_W = 100.0
BODY_H = 130.0

# Ancres par niveau de soif : 0 hydratée, 1, 2, 3 desséchée
_PETAL = ["#FF8FB1", "#F5A0BB", "#E4B6C2", "#C9A08B"]
_PETAL_IN = ["#FFD3E0", "#FCD8E2", "#F1DEE2", "#E3CAB9"]
_LEAF = ["#6CC070", "#88BD6C", "#A6B466", "#B39F5C"]
_LEAF_DARK = ["#4C9A53", "#699B51", "#86934C", "#8C7B43"]
_CENTER = ["#F7C948", "#F3C650", "#E6BE62", "#C9A363"]
_ANGLE = [0.0, 22.0, 52.0, 98.0]
_LEAF_ANGLE = [38.0, 22.0, -8.0, -52.0]
_PETAL_SCALE = [1.0, 0.97, 0.92, 0.84]

INK = QColor("#4A2E24")


def _interp(values, x):
    x = max(0.0, min(3.0, x))
    i = int(math.floor(x))
    if i >= 3:
        v = values[3]
        return QColor(v) if isinstance(v, str) else v
    t = x - i
    a, b = values[i], values[i + 1]
    if isinstance(a, str):
        ca, cb = QColor(a), QColor(b)
        return QColor(
            round(ca.red() + (cb.red() - ca.red()) * t),
            round(ca.green() + (cb.green() - ca.green()) * t),
            round(ca.blue() + (cb.blue() - ca.blue()) * t),
        )
    return a + (b - a) * t


def face_for(thirst, sleeping=False, drinking=False):
    if sleeping:
        return "sleep"
    if drinking:
        return "drink"
    return ("happy", "calm", "worried", "tired")[int(round(max(0.0, min(3.0, thirst))))]


def _stem_geometry(thirst, sleeping, sway):
    base = QPointF(50, 88)
    c1 = QPointF(50, 68)
    c2 = QPointF(50, 48)
    ang = _interp(_ANGLE, thirst) + (15 if sleeping else 0) + sway
    a = math.radians(ang)
    end = QPointF(50 + 30 * math.sin(a), 48 - 30 * math.cos(a))
    path = QPainterPath(base)
    path.cubicTo(c1, c2, end)
    d = end - c2
    head_rot = math.degrees(math.atan2(d.x(), -d.y())) if (d.x() or d.y()) else 0.0
    return path, end, head_rot


def head_position(thirst, sleeping=False):
    return _stem_geometry(thirst, sleeping, 0.0)[1]


def draw_body(p, thirst, *, sleeping=False, drinking=False, blink=False,
              walking=False, walk_phase=0.0, sway=0.0):
    p.save()
    if walking:
        _feet(p, walk_phase)
    bob = -abs(math.sin(walk_phase)) * 3 if walking else 0.0
    p.translate(0, bob)

    # terre
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#6B4A34"))
    p.drawEllipse(QRectF(21, 83.5, 58, 10))

    path, end, head_rot = _stem_geometry(thirst, sleeping, sway)
    dark = _interp(_LEAF_DARK, thirst)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(dark, 4, Qt.SolidLine, Qt.RoundCap))
    p.drawPath(path)

    attach = path.pointAtPercent(0.36)
    la = _interp(_LEAF_ANGLE, thirst) - (12 if sleeping else 0)
    for side in (-1, 1):
        _leaf(p, attach, side, la, _interp(_LEAF, thirst), dark)

    if thirst > 2.5:  # pétale tombé sur la terre
        p.save()
        p.translate(64, 87)
        p.rotate(70)
        col = _interp(_PETAL, thirst)
        p.setBrush(col)
        p.setPen(QPen(col.darker(118), 0.8))
        p.drawEllipse(QRectF(-3, -6, 6, 11))
        p.restore()

    _head(p, end, head_rot, thirst, sleeping)
    _pot(p)
    _face(p, face_for(thirst, sleeping, drinking), thirst, blink)
    p.restore()


def _feet(p, phase):
    p.setPen(QPen(QColor("#9A4A2C"), 1))
    p.setBrush(QColor("#B8583A"))
    for x, ph in ((39, 0.0), (61, math.pi)):
        lift = max(0.0, math.sin(phase + ph)) * 3.5
        p.drawEllipse(QRectF(x - 6, 126 - lift, 12, 7))


def _leaf(p, attach, side, angle_deg, fill, dark):
    a = math.radians(angle_deg)
    d = QPointF(side * math.cos(a), -math.sin(a))
    n = QPointF(-d.y(), d.x())
    length, width = 20.0, 7.0
    tip = attach + d * length
    mid = attach + d * (length * 0.5)
    path = QPainterPath(attach)
    path.quadTo(mid + n * width, tip)
    path.quadTo(mid - n * width, attach)
    p.setBrush(fill)
    p.setPen(QPen(dark, 1))
    p.drawPath(path)
    p.setPen(QPen(dark, 0.9))
    p.drawLine(attach, attach + d * (length * 0.8))


def _head(p, center, rot, thirst, sleeping):
    p.save()
    p.translate(center)
    p.rotate(rot)
    p.scale(1.0, 1.0 - 0.33 * min(thirst, 3.0) / 3.0)
    ps = _interp(_PETAL_SCALE, thirst) * (0.88 if sleeping else 1.0)
    col = _interp(_PETAL, thirst)
    inner = _interp(_PETAL_IN, thirst)
    edge = col.darker(118)
    n = 7
    for i in range(n):
        if thirst > 2.5 and i == 2:
            continue
        p.save()
        p.rotate(i * 360 / n + 8)
        g = QLinearGradient(0, -8 * ps, 0, -25 * ps)
        g.setColorAt(0, inner)
        g.setColorAt(1, col)
        p.setBrush(g)
        p.setPen(QPen(edge, 1))
        p.drawEllipse(QRectF(-5.8 * ps, -25 * ps, 11.6 * ps, 17.5 * ps))
        p.restore()
    c = _interp(_CENTER, thirst)
    rg = QRadialGradient(QPointF(-2, -2), 10)
    rg.setColorAt(0, c.lighter(125))
    rg.setColorAt(1, c.darker(108))
    p.setBrush(rg)
    p.setPen(QPen(c.darker(135), 1))
    p.drawEllipse(QPointF(0, 0), 8.5, 8.5)
    p.setPen(Qt.NoPen)
    p.setBrush(c.darker(145))
    for dx, dy in ((-3, -1), (2, -3), (3, 2), (-1, 3), (0, 0)):
        p.drawEllipse(QPointF(dx, dy), 0.9, 0.9)
    p.restore()


def _pot(p):
    body = QPainterPath(QPointF(20, 98))
    body.lineTo(80, 98)
    body.lineTo(74.5, 124)
    body.quadTo(73.5, 129, 68, 129)
    body.lineTo(32, 129)
    body.quadTo(26.5, 129, 25.5, 124)
    body.closeSubpath()
    g = QLinearGradient(20, 0, 80, 0)
    g.setColorAt(0, QColor("#CF6E44"))
    g.setColorAt(0.35, QColor("#EE9A6C"))
    g.setColorAt(1, QColor("#C9653C"))
    p.setBrush(g)
    p.setPen(QPen(QColor("#A9532F"), 1.2))
    p.drawPath(body)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(255, 255, 255, 45))
    p.drawRoundedRect(QRectF(27, 101, 4.5, 18), 2.2, 2.2)

    rim = QRectF(14, 86, 72, 13)
    rg = QLinearGradient(0, 86, 0, 99)
    rg.setColorAt(0, QColor("#F2A574"))
    rg.setColorAt(1, QColor("#CC6B40"))
    p.setBrush(rg)
    p.setPen(QPen(QColor("#A9532F"), 1.2))
    p.drawRoundedRect(rim, 6, 6)
    p.setPen(QPen(QColor(255, 255, 255, 80), 1.4, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(20, 89.2), QPointF(80, 89.2))


def _face(p, face, thirst, blink):
    pen = QPen(INK, 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    ex = (41.0, 59.0)
    ey = 110.5

    # joues
    alpha = int(160 * (1 - 0.7 * min(thirst, 3.0) / 3.0))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(255, 140, 160, alpha))
    for x in (33.5, 66.5):
        p.drawEllipse(QPointF(x, 116), 4, 2.4)

    p.setBrush(Qt.NoBrush)
    p.setPen(pen)
    if face in ("happy", "drink"):
        for x in ex:
            path = QPainterPath(QPointF(x - 4, ey + 1.5))
            path.quadTo(x, ey - 4, x + 4, ey + 1.5)
            p.drawPath(path)
    elif face == "sleep":
        for x in ex:
            path = QPainterPath(QPointF(x - 4, ey - 1))
            path.quadTo(x, ey + 3.5, x + 4, ey - 1)
            p.drawPath(path)
    else:
        for i, x in enumerate(ex):
            if blink:
                p.drawLine(QPointF(x - 3, ey), QPointF(x + 3, ey))
            elif face == "tired":
                lid = QPainterPath(QPointF(x - 3.2, ey))
                lid.arcTo(QRectF(x - 3.2, ey - 3.2, 6.4, 6.4), 180, 180)
                lid.closeSubpath()
                p.setPen(Qt.NoPen)
                p.setBrush(INK)
                p.drawPath(lid)
                p.setBrush(Qt.NoBrush)
                p.setPen(pen)
                p.drawLine(QPointF(x - 3.8, ey), QPointF(x + 3.8, ey))
            else:
                p.setPen(Qt.NoPen)
                p.setBrush(INK)
                p.drawEllipse(QPointF(x, ey), 2.7, 3.0)
                p.setBrush(QColor(255, 255, 255, 230))
                p.drawEllipse(QPointF(x + 0.9, ey - 1.1), 0.95, 0.95)
                p.setBrush(Qt.NoBrush)
                p.setPen(pen)
            if face in ("worried", "tired"):
                s = -1 if i == 0 else 1
                p.setPen(QPen(INK, 1.6, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(x - 4 * s, ey - 5), QPointF(x + 3 * s, ey - 7))
                p.setPen(pen)

    # bouche
    if face == "happy":
        m = QPainterPath(QPointF(45.5, 117))
        m.quadTo(50, 122, 54.5, 117)
        p.drawPath(m)
    elif face == "calm":
        m = QPainterPath(QPointF(47, 118))
        m.quadTo(50, 120.5, 53, 118)
        p.drawPath(m)
    elif face == "worried":
        m = QPainterPath(QPointF(46, 119))
        m.quadTo(48, 117, 50, 119)
        m.quadTo(52, 121, 54, 119)
        p.drawPath(m)
    elif face == "tired":
        p.setPen(QPen(INK, 1.2))
        p.setBrush(QColor("#7A2E2E"))
        p.drawEllipse(QRectF(47.3, 116.3, 5.4, 4.8))
    elif face == "drink":
        p.setPen(QPen(INK, 1.2))
        p.setBrush(INK)
        p.drawEllipse(QRectF(48, 116.5, 4, 4))
    elif face == "sleep":
        p.drawLine(QPointF(48.5, 118.5), QPointF(51.5, 118.5))

    if face in ("worried", "tired"):
        _drop(p, QPointF(77, 103), 5.5, QColor("#8FD0FA"), QColor("#4A9FD8"))


def _drop(p, c, size, fill, edge):
    path = QPainterPath(QPointF(c.x(), c.y() - size))
    path.quadTo(c.x() + size * 0.75, c.y() + size * 0.2, c.x(), c.y() + size * 0.55)
    path.quadTo(c.x() - size * 0.75, c.y() + size * 0.2, c.x(), c.y() - size)
    p.setBrush(fill)
    p.setPen(QPen(edge, 1))
    p.drawPath(path)


# --- overlays -------------------------------------------------------------
def draw_thought_bubble(p):
    """Bulle de pensée avec une goutte : 'j'ai très soif'."""
    p.save()
    p.setPen(QPen(QColor("#B8C4CF"), 1.2))
    p.setBrush(QColor(255, 255, 255, 240))
    p.drawEllipse(QPointF(33, 72), 2.2, 2.2)
    p.drawEllipse(QPointF(27, 63), 3.4, 3.4)
    p.drawEllipse(QPointF(18, 44), 13, 13)
    g = QLinearGradient(18, 36, 18, 52)
    g.setColorAt(0, QColor("#9ADBFF"))
    g.setColorAt(1, QColor("#3A95D8"))
    path = QPainterPath(QPointF(18, 36))
    path.quadTo(24.5, 45, 18, 51)
    path.quadTo(11.5, 45, 18, 36)
    p.setBrush(g)
    p.setPen(QPen(QColor("#2F7FBF"), 1))
    p.drawPath(path)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(255, 255, 255, 190))
    p.drawEllipse(QPointF(16, 45), 1.4, 2.2)
    p.restore()


def draw_zz(p, t=0.0):
    p.save()
    p.setPen(QColor("#7F93B5"))
    f = QFont("Segoe UI")
    f.setBold(True)
    f.setPixelSize(11)
    p.setFont(f)
    p.drawText(QPointF(70, 6 + math.sin(t * 2) * 1.5), "z")
    f.setPixelSize(16)
    p.setFont(f)
    p.drawText(QPointF(79, -5 + math.sin(t * 2 + 1) * 1.5), "Z")
    p.restore()


def draw_exclaim(p, x=74, y=0):
    p.save()
    p.setPen(QPen(QColor("#FFFFFF"), 1))
    p.setBrush(QColor("#E0584F"))
    p.drawEllipse(QPointF(x, y), 8, 8)
    f = QFont("Segoe UI")
    f.setBold(True)
    f.setPixelSize(12)
    p.setFont(f)
    p.setPen(QColor("#FFFFFF"))
    p.drawText(QRectF(x - 8, y - 8, 16, 16), Qt.AlignCenter, "!")
    p.restore()


def draw_ring(p, progress):
    """Jauge circulaire de l'appui long."""
    p.save()
    r = QRectF(50 - 70, 62 - 70, 140, 140)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor(58, 149, 216, 50), 5))
    p.drawEllipse(r)
    p.setPen(QPen(QColor(58, 149, 216, 220), 5, Qt.SolidLine, Qt.RoundCap))
    p.drawArc(r, 90 * 16, int(-360 * 16 * max(0.0, min(1.0, progress))))
    p.restore()


def star_path(r):
    path = QPainterPath()
    for i in range(8):
        a = math.pi / 4 * i - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.38
        pt = QPointF(math.cos(a) * rr, math.sin(a) * rr)
        if i == 0:
            path.moveTo(pt)
        else:
            path.lineTo(pt)
    path.closeSubpath()
    return path
