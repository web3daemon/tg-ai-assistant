import json
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import delete, func, select

from src.db.models import (
    BackgroundJobRecord,
    ChatSettingsRecord,
    ChatSummaryRecord,
    JobArtifactRecord,
    MessageRecord,
)
from src.db.session import SessionLocal


class ChatRepository:
    def add_message(
        self,
        chat_id: int,
        user_id: int,
        role: str,
        content: str,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
        cost: float | None = None,
    ) -> None:
        with SessionLocal() as session:
            session.add(
                MessageRecord(
                    chat_id=chat_id,
                    user_id=user_id,
                    role=role,
                    content=content,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    cost=cost,
                )
            )
            session.commit()

    def get_recent_messages(self, chat_id: int, limit: int) -> list[MessageRecord]:
        with SessionLocal() as session:
            stmt = (
                select(MessageRecord)
                .where(MessageRecord.chat_id == chat_id)
                .order_by(MessageRecord.id.desc())
                .limit(limit)
            )
            records: Sequence[MessageRecord] = session.execute(stmt).scalars().all()
            return list(reversed(records))

    def get_all_messages(self, chat_id: int) -> list[MessageRecord]:
        with SessionLocal() as session:
            stmt = (
                select(MessageRecord)
                .where(MessageRecord.chat_id == chat_id)
                .order_by(MessageRecord.id.asc())
            )
            return list(session.execute(stmt).scalars().all())

    def clear_chat(self, chat_id: int) -> int:
        with SessionLocal() as session:
            stmt = delete(MessageRecord).where(MessageRecord.chat_id == chat_id)
            result = session.execute(stmt)
            session.execute(delete(ChatSummaryRecord).where(ChatSummaryRecord.chat_id == chat_id))
            session.commit()
            return result.rowcount or 0

    def get_last_assistant_message(self, chat_id: int) -> MessageRecord | None:
        with SessionLocal() as session:
            stmt = (
                select(MessageRecord)
                .where(
                    MessageRecord.chat_id == chat_id,
                    MessageRecord.role == "assistant",
                )
                .order_by(MessageRecord.id.desc())
                .limit(1)
            )
            return session.execute(stmt).scalar_one_or_none()

    def get_chat_usage_summary(self, chat_id: int) -> dict[str, float | int]:
        with SessionLocal() as session:
            stmt = select(
                func.count(MessageRecord.id),
                func.coalesce(func.sum(MessageRecord.prompt_tokens), 0),
                func.coalesce(func.sum(MessageRecord.completion_tokens), 0),
                func.coalesce(func.sum(MessageRecord.total_tokens), 0),
                func.coalesce(func.sum(MessageRecord.cost), 0.0),
            ).where(
                MessageRecord.chat_id == chat_id,
                MessageRecord.role == "assistant",
            )
            count, prompt_tokens, completion_tokens, total_tokens, cost = session.execute(stmt).one()
            return {
                "requests": int(count or 0),
                "prompt_tokens": int(prompt_tokens or 0),
                "completion_tokens": int(completion_tokens or 0),
                "total_tokens": int(total_tokens or 0),
                "cost": float(cost or 0.0),
            }

    def get_chat_summary(self, chat_id: int) -> ChatSummaryRecord | None:
        with SessionLocal() as session:
            return session.get(ChatSummaryRecord, chat_id)

    def get_messages_after(self, chat_id: int, after_message_id: int) -> list[MessageRecord]:
        with SessionLocal() as session:
            stmt = (
                select(MessageRecord)
                .where(
                    MessageRecord.chat_id == chat_id,
                    MessageRecord.id > after_message_id,
                )
                .order_by(MessageRecord.id.asc())
            )
            return list(session.execute(stmt).scalars().all())

    def upsert_chat_summary(self, chat_id: int, summary_text: str, last_compacted_message_id: int) -> None:
        with SessionLocal() as session:
            record = session.get(ChatSummaryRecord, chat_id)
            if record is None:
                record = ChatSummaryRecord(
                    chat_id=chat_id,
                    summary_text=summary_text,
                    last_compacted_message_id=last_compacted_message_id,
                )
                session.add(record)
            else:
                record.summary_text = summary_text
                record.last_compacted_message_id = last_compacted_message_id
            session.commit()


