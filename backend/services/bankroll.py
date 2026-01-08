# backend/services/bankroll.py

def allocate_budget(combos, total_budget=10000):
    """
    combos: list of dict
    """

    if not combos:
        return []

    total_prob = sum(c["prob"] for c in combos)

    allocated = []
    for c in combos:
        weight = c["prob"] / total_prob if total_prob > 0 else 0
        stake = round(total_budget * weight)

        allocated.append({
            **c,
            "stake": stake
        })

    return allocated
