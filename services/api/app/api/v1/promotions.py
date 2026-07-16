"""Promotions bridge — proxy to Go promo service."""

import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import bearer_scheme, get_current_user, require_scopes
from app.core.config import settings
from app.core.errors import AppError
from app.domain.auth.scopes import Scope

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/promotions", tags=["promotions"])


async def _proxy_promo(
    request: Request,
    path: str,
    credentials: HTTPAuthorizationCredentials,
) -> Response:
    url = f"{settings.promo_url.rstrip('/')}/api/v1/campaigns{path}"
    headers: dict[str, str] = {
        "Accept": "application/json",
        "Authorization": f"{credentials.scheme} {credentials.credentials}",
    }

    body = await request.body()
    content_type = request.headers.get("content-type")
    if content_type:
        headers["Content-Type"] = content_type

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            upstream = await client.request(
                request.method,
                url,
                headers=headers,
                content=body if body else None,
                params=dict(request.query_params),
            )
    except httpx.RequestError as exc:
        logger.warning("promo proxy request failed: %s", exc)
        raise AppError("promo_unavailable", "Promotion service unavailable", status_code=502) from exc

    response_headers = {}
    if upstream.headers.get("content-type"):
        response_headers["content-type"] = upstream.headers["content-type"]

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )


async def _promo_read_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> HTTPAuthorizationCredentials:
    user = await get_current_user(credentials)
    if not user.has_scope(Scope.PROMO_READ):
        raise AppError("forbidden", "Insufficient scope", status_code=403)
    assert credentials is not None
    return credentials


async def _promo_write_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> HTTPAuthorizationCredentials:
    user = await get_current_user(credentials)
    if not user.has_scope(Scope.PROMO_WRITE):
        raise AppError("forbidden", "Insufficient scope", status_code=403)
    assert credentials is not None
    return credentials


@router.get("/campaigns")
async def list_campaigns(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_promo_read_user)],
):
    return await _proxy_promo(request, "", credentials)


@router.post("/campaigns")
async def create_campaign(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_promo_write_user)],
):
    return await _proxy_promo(request, "", credentials)


@router.get("/campaigns/{campaign_path:path}")
async def get_campaign_route(
    request: Request,
    campaign_path: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_promo_read_user)],
):
    return await _proxy_promo(request, f"/{campaign_path}", credentials)


@router.patch("/campaigns/{campaign_path:path}")
async def update_campaign_route(
    request: Request,
    campaign_path: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_promo_write_user)],
):
    return await _proxy_promo(request, f"/{campaign_path}", credentials)


@router.delete("/campaigns/{campaign_path:path}")
async def delete_campaign_route(
    request: Request,
    campaign_path: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_promo_write_user)],
):
    return await _proxy_promo(request, f"/{campaign_path}", credentials)


@router.post("/campaigns/{campaign_path:path}")
async def campaign_post_route(
    request: Request,
    campaign_path: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_promo_write_user)],
):
    return await _proxy_promo(request, f"/{campaign_path}", credentials)
