from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from llm import D_care_LLM
from llm_vectorstore import create_retriver
from app_router import router as chat_router
import app_state

from database import engine, Base
import models
from routers.auth import router as auth_router
from routers.health import router as health_router
from routers.glucose import router as glucose_router
from routers.predict import router as predict_router, load_models
from routers.chat_history import router as chat_history_router


#[스마트폰/실기기에서 어플 실행시]
#cd C:\Users\User\source\repos\D-care_01 이라고 입력 -> cd D-care_01 입력
# -> env-Dcare01\Scripts\activate.bat 입력후 
#uvicorn D_care_main:app --host 0.0.0.0 --port 8080 --reload

#[어플 실행후] ->ngrok http 8080 입력 -> 재실행 마다 안드로이드 스듀디오 에서 .env 파일의 API_BASE_URL ngrok 주소 변경할것

#[swagger_UI]에서 앱 기능 확인을 위해 서버 실행시 cmd창 열어서
#cd C:\Users\User\source\repos\D-care_01 이라고 입력 -> cd D-care_01 입력
# -> env-Dcare01\Scripts\activate.bat 입력후 
# uvicorn D_care_main:app --reload

#[만약, Medic INFO DB에 문제 발생시] main 파일 실행하기 전에 탐색기로 폴더 열기 들어가서  반드시 Medical_INFO_DB 폴더에 의료정보문서(index.faiss)와 피클파일(index.pkl)등이  존재하는지 확인 할것
#없으면 embedding.py 파일을 실행할것
# cd C:\Users\User\source\repos\D-care_01 이라고 입력 -> cd D-care_01 입력
#이후 가상환경 실행  -> env-Dcare01\Scripts\activate.bat 입력후 
#python embedding.py 입력

# 챗봇 기능 테스트 하기 
# 서버 실행후 http://localhost:8080/docs 접속
# POST / chat -> Try it out -> Request body에 {"question": "당뇨에 대해 설명해줘"}에서 원하는 질문 입력 -> Execute 클릭
#Swaager UI API 문서 기능 확인시 [주의]사항: 칼럼별 입력 자료중 bool형 자료형의 경우 [대문자 사용 금지], 소문자 true/false로 입력해야 정상적으로 작동함


#flutter SDK의 경로 C:\flutter\bin
#[참고] flutter SDK zip 폴더 해제 위치는 C:\
#D_care_pp 폴더경로 C:\D_care_app

#[앱 실행시 주의]안드로이드 스튜디오에서 Flutter 앱 실행전에항상 ipconfig 확인하고 "무선랜 WIFI"의 IPv4 주소 확인하기-> .env 파일의 형식은 http://<IPv4주소>:8080 이어야 한다.

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("서버 초기화 중...")
    print("LLM 초기화 중...")
    app_state.llm = D_care_LLM()
    print("LLM 연결 완료")

    print("RAG 파이프라인 초기화 중...")
    app_state.retriever = create_retriver()
    if app_state.retriever:
        print("RAG 파이프라인 연결 완료")
    else:
        print("RAG 파이프라인 연결 실패, 벡터스토어를 확인하세요")

    # 신규: DB 테이블 생성
    print("DB 테이블 확인 중....")
    Base.metadata.create_all(bind=engine)
    print("DB 테이블 확인 완료")

    load_models()

    print("서버 준비 완료")
    print("확인용 API문서: http://localhost:8080/docs")

    yield

    print("서버 종료 중...")

app = FastAPI(
    title = "D-care_bot API",
    description="당뇨 혈당 관리 LLM-RAG 챗봇",
    version="1.0.0",
    lifespan=lifespan,
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(glucose_router)
app.include_router(predict_router)
app.include_router(chat_history_router)