import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool

from backend.auth import (
    create_session,
    get_current_session,
    get_current_user,
    hash_password,
    verify_password,
    DUMMY_PASSWORD_HASH,
    throttle_login,
)
from backend.config import settings
from backend.database import recover_legacy_claim
from backend.models.session import AuthSession
from backend.models.user import (
    AuthResponse,
    LoginRequest,
    PasswordChange,
    SetupRequest,
    User,
    UserResponse,
    FIRST_ADMIN_ID,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/status")
async def auth_status():
    return {
        "setup_required": await User.find_all().count() == 0,
        "setup_token_required": settings.setup_token is not None,
    }


@router.post("/setup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def setup(payload: SetupRequest, x_setup_token: str | None = Header(default=None)):
    if settings.setup_token is not None and not secrets.compare_digest(
        (x_setup_token or "").encode("utf-8"), settings.setup_token.get_secret_value().encode("utf-8")
    ):
        raise HTTPException(status_code=403, detail="Invalid setup token")
    if await User.find_all().count() > 0:
        raise HTTPException(status_code=403, detail="Setup has already been completed")

    user = User(
        id=FIRST_ADMIN_ID,
        username=payload.username,
        password_hash=await run_in_threadpool(hash_password, payload.password),
        is_admin=True,
    )
    try:
        await user.insert()
    except DuplicateKeyError:
        raise HTTPException(status_code=403, detail="Setup has already been completed") from None
    await recover_legacy_claim()

    session, token = await create_session(user)
    return AuthResponse(token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, request: Request):
    throttle_login(request)
    user = await User.find_one(User.username == payload.username.strip().lower())
    valid = await run_in_threadpool(
        verify_password, payload.password, user.password_hash if user else DUMMY_PASSWORD_HASH
    )
    if not user or user.is_deleting or not valid:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    session, token = await create_session(user)
    return AuthResponse(token=token, user=UserResponse.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(session: AuthSession = Depends(get_current_session)):
    await session.delete()


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: PasswordChange,
    session: AuthSession = Depends(get_current_session),
    user: User = Depends(get_current_user),
):
    if not await run_in_threadpool(verify_password, payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    password_hash = await run_in_threadpool(hash_password, payload.new_password)
    result = await User.get_pymongo_collection().update_one(
        {"_id": user.id, "password_hash": user.password_hash, "is_deleting": {"$ne": True},
         "$or": [{"credential_version": user.credential_version}, {"credential_version": {"$exists": False}}]},
        {"$set": {"password_hash": password_hash}, "$inc": {"credential_version": 1}},
    )
    if not result.matched_count:
        raise HTTPException(status_code=409, detail="Credentials changed; log in again")
    result = await AuthSession.get_pymongo_collection().update_one(
        {"_id": session.id}, {"$set": {"credential_version": user.credential_version + 1}}
    )
    if not result.matched_count:
        raise HTTPException(status_code=409, detail="Session revoked; log in again")

    # Invalidate every other session; the one making the change stays valid.
    await AuthSession.find(
        AuthSession.user_id == user.id,
        AuthSession.id != session.id,
        {"$or": [{"credential_version": {"$lte": user.credential_version}}, {"credential_version": {"$exists": False}}]},
    ).delete()
