import threading

import pytest
from PySide6.QtCore import QTimer

from conftest import FakeTransformer
from prompt_coach.models import Mode, ProfileId, RewriteError
from prompt_coach.worker import RequestController


def test_single_request_keeps_main_loop_alive_until_finished(qtbot, qapp):
    gate = threading.Event()
    fake = FakeTransformer(gate)
    controller = RequestController()
    results, states = [], []
    controller.succeeded.connect(results.append)
    controller.busy_changed.connect(states.append)
    try:
        assert controller.start(fake, "原文", Mode.ENGINEERING, ProfileId.ASTRA)
        assert not controller.start(fake, "第二次", Mode.COMMAND, ProfileId.GENERIC)
        ticks = []
        QTimer.singleShot(0, lambda: ticks.append(True))
        qtbot.waitUntil(lambda: bool(ticks) and bool(fake.calls))
        assert controller.busy and controller._worker is not None
        assert fake.thread != qapp.thread()
        assert results == [] and states == [True]
    finally:
        gate.set()
        qtbot.waitUntil(lambda: not controller.busy)
    assert len(results) == 1 and len(fake.calls) == 1
    assert states == [True, False] and controller._worker is None


@pytest.mark.parametrize("error", [None, RewriteError("timeout"), RuntimeError("synthetic-key")], ids=["success", "known-error", "unknown-error"])
def test_close_after_finish_waits_for_thread_on_all_outcomes(qtbot, error):
    gate = threading.Event()
    fake = FakeTransformer(gate, error)
    controller = RequestController()
    results, errors, closed = [], [], []
    controller.succeeded.connect(results.append)
    controller.failed.connect(errors.append)
    controller.ready_to_close.connect(lambda: closed.append((controller.busy, controller._worker)))
    try:
        controller.start(fake, "合成", Mode.THOUGHT, ProfileId.GENERIC)
        controller.request_close_after_finish()
        qtbot.waitUntil(lambda: bool(fake.calls))
        assert closed == [] and controller._worker is not None
    finally:
        gate.set()
        qtbot.waitUntil(lambda: not controller.busy)
    assert closed == [(False, None)]
    assert len(errors) == (1 if error else 0)
    assert len(results) == (0 if error else 1)
    if error:
        assert "synthetic" not in str(errors[0])
        assert errors[0].code == ("timeout" if isinstance(error, RewriteError) else "internal")


def test_idle_close_signal_and_later_request(qtbot):
    controller = RequestController()
    with qtbot.waitSignal(controller.ready_to_close):
        controller.request_close_after_finish()
    for _ in range(2):
        assert controller.start(FakeTransformer(), "合成", Mode.COMMAND, ProfileId.ASTRA)
        qtbot.waitUntil(lambda: not controller.busy)
