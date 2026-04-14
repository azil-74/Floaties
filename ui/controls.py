# Save Notes: Window State Controls (SVG Edition)
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Replaced Unicode text with dynamic SVG injection. Added Size Experimentation zones.

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QMainWindow
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from ui.utils import load_colored_svg

class ModernButton(QPushButton):
    rightClicked = pyqtSignal()

    def __init__(self, icon_type: str):
        super().__init__()
        self.icon_type = icon_type
        
        # --- SIZE EXPERIMENTATION (CONTAINER) ---
        # Adjust these numbers to change the clickable 'hitbox' of the button.
        self.setFixedSize(28, 24) 
        
        self.is_close = (icon_type == "close")
        self.current_text_hex = "#000000"

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit()
        elif event.button() == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        # Native OS feel: Turn the 'X' white when hovering over the red close button
        if self.is_close:
            self.setIcon(load_colored_svg("close.svg", "#FFFFFF"))
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Revert back to the theme's text color when the mouse leaves
        if self.is_close:
            self.setIcon(load_colored_svg("close.svg", self.current_text_hex))
        super().leaveEvent(event)

    def set_theme(self, text_hex: str) -> None:
        self.current_text_hex = text_hex
        
        # Determine which SVG to load
        svg_file = "close.svg" if self.is_close else "minimize.svg"
        self.setIcon(load_colored_svg(svg_file, text_hex))
        
        # --- SIZE EXPERIMENTATION (ICON) ---
        # Adjust these numbers to change the scale of the drawn SVG inside the button.
        # Ensure it is slightly smaller than the Container size above.
        self.setIconSize(QSize(12, 12) if self.is_close else QSize(14, 14))
        
        hover_bg = "#E81123" if self.is_close else "rgba(0, 0, 0, 0.08)"
        
        self.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
        """)

class WindowControls(QWidget):
    def __init__(self, parent_window: QMainWindow) -> None:
        super().__init__()
        self.parent_window = parent_window
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.btn_min_combined = ModernButton("rollup")
        self.btn_min_combined.clicked.connect(self.parent_window.toggle_rollup) # type: ignore
        self.btn_min_combined.rightClicked.connect(self.parent_window.showMinimized)

        self.btn_close = ModernButton("close")
        self.btn_close.clicked.connect(self.parent_window.close)

        layout.addWidget(self.btn_min_combined)
        layout.addWidget(self.btn_close)

    def set_theme(self, text_hex: str) -> None:
        self.btn_min_combined.set_theme(text_hex)
        self.btn_close.set_theme(text_hex)
        
    def update_rollup_icon(self, is_rolled_up: bool) -> None:
        # With a minimalist SVG dash for minimize/rollup, we no longer need to flip text arrows.
        pass