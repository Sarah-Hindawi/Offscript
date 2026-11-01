from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import AUDIO_DIR, STATIC_DIR, settings

app = FastAPI(title="Offscript")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "env": {
            "elevenlabs_key": bool(settings.elevenlabs_api_key),
            "llm_key": bool(settings.llm_api_key),
            "llm_model": settings.llm_model or None,
            "tts_model": settings.tts_model,
            "credit_budget": settings.credit_budget,
        },
    }


app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
