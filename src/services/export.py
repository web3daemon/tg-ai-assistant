from datetime import datetime

from src.db.models import MessageRecord


ROLE_LABELS = {
    "user": "USER",
    "assistant": "ASSISTANT",
    "system": "SYSTEM",
}


def build_chat_export(chat_id: int, messages: list[MessageRecord]) -> str:
    lines = [
        "Telegram AI Bot chat export",
        f"chat_id: {chat_id}",
        f"exported_at: {datetime.now().isoformat(timespec='seconds')}",
        f"messages: {len(messages)}",
        "",
    ]

    for item in messages:
        role = ROLE_LABELS.get(item.role, item.role.upper())
        created_at = item.created_at.isoformat(sep=" ", timespec="seconds") if item.created_at else "unknown"
        lines.append(f"[{created_at}] {role}")
        lines.append(item.content)

        usage_line = _build_usage_line(item)
        if usage_line:
            lines.append(usage_line)
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _build_usage_line(item: MessageRecord) -> str:
    usage_parts: list[str] = []
    if item.prompt_tokens is not None:
        usage_parts.append(f"prompt_tokens={item.prompt_tokens}")
    if item.completion_tokens is not None:
        usage_parts.append(f"completion_tokens={item.completion_tokens}")
    if item.total_tokens is not None:
        usage_parts.append(f"total_tokens={item.total_tokens}")
    if item.cost is not None:
        usage_parts.append(f"cost=${item.cost:.6f}")
    if not usage_parts:
        return ""
    return "usage: " + ", ".join(usage_parts)
