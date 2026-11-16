

import traceback
import os
import uuid
from threading import Lock

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agents.research_agent import ResearchAgent


# Project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(REPORTS_DIR, exist_ok=True)


# Application
app = FastAPI(
    title="QELVORI - AI Research Intelligence",
    version="3.0.0"
)


# Research job storage
research_jobs = {}
jobs_lock = Lock()


# Request model
class ResearchRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=200)


# Frontend
if os.path.isdir(STATIC_DIR):
    app.mount(
        "/static",
        StaticFiles(directory=STATIC_DIR),
        name="static"
    )


# Home
@app.get("/")
def home():
    index_file = os.path.join(STATIC_DIR, "index.html")

    if not os.path.isfile(index_file):
        return {"message": "QELVORI AI Research Agent is running."}

    return FileResponse(index_file)


# Health check
@app.get("/health")
def health():
    return {
        "status": "running",
        "application": "QELVORI AI Research Intelligence",
        "version": "3.0.0"
    }


# Background research worker
def run_research_job(job_id, topic):

    def progress_callback(update):

        with jobs_lock:
            research_jobs[job_id].update({
                "stage": update["stage"],
                "progress": update["progress"],
                "message": update["message"]
            })

    try:

        agent = ResearchAgent()

        result = agent.run(
            topic,
            progress_callback=progress_callback
        )

        with jobs_lock:

            if result and result.get("success"):

                research_jobs[job_id].update({
                    "status": "completed",
                    "stage": "completed",
                    "progress": 100,
                    "message": "Research completed successfully!",
                    "result": result
                })

            else:

                research_jobs[job_id].update({
                    "status": "failed",
                    "stage": "failed",
                    "message": (
                        result.get("error", "Research failed.")
                        if result else "Research failed."
                    )
                })
    except Exception as error:

        print("\n========== QELVORI BACKEND ERROR ==========")
        print("Job ID:", job_id)
        print("Topic:", topic)
        print("Error:", str(error))
        traceback.print_exc()
        print("=========================================\n")

        with jobs_lock:
            research_jobs[job_id].update({
                "status": "failed",
                "stage": "failed",
                "message": str(error)
            })
# Start research
@app.post("/api/research")
def conduct_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
):

    topic = request.topic.strip()

    if len(topic) < 3:
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid research topic."
        )

    job_id = uuid.uuid4().hex

    with jobs_lock:
        research_jobs[job_id] = {
            "job_id": job_id,
            "topic": topic,
            "status": "running",
            "stage": "starting",
            "progress": 0,
            "message": "Preparing your research...",
            "result": None
        }

    background_tasks.add_task(
        run_research_job,
        job_id,
        topic
    )

    return {
        "job_id": job_id,
        "status": "running",
        "message": "Research started successfully."
    }


# Check research progress
@app.get("/api/research/{job_id}")
def get_research_progress(job_id: str):

    with jobs_lock:
        job = research_jobs.get(job_id)

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Research job not found."
            )

        return job.copy()


# List generated PDF reports
@app.get("/api/reports")
def get_reports():

    reports = []

    for filename in os.listdir(REPORTS_DIR):

        if filename.lower().endswith(".pdf"):
            reports.append(filename)

    return {"reports": reports}


# Download PDF report
@app.get("/api/reports/{filename}")
def download_report(filename: str):

    safe_filename = os.path.basename(filename)

    if (
        safe_filename != filename
        or not safe_filename.lower().endswith(".pdf")
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid report filename."
        )

    file_path = os.path.join(REPORTS_DIR, safe_filename)

    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=404,
            detail="Report not found."
        )

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=safe_filename
    )
