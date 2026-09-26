"""FastAPI entry point for the SustainIQ backend.

Routes: /health, /analyse (score + AI analysis, saved), /assessments (history).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.analyzer import AnalysisError, analyse_with_claude
from app.config import get_settings
from app.database import create_tables, get_assessment, get_db, list_assessments, save_assessment
from app.models import AnalysisResponse, AssessmentInput, AssessmentSummary
from app.report import build_pdf
from app.scoring import score_assessment

# Loading settings here means a missing .env value stops the app at startup.
settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Runs once when the server starts (before yield) and stops (after)."""
    create_tables()
    yield


# Title and version appear in the auto-generated docs at /docs.
app = FastAPI(title="SustainIQ API", version="0.1.0", lifespan=lifespan)

# Browsers block a page on one origin (e.g. localhost:5173) from calling an
# API on another origin (localhost:8000) unless the API allows it. We allow
# only our own frontend, never "*", so other websites cannot use the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Dependency injection: FastAPI calls get_db() for each request and passes the
# session in. Tests swap get_db for an in-memory database without changing routes.
DbSession = Annotated[Session, Depends(get_db)]


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
def analyse(data: AssessmentInput, db: DbSession) -> AnalysisResponse:
    """Score one company, ask Claude to explain the result, and save it.

    Typing the parameter as AssessmentInput makes FastAPI validate the JSON
    body first: invalid input gets a 422 and never reaches scoring or Claude.
    """
    score = score_assessment(data)

    # The score is deterministic and always available. If the AI part fails,
    # still return (and save) the score and explain what went wrong.
    try:
        response = AnalysisResponse(score=score, ai_analysis=analyse_with_claude(data, score))
    except AnalysisError as exc:
        response = AnalysisResponse(score=score, ai_analysis=None, ai_error=str(exc))

    record = save_assessment(db, data, response)
    # model_validate (not model_copy) so the UTC validator on created_at runs.
    return AnalysisResponse.model_validate(
        {**response.model_dump(), "id": record.id, "created_at": record.created_at}
    )


@app.get("/assessments", response_model=list[AssessmentSummary])
def assessments(db: DbSession) -> list[AssessmentSummary]:
    """List saved assessments, newest first."""
    return [AssessmentSummary.model_validate(record) for record in list_assessments(db)]


def _load(db: Session, assessment_id: int) -> tuple[AssessmentInput, AnalysisResponse]:
    """Load one saved assessment as validated models, or answer 404."""
    record = get_assessment(db, assessment_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    data = AssessmentInput.model_validate(record.input_data)
    result = AnalysisResponse.model_validate(
        {**record.result, "id": record.id, "created_at": record.created_at}
    )
    return data, result


@app.get("/assessments/{assessment_id}", response_model=AnalysisResponse)
def assessment(assessment_id: int, db: DbSession) -> AnalysisResponse:
    """Return one saved assessment in the same shape as /analyse."""
    return _load(db, assessment_id)[1]


@app.get("/assessments/{assessment_id}/pdf")
def assessment_pdf(assessment_id: int, db: DbSession) -> Response:
    """Download one saved assessment as a PDF report."""
    data, result = _load(db, assessment_id)
    return Response(
        content=build_pdf(data, result),
        media_type="application/pdf",
        # "attachment" makes the browser download the file instead of opening it.
        # The file name uses only the id, so no user text ends up in a header.
        headers={"Content-Disposition": f'attachment; filename="sustainiq-assessment-{assessment_id}.pdf"'},
    )
