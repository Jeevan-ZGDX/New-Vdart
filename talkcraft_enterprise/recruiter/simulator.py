from typing import Dict, List, Optional
from talkcraft_enterprise.utils.logger import get_logger

logger = get_logger("recruiter")


INTERVIEW_TYPES = {
    "behavioral": {
        "label": "Behavioral Interview",
        "description": "STAR method questions about past experiences",
        "difficulty": "intermediate",
        "typical_questions": [
            "Tell me about a time you faced a challenging situation at work.",
            "Describe a project where you demonstrated leadership.",
            "Give an example of a goal you achieved and how you accomplished it.",
            "Tell me about a time you had to resolve a conflict.",
            "Describe a situation where you had to adapt to change.",
        ],
    },
    "technical": {
        "label": "Technical Interview",
        "description": "Role-specific technical questions and problem-solving",
        "difficulty": "advanced",
        "typical_questions": [
            "Explain a complex technical concept in simple terms.",
            "How would you architect a solution for...?",
            "Walk me through your approach to debugging a production issue.",
            "Describe a technical project you're proud of.",
            "How do you stay current with industry developments?",
        ],
    },
    "general": {
        "label": "General Interview",
        "description": "Standard interview covering career and fit",
        "difficulty": "beginner",
        "typical_questions": [
            "Tell me about yourself.",
            "Why are you interested in this role?",
            "What are your greatest strengths and weaknesses?",
            "Where do you see yourself in 5 years?",
            "Why should we hire you?",
        ],
    },
    "case_study": {
        "label": "Case Study Interview",
        "description": "Problem-solving and analytical thinking assessment",
        "difficulty": "advanced",
        "typical_questions": [
            "Walk me through your approach to this business problem.",
            "What data would you need to make this decision?",
            "How would you prioritize these competing initiatives?",
            "Estimate the market size for this product.",
            "How would you improve this process?",
        ],
    },
    "panel": {
        "label": "Panel Interview Simulation",
        "description": "Multi-interviewer scenario with diverse questions",
        "difficulty": "advanced",
        "typical_questions": [
            "Multiple interviewers will ask questions from different perspectives.",
            "How do you handle multiple competing priorities?",
            "Describe your experience working cross-functionally.",
            "How do you handle pressure and deadlines?",
            "What makes you unique for this role?",
        ],
    },
}

RECRUITER_PERSONAS = {
    "friendly": {
        "name": "Friendly Recruiter",
        "style": "warm and supportive, puts candidate at ease",
        "prompt_suffix": "Be warm and encouraging. Put the candidate at ease while still evaluating their responses.",
    },
    "professional": {
        "name": "Professional Recruiter",
        "style": "formal and structured, follows standard interview format",
        "prompt_suffix": "Maintain a professional demeanor. Follow standard interview protocols and evaluate responses objectively.",
    },
    "challenging": {
        "name": "Challenging Interviewer",
        "style": "tough questions, stress-test responses, probes deeply",
        "prompt_suffix": "Ask challenging follow-up questions. Don't accept surface-level answers. Probe deeply into responses.",
    },
    "technical": {
        "name": "Technical Interviewer",
        "style": "focused on technical depth and problem-solving",
        "prompt_suffix": "Focus on technical depth. Ask for specifics, examples, and detailed explanations of technical concepts.",
    },
}


class RecruiterSimulator:
    def get_interview_types(self) -> List[Dict]:
        return [
            {"id": k, "label": v["label"], "description": v["description"], "difficulty": v["difficulty"]}
            for k, v in INTERVIEW_TYPES.items()
        ]

    def get_personas(self) -> List[Dict]:
        return [
            {"id": k, "name": v["name"], "style": v["style"]}
            for k, v in RECRUITER_PERSONAS.items()
        ]

    def get_questions(self, interview_type: str, count: int = 3) -> List[str]:
        interview = INTERVIEW_TYPES.get(interview_type, INTERVIEW_TYPES["general"])
        questions = interview["typical_questions"]
        return questions[:min(count, len(questions))]

    def generate_system_prompt(self, interview_type: str, persona: str, role_context: Optional[str] = None) -> str:
        interview = INTERVIEW_TYPES.get(interview_type, INTERVIEW_TYPES["general"])
        persona_info = RECRUITER_PERSONAS.get(persona, RECRUITER_PERSONAS["professional"])
        prompt = f"You are simulating a {interview['label']}. {persona_info['style']}."
        if role_context:
            prompt += f"\n\nRole context: {role_context}"
        prompt += f"\n\n{persona_info['prompt_suffix']}"
        prompt += "\n\nAsk one question at a time. Listen to the candidate's response before asking follow-ups or moving to the next question. Provide brief feedback after each response."
        return prompt

    def evaluate_interview_response(self, response: str, question: str, metrics: Dict) -> Dict:
        word_count = len(response.split())
        clarity = metrics.get("clarity_score", 0) or metrics.get("scores", {}).get("clarity", 0) or 0.5
        confidence = metrics.get("confidence_score", 0) or metrics.get("confidence", 0) or 0.5
        filler = metrics.get("filler_rate", 0)
        pace = metrics.get("average_wpm", 0) or metrics.get("avg_wpm", 0) or 0
        star_structure = self._detect_star_structure(response)
        response_quality = "excellent" if word_count > 50 and star_structure else ("good" if word_count > 30 else "brief")
        return {
            "question": question,
            "response_length": word_count,
            "response_quality": response_quality,
            "star_structure_detected": star_structure,
            "clarity_score": round(clarity, 2),
            "confidence_score": round(confidence, 2),
            "filler_rate": round(filler, 4),
            "wpm": round(pace, 0),
            "composite_score": round((clarity * 0.3 + confidence * 0.3 + (0.2 if star_structure else 0) + min(1.0, word_count / 100) * 0.2), 2),
            "feedback": self._generate_interview_feedback(response_quality, clarity, confidence, star_structure),
        }

    def _detect_star_structure(self, text: str) -> bool:
        text_lower = text.lower()
        star_indicators = ["situation", "task", "action", "result", "for example", "specifically", "i handled", "my role", "the outcome", "as a result"]
        return sum(1 for ind in star_indicators if ind in text_lower) >= 2

    def _generate_interview_feedback(self, quality: str, clarity: float, confidence: float, star: bool) -> List[str]:
        feedback = []
        if quality == "brief":
            feedback.append("Provide more detail in your responses using specific examples.")
        if clarity < 0.6:
            feedback.append("Structure your answers more clearly with a beginning, middle, and end.")
        if confidence < 0.6:
            feedback.append("Work on speaking with more confidence and conviction.")
        if not star:
            feedback.append("Use the STAR method (Situation, Task, Action, Result) for behavioral questions.")
        if not feedback:
            feedback.append("Strong interview response! Keep up the good work.")
        return feedback


recruiter_simulator = RecruiterSimulator()
