from typing import Dict, List, Optional
from talkcraft_coach.utils.logger import get_logger

logger = get_logger("topic_paths")


class TopicPaths:
    PATHS = {
        "interview_mastery": {
            "title": "Interview Mastery",
            "description": "Master the art of job interviews, from behavioral questions to technical discussions.",
            "topics": {
                "beginner": [
                    {"name": "Self Introduction", "duration_minutes": 5, "focus": "clarity"},
                    {"name": "Strengths & Weaknesses", "duration_minutes": 8, "focus": "confidence"},
                    {"name": "Career Goals", "duration_minutes": 8, "focus": "clarity"},
                    {"name": "Why This Role", "duration_minutes": 8, "focus": "engagement"},
                    {"name": "Teamwork Experience", "duration_minutes": 10, "focus": "filler_words"},
                ],
                "intermediate": [
                    {"name": "Behavioral Questions (STAR)", "duration_minutes": 15, "focus": "structure"},
                    {"name": "Leadership Scenarios", "duration_minutes": 12, "focus": "confidence"},
                    {"name": "Conflict Resolution", "duration_minutes": 12, "focus": "clarity"},
                    {"name": "Technical Explanations", "duration_minutes": 15, "focus": "speaking_pace"},
                    {"name": "Salary Negotiation", "duration_minutes": 10, "focus": "confidence"},
                ],
                "advanced": [
                    {"name": "Case Interviews", "duration_minutes": 20, "focus": "clarity"},
                    {"name": "Panel Interview Simulation", "duration_minutes": 25, "focus": "engagement"},
                    {"name": "Stress Interview Practice", "duration_minutes": 20, "focus": "confidence"},
                    {"name": "Executive Presence", "duration_minutes": 20, "focus": "posture"},
                    {"name": "Cross-functional Leadership", "duration_minutes": 25, "focus": "clarity"},
                ],
            },
        },
        "public_speaking": {
            "title": "Public Speaking",
            "description": "Develop confident, engaging public speaking skills for any audience.",
            "topics": {
                "beginner": [
                    {"name": "Overcoming Stage Fear", "duration_minutes": 5, "focus": "confidence"},
                    {"name": "Voice Projection", "duration_minutes": 8, "focus": "speaking_pace"},
                    {"name": "Basic Speech Structure", "duration_minutes": 10, "focus": "clarity"},
                    {"name": "Using Pauses Effectively", "duration_minutes": 8, "focus": "filler_words"},
                    {"name": "Audience Awareness", "duration_minutes": 10, "focus": "eye_contact"},
                ],
                "intermediate": [
                    {"name": "Storytelling Techniques", "duration_minutes": 15, "focus": "engagement"},
                    {"name": "Handling Q&A Sessions", "duration_minutes": 12, "focus": "confidence"},
                    {"name": "Persuasive Speaking", "duration_minutes": 15, "focus": "clarity"},
                    {"name": "Visual Aid Integration", "duration_minutes": 12, "focus": "posture"},
                    {"name": "Impromptu Speaking", "duration_minutes": 15, "focus": "filler_words"},
                ],
                "advanced": [
                    {"name": "Keynote Delivery", "duration_minutes": 25, "focus": "engagement"},
                    {"name": "Crisis Communication", "duration_minutes": 20, "focus": "confidence"},
                    {"name": "Inspirational Speaking", "duration_minutes": 20, "focus": "clarity"},
                    {"name": "Technical Presentation", "duration_minutes": 25, "focus": "speaking_pace"},
                    {"name": "TED-style Talk", "duration_minutes": 30, "focus": "engagement"},
                ],
            },
        },
        "professional_communication": {
            "title": "Professional Communication",
            "description": "Excel in workplace communication: meetings, presentations, and daily interactions.",
            "topics": {
                "beginner": [
                    {"name": "Meeting Etiquette", "duration_minutes": 5, "focus": "engagement"},
                    {"name": "Professional Greetings", "duration_minutes": 5, "focus": "confidence"},
                    {"name": "Clear Requests", "duration_minutes": 8, "focus": "clarity"},
                    {"name": "Active Listening", "duration_minutes": 8, "focus": "engagement"},
                    {"name": "Status Updates", "duration_minutes": 8, "focus": "filler_words"},
                ],
                "intermediate": [
                    {"name": "Leading Meetings", "duration_minutes": 15, "focus": "confidence"},
                    {"name": "Difficult Conversations", "duration_minutes": 15, "focus": "clarity"},
                    {"name": "Presentation Skills", "duration_minutes": 15, "focus": "posture"},
                    {"name": "Client Communication", "duration_minutes": 12, "focus": "eye_contact"},
                    {"name": "Feedback Delivery", "duration_minutes": 12, "focus": "clarity"},
                ],
                "advanced": [
                    {"name": "Executive Communication", "duration_minutes": 20, "focus": "confidence"},
                    {"name": "Negotiation Skills", "duration_minutes": 25, "focus": "engagement"},
                    {"name": "Strategic Storytelling", "duration_minutes": 20, "focus": "clarity"},
                    {"name": "Board Room Presence", "duration_minutes": 20, "focus": "posture"},
                    {"name": "Thought Leadership", "duration_minutes": 25, "focus": "engagement"},
                ],
            },
        },
        "confidence_building": {
            "title": "Confidence Building",
            "description": "Build unshakeable communication confidence from the ground up.",
            "topics": {
                "beginner": [
                    {"name": "Power Pose Practice", "duration_minutes": 3, "focus": "confidence"},
                    {"name": "Positive Self-talk", "duration_minutes": 5, "focus": "confidence"},
                    {"name": "Small Talk Mastery", "duration_minutes": 8, "focus": "filler_words"},
                    {"name": "Asking Questions", "duration_minutes": 5, "focus": "engagement"},
                    {"name": "Voice Warm-up", "duration_minutes": 5, "focus": "speaking_pace"},
                ],
                "intermediate": [
                    {"name": "Assertive Communication", "duration_minutes": 12, "focus": "confidence"},
                    {"name": "Handling Interruptions", "duration_minutes": 10, "focus": "posture"},
                    {"name": "Speaking Under Pressure", "duration_minutes": 15, "focus": "speaking_pace"},
                    {"name": "Expressing Opinions", "duration_minutes": 10, "focus": "clarity"},
                    {"name": "Managing Nerves", "duration_minutes": 12, "focus": "confidence"},
                ],
                "advanced": [
                    {"name": "High-stakes Simulation", "duration_minutes": 20, "focus": "confidence"},
                    {"name": "Media Interview Prep", "duration_minutes": 20, "focus": "eye_contact"},
                    {"name": "Crisis Composure", "duration_minutes": 20, "focus": "posture"},
                    {"name": "Charismatic Speaking", "duration_minutes": 25, "focus": "engagement"},
                    {"name": "Leadership Presence", "duration_minutes": 25, "focus": "confidence"},
                ],
            },
        },
        "debate_argumentation": {
            "title": "Debate & Argumentation",
            "description": "Develop structured argumentation, critical thinking, and debate skills.",
            "topics": {
                "beginner": [
                    {"name": "Structuring an Argument", "duration_minutes": 8, "focus": "clarity"},
                    {"name": "Fact vs Opinion", "duration_minutes": 5, "focus": "clarity"},
                    {"name": "Respectful Disagreement", "duration_minutes": 8, "focus": "engagement"},
                    {"name": "Building a Thesis", "duration_minutes": 8, "focus": "clarity"},
                    {"name": "Supporting Evidence", "duration_minutes": 10, "focus": "filler_words"},
                ],
                "intermediate": [
                    {"name": "Rebuttal Techniques", "duration_minutes": 12, "focus": "engagement"},
                    {"name": "Logical Fallacies", "duration_minutes": 12, "focus": "clarity"},
                    {"name": "Cross-examination", "duration_minutes": 15, "focus": "confidence"},
                    {"name": "Persuasion Strategies", "duration_minutes": 15, "focus": "speaking_pace"},
                    {"name": "Audience Analysis", "duration_minutes": 10, "focus": "eye_contact"},
                ],
                "advanced": [
                    {"name": "Oxford-style Debate", "duration_minutes": 25, "focus": "engagement"},
                    {"name": "Policy Debate", "duration_minutes": 25, "focus": "clarity"},
                    {"name": "Ethical Argumentation", "duration_minutes": 20, "focus": "confidence"},
                    {"name": "Impromptu Debate", "duration_minutes": 20, "focus": "filler_words"},
                    {"name": "Multi-round Debate", "duration_minutes": 30, "focus": "engagement"},
                ],
            },
        },
    }

    def get_all_paths(self) -> List[Dict]:
        return [
            {
                "id": k,
                "title": v["title"],
                "description": v["description"],
                "levels": list(v["topics"].keys()),
                "topic_count": sum(len(topics) for topics in v["topics"].values()),
            }
            for k, v in self.PATHS.items()
        ]

    def get_path(self, path_id: str) -> Optional[Dict]:
        path = self.PATHS.get(path_id)
        if not path:
            return None
        return {"id": path_id, "title": path["title"], "description": path["description"], "topics": path["topics"]}

    def get_topics_for_level(self, path_id: str, level: str) -> List[Dict]:
        path = self.PATHS.get(path_id)
        if not path:
            return []
        return path["topics"].get(level, [])

    def recommend_path(self, weaknesses: List[str], level: str) -> Dict:
        path_scores = {}
        for path_id, path in self.PATHS.items():
            score = 0
            for weakness in weaknesses:
                for lvl, topics in path["topics"].items():
                    for topic in topics:
                        if topic["focus"] == weakness:
                            score += 1
            path_scores[path_id] = score

        if not path_scores:
            return {"path_id": "confidence_building", "title": "Confidence Building"}

        best = max(path_scores, key=path_scores.get)
        return {"path_id": best, "title": self.PATHS[best]["title"], "score": path_scores[best]}

    def get_progress_estimate(self, path_id: str, completed_topics: List[str]) -> Dict:
        path = self.PATHS.get(path_id)
        if not path:
            return {"pct": 0, "completed": 0, "total": 0}
        total = sum(len(topics) for topics in path["topics"].values())
        completed = len([t for t_list in path["topics"].values() for t in t_list if t["name"] in completed_topics])
        return {"pct": round((completed / max(1, total)) * 100, 1), "completed": completed, "total": total}
