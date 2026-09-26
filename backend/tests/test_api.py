"""API tests: send real HTTP requests to the app without starting a server."""

import pytest
from fastapi.testclient import TestClient

import app.main
from app.analyzer import AnalysisError
from app.database import get_db
from app.main import app as fastapi_app
from app.models import AIAnalysis

# TestClient calls the app in-process, so tests are fast and need no port.
client = TestClient(fastapi_app)

FAKE_ANALYSIS = AIAnalysis(summary="Test summary.", recommendations=[], csrd_gaps=[], quick_wins=[])


@pytest.fixture(autouse=True)
def fake_claude(monkeypatch):
    """Replace the real Claude call in every API test (autouse = applies automatically).

    monkeypatch swaps the function only during the test and restores it after,
    so API tests never hit the network or spend API credits.
    """
    monkeypatch.setattr(app.main, "analyse_with_claude", lambda data, score: FAKE_ANALYSIS)


@pytest.fixture(autouse=True)
def test_db(db_session):
    """Routes get the in-memory test database instead of the real file."""
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    yield
    fastapi_app.dependency_overrides.clear()

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


def test_analyse_returns_score_and_ai_analysis():
    response = client.post("/analyse", json=AT_BENCHMARK)
    assert response.status_code == 200
    body = response.json()
    assert body["score"]["overall_score"] == 50
    assert len(body["score"]["metrics"]) == 6
    # The UI needs the source and indicative flag for every comparison.
    first = body["score"]["metrics"][0]
    assert first["benchmark_source"]
    assert first["benchmark_indicative"] is True
    assert body["ai_analysis"]["summary"] == "Test summary."
    assert body["ai_error"] is None


def test_analyse_still_returns_score_when_ai_fails(monkeypatch):
    def failing_claude(data, score):
        raise AnalysisError("AI analysis is busy. Please try again in a minute.")

    monkeypatch.setattr(app.main, "analyse_with_claude", failing_claude)
    response = client.post("/analyse", json=AT_BENCHMARK)
    # Not a 500: the deterministic score is still useful without the AI text.
    assert response.status_code == 200
    body = response.json()
    assert body["score"]["overall_score"] == 50
    assert body["ai_analysis"] is None
    assert "busy" in body["ai_error"]


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


# --- saved assessments ----------------------------------------------------

def test_analyse_saves_and_returns_id():
    body = client.post("/analyse", json=AT_BENCHMARK).json()
    assert body["id"] == 1
    # "Z" = UTC, so browsers convert the time to local time correctly.
    assert body["created_at"].endswith("Z")


def test_assessments_list_newest_first():
    client.post("/analyse", json=AT_BENCHMARK)
    client.post("/analyse", json={**AT_BENCHMARK, "company_name": "Second GmbH"})
    rows = client.get("/assessments").json()
    assert [row["company_name"] for row in rows] == ["Second GmbH", "Test GmbH"]
    assert rows[0]["overall_score"] == 50
    assert rows[0]["sector"] == "other"
    assert rows[0]["created_at"].endswith("Z")


def test_get_one_assessment_matches_analyse_response():
    created = client.post("/analyse", json=AT_BENCHMARK).json()
    loaded = client.get(f"/assessments/{created['id']}").json()
    assert loaded == created


def test_get_missing_assessment_returns_404():
    response = client.get("/assessments/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Assessment not found"}
