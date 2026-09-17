import threading

import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from conftest import FakeClipboard, FakeTransformer
from prompt_coach.models import RewriteError
from prompt_coach.ui import MainWindow
from prompt_coach.worker import RequestController


def make_window(qtbot, fake=None, clipboard=None, factory=None):
    fake = fake or FakeTransformer()
    clipboard = clipboard or FakeClipboard()
    window = MainWindow(RequestController(), factory or (lambda: fake), clipboard)
    qtbot.addWidget(window)
    window.show()
    return window, fake, clipboard


def click(qtbot, widget):
    qtbot.mouseClick(widget, Qt.MouseButton.LeftButton)


def choose_dialog(text):
    def choose():
        dialog = QApplication.activeModalWidget()
        if isinstance(dialog, QMessageBox):
            for button in dialog.buttons():
                if button.text() == text:
                    button.click()
                    return
            dialog.reject()
    QTimer.singleShot(0, choose)


def test_open_has_no_side_effects_and_plain_editors(qtbot):
    created = []
    def factory():
        created.append(True)
        return FakeTransformer()
    window, _, clipboard = make_window(qtbot, factory=factory)
    assert clipboard.read_count == 0 and clipboard.written_texts == [] and created == []
    assert window.mode_combo.currentText() == "Engineering"
    assert window.profile_combo.currentText() == "Astra"
    assert window.source_edit.toPlainText() == window.result_edit.toPlainText() == ""
    window.result_edit.setPlainText("<b>literal</b> **plain**")
    click(qtbot, window.copy_button)
    assert clipboard.written_texts == ["<b>literal</b> **plain**"]


@pytest.mark.parametrize("value", [None, ""])
def test_nontext_clipboard_preserves_source(qtbot, value):
    window, _, clipboard = make_window(qtbot, clipboard=FakeClipboard(value))
    window.source_edit.setPlainText("保留原文")
    click(qtbot, window.paste_button)
    assert window.source_edit.toPlainText() == "保留原文" and clipboard.read_count == 1
    assert "文字" in window.status_label.text()


def test_paste_empty_then_overwrite_cancel_and_yes(qtbot, monkeypatch):
    window, _, clipboard = make_window(qtbot)
    click(qtbot, window.paste_button)
    assert window.source_edit.toPlainText() == "合成貼文"
    clipboard.read_value = "替換內容"
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Cancel)
    click(qtbot, window.paste_button)
    assert window.source_edit.toPlainText() == "合成貼文"
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    click(qtbot, window.paste_button)
    assert window.source_edit.toPlainText() == "替換內容" and clipboard.read_count == 3


@pytest.mark.parametrize("text", ["", " \n", "😀" * 20_001], ids=["empty", "blank", "too-long"])
def test_invalid_source_does_not_create_transformer(qtbot, text):
    created = []
    window, _, _ = make_window(qtbot, factory=lambda: created.append(True))
    window.source_edit.setPlainText(text)
    click(qtbot, window.rewrite_button)
    assert created == [] and not window.controller.busy
    assert "20,000" in window.status_label.text()


def test_busy_freezes_input_controls_and_preserves_previous_result(qtbot):
    gate = threading.Event()
    window, fake, clipboard = make_window(qtbot, FakeTransformer(gate))
    window.source_edit.setPlainText("😀" * 20_000)
    window.result_edit.setPlainText("前次合成結果")
    window.set_destination("本機 loopback | 127.0.0.1 | test-model")
    try:
        click(qtbot, window.rewrite_button)
        for widget in (window.rewrite_button, window.paste_button, window.settings_button, window.mode_combo, window.profile_combo):
            assert not widget.isEnabled()
        assert window.source_edit.isReadOnly() and window.result_edit.isReadOnly()
        assert window.result_edit.toPlainText() == "前次合成結果"
        assert "前次結果" in window.result_label.text()
        assert "127.0.0.1" in window.destination_label.text()
        click(qtbot, window.rewrite_button)
        qtbot.waitUntil(lambda: bool(fake.calls))
        assert len(fake.calls) == 1 and len(fake.calls[0][0]) == 20_000
    finally:
        gate.set()
        qtbot.waitUntil(lambda: not window.controller.busy)
    assert window.result_edit.toPlainText() == "合成結果"
    assert window.rewrite_button.isEnabled() and not window.result_edit.isReadOnly()
    assert clipboard.written_texts == []
    window.result_edit.setPlainText("人工修正 <tag> 😀")
    click(qtbot, window.copy_button)
    assert clipboard.written_texts == ["人工修正 <tag> 😀"]


@pytest.mark.parametrize("code", ["timeout", "invalid_response", "truncated"])
def test_failure_retains_previous_result_and_source(qtbot, code):
    window, _, clipboard = make_window(qtbot, FakeTransformer(error=RewriteError(code)))
    window.source_edit.setPlainText("原文")
    window.result_edit.setPlainText("舊結果")
    click(qtbot, window.rewrite_button)
    qtbot.waitUntil(lambda: not window.controller.busy)
    assert window.source_edit.toPlainText() == "原文" and window.result_edit.toPlainText() == "舊結果"
    assert "本次整理失敗" in window.result_label.text() and "前次結果" in window.result_label.text()
    assert clipboard.written_texts == [] and window.rewrite_button.isEnabled()


@pytest.mark.parametrize("error", [None, RewriteError("timeout")], ids=["success", "failure"])
def test_busy_close_stay_then_close_after_finish(qtbot, error):
    gate = threading.Event()
    window, _, _ = make_window(qtbot, FakeTransformer(gate, error))
    window.source_edit.setPlainText("合成")
    try:
        click(qtbot, window.rewrite_button)
        choose_dialog("留在視窗")
        assert not window.close() and window.isVisible()
        choose_dialog("完成後退出")
        assert not window.close() and window.isVisible()
        assert window.controller.busy
    finally:
        gate.set()
        qtbot.waitUntil(lambda: not window.controller.busy)
    qtbot.waitUntil(lambda: not window.isVisible())


def test_idle_close(qtbot):
    window, _, _ = make_window(qtbot)
    assert window.close() and not window.isVisible()


def test_stay_revokes_previously_requested_close(qtbot):
    gate = threading.Event()
    window, _, _ = make_window(qtbot, FakeTransformer(gate))
    window.source_edit.setPlainText("合成")
    try:
        click(qtbot, window.rewrite_button)
        choose_dialog("完成後退出")
        window.close()
        choose_dialog("留在視窗")
        window.close()
    finally:
        gate.set()
        qtbot.waitUntil(lambda: not window.controller.busy)
    assert window.isVisible()
    assert window.result_edit.toPlainText() == "合成結果"


def test_finish_during_close_dialog_then_choose_exit(qtbot):
    gate = threading.Event()
    window, _, _ = make_window(qtbot, FakeTransformer(gate))
    window.source_edit.setPlainText("合成")
    try:
        click(qtbot, window.rewrite_button)
        # Release during the nested dialog loop; choose exit after QThread.finished.
        window.controller.busy_changed.connect(lambda busy: choose_dialog("完成後退出") if not busy else None)
        QTimer.singleShot(0, gate.set)
        window.close()
        qtbot.waitUntil(lambda: not window.controller.busy)
        qtbot.waitUntil(lambda: not window.isVisible(), timeout=1000)
    finally:
        gate.set()
        qtbot.waitUntil(lambda: not window.controller.busy)
