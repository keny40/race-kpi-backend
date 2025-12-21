BASE = {
    "recent_rank": 2.0,
    "draw": 0.5,
    "odds": 0.8,
    "noise": 0.2
}

BY_DISTANCE = {
    "short": {   # ≤1200m
        "recent_rank": 2.5,
        "draw": 0.8,
        "odds": 0.6,
        "noise": 0.15
    },
    "middle": {  # 1300~1800m
        "recent_rank": 2.0,
        "draw": 0.5,
        "odds": 0.8,
        "noise": 0.2
    },
    "long": {    # ≥1900m
        "recent_rank": 1.8,
        "draw": 0.3,
        "odds": 1.0,
        "noise": 0.25
    }
}

BY_TRACK = {
    "fast": {    # 건조/고속
        "recent_rank": 2.2,
        "draw": 0.6,
        "odds": 0.7,
        "noise": 0.15
    },
    "wet": {     # 습/우중
        "recent_rank": 1.7,
        "draw": 0.2,
        "odds": 1.1,
        "noise": 0.3
    }
}

def select_weights(distance: int | None, track: str | None):
    w = BASE.copy()

    if distance is not None:
        if distance <= 1200:
            w.update(BY_DISTANCE["short"])
        elif distance >= 1900:
            w.update(BY_DISTANCE["long"])
        else:
            w.update(BY_DISTANCE["middle"])

    if track in BY_TRACK:
        w.update(BY_TRACK[track])

    return w
