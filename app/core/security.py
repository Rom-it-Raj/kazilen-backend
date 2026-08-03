from datetime import datetime, timedelta, timezone
import hashlib
import random
import jwt

from app.core.config import settings


def generate_otp() -> str:
    """Generate 6-digit OTP."""
    return str(random.randint(100000, 999999))


def hash_otp(otp: str) -> str:
    """Hash OTP string using SHA-256 for secure storage."""
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"sub": str(subject), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

