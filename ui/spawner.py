# Save Notes: Window Spawner (Pure CSS / Modern Typography)
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Implemented typing.cast to satisfy Pylance strict type checking on QMainWindow attributes.

from PyQt6.QtWidgets import QPushButton, QMainWindow
from PyQt6.QtCore import QPoint
from typing import cast
from ui.toolbar import PRESET_THEMES

ACTIVE_NOTES = set()
SPAWN_COUNT = 0

class SpawnButton(QPushButton):
    def __init__(self, parent_window: QMainWindow) -> None:
        # Using a fullwidth plus symbol for perfect mathematical centering
        super().__init__("＋") 
        self.setFixedSize(28, 24)
        self.parent_window = parent_window
        self.clicked.connect(self.spawn_duplicate)

    def spawn_duplicate(self) -> None:
        global SPAWN_COUNT
        SPAWN_COUNT += 1
        theme_index = SPAWN_COUNT % len(PRESET_THEMES)
        
        from main import StickyNote 
        
        # Action: Cast the generic QMainWindow to StickyNote to expose custom Vault attributes to Pylance
        parent = cast(StickyNote, self.parent_window)
        
        new_note = StickyNote(
            db=parent.db, 
            pwd=parent.pwd, 
            salt=parent.salt,
            theme_index=theme_index
        )
        
        # Daisy-chain the signal: Child Note -> Parent Note -> Dashboard Refresh
        new_note.note_saved.connect(parent.note_saved.emit)

        ACTIVE_NOTES.add(new_note) 
        new_note.move(parent.pos() + QPoint(30, 30))
        new_note.show()
        
    def set_theme(self, text_hex: str) -> None:
        self.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                border-radius: 4px;
                color: {text_hex};
                font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
                font-size: 16px;
                font-weight: 300;
                padding-bottom: 2px;
            }}
            QPushButton:hover {{ 
                background-color: rgba(0, 0, 0, 0.08); 
            }}
        """)