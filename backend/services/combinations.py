# backend/services/combinations.py
import itertools

def combo_bok(df, top_n=4):
    ...

def combo_ssang(df):
    ...

def combo_sambok(df, min_conf=0.55):
    ...

def generate_combinations(score_df):
    result = {}
    for race_no, g in score_df.groupby("race_no"):
        result[race_no] = {
            "bok": combo_bok(g),
            "ssang": combo_ssang(g),
            "sambok": combo_sambok(g)
        }
    return result
