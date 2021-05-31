from datetime import datetime, timedelta
from typing import Type, Optional

import jwt
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.core.config import SECRET_KEY, JWT_AUDIENCE, ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM
from app.models.token import JWTMeta, JWTCreds, JWTPayload
from app.models.user import UserBase


def create_access_token_for_user(
    *,
    user: Type[UserBase],
    secret_key: str = str(SECRET_KEY),
    audience: str = JWT_AUDIENCE,
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    if not user or not isinstance(user, UserBase):
        return None

    jwt_meta = JWTMeta(
        aud=audience,
        iat=datetime.timestamp(datetime.utcnow()),
        exp=datetime.timestamp(datetime.utcnow() + timedelta(minutes=expires_in)),
    )
    jwt_creds = JWTCreds(sub=user.email, username=user.username)
    token_payload = JWTPayload(
        **jwt_meta.dict(),
        **jwt_creds.dict(),
    )

    access_token = jwt.encode(token_payload.dict(), secret_key, algorithm=JWT_ALGORITHM)

    return access_token


def get_username_from_token(*, token: str, secret_key: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(token, str(secret_key), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])
        payload = JWTPayload(**decoded_token)
    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload.username
