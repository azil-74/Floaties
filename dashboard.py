# Save Notes: Control Center & Cryptographic Key Rotation
# Target: Windows (Dev) -> Ubuntu (Prod)
# Action: Built Omni-Search dashboard and atomic re-encryption loop for password rotation.

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QLabel, QPushButton, QListWidget, QListWidgetItem, QTabWidget,
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt
from database import DatabaseManager
from security import Vault
import secrets

class Dashboard(QMainWindow):
    """Central Hub for managing the Offline Brain and Vault Security."""
    def __init__(self, db: DatabaseManager, pwd: str, salt: bytes):
        super().__init__()
        self.db = db
        self.pwd = pwd
        self.salt = salt
        
        self.setWindowTitle("Floatslate Control Center")
        self.setMinimumSize(450, 550)
        self.setStyleSheet("""
            QMainWindow { background-color: #1E1E1E; }
            QLabel { color: #D4D4D4; font-family: 'Segoe UI'; }
            QLineEdit { background: #2D2D30; color: #FFF; border: 1px solid #3E3E42; padding: 6px; border-radius: 4px; }
            QLineEdit:focus { border: 1px solid #007ACC; }
            QPushButton { background: #3E3E42; color: #FFF; border: none; padding: 8px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background: #505050; }
            QPushButton#ActionBtn { background: #007ACC; }
            QPushButton#ActionBtn:hover { background: #0098FF; }
            QTabWidget::pane { border: 1px solid #3E3E42; background: #1E1E1E; }
            QTabBar::tab { background: #2D2D30; color: #888; padding: 8px 16px; border: 1px solid #3E3E42; }
            QTabBar::tab:selected { background: #1E1E1E; color: #FFF; border-bottom-color: #1E1E1E; }
            QListWidget { background: #252526; border: 1px solid #3E3E42; color: #FFF; outline: none; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #3E3E42; }
            QListWidget::item:selected { background: #094771; }
        """)
        
        self._init_ui()
        self._refresh_notes_list()

    def _init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Tab 1: Notes Overview
        tab_notes = QWidget()
        layout_notes = QVBoxLayout(tab_notes)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Omni-Search by Title...")
        self.search_bar.textChanged.connect(self._filter_notes)
        
        self.list_notes = QListWidget()
        self.list_notes.itemDoubleClicked.connect(self._spawn_selected_note)
        
        # Patched layout: Added a Delete Button side-by-side with Create
        btn_row = QHBoxLayout()
        
        btn_spawn_new = QPushButton("+ Create New Note")
        btn_spawn_new.setObjectName("ActionBtn")
        btn_spawn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_spawn_new.clicked.connect(self._spawn_empty_note)
        
        btn_delete = QPushButton("Delete Selected")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.clicked.connect(self._delete_selected_note)
        
        btn_row.addWidget(btn_spawn_new)
        btn_row.addWidget(btn_delete)
        
        layout_notes.addWidget(self.search_bar)
        layout_notes.addWidget(self.list_notes)
        layout_notes.addLayout(btn_row)
        
        # Tab 2: Vault Settings
        tab_vault = QWidget()
        layout_vault = QVBoxLayout(tab_vault)
        layout_vault.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        lbl_sec = QLabel("Cryptographic Key Rotation")
        lbl_sec.setStyleSheet("font-size: 14px; font-weight: bold; color: #F1C40F;")
        
        self.inp_curr_pwd = QLineEdit()
        self.inp_curr_pwd.setPlaceholderText("Current Master Password")
        self.inp_curr_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.inp_new_pwd = QLineEdit()
        self.inp_new_pwd.setPlaceholderText("New Master Password")
        self.inp_new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.inp_conf_pwd = QLineEdit()
        self.inp_conf_pwd.setPlaceholderText("Confirm New Password")
        self.inp_conf_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.lbl_sec_status = QLabel("")
        
        btn_change_pwd = QPushButton("Re-Encrypt Vault")
        btn_change_pwd.setObjectName("ActionBtn")
        btn_change_pwd.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_change_pwd.clicked.connect(self._execute_key_rotation)
        
        layout_vault.addWidget(lbl_sec)
        layout_vault.addWidget(QLabel("Warning: This will re-encrypt all notes. Do not close the app during this process."))
        layout_vault.addSpacing(10)
        layout_vault.addWidget(self.inp_curr_pwd)
        layout_vault.addWidget(self.inp_new_pwd)
        layout_vault.addWidget(self.inp_conf_pwd)
        layout_vault.addWidget(self.lbl_sec_status)
        layout_vault.addWidget(btn_change_pwd)
        
        self.tabs.addTab(tab_notes, "Offline Brain")
        self.tabs.addTab(tab_vault, "Vault Settings")

    # --- Notes Management ---
    def _refresh_notes_list(self) -> None:
        self.list_notes.clear()
        self.all_notes_data = self.db.load_all_notes()
        for note in self.all_notes_data:
            item = QListWidgetItem(note["title"])
            item.setData(Qt.ItemDataRole.UserRole, note)
            self.list_notes.addItem(item)

    def _filter_notes(self, query: str) -> None:
        query = query.lower()
        for i in range(self.list_notes.count()):
            item = self.list_notes.item(i)
            # Strict Null Check to satisfy Pylance
            if item is not None:
                item.setHidden(query not in item.text().lower())

    def _spawn_selected_note(self, item: QListWidgetItem) -> None:
        note_data = item.data(Qt.ItemDataRole.UserRole)
        self._launch_note_instance(note_data)

    def _spawn_empty_note(self) -> None:
        self._launch_note_instance(None)

    def _delete_selected_note(self) -> None:
        item = self.list_notes.currentItem()
        if not item: return
        
        note_data = item.data(Qt.ItemDataRole.UserRole)
        
        from spawner import ACTIVE_NOTES
        for active_note in list(ACTIVE_NOTES):
            if active_note.db_id == note_data["id"]:
                # AUDIT FIX: Tell the window it's being assassinated so it doesn't try to save
                active_note._is_being_deleted = True 
                active_note.close()
                
        self.db.delete_note(note_data["id"])
        self._refresh_notes_list()

    def _launch_note_instance(self, note_data: dict | None) -> None:
        from main import StickyNote
        from spawner import ACTIVE_NOTES
        
        # Avoid opening duplicates
        if note_data:
            for active_note in ACTIVE_NOTES:
                if active_note.db_id == note_data["id"]:
                    active_note.raise_()
                    active_note.activateWindow()
                    return
                    
        note = StickyNote(db=self.db, pwd=self.pwd, salt=self.salt, note_data=note_data)
        # Action: Hook the sync signal so the list updates live as you type!
        note.note_saved.connect(self._refresh_notes_list)
        ACTIVE_NOTES.add(note)
        note.show()

    # --- Cryptographic Key Rotation Protocol ---
    def _execute_key_rotation(self) -> None:
        curr_pwd = self.inp_curr_pwd.text().strip()
        new_pwd = self.inp_new_pwd.text().strip()
        conf_pwd = self.inp_conf_pwd.text().strip()
        
        if not curr_pwd or not new_pwd:
            self._set_sec_err("Fields cannot be empty.")
            return
        if curr_pwd != self.pwd:
            self._set_sec_err("Current password incorrect.")
            return
        if new_pwd == curr_pwd:
            self._set_sec_err("New password must be different.")
            return
        if new_pwd != conf_pwd:
            self._set_sec_err("New passwords do not match.")
            return
            
        self.lbl_sec_status.setStyleSheet("color: #569CD6;")
        
        # --- NEW: Phase 0 Lockdown Protocol ---
        self.lbl_sec_status.setText("Phase 0: Securing active notes...")
        QApplication.processEvents()
        
        from spawner import ACTIVE_NOTES
        notes_to_save = [
            n for n in ACTIVE_NOTES 
            if (hasattr(n, 'save_timer') and n.save_timer.isActive()) 
            or getattr(n, 'pending_save', False)
            or (n.save_worker is not None and n.save_worker.isRunning())
        ]
        
        # Synchronously force-save any pending keystrokes
        for note in notes_to_save:
            note.force_sync_save_for_shutdown()
            
        # Forcibly close all floating windows to kill stale memory pointers
        for note in list(ACTIVE_NOTES):
            note.close()
            
        # Refresh the RAM cache to ensure we grab the absolute latest SQLite blobs
        self._refresh_notes_list()
        # --------------------------------------

        self.lbl_sec_status.setText("Phase 1: Decrypting RAM payload...")
        QApplication.processEvents()
        
        try:
            # 1. Pull and Decrypt everything using the OLD key
            decrypted_payloads = []
            for note in self.all_notes_data:
                if note["content"]:
                    # AUDIT FIX: Catch individual corruption so the rotation doesn't fail
                    try:
                        raw_text = Vault.decrypt(note["content"], self.pwd, self.salt)
                        decrypted_payloads.append({"id": note["id"], "raw_text": raw_text})
                    except ValueError:
                        print(f"Skipping corrupted payload for Note ID: {note['id']}")
                        continue
                else:
                    decrypted_payloads.append({"id": note["id"], "raw_text": ""})
            
            self.lbl_sec_status.setText("Phase 2: Generating new cryptographic keys...")
            QApplication.processEvents()
            
            # 2. Generate New Vault Infrastructure
            new_salt = Vault.generate_salt()
            new_token = Vault.encrypt("VALID", new_pwd, new_salt)
            
            # 3. Generate New Recovery Key
            new_rec_key = f"FS-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
            new_rec_salt = Vault.generate_salt()
            new_rec_enc_pwd = Vault.encrypt(new_pwd, new_rec_key, new_rec_salt)
            
            self.lbl_sec_status.setText("Phase 3: Re-encrypting Vault. Do not close...")
            QApplication.processEvents()
            
            # 4. Re-Encrypt payloads with the NEW key
            re_encrypted_data = []
            for payload in decrypted_payloads:
                new_blob = Vault.encrypt(payload["raw_text"], new_pwd, new_salt)
                re_encrypted_data.append({"id": payload["id"], "content": new_blob})
                
            # 5. ATOMIC COMMIT (The Point of No Return)
            self.db.update_all_notes_atomic(re_encrypted_data)
            
            # Update Meta tables
            self.db.set_meta("salt", new_salt)
            self.db.set_meta("val_token", new_token)
            self.db.set_meta("recovery_salt", new_rec_salt)
            self.db.set_meta("rec_enc_pwd", new_rec_enc_pwd)
            
            # Update Application State
            self.pwd = new_pwd
            self.salt = new_salt
            # ACTION: Flush the stale UI cache and load the newly encrypted blobs!
            self._refresh_notes_list()
            # Clean up UI
            self.inp_curr_pwd.clear()
            self.inp_new_pwd.clear()
            self.inp_conf_pwd.clear()
            self.lbl_sec_status.setText("")
            
            QMessageBox.information(
                self, 
                "Vault Re-Encrypted", 
                f"Your Master Password has been changed.\n\nYour NEW Emergency Recovery Key is:\n{new_rec_key}\n\nPlease save this immediately."
            )
            
        except Exception as e:
            self._set_sec_err(f"CRITICAL ERROR: {str(e)}")

    def _set_sec_err(self, msg: str) -> None:
        self.lbl_sec_status.setStyleSheet("color: #F44336;")
        self.lbl_sec_status.setText(msg)

    def closeEvent(self, event) -> None:
        """
        Graceful Shutdown: Intercepts app termination and enforces synchronous saves.
        """
        from spawner import ACTIVE_NOTES
        from PyQt6.QtWidgets import QApplication
        
        # Target notes that have unsaved changes or active background threads
        notes_to_save = [
            n for n in ACTIVE_NOTES 
            if (hasattr(n, 'save_timer') and n.save_timer.isActive()) 
            or getattr(n, 'pending_save', False)
            or (n.save_worker is not None and n.save_worker.isRunning())
        ]
        total = len(notes_to_save)

        if total > 0:
            for i, note in enumerate(notes_to_save, 1):
                self.setWindowTitle(f"Securing Vault... (Locking Note {i}/{total})")
                QApplication.processEvents()
                
                # Execute the synchronous safety fallback
                note.force_sync_save_for_shutdown()
                note.close()
        
        # Safely close any remaining open notes
        for note in list(ACTIVE_NOTES):
            note.close()
            
        super().closeEvent(event)