from typing import Dict, List, Optional

AVATAR_DEFINITIONS = {
    "coach": {
        "name": "AI Coach",
        "role": "communication_coach",
        "personality": "supportive",
        "color": "#4CAF50",
        "default_expression": "neutral",
    },
    "interviewer": {
        "name": "Interviewer",
        "role": "interviewer",
        "personality": "professional",
        "color": "#2196F3",
        "default_expression": "attentive",
    },
    "audience": {
        "name": "Audience",
        "role": "audience",
        "personality": "neutral",
        "color": "#FF9800",
        "default_expression": "listening",
    },
    "debater": {
        "name": "Debater",
        "role": "debate_opponent",
        "personality": "challenging",
        "color": "#f44336",
        "default_expression": "thoughtful",
    },
    "presentation_evaluator": {
        "name": "Presentation Evaluator",
        "role": "evaluator",
        "personality": "analytical",
        "color": "#9C27B0",
        "default_expression": "observing",
    },
    "conversation_partner": {
        "name": "Conversation Partner",
        "role": "partner",
        "personality": "friendly",
        "color": "#00BCD4",
        "default_expression": "smiling",
    },
}

EXPRESSION_MAP = {
    "neutral": {"eyes": "open", "eyebrows": "relaxed", "mouth": "closed"},
    "smiling": {"eyes": "squint", "eyebrows": "raised", "mouth": "smile"},
    "attentive": {"eyes": "wide", "eyebrows": "raised", "mouth": "slight_open"},
    "thoughtful": {"eyes": "squint", "eyebrows": "furrowed", "mouth": "pursed"},
    "surprised": {"eyes": "wide", "eyebrows": "raised", "mouth": "open"},
    "nodding": {"eyes": "open", "eyebrows": "relaxed", "mouth": "closed", "action": "nod"},
    "listening": {"eyes": "open", "eyebrows": "slightly_raised", "mouth": "closed", "action": "slight_nod"},
    "observing": {"eyes": "narrowed", "eyebrows": "relaxed", "mouth": "closed"},
    "speaking": {"eyes": "open", "eyebrows": "animated", "mouth": "talking"},
}

LIP_SYNC_VISEMES = {
    "A": {"mouth": "wide_open"},
    "E": {"mouth": "slight_open"},
    "I": {"mouth": "wide_smile"},
    "O": {"mouth": "rounded_open"},
    "U": {"mouth": "pursed"},
    "M": {"mouth": "closed"},
    "F": {"mouth": "lip_bite"},
    "default": {"mouth": "slight_open"},
}


class AvatarManager:
    def __init__(self):
        self._active_avatars: Dict[str, Dict] = {}

    def get_avatar(self, avatar_id: str) -> Optional[Dict]:
        return AVATAR_DEFINITIONS.get(avatar_id)

    def create_avatar(self, avatar_id: str, custom_name: Optional[str] = None) -> Dict:
        definition = self.get_avatar(avatar_id)
        if not definition:
            definition = AVATAR_DEFINITIONS["coach"]

        avatar = {
            "id": avatar_id,
            "name": custom_name or definition["name"],
            "role": definition["role"],
            "personality": definition["personality"],
            "color": definition["color"],
            "expression": definition["default_expression"],
            "emotion": "neutral",
            "listening": False,
            "speaking": False,
            "animation_queue": [],
        }
        self._active_avatars[avatar_id] = avatar
        return avatar

    def get_all_avatars(self) -> List[Dict]:
        return [
            {"id": k, "name": v["name"], "role": v["role"], "personality": v["personality"], "color": v["color"]}
            for k, v in AVATAR_DEFINITIONS.items()
        ]

    def set_expression(self, avatar_id: str, expression: str) -> Optional[Dict]:
        avatar = self._active_avatars.get(avatar_id)
        if not avatar:
            return None
        if expression in EXPRESSION_MAP:
            avatar["expression"] = expression
        return avatar

    def set_speaking(self, avatar_id: str, is_speaking: bool, phoneme: Optional[str] = None) -> Optional[Dict]:
        avatar = self._active_avatars.get(avatar_id)
        if not avatar:
            return None
        avatar["speaking"] = is_speaking
        if is_speaking and phoneme:
            viseme = LIP_SYNC_VISEMES.get(phoneme, LIP_SYNC_VISEMES["default"])
            avatar["viseme"] = viseme
        return avatar

    def set_listening(self, avatar_id: str, is_listening: bool) -> Optional[Dict]:
        avatar = self._active_avatars.get(avatar_id)
        if not avatar:
            return None
        avatar["listening"] = is_listening
        if is_listening:
            return self.set_expression(avatar_id, "listening")
        return avatar

    def get_avatar_state(self, avatar_id: str) -> Optional[Dict]:
        return self._active_avatars.get(avatar_id)

    def remove_avatar(self, avatar_id: str) -> bool:
        return self._active_avatars.pop(avatar_id, None) is not None

    def calculate_animation_frame(self, avatar_id: str) -> Dict:
        avatar = self._active_avatars.get(avatar_id)
        if not avatar:
            return {}
        expression = EXPRESSION_MAP.get(avatar["expression"], EXPRESSION_MAP["neutral"])
        frame = {
            "id": avatar_id,
            "expression": avatar["expression"],
            "viseme": avatar.get("viseme", {}),
            "features": expression,
            "speaking": avatar["speaking"],
            "listening": avatar["listening"],
            "action": expression.get("action", "idle"),
        }
        return frame


avatar_manager = AvatarManager()
