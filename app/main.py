import uuid
import json
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    FileResponse,
    JSONResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.queue import get_queue, get_redis
from app.worker import process_job


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BASE_DIR = Path("app")
DATA_DIR = BASE_DIR / "data"

UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUTS_DIR = DATA_DIR / "outputs"
JOBS_DIR = DATA_DIR / "jobs"

for d in (UPLOADS_DIR, OUTPUTS_DIR, JOBS_DIR):
    d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# App
# ---------------------------------------------------------

app = FastAPI(title="Offline Video Transcriber")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def dropbox_path(base: Path, job_id: str) -> Path:
    now = datetime.utcnow()
    return base / f"{now.year:04d}" / f"{now.month:02d}" / f"{now.day:02d}" / job_id


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload(
    request: Request,
    videos: list[UploadFile] = File(...),
    frame_interval: int = Form(2),
):
    # -----------------------------------------------------
    # One single job ID used everywhere
    # -----------------------------------------------------
    job_id = str(uuid.uuid4())

    upload_dir = dropbox_path(UPLOADS_DIR, job_id)
    output_dir = dropbox_path(OUTPUTS_DIR, job_id)
    state_dir = JOBS_DIR / job_id

    upload_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------
    # Save uploaded videos
    # -----------------------------------------------------
    video_paths: list[str] = []

    for video in videos:
        safe_name = video.filename.replace("/", "_").replace("\\", "_")
        dst = upload_dir / safe_name
        with open(dst, "wb") as f:
            f.write(await video.read())
        video_paths.append(str(dst))

    # -----------------------------------------------------
    # Initialize job state in Redis
    # -----------------------------------------------------
    r = get_redis()
    r.hset(
        f"job:{job_id}",
        mapping={
            "status": "queued",
            "progress": "0",
            "total_files": str(len(video_paths)),
            "done_files": "0",
            "message": "Job queued",
            "output_dir": str(output_dir),
            "created_at": datetime.utcnow().isoformat(),
            "result_index": json.dumps([]),
        },
    )

    # -----------------------------------------------------
    # Enqueue job (RQ job_id == UI job_id)
    # -----------------------------------------------------
    q = get_queue()
    q.enqueue(
        process_job,
        video_paths=video_paths,
        output_dir=str(output_dir),
        frame_interval=frame_interval,
        job_timeout=60 * 60 * 3,
        job_id=job_id,  # ← RQ internal job ID
    )

    return RedirectResponse(url=f"/jobs/{job_id}", status_code=303)


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_page(request: Request, job_id: str):
    return templates.TemplateResponse(
        "job.html",
        {"request": request, "job_id": job_id},
    )


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    r = get_redis()
    data = r.hgetall(f"job:{job_id}")

    if not data:
        return JSONResponse({"error": "not found"}, status_code=404)

    decoded = {k.decode(): v.decode() for k, v in data.items()}

    try:
        decoded["result_index"] = json.loads(decoded.get("result_index", "[]"))
    except Exception:
        decoded["result_index"] = []

    return decoded


@app.get("/download/{job_id}/{index}")
def download(job_id: str, index: int):
    r = get_redis()
    data = r.hgetall(f"job:{job_id}")

    if not data:
        return JSONResponse({"error": "not found"}, status_code=404)

    decoded = {k.decode(): v.decode() for k, v in data.items()}
    result_index = json.loads(decoded.get("result_index", "[]"))

    try:
        docx_path = Path(result_index[index]["docx_path"])
    except Exception:
        return JSONResponse({"error": "invalid index"}, status_code=400)

    if not docx_path.exists():
        return JSONResponse({"error": "file missing"}, status_code=404)

    return FileResponse(
        docx_path,
        filename=docx_path.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
