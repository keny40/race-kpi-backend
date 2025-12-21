from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

import matplotlib.pyplot as plt
import sqlite3
import os
import tempfile

from season import SeasonManager

DB_PATH = "races.db"

def _plot_png(fig, w=160, h=90):
    path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path, (w, h)

def _query_model_hitrate():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT pm.model_name,
               SUM(CASE WHEN pm.label = r.winner THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS hr,
               COUNT(*) AS n
        FROM prediction_models pm
        JOIN results r ON pm.race_id = r.race_id
        WHERE pm.label != 'PASS'
        GROUP BY pm.model_name
        ORDER BY pm.model_name
        """
    ).fetchall()

    conn.close()
    return [(r["model_name"], float(r["hr"]), int(r["n"])) for r in rows]

def generate_performance_pdf(period: str = "monthly", output_path: str | None = None):
    season = SeasonManager.get_status()
    now = datetime.utcnow()

    if not output_path:
        suffix = "M" if period == "monthly" else "Q"
        output_path = f"performance_{now.strftime('%Y%m')}_{suffix}.pdf"

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Horse Race Performance Report ({period.upper()})", styles["Title"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Report Date (UTC): {now.strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 10))

    rw = season["recent_window"]
    data = [
        ["Metric", "Value"],
        ["Season ID", season["season_id"]],
        ["Locked", "YES" if season["locked"] else "NO"],
        ["Lock Reason", season["lock_reason"] or ""],
        ["Lock Until", season["lock_until"] or ""],
        ["Recent Bets", rw["bets"]],
        ["Recent Hit", rw["hit"]],
        ["Recent Miss", rw["miss"]],
        ["Recent HitRate", f"{rw['hitrate']:.3f}"],
    ]
    story.append(Table(data, colWidths=[60 * mm, 110 * mm]))
    story.append(Spacer(1, 14))

    tmp_paths = []

    # 차트 1: Outcome distribution (predictions 기준)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    hit = cur.execute("""
        SELECT COUNT(*)
        FROM predictions p JOIN results r ON p.race_id=r.race_id
        WHERE p.decision=r.winner
    """).fetchone()[0] or 0
    miss = cur.execute("""
        SELECT COUNT(*)
        FROM predictions p JOIN results r ON p.race_id=r.race_id
        WHERE p.decision!='PASS' AND p.decision!=r.winner
    """).fetchone()[0] or 0
    passed = cur.execute("SELECT COUNT(*) FROM predictions WHERE decision='PASS'").fetchone()[0] or 0
    conn.close()

    fig1 = plt.figure()
    plt.bar(["HIT", "MISS", "PASS"], [hit, miss, passed])
    plt.title("Outcome Distribution")
    p1, _ = _plot_png(fig1)
    tmp_paths.append(p1)
    story.append(Image(p1, width=160 * mm, height=90 * mm))
    story.append(Spacer(1, 10))

    # ✅ 차트 2: Model HitRate
    mh = _query_model_hitrate()
    if mh:
        names = [x[0] for x in mh]
        hrs = [x[1] for x in mh]
        fig2 = plt.figure()
        plt.bar(names, hrs)
        plt.ylim(0, 1)
        plt.title("Model HitRate (vs Winner)")
        plt.xlabel("Model")
        plt.ylabel("HitRate")
        p2, _ = _plot_png(fig2)
        tmp_paths.append(p2)
        story.append(Image(p2, width=160 * mm, height=90 * mm))
        story.append(Spacer(1, 10))

        # 표로도 같이
        table = [["Model", "HitRate", "N"]]
        for n, hr, cnt in mh:
            table.append([n, f"{hr:.3f}", cnt])
        story.append(Table(table, colWidths=[60 * mm, 40 * mm, 30 * mm]))
        story.append(Spacer(1, 10))
    else:
        story.append(Paragraph("Model HitRate: (no joined results yet)", styles["Normal"]))
        story.append(Spacer(1, 10))

    doc.build(story)

    for p in tmp_paths:
        try:
            os.remove(p)
        except Exception:
            pass

    return output_path
