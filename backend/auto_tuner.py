# backend/auto_tuner.py
import sqlite3
import os


class AutoTuner:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__), "races.db"
        )

    def _get_recent_accuracy(self, season_key: str, limit: int = 100) -> float | None:
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()

        try:
            cur.execute("""
                SELECT correct
                FROM result_feedback
                WHERE season_key = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (season_key, limit))
            rows = cur.fetchall()
        except Exception:
            con.close()
            return None

        con.close()

        if not rows:
            return None

        return sum(r[0] for r in rows) / len(rows)

    def _adaptive_thresh(self, acc: float | None) -> float:
        if acc is None:
            return 0.66

        if acc >= 0.65:
            return 0.60
        elif acc >= 0.55:
            return 0.63
        elif acc >= 0.45:
            return 0.66
        elif acc >= 0.35:
            return 0.69
        else:
            return 0.72

    def get_params(self, season_key: str | None = None):
        acc = self._get_recent_accuracy(season_key) if season_key else None
        thresh = self._adaptive_thresh(acc)

        # 가중치는 아직 고정 (2번 단계에서 자동화)
        model_w = 0.5
        db_w = 0.5

        return {
            "thresh": round(thresh, 3),
            "model_w": model_w,
            "db_w": db_w,
            "recent_acc": None if acc is None else round(acc, 3),
        }
