from fastapi import APIRouter

router = APIRouter()

META = {
    "ewma_alpha": 0.12,
    "carry_over": True,      # ⭐ 시즌 간 승계 여부
    "combo": {},
    "recommendation": None
}

def carry_over(prev_meta: dict):
    if META["carry_over"]:
        META["combo"] = prev_meta.get("combo", {}).copy()
        META["recommendation"] = prev_meta.get("recommendation")

@router.post("/meta/carry-over")
def do_carry(payload: dict):
    carry_over(payload)
    return {"ok": True}
