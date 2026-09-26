"""Tests for scoring: per-FTE maths, metric score curve, overall score."""

import pytest

from app.benchmarks import METRIC_KEYS, Benchmark, get_benchmarks
from app.models import AssessmentInput, Sector
from app.scoring import WEIGHTS, compute_metrics, metric_score, score_assessment


def make_benchmark(value: float, higher_is_better: bool) -> Benchmark:
    """A simple benchmark so score tests don't depend on the real data."""
    return Benchmark(
        value=value, unit="test", source="test", indicative=True, higher_is_better=higher_is_better
    )


def company_at_benchmark(sector: Sector, fte: float = 10) -> AssessmentInput:
    """A company whose every metric equals its sector benchmark exactly."""
    b = {key: bench.value for key, bench in get_benchmarks(sector).items()}
    return AssessmentInput(
        company_name="Benchmark GmbH",
        sector=sector,
        employees_fte=fte,
        energy_kwh=b["energy_kwh_per_fte"] * fte,
        renewable_share_pct=b["renewable_share_pct"],
        scope12_emissions_t=b["scope12_t_per_fte"] * fte,
        waste_t=b["waste_t_per_fte"] * fte,
        recycling_rate_pct=b["recycling_rate_pct"],
        water_m3=b["water_m3_per_fte"] * fte,
    )


# --- compute_metrics ------------------------------------------------------

def test_values_are_divided_by_fte():
    data = AssessmentInput(
        company_name="Test GmbH", sector="other", employees_fte=4,
        energy_kwh=40_000, renewable_share_pct=50, scope12_emissions_t=8,
        waste_t=2, recycling_rate_pct=70, water_m3=100,
    )
    m = compute_metrics(data)
    assert m["energy_kwh_per_fte"] == 10_000
    assert m["scope12_t_per_fte"] == 2
    assert m["waste_t_per_fte"] == 0.5
    assert m["water_m3_per_fte"] == 25
    # Percentages are not divided.
    assert m["renewable_share_pct"] == 50
    assert m["recycling_rate_pct"] == 70


# --- metric_score: lower is better ---------------------------------------

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 100),     # no use at all: best score
        (50, 75),     # half the benchmark
        (100, 50),    # exactly at benchmark
        (150, 25),    # 50 % above benchmark
        (200, 0),     # twice the benchmark
        (500, 0),     # far worse: clamped at 0, never negative
    ],
)
def test_lower_is_better_curve(value, expected):
    assert metric_score(value, make_benchmark(100, higher_is_better=False)) == pytest.approx(expected)


# --- metric_score: higher is better --------------------------------------

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 0),       # 0 % renewables: worst score
        (20, 25),     # half the benchmark of 40 %
        (40, 50),     # exactly at benchmark
        (70, 75),     # halfway between benchmark and 100 %
        (100, 100),   # 100 % always gives full points
    ],
)
def test_higher_is_better_curve(value, expected):
    assert metric_score(value, make_benchmark(40, higher_is_better=True)) == pytest.approx(expected)


def test_benchmark_of_100_percent_does_not_divide_by_zero():
    assert metric_score(100, make_benchmark(100, higher_is_better=True)) == 100


# --- score_assessment -----------------------------------------------------

def test_weights_cover_all_metrics_and_sum_to_one():
    assert set(WEIGHTS) == set(METRIC_KEYS)
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


@pytest.mark.parametrize("sector", list(Sector))
def test_company_at_benchmark_scores_50(sector):
    result = score_assessment(company_at_benchmark(sector))
    assert result.overall_score == pytest.approx(50)
    assert all(m.status == "on_par" for m in result.metrics)
    assert all(m.diff_pct == 0 for m in result.metrics)


def test_company_size_does_not_change_score():
    # Per-FTE normalisation: a 10x bigger company with 10x the use scores the same.
    small = score_assessment(company_at_benchmark(Sector.MANUFACTURING, fte=5))
    large = score_assessment(company_at_benchmark(Sector.MANUFACTURING, fte=50))
    assert small.overall_score == large.overall_score


def test_better_company_scores_higher():
    base = company_at_benchmark(Sector.LOGISTICS_TRANSPORT)
    better = base.model_copy(update={"scope12_emissions_t": base.scope12_emissions_t / 2})
    result = score_assessment(better)
    assert result.overall_score > 50
    co2 = next(m for m in result.metrics if m.key == "scope12_t_per_fte")
    assert co2.status == "better"
    assert co2.diff_pct == -50


def test_result_carries_benchmark_source_and_indicative_flag():
    result = score_assessment(company_at_benchmark(Sector.FOOD_RETAIL))
    assert len(result.metrics) == len(METRIC_KEYS)
    for m in result.metrics:
        assert m.benchmark_source
        assert m.benchmark_indicative is True
