import html
import re


def render_telegram_html(text: str) -> str:
    normalized = text.replace("\r\n", "\n").strip()
    escaped = html.escape(normalized)

    # Code blocks first so inner formatting is not reprocessed.
    escaped = re.sub(
        r"```(?:\w+)?\n?(.*?)```",
        lambda match: f"<pre>{match.group(1).strip()}</pre>",
        escaped,
        flags=re.DOTALL,
    )

    escaped = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"__(.+?)__", r"<u>\1</u>", escaped)
    escaped = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", escaped)

    paragraphs = [part.strip() for part in escaped.split("\n\n") if part.strip()]
    rendered_parts: list[str] = []
    for paragraph in paragraphs:
        lines = [line.rstrip() for line in paragraph.split("\n") if line.strip()]
        if all(_is_list_line(line) for line in lines):
            rendered_parts.append("\n".join(lines))
        else:
            rendered_parts.append("\n".join(lines))

    return "\n\n".join(rendered_parts)


def strip_markup(text: str) -> str:
    return (
        text.replace("**", "")
        .replace("__", "")
        .replace("```", "")
        .replace("`", "")
    )


def _is_list_line(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith(("- ", "* ")) or bool(re.match(r"\d+\.\s", stripped))
