# backend/services/report_pdf.py
import sqlite3, io, matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet

DB_PATH = "races.db"

def generate_pdf(path: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT strategy,
               AVG(CASE WHEN decision = winner THEN 1 ELSE 0 END) AS hit,
               AVG(COALESCE(roi,1)) AS roi,
               COUNT(*) AS cnt
        FROM predictions p JOIN actual_results a
        ON p.race_id=a.race_id
        GROUP BY strategy
    """).fetchall()
    conn.close()

    strategies = [r[0] for r in rows]
    hits = [r[1] for r in rows]
    rois = [r[2] for r in rows]

    plt.figure(figsize=(8,4))
    plt.bar(strategies, hits)
    plt.title("Hit Rate")
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format="png")
    plt.close()
    img_buf.seek(0)

    doc = SimpleDocTemplate(path)
    styles = getSampleStyleSheet()
    story = [Paragraph("KPI Report", styles["Title"]),
             Image(img_buf, width=400, height=200)]
    doc.build(story)
