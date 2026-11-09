"""Plantes au choix : dessins SVG générés à la volée (rendus par QtSvg dans painter.py).

Chaque plante est une fonction (th, sl, kind, blink, sway) -> chaîne SVG de 100 x 130 unités, comme la fleur
classique. `th` (0..3) est la soif, interpolée entre 4 ancres ; `sl` (0..1) est le sommeil, cumulable avec la
soif (accessoire propre à chaque plante, fleurs qui se ferment, feuilles qui s'abaissent) ; `kind` est l'expression du visage
(happy / calm / worried / tired / sleep / drink, voir painter.face_for) ; `blink` ferme les yeux un instant ;
`sway` (degrés) incline la tige pendant la marche.
"""
import math

INK = "#4A2E24"


def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def A(anchors, x):
    """Interpolation entre 4 ancres (th = 0..3) : couleurs '#hex' ou nombres."""
    x = max(0.0, min(3.0, x))
    i = min(int(x), 2)
    t = x - i
    a, b = anchors[i], anchors[i + 1]
    if isinstance(a, str):
        ra, rb = _rgb(a), _rgb(b)
        return "#%02X%02X%02X" % tuple(round(ra[k] + (rb[k] - ra[k]) * t) for k in range(3))
    return a + (b - a) * t


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def bez(p, t):
    u = 1 - t
    return (u**3 * p[0][0] + 3 * u * u * t * p[1][0] + 3 * u * t * t * p[2][0] + t**3 * p[3][0],
            u**3 * p[0][1] + 3 * u * u * t * p[1][1] + 3 * u * t * t * p[2][1] + t**3 * p[3][1])


def tangent(p, t):
    u = 1 - t
    dx = 3 * u * u * (p[1][0] - p[0][0]) + 6 * u * t * (p[2][0] - p[1][0]) + 3 * t * t * (p[3][0] - p[2][0])
    dy = 3 * u * u * (p[1][1] - p[0][1]) + 6 * u * t * (p[2][1] - p[1][1]) + 3 * t * t * (p[3][1] - p[2][1])
    n = math.hypot(dx, dy) or 1.0
    return dx / n, dy / n


def face(kind, th, blink, cx=50, cy=106, k=0.7, ink=INK):
    """Visage sur le pot (mêmes expressions que painter._face), centré en (cx, cy), à l'échelle k."""
    alpha = 160 * (1 - 0.7 * min(th, 3) / 3) / 255
    ex, ey = (41, 59), 110.5
    st = f'stroke="{ink}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none"'
    o = [f'<ellipse cx="33.5" cy="116" rx="4" ry="2.4" fill="#FF8CA0" opacity="{alpha:.2f}"/>',
         f'<ellipse cx="66.5" cy="116" rx="4" ry="2.4" fill="#FF8CA0" opacity="{alpha:.2f}"/>']
    for i, x in enumerate(ex):
        s = -1 if i == 0 else 1
        if kind in ("happy", "drink"):
            o.append(f'<path d="M{x - 4} {ey + 1.5}Q{x} {ey - 4} {x + 4} {ey + 1.5}" {st}/>')
        elif kind == "sleep":
            o.append(f'<path d="M{x - 4} {ey - 1}Q{x} {ey + 3.5} {x + 4} {ey - 1}" {st}/>')
        elif blink:
            o.append(f'<path d="M{x - 3} {ey}L{x + 3} {ey}" {st}/>')
        elif kind == "tired":
            o.append(f'<path d="M{x - 3.2} {ey}A3.2 3.2 0 0 0 {x + 3.2} {ey}Z" fill="{ink}"/>')
            o.append(f'<path d="M{x - 3.8} {ey}L{x + 3.8} {ey}" {st}/>')
        else:
            o.append(f'<ellipse cx="{x}" cy="{ey}" rx="2.7" ry="3" fill="{ink}"/>'
                     f'<circle cx="{x + .9}" cy="{ey - 1.1}" r=".95" fill="#fff" opacity=".9"/>')
        if kind in ("worried", "tired"):
            o.append(f'<path d="M{x - 4 * s} {ey - 5}L{x + 3 * s} {ey - 7}" stroke="{ink}" stroke-width="1.6" stroke-linecap="round"/>')
    o.append({
        "happy": f'<path d="M45.5 117Q50 122 54.5 117" {st}/>',
        "calm": f'<path d="M47 118Q50 120.5 53 118" {st}/>',
        "worried": f'<path d="M46 119Q48 117 50 119Q52 121 54 119" {st}/>',
        "tired": f'<ellipse cx="50" cy="118.7" rx="2.7" ry="2.4" fill="#7A2E2E" stroke="{ink}" stroke-width="1.2"/>',
        "sleep": f'<path d="M48.5 118.5L51.5 118.5" {st}/>',
        "drink": f'<circle cx="50" cy="118.5" r="2" fill="{ink}" stroke="{ink}" stroke-width="1.2"/>',
    }[kind])
    if kind in ("worried", "tired"):
        x, y, s = 77, 103, 5.5
        o.append(f'<path d="M{x} {y - s}Q{x + s * .75} {y + s * .2} {x} {y + s * .55}Q{x - s * .75} {y + s * .2} {x} {y - s}Z" '
                 'fill="#8FD0FA" stroke="#4A9FD8" stroke-width="1"/>')
    return f'<g transform="translate({cx} {cy}) scale({k}) translate(-50 -110.5)">' + "".join(o) + "</g>"


def accessoire_2(op):
    """Accessoire de sommeil de la plante 2."""
    stars = "".join(f'<path d="M{x} {y - 1.4}l.4 1 1 .4-1 .4-.4 1-.4-1-1-.4 1-.4z" fill="#FFF3E6"/>'
                    for x, y in ((37, 122), (44, 125), (57, 121.5), (63, 125), (35, 126.5), (66, 120)))
    return (f'<g opacity="{op:.2f}">'
            '<path d="M29.5 116H70.5V121A7.5 7.5 0 0 1 63 128.5H37A7.5 7.5 0 0 1 29.5 121Z" fill="#D9475C"/>'
            '<rect x="29.5" y="116" width="41" height="3.2" fill="#EC6A7E"/>'
            '<path d="M50 119.2V128.5" stroke="#B3344A" stroke-width=".9"/>'
            f'{stars}'
            '<path d="M31.08 125.6H68.92A7.5 7.5 0 0 1 63 128.5H37A7.5 7.5 0 0 1 31.08 125.6Z" fill="#F4A3B0"/>'
            '<path d="M50 117.6c-2-2.6-4.8-2-4.4.1.3 1.4 2.8 1.1 4.4-.1zM50 117.6c2-2.6 4.8-2 4.4.1-.3 1.4-2.8 1.1-4.4-.1z" '
            'fill="#FFE9E0" stroke="#D9A89A" stroke-width=".4"/>'
            '<circle cx="50" cy="117.7" r=".9" fill="#FFE9E0" stroke="#D9A89A" stroke-width=".4"/></g>')


# ───────────────────────────── Plante 2 ─────────────────────────────

_STEM = [  # points de contrôle de la hampe pour th = 0, 1, 2, 3
    [(50, 90), (46, 62), (56, 34), (80, 24)],
    [(50, 90), (47, 64), (60, 38), (84, 32)],
    [(50, 90), (48, 66), (66, 42), (88, 48)],
    [(50, 90), (46, 64), (74, 32), (84, 66)],  # grand arc qui retombe
]
_SEPAL = ["#FFFFFF", "#FBF3F5", "#F1E3DD", "#D9C2A8"]
_PETAL = ["#FBE0EE", "#F5D6E2", "#E6C5C5", "#C9A68E"]
_LIP = ["#C2185B", "#B0305A", "#9A4A55", "#7A4A3A"]
_CTR = ["#F5C542", "#E9BF50", "#D2A85A", "#A98A5C"]
_EDGE = ["#EBCFE0", "#E5CDD2", "#D8BDB0", "#B89C86"]
_VEIN = ["#2C6E3B", "#38703A", "#566E36", "#6A6A30"]


def plante_2_stem(th, sl=0.0, sway=0.0):
    th = min(3.0, th + 0.35 * sl)
    p = [(A([_STEM[j][k][0] for j in range(4)], th), A([_STEM[j][k][1] for j in range(4)], th)) for k in range(4)]
    if sway:
        c, s = math.cos(math.radians(sway)), math.sin(math.radians(sway))
        p = [p[0]] + [(50 + (x - 50) * c - (y - 90) * s, 90 + (x - 50) * s + (y - 90) * c) for x, y in p[1:]]
    return p


def _flower(th):
    return (f'<g fill="{A(_SEPAL, th)}" stroke="{A(_EDGE, th)}" stroke-width=".6">'
            '<ellipse rx="2.6" ry="6" cy="-4"/><ellipse rx="2.6" ry="6" cy="-4" transform="rotate(125)"/>'
            '<ellipse rx="2.6" ry="6" cy="-4" transform="rotate(-125)"/></g>'
            f'<ellipse cx="-4.5" rx="4.6" ry="4" fill="{A(_PETAL, th)}"/><ellipse cx="4.5" rx="4.6" ry="4" fill="{A(_PETAL, th)}"/>'
            f'<ellipse cy="2.6" rx="2.3" ry="1.8" fill="{A(_LIP, th)}"/><circle r="1.2" fill="{A(_CTR, th)}"/>')


def _leaf(side, d, th, base, tip):
    d = d * (1.15 if side == "R" else 1.0)
    path = (f"M54 88C40 {81 + .3 * d:.1f} 18 {82 + .8 * d:.1f} 8 {90 + d:.1f}"
            f"C10 {96 + d:.1f} 18 {98 + .9 * d:.1f} 26 {96 + .6 * d:.1f}C36 {94 + .3 * d:.1f} 46 94 55 93Z")
    vein = f"M53 91C40 {88 + .3 * d:.1f} 22 {89 + .8 * d:.1f} 11 {93 + .95 * d:.1f}"
    tr = ' transform="translate(100 0) scale(-1 1)"' if side == "R" else ""
    return (f'<linearGradient id="g{side}" gradientUnits="userSpaceOnUse" x1="54" y1="0" x2="8" y2="0">'
            f'<stop offset="0" stop-color="{A(base, th)}"/><stop offset=".55" stop-color="{A(base, th)}"/>'
            f'<stop offset="1" stop-color="{A(tip, th)}"/></linearGradient>'
            f'<g{tr}><path d="{path}" fill="url(#g{side})"/><path d="{vein}" stroke="{A(_VEIN, th)}" stroke-width=".8" fill="none"/></g>')


