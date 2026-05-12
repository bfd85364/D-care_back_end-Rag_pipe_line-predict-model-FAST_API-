# crud.py - 계정, 조회, 수정, 삭제 기능 구현
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from passlib.context import CryptContext
import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 1. 사용자
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(
        models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(
        models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed = pwd_context.hash(user.password)
    db_user = models.User(
        email=user.email,
        name=user.name,
        hashed_password=hashed,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def delete_user(db: Session, user_id: int) -> bool:
    user = get_user(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


# 2. 건강 프로필
def get_health_profile(db: Session, user_id: int):
    return db.query(models.HealthProfile).filter(
        models.HealthProfile.user_id == user_id).first()

def create_or_update_health_profile(
    db: Session,
    user_id: int,
    data: schemas.HealthProfileCreate,
):
    # BMI 자동 계산
    bmi = round(data.weight_kg / (data.height_cm / 100) ** 2, 1)

    existing = get_health_profile(db, user_id)
    if existing:
        # 수정
        for k, v in data.dict().items():
            setattr(existing, k, v)
        existing.bmi = bmi
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # 신규 생성
        profile = models.HealthProfile(
            user_id=user_id,
            bmi=bmi,
            **data.dict(),
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

def save_risk_result(
    db: Session,
    user_id: int,
    label: str,
    prob: float,
):
    """ML 예측 결과를 health_profiles에 저장"""
    profile = get_health_profile(db, user_id)
    if profile:
        profile.last_risk_label    = label
        profile.last_risk_prob     = prob
        profile.last_predicted_at  = datetime.now()
        db.commit()


# 3. 혈당 기록
def _status(glucose: float, m_type: str) -> str:
    if m_type == "공복":
        if glucose < 100: return "정상"
        if glucose < 126: return "주의"
        return "위험"
    else:
        if glucose < 140: return "정상"
        if glucose < 200: return "주의"
        return "위험"

def create_glucose_record(
    db: Session,
    user_id: int,
    data: schemas.GlucoseRecordCreate,
):
    record = models.GlucoseRecord(user_id=user_id, **data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_glucose_records(
    db: Session,
    user_id: int,
    days: int = 30,
):
    since = datetime.now() - timedelta(days=days)
    return (
        db.query(models.GlucoseRecord)
        .filter(
            models.GlucoseRecord.user_id == user_id,
            models.GlucoseRecord.measured_at >= since,
        )
        .order_by(desc(models.GlucoseRecord.measured_at))
        .all()
    )

def delete_glucose_record(db: Session, record_id: int) -> bool:
    r = db.query(models.GlucoseRecord).filter(
        models.GlucoseRecord.id == record_id).first()
    if not r:
        return False
    db.delete(r)
    db.commit()
    return True

def get_glucose_stats(db: Session, user_id: int, days: int = 7):
    since = datetime.now() - timedelta(days=days)
    result = db.query(
        func.avg(models.GlucoseRecord.glucose).label("avg"),
        func.max(models.GlucoseRecord.glucose).label("max"),
        func.min(models.GlucoseRecord.glucose).label("min"),
        func.count(models.GlucoseRecord.id).label("count"),
    ).filter(
        models.GlucoseRecord.user_id == user_id,
        models.GlucoseRecord.measured_at >= since,
    ).first()
    return {
        "avg":   round(result.avg or 0, 1),
        "max":   result.max or 0,
        "min":   result.min or 0,
        "count": result.count or 0,
    }

def get_sidebar_records(db: Session, user_id: int, days: int = 30):
    """Drawer 사이드바용 날짜별 그룹 조회"""
    from collections import defaultdict
    from datetime import date

    records = get_glucose_records(db, user_id, days)
    today   = date.today()
    grouped = defaultdict(list)

    for r in records:
        grouped[r.measured_at.date()].append(r)

    result = []
    for d in sorted(grouped.keys(), reverse=True):
        day_records = grouped[d]
        delta = (today - d).days
        if delta == 0:   label = "오늘"
        elif delta == 1: label = "어제"
        else:            label = f"{d.month}월 {d.day}일"

        avg = sum(r.glucose for r in day_records) / len(day_records)
        result.append({
            "date":        str(d),
            "label":       label,
            "avg_glucose": round(avg, 1),
            "records": [
                {
                    "id":               r.id,
                    "glucose":          r.glucose,
                    "measurement_type": r.measurement_type.value,
                    "measured_at":      r.measured_at.isoformat(),
                    "status":           _status(r.glucose, r.measurement_type.value),
                    "memo":             r.memo,
                }
                for r in day_records
            ],
        })
    return result

#4, 대화 세션 
def create_chat_session(
    db: Session,
    user_id: int,
    first_question: str,
    ) -> models.ChatSession:
    """새 대화 세션 생성 (첫 질문 포함)"""
    title = first_question[:30] + "..." if len(first_question) > 30 else first_question
    session = models.ChatSession(user_id=user_id, title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_chat_sessions(
    db: Session,
    user_id: int,
    limit: int = 20,
    ) -> list:
        """사용자의 모든 대화 세션 조회 (최신순)"""
        return (
            db.query(models.ChatSession)
            .filter(models.ChatSession.user_id == user_id)
            .order_by(desc(models.ChatSession.updated_at.nullslast(), models.ChatSession.created_at))
            .limit(limit)
            .all()
        )

def save_chat_message(
    db: Session,
    session_id: int,
    sender: str,
    message: str,
) -> models.ChatMessage:
    """대화 메시지 저장"""
    msg= models.ChatMessage(
        session_id=session_id,
        sender=sender,
        message=message,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def get_recent_chat_summary(
    db: Session,
    user_id: int,
    limit: int = 5,
    ) -> list:
    """최근 대화 세션들의 요약 정보 반환 (대화 제목, 마지막 메시지, 마지막 업데이트 시간)"""
    sessions = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.user_id == user_id)
        .order_by(desc(models.ChatSession.created_at))
        .limit(limit)
        .all()
    )
    result = [ ]
    for s in sessions:
        last_msg = (
            db.query(models.ChatMessage)
            .filter(models.ChatMessage.session_id == s.id,
                    models.ChatMessage.role == "assistant")
            .order_by(desc(models.ChatMessage.created_at))
            .first()
        )
        result.append({
            "session_id": s.id,
            "title": s.title,
            "created_at": s.created_at.isoformat(),
            "last_answer": last_msg.content[:80] + "..." if last_msg and len(last_msg.content)>80 else (last_msg.content if last_msg else ""),
            })