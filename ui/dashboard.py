# Floaties Dashboard 
# Action: Applied universal Golden Yellow / Dark theme for brand consistency.

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QLabel, QPushButton, QListWidget, QListWidgetItem, QStackedWidget,
    QMessageBox, QApplication, QCheckBox, QFrame, QStyle, QDialog
)
from PyQt6.QtCore import Qt, QUrl, QSize, QTimer
from PyQt6.QtGui import QDesktopServices
from database import DatabaseManager
from security import Vault
import secrets
from datetime import datetime

class NoteItemWidget(QWidget):
    def __init__(self, note_data: dict, dashboard_ref):
        super().__init__()
        self.note_data = note_data
        self.dashboard = dashboard_ref
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        self.checkbox = QPushButton()
        self.checkbox.setCheckable(True)
        self.checkbox.setFixedSize(28, 28) 
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkbox.setStyleSheet("""
            QPushButton { 
                margin: 7px; 
                border: 1px solid #3A3A3C; 
                border-radius: 3px; 
                background: #2A2A2C; 
            }
            QPushButton:hover {
                border: 1px solid #555555;
            }
            QPushButton:checked { 
                background: #F1C40F; 
                border: 1px solid #F1C40F; 
            }
        """)
        self.checkbox.toggled.connect(self._on_check_toggled)
        
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        
        self.title_label = QLabel(note_data["title"])
        self.title_label.setStyleSheet("font-size: 14px; font-weight: 500; color: #E0E0E0;")
        
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

    def _delete_self(self) -> None:
        self.dashboard._delete_specific_note(self.note_data)

    def _on_check_toggled(self, checked: bool) -> None:
        from ui.utils import load_colored_svg
        from PyQt6.QtCore import QSize
        from PyQt6.QtGui import QIcon
        
        if checked:
            # Inject the dark brand color to pop against the yellow background
            self.checkbox.setIcon(load_colored_svg("check.svg", "#1A1A1A"))
            self.checkbox.setIconSize(QSize(14, 14))
        else:
            self.checkbox.setIcon(QIcon())
            
        self.dashboard._update_action_buttons_visibility() 

