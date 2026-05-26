import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session as DbSession
from talkcraft_coach.database.models import User, ImprovementPlan
from talkcraft_coach.utils.logger import get_logger

logger = get_logger("improvement_planner")


class ImprovementPlanner:
    EXERCISE_LIBRARY = {
        "filler_words": [
            {"name": "Filler Word Awareness", "description": "Record yourself speaking for 2 minutes. Count every filler word. Aim to reduce by 50%.", "duration_minutes": 5, "difficulty": "beginner"},
            {"name": "Pause Practice", "description": "Instead of saying 'um' or 'uh', practice pausing silently for 2 seconds before continuing.", "duration_minutes": 5, "difficulty": "beginner"},
            {"name": "Structured Response Drill", "description": "Answer questions with a structured format: Point-Reason-Example. This reduces filler reliance.", "duration_minutes": 10, "difficulty": "intermediate"},
            {"name": "Filler-Free Monologue", "description": "Speak for 3 minutes on any topic without using any filler words. Restart if you use one.", "duration_minutes": 10, "difficulty": "intermediate"},
            {"name": "Real-time Monitoring", "description": "Have a partner signal every time you use a filler word. Build awareness in natural conversation.", "duration_minutes": 15, "difficulty": "advanced"},
        ],
        "speaking_pace": [
            {"name": "Paced Reading", "description": "Read a passage aloud at 140-160 WPM. Use a metronome or timer.", "duration_minutes": 5, "difficulty": "beginner"},
            {"name": "Slow Down Drill", "description": "Speak at deliberately slow pace (120 WPM) for 3 minutes. Focus on clarity.", "duration_minutes": 5, "difficulty": "beginner"},
            {"name": "Variation Exercise", "description": "Tell a story varying your pace: slow for dramatic parts, normal for narrative, faster for excitement.", "duration_minutes": 10, "difficulty": "intermediate"},
            {"name": "Breath Control", "description": "Practice deep breathing before speaking. Pace your speech with your breath cycle.", "duration_minutes": 10, "difficulty": "intermediate"},
            {"name": "Speed Adjust Challenge", "description": "Record the same 2-minute speech at 3 different paces. Analyze each version.", "duration_minutes": 15, "difficulty": "advanced"},
        ],
        "grammar": [
            {"name": "Common Error Review", "description": "Review your 5 most common grammar errors. Write 10 correct sentences for each.", "duration_minutes": 10, "difficulty": "beginner"},
            {"name": "Sentence Building", "description": "Practice constructing grammatically complete sentences before speaking.", "duration_minutes": 5, "difficulty": "beginner"},
            {"name": "Self-Correction Practice", "description": "When you catch a grammar error, pause and restate correctly. Build the correction habit.", "duration_minutes": 10, "difficulty": "intermediate"},
            {"name": "Structured Response Grammar", "description": "Use past, present, and future tenses deliberately in a 2-minute response.", "duration_minutes": 10, "difficulty": "intermediate"},
            {"name": "Complex Sentence Practice", "description": "Practice using subordinate clauses, conditionals, and complex structures naturally.", "duration_minutes": 15, "difficulty": "advanced"},
        ],
        "eye_contact": [
            {"name": "Mirror Practice", "description": "Practice maintaining eye contact with yourself in a mirror for 2 minutes.", "duration_minutes": 5, "difficulty": "beginner"},
            {"name": "Triangle Technique", "description": "Focus on eye contact triangle: left eye, right eye, mouth. Shift every 5 seconds.", "duration_minutes": 5, "difficulty": "beginner"},
            {"name": "Webcam Recording", "description": "Record yourself speaking. Review and count how often you look at the camera.", "duration_minutes": 10, "difficulty": "intermediate"},
            {"name": "Consecutive Contact Drill", "description": "Maintain eye contact for 30 seconds without breaking. Gradually increase duration.", "duration_minutes": 10, "difficulty": "intermediate"},
            {"name": "Multi-person Engagement", "description": "Practice shifting eye contact naturally between 3 imaginary listeners.", "duration_minutes": 10, "difficulty": "advanced"},
        ],
        "posture": [
            {"name": "Posture Check-in", "description": "Set a timer every 2 minutes. Check your posture: shoulders back, chin level, spine straight.", "duration_minutes": 5, "difficulty": "beginner"},
            {"name": "Wall Alignment", "description": "Stand against a wall for 2 minutes with head, shoulders, and heels touching.", "duration_minutes": 5, "difficulty": "beginner"},
            {"name": "Movement Awareness", "description": "Practice speaking with minimal swaying. Keep your upper body stable.", "duration_minutes": 10, "difficulty": "intermediate"},
            {"name": "Power Stance Practice", "description": "Practice the power stance: feet shoulder-width apart, hands at sides, chin level.", "duration_minutes": 5, "difficulty": "intermediate"},
            {"name": "Dynamic Posture", "description": "Maintain good posture while using gestures and moving naturally.", "duration_minutes": 10, "difficulty": "advanced"},
        ],
        "confidence": [
            {"name": "Power Pose", "description": "Stand in a power pose for 2 minutes before speaking. Boosts confidence naturally.", "duration_minutes": 3, "difficulty": "beginner"},
            {"name": "Positive Affirmation", "description": "Start each session with: 'I am a capable communicator.' Build positive mindset.", "duration_minutes": 2, "difficulty": "beginner"},
            {"name": "Success Visualization", "description": "Visualize a successful conversation or presentation before starting.", "duration_minutes": 5, "difficulty": "intermediate"},
            {"name": "Progressive Exposure", "description": "Practice in increasingly challenging modes: casual -> interview -> presentation.", "duration_minutes": 15, "difficulty": "intermediate"},
            {"name": "High-stakes Simulation", "description": "Simulate a high-pressure scenario (CEO update, media interview) and practice calmly.", "duration_minutes": 15, "difficulty": "advanced"},
        ],
        "engagement": [
            {"name": "Question Practice", "description": "Practice asking 3 relevant questions after every response.", "duration_minutes": 5, "difficulty": "beginner"},
            {"name": "Active Listening", "description": "Listen to a 2-minute audio and summarize key points. Build listening engagement.", "duration_minutes": 10, "difficulty": "beginner"},
            {"name": "Conversation Balance", "description": "Let the other person speak 50% of the time. Practice turn-taking.", "duration_minutes": 10, "difficulty": "intermediate"},
            {"name": "Topic Deep Dive", "description": "Pick one topic and engage deeply for 5 minutes with follow-up exploration.", "duration_minutes": 10, "difficulty": "intermediate"},
            {"name": "Debate Practice", "description": "Argue both sides of a topic. Build engagement through intellectual challenge.", "duration_minutes": 15, "difficulty": "advanced"},
        ],
        "clarity": [
            {"name": "One-minute Summary", "description": "Summarize a complex topic in exactly 60 seconds. Focus on clarity.", "duration_minutes": 5, "difficulty": "beginner"},
            {"name": "Structure Practice", "description": "Use clear structure: Opening, 3 main points, Conclusion in every response.", "duration_minutes": 10, "difficulty": "beginner"},
            {"name": "Simplify Complex Ideas", "description": "Explain a complex concept as if teaching a 10-year-old. No jargon.", "duration_minutes": 10, "difficulty": "intermediate"},
            {"name": "Transitions Drill", "description": "Practice smooth transitions between ideas using phrases like 'furthermore', 'however', 'in addition'.", "duration_minutes": 5, "difficulty": "intermediate"},
            {"name": "Elevator Pitch Mastery", "description": "Create and deliver a 30-second elevator pitch. Refine until perfectly clear.", "duration_minutes": 15, "difficulty": "advanced"},
        ],
    }

    def generate_plan(self, user_id: int, db: DbSession) -> Dict:
        from talkcraft_coach.analytics.weakness_detector import WeaknessDetector
        detector = WeaknessDetector()
        weaknesses = detector.detect_weaknesses(user_id, db)
        user = db.query(User).filter(User.id == user_id).first()

        if not weaknesses.get("available"):
            return self._starter_plan(user, user_id, db)

        focus_areas = weaknesses.get("primary_focus_areas", [])
        if not focus_areas:
            focus_areas = ["filler_words", "confidence"]

        focus_areas = focus_areas[:3]
        difficulty = user.skill_level or "beginner"

        exercises = []
        for area in focus_areas:
            area_exercises = self.EXERCISE_LIBRARY.get(area, [])
            suitable = [e for e in area_exercises if
                        self._difficulty_order(e["difficulty"]) <= self._difficulty_order(difficulty) + 1]
            if not suitable:
                suitable = area_exercises[:2]
            for ex in suitable[:2]:
                exercises.append({
                    "area": area,
                    "name": ex["name"],
                    "description": ex["description"],
                    "duration_minutes": ex["duration_minutes"],
                    "difficulty": ex["difficulty"],
                })

        plan_title = f"{difficulty.capitalize()} Communication Improvement Plan"
        plan_desc = self._generate_description(focus_areas, difficulty)

        plan = ImprovementPlan(
            user_id=user_id,
            title=plan_title,
            description=plan_desc,
            focus_areas=[{"area": a, "label": a.replace("_", " ").title()} for a in focus_areas],
            exercises=exercises,
            recommendations=self._generate_recommendations(focus_areas, difficulty),
            difficulty=difficulty,
            is_active=True,
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        return self._plan_to_dict(plan, weaknesses)

    def get_active_plan(self, user_id: int, db: DbSession) -> Optional[Dict]:
        plan = db.query(ImprovementPlan).filter(
            ImprovementPlan.user_id == user_id,
            ImprovementPlan.is_active == True,
        ).order_by(ImprovementPlan.created_at.desc()).first()
        if plan:
            return self._plan_to_dict(plan)
        return None

    def regenerate_plan(self, user_id: int, db: DbSession) -> Dict:
        old_plans = db.query(ImprovementPlan).filter(
            ImprovementPlan.user_id == user_id,
            ImprovementPlan.is_active == True,
        ).all()
        for p in old_plans:
            p.is_active = False
        db.commit()
        return self.generate_plan(user_id, db)

    def complete_plan(self, plan_id: int, db: DbSession) -> bool:
        plan = db.query(ImprovementPlan).filter(ImprovementPlan.id == plan_id).first()
        if plan:
            plan.is_active = False
            plan.completed_at = datetime.datetime.utcnow()
            plan.progress_pct = 100.0
            db.commit()
            return True
        return False

    def _starter_plan(self, user, user_id: int, db: DbSession) -> Dict:
        difficulty = "beginner"
        exercises = [
            {"area": "filler_words", "name": "Filler Word Awareness", "description": "Record yourself speaking for 2 minutes. Count every filler word.", "duration_minutes": 5, "difficulty": "beginner"},
            {"area": "confidence", "name": "Power Pose", "description": "Stand in a power pose for 2 minutes before speaking.", "duration_minutes": 3, "difficulty": "beginner"},
            {"area": "speaking_pace", "name": "Paced Reading", "description": "Read a passage aloud at 140-160 WPM.", "duration_minutes": 5, "difficulty": "beginner"},
        ]
        plan = ImprovementPlan(
            user_id=user_id,
            title="Getting Started: Communication Basics",
            description="Welcome to TalkCraft! This starter plan helps you build foundational communication skills. Complete these exercises to begin your improvement journey.",
            focus_areas=[{"area": "filler_words", "label": "Filler Words"}, {"area": "confidence", "label": "Confidence"}, {"area": "speaking_pace", "label": "Speaking Pace"}],
            exercises=exercises,
            recommendations="Practice for 10-15 minutes daily. Focus on awareness before trying to change habits. Progress will come with consistent practice!",
            difficulty="beginner",
            is_active=True,
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return self._plan_to_dict(plan)

    def _generate_description(self, focus_areas: List[str], difficulty: str) -> str:
        areas = ", ".join(a.replace("_", " ").title() for a in focus_areas)
        return f"A {difficulty}-level improvement plan focusing on: {areas}. Complete the recommended exercises to strengthen these areas."

    def _generate_recommendations(self, focus_areas: List[str], difficulty: str) -> str:
        recs = [
            f"Practice exercises targeting {', '.join(a.replace('_', ' ').title() for a in focus_areas)}",
            "Use TalkCraft for at least 15 minutes daily for best results",
            "Review your progress analytics weekly to track improvement",
            "Try different conversation modes to challenge different skills",
        ]
        if difficulty == "beginner":
            recs.append("Focus on awareness before performance. Just noticing patterns is the first step.")
        elif difficulty == "advanced":
            recs.append("Push yourself with complex topics and debate mode to refine skills.")
        return " | ".join(recs)

    def _plan_to_dict(self, plan: ImprovementPlan, weaknesses: Dict = None) -> Dict:
        return {
            "id": plan.id,
            "title": plan.title,
            "description": plan.description,
            "focus_areas": plan.focus_areas,
            "exercises": plan.exercises,
            "recommendations": plan.recommendations,
            "difficulty": plan.difficulty,
            "created_at": plan.created_at.isoformat() if plan.created_at else "",
            "is_active": plan.is_active,
            "completed_at": plan.completed_at.isoformat() if plan.completed_at else None,
            "progress_pct": plan.progress_pct or 0,
            "weaknesses": weaknesses.get("weaknesses", []) if weaknesses else [],
            "strengths": weaknesses.get("strengths", []) if weaknesses else [],
        }

    def _difficulty_order(self, d: str) -> int:
        return {"beginner": 0, "intermediate": 1, "advanced": 2}.get(d, 0)
