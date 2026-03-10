import unittest
from datetime import datetime

from src.db.models import MessageRecord
from src.services.export import build_chat_export


class ExportTests(unittest.TestCase):
    def test_build_chat_export_contains_messages_and_usage(self) -> None:
        messages = [
            MessageRecord(
                id=1,
                chat_id=123,
                user_id=1,
                role="user",
                content="Привет",
                created_at=datetime(2026, 3, 10, 12, 0, 0),
            ),
            MessageRecord(
                id=2,
                chat_id=123,
                user_id=1,
                role="assistant",
                content="Ответ",
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
                cost=0.0015,
                created_at=datetime(2026, 3, 10, 12, 0, 5),
            ),
        ]

        export_text = build_chat_export(chat_id=123, messages=messages)

        self.assertIn("chat_id: 123", export_text)
        self.assertIn("[2026-03-10 12:00:00] USER", export_text)
        self.assertIn("[2026-03-10 12:00:05] ASSISTANT", export_text)
        self.assertIn("usage: prompt_tokens=10, completion_tokens=5, total_tokens=15, cost=$0.001500", export_text)


if __name__ == "__main__":
    unittest.main()
