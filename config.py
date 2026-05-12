import os 
from pathlib import Path
from dotenv import load_dotenv
#config.py는 OPEMAI API 키와 #LLM 모델 설정, 데이터 파일 경로,임베딩 모델,
# 챗봇 서버 호스트 및 포트 번호 등의 설정을 관리하는 모듈입니다. 
#.env 파일에서 OR_API_KEY를 로드하여 LLM 모델과 챗봇 서버 설정에 사용합니다.

load_dotenv()

OR_API_KEY = os.getenv("OR_API_KEY")
LLM_MODEL = "openrouter/free"

LLM_IGNORE_PROVIDERS =[
    "DeepSeek",
    "DeepInfra",
    "Novita",
    "Chutes",]

DATA_FILES: list[str] = [
    "data/deabets.pdf", "data/collum.csv", "data/collum_explain.csv", "data/dyslipidemia.pdf", "data/for_old_age.pdf"]

BASE_DIR = Path(__file__).parent.resolve()
FAISS_DB_PATH = str(BASE_DIR/"Medic_INFO_DB")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80
RETRIVER_TOP_K =3

HOST = "0.0.0.0"
PORT = 8080
