"""Auth request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class DevLoginRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token TTL in seconds")


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    display_name: str
    roles: list[str]

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    tokens: TokenResponse
    user: UserResponse


class SessionResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    expires_at: datetime
    ip_address: str | None
    user_agent: str | None

    model_config = {"from_attributes": True}


class OAuthStartResponse(BaseModel):
    redirect_url: str
    provider: str


class LoginEventResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    method: str
    success: bool
    failure_reason: str | None = None
    ip_address: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SetUserRolesRequest(BaseModel):
    roles: list[str] = Field(min_length=1)
