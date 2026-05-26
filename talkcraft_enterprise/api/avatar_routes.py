from fastapi import APIRouter
from talkcraft_enterprise.avatar.avatar_manager import avatar_manager
from talkcraft_enterprise.avatar.expressions import expression_mapper

router = APIRouter(prefix="/api/avatars", tags=["avatars"])


@router.get("")
async def get_avatars():
    return {"avatars": avatar_manager.get_all_avatars()}


@router.post("/create")
async def create_avatar(avatar_id: str, custom_name: str = None):
    return avatar_manager.create_avatar(avatar_id, custom_name)


@router.get("/{avatar_id}")
async def get_avatar(avatar_id: str):
    avatar = avatar_manager.get_avatar(avatar_id)
    if not avatar:
        return {"error": "Avatar not found"}
    return avatar


@router.post("/{avatar_id}/expression")
async def set_expression(avatar_id: str, expression: str):
    result = avatar_manager.set_expression(avatar_id, expression)
    if not result:
        return {"error": "Avatar not found"}
    return result


@router.post("/{avatar_id}/speaking")
async def set_speaking(avatar_id: str, is_speaking: bool, phoneme: str = None):
    result = avatar_manager.set_speaking(avatar_id, is_speaking, phoneme)
    if not result:
        return {"error": "Avatar not found"}
    return result


@router.post("/{avatar_id}/listening")
async def set_listening(avatar_id: str, is_listening: bool):
    result = avatar_manager.set_listening(avatar_id, is_listening)
    if not result:
        return {"error": "Avatar not found"}
    return result


@router.get("/{avatar_id}/frame")
async def get_animation_frame(avatar_id: str):
    frame = avatar_manager.calculate_animation_frame(avatar_id)
    if not frame:
        return {"error": "Avatar not found"}
    return frame


@router.get("/expressions/map")
async def map_expression(score: float = 0.5):
    return {"expression": expression_mapper.map_score_to_expression(score)}


@router.post("/expressions/phonemes")
async def text_to_phonemes(text: str):
    return {"phonemes": expression_mapper.text_to_phoneme_sequence(text)}
