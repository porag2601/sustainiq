"""Deterministic scoring: per-FTE metrics, benchmark comparison, 0-100 score.

This runs in plain Python on purpose: the same input always gives the same
score, every step can be unit-tested, and the number can be explained.
Claude never calculates the score, it only writes text about it.
"""

from app.benchmarks import METRIC_KEYS, Benchmark, get_benchmarks
from app.models import AssessmentInput, MetricResult, ScoreResult

# How much each metric counts in the overall score (sums to 1.0).
# Climate metrics weigh most: ESRS E1 (climate) is the core of CSRD, and
# energy + renewables drive Scope 1+2 emissions for most SMEs.
WEIGHTS: dict[str, float] = {
    "scope12_t_per_fte": 0.30,    # ESRS E1 climate
    "energy_kwh_per_fte": 0.20,   # ESRS E1 energy
    "renewable_share_pct": 0.20,  # ESRS E1 energy mix
    "waste_t_per_fte": 0.10,      # ESRS E5 resource use
    "recycling_rate_pct": 0.10,   # ESRS E5 circular economy
    "water_m3_per_fte": 0.10,     # ESRS E3 water
}

# A metric within +/- 5 score points of 50 counts as "on par" with the sector.
ON_PAR_BAND = 5.0


def compute_metrics(data: AssessmentInput) -> dict[str, float]:
    """Normalise absolute yearly values per FTE so companies of any size compare fairly.

    Percentages are already size-independent, so they pass through unchanged.
    employees_fte > 0 is guaranteed by the input schema, so no division by zero.
    """
    fte = data.employees_fte
    return {
        "energy_kwh_per_fte": data.energy_kwh / fte,
        "scope12_t_per_fte": data.scope12_emissions_t / fte,
        "waste_t_per_fte": data.waste_t / fte,
        "water_m3_per_fte": data.water_m3 / fte,
        "renewable_share_pct": data.renewable_share_pct,
        "recycling_rate_pct": data.recycling_rate_pct,
    }


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def metric_score(value: float, benchmark: Benchmark) -> float:
    """Score one metric from 0 (poor) to 100 (excellent); 50 = exactly at benchmark.

    Lower is better (energy, CO2, waste, water):
        0 use -> 100, benchmark -> 50, 2x benchmark or more -> 0.
    Higher is better (renewable %, recycling %):
        0 % -> 0, benchmark -> 50, 100 % -> 100.
    Both are straight lines between those points, so the score is easy to explain.
    """
    bench = benchmark.value

    if not benchmark.higher_is_better:
        ratio = value / bench
        return _clamp(50 * (2 - ratio))

    # Higher is better: two straight lines, below and above the benchmark.
    # 100 % is the best possible share, so it always earns full points
    # (checked first, even if the benchmark itself is 100 %).
    if value >= 100:
        return 100.0
    if value <= bench:
        return _clamp(50 * value / bench)
    # Here bench < value < 100, so (100 - bench) is never zero.
    return _clamp(50 + 50 * (value - bench) / (100 - bench))


def _status(score: float) -> str:
    if score > 50 + ON_PAR_BAND:
        return "better"
    if score < 50 - ON_PAR_BAND:
        return "worse"
    return "on_par"


def score_assessment(data: AssessmentInput) -> ScoreResult:
    """Run the full scoring pipeline for one company."""
    metrics = compute_metrics(data)
    benchmarks = get_benchmarks(data.sector)

    results: list[MetricResult] = []
    for key in METRIC_KEYS:
        value = metrics[key]
        benchmark = benchmarks[key]
        score = metric_score(value, benchmark)
        results.append(
            MetricResult(
                key=key,
                value=round(value, 2),
                unit=benchmark.unit,
                benchmark_value=benchmark.value,
                benchmark_source=benchmark.source,
                benchmark_indicative=benchmark.indicative,
                higher_is_better=benchmark.higher_is_better,
                diff_pct=round((value - benchmark.value) / benchmark.value * 100, 1),
                score=round(score, 1),
                status=_status(score),
            )
        )

    # Weighted average of the unrounded metric scores, rounded once at the end.
    overall = sum(WEIGHTS[key] * metric_score(metrics[key], benchmarks[key]) for key in METRIC_KEYS)
    return ScoreResult(overall_score=round(overall, 1), metrics=results)
