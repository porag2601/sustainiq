"""Pydantic schemas: the shape and rules of data entering and leaving the API.

FastAPI validates every request against these classes before our code runs.
Bad input (e.g. 120 % renewable share) gets an automatic 422 error response,
so scoring and the Claude call only ever see clean, plausible numbers.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Sector(str, Enum):
    """The five sectors we have benchmark data for.

    An Enum (fixed list) instead of free text means a typo like
    "manufactoring" is rejected instead of silently missing a benchmark.
    Inheriting from str makes the values plain strings in JSON.
    """

    MANUFACTURING = "manufacturing"
    LOGISTICS_TRANSPORT = "logistics_transport"
    FOOD_RETAIL = "food_retail"
    CONSTRUCTION = "construction"
    OTHER = "other"


class AssessmentInput(BaseModel):
    """Yearly operational data a company enters in the assessment form."""

    # extra="forbid": unknown fields are an error, which catches frontend typos.
    # str_strip_whitespace: "  ACME GmbH " is stored as "ACME GmbH".
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    company_name: str = Field(min_length=1, max_length=200)
    sector: Sector

    # gt=0 (not ge=0): we divide by employees for per-FTE metrics, so 0 is invalid.
    # float, because FTE can be fractional (two half-time staff = 1.0 FTE).
    employees_fte: float = Field(gt=0, description="Full-time equivalents")

    # ge=0: consumption and emissions can be zero, never negative.
    energy_kwh: float = Field(ge=0, description="Total energy use, kWh per year")
    renewable_share_pct: float = Field(ge=0, le=100, description="Renewable share of energy, %")
    scope12_emissions_t: float = Field(ge=0, description="Scope 1+2 emissions, t CO2e per year")
    waste_t: float = Field(ge=0, description="Total waste, tonnes per year")
    recycling_rate_pct: float = Field(ge=0, le=100, description="Share of waste recycled, %")
    water_m3: float = Field(ge=0, description="Water use, m3 per year")


class MetricResult(BaseModel):
    """One metric of the company compared with its sector benchmark."""

    key: str
    value: float
    unit: str
    benchmark_value: float
    # Copied from the benchmark so the UI can show the source and the
    # "indicative" label next to every comparison.
    benchmark_source: str
    benchmark_indicative: bool
    higher_is_better: bool
    # Difference to the benchmark in %: +20 means 20 % above the benchmark.
    diff_pct: float
    score: float = Field(ge=0, le=100)
    status: str  # "better", "on_par" or "worse" than the benchmark


class ScoreResult(BaseModel):
    """Deterministic scoring output, calculated in Python (not by Claude)."""

    overall_score: float = Field(ge=0, le=100)
    metrics: list[MetricResult]

