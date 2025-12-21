import os
import uuid
from pathlib import Path
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    abort,
)
from redis import Redis
from rq import Queue
from rq.job import Job

from app.worker import process_job
from app.progress import get_progress


# -------------------------------------------------------------------
# App setup
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024 * 1024  # 5GB


# -------------------------------------------------------------------
# Redis / RQ
# -------------------------------------------------------------------

redis_conn = Redis(host="redis", port=6379)
q = Queue("jobs", connection=redis_conn)


# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("videos")
        frame_interval = int(request.form.get("frame_interval", 2))

        if not files or not files[0].filename:
            return "No files uploaded", 400

        # Date-based folder structure (Dropbox-like)
        now = datetime.utcnow()
        job_folder = now.strftime("%Y/%m/%d")

        upload_subdir = UPLOAD_DIR / job_folder / str(uuid.uuid4())
        output_subdir = OUTPUT_DIR / job_folder / upload_subdir.name

        upload_subdir.mkdir(parents=True, exist_ok=True)
        output_subdir.mkdir(parents=True, exist_ok=True)

        saved_files = []
        for f in files:
            filename = f.filename
            path = upload_subdir / filename
            f.save(path)
            saved_files.append(str(path))

        # ------------------------------------------------------------
        # IMPORTANT: capture the RQ job object
        # ------------------------------------------------------------
        job = q.enqueue(
            process_job,
            video_paths=saved_files,
            output_dir=str(output_subdir),
            frame_interval=frame_interval,
            job_timeout=60 * 60 * 3,  # 3 hours
        )

        # Redirect using the *RQ job ID*
        return redirect(url_for("job_progress", job_id=job.id))

    return render_template("index.html")


@app.route("/jobs/<job_id>")
def job_progress(job_id):
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        abort(404)

    progress = get_progress(job_id)

    return render_template(
        "job_progress.html",
        job_id=job_id,
        job_status=job.get_status(),
        progress=progress,
    )


@app.route("/outputs/<path:filepath>")
def download_output(filepath):
    full_path = OUTPUT_DIR / filepath
    if not full_path.exists():
        abort(404)

    return send_from_directory(
        directory=full_path.parent,
        path=full_path.name,
        as_attachment=True,
    )


# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
