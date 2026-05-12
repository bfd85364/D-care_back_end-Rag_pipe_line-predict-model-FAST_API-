# routers/glucose.py — 혈당 기록 라우터
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud, schemas
from database import get_db

router = APIRouter(prefix="/api/glucose", tags=["혈당 기록"])


@router.post("/{user_id}", response_model=schemas.GlucoseRecordResponse)
def create_record(
    user_id: int,
    body: schemas.GlucoseRecordCreate,
    db: Session = Depends(get_db),
):
    record = crud.create_glucose_record(db, user_id, body)
    return {
        **record.__dict__,
        "measurement_type": record.measurement_type.value,
        "status": crud._status(record.glucose, record.measurement_type.value),
    }


@router.get("/sidebar/{user_id}")
def get_sidebar(
    user_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
):
    return crud.get_sidebar_records(db, user_id, days)


@router.get("/{user_id}/stats")
def get_stats(
    user_id: int,
    days: int = 7,
    db: Session = Depends(get_db),
):
    return crud.get_glucose_stats(db, user_id, days)


@router.delete("/record/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    if not crud.delete_glucose_record(db, record_id):
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다")
    return {"message": "삭제되었습니다"}
