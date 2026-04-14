# Save Notes: Static Footer Toolbar with WCAG Auto-Contrast
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Integrated the Guide/Menu button from the header.

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QMenu, QGridLayout
)
from PyQt6.QtGui import QTextCharFormat, QFont, QColor, QPainter, QBrush, QTextListFormat
from PyQt6.QtCore import Qt, pyqtSignal, QPoint

# Import the standalone guide window
from ui.guide import InfoDialog

PRESET_THEMES = [
    {"bg": "#FFF2AB", "border": "#D4C37A"}, 
    {"bg": "#FFD9E8", "border": "#D4A8BD"}, 
    {"bg": "#E2F0CB", "border": "#B5CFA3"}, 
    {"bg": "#D4F0F0", "border": "#A8C4C4"}, 
    {"bg": "#E6E6FA", "border": "#BDBDF0"}, 
    {"bg": "#FFE5B4", "border": "#D4B887"}, 
    {"bg": "#2D2D30", "border": "#1E1E1E"}, 
    {"bg": "#1E293B", "border": "#0F172A"}, 
    {"bg": "#3E2723", "border": "#261714"}, 
    {"bg": "#36454F", "border": "#1C2833"}, 
    {"bg": "#2C5F2D", "border": "#1A3C1B"}, 
    {"bg": "#722F37", "border": "#4A1E24"}, 
]

def get_wcag_text_color(hex_bg: str) -> str:
    color = QColor(hex_bg)
    luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
    return "#000000" if luminance > 0.5 else "#FFFFFF"

class ColorSwatchButton(QPushButton):
    def __init__(self, bg_hex: str, border_hex: str) -> None:
        super().__init__()
        self.bg_hex = bg_hex
        self.border_hex = border_hex
        self.setFixedSize(24, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(self.bg_hex)))
        painter.setPen(QColor(self.border_hex))
        painter.drawEllipse(2, 2, 20, 20)
        painter.end()

class FormattingToolbar(QFrame):
    theme_color_changed = pyqtSignal(str, str, str)

    def __init__(self, editor_reference) -> None:
        super().__init__()
        self.editor = editor_reference
        self.setFixedHeight(32) 
        self.setObjectName("FooterToolbar")
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.btn_container = QWidget()
        self.main_layout.addWidget(self.btn_container)
        
        self.btn_layout = QHBoxLayout(self.btn_container)
        self.btn_layout.setContentsMargins(4, 0, 16, 0) 
        self.btn_layout.setSpacing(4)
        
        self._init_ui()

    def set_theme(self, bg_hex: str, border_hex: str, text_hex: str) -> None:
        self.setStyleSheet(f"""
            #FooterToolbar {{ background-color: {bg_hex}; border-top: 1px solid {border_hex}; }}
            QPushButton {{ border: none; padding: 4px; border-radius: 4px; font-weight: bold; background-color: transparent; color: {text_hex}; }}
            QPushButton:hover {{ background-color: rgba(0,0,0,0.1); }}
        """) 

    def _init_ui(self) -> None:
        btn_bold = QPushButton("B")
        btn_bold.clicked.connect(self._toggle_bold)
        
        btn_italic = QPushButton("I")
        btn_italic.setFont(QFont("Segoe UI", -1, -1, italic=True))
        btn_italic.clicked.connect(self._toggle_italic)
        
        btn_under = QPushButton("U")
        btn_under.clicked.connect(self._toggle_underline)
        
        btn_strike = QPushButton("S")
        btn_strike.clicked.connect(self._toggle_strike)

        btn_list = QPushButton("L")
        btn_list.clicked.connect(self._toggle_list)

        # Meta Actions (Right Side)
        self.btn_guide = QPushButton("≡")
        self.btn_guide.setStyleSheet("font-size: 16px; font-weight: normal; font-family: 'Segoe UI', sans-serif;")
        self.btn_guide.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guide.clicked.connect(self._show_info_dialog)

        self.btn_color = QPushButton("◑")
        self.btn_color.setFont(QFont("Segoe UI", 12))
        self.btn_color.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_color_menu()
        self.btn_color.clicked.connect(self._show_color_menu)

        self.btn_layout.addWidget(btn_bold)
        self.btn_layout.addWidget(btn_italic)
        self.btn_layout.addWidget(btn_under)
        self.btn_layout.addWidget(btn_strike)
        self.btn_layout.addWidget(btn_list)
        
        self.btn_layout.addStretch() 
        
        self.btn_layout.addWidget(self.btn_guide)
        self.btn_layout.addWidget(self.btn_color)

    def _build_color_menu(self) -> None:
        self.color_menu = QMenu(self)
        self.color_menu.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.color_menu.setStyleSheet("QMenu { background-color: #FAFAFA; border: 1px solid #DCDCDC; border-radius: 6px; padding: 4px; }")
        
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(4, 4, 4, 4)
        grid_layout.setSpacing(6)

        for i, theme in enumerate(PRESET_THEMES):
            btn = ColorSwatchButton(theme["bg"], theme["border"])
            btn.clicked.connect(lambda checked, t=theme: self._apply_theme(t))
            row, col = divmod(i, 4) 
            grid_layout.addWidget(btn, row, col)

        from PyQt6.QtGui import QAction
        from PyQt6.QtWidgets import QWidgetAction
        
        action = QWidgetAction(self.color_menu)
        action.setDefaultWidget(grid_widget)
        self.color_menu.addAction(action)

    def _show_color_menu(self) -> None:
        pos = self.btn_color.mapToGlobal(QPoint(0, 0))
        self.color_menu.popup(QPoint(pos.x() - 60, pos.y() - 80))

    def _apply_theme(self, theme: dict) -> None:
        self.color_menu.close()
        text_color = get_wcag_text_color(theme["bg"])
        self.theme_color_changed.emit(theme["bg"], theme["border"], text_color)

    def _show_info_dialog(self) -> None:
        if hasattr(self, 'info_window') and self.info_window.isVisible():
            self.info_window.raise_()
            return
        self.info_window = InfoDialog()
        self.info_window.show()

    # --- Robust Text Formatting Logic ---
    def _toggle_bold(self) -> None:
        fmt = self.editor.currentCharFormat()
        weight = QFont.Weight.Bold if fmt.fontWeight() != QFont.Weight.Bold else QFont.Weight.Normal
        fmt.setFontWeight(weight)
        self.editor.mergeCurrentCharFormat(fmt)

    def _toggle_italic(self) -> None:
        fmt = self.editor.currentCharFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        self.editor.mergeCurrentCharFormat(fmt)

    def _toggle_underline(self) -> None:
        fmt = self.editor.currentCharFormat()
        fmt.setFontUnderline(not fmt.fontUnderline())
        self.editor.mergeCurrentCharFormat(fmt)

    def _toggle_strike(self) -> None:
        fmt = self.editor.currentCharFormat()
        fmt.setFontStrikeOut(not fmt.fontStrikeOut())
        self.editor.mergeCurrentCharFormat(fmt)

    def _toggle_list(self) -> None:
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        if cursor.currentList():
            block_format = cursor.blockFormat()
            block_format.setObjectIndex(-1)
            block_format.setIndent(0)
            cursor.setBlockFormat(block_format)
        else:
            list_format = QTextListFormat()
            list_format.setStyle(QTextListFormat.Style.ListDisc)
            cursor.createList(list_format)
        cursor.endEditBlock()
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()