def plante_2(th, sl=0.0, kind="happy", blink=False, sway=0.0):
    th = clamp(th, 0, 3)
    d = A([0, 3, 8, 16], th) + 5 * sl
    dd = A([0, 3, 9, 16], th) + 3 * sl
    p = plante_2_stem(th, sl, sway)
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 130">',
         '<rect x="30" y="88" width="40" height="40" rx="7" fill="#F6F2EC" stroke="#D8CFC2"/>'
         '<rect x="30" y="88" width="40" height="5" rx="2.5" fill="#E9E2D8"/>']
    # feuille du fond : par-dessus le pot, sous les grandes feuilles
    o.append(f'<path d="M50 88C44 {80 + .3 * dd:.1f} 32 {72 + .5 * dd:.1f} 23 {72 + dd:.1f}C28 {82 + .5 * dd:.1f} 40 90 50 90Z" '
             f'fill="{A(["#4FA060", "#5A9F55", "#7DA050", "#97964A"], th)}"/>')
    o.append(_leaf("L", d, th, ["#3E8E4E", "#4B8E48", "#6E9644", "#8C913E"], ["#3E8E4E", "#548F44", "#9C9A3E", "#B08A3A"]))
    o.append(_leaf("R", d, th, ["#357D44", "#437F42", "#65873E", "#80843A"], ["#357D44", "#4C8040", "#8F8E3A", "#A07C36"]))
    # hampe, cœur, bourgeon (collé au bout, dans l'axe)
    o.append(f'<path d="M{p[0][0]} {p[0][1]}C{p[1][0]:.1f} {p[1][1]:.1f} {p[2][0]:.1f} {p[2][1]:.1f} {p[3][0]:.1f} {p[3][1]:.1f}" '
             f'stroke="{A(["#7A8F3E", "#848F3E", "#8E8C3C", "#8A7A38"], th)}" stroke-width="2" fill="none" stroke-linecap="round"/>')
    o.append(f'<ellipse cx="50" cy="90" rx="5" ry="2.6" fill="{A(["#2F7A40", "#3A7A3C", "#55773A", "#6A6C34"], th)}"/>')
    bs = A([1, 1, .85, .55], th)
    bx, by = bez(p, 1.0)
    tx, ty = tangent(p, 1.0)
    cx, cy = bx + tx * 2.8 * bs, by + ty * 2.8 * bs
    o.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{2.4 * bs:.2f}" ry="{3.4 * bs:.2f}" '
             f'fill="{A(["#9CC46A", "#98BC66", "#A6A864", "#B49A62"], th)}" '
             f'transform="rotate({math.degrees(math.atan2(tx, -ty)):.0f} {cx:.1f} {cy:.1f})"/>')
    # fleurs : contre la hampe (côté intérieur), la chute se fait autour de leur centre
    droop = A([0, 8, 28, 52], th) + 10 * sl
    sx = A([1, 1, .92, .72], th) * (1 - .22 * sl)
    sy = A([1, 1, .95, .8], th) * (1 - .05 * sl)
    f3 = clamp((2.7 - th) / 0.7)  # la 3e fleur rapetisse puis tombe
    for t, sc in ((.36, 1.15), (.60, 1.1), (.80, 1.0 * f3)):
        if sc <= 0.02:
            continue
        px, py = bez(p, t)
        tx, ty = tangent(p, t)
        o.append(f'<g transform="translate({px - ty * 3.5:.1f},{py + tx * 3.5:.1f}) rotate({droop * (.4 + t):.1f}) '
                 f'scale({sc * sx:.3f},{sc * sy:.3f})">{_flower(th)}</g>')
    fall = clamp((th - 2.4) / 0.5)  # fleur tombée, à gauche (la roue des paramètres est en bas à droite)
    if fall > 0:
        o.append(f'<g transform="translate(15,123) rotate(-72) scale({.75 * fall:.3f},{.62 * fall:.3f})">{_flower(3)}</g>')
    o.append(face(kind, th, blink))
    if sl > 0:
        o.append(accessoire_2(sl))
    o.append("</svg>")
    return "".join(o)


def plante_2_head(th, sl=0.0):
    """Point (unités du corps) où se concentrent les fleurs, pour les étoiles et les gouttes."""
    return bez(plante_2_stem(th, sl), .75)


# ───────────────────────────── Plante 3 ─────────────────────────────

_D_STEM = [  # points de contrôle de la tige pour th = 0, 1, 2, 3 (le dernier point est le centre de la fleur)
    [(50, 86), (50, 72), (50, 54), (50, 40)],
    [(50, 86), (50, 72), (51, 56), (53, 42)],
    [(50, 86), (50, 72), (52, 56), (56, 44)],
    [(50, 86), (50, 72), (53, 58), (60, 47)],
]
# couronnes de pétales : (rayon, longueur, largeur, nombre, décalage d'angle, couleur hydratée) ; couleur desséchée commune
_D_RINGS = [(22, 10, 4.2, 16, 0, "#C9304F"), (19.5, 9, 3.9, 15, 11, "#DD4862"), (16.5, 8, 3.5, 13, 5, "#EC6178"),
            (13, 7, 3.1, 11, 16, "#F27C8E"), (9.5, 5.6, 2.7, 9, 8, "#F79AA8"), (6, 4.2, 2.2, 7, 22, "#FAB7C1")]
_D_DRY = ["#8E4A4C", "#9A5456", "#A66062", "#B27073", "#BC8386", "#C69A9C"]


def _mix(c1, c2, t):
    a, b = _rgb(c1), _rgb(c2)
    return "#%02X%02X%02X" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _petal(L, w):
    return f"M0 0C{-w} {-L * .3:.2f} {-w * .85:.2f} {-L * .82:.2f} 0 {-L:.2f}C{w * .85:.2f} {-L * .82:.2f} {w} {-L * .3:.2f} 0 0Z"


def _dleaf(x, y, rot, sc, col, dark):
    lf = '<path d="M0 0C-3-2-3.5-7 0-10C3.5-7 3-2 0 0Z" transform="{}"/>'
    return (f'<g transform="translate({x},{y}) rotate({rot:.1f}) scale({sc})" fill="{col}">'
            f'<path d="M0 0V-19" stroke="{dark}" stroke-width="1" fill="none"/>'
            + lf.format("translate(0,-18)") + lf.format("translate(0,-13) rotate(-55)") + lf.format("translate(0,-13) rotate(55)")
            + lf.format("translate(0,-6) rotate(-62)") + lf.format("translate(0,-6) rotate(62)") + "</g>")


_PANIER = ('<path d="M24 90H76L72 128H28Z" fill="#CFA56F" stroke="#9A7343"/>'
           + "".join(f'<path d="M{24 + (y - 90) * .105:.1f} {y}H{76 - (y - 90) * .105:.1f}" stroke="#A67F4B" stroke-width="1.6"/>'
                     for y in (98, 106, 114, 122))
           + "".join(f'<path d="M{x} {y}v6" stroke="#B58D57" stroke-width="1.2"/>' for y in (92, 108) for x in range(30, 72, 7))
           + "".join(f'<path d="M{x} {y}v6" stroke="#B58D57" stroke-width="1.2"/>' for y in (100, 116) for x in range(33, 70, 7))
           + '<rect x="21" y="86" width="58" height="8" rx="3" fill="#B98C55" stroke="#9A7343"/>')


def _etoile(x, y, s):
    return (f'<path d="M{x} {y - s}l{s * .3:.1f} {s * .7:.1f} {s * .7:.1f} {s * .3:.1f}-{s * .7:.1f} {s * .3:.1f}-{s * .3:.1f} {s * .7:.1f}'
            f'-{s * .3:.1f}-{s * .7:.1f}-{s * .7:.1f}-{s * .3:.1f} {s * .7:.1f}-{s * .3:.1f}z" fill="#FFE08A" stroke="#E6C46A" stroke-width=".4"/>')


def accessoire_3(op):
    """Accessoire de sommeil de la plante 3."""
    return (f'<g opacity="{op:.2f}"><path d="M84 18a8 8 0 1 0 8 10a6.4 6.4 0 1 1-8-10z" fill="#FFE9A8" stroke="#E6C46A" stroke-width=".8"/>'
            + _etoile(18, 30, 5) + _etoile(88, 48, 4) + _etoile(10, 56, 3.4) + _etoile(72, 12, 3) + "</g>")


def plante_3_stem(th, sl=0.0, sway=0.0):
    th = min(3.0, th + 0.35 * sl)
    p = [(A([_D_STEM[j][k][0] for j in range(4)], th), A([_D_STEM[j][k][1] for j in range(4)], th)) for k in range(4)]
    if sway:
        c, s = math.cos(math.radians(sway)), math.sin(math.radians(sway))
        p = [p[0]] + [(50 + (x - 50) * c - (y - 86) * s, 86 + (x - 50) * s + (y - 86) * c) for x, y in p[1:]]
    return p


