"""M1 check: each region's voice says one short sentence (~20 credits each on Flash).

    python scripts/test_voices.py            # regions with a voice_id that haven't been tested yet
    python scripts/test_voices.py --force    # regenerate (spends credits again)

Clips are saved to data/voice_tests/<region>.mp3. Listen: does each sound like its region?
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from elevenlabs import VoiceSettings  # noqa: E402
from elevenlabs.client import ElevenLabs  # noqa: E402

from app.config import DATA_DIR, REGIONS, settings  # noqa: E402

LINES = {
    "sco": "Aye, the bus is late again. It's baltic.",
    "au": "No worries, mate. See you this arvo.",
    "ng": "How far? Abeg wait small, I'm coming.",
}
FALLBACK_LINE = "Hi there, how are you doing today?"
RATES = {"eleven_flash_v2_5": 0.5, "eleven_turbo_v2_5": 0.5}  # credits per character; others 1.0

OUT_DIR = DATA_DIR / "voice_tests"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    if not settings.elevenlabs_api_key:
        sys.exit("ELEVENLABS_API_KEY is not set in .env")
    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rate = RATES.get(settings.tts_model, 1.0)

    total = 0.0
    for key, region in REGIONS.items():
        out = OUT_DIR / f"{key}.mp3"
        if not region.get("voice_id"):
            print(f"{key}: no voice_id in regions.json, skipping")
            continue
        if out.exists() and not args.force:
            print(f"{key}: already tested -> {out}  (use --force to regenerate)")
            continue
        text = LINES.get(key, FALLBACK_LINE)
        audio = client.text_to_speech.convert(
            voice_id=region["voice_id"],
            text=text,
            model_id=settings.tts_model,
            output_format="mp3_44100_128",
            voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75, speed=1.0),
        )
        out.write_bytes(b"".join(audio))
        credits = len(text) * rate
        total += credits
        print(f"{key}: \"{text}\" -> {out}  (~{credits:.0f} credits)")
    print(f"Estimated credits spent: {total:.0f}")


if __name__ == "__main__":
    main()