class PasswordUpdatedDialog(QDialog):
    """Custom, branded dialog for revealing the new recovery key after rotation."""
    def __init__(self, recovery_key: str, parent=None):
        super().__init__(parent)
        self.recovery_key = recovery_key
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(380, 260)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; border: 1px solid #333333; border-radius: 12px; }
            QLabel { font-family: 'Segoe UI', system-ui; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("Password Updated")
        title.setStyleSheet("color: #F1C40F; font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        desc = QLabel(
            "Your password has been changed successfully. The old recovery code has been securely destroyed.\n\n"
            "Please save your NEW Recovery Code:"
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 13px; color: #E0E0E0;")

        key_container = QFrame()
        key_container.setStyleSheet("QFrame { background: #2A2A2C; border: 1px solid #3A3A3C; border-radius: 6px; }")
        kc_layout = QHBoxLayout(key_container)
        kc_layout.setContentsMargins(10, 4, 4, 4)
        kc_layout.setSpacing(8)
        
        self.lbl_reveal_key = QLineEdit(self.recovery_key)
        self.lbl_reveal_key.setReadOnly(True)
        self.lbl_reveal_key.setStyleSheet("background: transparent; color: #F1C40F; font-size: 15px; font-weight: bold; border: none;")
        
        self.btn_copy = QPushButton("COPY")
        self.btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy.setAutoDefault(False)
        self.btn_copy.setStyleSheet("""
            QPushButton { 
                background: #3A3A3C; color: #A0A0A0; border: none; 
                border-radius: 4px; font-size: 11px; font-weight: bold; padding: 6px 12px; 
            }
            QPushButton:hover { background: #4A4A4C; color: #FFFFFF; }
        """)
        self.btn_copy.clicked.connect(self._copy_recovery_key)
        
        kc_layout.addWidget(self.lbl_reveal_key)
        kc_layout.addWidget(self.btn_copy)

        self.btn_ack = QPushButton("I've saved this safely")
        self.btn_ack.setAutoDefault(False)
        self.btn_ack.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ack.setStyleSheet("""
            QPushButton { 
                background: #F1C40F; color: #1A1A1A; border: none; 
                padding: 10px; border-radius: 6px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: #D4AC0D; }
        """)
        self.btn_ack.clicked.connect(self.accept)

        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(desc)
        layout.addStretch()
        layout.addWidget(key_container)
        layout.addSpacing(15)
        layout.addWidget(self.btn_ack)

    def _copy_recovery_key(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.recovery_key)
            self.btn_copy.setText("COPIED!")
            self.btn_copy.setStyleSheet("""
                QPushButton { 
                    background: #F1C40F; color: #1A1A1A; border: none; 
                    border-radius: 4px; font-size: 11px; font-weight: bold; padding: 6px 12px; 
                }
            """)
            QTimer.singleShot(2000, self._reset_copy_btn)

    def _reset_copy_btn(self) -> None:
        try:
            self.btn_copy.setText("COPY")
            self.btn_copy.setStyleSheet("""
                QPushButton { 
                    background: #3A3A3C; color: #A0A0A0; border: none; 
                    border-radius: 4px; font-size: 11px; font-weight: bold; padding: 6px 12px; 
                }
                QPushButton:hover { background: #4A4A4C; color: #FFFFFF; }
            """)
        except RuntimeError:
            pass

class ExitConfirmDialog(QDialog):
    """Custom dialog to intercept dashboard closure when notes are active."""
    def __init__(self, active_count: int, parent=None):
        super().__init__(parent)
        self.choice = "cancel"
        self.active_count = active_count
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(380, 220)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; border: 1px solid #333333; border-radius: 12px; }
            QLabel { font-family: 'Segoe UI', system-ui; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("Active Notes Detected")
        title.setStyleSheet("color: #F1C40F; font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc = QLabel(
            f"Closing the dashboard will also close your {self.active_count} active floating note(s).\n\n"
            "What would you like to do?"
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 13px; color: #E0E0E0;")

        btn_row = QHBoxLayout()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton { background: transparent; color: #A0A0A0; border: none; padding: 10px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { color: #E0E0E0; }
        """)
        btn_cancel.clicked.connect(self._choose_cancel)

        btn_minimize = QPushButton("Minimize")
        btn_minimize.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_minimize.setStyleSheet("""
            QPushButton { background: #3A3A3C; color: #E0E0E0; border: none; padding: 10px; border-radius: 6px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background: #4A4A4C; }
        """)
        btn_minimize.clicked.connect(self._choose_minimize)

        btn_exit = QPushButton("Exit Floaties")
        btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exit.setStyleSheet("""
            QPushButton { background: transparent; color: #FF453A; border: 1px solid #FF453A; padding: 10px; border-radius: 6px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background: rgba(255, 69, 58, 0.1); }
        """)
        btn_exit.clicked.connect(self._choose_exit)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_minimize)
        btn_row.addWidget(btn_exit)

        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(desc)
        layout.addStretch()
        layout.addLayout(btn_row)

    def _choose_minimize(self):
        self.choice = "minimize"
        self.accept()

    def _choose_exit(self):
        self.choice = "exit"
        self.accept()

    def _choose_cancel(self):
        self.choice = "cancel"
        self.reject()

class Dashboard(QMainWindow):
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
            QLineEdit:focus { border: 1px solid #F1C40F; } /* Yellow Focus */
            
            QPushButton { background: #2A2A2C; color: #E0E0E0; border: 1px solid #3A3A3C; padding: 8px 16px; border-radius: 6px; font-weight: 500; }
            QPushButton:hover { background: #353537; }
            
            /* Action Buttons (Yellow with Dark Text) */
            QPushButton#ActionBtn { background: #F1C40F; color: #1A1A1A; border: none; font-weight: bold; }
            QPushButton#ActionBtn:hover { background: #D4AC0D; }
            
            QPushButton#DangerBtn { background: transparent; color: #FF453A; border: 1px solid #FF453A; }
            QPushButton#DangerBtn:hover { background: rgba(255, 69, 58, 0.1); }
            
            QListWidget { background: transparent; border: none; outline: none; }
            QListWidget::item { border-bottom: 1px solid #2A2A2C; border-radius: 6px; margin-bottom: 2px;}
            QListWidget::item:hover { background: #222222; }
            QListWidget::item:selected { background: transparent; border: 1px solid #F1C40F; } /* Yellow Select Outline */
        """)
        
        self._init_ui()
        self._refresh_notes_list()

    def _init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
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
        
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        self.view_notes = self._build_notes_view()
        self.view_settings = self._build_settings_view()
        self.view_about = self._build_about_view()
        
        self.stack.addWidget(self.view_notes)
        self.stack.addWidget(self.view_settings)
        self.stack.addWidget(self.view_about)
        
        self.btn_nav_notes.clicked.connect(lambda: self._switch_tab(0, self.btn_nav_notes))
        self.btn_nav_settings.clicked.connect(lambda: self._switch_tab(1, self.btn_nav_settings))
        self.btn_nav_about.clicked.connect(lambda: self._switch_tab(2, self.btn_nav_about))

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

    def _build_notes_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search your vault...")
        
        # 1. Shift the typing area to the right so it doesn't overlap our new icon position
        self.search_bar.setTextMargins(42, 0, 0, 0) 
        
        from ui.utils import load_colored_svg
        search_icon = load_colored_svg("search.svg", "#888888")
        
        if not search_icon.isNull():
            # 2. Use an internal layout for pixel-perfect icon placement
            icon_layout = QHBoxLayout(self.search_bar)
            
            # 19px left margin perfectly aligns the icon with the checkboxes below
            icon_layout.setContentsMargins(19, 0, 0, 0) 
            
            search_label = QLabel()
            search_label.setPixmap(search_icon.pixmap(16, 16))
            search_label.setFixedSize(16, 16)
            search_label.setStyleSheet("border: none; background: transparent;")
            
            icon_layout.addWidget(search_label)
            icon_layout.addStretch() # Pushes the icon to stay on the left
            
        self.search_bar.textChanged.connect(self._filter_notes)
        
        self.list_notes = QListWidget()
        # ACTION: Removed the lambda to attach a robust error-catching method
        self.list_notes.itemDoubleClicked.connect(self._handle_note_open)
        
        btn_row = QHBoxLayout()
        
        # ACTION: Proper Native SVG Implementation
        btn_spawn_new = QPushButton()
        btn_spawn_new.setObjectName("ActionBtn")
        btn_spawn_new.setFixedWidth(36) 
        btn_spawn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Inject the custom #1A1A1A dark color to contrast the yellow background
        from ui.utils import load_colored_svg
        icon = load_colored_svg("plus.svg", "#1A1A1A")
        
        if not icon.isNull():
            btn_spawn_new.setIcon(icon)
            btn_spawn_new.setIconSize(QSize(16, 16)) # Scaled slightly to match the 12x12 minimalist aesthetic
        else:
            btn_spawn_new.setText("+") # Failsafe
            
        btn_spawn_new.setStyleSheet("""
            QPushButton { 
                background-color: #F1C40F; 
                border-radius: 6px; 
            }
            QPushButton:hover { background-color: #D4AC0D; }
        """)
        btn_spawn_new.clicked.connect(self._spawn_empty_note)
        
        self.btn_open_sel = QPushButton("Open")
        self.btn_open_sel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_sel.clicked.connect(self._open_marked_notes)
        
        self.btn_del_sel = QPushButton("Delete")
        self.btn_del_sel.setObjectName("DangerBtn")
        self.btn_del_sel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del_sel.clicked.connect(self._delete_marked_notes)
        
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

        # --- Export Vault Section ---
        export_container = QWidget()
        export_layout = QVBoxLayout(export_container)
        export_layout.setContentsMargins(16, 16, 16, 0)

        lbl_export = QLabel("Backup & Restore")
        lbl_export.setStyleSheet("color: #E0E0E0; font-size: 14px; font-weight: 600;")
        
        desc_export = QLabel(
            "Export an encrypted copy of your entire vault. "
            "You can restore this file on a new device using your current Master Password."
        )
        desc_export.setWordWrap(True)
        desc_export.setStyleSheet("font-size: 12px; color: #888888; margin-bottom: 5px;")

        btn_export = QPushButton("Export Secure Vault")
        btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export.setStyleSheet("""
            QPushButton { background: #3A3A3C; color: #E0E0E0; border: none; padding: 10px; border-radius: 6px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background: #4A4A4C; color: #FFF; }
        """)
        btn_export.clicked.connect(self._export_vault)

        # --- NEW: Crash Logs Button ---
        btn_export_logs = QPushButton("Export Crash Logs")
        btn_export_logs.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export_logs.setStyleSheet("""
            QPushButton { background: transparent; color: #F1C40F; border: 1px solid #F1C40F; padding: 10px; border-radius: 6px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background: rgba(241, 196, 15, 0.1); }
        """)
        btn_export_logs.clicked.connect(self._export_crash_logs)

        # Place them side-by-side
        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_export)
        btn_row.addWidget(btn_export_logs)

        export_layout.addWidget(lbl_export)
        export_layout.addWidget(desc_export)
        export_layout.addLayout(btn_row)

        l.addWidget(self.btn_toggle_security)
        l.addWidget(self.sec_container)
        l.addWidget(export_container) # Add the new container to the main layout
        l.addStretch()
        return w
    
    def _export_vault(self) -> None:
        import shutil
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from datetime import datetime

        # Suggest a filename with today's date
        date_str = datetime.now().strftime("%Y-%m-%d")
        suggested_name = f"Floaties_Backup_{date_str}.vault"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Encrypted Vault", suggested_name, "Floaties Vault (*.vault);;All Files (*)"
        )
        
        if file_path:
            try:
                # ACTION: Removed the encapsulation-breaking db.conn call.
                # Relying entirely on DatabaseManager's atomic writes.
                shutil.copy2(self.db.db_path, file_path)
                
                QMessageBox.information(
                    self, "Export Successful", 
                    "Your encrypted vault has been securely backed up.\n\nKeep this file safe!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Could not create backup: {e}")

    def _export_crash_logs(self) -> None:
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from datetime import datetime

        date_str = datetime.now().strftime("%Y-%m-%d")
        suggested_name = f"Floaties_CrashLogs_{date_str}.txt"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Crash Logs", suggested_name, "Text Files (*.txt);;All Files (*)",
            options=QFileDialog.Option.DontUseNativeDialog
        )
        
        if file_path:
            success = self.db.export_crash_logs(file_path)
            if success:
                QMessageBox.information(
                    self, "Export Successful", 
                    "Crash logs exported successfully.\n\nYou can securely share this file with the developer."
                )
            else:
                QMessageBox.information(
                    self, "System Stable", 
                    "There are no crash logs to export. Your application is perfectly healthy!"
                )

    def _build_about_view(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignmentFlag.AlignTop)
        l.setContentsMargins(16, 24, 16, 16)
        
        # 1. Branding Header
        title = QLabel("Floaties v1.0")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFF;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 2. Main Description
        desc = QLabel(
            "Floaties is a minimalist, local-first sticky note application designed "
            "for Linux and Windows. It was built to provide a clean, native experience "
            "without compromising on uncompromising offline security."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 13px; color: #A0A0A0; line-height: 1.5;")
        
        # 3. THE SECURITY PROMISE (Added here)
        security_pitch = QLabel(
            "<i>While most apps store your notes in plain text for anyone to see, Floaties treats your "
            "thoughts like physical valuables in a private safe. I used professional-grade encryption "
            "because I believe your personal ideas deserve to stay yours alone and invisible to hackers, "
            "other softwares, and even the operating system itself.</i>"
        )
        security_pitch.setWordWrap(True)
        security_pitch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Using the brand Yellow (#F1C40F) to make this promise pop
        security_pitch.setStyleSheet("""
            color: #F1C40F; 
            font-size: 12px; 
            line-height: 1.4; 
            margin-top: 10px; 
            padding: 10px;
        """)
        
        # 4. Support Button
        btn_donate = QPushButton("☕ Support the Developer")
        btn_donate.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_donate.setStyleSheet("""
            QPushButton { 
                background: #F1C40F; 
                color: #1A1A1A; 
                font-weight: bold; 
                padding: 12px; 
                font-size: 14px; 
                border-radius: 8px; 
                border: none; 
            }
            QPushButton:hover { background: #D4AC0D; }
        """)
        # ACTION: Removed the lambda to prevent silent C++ crashes on Wayland/Linux
        btn_donate.clicked.connect(self._open_support_link)
        
        l.addWidget(title)
        l.addSpacing(16)
        l.addWidget(desc)
        l.addWidget(security_pitch) # Injecting the pitch
        l.addSpacing(32)
        l.addWidget(btn_donate)
        l.addStretch()
        return w
    
    def _open_support_link(self) -> None:
        """Safely asks the native OS to open the default web browser."""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        try:
            # Safely hand off the URL to the operating system
            url = QUrl("https://ko-fi.com/therealazil")
            success = QDesktopServices.openUrl(url)
            
            if not success:
                print("OS refused to open the URL. (Check default browser settings)")
        except Exception as e:
            # If Wayland/Windows fails to find a browser, we catch it gracefully instead of crashing
            print(f"🚨 Browser routing failed: {e}")

    # --- Interaction Logic ---

    def _update_action_buttons_visibility(self) -> None:
        has_checked = len(self._get_marked_notes()) > 0
        self.btn_open_sel.setVisible(has_checked)
        self.btn_del_sel.setVisible(has_checked)

    def _toggle_security_accordion(self) -> None:
        is_vis = self.sec_container.isVisible()
        self.sec_container.setVisible(not is_vis)
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
        from ui.spawner import ACTIVE_NOTES
        for active_note in list(ACTIVE_NOTES):
            if active_note.db_id == note_data["id"]:
                active_note._is_being_deleted = True 
                active_note.close()
                
        self.db.delete_note(note_data["id"])
        self._refresh_notes_list()

    def _spawn_empty_note(self) -> None:
        self._launch_note_instance(None)
    
    # ERROR CATCHER TEMPORARY
    def _handle_note_open(self, item) -> None:
        """Robust wrapper to catch silent PyQt6 slot exceptions."""
        try:
            note_data = item.data(Qt.ItemDataRole.UserRole)
            self._launch_note_instance(note_data)
        except Exception as e:
            import traceback
            print("\n" + "="*40)
            print("🚨 REAL CRASH TRACEBACK REVEALED 🚨")
            traceback.print_exc()
            print("="*40 + "\n")
    # Save Notes: Dashboard Note Spawner Patch
# Target: ui/dashboard.py -> Dashboard class
# Action: Resolved SQLite NULL ID crash. Implemented decoupled O(1) theme cycling via event signals.

    def _launch_note_instance(self, note_data: dict | None) -> None:
        from main import StickyNote
        from ui.spawner import ACTIVE_NOTES
        from ui.toolbar import PRESET_THEMES, get_wcag_text_color
        
        if note_data:
            # Focus existing note if already active
            for active_note in ACTIVE_NOTES:
                if active_note.db_id == note_data["id"]:
                    active_note.raise_()
                    active_note.activateWindow()
                    return
            note = StickyNote(db=self.db, pwd=self.pwd, salt=self.salt, note_data=note_data)
        else:
            # 1. Clean Instantiation: Pass None to allow StickyNote to generate a valid DB ID securely
            note = StickyNote(db=self.db, pwd=self.pwd, salt=self.salt, note_data=None)
            
            # 2. O(1) Decoupled Theme Cycling
            if PRESET_THEMES:
                theme_count = len(PRESET_THEMES)
                # Action: Offset the cycle by 6 to ensure the first note is Charcoal/Black
                selected_theme = PRESET_THEMES[(len(ACTIVE_NOTES) + 6) % theme_count]
                
                bg_hex = selected_theme["bg"]
                border_hex = selected_theme["border"]
                text_hex = get_wcag_text_color(bg_hex)
                
                # Robustness: Emit through the existing event bus to prevent tight coupling and state mutation
                if hasattr(note, 'toolbar'):
                    note.toolbar.theme_color_changed.emit(bg_hex, border_hex, text_hex)
            
            # 3. Apply mathematical cascading for UI placement
            if ACTIVE_NOTES:
                last_note = list(ACTIVE_NOTES)[-1]
                note.move(last_note.x() + 30, last_note.y() + 30)
            else:
                note.move(self.x() + 50, self.y() + 50)
                
        note.note_saved.connect(self._refresh_notes_list)
        note.note_saved.connect(lambda: self.global_status.setText("All notes saved."))
        
        ACTIVE_NOTES.add(note)
        note.show()

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
            
        self.lbl_sec_status.setStyleSheet("color: #F1C40F;")
        self.lbl_sec_status.setText("Preparing...")
        QApplication.processEvents()
        
        from ui.spawner import ACTIVE_NOTES
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
            
            self.inp_curr_pwd.clear()
            self.inp_new_pwd.clear()
            self.inp_conf_pwd.clear()
            self.lbl_sec_status.setText("")
            
            # ACTION: Replaced native OS MessageBox with our custom branded dialog
            success_dialog = PasswordUpdatedDialog(new_rec_key, self)
            success_dialog.exec()
            
        except Exception as e:
            self._set_sec_err(f"CRITICAL ERROR: {str(e)}")

    def _set_sec_err(self, msg: str) -> None:
        self.lbl_sec_status.setStyleSheet("color: #FF453A;")
        self.lbl_sec_status.setText(msg)

    def closeEvent(self, event) -> None:
        from ui.spawner import ACTIVE_NOTES
        from PyQt6.QtWidgets import QApplication
        
        total_active = len(ACTIVE_NOTES)

        # ACTION: Intercept the close request if notes are open
        if total_active > 0:
            dialog = ExitConfirmDialog(total_active, self)
            dialog.exec()

            if dialog.choice == "cancel":
                event.ignore() # Stop the window from closing
                return
            elif dialog.choice == "minimize":
                event.ignore() # Stop the window from closing
                self.showMinimized() # Push it to the taskbar instead
                return
            elif dialog.choice == "exit":
                pass # Proceed downward to the save-and-close loop

        # --- The Standard Save & Close Loop ---
        notes_to_save = [
            n for n in ACTIVE_NOTES 
            if (hasattr(n, 'save_timer') and n.save_timer.isActive()) 
            or getattr(n, 'pending_save', False)
            or (n.save_worker is not None and n.save_worker.isRunning())
        ]
        total_to_save = len(notes_to_save)

        if total_to_save > 0:
            for i, note in enumerate(notes_to_save, 1):
                self.global_status.setStyleSheet("color: #F1C40F; font-size: 11px; padding-top: 8px;")
                self.global_status.setText(f"Closing... (Saving note {i}/{total_to_save})")
                QApplication.processEvents()
                
                note.force_sync_save_for_shutdown()
                note.close()
        
        for note in list(ACTIVE_NOTES):
            note.close()
            
        super().closeEvent(event)