def plante_3(th, sl=0.0, kind="happy", blink=False, sway=0.0):
    th = clamp(th, 0, 3)
    p = plante_3_stem(th, sl, sway)
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 130">']
    o.append(f'<path d="M50 94L{p[0][0]} {p[0][1]}C{p[1][0]:.1f} {p[1][1]:.1f} {p[2][0]:.1f} {p[2][1]:.1f} {p[3][0]:.1f} {p[3][1]:.1f}" '
             f'stroke="{A(["#4C9A53", "#5A9A4C", "#7A9A44", "#8E8A3C"], th)}" stroke-width="3" fill="none" stroke-linecap="round"/>')
    o.append(_PANIER)  # la tige sort de derrière le haut du panier
    leaf = A(["#4C9A53", "#5A9A4C", "#7A9A44", "#92903E"], th)
    dark = A(["#3E8E4E", "#4B8A44", "#6A8A3C", "#807A36"], th)
    o.append(_dleaf(50, 80, A([-58, -66, -84, -112], th) - 10 * sl, 1.05, leaf, dark))
    o.append(_dleaf(50, 72, A([62, 70, 88, 112], th) + 10 * sl, 0.85, leaf, dark))
    # fleur : en se desséchant elle rétrécit et se recroqueville sur elle-même (pétales plus courts et plus étroits,
    # bouts qui s'enroulent et foncent) ; la tête se penche à peine ; au sommeil elle se referme un peu
    d = clamp((th - 1) / 2)
    rot = A([0, 5, 20, 30], th) + 10 * sl
    hs = A([1, .98, .85, .68], th) * (1 - .12 * sl)
    h = [f'<g transform="translate({p[3][0]:.1f},{p[3][1]:.1f}) rotate({rot:.1f}) scale({hs:.3f})">',
         f'<circle r="{17 * (1 - .3 * d):.2f}" fill="{A(["#B82A47", "#A8283F", "#8A2A3A", "#6A2A32"], th)}"/>']
    for ri, (r, L, w, n, off, c0) in enumerate(_D_RINGS):
        dry = _D_DRY[ri]
        fill = A([c0, _mix(c0, dry, .25), _mix(c0, dry, .6), dry], th)
        edge = _mix(fill, "#3A1018", .3)
        tip = _mix(fill, "#3A1018", .5)
        thr = clamp((th - 2) / 1) * (0.3, 0.2, 0.1, 0, 0, 0)[ri]
        r2, Lr, wr = r * (1 - .32 * d), L * (1 - .25 * d), w * (1 - .3 * d)
        for i in range(n):
            if ((i * 37 + n * 11) % 16) / 16 < thr:
                continue
            tr = f'rotate({off + i * 360 / n:.1f}) translate(0,{-(r2 - Lr):.2f})'
            h.append(f'<g transform="{tr}"><path d="{_petal(Lr, wr)}" fill="{fill}" stroke="{edge}" stroke-width=".5"/>'
                     + (f'<ellipse cy="{-Lr + 1.4:.2f}" rx="{wr * .6:.2f}" ry="1.5" fill="{tip}" opacity="{min(1, d * 1.4):.2f}"/>' if d > 0 else "")
                     + "</g>")
    h.append(f'<circle r="{2.4 * (1 - d * .7):.2f}" fill="{A(["#F3D27A", "#E2C070", "#C0A060", "#8E7550"], th)}"/></g>')
    o.append("".join(h))
    fall = clamp((th - 2.4) / 0.5)  # pétales tombés à gauche (la roue des paramètres est à droite)
    if fall > 0:
        for x, y, rt in ((12, 126.5, -70), (21, 127.5, 25), (7, 121, 40)):
            o.append(f'<path d="{_petal(8, 3.6)}" transform="translate({x},{y}) rotate({rt}) scale({fall:.3f})" '
                     f'fill="{_D_DRY[1]}" stroke="{_mix(_D_DRY[1], "#3A1018", .3)}" stroke-width=".5"/>')
    o.append(face(kind, th, blink, 50, 107, 0.8))
    if sl > 0:
        o.append(accessoire_3(sl))
    o.append("</svg>")
    return "".join(o)


def plante_3_head(th, sl=0.0):
    return plante_3_stem(th, sl)[3]


# ───────────────────────────── Plante 4 ─────────────────────────────

_M_STEM = [  # points de contrôle (après (50, 90)) de la hampe pour th = 0, 1, 2, 3 : de l'arc léger au crochet
    [(50, 54), (57, 18), (76, 20)], [(50, 56), (60, 22), (80, 28)], [(50, 58), (66, 26), (84, 44)], [(50, 60), (70, 32), (82, 64)],
]
# fleurs : (position le long de la hampe, taille, côté) ; les dernières tombent quand la plante se dessèche
_M_BELLS = [(.42, 1.35, 1), (.50, 1.30, -1), (.60, 1.25, 1), (.68, 1.18, -1), (.78, 1.08, 1), (.86, .98, -1), (.94, .85, 1)]
_M_LIMIT = (99, 99, 99, 99, 2.8, 2.5, 2.2)  # th à partir duquel chaque clochette a fini de tomber
_BELL = "M-4 0C-4.6-6.5 4.6-6.5 4 0L3.3 1.4L2.2 .3L1.1 1.6L0 .4L-1.1 1.6L-2.2 .3L-3.3 1.4Z"
# feuilles : pose hydratée et pose flasque (les poses intermédiaires sont interpolées), chaque pose = 10 nombres
_M_FRONT = ((48, 90, 34, 76, 27, 54, 33, 34, 44, 48, 52, 68, 53, 90), (48, 90, 38, 74, 26, 62, 22, 52, 36, 62, 46, 78, 53, 90),
            (48, 90, 36, 70, 20, 66, 14, 80, 22, 90, 40, 92, 53, 90))
_M_BACK = ((52, 90, 62, 76, 68, 58, 64, 38, 57, 50, 52, 68, 50, 90), (52, 90, 62, 74, 74, 62, 78, 52, 66, 62, 56, 78, 50, 90),
           (52, 90, 64, 70, 80, 66, 86, 80, 78, 90, 60, 92, 50, 90))


def plante_4_stem(th, sl=0.0, sway=0.0):
    th = min(3.0, th + 0.35 * sl)
    p = [(50, 90)] + [(A([_M_STEM[j][k][0] for j in range(4)], th), A([_M_STEM[j][k][1] for j in range(4)], th)) for k in range(3)]
    if sway:
        c, s = math.cos(math.radians(sway)), math.sin(math.radians(sway))
        p = [p[0]] + [(50 + (x - 50) * c - (y - 90) * s, 90 + (x - 50) * s + (y - 90) * c) for x, y in p[1:]]
    return p


