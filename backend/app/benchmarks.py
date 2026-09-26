"""Sector benchmark values that a company's metrics are compared against.

IMPORTANT - data honesty:
Eurostat publishes sector *totals* (e.g. tonnes CO2e for all of NACE C),
not ready-made per-FTE values for SMEs. Every value below is therefore an
estimate derived from those totals, and is marked indicative=True. The UI
must show these as indicative, never as official figures.
To upgrade a value to official, replace it with a directly published
figure, set indicative=False and cite the exact table and year.
"""

from pydantic import BaseModel, ConfigDict

from app.models import Sector


class Benchmark(BaseModel):
    """One reference value for one metric in one sector."""

    # frozen: benchmark data is reference data and must not change at runtime.
    model_config = ConfigDict(frozen=True)

    value: float
    unit: str
    source: str
    indicative: bool
    # Tells scoring which direction is "good": less energy is better,
    # but a higher renewable share is better.
    higher_is_better: bool


# --- Metric definitions --------------------------------------------------
# Unit, direction and source are the same for every sector, so they are
# defined once here instead of repeated 5 times.
# Keys match the per-FTE / percentage metrics that scoring.py will compute.

_METRICS: dict[str, dict] = {
    "energy_kwh_per_fte": {
        "unit": "kWh per FTE per year",
        "higher_is_better": False,
        "source": "Indicative estimate derived from Eurostat nrg_bal_c (energy "
        "balances, final consumption by sector) and sbs_ovw_act (persons employed).",
    },
    "scope12_t_per_fte": {
        "unit": "t CO2e per FTE per year",
        "higher_is_better": False,
        "source": "Indicative estimate derived from Eurostat env_ac_ainah_r2 (air "
        "emissions accounts by NACE activity) and sbs_ovw_act (persons employed).",
    },
    "waste_t_per_fte": {
        "unit": "t waste per FTE per year",
        "higher_is_better": False,
        "source": "Indicative estimate derived from Eurostat env_wasgen (waste "
        "generation by NACE activity) and sbs_ovw_act (persons employed).",
    },
    "water_m3_per_fte": {
        "unit": "m3 water per FTE per year",
        "higher_is_better": False,
        "source": "Indicative estimate derived from Eurostat env_wat_use (water use "
        "by supply category and economic sector) and Destatis water statistics.",
    },
    "renewable_share_pct": {
        "unit": "% of energy use",
        "higher_is_better": True,
        "source": "Indicative estimate based on UBA 'Erneuerbare Energien in Zahlen' "
        "(renewable shares in Germany) and Eurostat nrg_ind_ren.",
    },
    "recycling_rate_pct": {
        "unit": "% of waste recycled",
        "higher_is_better": True,
        "source": "Indicative estimate based on Eurostat env_wasoper / env_wastrt "
        "(waste treatment) and UBA waste statistics.",
    },
}

# Keep this as the single list of metric names other modules can rely on.
METRIC_KEYS: tuple[str, ...] = tuple(_METRICS)


# --- Sector values -------------------------------------------------------
# Typical values for a German / EU SME in each sector (see module docstring).
# Rough reasoning, so each number can be explained:
# - Logistics: high energy and CO2 per FTE because of diesel fuel.
# - Construction: very high waste per FTE (construction & demolition waste
#   is the largest EU waste stream), but also high recycling rates.
# - Other (mostly services/offices): low energy, waste and water per FTE.

_SECTOR_VALUES: dict[Sector, dict[str, float]] = {
    Sector.MANUFACTURING: {
        "energy_kwh_per_fte": 40_000,
        "scope12_t_per_fte": 10.0,
        "waste_t_per_fte": 5.0,
        "water_m3_per_fte": 100,
        "renewable_share_pct": 25,
        "recycling_rate_pct": 65,
    },
    Sector.LOGISTICS_TRANSPORT: {
        "energy_kwh_per_fte": 60_000,
        "scope12_t_per_fte": 18.0,
        "waste_t_per_fte": 1.5,
        "water_m3_per_fte": 30,
        "renewable_share_pct": 10,
        "recycling_rate_pct": 55,
    },
    Sector.FOOD_RETAIL: {
        "energy_kwh_per_fte": 20_000,
        "scope12_t_per_fte": 5.0,
        "waste_t_per_fte": 3.0,
        "water_m3_per_fte": 80,
        "renewable_share_pct": 30,
        "recycling_rate_pct": 60,
    },
    Sector.CONSTRUCTION: {
        "energy_kwh_per_fte": 15_000,
        "scope12_t_per_fte": 6.0,
        "waste_t_per_fte": 40.0,
        "water_m3_per_fte": 40,
        "renewable_share_pct": 15,
        "recycling_rate_pct": 80,
    },
    Sector.OTHER: {
        "energy_kwh_per_fte": 8_000,
        "scope12_t_per_fte": 2.0,
        "waste_t_per_fte": 0.5,
        "water_m3_per_fte": 20,
        "renewable_share_pct": 30,
        "recycling_rate_pct": 55,
    },
}


def _build_benchmarks() -> dict[Sector, dict[str, Benchmark]]:
    """Combine metric definitions and sector values into Benchmark objects."""
    return {
        sector: {
            key: Benchmark(value=value, indicative=True, **_METRICS[key])
            for key, value in values.items()
        }
        for sector, values in _SECTOR_VALUES.items()
    }


# Built once when the module is imported; the data never changes at runtime.
BENCHMARKS: dict[Sector, dict[str, Benchmark]] = _build_benchmarks()


def get_benchmarks(sector: Sector) -> dict[str, Benchmark]:
    """Return all benchmarks for one sector, keyed by metric name."""
    return BENCHMARKS[sector]
