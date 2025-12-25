from fastapi import APIRouter
from pydantic import BaseModel
from backend.db.conn import get_conn

router = APIRouter(prefix="/api/kpi", tags=["kpi"])

class Threshold(BaseModel):
    warn: float
    fail: float

@router.get("/threshold")
def get_threshold():
    con = get_conn()
    cur = con.cursor()
    cur.execute("SELECT warn, fail FROM kpi_threshold WHERE id=1")
    row = cur.fetchone()
    con.close()

    if not row:
        return {"warn": 0.55, "fail": 0.45}
    return {"warn": float(row[0]), "fail": float(row[1])}

@router.post("/threshold")
def set_threshold(t: Threshold):
    warn = float(t.warn)
    fail = float(t.fail)

    if not (0.0 <= warn <= 1.0 and 0.0 <= fail <= 1.0):
        return {"status": "error", "message": "warn/fail must be between 0 and 1"}

    if fail > warn:
        return {"status": "error", "message": "fail must be <= warn"}

    con = get_conn()
    cur = con.cursor()
    cur.execute("UPDATE kpi_threshold SET warn=?, fail=? WHERE id=1", (warn, fail))
    con.commit()
    con.close()

    return {"status": "ok", "warn": warn, "fail": fail}
