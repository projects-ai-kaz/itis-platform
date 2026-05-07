"""models/bak.py — Модель БАК-матрицы (Бизнес-цель → AI-модуль → KPI)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Set


@dataclass
class Goal:
    id: int
    name: str
    kpi: str = "—"

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "kpi": self.kpi}


@dataclass
class BakModule:
    id: int
    name: str

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}


@dataclass
class BakMatrix:
    goals: List[Goal] = field(default_factory=list)
    modules: List[BakModule] = field(default_factory=list)
    # covered: set of (goal_id, module_id)
    covered: Set[tuple] = field(default_factory=set)

    def toggle(self, goal_id: int, module_id: int) -> bool:
        """Toggle coverage. Returns new state (True=covered)."""
        pair = (goal_id, module_id)
        if pair in self.covered:
            self.covered.discard(pair)
            return False
        self.covered.add(pair)
        return True

    def set_cell(self, goal_id: int, module_id: int, value: bool) -> None:
        pair = (goal_id, module_id)
        if value: self.covered.add(pair)
        else:      self.covered.discard(pair)

    def is_covered(self, goal_id: int, module_id: int) -> bool:
        return (goal_id, module_id) in self.covered

    def module_coverage_score(self, module_id: int) -> float:
        """Fraction of goals covered by this module."""
        if not self.goals: return 0.0
        c = sum(1 for g in self.goals if self.is_covered(g.id, module_id))
        return c / len(self.goals)

    def goal_coverage_pct(self, goal_id: int) -> float:
        """Fraction of modules covering this goal."""
        if not self.modules: return 0.0
        c = sum(1 for m in self.modules if self.is_covered(goal_id, m.id))
        return c / len(self.modules)

    def suggested_weights(self) -> List[Dict]:
        """Normalised weights proportional to coverage score."""
        scores = [(m, self.module_coverage_score(m.id)) for m in self.modules]
        total = sum(s for _, s in scores) or 1.0
        return [{"module_id": m.id, "module_name": m.name,
                 "coverage_score": round(s, 4),
                 "weight": round(s / total, 4)} for m, s in scores]

    def kpi_summary(self) -> List[Dict]:
        return [{"goal_id": g.id, "goal_name": g.name, "kpi": g.kpi,
                 "coverage_pct": round(self.goal_coverage_pct(g.id) * 100, 1),
                 "covered_modules": [m.name for m in self.modules
                                     if self.is_covered(g.id, m.id)]}
                for g in self.goals]

    def matrix_as_list(self) -> List[Dict]:
        return [{"goal_id": g.id, "goal_name": g.name,
                 "cells": {m.id: self.is_covered(g.id, m.id) for m in self.modules}}
                for g in self.goals]

    def to_dict(self) -> dict:
        return {
            "goals": [g.to_dict() for g in self.goals],
            "modules": [m.to_dict() for m in self.modules],
            "covered": [list(pair) for pair in self.covered],
            "suggested_weights": self.suggested_weights(),
            "kpi_summary": self.kpi_summary(),
            "matrix": self.matrix_as_list(),
        }

    @staticmethod
    def from_dict(d: dict) -> "BakMatrix":
        goals   = [Goal(**g) for g in d.get("goals", [])]
        modules = [BakModule(**m) for m in d.get("modules", [])]
        covered = {tuple(p) for p in d.get("covered", [])}
        bak = BakMatrix(goals=goals, modules=modules, covered=covered)
        return bak
