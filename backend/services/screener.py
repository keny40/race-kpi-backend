def screen_races(races):
    """
    races: list of dict
    required keys:
      race_no, horses_cnt, grade, is_2yo, is_mixed, distance
    """
    out = []
    for r in races:
        if r["is_2yo"]:
            continue
        if r["is_mixed"]:
            continue
        if r["horses_cnt"] < 8 or r["horses_cnt"] > 14:
            continue
        if r["race_no"] in (1, 2):      # 초반 배제
            continue
        out.append(r)
    return out
