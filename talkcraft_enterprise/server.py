import asyncio
import json
import threading
import time
from typing import Dict, Set, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from talkcraft_enterprise.utils.config import config
from talkcraft_enterprise.utils.logger import get_logger
from talkcraft_enterprise.database.database import init_db
from talkcraft_enterprise.api.multilingual_routes import router as multilingual_router
from talkcraft_enterprise.api.avatar_routes import router as avatar_router
from talkcraft_enterprise.api.collaboration_routes import router as collaboration_router
from talkcraft_enterprise.api.enterprise_routes import router as enterprise_router
from talkcraft_enterprise.api.behavioral_routes import router as behavioral_router
from talkcraft_enterprise.api.certification_routes import router as certification_router
from talkcraft_enterprise.api.benchmarking_routes import router as benchmarking_router
from talkcraft_enterprise.api.role_routes import router as role_router
from talkcraft_enterprise.api.recruiter_routes import router as recruiter_router
from talkcraft_enterprise.api.dashboard_routes import router as dashboard_router
from talkcraft_enterprise.api.recording_routes import router as recording_router

logger = get_logger("server")


class TalkCraftEnterpriseServer:
    def __init__(self):
        init_db()
        self._connected_clients: Dict[str, Set[WebSocket]] = {}
        self._running = False
        self._broadcast_thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._room_subscriptions: Dict[str, Set[WebSocket]] = {}
        self._shared_state: Dict = {
            "active_rooms": 0,
            "active_users": 0,
            "services": {
                "multilingual": True,
                "avatar": True,
                "collaboration": True,
                "enterprise": True,
                "certification": True,
                "recruiter": True,
            },
        }
        logger.info("TalkCraft Enterprise Server initialized")

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._broadcast_thread = threading.Thread(
            target=self._broadcast_loop, daemon=True, name="enterprise-broadcast"
        )
        self._broadcast_thread.start()
        logger.info("Enterprise server broadcast loop started")

    def stop(self) -> None:
        self._running = False
        if self._broadcast_thread and self._broadcast_thread.is_alive():
            self._broadcast_thread.join(timeout=3.0)
        logger.info("Enterprise server stopped")

    def _broadcast_loop(self) -> None:
        while self._running:
            for room_id, clients in self._room_subscriptions.items():
                if clients:
                    data = json.dumps({"type": "room_update", "room_id": room_id}, default=str)
                    for client in list(clients):
                        asyncio.run_coroutine_threadsafe(client.send_text(data), self._loop)
            if self._connected_clients.get("global"):
                data = json.dumps(self._shared_state, default=str)
                for client in list(self._connected_clients["global"]):
                    asyncio.run_coroutine_threadsafe(client.send_text(data), self._loop)
            time.sleep(1.0)

    def create_app(self) -> FastAPI:
        app = FastAPI(title="TalkCraft Enterprise", version="5.0.0")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.server.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        app.include_router(multilingual_router)
        app.include_router(avatar_router)
        app.include_router(collaboration_router)
        app.include_router(enterprise_router)
        app.include_router(behavioral_router)
        app.include_router(certification_router)
        app.include_router(benchmarking_router)
        app.include_router(role_router)
        app.include_router(recruiter_router)
        app.include_router(dashboard_router)
        app.include_router(recording_router)

        @app.on_event("startup")
        async def startup():
            self._loop = asyncio.get_event_loop()
            self.start()
            logger.info("FastAPI enterprise server started")

        @app.on_event("shutdown")
        async def shutdown():
            self.stop()

        @app.get("/health")
        async def health():
            return {"status": "ok", "version": "5.0.0", "running": self._running}

        @app.get("/")
        async def root():
            return {
                "name": "TalkCraft Enterprise",
                "version": "5.0.0",
                "endpoints": {
                    "multilingual": "/api/multilingual/*",
                    "avatars": "/api/avatars/*",
                    "collaboration": "/api/collaboration/*",
                    "enterprise": "/api/enterprise/*",
                    "behavioral": "/api/behavioral/*",
                    "certification": "/api/certification/*",
                    "benchmarks": "/api/benchmarks/*",
                    "role_training": "/api/roles/*",
                    "recruiter": "/api/recruiter/*",
                    "dashboard": "/api/dashboard/*",
                    "recordings": "/api/recordings/*",
                },
            }

        @app.websocket("/ws/enterprise")
        async def websocket_endpoint(ws: WebSocket):
            await ws.accept()
            if "global" not in self._connected_clients:
                self._connected_clients["global"] = set()
            self._connected_clients["global"].add(ws)
            logger.debug(f"Enterprise WebSocket client connected")
            try:
                while True:
                    data = await ws.receive_text()
                    msg = json.loads(data)
                    action = msg.get("action", "")
                    if action == "ping":
                        await ws.send_text(json.dumps({"type": "pong"}))
                    elif action == "subscribe_room":
                        room_id = msg.get("room_id")
                        if room_id:
                            if room_id not in self._room_subscriptions:
                                self._room_subscriptions[room_id] = set()
                            self._room_subscriptions[room_id].add(ws)
                            await ws.send_text(json.dumps({"type": "subscribed", "room_id": room_id}))
                    elif action == "unsubscribe_room":
                        room_id = msg.get("room_id")
                        if room_id and room_id in self._room_subscriptions:
                            self._room_subscriptions[room_id].discard(ws)
            except WebSocketDisconnect:
                pass
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                self._connected_clients.get("global", set()).discard(ws)
                for room_clients in self._room_subscriptions.values():
                    room_clients.discard(ws)

        return app

    def run(self, host: str = None, port: int = None) -> None:
        h = host or config.server.host
        p = port or config.server.port
        app = self.create_app()
        logger.info(f"Starting enterprise server on {h}:{p}")
        uvicorn.run(app, host=h, port=p, log_level=config.server.log_level)


def create_server() -> TalkCraftEnterpriseServer:
    return TalkCraftEnterpriseServer()
