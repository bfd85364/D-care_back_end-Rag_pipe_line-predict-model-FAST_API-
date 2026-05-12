from pydantic import BaseModel
#해당 파일은 어플리케이션의 회원가입폼에서 수집한 사용자의 건강 정보 데이터를 처리하기 위한 스키마임

class UserHealth(BaseModel):
    name: str = "사용자"
    age: int | None = None
    gender: str | None = None # 성별 
    height: float | None = None # 신장 
    weight: float | None = None # 체중
    waist_circumference: float | None = None # 허리둘레
    hypertension: bool | None = None # 고혈압 여부 (있음: True, 없음: False)
    dyslipidemia: bool | None = None # 이상지질혈증 여부 (있음: True, 없음: False)
    smoking: bool | None = None # 흡연 여부 (흡연자: True, 비흡연자: False)
    smoking_amount: int | None = None # 하루 흡연량 (개비 수)
    drinking_frequencys: int | None = None # 음주 빈도 (주당 횟수)
    drinking_amount: int | None = None # 1회 음주량 (잔 수)   
    vigorous_exercise: bool | None = None # 격렬한 운동 여부 (함: True, 안함: False)s
    vigorous_exercise_days: int | None = None # 격렬한 운동 일수 (주당 일수)
    vigorous_exercise_hours: float | None = None # 격렬한 운동 시간 (하루 시간)
    moderate_exercise: bool | None = None # 적당한 운동 여부 (함: True, 안함: False)
    moderate_exercise_days: int | None = None # 적당한 운동 일수 (주당 일수)
    moderate_exercise_hours: float | None = None # 적당한 운동 시간 (하루 시간)
    aerobic_exercise: bool | None = None # 유산소 운동 여부 (함: True, 안함: False)
    #breakfast: int | None = None # 아침 식사 여부 (주당 횟수)
    #lunch: int | None = None # 점심 식사 여부 (주당 횟수)
    #dinner: int | None = None # 저녁 식사 여부 (주당 횟수)
    #calorie_intake: float | None = None # 하루 총 섭취 칼로리 (kcal/일)
    #carbohydrate_intake: float | None = None # 하루 탄수화물 섭취량 (g/일)
    #sugar_intake: float | None = None # 하루 당 섭취량 (g/일)
    #fasting_glucose: float | None = None # 공복 혈당 수치
    diabetes_father: bool | None = None # 당뇨_가족력(부) (있음: True, 없음: False)
    diabetes_mother: bool | None = None # 당뇨_가족력(모) (있음: True, 없음: False)
    diabetes_siblings: bool | None = None # 당뇨_가족력(형제자매) (있음: True, 없음: False)
    hba1c: float | None = None # 당화혈색소 수치

class ChatRequest(BaseModel):
    question: str
    user_helth: UserHealth | None = None
    user_id: int | None = None # 대화 저장
    session_id: int | None = None # 이어서 대화용

class ChatResponse(BaseModel):
    answer: str
    rag_used: bool
    session_id: int | None = None # 생성된 세션 ID 반환 
    

