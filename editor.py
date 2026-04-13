# Save Notes: Custom Text Editor with Drag & Drop System Routing
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Created distinct module. Implemented URI parsing for native file/folder drops.

from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

class SmartEditor(QTextEdit):
    """Dedicated text editor handling advanced system interactions and text formatting."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Enable native OS drag-and-drop bridging
        self.setAcceptDrops(True)

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