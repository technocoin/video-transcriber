import subprocess
from pathlib import Path

def extract_frames(video_path, output_dir, interval=2):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-vf", f"fps=1/{interval}", str(out / "frame_%05d.jpg")],
        check=True
    )
    return [str(p) for p in out.glob("frame_*.jpg")]
