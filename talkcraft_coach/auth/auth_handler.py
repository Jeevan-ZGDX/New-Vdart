import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import HTTPException, status
from talkcraft_coach.utils.config import config
from talkcraft_coach.utils.logger import get_logger

logger = get_logger("auth")


class AuthHandler:
    def __init__(self):
        self.secret = config.auth.secret_key
        self.algorithm = config.auth.algorithm
        self.access_expire = config.auth.access_token_expire_minutes
        self.refresh_expire = config.auth.refresh_token_expire_days

    def hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return f"{salt}${pwd_hash.hex()}"

    def verify_password(self, password: str, stored: str) -> bool:
        try:
            salt, pwd_hash = stored.split("$", 1)
            computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
            return computed.hex() == pwd_hash
        except Exception:
            return False

    def create_access_token(self, user_id: int, username: str) -> str:
        expiry = datetime.utcnow() + timedelta(minutes=self.access_expire)
        payload = {
            "sub": str(user_id),
            "username": username,
            "type": "access",
            "exp": expiry,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: int) -> str:
        expiry = datetime.utcnow() + timedelta(days=self.refresh_expire)
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": expiry,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid token: {e}")
            return None

    def get_current_user(self, token: str) -> Optional[dict]:
        payload = self.decode_token(token)
        if payload is None or payload.get("type") != "access":
            return None
        return {"user_id": int(payload["sub"]), "username": payload.get("username", "")}


auth_handler = AuthHandler()
