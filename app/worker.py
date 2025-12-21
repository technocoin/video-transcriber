from rq import get_current_job
from pathlib import Path
from app.progress import update_progress
from app.processing.audio import extract_audio
from app.processing.whisper import transcribe_audio
from app.processing.frames import extract_frames
from app.processing.docx import generate_docx

def process_job(video_paths, output_dir, frame_interval, job_id=None):
    job = get_current_job()
    job_id = job_id or job.id
    total = len(video_paths)
    results = []
    update_progress(job_id, status="running", progress=5, message="Started", done_files=0, total_files=total)

    for i, vp in enumerate(video_paths, start=1):
        audio = extract_audio(vp)
        transcript = transcribe_audio(audio)
        frames = extract_frames(vp, output_dir, frame_interval)
        docx = generate_docx(Path(vp).name, transcript, frames, output_dir)
        results.append({"video": Path(vp).name, "docx_path": docx})
        update_progress(job_id, progress=int(i / total * 100), done_files=i)

    update_progress(job_id, status="done", progress=100, message="Done", result_index=results)
