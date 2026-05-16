"""Opaque refresh tokens: id + secret, secret stored as SHA256 hash."""

import base64
import hashlib
import json
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from src.core.config import Settings


@dataclass(frozen=True)
class RefreshMaterial:
    """Parsed refresh token from client."""

    row_id: uuid.UUID
    secret: str


def _hash_secret(settings: Settings, secret: str) -> str:
    raw = f"{settings.jwt_refresh_secret}:{secret}".encode()
    return hashlib.sha256(raw).hexdigest()


def create_refresh_pair(settings: Settings, row_id: uuid.UUID) -> tuple[str, str]:
    """Return (raw_refresh_token_for_client, secret_hash_for_db)."""
    secret = secrets.token_urlsafe(32)
    payload: dict[str, Any] = {"id": str(row_id), "s": secret}
    raw = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).decode()
    return raw, _hash_secret(settings, secret)


def parse_refresh_token(raw: str) -> RefreshMaterial:
    try:
        decoded = base64.urlsafe_b64decode(raw.encode())
        data = json.loads(decoded.decode())
        row_id = uuid.UUID(str(data["id"]))
        secret = str(data["s"])
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("malformed refresh token") from exc
    return RefreshMaterial(row_id=row_id, secret=secret)


def verify_refresh_secret(settings: Settings, secret: str, secret_hash: str) -> bool:
    return secrets.compare_digest(_hash_secret(settings, secret), secret_hash)


def refresh_expires_at(settings: Settings) -> datetime:
    return datetime.now(UTC) + timedelta(seconds=settings.jwt_refresh_expires_in)
