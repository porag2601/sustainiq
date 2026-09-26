"""Pydantic schemas: the shape and rules of data entering and leaving the API.

FastAPI validates every request against these classes before our code runs.
Bad input (e.g. 120 % renewable share) gets an automatic 422 error response,
so scoring and the Claude call only ever see clean, plausible numbers.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


# SQLite stores dates without a time zone. The database always holds UTC,
# so mark it explicitly: JSON then says "...Z" and browsers convert correctly
# to local time, instead of guessing and showing a wrong hour.
UtcDatetime = Annotated[datetime, AfterValidator(_as_utc)]


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


# --- Claude's answer ------------------------------------------------------
# These classes are sent to Claude as a JSON schema (structured outputs), so
# Claude must answer in exactly this shape, and the SDK validates the answer
# against them. Literal = only these exact strings are allowed.
# No numeric limits here on purpose: the schema should stay simple for the API.

EsrsStandard = Literal["E1", "E2", "E3", "E5"]


class Recommendation(BaseModel):
    title: str
    description: str
    esrs_standard: EsrsStandard
    priority: Literal["high", "medium", "low"]
    # e.g. "KfW 295" or "BAFA EEW"; None when no funding programme fits.
    funding_hint: str | None


class CsrdGap(BaseModel):
    esrs_standard: EsrsStandard
    gap: str     # what is missing for CSRD / ESRS reporting
    action: str  # concrete next step to close the gap


class AIAnalysis(BaseModel):
    summary: str
    recommendations: list[Recommendation]
    csrd_gaps: list[CsrdGap]
    quick_wins: list[str]


class AnalysisResponse(BaseModel):
    """What POST /analyse returns: the score always, the AI text if it worked."""

    # Set once the assessment is saved in the database.
    id: int | None = None
    created_at: UtcDatetime | None = None
    score: ScoreResult
    # None when the Claude call failed; the score is still valid on its own.
    ai_analysis: AIAnalysis | None
    ai_error: str | None = None


class AssessmentSummary(BaseModel):
    """One row in the list of past assessments."""

    # from_attributes: build this directly from a database record object.
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: UtcDatetime
    company_name: str
    sector: Sector
    overall_score: float
