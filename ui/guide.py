# Save Notes: Independent Guide/Info Window
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Updated text layout to match Footer-Menu migration and Drag/Drop features. Fixed button typography.

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QSize
from ui.utils import load_colored_svg

class GuideCloseButton(QPushButton):
    """Standalone SVG close button for the guide window."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(28, 24)
        
        # Action: Injecting the SVG directly into the button
        self.setIcon(load_colored_svg("close.svg", "#FFFFFF"))
        self.setIconSize(QSize(10, 10))
        
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                border-radius: 4px;
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
        self.setFixedSize(360, 340) 
        
        self.setStyleSheet("QDialog { background-color: #252526; border: 1px solid #3E3E42; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # ACTION: Updated branding to Floaties
        title = QLabel("Floaties Power-User Guide")
        title.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; font-family: 'Segoe UI', sans-serif;")
        
        self.btn_close = GuideCloseButton()
        self.btn_close.clicked.connect(self.close)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_close)

        content = QLabel()
        
        # --- ELITE TRICK: Dynamic In-Memory SVG to HTML Base64 ---
        def get_svg_html(filename: str, color: str, size: int = 14) -> str:
            from pathlib import Path
            import base64
            filepath = Path(__file__).parent.parent / "assets" / filename
            if not filepath.exists(): return ""
            with open(filepath, 'r', encoding='utf-8') as f:
                svg_data = f.read().replace("#TEXT_COLOR#", color)
            b64 = base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
            return f"<img src='data:image/svg+xml;base64,{b64}' width='{size}' height='{size}' style='vertical-align: middle;'>"

        # Pre-render the HTML image tags for the guide
        img_plus = get_svg_html("plus.svg", "#569CD6", 14)
        img_edit = get_svg_html("edit.svg", "#569CD6", 14)
        img_min = get_svg_html("minimize.svg", "#569CD6", 14)
        # Bumping the render size slightly to ensure visual clarity
        img_close = get_svg_html("close.svg", "#569CD6", 15)

        icon_css = "font-family: 'Segoe UI', 'Helvetica Neue', sans-serif; font-size: 15px; font-weight: bold; color: #569CD6; vertical-align: middle;"
        
        content.setText(
            f"<b style='color:#4EC9B0;'>Header Controls:</b><br>"
            f"&nbsp;&nbsp;{img_plus} : Spawn a new note<br>"
            f"&nbsp;&nbsp;{img_edit} : Edit note title<br>"
            f"&nbsp;&nbsp;{img_min} : Left-Click Roll-up, Right-Click Minimize<br>"
            f"&nbsp;&nbsp;{img_close} : Close note<br><br>"
            f"<b style='color:#4EC9B0;'>Interactions:</b><br>"
            f"&nbsp;&nbsp;<b>Bottom-Right Corner</b> : Drag to resize note<br>"
            f"&nbsp;&nbsp;<b>Drag & Drop file</b> : Drop a file/folder to paste its path<br><br>"
            f"<b style='color:#4EC9B0;'>Footer Tools:</b><br>"
            f"&nbsp;&nbsp;<span style=\"{icon_css}\">B I U S</span> : Format text<br>"
            f"&nbsp;&nbsp;<span style=\"{icon_css}\">L</span> : Toggle Bulleted list<br>"
            f"&nbsp;&nbsp;<span style=\"{icon_css}\">◑</span> : Change note theme<br>"
            f"&nbsp;&nbsp;<span style=\"{icon_css}\">≡</span> : Show this guide (obvious I know lol)"
        )
        content.setStyleSheet("color: #D4D4D4; font-size: 13px; font-family: 'Segoe UI', sans-serif; line-height: 1.5;")
        
        layout.addLayout(header_layout)
        layout.addWidget(content)
        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()