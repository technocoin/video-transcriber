import os
import subprocess
from pathlib import Path
from typing import List, Dict

from faster_whisper import WhisperModel
from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{p.stderr}")


def format_mmss(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}{s:02d}"


def extract_audio(video_path: str, out_wav: str) -> None:
    run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        out_wav
    ])


def extract_frames(video_path: str, frames_dir: str, every_n_seconds: int) -> List[Dict]:
    Path(frames_dir).mkdir(parents=True, exist_ok=True)
    fps = 1.0 / float(every_n_seconds)
    out_pattern = str(Path(frames_dir) / "frame_%05d.jpg")

    run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"fps={fps}",
        "-q:v", "2",
        out_pattern
    ])

    frames = sorted(Path(frames_dir).glob("frame_*.jpg"))
    return [{"second": i * every_n_seconds, "path": str(f)} for i, f in enumerate(frames)]


def transcribe_whisper(audio_wav: str, model_size: str = "small", device: str = "cpu") -> List[Dict]:
    model = WhisperModel(model_size, device=device, compute_type="int8" if device == "cpu" else "float16")
    segments, _info = model.transcribe(audio_wav, vad_filter=True)

    out = []
    for seg in segments:
        out.append({"start": float(seg.start), "end": float(seg.end), "text": seg.text.strip()})
    return out


class VisionCaptioner:
    def __init__(self, device: str = "cpu"):
        self.device = device
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model.to(device)

    @torch.inference_mode()
    def caption(self, image_path: str) -> str:
        image = Image.open(image_path).convert("RGB")
        inputs = self.processor(image, return_tensors="pt").to(self.device)
        out = self.model.generate(**inputs, max_new_tokens=30)
        return self.processor.decode(out[0], skip_special_tokens=True).strip()


def process_video_to_rows(video_path: str, job_dir: str, frame_interval_seconds: int = 2) -> List[Dict]:
    job = Path(job_dir)
    job.mkdir(parents=True, exist_ok=True)

    audio_path = job / "audio.wav"
    frames_dir = job / "frames"

    model_size = os.getenv("WHISPER_MODEL", "small")
    device = os.getenv("DEVICE", "cpu")

    extract_audio(video_path, str(audio_path))
    frames = extract_frames(video_path, str(frames_dir), frame_interval_seconds)
    segments = transcribe_whisper(str(audio_path), model_size=model_size, device=device)

    captioner = VisionCaptioner(device=device)

    frame_caps = []
    for fr in frames:
        cap = captioner.caption(fr["path"])
        frame_caps.append({"second": fr["second"], "text": cap})

    rows = []
    for seg in segments:
        vis = [f["text"] for f in frame_caps if f["second"] >= int(seg["start"]) and f["second"] <= int(seg["end"])]
        uniq = []
        for v in vis:
            if v and v not in uniq:
                uniq.append(v)

        rows.append({
            "Time": format_mmss(seg["start"]),
            "Sound": seg["text"],
            "Vision": " ".join(uniq[:2]) if uniq else "No major visual change.",
            "Compliance": ""
        })

    return rows
