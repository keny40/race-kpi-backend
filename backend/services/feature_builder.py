import pandas as pd

def build_features(entry_df: pd.DataFrame, history_df: pd.DataFrame) -> pd.DataFrame:
    agg = history_df.groupby("horse_name").agg(
        rating_avg=("earn_1y", "mean"),
        top3_rate=("top3", "mean"),
        recent_form=("rank", "mean")
    ).reset_index()

    return entry_df.merge(agg, on="horse_name", how="left").fillna(0)
