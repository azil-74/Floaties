# Save Notes: Custom Text Editor with Drag & Drop, URLs, and Native Overlays
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Hidden native OS scrollbars to maximize text real estate and maintain minimalist aesthetic.

from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import (
    QDragEnterEvent, QDropEvent, QMouseEvent, QDesktopServices
)
import re

class SmartEditor(QTextEdit):
    """Dedicated text editor handling advanced system interactions and text formatting."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMouseTracking(True) 
        
        # UI Polish: Eradicate chunky scrollbars. Native scrolling mechanics still work perfectly.
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def _get_url_at_pos(self, pos) -> str | None:
        """Calculates the exact text block under the mouse pointer to extract URLs."""
        cursor = self.cursorForPosition(pos)
        pos_in_block = cursor.positionInBlock()
        
        for match in re.finditer(r"https?://\S+", cursor.block().text()):
            if match.start() <= pos_in_block <= match.end():
                return match.group(0)
        return None

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Breaks the native C++ synthetic event loop by isolating cursor control."""
        viewport = self.viewport()
        
        # STRICT TYPING FIX: Ensure the viewport exists before modifying it
        if viewport is None:
            super().mouseMoveEvent(event)
            return

        # 1. If holding Ctrl and hovering over a link, HIJACK the cursor.
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if self._get_url_at_pos(event.pos()):
                viewport.setCursor(Qt.CursorShape.PointingHandCursor)
                # DO NOT call super(). This stops the native engine from fighting our override.
                event.accept()
                return

        # 2. If not over a link, relinquish control entirely back to the native engine.
        viewport.unsetCursor()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Intercepts Ctrl+Click to securely route URLs to the host OS browser."""
        if event.button() == Qt.MouseButton.LeftButton and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            url = self._get_url_at_pos(event.pos())
            if url:
                QDesktopServices.openUrl(QUrl(url))
                event.accept() 
                return 
        super().mousePressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        mime_data = event.mimeData()
        if mime_data is not None and mime_data.hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        mime_data = event.mimeData()
        if mime_data is not None and mime_data.hasUrls():
            paths = []
            for url in mime_data.urls():
                if url.isLocalFile():
                    paths.append(url.toLocalFile())
            
            if paths:
                insert_string = "\n".join(paths) + "\n"
                self.textCursor().insertText(insert_string)
                
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def insertFromMimeData(self, source) -> None:
        """Force plain-text pasting to strip background colors from VS Code/Browsers."""
        # STRICT TYPING FIX: Ensure source is not None before checking hasText()
        if source is not None and source.hasText():
            self.insertPlainText(source.text())
        else:
            super().insertFromMimeData(source)