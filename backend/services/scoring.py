def score_race(df):
    df = df.copy()
    df["rating_n"] = df["rating_avg"] / df["rating_avg"].max()
    df["form_n"] = df["recent_form"] / df["recent_form"].max()

    df["score"] = (
        0.4 * df["rating_n"] +
        0.3 * df["top3_rate"] +
        0.3 * (1 - df["form_n"])
    )
    return df
