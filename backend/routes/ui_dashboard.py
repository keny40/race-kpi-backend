from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from backend.db.conn import get_conn


router = APIRouter(prefix="/ui", tags=["ui"])


# 운영 기준 (필요하면 여기 숫자만 바꾸면 됩니다)
WINDOW = 10
MISS_RED = 7
MISS_YELLOW = 4
PASS_RED_RATIO = 0.60
PASS_YELLOW_RATIO = 0.40


def _status_color(status: str) -> str:
    if status == "RED":
        return "#e74c3c"
    if status == "YELLOW":
        return "#f1c40f"
    return "#2ecc71"


def _result_color(result: str) -> str:
    if result == "HIT":
        return "#2ecc71"
    if result == "MISS":
        return "#e74c3c"
    return "#95a5a6"


@router.get("/dashboard", response_class=HTMLResponse)
def ui_dashboard():
    conn = get_conn()
    cur = conn.cursor()

    # 1) KPI summary
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN result = 'HIT' THEN 1 ELSE 0 END) AS hit,
            SUM(CASE WHEN result = 'MISS' THEN 1 ELSE 0 END) AS miss,
            SUM(CASE WHEN result = 'PASS' THEN 1 ELSE 0 END) AS pass
        FROM (
            SELECT
                CASE
                    WHEN p.decision = 'PASS' THEN 'PASS'
                    WHEN p.decision = a.winner THEN 'HIT'
                    ELSE 'MISS'
                END AS result
            FROM predictions p
            LEFT JOIN race_actuals a
                ON p.race_id = a.race_id
        )
    """)
    total, hit, miss, pas = cur.fetchone()

    acc_ex_pass = round(hit / (hit + miss), 4) if (hit + miss) > 0 else 0.0
    acc_overall = round(hit / total, 4) if total > 0 else 0.0

    # 2) status window (최근 WINDOW건)
    cur.execute(f"""
        SELECT
            p.decision,
            a.winner
        FROM predictions p
        LEFT JOIN race_actuals a
            ON p.race_id = a.race_id
        ORDER BY p.created_at DESC
        LIMIT {WINDOW}
    """)
    window_rows = cur.fetchall()
    win_total = len(window_rows)

    win_miss = 0
    win_pass = 0
    for decision, winner in window_rows:
        if decision == "PASS":
            win_pass += 1
        elif winner is None or decision != winner:
            win_miss += 1

    reasons = []
    status = "GREEN"
    pass_ratio = (win_pass / win_total) if win_total > 0 else 0.0

    if win_total > 0:
        if win_miss >= MISS_RED or pass_ratio >= PASS_RED_RATIO:
            status = "RED"
            if win_miss >= MISS_RED:
                reasons.append("MISS_STREAK")
            if pass_ratio >= PASS_RED_RATIO:
                reasons.append("HIGH_PASS_RATIO")
        elif win_miss >= MISS_YELLOW or pass_ratio >= PASS_YELLOW_RATIO:
            status = "YELLOW"
            if win_miss >= MISS_YELLOW:
                reasons.append("MISS_INCREASE")
            if pass_ratio >= PASS_YELLOW_RATIO:
                reasons.append("PASS_INCREASE")

    # 3) match table (최근 100건)
    cur.execute("""
        SELECT
            p.race_id,
            p.decision,
            p.confidence,
            a.winner,
            CASE
                WHEN p.decision = 'PASS' THEN 'PASS'
                WHEN p.decision = a.winner THEN 'HIT'
                ELSE 'MISS'
            END AS result,
            p.created_at
        FROM predictions p
        LEFT JOIN race_actuals a
            ON p.race_id = a.race_id
        ORDER BY p.created_at DESC
        LIMIT 100
    """)
    rows = cur.fetchall()

    conn.close()

    reasons_text = ", ".join(reasons) if reasons else "-"
    status_color = _status_color(status)

    table_body = ""
    for r in rows:
        race_id, decision, confidence, winner, result, created_at = r
        table_body += f"""
        <tr style="color:{_result_color(result)}">
            <td>{race_id}</td>
            <td>{decision}</td>
            <td>{winner or '-'}</td>
            <td><b>{result}</b></td>
            <td>{round(confidence, 4) if confidence is not None else '-'}</td>
            <td>{created_at}</td>
        </tr>
        """

    html = f"""
    <html>
    <head>
        <title>KPI Dashboard</title>
        <style>
            body {{
                font-family: Arial;
                padding: 20px;
                background: #fafafa;
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 14px;
                margin-bottom: 18px;
            }}
            .card {{
                background: white;
                border: 1px solid #e6e6e6;
                border-radius: 10px;
                padding: 14px 16px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.04);
            }}
            .title {{
                font-size: 14px;
                color: #666;
                margin-bottom: 8px;
            }}
            .big {{
                font-size: 22px;
                font-weight: 700;
            }}
            .badge {{
                display: inline-block;
                padding: 6px 10px;
                border-radius: 999px;
                color: white;
                font-weight: 700;
                background: {status_color};
            }}
            .meta {{
                margin-top: 8px;
                color: #666;
                font-size: 13px;
                line-height: 1.5;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                background: white;
                border: 1px solid #e6e6e6;
                border-radius: 10px;
                overflow: hidden;
            }}
            th, td {{
                border-bottom: 1px solid #eee;
                padding: 10px;
                text-align: center;
                font-size: 13px;
            }}
            th {{
                background: #f4f4f4;
                font-weight: 700;
            }}
            h2 {{
                margin: 0 0 12px 0;
            }}
        </style>
    </head>
    <body>
        <h2>KPI Dashboard</h2>

        <div class="grid">
            <div class="card">
                <div class="title">STATUS (최근 {win_total}건)</div>
                <div class="big"><span class="badge">{status}</span></div>
                <div class="meta">
                    MISS: {win_miss} / PASS: {win_pass} / PASS Ratio: {round(pass_ratio, 4)}<br/>
                    Reason: {reasons_text}
                </div>
            </div>

            <div class="card">
                <div class="title">KPI SUMMARY (전체)</div>
                <div class="big">HIT {hit} / MISS {miss} / PASS {pas} / TOTAL {total}</div>
                <div class="meta">
                    Accuracy (ex PASS): {acc_ex_pass}<br/>
                    Accuracy (overall): {acc_overall}
                </div>
            </div>
        </div>

        <div class="card" style="margin-bottom:10px;">
            <div class="title">MATCH TABLE (최근 100건)</div>
        </div>

        <table>
            <tr>
                <th>Race ID</th>
                <th>Decision</th>
                <th>Winner</th>
                <th>Result</th>
                <th>Confidence</th>
                <th>Time</th>
            </tr>
            {table_body}
        </table>
    </body>
    </html>
    """
    return html
