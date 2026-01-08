def calc_ev(allocated, odds_map):
    """
    allocated: [{type, horses, confidence, bet_amount}]
    odds_map: {('쌍승', (1,3)): 12.4, ...}
    """
    results = []

    for it in allocated:
        key = (it["type"], tuple(it["horses"]))
        odds = odds_map.get(key)
        if not odds:
            continue

        p = min(0.95, it["confidence"])  # 상한
        ev = (p * odds - 1) * it["bet_amount"]

        results.append({
            **it,
            "odds": odds,
            "EV": round(ev, 0)
        })

    return results
