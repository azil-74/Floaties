from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtGui import QPixmap

GUMROAD_URL = "https://therealazil.gumroad.com/l/vdsqh"

UPI_URL = "" 

class SupportDialog(QDialog):
    """Sleek dialog offering dual-gateway donation routes."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(360)
        self.setStyleSheet("""
            QDialog { background: transparent; }
            QFrame#BaseFrame { background-color: #1E1E1E; border: 1px solid #333333; border-radius: 12px; }
            QLabel { font-family: 'Segoe UI', system-ui; }
        """)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)
        
        self.base_frame = QFrame(self)
        self.base_frame.setObjectName("BaseFrame")
        self.base_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        outer_layout.addWidget(self.base_frame)
        
        main_layout = QVBoxLayout(self.base_frame)
        main_layout.setContentsMargins(15, 10, 15, 25) 
        main_layout.setSpacing(0)
        
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.addStretch()
        
        btn_close_x = QPushButton("✕")
        btn_close_x.setFixedSize(26, 26)
        btn_close_x.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close_x.setStyleSheet("""
            QPushButton { background: transparent; color: #666666; border: none; font-size: 14px; font-weight: bold; }
            QPushButton:hover { color: #FF453A; }
        """)
        btn_close_x.clicked.connect(self.reject)
        top_bar.addWidget(btn_close_x)
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(15, 0, 15, 0)
        content_layout.setSpacing(14)
        
        title = QLabel("Support Floaties")
        title.setStyleSheet("color: #06B6D4; font-size: 19px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        desc = QLabel(
            "Floaties is 100% free, private, and built by a solo developer. "
            "If this app helps keep your daily life organized, a small tip helps keep "
            "the lights on for future updates! ☕🚀"
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 13px; color: #D1D5DB; line-height: 1.4;")

        btn_gumroad = QPushButton("🌍 International (Gumroad)")
        btn_gumroad.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_gumroad.setMinimumHeight(44)
        btn_gumroad.setStyleSheet("""
            QPushButton { background: #F1C40F; color: #1A1A1A; border: none; border-radius: 6px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background: #F39C12; }
        """)
        btn_gumroad.clicked.connect(lambda: self._open_link(GUMROAD_URL))

        btn_upi = QPushButton("🇮🇳 India (UPI)")
        btn_upi.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_upi.setMinimumHeight(44)
        btn_upi.setStyleSheet("""
            QPushButton { background: transparent; color: #F1C40F; border: 1px solid #F1C40F; border-radius: 6px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background: rgba(241, 196, 15, 0.1); }
        """)
        btn_upi.clicked.connect(self._show_qr)

        content_layout.addWidget(title)
        content_layout.addWidget(desc)
        content_layout.addSpacing(4)
        content_layout.addWidget(btn_gumroad)
        content_layout.addWidget(btn_upi)

        main_layout.addLayout(top_bar)
        main_layout.addLayout(content_layout)
        
    def _open_link(self, url_string: str) -> None:
        import webbrowser
        webbrowser.open(url_string) 
        self.accept()
    
    def _show_qr(self) -> None:
        self.accept()
        qr_dialog = UPIDialog(self.parentWidget())
        qr_dialog.exec()


class UPIDialog(QDialog):
    """Displays the static UPI QR code for desktop scanning."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 380)
        
        self.setStyleSheet("""
            QDialog { background: transparent; }
            QFrame#BaseFrame { background-color: #1E1E1E; border: 1px solid #333333; border-radius: 12px; }
            QLabel { font-family: 'Segoe UI', system-ui; }
        """)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.base_frame = QFrame(self)
        self.base_frame.setObjectName("BaseFrame")
        self.base_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        outer_layout.addWidget(self.base_frame)
        
        layout = QVBoxLayout(self.base_frame)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Scan to Support")
        title.setStyleSheet("color: #F1C40F; font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        desc = QLabel("Open GPay, PhonePe, or Paytm on your phone and scan this code.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 12px; color: #E0E0E0; margin-bottom: 15px;")

        from pathlib import Path
        qr_path = str(Path(__file__).parent.parent / "assets" / "upi_qr.png")
        
        lbl_qr = QLabel()
        lbl_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        pixmap = QPixmap(qr_path)
        if not pixmap.isNull():
            lbl_qr.setPixmap(pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            lbl_qr.setText("[QR Code Missing]")
            lbl_qr.setStyleSheet("color: #FF453A;")

        btn_close = QPushButton("Done")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setMinimumHeight(34)
        btn_close.setStyleSheet("""
            QPushButton { background: #3A3A3C; color: #FFFFFF; border: none; border-radius: 6px; font-weight: bold; font-size: 12px; margin-top: 15px;}
            QPushButton:hover { background: #4A4A4C; }
        """)
        btn_close.clicked.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(lbl_qr)
        layout.addWidget(btn_close)