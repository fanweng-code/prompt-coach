from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from .clipboard import QtClipboard
from .models import AppConfig, ERROR_MESSAGES, Mode, ProfileId, RewriteError, RewriteResult
from .transformer import PromptTransformer
from .worker import RequestController


def plain_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    return label


class MainWindow(QMainWindow):
    settings_requested = Signal()

    def __init__(self, controller: RequestController, transformer_factory: Callable[[], PromptTransformer], clipboard: QtClipboard, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.transformer_factory = transformer_factory
        self.clipboard = clipboard
        self.setWindowTitle("Prompt Coach")
        self.resize(1000, 600)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        controls = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([m.value for m in Mode])
        self.mode_combo.setCurrentText(Mode.ENGINEERING.value)
        self.profile_combo = QComboBox()
        self.profile_combo.addItems([p.value for p in ProfileId])
        controls.addWidget(plain_label("模式"))
        controls.addWidget(self.mode_combo)
        controls.addWidget(plain_label("輸出對象"))
        controls.addWidget(self.profile_combo)
        controls.addStretch()
        self.settings_button = QPushButton("設定")
        controls.addWidget(self.settings_button)
        layout.addLayout(controls)

        columns = QHBoxLayout()
        self.source_edit = QPlainTextEdit()
        self.source_edit.setPlaceholderText("手動貼上要整理的文字（最多 20,000 字元）")
        self.source_edit.setAccessibleName("原始文字")
        self.result_edit = QPlainTextEdit()
        self.result_edit.setPlaceholderText("整理後可在此預覽、編輯，再明確按複製結果")
        self.result_edit.setAccessibleName("整理後 Prompt")
        self.result_label = plain_label("整理後 Prompt")
        for label, editor in ((plain_label("原始文字"), self.source_edit), (self.result_label, self.result_edit)):
            column = QVBoxLayout()
            column.addWidget(label)
            column.addWidget(editor)
            columns.addLayout(column)
        layout.addLayout(columns, 1)

        actions = QHBoxLayout()
        self.paste_button = QPushButton("貼上")
        self.rewrite_button = QPushButton("整理")
        self.copy_button = QPushButton("複製結果")
        for button in (self.paste_button, self.rewrite_button, self.copy_button):
            actions.addWidget(button)
        layout.addLayout(actions)
        self.status_label = plain_label("就緒；請先設定實際改寫後端。")
        self.profile_label = plain_label("輸出對象：Astra")
        self.destination_label = plain_label("後端未設定")
        self.backend_result_label = plain_label("")
        for label in (self.status_label, self.profile_label, self.destination_label, self.backend_result_label):
            layout.addWidget(label)
        layout.addWidget(plain_label("僅按「整理」才送出文字。讀取 timeout 不是總耗時保證；失敗不自動重試。"))
        for name in ("source_edit", "result_edit", "mode_combo", "profile_combo", "paste_button", "rewrite_button", "copy_button", "settings_button", "status_label", "destination_label", "result_label"):
            getattr(self, name).setObjectName(name)
        self.paste_button.clicked.connect(self._paste)
        self.copy_button.clicked.connect(self._copy)
        self.rewrite_button.clicked.connect(self._rewrite)
        self.settings_button.clicked.connect(self.settings_requested)
        self.profile_combo.currentTextChanged.connect(lambda text: self.profile_label.setText(f"輸出對象：{text}"))
        controller.succeeded.connect(self._success)
        controller.failed.connect(self._failure)
        controller.busy_changed.connect(self._set_busy)
        controller.ready_to_close.connect(self.close)

    def set_destination(self, label: str) -> None:
        self.destination_label.setText(label)

    def _paste(self) -> None:
        if self.controller.busy:
            return
        text = self.clipboard.read_text()
        if not text:
            self.status_label.setText("剪貼簿沒有文字；可手動貼入純文字。")
            return
        if self.source_edit.toPlainText():
            answer = QMessageBox.question(self, "覆蓋原文", "要以剪貼簿文字覆蓋目前原文嗎？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.source_edit.setPlainText(text)
        self.status_label.setText("已貼上；按「整理」才會傳送。")

    def _copy(self) -> None:
        self.clipboard.write_text(self.result_edit.toPlainText())
        self.status_label.setText("已複製目前預覽文字。")

    def _rewrite(self) -> None:
        if self.controller.busy:
            return
        text = self.source_edit.toPlainText()
        if self.result_edit.toPlainText():
            self.result_label.setText("前次結果")
        try:
            if not text.strip() or len(text) > 20_000:
                raise RewriteError("input")
            transformer = self.transformer_factory()
        except RewriteError as error:
            self._failure(error)
            return
        except Exception:
            self._failure(RewriteError("internal"))
            return
        self.status_label.setText("整理中…")
        self.controller.start(transformer, text, Mode(self.mode_combo.currentText()), ProfileId(self.profile_combo.currentText()))

    def _set_busy(self, busy: bool) -> None:
        self.source_edit.setReadOnly(busy)
        self.result_edit.setReadOnly(busy)
        for widget in (self.rewrite_button, self.paste_button, self.settings_button, self.mode_combo, self.profile_combo):
            widget.setEnabled(not busy)

    def _success(self, result: RewriteResult) -> None:
        self.result_edit.setPlainText(result.text)
        self.result_label.setText(f"整理後 Prompt · {result.mode} / {result.profile_id} {result.profile_version}")
        model = f"後端回報 model={result.actual_model}" if result.actual_model else f"後端未回報實際 model；請求 model={result.requested_model}"
        self.backend_result_label.setText(f"{model} · {result.elapsed_s:.2f} 秒")
        self.status_label.setText("整理完成；請預覽並確認意圖、限制與授權，再複製。")

    def _failure(self, error: RewriteError) -> None:
        # Show only allowlisted UI text, never arbitrary exception messages.
        self.status_label.setText(ERROR_MESSAGES.get(error.code, ERROR_MESSAGES["internal"]))
        self.result_label.setText("本次整理失敗；前次結果" if self.result_edit.toPlainText() else "本次整理失敗；尚無結果")

    def closeEvent(self, event) -> None:
        if not self.controller.busy:
            event.accept()
            return
        event.ignore()
        # A new close dialog supersedes the previous exit choice, including
        # when the request completes while this modal event loop is running.
        self.controller.stay_open()
        dialog = QMessageBox(self)
        dialog.setWindowTitle("請求尚未完成")
        dialog.setText("請求仍在背景執行。可留在視窗，或等待完成後退出。")
        stay = dialog.addButton("留在視窗", QMessageBox.ButtonRole.RejectRole)
        later = dialog.addButton("完成後退出", QMessageBox.ButtonRole.AcceptRole)
        dialog.setDefaultButton(stay)
        dialog.exec()
        if dialog.clickedButton() == later:
            if self.controller.busy:
                self.controller.request_close_after_finish()
            else:
                event.accept()


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, session_key: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("設定實際改寫後端")
        self.resize(580, 300)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.base_url_edit = QLineEdit(config.base_url)
        self.base_url_edit.setPlaceholderText("http://127.0.0.1:8000/v1")
        self.model_edit = QLineEdit(config.model)
        self.key_edit = QLineEdit(session_key)
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(0.01, 1_000_000_000)
        self.timeout_spin.setDecimals(2)
        self.timeout_spin.setValue(config.read_timeout_s)
        for name, widget in (("Base URL", self.base_url_edit), ("Model", self.model_edit), ("API Key", self.key_edit), ("讀取 timeout（秒）", self.timeout_spin)):
            form.addRow(name, widget)
        layout.addLayout(form)
        layout.addWidget(plain_label("API Key 僅本次 session；留空使用 PROMPT_COACH_API_KEY。\nHTTP 僅限 loopback；非本機使用 HTTPS 且需 key。讀取 timeout 不是總耗時保證。"))
        self.error_label = plain_label("")
        layout.addWidget(self.error_label)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def values(self) -> tuple[AppConfig, str]:
        return AppConfig(self.base_url_edit.text(), self.model_edit.text(), self.timeout_spin.value()), self.key_edit.text()
