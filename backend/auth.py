import hashlib
import secrets
import math
import time
from threading import Lock
from typing import Tuple

import bcrypt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from beanie import PydanticObjectId
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.config import settings
from backend.models.car_model import CarModel
from backend.models.session import AuthSession
from backend.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)
password_hasher = PasswordHasher()
# A valid fixed hash makes unknown-user requests perform the same expensive verification.
DUMMY_PASSWORD_HASH = "$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQxMjM0NTY3OA$DLKqI7p0+T/XUrXTV/qHEkPxOOgg0goDYVP7YDJJJZ8"

# Process-local fixed-window limiter: workers do not share quotas. At capacity we
# reject new keys rather than evicting active limits; proxy headers are not trusted.
login_buckets: dict[str, tuple[float, int]] = {}
login_buckets_lock = Lock()


def throttle_login(request: Request) -> None:
    key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with login_buckets_lock:
        for expired in [key for key, (until, _) in login_buckets.items() if until <= now]:
            del login_buckets[expired]
        until, count = login_buckets.get(key, (now + settings.login_window_seconds, 0))
        if count >= settings.login_max_attempts or (
            key not in login_buckets and len(login_buckets) >= settings.login_max_buckets
        ):
            raise HTTPException(429, "Too many login attempts", headers={"Retry-After": str(max(1, math.ceil(until - now)))})
        login_buckets[key] = (until, count + 1)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        if password_hash.startswith("$2"):
            # Persisted bcrypt credentials remain usable, but never accept ambiguous
            # >72-byte input. Those accounts require an administrator password reset.
            encoded = password.encode("utf-8")
            return len(encoded) <= 72 and bcrypt.checkpw(encoded, password_hash.encode("utf-8"))
        return password_hasher.verify(password_hash, password)
    except (ValueError, InvalidHashError, VerificationError):
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_session(user: User) -> Tuple[AuthSession, str]:
    token = secrets.token_urlsafe(32)
    session = AuthSession(
        token_hash=hash_token(token),
        user_id=user.id,
        credential_version=user.credential_version,
        expires_at=AuthSession.new_expiry(settings.session_ttl_days),
    )
    await session.insert()
    current = await User.get(user.id)
    if not current or current.is_deleting or current.credential_version != session.credential_version:
        await session.delete()
        raise HTTPException(status_code=401, detail="Credentials changed; log in again")
    return session, token


async def get_current_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthSession:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    session = await AuthSession.find_one(AuthSession.token_hash == hash_token(credentials.credentials))
    if not session or session.is_expired():
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return session


async def get_current_user(session: AuthSession = Depends(get_current_session)) -> User:
    user = await User.get(session.user_id)
    if not user or user.is_deleting or user.credential_version != session.credential_version:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


async def get_owned_car(
    car_id: PydanticObjectId,
    user: User = Depends(get_current_user),
) -> CarModel:
    car = await CarModel.get(car_id)
    if not car or car.is_deleting or car.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


async def ensure_car_owner_active(car: CarModel) -> None:
    """Compensate for car creation already in flight when account deletion begins."""
    owner = await User.get(car.owner_id)
    if not owner or owner.is_deleting:
        await car.delete()
        raise HTTPException(status_code=401, detail="Account is being deleted")
