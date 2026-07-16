"""Office routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, client_ip, require_scopes
from app.application.office_service import office_service
from app.core.database import get_db
from app.domain.auth.scopes import Scope
from app.schemas.office import (
    OfficeProjectListResponse,
    OfficeProjectResponse,
    ReleaseCreate,
    ReleaseResponse,
    ReleaseUpdate,
    ScoringReportResponse,
    DistributionJobResponse,
    SubmitReleaseResponse,
    TrackCreate,
    TrackResponse,
    TrackUpdate,
)

router = APIRouter(prefix="/office", tags=["office"])

OfficeRead = Annotated[CurrentUser, Depends(require_scopes(Scope.OFFICE_READ))]
OfficeWrite = Annotated[CurrentUser, Depends(require_scopes(Scope.OFFICE_WRITE))]


def _office_response(project) -> OfficeProjectResponse:
    return OfficeProjectResponse(
        id=project.id,
        studio_project_id=project.studio_project_id,
        title=project.title,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        tracks=[TrackResponse.model_validate(t) for t in project.tracks],
        releases=[ReleaseResponse.model_validate(r) for r in project.releases],
    )


@router.get("/projects", response_model=OfficeProjectListResponse)
async def list_office_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: OfficeRead,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = await office_service.list_projects(
        db, user_id=current.user_id, page=page, page_size=page_size
    )
    return OfficeProjectListResponse(
        items=[_office_response(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/projects/{project_id}", response_model=OfficeProjectResponse)
async def get_office_project(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: OfficeRead,
):
    project = await office_service.get_project(db, user_id=current.user_id, project_id=project_id)
    return _office_response(project)


@router.post("/projects/{project_id}/releases", response_model=ReleaseResponse, status_code=201)
async def create_release(
    project_id: uuid.UUID,
    body: ReleaseCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: OfficeWrite,
):
    release = await office_service.create_release(
        db,
        user_id=current.user_id,
        office_project_id=project_id,
        title=body.title,
        release_type=body.release_type,
        contributors=body.contributors,
        explicit=body.explicit,
        release_date=body.release_date,
        cover_asset_id=body.cover_asset_id,
        upc=body.upc,
        is_test_code=body.is_test_code,
        ip_address=client_ip(request),
    )
    await db.commit()
    return release


@router.patch("/releases/{release_id}", response_model=ReleaseResponse)
async def update_release(
    release_id: uuid.UUID,
    body: ReleaseUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: OfficeWrite,
):
    release = await office_service.update_release(
        db,
        user_id=current.user_id,
        release_id=release_id,
        title=body.title,
        release_type=body.release_type,
        contributors=body.contributors,
        explicit=body.explicit,
        release_date=body.release_date,
        cover_asset_id=body.cover_asset_id,
        upc=body.upc,
        is_test_code=body.is_test_code,
        ip_address=client_ip(request),
    )
    await db.commit()
    await db.refresh(release)
    return release


@router.post("/releases/{release_id}/tracks", response_model=TrackResponse, status_code=201)
async def add_track(
    release_id: uuid.UUID,
    body: TrackCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: OfficeWrite,
):
    track = await office_service.add_track(
        db,
        user_id=current.user_id,
        release_id=release_id,
        title=body.title,
        media_asset_id=body.media_asset_id,
        isrc=body.isrc,
        is_test_code=body.is_test_code,
        ip_address=client_ip(request),
    )
    await db.commit()
    return track


@router.patch("/tracks/{track_id}", response_model=TrackResponse)
async def update_track(
    track_id: uuid.UUID,
    body: TrackUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: OfficeWrite,
):
    track = await office_service.update_track(
        db,
        user_id=current.user_id,
        track_id=track_id,
        title=body.title,
        media_asset_id=body.media_asset_id,
        isrc=body.isrc,
        is_test_code=body.is_test_code,
        ip_address=client_ip(request),
    )
    await db.commit()
    await db.refresh(track)
    return track


@router.post("/projects/{project_id}/ready", response_model=OfficeProjectResponse)
async def advance_project_ready(
    project_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: OfficeWrite,
):
    project = await office_service.advance_to_ready(
        db,
        user_id=current.user_id,
        office_project_id=project_id,
        ip_address=client_ip(request),
    )
    await db.commit()
    project = await office_service.get_project(db, user_id=current.user_id, project_id=project_id)
    return _office_response(project)


@router.get("/releases/{release_id}/scoring-report", response_model=list[ScoringReportResponse])
async def get_scoring_report(
    release_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: OfficeRead,
):
    reports = await office_service.get_scoring_report(
        db, user_id=current.user_id, release_id=release_id
    )
    return [ScoringReportResponse.model_validate(r) for r in reports]


@router.get("/releases/{release_id}/distribution-jobs", response_model=list[DistributionJobResponse])
async def list_distribution_jobs(
    release_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: OfficeRead,
):
    jobs = await office_service.list_distribution_jobs(
        db, user_id=current.user_id, release_id=release_id
    )
    return [DistributionJobResponse.model_validate(j) for j in jobs]


@router.post("/releases/{release_id}/submit", response_model=SubmitReleaseResponse, status_code=202)
async def submit_release(
    release_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: OfficeWrite,
):
    release, scoring_task_id = await office_service.submit_release(
        db,
        user_id=current.user_id,
        release_id=release_id,
        ip_address=client_ip(request),
    )
    return SubmitReleaseResponse(
        release_id=release.id,
        status=release.status,
        scoring_task_id=scoring_task_id,
    )
