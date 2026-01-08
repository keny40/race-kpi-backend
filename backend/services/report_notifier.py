from __future__ import annotations
import os, requests

def send_report(report: dict):
    url = os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        return

    def fmt(x):
        return "-" if x is None else f"{x*100:.1f}%"

    text = (
        f"*📊 운영 리포트 ({report['period_days']}일)*\n"
        f"- 전체 샘플: {report['total_samples']}\n"
        f"- HIT/MISS: {report['hit']} / {report['miss']} (HR {fmt(report['hit_rate'])})\n"
        f"- 고신뢰(conf≥0.65): {report['hi_conf_hit']} / {report['hi_conf_miss']} "
        f"(HR {fmt(report['hi_conf_hit_rate'])})"
    )

    try:
        requests.post(url, json={"text": text}, timeout=5)
    except Exception:
        pass
