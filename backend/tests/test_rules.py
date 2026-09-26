"""Tests for the free rule-based analysis and the AI on/off switch."""

import pytest

from app.config import Settings
from app.csrd import CHECKLIST_IDS, compute_readiness
from app.models import AssessmentInput
from app.rules import rule_based_analysis
from app.scoring import score_assessment

# Muster Metallbau: better than benchmark on energy, CO2, waste, water;
# on par for renewables (53.3); worse for recycling (42.3).
DATA = AssessmentInput(
    company_name="Muster Metallbau GmbH", sector="manufacturing", employees_fte=45,
    energy_kwh=850_000, renewable_share_pct=30, scope12_emissions_t=320,
    waste_t=60, recycling_rate_pct=55, water_m3=1_200,
)


def analyse(data=DATA, available=()):
    return rule_based_analysis(data, score_assessment(data), compute_readiness(list(available)))


def test_weakest_metric_comes_first_with_high_priority():
    recs = analyse().recommendations
    assert recs[0].title == "Raise the recycling rate"
    assert recs[0].priority == "high"
    assert recs[0].esrs_standard == "E5"


def test_only_metrics_at_or_below_benchmark_get_recommendations():
    titles = [r.title for r in analyse().recommendations]
    assert titles == ["Raise the recycling rate", "Increase the renewable energy share"]


def test_strong_company_still_gets_two_recommendations():
    strong = DATA.model_copy(update={"renewable_share_pct": 100, "recycling_rate_pct": 100,
                                     "energy_kwh": 1, "scope12_emissions_t": 0, "waste_t": 0, "water_m3": 0})
    recs = analyse(strong).recommendations
    assert len(recs) == 2
    assert all(r.priority == "low" for r in recs)


def test_description_quotes_the_calculated_difference():
    rec = analyse().recommendations[0]
    assert rec.description.startswith(
        "Recycling rate is worse than the sector benchmark (-15 % vs. the indicative sector benchmark, score 42/100)."
    )


def test_wording_follows_status_not_sign():
    # Renewables are +20 % (good direction) but only "on par": must not read as "worse" or "better".
    rec = analyse().recommendations[1]
    assert rec.description.startswith("Renewable energy share is around the sector benchmark (+20 %")


def test_strong_company_wording_says_already_better():
    strong = DATA.model_copy(update={"recycling_rate_pct": 100, "renewable_share_pct": 100})
    assert "already better than the sector benchmark" in analyse(strong).recommendations[0].description


def test_funding_hint_only_where_a_programme_fits():
    recs = {r.title: r for r in analyse().recommendations}
    assert recs["Increase the renewable energy share"].funding_hint.startswith("KfW")
    assert recs["Raise the recycling rate"].funding_hint is None


def test_csrd_gaps_come_from_missing_items_in_checklist_order():
    gaps = analyse(available=["esrs2_materiality"]).csrd_gaps
    assert len(gaps) == 4
    assert gaps[0].esrs_standard == "E1"
    assert gaps[0].gap == "No data yet for: Climate policies (E1-2)."


def test_no_gaps_when_all_data_is_available():
    assert analyse(available=CHECKLIST_IDS).csrd_gaps == []


def test_materiality_gap_uses_esrs_2():
    assert analyse().csrd_gaps[0].esrs_standard == "ESRS 2"


def test_three_distinct_quick_wins():
    wins = analyse().quick_wins
    assert len(wins) == 3 == len(set(wins))


def test_summary_names_company_score_and_readiness():
    summary = analyse(available=["e3_water"]).summary
    assert summary.startswith("Muster Metallbau GmbH (Manufacturing) reaches an overall score of 66.8/100")
    assert "1 of 12 key ESRS data points" in summary
    assert "indicative" in summary


def test_output_is_deterministic():
    assert analyse() == analyse()


@pytest.mark.parametrize(
    ("key", "model", "enabled"),
    [
        ("sk-ant-real", "claude-opus-5", True),
        ("", "", False),
        ("sk-ant-real", "", False),
        ("your-api-key-here", "your-model-name-here", False),  # .env.example placeholders
        ("  ", "claude-opus-5", False),
    ],
)
def test_ai_enabled_only_with_real_key_and_model(key, model, enabled):
    assert Settings(anthropic_api_key=key, claude_model=model).ai_enabled is enabled
