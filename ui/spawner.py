# Save Notes: Window Spawner (SVG Edition)
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Replaced Unicode '+' with SVG injection. Added Size Experimentation zones.

from PyQt6.QtWidgets import QPushButton, QMainWindow
from PyQt6.QtCore import QPoint, Qt, QSize
from typing import cast
from ui.toolbar import PRESET_THEMES
from ui.utils import load_colored_svg

ACTIVE_NOTES = set()
SPAWN_COUNT = 0

class SpawnButton(QPushButton):
    def __init__(self, parent_window: QMainWindow) -> None:
        super().__init__() 
        
        # --- SIZE EXPERIMENTATION (CONTAINER) ---
        # Adjust these numbers to change the clickable 'hitbox' of the button.
        self.setFixedSize(28, 24)
        
        self.parent_window = parent_window
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self.spawn_duplicate)

    def spawn_duplicate(self) -> None:
        global SPAWN_COUNT
        SPAWN_COUNT += 1
        theme_index = SPAWN_COUNT % len(PRESET_THEMES)
        
        from main import StickyNote 
        
        parent = cast(StickyNote, self.parent_window)
        
        new_note = StickyNote(
            db=parent.db, 
            pwd=parent.pwd, 
            salt=parent.salt,
            theme_index=theme_index
        )
        
        new_note.note_saved.connect(parent.note_saved.emit)

        ACTIVE_NOTES.add(new_note) 
        new_note.move(parent.pos() + QPoint(30, 30))
        new_note.show()
        
    def set_theme(self, text_hex: str) -> None:
        self.setIcon(load_colored_svg("plus.svg", text_hex))
        
        # --- SIZE EXPERIMENTATION (ICON) ---
        # Adjust these numbers to change the scale of the drawn SVG inside the button.
        self.setIconSize(QSize(12, 12))
        
        self.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                border-radius: 4px;
            }}
            QPushButton:hover {{ 
                background-color: rgba(0, 0, 0, 0.08); 
            }}
        """)