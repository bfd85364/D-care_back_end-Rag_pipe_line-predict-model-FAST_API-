# create_db.py
#cd C:\Users\User\source\repos\D-care_01 이라고 입력 -> cd D-care_01 입력
# -> env-Dcare01\Scripts\activate.bat 입력후 
# 최초 1회 실행하여 diabetes.db 생성
# 실행: python create_db.py
# deabetse.db 경로 --> "C:\Users\User\source\repos\D-care_01\D-care_01\diabetes.db"
#[주의]: DB browserfor SQLite로 diabetes.db 파일을 열 때, "C:\Users\User\source\repos\D-care_01\D-care_01" 경로로 열어야 diabetes.db 파일을 확인 가능함 

from database import engine, Base
import models

def create_tables():
    print("DB 테이블 생성 중...")
    Base.metadata.create_all(bind=engine)
    print("diabetes.db 생성 완료")
    print("\n생성된 테이블:")
    for table in Base.metadata.tables.keys():
        print(f"  - {table}")

if __name__ == "__main__":
    create_tables()
