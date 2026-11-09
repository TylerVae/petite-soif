import time
import types
import unittest

from tests import _support  # noqa: F401
from soif import config as cfgmod
from soif import main as mainmod
from soif.flower import FlowerWidget

C = mainmod.Controller


def fake(dnd_in_s, hours_without_drinking=3):
    c = types.SimpleNamespace()
    c.cfg, _ = cfgmod.load()
    c.flower = FlowerWidget(1.0)
    c.played = []
    c.sounds = types.SimpleNamespace(play=lambda n: c.played.append(n))
    c.storage = types.SimpleNamespace(log=lambda *a, **k: None, next_boundary=lambda: time.time() + 99999, last_boundary=lambda: 0)
    now = time.time()
    c.ref = now - hours_without_drinking * 3600
    c.fired_level, c.last_repeat, c.next_boundary = 0, 0, now + 99999
    c.dnd_until = now + dnd_in_s
    c._keep_on_top = lambda: None
    c._idle = lambda: 0
    c._update_tray = lambda *a: None
    for n in ("tick", "_fire", "_level", "_insist"):
        setattr(c, n, types.MethodType(getattr(C, n), c))
    return c


class ControllerTest(unittest.TestCase):
    def test_ne_pas_deranger_ne_fait_aucun_bruit(self):
        c = fake(+600)
        for _ in range(5):
            c.tick()
        self.assertEqual(c.played, [])
        self.assertTrue(c.flower.sleeping)

    def test_le_rappel_part_a_la_fin_du_mode(self):
        c = fake(-1)
        c.tick()
        self.assertEqual(c.played, ["soif_3"])
        self.assertFalse(c.flower.sleeping)

    def test_aucun_rappel_tant_quon_a_bu_recemment(self):
        c = fake(-1, hours_without_drinking=0)
        c.tick()
        self.assertEqual(c.played, [])


if __name__ == "__main__":
    unittest.main()
