import socket

import pytest
from PySide6.QtCore import QThread

from prompt_coach.models import RewriteResult


@pytest.fixture(autouse=True)
def isolate_test_environment(monkeypatch):
    monkeypatch.delenv("PROMPT_COACH_API_KEY", raising=False)

    def deny_network(*args, **kwargs):
        raise AssertionError("離線測試禁止真實網路")

    monkeypatch.setattr(socket, "create_connection", deny_network)
    monkeypatch.setattr(socket.socket, "connect", deny_network)


class FakeTransformer:
    def __init__(self, gate=None, error=None):
        self.gate = gate
        self.error = error
        self.calls = []
        self.thread = None

    def rewrite(self, text, mode, profile):
        self.calls.append((text, mode, profile))
        self.thread = QThread.currentThread()
        if self.gate is not None and not self.gate.wait(3):
            raise RuntimeError("test gate was not released")
        if self.error:
            raise self.error
        return RewriteResult("合成結果", mode, profile, "1.0.0", "requested-fake", "served-fake", 0.01)


class FakeClipboard:
    def __init__(self, read_value="合成貼文"):
        self.read_value = read_value
        self.read_count = 0
        self.written_texts = []

    def read_text(self):
        self.read_count += 1
        return self.read_value

    def write_text(self, text):
        self.written_texts.append(text)
