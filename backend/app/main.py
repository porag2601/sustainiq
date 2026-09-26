"""FastAPI entry point for the SustainIQ backend.

Routes: /health (is the server up?) and /analyse (score one company).
The Claude analysis is added to /analyse in a later step.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import AssessmentInput, ScoreResult
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


@app.post("/analyse", response_model=ScoreResult)
def analyse(data: AssessmentInput) -> ScoreResult:
    """Score one company's yearly data against its sector benchmarks.

    Typing the parameter as AssessmentInput makes FastAPI validate the JSON
    body before this function runs: invalid input never reaches scoring and
    the client gets a 422 response naming the wrong field.
    response_model makes FastAPI check our output against the schema too.
    """
    return score_assessment(data)
