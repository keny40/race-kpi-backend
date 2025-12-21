import os
import random
import tempfile
import smtplib
from email.message import EmailMessage
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime, timezone

import requests
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from backend.scheduler import start_scheduler
from fastapi.staticfiles import StaticFiles
from backend.routes import admin_settings, lock_admin

from backend.db import (
    bootstrap_db,
    connect,
    compute_kpi_overall,
    compute_kpi_by_model,
)

app = FastAPI(title="Race KPI Backend", version="1.8.0")

Decision = Literal["P", "B", "PASS"]
ActualLabel = Literal["P", "B"]
Period = Literal["daily", "weekly", "monthly"]

app.include_router(admin_settings.router)
app.include_router(lock_admin.router)

app.mount("/admin", StaticFiles(directory="web", html=True), name="admin")


@app.on_event("startup")
def on_startup():
    start_scheduler()

# =========================
# Startup / Utils
# =========================
@app.on_event("startup")
def startup():
    bootstrap_db()
    _ensure_admin_tables()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _ensure_admin_tables():
    con = connect()
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS app_lock (
              id INTEGER PRIMARY KEY CHECK (id=1),
              locked INTEGER NOT NULL DEFAULT 0,
              reason TEXT,
              locked_at TEXT
            )
            """
        )
        con.execute(
            "INSERT OR IGNORE INTO app_lock(id, locked, reason, locked_at) VALUES(1, 0, NULL, NULL)"
        )

        # 기본 설정값(없으면 삽입)
        defaults = _default_settings()
        for k, v in defaults.items():
            con.execute(
                "INSERT OR IGNORE INTO app_settings(key, value) VALUES(?,?)",
                (k, str(v)),
            )
        con.commit()
    finally:
        con.close()


def _default_settings() -> Dict[str, Any]:
    return {
        # thresholds (기본은 env, env 없으면 하드코딩)
        "hit_green": os.getenv("KPI_HIT_GREEN", "0.60"),
        "hit_yellow": os.getenv("KPI_HIT_YELLOW", "0.45"),
        "pass_green": os.getenv("KPI_PASS_GREEN", "0.20"),
        "pass_yellow": os.getenv("KPI_PASS_YELLOW", "0.35"),
        # report period default
        "period_default": os.getenv("KPI_PERIOD_DEFAULT", "daily"),
        # auto stop (RED streak lock)
        "auto_stop_enabled": os.getenv("KPI_AUTOSTOP_ENABLED", "1"),  # 1/0
        "auto_stop_window": os.getenv("KPI_AUTOSTOP_WINDOW", "3"),    # 최근 N기간
        "auto_stop_metric": os.getenv("KPI_AUTOSTOP_METRIC", "both"), # hit|pass|both
        # notify (선택)
        "slack_webhook_url": os.getenv("SLACK_WEBHOOK_URL", ""),
        "smtp_host": os.getenv("SMTP_HOST", ""),
        "smtp_port": os.getenv("SMTP_PORT", "587"),
        "smtp_user": os.getenv("SMTP_USER", ""),
        "smtp_pass": os.getenv("SMTP_PASS", ""),
        "mail_to": os.getenv("MAIL_TO", ""),
    }


def _get_settings(con) -> Dict[str, str]:
    rows = con.execute("SELECT key, value FROM app_settings").fetchall()
    return {r["key"]: r["value"] for r in rows}


def _set_settings(con, patch: Dict[str, Any]):
    for k, v in patch.items():
        con.execute(
            "INSERT INTO app_settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (k, str(v)),
        )


def _get_lock(con) -> Dict[str, Any]:
    r = con.execute("SELECT locked, reason, locked_at FROM app_lock WHERE id=1").fetchone()
    return {
        "locked": bool(r["locked"]),
        "reason": r["reason"],
        "locked_at": r["locked_at"],
    }


def _set_lock(con, locked: bool, reason: Optional[str] = None):
    con.execute(
        "UPDATE app_lock SET locked=?, reason=?, locked_at=? WHERE id=1",
        (1 if locked else 0, reason, _utc_now_iso() if locked else None),
    )


def _thresholds_from_settings(s: Dict[str, str]):
    hit_green = float(s["hit_green"])
    hit_yellow = float(s["hit_yellow"])
    pass_green = float(s["pass_green"])
    pass_yellow = float(s["pass_yellow"])
    return hit_green, hit_yellow, pass_green, pass_yellow


def _hit_status(rate: float, hit_green: float, hit_yellow: float):
    if rate >= hit_green:
        return colors.green, "GREEN"
    if rate >= hit_yellow:
        return colors.orange, "YELLOW"
    return colors.red, "RED"


def _pass_status(rate: float, pass_green: float, pass_yellow: float):
    if rate <= pass_green:
        return colors.green, "GREEN"
    if rate <= pass_yellow:
        return colors.orange, "YELLOW"
    return colors.red, "RED"


# =========================
# Request Models
# =========================
class PredictRequest(BaseModel):
    race_id: str = Field(..., min_length=1)
    model_name: str = Field(..., min_length=1)


class ActualRequest(BaseModel):
    race_id: str = Field(..., min_length=1)
    actual_label: ActualLabel
    note: Optional[str] = None


# =========================
# Predict / Actual / KPI
# =========================
@app.post("/api/predict")
def api_predict(req: PredictRequest):
    con = connect()
    try:
        lock = _get_lock(con)
        if lock["locked"]:
            # LOCK 중에는 예측을 DB에 기록하지 않음(통계 오염 방지)
            return {
                "race_id": req.race_id,
                "decision": "PASS",
                "confidence": 0.0,
                "model_name": req.model_name,
                "created_at": _utc_now_iso(),
                "meta": {
                    "locked": True,
                    "reason": lock["reason"],
                    "locked_at": lock["locked_at"],
                },
            }

        r = random.random()
        if r < 0.15:
            decision = "PASS"
            confidence = 0.0
        else:
            decision = "P" if r < 0.575 else "B"
            confidence = round(0.55 + random.random() * 0.35, 4)

        created_at = _utc_now_iso()
        con.execute(
            """
            INSERT INTO predictions(race_id, decision, confidence, model_name, created_at)
            VALUES(?,?,?,?,?)
            """,
            (req.race_id, decision, float(confidence), req.model_name, created_at),
        )
        con.commit()

        return {
            "race_id": req.race_id,
            "decision": decision,
            "confidence": float(confidence),
            "model_name": req.model_name,
            "created_at": created_at,
        }
    finally:
        con.close()


@app.post("/api/result/actual")
def api_result_actual(req: ActualRequest):
    con = connect()
    try:
        created_at = _utc_now_iso()
        con.execute(
            """
            INSERT INTO actual_results(race_id, actual_label, note, created_at)
            VALUES(?,?,?,?)
            ON CONFLICT(race_id) DO UPDATE SET
              actual_label=excluded.actual_label,
              note=excluded.note,
              created_at=excluded.created_at
            """,
            (req.race_id, req.actual_label, req.note, created_at),
        )
        con.commit()

        # KPI 계산
        kpi = compute_kpi_overall(con)

        # auto-stop 감지(RED 지속 시 LOCK)
        _auto_stop_check_and_lock(con)

        return {
            "race_id": req.race_id,
            "actual_label": req.actual_label,
            "note": req.note,
            "created_at": created_at,
            "kpi": kpi,
            "lock": _get_lock(con),
        }
    finally:
        con.close()


@app.get("/api/metrics/kpi")
def api_metrics_kpi():
    con = connect()
    try:
        k = compute_kpi_overall(con)
        lock = _get_lock(con)
    finally:
        con.close()
    return {**k, "lock": lock}


@app.get("/api/metrics/kpi/models")
def api_metrics_kpi_models():
    con = connect()
    try:
        rows = compute_kpi_by_model(con)
    finally:
        con.close()
    return rows


# =========================
# (NEW) Confidence bins by model
# =========================
@app.get("/api/metrics/confidence/bins/models")
def api_conf_bins_models():
    con = connect()
    try:
        rows = con.execute(
            """
            WITH latest AS (
              SELECT race_id, MAX(created_at) AS created_at
              FROM predictions
              GROUP BY race_id
            )
            SELECT
              p.model_name AS model_name,
              CASE
                WHEN p.confidence < 0.6 THEN '0.5-0.6'
                WHEN p.confidence < 0.7 THEN '0.6-0.7'
                ELSE '0.7+'
              END AS bin,
              COUNT(*) AS total,
              SUM(CASE WHEN a.actual_label=p.decision THEN 1 ELSE 0 END) AS hit
            FROM latest l
            JOIN predictions p ON p.race_id=l.race_id AND p.created_at=l.created_at
            LEFT JOIN actual_results a ON a.race_id=p.race_id
            WHERE p.decision!='PASS'
            GROUP BY p.model_name, bin
            ORDER BY p.model_name, bin
            """
        ).fetchall()

        out: Dict[str, List[Dict[str, Any]]] = {}
        for r in rows:
            m = r["model_name"]
            if m not in out:
                out[m] = []
            total = r["total"] or 0
            hit = r["hit"] or 0
            out[m].append(
                {
                    "bin": r["bin"],
                    "total": total,
                    "hit_rate": (hit / total) if total else 0.0,
                }
            )
        return out
    finally:
        con.close()


# =========================
# Trend aggregation (daily/weekly/monthly)
# =========================
def _aggregate_trend(con, period: str, limit: int):
    group = {
        "daily": "substr(p.created_at,1,10)",
        "weekly": "strftime('%Y-W%W', p.created_at)",
        "monthly": "substr(p.created_at,1,7)",
    }[period]

    rows = con.execute(
        f"""
        WITH latest AS (
          SELECT race_id, MAX(created_at) AS created_at
          FROM predictions
          GROUP BY race_id
        )
        SELECT
          {group} AS bucket,
          COUNT(*) AS total,
          SUM(CASE WHEN p.decision!='PASS' AND a.actual_label=p.decision THEN 1 ELSE 0 END) AS hit,
          SUM(CASE WHEN p.decision!='PASS' AND a.actual_label IS NOT NULL AND a.actual_label!=p.decision THEN 1 ELSE 0 END) AS miss,
          SUM(CASE WHEN p.decision='PASS' THEN 1 ELSE 0 END) AS pass_cnt
        FROM latest l
        JOIN predictions p ON p.race_id=l.race_id AND p.created_at=l.created_at
        LEFT JOIN actual_results a ON a.race_id=p.race_id
        GROUP BY bucket
        ORDER BY bucket DESC
        LIMIT ?
        """,
        (int(limit),),
    ).fetchall()

    # 오래된 순으로
    rows = list(reversed(rows))

    out = []
    for r in rows:
        hit = r["hit"] or 0
        miss = r["miss"] or 0
        total = r["total"] or 0
        out.append(
            {
                "bucket": r["bucket"],
                "total": total,
                "hit": hit,
                "miss": miss,
                "pass": r["pass_cnt"] or 0,
                "hit_rate": (hit / (hit + miss)) if (hit + miss) else 0.0,
                "pass_rate": (r["pass_cnt"] / total) if total else 0.0,
            }
        )
    return out


@app.get("/api/kpi/trend")
def api_kpi_trend(
    period: Period = Query("daily"),
    limit: int = Query(14, ge=3, le=120),
):
    con = connect()
    try:
        return _aggregate_trend(con, period, limit)
    finally:
        con.close()


# =========================
# Auto-stop (RED streak -> LOCK)
# =========================
def _auto_stop_check_and_lock(con):
    s = _get_settings(con)
    enabled = s.get("auto_stop_enabled", "1") == "1"
    if not enabled:
        return

    window = int(s.get("auto_stop_window", "3"))
    metric = s.get("auto_stop_metric", "both")
    period = s.get("period_default", "daily")
    if period not in ("daily", "weekly", "monthly"):
        period = "daily"

    hit_green, hit_yellow, pass_green, pass_yellow = _thresholds_from_settings(s)
    trend = _aggregate_trend(con, period, max(window, 3))
    if len(trend) < window:
        return

    recent = trend[-window:]

    def is_red_hit(x):  # hit_rate RED
        _, label = _hit_status(x["hit_rate"], hit_green, hit_yellow)
        return label == "RED"

    def is_red_pass(x):  # pass_rate RED
        _, label = _pass_status(x["pass_rate"], pass_green, pass_yellow)
        return label == "RED"

    if metric == "hit":
        red_streak = all(is_red_hit(x) for x in recent)
    elif metric == "pass":
        red_streak = all(is_red_pass(x) for x in recent)
    else:
        red_streak = all(is_red_hit(x) or is_red_pass(x) for x in recent)

    if red_streak:
        lock = _get_lock(con)
        if not lock["locked"]:
            _set_lock(con, True, reason=f"AUTO_STOP_RED_STREAK({metric})/{period}/N={window}")
            con.commit()


# =========================
# Admin APIs (UI toggle target)
# =========================
@app.get("/api/admin/settings")
def admin_get_settings():
    con = connect()
    try:
        s = _get_settings(con)
        lock = _get_lock(con)
    finally:
        con.close()
    return {"settings": s, "lock": lock}


@app.put("/api/admin/settings")
def admin_put_settings(payload: Dict[str, Any]):
    """
    payload 예:
    {
      "hit_green": 0.6,
      "hit_yellow": 0.45,
      "pass_green": 0.2,
      "pass_yellow": 0.35,
      "period_default": "daily|weekly|monthly",
      "auto_stop_enabled": 1,
      "auto_stop_window": 3,
      "auto_stop_metric": "hit|pass|both"
    }
    """
    con = connect()
    try:
        allowed = {
            "hit_green", "hit_yellow", "pass_green", "pass_yellow",
            "period_default",
            "auto_stop_enabled", "auto_stop_window", "auto_stop_metric",
            "slack_webhook_url",
            "smtp_host", "smtp_port", "smtp_user", "smtp_pass", "mail_to",
        }
        patch = {k: v for k, v in payload.items() if k in allowed}
        _set_settings(con, patch)
        con.commit()
        s = _get_settings(con)
        lock = _get_lock(con)
    finally:
        con.close()
    return {"ok": True, "settings": s, "lock": lock}


@app.get("/api/admin/lock")
def admin_get_lock():
    con = connect()
    try:
        return _get_lock(con)
    finally:
        con.close()


@app.post("/api/admin/lock/unlock")
def admin_unlock():
    con = connect()
    try:
        _set_lock(con, False, reason=None)
        con.commit()
        return {"ok": True, "lock": _get_lock(con)}
    finally:
        con.close()


@app.post("/api/admin/lock/lock")
def admin_lock(reason: str = Query("MANUAL_LOCK")):
    con = connect()
    try:
        _set_lock(con, True, reason=reason)
        con.commit()
        return {"ok": True, "lock": _get_lock(con)}
    finally:
        con.close()


# =========================
# PDF (기존 유지 + 설정 period_default 활용)
# =========================
def _draw_line(c, x, y, w, h, values, title):
    if not values:
        c.drawString(x, y + h / 2, "No data")
        return
    step = w / max(1, len(values) - 1)
    pts = [(x + i * step, y + v * h) for i, v in enumerate(values)]
    c.rect(x, y, w, h)
    c.setStrokeColor(colors.darkblue)
    c.setLineWidth(2)
    for i in range(len(pts) - 1):
        c.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, y + h + 6, title)


@app.get("/api/kpi/report/pdf")
def api_kpi_report_pdf(
    period: Optional[Period] = Query(None),
    notify_slack: bool = Query(False),
    notify_mail: bool = Query(False),
):
    con = connect()
    try:
        s = _get_settings(con)
        hit_green, hit_yellow, pass_green, pass_yellow = _thresholds_from_settings(s)

        if period is None:
            p = s.get("period_default", "daily")
            period = p if p in ("daily", "weekly", "monthly") else "daily"

        overall = compute_kpi_overall(con)
        models = compute_kpi_by_model(con)
        trend = _aggregate_trend(con, period, 14)

        lock = _get_lock(con)
    finally:
        con.close()

    hc, hl = _hit_status(overall["hit_rate"], hit_green, hit_yellow)
    pc, pl = _pass_status(overall["pass_rate"], pass_green, pass_yellow)

    hit_series = [t["hit_rate"] for t in trend]
    pass_series = [t["pass_rate"] for t in trend]

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(tmp.name, pagesize=A4)
    w, h = A4

    # Page 1 Summary
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, h - 40, "KPI Executive Summary")
    c.setFont("Helvetica", 10)
    c.drawString(40, h - 64, f"As of: {overall['asof_at']}  |  Period: {period}")
    c.drawString(40, h - 80, f"LOCK: {lock['locked']}  ({lock.get('reason')})")

    c.setFillColor(hc)
    c.rect(40, h - 112, 14, 14, fill=1)
    c.setFillColor(colors.black)
    c.drawString(60, h - 110, f"Hit Rate {overall['hit_rate']:.2%} ({hl})")

    c.setFillColor(pc)
    c.rect(40, h - 140, 14, 14, fill=1)
    c.setFillColor(colors.black)
    c.drawString(60, h - 138, f"Pass Rate {overall['pass_rate']:.2%} ({pl})")

    c.showPage()

    # Page 2 Detail
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, h - 40, "KPI Detail")

    y = h - 70
    c.setFont("Helvetica", 10)
    for m in models:
        c.drawString(
            40,
            y,
            f"{m['model_name']} | Total {m['total']} | HIT {m['hit']} | MISS {m['miss']} | PASS {m['pass']} | HitRate {m['hit_rate']:.2%}",
        )
        y -= 14

    _draw_line(c, 60, 300, 480, 140, hit_series, f"Hit Rate Trend ({period})")
    _draw_line(c, 60, 120, 480, 140, pass_series, f"Pass Rate Trend ({period})")

    c.showPage()
    c.save()

    # Notify(선택)
    if notify_slack and s.get("slack_webhook_url"):
        try:
            requests.post(
                s["slack_webhook_url"],
                json={"text": "📊 KPI PDF 리포트 생성 완료"},
                timeout=3,
            )
        except Exception:
            pass

    if notify_mail and s.get("smtp_host") and s.get("smtp_user") and s.get("smtp_pass") and s.get("mail_to"):
        try:
            msg = EmailMessage()
            msg["Subject"] = "[KPI] 자동 리포트"
            msg["From"] = s["smtp_user"]
            msg["To"] = s["mail_to"]
            msg.set_content("KPI 리포트를 첨부합니다.")

            with open(tmp.name, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="application",
                    subtype="pdf",
                    filename="kpi_report.pdf",
                )

            with smtplib.SMTP(s["smtp_host"], int(s.get("smtp_port", "587"))) as smtp:
                smtp.starttls()
                smtp.login(s["smtp_user"], s["smtp_pass"])
                smtp.send_message(msg)
        except Exception:
            pass

    return FileResponse(tmp.name, filename="kpi_report.pdf", media_type="application/pdf")
