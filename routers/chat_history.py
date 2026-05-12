#chat history 라우터 
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud
from database import get_db

router = APIRouter(prefix="/api", tags=["채팅 기록"])

@router.get("/sessions/{user_id}")
def get_sessions(
    user_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """사용자 대화 세션 목록"""
    return crud.get_chat_sessions(db, user_id, limit)

@router.get("/messages/{session_id}")
def get_messages(
    session_id: int,
    db: Session = Depends(get_db),
 ):
    """전체 세션 메시지 조회"""
    msgs = crud.get_chat_messages(db, session_id)
    return [
        {
            "id": m.id,
            "role": m.sender,
            "content": m.content,
            "timestamp": m.timestamp.isoformat(),
        }
        for m in msgs
    ]

@router.get("/summary/{user_id}")
def get_summary(
    user_id: int,
    db: Session = Depends(get_db),
):
    """대시보드: 사용자 대화 요약 조회"""
    return crud.get_recent_chat_summary(db, user_id)

@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    """대화 세션 삭제"""
    success = crud.delete_chat_session(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return {"detail": "세션이 삭제되었습니다."}