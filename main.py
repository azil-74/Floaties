# Save Notes: Core Application Entry Point
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Eradicated dynamic auto-resize for absolute window stability. 

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QGridLayout, QFrame, QSizeGrip
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

# Import our modular ecosystem
from toolbar import FormattingToolbar, PRESET_THEMES, get_wcag_text_color
from header import DragHeader
from spawner import ACTIVE_NOTES 
from editor import SmartEditor 
from highlighter import MarkdownHighlighter 

class ModernSizeGrip(QSizeGrip):
    """Pure CSS Size Grip to bypass C++ QPainter deadlocks. Relies on native Cursor UX."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setStyleSheet("""
            QSizeGrip {
                background-color: transparent;
                width: 16px;
                height: 16px;
            }
        """)

class StickyNote(QMainWindow):
    """Core Sticky Note Window adhering to Single Responsibility Principle."""
    def __init__(self, theme_index: int = 6) -> None:
        super().__init__()
        self.is_rolled_up = False
        self._normal_height = 150 
        self._initial_theme_index = theme_index
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setMinimumSize(150, 150)
        self.resize(200, 300) 

        self.container = QFrame(self)
        self.container.setObjectName("NoteContainer")
        self.setCentralWidget(self.container)

        # Dynamically fetch the theme based on the round-robin index
        theme = PRESET_THEMES[self._initial_theme_index % len(PRESET_THEMES)]
        base_bg = theme["bg"]
        base_border = theme["border"]
        base_text = get_wcag_text_color(base_bg)
        accent_bg = QColor(base_bg).darker(115).name()

        self.container.setStyleSheet(f"#NoteContainer {{ background-color: {base_bg}; border: 1px solid {base_border}; }}")

        # 1. Instantiate Header
        self.header = DragHeader(self)
        self.header.set_theme(accent_bg, base_border, base_text)
        
        # 2. Instantiate Text Editor
        self.text_editor = SmartEditor(self.container)
        self.text_editor.setStyleSheet(f"background: transparent; border: none; padding: 8px; font-size: 14px; color: {base_text};")
        # ACTION: self.text_editor.textChanged connection completely removed.

        self.highlighter = MarkdownHighlighter(self.text_editor.document(), base_text)

        # 3. Instantiate Hover-Footer Toolbar 
        self.toolbar = FormattingToolbar(self.text_editor)
        self.toolbar.theme_color_changed.connect(self._update_theme_color)
        self.toolbar.set_theme(accent_bg, base_border, base_text)

        self.size_grip = ModernSizeGrip(self.container)

        # --- Modular Layout Construction ---
        main_layout = QGridLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self.header, 0, 0)
        main_layout.addWidget(self.text_editor, 1, 0)
        main_layout.addWidget(self.toolbar, 2, 0) 
        
        main_layout.addWidget(self.size_grip, 2, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        self.size_grip.raise_()

    def toggle_rollup(self) -> None:
        """Soft-minimizes the window to just the header."""
        if not self.is_rolled_up:
            self._normal_height = self.height()
            self.text_editor.setVisible(False)
            self.toolbar.setVisible(False)
            self.size_grip.setVisible(False)
            self.is_rolled_up = True
            
            self.setMinimumSize(150, self.header.height())
            self.resize(self.width(), self.header.height())
        else:
            self.text_editor.setVisible(True)
            self.toolbar.setVisible(True)
            self.size_grip.setVisible(True)
            self.is_rolled_up = False
            
            self.setMinimumSize(150, 150)
            self.resize(self.width(), self._normal_height)
            
        self.header.window_controls.update_rollup_icon(self.is_rolled_up)

    def closeEvent(self, event) -> None:
        """Hooks into the native close event to ensure garbage collection memory safety."""
        ACTIVE_NOTES.discard(self)
        super().closeEvent(event)

    # ACTION: _adjust_height completely deleted.

    def _update_theme_color(self, bg_hex: str, border_hex: str, text_hex: str) -> None:
        self.container.setStyleSheet(f"#NoteContainer {{ background-color: {bg_hex}; border: 1px solid {border_hex}; }}")
        accent_bg = QColor(bg_hex).darker(115).name()
        
        self.header.set_theme(accent_bg, border_hex, text_hex)
        self.toolbar.set_theme(accent_bg, border_hex, text_hex)
        self.text_editor.setStyleSheet(f"background: transparent; border: none; padding: 8px; font-size: 14px; color: {text_hex};")

def main() -> None:
    app = QApplication(sys.argv)
    note = StickyNote()
    ACTIVE_NOTES.add(note) 
    note.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()