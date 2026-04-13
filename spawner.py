# Save Notes: Window Spawner (Pure CSS / Modern Typography)
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Stripped QtAwesome to bypass Windows GDI deadlock.

from PyQt6.QtWidgets import QPushButton, QMainWindow
from PyQt6.QtCore import QPoint
from toolbar import PRESET_THEMES

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
        
        new_note = StickyNote(theme_index=theme_index)
        ACTIVE_NOTES.add(new_note) 
        new_note.move(self.parent_window.pos() + QPoint(30, 30))
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