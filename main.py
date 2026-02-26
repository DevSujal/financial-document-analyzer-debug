from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import os
import uuid

from crewai import Crew, Process
from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from task import verification, analyze_financial_document, investment_analysis, risk_assessment
from database import create_analysis, update_analysis, get_analysis, get_all_analyses

app = FastAPI(title="Financial Document Analyzer")


def run_crew(query: str, file_path: str = "data/sample.pdf"):
    """Run the full financial analysis crew with all agents and tasks."""
    financial_crew = Crew(
        agents=[verifier, financial_analyst, investment_advisor, risk_assessor],
        tasks=[verification, analyze_financial_document, investment_analysis, risk_assessment],
        process=Process.sequential,
        verbose=True,
        memory=False,
    )

    result = financial_crew.kickoff({'query': query, 'file_path': file_path})
    return result


# ─── Health Check ───────────────────────────────────────────────
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Financial Document Analyzer API is running"}


# ─── Synchronous Analysis ──────────────────────────────────────
@app.post("/analyze")
async def analyze_document_endpoint(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights")
):
    """Analyze financial document synchronously (waits for result)."""

    file_id = str(uuid.uuid4())
    job_id = file_id
    file_path = f"data/financial_document_{file_id}.pdf"

    try:
        os.makedirs("data", exist_ok=True)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        if query == "" or query is None:
            query = "Analyze this financial document for investment insights"

        # Save to database
        create_analysis(job_id=job_id, filename=file.filename, query=query)
        update_analysis(job_id, status="processing")

        # Run crew synchronously
        response = run_crew(query=query.strip(), file_path=file_path)

        # Update database with result
        update_analysis(job_id, status="completed", result=str(response))

        return {
            "status": "success",
            "job_id": job_id,
            "query": query,
            "analysis": str(response),
            "file_processed": file.filename
        }

    except Exception as e:
        update_analysis(job_id, status="failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error processing financial document: {str(e)}")

    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass


# ─── Async Analysis (Celery Queue) ─────────────────────────────
@app.post("/analyze/async")
async def analyze_document_async(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights")
):
    """Submit financial document for async analysis via Celery queue. Returns a job_id to poll for results."""

    file_id = str(uuid.uuid4())
    job_id = file_id
    file_path = f"data/financial_document_{file_id}.pdf"

    try:
        os.makedirs("data", exist_ok=True)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        if query == "" or query is None:
            query = "Analyze this financial document for investment insights"

        # Save to database
        create_analysis(job_id=job_id, filename=file.filename, query=query)

        # Queue the task via Celery
        from celery_worker import run_analysis_task
        run_analysis_task.delay(job_id=job_id, query=query.strip(), file_path=file_path)

        return {
            "status": "queued",
            "job_id": job_id,
            "message": "Analysis job submitted. Use GET /status/{job_id} to check progress."
        }

    except Exception as e:
        update_analysis(job_id, status="failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error queuing analysis: {str(e)}")


# ─── Job Status ────────────────────────────────────────────────
@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Check the status of an analysis job."""
    analysis = get_analysis(job_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Job not found")
    return analysis


# ─── Analysis History ──────────────────────────────────────────
@app.get("/analyses")
async def list_analyses():
    """List all past analysis results."""
    return {"analyses": get_all_analyses()}


@app.get("/analyses/{job_id}")
async def get_analysis_detail(job_id: str):
    """Get detailed result of a specific analysis."""
    analysis = get_analysis(job_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)