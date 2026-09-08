import hashlib
import secrets
import math
from datetime import datetime, timezone
from typing import Tuple

import bcrypt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from beanie import PydanticObjectId
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from backend.config import settings
from backend.models.car_model import CarModel, CarResponse
from backend.models.car_share import CarAccess, CarShare, SharePermissions
from backend.models.session import AuthSession
from backend.models.user import LoginRateLimit, User

bearer_scheme = HTTPBearer(auto_error=False)
password_hasher = PasswordHasher()
# A valid fixed hash makes unknown-user requests perform the same expensive verification.
DUMMY_PASSWORD_HASH = "$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQxMjM0NTY3OA$DLKqI7p0+T/XUrXTV/qHEkPxOOgg0goDYVP7YDJJJZ8"

async def throttle_auth(request: Request, account: str) -> None:
    """Consume fixed-window quotas for both account and direct client IP."""
    now = datetime.now(timezone.utc)
    window = settings.login_window_seconds
    window_number = int(now.timestamp()) // window
    expires_at = datetime.fromtimestamp((window_number + 1) * window, timezone.utc)
    retry_after = str(max(1, math.ceil((expires_at - now).total_seconds())))
    ip = request.client.host if request.client else "unknown"

    # Consume the IP quota first so rejected rotating usernames cannot create
    # additional account buckets once a client has exhausted its quota.
    for dimension, value in (("ip", ip), ("account", account.strip().lower())):
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        key = f"{dimension}:{window_number}:{digest}"
        try:
            bucket = await LoginRateLimit.get_pymongo_collection().find_one_and_update(
                {"key": key, "attempts": {"$lt": settings.login_max_attempts}},
                {"$inc": {"attempts": 1}, "$setOnInsert": {"key": key, "expires_at": expires_at}},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError:
            bucket = None
        if bucket is None:
            raise HTTPException(
                status_code=429,
                detail="Too many authentication attempts",
                headers={"Retry-After": retry_after},
            )


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        if password_hash.startswith("$2"):
            # Persisted bcrypt credentials remain usable, but never accept ambiguous
            # >72-byte input. Those accounts require an administrator password reset.
            encoded = password.encode("utf-8")
            if len(encoded) > 72:
                bcrypt.checkpw(encoded[:72], password_hash.encode("utf-8"))
                return False
            return bcrypt.checkpw(encoded, password_hash.encode("utf-8"))
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
    car = await get_accessible_car(car_id, user)
    if car.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Vehicle owner required")
    return car


async def get_accessible_car(car_id: PydanticObjectId, user: User) -> CarModel:
    car = await CarModel.get(car_id)
    if not car or car.is_deleting:
        raise HTTPException(404, "Car not found")
    owner = await User.get(car.owner_id) if car.owner_id else None
    if not owner or owner.is_deleting:
        raise HTTPException(404, "Car not found")
    if car.owner_id != user.id and not await CarShare.find_one({"car_id": car.id, "user_id": user.id}):
        raise HTTPException(404, "Car not found")
    return car


def require_car_section(section: str):
    async def dependency(
        request: Request,
        car_id: PydanticObjectId,
        user: User = Depends(get_current_user),
    ) -> CarModel:
        car = await get_accessible_car(car_id, user)
        if car.owner_id != user.id:
            grant = await CarShare.find_one({"car_id": car.id, "user_id": user.id})
            if not grant:
                raise HTTPException(404, "Car not found")
            permission = getattr(grant.permissions, section)
            if permission == "none" or (request.method not in ("GET", "HEAD") and permission != "edit"):
                raise HTTPException(403, f"{section.capitalize()} permission required")
        return car

    return dependency


get_vehicle_car = require_car_section("vehicle")
get_maintenance_car = require_car_section("maintenance")
get_mods_car = require_car_section("mods")


async def car_response(car: CarModel, user: User) -> CarResponse:
    owner = await User.get(car.owner_id)
    is_owner = car.owner_id == user.id
    grant = None if is_owner else await CarShare.find_one({"car_id": car.id, "user_id": user.id})
    if not owner or owner.is_deleting or car.is_deleting or (not is_owner and not grant):
        raise HTTPException(404, "Car not found")
    return CarResponse(
        **car.model_dump(exclude={"is_deleting", "owner_id", "revision_id"}),
        access=CarAccess(is_owner=is_owner, owner_username=owner.username,
                         permissions=SharePermissions(vehicle="edit", maintenance="edit", mods="edit") if is_owner else grant.permissions),
    )


async def ensure_car_owner_active(car: CarModel) -> None:
    """Compensate for car creation already in flight when account deletion begins."""
    owner = await User.get(car.owner_id)
    if not owner or owner.is_deleting:
        await car.delete()
        raise HTTPException(status_code=401, detail="Account is being deleted")
