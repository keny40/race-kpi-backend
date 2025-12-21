from fastapi import APIRouter
from backend.routes.runtime import RUNTIME

router = APIRouter()
MATRIX = {}  # {(model,preset): {pred,hit}}

def record(model, preset, hit):
    key=(model,preset)
    if key not in MATRIX:
        MATRIX[key]={"pred":0,"hit":0}
    MATRIX[key]["pred"]+=1
    if hit: MATRIX[key]["hit"]+=1

@router.get("/optimizer/best")
def best():
    best=None; best_rate=0
    for (m,p),v in MATRIX.items():
        if v["pred"]<20: continue
        r=v["hit"]/v["pred"]
        if r>best_rate:
            best_rate=r; best={"model":m,"preset":p,"rate":r}
    return best or {}

@router.post("/optimizer/fix")
def fix_best():
    b=best()
    if not b: return {"ok":False}
    RUNTIME["locked"]=True
    RUNTIME["fixed_combo"]=b
    return {"ok":True,"fixed":b}
