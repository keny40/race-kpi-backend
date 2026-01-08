from fastapi import APIRouter
from backend.services.db import get_conn

router = APIRouter(prefix="/api/kpi", tags=["kpi"])


@router.get("/match")
def kpi_match():
    """
    실제 결과(actual_results) 없으므로
    RUN만 대상으로 '집계 가능한 항목'만 제공
    """
    conn = get_conn()
    cur = conn.cursor()

    # RUN만
    total_run = cur.execute(
        "SELECT COUNT(*) AS c FROM predictions WHERE passed=0"
    ).fetchone()["c"] or 0

    # 말 번호 분포(상위 10개)
    dist = cur.execute(
        """
        SELECT predicted_horse_no AS horse_no, COUNT(*) AS c
          FROM predictions
         WHERE passed=0
           AND predicted_horse_no IS NOT NULL
         GROUP BY predicted_horse_no
         ORDER BY c DESC
         LIMIT 10
        """
    ).fetchall()

    conn.close()

    return {
        "mode": "NO_ACTUAL_RESULTS",
        "filters": {"passed": 0},
        "run_total": int(total_run),
        "top_predicted_horses": [
            {"horse_no": int(r["horse_no"]), "count": int(r["c"])} for r in dist
        ],
        "note": "hit/miss 계산은 actual_results 연결 후 활성화",
    }
