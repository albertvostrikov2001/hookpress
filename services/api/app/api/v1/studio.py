"""Studio routes."""



import json

import uuid

from typing import Annotated



from fastapi import APIRouter, Depends, Header, Query, Request

from fastapi.responses import StreamingResponse

from sqlalchemy.ext.asyncio import AsyncSession



from app.api.deps import CurrentUser, client_ip, require_scopes
from app.domain.auth.scopes import Scope

from app.application.office_service import office_service

from app.application.studio_service import studio_service

from app.core.database import get_db

from app.core.errors import AppError

from app.infrastructure.tasks.events import task_event_bus

from app.schemas.pagination import PaginatedResponse

from app.schemas.studio import (

    AiTaskResponse,

    AnalyzeTextRequest,

    AssistantMessageRequest,

    AssistantMessageResponse,

    CreateLyricVersionRequest,

    CreateStudioProjectRequest,

    GenerateAudioRequest,

    GenerateLyricsRequest,

    GenerateWaveformRequest,

    LyricVersionResponse,

    PatchLyricFragmentRequest,

    PatchLyricVersionRequest,

    PresignedAudioResponse,

    RhymeAnalysisResponse,

    SendToOfficeResponse,

    StudioProjectResponse,

    SyllableAnalysisResponse,

)



router = APIRouter(prefix="/studio", tags=["studio"])

StudioRead = Annotated[CurrentUser, Depends(require_scopes(Scope.STUDIO_READ))]
StudioWrite = Annotated[CurrentUser, Depends(require_scopes(Scope.STUDIO_WRITE))]





def _project_response(project) -> StudioProjectResponse:

    return StudioProjectResponse(

        id=project.id,

        title=project.title,

        description=project.description,

        theme=project.theme,

        mood=project.mood,

        genre=project.genre,

        structure_json=project.structure_json,

        status=project.status,

        created_at=project.created_at,

        updated_at=project.updated_at,

        lyric_versions=[LyricVersionResponse.model_validate(v) for v in project.lyric_versions],

        ai_tasks=[AiTaskResponse.model_validate(t) for t in project.ai_tasks],

    )





@router.post("/projects", response_model=StudioProjectResponse, status_code=201)

async def create_project(

    body: CreateStudioProjectRequest,

    request: Request,

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioWrite,

):

    project = await studio_service.create_project(

        db,

        user_id=current.user_id,

        title=body.title,

        description=body.description,

        theme=body.theme,

        mood=body.mood,

        genre=body.genre,

        structure_json=body.structure_json,

        ip_address=client_ip(request),

    )

    return _project_response(project)





@router.get("/projects", response_model=PaginatedResponse[StudioProjectResponse])

async def list_projects(

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioRead,

    page: int = Query(1, ge=1),

    page_size: int = Query(20, ge=1, le=100),

):

    items, total = await studio_service.list_projects(

        db, user_id=current.user_id, page=page, page_size=page_size

    )

    offset = (page - 1) * page_size

    return PaginatedResponse(

        items=[_project_response(p) for p in items],

        total=total,

        page=page,

        page_size=page_size,

        has_more=(offset + len(items)) < total,

    )





@router.get("/projects/{project_id}", response_model=StudioProjectResponse)

async def get_project(

    project_id: uuid.UUID,

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioRead,

):

    project = await studio_service.get_project(db, user_id=current.user_id, project_id=project_id)

    return _project_response(project)





@router.get("/projects/{project_id}/lyrics/versions", response_model=list[LyricVersionResponse])

async def list_lyric_versions(

    project_id: uuid.UUID,

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioRead,

):

    versions = await studio_service.list_lyric_versions(

        db, user_id=current.user_id, project_id=project_id

    )

    return [LyricVersionResponse.model_validate(v) for v in versions]





@router.post("/projects/{project_id}/lyrics/versions", response_model=LyricVersionResponse, status_code=201)

async def create_lyric_version(

    project_id: uuid.UUID,

    body: CreateLyricVersionRequest,

    request: Request,

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioWrite,

):

    version = await studio_service.create_lyric_version(

        db,

        user_id=current.user_id,

        project_id=project_id,

        content=body.content,

        prompt=body.prompt,

        ip_address=client_ip(request),

    )

    return LyricVersionResponse.model_validate(version)





@router.patch("/projects/{project_id}/lyrics/versions/{version_id}", response_model=LyricVersionResponse)

async def patch_lyric_version(

    project_id: uuid.UUID,

    version_id: uuid.UUID,

    body: PatchLyricVersionRequest,

    request: Request,

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioWrite,

):

    version = await studio_service.patch_lyric_version(

        db,

        user_id=current.user_id,

        project_id=project_id,

        version_id=version_id,

        content=body.content,

        prompt=body.prompt,

        ip_address=client_ip(request),

    )

    return LyricVersionResponse.model_validate(version)





@router.post(

    "/projects/{project_id}/lyrics/versions/{version_id}/patch",

    response_model=LyricVersionResponse,

)

async def patch_lyric_fragment(

    project_id: uuid.UUID,

    version_id: uuid.UUID,

    body: PatchLyricFragmentRequest,

    request: Request,

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioWrite,

):

    version = await studio_service.patch_lyric_fragment(

        db,

        user_id=current.user_id,

        project_id=project_id,

        version_id=version_id,

        start_line=body.start_line,

        end_line=body.end_line,

        replacement=body.replacement,

        ip_address=client_ip(request),

    )

    return LyricVersionResponse.model_validate(version)





@router.post("/projects/{project_id}/lyrics/analyze-syllables", response_model=SyllableAnalysisResponse)

