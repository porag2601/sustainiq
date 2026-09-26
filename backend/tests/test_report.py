"""Tests for the PDF report. PDF text is compressed, so the tests check that a
valid PDF is produced for every case; the layout is checked by eye."""

from datetime import datetime

from app.csrd import compute_readiness
from app.models import AIAnalysis, AnalysisResponse, AssessmentInput
from app.report import build_pdf
from app.scoring import score_assessment

DATA = AssessmentInput(
    company_name="Muster Metallbau GmbH", sector="manufacturing", employees_fte=45,
    energy_kwh=850_000, renewable_share_pct=30, scope12_emissions_t=320,
    waste_t=60, recycling_rate_pct=55, water_m3=1_200,
)
ANALYSIS = AIAnalysis(
    summary="Good energy efficiency, weak recycling.",
    recommendations=[{
        "title": "Separate metal scrap", "description": "Collect steel and aluminium separately.",
        "esrs_standard": "E5", "priority": "high", "funding_hint": "BAFA EEW",
    }],
    csrd_gaps=[{"esrs_standard": "E1", "gap": "No Scope 3 data.", "action": "Start with purchased goods."}],
    quick_wins=["Switch off compressed air overnight."],
)


def make_result(ai_analysis=ANALYSIS, ai_error=None) -> AnalysisResponse:
    return AnalysisResponse(
        id=7, created_at=datetime(2026, 9, 26, 18, 25), score=score_assessment(DATA),
        ai_analysis=ai_analysis, ai_error=ai_error,
    )


def is_pdf(content: bytes) -> bool:
    # Every PDF file starts with "%PDF-" and ends with "%%EOF".
    return content.startswith(b"%PDF-") and content.rstrip().endswith(b"%%EOF")


def test_full_report_is_a_pdf():
    assert is_pdf(build_pdf(DATA, make_result()))


def test_report_without_ai_analysis_is_a_pdf():
    assert is_pdf(build_pdf(DATA, make_result(ai_analysis=None, ai_error="AI analysis is busy.")))


def test_markup_characters_in_user_and_ai_text_do_not_break_the_pdf():
    # Without escaping, ReportLab would read "<b" or "&" as markup and crash.
    tricky = DATA.model_copy(update={"company_name": "A & B <Holding> GmbH"})
    analysis = ANALYSIS.model_copy(update={"summary": "Use <less> energy & more renewables > 50 %"})
    assert is_pdf(build_pdf(tricky, make_result(ai_analysis=analysis)))


def test_report_with_csrd_readiness_is_a_pdf():
    result = make_result().model_copy(update={"csrd": compute_readiness(["e1_scope12", "e3_water"])})
    assert is_pdf(build_pdf(DATA, result))


def test_unsaved_result_without_id_and_date_works():
    result = make_result().model_copy(update={"id": None, "created_at": None})
    assert is_pdf(build_pdf(DATA, result))
