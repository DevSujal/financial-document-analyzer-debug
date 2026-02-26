import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///analysis_results.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class AnalysisResult(Base):
    """Model for storing financial document analysis results."""
    __tablename__ = "analysis_results"

    job_id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    query = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


# Create tables
Base.metadata.create_all(bind=engine)


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_analysis(job_id: str, filename: str, query: str) -> AnalysisResult:
    """Create a new analysis record."""
    db = SessionLocal()
    try:
        record = AnalysisResult(job_id=job_id, filename=filename, query=query, status="pending")
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    finally:
        db.close()


def update_analysis(job_id: str, status: str, result: str = None, error: str = None):
    """Update an analysis record with results or error."""
    db = SessionLocal()
    try:
        record = db.query(AnalysisResult).filter(AnalysisResult.job_id == job_id).first()
        if record:
            record.status = status
            if result:
                record.result = result
            if error:
                record.error = error
            if status in ("completed", "failed"):
                record.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


def get_analysis(job_id: str) -> dict | None:
    """Get a specific analysis result."""
    db = SessionLocal()
    try:
        record = db.query(AnalysisResult).filter(AnalysisResult.job_id == job_id).first()
        if record:
            return {
                "job_id": record.job_id,
                "filename": record.filename,
                "query": record.query,
                "status": record.status,
                "result": record.result,
                "error": record.error,
                "created_at": str(record.created_at),
                "completed_at": str(record.completed_at) if record.completed_at else None,
            }
        return None
    finally:
        db.close()


def get_all_analyses() -> list[dict]:
    """Get all analysis results, most recent first."""
    db = SessionLocal()
    try:
        records = db.query(AnalysisResult).order_by(AnalysisResult.created_at.desc()).all()
        return [
            {
                "job_id": r.job_id,
                "filename": r.filename,
                "query": r.query,
                "status": r.status,
                "created_at": str(r.created_at),
                "completed_at": str(r.completed_at) if r.completed_at else None,
            }
            for r in records
        ]
    finally:
        db.close()
