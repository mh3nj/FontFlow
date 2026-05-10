"""
FontFlow Studio - Language Selection Settings
Allows users to choose which languages to display
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QCheckBox, QPushButton, QScrollArea, QFrame,
                              QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Set, List, Dict

from ui.theme import COLORS, FONT_SIZES


class LanguageSettingsPanel(QWidget):
    """
    Panel for users to select which languages to show.
    Can be accessed via Settings menu or keyboard shortcut.
    """
    
    # Signal when language selection changes
    languages_changed = pyqtSignal(set)  # Emits set of selected language codes
    
    # All available language scripts with display info
    AVAILABLE_LANGUAGES: Dict[str, dict] = {
        'latin': {'name': 'English / Latin', 'emoji': '🔤', 'group': 'European', 'default': True},
        'latin_extended': {'name': 'European Extended', 'emoji': '🌍', 'group': 'European', 'default': False},
        'cyrillic': {'name': 'Russian / Cyrillic', 'emoji': '🇷🇺', 'group': 'European', 'default': False},
        'greek': {'name': 'Greek', 'emoji': '🇬🇷', 'group': 'European', 'default': False},
        'arabic': {'name': 'Arabic', 'emoji': '🇸🇦', 'group': 'Middle East', 'default': True},
        'arabic_persian': {'name': 'Persian (Farsi)', 'emoji': '🇮🇷', 'group': 'Middle East', 'default': True},
        'hebrew': {'name': 'Hebrew', 'emoji': '🇮🇱', 'group': 'Middle East', 'default': False},
        'devanagari': {'name': 'Hindi / Devanagari', 'emoji': '🇮🇳', 'group': 'South Asian', 'default': False},
        'bengali': {'name': 'Bengali', 'emoji': '🇧🇩', 'group': 'South Asian', 'default': False},
        'gurmukhi': {'name': 'Punjabi / Gurmukhi', 'emoji': '🇮🇳', 'group': 'South Asian', 'default': False},
        'gujarati': {'name': 'Gujarati', 'emoji': '🇮🇳', 'group': 'South Asian', 'default': False},
        'tamil': {'name': 'Tamil', 'emoji': '🇮🇳', 'group': 'South Asian', 'default': False},
        'telugu': {'name': 'Telugu', 'emoji': '🇮🇳', 'group': 'South Asian', 'default': False},
        'kannada': {'name': 'Kannada', 'emoji': '🇮🇳', 'group': 'South Asian', 'default': False},
        'malayalam': {'name': 'Malayalam', 'emoji': '🇮🇳', 'group': 'South Asian', 'default': False},
        'sinhala': {'name': 'Sinhala', 'emoji': '🇱🇰', 'group': 'South Asian', 'default': False},
        'thai': {'name': 'Thai', 'emoji': '🇹🇭', 'group': 'Southeast Asian', 'default': False},
        'lao': {'name': 'Lao', 'emoji': '🇱🇦', 'group': 'Southeast Asian', 'default': False},
        'tibetan': {'name': 'Tibetan', 'emoji': '🇹🇮', 'group': 'East Asian', 'default': False},
        'georgian': {'name': 'Georgian', 'emoji': '🇬🇪', 'group': 'Caucasian', 'default': False},
        'armenian': {'name': 'Armenian', 'emoji': '🇦🇲', 'group': 'Caucasian', 'default': False},
        'hangul': {'name': 'Korean / Hangul', 'emoji': '🇰🇷', 'group': 'East Asian', 'default': False},
        'hiragana': {'name': 'Japanese Hiragana', 'emoji': '🇯🇵', 'group': 'East Asian', 'default': False},
        'katakana': {'name': 'Japanese Katakana', 'emoji': '🇯🇵', 'group': 'East Asian', 'default': False},
        'cjk': {'name': 'Chinese / CJK', 'emoji': '🇨🇳', 'group': 'East Asian', 'default': False},
        'emoji': {'name': 'Emoji', 'emoji': '😊', 'group': 'Symbols', 'default': True},
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.selected_languages: Set[str] = set()
        self.checkboxes: Dict[str, QCheckBox] = {}
        
        self.init_ui()
        self.load_defaults()
    
    def init_ui(self):
        """Initialize the settings panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("🌍 Language Display Settings")
        title.setFont(QFont("Segoe UI", FONT_SIZES['h3'], QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['accent_primary']};")
        layout.addWidget(title)
        
        subtitle = QLabel(
            "Select which language scripts to show in the preview panel.\n"
            "Fonts will only show languages they actually support."
        )
        subtitle.setFont(QFont("Segoe UI", FONT_SIZES['small']))
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        
        # Scroll area for languages
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                background-color: {COLORS['bg_secondary']};
            }}
        """)
        
        # Container widget
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)
        
        # Group languages by region
        groups = self._group_by_region()
        
        for group_name, languages in groups.items():
            group_box = QGroupBox(group_name)
            group_box.setStyleSheet(f"""
                QGroupBox {{
                    font-weight: bold;
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                    margin-top: 10px;
                    padding-top: 10px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }}
            """)
            
            grid_layout = QGridLayout(group_box)
            grid_layout.setSpacing(8)
            
            row = 0
            col = 0
            for code, info in languages:
                checkbox = QCheckBox(f"{info['emoji']} {info['name']}")
                checkbox.setStyleSheet(f"""
                    QCheckBox {{
                        color: {COLORS['text_primary']};
                        spacing: 8px;
                    }}
                    QCheckBox::indicator {{
                        width: 16px;
                        height: 16px;
                    }}
                """)
                checkbox.stateChanged.connect(lambda state, c=code: self._on_language_toggled(c, state))
                
                self.checkboxes[code] = checkbox
                grid_layout.addWidget(checkbox, row, col)
                
                col += 1
                if col >= 3:  # 3 columns per row
                    col = 0
                    row += 1
            
            container_layout.addWidget(group_box)
        
        scroll.setWidget(container)
        layout.addWidget(scroll, stretch=1)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.setStyleSheet(self._button_style())
        select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Select None")
        select_none_btn.setStyleSheet(self._button_style())
        select_none_btn.clicked.connect(self.select_none)
        button_layout.addWidget(select_none_btn)
        
        select_common_btn = QPushButton("Common Only")
        select_common_btn.setStyleSheet(self._button_style())
        select_common_btn.clicked.connect(self.select_common_only)
        button_layout.addWidget(select_common_btn)
        
        button_layout.addStretch()
        
        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: {COLORS['bg_primary']};
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_dim']};
            }}
        """)
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(self._button_style())
        cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _button_style(self) -> str:
        """Style for secondary buttons"""
        return f"""
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                border-color: {COLORS['accent_dim']};
            }}
        """
    
    def _group_by_region(self) -> dict:
        """Group languages by region for organized display"""
        groups = {}
        for code, info in self.AVAILABLE_LANGUAGES.items():
            group = info['group']
            if group not in groups:
                groups[group] = []
            groups[group].append((code, info))
        
        # Sort groups
        group_order = ['European', 'Middle East', 'South Asian', 'Southeast Asian', 'East Asian', 'Caucasian', 'Symbols']
        sorted_groups = {}
        for group in group_order:
            if group in groups:
                sorted_groups[group] = groups[group]
        
        return sorted_groups
    
    def load_defaults(self):
        """Load default language selections"""
        self.selected_languages.clear()
        for code, info in self.AVAILABLE_LANGUAGES.items():
            if info.get('default', False):
                self.selected_languages.add(code)
                if code in self.checkboxes:
                    self.checkboxes[code].setChecked(True)
    
    def _on_language_toggled(self, code: str, state):
        """Handle language checkbox toggle"""
        if state == Qt.CheckState.Checked.value:
            self.selected_languages.add(code)
        else:
            self.selected_languages.discard(code)
    
    def select_all(self):
        """Select all languages"""
        for code in self.AVAILABLE_LANGUAGES:
            self.selected_languages.add(code)
            if code in self.checkboxes:
                self.checkboxes[code].setChecked(True)
    
    def select_none(self):
        """Select no languages - defaults to Latin only"""
        self.selected_languages.clear()
        # Always keep Latin as fallback
        self.selected_languages.add('latin')
        for code, checkbox in self.checkboxes.items():
            checkbox.setChecked(code == 'latin')
    
    def select_common_only(self):
        """Select only commonly used languages"""
        common = ['latin', 'arabic', 'arabic_persian', 'cyrillic', 'emoji']
        self.selected_languages.clear()
        for code in common:
            self.selected_languages.add(code)
            if code in self.checkboxes:
                self.checkboxes[code].setChecked(True)
        # Uncheck others
        for code, checkbox in self.checkboxes.items():
            if code not in common:
                checkbox.setChecked(False)
    
    def save_settings(self):
        """Save selected languages and emit signal"""
        self.languages_changed.emit(self.selected_languages.copy())
        print(f"✅ Language settings saved: {len(self.selected_languages)} languages selected")
        print(f"   Selected: {', '.join(sorted(self.selected_languages))}")
        self.close()


