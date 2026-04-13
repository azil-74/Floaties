# Save Notes: Independent Guide/Info Window
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Isolated custom frameless dialog. Fixed icon typography and removed redundant bullets.

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen

class GuideCloseButton(QPushButton):
    """Standalone close button for the guide to prevent circular imports."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(28, 24)
        self._hovered = False

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # UI Polish: Sleek red stroke on hover
        pen = QPen(QColor("#E81123") if self._hovered else QColor("#FFFFFF"))
        pen.setWidthF(1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        cx, cy = self.width() // 2, self.height() // 2
        painter.drawLine(cx - 4, cy - 4, cx + 4, cy + 4)
        painter.drawLine(cx + 4, cy - 4, cx - 4, cy + 4)
        painter.end()

class InfoDialog(QDialog):
    """A sleek, custom-built documentation panel that bypasses native OS deadlock bugs."""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(340, 270)
        
        # Premium Dark Mode Aesthetic 
        self.setStyleSheet("QDialog { background-color: #252526; border: 1px solid #3E3E42; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header: Title and Close Button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("SnapNote Power-User Guide")
        title.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; font-family: 'Segoe UI';")
        
        self.btn_close = GuideCloseButton()
        self.btn_close.clicked.connect(self.close)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_close)

        # Content: Rich Text Guide
        content = QLabel()
        
        # UI Polish: Bumped font-size to 18px and added vertical-align so the '+' doesn't drop its baseline
        icon_css = "font-family: 'Segoe UI Symbol', Consolas, monospace; font-size: 18px; font-weight: bold; color: #569CD6; vertical-align: middle;"
        
        content.setText(
            f"<b style='color:#4EC9B0;'>Header Controls:</b><br>"
            f"&nbsp;&nbsp;<span style=\"{icon_css}\">+</span> : Spawn a new note (cycles themes)<br>"
            f"&nbsp;&nbsp;<span style=\"{icon_css}\">≡</span> : Show this guide<br>"
            f"&nbsp;&nbsp;<span style=\"{icon_css}\">▴</span> : Left-Click Roll-up, Right-Click Minimize<br>"
            f"&nbsp;&nbsp;<span style=\"{icon_css}\">✕</span> : Close note<br><br>"
            f"<b style='color:#4EC9B0;'>Interactions:</b><br>"
            f"&nbsp;&nbsp;<b>Drag Anywhere</b> : Move this guide or a note header<br>"
            f"&nbsp;&nbsp;<b>Bottom-Right</b> &nbsp;: Drag to resize note<br>"
            f"&nbsp;&nbsp;<b>Footer</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: Text formatting & theme selection"
        )
        content.setStyleSheet("color: #D4D4D4; font-size: 13px; font-family: 'Segoe UI'; line-height: 1.5;")
        
        layout.addLayout(header_layout)
        layout.addWidget(content)
        layout.addStretch()

    # --- Allow the user to drag the guide out of the way ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()