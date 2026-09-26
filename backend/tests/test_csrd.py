"""Tests for the CSRD checklist, readiness calculation and input validation."""

import pytest
from pydantic import ValidationError

from app.csrd import CHECKLIST, CHECKLIST_IDS, compute_readiness, item_titles
from app.models import AssessmentInput

BASE_INPUT = {
    "company_name": "Test GmbH", "sector": "other", "employees_fte": 10, "energy_kwh": 80_000,
    "renewable_share_pct": 30, "scope12_emissions_t": 20, "waste_t": 5,
    "recycling_rate_pct": 55, "water_m3": 200,
}


def test_checklist_ids_are_unique():
    assert len(CHECKLIST_IDS) == len(CHECKLIST)


def test_nothing_available():
    r = compute_readiness([])
    assert (r.available, r.total, r.percent) == (0, 12, 0)
    assert r.missing_ids == [item.id for item in CHECKLIST]


def test_everything_available():
    r = compute_readiness(list(CHECKLIST_IDS))
    assert r.percent == 100
    assert r.missing_ids == []


def test_counts_per_standard():
    r = compute_readiness(["e1_scope12", "e1_energy_mix", "e3_water"])
    by_standard = {s.standard: (s.available, s.total) for s in r.standards}
    assert by_standard == {"ESRS 2": (0, 1), "E1": (2, 6), "E2": (0, 2), "E3": (1, 1), "E5": (0, 2)}
    assert r.percent == 25


def test_item_titles_include_reference():
    assert item_titles(["e1_scope3"]) == ["E1-6 Scope 3 GHG emissions"]


def test_input_accepts_known_ids_and_removes_duplicates():
    data = AssessmentInput(**BASE_INPUT, csrd_available=["e3_water", "e3_water", "e1_scope12"])
    assert data.csrd_available == ["e3_water", "e1_scope12"]


def test_input_defaults_to_empty_checklist():
    # Older saved assessments have no csrd_available field and must still load.
    assert AssessmentInput(**BASE_INPUT).csrd_available == []


def test_input_rejects_unknown_ids():
    with pytest.raises(ValidationError, match="unknown checklist ids: made_up"):
        AssessmentInput(**BASE_INPUT, csrd_available=["e3_water", "made_up"])
