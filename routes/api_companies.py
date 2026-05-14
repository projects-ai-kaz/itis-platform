"""routes/api_companies.py — REST API для управления компаниями и загрузки данных."""

from __future__ import annotations

import io
import csv

from flask import Blueprint, jsonify, request

companies_bp = Blueprint("companies", __name__, url_prefix="/api/companies")

# ── lazy import чтобы не ломать тесты без pandas ─────────────────────────────
def _get_store():
    from models.company_store import store
    return store


# ─────────────────────────────────────────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────────────────────────────────────────

@companies_bp.get("/")
def list_companies():
    """GET /api/companies/ — список всех компаний."""
    return jsonify({"companies": _get_store().list_companies()}), 200


@companies_bp.get("/<company_id>")
def get_company(company_id: str):
    """GET /api/companies/<id> — профиль одной компании."""
    result = _get_store().get_company(company_id)
    if result is None:
        return jsonify({"error": "Компания не найдена"}), 404
    return jsonify(result), 200


@companies_bp.post("/")
def create_company():
    """
    POST /api/companies/
    Body JSON:
    {
      "name": "ТОО Ромашка",
      "industry": "Торговля",
      "country": "KZ",
      "description": "...",
      "modules": [
        {"name": "CRM", "E": 0.9, "W": 0.4, "C": 0.85, "M": 0.8},
        ...
      ]
    }
    """
    data = request.get_json(silent=True) or {}
    if not data.get("name", "").strip():
        return jsonify({"error": "Поле name обязательно"}), 400
    result = _get_store().create_company(data)
    return jsonify(result), 201


@companies_bp.put("/<company_id>")
def update_company(company_id: str):
    """PUT /api/companies/<id> — обновить профиль компании."""
    data = request.get_json(silent=True) or {}
    result = _get_store().update_company(company_id, data)
    if result is None:
        return jsonify({"error": "Компания не найдена"}), 404
    return jsonify(result), 200


@companies_bp.delete("/<company_id>")
def delete_company(company_id: str):
    """DELETE /api/companies/<id>."""
    success = _get_store().delete_company(company_id)
    if not success:
        return jsonify({"error": "Компания не найдена"}), 404
    return jsonify({"deleted": company_id}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Сравнение
# ─────────────────────────────────────────────────────────────────────────────

@companies_bp.post("/compare")
def compare_companies():
    """
    POST /api/companies/compare
    Body: {"ids": ["uuid1", "uuid2", ...]}
    Возвращает ранжированный список с ITIS-оценками.
    """
    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])
    if not ids:
        # Если ids не указаны — сравниваем все компании
        all_companies = _get_store().list_companies()
        ids = [c["id"] for c in all_companies]
    result = _get_store().compare(ids)
    return jsonify({"comparison": result}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Загрузка данных (CSV / Excel)
# ─────────────────────────────────────────────────────────────────────────────

@companies_bp.post("/upload")
def upload_companies():
    """
    POST /api/companies/upload  (multipart/form-data)
    Поле файла: "file" (CSV или .xlsx)

    Ожидаемые колонки:
      company_name  — название компании (обязательно)
      module_name   — название модуля (обязательно)
      E             — эффект 0–1 (обязательно)
      W             — стратегический вес 0–1 (обязательно)
      C             — покрытие бизнес-целей 0–1 (обязательно)
      M             — зрелость внедрения 0–1 (обязательно)
      industry      — отрасль (необязательно)
      country       — страна/регион (необязательно)
      description   — описание компании (необязательно)

    Один файл может содержать несколько компаний —
    строки с одинаковым company_name объединяются.
    """
    if "file" not in request.files:
        return jsonify({"error": "Поле file не найдено в запросе"}), 400

    uploaded = request.files["file"]
    filename = uploaded.filename or ""

    rows = []
    try:
        if filename.endswith(".csv"):
            rows = _parse_csv(uploaded)
        elif filename.endswith((".xlsx", ".xls")):
            rows = _parse_excel(uploaded)
        else:
            return jsonify({"error": "Поддерживаются только CSV и Excel (.xlsx/.xls)"}), 400
    except Exception as exc:
        return jsonify({"error": f"Ошибка разбора файла: {exc}"}), 422

    if not rows:
        return jsonify({"error": "Файл пустой или не содержит данных"}), 422

    # Проверяем обязательные колонки
    required = {"company_name", "module_name", "E", "W", "C", "M"}
    missing = required - set(rows[0].keys())
    if missing:
        return jsonify({
            "error": f"Отсутствуют обязательные колонки: {', '.join(sorted(missing))}",
            "hint": "Ожидаемые колонки: company_name, module_name, E, W, C, M [, industry, country, description]"
        }), 422

    created = _get_store().import_from_rows(rows)
    return jsonify({
        "imported": len(created),
        "companies": created
    }), 201


@companies_bp.get("/template/csv")
def download_template_csv():
    """GET /api/companies/template/csv — скачать шаблон CSV."""
    from flask import Response
    header = "company_name,module_name,E,W,C,M,industry,country,description\n"
    example = (
        "ТОО Пример,NLP-модуль,0.90,0.30,0.85,0.80,IT,KZ,Пример компании\n"
        "ТОО Пример,CRM-интеграция,0.85,0.70,0.88,0.82,IT,KZ,\n"
        "Другая Компания,Чат-бот,0.75,0.50,0.70,0.65,Торговля,KZ,\n"
    )
    content = header + example
    return Response(
        content,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=companies_template.csv"}
    )


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_csv(file_obj) -> list[dict]:
    """Разбор CSV-файла в список словарей."""
    content = file_obj.read().decode("utf-8-sig")  # utf-8-sig убирает BOM
    reader = csv.DictReader(io.StringIO(content))
    return [dict(row) for row in reader]


def _parse_excel(file_obj) -> list[dict]:
    """Разбор Excel-файла в список словарей. Требует openpyxl."""
    try:
        import openpyxl
    except ImportError:
        raise RuntimeError("Для загрузки Excel установите openpyxl: pip install openpyxl")

    wb = openpyxl.load_workbook(file_obj, read_only=True, data_only=True)
    ws = wb.active

    rows_iter = ws.iter_rows(values_only=True)
    try:
        headers = [str(h).strip() if h is not None else "" for h in next(rows_iter)]
    except StopIteration:
        return []

    result = []
    for row in rows_iter:
        if all(cell is None for cell in row):
            continue
        result.append({
            headers[i]: (str(row[i]).strip() if row[i] is not None else "")
            for i in range(min(len(headers), len(row)))
        })
    return result
