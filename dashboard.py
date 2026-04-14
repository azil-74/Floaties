# Floaties Dashboard 
# Action: Dynamic action buttons, robust item delete UI, Base64 SVG Checkmarks, and Timestamp parsing.

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QLabel, QPushButton, QListWidget, QListWidgetItem, QStackedWidget,
    QMessageBox, QApplication, QCheckBox, QFrame, QStyle
)
from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtGui import QDesktopServices
from database import DatabaseManager
from security import Vault
import secrets
from datetime import datetime

class NoteItemWidget(QWidget):
    """Custom UI using Native OS Standard Icons and bulletproof typography."""
    def __init__(self, note_data: dict, dashboard_ref):
        super().__init__()
        self.note_data = note_data
        self.dashboard = dashboard_ref
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        # 1. Bulletproof Checkbox (Strict RGBA Color Toggling)
        self.checkbox = QPushButton("✓")
        self.checkbox.setCheckable(True)
        self.checkbox.setFixedSize(22, 22) 
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkbox.setStyleSheet("""
            QPushButton { 
                border: 1px solid #3A3A3C; 
                border-radius: 6px; 
                background: #2A2A2C; 
                color: rgba(0, 0, 0, 0); 
                font-size: 14px; 
                font-weight: 900;
                padding-bottom: 2px;
            }
            QPushButton:checked { 
                background: #0A84FF; 
                border: 1px solid #0A84FF; 
                color: #FFFFFF; 
            }
        """)
        self.checkbox.toggled.connect(self.dashboard._update_action_buttons_visibility)
        
        # 2. Text Column
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        
        self.title_label = QLabel(note_data["title"])
        self.title_label.setStyleSheet("font-size: 14px; font-weight: 500; color: #E0E0E0;")
        
        from datetime import datetime
        raw_date = note_data.get("created_at")
        if raw_date:
            try:
                dt = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%b %d, %Y")
            except ValueError:
                date_str = raw_date.split()[0]
        else:
            date_str = "Today"
            
        self.date_label = QLabel(date_str)
        self.date_label.setStyleSheet("font-size: 11px; color: #888888; font-family: 'Segoe UI', system-ui;")
        
        text_col.addWidget(self.title_label)
        text_col.addWidget(self.date_label)
        
        # 3. Restrained Native Delete Button
        self.btn_delete = QPushButton()
        self.btn_delete.setFixedSize(24, 24) 
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        
        app_style = QApplication.style()
        if app_style is not None:
            close_icon = app_style.standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton)
            self.btn_delete.setIcon(close_icon)
            self.btn_delete.setIconSize(QSize(10, 10)) 
        else:
            self.btn_delete.setText("✕")
        
        self.btn_delete.setStyleSheet("""
            QPushButton { 
                background: #2A2A2C; 
                border: 1px solid #3A3A3C; 
                border-radius: 6px; 
                color: #666666;
            }
            QPushButton:hover { 
                background: #FF453A; 
                border: 1px solid #FF453A; 
            }
        """)
        self.btn_delete.clicked.connect(self._delete_self)
        
        layout.addWidget(self.checkbox)
        layout.addLayout(text_col)
        layout.addStretch()
        layout.addWidget(self.btn_delete)

    # ---> THE MISSING METHOD <---
    def _delete_self(self) -> None:
        self.dashboard._delete_specific_note(self.note_data)


