"""Audit log read service."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.audit_log import AuditLog


class AuditReadService:
    async def list_logs(
        self,
        db: AsyncSession,
        *,
        limit: int = 50,
        offset: int = 0,
        action_prefix: str | None = None,
    ) -> tuple[list[AuditLog], int]:
        base = select(AuditLog)
        count_stmt = select(func.count()).select_from(AuditLog)
        if action_prefix:
            pattern = f"{action_prefix}%"
            base = base.where(AuditLog.action.like(pattern))
            count_stmt = count_stmt.where(AuditLog.action.like(pattern))
        total = int((await db.execute(count_stmt)).scalar_one())
        result = await db.execute(
            base.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total


audit_read_service = AuditReadService()
