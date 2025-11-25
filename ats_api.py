# ats_api.py

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Literal
from datetime import datetime

app = FastAPI(title="ATS Core API")

# -----------------------
# Pydantic Models
# -----------------------

Stage = Literal["Applied", "Screening", "Interview", "Offer", "Hired", "Rejected"]

class JobBase(BaseModel):
    title: str
    department: str
    hiring_manager: str
    location: str
    status: Literal["Open", "Closed", "On Hold"] = "Open"

class JobCreate(JobBase):
    pass

class Job(JobBase):
    job_id: int
    open_date: datetime
    close_date: Optional[datetime] = None


class CandidateBase(BaseModel):
    name: str
    email: EmailStr
    job_id: int
    stage: Stage = "Applied"
    source: Optional[str] = None
    notes: Optional[str] = None

class CandidateCreate(CandidateBase):
    pass

class CandidateUpdate(BaseModel):
    # All optional so we can PATCH-style update
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    job_id: Optional[int] = None
    stage: Optional[Stage] = None
    source: Optional[str] = None
    notes: Optional[str] = None

class Candidate(CandidateBase):
    candidate_id: int
    applied_date: datetime
    updated_date: datetime


class Message(BaseModel):
    message_id: int
    candidate_id: int
    to_name: str
    to_email: EmailStr
    subject: str
    body: str
    trigger: Literal["Manual", "Stage Change", "Scheduled"]
    related_stage: Optional[Stage] = None
    timestamp: datetime
    status: Literal["Sent", "Scheduled", "Draft"]


# -----------------------
# In-memory "database"
# -----------------------

jobs: dict[int, Job] = {}
candidates: dict[int, Candidate] = {}
messages: dict[int, Message] = {}

job_counter = 0
candidate_counter = 0
message_counter = 0


# Helper: auto message templates for stage changes
def build_stage_change_message(cand: Candidate, old_stage: Stage, new_stage: Stage) -> Optional[Message]:
    global message_counter

    templates: dict[tuple[Stage, Stage], str] = {
        ("Applied", "Screening"): "Thanks for applying! Our team will review your profile.",
        ("Screening", "Interview"): "Congrats! We’d like to schedule an interview.",
        ("Offer", "Hired"): "Welcome aboard! We’re excited to have you join us.",
    }

    key = (old_stage, new_stage)
    if key not in templates:
        return None

    message_counter += 1
    now = datetime.utcnow()

    msg = Message(
        message_id=message_counter,
        candidate_id=cand.candidate_id,
        to_name=cand.name,
        to_email=cand.email,
        subject=f"Update on your application ({new_stage})",
        body=templates[key],
        trigger="Stage Change",
        related_stage=new_stage,
        timestamp=now,
        status="Sent",
    )
    messages[msg.message_id] = msg
    return msg


# =======================
# JOB ROUTES (Job Launcher)
# =======================

@app.post("/jobs", response_model=Job, status_code=status.HTTP_201_CREATED)
def create_job(job_in: JobCreate):
    """
    Create a new job.
    """
    global job_counter
    job_counter += 1
    now = datetime.utcnow()

    job = Job(
        job_id=job_counter,
        open_date=now,
        **job_in.dict(),
    )
    jobs[job.job_id] = job
    return job


@app.get("/jobs", response_model=List[Job])
def list_jobs(status_filter: Optional[str] = None, department: Optional[str] = None):
    """
    List all jobs, optionally filter by status and department.
    """
    result = list(jobs.values())
    if status_filter:
        result = [j for j in result if j.status == status_filter]
    if department:
        result = [j for j in result if j.department == department]
    return result


@app.get("/jobs/{job_id}", response_model=Job)
def get_job(job_id: int):
    """
    Get a single job by ID.
    """
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.put("/jobs/{job_id}", response_model=Job)
def update_job(job_id: int, job_in: JobCreate):
    """
    Replace a job (full update).
    """
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    updated = job.copy(update=job_in.dict())
    jobs[job_id] = updated
    return updated


@app.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int):
    """
    Delete a job.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    # optionally, also handle candidates linked to this job
    del jobs[job_id]
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


# ==========================
# CANDIDATE ROUTES (Ingestor)
# ==========================

@app.post("/candidates", response_model=Candidate, status_code=status.HTTP_201_CREATED)
def create_candidate(cand_in: CandidateCreate):
    """
    Create a candidate. Stage defaults to Applied.
    """
    global candidate_counter
    # Validate job exists
    if cand_in.job_id not in jobs:
        raise HTTPException(status_code=400, detail="Job does not exist")

    candidate_counter += 1
    now = datetime.utcnow()
    cand = Candidate(
        candidate_id=candidate_counter,
        applied_date=now,
        updated_date=now,
        **cand_in.dict(),
    )
    candidates[cand.candidate_id] = cand
    return cand


@app.get("/candidates", response_model=List[Candidate])
def list_candidates(stage: Optional[Stage] = None, job_id: Optional[int] = None):
    """
    List candidates; filter by stage or job_id if provided.
    """
    result = list(candidates.values())
    if stage:
        result = [c for c in result if c.stage == stage]
    if job_id:
        result = [c for c in result if c.job_id == job_id]
    return result


@app.get("/candidates/{candidate_id}", response_model=Candidate)
def get_candidate(candidate_id: int):
    cand = candidates.get(candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return cand


