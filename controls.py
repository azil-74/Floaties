# Save Notes: Window State Controls (Close, Combined Minimize)
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Stripped red background hover bug. Outsourced info dialog to guide.py.

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QMainWindow
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, pyqtSignal

# Import the standalone guide window
from guide import InfoDialog

class ModernButton(QPushButton):
    """Custom pixel-perfect painted icons with right-click detection."""
    rightClicked = pyqtSignal()

    def __init__(self, icon_type: str):
        super().__init__()
        self.icon_type = icon_type
        self.setFixedSize(28, 24)
        self.icon_color = QColor("#000000")
        self.is_close = (icon_type == "close")
        self._hovered = False

    def set_icon_color(self, hex_color: str):
        self.icon_color = QColor(hex_color)
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit()
        elif event.button() == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        # FIX: Do NOT call super().paintEvent() here.
        # Qt's internal painter from super() + our QPainter = two painters on one device.
        # This is tolerated on Windows but crashes on Linux/Ubuntu. We own the full paint cycle.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Manually replicate the CSS :hover background (since we skip super, stylesheet won't render)
        # Close button keeps the subtle bg even on hover — red is shown via icon color change below
        if self._hovered:
            painter.setBrush(QColor(0, 0, 0, 20))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 4, 4)
        
        # UI Polish: Changes the stroke itself to red, rather than drawing a bulky background box
        current_color = QColor("#E81123") if (self._hovered and self.is_close) else self.icon_color
        
        pen = QPen(current_color)
        pen.setWidthF(1.5) 
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin) 
        painter.setPen(pen)

        cx, cy = self.width() // 2, self.height() // 2
        r = 4
        
        if self.icon_type == "close":
            painter.drawLine(cx - r, cy - r, cx + r, cy + r)
            painter.drawLine(cx + r, cy - r, cx - r, cy + r)
        elif self.icon_type == "min":
            painter.drawLine(cx - r, cy + 4, cx + r, cy + 4)
        elif self.icon_type == "rollup":
            painter.drawLine(cx - r, cy + 2, cx, cy - 3)
            painter.drawLine(cx, cy - 3, cx + r, cy + 2)
        elif self.icon_type == "rolldown":
            painter.drawLine(cx - r, cy - 3, cx, cy + 2)
            painter.drawLine(cx, cy + 2, cx + r, cy - 3)
        elif self.icon_type == "menu":
            painter.drawLine(cx - r, cy - 3, cx + r, cy - 3)
            painter.drawLine(cx - r, cy, cx + r, cy)
            painter.drawLine(cx - r, cy + 3, cx + r, cy + 3)
            
        painter.end()

class WindowControls(QWidget):
    def __init__(self, parent_window: QMainWindow) -> None:
        super().__init__()
        self.parent_window = parent_window
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.btn_info = ModernButton("menu")
        self.btn_info.clicked.connect(self.show_info_dialog)

        self.btn_min_combined = ModernButton("rollup")
        self.btn_min_combined.clicked.connect(self.parent_window.toggle_rollup) # type: ignore
        self.btn_min_combined.rightClicked.connect(self.parent_window.showMinimized)

        self.btn_close = ModernButton("close")
        self.btn_close.clicked.connect(self.parent_window.close)

        layout.addWidget(self.btn_info)
        layout.addWidget(self.btn_min_combined)
        layout.addWidget(self.btn_close)

    def set_theme(self, text_hex: str) -> None:
        self.btn_info.set_icon_color(text_hex)
        self.btn_min_combined.set_icon_color(text_hex)
        self.btn_close.set_icon_color(text_hex)
        
        # UI Polish: Only the subtle dark grey hover background remains. The red hover is handled by the QPainter.
        btn_css = """
            QPushButton { border: none; background: transparent; border-radius: 4px; }
            QPushButton:hover { background-color: rgba(0, 0, 0, 0.08); }
        """
        self.btn_info.setStyleSheet(btn_css)
        self.btn_min_combined.setStyleSheet(btn_css)
        self.btn_close.setStyleSheet(btn_css)
        
    def update_rollup_icon(self, is_rolled_up: bool) -> None:
        self.btn_min_combined.icon_type = "rolldown" if is_rolled_up else "rollup"
        self.btn_min_combined.update()
        
    def show_info_dialog(self) -> None:
        if hasattr(self, 'info_window') and self.info_window.isVisible():
            self.info_window.raise_()
            return
            
        self.info_window = InfoDialog()
        self.info_window.show()