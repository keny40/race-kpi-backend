from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.auth_utils import create_fake_token

router = APIRouter(prefix="/auth", tags=["Auth"])

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

users_db = {}  # email -> {id, name, password}

@router.post("/signup")
def signup(data: SignupRequest):
    if data.email in users_db:
        raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다.")
    user_id = len(users_db) + 1
    users_db[data.email] = {"id": user_id, "name": data.name, "password": data.password}
    return {"message": "회원가입이 완료되었습니다. 관리자 승인 대기 중입니다."}

@router.post("/login")
def login(data: LoginRequest):
    user = users_db.get(data.email)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    token = create_fake_token(user["id"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user["id"], "name": user["name"], "email": data.email},
    }