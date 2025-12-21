import subprocess
from pathlib import Path

def extract_audio(video_path):
    out = Path(video_path).with_suffix(".wav")
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", "16000", str(out)],
        check=True
    )
    return str(out)
