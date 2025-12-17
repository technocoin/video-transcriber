import os
import uuid
import json
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .queue import get_queue, get_redis
from app.worker import process_job

DATA_DIR = Path("app/data")
UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUTS_DIR = DATA_DIR / "outputs"
JOBS_DIR = DATA_DIR / "jobs"

for p in [UPLOADS_DIR, OUTPUTS_DIR, JOBS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Offline Video Transcriber (Queued)")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def dropbox_like_path(base: Path, job_id: str) -> Path:
    # /base/YYYY/MM/DD/job_id/
    now = datetime.utcnow()
    return base / f"{now.year:04d}" / f"{now.month:02d}" / f"{now.day:02d}" / job_id


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload(
    request: Request,
    videos: list[UploadFile] = File(...),
    frame_interval: int = Form(2),
):
    job_id = str(uuid.uuid4())
    job_upload_dir = dropbox_like_path(UPLOADS_DIR, job_id)
    job_output_dir = dropbox_like_path(OUTPUTS_DIR, job_id)
    job_state_dir = JOBS_DIR / job_id

    job_upload_dir.mkdir(parents=True, exist_ok=True)
    job_output_dir.mkdir(parents=True, exist_ok=True)
    job_state_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for v in videos:
        safe_name = v.filename.replace("/", "_").replace("\\", "_")
        dst = job_upload_dir / safe_name
        with open(dst, "wb") as f:
            f.write(await v.read())
        saved_files.append(str(dst))

    # Initialize status in Redis
    r = get_redis()
    r.hset(f"job:{job_id}", mapping={
        "status": "queued",
        "progress": "0",
        "total_files": str(len(saved_files)),
        "done_files": "0",
        "message": "Job queued",
        "output_dir": str(job_output_dir),
        "created_at": datetime.utcnow().isoformat(),
        "result_index": json.dumps([]),
    })

    q = get_queue()
    q.enqueue(
    process_job,
    video_paths=saved_files,
    output_dir=str(job_output_dir),
    frame_interval=frame_interval,
    job_timeout=60 * 60 * 3
)

    return RedirectResponse(url=f"/jobs/{job_id}", status_code=303)


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_page(request: Request, job_id: str):
    return templates.TemplateResponse("job.html", {"request": request, "job_id": job_id})


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    r = get_redis()
    data = r.hgetall(f"job:{job_id}")
    if not data:
        return JSONResponse({"error": "not found"}, status_code=404)

    # decode bytes
    decoded = {k.decode(): v.decode() for k, v in data.items()}
    # parse result_index if present
    try:
        decoded["result_index"] = json.loads(decoded.get("result_index", "[]"))
    except Exception:
        decoded["result_index"] = []
    return decoded


@app.get("/download/{job_id}/{file_key}")
def download_output(job_id: str, file_key: str):
    """
    file_key is an index into result_index, e.g. 0,1,2...
    """
    r = get_redis()
    data = r.hgetall(f"job:{job_id}")
    if not data:
        return JSONResponse({"error": "not found"}, status_code=404)

    decoded = {k.decode(): v.decode() for k, v in data.items()}
    idx = json.loads(decoded.get("result_index", "[]"))

    try:
        i = int(file_key)
        path = idx[i]["docx_path"]
    except Exception:
        return JSONResponse({"error": "invalid file"}, status_code=400)

    p = Path(path)
    if not p.exists():
        return JSONResponse({"error": "missing file"}, status_code=404)

    return FileResponse(
        str(p),
        filename=p.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
