import unittest

from PySide6.QtCore import QByteArray
from PySide6.QtSvg import QSvgRenderer

from tests import _support  # noqa: F401
from soif import painter as art
from soif import plantes


class PlantesTest(unittest.TestCase):
    def test_chaque_plante_donne_un_svg_valide_a_tous_les_etats(self):
        self.assertGreater(len(plantes.PLANTES), 0)
        for name, (draw, head) in plantes.PLANTES.items():
            for th in (0, .5, 1, 1.5, 2, 2.5, 3):
                for sl in (0, .5, 1):
                    for kind in ("happy", "calm", "worried", "tired", "sleep", "drink"):
                        svg = draw(th, sl, kind)
                        self.assertTrue(QSvgRenderer(QByteArray(svg.encode())).isValid(), (name, th, sl, kind))
                        self.assertIn('viewBox="0 0 100 130"', svg)
                    x, y = head(th, sl)
                    self.assertTrue(0 < x < 100 and 0 < y < 130, (name, th, sl, x, y))

    def test_plante_inconnue_retombe_sur_la_classique(self):
        art.set_skin("n_importe_quoi")
        self.assertEqual(art.SKIN, "classique")

    def test_clignement_et_balancement_acceptes(self):
        for name, (draw, _) in plantes.PLANTES.items():
            svg = draw(2, 0, "worried", True, 4.0)
            self.assertTrue(QSvgRenderer(QByteArray(svg.encode())).isValid(), name)


if __name__ == "__main__":
    unittest.main()
