# routers/predict.py
# LightGBM + SHAP 연동 /predict 엔드포인트

import json
import numpy as np
import pandas as pd
import lightgbm as lgb
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path

router = APIRouter(prefix="/api", tags=["위험군 예측"])

MODEL_DIR  = Path("outputs")
SAMPLE_DIR = Path(".")

_base_model = None
_full_model  = None
_meta        = None
_shap_base   = None
_shap_full   = None


def load_models():
    global _base_model, _full_model, _meta, _shap_base, _shap_full
    try:
        _base_model = lgb.Booster(model_file=str(MODEL_DIR / "lgbm_base.txt"))
        _full_model  = lgb.Booster(model_file=str(MODEL_DIR / "lgbm_full.txt"))
        with open(MODEL_DIR / "model_meta.json", encoding="utf-8") as f:
            _meta = json.load(f)
        print("LightGBM 모델 로드 완료")
        try:
            import shap
            base_sample = pd.read_csv(SAMPLE_DIR / "x_train_sample_base.csv")
            full_sample = pd.read_csv(SAMPLE_DIR / "x_train_sample_full.csv")
            _shap_base = shap.TreeExplainer(_base_model, base_sample)
            _shap_full = shap.TreeExplainer(_full_model, full_sample)
            print("SHAP Explainer 초기화 완료")
        except Exception as e:
            print(f"SHAP 초기화 실패: {e}")
    except Exception as e:
        print(f"모델 로드 실패: {e}")


LABEL_MAP    = {"0": "정상", "1": "당뇨 전단계", "2": "당뇨"}
LABEL_MAP_EN = {"0": "Normal", "1": "Pre-diabetes", "2": "Diabetes"}

VAR_KOR = {
    "age": "나이", "sex": "성별", "HE_ht": "신장", "HE_wt": "체중",
    "HE_wc": "허리둘레", "BMI": "BMI", "waist_height_ratio": "허리-신장 비율",
    "DI1_dg": "고혈압 진단", "DI2_dg": "이상지질혈증", "HE_HP": "고혈압 여부",
    "BS1_1": "흡연 여부", "BS3_1": "흡연량", "smoking_status": "흡연 상태",
    "BD1_11": "음주 빈도", "BD2_1": "1회 음주량", "alcohol_risk_score": "음주 위험도",
    "BE3_71": "격렬 활동", "BE3_81": "중등도 활동", "pa_aerobic": "유산소 실천",
    "total_MET_min_week": "주간 운동량", "L_BR_FQ": "아침 빈도",
    "L_LN_FQ": "점심 빈도", "L_DN_FQ": "저녁 빈도", "meal_regularity": "식사 규칙성",
    "N_EN": "하루 칼로리", "N_CHO": "탄수화물", "N_SUGAR": "당류",
    "HE_DMfh1": "부 가족력", "HE_DMfh2": "모 가족력", "HE_DMfh3": "형제자매 가족력",
    "family_dm_count": "가족력 합산", "HE_HbA1c": "당화혈색소",
    "HE_sbp": "수축기혈압", "HE_dbp": "이완기혈압", "HE_chol": "총콜레스테롤",
    "HE_TG": "중성지방", "HE_HDL_st2": "HDL", "HE_anem": "빈혈",
}


class PredictRequest(BaseModel):
    age:    int   = Field(..., ge=19, le=100)
    sex:    int   = Field(..., ge=1,  le=2)
    HE_ht:  float = Field(..., ge=100, le=220)
    HE_wt:  float = Field(..., ge=20,  le=200)
    HE_wc:  Optional[float] = None
    DI1_dg: Optional[int]   = None
    DI2_dg: Optional[int]   = None
    HE_HP:  Optional[int]   = None
    BS1_1:  Optional[int]   = None
    BS3_1:  Optional[int]   = None
    BD1_11: Optional[float] = None
    BD2_1:  Optional[float] = None
    BE3_71: Optional[int]   = None
    BE3_81: Optional[int]   = None
    pa_aerobic: Optional[int] = None
    L_BR_FQ: Optional[float] = None
    L_LN_FQ: Optional[float] = None
    L_DN_FQ: Optional[float] = None
    N_EN:    Optional[float] = None
    N_CHO:   Optional[float] = None
    N_SUGAR: Optional[float] = None
    HE_DMfh1: Optional[int] = None
    HE_DMfh2: Optional[int] = None
    HE_DMfh3: Optional[int] = None
    HE_HbA1c:   Optional[float] = None
    HE_sbp:     Optional[float] = None
    HE_dbp:     Optional[float] = None
    HE_chol:    Optional[float] = None
    HE_TG:      Optional[float] = None
    HE_HDL_st2: Optional[float] = None
    HE_anem:    Optional[int]   = None
    fasting_glucose: Optional[float] = None


