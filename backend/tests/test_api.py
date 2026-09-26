"""API tests: send real HTTP requests to the app without starting a server."""

from fastapi.testclient import TestClient

from app.main import app

# TestClient calls the app in-process, so tests are fast and need no port.
client = TestClient(app)

# Every value equals the "other" sector benchmark (10 FTE), so the score is 50.
AT_BENCHMARK = {
    "company_name": "Test GmbH",
    "sector": "other",
    "employees_fte": 10,
    "energy_kwh": 80_000,
    "renewable_share_pct": 30,
    "scope12_emissions_t": 20,
    "waste_t": 5,
    "recycling_rate_pct": 55,
    "water_m3": 200,
}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyse_returns_score():
    response = client.post("/analyse", json=AT_BENCHMARK)
    assert response.status_code == 200
    body = response.json()
    assert body["overall_score"] == 50
    assert len(body["metrics"]) == 6
    # The UI needs the source and indicative flag for every comparison.
    first = body["metrics"][0]
    assert first["benchmark_source"]
    assert first["benchmark_indicative"] is True


def test_analyse_rejects_invalid_input_with_422():
    response = client.post("/analyse", json={**AT_BENCHMARK, "renewable_share_pct": 120})
    assert response.status_code == 422
    # The error names the field, so the frontend can highlight it.
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", "renewable_share_pct"]


def test_analyse_rejects_missing_body():
    assert client.post("/analyse").status_code == 422


def test_cors_allows_frontend_origin():
    # Browsers send this "preflight" OPTIONS request before a JSON POST.
    response = client.options(
        "/analyse",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_blocks_other_origin():
    response = client.options(
        "/analyse",
        headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in response.headers
