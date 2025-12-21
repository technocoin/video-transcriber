import os
import json
from pathlib import Path

from rq import get_current_job

from app.progress import update_progress
from app.processing.audio import extract_audio
from app.processing.whisper import transcribe_audio
from app.processing.frames import extract_frames
from app.processing.docx import generate_docx


def process_job(video_paths, output_dir, frame_interval):
    job = get_current_job()
    job_id = job.id

    total_files = len(video_paths)
    results = []

    update_progress(
        job_id,
        status="running",
        progress=5,
        message="Job started",
        done_files=0,
    )

    for index, video_path in enumerate(video_paths, start=1):
        video_name = Path(video_path).name
        base_percent = int(((index - 1) / total_files) * 100)
        step = int(100 / total_files)

        update_progress(
            job_id,
            message=f"Extracting audio from {video_name}",
            progress=base_percent + int(step * 0.2),
        )

        audio_path = extract_audio(video_path)

        update_progress(
            job_id,
            message=f"Transcribing {video_name}",
            progress=base_percent + int(step * 0.4),
        )

        transcript = transcribe_audio(audio_path)

        update_progress(
            job_id,
            message=f"Extracting frames from {video_name}",
            progress=base_percent + int(step * 0.6),
        )

        frames = extract_frames(video_path, interval=frame_interval)

        update_progress(
            job_id,
            message=f"Generating DOCX for {video_name}",
            progress=base_percent + int(step * 0.85),
        )

        docx_path = generate_docx(
            video_name=video_name,
            transcript=transcript,
            frames=frames,
            output_dir=output_dir,
        )

        results.append(
            {
                "video": video_name,
                "docx_path": docx_path,
            }
        )

        update_progress(
            job_id,
            done_files=index,
            progress=base_percent + step,
        )

    update_progress(
        job_id,
        status="done",
        progress=100,
        message="All files processed",
        result_index=results,
    )
