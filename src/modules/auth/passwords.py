"""Password hashing (bcrypt, cost 12 per stack).

Uses the `bcrypt` package directly (passlib's bcrypt self-tests break on Python 3.14+
with modern bcrypt due to the 72-byte password limit during backend detection).
"""

import re

import bcrypt


def validate_password_strength(plain: str) -> str:
    """Password rules shared by register and admin user flows.

    Raises ValueError on failure.
    """
    if not re.search(r"[A-Z]", plain):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"\d", plain):
        raise ValueError("Password must contain at least one digit")
    return plain


def hash_password(plain: str) -> str:
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed.decode("ascii")


def verify_password(plain: str, password_hash: str) -> bool:
    return bool(
        bcrypt.checkpw(plain.encode("utf-8"), password_hash.encode("utf-8")),
    )
