"""SQLite storage for past assessments, using SQLAlchemy 2.0.

SQLAlchemy maps the Python class AssessmentRecord to the SQL table
"assessments", so the code works with objects instead of raw SQL strings.
That also protects against SQL injection: values are always sent as parameters.
"""

from collections.abc import Iterator
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import get_settings
from app.models import AnalysisResponse, AssessmentInput

_url = get_settings().database_url
# SQLite allows a connection only in the thread that created it by default.
# FastAPI handles requests in a thread pool, so this check must be switched off.
_connect_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}

# The engine manages connections to the database file. Nothing is opened
# until the first query, so importing this module creates no file.
engine = create_engine(_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    """Parent class of all tables; collects them in Base.metadata."""


class AssessmentRecord(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )  # stored as UTC; SQLite has no time zone type
    # Separate columns for what the list view and progress tracking need,
    # so those queries do not have to open the JSON.
    company_name: Mapped[str] = mapped_column(String(200), index=True)
    sector: Mapped[str] = mapped_column(String(50))
    overall_score: Mapped[float] = mapped_column(Float)
    # Full input and result as JSON: keeps the table simple while the result
    # schema is still changing, and allows showing an old report again.
    input_data: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)


def create_tables() -> None:
    """Create missing tables. Existing tables and data are left untouched."""
    Base.metadata.create_all(engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one database session per request, always closed.

    Routes ask for it with Depends(get_db). Tests replace it with an
    in-memory database via app.dependency_overrides.
    """
    with SessionLocal() as session:
        yield session


def save_assessment(db: Session, data: AssessmentInput, response: AnalysisResponse) -> AssessmentRecord:
    record = AssessmentRecord(
        company_name=data.company_name,
        sector=data.sector.value,
        overall_score=response.score.overall_score,
        # mode="json" turns Enums and dates into plain JSON values.
        input_data=data.model_dump(mode="json"),
        result=response.model_dump(mode="json", exclude={"id", "created_at"}),
    )
    db.add(record)
    db.commit()
    db.refresh(record)  # load the id and created_at the database assigned
    return record


def list_assessments(
    db: Session, limit: int = 50, company_name: str | None = None
) -> list[AssessmentRecord]:
    """Newest first. The limit keeps the response small as data grows.

    company_name filters to one company for progress tracking. The match is
    case-insensitive and ignores outer spaces, so "muster gmbh " finds "Muster GmbH".
    """
    query = select(AssessmentRecord)
    if company_name:
        query = query.where(func.lower(AssessmentRecord.company_name) == company_name.strip().lower())
    query = query.order_by(AssessmentRecord.id.desc()).limit(limit)
    return list(db.scalars(query))


def get_assessment(db: Session, assessment_id: int) -> AssessmentRecord | None:
    return db.get(AssessmentRecord, assessment_id)
