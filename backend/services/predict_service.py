from backend.services.combinations import generate_combinations

def run_today_prediction(score_df):
    combos = generate_combinations(score_df)
    return combos
