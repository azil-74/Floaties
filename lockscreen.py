# Floaties Onboarding & Authentication Flow
# Action: Stripped security jargon. Applied modern, minimalist UI/UX.

import secrets
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, 
    QPushButton, QStackedWidget, QWidget, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from database import DatabaseManager
from security import Vault

class AuthFlowDialog(QDialog):
    """Handles Onboarding, Authentication, and Recovery with a stealth, minimal UI."""
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.password: str | None = None
        self.salt: bytes | None = self.db.get_meta("salt")
        self.is_setup = self.salt is None
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(380, 260)
        
        # Clean, modern, soft-dark UI (macOS / Windows 11 native feel)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; border: 1px solid #333333; border-radius: 10px; }
            QLabel { font-family: 'Segoe UI', system-ui; color: #E0E0E0; }
            QLineEdit { background: #2A2A2C; color: #FFF; border: 1px solid #3A3A3C; padding: 10px; border-radius: 6px; font-family: 'Segoe UI'; font-size: 13px;}
            QLineEdit:focus { border: 1px solid #0A84FF; }
            QPushButton { background: #0A84FF; color: #FFF; border: none; padding: 10px; border-radius: 6px; font-weight: bold; font-family: 'Segoe UI'; font-size: 13px;}
            QPushButton:hover { background: #0070E0; }
            QPushButton:disabled { background: #3A3A3C; color: #888; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        self.view_setup = self._build_setup_view()
        self.view_login = self._build_login_view()
        self.view_reveal = self._build_reveal_view()
        self.view_recovery = self._build_recovery_view()
        
        self.stack.addWidget(self.view_setup)
        self.stack.addWidget(self.view_login)
        self.stack.addWidget(self.view_reveal)
        self.stack.addWidget(self.view_recovery)
        
        if self.is_setup:
            self.stack.setCurrentWidget(self.view_setup)
        else:
            self.stack.setCurrentWidget(self.view_login)

    def _build_setup_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Welcome to Floaties")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #FFFFFF;")
        
        desc = QLabel("Set a password to keep your notes private. This is stored locally and cannot be recovered if lost.")
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 13px; color: #A0A0A0; line-height: 1.4;")
        
        self.inp_setup_pwd = QLineEdit()
        self.inp_setup_pwd.setPlaceholderText("Create a password...")
        self.inp_setup_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_setup_pwd.returnPressed.connect(self._process_setup)
        
        self.btn_setup = QPushButton("Get Started")
        self.btn_setup.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_setup.clicked.connect(self._process_setup)
        
        l.addWidget(title)
        l.addWidget(desc)
        l.addStretch()
        l.addWidget(self.inp_setup_pwd)
        l.addSpacing(4)
        l.addWidget(self.btn_setup)
        return w

    def _build_login_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Welcome Back")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #FFFFFF;")
        
        self.inp_login_pwd = QLineEdit()
        self.inp_login_pwd.setPlaceholderText("Enter password...")
        self.inp_login_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_login_pwd.returnPressed.connect(self._process_login)
        
        self.lbl_login_err = QLabel("")
        self.lbl_login_err.setStyleSheet("color: #FF453A; font-size: 12px;")
        
        self.btn_login = QPushButton("Open Notes")
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.clicked.connect(self._process_login)
        
        # PYLANCE/PYQT FIX: Make it a class variable and disable Enter-key hijacking
        self.btn_forgot = QPushButton("Use a Recovery Code")
        self.btn_forgot.setAutoDefault(False) 
        self.btn_forgot.setStyleSheet("background: transparent; color: #0A84FF; font-weight: normal; font-size: 12px;")
        self.btn_forgot.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_forgot.clicked.connect(lambda: self.stack.setCurrentWidget(self.view_recovery))
        
        l.addWidget(title)
        l.addStretch()
        l.addWidget(self.inp_login_pwd)
        l.addWidget(self.lbl_login_err)
        l.addWidget(self.btn_login)
        l.addWidget(self.btn_forgot)
        return w

    def _build_reveal_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Recovery Code")
        title.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: 600;")
        
        desc = QLabel("Please save this code somewhere safe. It is the only way to restore access if you forget your password.")
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 13px; color: #A0A0A0;")
        
        self.lbl_reveal_key = QLineEdit()
        self.lbl_reveal_key.setReadOnly(True)
        self.lbl_reveal_key.setStyleSheet("background: #2A2A2C; color: #32D74B; font-size: 15px; font-weight: bold; text-align: center; border: 1px solid #3A3A3C;")
        
        self.btn_reveal_ack = QPushButton("I've saved this safely")
        self.btn_reveal_ack.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reveal_ack.clicked.connect(self.accept)
        
        l.addWidget(title)
        l.addWidget(desc)
        l.addStretch()
        l.addWidget(self.lbl_reveal_key)
        l.addSpacing(4)
        l.addWidget(self.btn_reveal_ack)
        return w

    def _build_recovery_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Account Recovery")
        title.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: 600;")
        
        self.inp_rec_key = QLineEdit()
        self.inp_rec_key.setPlaceholderText("Enter FL-XXXX-XXXX")
        self.inp_rec_key.returnPressed.connect(self._process_recovery)
        
        self.lbl_rec_err = QLabel("")
        self.lbl_rec_err.setStyleSheet("color: #FF453A; font-size: 12px;")
        
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background: #3A3A3C; color: #E0E0E0;")
        btn_cancel.clicked.connect(lambda: self.stack.setCurrentWidget(self.view_login))
        
        self.btn_recover = QPushButton("Recover")
        self.btn_recover.clicked.connect(self._process_recovery)
        
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self.btn_recover)
        
        l.addWidget(title)
        l.addStretch()
        l.addWidget(self.inp_rec_key)
        l.addWidget(self.lbl_rec_err)
        l.addLayout(btn_row)
        return w

    def _generate_recovery_key(self, master_pwd: str) -> str:
        # Rebranded the key prefix to FL (Floaties)
        raw_key = f"FL-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
        rec_salt = Vault.generate_salt()
        encrypted_pwd = Vault.encrypt(master_pwd, raw_key, rec_salt)
        self.db.set_meta("recovery_salt", rec_salt)
        self.db.set_meta("rec_enc_pwd", encrypted_pwd)
        return raw_key

    def _process_setup(self) -> None:
        pwd = self.inp_setup_pwd.text().strip()
        if len(pwd) < 4:
            return 
            
        self.btn_setup.setEnabled(False)
        self.inp_setup_pwd.setEnabled(False)
        self.btn_setup.setText("Preparing...")
        QTimer.singleShot(50, lambda: self._execute_setup_crypto(pwd))

    def _execute_setup_crypto(self, pwd: str) -> None:
        self.salt = Vault.generate_salt()
        self.db.set_meta("salt", self.salt)
        token = Vault.encrypt("VALID", pwd, self.salt)
        self.db.set_meta("val_token", token)
        
        recovery_key = self._generate_recovery_key(pwd)
        self.password = pwd
        
        self.lbl_reveal_key.setText(recovery_key)
        self.stack.setCurrentWidget(self.view_reveal)

    def _process_login(self) -> None:
        pwd = self.inp_login_pwd.text().strip()
        if not pwd: return
        
        self.btn_login.setEnabled(False)
        self.inp_login_pwd.setEnabled(False)
        self.btn_forgot.setEnabled(False) # ACTION: Lock this button too!
        
        self.lbl_login_err.setStyleSheet("color: #0A84FF;")
        self.lbl_login_err.setText("Loading...")
        QTimer.singleShot(50, lambda: self._execute_login_crypto(pwd))

    def _execute_login_crypto(self, pwd: str) -> None:
        token = self.db.get_meta("val_token")
        if token is None or self.salt is None:
            self._reset_login("Critical Error: App token missing.")
            return
            
        try:
            res = Vault.decrypt(token, pwd, self.salt) # type: ignore
            if res == "VALID":
                self.password = pwd
                if self.db.get_meta("recovery_salt") is None:
                    recovery_key = self._generate_recovery_key(pwd)
                    self.lbl_reveal_key.setText(recovery_key)
                    self.stack.setCurrentWidget(self.view_reveal)
                else:
                    self.accept()
            else:
                self._reset_login("Data integrity compromised.")
        except ValueError:
            self._reset_login("Incorrect password.")

    def _reset_login(self, err_msg: str) -> None:
        self.lbl_login_err.setStyleSheet("color: #FF453A;")
        self.lbl_login_err.setText(err_msg)
        self.inp_login_pwd.clear()
        
        self.inp_login_pwd.setEnabled(True)
        self.btn_login.setEnabled(True)
        self.btn_forgot.setEnabled(True) # ACTION: Unlock the button
        
        self.inp_login_pwd.setFocus()

    def _process_recovery(self) -> None:
        rec_key = self.inp_rec_key.text().strip().upper()
        if not rec_key: return
        
        self.btn_recover.setEnabled(False)
        self.lbl_rec_err.setStyleSheet("color: #0A84FF;")
        self.lbl_rec_err.setText("Verifying...")
        QApplication.processEvents()
        
        rec_salt = self.db.get_meta("recovery_salt")
        enc_pwd = self.db.get_meta("rec_enc_pwd")
        
        if not rec_salt or not enc_pwd:
            self._reset_recovery("Recovery data corrupted or missing.")
            return
            
        try:
            recovered_pwd = Vault.decrypt(enc_pwd, rec_key, rec_salt) # type: ignore
            new_recovery_key = self._generate_recovery_key(recovered_pwd)
            self.password = recovered_pwd
            
            self.lbl_reveal_key.setText(new_recovery_key)
            self.stack.setCurrentWidget(self.view_reveal)
            
            desc_label = self.view_reveal.findChildren(QLabel)[1]
            desc_label.setText(f"SUCCESS! Your password is: <b>{recovered_pwd}</b><br><br>The old recovery code has been securely destroyed. Please save this NEW code:")
            
        except ValueError:
            self._reset_recovery("Invalid or expired code.")

    def _reset_recovery(self, err_msg: str) -> None:
        self.lbl_rec_err.setStyleSheet("color: #FF453A;")
        self.lbl_rec_err.setText(err_msg)
        self.inp_rec_key.clear()
        self.btn_recover.setEnabled(True)
        self.inp_rec_key.setFocus()