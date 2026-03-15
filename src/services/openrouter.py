import logging
from asyncio import sleep
from dataclasses import dataclass, field

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class OpenRouterError(Exception):
    pass


@dataclass(slots=True)
class OpenRouterRequestOptions:
    primary_model: str
    fallback_models: list[str] = field(default_factory=list)
    temperature: float | None = None
    max_tokens: int | None = None
    route_name: str = "default"


class OpenRouterClient:
    def __init__(self) -> None:
        self._base_url = settings.openrouter_base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "Telegram AI Bot",
        }
        self._timeout = settings.openrouter_timeout_seconds
        self._max_retries = max(settings.openrouter_max_retries, 0)
        self._retry_backoff_seconds = max(settings.openrouter_retry_backoff_seconds, 0.0)
        self._client = httpx.AsyncClient(timeout=self._timeout)

    async def generate_response(
        self,
        messages: list[dict[str, object]],
        request_options: OpenRouterRequestOptions | None = None,
    ) -> dict[str, str | int | float | None]:
        options = request_options or OpenRouterRequestOptions(primary_model=settings.openrouter_model)
        models = [options.primary_model, *options.fallback_models]
        last_error: Exception | None = None

        for model_name in self._dedupe_models(models):
            try:
                response = await self._send_with_retries(
                    model_name=model_name,
                    messages=messages,
                    temperature=options.temperature if options.temperature is not None else settings.model_temperature,
                    max_tokens=options.max_tokens if options.max_tokens is not None else settings.model_max_tokens,
                    route_name=options.route_name,
                )
                parsed = self._parse_response(response.json())
                parsed["model"] = model_name
                return parsed
            except OpenRouterError as exc:
                last_error = exc
                logger.warning("OpenRouter route '%s' failed for model %s", options.route_name, model_name, exc_info=True)
                continue

        raise OpenRouterError("AI service is temporarily unavailable.") from last_error

    async def _send_with_retries(
        self,
        *,
        model_name: str,
        messages: list[dict[str, object]],
        temperature: float,
        max_tokens: int,
        route_name: str,
    ) -> httpx.Response:
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = await self._client.post(
                    f"{self._base_url}/chat/completions",
                    headers=self._headers,
                    json=payload,
                )
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                body = exc.response.text
                if self._is_retryable_status(exc.response.status_code) and attempt < self._max_retries:
                    last_error = exc
                    logger.warning(
                        "OpenRouter route '%s' model=%s retryable HTTP error on attempt %s/%s: %s",
                        route_name,
                        model_name,
                        attempt + 1,
                        self._max_retries + 1,
                        body,
                    )
                    await sleep(self._retry_delay(attempt))
                    continue

                logger.exception("OpenRouter returned an HTTP error for model %s: %s", model_name, body)
                raise OpenRouterError("AI service returned an error. Check model access or limits.") from exc
            except httpx.HTTPError as exc:
                if attempt < self._max_retries:
                    last_error = exc
                    logger.warning(
                        "OpenRouter route '%s' model=%s request failed on attempt %s/%s",
                        route_name,
                        model_name,
                        attempt + 1,
                        self._max_retries + 1,
                        exc_info=True,
                    )
                    await sleep(self._retry_delay(attempt))
                    continue

                logger.exception("OpenRouter request failed for model %s", model_name)
                raise OpenRouterError("Failed to reach AI service. Check network and API settings.") from exc

        raise OpenRouterError("AI service is temporarily unavailable.") from last_error

    @staticmethod
    def _parse_response(data: dict[str, object]) -> dict[str, str | int | float | None]:
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

    @staticmethod
    def _dedupe_models(models: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for model in models:
            normalized = model.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)
        return result

    async def close(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _is_retryable_status(status_code: int) -> bool:
        return status_code in {408, 409, 425, 429, 500, 502, 503, 504}

    def _retry_delay(self, attempt: int) -> float:
        return self._retry_backoff_seconds * (attempt + 1)
