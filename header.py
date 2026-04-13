# Save Notes: Drag Header with Injected UI Modules
# Target: Windows (Dev) -> Ubuntu (Prod)
# Dependencies: PyQt6

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QMainWindow
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent

# Import our new distinct modules
from controls import WindowControls
from spawner import SpawnButton

class DragHeader(QFrame):
    """Modular header acting as the drag zone and UI container."""
    def __init__(self, parent_window: QMainWindow) -> None:
        super().__init__()
        self.setObjectName("DragHeader") # Scope ID to prevent CSS leaking to buttons
        self._parent_window = parent_window 
        self._drag_pos = QPoint()
        self.setFixedHeight(24)

        # Assemble the modular layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(4)

        # Inject the modules
        self.btn_new = SpawnButton(self._parent_window)
        self.window_controls = WindowControls(self._parent_window)

        layout.addWidget(self.btn_new)
        layout.addStretch() # Pushes window controls completely to the right
        layout.addWidget(self.window_controls)

    def set_theme(self, bg_hex: str, border_hex: str, text_hex: str) -> None:
        """Dynamically updates header and cascades theme to injected modules."""
        self.setStyleSheet(f"#DragHeader {{ background-color: {bg_hex}; border-bottom: 1px solid {border_hex}; }}")
        self.btn_new.set_theme(text_hex)
        self.window_controls.set_theme(text_hex)

    # --- Manual Drag Interface ---
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self._parent_window.move(self._parent_window.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()