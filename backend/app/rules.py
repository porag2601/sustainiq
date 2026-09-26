"""Free, rule-based analysis text: the fallback when Claude is not used.

Returns the same AIAnalysis structure Claude returns, so the frontend and the
PDF need no special case. Everything here is deterministic: the same input
always gives the same text, and every rule is unit-tested.

The rules follow the same logic the prompt gives Claude:
weakest metrics first, each mapped to an ESRS standard; CSRD gaps from the
missing checklist items; quick wins that cost little.
"""

from app.csrd import CHECKLIST, CsrdReadiness
from app.labels import METRIC_LABELS, SECTOR_LABELS, status_text
from app.models import AIAnalysis, AssessmentInput, CsrdGap, MetricResult, Recommendation, ScoreResult

MAX_RECOMMENDATIONS = 4
MAX_GAPS = 4
QUICK_WINS = 3

# One recommendation per metric: (title, advice, ESRS standard, funding hint).
# Funding programmes named here exist in Germany; conditions change, so the
# UI and PDF present them as hints to check, not as promises.
_METRIC_ADVICE = {
    "energy_kwh_per_fte": (
        "Reduce energy consumption",
        "Start with an energy audit (DIN EN 16247) to find the largest consumers, typically "
        "compressed air, heating, lighting and electric motors, then fix the biggest ones first.",
        "E1",
        "BAFA/KfW: Bundesförderung für Energie- und Ressourceneffizienz in der Wirtschaft (EEW)",
    ),
    "scope12_t_per_fte": (
        "Cut Scope 1 and 2 emissions",
        "Switch to certified green electricity (lowers market-based Scope 2), replace fossil "
        "heating with heat pumps where possible, and set a reduction target against a base year.",
        "E1",
        "BAFA/KfW: Bundesförderung für Energie- und Ressourceneffizienz in der Wirtschaft (EEW)",
    ),
    "renewable_share_pct": (
        "Increase the renewable energy share",
        "Check the roof for a photovoltaic system and move the electricity contract to a certified "
        "green tariff or a power purchase agreement (PPA).",
        "E1",
        "KfW Erneuerbare Energien – Standard (270)",
    ),
    "waste_t_per_fte": (
        "Reduce waste volumes",
        "Analyse waste by type and source for one month, then target the largest stream, "
        "for example with reusable packaging agreed with suppliers.",
        "E5",
        None,
    ),
    "recycling_rate_pct": (
        "Raise the recycling rate",
        "Separate waste streams where they arise (paper, plastics, metals, wood, glass); the German "
        "Gewerbeabfallverordnung already requires separate collection for most of them.",
        "E5",
        None,
    ),
    "water_m3_per_fte": (
        "Reduce water use",
        "Install sub-meters to see where water is used, repair leaks, and reuse process or "
        "cooling water where the quality allows it.",
        "E3",
        None,
    ),
}

_QUICK_WINS = {
    "energy_kwh_per_fte": "Switch off compressed air, machines and lighting outside working hours.",
    "scope12_t_per_fte": "Ask your electricity supplier for a certified green tariff.",
    "renewable_share_pct": "Get a quote for a rooftop photovoltaic system.",
    "waste_t_per_fte": "Agree reusable transport packaging with your two largest suppliers.",
    "recycling_rate_pct": "Put labelled bins for separate waste streams at every workstation.",
    "water_m3_per_fte": "Check for leaks and fit water-saving aerators on taps.",
}

# Concrete next step for each missing CSRD checklist item (ids from csrd.py).
_GAP_ACTIONS = {
    "esrs2_materiality": "Run a double materiality assessment: list impacts, risks and opportunities, "
                         "then rate each for impact and financial materiality.",
    "e1_policies": "Write a short climate and energy policy and have management approve it.",
    "e1_transition_plan": "Draft a transition plan with base year, targets, measures and investment needs.",
    "e1_targets": "Set a Scope 1+2 reduction target against a base year, e.g. using the SBTi route for SMEs.",
    "e1_energy_mix": "Collect a year of energy bills and split consumption by source (fossil, renewable).",
    "e1_scope12": "Calculate Scope 1 and 2 emissions from fuel and electricity data (GHG Protocol), "
                  "Scope 2 both location- and market-based.",
    "e1_scope3": "Estimate the largest Scope 3 categories first, usually purchased goods and transport, "
                 "with spend-based emission factors.",
    "e2_pollutants": "Use permits and measurement reports to list pollutants emitted to air, water and soil.",
    "e2_substances": "Screen safety data sheets against the REACH list of substances of very high concern.",
    "e3_water": "Read water meters and bills, and check whether sites lie in water-stressed areas.",
    "e5_inflows": "Record the main materials by weight and their share of recycled or renewable input.",
    "e5_waste": "Use disposal records to report total and hazardous waste and the share recycled.",
}


