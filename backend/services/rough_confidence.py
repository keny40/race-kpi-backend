def rough_confidence(entry_df):
    """
    entry_df: 출전표 DataFrame
    """
    score = 0.0

    # 말 수 안정성
    n = len(entry_df)
    score += 0.15 if 9 <= n <= 12 else 0.05

    # 중량 분산
    w_std = entry_df["weight"].std()
    score += 0.15 if w_std < 0.8 else 0.05

    # 기수 중복 (강기수 편중)
    top_jockey_ratio = entry_df["jockey"].value_counts().iloc[0] / n
    score += 0.2 if top_jockey_ratio >= 0.25 else 0.1

    # 레이팅 존재 여부
    if "rating" in entry_df.columns:
        score += 0.2

    return round(min(score, 1.0), 2)
