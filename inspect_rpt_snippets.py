from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent
RPT_PATH = BASE_DIR / "20260103dacom01.rpt"

OUT_DIR = BASE_DIR / "parsed_output"
OUT_DIR.mkdir(exist_ok=True)
OUT_PATH = OUT_DIR / "snippets.txt"

def read_lines(path: Path):
    raw = path.read_bytes()
    for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
        try:
            return raw.decode(enc).splitlines(), enc
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace").splitlines(), "utf-8(errors=replace)"

def is_race_header_candidate(line: str) -> bool:
    # '경주' + 거리(M) 같은 힌트가 있는 줄을 최대한 넓게 잡습니다
    if "경주" in line and ("M" in line or "m" in line or "미터" in line):
        if re.search(r"\d", line):
            return True
    # '제1경주' 같은 케이스도 포함
    if re.search(r"제?\s*\d+\s*경주", line):
        return True
    return False

def is_horse_row_candidate(line: str) -> bool:
    # 출전마 표는 대개 "1  마명  ..." 처럼 시작하는 줄이 많아서 넓게 잡습니다
    s = line.strip()
    if not s:
        return False
    if re.match(r"^\d+\s+", s):
        # 너무 짧은 숫자줄 제외
        if len(s) >= 10:
            return True
    return False

def main():
    if not RPT_PATH.exists():
        raise FileNotFoundError(f"RPT not found: {RPT_PATH}")

    lines, enc = read_lines(RPT_PATH)

    race_candidates = []
    horse_candidates = []

    for i, line in enumerate(lines):
        # 원문 보존을 위해 그대로 저장(탭/공백 유지)
        if is_race_header_candidate(line):
            race_candidates.append((i + 1, line))
        if is_horse_row_candidate(line):
            horse_candidates.append((i + 1, line))

    # 너무 많으면 앞부분만 잘라서 저장
    race_candidates = race_candidates[:200]
    horse_candidates = horse_candidates[:400]

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(f"[encoding_used] {enc}\n\n")

        f.write("=== RACE HEADER CANDIDATES (line_no: text) ===\n")
        if not race_candidates:
            f.write("(none)\n")
        else:
            for ln, txt in race_candidates:
                f.write(f"{ln}: {txt}\n")

        f.write("\n=== HORSE ROW CANDIDATES (line_no: text) ===\n")
        if not horse_candidates:
            f.write("(none)\n")
        else:
            for ln, txt in horse_candidates:
                f.write(f"{ln}: {txt}\n")

    print("✅ snippets 추출 완료")
    print(f"- encoding_used: {enc}")
    print(f"- race_candidates: {len(race_candidates)}")
    print(f"- horse_candidates: {len(horse_candidates)}")
    print(f"- output: {OUT_PATH}")

if __name__ == "__main__":
    main()
s