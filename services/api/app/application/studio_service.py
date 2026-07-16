"""Studio use cases."""



import uuid



from sqlalchemy import func, select

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload



from app.application.audit import write_audit

from app.core.config import settings

from app.core.errors import AppError

from app.domain.studio.enums import AiTaskStatus, AiTaskType, StudioProjectStatus

from app.domain.studio.rhymes import analyze_rhymes

from app.domain.studio.syllables import analyze_syllables

from app.infrastructure.models.ai_task import AiTask

from app.infrastructure.models.lyric_version import LyricVersion

from app.infrastructure.models.media_asset import MediaAsset

from app.infrastructure.models.studio_assistant_message import StudioAssistantMessage

from app.infrastructure.models.studio_project import StudioProject

from app.infrastructure.providers.factory import get_llm_provider

from app.infrastructure.storage.s3 import s3_storage

from app.infrastructure.tasks.celery_client import celery_app





class StudioService:

    async def create_project(

        self,

        db: AsyncSession,

        *,

        user_id: uuid.UUID,

        title: str,

        description: str | None,

        theme: str | None = None,

        mood: str | None = None,

        genre: str | None = None,

        structure_json: dict | None = None,

        ip_address: str | None,

    ) -> StudioProject:

        project = StudioProject(

            user_id=user_id,

            title=title,

            description=description,

            theme=theme,

            mood=mood,

            genre=genre,

            structure_json=structure_json,

            status=StudioProjectStatus.ACTIVE,

        )

        db.add(project)

        await db.flush()

        await write_audit(

            db,

            action="studio.project.create",

            resource_type="studio_project",

            resource_id=str(project.id),

            actor_user_id=user_id,

            ip_address=ip_address,

            metadata={"title": title},

        )

        await db.commit()

        await db.refresh(project)

        return project



    async def list_projects(

        self,

        db: AsyncSession,

        *,

        user_id: uuid.UUID,

        page: int = 1,

        page_size: int = 20,

    ) -> tuple[list[StudioProject], int]:

        offset = (page - 1) * page_size

        count_result = await db.execute(

            select(func.count()).select_from(StudioProject).where(StudioProject.user_id == user_id)

        )

        total = count_result.scalar_one()

        result = await db.execute(

            select(StudioProject)

            .options(

                selectinload(StudioProject.lyric_versions),

                selectinload(StudioProject.ai_tasks),

            )

            .where(StudioProject.user_id == user_id)

            .order_by(StudioProject.created_at.desc())

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

    ) -> StudioProject:

        result = await db.execute(

            select(StudioProject)

            .options(

                selectinload(StudioProject.lyric_versions),

                selectinload(StudioProject.ai_tasks),

                selectinload(StudioProject.office_project),

            )

            .where(StudioProject.id == project_id, StudioProject.user_id == user_id)

        )

        project = result.scalar_one_or_none()

        if project is None:

            raise AppError("studio_project_not_found", "Studio project not found", status_code=404)

        return project



    async def _next_version_number(self, db: AsyncSession, project_id: uuid.UUID) -> int:

        result = await db.execute(

            select(func.coalesce(func.max(LyricVersion.version_number), 0)).where(

                LyricVersion.studio_project_id == project_id

            )

        )

        return result.scalar_one() + 1



    async def list_lyric_versions(

        self,

        db: AsyncSession,

        *,

        user_id: uuid.UUID,

        project_id: uuid.UUID,

    ) -> list[LyricVersion]:

        project = await self.get_project(db, user_id=user_id, project_id=project_id)

        return sorted(project.lyric_versions, key=lambda v: v.version_number)



    async def create_lyric_version(

        self,

        db: AsyncSession,

        *,

        user_id: uuid.UUID,

        project_id: uuid.UUID,

        content: str,

        prompt: str | None,

        ip_address: str | None,

    ) -> LyricVersion:

        await self.get_project(db, user_id=user_id, project_id=project_id)

        version = LyricVersion(

            studio_project_id=project_id,

            version_number=await self._next_version_number(db, project_id),

            content=content,

            prompt=prompt,

        )

        db.add(version)

        await write_audit(

            db,

            action="studio.lyrics.create",

            resource_type="lyric_version",

            resource_id=str(version.id),

            actor_user_id=user_id,

            ip_address=ip_address,

            metadata={"studio_project_id": str(project_id)},

        )

        await db.commit()

        await db.refresh(version)

        return version



    async def get_lyric_version(

        self,

        db: AsyncSession,

        *,

        user_id: uuid.UUID,

        project_id: uuid.UUID,

        version_id: uuid.UUID,

    ) -> LyricVersion:

        await self.get_project(db, user_id=user_id, project_id=project_id)

        result = await db.execute(

            select(LyricVersion).where(

                LyricVersion.id == version_id,

                LyricVersion.studio_project_id == project_id,

            )

        )

        version = result.scalar_one_or_none()

        if version is None:

            raise AppError("lyric_version_not_found", "Lyric version not found", status_code=404)

        return version



    async def patch_lyric_version(

        self,

        db: AsyncSession,

        *,

        user_id: uuid.UUID,

        project_id: uuid.UUID,

        version_id: uuid.UUID,

        content: str | None,

        prompt: str | None,

        ip_address: str | None,

    ) -> LyricVersion:

        version = await self.get_lyric_version(

            db, user_id=user_id, project_id=project_id, version_id=version_id

        )

        if content is not None:

            version.content = content

        if prompt is not None:

            version.prompt = prompt

        await write_audit(

            db,

            action="studio.lyrics.patch",

            resource_type="lyric_version",

            resource_id=str(version.id),

            actor_user_id=user_id,

            ip_address=ip_address,

            metadata={"studio_project_id": str(project_id)},

        )

        await db.commit()

        await db.refresh(version)

        return version



    async def patch_lyric_fragment(

        self,

        db: AsyncSession,

        *,

        user_id: uuid.UUID,

        project_id: uuid.UUID,

        version_id: uuid.UUID,

        start_line: int,

        end_line: int,

        replacement: str,

        ip_address: str | None,

    ) -> LyricVersion:

        if end_line < start_line:

            raise AppError("invalid_line_range", "end_line must be >= start_line", status_code=400)



        version = await self.get_lyric_version(

            db, user_id=user_id, project_id=project_id, version_id=version_id

        )

        lines = version.content.splitlines()

        if start_line > len(lines):

            raise AppError("invalid_line_range", "start_line exceeds line count", status_code=400)



        replacement_lines = replacement.splitlines()

        new_lines = lines[: start_line - 1] + replacement_lines + lines[end_line:]

        version.content = "\n".join(new_lines)



        await write_audit(

            db,

            action="studio.lyrics.fragment_patch",

            resource_type="lyric_version",

            resource_id=str(version.id),

            actor_user_id=user_id,

            ip_address=ip_address,

            metadata={

                "studio_project_id": str(project_id),

                "start_line": start_line,

                "end_line": end_line,

            },

        )

        await db.commit()

        await db.refresh(version)

        return version



    async def analyze_syllables_for_project(

        self,

        db: AsyncSession,

        *,

        user_id: uuid.UUID,

        project_id: uuid.UUID,

        text: str | None,

        lyric_version_id: uuid.UUID | None,

    ) -> dict:

        content = text

        if content is None and lyric_version_id:

            version = await self.get_lyric_version(

                db, user_id=user_id, project_id=project_id, version_id=lyric_version_id

            )

            content = version.content

        if not content:

            raise AppError("no_text", "Provide text or lyric_version_id", status_code=400)

        return analyze_syllables(content)



    async def analyze_rhymes_for_project(

        self,

        db: AsyncSession,

        *,

        user_id: uuid.UUID,

        project_id: uuid.UUID,

        text: str | None,

        lyric_version_id: uuid.UUID | None,

    ) -> dict:

        content = text

        if content is None and lyric_version_id:

            version = await self.get_lyric_version(

                db, user_id=user_id, project_id=project_id, version_id=lyric_version_id

            )

            content = version.content

        if not content:

            raise AppError("no_text", "Provide text or lyric_version_id", status_code=400)

        return analyze_rhymes(content)



    async def send_assistant_message(

        self,

        db: AsyncSession,

        *,

        user_id: uuid.UUID,

        project_id: uuid.UUID,

        content: str,

        ip_address: str | None,

    ) -> tuple[StudioAssistantMessage, StudioAssistantMessage]:

        project = await self.get_project(db, user_id=user_id, project_id=project_id)



        user_msg = StudioAssistantMessage(

            studio_project_id=project.id,

            role="user",

            content=content,

        )

        db.add(user_msg)

        await db.flush()



        history_result = await db.execute(

            select(StudioAssistantMessage)

            .where(StudioAssistantMessage.studio_project_id == project.id)

            .order_by(StudioAssistantMessage.created_at.asc())

            .limit(20)

        )

        history = history_result.scalars().all()

        messages = [{"role": m.role, "content": m.content} for m in history]



        context_parts = []

        if project.theme:

            context_parts.append(f"Theme: {project.theme}")

        if project.mood:

            context_parts.append(f"Mood: {project.mood}")

        if project.genre:

            context_parts.append(f"Genre: {project.genre}")

        if project.lyric_versions:

            latest = max(project.lyric_versions, key=lambda v: v.version_number)

            context_parts.append(f"Current lyrics:\n{latest.content[:2000]}")



        system_context = "\n".join(context_parts)

        llm_messages = []

        if system_context:

            llm_messages.append(

                {"role": "user", "content": f"Project context:\n{system_context}"}

            )

            llm_messages.append(

                {

                    "role": "assistant",

                    "content": "Understood. I'll help with this song project.",

                }

            )

        llm_messages.extend(messages)



        llm = get_llm_provider()

        if hasattr(llm, "chat"):

            reply = await llm.chat(llm_messages)  # type: ignore[attr-defined]

        else:

            reply = await llm.generate_lyrics(content)



        assistant_msg = StudioAssistantMessage(

            studio_project_id=project.id,

            role="assistant",

            content=reply,

        )

        db.add(assistant_msg)



        await write_audit(

            db,

            action="studio.assistant.message",

            resource_type="studio_project",

            resource_id=str(project.id),

            actor_user_id=user_id,

            ip_address=ip_address,

            metadata={"user_message_id": str(user_msg.id)},

        )

        await db.commit()

        await db.refresh(user_msg)

        await db.refresh(assistant_msg)

        return user_msg, assistant_msg



    async def start_generate_lyrics(

        self,

        db: AsyncSession,

        *,

        user_id: uuid.UUID,

        project_id: uuid.UUID,

        prompt: str,

        ip_address: str | None,

    ) -> AiTask:

        project = await self.get_project(db, user_id=user_id, project_id=project_id)

        task = AiTask(

            studio_project_id=project.id,

            task_type=AiTaskType.GENERATE_LYRICS,

            status=AiTaskStatus.PENDING,

            input_payload={"prompt": prompt},

        )

        db.add(task)

        await db.flush()



        celery_result = celery_app.send_task(

            "studio.generate_lyrics",

            args=[str(task.id)],

            kwargs={"prompt": prompt},

        )

        task.celery_task_id = celery_result.id



        await write_audit(

            db,

            action="studio.generate_lyrics",

            resource_type="ai_task",

            resource_id=str(task.id),

            actor_user_id=user_id,

            ip_address=ip_address,

            metadata={"studio_project_id": str(project.id)},

        )

        await db.commit()

        await db.refresh(task)

        return task



    async def start_generate_audio(

        self,

        db: AsyncSession,

        *,

        user_id: uuid.UUID,

        project_id: uuid.UUID,

        lyric_version_id: uuid.UUID | None,

        ip_address: str | None,

    ) -> AiTask:

        project = await self.get_project(db, user_id=user_id, project_id=project_id)

        lyrics = ""

        if lyric_version_id:

            version = next((v for v in project.lyric_versions if v.id == lyric_version_id), None)

            if version is None:

                raise AppError("lyric_version_not_found", "Lyric version not found", status_code=404)

            lyrics = version.content

        elif project.lyric_versions:

            latest = max(project.lyric_versions, key=lambda v: v.version_number)

            lyrics = latest.content

            lyric_version_id = latest.id

        else:

            raise AppError("no_lyrics", "No lyrics available for audio generation", status_code=400)



        task = AiTask(

            studio_project_id=project.id,

            task_type=AiTaskType.GENERATE_AUDIO,

            status=AiTaskStatus.PENDING,

            input_payload={"lyric_version_id": str(lyric_version_id), "lyrics": lyrics},

        )

        db.add(task)

        await db.flush()



        celery_result = celery_app.send_task(

            "studio.generate_audio",

            args=[str(task.id)],

            kwargs={"lyrics": lyrics, "lyric_version_id": str(lyric_version_id)},

        )

        task.celery_task_id = celery_result.id



        await write_audit(

            db,

            action="studio.generate_audio",

            resource_type="ai_task",

            resource_id=str(task.id),

            actor_user_id=user_id,

            ip_address=ip_address,

            metadata={"studio_project_id": str(project.id)},

        )

        await db.commit()

        await db.refresh(task)

        return task



    async def start_generate_waveform(

        self,

        db: AsyncSession,

        *,

        user_id: uuid.UUID,

        project_id: uuid.UUID,

        audio_task_id: uuid.UUID | None,

        ip_address: str | None,

    ) -> AiTask:

        project = await self.get_project(db, user_id=user_id, project_id=project_id)



        source_task: AiTask | None = None

        if audio_task_id:

            source_task = next((t for t in project.ai_tasks if t.id == audio_task_id), None)

        else:

            audio_tasks = [

                t

                for t in project.ai_tasks

                if t.task_type == AiTaskType.GENERATE_AUDIO and t.status == AiTaskStatus.SUCCEEDED

            ]

            source_task = max(audio_tasks, key=lambda t: t.created_at) if audio_tasks else None



        if source_task is None:

            raise AppError("audio_task_not_found", "No succeeded audio task found", status_code=404)



        task = AiTask(

            studio_project_id=project.id,

            task_type=AiTaskType.GENERATE_WAVEFORM,

            status=AiTaskStatus.PENDING,

            input_payload={"source_audio_task_id": str(source_task.id)},

        )

        db.add(task)

        await db.flush()



        celery_result = celery_app.send_task(

            "studio.generate_waveform",

            args=[str(task.id)],

            kwargs={"source_audio_task_id": str(source_task.id)},

        )

        task.celery_task_id = celery_result.id



        await write_audit(

            db,

            action="studio.generate_waveform",

            resource_type="ai_task",

            resource_id=str(task.id),

            actor_user_id=user_id,

            ip_address=ip_address,

            metadata={"studio_project_id": str(project.id)},

        )

        await db.commit()

        await db.refresh(task)

        return task



    async def transition_ai_task_status(

        self,

        task: AiTask,

        to_status: AiTaskStatus,

        **fields,

    ) -> AiTask:

        from app.domain.studio.state_machines import assert_ai_task_transition

        assert_ai_task_transition(task.status, to_status)

        task.status = to_status

        for key, value in fields.items():

            setattr(task, key, value)

        return task



    async def get_task(

        self,

        db: AsyncSession,

        *,

        user_id: uuid.UUID,

        project_id: uuid.UUID,

        task_id: uuid.UUID,

    ) -> AiTask:

        await self.get_project(db, user_id=user_id, project_id=project_id)

        result = await db.execute(

            select(AiTask).where(

                AiTask.id == task_id,

                AiTask.studio_project_id == project_id,

            )

        )

        task = result.scalar_one_or_none()

        if task is None:

            raise AppError("ai_task_not_found", "AI task not found", status_code=404)

        return task



    async def get_audio_presigned_url(

        self,

        db: AsyncSession,

        *,

        user_id: uuid.UUID,

        project_id: uuid.UUID,

    ) -> tuple[str, int, uuid.UUID | None]:

        project = await self.get_project(db, user_id=user_id, project_id=project_id)

        audio_tasks = [

            t

            for t in project.ai_tasks

            if t.task_type == AiTaskType.GENERATE_AUDIO

            and t.status == AiTaskStatus.SUCCEEDED

            and t.result_payload

        ]

        if not audio_tasks:

            raise AppError("no_audio", "No generated audio found", status_code=404)



        latest = max(audio_tasks, key=lambda t: t.created_at)

        asset_id_str = (latest.result_payload or {}).get("media_asset_id")

        if not asset_id_str:

            raise AppError("no_audio_asset", "Audio asset not available", status_code=404)



        asset_id = uuid.UUID(asset_id_str)

        result = await db.execute(

            select(MediaAsset).where(

                MediaAsset.id == asset_id,

                MediaAsset.user_id == user_id,

            )

        )

        asset = result.scalar_one_or_none()

        if asset is None:

            raise AppError("media_asset_not_found", "Media asset not found", status_code=404)



        expires_in = settings.presigned_url_ttl_seconds

        url = await s3_storage.generate_presigned_url(

            bucket=asset.bucket,

            key=asset.object_key,

            expires_in=expires_in,

        )

        return url, expires_in, asset.id





studio_service = StudioService()

