import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, List

DB_PATH = "backend/races.db"


def _weight_from_retry(retry_count: int) -> float:
    if retry_count <= 0:
        return 1.0
    if retry_count <= 2:
        return 0.7
    if retry_count <= 4:
        return 0.4
    return 0.0


def _get_strategy_state(con) -> Dict[str, Dict[str, float]]:
    """
    strategy_state 테이블이 없을 수도 있으므로
    실패 시 기본값으로 처리
    """
    state = {}
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT strategy, enabled, weight_multiplier FROM strategy_state"
        )
        for strategy, enabled, mul in cur.fetchall():
            state[strategy] = {
                "enabled": int(enabled),
                "mul": float(mul),
            }
    except Exception:
        pass
    return state


def build_kpi_matrix(
    mode: str = "weight",
    days: int = 30,
    include_disabled: bool = False,
    season: str | None = None,
) -> Dict[str, Any]:
    """
    KPI Matrix
    - strategy × model
    - predictions + ingest_meta 기준
    """

    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        state = _get_strategy_state(con)

        dt_cut = datetime.now() - timedelta(days=int(days))
        cut_iso = dt_cut.isoformat()

        query = """
            SELECT
                p.strategy,
                p.model,
                p.outcome,
                COALESCE(m.confirmed_retry_count, 0) AS retry_count,
                m.confirmed_at,
                COALESCE(m.season, '') AS season
            FROM predictions p
            LEFT JOIN ingest_meta m
                ON p.race_id = m.race_id
            WHERE p.outcome IS NOT NULL
              AND m.confirmed_at IS NOT NULL
              AND m.confirmed_at >= ?
        """
        params = [cut_iso]

        if season:
            query += " AND m.season = ? "
            params.append(season)

        cur.execute(query, params)
        rows = cur.fetchall()

    except Exception as e:
        return {
            "status": "ERROR",
            "message": str(e),
            "strategies": [],
            "models": [],
            "grid": [],
        }

    finally:
        try:
            con.close()
        except Exception:
            pass

    # matrix[strategy][model]
    matrix = defaultdict(
        lambda: defaultdict(
            lambda: {
                "HIT": 0.0,
                "MISS": 0.0,
                "PASS": 0.0,
                "TOTAL": 0.0,
                "HIT_RATE": 0.0,
            }
        )
    )

    strategies_set = set()
    models_set = set()

    for strategy, model, outcome, retry_count, confirmed_at, season_val in rows:
        strategy = strategy or "UNKNOWN"
        model = model or "UNKNOWN"

        strategies_set.add(strategy)
        models_set.add(model)

        st = state.get(strategy, {"enabled": 1, "mul": 1.0})
        if not include_disabled and st["enabled"] == 0:
            continue

        if mode == "raw":
            weight = 1.0
        else:
            weight = _weight_from_retry(int(retry_count)) * float(st["mul"])

        if weight <= 0:
            continue

        if outcome not in ("HIT", "MISS", "PASS"):
            continue

        b = matrix[strategy][model]
        b[outcome] += weight
        b["TOTAL"] += weight

    # finalize
    for s in matrix:
        for m in matrix[s]:
            b = matrix[s][m]
            if b["TOTAL"] > 0:
                b["HIT_RATE"] = round(b["HIT"] / b["TOTAL"] * 100.0, 2)
            b["HIT"] = round(b["HIT"], 2)
            b["MISS"] = round(b["MISS"], 2)
            b["PASS"] = round(b["PASS"], 2)
            b["TOTAL"] = round(b["TOTAL"], 2)

    strategies = sorted(strategies_set)
    models = sorted(models_set)

    grid: List[Dict[str, Any]] = []
    for s in strategies:
        row = {"strategy": s, "cells": []}
        for m in models:
            row["cells"].append({
                "model": m,
                **matrix.get(s, {}).get(
                    m,
                    {"HIT": 0.0, "MISS": 0.0, "PASS": 0.0, "TOTAL": 0.0, "HIT_RATE": 0.0},
                ),
            })
        grid.append(row)

    return {
        "status": "OK",
        "mode": mode,
        "days": int(days),
        "season": season,
        "strategies": strategies,
        "models": models,
        "grid": grid,
    }