def _arc_t(p, f, n=60):
    pts = [bez(p, i / n) for i in range(n + 1)]
    d = [0.0]
    for i in range(1, n + 1):
        d.append(d[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    target = f * d[-1]
    for i in range(1, n + 1):
        if d[i] >= target:
            return (i - 1 + (target - d[i - 1]) / ((d[i] - d[i - 1]) or 1)) / n
    return 1.0


def _m_leaf(pose, u, fill):
    lo, hi, k = (pose[0], pose[1], 2 * u) if u < .5 else (pose[1], pose[2], 2 * u - 1)
    v = [a + (b - a) * k for a, b in zip(lo, hi)]
    return (f'<path d="M{v[0]:.1f} {v[1]:.1f}C{v[2]:.1f} {v[3]:.1f} {v[4]:.1f} {v[5]:.1f} {v[6]:.1f} {v[7]:.1f}'
            f'C{v[8]:.1f} {v[9]:.1f} {v[10]:.1f} {v[11]:.1f} {v[12]:.1f} {v[13]:.1f}Z" fill="{fill}"/>', v)


def accessoire_4(x, y, ang, op):
    """Accessoire de sommeil de la plante 4."""
    return (f'<g opacity="{op:.2f}" transform="translate({x:.1f},{y:.1f}) rotate({ang:.0f}) scale(1.25)">'
            '<path d="M-3.6 1Q-3.4 -7 3 -9.5Q7.4 -10 8.4 -5.6Q4.6 -7.4 2 -4.2Q3.4 -2 3.7 1Z" fill="#4A5FA8" stroke="#34447E" stroke-width=".5"/>'
            '<path d="M-1 -3L-.6 -7.4M1.6 -5.6L1.8 -8.6" stroke="#FFFFFF" stroke-width=".9" opacity=".85"/>'
            '<path d="M-4.1 .4Q0 -1.2 4.1 .4L3.9 2Q0 .4-3.9 2Z" fill="#F3EEFF" stroke="#BDB3E0" stroke-width=".4"/>'
            '<circle cx="8.4" cy="-5.6" r="1.9" fill="#FFFFFF" stroke="#BDB3E0" stroke-width=".4"/></g>')


def plante_4(th, sl=0.0, kind="happy", blink=False, sway=0.0):
    th = clamp(th, 0, 3)
    p = plante_4_stem(th, sl, sway)
    tl = min(3.0, th + 0.6 * sl)
    u = tl / 3
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 130">']
    back, bv = _m_leaf(_M_BACK, u, A(["#3E8E4E", "#4B8E48", "#6E9644", "#8C913E"], th))
    o.append(back)
    stalk = A(["#5E9F4F", "#6A9F4A", "#8A9A44", "#8E8238"], th)
    o.append(f'<path d="M50 90C{p[1][0]:.1f} {p[1][1]:.1f} {p[2][0]:.1f} {p[2][1]:.1f} {p[3][0]:.1f} {p[3][1]:.1f}" '
             f'stroke="{stalk}" stroke-width="1.7" fill="none" stroke-linecap="round"/>')
    front, fv = _m_leaf(_M_FRONT, u, A(["#4FA060", "#5A9F55", "#7DA050", "#97964A"], th))
    o.append(front)
    vein = A(["#6CBB78", "#78B572", "#92AA68", "#A5A262"], th)
    for v in (bv, fv):  # nervure médiane : suit la pose de la feuille
        o.append(f'<path d="M{v[0]:.1f} 88Q{(v[2] + v[4]) / 2:.1f} {(v[3] + v[5]) / 2:.1f} {v[6]:.1f} {v[7]:.1f}" stroke="{vein}" stroke-width=".7" fill="none"/>')
    o.append(f'<path d="M47 90C45 84 46 80 50 78C54 80 55 84 53 90Z" fill="{A(["#2F7A40", "#3A7A3C", "#55773A", "#6A6C34"], th)}"/>')
    # fleurs
    fill = A(["#FFFFFF", "#FBF4E6", "#EFE0B4", "#C8A670"], th)
    edge = A(["#D9D2C2", "#D8CBA8", "#C2A66A", "#8F6F3E"], th)
    for (f, sz, d), lim in zip(_M_BELLS, _M_LIMIT):
        k = clamp((lim - th) / 0.4)
        if k <= 0.02:
            continue
        x, y = bez(p, _arc_t(p, f))
        s = sz * k * (1 - .18 * th / 3)
        bx, by = x + d * (3 + s), y + 5.5 + 5 * s
        rot = d * (th * 7 + 10 * sl)
        o.append(f'<path d="M{x:.1f} {y:.1f}Q{bx:.1f} {y - .5:.1f} {bx:.1f} {by - 5.3 * s:.1f}" stroke="{stalk}" stroke-width=".8" fill="none"/>')
        o.append(f'<g transform="translate({bx:.1f},{by - 5.3 * s:.1f}) rotate({rot:.1f}) translate(0,{5.3 * s:.1f}) scale({s:.3f})">'
                 f'<path d="{_BELL}" fill="{fill}" stroke="{edge}" stroke-width=".45"/>'
                 f'<path d="M-2.6-1C-2.8-4.2-1.6-5.2 0-5.4" stroke="{A(["#EEE8DC", "#EFE6CC", "#E0CE9A", "#B08C58"], th)}" '
                 'stroke-width=".9" fill="none" stroke-linecap="round"/></g>')
    ex, ey = bez(p, 1.0)
    tx, ty = tangent(p, 1.0)
    if sl < 0.5:
        o.append(f'<circle cx="{ex + tx * 2:.1f}" cy="{ey + ty * 2:.1f}" r="1.7" fill="{A(["#CDE6B8", "#C8DDA8", "#BFC590", "#A89A70"], th)}"/>')
    fall = clamp((th - 2.2) / 0.7)  # fleurs tombées à gauche (la roue des paramètres est à droite)
    if fall > 0:
        for x, y, rt in ((13, 126.6, -70), (22, 128, 30)):
            o.append(f'<g transform="translate({x},{y}) rotate({rt}) scale({.8 * fall:.3f})"><path d="{_BELL}" fill="{fill}" stroke="{edge}" stroke-width=".5"/></g>')
    # bol céladon, par-dessus le pied des feuilles
    o.append('<path d="M26 94H74C76 114 70 128 50 128C30 128 24 114 26 94Z" fill="#BFD9C6"/>'
             '<path d="M30 100C29 112 33 122 42 125" stroke="#D6E9DB" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
             '<rect x="23" y="88" width="54" height="8" rx="4" fill="#A7C9B0"/>')
    o.append(face(kind, th, blink, 50, 108, 0.8))
    if sl > 0:
        o.append(accessoire_4(ex + tx * 1.5, ey + ty * 1.5, math.degrees(math.atan2(tx, -ty)), sl))
    o.append("</svg>")
    return "".join(o)


def plante_4_head(th, sl=0.0):
    return bez(plante_4_stem(th, sl), .8)


# ───────────────────────────── Plante 5 ─────────────────────────────

_T_STEM = [  # points de contrôle (après (50, 94)) de la tige pour th = 0..3 : droite, puis le cou se courbe sous le poids de la tête
    [(50, 76), (50, 58), (50, 34)], [(50, 76), (50, 58), (53, 37)], [(50, 76), (51, 56), (60, 43)], [(50, 76), (52, 52), (70, 57)],
]
# deux couronnes de pétales : (rayon, longueur, largeur, nombre, décalage, couleurs hydratée / desséchée)
_T_RINGS = [(25, 13, 3.8, 22, 0, "#F2A80F", "#8A5A1E", "#D08A06"), (22.5, 11.5, 3.4, 22, 8.2, "#FFCB2F", "#A8772C", "#E8A80F")]
_T_LEAF_L = ((50, 74, 40, 64, 30, 66, 26, 70, 32, 78, 44, 78, 50, 74), (50, 74, 38, 76, 26, 84, 20, 98, 32, 92, 44, 86, 50, 74))
_T_LEAF_R = ((50, 80, 60, 72, 70, 74, 74, 78, 68, 86, 56, 85, 50, 80), (50, 80, 62, 84, 74, 92, 80, 104, 68, 98, 58, 90, 50, 80))


def plante_5_stem(th, sl=0.0, sway=0.0):
    th = min(3.0, th + 0.3 * sl)
    p = [(50, 94)] + [(A([_T_STEM[j][k][0] for j in range(4)], th), A([_T_STEM[j][k][1] for j in range(4)], th)) for k in range(3)]
    if sway:
        c, s = math.cos(math.radians(sway)), math.sin(math.radians(sway))
        p = [p[0]] + [(50 + (x - 50) * c - (y - 94) * s, 94 + (x - 50) * s + (y - 94) * c) for x, y in p[1:]]
    return p


def accessoire_5(op):
    """Accessoire de sommeil de la plante 5."""
    return (f'<g opacity="{op:.2f}">'
            '<rect x="23.6" y="105.6" width="52.8" height="4.2" rx="2" fill="#3F3B7A" stroke="#2B2858" stroke-width=".6"/>'
            '<path d="M24.5 107.7H75.5" stroke="#6D68B5" stroke-width=".6" stroke-dasharray="1.6 1.4"/>'
            '<path d="M47.6 106.6Q50 104.6 52.4 106.6" stroke="#2B2858" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
            '<ellipse cx="43" cy="107.6" rx="6.2" ry="5.1" fill="#5A52A6" stroke="#2B2858" stroke-width=".8"/>'
            '<ellipse cx="57" cy="107.6" rx="6.2" ry="5.1" fill="#5A52A6" stroke="#2B2858" stroke-width=".8"/>'
            '<ellipse cx="43" cy="107.6" rx="4.8" ry="3.8" fill="none" stroke="#B7B2EA" stroke-width=".6" stroke-dasharray="1.4 1.2"/>'
            '<ellipse cx="57" cy="107.6" rx="4.8" ry="3.8" fill="none" stroke="#B7B2EA" stroke-width=".6" stroke-dasharray="1.4 1.2"/>'
            '</g>')


def plante_5(th, sl=0.0, kind="happy", blink=False, sway=0.0):
    th = clamp(th, 0, 3)
    p = plante_5_stem(th, sl, sway)
    tl = min(3.0, th + 0.5 * sl)
    u = tl / 3
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 130">',
         '<path d="M30 92Q50 70 70 92" stroke="#8C99A6" stroke-width="2" fill="none"/>']  # l'anse, derrière la plante
    o.append(f'<path d="M50 94C{p[1][0]:.1f} {p[1][1]:.1f} {p[2][0]:.1f} {p[2][1]:.1f} {p[3][0]:.1f} {p[3][1]:.1f}" '
             f'stroke="{A(["#4C9A53", "#5A9A4C", "#7A9A44", "#8E8A3C"], th)}" stroke-width="3.2" fill="none" stroke-linecap="round"/>')
    o.append('<path d="M22 92H78L72 128H28Z" fill="#5DA9E9"/><rect x="20" y="88" width="60" height="6" rx="3" fill="#2F6FA8"/>'
             '<rect x="26" y="123" width="48" height="5" rx="2" fill="#2F6FA8"/>')
    for pose, base in ((_T_LEAF_L, ["#5FAE6E", "#6AAA5C", "#8EA84E", "#A39640"]), (_T_LEAF_R, ["#6CC070", "#76B862", "#98AE50", "#A89A44"])):
        v = [a_ + (b_ - a_) * u for a_, b_ in zip(pose[0], pose[1])]
        o.append(f'<path d="M{v[0]:.1f} {v[1]:.1f}C{v[2]:.1f} {v[3]:.1f} {v[4]:.1f} {v[5]:.1f} {v[6]:.1f} {v[7]:.1f}'
                 f'C{v[8]:.1f} {v[9]:.1f} {v[10]:.1f} {v[11]:.1f} {v[12]:.1f} {v[13]:.1f}Z" fill="{A(base, th)}"/>'
                 f'<path d="M{v[0]:.1f} {v[1]:.1f}L{v[6]:.1f} {v[7]:.1f}" stroke="{A(["#3E8E4E", "#4B8A44", "#6A8A3C", "#807A36"], th)}" stroke-width=".7"/>')
    # tête : elle s'incline, ses pétales se raccourcissent, foncent et retombent, quelques-uns tombent
    d = clamp((th - 1.2) / 1.8)
    rot = A([0, 10, 38, 75], th) + 12 * sl
    hs = A([1, .98, .92, .82], th) * (1 - .06 * sl)
    h = [f'<g transform="translate({p[3][0]:.1f},{p[3][1]:.1f}) rotate({rot:.1f}) scale({hs:.3f})">']
    for ri, (r, L, w, n, off, c0, c1, e0) in enumerate(_T_RINGS):
        fill = A([c0, _mix(c0, c1, .25), _mix(c0, c1, .6), c1], th)
        edge = _mix(e0, "#3A2010", th / 3 * .5)
        thr = clamp((th - 2) / 1) * (0.35, 0.25)[ri]
        Lr = L * A([1, 1, .92, .82], th)
        for i in range(n):
            if ((i * 37 + n * 11) % 16) / 16 < thr:
                continue
            ang = 180 + ((off + i * 360 / n) % 360 - 180) * (1 - .45 * d)
            h.append(f'<path d="{_petal(Lr, w)}" transform="rotate({ang:.1f}) translate(0,{-(r - Lr):.2f})" '
                     f'fill="{fill}" stroke="{edge}" stroke-width=".5"/>')
    h.append(f'<circle r="11.5" fill="{A(["#5A3418", "#563218", "#4C2E18", "#3E2614"], th)}" stroke="#8A5A2A" stroke-width="1.6"/>')
    for i in range(1, 110):
        a_, rr = i * 2.39996, 10 * math.sqrt(i / 110)
        h.append(f'<circle cx="{rr * math.cos(a_):.2f}" cy="{rr * math.sin(a_):.2f}" r=".55" fill="{"#3A2010" if i % 3 else "#B07A3A"}"/>')
    h.append("</g>")
    o.append("".join(h))
    fall = clamp((th - 2.4) / 0.5)  # pétales tombés à gauche (la roue des paramètres est à droite)
    if fall > 0:
        for x, y, rt in ((10, 126.5, -70), (19, 127.8, 25), (6, 120, 40)):
            o.append(f'<path d="{_petal(9, 3.4)}" transform="translate({x},{y}) rotate({rt}) scale({fall:.3f})" '
                     'fill="#A8772C" stroke="#7A5A20" stroke-width=".5"/>')
    o.append(face(kind, th, blink, 50, 108, 0.8))
    if sl > 0:
        o.append(accessoire_5(sl))
    o.append("</svg>")
    return "".join(o)


def plante_5_head(th, sl=0.0):
    return plante_5_stem(th, sl)[3]


# ───────────────────────────── Plante 6 ─────────────────────────────

_C_BODY = ["#5FAE6E", "#6AAE68", "#8AAE5E", "#A39F56"]
_C_RIB = ["#4C9A53", "#5C9A4A", "#7A8A40", "#8E7C38"]
_C_PETAL = ["#FF8FB1", "#F59AB0", "#D7A0A0", "#9A7A5A"]
_C_CTR = ["#F7C948", "#E8BC50", "#C0A060", "#8A7048"]


def _cf(th, sc=1.0):
    """Petite fleur à cinq pétales."""
    pet = A(_C_PETAL, th)
    ps = "".join(f'<ellipse cy="-3" rx="1.8" ry="3" transform="rotate({r})"/>' for r in (0, 72, 144, 216, 288))
    return f'<g transform="scale({sc:.3f})"><g fill="{pet}">{ps}</g><circle r="1.3" fill="{A(_C_CTR, th)}"/></g>'


def accessoire_6(op):
    """Accessoire de sommeil de la plante 6."""
    zig = "M33.4 121" + "".join("l2.4-2.4 2.4 2.4" for _ in range(7))
    ticks = "".join(f'<path d="M{x} 116.8v3" stroke="#2E807F" stroke-width=".7"/>' for x in range(34, 67, 3))
    return (f'<g opacity="{op:.2f}">'
            '<ellipse cx="29.6" cy="121.6" rx="3.2" ry="4.6" transform="rotate(14 29.6 121.6)" fill="#3E9C9A" stroke="#2E807F" stroke-width=".7"/>'
            '<ellipse cx="70.4" cy="121.6" rx="3.2" ry="4.6" transform="rotate(-14 70.4 121.6)" fill="#3E9C9A" stroke="#2E807F" stroke-width=".7"/>'
            '<path d="M31.67 117H68.33A20 20 0 0 1 31.67 117Z" fill="#3E9C9A"/>'
            + ticks + f'<path d="{zig}" stroke="#FFF3E0" stroke-width="1.3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            '<path d="M31.67 117Q50 120.6 68.33 117" stroke="#2E807F" stroke-width="3.2" fill="none" stroke-linecap="round"/>'
            '<path d="M36.2 124.6H63.8A20 20 0 0 1 36.2 124.6Z" fill="#2E807F" opacity=".35"/>'
            '<circle cx="40" cy="124.6" r=".9" fill="#FFF3E0"/><circle cx="50" cy="125.4" r=".9" fill="#FFF3E0"/><circle cx="60" cy="124.6" r=".9" fill="#FFF3E0"/></g>')


def plante_6(th, sl=0.0, kind="happy", blink=False, sway=0.0):
    th = clamp(th, 0, 3)
    sx = A([1, .97, .92, .84], th)
    top = 40 + A([0, 0, 2, 6], th)
    body, rib = A(_C_BODY, th), A(_C_RIB, th)
    theta = A([0, 4, 12, 28], th) + 8 * sl  # les bras s'affaissent (elle ne penche pas : elle se ride, jaunit et se tasse)
    kf = clamp((2.5 - th) / 0.4)  # fleurs des bras : elles tombent
    fl = A([1, .95, .72, .5], th) * (1 - .15 * sl)
    wr = clamp((th - 1.4) / 1.2)
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 130">', f'<g transform="rotate({sway:.1f} 50 92)">']
    o.append(f'<rect x="{50 - 9 * sx:.2f}" y="{top:.1f}" width="{18 * sx:.2f}" height="{92 - top:.1f}" rx="{9 * sx:.2f}" fill="{body}"/>')
    o.append(f'<path d="M50 {top + 4:.1f}V90M{50 - 5 * sx:.1f} {top + 8:.1f}V88M{50 + 5 * sx:.1f} {top + 8:.1f}V88" stroke="{rib}" stroke-width=".8"/>')
    if wr > 0:
        for sgn in (-1, 1):
            xx = 50 + sgn * 3.2 * sx
            o.append(f'<path d="M{xx:.1f} {top + 12:.1f}q{-1.8 * sgn} 6 0 12q{1.8 * sgn} 6 0 12q{-1.8 * sgn} 6 0 12q{1.8 * sgn} 6 0 12" '
                     f'stroke="{rib}" stroke-width="1" fill="none" opacity="{wr:.2f}"/>')
    o.append(f'<g transform="rotate({-theta:.1f} 43 72)"><rect x="28" y="56" width="9" height="20" rx="4.5" fill="{body}"/>'
             f'<rect x="28" y="68" width="15" height="8" rx="4" fill="{body}"/>'
             + (f'<g transform="translate(32.5,55)">{_cf(th, .85 * kf)}</g>' if kf > .02 else "") + '</g>')
    o.append(f'<g transform="rotate({theta:.1f} 57 65)"><rect x="63" y="50" width="9" height="18" rx="4.5" fill="{body}"/>'
             f'<rect x="57" y="61" width="15" height="7" rx="3.5" fill="{body}"/>'
             + (f'<g transform="translate(67.5,49)">{_cf(th, .85 * kf)}</g>' if kf > .02 else "") + '</g>')
    spine = A(["#E8F4E0", "#EDEBC8", "#D8CFA0", "#B8A878"], th)
    o.append("".join(f'<circle cx="{x}" cy="{y}" r=".6" fill="{spine}"/>' for x, y in
                     ((47.5, 54 + top - 40), (52.5, 62 + top - 40), (47.5, 72), (52.5, 80), (32.5, 64), (67.5, 58))))
    o.append(f'<g transform="translate(50,{top + 1 - 3.5 * fl:.1f}) scale({fl:.3f},{fl * A([1, 1, .9, .8], th):.3f})">'
             f'<g fill="{A(_C_PETAL, th)}"><circle cx="-4" cy="0" r="3.5"/><circle cx="4" cy="0" r="3.5"/><circle cx="0" cy="-4" r="3.5"/></g>'
             f'<circle r="2" fill="{A(_C_CTR, th)}"/></g>')
    if kf > .02:
        o.append(f'<ellipse cx="60" cy="74" rx="{1.8 * kf:.2f}" ry="{2.6 * kf:.2f}" fill="{A(_C_PETAL, th)}" transform="rotate(50 60 74)"/>')
    o.append("</g>")
    fall = clamp((th - 2.3) / 0.6)  # fleurs tombées à gauche (la roue des paramètres est à droite)
    if fall > 0:
        for x, y, rt in ((13, 127.4, 30), (23, 128.4, -40)):
            o.append(f'<g transform="translate({x},{y}) rotate({rt})">{_cf(3, .75 * fall)}</g>')
    o.append('<circle cx="50" cy="109" r="20" fill="#F7B7C8"/><rect x="33" y="86" width="34" height="7" rx="3.5" fill="#EE9BB1"/>')
    o.append(face(kind, th, blink, 50, 108.5, 0.7))
    if sl > 0:
        o.append(accessoire_6(sl))
    o.append("</svg>")
    return "".join(o)


def plante_6_head(th, sl=0.0):
    return (50, 40 + A([0, 0, 2, 6], th))


# ───────────────────────────── Plante 7 ─────────────────────────────

# trois tiges (grande à gauche, petite au milieu, une à droite) : (P1, P2, P3 = centre de la fleur) pour th = 0..3
_TU_STEMS = [
    [((47.3, 72), (45, 54), (35, 38)), ((47, 72), (44, 54), (35, 41)), ((46, 68), (38, 52), (28, 50)), ((46, 66), (34, 48), (22, 70))],
    [((51.7, 77.3), (55, 60), (57, 54)), ((51.7, 77), (55, 61), (58, 57)), ((52, 75), (58, 60), (62, 62)), ((52, 74), (60, 58), (66, 72))],
    [((55.3, 74.7), (64.7, 50), (68, 34)), ((55, 74), (64.5, 52), (69, 37)), ((56, 72), (68, 52), (76, 50)), ((56, 70), (74, 50), (82, 72))],
]
_TU_COL = [  # (couleur hydratée -> desséchée) des trois fleurs
    ["#E5484D", "#D9505A", "#B85A5E", "#8A5A52"], ["#F28CA8", "#E49AAE", "#C0A0A8", "#9A8478"], ["#F7C948", "#E8C458", "#C8AE62", "#9A8650"],
]
_TU_SIZE = (1.25, .82, 1.02)
_TU_SIGN = (-1, 1, 1)
# feuilles : (cx, cy, rx, ry, rotation, couleurs, côté) ; la grande feuille de gauche porte la nervure centrale
_TU_LEAVES = [
    (35, 70, 6.5, 23, -20, ["#5FAE6E", "#6AAA5C", "#8EA84E", "#A39640"], -1),
    (67, 80, 3.5, 11, 26, ["#6CC070", "#76B862", "#98AE50", "#A89A44"], 1),
    (44, 82, 3, 9, -10, ["#7CC77A", "#86BC68", "#A4B058", "#AE9E48"], -1),
    (57, 81, 3.2, 10, 14, ["#4C9A53", "#5A9A4C", "#7A9A44", "#8E8A3C"], 1),
    (51, 84, 2.4, 7, 0, ["#6CC070", "#76B862", "#98AE50", "#A89A44"], 1),
]


def _tu_stem(i, th, sl=0.0, sway=0.0):
    th = min(3.0, th + 0.35 * sl)
    pts = [(50, 92)] + [(A([_TU_STEMS[i][j][k][0] for j in range(4)], th), A([_TU_STEMS[i][j][k][1] for j in range(4)], th)) for k in range(3)]
    if sway:
        c, s_ = math.cos(math.radians(sway)), math.sin(math.radians(sway))
        pts = [pts[0]] + [(50 + (x - 50) * c - (y - 92) * s_, 92 + (x - 50) * s_ + (y - 92) * c) for x, y in pts[1:]]
    return pts


def accessoire_7(op):
    """Accessoire de sommeil de la plante 7."""
    fx = "".join(f'<path d="M{x} 86q-3-3.4 0-6.8q3-3.4 0-6.8" stroke="#E6EEF8" stroke-width="1.5" fill="none" stroke-linecap="round" opacity=".8"/>'
                    for x in (41, 60))
    return (f'<g opacity="{op:.2f}">{fx}<path d="M35 90Q31 95 32 101" stroke="#B8A890" stroke-width=".9" fill="none"/>'
            '<g transform="rotate(8 33 106)"><rect x="28.4" y="100.6" width="9" height="11" rx="1.8" fill="#FFF3E0" stroke="#C9653C" stroke-width=".8"/>'
            '<circle cx="33" cy="102.6" r=".8" fill="#C9653C"/>'
            '<path d="M30.8 105.4h4.2l-4.2 4.2h4.2" stroke="#5B6EAE" stroke-width="1.1" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g></g>')


def plante_7(th, sl=0.0, kind="happy", blink=False, sway=0.0):
    th = clamp(th, 0, 3)
    d = th / 3
    thl = min(3.0, th + 0.4 * sl)
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 130">', f'<g transform="rotate({sway:.1f} 50 92)">']
    stem = A(["#4C9A53", "#5A9A4C", "#7A9A44", "#8E8A3C"], th)
    stems = [_tu_stem(i, th, sl) for i in range(3)]
    for q in stems:
        o.append(f'<path d="M50 92C{q[1][0]:.1f} {q[1][1]:.1f} {q[2][0]:.1f} {q[2][1]:.1f} {q[3][0]:.1f} {q[3][1]:.1f}" '
                 f'stroke="{stem}" stroke-width="2.2" fill="none" stroke-linecap="round"/>')
    ang = A([0, 5, 16, 30], thl)
    for cx, cy, rx, ry, rot, cols, side in _TU_LEAVES:
        o.append(f'<g transform="rotate({side * ang:.1f} 50 92)"><ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry * (1 - .12 * d):.1f}" '
                 f'fill="{A(cols, th)}" transform="rotate({rot} {cx} {cy})"/>'
                 + ('<path d="M41.7 88.3L28.3 51.7" stroke="#4C9A53" stroke-width=".8"/>' if cx == 35 else "") + '</g>')
    droop = A([0, 8, 40, 165], th) + 12 * sl
    sc = A([1, .98, .9, .8], th) * (1 - .06 * sl)
    openx = A([1, 1, 1.12, 1.25], th)
    for i, q in enumerate(stems):
        col = A(_TU_COL[i], th)
        s_ = _TU_SIZE[i]
        o.append(f'<g transform="translate({q[3][0]:.1f},{q[3][1]:.1f}) rotate({_TU_SIGN[i] * droop:.1f}) scale({s_ * sc * openx:.3f},{s_ * sc:.3f})">'
                 f'<path d="M-6 0C-7-10-3-14 0-9C3-14 7-10 6 0C4 4-4 4-6 0Z" fill="{col}" stroke="{_mix(col, "#3A1018", .25)}" stroke-width=".5"/>'
                 '<path d="M0-9C-2.5-5-2.5 0 0 2C2.5 0 2.5-5 0-9Z" fill="#000" opacity=".13"/></g>')
    o.append("</g>")
    fall = clamp((th - 2.3) / 0.6)  # pétales tombés à gauche (la roue des paramètres est à droite)
    if fall > 0:
        for x, y, rt, ci in ((12, 126, -60, 0), (21, 128, 20, 1), (28, 129.4, 80, 2)):
            o.append(f'<ellipse cx="{x}" cy="{y}" rx="{2.2 * fall:.2f}" ry="{3.8 * fall:.2f}" transform="rotate({rt} {x} {y})" '
                     f'fill="{A(_TU_COL[ci], 3)}" stroke="{_mix(A(_TU_COL[ci], 3), "#3A1018", .3)}" stroke-width=".4"/>')
    o.append('<path d="M70 98a9 9 0 0 1 0 18" stroke="#EDE6DC" stroke-width="5" fill="none"/>'
             '<rect x="28" y="90" width="44" height="38" rx="7" fill="#F7F3EE" stroke="#DCD3C6"/><rect x="28" y="96" width="44" height="3" fill="#7DB6E3"/>')
    o.append(face(kind, th, blink, 50, 109, 0.8))
    if sl > 0:
        o.append(accessoire_7(sl))
    o.append("</svg>")
    return "".join(o)


def plante_7_head(th, sl=0.0):
    return _tu_stem(1, th, sl)[3]


# ───────────────────────────── Plante 8 ─────────────────────────────

# pointe de chaque tige (th = 0) ; les tiges partent toutes de (50, 88)
_L_TIPS = [(50, 24), (42, 30), (58, 28), (35, 38), (65, 36), (29, 49), (71, 47), (54, 40), (45, 44)]
# inclinaison de chaque tige en se desséchant (signe = côté, valeur = intensité) : pas deux paquets symétriques
_L_DROOP = (.5, -.7, 1.0, -.4, .8, -1.0, .6, -.9, .3)
_L_G1 = ["#A3B898", "#A8B890", "#B2B07C", "#A89A64"]
_L_G2 = ["#8FA884", "#98A87C", "#A8A670", "#9A8A5C"]


def _rot(v, deg):
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (v[0] * c - v[1] * s_, v[0] * s_ + v[1] * c)


def accessoire_8(x, y, op):
    """Accessoire de sommeil de la plante 8."""
    return (f'<g opacity="{op:.2f}" transform="translate({x + 2.5:.1f},{y + 5:.1f})">'
            '<ellipse cx="-1.4" cy="-3.6" rx="2.6" ry="1.4" fill="#EAF2FF" stroke="#B9CBE6" stroke-width=".4" transform="rotate(-25 -1.4 -3.6)"/>'
            '<ellipse cx="1.4" cy="-3.8" rx="2.6" ry="1.4" fill="#EAF2FF" stroke="#B9CBE6" stroke-width=".4" transform="rotate(20 1.4 -3.8)"/>'
            '<ellipse cx="0" cy="0" rx="5" ry="3.4" fill="#F7C948" stroke="#8A6A12" stroke-width=".6"/>'
            '<path d="M0.4-3.2V3.2M3 -2.6V2.6" stroke="#3A2A1A" stroke-width="1.3"/>'
            '<circle cx="-4.8" cy="0.4" r="2.5" fill="#F7C948" stroke="#8A6A12" stroke-width=".6"/>'
            '<path d="M-6 0.2q1 1 2 0" stroke="#3A2A1A" stroke-width=".7" fill="none" stroke-linecap="round"/>'
            '<path d="M-5.6-1.8q-1-2-2.2-2.4M-4.2-2q-.2-2.2-1.2-3" stroke="#3A2A1A" stroke-width=".6" fill="none" stroke-linecap="round"/>'
            '<path d="M6 -7h3l-3 3.4h3" stroke="#7F93B5" stroke-width=".9" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>')


def plante_8(th, sl=0.0, kind="happy", blink=False, sway=0.0):
    th = clamp(th, 0, 3)
    d = th / 3
    thl = min(3.0, th + 0.4 * sl)
    c1, c2 = A(_L_G1, th), A(_L_G2, th)
    tl = A([0, 5, 14, 26], thl)
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 130">', f'<g transform="rotate({sway:.1f} 50 90)">']

    def leaf(cy, ry, rot, fill, extra=1.0):
        sg = 1 if rot >= 0 else -1
        return (f'<ellipse cx="50" cy="{cy}" rx="2" ry="{ry * (1 - .15 * d):.1f}" fill="{fill}" '
                f'transform="rotate({rot + sg * tl * extra:.1f} 50 91)"/>')
    o += [leaf(78, 13, r_, c1) for r_ in (-62, -36, -12, 14, 38, 64)]
    o += [leaf(80, 11, r_, c2) for r_ in (-50, -24, 2, 26, 52)]
    stalk = A(["#8BA77F", "#8FA474", "#A0A06A", "#9A8A58"], th)
    spike = A(["#8E6BC7", "#9A7BC0", "#A890A8", "#8E7A70"], th)
    tipc = A(["#B79BE0", "#B8A0C8", "#C0B0B0", "#A89888"], th)
    dash = f"{A([3, 2.8, 2.4, 2.0], th):.1f} {A([1.6, 1.8, 2.6, 3.4], th):.1f}"
    tip = (65, 36)
    for idx, ((tx, ty), fk) in enumerate(zip(_L_TIPS, _L_DROOP)):
        phi = (A([0, 4, 12, 24], th) + 6 * sl) * fk
        v = ((tx - 50) * A([1, .98, .94, .88], th), (ty - 88) * A([1, .98, .94, .88], th))
        pts = [(50, 88), (50 + _rot((v[0] * .4, v[1] * .4), phi * .2)[0], 88 + _rot((v[0] * .4, v[1] * .4), phi * .2)[1]),
               (50 + _rot((v[0] * .78, v[1] * .78), phi * .75)[0], 88 + _rot((v[0] * .78, v[1] * .78), phi * .75)[1]),
               (50 + _rot(v, phi)[0], 88 + _rot(v, phi)[1])]
        if idx == 4:  # la tige qui porte l'accessoire de sommeil
            tip = pts[3]
        o.append(f'<path d="M50 88C{pts[1][0]:.1f} {pts[1][1]:.1f} {pts[2][0]:.1f} {pts[2][1]:.1f} {pts[3][0]:.1f} {pts[3][1]:.1f}" '
                 f'stroke="{stalk}" stroke-width="1.3" fill="none"/>')
        sp = [bez(pts, .52 + .48 * k / 8) for k in range(9)]
        o.append('<path d="M' + "L".join(f"{x:.1f} {y:.1f}" for x, y in sp) + f'" stroke="{spike}" stroke-width="{A([5, 4.8, 4.4, 4], th):.1f}" '
                 f'stroke-dasharray="{dash}" stroke-linecap="round" fill="none"/>')
        o.append(f'<circle cx="{sp[-1][0]:.1f}" cy="{sp[-1][1]:.1f}" r="1.3" fill="{tipc}"/>')
    o.append("</g>")
    fall = clamp((th - 2.3) / 0.6)  # fleurs tombées à gauche (la roue des paramètres est à droite)
    if fall > 0:
        for x, y in ((11, 127), (17, 128.4), (23, 127.2), (14, 123.4)):
            o.append(f'<ellipse cx="{x}" cy="{y}" rx="{1.7 * fall:.2f}" ry="{1.2 * fall:.2f}" fill="{A(["#8E6BC7", "#9A7BC0", "#A890A8", "#8E7A70"], 3)}"/>')
    o.append('<rect x="26" y="90" width="48" height="38" rx="4" fill="#E2DDD5"/><rect x="26" y="90" width="48" height="6" fill="#CFC9C0"/>')
    # feuilles de devant : sortent du centre du pot et retombent sur son bord
    o.append(f'<g transform="rotate({sway:.1f} 50 90)">')
    for cy, ry, rot, fill in ((78, 13, 74, c2), (80, 11, 104, c2), (77, 14, 88, c1), (82, 9, 118, c1)):
        for sg in (-1, 1):
            o.append(f'<ellipse cx="50" cy="{cy}" rx="2.1" ry="{ry * (1 - .15 * d):.1f}" fill="{fill}" '
                     f'transform="rotate({sg * min(150, rot + tl * .25):.1f} 50 91)"/>')
    o.append("</g>")
    o.append(face(kind, th, blink, 50, 110, 0.8))
    if sl > 0:
        o.append(f'<g transform="rotate({sway:.1f} 50 90)">{accessoire_8(tip[0], tip[1], sl)}</g>')
    o.append("</svg>")
    return "".join(o)


def plante_8_head(th, sl=0.0):
    return (50, 36 + 12 * th / 3)


# ───────────────────────────── Plante 9 ─────────────────────────────

_B_PAD = [  # couleurs des quatre ellipses d'un nuage de feuillage, hydraté -> desséché
    ["#4F8F42", "#6A9340", "#8E8A3C", "#8A6A30"], ["#5E9F4F", "#78A048", "#9C9244", "#9A7438"],
    ["#6FB35E", "#8AAA52", "#AC9C4E", "#A88440"], ["#86C774", "#9CB860", "#B8A858", "#B88E48"],
]
# nuages de feuillage : (x, y, taille, th où il a fini de tomber ; 99 = reste)
_B_PADS = [(24, 80, 1.0, 99), (76, 56, 1.05, 99), (70, 88, .6, 2.8), (40, 44, .75, 99), (57, 40, 1.2, 99)]


def accessoire_9(x, y, op):
    """Accessoire de sommeil de la plante 9."""
    return (f'<g opacity="{op:.2f}" transform="translate({x:.1f},{y:.1f})">'
            '<path d="M4.4 .6L8.4 -1.2L8.2 1.8Z" fill="#5D93C6" stroke="#3F6C99" stroke-width=".4" stroke-linejoin="round"/>'
            '<ellipse cx="0" cy="-1" rx="5" ry="3.8" fill="#7FB3E0" stroke="#4C7FAE" stroke-width=".6"/>'
            '<ellipse cx="0.4" cy="0.4" rx="3.2" ry="2" fill="#EAF4FF"/>'
            '<circle cx="-3.4" cy="-3.4" r="2.5" fill="#7FB3E0" stroke="#4C7FAE" stroke-width=".6"/>'
            '<path d="M-5.2 -3.4L-7.2 -2.6L-5 -2Z" fill="#F0A24A" stroke="#C07A28" stroke-width=".3" stroke-linejoin="round"/>'
            '<path d="M-4.6 -4.2q.9.9 1.8 0" stroke="#1E3F5D" stroke-width=".6" fill="none" stroke-linecap="round"/>'
            '<ellipse cx="1" cy="-1.2" rx="2.8" ry="1.8" fill="#5D93C6" stroke="#3F6C99" stroke-width=".4" transform="rotate(-12 1 -1.2)"/>'
            '<path d="M5.4 -7h2.8l-2.8 3h2.8" stroke="#7F93B5" stroke-width=".8" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>')


def plante_9(th, sl=0.0, kind="happy", blink=False, sway=0.0):
    th = clamp(th, 0, 3)
    dy = A([0, 1.5, 4.5, 9], th) + 2 * sl
    sc = A([1, .97, .88, .74], th)
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 130">', f'<g transform="rotate({sway:.1f} 50 108)">',
         f'<ellipse cx="50" cy="107" rx="27" ry="2.6" fill="{A(["#7FA35A", "#8FA656", "#A09A50", "#8A7A46"], th)}"/>',
         '<path d="M47 108q-8-1-13 3M53 108q8-1 13 3" stroke="#7A5236" stroke-width="2.2" fill="none" stroke-linecap="round"/>',
         f'<path d="M50 108C42 100 60 94 51 85C42 76 61 72 54 62C49 56 57 50 57 {44 + dy * .9:.1f}" stroke="#7A5236" stroke-width="6.5" fill="none" stroke-linecap="round"/>',
         '<path d="M50 108C42 100 60 94 51 85" stroke="#93684A" stroke-width="2" fill="none" stroke-linecap="round" transform="translate(1.5,0)"/>',
         '<g stroke="#7A5236" stroke-linecap="round" fill="none">'
         f'<path d="M49 86C40 85 33 {82 + dy * .5:.1f} 24 {84 + dy * .9:.1f}" stroke-width="3"/>'
         f'<path d="M53 67C61 65 68 {60 + dy * .4:.1f} 76 {60 + dy:.1f}" stroke-width="3"/>'
         f'<path d="M53 92C60 94 64 92 70 {90 + dy * .5:.1f}" stroke-width="2"/>'
         f'<path d="M55 54C50 50 44 {50 + dy * .3:.1f} 40 {46 + dy * .7:.1f}" stroke-width="2"/></g>']
    cols = [A(c, th) for c in _B_PAD]
    pose = (76, 50)
    for x, y, sz, lim in _B_PADS:
        k = clamp((lim - th) / 0.4)
        if k <= 0.02:
            continue
        yy = y + dy * (1.1 if x < 60 else 1.0)
        z = sz * sc * k
        if (x, y) == (76, 56):
            pose = (x, yy - 6.4 * z)
        o.append(f'<g transform="translate({x},{yy:.1f}) scale({z:.3f},{z * (1 - .12 * th / 3):.3f})">'
                 f'<ellipse cx="0" cy="0" rx="12" ry="6.5" fill="{cols[0]}"/><ellipse cx="-5" cy="-2" rx="7" ry="4.5" fill="{cols[1]}"/>'
                 f'<ellipse cx="5" cy="-3" rx="7" ry="4" fill="{cols[2]}"/><ellipse cx="1" cy="-4.5" rx="5" ry="2" fill="{cols[3]}"/></g>')
    if sl > 0:
        o.append(accessoire_9(pose[0], pose[1], sl))
    o.append("</g>")
    o.append('<rect x="18" y="110" width="64" height="16" rx="3" fill="#3F8F8A"/><rect x="16" y="107" width="68" height="5" rx="2" fill="#2F6F6B"/>'
             '<rect x="24" y="126" width="8" height="3" fill="#2F6F6B"/><rect x="68" y="126" width="8" height="3" fill="#2F6F6B"/>')
    o.append(face(kind, th, blink, 50, 118.4, 0.55, ink="#1E3F3D"))
    o.append("</svg>")
    return "".join(o)


