import json
import threading

import httpx
import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QLineEdit

import prompt_coach.app as app_module
from prompt_coach.app import build_window
from prompt_coach.clipboard import QtClipboard
from prompt_coach.config import load_config, save_config
from prompt_coach.models import AppConfig, RewriteError
from test_ui import click


def configure(qtbot, window, action):
    failures = []
    def run():
        dialog = QApplication.activeModalWidget()
        try:
            action(dialog)
        except BaseException as error:
            failures.append(error)
            dialog.reject()
    QTimer.singleShot(0, run)
    click(qtbot, window.settings_button)
    if failures:
        raise failures[0]


def fill(dialog, url="http://127.0.0.1:8000/v1", model="local-rewriter", key="", timeout=23):
    dialog.base_url_edit.setText(url)
    dialog.model_edit.setText(model)
    dialog.key_edit.setText(key)
    dialog.timeout_spin.setValue(timeout)


def save_button(dialog):
    return dialog.buttons.button(QDialogButtonBox.StandardButton.Save)


def make_app(qtbot, tmp_path, handler=None, environ=None, config=None):
    path = tmp_path / "settings.json"
    if config:
        save_config(path, config)
    seen = []
    def dispatch(request):
        seen.append(request)
        return handler(request) if handler else httpx.Response(200, json={"choices": [
            {"message": {"content": "合成結果"}, "finish_reason": "stop"}]})
    window = build_window(path, environ or {}, httpx.MockTransport(dispatch))
    qtbot.addWidget(window)
    window.show()
    return window, path, seen


@pytest.mark.parametrize("mode", ["Command", "Engineering", "Thought"])
@pytest.mark.parametrize("profile", ["Astra", "Generic"])
def test_six_combinations_never_change_destination_or_backend(qtbot, tmp_path, mode, profile, monkeypatch):
    def no_clipboard(self):
        raise AssertionError("startup read clipboard")
    monkeypatch.setattr(QtClipboard, "read_text", no_clipboard)
    window, _, seen = make_app(qtbot, tmp_path, config=AppConfig("http://127.0.0.1:8000/v1", "local-rewriter"))
    assert seen == [] and window.source_edit.toPlainText() == ""
    window.mode_combo.setCurrentText(mode)
    window.profile_combo.setCurrentText(profile)
    assert profile in window.profile_label.text()
    window.source_edit.setPlainText("整理這句話")
    click(qtbot, window.rewrite_button)
    qtbot.waitUntil(lambda: not window.controller.busy)
    assert window.result_edit.toPlainText() == "合成結果"
    assert len(seen) == 1 and seen[0].url.host == "127.0.0.1"
    assert json.loads(seen[0].content)["model"] == "local-rewriter"
    assert "後端未回報" in window.backend_result_label.text()
    assert "本機 loopback" in window.destination_label.text()


def test_settings_save_cancel_session_precedence_and_reopen(qtbot, tmp_path):
    env = {"PROMPT_COACH_API_KEY": "synthetic-env"}
    window, path, seen = make_app(qtbot, tmp_path, environ=env)
    def save(dialog):
        assert dialog.key_edit.echoMode() == QLineEdit.EchoMode.Password
        assert dialog.key_edit.text() == ""
        fill(dialog, "https://example.test/v1", key="synthetic-session")
        save_button(dialog).click()
    configure(qtbot, window, save)
    assert "非本機 HTTPS" in window.destination_label.text() and "example.test" in window.destination_label.text()
    assert set(json.loads(path.read_text(encoding="utf-8"))) == {"base_url", "model", "read_timeout_s"}
    assert "synthetic" not in path.read_text(encoding="utf-8")
    def cancel(dialog):
        fill(dialog, model="cancelled", key="synthetic-cancelled")
        dialog.reject()
    configure(qtbot, window, cancel)
    window.source_edit.setPlainText("合成")
    click(qtbot, window.rewrite_button)
    qtbot.waitUntil(lambda: not window.controller.busy)
    assert seen[-1].headers["Authorization"] == "Bearer synthetic-session"
    assert json.loads(seen[-1].content)["model"] == "local-rewriter"
    assert seen[-1].extensions["timeout"]["read"] == 23
    def clear_key(dialog):
        dialog.key_edit.clear()
        save_button(dialog).click()
    configure(qtbot, window, clear_key)
    click(qtbot, window.rewrite_button)
    qtbot.waitUntil(lambda: not window.controller.busy)
    assert seen[-1].headers["Authorization"] == "Bearer synthetic-env"
    window.close()
    reopened = build_window(path, {}, httpx.MockTransport(lambda r: pytest.fail("must not request")))
    qtbot.addWidget(reopened)
    reopened.show()
    def check(dialog):
        assert dialog.key_edit.text() == ""
        assert dialog.model_edit.text() == "local-rewriter" and dialog.timeout_spin.value() == 23
        dialog.reject()
    configure(qtbot, reopened, check)
    reopened.source_edit.setPlainText("合成")
    click(qtbot, reopened.rewrite_button)
    assert not reopened.controller.busy


