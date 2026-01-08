from fastapi import APIRouter, Query
from backend.services.db import get_conn

router = APIRouter(prefix="/api/admin/pre-race", tags=["admin-pre-race-compare"])


@router.get("/compare")
def compare_pre_post(limit: int = Query(200, ge=1, le=2000)):
    """
    같은 race_id에 대해
    pre-race pick vs post-race pick vs 실제 winner 비교
    """
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT
            h.race_id,
            h.confidence AS pre_confidence,
            json_extract(h.summary_json, '$.top_horses[0].horse_no') AS pre_pick,
            p.predicted_horse_no AS post_pick,
            p.confidence AS post_confidence,
            a.winner
        FROM pre_race_run_history h
        JOIN predictions p ON h.race_id = p.race_id
        JOIN actual_results a ON h.race_id = a.race_id
        ORDER BY h.run_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    total = 0
    pre_hit = 0
    post_hit = 0
    agree = 0
    both_miss = 0

    items = []

    for r in rows:
        total += 1
        winner = r["winner"]
        pre_pick = r["pre_pick"]
        post_pick = r["post_pick"]

        pre_ok = pre_pick is not None and winner is not None and str(pre_pick) == str(winner)
        post_ok = post_pick is not None and winner is not None and str(post_pick) == str(winner)
        if pre_ok:
            pre_hit += 1
        if post_ok:
            post_hit += 1
        if pre_pick is not None and post_pick is not None and str(pre_pick) == str(post_pick):
            agree += 1
        if (not pre_ok) and (not post_ok):
            both_miss += 1

        items.append(
            {
                "race_id": r["race_id"],
                "winner": winner,
                "pre_pick": pre_pick,
                "pre_confidence": r["pre_confidence"],
                "post_pick": post_pick,
                "post_confidence": r["post_confidence"],
                "pre_hit": pre_ok,
                "post_hit": post_ok,
                "agree": (pre_pick is not None and post_pick is not None and str(pre_pick) == str(post_pick)),
            }
        )

    return {
        "total": total,
        "pre_hit": pre_hit,
        "pre_hit_rate": round(pre_hit / total, 3) if total else 0.0,
        "post_hit": post_hit,
        "post_hit_rate": round(post_hit / total, 3) if total else 0.0,
        "agree": agree,
        "agree_rate": round(agree / total, 3) if total else 0.0,
        "both_miss": both_miss,
        "items": items[:50],  # UI용 샘플 50건만
    }
