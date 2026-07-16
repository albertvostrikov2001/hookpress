"""Office and release use cases."""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.audit import write_audit
from app.application.media_service import media_service
from app.core.errors import AppError
from app.domain.office.enums import OfficeProjectStatus, ReleaseStatus, ReleaseType
from app.domain.office.state_machines import office_project_state_machine, release_state_machine
from app.infrastructure.models.distribution_job import DistributionJob
from app.infrastructure.models.office_project import OfficeProject
from app.infrastructure.models.release import Release
from app.infrastructure.models.scoring_report import ScoringReport
from app.infrastructure.models.studio_project import StudioProject
from app.infrastructure.models.track import Track
from app.infrastructure.providers.distribution import MockDistributionProvider
from app.infrastructure.tasks.celery_client import celery_app


class OfficeService:
    def __init__(self) -> None:
        self._distribution = MockDistributionProvider()

    async def send_to_office(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        studio_project_id: uuid.UUID,
        idempotency_key: str,
        ip_address: str | None,
    ) -> tuple[OfficeProject, bool]:
        if not idempotency_key:
            raise AppError("idempotency_required", "Idempotency-Key header required", status_code=400)

        existing = await db.execute(
            select(OfficeProject).where(
                OfficeProject.user_id == user_id,
                OfficeProject.idempotency_key == idempotency_key,
            )
        )
        office = existing.scalar_one_or_none()
        if office:
            return office, True

        result = await db.execute(
            select(StudioProject)
            .options(selectinload(StudioProject.lyric_versions), selectinload(StudioProject.office_project))
            .where(StudioProject.id == studio_project_id, StudioProject.user_id == user_id)
        )
        studio = result.scalar_one_or_none()
        if studio is None:
            raise AppError("studio_project_not_found", "Studio project not found", status_code=404)
        if studio.office_project is not None:
            return studio.office_project, True

        office = OfficeProject(
            user_id=user_id,
            studio_project_id=studio.id,
            title=studio.title,
            status=OfficeProjectStatus.DRAFT_IN_OFFICE,
            idempotency_key=idempotency_key,
        )
        db.add(office)
        await db.flush()

        lyric = None
        if studio.lyric_versions:
            lyric = max(studio.lyric_versions, key=lambda v: v.version_number)

        track = Track(
            office_project_id=office.id,
            title=studio.title,
            position=1,
            lyric_version_id=lyric.id if lyric else None,
        )
        db.add(track)
        await db.flush()

        release = Release(
            office_project_id=office.id,
            user_id=user_id,
            title=studio.title,
            status=ReleaseStatus.DRAFT,
        )
        db.add(release)
        await db.flush()

        await write_audit(
            db,
            action="studio.send_to_office",
            resource_type="office_project",
            resource_id=str(office.id),
            actor_user_id=user_id,
            ip_address=ip_address,
            metadata={"studio_project_id": str(studio.id), "idempotency_key": idempotency_key},
        )
        await db.commit()

        result = await db.execute(
            select(OfficeProject)
            .options(
                selectinload(OfficeProject.tracks),
                selectinload(OfficeProject.releases),
            )
            .where(OfficeProject.id == office.id)
        )
        return result.scalar_one(), False

    async def list_projects(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[OfficeProject], int]:
        offset = (page - 1) * page_size
        count_result = await db.execute(
            select(func.count()).select_from(OfficeProject).where(OfficeProject.user_id == user_id)
        )
        total = count_result.scalar_one()
        result = await db.execute(
            select(OfficeProject)
            .options(
                selectinload(OfficeProject.tracks),
                selectinload(OfficeProject.releases),
            )
            .where(OfficeProject.user_id == user_id)
            .order_by(OfficeProject.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_project(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> OfficeProject:
        result = await db.execute(
            select(OfficeProject)
            .options(
                selectinload(OfficeProject.tracks),
                selectinload(OfficeProject.releases),
            )
            .where(OfficeProject.id == project_id, OfficeProject.user_id == user_id)
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise AppError("office_project_not_found", "Office project not found", status_code=404)
        return project

    async def get_release(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        release_id: uuid.UUID,
    ) -> Release:
        result = await db.execute(
            select(Release)
            .options(
                selectinload(Release.office_project).selectinload(OfficeProject.tracks),
                selectinload(Release.scoring_reports),
                selectinload(Release.distribution_jobs),
            )
            .where(Release.id == release_id, Release.user_id == user_id)
        )
        release = result.scalar_one_or_none()
        if release is None:
            raise AppError("release_not_found", "Release not found", status_code=404)
        return release

    async def create_release(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        office_project_id: uuid.UUID,
        title: str,
        release_type: str = ReleaseType.SINGLE,
        contributors: list | None = None,
        explicit: bool = False,
        release_date: date | None = None,
        cover_asset_id: uuid.UUID | None = None,
        upc: str | None = None,
        is_test_code: bool = False,
        ip_address: str | None = None,
    ) -> Release:
        project = await self.get_project(db, user_id=user_id, project_id=office_project_id)
        if release_type not in {t.value for t in ReleaseType}:
            raise AppError("invalid_release_type", "Invalid release type", status_code=400)
        if cover_asset_id:
            await media_service.get_asset(db, user_id=user_id, asset_id=cover_asset_id, require_ready=True)

        release = Release(
            office_project_id=project.id,
            user_id=user_id,
            title=title,
            status=ReleaseStatus.DRAFT,
            release_type=release_type,
            contributors=contributors,
            explicit=explicit,
            release_date=release_date,
            cover_asset_id=cover_asset_id,
            upc=upc,
            is_test_code=is_test_code,
        )
        db.add(release)
        await write_audit(
            db,
            action="office.release.create",
            resource_type="release",
            resource_id=str(release.id),
            actor_user_id=user_id,
            ip_address=ip_address,
        )
        await db.flush()
        return release

    async def update_release(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        release_id: uuid.UUID,
        title: str | None = None,
        release_type: str | None = None,
        contributors: list | None = None,
        explicit: bool | None = None,
        release_date: date | None = None,
        cover_asset_id: uuid.UUID | None = None,
        upc: str | None = None,
        is_test_code: bool | None = None,
        ip_address: str | None = None,
    ) -> Release:
        release = await self.get_release(db, user_id=user_id, release_id=release_id)
        if release.status != ReleaseStatus.DRAFT:
            raise AppError("release_not_editable", "Only draft releases can be edited", status_code=409)

        if title is not None:
            release.title = title
        if release_type is not None:
            if release_type not in {t.value for t in ReleaseType}:
                raise AppError("invalid_release_type", "Invalid release type", status_code=400)
            release.release_type = release_type
        if contributors is not None:
            release.contributors = contributors
        if explicit is not None:
            release.explicit = explicit
        if release_date is not None:
            release.release_date = release_date
        if cover_asset_id is not None:
            if cover_asset_id:
                await media_service.get_asset(db, user_id=user_id, asset_id=cover_asset_id, require_ready=True)
            release.cover_asset_id = cover_asset_id
        if upc is not None:
            release.upc = upc
        if is_test_code is not None:
            release.is_test_code = is_test_code

        await write_audit(
            db,
            action="office.release.update",
            resource_type="release",
            resource_id=str(release.id),
            actor_user_id=user_id,
            ip_address=ip_address,
        )
        await db.flush()
        return release

    async def add_track(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        release_id: uuid.UUID,
        title: str,
        media_asset_id: uuid.UUID | None = None,
        isrc: str | None = None,
        is_test_code: bool = False,
        ip_address: str | None = None,
    ) -> Track:
        release = await self.get_release(db, user_id=user_id, release_id=release_id)
        if release.status != ReleaseStatus.DRAFT:
            raise AppError("release_not_editable", "Only draft releases can be edited", status_code=409)

        if media_asset_id:
            await media_service.get_asset(db, user_id=user_id, asset_id=media_asset_id, require_ready=True)

        position = len(release.office_project.tracks) + 1
        track = Track(
            office_project_id=release.office_project_id,
            title=title,
            position=position,
            media_asset_id=media_asset_id,
            isrc=isrc,
            is_test_code=is_test_code,
        )
        db.add(track)
        await write_audit(
            db,
            action="office.track.add",
            resource_type="track",
            resource_id=str(track.id),
            actor_user_id=user_id,
            ip_address=ip_address,
            metadata={"release_id": str(release_id)},
        )
        await db.flush()
        return track

    async def update_track(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        track_id: uuid.UUID,
        title: str | None = None,
        media_asset_id: uuid.UUID | None = None,
        isrc: str | None = None,
        is_test_code: bool | None = None,
        ip_address: str | None = None,
    ) -> Track:
        result = await db.execute(
            select(Track)
            .join(OfficeProject, Track.office_project_id == OfficeProject.id)
            .where(Track.id == track_id, OfficeProject.user_id == user_id)
        )
        track = result.scalar_one_or_none()
        if track is None:
            raise AppError("track_not_found", "Track not found", status_code=404)
        release_result = await db.execute(
            select(Release).where(Release.office_project_id == track.office_project_id)
        )
        release = release_result.scalars().first()
        if release is None or release.status != ReleaseStatus.DRAFT:
            raise AppError("release_not_editable", "Only draft releases can be edited", status_code=409)
        if title is not None:
            track.title = title
        if media_asset_id is not None:
            await media_service.get_asset(db, user_id=user_id, asset_id=media_asset_id, require_ready=True)
            track.media_asset_id = media_asset_id
        if isrc is not None:
            track.isrc = isrc
        if is_test_code is not None:
            track.is_test_code = is_test_code
        await write_audit(
            db,
            action="office.track.update",
            resource_type="track",
            resource_id=str(track.id),
            actor_user_id=user_id,
            ip_address=ip_address,
        )
        await db.flush()
        return track

    async def advance_to_ready(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        office_project_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> OfficeProject:
        project = await self.get_project(db, user_id=user_id, project_id=office_project_id)
        if not project.releases:
            raise AppError("no_release", "Project has no release", status_code=400)

        release = project.releases[0]
        if not project.tracks:
            raise AppError("no_tracks", "Release must have at least one track", status_code=400)
        for track in project.tracks:
            if track.media_asset_id is None:
                raise AppError("track_missing_media", f"Track '{track.title}' has no media asset", status_code=400)

        if project.status == OfficeProjectStatus.DRAFT_IN_OFFICE:
            office_project_state_machine.assert_transition(
                project.status, OfficeProjectStatus.READY_FOR_RELEASE
            )
            project.status = OfficeProjectStatus.READY_FOR_RELEASE
            await write_audit(
                db,
                action="office.project.ready",
                resource_type="office_project",
                resource_id=str(project.id),
                actor_user_id=user_id,
                ip_address=ip_address,
                metadata={"release_id": str(release.id)},
            )
            await db.flush()
        return project

    async def get_scoring_report(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        release_id: uuid.UUID,
    ) -> list[ScoringReport]:
        release = await self.get_release(db, user_id=user_id, release_id=release_id)
        return list(release.scoring_reports)

    async def list_distribution_jobs(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        release_id: uuid.UUID,
    ) -> list[DistributionJob]:
        release = await self.get_release(db, user_id=user_id, release_id=release_id)
        return sorted(release.distribution_jobs, key=lambda j: j.created_at, reverse=True)

    async def submit_release(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        release_id: uuid.UUID,
        ip_address: str | None,
    ) -> tuple[Release, str | None]:
        release = await self.get_release(db, user_id=user_id, release_id=release_id)
        if release.office_project.status != OfficeProjectStatus.READY_FOR_RELEASE:
            raise AppError(
                "office_not_ready",
                "Office project must be READY_FOR_RELEASE before submit",
                status_code=409,
            )
        release_state_machine.assert_transition(release.status, ReleaseStatus.VALIDATING)
        release.status = ReleaseStatus.VALIDATING
        await db.flush()

        celery_result = celery_app.send_task(
            "scoring.score_release",
            args=[str(release.id)],
        )

        await write_audit(
            db,
            action="office.release.submit",
            resource_type="release",
            resource_id=str(release.id),
            actor_user_id=user_id,
            ip_address=ip_address,
            metadata={"scoring_task_id": celery_result.id},
        )
        await db.commit()
        await db.refresh(release)
        return release, celery_result.id

    async def advance_release_after_scoring(
        self,
        db: AsyncSession,
        *,
        release_id: uuid.UUID,
        passed: bool,
    ) -> Release:
        result = await db.execute(select(Release).where(Release.id == release_id))
        release = result.scalar_one_or_none()
        if release is None:
            raise AppError("release_not_found", "Release not found", status_code=404)

        if release.status == ReleaseStatus.VALIDATING:
            next_status = ReleaseStatus.MODERATION if passed else ReleaseStatus.FAILED
            release_state_machine.assert_transition(release.status, next_status)
            release.status = next_status
            await db.flush()

        if release.status == ReleaseStatus.MODERATION:
            release_state_machine.assert_transition(release.status, ReleaseStatus.DELIVERED)
            release.status = ReleaseStatus.DELIVERED
            dist_result = await self._distribution.submit_release(
                release.id,
                {"title": release.title},
            )
            job = DistributionJob(
                release_id=release.id,
                provider="mock",
                status="SUCCEEDED",
                external_id=dist_result["external_id"],
                result_payload=dist_result,
            )
            db.add(job)
            await db.flush()
            release_state_machine.assert_transition(release.status, ReleaseStatus.RELEASED)
            release.status = ReleaseStatus.RELEASED

        await db.commit()
        await db.refresh(release)
        return release

    async def process_distribution_webhook(
        self,
        db: AsyncSession,
        *,
        release_id: uuid.UUID,
        status: str,
        external_id: str | None = None,
        payload: dict | None = None,
    ) -> DistributionJob:
        result = await db.execute(
            select(Release).where(Release.id == release_id)
        )
        release = result.scalar_one_or_none()
        if release is None:
            raise AppError("release_not_found", "Release not found", status_code=404)

        job = DistributionJob(
            release_id=release.id,
            provider="mock",
            status=status,
            external_id=external_id,
            result_payload=payload,
        )
        db.add(job)
        await db.flush()

        if status == "RELEASED" and release.status == ReleaseStatus.DELIVERED:
            release_state_machine.assert_transition(release.status, ReleaseStatus.RELEASED)
            release.status = ReleaseStatus.RELEASED
        elif status == "REJECTED":
            release_state_machine.assert_transition(release.status, ReleaseStatus.REJECTED)
            release.status = ReleaseStatus.REJECTED

        await db.commit()
        await db.refresh(job)
        return job

    async def mark_office_ready(
        self,
        db: AsyncSession,
        *,
        office_project_id: uuid.UUID,
    ) -> OfficeProject:
        result = await db.execute(select(OfficeProject).where(OfficeProject.id == office_project_id))
        office = result.scalar_one_or_none()
        if office is None:
            raise AppError("office_project_not_found", "Office project not found", status_code=404)
        if office.status == OfficeProjectStatus.DRAFT_IN_OFFICE:
            office_project_state_machine.assert_transition(
                office.status, OfficeProjectStatus.READY_FOR_RELEASE
            )
            office.status = OfficeProjectStatus.READY_FOR_RELEASE
            await db.commit()
            await db.refresh(office)
        return office


office_service = OfficeService()