def plante_9_head(th, sl=0.0):
    return (57, 44 + A([0, 1.5, 4.5, 9], th))


# ───────────────────────────── Plante 10 ─────────────────────────────

_F_DARK = ["#3E8E4E", "#58904A", "#8A8C40", "#96803C"]
_F_FRONT = ["#5FAE6E", "#78A852", "#A09A48", "#A8843E"]
_F_DOME = ["#357D44", "#4C7E3E", "#7A7A38", "#7A6430"]
_F_FRUIT = ["#E5484D", "#C8504C", "#9A5048", "#6A4A3C"]
_F_LEAVES_DARK = [(26, 86, -62, 1.05), (36, 78, -32, 1.1), (50, 74, 0, 1.15), (64, 78, 32, 1.1), (74, 86, 62, 1.05)]
_F_LEAVES_FRONT = [(32, 92, -48, 1.1), (43, 86, -18, 1.2), (57, 86, 18, 1.2), (68, 92, 48, 1.1)]
_F_FLOWERS = [(30, 74, 1.0), (51, 66, .95), (70, 73, .9), (42, 72, .75)]
_F_FRUITS = [(23, 96, 30, 1.0, 99), (77, 97, -28, 1.0, 99), (63, 101, -14, .85, 2.9)]


def _f_leaf(x, y, rot, sc, fill, sy):
    return (f'<g transform="translate({x},{y:.1f}) rotate({rot:.1f}) scale({sc:.3f},{sc * sy:.3f})" fill="{fill}">'
            '<ellipse cy="-7" rx="4.8" ry="6.2"/><ellipse cx="-6" cy="-3" rx="4.5" ry="5.5" transform="rotate(-50 -6 -3)"/>'
            '<ellipse cx="6" cy="-3" rx="4.5" ry="5.5" transform="rotate(50 6 -3)"/>'
            '<path d="M0 0V-11M0 0L-9-6M0 0L9-6" stroke="#2F7340" stroke-width=".6" fill="none"/></g>')


