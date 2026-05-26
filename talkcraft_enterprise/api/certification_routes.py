from fastapi import APIRouter
from talkcraft_enterprise.certification.scoring import certification_scorer, CERTIFICATION_LEVELS

router = APIRouter(prefix="/api/certification", tags=["certification"])


@router.get("/levels")
async def get_levels():
    return {"levels": [{"id": k, "name": v["name"], "description": v["description"], "min_score": v["min_score"], "requirements": v["requirements"]} for k, v in CERTIFICATION_LEVELS.items()]}


@router.post("/assess")
async def assess_level(user_stats: dict):
    return certification_scorer.assess_level(user_stats)


@router.post("/evaluate")
async def evaluate_session(session_data: dict):
    return certification_scorer.evaluate_session_for_certification(session_data)


@router.post("/certificate/generate")
async def generate_certificate(user_id: int, level: str, score: float, language: str = "en"):
    return certification_scorer.generate_certificate(user_id, level, score, language)
