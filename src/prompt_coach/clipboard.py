from PySide6.QtWidgets import QApplication


class QtClipboard:
    def read_text(self) -> str | None:
        mime = QApplication.clipboard().mimeData()
        return mime.text() if mime is not None and mime.hasText() else None

    def write_text(self, text: str) -> None:
        QApplication.clipboard().setText(text)
