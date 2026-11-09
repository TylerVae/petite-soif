import unittest

from tests import _support  # noqa: F401
from soif import config as cfgmod
from soif import main as mainmod
from soif import painter as art
from soif import plantes
from soif import settings as st
from soif.sounds import SoundPlayer

SKINS = st.SKINS


class _Flower:
    def __init__(self):
        self.celebrated = 0

    def update(self): pass
    def celebrate(self): self.celebrated += 1
    def set_news(self, v): pass


class _Hotkey:
    registered = True
    def unregister(self): pass


class Fake:
    def __init__(self, xp):
        self.cfg, _ = cfgmod.load()
        self.sounds = SoundPlayer(cfgmod.SOUNDS_DIR, 0)
        self.hotkey, self.flower, self._xp = _Hotkey(), _Flower(), xp

    def xp(self): return self._xp
    def has_news(self): return False
    def mark_plants_seen(self): pass
    def refresh_icons(self): pass
    def schedule_reload(self): pass
    def register_hotkey(self, *a, **k): return True
    def toggle_autostart(self, v): pass
    def set_language(self, lang): pass
    def open_settings(self): pass
    def stats(self): return {}


def window(xp, collection=False):
    c = Fake(xp)
    c.cfg["tout_debloque"] = collection
    c.cfg["plante"] = "classique"
    w = st.SettingsWindow(c)
    w._show_tab([n for _, n in st.TABS].index("Ma plante"))
    return c, w


def setUpModule():
    mainmod.load_fonts()


class SettingsTest(unittest.TestCase):
    def tearDown(self):
        art.set_skin("classique")

    def test_etagere_au_depart_une_plante_puis_un_point_dinterrogation(self):
        c, w = window(0)
        pids = list(SKINS)
        self.assertEqual(w.slots[pids[0]].state, "open")
        self.assertEqual(w.slots[pids[1]].state, "next")
        self.assertTrue(all(w.slots[p].state == "hidden" for p in pids[2:]))
        self.assertIn("200 XP", w.xp_next.text())

    def test_choisir_une_plante_debloquee_et_dessinee(self):
        c, w = window(200 * (len(SKINS) - 1))  # tout est débloqué par l'XP
        pid = next(p for p in SKINS[1:] if p in plantes.PLANTES)
        w.slots[pid].click()
        self.assertEqual((c.cfg["plante"], art.SKIN), (pid, pid))
        self.assertTrue(w.slots[pid].current)
        self.assertEqual(c.flower.celebrated, 1)

    def test_plante_pas_encore_debloquee_non_cliquable(self):
        c, w = window(0)
        pid = SKINS[-1]
        w.slots[pid].click()
        self.assertEqual(c.cfg["plante"], "classique")

    def test_plante_debloquee_mais_pas_dessinee_non_cliquable(self):
        pid = SKINS[-1]
        saved = plantes.PLANTES.pop(pid, None)
        try:
            c, w = window(200 * (len(SKINS) - 1))
            self.assertEqual((w.slots[pid].state, w.slots[pid].ready), ("open", False))
            w.slots[pid].click()
            self.assertEqual(c.cfg["plante"], "classique")
        finally:
            if saved:
                plantes.PLANTES[pid] = saved

    def test_mode_collection_avec_confirmation_et_retour_sans(self):
        c, w = window(50)
        box, no, yes = w._confirm_box()
        box.show()
        _support.app.processEvents()
        for b in (no, yes):  # les boutons ne rognent pas leur texte
            self.assertGreaterEqual(b.width(), b.fontMetrics().horizontalAdvance(b.text()) + 20, b.text())
        box.close()
        w._save("tout_debloque", True)
        w._refresh_xp()
        self.assertTrue(all(s.state == "open" for s in w.slots.values()))
        self.assertFalse(w.xp_box.isVisibleTo(w))

    def test_lien_de_bug_prerempli_et_visible_dans_la_barre_laterale(self):
        url = st.report_bug_url()
        self.assertTrue(url.startswith(cfgmod.REPO_URL + "/issues/new?"))
        for part in ("template=bug.yml", "version=", "windows="):
            self.assertIn(part, url)
        c, w = window(0)
        texts = [b.text() for b in w.findChildren(st.QPushButton)]
        self.assertTrue(any("bug" in t.lower() for t in texts))


if __name__ == "__main__":
    unittest.main()
