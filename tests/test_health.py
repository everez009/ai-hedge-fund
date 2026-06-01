import importlib.util
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

health_path = Path(__file__).resolve().parent.parent / "app" / "backend" / "routes" / "health.py"
spec = importlib.util.spec_from_file_location("health_route", health_path)
health_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(health_module)
router = health_module.router


def test_health_status_route(monkeypatch):
    def fake_check_service(host: str):
        return {
            "host": host,
            "dns_resolved": True,
            "http_reachable": True,
            "status_code": 200,
            "content_type": "application/json",
            "error": None,
        }

    monkeypatch.setattr(health_module, "_check_service", fake_check_service)

    app = FastAPI()
    app.include_router(router, prefix="/health")
    client = TestClient(app)

    response = client.get("/health/status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert len(body["services"]) == 2
    assert body["services"][0]["host"] == "api.twelvedata.com"
    assert body["services"][1]["host"] == "api.financialdatasets.ai"
