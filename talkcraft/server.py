import sys
import os

os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["ABSL_MIN_LOG_LEVEL"] = "2"

import asyncio
import json
from pathlib import Path
from typing import Optional

_ex_root = str(Path(__file__).resolve().parent.parent)
if _ex_root not in sys.path:
    sys.path.insert(0, _ex_root)

import uvicorn
from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from talkcraft.utils.logger import setup_logger, get_logger
from talkcraft.utils.config import config
from talkcraft.engine import TalkCraftEngine
from talkcraft.ui.dashboard import shared_state


logger = get_logger("talkcraft.server")

app = FastAPI(title="TalkCraft API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = TalkCraftEngine()
_broadcast_queue: asyncio.Queue = None
WS_POLL_INTERVAL = 0.25

_llm_client: Optional[any] = None


def _get_llm_client():
    global _llm_client
    if _llm_client is not None:
        return _llm_client
    try:
        from talkcraft_ai.agents.llm_client import LLMClient
        _llm_client = LLMClient()
        logger.info("LLM client loaded for professional feedback")
    except Exception as e:
        logger.warning(f"LLM client not available: {e}")
        _llm_client = None
    return _llm_client


class FeedbackRequest(BaseModel):
    transcription: str
    language: str = ""


class FeedbackResponse(BaseModel):
    english_translation: str = ""
    original_scores: dict = {}
    professional_alternatives: list = []
    tips: list = []


def _poll_engine():
    try:
        engine.poll_updates()
    except Exception:
        pass


def _detect_ffmpeg() -> bool:
    try:
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=3
        )
        return result.returncode == 0
    except Exception:
        return False


@app.on_event("startup")
async def _startup():
    global _broadcast_queue
    _broadcast_queue = asyncio.Queue(maxsize=50)
    if not _detect_ffmpeg():
        logger.warning(
            "ffmpeg NOT detected. MP3/M4A/AAC/WMA files will not load. "
            "Install from https://ffmpeg.org or run: winget install ffmpeg"
        )
    logger.info("Broadcast loop ready")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected")
    try:
        while True:
            _poll_engine()
            state = shared_state.get_state()
            try:
                _broadcast_queue.put_nowait(state)
            except asyncio.QueueFull:
                try:
                    _broadcast_queue.get_nowait()
                    _broadcast_queue.put_nowait(state)
                except asyncio.QueueEmpty:
                    pass
            try:
                data = await asyncio.wait_for(
                    _broadcast_queue.get(), timeout=WS_POLL_INTERVAL
                )
            except asyncio.TimeoutError:
                continue
            try:
                await websocket.send_json(data)
            except Exception:
                break
    except asyncio.CancelledError:
        pass
    except Exception:
        pass
    finally:
        logger.debug("WebSocket client disconnected")


@app.get("/state")
async def get_state():
    return shared_state.get_state()


@app.post("/start-mic")
async def start_mic():
    engine.start_mic()
    shared_state.input_mode = "mic"
    return {"status": "ok", "mode": "mic"}


