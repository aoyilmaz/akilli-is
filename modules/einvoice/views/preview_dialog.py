from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox


class PreviewDialog(QDialog):
    def __init__(
        self, content: str, title: str = "Önizleme", is_html: bool = False, parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        self.browser = QTextBrowser()
        if is_html:
            self.browser.setHtml(content)
        else:
            self.browser.setPlainText(content)

        layout.addWidget(self.browser)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)
