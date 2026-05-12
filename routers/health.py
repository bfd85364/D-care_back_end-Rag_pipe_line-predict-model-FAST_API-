# routers/health.py — 건강 프로필 라우터
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud, schemas
from database import get_db

router = APIRouter(prefix="/api/health", tags=["건강 프로필"])


@router.get("/{user_id}", response_model=schemas.HealthProfileResponse)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    profile = crud.get_health_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="건강 프로필이 없습니다")
    return profile


@router.post("/{user_id}", response_model=schemas.HealthProfileResponse)
def save_profile(
    user_id: int,
    body: schemas.HealthProfileCreate,
    db: Session = Depends(get_db),
):
    """건강 프로필 생성 또는 수정 (upsert)"""
    return crud.create_or_update_health_profile(db, user_id, body)
