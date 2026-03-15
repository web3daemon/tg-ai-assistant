import unittest

from src.services.chat_service import ChatService


class FakeMessage:
    def __init__(self, message_id: int, role: str, content: str) -> None:
        self.id = message_id
        self.role = role
        self.content = content
        self.prompt_tokens = None
        self.completion_tokens = None
        self.total_tokens = None
        self.cost = None


class FakeSummary:
    def __init__(self, summary_text: str, last_compacted_message_id: int) -> None:
        self.summary_text = summary_text
        self.last_compacted_message_id = last_compacted_message_id


class FakeRepository:
    def __init__(self) -> None:
        self.messages: list[FakeMessage] = []
        self.summary: FakeSummary | None = None

    def get_recent_messages(self, chat_id: int, limit: int) -> list[FakeMessage]:
        return self.messages[-limit:]

    def add_message(self, chat_id: int, user_id: int, role: str, content: str, **kwargs: object) -> None:
        self.messages.append(FakeMessage(len(self.messages) + 1, role, content))

    def get_chat_summary(self, chat_id: int) -> FakeSummary | None:
        return self.summary

    def get_messages_after(self, chat_id: int, after_message_id: int) -> list[FakeMessage]:
        return [message for message in self.messages if message.id > after_message_id]

    def upsert_chat_summary(self, chat_id: int, summary_text: str, last_compacted_message_id: int) -> None:
        self.summary = FakeSummary(summary_text, last_compacted_message_id)

    def get_all_messages(self, chat_id: int) -> list[FakeMessage]:
        return self.messages

    def get_last_assistant_message(self, chat_id: int) -> FakeMessage | None:
        for message in reversed(self.messages):
            if message.role == "assistant":
                return message
        return None

    def get_chat_usage_summary(self, chat_id: int) -> dict[str, float | int]:
        return {"requests": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cost": 0.0}

    def clear_chat(self, chat_id: int) -> int:
        deleted = len(self.messages)
        self.messages = []
        self.summary = None
        return deleted


class FakeSettings:
    def __init__(self, system_prompt_override: str | None = None, memory_enabled: int = 1, mode: str = "chat") -> None:
        self.system_prompt_override = system_prompt_override
        self.memory_enabled = memory_enabled
        self.mode = mode


class FakeSettingsRepository:
    def __init__(self, chat_settings: FakeSettings | None = None) -> None:
        self.chat_settings = chat_settings

    def get_chat_settings(self, chat_id: int) -> FakeSettings | None:
        return self.chat_settings


class FakeAIClient:
    def __init__(self) -> None:
        self.calls: list[list[dict[str, object]]] = []
        self.request_options: list[object | None] = []

    async def generate_response(self, messages: list[dict[str, object]], request_options: object | None = None) -> dict[str, object]:
        self.calls.append(messages)
        self.request_options.append(request_options)
        if messages and messages[0]["content"] == "Summarize the conversation state for future turns.":
            return {"content": "summary v2", "prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2, "cost": 0.001}
        return {"content": "assistant reply", "prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15, "cost": 0.002}


class ChatServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_build_context_includes_summary_before_recent_messages(self) -> None:
        repository = FakeRepository()
        repository.summary = FakeSummary("known preferences", 2)
        repository.messages = [
            FakeMessage(3, "user", "recent user"),
            FakeMessage(4, "assistant", "recent assistant"),
        ]
        service = ChatService(repository=repository, ai_client=FakeAIClient(), settings_repository=FakeSettingsRepository())

        context = await service.build_context_messages(chat_id=1)

        self.assertEqual(context[0]["role"], "system")
        self.assertIn("known preferences", str(context[1]["content"]))
        self.assertEqual(context[2]["content"], "recent user")
        self.assertEqual(context[3]["content"], "recent assistant")

    async def test_handle_user_request_refreshes_summary_after_enough_new_messages(self) -> None:
        repository = FakeRepository()
        repository.summary = FakeSummary("old summary", 0)
        repository.messages = [
            FakeMessage(1, "user", "u1"),
            FakeMessage(2, "assistant", "a1"),
            FakeMessage(3, "user", "u2"),
            FakeMessage(4, "assistant", "a2"),
            FakeMessage(5, "user", "u3"),
            FakeMessage(6, "assistant", "a3"),
            FakeMessage(7, "user", "u4"),
        ]
        ai_client = FakeAIClient()
        service = ChatService(repository=repository, ai_client=ai_client, settings_repository=FakeSettingsRepository())

        await service.handle_text_message(chat_id=1, user_id=1, text="new question")

        self.assertIsNotNone(repository.summary)
        assert repository.summary is not None
        self.assertEqual(repository.summary.summary_text, "summary v2")
        self.assertEqual(repository.summary.last_compacted_message_id, len(repository.messages))

    async def test_build_context_uses_chat_prompt_override(self) -> None:
        repository = FakeRepository()
        service = ChatService(
            repository=repository,
            ai_client=FakeAIClient(),
            settings_repository=FakeSettingsRepository(FakeSettings(system_prompt_override="custom prompt")),
        )

        context = await service.build_context_messages(chat_id=1)

        self.assertEqual(context[0]["content"], "custom prompt")

    async def test_build_context_includes_mode_instruction(self) -> None:
        repository = FakeRepository()
        ai_client = FakeAIClient()
        service = ChatService(
            repository=repository,
            ai_client=ai_client,
            settings_repository=FakeSettingsRepository(FakeSettings(mode="translate")),
        )

        context = await service.build_context_messages(chat_id=1)

        self.assertIn("translate", str(context[1]["content"]).lower())

    async def test_handle_text_message_uses_mode_specific_request_options(self) -> None:
        repository = FakeRepository()
        ai_client = FakeAIClient()
        service = ChatService(
            repository=repository,
            ai_client=ai_client,
            settings_repository=FakeSettingsRepository(FakeSettings(mode="translate")),
        )

        await service.handle_text_message(chat_id=1, user_id=1, text="hello")

        self.assertGreaterEqual(len(ai_client.request_options), 1)
        route_name = getattr(ai_client.request_options[0], "route_name", "")
        self.assertEqual(route_name, "chat:translate")


if __name__ == "__main__":
    unittest.main()