class LanguageFilter:
    """
    Filters font language samples based on user preferences.
    """
    
    def __init__(self):
        self.selected_languages: Set[str] = set()
        self._load_preferences()
    
    def _load_preferences(self):
        """Load saved language preferences"""
        # Default: Latin + Persian + Emoji
        default = {'latin', 'arabic_persian', 'emoji'}
        
        try:
            from pathlib import Path
            import json
            
            config_path = Path("data/language_preferences.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    self.selected_languages = set(data.get('selected_languages', default))
            else:
                self.selected_languages = default
        except Exception as e:
            print(f"Could not load language preferences: {e}")
            self.selected_languages = default
    
    def save_preferences(self):
        """Save language preferences to disk"""
        try:
            from pathlib import Path
            import json
            
            config_path = Path("data/language_preferences.json")
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump({
                    'selected_languages': list(self.selected_languages)
                }, f, indent=2)
        except Exception as e:
            print(f"Could not save language preferences: {e}")
    
    def set_selected_languages(self, languages: Set[str]):
        """Update selected languages"""
        self.selected_languages = languages
        self.save_preferences()
    
    def filter_samples(self, samples: Dict[str, str], max_samples: int = 3) -> List[str]:
        """
        Filter language samples based on user preferences.
        
        Args:
            samples: Dictionary of script_code -> sample_text
            max_samples: Maximum number of samples to return
            
        Returns:
            List of sample texts (up to max_samples)
        """
        if not self.selected_languages:
            # Default to Latin if nothing selected
            return [samples.get('latin', 'The Quick Brown Fox')][:max_samples]
        
        # Priority order for display
        priority = ['latin', 'arabic_persian', 'arabic', 'cyrillic', 'devanagari', 'hangul', 'cjk']
        
        filtered = []
        
        # First, get user-selected languages in priority order
        for script in priority:
            if script in self.selected_languages and script in samples and len(filtered) < max_samples:
                filtered.append(samples[script])
        
        # Then, get any other selected languages
        if len(filtered) < max_samples:
            for script in sorted(self.selected_languages):
                if script not in priority and script in samples and len(filtered) < max_samples:
                    filtered.append(samples[script])
        
        # Fallback to Latin if nothing matched
        if not filtered and 'latin' in samples:
            filtered.append(samples['latin'])
        
        return filtered[:max_samples]
    
    def should_show_script(self, script_code: str) -> bool:
        """Check if a script should be displayed"""
        return script_code in self.selected_languages


# Global instance
_language_filter = None

def get_language_filter() -> LanguageFilter:
    """Get global language filter instance"""
    global _language_filter
    if _language_filter is None:
        _language_filter = LanguageFilter()
    return _language_filter
