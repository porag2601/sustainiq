"""Tests for the input schema: valid data passes, each kind of bad data fails."""

import pytest
from pydantic import ValidationError

from app.models import AssessmentInput, Sector


def valid_input() -> dict:
    """A realistic small manufacturer. Each test changes one field from this."""
    return {
        "company_name": "Muster Metallbau GmbH",
        "sector": "manufacturing",
        "employees_fte": 45,
        "energy_kwh": 850_000,
        "renewable_share_pct": 30,
        "scope12_emissions_t": 320,
        "waste_t": 60,
        "recycling_rate_pct": 55,
        "water_m3": 1_200,
    }


def test_valid_input_is_accepted():
    data = AssessmentInput(**valid_input())
    # The sector string is converted to the Enum member.
    assert data.sector is Sector.MANUFACTURING
    assert data.employees_fte == 45


def test_company_name_whitespace_is_stripped():
    data = AssessmentInput(**{**valid_input(), "company_name": "  Muster GmbH  "})
    assert data.company_name == "Muster GmbH"


def test_zero_values_are_allowed():
    # A company can genuinely have 0 % renewables or 0 water use.
    data = AssessmentInput(**{**valid_input(), "renewable_share_pct": 0, "water_m3": 0})
    assert data.renewable_share_pct == 0


# parametrize runs the same test once per (field, bad value) pair,
# so each rule is checked without copy-pasting a test function.
@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("employees_fte", 0),            # would cause division by zero
        ("employees_fte", -5),
        ("energy_kwh", -1),
        ("scope12_emissions_t", -0.1),
        ("waste_t", -10),
        ("water_m3", -3),
        ("renewable_share_pct", 101),    # percentages above 100
        ("recycling_rate_pct", 150),
        ("renewable_share_pct", -1),     # and below 0
        ("sector", "mining"),            # not one of the five sectors
        ("company_name", ""),
        ("company_name", "   "),         # only spaces, empty after stripping
        ("energy_kwh", "a lot"),         # not a number
    ],
)
def test_invalid_value_is_rejected(field, bad_value):
    with pytest.raises(ValidationError):
        AssessmentInput(**{**valid_input(), field: bad_value})


def test_missing_field_is_rejected():
    data = valid_input()
    del data["energy_kwh"]
    with pytest.raises(ValidationError):
        AssessmentInput(**data)


def test_unknown_field_is_rejected():
    # Catches typos like "energy_kwhh" sent by the frontend.
    with pytest.raises(ValidationError):
        AssessmentInput(**{**valid_input(), "energy_kwhh": 100})
