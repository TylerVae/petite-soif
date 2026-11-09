import copy
import json
import unittest

from tests import _support  # noqa: F401
from soif import config as cfg


class ConfigTest(unittest.TestCase):
    def test_valeurs_absurdes_ramenees_a_des_valeurs_sures(self):
        bad = copy.deepcopy(cfg.DEFAULTS)
        bad.update({"echelle": 0, "volume": 7, "absence_minutes": "abc", "insistance": "zzz", "langue": "de", "objectif_cl": -5,
                    "rappels_minutes": {"soif_1": 50, "soif_2": 10, "soif_3": 5, "repetition": 1},
                    "ne_pas_deranger_minutes": ["x"], "tout_debloque": "oui", "plante": ""})
        out = cfg.sanitize(bad)
        self.assertEqual((out["echelle"], out["volume"], out["objectif_cl"]), (0.5, 1.0, 50))
        self.assertEqual(out["absence_minutes"], cfg.DEFAULTS["absence_minutes"])
        self.assertEqual((out["insistance"], out["langue"], out["plante"]), ("normale", "fr", "classique"))
        self.assertEqual(out["rappels_minutes"], cfg.DEFAULTS["rappels_minutes"])
        self.assertEqual(out["ne_pas_deranger_minutes"], [30, 60, 120])
        self.assertIs(out["tout_debloque"], False)

    def test_une_config_valide_ne_change_pas(self):
        good, err = cfg.load()
        self.assertIsNone(err)
        self.assertEqual(good, cfg.sanitize(copy.deepcopy(good)))

    def test_json_invalide_donne_les_defauts_et_une_erreur(self):
        cfg.load()
        cfg.CONFIG_PATH.write_text("{ pas du json", encoding="utf-8")
        try:
            out, err = cfg.load()
            self.assertIsNotNone(err)
            self.assertEqual(out, cfg.DEFAULTS)
        finally:
            cfg.CONFIG_PATH.write_text(json.dumps({}), encoding="utf-8")

    def test_les_donnees_vont_dans_appdata(self):
        for p in (cfg.CONFIG_PATH, cfg.DB_PATH, cfg.LOG_PATH):
            self.assertIn("petite_soif_test_", str(p))


if __name__ == "__main__":
    unittest.main()


class HasKeyTest(unittest.TestCase):
    def test_config_d_une_v1_sans_langue(self):
        old = cfg.CONFIG_PATH.read_text(encoding="utf-8") if cfg.CONFIG_PATH.exists() else None
        try:
            cfg.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            cfg.CONFIG_PATH.write_text(json.dumps({"verre_cl": 25}), encoding="utf-8")
            self.assertFalse(cfg.has_key("langue"))
            self.assertTrue(cfg.has_key("verre_cl"))
            self.assertEqual(cfg.load()[0]["verre_cl"], 25)  # le reste d'une config V1 est conservé
        finally:
            if old is None:
                cfg.CONFIG_PATH.unlink(missing_ok=True)
            else:
                cfg.CONFIG_PATH.write_text(old, encoding="utf-8")
