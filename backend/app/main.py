"""FastAPI entry point for the SustainIQ backend.

Routes: /health (is the server up?) and /analyse (score + AI analysis).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.analyzer import AnalysisError, analyse_with_claude
from app.config import get_settings
from app.models import AnalysisResponse, AssessmentInput
from app.scoring import score_assessment

# Loading settings here means a missing .env value stops the app at startup.
settings = get_settings()

# Title and version appear in the auto-generated docs at /docs.
app = FastAPI(title="SustainIQ API", version="0.1.0")

# Browsers block a page on one origin (e.g. localhost:5173) from calling an
# API on another origin (localhost:8000) unless the API allows it. We allow
# only our own frontend, never "*", so other websites cannot use the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the server is running.

    Hosting platforms like Render call a route like this to check
    that the app is alive, so it must stay fast and dependency-free.
    """
    return {"status": "ok"}


# A plain "def" (not "async def") on purpose: the Claude call blocks while it
# waits, and FastAPI runs plain functions in a thread pool, so other requests
# are not stuck behind it.
@app.post("/analyse", response_model=AnalysisResponse)
def analyse(data: AssessmentInput) -> AnalysisResponse:
    """Score one company, then ask Claude to explain the result.

    Typing the parameter as AssessmentInput makes FastAPI validate the JSON
    body first: invalid input gets a 422 and never reaches scoring or Claude.
    """
    score = score_assessment(data)

    # The score is deterministic and always available. If the AI part fails,
    # still return the score and explain what went wrong, instead of a 500.
    try:
        ai_analysis = analyse_with_claude(data, score)
    except AnalysisError as exc:
        return AnalysisResponse(score=score, ai_analysis=None, ai_error=str(exc))

    return AnalysisResponse(score=score, ai_analysis=ai_analysis)
