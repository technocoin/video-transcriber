from docx import Document
from docx.shared import Pt
from pathlib import Path


def create_docx(
    output_path: str,
    video_name: str,
    transcript_segments: list[dict],
):
    doc = Document()

    # Title
    title = doc.add_heading(video_name, level=1)
    title.alignment = 1

    doc.add_paragraph("")

    for seg in transcript_segments:
        start = _format_time(seg["start"])
        end = _format_time(seg["end"])
        text = seg["text"].strip()

        p = doc.add_paragraph()
        run = p.add_run(f"[{start} → {end}] ")
        run.bold = True
        run.font.size = Pt(10)

        run2 = p.add_run(text)
        run2.font.size = Pt(11)

        doc.add_paragraph("")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)


def _format_time(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"
