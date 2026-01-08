from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class StakePlan:
    action: str               # "PASS" | "BET"
    tier: str                 # "NONE" | "SMALL" | "NORMAL"
    stake: float              # stake amount
    reason: str               # short reason


@dataclass
class KillDecision:
    enabled: bool
    reason: str


def default_cut_config() -> Dict[str, float]:
    return {
        "cut_pass": 0.60,
        "cut_small": 0.68,
        "stake_small": 300.0,
        "stake_normal": 1000.0,
    }


def default_kill_config() -> Dict[str, float]:
    return {
        "min_bets_for_kill": 30.0,
        "kill_roi": -0.20,
        "warn_roi": 0.05,
        "promote_roi": 0.30,
    }


def decide_stake(calibrated_conf: float, cfg: Optional[Dict[str, float]] = None) -> StakePlan:
    c = cfg or default_cut_config()

    if calibrated_conf < c["cut_pass"]:
        return StakePlan(action="PASS", tier="NONE", stake=0.0, reason=f"conf<{c['cut_pass']}")
    if calibrated_conf < c["cut_small"]:
        return StakePlan(action="BET", tier="SMALL", stake=float(c["stake_small"]), reason=f"{c['cut_pass']}<=conf<{c['cut_small']}")
    return StakePlan(action="BET", tier="NORMAL", stake=float(c["stake_normal"]), reason=f"conf>={c['cut_small']}")


def decide_kill_switch(bets: int, roi: float, cfg: Optional[Dict[str, float]] = None) -> KillDecision:
    k = cfg or default_kill_config()

    if bets < int(k["min_bets_for_kill"]):
        return KillDecision(enabled=True, reason=f"warmup(bets<{int(k['min_bets_for_kill'])})")

    if roi <= k["kill_roi"]:
        return KillDecision(enabled=False, reason=f"kill(roi<={k['kill_roi']})")

    return KillDecision(enabled=True, reason="ok")
