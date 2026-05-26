from fastapi import APIRouter
from talkcraft_enterprise.benchmarking.benchmarks import benchmark_engine

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])


@router.post("/calculate")
async def calculate_benchmarks(session_data: dict):
    return benchmark_engine.calculate_benchmarks(session_data)


@router.get("/roles")
async def get_roles():
    return {"roles": benchmark_engine.get_role_list()}


@router.post("/roles/{role_id}/score")
async def get_role_score(role_id: str, session_data: dict):
    return benchmark_engine.get_role_score(role_id, session_data)


@router.post("/percentile")
async def calculate_percentile(user_score: float, all_scores: list):
    return {"percentile": benchmark_engine.calculate_percentile(user_score, all_scores)}
