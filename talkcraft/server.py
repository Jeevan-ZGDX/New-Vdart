import sys
import asyncio
import json
import threading
import time
from pathlib import Path
from queue import Queue, Full, Empty

_ex_root = str(Path(__file__).resolve().parent.parent)
if _ex_root not in sys.path:
    sys.path.insert(0, _ex_root)

import uvicorn
from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
_broadcast_queue: Queue = None


def _broadcast_loop():
    while True:
        try:
            engine.poll_updates()
            state = shared_state.get_state()
            try:
                _broadcast_queue.put_nowait(state)
            except Full:
                try:
                    _broadcast_queue.get_nowait()
                    _broadcast_queue.put_nowait(state)
                except Empty:
                    pass
        except Exception:
            pass
        time.sleep(0.25)


@app.on_event("startup")
async def _startup():
    global _broadcast_queue
    _broadcast_queue = Queue(maxsize=50)
    thread = threading.Thread(target=_broadcast_loop, daemon=True)
    thread.start()
    logger.info("Broadcast loop started")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected")
    loop = asyncio.get_event_loop()
    try:
        while True:
            data = await loop.run_in_executor(None, _broadcast_queue.get)
            try:
                await websocket.send_json(data)
            except Exception:
                break
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
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / file.filename
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        success = engine.start_file(str(file_path))
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to process file. Check format compatibility.",
            )
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


@app.get("/health")
async def health():
    return {"status": "ok", "running": engine.is_running}


def main():
    setup_logger("talkcraft.server", level=config.log_level)
    logger.info("=" * 50)
    logger.info("TalkCraft API Server")
    logger.info("=" * 50)
    logger.info(f"API:       http://localhost:8000")
    logger.info(f"WebSocket: ws://localhost:8000/ws")
    logger.info(f"Frontend:  http://localhost:3000")
    logger.info(f"Docs:      http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
