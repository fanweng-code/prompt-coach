import json
from pathlib import Path

import pytest

from prompt_coach.config import completion_url, load_config, resolve_settings, save_config
from prompt_coach.models import AppConfig, RewriteError


def test_missing_config_and_empty_destination(tmp_path):
    assert load_config(tmp_path / "absent.json") == AppConfig()
    for config in (AppConfig(), AppConfig("http://localhost/v1", "")):
        with pytest.raises(RewriteError) as error:
            resolve_settings(config, "", {})
        assert error.value.code == "config"


@pytest.mark.parametrize("url,loopback", [
    ("http://localhost:8000/v1/", True), ("http://127.0.0.2/v1", True),
    ("http://[::1]:8000/v1", True), ("https://localhost/v1", True),
    ("https://example.test/v1", False),
])
def test_destination_matrix(url, loopback):
    settings = resolve_settings(AppConfig(url, "改寫模型"), "" if loopback else "synthetic", {})
    assert settings.is_loopback is loopback
    assert completion_url(settings.base_url) == url.rstrip("/") + "/chat/completions"


@pytest.mark.parametrize("url", [
    "ftp://example.test", "http:///v1", "http://localhost:bad", "http://localhost:99999",
    "https://user:synthetic@example.test/v1", "https://example.test/v1?key=synthetic",
    "https://example.test/v1#synthetic", "http://192.168.1.2/v1", "http://example.test/v1",
    "http://localhost/v1/chat/completions/", "http://local host/v1", "http://localhost\\@example.test",
])
def test_unsafe_or_ambiguous_url_rejected(url):
    with pytest.raises(RewriteError) as error:
        resolve_settings(AppConfig(url, "model"), "synthetic", {})
    assert error.value.code == "config"
    assert "synthetic" not in str(error.value)


def test_remote_requires_key_and_session_precedence():
    config = AppConfig("https://example.test/v1", "model")
    with pytest.raises(RewriteError):
        resolve_settings(config, "", {})
    env = {"PROMPT_COACH_API_KEY": "synthetic-env"}
    settings = resolve_settings(config, "synthetic-session", env)
    assert settings.api_key == "synthetic-session"
    assert "synthetic-session" not in repr(settings)
    assert resolve_settings(config, "", env).api_key == "synthetic-env"


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf"), "60", True])
def test_invalid_timeout_rejected(timeout):
    with pytest.raises(RewriteError):
        resolve_settings(AppConfig("http://localhost", "model", timeout), "", {})


def test_config_roundtrip_whitelist_and_unknown_key(tmp_path):
    path = tmp_path / "new" / "settings.json"
    config = AppConfig("http://localhost/v1", "繁體模型", 12.5)
    save_config(path, config)
    assert load_config(path) == config
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert set(payload) == {"base_url", "model", "read_timeout_s"}
    payload["api_key"] = "synthetic-ignored"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert load_config(path) == config
    assert resolve_settings(load_config(path), "", {}).api_key == ""


@pytest.mark.parametrize("data", ["not json synthetic", "[]", '{"model": 12}', '{"base_url": null}', '{"read_timeout_s": true}'])
def test_bad_config_safe_error(tmp_path, data):
    path = tmp_path / "settings.json"
    path.write_text(data, encoding="utf-8")
    with pytest.raises(RewriteError) as error:
        load_config(path)
    assert error.value.code == "config"
    assert "synthetic" not in str(error.value)
    assert path.read_text(encoding="utf-8") == data


def test_write_io_error_is_safe(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise PermissionError("synthetic-sensitive-path")
    monkeypatch.setattr(Path, "write_text", fail)
    with pytest.raises(RewriteError) as error:
        save_config(tmp_path / "settings.json", AppConfig())
    assert error.value.code == "config"
    assert "synthetic" not in str(error.value)
