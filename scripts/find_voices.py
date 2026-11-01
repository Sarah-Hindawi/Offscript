"""Search the ElevenLabs Voice Library, or add a shared voice to your account.

Search (free, no credits):
    python scripts/find_voices.py --language en --accent scottish
    python scripts/find_voices.py --language en --locale en-AU --gender female
    python scripts/find_voices.py --search glasgow

Add (uses one of your 3 free custom voice slots):
    python scripts/find_voices.py --add <public_user_id> <voice_id> --name Offscript-SCO

Accent labels in the library are inconsistent, so this prints whatever the API returns
and leaves the choice to you. Open the preview URLs in a browser to listen.
"""
import argparse
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings  # noqa: E402

API = "https://api.elevenlabs.io/v1"


def headers() -> dict:
    if not settings.elevenlabs_api_key:
        sys.exit("ELEVENLABS_API_KEY is not set in .env")
    return {"xi-api-key": settings.elevenlabs_api_key}


def search(args) -> None:
    params = {
        "language": args.language,
        "accent": args.accent,
        "locale": args.locale,
        "gender": args.gender,
        "age": args.age,
        "search": args.search,
        "page_size": args.limit,
    }
    params = {k: v for k, v in params.items() if v}
    r = httpx.get(f"{API}/shared-voices", params=params, headers=headers(), timeout=30)
    r.raise_for_status()
    voices = r.json().get("voices", [])
    if not args.include_restricted:
        # Some library voices can't be added on the free plan
        voices = [v for v in voices if v.get("free_users_allowed", True)]
    if not voices:
        print("No voices found. Try fewer filters, or --search with a city/country name.")
        return

    for v in voices:
        print(f"\n{v.get('name')}  [{v.get('gender')}, {v.get('age')}, accent={v.get('accent')}, "
              f"locale={v.get('locale')}]  used by {v.get('cloned_by_count', '?')}")
        desc = (v.get("description") or v.get("descriptive") or "").strip().replace("\n", " ")
        if desc:
            print(f"  {desc[:160]}")
        for lang in v.get("verified_languages") or []:
            print(f"  verified: {lang.get('language')} accent={lang.get('accent')} "
                  f"locale={lang.get('locale')}")
        print(f"  preview: {v.get('preview_url')}")
        print(f"  add:     python scripts/find_voices.py --add {v.get('public_owner_id')} "
              f"{v.get('voice_id')} --name Offscript-XXX")
    print(f"\n{len(voices)} voice(s)")


def add(public_user_id: str, voice_id: str, name: str) -> None:
    r = httpx.post(
        f"{API}/voices/add/{public_user_id}/{voice_id}",
        json={"new_name": name},
        headers=headers(),
        timeout=30,
    )
    if r.status_code != 200:
        sys.exit(f"Add failed ({r.status_code}): {r.text}")
    print(f"Added '{name}'. Paste this voice_id into regions.json: {r.json()['voice_id']}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--language", default="en")
    p.add_argument("--accent")
    p.add_argument("--locale", help="e.g. en-GB, en-AU, en-IE, en-ZA")
    p.add_argument("--gender", choices=["male", "female", "neutral"])
    p.add_argument("--age", choices=["young", "middle_aged", "old"])
    p.add_argument("--search", help="free-text search over name/description")
    p.add_argument("--limit", type=int, default=15)
    p.add_argument("--include-restricted", action="store_true",
                   help="also show voices that free-plan users can't add")
    p.add_argument("--add", nargs=2, metavar=("PUBLIC_USER_ID", "VOICE_ID"))
    p.add_argument("--name", help="name for the added voice, e.g. Offscript-SCO")
    args = p.parse_args()

    if args.add:
        if not args.name:
            p.error("--add needs --name")
        add(*args.add, args.name)
    else:
        search(args)


if __name__ == "__main__":
    main()
