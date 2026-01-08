from datetime import datetime
from backend.services.db import get_conn


def get_weight(horse_no: int) -> float:
    """
    Beta prior 기반(간단/안정): weight = (wins+1)/(wins+losses+2)
    0~1 범위, 데이터 적으면 0.5 근처로 수렴
    """
    conn = get_conn()
    row = conn.execute(
        "SELECT wins, losses FROM horse_reliability WHERE horse_no=?",
        (int(horse_no),),
    ).fetchone()

    if not row:
        return 0.5

    wins = int(row["wins"])
    losses = int(row["losses"])
    return (wins + 1) / (wins + losses + 2)


def update_from_result(pick_horse_no: int, winner_horse_no: int):
    """
    BET 결과 확정 시 horse_reliability 누적 업데이트
    """
    pick = int(pick_horse_no)
    winner = int(winner_horse_no)

    conn = get_conn()

    # ensure row
    conn.execute(
        """
        INSERT INTO horse_reliability (horse_no, wins, losses, updated_at)
        VALUES (?, 0, 0, ?)
        ON CONFLICT(horse_no) DO NOTHING
        """,
        (pick, datetime.utcnow().isoformat()),
    )

    if pick == winner:
        conn.execute(
            """
            UPDATE horse_reliability
            SET wins = wins + 1,
                updated_at = ?
            WHERE horse_no = ?
            """,
            (datetime.utcnow().isoformat(), pick),
        )
    else:
        conn.execute(
            """
            UPDATE horse_reliability
            SET losses = losses + 1,
                updated_at = ?
            WHERE horse_no = ?
            """,
            (datetime.utcnow().isoformat(), pick),
        )

    conn.commit()


def apply_weights_to_scored_horses(scored: list[dict]) -> list[dict]:
    """
    scored: [{"horse_no": 3, "score": 0.82}, ...]
    score_weighted = score * (0.6 + 0.8*weight)  # 0.6~1.4 배
    """
    out = []
    for item in scored:
        hn = int(item["horse_no"])
        score = float(item["score"])
        w = float(get_weight(hn))
        mult = 0.6 + 0.8 * w
        out.append(
            {
                "horse_no": hn,
                "score": score,
                "weight": round(w, 3),
                "score_weighted": round(score * mult, 6),
            }
        )
    out.sort(key=lambda x: x["score_weighted"], reverse=True)
    return out
