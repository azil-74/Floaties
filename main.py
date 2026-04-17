import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGridLayout, QFrame, QSizeGrip, QDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QMoveEvent, QResizeEvent

from ui.toolbar import FormattingToolbar, PRESET_THEMES, get_wcag_text_color
from ui.header import DragHeader
from ui.spawner import ACTIVE_NOTES 
from ui.editor import SmartEditor 
from ui.highlighter import MarkdownHighlighter 

from database import DatabaseManager
from security import Vault
from ui.lockscreen import AuthFlowDialog
from ui.dashboard import Dashboard

import traceback

def global_exception_hook(exctype, value, tb):
    """Catches PyQt6 crashes, prints to terminal, and logs to the local database."""
    
    if exctype is KeyboardInterrupt:
        print("\n⚡ [Shield] Neutralized a ghost IDE KeyboardInterrupt. App continues running.\n")
        return

   
    traceback_str = "".join(traceback.format_exception(exctype, value, tb))
    
    print("\n" + "="*50)
    print("🚨 CRITICAL APPLICATION CRASH 🚨")
    print(traceback_str)
    print("="*50 + "\n")
    
    try:
        from database import DatabaseManager
        # Spin up an independent DB connection just for the crash report
        crash_db = DatabaseManager() 
        crash_db.log_crash(traceback_str)
    except Exception as e:
        print(f"Telemetry Failure: Could not save crash to DB. {e}")
        
    sys.exit(1)

sys.excepthook = global_exception_hook

