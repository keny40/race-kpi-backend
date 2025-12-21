from server import score_horse

def run_backtest(dataset):
    hit = 0
    total = len(dataset)

    for race in dataset:
        scores = [(h["horse_id"], score_horse(type("H", (), h))) for h in race["horses"]]
        scores.sort(key=lambda x: x[1], reverse=True)

        if scores[0][0] == race["winner"]:
            hit += 1

    return round(hit / total, 3)
