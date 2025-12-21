import whisper
_model = None

def transcribe_audio(audio_path):
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model.transcribe(audio_path)["segments"]
