# Save Notes: Markdown & URL Syntax Highlighter
# Target: Windows (Dev) -> Ubuntu (Prod)
# Status: Phase 3 Stable (Python Native Regex to prevent C++ Iterator lockups)

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
import re

class MarkdownHighlighter(QSyntaxHighlighter):
    """Scans visible text blocks and applies non-destructive formatting for URLs."""
    def __init__(self, document, base_text_hex: str):
        super().__init__(document)
        self._setup_formats()

    def _setup_formats(self) -> None:
        # URL Styling: Vibrant Blue and Underlined
        self.url_format = QTextCharFormat()
        self.url_format.setForeground(QColor("#569CD6")) # VS Code Blue
        self.url_format.setFontUnderline(True)

    def update_theme(self, base_text_hex: str) -> None:
        """Allows dynamic theme swapping."""
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        # Highlight URLs safely using Python's native C-backend Regex
        # This completely bypasses the QRegularExpression C++ memory locks
        for match in re.finditer(r"https?://\S+", text):
            # Calculate length dynamically to feed into Qt's format engine
            length = match.end() - match.start()
            self.setFormat(match.start(), length, self.url_format)