class ModernSizeGrip(QSizeGrip):
    """Pure CSS Size Grip to bypass C++ QPainter deadlocks. Relies on native Cursor UX."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setStyleSheet("""
            QSizeGrip {
                background-color: transparent;
                width: 16px;
                height: 16px;
            }
        """)

class SaveWorker(QThread):
    """Isolated background thread for heavy Argon2id cryptography and SQLite I/O."""
    finished_save = pyqtSignal(object) 
    error_save = pyqtSignal(str)

    def __init__(self, db, pwd: str, salt: bytes, note_data: dict):
        super().__init__()
        self.db = db
        self.pwd = pwd
        self.salt = salt
        self.note_data = note_data # Contains raw text, NOT GUI objects

    def run(self) -> None:
        try:
            from security import Vault
            encrypted_content = Vault.encrypt(self.note_data["plain_text"], self.pwd, self.salt)
            self.note_data["content"] = encrypted_content
            del self.note_data["plain_text"]
            
            db_id = self.db.upsert_note(self.note_data)
            self.finished_save.emit(db_id)
        except Exception as e:
            self.error_save.emit(str(e))

class StickyNote(QMainWindow):
    """Core Sticky Note Window with Debounced DB Sync."""
    
    note_saved = pyqtSignal()

    def __init__(self, db: DatabaseManager, pwd: str, salt: bytes, theme_index: int = 6, note_data: dict | None = None) -> None:
        super().__init__()
        
        self.db = db
        self.pwd = pwd
        self.salt = salt
        self.db_id = note_data.get("id") if note_data else None
        
        self.is_rolled_up = False
        self._normal_height = 150 
        
        if note_data:
            self._current_theme_index = note_data.get("theme_index", theme_index)
        else:
            self._current_theme_index = theme_index
            
        self._init_ui()
        
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._sync_to_db)
        
        if note_data:
            self.move(note_data["pos_x"], note_data["pos_y"])
            self.resize(note_data["width"], note_data["height"])
            self._normal_height = note_data["height"]
            
            self.header.title_label.setText(note_data["title"])
            
            if note_data["content"]:
                self._cached_encrypted_content = note_data["content"]
                self.text_editor.setPlainText("Decrypting payload... (Please wait)")
                self.text_editor.setEnabled(False)
                
                # Bound timer prevents segfaults if window is closed instantly
                self.decrypt_timer = QTimer(self)
                self.decrypt_timer.setSingleShot(True)
                self.decrypt_timer.timeout.connect(self._execute_decryption)
                self.decrypt_timer.start(100)
            
            if note_data["is_rolled_up"]:
                self.toggle_rollup()
                
        # --- Attach Triggers (Post-Init to prevent boot-flooding) ---
        self.text_editor.textChanged.connect(self._trigger_save)
        self.header.title_changed.connect(self._trigger_save)
        self.save_worker = None
        self.pending_save = False
        

    def _init_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(150, 150)
        self.resize(200, 300) 

        self.setStyleSheet("QMainWindow { background: transparent; }")

        self.container = QFrame(self)
        self.container.setObjectName("NoteContainer")
        self.container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCentralWidget(self.container)

        theme = PRESET_THEMES[self._current_theme_index % len(PRESET_THEMES)]
        base_bg = theme["bg"]
        base_border = theme["border"]
        base_text = get_wcag_text_color(base_bg)
        accent_bg = QColor(base_bg).darker(115).name()

        self.container.setStyleSheet(f"#NoteContainer {{ background-color: {base_bg}; border: 1px solid {base_border}; border-radius: 8px; }}")

        self.header = DragHeader(self)
        self.header.set_theme(accent_bg, base_border, base_text)
        
        self.text_editor = SmartEditor(self.container)
        self.text_editor.setStyleSheet(f"background: transparent; border: none; padding: 8px; font-size: 14px; color: {base_text};")

        self.highlighter = MarkdownHighlighter(self.text_editor.document(), base_text)

        self.toolbar = FormattingToolbar(self.text_editor)
        self.toolbar.theme_color_changed.connect(self._update_theme_color)
        self.toolbar.set_theme(accent_bg, base_border, base_text)

        self.size_grip = ModernSizeGrip(self.container)

        main_layout = QGridLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self.header, 0, 0)
        main_layout.addWidget(self.text_editor, 1, 0)
        main_layout.addWidget(self.toolbar, 2, 0) 
        
        main_layout.addWidget(self.size_grip, 2, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        self.size_grip.raise_()
    
    def _execute_decryption(self) -> None:
        """Runs the heavy Argon2id decryption after the window has safely rendered."""
        try:
            decrypted_text = Vault.decrypt(self._cached_encrypted_content, self.pwd, self.salt)
            self.text_editor.setPlainText(decrypted_text)
        except ValueError:
            self.text_editor.setPlainText("[ERROR: Vault Decryption Failed]")
        finally:
            self.text_editor.setEnabled(True)
            self.text_editor.setFocus()
            
            if hasattr(self, '_cached_encrypted_content'):
                del self._cached_encrypted_content

    
    def _trigger_save(self) -> None:
        """Debounces continuous events to prevent SQL/I-O lockups."""
        if hasattr(self, 'save_timer'):
            self.save_timer.start(1000)

    
        self.save_worker = None
        self.pending_save = False
        
    
    def _sync_to_db(self) -> None:
        """Packages GUI state and dispatches it to the background cryptography thread."""
        if not hasattr(self, 'db') or not self.db:
            return

        if self.save_worker is not None and self.save_worker.isRunning():
            self.pending_save = True
            return

        raw_data = {
            "id": self.db_id,
            "title": self.header.title_label.text(),
            "plain_text": self.text_editor.toPlainText(),
            "theme_index": self._current_theme_index,
            "pos_x": self.pos().x(),
            "pos_y": self.pos().y(),
            "width": self.width(),
            "height": self._normal_height,
            "is_rolled_up": int(self.is_rolled_up)
        }

        
        self.save_worker = SaveWorker(self.db, self.pwd, self.salt, raw_data)
        self.save_worker.finished_save.connect(self._on_save_finished)
        
        self.save_worker.finished.connect(self.save_worker.deleteLater)
        self.save_worker.start()

    def _on_save_finished(self, new_db_id: int) -> None:
        """Callback executed strictly on the Main Thread when crypto finishes."""
        self.db_id = new_db_id
        self.note_saved.emit() 
        
        self.save_worker = None 
        
        if getattr(self, 'pending_save', False):
            self.pending_save = False
            self._sync_to_db()

    def moveEvent(self, event: QMoveEvent) -> None:
        super().moveEvent(event)
        self._trigger_save()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._trigger_save()

    def toggle_rollup(self) -> None:
        if not self.is_rolled_up:
            self._normal_height = self.height()
            self.text_editor.setVisible(False)
            self.toolbar.setVisible(False)
            self.size_grip.setVisible(False)
            self.is_rolled_up = True
            
            self.setMinimumSize(150, self.header.height())
            self.resize(self.width(), self.header.height())
        else:
            self.text_editor.setVisible(True)
            self.toolbar.setVisible(True)
            self.size_grip.setVisible(True)
            self.is_rolled_up = False
            
            self.setMinimumSize(150, 150)
            self.resize(self.width(), self._normal_height)
            
        self.header.window_controls.update_rollup_icon(self.is_rolled_up)
        self._trigger_save()

    def closeEvent(self, event) -> None:
        ACTIVE_NOTES.discard(self)
        
        real_title = self.header.title_label.text()
        
        if (self.save_worker is not None and self.save_worker.isRunning()) or \
           (hasattr(self, 'save_timer') and self.save_timer.isActive()) or \
           getattr(self, 'pending_save', False):
            self.header.title_label.setText("Securing...")
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
        
        
        self.force_sync_save_for_shutdown(real_title)
            
        super().closeEvent(event)

    def _update_theme_color(self, bg_hex: str, border_hex: str, text_hex: str) -> None:
        self.container.setStyleSheet(f"#NoteContainer {{ background-color: {bg_hex}; border: 1px solid {border_hex}; border-radius: 8px; }}")
        accent_bg = QColor(bg_hex).darker(115).name()
        
        self.header.set_theme(accent_bg, border_hex, text_hex)
        self.toolbar.set_theme(accent_bg, border_hex, text_hex)
        self.text_editor.setStyleSheet(f"background: transparent; border: none; padding: 8px; font-size: 14px; color: {text_hex};")
        
        for i, theme in enumerate(PRESET_THEMES):
            if theme["bg"] == bg_hex:
                self._current_theme_index = i
                break
        self._trigger_save()

    def force_sync_save_for_shutdown(self, actual_title: str | None = None) -> None:
        """Synchronous fallback exclusively for app shutdown."""
        
        if getattr(self, '_is_being_deleted', False):
            return

        if self.save_worker is not None and self.save_worker.isRunning():
            try:
                self.save_worker.finished_save.disconnect()
            except TypeError:
                pass
            self.save_worker.wait() 

        if (hasattr(self, 'save_timer') and self.save_timer.isActive()) or getattr(self, 'pending_save', False):
            if hasattr(self, 'save_timer'):
                self.save_timer.stop()
            
            from security import Vault
            plain_text = self.text_editor.toPlainText()
            encrypted_content = Vault.encrypt(plain_text, self.pwd, self.salt)
            
            final_title = actual_title if actual_title else self.header.title_label.text()
            
            data = {
                "id": self.db_id,
                "title": final_title,
                "content": encrypted_content,
                "theme_index": self._current_theme_index,
                "pos_x": self.pos().x(),
                "pos_y": self.pos().y(),
                "width": self.width(),
                "height": self._normal_height,
                "is_rolled_up": int(self.is_rolled_up)
            }
            self.db.upsert_note(data)

def main() -> None:
    if sys.platform == "win32":
        import ctypes
        myappid = 'floaties.app.core.1' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    QApplication.setQuitOnLastWindowClosed(False)
    app = QApplication(sys.argv)
    
    from PyQt6.QtGui import QIcon
    from pathlib import Path
    
    icon_path = Path(__file__).parent / "assets" / "Floaties.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    else:
        print(f"Warning: Icon not found at {icon_path}")
    # --------------------------------------
    
    db = DatabaseManager()

    if db.get_meta("salt") is None:
        from ui.onboarding import OnboardingDialog
        intro = OnboardingDialog()
        if intro.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)
            
    lock = AuthFlowDialog(db)
    if lock.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)
        
    pwd = lock.password
    salt = lock.salt
    
    if not pwd or not salt:
        sys.exit(1)
    
    global dashboard_instance 
    dashboard_instance = Dashboard(db=db, pwd=pwd, salt=salt)
    dashboard_instance.show()
    
    dashboard_instance.destroyed.connect(app.quit)
    QApplication.setQuitOnLastWindowClosed(True)
            
    sys.exit(app.exec())

def run_background_maintenance():
    """Independent thread for DB optimization and log purging."""
    import time
    from database import DatabaseManager

    time.sleep(5) 
    try:
        db = DatabaseManager()
        db.cleanup_old_logs(days=30)
        print("⚡ [Maintenance] 30-day crash log cleanup completed.")
    except Exception as e:
        print(f"Maintenance Thread Error: {e}")

if __name__ == "__main__":
    import threading
    # Launch maintenance as a daemon so it doesn't block app exit
    threading.Thread(target=run_background_maintenance, daemon=True).start()
    
    main()