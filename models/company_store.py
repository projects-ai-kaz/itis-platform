"""models/company_store.py — Хранилище профилей компаний с персистентностью."""

from __future__ import annotations

import json
import math
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

# Путь к файлу хранилища (рядом с этим модулем)
_STORE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "companies.json")


@dataclass
class CompanyModule:
    """Один модуль/компонент AI-решения для компании."""
    name: str
    E: float   # Эффект (0–1)
    W: float   # Стратегический вес (0–1)
    C: float   # Покрытие бизнес-целей (0–1)
    M: float   # Зрелость внедрения (0–1)

    def itis_i(self) -> float:
        """ITIS по одному модулю: кубический корень из E×C×M."""
        product = max(0.0, self.E * self.C * self.M)
        return round(product ** (1 / 3), 4)


@dataclass
class CompanyProfile:
    """Профиль компании с набором модулей и метаданными."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    industry: str = ""
    country: str = ""
    description: str = ""
    modules: list[CompanyModule] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # ── ITIS calculation ──────────────────────────────────────────────────

    def itis_score(self) -> float:
        """
        ITIS = Σ(Wᵢ / ΣW × ITISᵢ)
        Возвращает 0.0 если модулей нет.
        """
        if not self.modules:
            return 0.0
        total_w = sum(m.W for m in self.modules) or 1.0
        score = sum((m.W / total_w) * m.itis_i() for m in self.modules)
        return round(score, 4)

    def itis_class(self) -> str:
        s = self.itis_score()
        if s < 0.45:
            return "Низкая эффективность"
        if s < 0.70:
            return "Средняя эффективность"
        return "Высокая эффективность"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["itis_score"] = self.itis_score()
        d["itis_class"] = self.itis_class()
        return d


class CompanyStore:
    """
    Singleton-хранилище компаний.
    Данные хранятся в памяти и сериализуются в JSON-файл.
    """
    _instance: Optional["CompanyStore"] = None
    _companies: dict[str, CompanyProfile]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._companies = {}
            cls._instance._load()
        return cls._instance

    # ── Persistence ───────────────────────────────────────────────────────

    def _load(self) -> None:
        os.makedirs(os.path.dirname(_STORE_FILE), exist_ok=True)
        if os.path.exists(_STORE_FILE):
            try:
                with open(_STORE_FILE, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                for item in raw:
                    modules = [CompanyModule(**m) for m in item.pop("modules", [])]
                    item.pop("itis_score", None)
                    item.pop("itis_class", None)
                    cp = CompanyProfile(**item, modules=modules)
                    self._companies[cp.id] = cp
            except Exception:
                self._companies = {}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(_STORE_FILE), exist_ok=True)
        with open(_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in self._companies.values()], f,
                      ensure_ascii=False, indent=2)

    # ── CRUD ──────────────────────────────────────────────────────────────

    def list_companies(self) -> list[dict]:
        return [c.to_dict() for c in self._companies.values()]

    def get_company(self, company_id: str) -> Optional[dict]:
        cp = self._companies.get(company_id)
        return cp.to_dict() if cp else None

    def create_company(self, data: dict) -> dict:
        modules = [CompanyModule(**m) for m in data.get("modules", [])]
        cp = CompanyProfile(
            name=data.get("name", ""),
            industry=data.get("industry", ""),
            country=data.get("country", ""),
            description=data.get("description", ""),
            modules=modules,
        )
        self._companies[cp.id] = cp
        self._save()
        return cp.to_dict()

    def update_company(self, company_id: str, data: dict) -> Optional[dict]:
        cp = self._companies.get(company_id)
        if not cp:
            return None
        cp.name = data.get("name", cp.name)
        cp.industry = data.get("industry", cp.industry)
        cp.country = data.get("country", cp.country)
        cp.description = data.get("description", cp.description)
        if "modules" in data:
            cp.modules = [CompanyModule(**m) for m in data["modules"]]
        cp.updated_at = datetime.utcnow().isoformat()
        self._save()
        return cp.to_dict()

    def delete_company(self, company_id: str) -> bool:
        if company_id not in self._companies:
            return False
        del self._companies[company_id]
        self._save()
        return True

    # ── Bulk import ───────────────────────────────────────────────────────

    def import_from_rows(self, rows: list[dict]) -> list[dict]:
        """
        Пакетный импорт из CSV/Excel.

        Ожидаемые колонки (обязательные):
          company_name, module_name, E, W, C, M

        Необязательные: industry, country, description
        """
        # Группируем строки по имени компании
        groups: dict[str, list[dict]] = {}
        for row in rows:
            key = str(row.get("company_name", "")).strip()
            if not key:
                continue
            groups.setdefault(key, []).append(row)

        created = []
        for company_name, company_rows in groups.items():
            first = company_rows[0]
            modules = []
            for r in company_rows:
                try:
                    modules.append(CompanyModule(
                        name=str(r.get("module_name", "Модуль")).strip(),
                        E=float(r.get("E", 0)),
                        W=float(r.get("W", 0)),
                        C=float(r.get("C", 0)),
                        M=float(r.get("M", 0)),
                    ))
                except (ValueError, TypeError):
                    continue
            cp = CompanyProfile(
                name=company_name,
                industry=str(first.get("industry", "")).strip(),
                country=str(first.get("country", "")).strip(),
                description=str(first.get("description", "")).strip(),
                modules=modules,
            )
            self._companies[cp.id] = cp
            created.append(cp.to_dict())
        if created:
            self._save()
        return created

    # ── Comparison ────────────────────────────────────────────────────────

    def compare(self, company_ids: list[str]) -> list[dict]:
        """Возвращает сравнительную сводку по списку ID компаний."""
        result = []
        for cid in company_ids:
            cp = self._companies.get(cid)
            if cp:
                result.append({
                    "id": cp.id,
                    "name": cp.name,
                    "industry": cp.industry,
                    "country": cp.country,
                    "itis_score": cp.itis_score(),
                    "itis_class": cp.itis_class(),
                    "modules_count": len(cp.modules),
                })
        result.sort(key=lambda x: x["itis_score"], reverse=True)
        for i, item in enumerate(result):
            item["rank"] = i + 1
        return result


# Глобальный экземпляр
store = CompanyStore()
