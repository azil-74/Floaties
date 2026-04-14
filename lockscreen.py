# Save Notes: Dedicated Authentication & Onboarding Flow
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Implemented QStackedWidget for seamless UX and One-Time Recovery Key mechanics.

import secrets
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, 
    QPushButton, QStackedWidget, QWidget, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from database import DatabaseManager
from security import Vault

class AuthFlowDialog(QDialog):
    """Handles Onboarding, Authentication, and Vault Recovery via a stacked UI."""
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.password: str | None = None
        self.salt: bytes | None = self.db.get_meta("salt")
        self.is_setup = self.salt is None
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(380, 240)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; border: 1px solid #3E3E42; border-radius: 8px; }
            QLabel { font-family: 'Segoe UI'; color: #D4D4D4; }
            QLineEdit { background: #2D2D30; color: #FFF; border: 1px solid #3E3E42; padding: 8px; border-radius: 4px; font-family: 'Segoe UI';}
            QLineEdit:focus { border: 1px solid #007ACC; }
            QPushButton { background: #007ACC; color: #FFF; border: none; padding: 8px; border-radius: 4px; font-weight: bold; font-family: 'Segoe UI';}
            QPushButton:hover { background: #0098FF; }
            QPushButton:disabled { background: #3E3E42; color: #888; }
        """)
        
        layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # Build the Views
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

    # --- View Builders ---
    def _build_setup_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        
        title = QLabel("Initialize Offline Brain")
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold;")
        
        desc = QLabel("Welcome. Please create a permanent Master Password to encrypt your vault. This cannot be changed later.")
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 12px; color: #9CDCFE;")
        
        self.inp_setup_pwd = QLineEdit()
        self.inp_setup_pwd.setPlaceholderText("Enter Master Password...")
        self.inp_setup_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_setup_pwd.returnPressed.connect(self._process_setup)
        
        self.btn_setup = QPushButton("Initialize Vault")
        self.btn_setup.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_setup.clicked.connect(self._process_setup)
        
        l.addWidget(title)
        l.addWidget(desc)
        l.addStretch()
        l.addWidget(self.inp_setup_pwd)
        l.addWidget(self.btn_setup)
        return w

    def _build_login_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        
        title = QLabel("Unlock Offline Brain")
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold;")
        
        self.inp_login_pwd = QLineEdit()
        self.inp_login_pwd.setPlaceholderText("Master Password")
        self.inp_login_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_login_pwd.returnPressed.connect(self._process_login)
        
        self.lbl_login_err = QLabel("")
        self.lbl_login_err.setStyleSheet("color: #F44336; font-size: 12px;")
        
        self.btn_login = QPushButton("Unlock")
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.clicked.connect(self._process_login)
        
        btn_forgot = QPushButton("Forgot Password? Use Recovery Key")
        btn_forgot.setStyleSheet("background: transparent; color: #007ACC; font-weight: normal; text-decoration: underline;")
        btn_forgot.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_forgot.clicked.connect(lambda: self.stack.setCurrentWidget(self.view_recovery))
        
        l.addWidget(title)
        l.addStretch()
        l.addWidget(self.inp_login_pwd)
        l.addWidget(self.lbl_login_err)
        l.addWidget(self.btn_login)
        l.addWidget(btn_forgot)
        return w

    def _build_reveal_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        
        title = QLabel("Emergency Recovery Key")
        title.setStyleSheet("color: #F1C40F; font-size: 16px; font-weight: bold;")
        
        desc = QLabel("Write this down and store it safely. This is a single-use key that can recover your Master Password if you forget it.")
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 12px;")
        
        self.lbl_reveal_key = QLineEdit()
        self.lbl_reveal_key.setReadOnly(True)
        self.lbl_reveal_key.setStyleSheet("background: #252526; color: #4EC9B0; font-size: 16px; font-weight: bold; text-align: center;")
        
        self.btn_reveal_ack = QPushButton("I have saved this safely")
        self.btn_reveal_ack.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reveal_ack.clicked.connect(self.accept)
        
        l.addWidget(title)
        l.addWidget(desc)
        l.addStretch()
        l.addWidget(self.lbl_reveal_key)
        l.addWidget(self.btn_reveal_ack)
        return w

    def _build_recovery_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        
        title = QLabel("Vault Recovery")
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold;")
        
        self.inp_rec_key = QLineEdit()
        self.inp_rec_key.setPlaceholderText("Enter FS-XXXX-XXXX")
        self.inp_rec_key.returnPressed.connect(self._process_recovery)
        
        self.lbl_rec_err = QLabel("")
        self.lbl_rec_err.setStyleSheet("color: #F44336; font-size: 12px;")
        
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background: #3E3E42;")
        btn_cancel.clicked.connect(lambda: self.stack.setCurrentWidget(self.view_login))
        
        self.btn_recover = QPushButton("Recover Password")
        self.btn_recover.clicked.connect(self._process_recovery)
        
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self.btn_recover)
        
        l.addWidget(title)
        l.addStretch()
        l.addWidget(self.inp_rec_key)
        l.addWidget(self.lbl_rec_err)
        l.addLayout(btn_row)
        return w

    # --- Core Logic ---
    def _generate_recovery_key(self, master_pwd: str) -> str:
        """Generates a new recovery key, encrypts the master password, and returns the raw key."""
        raw_key = f"FS-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
        rec_salt = Vault.generate_salt()
        
        # Encrypt the Master Password using the Recovery Key
        encrypted_pwd = Vault.encrypt(master_pwd, raw_key, rec_salt)
        
        self.db.set_meta("recovery_salt", rec_salt)
        self.db.set_meta("rec_enc_pwd", encrypted_pwd)
        return raw_key

    def _process_setup(self) -> None:
        pwd = self.inp_setup_pwd.text().strip()
        if len(pwd) < 4:
            return 
            
        # Instantly lock UI to prevent double-click queues
        self.btn_setup.setEnabled(False)
        self.inp_setup_pwd.setEnabled(False)
        self.btn_setup.setText("Generating Vault Keys (This takes a moment)...")
        
        # Yield to OS event loop so the button visually updates, THEN run crypto
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
        
        # Instantly lock UI
        self.btn_login.setEnabled(False)
        self.inp_login_pwd.setEnabled(False)
        self.lbl_login_err.setStyleSheet("color: #569CD6;")
        self.lbl_login_err.setText("Decrypting Vault...")
        
        # Yield to OS event loop
        QTimer.singleShot(50, lambda: self._execute_login_crypto(pwd))

    def _execute_login_crypto(self, pwd: str) -> None:
        token = self.db.get_meta("val_token")
        if token is None or self.salt is None:
            self._reset_login("Critical Error: Vault token missing.")
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
                self._reset_login("Vault integrity compromised.")
        except ValueError:
            self._reset_login("Invalid Master Password.")

    def _reset_login(self, err_msg: str) -> None:
        self.lbl_login_err.setStyleSheet("color: #F44336;")
        self.lbl_login_err.setText(err_msg)
        self.inp_login_pwd.clear()
        self.inp_login_pwd.setEnabled(True)
        self.btn_login.setEnabled(True)
        self.inp_login_pwd.setFocus()

    def _process_recovery(self) -> None:
        rec_key = self.inp_rec_key.text().strip().upper()
        if not rec_key: return
        
        self.btn_recover.setEnabled(False)
        self.lbl_rec_err.setStyleSheet("color: #569CD6;")
        self.lbl_rec_err.setText("Attempting Recovery...")
        QApplication.processEvents()
        
        rec_salt = self.db.get_meta("recovery_salt")
        enc_pwd = self.db.get_meta("rec_enc_pwd")
        
        if not rec_salt or not enc_pwd:
            self._reset_recovery("Recovery data corrupted or missing.")
            return
            
        try:
            # Decrypt the original master password using the entered recovery key
            recovered_pwd = Vault.decrypt(enc_pwd, rec_key, rec_salt) # type: ignore
            
            # Success! Immediately rotate the recovery key to prevent reuse.
            new_recovery_key = self._generate_recovery_key(recovered_pwd)
            self.password = recovered_pwd
            
            # Show the newly generated key, and inform them of their Master Password
            self.lbl_reveal_key.setText(new_recovery_key)
            self.stack.setCurrentWidget(self.view_reveal)
            
            # Inject the recovered password into the description for them to note down
            desc_label = self.view_reveal.findChildren(QLabel)[1]
            desc_label.setText(f"SUCCESS! Your Master Password is: <b>{recovered_pwd}</b><br><br>The old recovery key has been securely destroyed. Please save this NEW recovery key:")
            
        except ValueError:
            self._reset_recovery("Invalid or Expired Recovery Key.")

    def _reset_recovery(self, err_msg: str) -> None:
        self.lbl_rec_err.setStyleSheet("color: #F44336;")
        self.lbl_rec_err.setText(err_msg)
        self.inp_rec_key.clear()
        self.btn_recover.setEnabled(True)
        self.inp_rec_key.setFocus()