def _f_fruit(col):
    return (f'<path d="M0 0C-5 0-6 5-3 9Q0 12 3 9C6 5 5 0 0 0Z" fill="{col}"/>'
            '<path d="M-3.5-.5L0 1.5L3.5-.5L1.5-2L0-.5L-1.5-2Z" fill="#4C9A53"/>'
            '<g fill="#FFE08A"><circle cx="-1.5" cy="4" r=".5"/><circle cx="1.5" cy="3" r=".5"/><circle cx="0" cy="7" r=".5"/>'
            '<circle cx="-2.5" cy="6.5" r=".4"/><circle cx="2.5" cy="6" r=".4"/></g>')


def accessoire_10(op):
    return (f'<g opacity="{op:.2f}" transform="translate(0,-1) scale(1.15)">'
            '<path d="M-3.4 .4Q-3.2 -6 2 -8Q5.8 -8.4 6.8 -5Q3.8 -6 1.9 -3.4Q3 -1.6 3.4 .4Z" fill="#4A5FA8" stroke="#34447E" stroke-width=".5"/>'
            '<path d="M-.8 -2.6L-.4 -6.6M1.6 -5L1.8 -7.6" stroke="#FFFFFF" stroke-width=".8" opacity=".85"/>'
            '<path d="M-3.8 -.2Q0 -1.6 3.8 -.2L3.6 1.4Q0 0-3.6 1.4Z" fill="#F3EEFF" stroke="#BDB3E0" stroke-width=".4"/>'
            '<circle cx="6.8" cy="-5" r="1.7" fill="#FFFFFF" stroke="#BDB3E0" stroke-width=".4"/></g>')


