from fastapi import APIRouter
from talkcraft_enterprise.multilingual.engine import multilingual_engine
from talkcraft_enterprise.multilingual.languages import language_manager

router = APIRouter(prefix="/api/multilingual", tags=["multilingual"])


@router.get("/languages")
async def get_languages():
    return {"languages": language_manager.get_supported_languages()}


@router.get("/languages/{code}")
async def get_language(code: str):
    lang = language_manager.get_language(code)
    if not lang:
        return {"error": "Language not found"}
    return lang


@router.post("/session/start")
async def start_session(user_id: int, language: str = "en", session_type: str = "practice"):
    return multilingual_engine.start_session(user_id, language, session_type)


@router.post("/session/process")
async def process_transcription(user_id: int, text: str):
    return multilingual_engine.process_transcription(user_id, text)


@router.post("/session/end")
async def end_session(user_id: int):
    return multilingual_engine.end_session(user_id)


@router.get("/session/{user_id}")
async def get_session_state(user_id: int):
    return multilingual_engine.get_session_state(user_id) or {"error": "No active session"}


@router.post("/pronunciation")
async def analyze_pronunciation(text: str, language: str, expected_text: str):
    return multilingual_engine.analyze_pronunciation(text, language, expected_text)


@router.get("/phrase/{lang_code}/{phrase_key}")
async def get_phrase(lang_code: str, phrase_key: str):
    return {"phrase": language_manager.get_phrase(lang_code, phrase_key)}
