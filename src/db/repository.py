from collections.abc import Sequence

from sqlalchemy import delete, func, select

from src.db.models import MessageRecord
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
