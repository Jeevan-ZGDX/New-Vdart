import os

os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["ABSL_MIN_LOG_LEVEL"] = "2"
os.environ["MEDIAPIPE_DISABLE_GPU"] = "1"

import asyncio
import json
import logging
import websockets
from typing import Dict, Set
from main import TalkCraftBackend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONNECTED_CLIENTS: Set[websockets.WebSocketServerProtocol] = set()
backend = None


async def broadcast(data: dict):
    if CONNECTED_CLIENTS:
        message = json.dumps(data)
        websockets.broadcast(CONNECTED_CLIENTS, message)


async def websocket_handler(websocket):
    CONNECTED_CLIENTS.add(websocket)
    logger.info(f"Client connected. Total clients: {len(CONNECTED_CLIENTS)}")

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                command = data.get('command')

                if command == 'update_speech':
                    speech_data = data.get('data', {})
                    backend.update_speech_data(speech_data)
                    await websocket.send(json.dumps({'status': 'ok'}))

                elif command == 'get_status':
                    status = backend.get_status()
                    await websocket.send(json.dumps({'status': 'ok', 'data': status}))

            except json.JSONDecodeError:
                await websocket.send(json.dumps({'status': 'error', 'message': 'Invalid JSON'}))

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CONNECTED_CLIENTS.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(CONNECTED_CLIENTS)}")


async def broadcast_loop():
    while True:
        try:
            output = backend.get_latest_output()
            if output:
                broadcast_data = {
                    'type': 'multimodal_update',
                    'face_detected': output.get('face_detected', False),
                    'eye_contact_score': output.get('eye_contact_score', 0),
                    'gaze_direction': output.get('gaze_direction', 'center'),
                    'posture_stability': output.get('posture_stability', 0),
                    'head_pitch': output.get('head_pitch', 0),
                    'head_yaw': output.get('head_yaw', 0),
                    'head_roll': output.get('head_roll', 0),
                    'hands_detected': output.get('hands_detected', 0),
                    'hand_activity': output.get('hand_activity', 0),
                    'gestures': output.get('gestures', []),
                    'confidence_score': output.get('confidence_score', 0),
                    'confidence_level': output.get('confidence_level', 'moderate'),
                    'feedback': output.get('feedback', []),
                    'session_duration': output.get('session_duration', 0)
                }
                await broadcast(broadcast_data)

            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in broadcast loop: {e}")
            await asyncio.sleep(0.5)


async def main():
    global backend
    backend = TalkCraftBackend(webcam_device=0, target_fps=12)
    backend.start()

    server = await websockets.serve(websocket_handler, '0.0.0.0', 8765)
    logger.info("WebSocket server started on ws://0.0.0.0:8765")

    broadcast_task = asyncio.create_task(broadcast_loop())

    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        broadcast_task.cancel()
        backend.stop()
        server.close()
        await server.wait_closed()


if __name__ == '__main__':
    asyncio.run(main())
