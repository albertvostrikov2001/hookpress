"""Seed script for local development."""

import asyncio
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.application.chart_service import chart_service
from app.application.chat_service import chat_service
from app.application.office_service import office_service
from app.core.database import SessionLocal
from app.domain.auth.roles import Role
from app.infrastructure.models import User, UserRole
from app.infrastructure.models.chat_message import ChatMessage
from app.infrastructure.models.chat_room import ChatRoom
from app.infrastructure.models.feed_article import FeedArticle
from app.infrastructure.models.feed_category import FeedCategory
from app.infrastructure.models.feed_tag import FeedArticleTag, FeedTag
from app.infrastructure.models.kwork import Kwork
from app.infrastructure.models.kwork_profile import KworkProfile
from app.infrastructure.models.studio_project import StudioProject

SEED_OFFICE_IDEMPOTENCY = "seed-demo-office-v1"
DEMO_CHAT_ROOM_NAME = "Общий чат hook.press"
DEMO_STUDIO_TITLE = "Midnight Echo (demo)"


async def seed() -> None:
    async with SessionLocal() as session:
        # Users
        result = await session.execute(select(User).where(User.email == "artist@example.com"))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                id=uuid.uuid4(),
                email="artist@example.com",
                display_name="Demo Artist",
            )
            session.add(user)
            await session.flush()
            session.add(UserRole(user_id=user.id, role=Role.ARTIST))
            session.add(UserRole(user_id=user.id, role=Role.PERFORMER))

        admin_result = await session.execute(select(User).where(User.email == "admin@example.com"))
        admin = admin_result.scalar_one_or_none()
        if admin is None:
            admin = User(
                id=uuid.uuid4(),
                email="admin@example.com",
                display_name="Demo Admin",
            )
            session.add(admin)
            await session.flush()
            session.add(UserRole(user_id=admin.id, role=Role.ADMIN))

        mod_result = await session.execute(select(User).where(User.email == "moderator@example.com"))
        moderator = mod_result.scalar_one_or_none()
        if moderator is None:
            moderator = User(
                id=uuid.uuid4(),
                email="moderator@example.com",
                display_name="Demo Moderator",
            )
            session.add(moderator)
            await session.flush()
            session.add(UserRole(user_id=moderator.id, role=Role.MODERATOR))

        now = datetime.now(UTC)

        # Feed
        if user:
            cat_result = await session.execute(select(FeedCategory).where(FeedCategory.slug == "news"))
            cat = cat_result.scalar_one_or_none()
            if cat is None:
                cat = FeedCategory(id=uuid.uuid4(), name="Новости", slug="news")
                session.add(cat)
                await session.flush()

            tag_specs = [
                ("platform", "Платформа"),
                ("guides", "Гайды"),
                ("market", "Маркет"),
                ("security", "Безопасность"),
            ]
            tags_by_slug: dict[str, FeedTag] = {}
            for slug, name in tag_specs:
                tag_result = await session.execute(select(FeedTag).where(FeedTag.slug == slug))
                tag = tag_result.scalar_one_or_none()
                if tag is None:
                    tag = FeedTag(id=uuid.uuid4(), slug=slug, name=name)
                    session.add(tag)
                    await session.flush()
                tags_by_slug[slug] = tag

            articles = [
                {
                    "title": "Добро пожаловать в hook.press",
                    "slug": "welcome-hookpress",
                    "summary": "Платформа для артистов и продюсеров",
                    "body": "Полный текст статьи MVP seed. Создавайте треки в Студии, оформляйте релизы в Офисе и находите исполнителей на Маркете.",
                    "tags": ["platform"],
                },
                {
                    "title": "Как выпустить релиз через Офис",
                    "slug": "office-release-guide",
                    "summary": "Пошаговый гайд по конструктору релиза",
                    "body": "Отправьте проект из студии, заполните метаданные, добавьте треки и отправьте на дистрибуцию.",
                    "tags": ["guides", "platform"],
                },
                {
                    "title": "Маркетплейс услуг для музыкантов",
                    "slug": "marketplace-overview",
                    "summary": "Заказывайте сведение, дизайн и продакшн",
                    "body": "Kwork-категории: design, production, sound_engineering, songwriting. Оплата через эскроу.",
                    "tags": ["market"],
                },
                {
                    "title": "Безопасная загрузка медиа",
                    "slug": "media-upload-security",
                    "summary": "AV-сканирование и карантин файлов",
                    "body": "Все загруженные файлы проходят сканирование перед использованием в релизах и заказах.",
                    "tags": ["security"],
                },
            ]
            for article in articles:
                existing = await session.execute(
                    select(FeedArticle).where(FeedArticle.slug == article["slug"])
                )
                row = existing.scalar_one_or_none()
                if row is None:
                    row = FeedArticle(
                        id=uuid.uuid4(),
                        author_id=user.id,
                        category_id=cat.id,
                        title=article["title"],
                        slug=article["slug"],
                        summary=article["summary"],
                        body=article["body"],
                        status="PUBLISHED",
                        moderation_status="APPROVED",
                        published_at=now,
                        view_count=12,
                    )
                    session.add(row)
                    await session.flush()
                elif row.published_at is None:
                    row.published_at = now

                for tag_slug in article["tags"]:
                    tag = tags_by_slug[tag_slug]
                    link = await session.execute(
                        select(FeedArticleTag).where(
                            FeedArticleTag.article_id == row.id,
                            FeedArticleTag.tag_id == tag.id,
                        )
                    )
                    if link.scalar_one_or_none() is None:
                        session.add(FeedArticleTag(article_id=row.id, tag_id=tag.id))

        # Market
        if user:
            profile_result = await session.execute(
                select(KworkProfile).where(KworkProfile.user_id == user.id)
            )
            profile = profile_result.scalar_one_or_none()
            if profile is None:
                profile = KworkProfile(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    title="Звукорежиссура и продакшн",
                    bio="Demo performer profile",
                )
                session.add(profile)
                await session.flush()

            kworks = [
                {
                    "title": "Сведение трека (demo)",
                    "description": "Demo kwork for marketplace",
                    "category": "sound_engineering",
                    "price_minor": 150_000,
                },
                {
                    "title": "Обложка релиза (demo)",
                    "description": "Дизайн обложки для сингла или EP",
                    "category": "design",
                    "price_minor": 80_000,
                },
            ]
            for kw in kworks:
                existing = await session.execute(select(Kwork).where(Kwork.title == kw["title"]))
                if existing.scalar_one_or_none() is None:
                    session.add(
                        Kwork(
                            id=uuid.uuid4(),
                            profile_id=profile.id,
                            title=kw["title"],
                            description=kw["description"],
                            category=kw["category"],
                            price_minor=kw["price_minor"],
                            status="PUBLISHED",
                        )
                    )

        # Studio → Office demo project
        if user:
            studio_result = await session.execute(
                select(StudioProject).where(
                    StudioProject.user_id == user.id,
                    StudioProject.title == DEMO_STUDIO_TITLE,
                )
            )
            studio = studio_result.scalar_one_or_none()
            if studio is None:
                studio = StudioProject(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    title=DEMO_STUDIO_TITLE,
                    description="Демо-трек для конструктора релиза",
                    genre="electronic",
                    mood="night",
                )
                session.add(studio)
                await session.flush()

            await office_service.send_to_office(
                session,
                user_id=user.id,
                studio_project_id=studio.id,
                idempotency_key=SEED_OFFICE_IDEMPOTENCY,
                ip_address="127.0.0.1",
            )

        # Chat demo room
        if user and admin:
            room_result = await session.execute(
                select(ChatRoom).where(ChatRoom.name == DEMO_CHAT_ROOM_NAME)
            )
            room = room_result.scalar_one_or_none()
            if room is None:
                room = await chat_service.create_room(
                    session,
                    name=DEMO_CHAT_ROOM_NAME,
                    member_ids=[user.id, admin.id],
                    room_type="GROUP",
                )
            msg_result = await session.execute(
                select(ChatMessage).where(ChatMessage.room_id == room.id).limit(1)
            )
            if msg_result.scalar_one_or_none() is None:
                session.add(
                    ChatMessage(
                        room_id=room.id,
                        sender_id=admin.id,
                        client_message_id=f"seed-welcome-{room.id}",
                        body="Добро пожаловать в hook.press! Это демо-чат для тестирования.",
                    )
                )
                session.add(
                    ChatMessage(
                        room_id=room.id,
                        sender_id=user.id,
                        client_message_id=f"seed-reply-{room.id}",
                        body="Отлично, вижу сообщения и комнаты 👋",
                    )
                )

        # Charts (demo-top-40)
        await chart_service.seed_previous_week(session)
        await chart_service.run_mock_pipeline(session)

        await session.commit()
        print("Seed complete: users, feed, kworks, office project, chat room, demo chart")


if __name__ == "__main__":
    asyncio.run(seed())
