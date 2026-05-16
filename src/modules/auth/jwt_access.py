"""Access JWT (HS256, short TTL)."""

from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

from jose import JWTError, jwt

from src.core.config import Settings


def create_access_token(user_id: UUID, settings: Settings) -> str:
    now = datetime.now(UTC)
    expire = now + timedelta(seconds=settings.jwt_expires_in)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "typ": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if settings.jwt_issuer:
        payload["iss"] = settings.jwt_issuer
    if settings.jwt_audience:
        payload["aud"] = settings.jwt_audience
    return cast(str, jwt.encode(payload, settings.jwt_secret, algorithm="HS256"))


def decode_access_token(token: str, settings: Settings) -> UUID:
    options: dict[str, Any] = {"require": ["exp", "sub"]}
    if settings.jwt_audience:
        options["verify_aud"] = True
    else:
        options["verify_aud"] = False
    decode_kw: dict[str, Any] = {
        "algorithms": ["HS256"],
        "options": options,
    }
    if settings.jwt_audience:
        decode_kw["audience"] = settings.jwt_audience
    if settings.jwt_issuer:
        decode_kw["issuer"] = settings.jwt_issuer
    try:
        payload = jwt.decode(token, settings.jwt_secret, **decode_kw)
    except JWTError as exc:
        raise ValueError("invalid access token") from exc
    if payload.get("typ") != "access":
        raise ValueError("wrong token type")
    sub = payload.get("sub")
    if not sub or not isinstance(sub, str):
        raise ValueError("missing sub")
    return UUID(sub)
