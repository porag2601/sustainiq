"""Tests for the Claude analyzer, using a fake client: no network, no API cost."""

import json
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from app.analyzer import AnalysisError, analyse_with_claude, build_prompt
from app.models import AIAnalysis, AssessmentInput
from app.scoring import score_assessment

DATA = AssessmentInput(
    company_name="Muster Metallbau GmbH",
    sector="manufacturing",
    employees_fte=45,
    energy_kwh=850_000,
    renewable_share_pct=30,
    scope12_emissions_t=320,
    waste_t=60,
    recycling_rate_pct=55,
    water_m3=1_200,
)
SCORE = score_assessment(DATA)

FAKE_ANALYSIS = AIAnalysis(
    summary="Solid performance with a weak recycling rate.",
    recommendations=[
        {
            "title": "Separate metal scrap streams",
            "description": "Collect steel and aluminium scrap separately.",
            "esrs_standard": "E5",
            "priority": "high",
            "funding_hint": None,
        }
    ],
    csrd_gaps=[{"esrs_standard": "E1", "gap": "No Scope 3 data.", "action": "Start with purchased goods."}],
    quick_wins=["Switch off compressed air overnight."],
)


class FakeMessages:
    """Stands in for client.messages: returns a prepared response or raises an error."""

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []  # remember what the analyzer sent, so tests can check it

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


def fake_client(response=None, error=None):
    return SimpleNamespace(messages=FakeMessages(response, error))


def fake_response(stop_reason="end_turn", parsed_output=FAKE_ANALYSIS):
    return SimpleNamespace(stop_reason=stop_reason, parsed_output=parsed_output)


# --- build_prompt ---------------------------------------------------------

def test_prompt_contains_calculated_numbers_as_json():
    prompt = build_prompt(DATA, SCORE)
    payload = json.loads(prompt[prompt.index("{"):])
    assert payload["company"]["name"] == "Muster Metallbau GmbH"
    assert payload["overall_score_0_to_100"] == SCORE.overall_score
    assert len(payload["metrics"]) == 6
    # Benchmarks are labelled as indicative even inside the prompt.
    assert "indicative_sector_benchmark" in payload["metrics"][0]


# --- analyse_with_claude --------------------------------------------------

def test_success_returns_parsed_analysis():
    client = fake_client(fake_response())
    result = analyse_with_claude(DATA, SCORE, client=client)
    assert result == FAKE_ANALYSIS


def test_model_comes_from_settings_and_schema_is_sent():
    client = fake_client(fake_response())
    analyse_with_claude(DATA, SCORE, client=client)
    call = client.messages.calls[0]
    # conftest.py sets CLAUDE_MODEL=test-model; the model is never hardcoded.
    assert call["model"] == "test-model"
    assert call["output_format"] is AIAnalysis


@pytest.mark.parametrize(
    ("stop_reason", "parsed_output", "message_part"),
    [
        ("refusal", None, "declined"),
        ("max_tokens", None, "cut off"),
        ("end_turn", None, "expected format"),
    ],
)
def test_bad_responses_raise_analysis_error(stop_reason, parsed_output, message_part):
    client = fake_client(fake_response(stop_reason, parsed_output))
    with pytest.raises(AnalysisError, match=message_part):
        analyse_with_claude(DATA, SCORE, client=client)


def _api_error(error_class, status_code):
    """Build a real SDK exception, as the SDK would raise it."""
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx2.Response(status_code, request=request)
    return error_class("error", response=response, body=None)


@pytest.mark.parametrize(
    ("error", "message_part"),
    [
        (_api_error(anthropic.AuthenticationError, 401), "invalid API key"),
        (_api_error(anthropic.RateLimitError, 429), "busy"),
        (_api_error(anthropic.InternalServerError, 500), "API error"),
        (
            anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com")),
            "no connection",
        ),
    ],
)
def test_api_errors_become_friendly_analysis_errors(error, message_part):
    with pytest.raises(AnalysisError, match=message_part):
        analyse_with_claude(DATA, SCORE, client=fake_client(error=error))


def test_prompt_lists_missing_csrd_data():
    data = DATA.model_copy(update={"csrd_available": ["e1_scope12"]})
    prompt = build_prompt(data, SCORE)
    payload = json.loads(prompt[prompt.index("{"):])
    assert payload["csrd_data_available"] == ["E1-6 Scope 1 and 2 GHG emissions"]
    assert "E1-6 Scope 3 GHG emissions" in payload["csrd_data_missing"]
    assert "E1-6 Scope 1 and 2 GHG emissions" not in payload["csrd_data_missing"]
