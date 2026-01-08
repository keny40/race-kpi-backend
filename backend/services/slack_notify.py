import requests
import os

def notify_slack(candidates):
    if not candidates:
        return

    msg = "📌 오늘 RUN 후보\n"
    for c in candidates:
        msg += f"- R{c['race_no']} (rough {c['rough_conf']})\n"

    requests.post(
        os.environ["SLACK_WEBHOOK"],
        json={"text": msg}
    )
