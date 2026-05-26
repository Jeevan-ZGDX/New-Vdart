from fastapi import APIRouter
from talkcraft_enterprise.recruiter.simulator import recruiter_simulator

router = APIRouter(prefix="/api/recruiter", tags=["recruiter"])


@router.get("/interview-types")
async def get_interview_types():
    return {"interview_types": recruiter_simulator.get_interview_types()}


@router.get("/personas")
async def get_personas():
    return {"personas": recruiter_simulator.get_personas()}


@router.get("/questions")
async def get_questions(interview_type: str = "general", count: int = 3):
    return {"questions": recruiter_simulator.get_questions(interview_type, count)}


@router.post("/prompt")
async def generate_prompt(interview_type: str = "general", persona: str = "professional", role_context: str = None):
    return {"system_prompt": recruiter_simulator.generate_system_prompt(interview_type, persona, role_context)}


@router.post("/evaluate")
async def evaluate_response(response: str, question: str, metrics: dict):
    return recruiter_simulator.evaluate_interview_response(response, question, metrics)
