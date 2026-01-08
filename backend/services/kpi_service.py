import sqlite3
from typing import Dict, Any, List, Optional, Tuple
import math

DB_PATH = "races.db"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _safe_float(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def get_kpi_summary() -> Dict[str, Any]:
    """
    기존 summary + confidence bin 히트율
    (멀티전략 구조에서는 전체 합산)
    """
    conn = _conn()
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT race_id, strategy, predicted_horse_no AS decision, confidence, passed,
               (SELECT winner FROM actual_results a WHERE a.race_id = p.race_id) AS winner
        FROM predictions p
        WHERE passed = 0
          AND predicted_horse_no IS NOT NULL
        """
    ).fetchall()

    total = len(rows)
    hit = 0
    bins = {"0.0-0.3": {"n": 0, "hit": 0}, "0.3-0.6": {"n": 0, "hit": 0}, "0.6-1.0": {"n": 0, "hit": 0}}

    for r in rows:
        w = r["winner"]
        if w is not None and int(r["decision"]) == int(w):
            hit += 1

        c = _safe_float(r["confidence"])
        if c < 0.3:
            key = "0.0-0.3"
        elif c < 0.6:
            key = "0.3-0.6"
        else:
            key = "0.6-1.0"

        bins[key]["n"] += 1
        if w is not None and int(r["decision"]) == int(w):
            bins[key]["hit"] += 1

    conn.close()

    def acc(h, n):
        return (h / n) if n else 0.0

    return {
        "total": total,
        "hit": hit,
        "accuracy": acc(hit, total),
        "bins": {
            k: {"n": v["n"], "hit": v["hit"], "accuracy": acc(v["hit"], v["n"])}
            for k, v in bins.items()
        },
    }


def get_kpi_by_strategy() -> List[Dict[str, Any]]:
    """
    전략별 성능판: total/hit/accuracy/avg_confidence
    """
    conn = _conn()
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT
          p.strategy AS strategy,
          COUNT(*) AS total,
          SUM(CASE WHEN a.winner IS NOT NULL AND p.predicted_horse_no = a.winner THEN 1 ELSE 0 END) AS hit,
          AVG(p.confidence) AS avg_confidence
        FROM predictions p
        LEFT JOIN actual_results a
          ON a.race_id = p.race_id
        WHERE p.passed = 0
          AND p.predicted_horse_no IS NOT NULL
        GROUP BY p.strategy
        ORDER BY total DESC
        """
    ).fetchall()

    conn.close()

    out = []
    for r in rows:
        total = int(r["total"] or 0)
        hit = int(r["hit"] or 0)
        out.append(
            {
                "strategy": r["strategy"],
                "total": total,
                "hit": hit,
                "accuracy": (hit / total) if total else 0.0,
                "avg_confidence": _safe_float(r["avg_confidence"]),
            }
        )
    return out


def get_kpi_by_confidence(threshold: float, strategy: Optional[str] = None) -> Dict[str, Any]:
    """
    컷 이상만 대상으로 KPI
    """
    conn = _conn()
    cur = conn.cursor()

    params: List[Any] = [float(threshold)]
    where_strategy = ""
    if strategy:
        where_strategy = " AND p.strategy = ? "
        params.append(strategy)

    rows = cur.execute(
        f"""
        SELECT p.predicted_horse_no AS decision, p.confidence,
               a.winner
        FROM predictions p
        LEFT JOIN actual_results a ON a.race_id = p.race_id
        WHERE p.passed = 0
          AND p.predicted_horse_no IS NOT NULL
          AND p.confidence >= ?
          {where_strategy}
        """,
        params,
    ).fetchall()

    total = len(rows)
    hit = 0
    for r in rows:
        w = r["winner"]
        if w is not None and int(r["decision"]) == int(w):
            hit += 1

    conn.close()
    return {"threshold": threshold, "strategy": strategy or "ALL", "total": total, "hit": hit, "accuracy": (hit / total) if total else 0.0}


def get_roi_by_strategy(strategy: Optional[str] = None) -> Dict[str, Any]:
    """
    ROI KPI: sum(profit)/sum(stake)
    profit가 이미 채워져 있으면 그것을 사용, 없으면 winner로 계산(odds/payout 필요)
    """
    conn = _conn()
    cur = conn.cursor()

    params: List[Any] = []
    where_strategy = ""
    if strategy:
        where_strategy = " AND p.strategy = ? "
        params.append(strategy)

    rows = cur.execute(
        f"""
        SELECT
          p.race_id, p.strategy, p.predicted_horse_no, p.stake, p.odds, p.payout, p.profit,
          a.winner
        FROM predictions p
        LEFT JOIN actual_results a ON a.race_id = p.race_id
        WHERE p.passed = 0
          AND p.predicted_horse_no IS NOT NULL
          AND p.stake > 0
          {where_strategy}
        """,
        params,
    ).fetchall()

    sum_stake = 0.0
    sum_profit = 0.0
    computed = 0

    for r in rows:
        stake = _safe_float(r["stake"])
        if stake <= 0:
            continue

        profit = r["profit"]
        if profit is None:
            w = r["winner"]
            if w is None:
                continue

            hit = int(r["predicted_horse_no"]) == int(w)
            payout = r["payout"]
            odds = r["odds"]

            if hit:
                if payout is not None:
                    profit_val = _safe_float(payout) - stake
                elif odds is not None:
                    profit_val = stake * _safe_float(odds) - stake
                else:
                    continue
            else:
                profit_val = -stake
        else:
            profit_val = _safe_float(profit)

        sum_stake += stake
        sum_profit += profit_val
        computed += 1

    conn.close()

    roi = (sum_profit / sum_stake) if sum_stake else 0.0
    return {
        "strategy": strategy or "ALL",
        "bets": computed,
        "sum_stake": sum_stake,
        "sum_profit": sum_profit,
        "roi": roi,
    }

def get_roi_by_strategy(strategy=None):
    import sqlite3

    conn = sqlite3.connect("races.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    params = []
    where_strategy = ""
    if strategy:
        where_strategy = "AND p.strategy = ?"
        params.append(strategy)

    rows = cur.execute(
        f"""
        SELECT
          p.strategy,
          p.stake,
          p.profit,
          p.odds,
          p.payout,
          p.predicted_horse_no,
          a.winner
        FROM predictions p
        LEFT JOIN actual_results a
          ON a.race_id = p.race_id
        WHERE p.passed = 0
          AND p.predicted_horse_no IS NOT NULL
          AND p.stake > 0
          {where_strategy}
        """,
        params,
    ).fetchall()

    sum_stake = 0.0
    sum_profit = 0.0
    bets = 0

    for r in rows:
        stake = float(r["stake"] or 0)
        if stake <= 0:
            continue

        profit = r["profit"]
        if profit is None:
            # winner 없으면 아직 미정 → 손익 계산 안 함
            if r["winner"] is None:
                continue

            hit = int(r["predicted_horse_no"]) == int(r["winner"])
            if hit:
                if r["payout"] is not None:
                    profit_val = float(r["payout"]) - stake
                elif r["odds"] is not None:
                    profit_val = stake * float(r["odds"]) - stake
                else:
                    continue
            else:
                profit_val = -stake
        else:
            profit_val = float(profit)

        sum_stake += stake
        sum_profit += profit_val
        bets += 1

    conn.close()

    roi = (sum_profit / sum_stake) if sum_stake else 0.0
    return {
        "strategy": strategy or "ALL",
        "bets": bets,
        "sum_stake": sum_stake,
        "sum_profit": sum_profit,
        "roi": roi,
    }
