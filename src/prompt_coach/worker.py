from PySide6.QtCore import QObject, QThread, Signal, Slot

from .models import Mode, ProfileId, RewriteError
from .transformer import PromptTransformer


class RewriteWorker(QThread):
    succeeded = Signal(object)
    failed = Signal(object)

    def __init__(self, transformer: PromptTransformer, text: str, mode: Mode, profile: ProfileId, parent=None):
        super().__init__(parent)
        self.transformer = transformer
        self.text = text
        self.mode = mode
        self.profile = profile

    def run(self) -> None:
        try:
            result = self.transformer.rewrite(self.text, self.mode, self.profile)
        except RewriteError as error:
            self.failed.emit(error)
        except Exception:
            self.failed.emit(RewriteError("internal"))
        else:
            self.succeeded.emit(result)


class RequestController(QObject):
    succeeded = Signal(object)
    failed = Signal(object)
    busy_changed = Signal(bool)
    ready_to_close = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._close_after_finish = False

    @property
    def busy(self) -> bool:
        return self._worker is not None

    def start(self, transformer: PromptTransformer, text: str, mode: Mode, profile: ProfileId) -> bool:
        if self.busy:
            return False
        self._close_after_finish = False
        worker = RewriteWorker(transformer, text, mode, profile, self)
        self._worker = worker
        worker.succeeded.connect(self.succeeded)
        worker.failed.connect(self.failed)
        worker.finished.connect(self._finished)
        self.busy_changed.emit(True)
        worker.start()
        return True

    def request_close_after_finish(self) -> None:
        if self.busy:
            self._close_after_finish = True
        else:
            self.ready_to_close.emit()

    @Slot()
    def _finished(self) -> None:
        worker = self._worker
        self._worker = None
        worker.deleteLater()
        self.busy_changed.emit(False)
        if self._close_after_finish:
            self._close_after_finish = False
            self.ready_to_close.emit()
