# Floaties Onboarding & Authentication Flow
# Action: Patched QDialog event loop panics (KeyboardInterrupt) and removed late-binding lambdas.

import secrets
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, 
    QPushButton, QStackedWidget, QWidget, QApplication, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
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
        # Action: Expanded height to 420px to comfortably fit the new fields and spacing
        self.setFixedSize(380, 420)
        
        from pathlib import Path
        self.icon_path = str(Path(__file__).parent.parent / "assets" / "Floaties.png")
        
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; border: 1px solid #333333; border-radius: 12px; }
            QLabel { font-family: 'Segoe UI', system-ui; color: #E0E0E0; }
            QLineEdit { background: #2A2A2C; color: #FFF; border: 1px solid #3A3A3C; padding: 10px; border-radius: 6px; font-size: 13px;}
            QLineEdit:focus { border: 1px solid #F1C40F; }
            QPushButton { background: #F1C40F; color: #1A1A1A; border: none; padding: 10px; border-radius: 6px; font-weight: bold; font-size: 13px;}
            QPushButton:hover { background: #D4AC0D; }
            QPushButton:disabled { background: #3A3A3C; color: #888; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
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
        
        self.stack.setCurrentWidget(self.view_setup if self.is_setup else self.view_login)

    # --- View Navigation Helpers (Fixes Lambda crash) ---
    def _nav_to_recovery(self):
        self.stack.setCurrentWidget(self.view_recovery)
        
    def _nav_to_login(self):
        self.stack.setCurrentWidget(self.view_login)

    def _get_logo_header(self) -> QWidget:
        header = QWidget()
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 10)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo = QLabel()
        pixmap = QPixmap(self.icon_path)
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        h_layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("Floaties")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; margin-top: 5px;")
        h_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        return header

    def _build_setup_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(12) # Add consistent breathing room between all elements
        
        l.addWidget(self._get_logo_header())
        
        desc = QLabel("Create your Master Password.")
        desc.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        helper_text = QLabel(
            "This password permanently encrypts Floaties' local database. "
            "Do not forget it as there is no central server to reset it for you."
        )
        helper_text.setWordWrap(True)
        helper_text.setStyleSheet("font-size: 11px; color: #FAF9F6; text-align: center; margin-bottom: 5px;")
        helper_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        from ui.utils import load_colored_svg
        self.icon_eye = load_colored_svg("eye.svg", "#888888")
        self.icon_eye_off = load_colored_svg("eye-off.svg", "#888888")

        from PyQt6.QtGui import QAction

        # --- Primary Password Field ---
        self.inp_setup_pwd = QLineEdit()
        self.inp_setup_pwd.setPlaceholderText("Create a password...")
        self.inp_setup_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_setup_pwd.setAccessibleName("New Password") # Accessibility flag for Password Managers
        
        # Action: Explicitly instantiate QAction with parent, then set icon to satisfy strict typing
        self.action_eye_pwd = QAction(self.inp_setup_pwd)
        self.action_eye_pwd.setIcon(self.icon_eye)
        self.inp_setup_pwd.addAction(self.action_eye_pwd, QLineEdit.ActionPosition.TrailingPosition)
        self.action_eye_pwd.triggered.connect(self._toggle_pwd_vis)
        
        # --- Confirm Password Field ---
        self.inp_setup_conf_pwd = QLineEdit()
        self.inp_setup_conf_pwd.setPlaceholderText("Confirm password...")
        self.inp_setup_conf_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_setup_conf_pwd.setAccessibleName("Confirm Password") # Accessibility flag
        
        self.action_eye_conf = QAction(self.inp_setup_conf_pwd)
        self.action_eye_conf.setIcon(self.icon_eye)
        self.inp_setup_conf_pwd.addAction(self.action_eye_conf, QLineEdit.ActionPosition.TrailingPosition)
        self.action_eye_conf.triggered.connect(self._toggle_conf_vis)

        # Validation Label & Hooks
        self.lbl_setup_err = QLabel("")
        self.lbl_setup_err.setStyleSheet("color: #FF453A; font-size: 11px;")
        self.lbl_setup_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.inp_setup_pwd.textChanged.connect(self._validate_setup_passwords)
        self.inp_setup_conf_pwd.textChanged.connect(self._validate_setup_passwords)

        self.btn_setup = QPushButton("Encrypt & Start")
        self.btn_setup.setAutoDefault(False) 
        self.btn_setup.setEnabled(False) # Locked until passwords match
        self.btn_setup.clicked.connect(self._process_setup)

        self.btn_restore = QPushButton("Restore from Backup (.vault)")
        self.btn_restore.setAutoDefault(False)
        self.btn_restore.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_restore.setStyleSheet("background: transparent; color: #F1C40F; font-size: 12px; font-weight: normal; border: 1px solid #3A3A3C;")
        self.btn_restore.clicked.connect(self._import_vault)
        
        l.addWidget(desc)
        l.addWidget(helper_text)
        l.addWidget(self.inp_setup_pwd)
        l.addWidget(self.inp_setup_conf_pwd)
        l.addWidget(self.lbl_setup_err)
        l.addWidget(self.btn_setup)
        l.addWidget(self.btn_restore)
        l.addStretch()
        return w
    
    def _toggle_login_vis(self) -> None:
        if self.inp_login_pwd.echoMode() == QLineEdit.EchoMode.Password:
            self.inp_login_pwd.setEchoMode(QLineEdit.EchoMode.Normal)
            self.action_eye_login.setIcon(self.icon_eye_off)
        else:
            self.inp_login_pwd.setEchoMode(QLineEdit.EchoMode.Password)
            self.action_eye_login.setIcon(self.icon_eye)

    def _toggle_pwd_vis(self) -> None:
        if self.inp_setup_pwd.echoMode() == QLineEdit.EchoMode.Password:
            self.inp_setup_pwd.setEchoMode(QLineEdit.EchoMode.Normal)
            self.action_eye_pwd.setIcon(self.icon_eye_off)
        else:
            self.inp_setup_pwd.setEchoMode(QLineEdit.EchoMode.Password)
            self.action_eye_pwd.setIcon(self.icon_eye)

    def _toggle_conf_vis(self) -> None:
        if self.inp_setup_conf_pwd.echoMode() == QLineEdit.EchoMode.Password:
            self.inp_setup_conf_pwd.setEchoMode(QLineEdit.EchoMode.Normal)
            self.action_eye_conf.setIcon(self.icon_eye_off)
        else:
            self.inp_setup_conf_pwd.setEchoMode(QLineEdit.EchoMode.Password)
            self.action_eye_conf.setIcon(self.icon_eye)

    def _validate_setup_passwords(self) -> None:
        pwd = self.inp_setup_pwd.text()
        conf = self.inp_setup_conf_pwd.text()
        
        if not pwd and not conf:
            self.lbl_setup_err.setText("")
            self.btn_setup.setEnabled(False)
            return

        if len(pwd) < 4:
            self.lbl_setup_err.setStyleSheet("color: #FF453A;")
            self.lbl_setup_err.setText("Password must be at least 4 characters.")
            self.btn_setup.setEnabled(False)
        elif pwd != conf:
            self.lbl_setup_err.setStyleSheet("color: #FF453A;")
            self.lbl_setup_err.setText("Passwords do not match.")
            self.btn_setup.setEnabled(False)
        else:
            self.lbl_setup_err.setStyleSheet("color: #4EC9B0;")
            self.lbl_setup_err.setText("Passwords match.")
            self.btn_setup.setEnabled(True)

    def _import_vault(self) -> None:
        import shutil
        from PyQt6.QtWidgets import QFileDialog, QMessageBox

        # ACTION: Added DontUseNativeDialog to prevent event-loop hijacking and VS Code crashes
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Vault Backup", 
            "", 
            "Floaties Vault (*.vault *.db);;All Files (*)",
            options=QFileDialog.Option.DontUseNativeDialog
        )
        
        if file_path:
            try:
                # Overwrite the empty local database with the imported backup
                shutil.copy2(file_path, self.db.db_path)
                
                # Reload the database connection and fetch the imported metadata
                self.db._init_db() 
                self.salt = self.db.get_meta("salt")
                
                # Verify that it's a valid Floaties DB by checking for the salt
                if self.salt:
                    self.is_setup = False
                    self.inp_setup_pwd.clear()
                    
                    # Dynamically switch the UI to the Login screen
                    self.stack.setCurrentWidget(self.view_login)
                    
                    QMessageBox.information(
                        self, "Import Successful", 
                        "Vault imported successfully. Please log in with your existing Master Password."
                    )
                else:
                    raise ValueError("The selected file is not a valid Floaties vault.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Import Failed", f"Could not restore vault: {e}")

    def _build_login_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(12) 
        
        # 1. Fixed top breathing room so the flat-topped logo never looks clipped
        l.addSpacing(20) 
        
        l.addWidget(self._get_logo_header())
        
        # 2. The Shock Absorber: Pushes the logo up, and the fields down
        l.addStretch() 
        
        desc = QLabel("Unlock your vault")
        desc.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.inp_login_pwd = QLineEdit()
        self.inp_login_pwd.setPlaceholderText("Enter Master Password...")
        self.inp_login_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_login_pwd.returnPressed.connect(self._process_login)
        
        from PyQt6.QtGui import QAction
        from ui.utils import load_colored_svg
        
        if not hasattr(self, 'icon_eye'):
            self.icon_eye = load_colored_svg("eye.svg", "#888888")
            self.icon_eye_off = load_colored_svg("eye-off.svg", "#888888")
            
        self.action_eye_login = QAction(self.inp_login_pwd)
        self.action_eye_login.setIcon(self.icon_eye)
        self.inp_login_pwd.addAction(self.action_eye_login, QLineEdit.ActionPosition.TrailingPosition)
        self.action_eye_login.triggered.connect(self._toggle_login_vis)
        
        self.lbl_login_err = QLabel("")
        self.lbl_login_err.setStyleSheet("color: #FF453A; font-size: 12px;")
        self.lbl_login_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_login = QPushButton("Open Notes")
        self.btn_login.setAutoDefault(False) 
        self.btn_login.clicked.connect(self._process_login)
        
        self.btn_forgot = QPushButton("Use a Recovery Code")
        self.btn_forgot.setAutoDefault(False)
        self.btn_forgot.setStyleSheet("background: transparent; color: #06B6D4; font-size: 12px; font-weight: normal;")
        self.btn_forgot.clicked.connect(self._nav_to_recovery) 
        
        # Stack the bottom elements
        l.addWidget(desc)
        l.addWidget(self.inp_login_pwd)
        l.addWidget(self.lbl_login_err)
        l.addWidget(self.btn_login)
        l.addWidget(self.btn_forgot)
        
        # 3. Fixed bottom margin so the buttons don't touch the window edge
        l.addSpacing(10) 
        return w

    def _build_reveal_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("CRITICAL: Recovery Code")
        title.setStyleSheet("color: #FF453A; font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        desc = QLabel(
            "Please write this down and store it offline. Because Floaties is 100% offline, "
            "this code is the ONLY way to decrypt your notes if you forget your Master Password."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 12px; color: #E0E0E0;")
        
        # --- THE ILLUSION: A container that acts as the "Input Box" ---
        key_container = QFrame()
        key_container.setStyleSheet("QFrame { background: #2A2A2C; border: 1px solid #3A3A3C; border-radius: 6px; }")
        kc_layout = QHBoxLayout(key_container)
        kc_layout.setContentsMargins(10, 4, 4, 4) # Tight right margin to hug the button
        kc_layout.setSpacing(8)
        
        self.lbl_reveal_key = QLineEdit()
        self.lbl_reveal_key.setReadOnly(True)
        # The actual input is transparent and borderless
        self.lbl_reveal_key.setStyleSheet("background: transparent; color: #F1C40F; font-size: 15px; font-weight: bold; border: none;")
        
        self.btn_copy = QPushButton("COPY")
        self.btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy.setAutoDefault(False)
        self.btn_copy.setStyleSheet("""
            QPushButton { 
                background: #3A3A3C; 
                color: #A0A0A0; 
                border: none; 
                border-radius: 4px; 
                font-size: 11px; 
                font-weight: bold; 
                padding: 6px 12px; 
            }
            QPushButton:hover { background: #4A4A4C; color: #FFFFFF; }
        """)
        self.btn_copy.clicked.connect(self._copy_recovery_key)
        
        kc_layout.addWidget(self.lbl_reveal_key)
        kc_layout.addWidget(self.btn_copy)
        # --------------------------------------------------------------
        
        self.btn_reveal_ack = QPushButton("I've saved this safely")
        self.btn_reveal_ack.setAutoDefault(False)
        self.btn_reveal_ack.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reveal_ack.clicked.connect(self.accept)
        
        l.addWidget(title)
        l.addSpacing(5)
        l.addWidget(desc)
        l.addStretch()
        l.addWidget(key_container) # Add the container instead of just the line edit
        l.addSpacing(4)
        l.addWidget(self.btn_reveal_ack)
        return w

    def _build_recovery_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(12) 
        
        # 1. Identical top margin
        l.addSpacing(20) 
        
        l.addWidget(self._get_logo_header())
        
        # 2. Identical Shock Absorber
        l.addStretch() 
        
        subtitle = QLabel("Account Recovery")
        subtitle.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.inp_rec_key = QLineEdit()
        self.inp_rec_key.setPlaceholderText("Enter FL-XXXX-XXXX")
        self.inp_rec_key.returnPressed.connect(self._process_recovery)
        
        self.lbl_rec_err = QLabel("")
        self.lbl_rec_err.setStyleSheet("color: #FF453A; font-size: 12px;")
        self.lbl_rec_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setAutoDefault(False)
        btn_cancel.setStyleSheet("background: transparent; color: #A0A0A0; font-weight: normal; border: 1px solid #3A3A3C;")
        btn_cancel.clicked.connect(self._nav_to_login)
        
        self.btn_recover = QPushButton("Recover")
        self.btn_recover.setAutoDefault(False)
        self.btn_recover.clicked.connect(self._process_recovery)
        
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self.btn_recover)
        
        # Stack the bottom elements
        l.addWidget(subtitle)
        l.addWidget(self.inp_rec_key)
        l.addWidget(self.lbl_rec_err)
        l.addLayout(btn_row)
        
        # 3. Identical bottom margin
        l.addSpacing(10) 
        return w

    def _generate_recovery_key(self, master_pwd: str) -> str:
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
            
        self.setFocus() # ACTION: Safely shift focus away from input
        self.btn_setup.setEnabled(False)
        self.inp_setup_pwd.setEnabled(False)
        self.inp_setup_conf_pwd.setEnabled(False)
        self.btn_setup.setText("Preparing...")
        
        # ACTION: Removed processEvents() to stop VS Code debugger panics.
        # QTimer naturally yields to the event loop, so the UI will update on its own!
        QTimer.singleShot(50, self._execute_setup_crypto)

    def _execute_setup_crypto(self) -> None:
        # Read the password directly from the locked UI field
        pwd = self.inp_setup_pwd.text().strip()
        
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
        
        self.setFocus() # ACTION: Safely shift focus away from input
        self.btn_login.setEnabled(False)
        self.inp_login_pwd.setEnabled(False)
        self.btn_forgot.setEnabled(False) 
        
        self.lbl_login_err.setStyleSheet("color: #F1C40F;")
        self.lbl_login_err.setText("Loading...")
        
        # ACTION: Removed processEvents() to stop VS Code debugger panics.
        QTimer.singleShot(100, self._execute_login_crypto)

    def _execute_login_crypto(self) -> None:
        # Read the password directly from the locked UI field
        pwd = self.inp_login_pwd.text().strip()
        
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
        self.btn_forgot.setEnabled(True) 
        
        self.inp_login_pwd.setFocus()

    def _process_recovery(self) -> None:
        rec_key = self.inp_rec_key.text().strip().upper()
        if not rec_key: return
        
        self.setFocus() # ACTION: Safely shift focus away from input
        self.btn_recover.setEnabled(False)
        self.lbl_rec_err.setStyleSheet("color: #F1C40F;")
        self.lbl_rec_err.setText("Verifying...")
        
        # ACTION: Removed processEvents() to stop VS Code debugger panics.
        
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
    
    def _copy_recovery_key(self) -> None:
        # Access the OS clipboard and inject the key
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.lbl_reveal_key.text())
            
            # Visual feedback: Flash the brand yellow
            self.btn_copy.setText("COPIED!")
            self.btn_copy.setStyleSheet("""
                QPushButton { 
                    background: #F1C40F; 
                    color: #1A1A1A; 
                    border: none; 
                    border-radius: 4px; 
                    font-size: 11px; 
                    font-weight: bold; 
                    padding: 6px 12px; 
                }
            """)
            # Reset back to normal after 2 seconds
            QTimer.singleShot(2000, self._reset_copy_btn)

    def _reset_copy_btn(self) -> None:
        try:
            # Check if the C++ object still exists before modifying it
            self.btn_copy.setText("COPY")
            self.btn_copy.setStyleSheet("""
                QPushButton { 
                    background: #3A3A3C; 
                    color: #A0A0A0; 
                    border: none; 
                    border-radius: 4px; 
                    font-size: 11px; 
                    font-weight: bold; 
                    padding: 6px 12px; 
                }
                QPushButton:hover { background: #4A4A4C; color: #FFFFFF; }
            """)
        except RuntimeError:
            # The window was closed before the 2 seconds finished. Safely ignore!
            pass