"""tests/test_companies.py — тесты для multi-company API."""

import io
import json
import pytest

from app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Тестовый клиент с изолированным хранилищем."""
    # Перенаправляем файл хранилища во временную директорию
    store_file = tmp_path / "companies.json"
    monkeypatch.setattr(
        "models.company_store._STORE_FILE", str(store_file)
    )
    # Сбрасываем singleton
    import models.company_store as cs_module
    cs_module.CompanyStore._instance = None

    app = create_app(testing=True)
    with app.test_client() as client:
        yield client


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _company_payload(name="Test Co", n_modules=2):
    modules = [
        {"name": f"Module {i}", "E": 0.8, "W": 0.5, "C": 0.75, "M": 0.70}
        for i in range(n_modules)
    ]
    return {"name": name, "industry": "IT", "country": "KZ",
            "description": "Desc", "modules": modules}


# ─── CRUD ────────────────────────────────────────────────────────────────────

class TestCRUD:
    def test_list_empty(self, client):
        r = client.get("/api/companies/")
        assert r.status_code == 200
        assert r.get_json()["companies"] == []

    def test_create(self, client):
        r = client.post("/api/companies/",
                        data=json.dumps(_company_payload()),
                        content_type="application/json")
        assert r.status_code == 201
        data = r.get_json()
        assert data["name"] == "Test Co"
        assert "id" in data
        assert data["itis_score"] > 0

    def test_create_missing_name(self, client):
        r = client.post("/api/companies/",
                        data=json.dumps({"modules": []}),
                        content_type="application/json")
        assert r.status_code == 400

    def test_get_existing(self, client):
        cp = client.post("/api/companies/",
                         data=json.dumps(_company_payload("Alpha")),
                         content_type="application/json").get_json()
        r = client.get(f"/api/companies/{cp['id']}")
        assert r.status_code == 200
        assert r.get_json()["name"] == "Alpha"

    def test_get_missing(self, client):
        r = client.get("/api/companies/nonexistent-id")
        assert r.status_code == 404

    def test_update(self, client):
        cp = client.post("/api/companies/",
                         data=json.dumps(_company_payload()),
                         content_type="application/json").get_json()
        r = client.put(f"/api/companies/{cp['id']}",
                       data=json.dumps({"name": "Updated Name"}),
                       content_type="application/json")
        assert r.status_code == 200
        assert r.get_json()["name"] == "Updated Name"

    def test_delete(self, client):
        cp = client.post("/api/companies/",
                         data=json.dumps(_company_payload()),
                         content_type="application/json").get_json()
        r = client.delete(f"/api/companies/{cp['id']}")
        assert r.status_code == 200
        # Проверяем что удалена
        r2 = client.get(f"/api/companies/{cp['id']}")
        assert r2.status_code == 404


# ─── Compare ─────────────────────────────────────────────────────────────────

class TestCompare:
    def test_compare_all(self, client):
        for name in ["Alpha", "Beta", "Gamma"]:
            client.post("/api/companies/",
                        data=json.dumps(_company_payload(name)),
                        content_type="application/json")
        r = client.post("/api/companies/compare",
                        data=json.dumps({"ids": []}),
                        content_type="application/json")
        assert r.status_code == 200
        result = r.get_json()["comparison"]
        assert len(result) == 3
        assert result[0]["rank"] == 1

    def test_compare_selected(self, client):
        ids = []
        for name in ["A", "B"]:
            cp = client.post("/api/companies/",
                             data=json.dumps(_company_payload(name)),
                             content_type="application/json").get_json()
            ids.append(cp["id"])
        r = client.post("/api/companies/compare",
                        data=json.dumps({"ids": [ids[0]]}),
                        content_type="application/json")
        assert r.status_code == 200
        assert len(r.get_json()["comparison"]) == 1


# ─── Upload CSV ───────────────────────────────────────────────────────────────

class TestUploadCSV:
    CSV_VALID = (
        "company_name,module_name,E,W,C,M,industry,country\n"
        "ТОО Ромашка,NLP-модуль,0.9,0.3,0.85,0.8,IT,KZ\n"
        "ТОО Ромашка,CRM,0.85,0.7,0.88,0.82,IT,KZ\n"
        "Другая Компания,Чат-бот,0.75,0.5,0.7,0.65,Торговля,KZ\n"
    )

    def test_upload_csv_valid(self, client):
        data = {"file": (io.BytesIO(self.CSV_VALID.encode("utf-8")), "test.csv")}
        r = client.post("/api/companies/upload",
                        data=data, content_type="multipart/form-data")
        assert r.status_code == 201
        result = r.get_json()
        assert result["imported"] == 2  # 2 компании
        names = {c["name"] for c in result["companies"]}
        assert "ТОО Ромашка" in names
        assert "Другая Компания" in names

    def test_upload_csv_missing_column(self, client):
        csv_bad = "company_name,module_name,E,W\nX,Y,0.5,0.3\n"
        data = {"file": (io.BytesIO(csv_bad.encode("utf-8")), "bad.csv")}
        r = client.post("/api/companies/upload",
                        data=data, content_type="multipart/form-data")
        assert r.status_code == 422
        assert "error" in r.get_json()

    def test_upload_unsupported_format(self, client):
        data = {"file": (io.BytesIO(b"data"), "file.txt")}
        r = client.post("/api/companies/upload",
                        data=data, content_type="multipart/form-data")
        assert r.status_code == 400

    def test_upload_no_file(self, client):
        r = client.post("/api/companies/upload")
        assert r.status_code == 400

    def test_template_csv_download(self, client):
        r = client.get("/api/companies/template/csv")
        assert r.status_code == 200
        assert "company_name" in r.data.decode("utf-8")


# ─── ITIS calculation ─────────────────────────────────────────────────────────

class TestITISCalculation:
    def test_score_formula(self):
        """Проверяем формулу ITIS независимо от API."""
        from models.company_store import CompanyModule, CompanyProfile
        modules = [
            CompanyModule("NLP", 0.95, 0.30, 0.90, 0.85),
            CompanyModule("CRM", 0.88, 0.70, 0.85, 0.90),
        ]
        cp = CompanyProfile(name="Test", modules=modules)
        # Ручной расчёт
        total_w = 0.30 + 0.70
        itis_nlp = (0.95 * 0.90 * 0.85) ** (1/3)
        itis_crm = (0.88 * 0.85 * 0.90) ** (1/3)
        expected = (0.30/total_w * itis_nlp) + (0.70/total_w * itis_crm)
        assert abs(cp.itis_score() - round(expected, 4)) < 0.001

    def test_class_high(self):
        from models.company_store import CompanyModule, CompanyProfile
        cp = CompanyProfile(name="High", modules=[
            CompanyModule("A", 0.95, 1.0, 0.95, 0.95)
        ])
        assert cp.itis_class() == "Высокая эффективность"

    def test_class_low(self):
        from models.company_store import CompanyModule, CompanyProfile
        cp = CompanyProfile(name="Low", modules=[
            CompanyModule("A", 0.1, 1.0, 0.1, 0.1)
        ])
        assert cp.itis_class() == "Низкая эффективность"

    def test_empty_modules(self):
        from models.company_store import CompanyProfile
        cp = CompanyProfile(name="Empty")
        assert cp.itis_score() == 0.0
