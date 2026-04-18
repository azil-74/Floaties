from PyQt6.QtWidgets import QFrame, QHBoxLayout, QMainWindow, QLineEdit, QLabel, QPushButton
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QMouseEvent

from ui.controls import WindowControls
from ui.spawner import SpawnButton
from ui.utils import load_colored_svg

class EditButton(QPushButton):
    def __init__(self):
        super().__init__()
        
        self.setFixedSize(22, 22) 
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_theme(self, text_hex: str) -> None:
        self.setIcon(load_colored_svg("edit.svg", text_hex))
        
        from PyQt6.QtCore import QSize
        self.setIconSize(QSize(12, 12)) 
        
        self.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.08);
                border-radius: 4px;
            }}
        """)


class DragHeader(QFrame):
    title_changed = pyqtSignal(str)

    def __init__(self, parent_window: QMainWindow) -> None:
        super().__init__()
        self.setObjectName("DragHeader")
        self._parent_window = parent_window 
        self._drag_pos = QPoint()
        self.setFixedHeight(24)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(4)

        self.btn_new = SpawnButton(self._parent_window)
        self.window_controls = WindowControls(self._parent_window)

        self.title_label = QLabel("Untitled")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.btn_edit = EditButton()
        self.btn_edit.clicked.connect(self._enable_editing)

        self.title_editor = QLineEdit()
        self.title_editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_editor.setMaxLength(64)
        self.title_editor.setVisible(False)
        self.title_editor.editingFinished.connect(self._on_title_edited)

        layout.addWidget(self.btn_new)
        layout.addStretch() 
        layout.addWidget(self.title_label)
        layout.addWidget(self.title_editor)
        layout.addWidget(self.btn_edit)
        layout.addStretch() 
        layout.addWidget(self.window_controls)

    def set_theme(self, bg_hex: str, border_hex: str, text_hex: str) -> None:
        self.setStyleSheet(f"""
            #DragHeader {{ 
                background-color: {bg_hex}; 
                border-bottom: 1px solid {border_hex}; 
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
        """)
        
        common_font = f"color: {text_hex}; font-family: 'Segoe UI', 'Helvetica Neue', sans-serif; font-weight: bold; font-size: 12px;"
        self.title_label.setStyleSheet(common_font)
        self.title_editor.setStyleSheet(f"QLineEdit {{ background: transparent; border: none; {common_font} }}")
        
        self.btn_new.set_theme(text_hex)
        self.btn_edit.set_theme(text_hex)
        self.window_controls.set_theme(text_hex)

    def _enable_editing(self) -> None:
        """Swaps the UI from Display Mode to Edit Mode."""
        self.title_label.setVisible(False)
        self.btn_edit.setVisible(False)
        
        self.title_editor.setText(self.title_label.text())
        self.title_editor.setVisible(True)
        self.title_editor.setFocus()
        self.title_editor.selectAll()

    def _on_title_edited(self) -> None:
        """Saves the title and swaps the UI back to Display Mode."""
        raw_text = self.title_editor.text().strip()
        if not raw_text:
            raw_text = "Untitled Note"
            
        self.title_label.setText(raw_text)
        self.title_changed.emit(raw_text)
        
        self.title_editor.setVisible(False)
        self.title_label.setVisible(True)
        self.btn_edit.setVisible(True)

    def mousePressEvent(self, event):
        """Enable dragging via Native System Compositor (Wayland/X11 Safe)"""
        if event.button() == Qt.MouseButton.LeftButton:
            window_handle = self._parent_window.windowHandle()
            if window_handle:
                window_handle.startSystemMove()
            event.accept()

    def mouseMoveEvent(self, event):
        """Delegated to startSystemMove()"""
        pass