def _priority(score: float) -> str:
    # Same band as the metric status in scoring.py: below 45 = worse than benchmark.
    if score < 45:
        return "high"
    if score <= 55:
        return "medium"
    return "low"


def _weakest(metrics: list[MetricResult]) -> list[MetricResult]:
    """Lowest score first; ties keep the metric order, so the output is stable."""
    return sorted(metrics, key=lambda m: m.score)


def _position(m: MetricResult) -> str:
    """Where the metric stands, in words that match its status.

    Uses the status (not the sign of diff_pct), because "+20 %" is good for
    the renewable share but bad for energy use.
    """
    label = METRIC_LABELS[m.key]
    facts = f"({m.diff_pct:+.0f} % vs. the indicative sector benchmark, score {m.score:.0f}/100)"
    if m.status == "worse":
        return f"{label} is worse than the sector benchmark {facts}."
    if m.status == "on_par":
        return f"{label} is around the sector benchmark {facts}, so there is clear room to improve."
    return f"{label} is already better than the sector benchmark {facts}, but it is your weakest area."


def _recommendations(metrics: list[MetricResult]) -> list[Recommendation]:
    weakest = _weakest(metrics)
    # Every metric at or below the benchmark band; at least two, so a strong
    # company still gets something to work on.
    chosen = [m for m in weakest if m.status != "better"]
    if len(chosen) < 2:
        chosen = weakest[:2]
    recs = []
    for m in chosen[:MAX_RECOMMENDATIONS]:
        title, advice, standard, funding = _METRIC_ADVICE[m.key]
        recs.append(Recommendation(
            title=title,
            description=f"{_position(m)} {advice}",
            esrs_standard=standard,
            priority=_priority(m.score),
            funding_hint=funding,
        ))
    return recs


def _csrd_gaps(readiness: CsrdReadiness) -> list[CsrdGap]:
    by_id = {item.id: item for item in CHECKLIST}
    gaps = []
    for item_id in readiness.missing_ids[:MAX_GAPS]:
        item = by_id[item_id]
        gaps.append(CsrdGap(
            esrs_standard=item.standard,
            gap=f"No data yet for: {item.title} ({item.reference}).",
            action=_GAP_ACTIONS[item_id],
        ))
    return gaps


def _quick_wins(metrics: list[MetricResult]) -> list[str]:
    return [_QUICK_WINS[m.key] for m in _weakest(metrics)[:QUICK_WINS]]


def _summary(data: AssessmentInput, score: ScoreResult, readiness: CsrdReadiness) -> str:
    ranked = _weakest(score.metrics)
    weakest, strongest = ranked[0], ranked[-1]
    return (
        f"{data.company_name} ({SECTOR_LABELS[data.sector.value]}) reaches an overall score of "
        f"{score.overall_score:.1f}/100: {status_text(score.overall_score).lower()}. "
        f"The strongest area is {METRIC_LABELS[strongest.key].lower()} (score {strongest.score:.0f}), "
        f"the weakest is {METRIC_LABELS[weakest.key].lower()} (score {weakest.score:.0f}). "
        f"For CSRD reporting, {readiness.available} of {readiness.total} key ESRS data points are "
        f"available. All comparisons use indicative sector benchmarks, not official statistics."
    )


def rule_based_analysis(data: AssessmentInput, score: ScoreResult, readiness: CsrdReadiness) -> AIAnalysis:
    """Build the full analysis text without any AI call."""
    return AIAnalysis(
        summary=_summary(data, score, readiness),
        recommendations=_recommendations(score.metrics),
        csrd_gaps=_csrd_gaps(readiness),
        quick_wins=_quick_wins(score.metrics),
    )
