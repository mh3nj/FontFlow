"""
FontFlow Studio - Main Window
Orchestrates the entire UI with keyboard handling
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                              QLabel, QStatusBar, QSplitter, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeyEvent, QFont
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
        
        # Initialize shortcut tooltips FIRST
        self._init_shortcut_tooltips()
        
        self.init_ui()
        
        # Load saved window state
        self._load_window_geometry()
        
        # Auto-save timer (every 30 seconds)
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start(30000)  # 30 seconds
    
    def _init_shortcut_tooltips(self):
        """Initialize shortcut tooltips"""
        self.shortcut_tooltips = {
            "1-5": "Primary category keys",
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
            "C": "Toggle comparison mode (side-by-side view)",
            "W": "Toggle weight stress test mode",
            "L": "Toggle logo test mode",
            "P": "Toggle Persian shaping stress mode",
            "Ctrl+L": "Open language selection settings",
            "Ctrl+K": "Open keyboard shortcut editor",
            "Ctrl+F": "Open search panel",
            "Ctrl+E": "Export HTML classification report",
            "F1": "Show this help dialog",
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
        
        # Top bar (library info)
        self.create_top_bar(main_layout)
        
        # Splitter for preview + comparison + search
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        
        # Left: Preview panel
        self.preview_panel = PreviewPanel()
        self.splitter.addWidget(self.preview_panel)
        
        # Right: Comparison panel (hidden by default)
        self.comparison_panel = ComparisonPanel(self.preview_panel.font_loader)
        self.comparison_panel.setVisible(False)
        self.splitter.addWidget(self.comparison_panel)
        
        # Search panel (created later, hidden by default)
        self.search_panel = None
        
        # Set initial sizes
        self.splitter.setSizes([1000, 0])
        
        main_layout.addWidget(self.splitter, stretch=1)
        
        # HUD overlay (positioned absolutely on preview panel)
        self.hud = IntelligenceHUD()
        
        # Bottom bar (keyboard hints)
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
        
        # Set initial status message
        self.status_bar.showMessage("Ready — Press F1 for help", 3000)
    
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
        
        # Library path
        self.library_label = QLabel(f"⚡ Library: {self.engine.session.library_root}")
        self.library_label.setFont(QFont("Consolas", FONT_SIZES['micro']))
        self.library_label.setStyleSheet(f"color: {COLORS['text_secondary']}; border: none;")
        self.library_label.setToolTip("Current font library location")
        layout.addWidget(self.library_label)
        
        layout.addStretch()
        
        # Stage indicator
        self.stage_indicator = QLabel("Stage A")
        self.stage_indicator.setFont(QFont("Segoe UI", FONT_SIZES['small'], QFont.Weight.Bold))
        self.stage_indicator.setStyleSheet(f"color: {COLORS['accent_primary']}; border: none;")
        self.stage_indicator.setToolTip("Current classification stage (Primary or Refine)")
        layout.addWidget(self.stage_indicator)
        
        # Speed indicator
        self.speed_indicator = QLabel(f"⏱ {self.engine.cycle_speed_ms}ms")
        self.speed_indicator.setFont(QFont("Consolas", FONT_SIZES['micro']))
        self.speed_indicator.setStyleSheet(f"color: {COLORS['text_dim']}; border: none; margin-left: 20px;")
        self.speed_indicator.setToolTip("Auto-cycle speed (use [/] to adjust)")
        layout.addWidget(self.speed_indicator)
        
        # Progress
        self.progress_indicator = QLabel(f"0 / {self.engine.total_families}")
        self.progress_indicator.setFont(QFont("Consolas", FONT_SIZES['micro']))
        self.progress_indicator.setStyleSheet(f"color: {COLORS['text_dim']}; border: none; margin-left: 20px;")
        self.progress_indicator.setToolTip("Classification progress")
        layout.addWidget(self.progress_indicator)
        
        parent_layout.addWidget(top_bar)
    
    def create_bottom_bar(self, parent_layout):
        """Create the bottom keyboard hints bar with organized grid layout"""
        bottom_bar = QWidget()
        bottom_bar.setMinimumHeight(110)
        bottom_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_secondary']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        
        # Main layout
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
        from PyQt6.QtWidgets import QGridLayout
        
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setHorizontalSpacing(20)
        
        # Define shortcut groups (key, description, tooltip_key)
        shortcuts = [
            # Row 1: Classification
            ("1-5", "Primary Categories", "1-5"),
            ("0", "Experimental", "0"),
            ("/", "Uncertain", "/"),
            ("Space", "Skip", "Space"),
            
            # Row 2: Navigation
            ("←/→", "Prev/Next Family", "←/→"),
            ("↑/↓", "Prev/Next Style", "↑/↓"),
            ("Ctrl+Z", "Undo", "Ctrl+Z"),
            ("Ctrl+Y", "Redo", "Ctrl+Y"),
            
            # Row 3: Speed & Zoom
            ("[/]", "Speed -/+", "[/]"),
            ("Ctrl+Scroll", "Zoom", "Ctrl+Scroll"),
            ("Ctrl+0", "Reset Zoom", "Ctrl+0"),
            
            # Row 4: Modes
            ("C", "Compare", "C"),
            ("W", "Weight Test", "W"),
            ("L", "Logo Test", "L"),
            ("P", "Persian Stress", "P"),
            
            # Row 5: Settings
            ("Ctrl+L", "Language", "Ctrl+L"),
            ("Ctrl+K", "Shortcuts", "Ctrl+K"),
            ("Ctrl+F", "Search", "Ctrl+F"),
            ("Ctrl+E", "Report", "Ctrl+E"),
        ]
        
        row = 0
        col = 0
        max_cols = 4
        
        for key, description, tooltip_key in shortcuts:
            # Key badge
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
            
            # Description label
            desc_label = QLabel(description)
            desc_label.setFont(QFont("Segoe UI", FONT_SIZES['micro']))
            desc_label.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
            
            # Container for this shortcut
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
        
        # Hint about customization
        hint_label = QLabel("💡 Tip: Press Ctrl+K to customize any shortcut  |  Ctrl+F to search fonts  |  Ctrl+E to export report  |  F1 for help")
        hint_label.setFont(QFont("Segoe UI", FONT_SIZES['micro']))
        hint_label.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(hint_label)
        
        parent_layout.addWidget(bottom_bar)
    
    def resizeEvent(self, event):
        """Position HUD when window resizes"""
        super().resizeEvent(event)
        
        # Position HUD in top-right of preview panel
        if hasattr(self, 'preview_panel') and hasattr(self, 'hud'):
            hud_x = self.preview_panel.width() - self.hud.width() - 20
            hud_y = 20
            self.hud.setParent(self.preview_panel)
            self.hud.move(hud_x, hud_y)
            self.hud.raise_()

    def wheelEvent(self, event):
        """Handle mouse wheel for zoom (with Ctrl key)"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl + Scroll = Zoom
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
        
        def on_shortcuts_changed(shortcuts):
            print("✅ Shortcuts updated - restart recommended for full effect")
            self.status_bar.showMessage("Shortcuts saved! Restart app for full effect.", 3000)
        
        editor.shortcuts_changed.connect(on_shortcuts_changed)
        editor.exec()
    
    def show_search(self):
        """Show search panel"""
        if not hasattr(self, 'search_panel') or self.search_panel is None:
            # Create search panel with all families
            all_families = []
            failed_families = []
            
            self.status_bar.showMessage("Loading fonts for search...", 2000)
            
            for i in range(len(self.engine.library.families)):
                try:
                    family = self.engine.library.get_family(i, parse=True)
                    if family:
                        all_families.append(family)
                    else:
                        failed_families.append(i)
                except Exception as e:
                    failed_families.append(i)
            
            if failed_families:
                print(f"⚠ Skipped {len(failed_families)} families with parsing errors")
            
            if not all_families:
                QMessageBox.warning(
                    self,
                    "No Fonts Found",
                    "No valid font families found for search.\n\n"
                    "This may happen if your font library contains only corrupt or unsupported fonts."
                )
                return
            
            self.search_panel = SearchPanel(all_families, self)
            self.search_panel.family_selected.connect(self.engine.jump_to_family)
            
            # Add to right side
            self.splitter.addWidget(self.search_panel)
            self.search_panel.hide()
        
        self.search_panel.show_search()
        self.status_bar.showMessage("Search panel open - type to filter fonts", 2000)
    
    def export_report(self):
        """Export classification report as HTML"""
        from PyQt6.QtWidgets import QFileDialog
        from utils.report_generator import ReportGenerator
        from datetime import datetime
        
        # Get save location
        default_name = f"fontflow_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            str(Path.home() / default_name),
            "HTML Files (*.html)"
        )
        
        if not file_path:
            return
        
        # Show progress dialog
        progress_msg = QMessageBox()
        progress_msg.setWindowTitle("Generating Report")
        progress_msg.setText("Scanning font families...")
        progress_msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress_msg.show()
        
        # Collect all families
        all_families = []
        for i in range(len(self.engine.library.families)):
            try:
                family = self.engine.library.get_family(i, parse=True)
                if family:
                    all_families.append(family)
            except Exception as e:
                print(f"⚠ Skipping family {i} for report: {e}")
        
        progress_msg.setText(f"Generating report for {len(all_families)} families...")
        
        try:
            generator = ReportGenerator(
                library_path=Path(self.engine.session.library_root),
                families=all_families,
                session_data={}
            )
            
            output_path = generator.generate_html_report(Path(file_path))
            progress_msg.accept()
            
            QMessageBox.information(
                self,
                "Report Complete",
                f"✅ Report saved successfully!\n\n📍 Location: {output_path}\n\n📊 {len(all_families)} families analyzed\n✓ {len([f for f in all_families if hasattr(f, 'classified') and f.classified])} classified"
            )
            
            self.status_bar.showMessage(f"Report exported: {output_path}", 5000)
            
        except Exception as e:
            progress_msg.accept()
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate report:\n\n{str(e)}"
            )
    
    # ═══════════════════════════════════════════════════════════════
    # WINDOW STATE MANAGEMENT
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
            <b>🎨 FontFlow Studio Help</b><br><br>
            <b>📋 Classification:</b><br>
            • 1-9,0 - Classify font into categories<br>
            • Space - Skip current font<br>
            • / - Mark as uncertain (moves to REVIEW_LATER)<br><br>
            <b>🎮 Navigation:</b><br>
            • ←/→ - Previous/Next family<br>
            • ↑/↓ - Manual style cycle<br>
            • Ctrl+Z/Y - Undo/Redo<br><br>
            <b>👁️ Viewing:</b><br>
            • Ctrl+Scroll - Zoom in/out<br>
            • Ctrl+0 - Reset zoom<br>
            • [/] - Adjust auto-cycle speed<br><br>
            <b>🎨 Special Modes:</b><br>
            • C - Comparison mode<br>
            • W - Weight stress test<br>
            • L - Logo test<br>
            • P - Persian stress test<br><br>
            <b>⚙️ Settings:</b><br>
            • Ctrl+K - Customize shortcuts<br>
            • Ctrl+L - Language settings<br>
            • Ctrl+F - Search fonts<br>
            • Ctrl+E - Export report<br>
            """
            QMessageBox.information(self, "FontFlow Help", help_text)
            return
        
        # Classification keys (1-9, 0)
        if Qt.Key.Key_1 <= key <= Qt.Key.Key_9:
            category_key = str(key - Qt.Key.Key_1 + 1)
            self.engine.classify(category_key)
            return
        
        if key == Qt.Key.Key_0:
            self.engine.classify("0")
            return
        
        # Flow control
        if key == Qt.Key.Key_Space:
            self.engine.skip_family()
            self.status_bar.showMessage("⏭ Skipped", 500)
            return
        
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
        
        # Navigation
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
        
        # ZOOM with Ctrl + / = and Ctrl + -
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
        
        # Language settings (Ctrl+L)
        if key == Qt.Key.Key_L and modifiers & Qt.KeyboardModifier.ControlModifier:
            self.preview_panel.show_language_settings()
            return

        # Shortcut editor (Ctrl+K)
        if key == Qt.Key.Key_K and modifiers & Qt.KeyboardModifier.ControlModifier:
            self.show_shortcut_editor()
            return
        
        # Search (Ctrl+F)
        if key == Qt.Key.Key_F and modifiers & Qt.KeyboardModifier.ControlModifier:
            self.show_search()
            return
        
        # Export report (Ctrl+E)
        if key == Qt.Key.Key_E and modifiers & Qt.KeyboardModifier.ControlModifier:
            self.export_report()
            return
        
        # Escape to close search panel
        if key == Qt.Key.Key_Escape:
            if hasattr(self, 'search_panel') and self.search_panel and self.search_panel.isVisible():
                self.search_panel.hide()
                self.status_bar.showMessage("Search closed", 1000)
                return
        
        # Pass to parent if not handled
        super().keyPressEvent(event)
    
    # ═══════════════════════════════════════════════════════════════
    # ENGINE EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════
    
    def on_family_changed(self, family):
        """Handle family change from engine"""
        self.preview_panel.set_family(family)
        self.hud.update_family(family)
        
        # Update search panel current index
        if hasattr(self, 'search_panel') and self.search_panel:
            self.search_panel.current_index = self.engine.current_family_index
        
        # Update window title with current family
        self.setWindowTitle(f"FontFlow Studio — {family.family_name} ({self.engine.current_family_index + 1}/{self.engine.total_families})")
        
        self.status_bar.showMessage(f"📁 Viewing: {family.family_name} ({family.style_count} styles)", 2000)
    
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
        
        # Update bottom hints based on stage
        if stage == "A":
            hints = []
            for key in ['1', '2', '3', '4', '5']:
                if key in self.engine.categories:
                    cat = self.engine.categories[key]
                    hints.append(f"[{key}] {cat.name}")
        else:
            hints = []
            for key in ['1', '2', '3', '4', '5']:
                if key in self.engine.subcategories:
                    subcat = self.engine.subcategories[key]
                    hints.append(f"[{key}] {subcat.name}")
        
        hints.append("[/] Uncertain")
        hints.append("[Space] Skip")
        hint_text = "  •  ".join(hints)
        if hasattr(self, 'hints_label'):
            self.hints_label.setText(hint_text)
    
    def on_progress_updated(self, current: int, total: int):
        """Handle progress update from engine"""
        percent = int((current + 1) / total * 100) if total > 0 else 0
        self.progress_indicator.setText(f"{current + 1} / {total} ({percent}%)")
        self.hud.update_progress(current, total)
    
    def on_mode_changed(self, mode: str, enabled: bool):
        """Handle mode toggle from engine"""
        if mode == "comparison":
            # Toggle comparison panel visibility
            self.comparison_panel.setVisible(enabled)
            if enabled:
                self.splitter.setSizes([700, 900])
                self.status_bar.showMessage("🔍 Comparison mode: ON - Select a folder to compare", 3000)
            else:
                self.splitter.setSizes([1000, 0])
                self.status_bar.showMessage("Comparison mode: OFF", 2000)
        
        elif mode == "weight":
            if enabled:
                self.preview_panel.set_mode("weight")
                self.status_bar.showMessage("💪 Weight Stress Test: ON", 2000)
            else:
                self.preview_panel.set_mode("normal")
                self.status_bar.showMessage("Normal mode", 2000)
        
        elif mode == "logo":
            if enabled:
                self.preview_panel.set_mode("logo")
                self.status_bar.showMessage("🏷️ Logo Test: ON", 2000)
            else:
                self.preview_panel.set_mode("normal")
                self.status_bar.showMessage("Normal mode", 2000)
        
        elif mode == "persian":
            if enabled:
                self.preview_panel.set_mode("persian")
                self.status_bar.showMessage("🕌 Persian Shaping Stress: ON", 2000)
            else:
                self.preview_panel.set_mode("normal")
                self.status_bar.showMessage("Normal mode", 2000)
    
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
