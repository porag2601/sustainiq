"""Builds the prompt, calls Claude, and returns a validated AIAnalysis.

Division of work (see docs/PROJECT_NOTES.md): Python calculates every number; Claude only
writes text about those numbers. The prompt therefore hands Claude the finished
score and tells it never to invent or recalculate figures.
"""

import json
import logging

import anthropic

from app.config import get_settings
from app.csrd import compute_readiness, item_titles
from app.models import AIAnalysis, AssessmentInput, ScoreResult

logger = logging.getLogger(__name__)

# Enough room for summary + recommendations; the answer is usually far shorter.
MAX_TOKENS = 16_000

SYSTEM_PROMPT = """\
You are a sustainability consultant for German SMEs (KMU). You write the text
part of an assessment report. All numbers have already been calculated by the
application and are given to you.

Rules:
- Use only the numbers provided. Never invent, estimate or recalculate figures.
- The sector benchmarks are indicative estimates, not official statistics.
  Say so whenever you compare the company with a benchmark.
- Base recommendations on the weakest metrics (lowest scores) first.
- Map each recommendation and CSRD gap to one ESRS standard:
  E1 climate and energy, E2 pollution, E3 water, E5 resource use and circular economy.
- Where it fits, name German regulation (EnEfG, CSRD, EU Taxonomy) and German
  funding programmes (KfW, BAFA) by name. Use null for funding_hint otherwise.
- CSRD gaps: base them on "csrd_data_missing" (data points the company said it
  does not have yet). Prioritise the most important missing items. Do not list
  items from "csrd_data_available" as gaps.
- Give 3 to 5 recommendations, 2 to 4 CSRD gaps and 3 quick wins.
  Quick wins are low-cost actions possible within 3 months.
- Write in clear, plain English for a managing director, not an expert.
"""


class AnalysisError(Exception):
    """The AI analysis failed. The message is safe to show to the user."""


def build_prompt(data: AssessmentInput, score: ScoreResult) -> str:
    """Turn company data and score into the user message for Claude.

    JSON keeps the data unambiguous, and marks the company name clearly as
    data (not instructions) even if someone types odd text into that field.
    """
    payload = {
        "company": {
            "name": data.company_name,
            "sector": data.sector.value,
            "employees_fte": data.employees_fte,
        },
        "overall_score_0_to_100": score.overall_score,
        "metrics": [
            {
                "metric": m.key,
                "company_value": m.value,
                "unit": m.unit,
                "indicative_sector_benchmark": m.benchmark_value,
                "difference_to_benchmark_pct": m.diff_pct,
                "score_0_to_100": m.score,
                "status": m.status,
            }
            for m in score.metrics
        ],
        # From the CSRD checklist in the form (see csrd.py).
        "csrd_data_available": item_titles(data.csrd_available),
        "csrd_data_missing": item_titles(compute_readiness(data.csrd_available).missing_ids),
    }
    return (
        "Write the assessment for this company. The data is JSON:\n\n"
        + json.dumps(payload, indent=2, ensure_ascii=False)
    )


def _make_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=get_settings().anthropic_api_key)


def analyse_with_claude(
    data: AssessmentInput,
    score: ScoreResult,
    client: anthropic.Anthropic | None = None,
) -> AIAnalysis:
    """Ask Claude for the text analysis and return it as a validated AIAnalysis.

    `client` can be passed in so tests can use a fake client (no network, no cost).
    Raises AnalysisError with a user-friendly message on any failure.
    """
    client = client or _make_client()

    try:
        # messages.parse sends AIAnalysis as a JSON schema (structured outputs)
        # and validates the answer into an AIAnalysis object for us.
        response = client.messages.parse(
            model=get_settings().claude_model,  # from .env, never hardcoded
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_prompt(data, score)}],
            output_format=AIAnalysis,
        )
    # Most specific errors first, so each gets its own message.
    # Details go to the server log; the user gets a short, safe message.
    except anthropic.AuthenticationError as exc:
        logger.error("Claude authentication failed: %s", exc)
        raise AnalysisError("AI analysis unavailable: invalid API key.") from exc
    except anthropic.RateLimitError as exc:
        logger.warning("Claude rate limit: %s", exc)
        raise AnalysisError("AI analysis is busy. Please try again in a minute.") from exc
    except anthropic.APIStatusError as exc:
        logger.error("Claude API error %s: %s", exc.status_code, exc)
        raise AnalysisError("AI analysis failed because of an API error.") from exc
    except anthropic.APIConnectionError as exc:
        logger.error("Cannot reach Claude API: %s", exc)
        raise AnalysisError("AI analysis unavailable: no connection to the AI service.") from exc

    # Check why Claude stopped before trusting the content.
    if response.stop_reason == "refusal":
        raise AnalysisError("The AI declined to analyse this input.")
    if response.stop_reason == "max_tokens":
        raise AnalysisError("The AI answer was cut off. Please try again.")
    if response.parsed_output is None:
        raise AnalysisError("The AI answer did not match the expected format.")

    return response.parsed_output
