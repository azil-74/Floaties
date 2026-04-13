# Save Notes: Custom Text Editor with Drag & Drop System Routing
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Created distinct module. Implemented URI parsing for native file/folder drops.

from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent, QDesktopServices
from PyQt6.QtCore import Qt, QUrl
import re

class SmartEditor(QTextEdit):
    """Dedicated text editor handling advanced system interactions and text formatting."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Enable native OS drag-and-drop bridging
        self.setAcceptDrops(True)
        # REQUIRED: Enables mouseMoveEvent firing without holding down a click
        self.setMouseTracking(True) 

    def _get_url_at_pos(self, pos) -> str | None:
        """Calculates the exact text block under the mouse pointer to extract URLs."""
        cursor = self.cursorForPosition(pos)
        pos_in_block = cursor.positionInBlock()
        
        # O(1) regex check exclusively on the specific line currently under the mouse
        for match in re.finditer(r"https?://\S+", cursor.block().text()):
            if match.start() <= pos_in_block <= match.end():
                return match.group(0)
        return None

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Changes cursor to pointing hand if hovering over a URL while holding Ctrl."""
        viewport = self.viewport()
        
        # Pylance fix: Ensure the viewport hasn't been destroyed by the C++ backend
        if viewport is not None:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if self._get_url_at_pos(event.pos()):
                    viewport.setCursor(Qt.CursorShape.PointingHandCursor)
                    return
            
            viewport.setCursor(Qt.CursorShape.IBeamCursor)
            
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Intercepts Ctrl+Click to securely route URLs to the host OS browser."""
        if event.button() == Qt.MouseButton.LeftButton and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            url = self._get_url_at_pos(event.pos())
            if url:
                QDesktopServices.openUrl(QUrl(url))
                return # Consume the event: prevents the text cursor from jumping
        super().mousePressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Filters incoming drops to strictly allow local OS file URLs."""
        mime_data = event.mimeData()
        
        # Detect if the GNOME/Windows file manager is dropping an actual file/folder
        # Pylance fix: Explicitly check for None to prevent null pointer crashes
        if mime_data is not None and mime_data.hasUrls():
            event.acceptProposedAction()
        else:
            # Fallback to allow normal text highlighting/dragging
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        """Intercepts system file drops, sanitizes paths, and injects them as text."""
        mime_data = event.mimeData()
        
        if mime_data is not None and mime_data.hasUrls():
            paths = []
            for url in mime_data.urls():
                # Strictly isolate local files (ignores accidental http/browser image drops)
                if url.isLocalFile():
                    # SECURITY/BUG-FIX: .toLocalFile() automatically strips the "file://" 
                    # prefix Wayland uses and safely decodes URL-encoded spaces (e.g. %20)
                    paths.append(url.toLocalFile())
            
            if paths:
                # UX Polish: Join multiple files with newlines and inject at the exact cursor position
                insert_string = "\n".join(paths) + "\n"
                self.textCursor().insertText(insert_string)
                
            event.acceptProposedAction()
        else:
            # Fallback to default behavior if the user is just dragging text around inside the note
            super().dropEvent(event)