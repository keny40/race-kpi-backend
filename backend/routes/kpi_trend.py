from fastapi import APIRouter, Query
from backend.db.conn import get_conn

router = APIRouter(prefix="/api/kpi", tags=["kpi"])


@router.get("/trend")
@router.post("/trend")
def get_kpi_trend(period: str = Query("day", pattern="^(day|week|month)$")):
    """
    period:
      - day:   YYYY-MM-DD
      - week:  YYYY-WW
      - month: YYYY-MM
    """

    if period == "day":
        bucket_expr = "substr(created_at, 1, 10)"
        order_expr = "substr(created_at, 1, 10)"
    elif period == "week":
        bucket_expr = "strftime('%Y-%W', created_at)"
        order_expr = "strftime('%Y-%W', created_at)"
    else:
        bucket_expr = "strftime('%Y-%m', created_at)"
        order_expr = "strftime('%Y-%m', created_at)"

    con = get_conn()
    cur = con.cursor()

    sql = f"""
        SELECT
            {bucket_expr} AS bucket,
            COUNT(*) AS total,
            SUM(CASE WHEN result = 'HIT' THEN 1 ELSE 0 END) AS hit,
            SUM(CASE WHEN result = 'MISS' THEN 1 ELSE 0 END) AS miss,
            SUM(CASE WHEN result = 'PASS' THEN 1 ELSE 0 END) AS pass
        FROM v_race_match
        GROUP BY bucket
        ORDER BY {order_expr} ASC
    """

    cur.execute(sql)
    rows = cur.fetchall()
    con.close()

    series = []
    for bucket, total, hit, miss, passed in rows:
        total = total or 0
        hit = hit or 0
        miss = miss or 0
        passed = passed or 0

        accuracy = round(hit / (hit + miss), 4) if (hit + miss) > 0 else 0.0

        series.append({
            "bucket": bucket,
            "total": total,
            "hit": hit,
            "miss": miss,
            "pass": passed,
            "accuracy": accuracy
        })

    return {
        "period": period,
        "series": series
    }