class ChatSettingsRepository:
    def get_chat_settings(self, chat_id: int) -> ChatSettingsRecord | None:
        with SessionLocal() as session:
            return session.get(ChatSettingsRecord, chat_id)

    def upsert_chat_settings(
        self,
        *,
        chat_id: int,
        mode: str | None = None,
        model_override: str | None = None,
        system_prompt_override: str | None = None,
        temperature_override: float | None = None,
        max_tokens_override: int | None = None,
        memory_enabled: bool | None = None,
    ) -> None:
        with SessionLocal() as session:
            record = session.get(ChatSettingsRecord, chat_id)
            if record is None:
                record = ChatSettingsRecord(chat_id=chat_id)
                session.add(record)

            if mode is not None:
                record.mode = mode
            if model_override is not None:
                record.model_override = model_override
            if system_prompt_override is not None:
                record.system_prompt_override = system_prompt_override
            if temperature_override is not None:
                record.temperature_override = temperature_override
            if max_tokens_override is not None:
                record.max_tokens_override = max_tokens_override
            if memory_enabled is not None:
                record.memory_enabled = 1 if memory_enabled else 0
            session.commit()


class BackgroundJobRepository:
    def create_job(
        self,
        *,
        chat_id: int,
        user_id: int,
        job_type: str,
        payload: dict[str, object],
    ) -> int:
        with SessionLocal() as session:
            record = BackgroundJobRecord(
                chat_id=chat_id,
                user_id=user_id,
                job_type=job_type,
                status="queued",
                payload_json=json.dumps(payload, ensure_ascii=False),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record.id

    def add_job_artifact(
        self,
        *,
        job_id: int,
        telegram_file_id: str,
        source_kind: str,
        telegram_file_unique_id: str | None = None,
        file_name: str | None = None,
        mime_type: str | None = None,
        file_size: int | None = None,
        caption_text: str | None = None,
    ) -> int:
        with SessionLocal() as session:
            record = JobArtifactRecord(
                job_id=job_id,
                telegram_file_id=telegram_file_id,
                telegram_file_unique_id=telegram_file_unique_id,
                file_name=file_name,
                mime_type=mime_type,
                file_size=file_size,
                source_kind=source_kind,
                caption_text=caption_text,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record.id

    def get_job_artifacts(self, job_id: int) -> list[JobArtifactRecord]:
        with SessionLocal() as session:
            stmt = (
                select(JobArtifactRecord)
                .where(JobArtifactRecord.job_id == job_id)
                .order_by(JobArtifactRecord.id.asc())
            )
            return list(session.execute(stmt).scalars().all())

    def claim_next_job(self) -> BackgroundJobRecord | None:
        with SessionLocal() as session:
            stmt = (
                select(BackgroundJobRecord)
                .where(BackgroundJobRecord.status == "queued")
                .order_by(BackgroundJobRecord.id.asc())
                .limit(1)
            )
            record = session.execute(stmt).scalar_one_or_none()
            if record is None:
                return None

            record.status = "processing"
            record.started_at = datetime.utcnow()
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record

    def mark_completed(self, job_id: int) -> None:
        with SessionLocal() as session:
            record = session.get(BackgroundJobRecord, job_id)
            if record is None:
                return
            record.status = "completed"
            record.finished_at = datetime.utcnow()
            record.error_message = None
            session.commit()

    def mark_failed(self, job_id: int, error_message: str) -> None:
        with SessionLocal() as session:
            record = session.get(BackgroundJobRecord, job_id)
            if record is None:
                return
            record.status = "failed"
            record.finished_at = datetime.utcnow()
            record.error_message = error_message
            session.commit()
