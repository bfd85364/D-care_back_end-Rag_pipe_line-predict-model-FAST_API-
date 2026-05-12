# routers/auth.py
# 로그인 / 회원가입 JWT 발급

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/api/auth", tags=["인증"])

# 설정
SECRET_KEY = os.getenv("SECRET_KEY", "dcare-secret-key-change-in-production")
ALGORITHM  = "HS256" # JWT 서명 알고리즘(암호화)
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7일

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


#JWT 토큰 생성
def create_access_token(user_id: int, name: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub":  str(user_id),
        "name": name,
        "exp":  expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# JWT 토큰 검증
def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="인증이 만료되었습니다")


# 현재 사용자 가져오기 (의존성 주입용)
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    payload = verify_token(token)
    user_id = int(payload.get("sub"))
    user    = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")
    return user


# 회원가입 
@router.post("/register", response_model=schemas.TokenResponse)
def register(body: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, body.email):
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다")
    user  = crud.create_user(db, body)
    token = create_access_token(user.id, user.name)
    return schemas.TokenResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
    )


#로그인
@router.post("/login", response_model=schemas.TokenResponse)
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, body.email)
    if not user or not crud.verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다"
        )
    token = create_access_token(user.id, user.name)
    return schemas.TokenResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
    )


#토큰 유효성 확인
@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "name":    current_user.name,
        "email":   current_user.email,
    }