def plante_10(th, sl=0.0, kind="happy", blink=False, sway=0.0):
    th = clamp(th, 0, 3)
    d = th / 3
    dy = A([0, 1.5, 4, 7], th) + 1.5 * sl
    sc = A([1, .98, .9, .8], th)
    sy = A([1, 1, .92, .82], th)
    out = 1 + .35 * d
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 130">',
         '<rect x="30" y="90" width="40" height="38" rx="3" fill="#C8CDD2"/><path d="M30 94H70M30 124H70" stroke="#A9B0B7"/>'
         '<rect x="30" y="99" width="40" height="20" fill="#F2E8DA"/><rect x="30" y="99" width="40" height="4" fill="#E5484D"/>',
         f'<g transform="rotate({sway:.1f} 50 92)">']
    vine = A(["#4C9A53", "#5C9A4A", "#7A8A40", "#8E7C38"], th)
    o.append(f'<g stroke="{vine}" stroke-width="1.1" fill="none"><path d="M38 90Q28 90 23 {97 + dy * .6:.1f}"/><path d="M62 90Q72 90 77 {98 + dy * .6:.1f}"/>'
             f'<path d="M55 92Q61 95 63 {102 + dy * .4:.1f}"/></g>')
    o.append(f'<ellipse cx="50" cy="{82 + dy * .8:.1f}" rx="27" ry="{10 * (1 - .15 * d):.1f}" fill="{A(_F_DOME, th)}"/>')
    for x, y, rot, z in _F_LEAVES_DARK:
        o.append(_f_leaf(x, y + dy * (1.3 if y < 80 else 1.0), max(-95, min(95, rot * out)), z * sc, A(_F_DARK, th), sy))
    for x, y, rot, z in _F_LEAVES_FRONT:
        o.append(_f_leaf(x, y + dy * 0.9, max(-95, min(95, rot * out)), z * sc, A(_F_FRONT, th), sy))
    fk = clamp((2.0 - th) / 0.6)  # les fleurs blanches se referment puis tombent
    if fk > .02:
        for x, y, z in _F_FLOWERS:
            ps = "".join(f'<circle cx="{cx}" cy="{cy}" r="2.2"/>' for cx, cy in ((0, -2.6), (2.5, -.8), (1.5, 2.1), (-1.5, 2.1), (-2.5, -.8)))
            o.append(f'<g transform="translate({x},{y + dy * 1.2:.1f}) scale({z * fk:.3f})"><g fill="#FFFFFF" stroke="#EADFD3" stroke-width=".4">{ps}</g>'
                     '<circle r="1.4" fill="#F7C948"/></g>')
    for i, (x, y, rot, z, lim) in enumerate(_F_FRUITS):
        k = clamp((lim - th) / 0.4)
        if k <= .02:
            continue
        zz = z * A([1, .95, .8, .6], th) * k
        o.append(f'<g transform="translate({x},{y + dy * .6:.1f}) rotate({rot + (12 if x > 50 else -12) * d:.1f}) scale({zz:.3f})">{_f_fruit(A(_F_FRUIT, th))}'
                 + (accessoire_10(sl) if (sl > 0 and i == 1) else "") + "</g>")
    o.append("</g>")
    fall = clamp((th - 2.4) / 0.5)  # un fruit ridé est tombé à gauche (la roue des paramètres est à droite)
    if fall > 0:
        o.append(f'<g transform="translate(13,127) rotate(80) scale({.7 * fall:.3f})">{_f_fruit(A(_F_FRUIT, 3))}</g>')
    o.append(face(kind, th, blink, 50, 109, 0.7))
    o.append("</svg>")
    return "".join(o)


