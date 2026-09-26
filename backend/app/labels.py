"""Readable names for codes, shared by the PDF report and the rule-based analysis.

The same labels exist in frontend/src/metrics.js for the web page.
"""

METRIC_LABELS = {
    "energy_kwh_per_fte": "Energy per employee",
    "scope12_t_per_fte": "Scope 1+2 emissions per employee",
    "waste_t_per_fte": "Waste per employee",
    "water_m3_per_fte": "Water per employee",
    "renewable_share_pct": "Renewable energy share",
    "recycling_rate_pct": "Recycling rate",
}

SECTOR_LABELS = {
    "manufacturing": "Manufacturing",
    "logistics_transport": "Logistics & Transport",
    "food_retail": "Food & Retail",
    "construction": "Construction",
    "other": "Other",
}


def status_text(score: float) -> str:
    """Overall score in words. Same +/- 5 band around 50 as ON_PAR_BAND in scoring.py."""
    if score > 55:
        return "Better than the sector benchmark"
    if score < 45:
        return "Below the sector benchmark"
    return "Around the sector benchmark"