class PredictResponse(BaseModel):
    predicted_class: int
    label_ko:        str
    label_en:        str
    model_used:      str
    probabilities:   dict
    risk_detail:     Optional[str]  = None
    shap_feedback:   Optional[list] = None


def compute_derived(req: PredictRequest) -> dict:
    d = req.dict()
    if req.HE_ht and req.HE_wt:
        bmi = req.HE_wt / (req.HE_ht / 100) ** 2
        d["BMI"] = round(bmi, 1) if 10 <= bmi <= 80 else np.nan
    else:
        d["BMI"] = np.nan
    if req.HE_wc and req.HE_ht:
        whr = req.HE_wc / req.HE_ht
        d["waist_height_ratio"] = round(whr, 3) if 0.3 <= whr <= 1.0 else np.nan
    else:
        d["waist_height_ratio"] = np.nan
    bs1 = req.BS1_1
    if bs1 is None:       d["smoking_status"] = np.nan
    elif bs1 == 2:        d["smoking_status"] = 0
    elif req.BS3_1 == 1:  d["smoking_status"] = 2
    else:                 d["smoking_status"] = 1
    d["alcohol_risk_score"] = (req.BD1_11 or 0) * (req.BD2_1 or 0)
    d["total_MET_min_week"] = 1500 if req.pa_aerobic == 1 else 0
    fam = [req.HE_DMfh1, req.HE_DMfh2, req.HE_DMfh3]
    d["family_dm_count"] = sum(1 for v in fam if v == 1)
    meals = [req.L_BR_FQ, req.L_LN_FQ, req.L_DN_FQ]
    valid = [v for v in meals if v is not None]
    d["meal_regularity"] = np.mean(valid) if valid else np.nan
    return d


def evaluate_goal(fasting_glucose):
    if fasting_glucose is None: return None
    if fasting_glucose <= 130:  return "저위험 (80~130 mg/dL)"
    if fasting_glucose <= 179:  return "중위험 (131~179 mg/dL)"
    return "고위험 (≥180 mg/dL)"


def get_shap_feedback(X, explainer, predicted_class, top_n=5):
    try:
        import shap
        shap_values = explainer.shap_values(X)
        sv = shap_values[predicted_class][0] if isinstance(shap_values, list) else shap_values[0]
        indices = np.argsort(np.abs(sv))[::-1][:top_n]
        return [{
            "variable":  X.columns[i],
            "label":     VAR_KOR.get(X.columns[i], X.columns[i]),
            "value":     round(float(X.iloc[0, i]), 2) if not np.isnan(float(X.iloc[0, i])) else None,
            "shap":      round(float(sv[i]), 4),
            "direction": "위험 증가" if sv[i] > 0 else "위험 감소",
        } for i in indices]
    except Exception as e:
        print(f"SHAP 계산 실패: {e}")
        return []


@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    if _base_model is None or _meta is None:
        raise HTTPException(status_code=503, detail="모델이 로드되지 않았습니다")
    d          = compute_derived(req)
    layer_b    = _meta["features"]["layer_b"]
    has_b      = any(req.dict().get(k) is not None for k in layer_b)
    features   = _meta["features"]["full_features" if has_b else "base_features"]
    model      = _full_model if has_b else _base_model
    explainer  = _shap_full  if has_b else _shap_base
    model_used = "full" if has_b else "base"
    X    = pd.DataFrame([{col: d.get(col, np.nan) for col in features}])
    prob = model.predict(X)[0]
    cls  = int(np.argmax(prob))
    shap_feedback = get_shap_feedback(X, explainer, cls) if explainer else []
    return PredictResponse(
        predicted_class = cls,
        label_ko        = LABEL_MAP[str(cls)],
        label_en        = LABEL_MAP_EN[str(cls)],
        model_used      = model_used,
        probabilities   = {LABEL_MAP_EN[str(i)]: round(float(prob[i]), 4) for i in range(3)},
        risk_detail     = evaluate_goal(req.fasting_glucose),
        shap_feedback   = shap_feedback if shap_feedback else None,
    )