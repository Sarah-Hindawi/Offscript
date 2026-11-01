# Earshot — train your ear for real-world English accents

> English learners study with clear, neutral textbook audio. Then they start a job with a Glaswegian manager, an Australian client and an Indian team lead, and can't follow the meeting. Earshot trains you on **regional accents, real speed, and background noise**, ramping up until it sounds like real life.

This file is the build spec. **Claude Code: read this whole file first, then build milestone by milestone (section 8). Stop after each milestone, run its check, and tell me what to verify before moving on.**

---

## 1. Product

The user picks a **region**, a **scenario**, and a **level**. The app plays a short clip of a local speaking *to them* (a waiter, a taxi driver, a coworker, a station announcement), mixed with background noise. The user answers one comprehension question. Then the app reveals the transcript with **regional words highlighted and explained**, and offers a slow, clean replay.

The core idea is the **difficulty ladder**: start slow, standard and quiet, then increase speed, slang and noise until it matches real life.

The key insight: an accent isn't only pronunciation. It's also vocabulary and phrasing (Scotland: *wee*, *cannae*; Australia: *arvo*, *heaps*; India: *prepone*, *today itself*). So the LLM writes the script **in the region's dialect**, and a **native voice from that region** reads it.

**Users:** international students, immigrants, and people on global teams who learned "textbook" English.

### MVP (today)
- 3 regions × ~6 scenarios × 4 levels
- Single speaker per clip (monologue addressed to the listener)
- Multiple-choice comprehension question
- Transcript reveal with highlighted regional terms + tooltip explanations
- "Replay clean" button (slower, no noise)
- Everything cached; a pre-generated library so the demo never waits or spends credits live

### Stretch (later)
- Speak your answer out loud (ElevenLabs speech-to-text), graded by the LLM
- Speed realism experiment (section 9)
- Two-person dialogues (needs more voice slots)
- More regions / other languages

---

## 2. Stack

- **Python 3.11+**, **FastAPI** + **uvicorn**
- **Frontend:** one static page, vanilla HTML/CSS/JS, served by FastAPI. No build step, no framework.
- **TTS:** ElevenLabs Python SDK (`pip install elevenlabs`)
- **LLM:** any OpenAI-compatible endpoint via the `openai` SDK. Default: **Featherless AI** (free for LarpHacks participants). Model is configurable.
- `pydantic`, `python-dotenv`, `httpx`
- Background noise: CC0 audio loops from freesound.org (no credits spent)

---

## 3. Repo layout

```
earshot/
  app/
    main.py        # FastAPI app + routes
    config.py      # env settings, loads regions.json, levels, scenarios
    models.py      # pydantic schemas (Exercise, Question, RegionalTerm, ...)
    llm.py         # script generation + validation + retries
    tts.py         # TTSProvider protocol, ElevenLabsTTS, cache wrapper
    cache.py       # content-addressed file cache
    metrics.py     # append-only JSONL metrics + credit guard
  static/
    index.html
    app.js
    style.css
    noise/         # cafe.mp3, street.mp3, station.mp3, office.mp3 (user downloads, CC0)
  data/
    exercises/     # generated exercise JSON (the library)
    audio/         # cached mp3s, named by hash
    metrics.jsonl
  scripts/
    find_voices.py     # search Voice Library by language/accent, optionally add
    pregenerate.py     # build the exercise library offline
    check_credits.py   # show credits used / remaining
  regions.json
  .env.example
  requirements.txt
  README.md
```

---

## 4. Configuration

### `.env.example`
```
ELEVENLABS_API_KEY=
LLM_BASE_URL=https://api.featherless.ai/v1
LLM_API_KEY=
LLM_MODEL=            # pick a strong instruct model from the Featherless catalog
TTS_MODEL=eleven_flash_v2_5
CREDIT_BUDGET=8000    # app refuses new TTS once local estimate passes this
TARGET_LANGUAGE=English
EXPLANATION_LANGUAGE=English
```

