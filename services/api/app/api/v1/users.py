"""User routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user, get_user_entity
from app.application.auth_service import auth_service
from app.core.database import get_db
from app.schemas.auth import LoginEventResponse, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: Annotated[object, Depends(get_user_entity)]):
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        roles=[r.role for r in user.roles],
    )


@router.get("/me/login-events", response_model=list[LoginEventResponse])
async def list_my_login_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    limit: int = Query(default=50, ge=1, le=200),
):
    events = await auth_service.list_login_events(db, user_id=current.user_id, limit=limit)
    return [LoginEventResponse.model_validate(event) for event in events]
