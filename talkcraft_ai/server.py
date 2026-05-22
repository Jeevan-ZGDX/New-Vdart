import asyncio
import json
import threading
import time
from typing import Dict, Set, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from talkcraft_ai.utils.config import config
from talkcraft_ai.utils.logger import get_logger
from talkcraft_ai.conversation.engine import ConversationEngine
from talkcraft_ai.conversation.modes import MODES, get_topics_for_mode
from talkcraft_ai.conversation.memory import ConversationMemory
from talkcraft_ai.realtime.pipelines import ConversationPipeline, PipelineState
from talkcraft_ai.scoring.conversation_scorer import ConversationScorer
from talkcraft_ai.feedback.live_feedback import FeedbackItem, LiveFeedbackEngine
from talkcraft_ai.audio.tts_engine import TTSEngine
from talkcraft_ai.agents.llm_client import LLMClient

logger = get_logger("server")


class TalkCraftAIServer:
    def __init__(self):
        self._llm = LLMClient()
        self._tts = TTSEngine()
        self._scorer = ConversationScorer()
        self._feedback = LiveFeedbackEngine()
        self._engine = ConversationEngine(self._llm, self._scorer)
        self._pipeline = ConversationPipeline(self._engine, self._tts, self._scorer, self._feedback)
        self._connected_clients: Set[WebSocket] = set()
        self._running = False
        self._broadcast_thread: Optional[threading.Thread] = None
        self._shared_state: Dict = {
            "mode": "casual_conversation",
            "topic": "",
            "difficulty": "intermediate",
            "transcript": [],
            "ai_response": "",
            "scores": {},
            "feedback": [],
            "status": "idle",
            "session_summary": {},
        }
        self._setup_pipeline_callbacks()
        logger.info("TalkCraft AI Server initialized")

    def _setup_pipeline_callbacks(self) -> None:
        self._pipeline.set_callbacks(
            on_transcription=self._on_transcription,
            on_ai_chunk=self._on_ai_chunk,
            on_ai_response=self._on_ai_response,
            on_feedback=self._on_feedback,
            on_state_change=self._on_pipeline_state,
            on_scores=self._on_scores,
        )
        self._engine.set_callbacks(
            on_difficulty_change=self._on_difficulty_change,
            on_mode_change=self._on_mode_change,
        )

    def _on_transcription(self, text: str) -> None:
        self._shared_state["transcript"].append({"role": "user", "content": text})
        if len(self._shared_state["transcript"]) > 100:
            self._shared_state["transcript"] = self._shared_state["transcript"][-50:]

    def _on_ai_chunk(self, chunk: str) -> None:
        pass

    def _on_ai_response(self, text: str) -> None:
        self._shared_state["transcript"].append({"role": "assistant", "content": text})
        if len(self._shared_state["transcript"]) > 100:
            self._shared_state["transcript"] = self._shared_state["transcript"][-50:]

    def _on_feedback(self, items: list) -> None:
        feedback_data = [
            {"category": i.category, "message": i.message, "severity": i.severity}
            for i in items
        ]
        self._shared_state["feedback"].extend(feedback_data)
        if len(self._shared_state["feedback"]) > 100:
            self._shared_state["feedback"] = self._shared_state["feedback"][-50:]

    def _on_pipeline_state(self, state: PipelineState) -> None:
        self._shared_state["status"] = "running" if state.running else "idle"

    def _on_scores(self, scores: Dict) -> None:
        self._shared_state["scores"] = scores

    def _on_difficulty_change(self, old: str, new: str) -> None:
        self._shared_state["difficulty"] = new

    def _on_mode_change(self, mode_id: str) -> None:
        self._shared_state["mode"] = mode_id

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._broadcast_thread = threading.Thread(
            target=self._broadcast_loop, daemon=True, name="broadcast"
        )
        self._broadcast_thread.start()
        logger.info("Server broadcast loop started")

    def stop(self) -> None:
        self._running = False
        self._pipeline.stop()
        if self._broadcast_thread and self._broadcast_thread.is_alive():
            self._broadcast_thread.join(timeout=3.0)
        logger.info("Server stopped")

    def _broadcast_loop(self) -> None:
        while self._running:
            if self._connected_clients:
                data = json.dumps(self._shared_state, default=str)
                for client in list(self._connected_clients):
                    asyncio.run_coroutine_threadsafe(
                        client.send_text(data), self._loop
                    )
            time.sleep(config.dashboard.refresh_interval_ms / 1000.0)

    def create_app(self) -> FastAPI:
        app = FastAPI(title="TalkCraft AI", version="3.0.0")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.on_event("startup")
        async def startup():
            self._loop = asyncio.get_event_loop()
            self.start()
            logger.info("FastAPI server started")

        @app.on_event("shutdown")
        async def shutdown():
            self.stop()

        @app.get("/health")
        async def health():
            llm_ok = self._llm.is_available()
            return {
                "status": "ok",
                "llm_available": llm_ok,
                "mode": self._shared_state["mode"],
                "running": self._running,
            }

        @app.get("/state")
        async def get_state():
            return self._shared_state

        @app.get("/modes")
        async def get_modes():
            return {
                "modes": [
                    {"id": k, "name": v.name, "description": v.description}
                    for k, v in MODES.items()
                ]
            }

        @app.get("/modes/{mode_id}/topics")
        async def get_mode_topics(mode_id: str):
            return {"topics": get_topics_for_mode(mode_id)}

        @app.post("/start")
        async def start_conversation(mode: str = "casual_conversation", topic: str = ""):
            if self._pipeline.state.running:
                return {"status": "already_running"}
            self._engine.set_mode(mode, topic)
            greeting = self._engine.start_conversation()
            self._pipeline.start()
            if greeting:
                self._shared_state["transcript"].append(
                    {"role": "assistant", "content": greeting.content}
                )
            return {"status": "started", "greeting": greeting.content if greeting else ""}

        @app.post("/stop")
        async def stop_conversation():
            summary = self._engine.stop_conversation()
            self._pipeline.stop()
            self._shared_state["session_summary"] = summary
            self._shared_state["status"] = "idle"
            return {"status": "stopped", "summary": summary}

        @app.post("/send")
        async def send_message(text: str):
            if not self._pipeline.state.running:
                return {"status": "not_running"}
            self._pipeline.receive_transcription(text)
            return {"status": "queued"}

        @app.websocket("/ws")
        async def websocket_endpoint(ws: WebSocket):
            await ws.accept()
            self._connected_clients.add(ws)
            logger.debug(f"WebSocket client connected ({len(self._connected_clients)} total)")
            try:
                while True:
                    data = await ws.receive_text()
                    msg = json.loads(data)
                    action = msg.get("action", "")
                    if action == "start":
                        mode = msg.get("mode", "casual_conversation")
                        topic = msg.get("topic", "")
                        await start_conversation(mode=mode, topic=topic)
                    elif action == "stop":
                        await stop_conversation()
                    elif action == "send":
                        text = msg.get("text", "")
                        self._pipeline.receive_transcription(text)
                    elif action == "set_mode":
                        self._engine.set_mode(msg.get("mode", "casual_conversation"), msg.get("topic", ""))
                    elif action == "get_state":
                        await ws.send_text(json.dumps(self._shared_state, default=str))
            except WebSocketDisconnect:
                pass
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                self._connected_clients.discard(ws)
                logger.debug(f"WebSocket client disconnected ({len(self._connected_clients)} total)")

        return app

    def run(self, host: str = None, port: int = None) -> None:
        h = host or config.server.host
        p = port or config.server.port
        app = self.create_app()
        logger.info(f"Starting server on {h}:{p}")
        uvicorn.run(app, host=h, port=p, log_level=config.server.log_level)


def create_server() -> TalkCraftAIServer:
    return TalkCraftAIServer()
