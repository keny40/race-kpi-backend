import sqlite3
import json
from datetime import datetime, timedelta

DB_PATH = "races.db"

def _utc_now():
    return datetime.utcnow()

def _iso(dt: datetime):
    return dt.replace(microsecond=0).isoformat()

class SeasonManager:
    WINDOW_N = 20
    LOCK_MIN_BETS = 15
    LOCK_HITRATE_BELOW = 0.35
    LOCK_CONSEC_MISS = 4
    LOCK_COOLDOWN_MIN = 30

    UNLOCK_HITRATE_ABOVE = 0.50
    UNLOCK_MIN_BETS = 10

    @staticmethod
    def _conn():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def ensure_current_season(conn: sqlite3.Connection) -> str:
        row = conn.execute("SELECT season_id FROM seasons WHERE is_current=1 LIMIT 1").fetchone()
        if row:
            return row["season_id"]
        sid = _utc_now().strftime("S%Y%m%d_%H%M%S")
        conn.execute(
            "INSERT INTO seasons (season_id, started_at, locked, lock_reason, lock_until, is_current) VALUES (?,?,?,?,?,1)",
            (sid, _iso(_utc_now()), 0, None, None),
        )
        conn.commit()
        return sid

    @staticmethod
    def get_current(conn: sqlite3.Connection):
        sid = SeasonManager.ensure_current_season(conn)
        return conn.execute("SELECT * FROM seasons WHERE season_id=?", (sid,)).fetchone()

    @staticmethod
    def is_locked(conn: sqlite3.Connection) -> bool:
        s = SeasonManager.get_current(conn)
        if not s or int(s["locked"]) != 1:
            return False
        until = s["lock_until"]
        if not until:
            return True
        try:
            return _utc_now() < datetime.fromisoformat(until)
        except Exception:
            return True

    @staticmethod
    def lock(conn: sqlite3.Connection, reason: str):
        sid = SeasonManager.ensure_current_season(conn)
        lock_until = _iso(_utc_now() + timedelta(minutes=SeasonManager.LOCK_COOLDOWN_MIN))
        conn.execute(
            "UPDATE seasons SET locked=1, lock_reason=?, lock_until=? WHERE season_id=?",
            (reason, lock_until, sid),
        )
        conn.execute(
            "INSERT INTO season_events (season_id, event_type, payload, created_at) VALUES (?,?,?,?)",
            (sid, "LOCK", json.dumps({"reason": reason, "lock_until": lock_until}), _iso(_utc_now())),
        )
        conn.commit()

    @staticmethod
    def unlock(conn: sqlite3.Connection, reason: str = "auto-unlock"):
        sid = SeasonManager.ensure_current_season(conn)
        conn.execute(
            "UPDATE seasons SET locked=0, lock_reason=NULL, lock_until=NULL WHERE season_id=?",
            (sid,),
        )
        conn.execute(
            "INSERT INTO season_events (season_id, event_type, payload, created_at) VALUES (?,?,?,?)",
            (sid, "UNLOCK", json.dumps({"reason": reason}), _iso(_utc_now())),
        )
        conn.commit()

    @staticmethod
    def _recent_outcomes(conn: sqlite3.Connection, n: int):
        rows = conn.execute(
            """
            SELECT p.race_id, p.decision, r.winner
            FROM predictions p
            JOIN results r ON p.race_id = r.race_id
            WHERE p.decision != 'PASS'
            ORDER BY p.id DESC
            LIMIT ?
            """,
            (n,),
        ).fetchall()
        outcomes = []
        for r in rows:
            outcomes.append(1 if r["decision"] == r["winner"] else 0)
        return outcomes

    @staticmethod
    def evaluate_lock_state():
        conn = SeasonManager._conn()
        SeasonManager.ensure_current_season(conn)

        s = SeasonManager.get_current(conn)
        locked = int(s["locked"]) == 1
        lock_until = s["lock_until"]

        outcomes = SeasonManager._recent_outcomes(conn, SeasonManager.WINDOW_N)
        bets = len(outcomes)
        hit = sum(outcomes)
        hitrate = (hit / bets) if bets else 0.0

        consec_miss = 0
        for x in outcomes:
            if x == 0:
                consec_miss += 1
            else:
                break

        now = _utc_now()

        if locked:
            if lock_until:
                try:
                    until_dt = datetime.fromisoformat(lock_until)
                    if now < until_dt:
                        conn.close()
                        return
                except Exception:
                    conn.close()
                    return

            recent = outcomes[: SeasonManager.UNLOCK_MIN_BETS]
            if len(recent) >= SeasonManager.UNLOCK_MIN_BETS:
                hr = sum(recent) / len(recent)
                if hr >= SeasonManager.UNLOCK_HITRATE_ABOVE:
                    SeasonManager.unlock(conn, reason=f"auto-unlock hr={hr:.2f}")
            conn.close()
            return

        if bets >= SeasonManager.LOCK_MIN_BETS:
            if hitrate < SeasonManager.LOCK_HITRATE_BELOW:
                SeasonManager.lock(conn, reason=f"low-hitrate {hitrate:.2f} over {bets}")
            elif consec_miss >= SeasonManager.LOCK_CONSEC_MISS:
                SeasonManager.lock(conn, reason=f"consec-miss {consec_miss}")

        conn.close()

    @staticmethod
    def get_status():
        conn = SeasonManager._conn()
        s = SeasonManager.get_current(conn)

        outcomes = SeasonManager._recent_outcomes(conn, SeasonManager.WINDOW_N)
        bets = len(outcomes)
        hit = sum(outcomes)
        miss = bets - hit
        hitrate = (hit / bets) if bets else 0.0

        locked = int(s["locked"]) == 1
        lock_until = s["lock_until"]
        if locked and lock_until:
            try:
                locked = _utc_now() < datetime.fromisoformat(lock_until)
            except Exception:
                locked = True

        conn.close()
        return {
            "season_id": s["season_id"],
            "started_at": s["started_at"],
            "locked": locked,
            "lock_reason": s["lock_reason"],
            "lock_until": lock_until,
            "recent_window": {"bets": bets, "hit": hit, "miss": miss, "hitrate": round(hitrate, 3)},
        }