async def analyze_syllables(

    project_id: uuid.UUID,

    body: AnalyzeTextRequest,

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioWrite,

):

    result = await studio_service.analyze_syllables_for_project(

        db,

        user_id=current.user_id,

        project_id=project_id,

        text=body.text,

        lyric_version_id=body.lyric_version_id,

    )

    return SyllableAnalysisResponse.model_validate(result)





@router.post("/projects/{project_id}/lyrics/analyze-rhymes", response_model=RhymeAnalysisResponse)

async def analyze_rhymes(

    project_id: uuid.UUID,

    body: AnalyzeTextRequest,

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioWrite,

):

    result = await studio_service.analyze_rhymes_for_project(

        db,

        user_id=current.user_id,

        project_id=project_id,

        text=body.text,

        lyric_version_id=body.lyric_version_id,

    )

    return RhymeAnalysisResponse.model_validate(result)





@router.post("/projects/{project_id}/assistant/messages", response_model=AssistantMessageResponse)

async def assistant_message(

    project_id: uuid.UUID,

    body: AssistantMessageRequest,

    request: Request,

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioWrite,

):

    user_msg, assistant_msg = await studio_service.send_assistant_message(

        db,

        user_id=current.user_id,

        project_id=project_id,

        content=body.content,

        ip_address=client_ip(request),

    )

    return AssistantMessageResponse(

        user_message=user_msg.content,

        assistant_message=assistant_msg.content,

        message_id=assistant_msg.id,

    )





@router.post("/projects/{project_id}/generate-lyrics", response_model=AiTaskResponse, status_code=202)

async def generate_lyrics(

    project_id: uuid.UUID,

    body: GenerateLyricsRequest,

    request: Request,

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioWrite,

):

    task = await studio_service.start_generate_lyrics(

        db,

        user_id=current.user_id,

        project_id=project_id,

        prompt=body.prompt,

        ip_address=client_ip(request),

    )

    return AiTaskResponse.model_validate(task)





@router.post("/projects/{project_id}/generate-audio", response_model=AiTaskResponse, status_code=202)

async def generate_audio(

    project_id: uuid.UUID,

    body: GenerateAudioRequest,

    request: Request,

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioWrite,

):

    task = await studio_service.start_generate_audio(

        db,

        user_id=current.user_id,

        project_id=project_id,

        lyric_version_id=body.lyric_version_id,

        ip_address=client_ip(request),

    )

    return AiTaskResponse.model_validate(task)





@router.post("/projects/{project_id}/generate-waveform", response_model=AiTaskResponse, status_code=202)

async def generate_waveform(

    project_id: uuid.UUID,

    body: GenerateWaveformRequest,

    request: Request,

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioWrite,

):

    task = await studio_service.start_generate_waveform(

        db,

        user_id=current.user_id,

        project_id=project_id,

        audio_task_id=body.audio_task_id,

        ip_address=client_ip(request),

    )

    return AiTaskResponse.model_validate(task)





@router.get("/projects/{project_id}/tasks/{task_id}", response_model=AiTaskResponse)

async def get_task(

    project_id: uuid.UUID,

    task_id: uuid.UUID,

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioRead,

):

    task = await studio_service.get_task(

        db, user_id=current.user_id, project_id=project_id, task_id=task_id

    )

    return AiTaskResponse.model_validate(task)





@router.get("/projects/{project_id}/tasks/{task_id}/events")

async def task_events(

    project_id: uuid.UUID,

    task_id: uuid.UUID,

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioRead,

):

    task = await studio_service.get_task(

        db, user_id=current.user_id, project_id=project_id, task_id=task_id

    )



    async def event_stream():

        yield f"data: {json.dumps({'event': 'connected', 'task_id': str(task.id), 'status': task.status})}\n\n"

        if task.status in {"SUCCEEDED", "FAILED", "CANCELLED"}:

            yield f"data: {json.dumps({'event': 'status', 'status': task.status, 'result': task.result_payload, 'result_metadata': task.result_metadata})}\n\n"

            return

        async for message in task_event_bus.subscribe(str(task.id)):

            yield f"data: {message}\n\n"

            try:

                payload = json.loads(message)

            except json.JSONDecodeError:

                continue

            if payload.get("status") in {"SUCCEEDED", "FAILED", "CANCELLED"}:

                break



    return StreamingResponse(event_stream(), media_type="text/event-stream")





@router.get("/projects/{project_id}/audio/presigned-url", response_model=PresignedAudioResponse)

async def get_audio_presigned_url(

    project_id: uuid.UUID,

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioRead,

):

    url, expires_in, asset_id = await studio_service.get_audio_presigned_url(

        db, user_id=current.user_id, project_id=project_id

    )

    return PresignedAudioResponse(url=url, expires_in=expires_in, media_asset_id=asset_id)





@router.post("/projects/{project_id}/send-to-office", response_model=SendToOfficeResponse, status_code=202)

async def send_to_office(

    project_id: uuid.UUID,

    request: Request,

    db: Annotated[AsyncSession, Depends(get_db)],

    current: StudioWrite,

    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,

):

    if not idempotency_key:

        raise AppError("idempotency_required", "Idempotency-Key header required", status_code=400)



    office, idempotent = await office_service.send_to_office(

        db,

        user_id=current.user_id,

        studio_project_id=project_id,

        idempotency_key=idempotency_key,

        ip_address=client_ip(request),

    )

    return SendToOfficeResponse(

        office_project_id=office.id,

        studio_project_id=office.studio_project_id,

        status=office.status,

        idempotent=idempotent,

    )

