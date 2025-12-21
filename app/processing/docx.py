from docx import Document
from pathlib import Path

def generate_docx(video_name, transcript, frames, output_dir):
    path = Path(output_dir) / f"{video_name}.docx"
    doc = Document()
    doc.add_heading(video_name, level=1)
    for s in transcript:
        p = doc.add_paragraph()
        p.add_run(f"[{int(s['start'])}-{int(s['end'])}] ").bold = True
        p.add_run(s['text'])
    doc.save(path)
    return str(path)
