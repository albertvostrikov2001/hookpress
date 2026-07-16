"""API v1 routes."""

from fastapi import APIRouter

from app.api.v1 import admin, auth, billing, charts, chat, disputes, feed, market, media, notifications, office, promotions, studio, users, webhooks

router = APIRouter()

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(admin.router)
router.include_router(studio.router)
router.include_router(media.router)
router.include_router(office.router)
router.include_router(market.router)
router.include_router(billing.router)
router.include_router(disputes.router)
router.include_router(feed.router)
router.include_router(charts.router)
router.include_router(chat.router)
router.include_router(notifications.router)
router.include_router(promotions.router)
router.include_router(webhooks.router)


@router.get("/")
async def api_root():
    return {
        "name": "hook.press API",
        "version": "v1",
        "docs": "/api/v1/docs",
    }
