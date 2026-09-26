"""Tests for benchmark data: complete, consistent, and honestly labelled."""

import pytest
from pydantic import ValidationError

from app.benchmarks import BENCHMARKS, METRIC_KEYS, get_benchmarks
from app.models import Sector


def test_every_sector_has_benchmarks():
    # If a sector is added to the Enum but not here, scoring would crash.
    assert set(BENCHMARKS) == set(Sector)


@pytest.mark.parametrize("sector", list(Sector))
def test_every_sector_has_all_metrics(sector):
    assert set(get_benchmarks(sector)) == set(METRIC_KEYS)


def all_benchmarks():
    """Yield every (sector, metric, benchmark) triple for checks across all data."""
    for sector, metrics in BENCHMARKS.items():
        for key, benchmark in metrics.items():
            yield sector, key, benchmark


def test_every_benchmark_has_a_source():
    # Domain rule: no benchmark value without a source.
    for sector, key, benchmark in all_benchmarks():
        assert benchmark.source.strip(), f"{sector.value}/{key} has no source"


def test_estimates_say_so_in_their_source():
    # Domain rule: estimates must never look like official figures.
    for sector, key, benchmark in all_benchmarks():
        if benchmark.indicative:
            assert "indicative" in benchmark.source.lower(), f"{sector.value}/{key}"


def test_values_are_plausible():
    for sector, key, benchmark in all_benchmarks():
        assert benchmark.value > 0, f"{sector.value}/{key} must be positive"
        if key.endswith("_pct"):
            assert benchmark.value <= 100, f"{sector.value}/{key} is over 100 %"


def test_direction_is_correct():
    # Only the two share metrics are "higher is better".
    for _, key, benchmark in all_benchmarks():
        assert benchmark.higher_is_better == key.endswith("_pct")


def test_benchmarks_cannot_be_changed_at_runtime():
    benchmark = get_benchmarks(Sector.MANUFACTURING)["energy_kwh_per_fte"]
    with pytest.raises(ValidationError):
        benchmark.value = 1
