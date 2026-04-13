import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QGridLayout, QWidget, QSizeGrip, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen

# Import our modular ecosystem
from toolbar import FormattingToolbar, PRESET_THEMES, get_wcag_text_color
from header import DragHeader
from spawner import ACTIVE_NOTES # Import global memory tracker

class ModernSizeGrip(QSizeGrip):
    """Custom painted size grip providing a premium, native-looking resize indicator."""
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Subtle 60-alpha black creates a watermark effect visible on any background color
        pen = QPen(QColor(0, 0, 0, 60)) 
        pen.setWidthF(1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        w, h = self.width(), self.height()
        
        # Draw two elegant minimalist diagonal lines
        painter.drawLine(int(w - 6), int(h - 10), int(w - 10), int(h - 6))
        painter.drawLine(int(w - 6), int(h - 16), int(w - 16), int(h - 6))
        
        painter.end()

class StickyNote(QMainWindow):
    """Core Sticky Note Window adhering to Single Responsibility Principle."""
    # theme_index defaults to 0 (Classic Yellow) for the very first app launch
    def __init__(self, theme_index: int = 6) -> None:
        super().__init__()
        self.is_rolled_up = False
        self._normal_height = 150 # Memory variable for un-rolling
        self._initial_theme_index = theme_index
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setMinimumSize(150, 150)
        # CRITICAL FIX: Starting size MUST be larger than MinimumSize to prevent C++ geometry crashes
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

        # Apply the initial default theme to the container to prevent the black background
        self.container.setStyleSheet(f"#NoteContainer {{ background-color: {base_bg}; border: 1px solid {base_border}; }}")

        # 1. Instantiate Header (Logic now handled in header.py)
        self.header = DragHeader(self)
        self.header.set_theme(accent_bg, base_border, base_text)
        
        # 2. Instantiate Text Editor
        self.text_editor = QTextEdit(self.container)
        self.text_editor.setStyleSheet(f"background: transparent; border: none; padding: 8px; font-size: 14px; color: {base_text};")
        self.text_editor.textChanged.connect(self._adjust_height)

        # 3. Instantiate Hover-Footer Toolbar 
        self.toolbar = FormattingToolbar(self.text_editor)
        self.toolbar.theme_color_changed.connect(self._update_theme_color)
        self.toolbar.set_theme(accent_bg, base_border, base_text)

        self.size_grip = ModernSizeGrip(self.container)
        self.size_grip.setStyleSheet("background-color: transparent;")
        self.size_grip.setFixedSize(16, 16)
        self.size_grip.setCursor(Qt.CursorShape.SizeFDiagCursor)

        # --- Modular Layout Construction ---
        # UI Polish: Use QGridLayout to natively anchor the grip without Python math (Zero Crash)
        main_layout = QGridLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self.header, 0, 0)
        main_layout.addWidget(self.text_editor, 1, 0)
        main_layout.addWidget(self.toolbar, 2, 0) 
        
        # Anchor the grip to the exact same cell as the toolbar (bottom-right)
        main_layout.addWidget(self.size_grip, 2, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        
        # CRITICAL: Force the grip to the absolute top of the visual stack so it remains clickable!
        self.size_grip.raise_()
        
    # NOTE: resizeEvent is completely deleted to permanently kill the event feedback loop!

    # --- Core Window State Methods ---
    
    def toggle_rollup(self) -> None:
        """Soft-minimizes the window to just the header."""
        if not self.is_rolled_up:
            self._normal_height = self.height()
            self.text_editor.setVisible(False)
            self.toolbar.setVisible(False)
            self.size_grip.setVisible(False)
            self.is_rolled_up = True
            
            # Temporarily drop the minimum height constraint so the window can shrink
            self.setMinimumSize(150, self.header.height())
            self.resize(self.width(), self.header.height())
        else:
            self.text_editor.setVisible(True)
            self.toolbar.setVisible(True)
            self.size_grip.setVisible(True)
            self.is_rolled_up = False
            
            # Restore the original minimum height constraint to protect the layout
            self.setMinimumSize(150, 150)
            self.resize(self.width(), self._normal_height)
            
        # Update the icon inside the modular controls
        self.header.window_controls.update_rollup_icon(self.is_rolled_up)

    def closeEvent(self, event) -> None:
        """Hooks into the native close event to ensure garbage collection memory safety."""
        ACTIVE_NOTES.discard(self)
        super().closeEvent(event)

    def _adjust_height(self) -> None:
        document = self.text_editor.document()
        if document is None: return 
            
        doc_height = int(document.size().height())
        target_height = doc_height + self.header.height() + self.toolbar.height() + 16 
        
        if target_height > self.height() and not self.is_rolled_up:
            max_allowed_height = 800 
            self.resize(self.width(), min(target_height, max_allowed_height))

    def _update_theme_color(self, bg_hex: str, border_hex: str, text_hex: str) -> None:
        self.container.setStyleSheet(f"#NoteContainer {{ background-color: {bg_hex}; border: 1px solid {border_hex}; }}")
        accent_bg = QColor(bg_hex).darker(115).name()
        
        self.header.set_theme(accent_bg, border_hex, text_hex)
        self.toolbar.set_theme(accent_bg, border_hex, text_hex)
        self.text_editor.setStyleSheet(f"background: transparent; border: none; padding: 8px; font-size: 14px; color: {text_hex};")

def main() -> None:
    app = QApplication(sys.argv)
    note = StickyNote()
    ACTIVE_NOTES.add(note) # Register the very first boot note
    note.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()