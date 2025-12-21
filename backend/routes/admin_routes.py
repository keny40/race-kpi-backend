from fastapi import APIRouter
from typing import List
from pydantic import BaseModel
from routes.auth_routes import users_db

router = APIRouter(prefix="/admin", tags=["Admin"])

approved_users = set()

class PendingUser(BaseModel):
    id: int
    name: str
    email: str

class ApproveRequest(BaseModel):
    user_id: int

@router.get("/pending", response_model=List[PendingUser])
def get_pending_users():
    result = []
    for email, u in users_db.items():
        if u["id"] not in approved_users:
            result.append(PendingUser(id=u["id"], name=u["name"], email=email))
    return result

@router.post("/approve")
def approve_user(req: ApproveRequest):
    approved_users.add(req.user_id)
    return {"message": f"유저 {req.user_id}가 승인되었습니다."}