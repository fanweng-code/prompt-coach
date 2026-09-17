import socket

import pytest


@pytest.fixture(autouse=True)
def isolate_test_environment(monkeypatch):
    monkeypatch.delenv("PROMPT_COACH_API_KEY", raising=False)

    def deny_network(*args, **kwargs):
        raise AssertionError("離線測試禁止真實網路")

    monkeypatch.setattr(socket, "create_connection", deny_network)
    monkeypatch.setattr(socket.socket, "connect", deny_network)
