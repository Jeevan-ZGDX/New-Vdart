import datetime
import uuid
from typing import Dict, List, Optional, Set
from talkcraft_enterprise.utils.logger import get_logger

logger = get_logger("room_manager")


class Participant:
    def __init__(self, user_id: int, username: str, role: str = "participant"):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.joined_at = datetime.datetime.utcnow()
        self.score = 0.0
        self.metrics = {
            "speaking_time": 0,
            "utterance_count": 0,
            "word_count": 0,
            "engagement_score": 0.0,
            "clarity_score": 0.0,
            "eye_contact_avg": 0.0,
            "posture_avg": 0.0,
        }
        self.is_speaking = False

    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "joined_at": self.joined_at.isoformat(),
            "score": round(self.score, 2),
            "metrics": self.metrics,
            "is_speaking": self.is_speaking,
        }


class CollaborativeRoom:
    def __init__(self, room_id: str, name: str, room_type: str, host_user_id: int,
                 host_username: str, language: str = "en", max_participants: int = 6,
                 difficulty: str = "intermediate", topic: str = ""):
        self.room_id = room_id
        self.name = name
        self.room_type = room_type
        self.host_user_id = host_user_id
        self.language = language
        self.max_participants = max_participants
        self.difficulty = difficulty
        self.topic = topic
        self.status = "waiting"
        self.participants: Dict[int, Participant] = {}
        self.messages: List[Dict] = []
        self.transcript: List[Dict] = []
        self.created_at = datetime.datetime.utcnow()
        self.started_at: Optional[datetime.datetime] = None
        self.ended_at: Optional[datetime.datetime] = None

        self._add_host(host_user_id, host_username)

    def _add_host(self, user_id: int, username: str):
        host_role = self._get_host_role()
        participant = Participant(user_id, username, host_role)
        self.participants[user_id] = participant

    def _get_host_role(self) -> str:
        role_map = {
            "mock_interview": "interviewer",
            "group_discussion": "moderator",
            "debate": "moderator",
            "presentation": "evaluator",
            "casual": "host",
        }
        return role_map.get(self.room_type, "host")

    def add_participant(self, user_id: int, username: str) -> Dict:
        if len(self.participants) >= self.max_participants:
            return {"error": "Room is full"}
        if user_id in self.participants:
            return {"error": "Already in room"}
        participant = Participant(user_id, username)
        self.participants[user_id] = participant
        self._add_message("system", f"{username} joined the room")
        return participant.to_dict()

    def remove_participant(self, user_id: int) -> bool:
        participant = self.participants.pop(user_id, None)
        if participant:
            self._add_message("system", f"{participant.username} left the room")
            return True
        return False

    def start_session(self) -> Dict:
        if self.status != "waiting":
            return {"error": f"Room is {self.status}"}
        self.status = "active"
        self.started_at = datetime.datetime.utcnow()
        greetings = self._generate_greeting()
        self._add_message("system", greetings)
        return {"status": "started", "greeting": greetings, "started_at": self.started_at.isoformat()}

    def end_session(self) -> Dict:
        if self.status != "active":
            return {"error": f"Room is {self.status}"}
        self.status = "ended"
        self.ended_at = datetime.datetime.utcnow()
        duration = (self.ended_at - self.started_at).seconds if self.started_at else 0
        summary = self._generate_summary()
        self._add_message("system", "Session ended")
        return {"status": "ended", "duration_seconds": duration, "summary": summary}

    def update_participant_metrics(self, user_id: int, metrics: Dict) -> bool:
        participant = self.participants.get(user_id)
        if not participant:
            return False
        for key, value in metrics.items():
            if key in participant.metrics:
                participant.metrics[key] = value
        participant.score = self._calculate_participant_score(participant)
        return True

    def set_participant_speaking(self, user_id: int, is_speaking: bool) -> bool:
        participant = self.participants.get(user_id)
        if not participant:
            return False
        participant.is_speaking = is_speaking
        if is_speaking:
            participant.metrics["utterance_count"] += 1
        return True

    def add_transcription(self, user_id: int, text: str) -> Dict:
        participant = self.participants.get(user_id)
        if not participant:
            return {"error": "Participant not found"}
        entry = {
            "user_id": user_id,
            "username": participant.username,
            "text": text,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "word_count": len(text.split()),
        }
        self.transcript.append(entry)
        participant.metrics["word_count"] += entry["word_count"]
        participant.metrics["speaking_time"] += len(text.split()) * 0.3
        return entry

    def add_message(self, user_id: int, text: str) -> Dict:
        participant = self.participants.get(user_id)
        username = participant.username if participant else "system"
        return self._add_message("user" if participant else "system", text, user_id, username)

    def _add_message(self, msg_type: str, text: str, user_id: int = 0, username: str = "system") -> Dict:
        msg = {
            "type": msg_type,
            "user_id": user_id,
            "username": username,
            "text": text,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
        self.messages.append(msg)
        return msg

    def get_state(self) -> Dict:
        return {
            "room_id": self.room_id,
            "name": self.name,
            "type": self.room_type,
            "status": self.status,
            "language": self.language,
            "difficulty": self.difficulty,
            "topic": self.topic,
            "max_participants": self.max_participants,
            "participant_count": len(self.participants),
            "participants": [p.to_dict() for p in self.participants.values()],
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "duration_seconds": (datetime.datetime.utcnow() - self.started_at).seconds if self.started_at and self.status == "active" else 0,
        }

    def get_participant_rankings(self) -> List[Dict]:
        sorted_parts = sorted(self.participants.values(), key=lambda p: p.score, reverse=True)
        return [p.to_dict() for p in sorted_parts]

    def _generate_greeting(self) -> str:
        templates = {
            "mock_interview": f"Welcome to the mock interview session! Topic: {self.topic or 'General'}. Let's begin.",
            "group_discussion": f"Welcome to the group discussion! Topic: {self.topic or 'General'}. Everyone gets a chance to speak.",
            "debate": f"Welcome to the debate session! Topic: {self.topic or 'General'}. Let's hear both sides.",
            "presentation": f"Welcome to the presentation session! Presenter, you have the floor.",
            "casual": f"Welcome to the conversation session! Let's practice together.",
        }
        return templates.get(self.room_type, f"Welcome to {self.name}!")

    def _generate_summary(self) -> Dict:
        total_words = sum(p.metrics["word_count"] for p in self.participants.values())
        total_utterances = sum(p.metrics["utterance_count"] for p in self.participants.values())
        avg_engagement = sum(p.metrics["engagement_score"] for p in self.participants.values()) / max(1, len(self.participants))
        return {
            "total_participants": len(self.participants),
            "total_words": total_words,
            "total_utterances": total_utterances,
            "avg_engagement": round(avg_engagement, 2),
            "top_participant": self.get_participant_rankings()[0]["username"] if self.participants else "",
            "duration_seconds": (self.ended_at - self.started_at).seconds if self.ended_at and self.started_at else 0,
        }

    def _calculate_participant_score(self, participant: Participant) -> float:
        weights = {"engagement_score": 0.25, "clarity_score": 0.25, "eye_contact_avg": 0.2, "posture_avg": 0.15, "word_count": 0.15}
        score = 0.0
        for metric, weight in weights.items():
            value = participant.metrics.get(metric, 0)
            if metric == "word_count":
                value = min(1.0, value / 500)
            score += value * weight
        return round(min(1.0, score), 2)


class RoomManager:
    def __init__(self):
        self._rooms: Dict[str, CollaborativeRoom] = {}

    def create_room(self, name: str, room_type: str, host_user_id: int, host_username: str,
                    language: str = "en", max_participants: int = 6,
                    difficulty: str = "intermediate", topic: str = "") -> Dict:
        room_id = uuid.uuid4().hex[:12]
        room = CollaborativeRoom(room_id, name, room_type, host_user_id, host_username,
                                 language, max_participants, difficulty, topic)
        self._rooms[room_id] = room
        logger.info(f"Room created: {room_id} ({name}) by user {host_user_id}")
        return room.get_state()

    def get_room(self, room_id: str) -> Optional[CollaborativeRoom]:
        return self._rooms.get(room_id)

    def list_rooms(self, status: Optional[str] = None) -> List[Dict]:
        rooms = self._rooms.values()
        if status:
            rooms = [r for r in rooms if r.status == status]
        return [r.get_state() for r in rooms]

    def join_room(self, room_id: str, user_id: int, username: str) -> Dict:
        room = self.get_room(room_id)
        if not room:
            return {"error": "Room not found"}
        return room.add_participant(user_id, username)

    def leave_room(self, room_id: str, user_id: int) -> Dict:
        room = self.get_room(room_id)
        if not room:
            return {"error": "Room not found"}
        room.remove_participant(user_id)
        if len(room.participants) == 0:
            if room.status == "active":
                room.end_session()
            self._rooms.pop(room_id, None)
            return {"status": "room_closed"}
        return {"status": "left"}

    def start_room(self, room_id: str, user_id: int) -> Dict:
        room = self.get_room(room_id)
        if not room:
            return {"error": "Room not found"}
        if room.host_user_id != user_id:
            return {"error": "Only host can start the room"}
        return room.start_session()

    def end_room(self, room_id: str, user_id: int) -> Dict:
        room = self.get_room(room_id)
        if not room:
            return {"error": "Room not found"}
        if room.host_user_id != user_id:
            return {"error": "Only host can end the room"}
        result = room.end_session()
        return result

    def get_active_room_count(self) -> int:
        return len([r for r in self._rooms.values() if r.status == "active"])


room_manager = RoomManager()