### `regions.json` (voice_ids filled in after milestone 1)
```json
{
  "sco": {
    "name": "Scotland (Glasgow)",
    "locale": "en-GB",
    "voice_id": "",
    "dialect_notes": "aye (yes), naw (no), wee (small), cannae / dinnae / willnae (can't / don't / won't), weans (kids), the now (right now), pure as an intensifier (pure brilliant), messages (groceries), outwith (outside of), it's baltic (it's freezing), how's it gaun? (how's it going?), how (= why, e.g. 'how did you no come?'). Fillers: like, ken (more east coast), so it is / so I am as sentence tags."
  },
  "au": {
    "name": "Australia (Sydney)",
    "locale": "en-AU",
    "voice_id": "",
    "dialect_notes": "arvo (afternoon), brekkie (breakfast), servo (gas station), bottle-o (liquor store), heaps (very / a lot), reckon (think), keen (eager), no worries, she'll be right (it'll be fine), how ya going? (how are you), ute (pickup truck), esky (cooler), thongs (flip-flops), Maccas (McDonald's). Lots of shortening + -o / -ie endings. Fillers: yeah nah, nah yeah, mate."
  },
  "in": {
    "name": "India (Indian English)",
    "locale": "en-IN",
    "voice_id": "",
    "dialect_notes": "prepone (move earlier), do the needful, revert (reply), today itself / now itself (emphasis), only as emphasis (I am here only), na? / no? as a tag question, out of station (out of town), cousin-brother / cousin-sister, timepass, don't take tension (don't worry), batchmate, PG (paying-guest accommodation), lakh / crore (100,000 / 10,000,000). Fillers: actually, basically, see, yaar (casual)."
  }
}
```
Alternate regions if a voice is poor: Ireland (Dublin), Nigeria (Lagos), Southern US, Jamaica, South Africa.

### Levels (in `config.py`)

| Level | Name       | TTS speed | Browser playbackRate | Noise volume | Script style |
|-------|------------|-----------|----------------------|--------------|--------------|
| 1     | Classroom  | 0.85      | 1.0                  | 0.0          | Standard vocabulary, short sentences, 1–2 regional words |
| 2     | Visitor    | 1.0       | 1.0                  | 0.15         | Natural, a few regional words |
| 3     | Local      | 1.15      | 1.0                  | 0.30         | Heavy regional vocab + fillers + contractions |
| 4     | Real life  | 1.2       | 1.1                  | 0.45         | Same as 3, faster, noisier |

