# Save Notes: Independent Guide/Info Window
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Updated text layout to match Footer-Menu migration and Drag/Drop features. Fixed button typography.

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

class GuideCloseButton(QPushButton):
    """Standalone CSS close button to prevent circular imports and bypass QPainter deadlocks."""
    def __init__(self):
        # Using a naturally thicker cross glyph, reinforced by bold CSS
        super().__init__("✖")
        self.setFixedSize(28, 24)
        
        # Pure CSS styling for absolute stability
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                border-radius: 4px;
                color: #FFFFFF;
                font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
                font-size: 13px;
                font-weight: 900;
            }
            QPushButton:hover {
                background-color: #E81123;
            }
        """)

class InfoDialog(QDialog):
    """A sleek, custom-built documentation panel that bypasses native OS deadlock bugs."""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        # Bumped height to perfectly fit the new footer layout
        self.setFixedSize(360, 340) 
        
        # Premium Dark Mode Aesthetic 
        self.setStyleSheet("QDialog { background-color: #252526; border: 1px solid #3E3E42; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header: Title and Close Button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("SnapNote Power-User Guide")
        title.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; font-family: 'Segoe UI', sans-serif;")
        
        self.btn_close = GuideCloseButton()
        self.btn_close.clicked.connect(self.close)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_close)

        # Content: Rich Text Guide
        content = QLabel()
        
        # UI Polish: Web-safe font stack ensures perfect rendering across Windows and Ubuntu
        icon_css = "font-family: 'Segoe UI', 'Helvetica Neue', sans-serif; font-size: 15px; font-weight: bold; color: #569CD6; vertical-align: middle;"
        
        content.setText(
            f"<b style='color:#4EC9B0;'>Header Controls:</b><br>"
            f"&nbsp;&nbsp;<span style=\"{icon_css}\">＋</span> : Spawn a new note<br>"
            f"&nbsp;&nbsp;<span style=\"{icon_css}\">✎</span> : Edit note title<br>"
            f"&nbsp;&nbsp;<span style=\"{icon_css}\">▴</span> : Left-Click Roll-up, Right-Click Min<br>"
            f"&nbsp;&nbsp;<span style=\"{icon_css}\">✖</span> : Close note<br><br>"
            f"<b style='color:#4EC9B0;'>Interactions:</b><br>"
            f"&nbsp;&nbsp;<b>Drag Header</b> : Click empty space to move note<br>"
            f"&nbsp;&nbsp;<b>Bottom-Right Corner</b> : Drag to resize note<br>"
            f"&nbsp;&nbsp;<b>Drag & Drop</b> : Drop a file/folder to paste its path<br><br>"
            f"<b style='color:#4EC9B0;'>Footer Tools:</b><br>"
            f"&nbsp;&nbsp;<span style=\"{icon_css}\">B I U S</span> : Format text<br>"
            f"&nbsp;&nbsp;<span style=\"{icon_css}\">L</span> : Toggle Checklist<br>"
            f"&nbsp;&nbsp;<span style=\"{icon_css}\">◑</span> : Change note theme<br>"
            f"&nbsp;&nbsp;<span style=\"{icon_css}\">≡</span> : Show this guide"
        )
        content.setStyleSheet("color: #D4D4D4; font-size: 13px; font-family: 'Segoe UI', sans-serif; line-height: 1.5;")
        
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