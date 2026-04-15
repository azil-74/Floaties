# Floaties Onboarding Experience
# Action: Implemented a professional, slide-based intro to justify the "Security-First" architecture.

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QStackedWidget, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap
from ui.utils import load_colored_svg

class OnboardingDialog(QDialog):
    """A professional walkthrough to hook users and explain the value of Floaties' security."""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(420, 480)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; border: 1px solid #333333; border-radius: 12px; }
            QLabel { font-family: 'Segoe UI', system-ui; color: #E0E0E0; }
            
            /* Action: Removed font-weight: bold for a sleeker aesthetic */
            QPushButton { background: #F1C40F; color: #1A1A1A; border: none; padding: 10px 20px; border-radius: 8px; font-size: 14px; }
            QPushButton:hover { background: #D4AC0D; }
            
            /* Specific styling for the secondary Back button */
            QPushButton#BackButton { background: transparent; color: #A0A0A0; border: 1px solid #3A3A3C; }
            QPushButton#BackButton:hover { background: #2A2A2C; color: #FFFFFF; }
        """)
        
        layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        
        # Build Slides
        self.stack.addWidget(self._slide_welcome())
        self.stack.addWidget(self._slide_security())
        self.stack.addWidget(self._slide_privacy())
        
        layout.addWidget(self.stack)
        
        # Navigation Row
        nav_layout = QHBoxLayout()
        
        self.btn_back = QPushButton("← Back")
        self.btn_back.setObjectName("BackButton")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.clicked.connect(self._handle_back)
        self.btn_back.hide() # Hidden on the first slide
        
        self.btn_next = QPushButton("Next →")
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.clicked.connect(self._handle_next)
        
        # Action: Squeeze the buttons between two stretches to perfectly center them
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_back)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(self.btn_next)
        nav_layout.addStretch()
        
        layout.addLayout(nav_layout)

    def _slide_welcome(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo placeholder
        from pathlib import Path
        logo_path = str(Path(__file__).parent.parent / "assets" / "Floaties.png")
        logo = QLabel()
        pix = QPixmap(logo_path)
        if not pix.isNull():
            logo.setPixmap(pix.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        title = QLabel("Welcome to Floaties")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF; margin-top: 20px;")
        
        desc = QLabel("The minimalist sticky note app designed to stay out of your way and keep your ideas in sight.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 14px; color: #A0A0A0; margin-top: 10px;")
        
        l.addStretch()
        l.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        l.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        l.addWidget(desc, alignment=Qt.AlignmentFlag.AlignCenter)
        l.addStretch()
        return w

    def _slide_security(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Action: Create a horizontal layout to hold the title and the SVG side-by-side
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("Give your ideas a private sky.")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #F1C40F;")
        
        icon = QLabel()
        from ui.utils import load_colored_svg
        # Scaled down to 24x24 to perfectly match the height of the 22px font
        icon.setPixmap(load_colored_svg("lock.svg", "#F1C40F").pixmap(24, 24)) 
        
        title_layout.addWidget(title)
        title_layout.addSpacing(8)
        title_layout.addWidget(icon)
        
        desc = QLabel(
            "<b>Notes for your eyes only. Literally.</b><br><br>"
            "Why let your OS, background processes, or hidden scrapers see what you’re thinking? "
            "Floaties is a professional-grade safe-house for your fleeting thoughts. "
            "It’s as fast as a spark, but as secure as a vault-shielding your "
            "ideas from the prying eyes of other installed software."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 14px; color: #E0E0E0; margin-top: 15px; line-height: 1.4;")
        
        l.addStretch()
        l.addLayout(title_layout)
        l.addWidget(desc, alignment=Qt.AlignmentFlag.AlignCenter)
        l.addStretch()
        return w

    def _slide_privacy(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("100% Private & Offline")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFFFFF;")
        
        desc = QLabel(
            "There are no servers, no tracking, and no cloud syncing. Your data never leaves "
            "this device. You hold the master key-make sure it's a strong one."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 14px; color: #A0A0A0;")
        
        l.addStretch()
        l.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        l.addWidget(desc, alignment=Qt.AlignmentFlag.AlignCenter)
        l.addStretch()
        return w

    def _update_nav_state(self):
        """Dynamically updates button text and visibility based on the slide index."""
        current = self.stack.currentIndex()
        self.btn_back.setVisible(current > 0)
        
        if current == self.stack.count() - 1:
            self.btn_next.setText("Set Master Password")
        else:
            self.btn_next.setText("Next →")

    def _handle_next(self):
        current = self.stack.currentIndex()
        if current < self.stack.count() - 1:
            self.stack.setCurrentIndex(current + 1)
            self._update_nav_state()
        else:
            self.accept()

    def _handle_back(self):
        current = self.stack.currentIndex()
        if current > 0:
            self.stack.setCurrentIndex(current - 1)
            self._update_nav_state()