def test_failed_save_keeps_active_config_and_session(qtbot, tmp_path, monkeypatch):
    window, path, seen = make_app(qtbot, tmp_path, config=AppConfig("http://localhost/v1", "old"))
    old = path.read_bytes()
    def fail(*args):
        raise RewriteError("config")
    monkeypatch.setattr(app_module, "save_config", fail)
    def edit(dialog):
        fill(dialog, "https://example.test/v1", "new", "synthetic-new")
        save_button(dialog).click()
        assert dialog.isVisible() and dialog.error_label.text()
        dialog.reject()
    configure(qtbot, window, edit)
    assert path.read_bytes() == old and "localhost" in window.destination_label.text()
    window.source_edit.setPlainText("合成")
    click(qtbot, window.rewrite_button)
    qtbot.waitUntil(lambda: not window.controller.busy)
    assert "Authorization" not in seen[0].headers and json.loads(seen[0].content)["model"] == "old"


def test_corrupt_config_is_not_overwritten_until_explicit_save(qtbot, tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("synthetic-broken-json", encoding="utf-8")
    window = build_window(path, {}, httpx.MockTransport(lambda r: pytest.fail("startup network")))
    qtbot.addWidget(window)
    window.show()
    assert "synthetic" not in window.status_label.text()
    assert window.destination_label.text() == "後端未設定"
    assert path.read_text(encoding="utf-8") == "synthetic-broken-json"
    configure(qtbot, window, lambda d: d.reject())
    assert path.read_text(encoding="utf-8") == "synthetic-broken-json"
    def save(dialog):
        fill(dialog)
        save_button(dialog).click()
    configure(qtbot, window, save)
    assert load_config(path).model == "local-rewriter"


@pytest.mark.parametrize("kind", ["success", "401", "timeout", "truncated", "unknown"])
def test_full_ui_mock_outcomes_busy_and_safe_errors(qtbot, tmp_path, kind):
    gate = threading.Event()
    def handler(request):
        assert gate.wait(3)
        if kind == "timeout":
            raise httpx.ReadTimeout("synthetic-secret", request=request)
        if kind == "unknown":
            raise RuntimeError("synthetic-secret")
        return httpx.Response(401 if kind == "401" else 200, json={"model": "served-local", "choices": [
            {"message": {"content": "新結果"}, "finish_reason": "length" if kind == "truncated" else "stop"}]})
    window, _, seen = make_app(qtbot, tmp_path, handler, config=AppConfig("http://localhost/v1", "local-rewriter"))
    window.source_edit.setPlainText("原文")
    window.result_edit.setPlainText("舊結果")
    try:
        click(qtbot, window.rewrite_button)
        assert not window.settings_button.isEnabled() and not window.profile_combo.isEnabled()
    finally:
        gate.set()
        qtbot.waitUntil(lambda: not window.controller.busy)
    assert len(seen) == 1 and "synthetic" not in window.status_label.text()
    assert window.result_edit.toPlainText() == ("新結果" if kind == "success" else "舊結果")
    if kind == "success":
        assert "served-local" in window.backend_result_label.text()
    else:
        assert "本次整理失敗" in window.result_label.text()


def test_settings_invalid_endpoint_has_correction_and_no_save(qtbot, tmp_path):
    window, path, _ = make_app(qtbot, tmp_path)
    def edit(dialog):
        fill(dialog, "http://localhost/v1/chat/completions")
        save_button(dialog).click()
        assert dialog.isVisible() and "/chat/completions" in dialog.error_label.text()
        dialog.reject()
    configure(qtbot, window, edit)
    assert not path.exists()
