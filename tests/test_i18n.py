import ast
import string
import unittest

from tests import _support  # noqa: F401
from soif import i18n

SRC = _support.ROOT / "soif"


def _fields(s):
    return {f for _, f, _, _ in string.Formatter().parse(s) if f}


class I18nTest(unittest.TestCase):
    def test_chaque_texte_passe_par_t_a_une_traduction_anglaise(self):
        missing = []
        for py in SRC.glob("*.py"):
            if py.name == "i18n.py":
                continue
            for node in ast.walk(ast.parse(py.read_text(encoding="utf-8"))):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "t"
                        and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                    key = node.args[0].value
                    if key not in i18n.EN:
                        missing.append(f"{py.name}:{node.lineno} {key[:60]!r}")
        self.assertEqual(missing, [], "textes sans traduction anglaise")

    def test_les_champs_des_traductions_correspondent(self):
        for fr, en in i18n.EN.items():
            plural = {"s", "es"}  # suffixes de pluriel : chaque langue utilise le sien
            self.assertEqual(_fields(fr) - plural, _fields(en) - plural, fr[:60])

    def test_t_formate_dans_les_deux_langues(self):
        old = i18n.lang
        try:
            i18n.lang = "en"
            self.assertNotEqual(i18n.t("Quitter"), "Quitter")
            i18n.lang = "fr"
            self.assertEqual(i18n.t("Quitter"), "Quitter")
        finally:
            i18n.lang = old


if __name__ == "__main__":
    unittest.main()


class HourTest(unittest.TestCase):
    def tearDown(self):
        i18n.lang = "fr"

    def test_heure_24h_en_francais_et_am_pm_en_anglais(self):
        from soif.popup import fmt_hour
        i18n.lang = "fr"
        self.assertEqual((fmt_hour(0), fmt_hour(23)), ("0 h", "23 h"))
        i18n.lang = "en"
        self.assertEqual([fmt_hour(h) for h in (0, 6, 12, 13, 23)], ["12 AM", "6 AM", "12 PM", "1 PM", "11 PM"])
