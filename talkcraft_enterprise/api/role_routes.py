from fastapi import APIRouter
from talkcraft_enterprise.role_training.roles import role_trainer

router = APIRouter(prefix="/api/roles", tags=["role_training"])


@router.get("")
async def get_roles():
    return {"roles": role_trainer.get_roles()}


@router.get("/{role_id}")
async def get_role(role_id: str):
    role = role_trainer.get_role(role_id)
    if not role:
        return {"error": "Role not found"}
    return role


@router.get("/{role_id}/system-prompt")
async def get_system_prompt(role_id: str, scenario_id: str = None):
    return {"system_prompt": role_trainer.get_system_prompt(role_id, scenario_id)}


@router.post("/{role_id}/evaluate")
async def evaluate_response(role_id: str, response_data: dict):
    return role_trainer.evaluate_role_response(role_id, response_data)
