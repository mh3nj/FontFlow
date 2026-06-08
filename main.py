"""
FontFlow Studio - Main Entry Point
Professional font family curation tool with lazy loading
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QProgressBar, QSplashScreen
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap

from ui.theme import apply_dark_theme, COLORS, FONT_SIZES
from core.session import SessionManager
from core.fast_library import FastFontLibrary
import yaml


class ScanWorker(QThread):
    """Background thread for scanning fonts (non-blocking)"""
    
    progress = pyqtSignal(int, int)  # current, total
    finished_scan = pyqtSignal(object)  # library object
    error = pyqtSignal(str)
    
    def __init__(self, library_path: Path):
        super().__init__()
        self.library_path = library_path
    
    def run(self):
        try:
            library = FastFontLibrary(self.library_path)
            families = library.fast_scan(
                progress_callback=lambda cur, total: self.progress.emit(cur, total)
            )
            self.finished_scan.emit(library)
        except Exception as e:
            self.error.emit(str(e))


class FontFlowApp(QMainWindow):
    """Main application window with lazy loading support"""
    
    def __init__(self):
        super().__init__()
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize session manager
        self.session_manager = SessionManager(Path("data/sessions"))
        
        # Font library (will be loaded after selecting directory)
        self.font_library: FastFontLibrary = None
        self.session = None
        self.scan_worker = None
        
        # Setup UI
        self.init_ui()
        
        # Set window icon
        self.set_window_icon()
    
    def set_window_icon(self):
        """Set the window icon for title bar and taskbar"""
        icon_paths = [
            Path("resources/icons/favicon.ico"),
            Path("resources/icons/fontflow.png"),
            Path("resources/icons/android-chrome-192x192.png"),
            Path("resources/icons/android-chrome-512x512.png"),
            Path("resources/icons/apple-touch-icon.png"),
            Path("resources/icons/favicon-32x32.png"),
        ]
        
        for icon_path in icon_paths:
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
                print(f"✓ Window icon loaded: {icon_path}")
                return
        
        print("⚠ No icon found in resources/icons/")
    
    def load_config(self) -> dict:
        """Load configuration from config.yaml"""
        config_path = Path("config.yaml")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("FontFlow Studio")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Welcome screen
        title = QLabel("FontFlow Studio")
        title.setFont(QFont("Segoe UI", FONT_SIZES['h1']))
        title.setStyleSheet(f"color: {COLORS['accent_primary']};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Professional Font Family Curation")
        subtitle.setFont(QFont("Segoe UI", FONT_SIZES['body']))
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-bottom: 40px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Select folder button
        select_btn = QPushButton("Select Font Library Folder")
        select_btn.setFont(QFont("Segoe UI", FONT_SIZES['small']))
        select_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: {COLORS['bg_primary']};
                border: none;
                border-radius: 8px;
                padding: 16px 32px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_dim']};
            }}
        """)
        select_btn.clicked.connect(self.select_library_folder)
        select_btn.setMaximumWidth(400)
        layout.addWidget(select_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Progress bar for scanning
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                text-align: center;
                color: {COLORS['text_primary']};
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent_primary']};
                border-radius: 3px;
            }}
        """)
        self.progress_bar.setMaximumWidth(400)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Progress label
        self.progress_label = QLabel("")
        self.progress_label.setFont(QFont("Consolas", FONT_SIZES['micro']))
        self.progress_label.setStyleSheet(f"color: {COLORS['text_dim']}; margin-top: 10px;")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        # Instructions
        instructions = QLabel(
            "Select a folder containing font files (.ttf, .otf, .woff2)\n"
            "FontFlow will scan and organize them for you.\n\n"
            "✨ Lazy loading enabled: Scans instantly, parses fonts on demand ✨"
        )
        instructions.setFont(QFont("Segoe UI", FONT_SIZES['small']))
        instructions.setStyleSheet(f"color: {COLORS['text_dim']}; margin-top: 20px;")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions)
        
        # Recent sessions (if any)
        recent_sessions = self.session_manager.list_recent_sessions(3)
        if recent_sessions:
            recent_label = QLabel("\nRecent Libraries:")
            recent_label.setFont(QFont("Segoe UI", FONT_SIZES['small']))
            recent_label.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-top: 40px;")
            layout.addWidget(recent_label, alignment=Qt.AlignmentFlag.AlignCenter)
            
            for session_info in recent_sessions:
                recent_btn = QPushButton(f"{session_info['library_root']}")
                recent_btn.setFont(QFont("Consolas", FONT_SIZES['micro']))
                recent_btn.setStyleSheet(f"color: {COLORS['text_dim']}; text-align: left;")
                recent_btn.clicked.connect(
                    lambda checked, path=session_info['library_root']: self.load_library(Path(path))
                )
                layout.addWidget(recent_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def select_library_folder(self):
        """Open folder selection dialog"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Font Library Folder",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.load_library(Path(folder))
    
    def load_library(self, library_path: Path):
        """Load a font library with lazy loading"""
        print(f"\n🚀 Loading library with lazy loading: {library_path}")
        
        # Disable UI during load
        self.centralWidget().setEnabled(False)
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setVisible(True)
        self.progress_label.setText("Scanning file structure... (fast mode)")
        self.statusBar().showMessage(f"Scanning {library_path} for font files...")
        
        # Start background scan
        self.scan_worker = ScanWorker(library_path)
        self.scan_worker.progress.connect(self.on_scan_progress)
        self.scan_worker.finished_scan.connect(self.on_scan_finished)
        self.scan_worker.error.connect(self.on_scan_error)
        self.scan_worker.start()
    
    def on_scan_progress(self, current: int, total: int):
        """Update progress bar during scan"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.progress_label.setText(f"Found {current} font files...")
            self.statusBar().showMessage(f"Scanning: {current}/{total} files")
    
    def on_scan_finished(self, library: FastFontLibrary):
        """Handle scan completion"""
        self.font_library = library
        
        # Hide progress UI
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # Get stats
        stats = self.font_library.get_stats()
        
        if stats['total_families'] == 0:
            self.statusBar().showMessage("No font families found in selected folder", 5000)
            self.centralWidget().setEnabled(True)
            return
        
        # Load or create session
        self.session = self.session_manager.load_or_create(library.root_path)
        
        # Show success message
        self.statusBar().showMessage(
            f"✅ Loaded {stats['total_families']} font families | "
            f"{stats['total_font_files']} font files | "
            f"Lazy mode: {stats['cached_families']}/{stats['cache_limit']} cached | "
            f"Memory: ~{stats['total_families'] * 0.01:.0f}MB estimated",
            8000
        )
        
        print(f"\n📊 Library Stats:")
        print(f"   Families: {stats['total_families']}")
        print(f"   Font files: {stats['total_font_files']}")
        print(f"   Cache limit: {stats['cache_limit']} families")
        print(f"   Lazy loading: ENABLED (parsing on demand)")
        
        # Show main interface
        self.show_main_interface()
    
    def on_scan_error(self, error_msg: str):
        """Handle scan error"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.statusBar().showMessage(f"❌ Error: {error_msg}", 8000)
        self.centralWidget().setEnabled(True)
        print(f"Scan error: {error_msg}")
    
    def show_main_interface(self):
        """Switch to the main curation interface"""
        from core.engine import FontFlowEngine
        from ui.main_window import MainWindow
        
        # Create config with lazy loading flag
        self.config['lazy_loading'] = True
        
        # Create the engine with fast library
        self.engine = FontFlowEngine(
            library=self.font_library,
            session=self.session,
            config=self.config
        )
        
        # Set lazy loading flag on engine
        self.engine.use_lazy_loading = True
        
        # Create and show the main window
        self.main_window = MainWindow(self.engine)
        self.main_window.show()
        
        # Initialize engine (starts auto-cycling)
        self.engine.initialize()
        
        # Hide the startup window
        self.hide()
    
    def closeEvent(self, event):
        """Handle application close - save session"""
        if self.session:
            print("💾 Saving session...")
            self.session_manager.save_current()
        
        # Clean up scan worker if running
        if self.scan_worker and self.scan_worker.isRunning():
            self.scan_worker.quit()
            self.scan_worker.wait()
        
        event.accept()


def show_splash_screen():
    """Show splash screen while loading"""
    splash_path = Path("assets/logo/splash.png")
    if splash_path.exists():
        pixmap = QPixmap(str(splash_path))
        splash = QSplashScreen(pixmap)
        splash.show()
        QApplication.processEvents()
        return splash
    return None


def main():
    """Application entry point"""
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("FontFlow Studio")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("FontFlow")
    
    # Set application icon (for taskbar/dock)
    icon_paths = [
        Path("resources/icons/favicon.ico"),
        Path("resources/icons/fontflow.png"),
        Path("resources/icons/android-chrome-192x192.png"),
    ]
    for icon_path in icon_paths:
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
            break
    
    # Set Fusion style for cross-platform consistency
    app.setStyle("Fusion")
    
    # Apply dark theme
    apply_dark_theme(app)
    
    # Show splash screen
    splash = show_splash_screen()
    if splash:
        splash.show()
        app.processEvents()
    
    # Create and show main window
    window = FontFlowApp()
    window.show()
    
    # Close splash screen
    if splash:
        splash.finish(window)
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()