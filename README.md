# ITIS Platform — AI Impact Analytics

Полноценное веб-приложение для оценки эффективности внедрения AI-решений.
Три инструмента в одном интерфейсе.

> Байтукенов Б.А. — Магистерская диссертация, 2026.

---

## Структура проекта

```
itis-platform/
├── app.py                        ← Точка входа Flask
├── requirements.txt
├── pyproject.toml
│
├── models/
│   ├── itis.py                   ← ITIS: Module, calculate, classify
│   ├── bak.py                    ← БАК-матрица: BakMatrix, Goal, BakModule
│   └── ml_predictor.py           ← ML: PredictInput, predict (Random Forest)
│
├── routes/
│   ├── api_itis.py               ← /api/itis/*
│   ├── api_bak.py                ← /api/bak/*
│   ├── api_ml.py                 ← /api/ml/*
│   └── export.py                 ← /export/itis, /export/bak, /export/ml
│
├── templates/index.html          ← Jinja2 (3 вкладки)
├── static/css/main.css
├── static/js/
│   ├── app.js                    ← Общие утилиты, переключение страниц
│   ├── itis.js                   ← Вкладка 1: ITIS-калькулятор
│   ├── bak.js                    ← Вкладка 2: БАК-матрица
│   └── ml.js                     ← Вкладка 3: ML-предсказатель
│
└── tests/
    └── test_all.py               ← 71 тест (models + API + export)
```

---

## Запуск

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py          # → http://localhost:5000
```

---

## REST API

### Вкладка 1 — ITIS-калькулятор
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/itis/calculate` | Рассчитать ITIS по модулям |
| POST | `/api/itis/validate` | Валидировать один модуль |
| GET  | `/api/itis/health` | Статус сервиса |
| POST | `/export/itis` | Экспорт в Excel (2 листа) |

### Вкладка 2 — БАК-матрица
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/bak/weights` | Рекомендованные веса W |
| POST | `/api/bak/toggle` | Переключить ячейку матрицы |
| POST | `/api/bak/summary` | Полный дамп матрицы |
| POST | `/export/bak` | Экспорт матрицы в Excel |

### Вкладка 3 — ML-предсказатель
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/ml/predict` | Предсказать класс эффекта |
| GET  | `/api/ml/features` | Список признаков с важностью |
| POST | `/export/ml` | Экспорт прогноза в Excel |

---

## Пример запроса — ITIS

```bash
curl -X POST http://localhost:5000/api/itis/calculate \
  -H "Content-Type: application/json" \
  -d '{"modules":[
    {"name":"NLP-модуль","E":0.95,"W":0.30,"C":0.90,"M":0.85},
    {"name":"CRM","E":0.88,"W":0.70,"C":0.85,"M":0.90}
  ]}'
```

---

## Тесты

```bash
pytest tests/ -v                                  # все тесты
pytest tests/ --cov=models --cov=routes           # с покрытием
```

**71 тест**: модели ITIS / BAK / ML + REST API + Excel-экспорт.

---

## Формула ITIS

```
ITISᵢ = ∛(E × C × M)
ITIS  = Σ(Wᵢ / ΣW × ITISᵢ)
```

| ITIS | Класс |
|------|-------|
| 0.00–0.44 | Низкая эффективность |
| 0.45–0.69 | Средняя эффективность |
| 0.70–1.00 | Высокая эффективность |
