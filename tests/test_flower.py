import unittest

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QMouseEvent

from tests import _support  # noqa: F401
from soif import main as mainmod
from soif import painter as art
from soif import plantes
from soif.flower import MARGIN, FlowerWidget

M = int(MARGIN)


def setUpModule():
    mainmod.load_fonts()


def widget(skin="classique", scale=1.0):
    art.set_skin(skin)
    f = FlowerWidget(scale)
    f.title_font = mainmod.settings_mod.FAMILY
    return f


class FlowerTest(unittest.TestCase):
    def tearDown(self):
        art.set_skin("classique")

    def test_couloir_pot_vers_roue_sans_trou_pour_toutes_les_plantes(self):
        # Windows laisse passer la souris à travers les pixels d'alpha 0 : sans voile, le survol se perd vers les boutons
        for skin in ["classique"] + list(plantes.PLANTES):
            f = widget(skin)
            f._hover = True
            img = f.grab().toImage()
            for y in (110, 118, 126):
                for x in list(range(60, 70)) + list(range(30, 40)):
                    self.assertGreater(img.pixelColor(M + x, M + y).alpha(), 0, (skin, x, y))

    def test_le_voile_est_invisible_sur_fond_noir(self):
        f = widget("classique")
        f._hover = True
        c = f.grab().toImage().pixelColor(M + 95, M + 104)
        self.assertEqual((c.red(), c.green(), c.blue()), (0, 0, 0))
        self.assertLessEqual(c.alpha(), 2)

    def test_boutons_parametres_et_sommeil_cliquables(self):
        f = widget("classique")
        got = []
        f.settings_requested.connect(lambda: got.append("settings"))
        f.dnd_requested.connect(lambda: got.append("dnd"))
        f._hover = True
        for r in (f._dnd_rect_local(), f._gear_rect_local()):
            pt = r.center()
            f.mousePressEvent(QMouseEvent(QEvent.MouseButtonPress, pt, f.mapToGlobal(pt), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
        self.assertEqual(got, ["dnd", "settings"])

    def test_le_plus_xp_ne_touche_jamais_le_bord_haut(self):
        for scale in (0.7, 1.0, 1.5):
            for big in (False, True):
                f = widget("classique", scale)
                f.show_xp("Nouvelle plante !" if big else "+5 XP", big=big)
                life = f._particles[-1].life
                t = 0.0
                while t < life + 0.1:
                    f._update_particles(0.05)
                    t += 0.05
                    img = f.grab().toImage()
                    top = max(img.pixelColor(x, y).alpha() for x in range(img.width()) for y in range(3))
                    self.assertLessEqual(top, 8, (scale, big, t))

    def test_endormie_la_fleur_anime_a_4_images_par_seconde(self):
        f = widget("classique")
        f.set_sleeping(True)
        self.assertEqual(f._anim.interval(), 33)  # fondu d'endormissement à la cadence normale
        for _ in range(60):
            f._last -= 0.05
            f._tick()
        self.assertAlmostEqual(f.sl, 1.0, delta=0.02)
        self.assertTrue(f._anim.isActive())
        self.assertEqual(f._anim.interval(), 250)
        t0 = f._t
        f._last -= 0.25
        f._tick()
        self.assertAlmostEqual(f._t - t0, 0.25, delta=0.01)  # le temps d'animation reste réel
        f.set_sleeping(False)
        self.assertEqual(f._anim.interval(), 33)
        for _ in range(80):
            f._last -= 0.05
            f._tick()
        self.assertFalse(f._anim.isActive(), "réveillée et au repos : plus d'animation")

    def test_toutes_les_plantes_se_dessinent_dans_le_widget(self):
        for skin in ["classique"] + list(plantes.PLANTES):
            f = widget(skin)
            for th in (0, 1.5, 3):
                for sleeping in (False, True):
                    f.thirst = f.thirst_target = th
                    f.sleeping, f.sl = sleeping, 1.0 if sleeping else 0.0
                    f._walking, f._walk_phase = th == 1.5, 1.0
                    self.assertFalse(f.grab().isNull(), (skin, th, sleeping))


if __name__ == "__main__":
    unittest.main()