class Dashboard(QMainWindow):
    """Clean, minimalistic central hub for managing Floaties."""
    def __init__(self, db: DatabaseManager, pwd: str, salt: bytes):
        super().__init__()
        self.db = db
        self.pwd = pwd
        self.salt = salt
        
        self.setWindowTitle("Floaties")
        self.setMinimumSize(420, 550)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #1A1A1A; }
            QLabel { color: #E0E0E0; font-family: 'Segoe UI', system-ui; }
            QLineEdit { background: #2A2A2C; color: #FFF; border: 1px solid #3A3A3C; padding: 10px; border-radius: 6px; font-size: 13px; }
            QLineEdit:focus { border: 1px solid #0A84FF; }
            
            QPushButton { background: #2A2A2C; color: #E0E0E0; border: 1px solid #3A3A3C; padding: 8px 16px; border-radius: 6px; font-weight: 500; }
            QPushButton:hover { background: #353537; }
            QPushButton#ActionBtn { background: #0A84FF; color: #FFF; border: none; font-weight: bold; }
            QPushButton#ActionBtn:hover { background: #0070E0; }
            QPushButton#DangerBtn { background: transparent; color: #FF453A; border: 1px solid #FF453A; }
            QPushButton#DangerBtn:hover { background: rgba(255, 69, 58, 0.1); }
            
            QListWidget { background: transparent; border: none; outline: none; }
            QListWidget::item { border-bottom: 1px solid #2A2A2C; border-radius: 6px; margin-bottom: 2px;}
            QListWidget::item:hover { background: #222222; }
            QListWidget::item:selected { background: transparent; border: 1px solid #0A84FF; }
        """)
        
        self._init_ui()
        self._refresh_notes_list()

    def _init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # --- 1. The Pill Navigation Bar ---
        nav_container = QFrame()
        nav_container.setStyleSheet("QFrame { background: #2A2A2C; border-radius: 8px; padding: 2px; }")
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(2, 2, 2, 2)
        nav_layout.setSpacing(2)
        
        self.btn_nav_notes = self._create_nav_pill("My Notes", True)
        self.btn_nav_settings = self._create_nav_pill("Settings", False)
        self.btn_nav_about = self._create_nav_pill("About", False)
        
        nav_layout.addWidget(self.btn_nav_notes)
        nav_layout.addWidget(self.btn_nav_settings)
        nav_layout.addWidget(self.btn_nav_about)
        
        main_layout.addWidget(nav_container)
        main_layout.addSpacing(10)
        
        # --- 2. The Stacked Views ---
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        self.view_notes = self._build_notes_view()
        self.view_settings = self._build_settings_view()
        self.view_about = self._build_about_view()
        
        self.stack.addWidget(self.view_notes)
        self.stack.addWidget(self.view_settings)
        self.stack.addWidget(self.view_about)
        
        # Connect Nav Buttons
        self.btn_nav_notes.clicked.connect(lambda: self._switch_tab(0, self.btn_nav_notes))
        self.btn_nav_settings.clicked.connect(lambda: self._switch_tab(1, self.btn_nav_settings))
        self.btn_nav_about.clicked.connect(lambda: self._switch_tab(2, self.btn_nav_about))

        # Global Status Bar
        self.global_status = QLabel("All notes saved.")
        self.global_status.setStyleSheet("color: #888888; font-size: 11px; padding-top: 8px;")
        main_layout.addWidget(self.global_status)

    def _create_nav_pill(self, text: str, is_active: bool) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setCheckable(True)
        btn.setChecked(is_active)
        btn.setFixedHeight(30)
        btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: #A0A0A0; font-weight: 600; border-radius: 6px; }
            QPushButton:hover { color: #E0E0E0; }
            QPushButton:checked { background: #3A3A3C; color: #FFF; border: 1px solid #4A4A4C; }
        """)
        return btn

    def _switch_tab(self, index: int, active_btn: QPushButton) -> None:
        self.stack.setCurrentIndex(index)
        self.btn_nav_notes.setChecked(active_btn == self.btn_nav_notes)
        self.btn_nav_settings.setChecked(active_btn == self.btn_nav_settings)
        self.btn_nav_about.setChecked(active_btn == self.btn_nav_about)

    # --- View Builders ---

    def _build_notes_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search notes...")
        self.search_bar.textChanged.connect(self._filter_notes)
        
        self.list_notes = QListWidget()
        self.list_notes.itemDoubleClicked.connect(lambda item: self._launch_note_instance(item.data(Qt.ItemDataRole.UserRole)))
        
        btn_row = QHBoxLayout()
        btn_spawn_new = QPushButton("+ New Note")
        btn_spawn_new.setObjectName("ActionBtn")
        btn_spawn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_spawn_new.clicked.connect(self._spawn_empty_note)
        
        self.btn_open_sel = QPushButton("Open")
        self.btn_open_sel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_sel.clicked.connect(self._open_marked_notes)
        
        self.btn_del_sel = QPushButton("Delete")
        self.btn_del_sel.setObjectName("DangerBtn")
        self.btn_del_sel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del_sel.clicked.connect(self._delete_marked_notes)
        
        # Hide dynamic buttons by default
        self.btn_open_sel.hide()
        self.btn_del_sel.hide()
        
        btn_row.addWidget(self.btn_del_sel)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_open_sel)
        btn_row.addWidget(btn_spawn_new)
        
        l.addWidget(self.search_bar)
        l.addSpacing(8)
        l.addWidget(self.list_notes)
        l.addLayout(btn_row)
        return w

    def _build_settings_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignmentFlag.AlignTop)
        l.setContentsMargins(0, 8, 0, 0)
        
        self.btn_toggle_security = QPushButton("Security && Password  ↓")
        self.btn_toggle_security.setStyleSheet("text-align: left; padding: 12px; background: #2A2A2C; border: none; font-size: 14px;")
        self.btn_toggle_security.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.sec_container = QWidget()
        self.sec_container.setVisible(False) 
        sec_layout = QVBoxLayout(self.sec_container)
        sec_layout.setContentsMargins(16, 8, 16, 16)
        
        self.inp_curr_pwd = QLineEdit()
        self.inp_curr_pwd.setPlaceholderText("Current Password")
        self.inp_curr_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.inp_new_pwd = QLineEdit()
        self.inp_new_pwd.setPlaceholderText("New Password")
        self.inp_new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.inp_conf_pwd = QLineEdit()
        self.inp_conf_pwd.setPlaceholderText("Confirm New Password")
        self.inp_conf_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.lbl_sec_status = QLabel("")
        
        btn_change_pwd = QPushButton("Update Password")
        btn_change_pwd.setObjectName("ActionBtn")
        btn_change_pwd.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_change_pwd.clicked.connect(self._execute_key_rotation)
        
        sec_layout.addWidget(QLabel("Warning: Rotating keys takes a moment. Do not close the app."))
        sec_layout.addSpacing(8)
        sec_layout.addWidget(self.inp_curr_pwd)
        sec_layout.addWidget(self.inp_new_pwd)
        sec_layout.addWidget(self.inp_conf_pwd)
        sec_layout.addWidget(self.lbl_sec_status)
        sec_layout.addWidget(btn_change_pwd)
        
        self.btn_toggle_security.clicked.connect(self._toggle_security_accordion)
        
        l.addWidget(self.btn_toggle_security)
        l.addWidget(self.sec_container)
        l.addStretch()
        return w

    def _build_about_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignmentFlag.AlignTop)
        l.setContentsMargins(16, 24, 16, 16)
        
        title = QLabel("Floaties v1.0")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFF; text-align: center;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        desc = QLabel(
            "Floaties is a minimalist, local-first sticky note application designed "
            "for Linux and Windows. It was built to provide a clean, native experience "
            "without compromising on uncompromising offline security.<br><br>"
            "Developed independently by a solo Systems Engineer to fill the gap of "
            "reliable, aesthetic productivity tools in the open-source ecosystem."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 13px; color: #A0A0A0; line-height: 1.5;")
        
        btn_donate = QPushButton("☕ Support the Developer")
        btn_donate.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_donate.setStyleSheet("""
            QPushButton { background: #FF5E5B; color: #FFF; font-weight: bold; padding: 12px; font-size: 14px; border-radius: 8px; border: none; }
            QPushButton:hover { background: #FF453A; }
        """)
        # UPDATE THIS URL
        btn_donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://ko-fi.com/yourusername")))
        
        l.addWidget(title)
        l.addSpacing(16)
        l.addWidget(desc)
        l.addSpacing(32)
        l.addWidget(btn_donate)
        l.addStretch()
        return w

    # --- Interaction Logic ---

    def _update_action_buttons_visibility(self) -> None:
        """Dynamically shows/hides footer tools based on checkbox states."""
        has_checked = len(self._get_marked_notes()) > 0
        self.btn_open_sel.setVisible(has_checked)
        self.btn_del_sel.setVisible(has_checked)

    def _toggle_security_accordion(self) -> None:
        is_vis = self.sec_container.isVisible()
        self.sec_container.setVisible(not is_vis)
        
        # ACTION: Clean up/down arrows and escaped ampersands
        self.btn_toggle_security.setText("Security && Password  ↑" if not is_vis else "Security && Password  ↓")

    def _refresh_notes_list(self) -> None:
        self.list_notes.clear()
        self.all_notes_data = self.db.load_all_notes()
        for note in self.all_notes_data:
            item = QListWidgetItem()
            custom_widget = NoteItemWidget(note, self)
            item.setSizeHint(custom_widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, note)
            
            self.list_notes.addItem(item)
            self.list_notes.setItemWidget(item, custom_widget)
            
        self._update_action_buttons_visibility()

    def _filter_notes(self, query: str) -> None:
        query = query.lower()
        for i in range(self.list_notes.count()):
            item = self.list_notes.item(i)
            if item is not None:
                widget = self.list_notes.itemWidget(item)
                if isinstance(widget, NoteItemWidget):
                    item.setHidden(query not in widget.note_data["title"].lower())

    def _get_marked_notes(self) -> list[dict]:
        marked = []
        for i in range(self.list_notes.count()):
            item = self.list_notes.item(i)
            if item and not item.isHidden():
                widget = self.list_notes.itemWidget(item)
                if isinstance(widget, NoteItemWidget) and widget.checkbox.isChecked():
                    marked.append(widget.note_data)
        return marked

    def _open_marked_notes(self) -> None:
        notes = self._get_marked_notes()
        for note_data in notes:
            self._launch_note_instance(note_data)
            
        for i in range(self.list_notes.count()):
            widget = self.list_notes.itemWidget(self.list_notes.item(i))
            if isinstance(widget, NoteItemWidget):
                widget.checkbox.setChecked(False)

    def _delete_marked_notes(self) -> None:
        notes = self._get_marked_notes()
        if not notes: return
        
        reply = QMessageBox.question(self, 'Delete Notes', f"Are you sure you want to delete {len(notes)} selected note(s)?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            for note_data in notes:
                self._delete_specific_note(note_data)

    def _delete_specific_note(self, note_data: dict) -> None:
        from spawner import ACTIVE_NOTES
        for active_note in list(ACTIVE_NOTES):
            if active_note.db_id == note_data["id"]:
                active_note._is_being_deleted = True 
                active_note.close()
                
        self.db.delete_note(note_data["id"])
        self._refresh_notes_list()

    def _spawn_empty_note(self) -> None:
        self._launch_note_instance(None)

    def _launch_note_instance(self, note_data: dict | None) -> None:
        from main import StickyNote
        from spawner import ACTIVE_NOTES
        
        if note_data:
            for active_note in ACTIVE_NOTES:
                if active_note.db_id == note_data["id"]:
                    active_note.raise_()
                    active_note.activateWindow()
                    return
                    
        note = StickyNote(db=self.db, pwd=self.pwd, salt=self.salt, note_data=note_data)
        note.note_saved.connect(self._refresh_notes_list)
        note.note_saved.connect(lambda: self.global_status.setText("All notes saved."))
        
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
            
        self.lbl_sec_status.setStyleSheet("color: #0A84FF;")
        self.lbl_sec_status.setText("Preparing...")
        QApplication.processEvents()
        
        from spawner import ACTIVE_NOTES
        notes_to_save = [
            n for n in ACTIVE_NOTES 
            if (hasattr(n, 'save_timer') and n.save_timer.isActive()) 
            or getattr(n, 'pending_save', False)
            or (n.save_worker is not None and n.save_worker.isRunning())
        ]
        
        for note in notes_to_save:
            note.force_sync_save_for_shutdown()
            
        for note in list(ACTIVE_NOTES):
            note.close()
            
        self._refresh_notes_list()

        self.lbl_sec_status.setText("Updating...")
        QApplication.processEvents()
        
        try:
            decrypted_payloads = []
            for note in self.all_notes_data:
                if note["content"]:
                    try:
                        raw_text = Vault.decrypt(note["content"], self.pwd, self.salt)
                        decrypted_payloads.append({"id": note["id"], "raw_text": raw_text})
                    except ValueError:
                        continue
                else:
                    decrypted_payloads.append({"id": note["id"], "raw_text": ""})
            
            new_salt = Vault.generate_salt()
            new_token = Vault.encrypt("VALID", new_pwd, new_salt)
            
            new_rec_key = f"FL-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
            new_rec_salt = Vault.generate_salt()
            new_rec_enc_pwd = Vault.encrypt(new_pwd, new_rec_key, new_rec_salt)
            
            re_encrypted_data = []
            for payload in decrypted_payloads:
                new_blob = Vault.encrypt(payload["raw_text"], new_pwd, new_salt)
                re_encrypted_data.append({"id": payload["id"], "content": new_blob})
                
            self.db.update_all_notes_atomic(re_encrypted_data)
            
            self.db.set_meta("salt", new_salt)
            self.db.set_meta("val_token", new_token)
            self.db.set_meta("recovery_salt", new_rec_salt)
            self.db.set_meta("rec_enc_pwd", new_rec_enc_pwd)
            
            self.pwd = new_pwd
            self.salt = new_salt
            self._refresh_notes_list()
            
            self.inp_curr_pwd.clear()
            self.inp_new_pwd.clear()
            self.inp_conf_pwd.clear()
            self.lbl_sec_status.setText("")
            
            QMessageBox.information(
                self, 
                "Password Updated", 
                f"Your password has been changed successfully.\n\nYour NEW Recovery Code is:\n{new_rec_key}\n\nPlease save this immediately."
            )
            
        except Exception as e:
            self._set_sec_err(f"CRITICAL ERROR: {str(e)}")

    def _set_sec_err(self, msg: str) -> None:
        self.lbl_sec_status.setStyleSheet("color: #FF453A;")
        self.lbl_sec_status.setText(msg)

    def closeEvent(self, event) -> None:
        from spawner import ACTIVE_NOTES
        from PyQt6.QtWidgets import QApplication
        
        notes_to_save = [
            n for n in ACTIVE_NOTES 
            if (hasattr(n, 'save_timer') and n.save_timer.isActive()) 
            or getattr(n, 'pending_save', False)
            or (n.save_worker is not None and n.save_worker.isRunning())
        ]
        total = len(notes_to_save)

        if total > 0:
            for i, note in enumerate(notes_to_save, 1):
                self.global_status.setStyleSheet("color: #0A84FF; font-size: 11px; padding-top: 8px;")
                self.global_status.setText(f"Closing... (Saving note {i}/{total})")
                QApplication.processEvents()
                
                note.force_sync_save_for_shutdown()
                note.close()
        
        for note in list(ACTIVE_NOTES):
            note.close()
            
        super().closeEvent(event)