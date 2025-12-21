# backend/auto_tuner.py

class AutoTuner:
    def __init__(self, db_path=None):
        # import 시점에는 아무 것도 하지 않음
        self.db_path = db_path or "backend/races.db"

    def get_params(self, season_key=None):
        # DB 접근은 호출 시점에만
        try:
            import sqlite3

            con = sqlite3.connect(self.db_path)
            cur = con.cursor()

            cur.execute("""
                SELECT decision, confidence
                FROM predictions
                ORDER BY created_at DESC
                LIMIT 200
            """)
            rows = cur.fetchall()
            con.close()

            if not rows:
                raise ValueError("no rows")

            avg_conf = sum(r[1] for r in rows) / len(rows)

            pass_threshold = max(0.3, min(0.7, 1 - avg_conf))
            db_weight = min(1.0, max(0.5, avg_conf))

            return {
                "thresh": round(pass_threshold, 2),
                "model_w": round(1.0 - db_weight, 2),
                "db_w": round(db_weight, 2),
            }

        except Exception:
            # 🔥 어떤 에러든 기본값으로 안전하게
            return {
                "thresh": 0.66,
                "model_w": 0.5,
                "db_w": 0.5,
            }
