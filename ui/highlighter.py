from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
import re

class MarkdownHighlighter(QSyntaxHighlighter):
    """Scans visible text blocks and applies non-destructive formatting for URLs."""
    def __init__(self, document, base_text_hex: str):
        super().__init__(document)
        self._setup_formats()

    def _setup_formats(self) -> None:
        
        self.url_format = QTextCharFormat()
        self.url_format.setForeground(QColor("#569CD6"))
        self.url_format.setFontUnderline(True)

    def update_theme(self, base_text_hex: str) -> None:
        """Allows dynamic theme swapping."""
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        
        for match in re.finditer(r"https?://\S+", text):
            
            length = match.end() - match.start()
            self.setFormat(match.start(), length, self.url_format)