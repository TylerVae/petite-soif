import sqlite3
import tempfile
import unittest
from pathlib import Path

from tests import _support  # noqa: F401
from soif.storage import SCHEMA_VERSION, Storage


class StorageTest(unittest.TestCase):
    def setUp(self):
        self.path = Path(tempfile.mkdtemp()) / "t.db"
        self.s = Storage(self.path)

    def test_xp_premiere_gorgee_5_puis_1_et_3_par_verre(self):
        self.s.log("gorgee")
        self.assertEqual(self.s.xp(), 5)
        self.s.log("gorgee")
        self.assertEqual(self.s.xp(), 6)
        self.s.log("verre", cl=50)
        self.assertEqual(self.s.xp(), 9)

    def test_version_du_schema(self):
        self.assertEqual(sqlite3.connect(str(self.path)).execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
        Storage(self.path)  # réouverture d'une base déjà versionnée

    def test_base_trop_recente_refusee(self):
        con = sqlite3.connect(str(self.path))
        con.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
        con.commit()
        con.close()
        with self.assertRaises(RuntimeError):
            Storage(self.path)

    def test_etat_cle_valeur(self):
        self.s.set_state("k", "v")
        self.assertEqual(self.s.get_state("k", "?"), "v")
        self.assertEqual(self.s.get_state("absent", "x"), "x")


if __name__ == "__main__":
    unittest.main()


V1_SCHEMA = """
CREATE TABLE events(
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, jour TEXT NOT NULL,
    type TEXT NOT NULL, cl INTEGER NOT NULL DEFAULT 0, detail TEXT);
CREATE INDEX idx_events_jour ON events(jour);
CREATE INDEX idx_events_type_ts ON events(type, ts);
CREATE TABLE state(key TEXT PRIMARY KEY, value TEXT);
"""  # copie exacte du schéma de la v1.0.0 (sans numéro de version)


class MigrationV1Test(unittest.TestCase):
    def test_une_base_v1_s_ouvre_sans_perte(self):
        path = Path(tempfile.mkdtemp()) / "v1.db"
        db = sqlite3.connect(str(path))
        db.executescript(V1_SCHEMA)
        db.execute("INSERT INTO events(ts, jour, type, cl) VALUES (1.0, '2026-01-01', 'gorgee', 0)")
        db.execute("INSERT INTO events(ts, jour, type, cl) VALUES (2.0, '2026-01-01', 'verre', 50)")
        db.execute("INSERT INTO state VALUES ('home', '10,20')")
        db.commit()
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 0)
        db.close()
        s = Storage(path)
        self.assertEqual((s.total_cl("2026-01-01"), s.xp(), s.get_state("home")), (50, 5 + 3, "10,20"))
        self.assertEqual(s.db.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
        s.log("gorgee")  # et on peut continuer à écrire dedans
