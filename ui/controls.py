# Save Notes: Window State Controls
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Migrated Hamburger Menu to Footer to resolve header congestion.

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QMainWindow
from PyQt6.QtCore import Qt, pyqtSignal

class ModernButton(QPushButton):
    rightClicked = pyqtSignal()

    def __init__(self, icon_type: str):
        text_map = {
            "close": "✕",
            "rollup": "▴",
            "rolldown": "▾"
        }
        super().__init__(text_map.get(icon_type, ""))
        self.icon_type = icon_type
        self.setFixedSize(28, 24)
        self.is_close = (icon_type == "close")

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit()
        elif event.button() == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)

    def set_theme(self, text_hex: str) -> None:
        hover_bg = "#E81123" if self.is_close else "rgba(0, 0, 0, 0.08)"
        hover_color = "#FFFFFF" if self.is_close else text_hex
        font_size = "12px" if self.is_close else "14px"
        
        self.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                border-radius: 4px;
                color: {text_hex};
                font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
                font-size: {font_size};
                font-weight: normal;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
                color: {hover_color};
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
        self.btn_min_combined.setText("▾" if is_rolled_up else "▴")