def plante_10_head(th, sl=0.0):
    return (50, 70 + A([0, 1.5, 4, 7], th))


# ───────────────────────────── Plante 11 ─────────────────────────────

# (couleur hydratée, couleur desséchée) de chaque morceau de la fleur
_R_BLOOM = [("#B8263F", "#5E2A36"), ("#8E1C30", "#40202A"), ("#C42D45", "#6E3040"), ("#E04A60", "#8A4A56"),
            ("#DC3F57", "#7C3444"), ("#EC5C72", "#8E4A58"), ("#E86A7E", "#9A5A66")]
# sommet de la tige (P3) et deuxième point de contrôle (P2) pour th = 0..3 : le cou se courbe sous la fleur
_R_TOP = [(51.6, 44), (53, 45), (56, 46), (58, 47)]
_R_P2 = [(53, 60), (54, 60), (55, 60), (55, 60)]


def accessoire_11(op):
    """Accessoire de sommeil de la plante 11."""
    return (f'<g opacity="{op:.2f}"><ellipse cx="28.6" cy="128.4" rx="6.8" ry="1.5" fill="#C9A24A"/>'
            '<rect x="25" y="118.4" width="7.2" height="10" rx="1.2" fill="#F6E7C8" stroke="#D9C79E" stroke-width=".5"/>'
            '<path d="M25.4 118.8q1.2 2.6 2.2 .5q.9 2.2 1.9 .2q1.4 2.2 2.9-.3" fill="#FFF6DC"/>'
            '<path d="M28.6 118.4V117" stroke="#4A3A2A" stroke-width=".7"/></g>')


def plante_11(th, sl=0.0, kind="happy", blink=False, sway=0.0):
    th = clamp(th, 0, 3)
    thl = min(3.0, th + 0.4 * sl)
    top = (A([t[0] for t in _R_TOP], th), A([t[1] for t in _R_TOP], th))
    p2 = (A([t[0] for t in _R_P2], th), A([t[1] for t in _R_P2], th))
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 130">', f'<g transform="rotate({sway:.1f} 50 92)">']
    stem = A(["#3E8E4E", "#4B8A44", "#6A8A3C", "#807A36"], th)
    o.append(f'<path d="M50 92C47 76 {p2[0]:.1f} {p2[1]:.1f} {top[0]:.1f} {top[1]:.1f}" stroke="{stem}" stroke-width="2.4" fill="none" stroke-linecap="round"/>')
    o.append(f'<path d="M49.5 76Q60 72 64 {60 + A([0, 1, 4, 8], th):.1f}" stroke="{stem}" stroke-width="1.5" fill="none"/>')
    o.append("</g>")
    # pot noir mince, par-dessus le pied de la tige
    o.append('<path d="M35 92H65L63.5 127Q63.3 129 61 129H39Q36.7 129 36.5 127Z" fill="#2B2A2E"/>'
             '<path d="M39 95L38.6 125" stroke="#4A494F" stroke-width="2" stroke-linecap="round" fill="none"/>'
             '<rect x="34" y="89" width="32" height="4" rx="1.5" fill="#3A393E"/>')
    o.append(f'<g transform="rotate({sway:.1f} 50 92)">')
    leaf, dark = A(["#4C9A53", "#5A9A4C", "#7A9A44", "#8E8A3C"], th), A(["#3E8E4E", "#4B8A44", "#6A8A3C", "#807A36"], th)
    k = A([1, 1, .92, .82], th)
    o.append(_dleaf(48.5, 84, A([-60, -68, -85, -110], thl), 1.2 * k, leaf, dark))
    o.append(_dleaf(50, 68, A([60, 68, 85, 108], thl), 1.05 * k, leaf, dark))
    o.append(_dleaf(top[0] - .1, 57 + (top[1] - 44) * .6, A([-46, -55, -75, -100], thl), .75 * k, leaf, dark))
    bud = A(["#C92A44", "#B0304A", "#8A3A44", "#6A3A3A"], th)
    fb = clamp((th - 1.6) / 1.2)  # chute progressive du bourgeon
    by = A([0, 1, 2, 3], th) + 70 * fb ** 1.6
    if fb < 0.999:
        o.append(f'<g opacity="{1 - clamp((fb - .85) / .15):.2f}" transform="translate({8 * fb:.1f},{by:.1f}) rotate({220 * fb:.0f} 64 56)">'
                 f'<path d="M61.5 58Q64 50 66.5 58Q64 61 61.5 58Z" fill="{bud}"/><path d="M61 59l3-2 3 2-3 1.6z" fill="{leaf}"/></g>')
    # fleur : la tête s'incline jusqu'à pendre à l'envers, se referme un peu et fonce
    droop = A([0, 5, 16, 30], th) + 10 * sl
    sc = .78 * A([1, .98, .9, .78], th)
    sx = A([1, 1, .92, .82], th)
    col = [A([c0, _mix(c0, c1, .3), _mix(c0, c1, .65), c1], th) for c0, c1 in _R_BLOOM]
    o.append(f'<path d="M{top[0] - 7:.1f} {top[1] + 1.2:.1f}l7-2.4 7 2.4-7 2.8z" fill="{leaf}" transform="rotate({droop * .5:.1f} {top[0]:.1f} {top[1]:.1f})"/>')
    o.append(f'<g transform="translate({top[0]:.1f},{top[1]:.1f}) rotate({droop:.1f}) translate({3.4 * sc / .78:.2f},{.6 - 15 * sc:.2f}) scale({sc * sx:.3f},{sc:.3f}) translate(-50,-30)">'
             f'<path d="M33 26Q29 16 40 18Q50 12 60 18Q71 16 67 26Q66 42 50 45Q34 42 33 26Z" fill="{col[0]}"/>'
             f'<ellipse cx="50" cy="22" rx="12" ry="5" fill="{col[1]}"/><path d="M41 23Q50 15 59 23Q50 20 41 23Z" fill="{col[2]}"/>'
             f'<path d="M47 21q4-3 7 0q-2 2-5 1" stroke="{col[3]}" stroke-width="1" fill="none" stroke-linecap="round"/>'
             f'<path d="M32 24Q31 44 50 46Q69 44 68 24Q62 35 50 36Q38 35 32 24Z" fill="{col[4]}"/>'
             f'<path d="M39 29Q41 43 50 45Q59 43 61 29Q56 33 50 33Q44 33 39 29Z" fill="{col[5]}"/>'
             f'<path d="M33 25Q30 19 35 17M67 25Q70 19 65 17" stroke="{col[6]}" stroke-width="1.6" fill="none" stroke-linecap="round"/></g>')
    o.append("</g>")
    fall = clamp((th - 2.3) / 0.6)  # pétales tombés à gauche (la roue des paramètres est à droite)
    if fall > 0:
        for x, y, rt in ((12, 126.4, -50), (21, 128, 30), (28, 126.8, 80)):
            o.append(f'<ellipse cx="{x}" cy="{y}" rx="{3 * fall:.2f}" ry="{4.4 * fall:.2f}" transform="rotate({rt} {x} {y})" '
                     f'fill="{col[4]}" stroke="{col[0]}" stroke-width=".5"/>')
    o.append(face(kind, th, blink, 50, 109, 0.62, ink="#F3E6D7"))
    if sl > 0:
        o.append(accessoire_11(sl))
    o.append("</svg>")
    return "".join(o)


def plante_11_head(th, sl=0.0):
    return (A([55, 56, 58, 60], th), A([32, 34, 40, 48], th))


# effet A (sommeil, animé par painter.draw_effet_a) : point de départ (unités du corps), par plante
EFFET_A = {"plante_5": (50.4, 111.4)}
# effet B (sommeil, animé par painter.draw_effet_b) : point de départ (unités du corps), par plante
EFFET_B = {"plante_11": (28.6, 117.2)}

# nom dans config.json -> (dessin, position de la tête)
PLANTES = {"plante_2": (plante_2, plante_2_head), "plante_3": (plante_3, plante_3_head), "plante_4": (plante_4, plante_4_head), "plante_5": (plante_5, plante_5_head), "plante_6": (plante_6, plante_6_head), "plante_7": (plante_7, plante_7_head), "plante_8": (plante_8, plante_8_head), "plante_9": (plante_9, plante_9_head), "plante_10": (plante_10, plante_10_head), "plante_11": (plante_11, plante_11_head)}
