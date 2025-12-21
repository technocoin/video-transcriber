🎬 Video Transcriber (Docker • Open Source • Offline)

A self-hosted, fully open-source video transcription web app that converts uploaded videos into professionally formatted Word (DOCX) transcripts using OpenAI Whisper (local) — no paid APIs, no cloud dependencies.

Designed to run on Docker / Docker Compose, including ZimaOS, NAS devices, and home servers.

✨ Features

📁 Upload multiple videos at once

🎧 Automatic audio extraction (FFmpeg)

🧠 Offline speech-to-text using Whisper

🖼 Optional frame extraction (1 frame every N seconds)

📄 DOCX transcript generation with timestamps

📊 Job queue with background worker (Redis + RQ)

📈 Live progress bar (Redis-backed)

🐳 Fully containerised (Docker Compose)

💯 100% free & open-source

🧱 Tech Stack
Component	Technology
Web UI	FastAPI + Jinja2
Background Jobs	Redis + RQ
Transcription	OpenAI Whisper (local)
Media Processing	FFmpeg
Document Output	python-docx
Deployment	Docker + Docker Compose

📂 Project Structure
video-transcriber/
│
├── app/
│   ├── main.py              # FastAPI web app
│   ├── worker.py            # Background job worker
│   ├── queue.py             # Redis / RQ helpers
│   ├── progress.py          # Job progress tracking
│   │
│   ├── processing/
│   │   ├── audio.py         # Audio extraction (ffmpeg)
│   │   ├── whisper.py       # Whisper transcription
│   │   ├── frames.py        # Frame extraction
│   │   └── docx.py          # DOCX generation
│   │
│   ├── templates/
│   │   ├── index.html       # Upload page
│   │   └── job.html         # Progress page
│   │
│   └── static/
│       └── style.css
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md

🚀 Installation (Docker – Recommended)
1️⃣ Prerequisites

Make sure you have installed:

Docker

Docker Compose

Check with:

docker --version
docker compose version

2️⃣ Clone the Repository
git clone https://github.com/technocoin/video-transcriber.git
cd video-transcriber

3️⃣ Build & Start the App
docker compose build
docker compose up


⏳ First run may take a few minutes (Whisper model download).

4️⃣ Open the App

The web interface runs on port 8050:

http://localhost:8050


(or replace localhost with your server / NAS IP)

🖥 How to Use

Open the web app

Upload one or more video files

Choose frame interval (default: 1 frame every 2 seconds)

Submit the job

Watch live progress

DOCX transcripts are generated per video

Output files are saved under:

app/data/outputs/<job_id>/

📊 Progress Tracking

Each job has a unique Job ID

Progress is stored in Redis

UI polls job status every 500ms

Progress updates incrementally as each video finishes

⚙ Configuration Notes
Change Web Port

The app is currently configured to run on port 8050.
If you want to change it, edit:

docker-compose.yml

ports:
  - "8050:8000"

🧪 Supported Formats

Video: MP4, MOV, MKV, AVI (anything FFmpeg supports)

Audio: Extracted automatically

Output: .docx

🧠 Whisper Model

Default model:

whisper.load_model("base")


You can change this to:

"tiny" (faster, less accurate)

"small"

"medium" (slower, more accurate)

In:

app/processing/whisper.py

🛠 Troubleshooting
App builds but does nothing

Ensure Redis container is running

Check worker logs:

docker compose logs worker

Whisper not found

Rebuild without cache:

docker compose build --no-cache

Progress bar stuck

Redis must be reachable at redis:6379

Worker must be running

🔐 Privacy & Security

No data leaves your machine

No API keys required

Fully offline once built

Ideal for sensitive or private content

📌 Roadmap Ideas

Embed frame images into DOCX

ZIP download of results

Per-file progress bars

Multi-language support

GPU acceleration

User authentication

📄 License

MIT License
Free to use, modify, and self-host.

🙌 Credits

Built with ❤️ using:

FastAPI

Redis + RQ

OpenAI Whisper

FFmpeg

Docker
