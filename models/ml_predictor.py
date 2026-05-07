"""
models/ml_predictor.py
Имитация Random Forest-классификатора для предсказания
класса эффекта AI-внедрения по 7 характеристикам.

Веса признаков и логика основаны на экспериментальной
части диссертации (Байтукенов Б.А., 2025).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict

# ─── Признаки ─────────────────────────────────────────────────────────────
FEATURES = [
    {"key": "digitalization",    "name": "Уровень цифровизации",         "importance": 0.21},
    {"key": "data_readiness",    "name": "Зрелость данных",               "importance": 0.19},
    {"key": "mgmt_support",      "name": "Поддержка руководства",         "importance": 0.18},
    {"key": "goal_clarity",      "name": "Чёткость бизнес-целей",         "importance": 0.16},
    {"key": "budget",            "name": "Бюджет проекта (норм.)",        "importance": 0.14},
    {"key": "company_size",      "name": "Размер компании",               "importance": 0.07},
    {"key": "industry_coeff",    "name": "Отраслевой коэффициент",        "importance": 0.05},
]
FEATURE_KEYS   = [f["key"] for f in FEATURES]
FEATURE_NAMES  = [f["name"] for f in FEATURES]
FEATURE_WEIGHTS = [f["importance"] for f in FEATURES]

# ─── Классы ───────────────────────────────────────────────────────────────
CLASS_HIGH = "Высокий эффект"
CLASS_MID  = "Средний эффект"
CLASS_LOW  = "Низкий эффект"

RECOMMENDATIONS = {
    CLASS_HIGH: [
        "Масштабируйте решение на новые бизнес-направления и регионы.",
        "Зафиксируйте метрики успеха для кейса внедрения.",
        "Рассмотрите интеграцию дополнительных AI-модулей.",
        "Инвестируйте в обучение команды для максимизации ROI.",
    ],
    CLASS_MID: [
        "Усильте процесс подготовки и качество данных (Data Readiness).",
        "Повысьте вовлечённость руководства — это ключевой фактор успеха.",
        "Уточните бизнес-цели и KPI до начала внедрения.",
        "Проведите пилотный запуск на одном бизнес-процессе.",
    ],
    CLASS_LOW: [
        "Пересмотрите готовность данных — это главное ограничение.",
        "Проведите аудит бизнес-процессов перед внедрением AI.",
        "Обеспечьте спонсорство на уровне C-suite для проекта.",
        "Начните с более простого и точечного AI-кейса (Quick Win).",
    ],
}


@dataclass
class PredictInput:
    digitalization: float   # [0, 1]
    data_readiness: float   # [0, 1]
    mgmt_support: float     # [0, 1]
    goal_clarity: float     # [0, 1]
    budget: float           # [0, 1]
    company_size: float     # [0, 1]
    industry_coeff: float   # [0, 1]

    def to_vector(self) -> List[float]:
        return [getattr(self, k) for k in FEATURE_KEYS]

    def validate(self) -> None:
        errs = []
        for k in FEATURE_KEYS:
            v = getattr(self, k)
            if not (0.0 <= v <= 1.0):
                errs.append(f"Признак '{k}' должен быть в [0,1], получено: {v}.")
        if errs: raise ValueError(" | ".join(errs))

    @staticmethod
    def from_dict(d: dict) -> "PredictInput":
        try:
            return PredictInput(**{k: float(d[k]) for k in FEATURE_KEYS})
        except KeyError as e:
            raise KeyError(f"Отсутствует признак: {e}")


@dataclass
class PredictResult:
    predicted_class: str
    prob_high: float
    prob_mid: float
    prob_low: float
    raw_score: float
    feature_importance: List[Dict]
    feature_contributions: List[Dict]
    recommendations: List[str]

    @property
    def probabilities(self) -> dict:
        return {CLASS_HIGH: round(self.prob_high,4),
                CLASS_MID:  round(self.prob_mid, 4),
                CLASS_LOW:  round(self.prob_low, 4)}

    def to_dict(self) -> dict:
        return {
            "predicted_class": self.predicted_class,
            "probabilities": self.probabilities,
            "raw_score": round(self.raw_score, 4),
            "feature_importance": self.feature_importance,
            "feature_contributions": self.feature_contributions,
            "recommendations": self.recommendations,
        }


def predict(inp: PredictInput) -> PredictResult:
    """
    Имитирует Random Forest: взвешенная сумма + interaction terms → вероятности.
    """
    inp.validate()
    vec = inp.to_vector()

    # Линейная комбинация (листья RF)
    score = sum(w * v for w, v in zip(FEATURE_WEIGHTS, vec))

    # Interaction terms (парные взаимодействия ключевых признаков)
    score += vec[0] * vec[1] * 0.15   # digitalization × data_readiness
    score += vec[2] * vec[3] * 0.12   # mgmt_support × goal_clarity
    score += vec[1] * vec[4] * 0.08   # data_readiness × budget
    raw = min(1.0, max(0.0, score))

    # Конвертация в вероятности трёх классов (softmax-like)
    if raw >= 0.72:
        pH = 0.55 + raw * 0.35;  pM = 1 - pH - 0.05; pL = 0.05
    elif raw >= 0.50:
        pM = 0.45 + raw * 0.40;  pH = (raw - 0.45) * 0.60; pL = 1 - pH - pM
    else:
        pL = 0.50 + (0.50 - raw) * 0.80; pM = 1 - pL - 0.05; pH = 0.05

    pL = max(0.0, min(1.0, pL))
    pM = max(0.0, min(1.0, pM))
    pH = max(0.0, min(1.0, pH))
    total = pL + pM + pH or 1.0
    pL /= total; pM /= total; pH /= total

    if   pH >= pM and pH >= pL: cls = CLASS_HIGH
    elif pM >= pL:               cls = CLASS_MID
    else:                        cls = CLASS_LOW

    feat_imp = [{"feature": FEATURE_NAMES[i], "importance": round(FEATURE_WEIGHTS[i], 4)}
                for i in range(len(FEATURES))]
    feat_imp.sort(key=lambda x: x["importance"], reverse=True)

    feat_contrib = [{"feature": FEATURE_NAMES[i],
                     "value": round(vec[i], 4),
                     "contribution": round(FEATURE_WEIGHTS[i] * vec[i], 4)}
                    for i in range(len(FEATURES))]
    feat_contrib.sort(key=lambda x: x["contribution"], reverse=True)

    return PredictResult(
        predicted_class=cls,
        prob_high=round(pH, 4), prob_mid=round(pM, 4), prob_low=round(pL, 4),
        raw_score=round(raw, 4),
        feature_importance=feat_imp,
        feature_contributions=feat_contrib,
        recommendations=RECOMMENDATIONS[cls],
    )
