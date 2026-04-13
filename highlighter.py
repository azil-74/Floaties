# Save Notes: Markdown & URL Syntax Highlighter
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: O(1) text styling decoupled from the main UI thread.

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QRegularExpression

class MarkdownHighlighter(QSyntaxHighlighter):
    """Scans visible text blocks and applies non-destructive formatting."""
    def __init__(self, document, base_text_hex: str):
        super().__init__(document)
        self._setup_formats()

    def _setup_formats(self) -> None:
        # URL Styling: Vibrant Blue and Underlined
        self.url_format = QTextCharFormat()
        self.url_format.setForeground(QColor("#569CD6")) # VS Code Blue
        self.url_format.setFontUnderline(True)
        
        # C++ Native Regex for zero-latency UI thread execution
        self.url_pattern = QRegularExpression(r"(https?://\S+)")

    def update_theme(self, base_text_hex: str) -> None:
        """Allows dynamic theme swapping without destroying text state."""
        # URLs stay blue regardless of theme, but we prep this for Phase 4 text updates
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        # 1. Highlight URLs
        iterator = self.url_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self.url_format)