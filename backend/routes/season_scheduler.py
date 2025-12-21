from backend.routes.pdf_reports import generate_executive_pdf
from backend.routes.season_notify import upload_pdf_to_slack

def _commit(reason: str):
    payload = {
        "reason": reason,
        "runtime_state": RUNTIME,
        "matrix": MATRIX,
        "meta_state": META
    }

    result = commit_season(payload)
    do_carry(payload["meta_state"])

    now = datetime.utcnow()
    # 경영진 요약 PDF
    exec_pdf = generate_executive_pdf(
        period="month",
        year=now.year,
        month=now.month
    )

    upload_pdf_to_slack(exec_pdf, title="📊 Executive Summary")

    return result