@app.post("/start-file")
async def start_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    safe_name = Path(file.filename).name
    file_path = upload_dir / safe_name
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        success = engine.start_file(str(file_path))
        if not success:
            ext = Path(file.filename).suffix.lower()
            if ext in (".mp3", ".m4a", ".aac", ".wma") and not _detect_ffmpeg():
                detail = (
                    f"Cannot process '{file.filename}'. "
                    "ffmpeg is required for MP3/M4A/AAC/WMA files. "
                    "Install ffmpeg: https://ffmpeg.org  or  winget install ffmpeg"
                )
            else:
                detail = f"Failed to process '{file.filename}'. Unsupported or corrupted audio."
            raise HTTPException(status_code=400, detail=detail)
        shared_state.input_mode = "file"
        return {
            "status": "ok",
            "mode": "file",
            "filename": file.filename,
            "size": len(content),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop")
async def stop():
    engine.stop()
    return {"status": "stopped"}


@app.post("/professional-feedback", response_model=FeedbackResponse)
async def professional_feedback(req: FeedbackRequest):
    text = req.transcription.strip()
    if not text:
        raise HTTPException(status_code=400, detail="No transcription text provided.")

    state = shared_state.get_state()
    scores = {
        "speaking_pace_wpm": state.get("current_wpm", 0),
        "average_pace_wpm": state.get("average_wpm", 0),
        "pace_status": state.get("pace_status", "normal"),
        "filler_words": state.get("filler_count", 0),
        "filler_rate_pct": round(state.get("filler_rate", 0) * 100, 1),
        "grammar_errors": state.get("grammar_errors", 0),
        "total_words": state.get("total_words", 0),
        "session_duration_s": round(state.get("session_duration", 0), 1),
    }

    client = _get_llm_client()
    if client is None or not client.is_available():
        return FeedbackResponse(
            english_translation="",
            original_scores=scores,
            professional_alternatives=[
                "Install Ollama or configure an LLM API to enable professional feedback.",
                "See talkcraft_ai/config.json to set up your LLM endpoint.",
            ],
            tips=["ℹ️ Scores are shown from the current analysis without LLM enhancement."],
        )

    lang_hint = f" (detected language hint: {req.language})" if req.language else ""
    prompt = (
        f"Below is a speech transcription from a communication coaching session{lang_hint}.\n\n"
        f"TRANSCRIPTION:\n{text}\n\n"
        f"ANALYSIS SCORES:\n"
        f"- Speaking pace: {scores['speaking_pace_wpm']} WPM (avg: {scores['average_pace_wpm']} WPM, status: {scores['pace_status']})\n"
        f"- Filler words: {scores['filler_words']} (rate: {scores['filler_rate_pct']}%)\n"
        f"- Grammar issues: {scores['grammar_errors']}\n"
        f"- Total words: {scores['total_words']}\n\n"
        f"Please provide the following:\n"
        f"1. **english_translation**: If the transcription is not in English, translate it to English. "
        f"If it is already in English, repeat it as-is.\n"
        f"2. **professional_alternatives**: Rewrite 3-5 key sentences from the speech in a more professional, "
        f"polished way. Keep the original meaning but improve clarity, confidence, and impact.\n"
        f"3. **tips**: Provide 2-3 actionable tips for improving this specific speech (focus on delivery, "
        f"structure, filler words, pacing, or grammar).\n\n"
        f"Format your response as valid JSON with exactly these keys:\n"
        f'{{"english_translation": "...", "professional_alternatives": ["...", "..."], "tips": ["...", "..."]}}'
    )

    messages = [
        {
            "role": "system",
            "content": "You are a professional communication coach. Provide clear, actionable feedback."
        },
        {"role": "user", "content": prompt},
    ]

    try:
        response = client.generate(messages)
        result = json.loads(response.content)
        return FeedbackResponse(
            english_translation=result.get("english_translation", ""),
            original_scores=scores,
            professional_alternatives=result.get("professional_alternatives", []),
            tips=result.get("tips", []),
        )
    except json.JSONDecodeError:
        return FeedbackResponse(
            english_translation="",
            original_scores=scores,
            professional_alternatives=["Could not parse LLM response. Try again."],
            tips=[],
        )
    except Exception as e:
        logger.error(f"Professional feedback error: {e}")
        return FeedbackResponse(
            english_translation="",
            original_scores=scores,
            professional_alternatives=[f"Error generating feedback: {str(e)}"],
            tips=[],
        )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "running": engine.is_running,
        "ffmpeg_available": _detect_ffmpeg(),
        "llm_available": _get_llm_client() is not None and _get_llm_client().is_available(),
    }


def main():
    setup_logger("talkcraft.server", level=config.log_level)
    logger.info("=" * 50)
    logger.info("TalkCraft API Server")
    logger.info("=" * 50)
    logger.info(f"API:       http://localhost:8000")
    logger.info(f"WebSocket: ws://localhost:8000/ws")
    logger.info(f"Frontend:  http://localhost:3000")
    logger.info(f"Docs:      http://localhost:8000/docs")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        ws_ping_interval=None,
    )


if __name__ == "__main__":
    main()
