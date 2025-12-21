# backend/offline/train_model.py

"""
오프라인 학습 스크립트

사용 예:
  python -m backend.offline.train_model

전제:
  data/races_history.csv 파일이 있고, 컬럼은 아래와 같다고 가정
    race_id, horse_no, is_winner
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple

from backend.offline.data_loader import load_race_csv, RaceRecord


DEFAULT_DATA_PATH = Path("data") / "races_history.csv"
DEFAULT_MODEL_PATH = Path("models") / "baseline_winrate.json"


def compute_baseline_model(records: list[RaceRecord]) -> Dict:
    """
    매우 단순한 베이스라인:

    - 말 번호(horse_no)별로
        win_count / total_count = 우승률
    - 전체 평균 우승률도 함께 저장 (데이터 부족 시 fallback용)
    """
    per_horse: Dict[int, Tuple[int, int]] = defaultdict(lambda: [0, 0])
    total_win = 0
    total_cnt = 0

    for r in records:
        per_horse[r.horse_no][1] += 1
        total_cnt += 1
        if r.is_winner == 1:
            per_horse[r.horse_no][0] += 1
            total_win += 1

    if total_cnt == 0:
        raise ValueError("입력 데이터가 비어 있습니다.")

    global_rate = total_win / total_cnt

    model = {
        "global_win_rate": global_rate,
        "horse_win_rate": {
            str(horse_no): (wins / total if total > 0 else global_rate)
            for horse_no, (wins, total) in per_horse.items()
        },
        "meta": {
            "total_records": total_cnt,
            "total_wins": total_win,
        },
    }
    return model


def main(
    csv_path: Path = DEFAULT_DATA_PATH,
    model_path: Path = DEFAULT_MODEL_PATH,
) -> None:
    print(f"[INFO] CSV 로딩: {csv_path}")
    records = load_race_csv(str(csv_path))
    print(f"[INFO] 로드된 레코드 수: {len(records)}")

    print("[INFO] 베이스라인 모델 계산 중...")
    model_dict = compute_baseline_model(records)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    with model_path.open("w", encoding="utf-8") as f:
        json.dump(model_dict, f, ensure_ascii=False, indent=2)

    print(f"[INFO] 모델 저장 완료: {model_path}")
    print(f"[INFO] 글로벌 우승률: {model_dict['global_win_rate']:.4f}")


if __name__ == "__main__":
    main()
