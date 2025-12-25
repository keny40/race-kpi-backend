from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from backend.db.conn import get_conn


router = APIRouter(prefix="/ui", tags=["ui"])

@router.get("/kpi-results", response_class=HTMLResponse)
def ui_kpi_results():
    conn = get_conn()
    cur = conn.cursor()

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

    def color(r):
        return {"HIT":"#2ecc71","MISS":"#e74c3c","PASS":"#95a5a6"}.get(r,"#000")

    body = ""
    for r in rows:
        body += f"""
        <tr style="color:{color(r[4])}">
            <td>{r[0]}</td>
            <td>{r[1]}</td>
            <td>{r[3] or '-'}</td>
            <td><b>{r[4]}</b></td>
            <td>{round(r[2],4) if r[2] else '-'}</td>
            <td>{r[5]}</td>
        </tr>
        """

    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial; padding:20px; }}
            table {{ border-collapse: collapse; width:100%; }}
            th, td {{ border:1px solid #ddd; padding:8px; text-align:center; }}
            th {{ background:#f4f4f4; }}
        </style>
    </head>
    <body>
        <h2>Prediction vs Actual (KPI)</h2>
        <table>
            <tr>
                <th>Race ID</th>
                <th>Decision</th>
                <th>Winner</th>
                <th>Result</th>
                <th>Confidence</th>
                <th>Time</th>
            </tr>
            {body}
        </table>
    </body>
    </html>
    """
