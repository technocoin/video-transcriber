from rq import Worker
from .queue import get_queue, get_redis

from pathlib import Path
import json
import os

from .processing import process_video_to_rows
from .docx_export import rows_to_docx


def update(job_id: str, **fields):
    r = get_redis()
    # convert to strings
    mapping = {k: str(v) for k, v in fields.items()}
    r.hset(f"job:{job_id}", mapping=mapping)


def process_job(job_id: str, video_paths: list[str], output_dir: str, frame_interval: int):
    out_base = Path(output_dir)
    out_base.mkdir(parents=True, exist_ok=True)

    update(job_id, status="running", progress=0, message="Starting job")

    results = []
    total = max(1, len(video_paths))
    done = 0

    for vp in video_paths:
        done += 1
        video_path = Path(vp)
        video_stem = video_path.stem

        # per-video output folder (Dropbox-like within job)
        per_video_dir = out_base / video_stem
        per_video_dir.mkdir(parents=True, exist_ok=True)

        update(
            job_id,
            message=f"Processing {video_path.name} ({done}/{total})",
            done_files=done-1,
            progress=int(((done-1) / total) * 100)
        )

        rows = process_video_to_rows(
            video_path=str(video_path),
            job_dir=str(per_video_dir),
            frame_interval_seconds=frame_interval,
        )

        docx_path = per_video_dir / f"{video_stem}_transcript.docx"
        rows_to_docx(rows, str(docx_path), template_path="app/templates/template.docx")

        results.append({
            "video": video_path.name,
            "docx_path": str(docx_path)
        })

        update(
            job_id,
            done_files=done,
            progress=int((done / total) * 100),
            result_index=json.dumps(results)
        )

    update(job_id, status="done", message="All files processed", progress=100)


def main():
    q = get_queue()
    w = Worker([q], connection=q.connection)
    w.work(with_scheduler=True)


if __name__ == "__main__":
    main()
