"""
FontFlow Studio - Preview Panel
Auto-cycling font preview with dual language selector
Includes special rendering modes: Weight Test, Logo Test, Persian Stress
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import Optional

from models.font_family import FontFamily, FontStyle
from ui.theme import COLORS, FONT_SIZES
from utils.text_samples import TextSamples
from utils.persian_text import TextSampleProvider, PersianTextHandler
from utils.font_loader import FontLoader
from ui.rendering_modes import WeightStressTestMode, LogoTestMode, PersianStressMode
from ui.language_settings import get_language_filter, LanguageSettingsPanel
from ui.language_selector import LanguageSelector


class PreviewPanel(QWidget):
    """
    Main preview panel showing auto-cycling font styles.
    Left panel in the main window with working zoom.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_family: Optional[FontFamily] = None
        self.current_style: Optional[FontStyle] = None
        
        # Font loader for actual font files
        self.font_loader = FontLoader()
        
        # Current mode
        self.current_mode = "normal"
        
        # Zoom settings
        self.zoom_level = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 3.0
        
        # Label references (will be set in _create_normal_mode)
        self.top_label = None
        self.bottom_label = None
        self.top_language_selector = None
        self.bottom_language_selector = None
        
        self.init_ui()
        self._load_zoom_setting()
    
    def init_ui(self):
        """Initialize the UI with stacked modes"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Stacked widget to switch between modes
        self.mode_stack = QStackedWidget()
        
        # Create all rendering modes
        self.normal_mode = self._create_normal_mode()
        self.weight_mode = WeightStressTestMode(self.font_loader)
        self.logo_mode = LogoTestMode(self.font_loader)
        self.persian_mode = PersianStressMode(self.font_loader)
        
        # Add modes to stack
        self.mode_stack.addWidget(self.normal_mode)
        self.mode_stack.addWidget(self.weight_mode)
        self.mode_stack.addWidget(self.logo_mode)
        self.mode_stack.addWidget(self.persian_mode)
        
        main_layout.addWidget(self.mode_stack)
    
    def _create_normal_mode(self) -> QWidget:
        """Create the normal preview mode with dual language samples"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # === TOP PREVIEW AREA ===
        top_container = QWidget()
        top_layout = QVBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)
        
        # Language selector for top area
        self.top_language_selector = LanguageSelector()
        self.top_language_selector.language_changed.connect(self._on_top_language_changed)
        top_layout.addWidget(self.top_language_selector, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Top preview label
        self.top_label = QLabel()
        self.top_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.top_label.setWordWrap(True)
        self.top_label.setStyleSheet(f"color: {COLORS['text_primary']}; padding: 20px;")
        top_layout.addWidget(self.top_label, stretch=1)
        
        layout.addWidget(top_container, stretch=1)
        
        # === BOTTOM PREVIEW AREA ===
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)
        
        # Language selector for bottom area
        self.bottom_language_selector = LanguageSelector()
        self.bottom_language_selector.language_changed.connect(self._on_bottom_language_changed)
        bottom_layout.addWidget(self.bottom_language_selector, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Bottom preview label
        self.bottom_label = QLabel()
        self.bottom_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.bottom_label.setWordWrap(True)
        self.bottom_label.setStyleSheet(f"color: {COLORS['text_primary']}; padding: 20px;")
        bottom_layout.addWidget(self.bottom_label, stretch=1)
        
        layout.addWidget(bottom_container, stretch=1)
        
        # Set default texts
        self.top_label.setText("The Quick Brown Fox Jumps Over The Lazy Dog")
        self.bottom_label.setText(PersianTextHandler.prepare_text("طراحی تایپوگرافی حرفه‌ای نیازمند دقت است"))
        
        return widget
    
    def _on_top_language_changed(self, language_code: str, language_name: str):
        """Handle top language change"""
        if language_code:
            sample = self.top_language_selector.get_current_sample()
            secondary = self.top_language_selector.get_secondary_sample()
            
            if secondary:
                self.top_label.setText(f"{sample}\n\n{secondary}")
            else:
                self.top_label.setText(sample)
            
            # Re-apply current font with zoom
            self._apply_font_with_zoom()
    
    def _on_bottom_language_changed(self, language_code: str, language_name: str):
        """Handle bottom language change"""
        if language_code:
            sample = self.bottom_language_selector.get_current_sample()
            secondary = self.bottom_language_selector.get_secondary_sample()
            
            if secondary:
                self.bottom_label.setText(f"{sample}\n\n{secondary}")
            else:
                self.bottom_label.setText(sample)
            
            # Re-apply current font with zoom
            self._apply_font_with_zoom()
    
    def _apply_font_with_zoom(self):
        """Apply current font to both labels with zoom level"""
        if not self.current_family or not self.current_style:
            print("⚠ Cannot apply font: no current family/style")
            return
        
        # Force reload of current style
        self.current_style = self.current_family.current_style
        
        # Calculate font size with zoom
        base_size = FONT_SIZES['body']
        font_size = int(base_size * self.zoom_level)
        
        print(f"🎨 Applying font: {self.current_style.style_name} at {font_size}px (zoom: {self.zoom_level:.1f}x)")
        
        try:
            actual_font = self.font_loader.get_font_for_style(self.current_style, font_size)
            
            if actual_font:
                self.top_label.setFont(actual_font)
                self.bottom_label.setFont(actual_font)
                print(f"✓ Font applied successfully")
            else:
                fallback_font = self.font_loader.get_system_fallback(
                    size=font_size,
                    weight=self.current_style.weight,
                    italic=self.current_style.is_italic
                )
                self.top_label.setFont(fallback_font)
                self.bottom_label.setFont(fallback_font)
                print(f"⚠ Using fallback font at {font_size}px")
        except Exception as e:
            print(f"✗ Error applying font: {e}")
            # Ultimate fallback
            fallback_font = QFont("Segoe UI", font_size)
            self.top_label.setFont(fallback_font)
            self.bottom_label.setFont(fallback_font)
    
    def set_family(self, family: FontFamily):
        """Set the current family to preview"""
        self.current_family = family
        self.current_style = family.current_style
        
        # Update background color
        bg_color = family.bg_color
        text_color = family.text_color
        
        bg = QColor(*bg_color)
        text = QColor(*text_color)
        
        self.setStyleSheet(f"""
            PreviewPanel {{
                background-color: rgb({bg.red()}, {bg.green()}, {bg.blue()});
            }}
        """)
        
        # Update both labels
        label_style = f"""
            color: rgb({text.red()}, {text.green()}, {text.blue()});
            padding: 20px;
        """
        self.top_label.setStyleSheet(label_style)
        self.bottom_label.setStyleSheet(label_style)
        
        # Update all modes
        self.weight_mode.set_family(family, bg_color, text_color)
        self.logo_mode.set_family(family, bg_color, text_color)
        self.persian_mode.set_family(family, bg_color, text_color)
        
        # Apply font with zoom
        self._apply_font_with_zoom()
    
    def set_mode(self, mode: str):
        """Switch rendering mode"""
        self.current_mode = mode
        
        mode_map = {
            "normal": 0,
            "weight": 1,
            "logo": 2,
            "persian": 3,
        }
        
        if mode in mode_map:
            self.mode_stack.setCurrentIndex(mode_map[mode])
            print(f"Switched to {mode} mode")
        
        # Update fonts for the active mode
        if self.current_family:
            if mode == "normal":
                self._apply_font_with_zoom()
            elif mode == "weight":
                self.weight_mode.set_family(
                    self.current_family,
                    self.current_family.bg_color,
                    self.current_family.text_color
                )
            elif mode == "logo":
                self.logo_mode.set_family(
                    self.current_family,
                    self.current_family.bg_color,
                    self.current_family.text_color
                )
            elif mode == "persian":
                self.persian_mode.set_family(
                    self.current_family,
                    self.current_family.bg_color,
                    self.current_family.text_color
                )
    
    def update_style(self):
        """Update the displayed font style (called by engine on cycle)"""
        if not self.current_family:
            return
        
        self.current_style = self.current_family.current_style
        print(f"🎨 Cycling to style: {self.current_style.style_name}")
        self._apply_font_with_zoom()
    
    # ═══════════════════════════════════════════════════════════════
    # ZOOM CONTROLS
    # ═══════════════════════════════════════════════════════════════
    
    def set_zoom(self, zoom_level: float):
        """Set zoom level (0.5 to 3.0)"""
        new_zoom = max(self.min_zoom, min(self.max_zoom, zoom_level))
        
        if new_zoom == self.zoom_level:
            return
        
        self.zoom_level = new_zoom
        font_size = int(FONT_SIZES['body'] * self.zoom_level)
        
        print(f"🔍 Zoom set to {self.zoom_level:.1f}x (font size: {font_size}px)")
        
        # Re-apply font to both labels
        if self.current_family and self.current_style:
            self._apply_font_with_zoom()
        
        # Save to config
        self._save_zoom_setting()
    
    def zoom_in(self):
        """Increase zoom level by 0.1"""
        new_zoom = min(self.max_zoom, self.zoom_level + 0.1)
        self.set_zoom(new_zoom)
    
    def zoom_out(self):
        """Decrease zoom level by 0.1"""
        new_zoom = max(self.min_zoom, self.zoom_level - 0.1)
        self.set_zoom(new_zoom)
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.set_zoom(1.0)
    
    def _load_zoom_setting(self):
        """Load saved zoom from config"""
        try:
            from pathlib import Path
            import json
            config_path = Path("data/settings.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    settings = json.load(f)
                    saved_zoom = settings.get('zoom_level', 1.0)
                    self.zoom_level = saved_zoom
                    print(f"📂 Loaded zoom setting: {self.zoom_level:.1f}x")
        except Exception as e:
            print(f"Could not load zoom setting: {e}")
    
    def _save_zoom_setting(self):
        """Save zoom level to config"""
        try:
            from pathlib import Path
            import json
            config_path = Path("data/settings.json")
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            settings = {}
            if config_path.exists():
                with open(config_path, 'r') as f:
                    settings = json.load(f)
            
            settings['zoom_level'] = self.zoom_level
            
            with open(config_path, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Could not save zoom setting: {e}")
    
    def show_language_settings(self):
        """Show language selection dialog"""
        settings = LanguageSettingsPanel()
        
        def on_languages_changed(languages):
            lang_filter = get_language_filter()
            lang_filter.set_selected_languages(languages)
        
        settings.languages_changed.connect(on_languages_changed)
        settings.setWindowFlags(Qt.WindowType.Window)
        settings.setWindowTitle("Language Display Settings")
        settings.resize(600, 500)
        settings.show()


class IntelligenceHUD(QWidget):
    """
    Font intelligence overlay showing metadata and progress.
    Appears in the top-right of the preview panel.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_family: Optional[FontFamily] = None
        self.current_index = 0
        self.total_families = 0
        self.current_stage = "A"
        self.cycle_speed_ms = 1000
        
        self.setFixedWidth(320)
        self.setStyleSheet(f"""
            IntelligenceHUD {{
                background-color: {COLORS['bg_panel']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize HUD layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Family name
        self.family_name_label = QLabel("—")
        self.family_name_label.setFont(QFont("Segoe UI", FONT_SIZES['small'], QFont.Weight.Bold))
        self.family_name_label.setStyleSheet(f"color: {COLORS['accent_primary']};")
        self.family_name_label.setWordWrap(True)
        layout.addWidget(self.family_name_label)
        
        # Style info
        self.style_info_label = QLabel()
        self.style_info_label.setFont(QFont("Consolas", FONT_SIZES['micro']))
        self.style_info_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.style_info_label)
        
        # Language support
        self.language_label = QLabel()
        self.language_label.setFont(QFont("Consolas", FONT_SIZES['micro']))
        self.language_label.setStyleSheet(f"color: {COLORS['text_dim']};")
        self.language_label.setWordWrap(True)
        layout.addWidget(self.language_label)
        
        # Separator
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(separator)
        
        # Progress
        self.progress_label = QLabel()
        self.progress_label.setFont(QFont("Consolas", FONT_SIZES['micro']))
        self.progress_label.setStyleSheet(f"color: {COLORS['text_dim']};")
        layout.addWidget(self.progress_label)
        
        # Stage indicator
        self.stage_label = QLabel()
        self.stage_label.setFont(QFont("Segoe UI", FONT_SIZES['micro'], QFont.Weight.Bold))
        self.stage_label.setStyleSheet(f"color: {COLORS['accent_primary']};")
        layout.addWidget(self.stage_label)
        
        # Speed indicator
        self.speed_label = QLabel()
        self.speed_label.setFont(QFont("Consolas", FONT_SIZES['micro']))
        self.speed_label.setStyleSheet(f"color: {COLORS['text_dim']};")
        layout.addWidget(self.speed_label)
        
        layout.addStretch()
    
    def update_family(self, family: FontFamily):
        """Update HUD with new family info"""
        self.current_family = family
        
        self.family_name_label.setText(family.family_name)
        
        if not family.supported_scripts:
            family.detect_supported_languages()
        
        style_info = (
            f"{family.style_count} styles\n"
            f"{family.weight_range_name}\n"
            f"{'✓ Variable font' if family.has_variable else ''}"
        )
        self.style_info_label.setText(style_info)
        
        if family.supported_scripts:
            script_names = []
            name_map = {
                'latin': 'Latin', 'cyrillic': 'Cyrillic', 'greek': 'Greek',
                'arabic': 'Arabic', 'arabic_persian': 'Persian', 'hebrew': 'Hebrew',
                'devanagari': 'Devanagari', 'hangul': 'Korean', 'cjk': 'Chinese',
                'emoji': 'Emoji'
            }
            for script in family.supported_scripts[:4]:
                display_name = name_map.get(script, script.capitalize())
                script_names.append(display_name)
            
            language_text = f"🌍 {', '.join(script_names)}"
            if len(family.supported_scripts) > 4:
                language_text += f" +{len(family.supported_scripts) - 4}"
            self.language_label.setText(language_text)
        else:
            self.language_label.setText("🌍 Latin only")
    
    def update_progress(self, current: int, total: int):
        """Update progress indicator"""
        self.current_index = current
        self.total_families = total
        percent = int((current + 1) / total * 100) if total > 0 else 0
        self.progress_label.setText(f"Progress: {current + 1} / {total} ({percent}%)")
    
    def update_stage(self, stage: str):
        """Update classification stage"""
        self.current_stage = stage
        stage_text = "📋 Stage A: Primary" if stage == "A" else "🎯 Stage B: Refine"
        self.stage_label.setText(stage_text)
    
    def update_speed(self, speed_ms: int):
        """Update cycle speed display"""
        self.cycle_speed_ms = speed_ms
        speed_text = f"⚡ {speed_ms}ms"
        if speed_ms <= 500:
            speed_text += " (Fast)"
        elif speed_ms >= 3000:
            speed_text += " (Slow)"
        self.speed_label.setText(speed_text)
