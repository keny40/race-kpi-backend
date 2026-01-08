def calc_kpi():
    for race_id in predictions:
        pred = load_prediction(race_id)
        result = load_result(race_id)

        if pred["decision"] == "PLAY":
            play += 1
            if pred["top"][0]["no"] == result["winner"]:
                hit += 1
