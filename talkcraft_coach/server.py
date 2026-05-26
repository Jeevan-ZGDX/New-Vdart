import asyncio
import json
import threading
import time
from typing import Dict, Set, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from talkcraft_coach.utils.config import config
from talkcraft_coach.utils.logger import get_logger
from talkcraft_coach.database.database import init_db, get_db_sync
from talkcraft_coach.database.models import User, Session as SessionModel
from talkcraft_coach.api.auth_routes import router as auth_router
from talkcraft_coach.api.analytics_routes import router as analytics_router
from talkcraft_coach.api.coaching_routes import router as coaching_router
from talkcraft_coach.api.achievement_routes import router as achievement_router
from talkcraft_coach.api.dashboard_routes import router as dashboard_router
from talkcraft_coach.api.session_routes import router as session_router

logger = get_logger("server")


class TalkCraftCoachServer:
    def __init__(self):
        init_db()
        self._connected_clients: Set[WebSocket] = set()
        self._running = False
        self._broadcast_thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._shared_state: Dict = {
            "coaching_mode": "active",
            "connected": False,
            "active_sessions": 0,
        }
        logger.info("TalkCraft Coach Server initialized")

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._broadcast_thread = threading.Thread(
            target=self._broadcast_loop, daemon=True, name="coach-broadcast"
        )
        self._broadcast_thread.start()
        logger.info("Coach server broadcast loop started")

    def stop(self) -> None:
        self._running = False
        if self._broadcast_thread and self._broadcast_thread.is_alive():
            self._broadcast_thread.join(timeout=3.0)
        logger.info("Coach server stopped")

    def _broadcast_loop(self) -> None:
        while self._running:
            if self._connected_clients:
                data = json.dumps(self._shared_state, default=str)
                for client in list(self._connected_clients):
                    asyncio.run_coroutine_threadsafe(
                        client.send_text(data), self._loop
                    )
            time.sleep(2.0)

    def create_app(self) -> FastAPI:
        app = FastAPI(title="TalkCraft Coach", version="4.0.0")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.server.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        app.include_router(auth_router)
        app.include_router(analytics_router)
        app.include_router(coaching_router)
        app.include_router(achievement_router)
        app.include_router(dashboard_router)
        app.include_router(session_router)

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
            return {
                "status": "ok",
                "version": "4.0.0",
                "running": self._running,
            }

        @app.get("/")
        async def root():
            return {
                "name": "TalkCraft Coach",
                "version": "4.0.0",
                "endpoints": {
                    "auth": "/api/auth/*",
                    "analytics": "/api/analytics/*",
                    "coaching": "/api/coaching/*",
                    "achievements": "/api/achievements/*",
                    "dashboard": "/api/dashboard/*",
                    "sessions": "/api/sessions/*",
                },
            }

        @app.websocket("/ws/coach")
        async def websocket_endpoint(ws: WebSocket):
            await ws.accept()
            self._connected_clients.add(ws)
            logger.debug(f"Coach WebSocket client connected ({len(self._connected_clients)} total)")
            try:
                while True:
                    data = await ws.receive_text()
                    msg = json.loads(data)
                    action = msg.get("action", "")
                    if action == "ping":
                        await ws.send_text(json.dumps({"type": "pong"}))
                    elif action == "get_state":
                        await ws.send_text(json.dumps(self._shared_state, default=str))
            except WebSocketDisconnect:
                pass
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                self._connected_clients.discard(ws)
                logger.debug(f"Coach WebSocket client disconnected ({len(self._connected_clients)} total)")

        @app.post("/api/sync/session")
        async def sync_session(data: dict):
            try:
                db = get_db_sync()
                user_id = data.get("user_id")
                if not user_id:
                    return {"status": "error", "message": "user_id required"}

                session = SessionModel(
                    user_id=user_id,
                    session_type=data.get("session_type", "mic"),
                    mode=data.get("mode", ""),
                    topic=data.get("topic", ""),
                    difficulty=data.get("difficulty", "intermediate"),
                    duration_seconds=data.get("duration_seconds", 0),
                    overall_score=data.get("overall_score", 0.0),
                    word_count=data.get("word_count", 0),
                    filler_count=data.get("filler_count", 0),
                    filler_rate=data.get("filler_rate", 0.0),
                    grammar_error_count=data.get("grammar_error_count", 0),
                    average_wpm=data.get("average_wpm", 0.0),
                    pace_consistency=data.get("pace_consistency", 0.0),
                    average_eye_contact=data.get("average_eye_contact", 0.0),
                    average_posture=data.get("average_posture", 0.0),
                    average_hand_activity=data.get("average_hand_activity", 0.0),
                    confidence_score=data.get("confidence_score", 0.0),
                    engagement_score=data.get("engagement_score", 0.0),
                    clarity_score=data.get("clarity_score", 0.0),
                    transcript_text=data.get("transcript_text", ""),
                    ai_summary=data.get("ai_summary", ""),
                    weakness_tags=data.get("weakness_tags", []),
                    strength_tags=data.get("strength_tags", []),
                    metadata_json=data.get("metadata_json", {}),
                    ended_at=None,
                )
                db.add(session)
                db.commit()
                db.refresh(session)
                db.close()
                return {"status": "ok", "session_id": session.id}
            except Exception as e:
                logger.error(f"Session sync error: {e}")
                return {"status": "error", "message": str(e)}

        return app

    def run(self, host: str = None, port: int = None) -> None:
        h = host or config.server.host
        p = port or config.server.port
        app = self.create_app()
        logger.info(f"Starting coach server on {h}:{p}")
        uvicorn.run(app, host=h, port=p, log_level=config.server.log_level)


def create_server() -> TalkCraftCoachServer:
    return TalkCraftCoachServer()
