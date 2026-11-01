"""Environment settings plus the static content tables: regions, levels, scenarios."""
import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

STATIC_DIR = ROOT / "static"
DATA_DIR = ROOT / "data"
EXERCISES_DIR = DATA_DIR / "exercises"
AUDIO_DIR = DATA_DIR / "audio"
METRICS_FILE = DATA_DIR / "metrics.jsonl"
REGIONS_FILE = ROOT / "regions.json"


@dataclass(frozen=True)
class Settings:
    elevenlabs_api_key: str
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    tts_model: str
    credit_budget: float
    target_language: str
    explanation_language: str


def load_settings() -> Settings:
    return Settings(
        elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY", ""),
        llm_base_url=os.getenv("LLM_BASE_URL", "https://api.featherless.ai/v1"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_model=os.getenv("LLM_MODEL", ""),
        tts_model=os.getenv("TTS_MODEL", "eleven_flash_v2_5"),
        credit_budget=float(os.getenv("CREDIT_BUDGET", "8000")),
        target_language=os.getenv("TARGET_LANGUAGE", "English"),
        explanation_language=os.getenv("EXPLANATION_LANGUAGE", "English"),
    )


settings = load_settings()


def load_regions() -> dict:
    with open(REGIONS_FILE, encoding="utf-8") as f:
        return json.load(f)


REGIONS = load_regions()


@dataclass(frozen=True)
class Level:
    id: int
    name: str
    tts_speed: float      # ElevenLabs voice_settings.speed, valid range 0.7-1.2
    playback_rate: float  # browser playbackRate, for anything faster than 1.2
    noise_volume: float
    style: str


LEVELS: dict[int, Level] = {
    1: Level(1, "Classroom", 0.85, 1.0, 0.0,
             "Standard vocabulary, short sentences, only 1-2 regional words."),
    2: Level(2, "Visitor", 1.0, 1.0, 0.15,
             "Natural spoken English with a few regional words."),
    3: Level(3, "Local", 1.15, 1.0, 0.30,
             "Heavy regional vocabulary, fillers and contractions, like a real local talking casually."),
    4: Level(4, "Real life", 1.2, 1.1, 0.45,
             "Heavy regional vocabulary, fillers and contractions, like a real local talking casually and quickly."),
}


@dataclass(frozen=True)
class Scenario:
    id: str
    name: str
    noise: str | None  # file in static/noise/, or None for silence
    description: str


SCENARIOS: dict[str, Scenario] = {
    "cafe": Scenario("cafe", "Cafe", "cafe.mp3",
                     "A server explaining today's specials and asking what you want."),
    "taxi": Scenario("taxi", "Taxi", "street.mp3",
                     "A taxi driver making small talk about traffic, the route and the price."),
    "station": Scenario("station", "Station", "station.mp3",
                        "A platform announcement about a delay or a platform change."),
    "voicemail": Scenario("voicemail", "Voicemail", None,
                          "A landlord or friend leaving you a voicemail with a time, a place and a request."),
    "directions": Scenario("directions", "Directions", "street.mp3",
                           "A stranger giving you walking directions."),
    "work": Scenario("work", "Work", "office.mp3",
                     "A coworker catching you before a meeting about a changed deadline or plan."),
}
