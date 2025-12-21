import subprocess
from pathlib import Path


def extract_frames(video_path: str, output_dir: str, interval: int = 2) -> list[str]:
    """
    Extract 1 frame every `interval` seconds
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    frame_pattern = output_dir / "frame_%05d.jpg"

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-vf",
            f"fps=1/{interval}",
            str(frame_pattern),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    return sorted(str(p) for p in output_dir.glob("frame_*.jpg"))
