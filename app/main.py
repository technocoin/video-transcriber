from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uuid
from pathlib import Path
from app.queue import get_queue, get_redis
from app.worker import process_job

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

DATA = Path("app/data")
UPLOADS = DATA / "uploads"
OUTPUTS = DATA / "outputs"
UPLOADS.mkdir(parents=True, exist_ok=True)
OUTPUTS.mkdir(parents=True, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload(videos: list[UploadFile] = File(...), frame_interval: int = Form(2)):
    job_id = str(uuid.uuid4())
    upload_dir = UPLOADS / job_id
    output_dir = OUTPUTS / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    for v in videos:
        p = upload_dir / v.filename
        p.write_bytes(await v.read())
        paths.append(str(p))

    r = get_redis()
    r.hset(f"job:{job_id}", mapping={
        "status": "queued",
        "progress": "0",
        "done_files": "0",
        "total_files": str(len(paths)),
        "message": "Queued",
        "result_index": "[]"
    })

    q = get_queue()
    q.enqueue(process_job, video_paths=paths, output_dir=str(output_dir), frame_interval=frame_interval, job_id=job_id)

    return RedirectResponse(f"/jobs/{job_id}", status_code=303)

@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job(job_id: str, request: Request):
    return templates.TemplateResponse("job.html", {"request": request, "job_id": job_id})

@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    return get_redis().hgetall(f"job:{job_id}")
