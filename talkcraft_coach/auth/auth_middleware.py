from fastapi import Header, HTTPException, status
from typing import Optional
from talkcraft_coach.auth.auth_handler import auth_handler


async def require_auth(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Use: Bearer <token>",
        )
    user = auth_handler.get_current_user(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return user


async def optional_auth(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return auth_handler.get_current_user(token)
