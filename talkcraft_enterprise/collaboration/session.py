from typing import Dict, List, Optional
from talkcraft_enterprise.collaboration.room_manager import room_manager
from talkcraft_enterprise.utils.logger import get_logger

logger = get_logger("session")


class CollaborationSession:
    def handle_speech_data(self, room_id: str, user_id: int, text: str, metrics: Optional[Dict] = None) -> Dict:
        room = room_manager.get_room(room_id)
        if not room:
            return {"error": "Room not found"}
        entry = room.add_transcription(user_id, text)
        if metrics:
            room.update_participant_metrics(user_id, metrics)
        return {
            "entry": entry,
            "participant_count": len(room.participants),
            "total_words": sum(p.metrics["word_count"] for p in room.participants.values()),
        }

    def get_room_analytics(self, room_id: str) -> Dict:
        room = room_manager.get_room(room_id)
        if not room:
            return {"error": "Room not found"}
        participants = room.participants.values()
        total_words = sum(p.metrics["word_count"] for p in participants)
        total_speaking_time = sum(p.metrics["speaking_time"] for p in participants)
        avg_engagement = sum(p.metrics["engagement_score"] for p in participants) / max(1, len(participants))
        avg_clarity = sum(p.metrics["clarity_score"] for p in participants) / max(1, len(participants))
        return {
            "room_id": room_id,
            "room_name": room.name,
            "room_type": room.room_type,
            "status": room.status,
            "duration_seconds": room.get_state().get("duration_seconds", 0),
            "participant_count": len(participants),
            "total_words": total_words,
            "total_speaking_time_seconds": total_speaking_time,
            "avg_engagement": round(avg_engagement, 2),
            "avg_clarity": round(avg_clarity, 2),
            "speaking_distribution": self._calculate_speaking_distribution(room),
            "rankings": room.get_participant_rankings(),
        }

    def _calculate_speaking_distribution(self, room) -> Dict:
        participants = room.participants.values()
        total_words = sum(p.metrics["word_count"] for p in participants) or 1
        distribution = {}
        for p in participants:
            distribution[p.username] = round(p.metrics["word_count"] / total_words * 100, 1)
        return distribution

    def compare_participants(self, room_id: str) -> Dict:
        room = room_manager.get_room(room_id)
        if not room:
            return {"error": "Room not found"}
        participants = room.participants.values()
        if len(participants) < 2:
            return {"error": "Need at least 2 participants for comparison"}
        metrics_keys = ["speaking_time", "utterance_count", "word_count", "engagement_score", "clarity_score"]
        comparison = {}
        for key in metrics_keys:
            values = [(p.username, p.metrics.get(key, 0)) for p in participants]
            values.sort(key=lambda x: x[1], reverse=True)
            comparison[key] = [{"username": v[0], "value": round(v[1], 2)} for v in values]
        return {"room_id": room_id, "comparison": comparison, "rankings": room.get_participant_rankings()}


collaboration_session = CollaborationSession()