- ElevenLabs `voice_settings.speed` only supports **0.7–1.2**. Anything faster than 1.2 must be done with browser `playbackRate` (that's why level 4 uses both).
- Noise volumes are starting points. Tune by ear.

### Scenarios (in `config.py`)
Each is a monologue addressed to the listener, with its noise file:
- `cafe` (cafe.mp3): server explaining today's specials and asking what you want
- `taxi` (street.mp3): driver making small talk about traffic, route, price
- `station` (station.mp3): platform announcement about a delay or platform change
- `voicemail` (none): landlord or friend leaving a message with a time, place and request
- `directions` (street.mp3): stranger giving walking directions
- `work` (office.mp3): coworker catching you before a meeting about a changed deadline or plan

---

## 5. External APIs (verified Nov 2026; check docs if anything fails)

Docs index for agents: https://elevenlabs.io/docs/llms.txt (full docs in one file: https://elevenlabs.io/docs/llms-full.txt)

### 5.1 Text to speech
```python
import os
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

audio_iter = client.text_to_speech.convert(
    voice_id=voice_id,
    text=text,
    model_id="eleven_flash_v2_5",          # or "eleven_multilingual_v2"
    output_format="mp3_44100_128",
    voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75, speed=speed),
)
audio_bytes = b"".join(audio_iter)          # convert() yields chunks
```
- **Models:** `eleven_flash_v2_5` costs 0.5 credit per character; `eleven_multilingual_v2` costs 1 credit per character and is higher quality. Use Flash during development. Optionally compare both by ear for accent fidelity before pre-generating the final library.
- **Speed:** 0.7–1.2, all voices and models.
- Ref: https://elevenlabs.io/docs/overview/models

### 5.2 Finding regional voices (Voice Library)
Use plain HTTP (httpx) for these two calls; header `xi-api-key: <key>`.

- **Search:** `GET https://api.elevenlabs.io/v1/shared-voices` with query params such as `language=en`, `accent=...`, `locale=...`, `gender`, `age`, `search`, `page_size`.
  Ref: https://elevenlabs.io/docs/api-reference/voices/voice-library/get-shared
- **Add to account:** `POST https://api.elevenlabs.io/v1/voices/add/{public_user_id}/{voice_id}` with JSON body `{"new_name": "Earshot-SCO"}`. Use the `voice_id` returned in the response afterwards.
  Ref: https://elevenlabs.io/docs/api-reference/voices/voice-library/share

**Free plan limit:** 3 custom voices (from Voice Library or Voice Design). That's why the MVP has exactly 3 regions. Accent labels in the library can be inconsistent, so `find_voices.py` should print what the API actually returns (name, accent, locale/verified language info, gender, age, preview_url) and let the user choose. Don't hardcode accent strings.

### 5.3 Credits
- Free plan: 10,000 credits/month. On Flash that's ~20,000 characters.
- Track locally: `chars × model_rate` per call → `data/metrics.jsonl`.
- `scripts/check_credits.py`: call `GET https://api.elevenlabs.io/v1/user/subscription` and print character count vs. limit (verify field names in docs).

### 5.4 LLM (OpenAI-compatible)
```python
from openai import OpenAI
llm = OpenAI(base_url=os.environ["LLM_BASE_URL"], api_key=os.environ["LLM_API_KEY"])
resp = llm.chat.completions.create(model=os.environ["LLM_MODEL"], messages=[...], temperature=0.9)
```
Ref: https://featherless.ai/docs/api-overview-and-common-options
Open models may not support strict JSON mode, so parse defensively (section 6.2).

---

## 6. Core logic

### 6.1 Schemas (`models.py`)
```python
class RegionalTerm(BaseModel):
    term: str          # exactly as it appears in the text
    meaning: str       # plain-English meaning
    note: str          # why it's regional, e.g. "Australian; elsewhere: afternoon"

class Question(BaseModel):
    prompt: str
    options: list[str] # 4 options
    answer_index: int
    explanation: str

class Exercise(BaseModel):
    id: str            # hash of region|scenario|level|variant
    region: str
    scenario: str
    level: int
    text: str          # what the voice says
    regional_terms: list[RegionalTerm]
    question: Question
    audio_file: str | None   # None => frontend uses browser TTS fallback
```

### 6.2 Script generation (`llm.py`)
System prompt includes: region name + `dialect_notes`, scenario description, level style, and these rules:
- Monologue, spoken **to the listener** ("you"), natural spoken register, not written prose.
- **Hard cap: 350 characters** for `text` (credit budget).
- Level 3–4: include fillers, contractions and regional vocabulary a real local would use.
- **Sound like a real person from the region, not a caricature.** Use regional words at a natural frequency; don't stack slang into every sentence; no jokes about the region or its people.
- Keep it PG. Mild slang is fine; no slurs or vulgarity.
- The question must require actually understanding the audio (a time, place, price, or request), not general knowledge.
- Return **only** JSON matching the schema.

Validation after parsing (retry up to 2 times on failure, feeding the error back to the model):
- Extract the first `{...}` block from the response, then validate with pydantic.
- `len(text) <= 350`.
- Drop any `regional_term` whose `term` doesn't appear in `text` (case-insensitive). LLMs invent these.
- `0 <= answer_index < len(options)`, and exactly 4 options.

### 6.3 TTS + cache (`tts.py`, `cache.py`)
```python
class TTSProvider(Protocol):
    def synthesize(self, text: str, voice_id: str, speed: float) -> bytes: ...
```
- `ElevenLabsTTS` implements it.
- `CachedTTS` wraps any provider. Key = `sha256(model_id|voice_id|speed|text)`. Files go in `data/audio/<key>.mp3`. A cache hit costs 0 credits and is logged as a hit.
- **Credit guard:** before a real call, estimate cost; if the running total would exceed `CREDIT_BUDGET`, don't call. Return `audio_file=None` so the frontend falls back to browser TTS.
- **Browser fallback:** the frontend uses `window.speechSynthesis` with `utterance.lang = region.locale`. Robotic, and accent support depends on the OS, but the app keeps working with zero credits.

### 6.4 Metrics (`metrics.py`)
Append one JSON line per event to `data/metrics.jsonl`:
`{ts, event: "llm"|"tts", region, level, latency_ms, chars, est_credits, cache_hit, model}`
`GET /api/stats` aggregates: total credits used, cache hit rate, median LLM and TTS latency. This feeds the README.

---

## 7. API + frontend

### Endpoints
- `GET /` → `static/index.html`
- `GET /api/config` → regions (without voice_ids), scenarios, levels
- `POST /api/exercise` `{region, scenario, level, fresh: bool=false}` → returns a cached exercise from `data/exercises/` if one exists (unless `fresh`), otherwise generates one. Response **hides** `text`, `regional_terms` and the answer: `{id, audio_url | null, locale, playback_rate, noise: {file, volume}, question: {prompt, options}}`
- `POST /api/exercise/{id}/answer` `{choice}` → `{correct, answer_index, explanation, text, regional_terms}`
- `GET /audio/{file}` → static mount of `data/audio/`
- `GET /api/stats`

### Page (single screen, mobile-friendly)
1. Selectors: region, scenario, level (1–4 slider with level names).
2. **Play** button. Two `<audio>` elements: speech, and noise (`loop = true`, `volume` from level). Set `speech.playbackRate` from level; `preservesPitch` stays true (browser default). Start noise ~0.5s before speech and fade it out after.
3. Question + 4 option buttons. Allow replays before answering (count them, show "replays: 2").
4. After answering: correct/incorrect + explanation, then the transcript with each regional term wrapped in `<mark>` and a tooltip (meaning + note).
5. **Replay clean**: same audio, `playbackRate = 0.85`, noise off. Costs no credits.
6. **Next**: new exercise at the same settings.
7. Small footer: credits used this session, cache hit rate (from `/api/stats`).

---

## 8. Build order (milestones)

Each milestone ends with a check. Don't start the next until the check passes.

**M0. Skeleton.** FastAPI serves the static page; `/api/health` returns ok; `.env` loads.
✅ Check: `uvicorn app.main:app --reload`, open http://localhost:8000.

**M1. Voices.** `scripts/find_voices.py --language en [--accent scottish] [--search ...]` prints candidates with preview URLs (searching costs no credits; listen to previews in the browser). `--add <public_user_id> <voice_id> --name Earshot-SCO` adds one and prints the new voice_id. User pastes the 3 ids into `regions.json`.
✅ Check: a tiny script makes each voice say one short sentence (~40 chars, ~20 credits each on Flash). Listen: does each sound like its region?

**M2. Script generation (no TTS cost).** `python -m app.llm --region sco --scenario taxi --level 3` prints a validated Exercise.
✅ Check: run all 3 regions at levels 1 and 4. Level 4 should have clearly more regional vocabulary and fillers, and should read like a real local, not a parody.

**M3. TTS + cache + metrics.** Generate audio for one exercise. Run the same call again.
✅ Check: second run is a cache hit, 0 credits, logged in `metrics.jsonl`.

**M4. Frontend loop.** Full flow from section 7 working end to end.
✅ Check: play → answer → transcript with highlights → replay clean.

**M5. Levels, credit guard, fallback.** All 4 levels apply speed/rate/noise correctly. Set `CREDIT_BUDGET=0` to test the browser TTS fallback.
✅ Check: app still works with the budget at 0.

**M6. Library + README.** `scripts/pregenerate.py --regions sco,au,in --scenarios cafe,taxi,work --levels 1,2,3,4` builds the library, skipping anything already cached, and prints the estimated credit cost **before** running (ask y/n). Then write the README (section 10).
✅ Check: with the network off for TTS, every pre-generated combination still plays.

**Credit math:** ~300 chars × 0.5 credit (Flash) ≈ 150 credits per clip. 3 regions × 3 scenarios × 4 levels = 36 clips ≈ 5,400 credits. Fits in the free 10,000 with room for development, as long as caching works from M3 onward.

---

## 9. Stretch: the speed realism experiment

Question: is **regenerating speech at a faster speed** better than **speeding up playback**? Real fast speakers blur and drop sounds; time-stretching just compresses normal speech.

`scripts/speed_experiment.py`:
1. For N scripts, generate audio at `speed=1.2` (native fast) and at `speed=1.0`.
2. Time-stretch the 1.0 version to the same duration with ffmpeg (`-filter:a atempo=1.2`).
3. Save pairs with random A/B labels plus a hidden answer key CSV.
4. Blind-test with friends: which sounds more natural, and comprehension accuracy on each.
5. Record credits per approach (stretching is free after the first generation).

Results go in the README as a small table. This is the best interview talking point in the project.

---

## 10. README (write at M6)

1. One-line pitch + a **short screen recording with sound** at the top (GitHub plays uploaded .mp4 videos in READMEs).
2. Why: the gap between textbook English and how people actually talk in Glasgow, Sydney or Bangalore.
3. How it works: a simple diagram — `LLM (dialect script) → validation → ElevenLabs TTS (regional voice, speed) → cache → browser (playbackRate + noise mix)`.
4. **Design decisions** (one short paragraph each):
   - Accent = pronunciation + vocabulary (dialect-aware scripts, validated regional terms)
   - Content-addressed cache + pre-generated library (cost and demo reliability)
   - Credit guard + swappable TTS provider with browser fallback
   - Native speed (0.7–1.2) vs. browser time-stretch, and when to use each
5. **Numbers** from `/api/stats`: credits per clip, cache hit rate, median LLM/TTS latency, experiment results.
6. Setup: keys, `find_voices.py`, `pregenerate.py`, run.
7. Credits: ElevenLabs, noise sources (CC0, Freesound).

---

## 11. Human setup (do these while Claude Code builds M0)

1. ElevenLabs API key (the free plan works; the hackathon coupon gives more credits).
2. Featherless API key from the LarpHacks participant setup guide; set `LLM_MODEL`.
3. Download 4 CC0 loops from freesound.org (filter license: Creative Commons 0): café chatter, street traffic, train station, office background. Save to `static/noise/` as `cafe.mp3`, `street.mp3`, `station.mp3`, `office.mp3`.

---

## 12. Switching languages

Everything language-specific lives in `.env` (`TARGET_LANGUAGE`, `EXPLANATION_LANGUAGE`) and `regions.json`. Examples:
- Spanish: Mexico City, Madrid, Buenos Aires
- French: Paris, Québec, Belgium
- Portuguese: São Paulo, Lisbon
- Arabic: Egyptian, Levantine, Gulf

Keep 3 regions on the free plan (3 custom voice slots).
