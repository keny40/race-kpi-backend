from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from backend.db.conn import get_conn

router = APIRouter(
    prefix="/ui",
    tags=["ui"]
)

@router.get("/results", response_class=HTMLResponse)
def ui_results():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT race_id, winner, placed, created_at
        FROM race_actuals
        ORDER BY created_at DESC
        LIMIT 20
    """)
    rows = cur.fetchall()
    conn.close()

    html = """
    <html>
    <head>
        <title>Race Results</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; }
            th { background: #333; color: #fff; }
        </style>
    </head>
    <body>
        <h2>최근 경기 결과</h2>
        <table>
            <tr>
                <th>Race ID</th>
                <th>Winner</th>
                <th>Placed</th>
                <th>Time</th>
            </tr>
    """

    for r in rows:
        html += f"""
            <tr>
                <td>{r[0]}</td>
                <td>{r[1]}</td>
                <td>{r[2]}</td>
                <td>{r[3]}</td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    return html
