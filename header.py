# Save Notes: Drag Header with Injected UI Modules, seamlessly integrated QLineEdit for dynamic DB-ready titling.
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Implemented Phase 3 titling. Added max length constraint to prevent memory/DB bloat. Added focus clearing on drag.

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QMainWindow, QLineEdit
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QMouseEvent

# Import our new distinct modules
from controls import WindowControls
from spawner import SpawnButton

class DragHeader(QFrame):
    """Modular header acting as the drag zone and UI container."""
    
    # Future-proofing: Signal to decouple DB logic from UI interaction.
    title_changed = pyqtSignal(str)

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
        
        # --- Phase 3: Seamless Titling ---
        self.title_editor = QLineEdit()
        self.title_editor.setPlaceholderText("Untitled Note")
        self.title_editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_editor.setMaxLength(64) # Security/DB constraint: prevent massive payload injection
        
        # Emit signal exclusively on focus loss or return key (optimal DB sync trigger point)
        self.title_editor.editingFinished.connect(self._on_title_edited)

        self.window_controls = WindowControls(self._parent_window)

        layout.addWidget(self.btn_new)
        layout.addWidget(self.title_editor, stretch=1) # Expanding policy pushes controls to the edges
        layout.addWidget(self.window_controls)

    def set_theme(self, bg_hex: str, border_hex: str, text_hex: str) -> None:
        """Dynamically updates header and cascades theme to injected modules."""
        self.setStyleSheet(f"#DragHeader {{ background-color: {bg_hex}; border-bottom: 1px solid {border_hex}; }}")
        
        # Apply transparent, theme-aware styling to the title
        self.title_editor.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {text_hex};
                font-family: 'Segoe UI';
                font-weight: bold;
                font-size: 12px;
            }}
        """)
        
        self.btn_new.set_theme(text_hex)
        self.window_controls.set_theme(text_hex)

    def _on_title_edited(self) -> None:
        """Validates and emits the cleaned title for future DB serialization."""
        raw_text = self.title_editor.text().strip()
        self.title_changed.emit(raw_text)

    # --- Manual Drag Interface ---
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            # UX Polish: Unfocus the title editor if the user clicks the header background
            self.setFocus()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self._parent_window.move(self._parent_window.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()