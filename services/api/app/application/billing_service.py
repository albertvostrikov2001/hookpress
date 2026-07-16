"""Double-entry billing and payment webhooks."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.audit import write_audit
from app.application.market_service import market_service
from app.core.config import settings
from app.core.errors import AppError
from app.infrastructure.models.ledger_account import LedgerAccount
from app.infrastructure.models.ledger_entry import LedgerEntry
from app.infrastructure.models.market_order import MarketOrder
from app.infrastructure.providers.payment import PaymentIntent, PaymentProvider


class BillingService:
    ACCOUNT_USER_WALLET = "USER_WALLET"
    ACCOUNT_ESCROW = "ESCROW"
    ACCOUNT_SYSTEM = "SYSTEM"
    ACCOUNT_COMMISSION = "COMMISSION"

    async def ensure_commission(self, db: AsyncSession) -> LedgerAccount:
        return await self._get_or_create_account(
            db, owner_id=None, account_type=self.ACCOUNT_COMMISSION
        )

    async def ensure_system(self, db: AsyncSession) -> LedgerAccount:
        return await self._get_or_create_account(
            db, owner_id=None, account_type=self.ACCOUNT_SYSTEM
        )

    async def ensure_wallet(self, db: AsyncSession, user_id: uuid.UUID) -> LedgerAccount:
        return await self._get_or_create_account(
            db, owner_id=user_id, account_type=self.ACCOUNT_USER_WALLET
        )

    async def ensure_escrow(self, db: AsyncSession, order_id: uuid.UUID) -> LedgerAccount:
        return await self._get_or_create_account(
            db,
            owner_id=None,
            account_type=self.ACCOUNT_ESCROW,
            reference_type="market_order",
            reference_id=order_id,
        )

    async def get_balance(self, db: AsyncSession, account_id: uuid.UUID) -> int:
        result = await db.execute(
            select(func.coalesce(func.sum(LedgerEntry.amount_minor), 0)).where(
                LedgerEntry.account_id == account_id
            )
        )
        return int(result.scalar_one())

    async def credit_wallet(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        amount_minor: int,
        idempotency_key: str,
        description: str,
        reference_type: str | None = None,
        reference_id: uuid.UUID | None = None,
    ) -> list[LedgerEntry]:
        if amount_minor <= 0:
            raise AppError("invalid_amount", "Amount must be positive", status_code=400)
        account = await self.ensure_wallet(db, user_id)
        system = await self.ensure_system(db)
        return await self._post_transaction(
            db,
            entries=[
                (system.id, -amount_minor, "DEBIT", description),
                (account.id, amount_minor, "CREDIT", description),
            ],
            idempotency_prefix=idempotency_key,
            reference_type=reference_type,
            reference_id=reference_id,
        )

    async def hold_funds(
        self,
        db: AsyncSession,
        *,
        buyer_id: uuid.UUID,
        order_id: uuid.UUID,
        amount_minor: int,
        idempotency_key: str,
    ) -> list[LedgerEntry]:
        buyer_wallet = await self.ensure_wallet(db, buyer_id)
        escrow = await self.ensure_escrow(db, order_id)
        balance = await self.get_balance(db, buyer_wallet.id)
        if balance < amount_minor:
            raise AppError("insufficient_funds", "Insufficient wallet balance", status_code=402)
        return await self._post_transaction(
            db,
            entries=[
                (buyer_wallet.id, -amount_minor, "DEBIT", f"Hold for order {order_id}"),
                (escrow.id, amount_minor, "CREDIT", f"Escrow hold for order {order_id}"),
            ],
            idempotency_prefix=idempotency_key,
            reference_type="market_order",
            reference_id=order_id,
        )

    async def capture_funds(
        self,
        db: AsyncSession,
        *,
        seller_id: uuid.UUID,
        order_id: uuid.UUID,
        amount_minor: int,
        idempotency_key: str,
    ) -> list[LedgerEntry]:
        escrow = await self.ensure_escrow(db, order_id)
        seller_wallet = await self.ensure_wallet(db, seller_id)
        commission_account = await self.ensure_commission(db)
        escrow_balance = await self.get_balance(db, escrow.id)
        if escrow_balance < amount_minor:
            raise AppError("insufficient_escrow", "Escrow balance insufficient", status_code=409)

        commission = (amount_minor * settings.platform_commission_bps) // 10_000
        seller_payout = amount_minor - commission

        entries: list[tuple[uuid.UUID, int, str, str]] = [
            (escrow.id, -amount_minor, "DEBIT", f"Capture for order {order_id}"),
            (seller_wallet.id, seller_payout, "CREDIT", f"Payout for order {order_id}"),
        ]
        if commission > 0:
            entries.append(
                (commission_account.id, commission, "CREDIT", f"Platform commission for order {order_id}")
            )

        return await self._post_transaction(
            db,
            entries=entries,
            idempotency_prefix=idempotency_key,
            reference_type="market_order",
            reference_id=order_id,
        )

    async def refund_funds(
        self,
        db: AsyncSession,
        *,
        buyer_id: uuid.UUID,
        order_id: uuid.UUID,
        amount_minor: int,
        idempotency_key: str,
        partial: bool = False,
    ) -> list[LedgerEntry]:
        escrow = await self.ensure_escrow(db, order_id)
        buyer_wallet = await self.ensure_wallet(db, buyer_id)
        escrow_balance = await self.get_balance(db, escrow.id)
        if escrow_balance < amount_minor:
            raise AppError("insufficient_escrow", "Escrow balance insufficient for refund", status_code=409)
        label = "Partial refund" if partial else "Refund"
        return await self._post_transaction(
            db,
            entries=[
                (escrow.id, -amount_minor, "DEBIT", f"{label} for order {order_id}"),
                (buyer_wallet.id, amount_minor, "CREDIT", f"{label} for order {order_id}"),
            ],
            idempotency_prefix=idempotency_key,
            reference_type="market_order",
            reference_id=order_id,
        )

    async def initiate_payment(
        self,
        db: AsyncSession,
        payment_provider: PaymentProvider,
        *,
        order_id: uuid.UUID,
        buyer_id: uuid.UUID,
        idempotency_key: str,
    ) -> PaymentIntent:
        order = await market_service.get_order(db, order_id)
        if order.buyer_id != buyer_id:
            raise AppError("forbidden", "Not the order buyer", status_code=403)
        if order.status != "AWAITING_PAYMENT":
            raise AppError("invalid_order_state", "Order is not awaiting payment", status_code=409)
        if order.payment_idempotency_key:
            idempotency_key = order.payment_idempotency_key
        else:
            order.payment_idempotency_key = idempotency_key
            await db.flush()
        return await payment_provider.create_payment(
            order_id=str(order_id),
            amount_minor=order.amount_minor,
            idempotency_key=idempotency_key,
        )

    async def process_payment_webhook(
        self,
        db: AsyncSession,
        payment_provider: PaymentProvider,
        *,
        payload: dict,
        idempotency_key: str,
    ) -> MarketOrder:
        existing = await db.execute(
            select(LedgerEntry).where(LedgerEntry.idempotency_key == f"{idempotency_key}:hold")
        )
        if existing.scalar_one_or_none():
            order_id = uuid.UUID(payload["order_id"])
            return await market_service.get_order(db, order_id)

        intent = await payment_provider.parse_webhook({**payload, "idempotency_key": idempotency_key})
        if intent.status != "succeeded":
            raise AppError("payment_failed", "Payment not successful", status_code=402)

        order_id = uuid.UUID(intent.metadata["order_id"])
        order = await market_service.get_order(db, order_id)
        if order.status == "FUNDS_HELD":
            return order

        await self.credit_wallet(
            db,
            user_id=order.buyer_id,
            amount_minor=intent.amount_minor,
            idempotency_key=f"{idempotency_key}:topup",
            description=f"Payment top-up for order {order_id}",
            reference_type="market_order",
            reference_id=order_id,
        )
        await self.hold_funds(
            db,
            buyer_id=order.buyer_id,
            order_id=order_id,
            amount_minor=intent.amount_minor,
            idempotency_key=f"{idempotency_key}:hold",
        )
        await market_service.transition_order(db, order, "FUNDS_HELD", actor_user_id=order.buyer_id)
        await write_audit(
            db,
            action="billing.payment_webhook",
            resource_type="market_order",
            resource_id=str(order_id),
            metadata={"idempotency_key": idempotency_key},
        )
        await db.commit()
        return order

    async def list_wallet_entries(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        limit: int = 50,
    ) -> list[LedgerEntry]:
        account = await self.ensure_wallet(db, user_id)
        result = await db.execute(
            select(LedgerEntry)
            .where(LedgerEntry.account_id == account.id)
            .order_by(LedgerEntry.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def reconciliation(self, db: AsyncSession) -> dict:
        system = await self.ensure_system(db)
        commission = await self.ensure_commission(db)

        escrow_result = await db.execute(
            select(LedgerAccount).where(LedgerAccount.account_type == self.ACCOUNT_ESCROW)
        )
        escrow_accounts = list(escrow_result.scalars().all())
        escrow_total = 0
        for account in escrow_accounts:
            escrow_total += await self.get_balance(db, account.id)

        wallet_result = await db.execute(
            select(LedgerAccount).where(LedgerAccount.account_type == self.ACCOUNT_USER_WALLET)
        )
        wallet_accounts = list(wallet_result.scalars().all())
        wallet_total = 0
        for account in wallet_accounts:
            wallet_total += await self.get_balance(db, account.id)

        system_balance = await self.get_balance(db, system.id)
        commission_balance = await self.get_balance(db, commission.id)

        grand_total = system_balance + commission_balance + escrow_total + wallet_total
        return {
            "system_balance_minor": system_balance,
            "commission_balance_minor": commission_balance,
            "escrow_total_minor": escrow_total,
            "wallet_total_minor": wallet_total,
            "escrow_account_count": len(escrow_accounts),
            "wallet_account_count": len(wallet_accounts),
            "balanced": grand_total == 0,
            "platform_commission_bps": settings.platform_commission_bps,
        }

    async def _get_or_create_account(
        self,
        db: AsyncSession,
        *,
        owner_id: uuid.UUID | None,
        account_type: str,
        reference_type: str | None = None,
        reference_id: uuid.UUID | None = None,
    ) -> LedgerAccount:
        stmt = select(LedgerAccount).where(
            LedgerAccount.owner_id == owner_id,
            LedgerAccount.account_type == account_type,
            LedgerAccount.reference_type == reference_type,
            LedgerAccount.reference_id == reference_id,
        )
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()
        if account:
            return account
        account = LedgerAccount(
            owner_id=owner_id,
            account_type=account_type,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        db.add(account)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            result = await db.execute(stmt)
            account = result.scalar_one()
        return account

    async def _post_transaction(
        self,
        db: AsyncSession,
        *,
        entries: list[tuple[uuid.UUID, int, str, str]],
        idempotency_prefix: str,
        reference_type: str | None = None,
        reference_id: uuid.UUID | None = None,
    ) -> list[LedgerEntry]:
        existing_key = f"{idempotency_prefix}:0"
        result = await db.execute(select(LedgerEntry).where(LedgerEntry.idempotency_key == existing_key))
        existing = result.scalar_one_or_none()
        if existing:
            txn_id = existing.transaction_id
            result = await db.execute(select(LedgerEntry).where(LedgerEntry.transaction_id == txn_id))
            return list(result.scalars().all())

        transaction_id = uuid.uuid4()
        created: list[LedgerEntry] = []
        total = 0
        for idx, (account_id, amount_minor, entry_type, description) in enumerate(entries):
            total += amount_minor
            entry = LedgerEntry(
                transaction_id=transaction_id,
                account_id=account_id,
                amount_minor=amount_minor,
                entry_type=entry_type,
                description=description,
                reference_type=reference_type,
                reference_id=reference_id,
                idempotency_key=f"{idempotency_prefix}:{idx}",
            )
            db.add(entry)
            created.append(entry)
        if total != 0:
            raise AppError("unbalanced_transaction", "Ledger entries must balance to zero", status_code=500)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            result = await db.execute(select(LedgerEntry).where(LedgerEntry.idempotency_key == existing_key))
            existing = result.scalar_one_or_none()
            if existing:
                result = await db.execute(
                    select(LedgerEntry).where(LedgerEntry.transaction_id == existing.transaction_id)
                )
                return list(result.scalars().all())
            raise
        return created


billing_service = BillingService()
