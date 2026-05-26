from typing import Dict, List, Optional
from talkcraft_enterprise.utils.logger import get_logger

logger = get_logger("roles")


ROLE_DEFINITIONS = {
    "software_engineer": {
        "label": "Software Engineer",
        "description": "Technical communication for engineering roles",
        "focus_areas": ["clarity", "structure", "technical_accuracy"],
        "scenario_themes": ["code_review", "system_design", "technical_explanation", "sprint_planning", "bug_discussion"],
        "system_prompt": "You are a senior software engineer interviewer. Ask technical questions about algorithms, system design, and coding practices. Evaluate clarity of technical explanations.",
    },
    "product_manager": {
        "label": "Product Manager",
        "description": "Strategic communication for product leadership",
        "focus_areas": ["engagement", "vision", "stakeholder_management"],
        "scenario_themes": ["product_strategy", "stakeholder_update", "feature_prioritization", "roadmap_presentation", "user_research"],
        "system_prompt": "You are a product management coach. Present product scenarios and evaluate strategic thinking, stakeholder communication, and vision articulation.",
    },
    "sales_executive": {
        "label": "Sales Executive",
        "description": "Persuasive communication for sales roles",
        "focus_areas": ["confidence", "persuasion", "objection_handling"],
        "scenario_themes": ["pitch_presentation", "objection_handling", "negotiation", "client_meeting", "closing_techniques"],
        "system_prompt": "You are a sales coach. Simulate client interactions and evaluate persuasion skills, confidence, objection handling, and closing techniques.",
    },
    "team_lead": {
        "label": "Team Lead / Manager",
        "description": "Leadership communication for management roles",
        "focus_areas": ["clarity", "motivation", "feedback_delivery"],
        "scenario_themes": ["team_meeting", "feedback_session", "conflict_resolution", "project_update", "one_on_one"],
        "system_prompt": "You are a leadership coach. Simulate management scenarios and evaluate team communication, feedback delivery, motivation, and conflict resolution.",
    },
    "executive": {
        "label": "Executive / Director",
        "description": "Executive-level communication and presence",
        "focus_areas": ["confidence", "strategic_thinking", "presence"],
        "scenario_themes": ["board_presentation", "all_hands_meeting", "strategic_decision", "crisis_communication", "vision_talk"],
        "system_prompt": "You are an executive coach. Simulate high-stakes leadership scenarios and evaluate executive presence, strategic communication, and decision-making clarity.",
    },
    "teacher_trainer": {
        "label": "Teacher / Trainer",
        "description": "Educational communication for teaching roles",
        "focus_areas": ["engagement", "clarity", "adaptability"],
        "scenario_themes": ["lesson_delivery", "student_questions", "curriculum_explanation", "classroom_management", "parent_meeting"],
        "system_prompt": "You are a teaching coach. Simulate classroom and training scenarios. Evaluate engagement, clarity of explanation, and adaptability to different learner levels.",
    },
}


SCENARIO_TEMPLATES = {
    "code_review": {
        "title": "Code Review Discussion",
        "description": "Explain your code changes and respond to reviewer feedback",
        "difficulty": "intermediate",
        "duration_minutes": 10,
    },
    "system_design": {
        "title": "System Design Explanation",
        "description": "Present a system architecture and justify design decisions",
        "difficulty": "advanced",
        "duration_minutes": 15,
    },
    "pitch_presentation": {
        "title": "Product Pitch",
        "description": "Present a product idea to potential investors",
        "difficulty": "intermediate",
        "duration_minutes": 10,
    },
    "board_presentation": {
        "title": "Board Meeting Presentation",
        "description": "Present quarterly results and strategy to the board",
        "difficulty": "advanced",
        "duration_minutes": 15,
    },
    "team_meeting": {
        "title": "Team Stand-up",
        "description": "Lead a team stand-up meeting with updates and blockers",
        "difficulty": "beginner",
        "duration_minutes": 5,
    },
    "feedback_session": {
        "title": "Performance Feedback",
        "description": "Deliver constructive feedback to a team member",
        "difficulty": "intermediate",
        "duration_minutes": 10,
    },
    "stakeholder_update": {
        "title": "Stakeholder Status Update",
        "description": "Update stakeholders on project progress and risks",
        "difficulty": "intermediate",
        "duration_minutes": 10,
    },
    "negotiation": {
        "title": "Client Negotiation",
        "description": "Negotiate terms with a client while maintaining relationship",
        "difficulty": "advanced",
        "duration_minutes": 15,
    },
    "lesson_delivery": {
        "title": "Lesson Delivery",
        "description": "Teach a concept to students with clear explanations",
        "difficulty": "intermediate",
        "duration_minutes": 10,
    },
    "crisis_communication": {
        "title": "Crisis Communication",
        "description": "Address a crisis situation with stakeholders",
        "difficulty": "advanced",
        "duration_minutes": 15,
    },
}


class RoleTrainer:
    def get_roles(self) -> List[Dict]:
        return [
            {"id": k, "label": v["label"], "description": v["description"], "focus_areas": v["focus_areas"]}
            for k, v in ROLE_DEFINITIONS.items()
        ]

    def get_role(self, role_id: str) -> Optional[Dict]:
        role = ROLE_DEFINITIONS.get(role_id)
        if not role:
            return None
        scenarios = []
        for theme in role.get("scenario_themes", []):
            template = SCENARIO_TEMPLATES.get(theme, {})
            if template:
                scenarios.append({"id": theme, **template})
        return {"id": role_id, **role, "scenarios": scenarios}

    def get_scenario(self, scenario_id: str) -> Optional[Dict]:
        return SCENARIO_TEMPLATES.get(scenario_id)

    def get_system_prompt(self, role_id: str, scenario_id: Optional[str] = None) -> str:
        role = ROLE_DEFINITIONS.get(role_id)
        if not role:
            return "You are a communication coach."
        prompt = role["system_prompt"]
        if scenario_id:
            scenario = SCENARIO_TEMPLATES.get(scenario_id, {})
            prompt += f"\n\nScenario: {scenario.get('title', scenario_id)} - {scenario.get('description', '')}"
        return prompt

    def evaluate_role_response(self, role_id: str, response_data: Dict) -> Dict:
        role = ROLE_DEFINITIONS.get(role_id)
        if not role:
            return {"error": "Unknown role"}
        focus_scores = {}
        for area in role.get("focus_areas", []):
            if area == "clarity":
                focus_scores[area] = response_data.get("clarity_score", 0) or (response_data.get("scores") or {}).get("clarity", 0) or 0.5
            elif area == "engagement":
                focus_scores[area] = response_data.get("engagement_score", 0) or (response_data.get("scores") or {}).get("engagement", 0) or 0.5
            elif area == "confidence":
                focus_scores[area] = response_data.get("confidence_score", 0) or (response_data.get("scores") or {}).get("confidence", 0) or 0.5
            else:
                focus_scores[area] = 0.5
        avg_score = sum(focus_scores.values()) / len(focus_scores) if focus_scores else 0
        return {
            "role": role["label"],
            "focus_scores": focus_scores,
            "overall_score": round(avg_score, 2),
            "primary_recommendation": self._get_primary_recommendation(focus_scores),
        }

    def _get_primary_recommendation(self, scores: Dict) -> str:
        lowest = min(scores, key=scores.get)
        return f"Focus on improving {lowest.replace('_', ' ').title()} (current: {scores[lowest]*100:.0f}%)"


role_trainer = RoleTrainer()
