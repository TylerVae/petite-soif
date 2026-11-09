"""Stockage SQLite : chaque événement est horodaté, une 'journée' commence à heure_reset."""
import csv
import sqlite3
import time
from datetime import date, datetime, timedelta


SCHEMA_VERSION = 1  # à incrémenter à chaque changement de tables, avec sa migration dans Storage._migrate


class Storage:
    def __init__(self, path, reset_hour=6):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.reset_hour = int(reset_hour)
        self.db = sqlite3.connect(str(path))
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                jour TEXT NOT NULL,
                type TEXT NOT NULL,
                cl INTEGER NOT NULL DEFAULT 0,
                detail TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_events_jour ON events(jour);
            CREATE INDEX IF NOT EXISTS idx_events_type_ts ON events(type, ts);
            CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY, value TEXT);
            """
        )
        self._migrate()
        self.db.commit()

    def _migrate(self):
        """Une base sans numéro (user_version 0) est une base v1. Futures migrations : `if v < 2: ...` puis user_version = 2."""
        v = self.db.execute("PRAGMA user_version").fetchone()[0]
        if v > SCHEMA_VERSION:
            raise RuntimeError(f"base de données plus récente que l'appli (v{v})")
        self.db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    # --- journées -------------------------------------------------------
    def day_key(self, ts=None):
        ts = time.time() if ts is None else ts
        return (datetime.fromtimestamp(ts) - timedelta(hours=self.reset_hour)).date().isoformat()

    def last_boundary(self, ts=None):
        now = datetime.fromtimestamp(time.time() if ts is None else ts)
        b = now.replace(hour=self.reset_hour, minute=0, second=0, microsecond=0)
        if now < b:
            b -= timedelta(days=1)
        return b.timestamp()

    def next_boundary(self, ts=None):
        b = datetime.fromtimestamp(self.last_boundary(ts)) + timedelta(days=1)
        return b.replace(hour=self.reset_hour, minute=0, second=0, microsecond=0).timestamp()

    # --- événements -----------------------------------------------------
    def log(self, type_, cl=0, detail=None, ts=None):
        ts = time.time() if ts is None else ts
        self.db.execute(
            "INSERT INTO events(ts, jour, type, cl, detail) VALUES (?,?,?,?,?)",
            (ts, self.day_key(ts), type_, int(cl), detail),
        )
        self.db.commit()

    def total_cl(self, jour=None):
        jour = jour or self.day_key()
        row = self.db.execute(
            "SELECT COALESCE(SUM(cl),0) FROM events WHERE jour=? AND type='verre'", (jour,)
        ).fetchone()
        return int(row[0])

    def count(self, type_, jour=None):
        jour = jour or self.day_key()
        row = self.db.execute("SELECT COUNT(*) FROM events WHERE jour=? AND type=?", (jour, type_)).fetchone()
        return int(row[0])

    def last_event_ts(self, types):
        marks = ",".join("?" * len(types))
        row = self.db.execute(f"SELECT MAX(ts) FROM events WHERE type IN ({marks})", tuple(types)).fetchone()
        return row[0]

    def undo_last_glass(self):
        row = self.db.execute(
            "SELECT id FROM events WHERE jour=? AND type='verre' ORDER BY ts DESC LIMIT 1", (self.day_key(),)
        ).fetchone()
        if not row:
            return False
        self.db.execute("DELETE FROM events WHERE id=?", (row[0],))
        self.db.commit()
        return True

    def totals_by_day(self, n=7):
        today = date.fromisoformat(self.day_key())
        days = [(today - timedelta(days=i)) for i in range(n - 1, -1, -1)]
        rows = dict(
            self.db.execute(
                "SELECT jour, SUM(cl) FROM events WHERE type='verre' AND jour>=? GROUP BY jour",
                (days[0].isoformat(),),
            ).fetchall()
        )
        return [(d, int(rows.get(d.isoformat(), 0) or 0)) for d in days]

    def average_cl(self, n=7):
        """Moyenne des n journées précédentes (hors aujourd'hui) où l'appli a servi."""
        today = date.fromisoformat(self.day_key())
        start = (today - timedelta(days=n)).isoformat()
        rows = self.db.execute(
            """SELECT jour, SUM(CASE WHEN type='verre' THEN cl ELSE 0 END)
               FROM events WHERE jour>=? AND jour<? GROUP BY jour""",
            (start, today.isoformat()),
        ).fetchall()
        if not rows:
            return None
        return sum(r[1] for r in rows) / len(rows)

    def xp(self):
        """XP recalculée depuis l'historique : 1re gorgée du jour 5, puis 1 par gorgée, 3 par verre."""
        rows = self.db.execute(
            "SELECT SUM(type='gorgee'), SUM(type='verre') FROM events GROUP BY jour"
        ).fetchall()
        return sum((4 if g else 0) + g + 3 * v for g, v in ((g or 0, v or 0) for g, v in rows))

    # --- état persistant ------------------------------------------------
    def get_state(self, key, default=None):
        row = self.db.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def set_state(self, key, value):
        self.db.execute("INSERT OR REPLACE INTO state(key, value) VALUES (?,?)", (key, str(value)))
        self.db.commit()

    # --- export ---------------------------------------------------------
    def export_csv(self, path):
        rows = self.db.execute("SELECT id, ts, jour, type, cl, detail FROM events ORDER BY ts").fetchall()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["id", "date_heure", "journee", "type", "cl", "detail"])
            for r in rows:
                w.writerow([r[0], datetime.fromtimestamp(r[1]).isoformat(sep=" ", timespec="seconds"), r[2], r[3], r[4], r[5] or ""])
        return len(rows)
