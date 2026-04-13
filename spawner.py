# Save Notes: Window Spawner (Symmetric Geometry)
# Action: Stripped tooltips to prevent UI flickering.

from PyQt6.QtWidgets import QPushButton, QMainWindow
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QPainter, QColor, QPen
from toolbar import PRESET_THEMES

# Global registry to prevent Python garbage collection of active windows
ACTIVE_NOTES = set()
# Global counter to track round-robin color assignments across all notes
SPAWN_COUNT = 0

class SpawnButton(QPushButton):
    def __init__(self, parent_window: QMainWindow) -> None:
        super().__init__()
        # UI Polish: Tooltip removed to ensure zero-flicker hover states
        self.setFixedSize(28, 24)
        self.parent_window = parent_window
        self.clicked.connect(self.spawn_duplicate)
        self.icon_color = QColor("#000000")

    def spawn_duplicate(self) -> None:
        """Instantiates a new window with the next round-robin theme."""
        global SPAWN_COUNT
        SPAWN_COUNT += 1
        theme_index = SPAWN_COUNT % len(PRESET_THEMES)
        
        from main import StickyNote 
        
        # Inject the newly calculated theme index into the constructor
        new_note = StickyNote(theme_index=theme_index)
        ACTIVE_NOTES.add(new_note) 
        new_note.move(self.parent_window.pos() + QPoint(30, 30))
        new_note.show()
        
    def set_theme(self, text_hex: str) -> None:
        self.icon_color = QColor(text_hex)
        self.setStyleSheet("""
            QPushButton { border: none; background: transparent; border-radius: 4px; }
            QPushButton:hover { background-color: rgba(0, 0, 0, 0.08); }
        """)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(self.icon_color)
        pen.setWidthF(1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        cx, cy = self.width() // 2, self.height() // 2
        r = 4 # Mathematically perfect radius guarantees identical horizontal/vertical lines
        
        painter.drawLine(cx, cy - r, cx, cy + r)
        painter.drawLine(cx - r, cy, cx + r, cy)
        
        painter.end()