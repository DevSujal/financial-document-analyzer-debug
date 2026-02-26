import os
from celery import Celery
from dotenv import load_dotenv
load_dotenv()

from database import create_analysis, update_analysis

# Celery configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "financial_analyzer",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
)


@celery_app.task(name="run_analysis_task", bind=True)
def run_analysis_task(self, job_id: str, query: str, file_path: str):
    """Celery task to run the CrewAI financial analysis crew asynchronously."""
    try:
        # Update status to processing
        update_analysis(job_id, status="processing")

        # Import here to avoid circular imports
        from crewai import Crew, Process
        from agents import financial_analyst, verifier, investment_advisor, risk_assessor
        from task import verification, analyze_financial_document, investment_analysis, risk_assessment

        # Run the crew
        financial_crew = Crew(
            agents=[verifier, financial_analyst, investment_advisor, risk_assessor],
            tasks=[verification, analyze_financial_document, investment_analysis, risk_assessment],
            process=Process.sequential,
            verbose=True,
        )

        result = financial_crew.kickoff({"query": query, "file_path": file_path})

        # Save result to database
        update_analysis(job_id, status="completed", result=str(result))

        return {"job_id": job_id, "status": "completed", "result": str(result)}

    except Exception as e:
        update_analysis(job_id, status="failed", error=str(e))
        return {"job_id": job_id, "status": "failed", "error": str(e)}

    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
