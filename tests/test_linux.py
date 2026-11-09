"""Couche Linux (expérimentale) : testable sous Windows aussi, car elle ne dépend d'aucun appel système."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import _support  # noqa: F401

from soif import sounds, x11api


class LinuxTest(unittest.TestCase):
    def test_fichier_autostart_cree_puis_supprime(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": d}):
            x11api.set_autostart(True, Path("/opt/petite soif/petite_soif.pyw"))
            f = Path(d) / "autostart" / "petite-soif.desktop"
            txt = f.read_text(encoding="utf-8")
            line = next(l for l in txt.splitlines() if l.startswith("Exec="))
            self.assertTrue(line.endswith('petite_soif.pyw"'), line)  # chemin entre doubles guillemets (espace)
            self.assertNotIn("'", line)  # les apostrophes ne sont pas des guillemets valides dans Exec=
            x11api.set_autostart(False, None)
            self.assertFalse(f.exists())
            x11api.set_autostart(False, None)  # déjà absent : sans erreur

    def test_lecteur_de_son_premier_trouve(self):
        def which(prog):
            return "/usr/bin/" + prog if prog in ("pw-play", "aplay") else None
        with mock.patch("soif.sounds.shutil.which", which):
            self.assertEqual(sounds.linux_player_command("a.wav"), ["/usr/bin/pw-play", "a.wav"])
        with mock.patch("soif.sounds.shutil.which", lambda p: None):
            self.assertIsNone(sounds.linux_player_command("a.wav"))

    def test_sans_libxss_le_nombre_de_rappels_est_plafonne(self):
        from soif import main
        ctrl = mock.Mock(repeats=0)
        with mock.patch.object(main.osapi, "HAS_IDLE", False):
            self.assertTrue(main.Controller._may_repeat(ctrl))
            ctrl.repeats = main.MAX_REPEATS_NO_IDLE
            self.assertFalse(main.Controller._may_repeat(ctrl))
        with mock.patch.object(main.osapi, "HAS_IDLE", True):
            self.assertTrue(main.Controller._may_repeat(ctrl))


if __name__ == "__main__":
    unittest.main()
