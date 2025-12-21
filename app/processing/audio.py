import subprocess
from pathlib import Path


def extract_audio(video_path: str) -> str:
    """
    Extract mono 16kHz WAV audio from video using ffmpeg
    """
    video_path = Path(video_path)
    audio_path = video_path.with_suffix(".wav")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(audio_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    return str(audio_path)
