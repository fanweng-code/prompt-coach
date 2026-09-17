import os
import sys
from collections.abc import Mapping
from pathlib import Path

import httpx
from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QApplication

from .clipboard import QtClipboard
from .config import load_config, resolve_settings, save_config
from .llm_client import LLMClient
from .models import AppConfig, ERROR_MESSAGES, RewriteError
from .transformer import PromptTransformer
from .ui import MainWindow, SettingsDialog
from .worker import RequestController


def config_path() -> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)) / "settings.json"


def build_window(path: Path, environ: Mapping[str, str], transport: httpx.BaseTransport | None = None) -> MainWindow:
    load_failed = False
    try:
        active_config = load_config(path)
    except RewriteError:
        active_config = AppConfig()
        load_failed = True
    session_key = ""

    def transformer_factory():
        settings = resolve_settings(active_config, session_key, environ)
        return PromptTransformer(LLMClient(settings, transport=transport))

    window = MainWindow(RequestController(), transformer_factory, QtClipboard())

    def refresh_destination():
        if not active_config.base_url or not active_config.model:
            window.set_destination("後端未設定")
            return
        try:
            # Validate/display destination even if a remote session key has expired.
            settings = resolve_settings(active_config, session_key or environ.get("PROMPT_COACH_API_KEY", "") or "display-only", {})
        except RewriteError:
            window.set_destination("後端設定無效；請開啟設定修正。")
            return
        locality = "本機 loopback" if settings.is_loopback else "非本機 HTTPS"
        window.set_destination(f"資料目的地：{locality} · {settings.host} · 設定改寫 model={settings.model}")

    def open_settings():
        nonlocal active_config, session_key
        if window.controller.busy:
            return
        dialog = SettingsDialog(active_config, session_key, window)

        def save():
            nonlocal active_config, session_key
            config, key = dialog.values()
            try:
                resolve_settings(config, key, environ)
                save_config(path, config)
            except RewriteError as error:
                dialog.error_label.setText(error.message)
                return
            except Exception:
                dialog.error_label.setText(ERROR_MESSAGES["config"])
                return
            active_config, session_key = config, key
            refresh_destination()
            window.status_label.setText("設定已儲存；API Key 僅保留在本次 session。")
            dialog.accept()

        dialog.buttons.accepted.connect(save)
        dialog.exec()
        dialog.deleteLater()

    window.settings_requested.connect(open_settings)
    refresh_destination()
    if load_failed:
        window.status_label.setText("無法讀取設定；已使用未設定狀態。原檔保留，僅在明確儲存設定時更新。")
    return window


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PromptCoach")
    app.setOrganizationName("PromptCoach")
    window = build_window(config_path(), os.environ)
    window.show()
    return app.exec()
