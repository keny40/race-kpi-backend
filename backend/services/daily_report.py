def make_daily_report(race_results):
    """
    race_results: list of dict
    keys: race_no, rough_conf
    """
    report = []
    for r in race_results:
        report.append({
            "race_no": r["race_no"],
            "rough_conf": r["rough_conf"],
            "status": "PDF_CHECK" if r["rough_conf"] >= 0.45 else "PASS"
        })
    return sorted(report, key=lambda x: x["rough_conf"], reverse=True)
