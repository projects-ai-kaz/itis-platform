"""models/itis.py — Ядро расчёта AI Impact Score."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

THRESHOLD_LOW  = 0.45
THRESHOLD_HIGH = 0.70
CLASS_LOW  = "Низкая эффективность"
CLASS_MID  = "Средняя эффективность"
CLASS_HIGH = "Высокая эффективность"
RECOMMENDATIONS = {
    CLASS_LOW:  "Требуется пересмотр стратегии и архитектуры внедрения AI-решения.",
    CLASS_MID:  "Необходима доработка слабых модулей (параметры E, C или M).",
    CLASS_HIGH: "Рекомендуется масштабирование решения на новые бизнес-направления.",
}


def classify(value: float) -> str:
    if value < THRESHOLD_LOW:  return CLASS_LOW
    if value < THRESHOLD_HIGH: return CLASS_MID
    return CLASS_HIGH


@dataclass
class Module:
    name: str
    E: float
    W: float
    C: float
    M: float

    def validate(self) -> None:
        errs = []
        if not self.name or not self.name.strip():
            errs.append("Название модуля не может быть пустым.")
        for p, v in [("E", self.E), ("C", self.C), ("M", self.M)]:
            if not (0.0 <= v <= 1.0):
                errs.append(f"Параметр {p} должен быть в [0,1], получено: {v}.")
        if self.W <= 0:
            errs.append(f"Вес W должен быть > 0, получено: {self.W}.")
        if errs: raise ValueError(" | ".join(errs))

    @property
    def itis_i(self) -> float:
        return (self.E * self.C * self.M) ** (1 / 3)

    @property
    def efficiency_class(self) -> str:
        return classify(self.itis_i)

    def to_dict(self) -> dict:
        return {"name": self.name, "E": round(self.E, 4), "W": round(self.W, 4),
                "C": round(self.C, 4), "M": round(self.M, 4),
                "itis_i": round(self.itis_i, 4), "efficiency_class": self.efficiency_class}

    @staticmethod
    def from_dict(d: dict) -> "Module":
        return Module(name=d["name"], E=float(d["E"]), W=float(d["W"]),
                      C=float(d["C"]), M=float(d["M"]))


@dataclass
class ITISResult:
    modules: List[Module]
    total_itis: float
    w_sum: float
    efficiency_class: str
    recommendation: str
    best_module: str
    worst_module: str
    contributions: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"total_itis": round(self.total_itis, 4), "w_sum": round(self.w_sum, 4),
                "efficiency_class": self.efficiency_class, "recommendation": self.recommendation,
                "best_module": self.best_module, "worst_module": self.worst_module,
                "modules": [m.to_dict() for m in self.modules],
                "contributions": self.contributions}


def calculate(modules: List[Module]) -> ITISResult:
    if not modules: raise ValueError("Список модулей не может быть пустым.")
    for m in modules: m.validate()
    w_sum = sum(m.W for m in modules)
    total = round(sum((m.W / w_sum) * m.itis_i for m in modules), 6)
    by_itis = sorted(modules, key=lambda m: m.itis_i)
    contribs = [{"name": m.name,
                  "contribution": round((m.W / w_sum) * m.itis_i, 4),
                  "share_pct": round((m.W / w_sum) * m.itis_i / total * 100, 2) if total > 0 else 0}
                for m in modules]
    return ITISResult(
        modules=modules, total_itis=total, w_sum=w_sum,
        efficiency_class=classify(total),
        recommendation=RECOMMENDATIONS[classify(total)],
        best_module=f"{by_itis[-1].name} ({by_itis[-1].itis_i:.3f})",
        worst_module=f"{by_itis[0].name} ({by_itis[0].itis_i:.3f})",
        contributions=contribs)
