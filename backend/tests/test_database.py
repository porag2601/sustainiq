"""Tests for saving and reading assessments (uses the in-memory db_session fixture)."""

import pytest
from sqlalchemy import create_engine

from app.database import get_assessment, list_assessments, normalize_database_url, save_assessment
from app.models import AnalysisResponse, AssessmentInput
from app.scoring import score_assessment


def make_input(name: str = "Test GmbH") -> AssessmentInput:
    return AssessmentInput(
        company_name=name, sector="other", employees_fte=10, energy_kwh=80_000,
        renewable_share_pct=30, scope12_emissions_t=20, waste_t=5,
        recycling_rate_pct=55, water_m3=200,
    )


def save(db, name: str = "Test GmbH"):
    data = make_input(name)
    response = AnalysisResponse(score=score_assessment(data), ai_analysis=None, ai_error="test")
    return save_assessment(db, data, response)


def test_save_assigns_id_and_date(db_session):
    record = save(db_session)
    assert record.id == 1
    assert record.created_at is not None
    assert record.overall_score == 50
    assert record.sector == "other"


def test_saved_json_can_be_read_back(db_session):
    record = save(db_session)
    loaded = get_assessment(db_session, record.id)
    assert loaded.input_data["company_name"] == "Test GmbH"
    # The stored result is valid against the response schema again.
    result = AnalysisResponse.model_validate(loaded.result)
    assert result.score.overall_score == 50
    assert result.ai_error == "test"


def test_list_is_newest_first(db_session):
    save(db_session, "First GmbH")
    save(db_session, "Second GmbH")
    names = [r.company_name for r in list_assessments(db_session)]
    assert names == ["Second GmbH", "First GmbH"]


def test_list_respects_limit(db_session):
    for i in range(5):
        save(db_session, f"Company {i}")
    assert len(list_assessments(db_session, limit=3)) == 3


def test_missing_assessment_returns_none(db_session):
    assert get_assessment(db_session, 999) is None


def test_filter_by_company_name_is_case_insensitive(db_session):
    save(db_session, "Muster GmbH")
    save(db_session, "Other AG")
    save(db_session, "Muster GmbH")
    rows = list_assessments(db_session, company_name="  muster gmbh ")
    assert [r.company_name for r in rows] == ["Muster GmbH", "Muster GmbH"]


# --- PostgreSQL URL handling (deployment) --------------------------------


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("postgresql://u:p@host/db?sslmode=require", "postgresql+psycopg://u:p@host/db?sslmode=require"),
        ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("sqlite:///./sustainiq.db", "sqlite:///./sustainiq.db"),
    ],
)
def test_normalize_database_url(given, expected):
    assert normalize_database_url(given) == expected


def test_postgres_driver_is_installed():
    # Creating an engine loads the driver but opens no connection,
    # so this runs without a PostgreSQL server.
    engine = create_engine(normalize_database_url("postgresql://u:p@localhost/db"))
    assert engine.dialect.driver == "psycopg"
