import ipaddress
import json
import math
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlsplit

from .models import AppConfig, RequestSettings, RewriteError


def _validate_fields(config: AppConfig) -> None:
    if not isinstance(config.base_url, str) or not isinstance(config.model, str):
        raise RewriteError("config")
    value = config.read_timeout_s
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise RewriteError("config")


def _destination(base_url: str) -> tuple[str, str, bool]:
    try:
        if not isinstance(base_url, str) or any(c.isspace() or ord(c) < 32 for c in base_url) or "\\" in base_url:
            raise ValueError
        parts = urlsplit(base_url)
        host = parts.hostname
        port = parts.port
        if parts.scheme not in {"http", "https"} or not host or parts.username is not None or parts.password is not None or "?" in base_url or "#" in base_url:
            raise ValueError
        try:
            loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            loopback = host.lower() == "localhost"
        if parts.scheme == "http" and not loopback:
            raise RewriteError("config", "HTTP 僅允許 loopback；非本機目的地請使用 HTTPS。")
        base = base_url.rstrip("/")
        if parts.path.rstrip("/").endswith("/chat/completions"):
            raise RewriteError("config", "Base URL 請填 API 根路徑，移除末尾 /chat/completions。")
        display_host = f"[{host}]" if ":" in host else host
        return base, f"{display_host}:{port}" if port is not None else display_host, loopback
    except (ValueError, TypeError):
        raise RewriteError("config", "Base URL 無效；請填含 http/https 的 API 根路徑，不含認證、query 或 fragment。") from None


def completion_url(base_url: str) -> str:
    base, _, _ = _destination(base_url)
    return base + "/chat/completions"


def resolve_settings(config: AppConfig, session_key: str, environ: Mapping[str, str]) -> RequestSettings:
    _validate_fields(config)
    base, host, loopback = _destination(config.base_url)
    if not config.model.strip():
        raise RewriteError("config", "請先設定實際改寫 Model。")
    key = session_key or environ.get("PROMPT_COACH_API_KEY", "")
    if not loopback and not key:
        raise RewriteError("config", "非本機 HTTPS 後端需要 API Key；請在設定輸入或使用環境變數。")
    return RequestSettings(base, config.model, config.read_timeout_s, key, loopback, host)


def load_config(path: Path) -> AppConfig:
    try:
        if not path.exists():
            return AppConfig()
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError
        config = AppConfig(**{key: data[key] for key in ("base_url", "model", "read_timeout_s") if key in data})
        _validate_fields(config)
        return config
    except (OSError, ValueError, TypeError):
        raise RewriteError("config") from None


def save_config(path: Path, config: AppConfig) -> None:
    _validate_fields(config)
    payload = {"base_url": config.base_url, "model": config.model, "read_timeout_s": config.read_timeout_s}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        raise RewriteError("config") from None
