from fastapi import APIRouter, HTTPException, Depends
from app_schemas import ChatRequest, ChatResponse
from sqlalchemy.orm import Session
from llm_service import run_chat
from database import get_db
import app_state
import crud
import traceback

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    if app_state.llm is None:
        raise HTTPException(
            status_code=503, 
            detail="LLM이 초기화되지 않았습니다.",
        )
    try:
        response = run_chat(
            llm=app_state.llm,
            retriever=app_state.retriever,
            question=request.question,
            user_health=request.user_helth,
        )

        # DB에 대화 기록 저장
        if request.user_id:
            try:
                if not request.session_id:
                    session = crud.create_session(
                        db, 
                        user_id=request.user_id,
                        first_question=request.question,
                    )
                    session_id = session.id
                else:
                    session_id = request.session_id

                    #사용자 메시지 저장 
                    crud.save_chat_message(
                        db, 
                        session_id=session_id,
                        sender="user",
                        content=request.question,
                        rag_used=False,
                    )
                    # 봇 답변 저장
                    crud.save_chat_message(
                        db, 
                        session_id=session_id,
                        role="assistant",
                        content=response.answer,
                        rag_used=response.rag_used,
                    )
                    return ChatResponse(
                        answer=response.answer,
                        rag_used=response.rag_used,
                        session_id=session_id,
                    )
            except Exception as db_err:
                print(f"[DB 저장 오류]: {db_err}")
        return response

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"챗봇 응답 생성 중 오류가 발생 :{e}",
        )

