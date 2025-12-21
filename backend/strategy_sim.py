from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class SimResult:
    strategy: str
    stake: float
    total_bets: int
    wins: int
    losses: int
    passes: int
    profit: float
    roi: float
    equity: List[Dict[str, Any]]  # [{i, race_id, outcome, pnl, equity}]


def _pick_top_label(pred: Dict[str, Any]) -> str:
    return str(pred.get("label", "PASS"))


def _label_to_horse_no(label: str) -> Optional[int]:
    if not label or label == "PASS":
        return None
    if label.startswith("HORSE_"):
        try:
            return int(label.split("_", 1)[1])
        except Exception:
            return None
    return None


def _get_odds(odds_map: Dict[str, Any], horse_no: int) -> Optional[float]:
    if not odds_map:
        return None
    # 저장은 {"1": 3.1, "2": 5.2} 형태로 들어갈 수 있어 문자열/정수 모두 대응
    v = odds_map.get(str(horse_no))
    if v is None:
        v = odds_map.get(horse_no)
    try:
        return float(v) if v is not None else None
    except Exception:
        return None


def simulate_strategy(
    *,
    predictions: List[Dict[str, Any]],
    results: List[Dict[str, Any]],
    strategy: str,
    stake: float = 1.0,
    min_confidence: float = 0.0,
) -> SimResult:
    """
    assumptions:
      - results row: {race_id, winner_horse_no, outcome(HIT/MISS/PASS), predicted_label}
      - predictions row includes meta.odds_map: {"1": 3.1, ...}
      - payout model (단순):
          WIN: + stake*(odds-1)
          LOSE: - stake
          PASS: 0
    strategies:
      - flat_top1: top1이면 무조건 베팅
      - conf_threshold: top1 confidence >= min_confidence 일 때만 베팅
    """
    pred_by_key: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for p in predictions:
        pred_by_key[(str(p.get("season_key")), str(p.get("race_id")))] = p

    equity = 0.0
    curve: List[Dict[str, Any]] = []

    wins = losses = passes = bets = 0
    profit = 0.0

    for i, r in enumerate(results, start=1):
        season_key = str(r.get("season_key"))
        race_id = str(r.get("race_id"))
        pred = pred_by_key.get((season_key, race_id))

        predicted_label = str(r.get("predicted_label", "PASS"))
        outcome = str(r.get("outcome", "PASS"))
        winner_no = int(r.get("winner_horse_no", 0))

        pnl = 0.0

        if not pred:
            # 예측이 없으면 PASS 처리
            passes += 1
            curve.append({"i": i, "race_id": race_id, "outcome": "NO_PRED", "pnl": 0.0, "equity": equity})
            continue

        top_label = _pick_top_label(pred)
        top_conf = float(pred.get("confidence", 0.0))
        odds_map = (pred.get("meta") or {}).get("odds_map") or {}

        if strategy == "flat_top1":
            if top_label == "PASS":
                passes += 1
            else:
                bet_horse = _label_to_horse_no(top_label)
                if bet_horse is None:
                    passes += 1
                else:
                    bets += 1
                    odds = _get_odds(odds_map, bet_horse)
                    # odds 없으면 베팅 자체를 PASS로 처리(실데이터 누락 방지)
                    if odds is None or odds <= 1.0:
                        passes += 1
                        bets -= 1
                    else:
                        if bet_horse == winner_no:
                            wins += 1
                            pnl = stake * (odds - 1.0)
                        else:
                            losses += 1
                            pnl = -stake

        elif strategy == "conf_threshold":
            if top_label == "PASS":
                passes += 1
            elif top_conf < float(min_confidence):
                passes += 1
            else:
                bet_horse = _label_to_horse_no(top_label)
                if bet_horse is None:
                    passes += 1
                else:
                    bets += 1
                    odds = _get_odds(odds_map, bet_horse)
                    if odds is None or odds <= 1.0:
                        passes += 1
                        bets -= 1
                    else:
                        if bet_horse == winner_no:
                            wins += 1
                            pnl = stake * (odds - 1.0)
                        else:
                            losses += 1
                            pnl = -stake
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        equity += pnl
        profit += pnl
        curve.append({"i": i, "race_id": race_id, "outcome": outcome, "pnl": round(pnl, 6), "equity": round(equity, 6)})

    total_bets = bets
    roi = (profit / (stake * total_bets)) if total_bets > 0 else 0.0

    return SimResult(
        strategy=strategy,
        stake=float(stake),
        total_bets=int(total_bets),
        wins=int(wins),
        losses=int(losses),
        passes=int(passes),
        profit=round(float(profit), 6),
        roi=round(float(roi), 6),
        equity=curve,
    ).__dict__
