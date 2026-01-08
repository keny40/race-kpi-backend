from backend.services.pre_race import run_pre_race
from backend.services.pre_race_store import save_pre_race_result


def trigger_after_collect(race_ids: list[str]):
    """
    업로드 후 자동 실행되는 pre-race 트리거
    """
    results = []

    for race_id in race_ids:
        try:
            summary = run_pre_race(race_id)

            save_pre_race_result(
                race_id=race_id,
                summary=summary
            )

            results.append({
                "race_id": race_id,
                "pre_race": "OK"
            })

        except Exception as e:
            results.append({
                "race_id": race_id,
                "pre_race": "FAIL",
                "error": str(e)
            })

    return results
