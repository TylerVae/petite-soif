"""Garde-fous de la promesse « rien ne quitte ton ordinateur »."""
import re
import unittest

from tests import _support  # noqa: F401

ROOT = _support.ROOT
FORBIDDEN_IMPORTS = re.compile(r"^\s*(import|from)\s+(socket|http|urllib\.request|urllib3|requests|ftplib|smtplib|xmlrpc|websocket|aiohttp|PySide6\.QtNetwork)\b", re.M)


class PrivacyTest(unittest.TestCase):
    def test_aucun_module_reseau_dans_lappli(self):
        for py in list((ROOT / "soif").glob("*.py")) + [ROOT / "petite_soif.pyw"]:
            self.assertIsNone(FORBIDDEN_IMPORTS.search(py.read_text(encoding="utf-8")), py.name)

    def test_le_build_exclut_le_module_reseau_de_qt(self):
        spec = (ROOT / "petite_soif.spec").read_text(encoding="utf-8")
        self.assertIn("PySide6.QtNetwork", spec)

    def test_aucun_chemin_personnel_dans_les_sources(self):
        pattern = re.compile(r"C:\\Users\\|/Users/[A-Za-z]|@gmail\.|ghp_[A-Za-z0-9]{20}")
        for p in list((ROOT / "soif").glob("*.py")) + list(ROOT.glob("*.md")) + list((ROOT / "tests").glob("*.py")):
            if p.name in ("test_privacy.py", "CLAUDE.md", "HANDOFF.md"):  # CLAUDE.md cite ces motifs ; HANDOFF.md est local, ignoré par git
                continue
            self.assertIsNone(pattern.search(p.read_text(encoding="utf-8")), p.name)

    def test_fichiers_de_donnees_jamais_suivis(self):
        gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for needle in ("config.json", "*.db", "*.log", "HANDOFF.md"):
            self.assertIn(needle, gi)


if __name__ == "__main__":
    unittest.main()


class SpoilerTest(unittest.TestCase):
    def test_les_noms_des_plantes_ne_sont_pas_lisibles_dans_le_depot(self):
        import codecs
        noms = [codecs.decode(n, "rot13") for n in ("bepuvq", "qnuyvn", "zhthrg", "gbhearfby", "fhasybjre", "pnpghf", "ghyvc", "yninaq", "obafn", "senvfvre")]  # eux-mêmes en ROT13, sinon ce test les révélerait
        for p in list((ROOT / "soif").glob("*.py")) + [ROOT / "README.md", ROOT / "CHANGELOG.md"]:
            txt = p.read_text(encoding="utf-8").lower()
            for n in noms:
                self.assertNotIn(n, txt, f"{n} dans {p.name}")
