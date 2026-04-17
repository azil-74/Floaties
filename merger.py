# Merge Module: Handles the complex process of securely merging an imported vault into the active vault, including password validation, cryptographic translation.
import sqlite3
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox, QFrame, QApplication
)
from PyQt6.QtCore import Qt
from security import Vault
from database import DatabaseManager

class MergeAuthDialog(QDialog):
    """Sleek dialog to securely capture the password of the imported vault."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.password = None
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(380, 240)
        
        self.setStyleSheet("""
            QDialog { background: transparent; }
            QFrame#BaseFrame { background-color: #1E1E1E; border: 1px solid #333333; border-radius: 12px; }
            QLabel { font-family: 'Segoe UI', system-ui; }
            QLineEdit { background: #2A2A2C; color: #FFF; border: 1px solid #3A3A3C; padding: 10px; border-radius: 6px; font-size: 13px; }
            QLineEdit:focus { border: 1px solid #F1C40F; }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.base_frame = QFrame(self)
        self.base_frame.setObjectName("BaseFrame")
        self.base_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        outer_layout.addWidget(self.base_frame)

        layout = QVBoxLayout(self.base_frame)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("Unlock Imported Vault")
        title.setStyleSheet("color: #F1C40F; font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc = QLabel("Enter the Master Password for the vault you are trying to merge.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 13px; color: #E0E0E0;")

        self.inp_pwd = QLineEdit()
        self.inp_pwd.setPlaceholderText("Imported Master Password")
        self.inp_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_pwd.setMinimumHeight(38)

        btn_row = QVBoxLayout()
        btn_unlock = QPushButton("Decrypt && Merge")
        btn_unlock.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_unlock.setMinimumHeight(38)
        btn_unlock.setStyleSheet("""
            QPushButton { background: #F1C40F; color: #1A1A1A; border: none; border-radius: 6px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background: #D4AC0D; }
        """)
        btn_unlock.clicked.connect(self._submit)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton { background: transparent; color: #A0A0A0; border: none; font-weight: bold; font-size: 13px; }
            QPushButton:hover { color: #E0E0E0; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(btn_unlock)
        btn_row.addWidget(btn_cancel)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addSpacing(10)
        layout.addWidget(self.inp_pwd)
        layout.addStretch()
        layout.addLayout(btn_row)

    def _submit(self):
        self.password = self.inp_pwd.text()
        self.accept()

class VaultMerger:
    @staticmethod
    def execute_merge(parent_widget, current_db: DatabaseManager, current_pwd: str, current_salt: bytes, import_path: str) -> bool:
        import shutil
        import os
        import secrets
        
        auth = MergeAuthDialog(parent_widget)
        if auth.exec() != QDialog.DialogCode.Accepted or not auth.password:
            return False
            
        imported_pwd = auth.password
        temp_db_path = None
        
        try:
            temp_dir = current_db.db_path.parent
            temp_db_path = temp_dir / f"temp_merge_{secrets.token_hex(4)}.db"
            
            shutil.copy2(import_path, temp_db_path)
            
            temp_db = DatabaseManager(db_path=temp_db_path)
            
            imported_salt = temp_db.get_meta("salt")
            if not imported_salt:
                QMessageBox.critical(parent_widget, "Invalid Vault", "The imported file is not a valid Floaties vault or is missing its security salt.")
                return False
            
            imported_notes = temp_db.load_all_notes()
            
            if not imported_notes:
                QMessageBox.information(parent_widget, "Empty Vault", "The selected vault has no notes to merge.")
                return False

            password_valid = False
            for note in imported_notes:
                if note["content"]: 
                    try:
                        Vault.decrypt(note["content"], imported_pwd, imported_salt)
                        password_valid = True
                        break
                    except Exception:
                        QMessageBox.critical(parent_widget, "Merge Failed", "Incorrect Master Password for the imported vault.")
                        return False
            
            if not password_valid and any(n["content"] for n in imported_notes):
                return False

            success_count = 0
            for note in imported_notes:
                enc_content = note["content"]
                
                if enc_content:
                    plain_content = Vault.decrypt(enc_content, imported_pwd, imported_salt)
                    new_enc_content = Vault.encrypt(plain_content, current_pwd, current_salt)
                else:
                    new_enc_content = ""
                
                data = {
                    "id": None,
                    "title": f"{note['title']} (Imported)",
                    "content": new_enc_content,
                    "theme_index": note["theme_index"],
                    "pos_x": note["pos_x"] + 40,
                    "pos_y": note["pos_y"] + 40,
                    "width": note["width"],
                    "height": note["height"],
                    "is_rolled_up": note["is_rolled_up"]
                }
                current_db.upsert_note(data)
                success_count += 1
                
            QMessageBox.information(
                parent_widget, 
                "Merge Complete", 
                f"Successfully decrypted, translated, and merged {success_count} note(s) into your active vault!"
            )
            return True
            
        except Exception as e:
            QMessageBox.critical(parent_widget, "Merge Failed", f"An error occurred: {e}")
            return False
        finally:
            if temp_db_path:
                try:
                    import time
                    time.sleep(0.1) 
                    if os.path.exists(temp_db_path): os.remove(temp_db_path)
                    if os.path.exists(f"{temp_db_path}-wal"): os.remove(f"{temp_db_path}-wal")
                    if os.path.exists(f"{temp_db_path}-shm"): os.remove(f"{temp_db_path}-shm")
                except OSError:
                    pass