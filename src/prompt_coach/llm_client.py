import httpx

from .config import completion_url
from .models import Completion, RequestSettings, RewriteError


class LLMClient:
    def __init__(self, settings: RequestSettings, transport: httpx.BaseTransport | None = None):
        self.settings = settings
        self.transport = transport

    @property
    def requested_model(self) -> str:
        return self.settings.model

    def complete(self, system: str, user: str) -> Completion:
        settings = self.settings
        timeout = httpx.Timeout(connect=5.0, read=settings.read_timeout_s, write=60.0, pool=5.0)
        headers = {"Authorization": f"Bearer {settings.api_key}"} if settings.api_key else {}
        try:
            with httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False, transport=self.transport) as client:
                response = client.post(completion_url(settings.base_url), headers=headers, json={
                    "model": settings.model, "stream": False,
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                })
        except httpx.TimeoutException:
            raise RewriteError("timeout") from None
        except httpx.RequestError:
            raise RewriteError("connection") from None

        if response.status_code in (401, 403):
            raise RewriteError("auth")
        if response.status_code == 429:
            raise RewriteError("rate_limit")
        if not 200 <= response.status_code < 300:
            raise RewriteError("http", f"後端回傳 HTTP {response.status_code}；請檢查服務狀態。")
        try:
            body = response.json()
        except (ValueError, UnicodeError):
            raise RewriteError("invalid_response") from None
        if not isinstance(body, dict):
            raise RewriteError("invalid_response")
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise RewriteError("invalid_response")
        choice = choices[0]
        finish = choice.get("finish_reason")
        if finish == "length":
            raise RewriteError("truncated")
        if finish not in (None, "stop", ""):
            raise RewriteError("unsupported_response")
        message = choice.get("message")
        if not isinstance(message, dict):
            raise RewriteError("invalid_response")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            if any(message.get(key) for key in ("reasoning", "reasoning_content", "tool_calls", "function_call")):
                raise RewriteError("unsupported_response")
            raise RewriteError("invalid_response")
        model = body.get("model")
        return Completion(content, model if isinstance(model, str) and model.strip() else None)
