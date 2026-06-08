"""
FontFlow Studio - Main Window
Orchestrates the entire UI with keyboard handling
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                              QLabel, QStatusBar, QSplitter, QMessageBox,
                              QDialog, QPushButton)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeyEvent, QFont, QPixmap, QIcon
from pathlib import Path
import json

from ui.theme import COLORS, FONT_SIZES
from ui.preview_panel import PreviewPanel, IntelligenceHUD
from ui.comparison_panel import ComparisonPanel
from ui.search_panel import SearchPanel
from core.engine import FontFlowEngine


class MainWindow(QMainWindow):
    """
    Main application window for FontFlow Studio.
    Handles keyboard input and coordinates all UI components.
    """
    
    def __init__(self, engine: FontFlowEngine):
        super().__init__()
        
        self.engine = engine
        
        # Connect engine signals
        self.engine.family_changed.connect(self.on_family_changed)
        self.engine.style_changed.connect(self.on_style_changed)
        self.engine.speed_changed.connect(self.on_speed_changed)
        self.engine.stage_changed.connect(self.on_stage_changed)
        self.engine.progress_updated.connect(self.on_progress_updated)
        self.engine.mode_changed.connect(self.on_mode_changed)
        
        # Initialize shortcut tooltips
        self._init_shortcut_tooltips()
        
        self.init_ui()
        
        # Load saved window state
        self._load_window_geometry()
        
        # Auto-save timer (every 30 seconds)
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start(30000)
        
        # Set window icon
        self._set_window_icon()
        
        # Set focus policy to ensure keyboard works
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        print(f"\n🎮 Available categories: {list(self.engine.categories.keys())}")
        print(f"🎮 Available subcategories: {list(self.engine.subcategories.keys())}")
    
    def _set_window_icon(self):
        """Set window icon for title bar and taskbar"""
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
    
    def _init_shortcut_tooltips(self):
        """Initialize shortcut tooltips"""
        self.shortcut_tooltips = {
            "1-9": "Primary category keys (Stage A)",
            "0": "Experimental category",
            "/": "Mark as uncertain, move to review later",
            "Space": "Skip current font without classifying",
            "←/→": "Navigate to previous/next font family",
            "↑/↓": "Manually cycle through font styles",
            "Ctrl+Z": "Undo last classification",
            "Ctrl+Y": "Redo last undone classification",
            "[/]": "Decrease/Increase auto-cycle speed",
            "Ctrl+Scroll": "Zoom in/out (hold Ctrl and scroll)",
            "Ctrl+0": "Reset zoom to 100%",
            "C": "Toggle comparison mode",
            "W": "Toggle weight stress test mode",
            "L": "Toggle logo test mode",
            "P": "Toggle Persian shaping stress mode",
            "Ctrl+L": "Open language settings",
            "Ctrl+K": "Open keyboard shortcut editor",
            "Ctrl+F": "Open search panel",
            "Ctrl+E": "Export HTML report",
            "Ctrl+I": "About FontFlow",
            "F1": "Show help dialog",
        }
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("FontFlow Studio — Professional Font Curation")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top bar
        self.create_top_bar(main_layout)
        
        # Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        
        # Preview panel
        self.preview_panel = PreviewPanel()
        self.splitter.addWidget(self.preview_panel)
        
        # Comparison panel
        self.comparison_panel = ComparisonPanel(self.preview_panel.font_loader)
        self.comparison_panel.setVisible(False)
        self.splitter.addWidget(self.comparison_panel)
        
        self.search_panel = None
        self.splitter.setSizes([1000, 0])
        
        main_layout.addWidget(self.splitter, stretch=1)
        
        # HUD
        self.hud = IntelligenceHUD()
        
        # Bottom bar
        self.create_bottom_bar(main_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_dim']};
                padding: 4px;
            }}
        """)
        
        self.status_bar.showMessage("Ready — Press 1-9 to classify, F1 for help", 4000)
    
    def create_top_bar(self, parent_layout):
        """Create the top information bar"""
        top_bar = QWidget()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_secondary']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 0, 20, 0)
        
        self.library_label = QLabel(f"⚡ Library: {self.engine.session.library_root}")
        self.library_label.setFont(QFont("Consolas", FONT_SIZES['micro']))
        self.library_label.setStyleSheet(f"color: {COLORS['text_secondary']}; border: none;")
        self.library_label.setToolTip("Current font library location")
        layout.addWidget(self.library_label)
        
        layout.addStretch()
        
        self.stage_indicator = QLabel("Stage A")
        self.stage_indicator.setFont(QFont("Segoe UI", FONT_SIZES['small'], QFont.Weight.Bold))
        self.stage_indicator.setStyleSheet(f"color: {COLORS['accent_primary']}; border: none;")
        self.stage_indicator.setToolTip("Current classification stage (Primary or Refine)")
        layout.addWidget(self.stage_indicator)
        
        self.speed_indicator = QLabel(f"⏱ {self.engine.cycle_speed_ms}ms")
        self.speed_indicator.setFont(QFont("Consolas", FONT_SIZES['micro']))
        self.speed_indicator.setStyleSheet(f"color: {COLORS['text_dim']}; border: none; margin-left: 20px;")
        self.speed_indicator.setToolTip("Auto-cycle speed (use [/] to adjust)")
        layout.addWidget(self.speed_indicator)
        
        self.progress_indicator = QLabel(f"0 / {self.engine.total_families}")
        self.progress_indicator.setFont(QFont("Consolas", FONT_SIZES['micro']))
        self.progress_indicator.setStyleSheet(f"color: {COLORS['text_dim']}; border: none; margin-left: 20px;")
        self.progress_indicator.setToolTip("Classification progress")
        layout.addWidget(self.progress_indicator)
        
        parent_layout.addWidget(top_bar)
    
    def create_bottom_bar(self, parent_layout):
        """Create the bottom keyboard hints bar"""
        from PyQt6.QtWidgets import QGridLayout
        
        bottom_bar = QWidget()
        bottom_bar.setMinimumHeight(120)
        bottom_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_secondary']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        
        main_layout = QVBoxLayout(bottom_bar)
        main_layout.setContentsMargins(20, 8, 20, 8)
        main_layout.setSpacing(8)
        
        # Title
        title = QLabel("⌨️ KEYBOARD SHORTCUTS")
        title.setFont(QFont("Segoe UI", FONT_SIZES['micro'], QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['accent_primary']}; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setToolTip("All available keyboard shortcuts - customize with Ctrl+K")
        main_layout.addWidget(title)
        
        # Grid for shortcuts
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setHorizontalSpacing(20)
        
        shortcuts = [
            ("1-9", "Categories (A)", "1-9"),
            ("0", "Experimental", "0"),
            ("/", "Uncertain", "/"),
            ("Space", "Skip", "Space"),
            ("←/→", "Prev/Next Family", "←/→"),
            ("↑/↓", "Prev/Next Style", "↑/↓"),
            ("Ctrl+Z", "Undo", "Ctrl+Z"),
            ("Ctrl+Y", "Redo", "Ctrl+Y"),
            ("[/]", "Speed -/+", "[/]"),
            ("Ctrl+Scroll", "Zoom", "Ctrl+Scroll"),
            ("Ctrl+0", "Reset Zoom", "Ctrl+0"),
            ("C", "Compare", "C"),
            ("W", "Weight Test", "W"),
            ("L", "Logo Test", "L"),
            ("P", "Persian Stress", "P"),
            ("Ctrl+L", "Language", "Ctrl+L"),
            ("Ctrl+K", "Shortcuts", "Ctrl+K"),
            ("Ctrl+F", "Search", "Ctrl+F"),
            ("Ctrl+E", "Report", "Ctrl+E"),
            ("Ctrl+I", "About", "Ctrl+I"),
            ("F1", "Help", "F1"),
        ]
        
        row = 0
        col = 0
        max_cols = 4
        
        for key, description, tooltip_key in shortcuts:
            key_label = QLabel(key)
            key_label.setFont(QFont("Consolas", FONT_SIZES['micro'], QFont.Weight.Bold))
            key_label.setStyleSheet(f"""
                background-color: {COLORS['bg_panel']};
                color: {COLORS['accent_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 2px 6px;
                min-width: 70px;
            """)
            key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            key_label.setToolTip(self.shortcut_tooltips.get(tooltip_key, description))
            
            desc_label = QLabel(description)
            desc_label.setFont(QFont("Segoe UI", FONT_SIZES['micro']))
            desc_label.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
            
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(6)
            container_layout.addWidget(key_label)
            container_layout.addWidget(desc_label)
            container_layout.addStretch()
            
            grid.addWidget(container, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        main_layout.addLayout(grid)
        
        # Stage-specific hints
        self.stage_hints_label = QLabel()
        self.stage_hints_label.setFont(QFont("Segoe UI", FONT_SIZES['micro']))
        self.stage_hints_label.setStyleSheet(f"color: {COLORS['accent_primary']}; border: none;")
        self.stage_hints_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.stage_hints_label)
        
        self._update_stage_hints()
        
        parent_layout.addWidget(bottom_bar)
    
    def _update_stage_hints(self):
        """Update stage-specific hints"""
        if hasattr(self.engine, 'session') and self.engine.session.current_stage == "A":
            hints = []
            for key in ['1', '2', '3', '4', '5']:
                if key in self.engine.categories:
                    cat = self.engine.categories[key]
                    hints.append(f"[{key}] {cat.name}")
            self.stage_hints_label.setText("  •  ".join(hints) + "  •  ...")
            self.stage_hints_label.setToolTip("Press 1-9 to choose category")
        else:
            hints = []
            for key in ['1', '2', '3', '4', '5']:
                if key in self.engine.subcategories:
                    subcat = self.engine.subcategories[key]
                    hints.append(f"[{key}] {subcat.name}")
            self.stage_hints_label.setText("  •  ".join(hints))
            self.stage_hints_label.setToolTip("Press 1-5 to choose subcategory and MOVE files")
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'preview_panel') and hasattr(self, 'hud'):
            hud_x = self.preview_panel.width() - self.hud.width() - 20
            hud_y = 20
            self.hud.setParent(self.preview_panel)
            self.hud.move(hud_x, hud_y)
            self.hud.raise_()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.preview_panel.zoom_in()
                self.status_bar.showMessage(f"Zoom: {self.preview_panel.zoom_level:.1f}x", 1000)
            else:
                self.preview_panel.zoom_out()
                self.status_bar.showMessage(f"Zoom: {self.preview_panel.zoom_level:.1f}x", 1000)
            event.accept()
        else:
            super().wheelEvent(event)

    def show_shortcut_editor(self):
        """Open the keyboard shortcut editor"""
        from ui.shortcut_editor import ShortcutEditor
        editor = ShortcutEditor(self)
        editor.shortcuts_changed.connect(lambda s: self.status_bar.showMessage("Shortcuts saved! Restart app.", 3000))
        editor.exec()
    
    def show_search(self):
        """Show search panel"""
        if not hasattr(self, 'search_panel') or self.search_panel is None:
            all_families = []
            for i in range(len(self.engine.library.families)):
                try:
                    family = self.engine.library.get_family(i, parse=True)
                    if family:
                        all_families.append(family)
                except Exception:
                    pass
            
            if not all_families:
                QMessageBox.warning(self, "No Fonts Found", "No valid font families found for search.")
                return
            
            self.search_panel = SearchPanel(all_families, self)
            self.search_panel.family_selected.connect(self.engine.jump_to_family)
            self.splitter.addWidget(self.search_panel)
            self.search_panel.hide()
        
        self.search_panel.show_search()
    
    def export_report(self):
        """Export classification report as HTML"""
        from PyQt6.QtWidgets import QFileDialog
        from utils.report_generator import ReportGenerator
        from datetime import datetime
        
        default_name = f"fontflow_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", str(Path.home() / default_name), "HTML Files (*.html)"
        )
        
        if not file_path:
            return
        
        all_families = []
        for i in range(len(self.engine.library.families)):
            try:
                family = self.engine.library.get_family(i, parse=True)
                if family:
                    all_families.append(family)
            except Exception:
                pass
        
        try:
            generator = ReportGenerator(
                library_path=Path(self.engine.session.library_root),
                families=all_families,
                session_data={}
            )
            output_path = generator.generate_html_report(Path(file_path))
            QMessageBox.information(self, "Report Complete", f"Report saved to:\n{output_path}")
            self.status_bar.showMessage(f"Report exported: {output_path}", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report:\n{str(e)}")
    
    def show_about(self):
        """Show about dialog with logo"""
        about = QDialog(self)
        about.setWindowTitle("About FontFlow Studio")
        about.setFixedSize(500, 450)
        about.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_secondary']};
            }}
        """)
        
        layout = QVBoxLayout(about)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Logo
        logo_paths = [
            Path("assets/logo/logo-dark.png"),
            Path("assets/logo/logo-light.png"),
            Path("resources/icons/fontflow-128.png"),
            Path("resources/icons/fontflow.png"),
        ]
        
        logo_found = False
        for logo_path in logo_paths:
            if logo_path.exists():
                pixmap = QPixmap(str(logo_path))
                if not pixmap.isNull():
                    scaled = pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    logo_label = QLabel()
                    logo_label.setPixmap(scaled)
                    logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(logo_label)
                    logo_found = True
                    break
        
        if not logo_found:
            # Fallback text icon
            icon_label = QLabel("🎨")
            icon_label.setFont(QFont("Segoe UI", 64))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)
        
        # Title
        title = QLabel("FontFlow Studio")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['accent_primary']};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Version
        version = QLabel("Version 1.0")
        version.setFont(QFont("Segoe UI", 12))
        version.setStyleSheet(f"color: {COLORS['text_secondary']};")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        
        # Description
        desc = QLabel(
            "Professional Font Family Curation Tool\n\n"
            "Keyboard-driven · Persian-ready · Crash-proof\n\n"
            "Organize thousands of fonts in minutes."
        )
        desc.setFont(QFont("Segoe UI", 11))
        desc.setStyleSheet(f"color: {COLORS['text_primary']};")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Separator
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(separator)
        
        # Credits
        credits = QLabel("© 2026 Mohsen Jafari\nBuilt with PyQt6 and love")
        credits.setFont(QFont("Segoe UI", 10))
        credits.setStyleSheet(f"color: {COLORS['text_dim']};")
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits)
        
        # Website link
        website = QLabel('<a href="https://github.com/mh3nj/fontflow">github.com/mh3nj/fontflow</a>')
        website.setOpenExternalLinks(True)
        website.setStyleSheet(f"color: {COLORS['accent_primary']}; border: none;")
        website.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(website)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: {COLORS['bg_primary']};
                border: none;
                border-radius: 6px;
                padding: 10px 30px;
                font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_dim']};
            }}
        """)
        close_btn.clicked.connect(about.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        about.exec()
    
    # ═══════════════════════════════════════════════════════════════
    # WINDOW STATE
    # ═══════════════════════════════════════════════════════════════
    
    def _load_window_geometry(self):
        """Load saved window position and size"""
        try:
            config_path = Path("data/window_state.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    state = json.load(f)
                    self.resize(state.get('width', 1600), state.get('height', 1000))
                    self.move(state.get('x', 100), state.get('y', 100))
                    if state.get('maximized', False):
                        self.showMaximized()
        except Exception as e:
            print(f"Could not load window state: {e}")
    
    def _save_window_geometry(self):
        """Save window position and size"""
        try:
            config_path = Path("data/window_state.json")
            config_path.parent.mkdir(parents=True, exist_ok=True)
            state = {
                'width': self.width(),
                'height': self.height(),
                'x': self.x(),
                'y': self.y(),
                'maximized': self.isMaximized()
            }
            with open(config_path, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Could not save window state: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # KEYBOARD HANDLING
    # ═══════════════════════════════════════════════════════════════
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle all keyboard input"""
        key = event.key()
        modifiers = event.modifiers()
        
        # F1 for help
        if key == Qt.Key.Key_F1:
            help_text = """
            <b>FontFlow Studio Help</b><br><br>
            <b>Classification:</b><br>
            • 1-9 - Choose category (Stage A)<br>
            • Then 1-5 - Choose subcategory (Stage B) - FILES MOVE!<br>
            • Space - Skip current font<br>
            • / - Mark as uncertain (moves to REVIEW_LATER)<br><br>
            <b>Navigation:</b><br>
            • ←/→ - Previous/Next family<br>
            • ↑/↓ - Manual style cycle<br>
            • Ctrl+Z/Y - Undo/Redo<br><br>
            <b>Viewing:</b><br>
            • Ctrl+Scroll - Zoom in/out<br>
            • Ctrl+0 - Reset zoom<br>
            • [/] - Adjust auto-cycle speed<br><br>
            <b>Modes:</b><br>
            • C - Comparison mode<br>
            • W - Weight stress test<br>
            • L - Logo test<br>
            • P - Persian stress test<br><br>
            <b>Settings:</b><br>
            • Ctrl+K - Customize shortcuts<br>
            • Ctrl+L - Language settings<br>
            • Ctrl+F - Search fonts<br>
            • Ctrl+E - Export report<br>
            • Ctrl+I - About FontFlow<br>
            """
            QMessageBox.information(self, "FontFlow Help", help_text)
            return
        
        # Classification keys (1-9, 0)
        if key == Qt.Key.Key_1:
            self.engine.classify("1")
            self._update_stage_hints()
            return
        if key == Qt.Key.Key_2:
            self.engine.classify("2")
            self._update_stage_hints()
            return
        if key == Qt.Key.Key_3:
            self.engine.classify("3")
            self._update_stage_hints()
            return
        if key == Qt.Key.Key_4:
            self.engine.classify("4")
            self._update_stage_hints()
            return
        if key == Qt.Key.Key_5:
            self.engine.classify("5")
            self._update_stage_hints()
            return
        if key == Qt.Key.Key_6:
            self.engine.classify("6")
            self._update_stage_hints()
            return
        if key == Qt.Key.Key_7:
            self.engine.classify("7")
            self._update_stage_hints()
            return
        if key == Qt.Key.Key_8:
            self.engine.classify("8")
            self._update_stage_hints()
            return
        if key == Qt.Key.Key_9:
            self.engine.classify("9")
            self._update_stage_hints()
            return
        if key == Qt.Key.Key_0:
            self.engine.classify("0")
            self._update_stage_hints()
            return
        
        # Space - Skip
        if key == Qt.Key.Key_Space:
            self.engine.skip_family()
            self.status_bar.showMessage("⏭ Skipped", 500)
            return
        
        # Slash - Uncertain
        if key == Qt.Key.Key_Slash:
            self.engine.mark_uncertain()
            self.status_bar.showMessage("⚠ Marked for review", 500)
            return
        
        # Undo/Redo
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_Z:
                self.engine.undo()
                self.status_bar.showMessage("↩ Undo", 500)
                return
            if key == Qt.Key.Key_Y:
                self.engine.redo()
                self.status_bar.showMessage("↪ Redo", 500)
                return
        
        # Speed control
        if key == Qt.Key.Key_BracketLeft:
            self.engine.slow_down()
            self.status_bar.showMessage(f"🐢 Speed: {self.engine.cycle_speed_ms}ms", 1000)
            return
        if key == Qt.Key.Key_BracketRight:
            self.engine.speed_up()
            self.status_bar.showMessage(f"🐇 Speed: {self.engine.cycle_speed_ms}ms", 1000)
            return
        
        # Navigation arrows
        if key == Qt.Key.Key_Left:
            self.engine.prev_family()
            return
        if key == Qt.Key.Key_Right:
            self.engine.next_family()
            return
        if key == Qt.Key.Key_Up:
            self.engine.prev_style()
            return
        if key == Qt.Key.Key_Down:
            self.engine.next_style()
            return
        
        # Zoom with Ctrl
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_Equal or key == Qt.Key.Key_Plus:
                self.preview_panel.zoom_in()
                self.status_bar.showMessage(f"🔍 Zoom: {self.preview_panel.zoom_level:.1f}x", 1000)
                return
            if key == Qt.Key.Key_Minus:
                self.preview_panel.zoom_out()
                self.status_bar.showMessage(f"🔍 Zoom: {self.preview_panel.zoom_level:.1f}x", 1000)
                return
            if key == Qt.Key.Key_0:
                self.preview_panel.reset_zoom()
                self.status_bar.showMessage("🔍 Zoom reset to 100%", 1000)
                return
        
        # Mode toggles
        if key == Qt.Key.Key_C:
            self.engine.toggle_comparison_mode()
            return
        if key == Qt.Key.Key_W:
            self.engine.toggle_weight_test_mode()
            return
        if key == Qt.Key.Key_L:
            self.engine.toggle_logo_test_mode()
            return
        if key == Qt.Key.Key_P:
            self.engine.toggle_persian_stress_mode()
            return
        
        # Settings with Ctrl
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_L:
                self.preview_panel.show_language_settings()
                return
            if key == Qt.Key.Key_K:
                self.show_shortcut_editor()
                return
            if key == Qt.Key.Key_F:
                self.show_search()
                return
            if key == Qt.Key.Key_E:
                self.export_report()
                return
            if key == Qt.Key.Key_I:
                self.show_about()
                return
        
        # Escape to close search
        if key == Qt.Key.Key_Escape:
            if hasattr(self, 'search_panel') and self.search_panel and self.search_panel.isVisible():
                self.search_panel.hide()
                self.status_bar.showMessage("Search closed", 1000)
                return
        
        super().keyPressEvent(event)
    
    # ═══════════════════════════════════════════════════════════════
    # ENGINE EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════
    
    def on_family_changed(self, family):
        """Handle family change from engine"""
        self.preview_panel.set_family(family)
        self.hud.update_family(family)
        
        if hasattr(self, 'search_panel') and self.search_panel:
            self.search_panel.current_index = self.engine.current_family_index
        
        self.setWindowTitle(f"FontFlow Studio — {family.family_name} ({self.engine.current_family_index + 1}/{self.engine.total_families})")
        
        stage = self.engine.session.current_stage
        if stage == "A":
            self.status_bar.showMessage(f"📁 {family.family_name} - Press 1-9 to choose category", 3000)
        else:
            self.status_bar.showMessage(f"📁 {family.family_name} - Press 1-5 to choose subcategory", 3000)
    
    def on_style_changed(self):
        """Handle style cycle from engine"""
        self.preview_panel.update_style()
    
    def on_speed_changed(self, speed_ms: int):
        """Handle speed change from engine"""
        self.speed_indicator.setText(f"⏱ {speed_ms}ms")
        self.hud.update_speed(speed_ms)
    
    def on_stage_changed(self, stage: str):
        """Handle classification stage change"""
        stage_text = "📋 Stage A: Primary" if stage == "A" else "🎯 Stage B: Refine"
        self.stage_indicator.setText(stage_text)
        self.hud.update_stage(stage)
        self._update_stage_hints()
        
        if stage == "A":
            self.status_bar.showMessage("Stage A: Press 1-9 to choose category", 2000)
        else:
            self.status_bar.showMessage("Stage B: Press 1-5 to choose subcategory (files will move)", 3000)
    
    def on_progress_updated(self, current: int, total: int):
        """Handle progress update from engine"""
        percent = int((current + 1) / total * 100) if total > 0 else 0
        self.progress_indicator.setText(f"{current + 1} / {total} ({percent}%)")
        self.hud.update_progress(current, total)
    
    def on_mode_changed(self, mode: str, enabled: bool):
        """Handle mode toggle from engine"""
        if mode == "comparison":
            self.comparison_panel.setVisible(enabled)
            if enabled:
                self.splitter.setSizes([700, 900])
                self.status_bar.showMessage("Comparison mode: ON", 3000)
            else:
                self.splitter.setSizes([1000, 0])
                self.status_bar.showMessage("Comparison mode: OFF", 2000)
        elif mode == "weight":
            self.preview_panel.set_mode("weight" if enabled else "normal")
            self.status_bar.showMessage("Weight Stress Test: ON" if enabled else "Normal mode", 2000)
        elif mode == "logo":
            self.preview_panel.set_mode("logo" if enabled else "normal")
            self.status_bar.showMessage("Logo Test: ON" if enabled else "Normal mode", 2000)
        elif mode == "persian":
            self.preview_panel.set_mode("persian" if enabled else "normal")
            self.status_bar.showMessage("Persian Stress: ON" if enabled else "Normal mode", 2000)
    
    # ═══════════════════════════════════════════════════════════════
    # SESSION MANAGEMENT
    # ═══════════════════════════════════════════════════════════════
    
    def autosave(self):
        """Auto-save session state"""
        from core.session import SessionManager
        session_mgr = SessionManager(Path("data/sessions"))
        session_mgr.current_session = self.engine.session
        session_mgr.save_current()
        print("💾 Auto-saved session")
    
    def closeEvent(self, event):
        """Handle window close - save session and window state"""
        self._save_window_geometry()
        print("\n📝 Saving session before exit...")
        self.autosave()
        self.engine.shutdown()
        print("👋 FontFlow Studio closed. Have a great day!")
        event.accept()