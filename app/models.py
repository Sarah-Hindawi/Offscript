from pydantic import BaseModel


class RegionalTerm(BaseModel):
    term: str     # exactly as it appears in the text
    meaning: str  # plain-English meaning
    note: str     # why it's regional, e.g. "Australian; elsewhere: afternoon"


class Question(BaseModel):
    prompt: str
    options: list[str]  # 4 options
    answer_index: int
    explanation: str


class Exercise(BaseModel):
    id: str  # hash of region|scenario|level|variant
    region: str
    scenario: str
    level: int
    text: str  # what the voice says
    regional_terms: list[RegionalTerm]
    question: Question
    audio_file: str | None = None  # None => frontend uses browser TTS fallback
