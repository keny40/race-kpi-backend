import re

def parse_single_race_odds(text: str) -> float | None:
    """
    PDF 텍스트에서 단승식 1위 배당 추출
    """
    lines = text.splitlines()

    for i, line in enumerate(lines):
        if "단승식" in line:
            # 다음 몇 줄에서 숫자 + 배당 패턴 탐색
            for j in range(i + 1, i + 6):
                m = re.search(r"\b1\s+([0-9]+\.[0-9]+)", lines[j])
                if m:
                    return float(m.group(1))

    return None
