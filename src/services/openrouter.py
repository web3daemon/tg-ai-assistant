import logging

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class OpenRouterError(Exception):
    pass


class OpenRouterClient:
    def __init__(self) -> None:
        self._base_url = settings.openrouter_base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "Telegram AI Bot",
        }

    async def generate_response(self, messages: list[dict[str, object]]) -> dict[str, str | int | float | None]:
        payload = {
            "model": settings.openrouter_model,
            "messages": messages,
            "temperature": settings.model_temperature,
            "max_tokens": settings.model_max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers=self._headers,
                    json=payload,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                body = exc.response.text
                logger.exception("OpenRouter returned an HTTP error: %s", body)
                raise OpenRouterError("AI service returned an error. Check model access or limits.") from exc
            except httpx.HTTPError as exc:
                logger.exception("OpenRouter request failed")
                raise OpenRouterError("Failed to reach AI service. Check network and API settings.") from exc

        data = response.json()

        try:
            usage = data.get("usage", {})
            content = data["choices"][0]["message"]["content"]
            if isinstance(content, list):
                content = "\n".join(
                    item.get("text", "")
                    for item in content
                    if isinstance(item, dict) and item.get("type") == "text"
                ).strip()

            return {
                "content": str(content).strip(),
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
                "cost": usage.get("cost"),
            }
        except (KeyError, IndexError, AttributeError, TypeError) as exc:
            logger.exception("Unexpected OpenRouter response: %s", data)
            raise OpenRouterError("AI service returned an unexpected response.") from exc
