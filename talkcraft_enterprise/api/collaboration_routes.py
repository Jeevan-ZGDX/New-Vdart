from fastapi import APIRouter, Query
from talkcraft_enterprise.collaboration.room_manager import room_manager
from talkcraft_enterprise.collaboration.session import collaboration_session

router = APIRouter(prefix="/api/collaboration", tags=["collaboration"])


@router.post("/rooms/create")
async def create_room(name: str, room_type: str = "mock_interview", host_user_id: int = 0,
                      host_username: str = "host", language: str = "en",
                      max_participants: int = 6, difficulty: str = "intermediate", topic: str = ""):
    return room_manager.create_room(name, room_type, host_user_id, host_username,
                                    language, max_participants, difficulty, topic)


@router.get("/rooms")
async def list_rooms(status: str = None):
    return {"rooms": room_manager.list_rooms(status)}


@router.get("/rooms/{room_id}")
async def get_room(room_id: str):
    room = room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}
    return room.get_state()


@router.post("/rooms/{room_id}/join")
async def join_room(room_id: str, user_id: int, username: str):
    return room_manager.join_room(room_id, user_id, username)


@router.post("/rooms/{room_id}/leave")
async def leave_room(room_id: str, user_id: int):
    return room_manager.leave_room(room_id, user_id)


@router.post("/rooms/{room_id}/start")
async def start_room(room_id: str, user_id: int):
    return room_manager.start_room(room_id, user_id)


@router.post("/rooms/{room_id}/end")
async def end_room(room_id: str, user_id: int):
    return room_manager.end_room(room_id, user_id)


@router.post("/rooms/{room_id}/transcription")
async def add_transcription(room_id: str, user_id: int, text: str):
    return collaboration_session.handle_speech_data(room_id, user_id, text)


@router.get("/rooms/{room_id}/analytics")
async def get_room_analytics(room_id: str):
    return collaboration_session.get_room_analytics(room_id)


@router.get("/rooms/{room_id}/rankings")
async def get_rankings(room_id: str):
    room = room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}
    return {"rankings": room.get_participant_rankings()}


@router.get("/stats")
async def get_stats():
    return {"active_rooms": room_manager.get_active_room_count(), "total_rooms": len(room_manager.list_rooms())}
