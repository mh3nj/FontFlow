"""
FontFlow Studio - Language Selector
Allows users to choose which language samples to display in preview
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QComboBox, QPushButton, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import List, Dict

from ui.theme import COLORS, FONT_SIZES


class LanguageSelector(QWidget):
    """Language selection widget for preview panel"""
    
    language_changed = pyqtSignal(str, str)  # (language_code, language_name)
    
    # Available languages with sample text
    LANGUAGES = {
        'english': {'name': 'English', 'sample': 'The Quick Brown Fox Jumps Over The Lazy Dog', 'emoji': '🇬🇧'},
        'german': {'name': 'Deutsch', 'sample': 'Zwölf Boxkämpfer joggen quer über die große Sylter Deich', 'emoji': '🇩🇪'},
        'french': {'name': 'Français', 'sample': 'Portez ce vieux whisky au juge blond qui fume', 'emoji': '🇫🇷'},
        'spanish': {'name': 'Español', 'sample': 'El veloz murciélago hindú comía feliz cardillo y kiwi', 'emoji': '🇪🇸'},
        'italian': {'name': 'Italiano', 'sample': 'Ma la volpe, col suo balzo, ha raggiunto il quieto Fido', 'emoji': '🇮🇹'},
        'portuguese': {'name': 'Português', 'sample': 'Luís argüia à Júlia que «brações, fé, chá, óxido, pôr, zângão»', 'emoji': '🇵🇹'},
        'russian': {'name': 'Русский', 'sample': 'Съешь же ещё этих мягких французских булок, да выпей чаю', 'emoji': '🇷🇺'},
        'greek': {'name': 'Ελληνικά', 'sample': 'Θα σας δω σήμερα στην παραλία', 'emoji': '🇬🇷'},
        'arabic': {'name': 'العربية', 'sample': 'السلام عليكم ورحمة الله وبركاته', 'emoji': '🇸🇦'},
        'persian': {'name': 'فارسی', 'sample': 'درود بر جهان هنر و تایپوگرافی', 'emoji': '🇮🇷'},
        'hebrew': {'name': 'עברית', 'sample': 'שלום עולם', 'emoji': '🇮🇱'},
        'hindi': {'name': 'हिन्दी', 'sample': 'नमस्ते दुनिया', 'emoji': '🇮🇳'},
        'korean': {'name': '한국어', 'sample': '안녕하세요 세계', 'emoji': '🇰🇷'},
        'japanese': {'name': '日本語', 'sample': 'こんにちは世界', 'emoji': '🇯🇵'},
        'chinese': {'name': '中文', 'sample': '你好世界', 'emoji': '🇨🇳'},
        'emoji': {'name': 'Emoji', 'sample': '😀 😃 😄 😁 😆 😅 😂 🤣', 'emoji': '😊'},
    }
    
    def __init__(self, parent=None, default_language='english'):
        super().__init__(parent)
        self.default_language = default_language
        self.current_language = default_language
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Language label
        label = QLabel("🌍 Preview Language:")
        label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: {FONT_SIZES['micro']}px;")
        layout.addWidget(label)
        
        # Language dropdown
        self.combo = QComboBox()
        for code, info in self.LANGUAGES.items():
            self.combo.addItem(f"{info['emoji']} {info['name']}", code)
        
        self.combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: {FONT_SIZES['micro']}px;
                min-width: 120px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {COLORS['text_secondary']};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['bg_hover']};
            }}
        """)
        self.combo.currentIndexChanged.connect(self._on_language_changed)
        layout.addWidget(self.combo)
        
        # Also add a second language selector (for dual preview)
        layout.addSpacing(20)
        
        label2 = QLabel("+ Secondary:")
        label2.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: {FONT_SIZES['micro']}px;")
        layout.addWidget(label2)
        
        self.combo2 = QComboBox()
        self.combo2.addItem("None", None)
        for code, info in self.LANGUAGES.items():
            self.combo2.addItem(f"{info['emoji']} {info['name']}", code)
        self.combo2.setStyleSheet(self.combo.styleSheet())
        self.combo2.currentIndexChanged.connect(self._on_secondary_changed)
        layout.addWidget(self.combo2)
    
    def _on_language_changed(self, index):
        code = self.combo.currentData()
        if code:
            self.current_language = code
            info = self.LANGUAGES.get(code, {})
            self.language_changed.emit(code, info.get('name', code))
    
    def _on_secondary_changed(self, index):
        code = self.combo2.currentData()
        if code:
            info = self.LANGUAGES.get(code, {})
            self.language_changed.emit(code, info.get('name', code))
    
    def get_current_sample(self) -> str:
        """Get sample text for current language"""
        info = self.LANGUAGES.get(self.current_language, {})
        return info.get('sample', 'The Quick Brown Fox')
    
    def get_secondary_sample(self) -> str:
        """Get sample text for secondary language"""
        code = self.combo2.currentData()
        if code:
            info = self.LANGUAGES.get(code, {})
            return info.get('sample', '')
        return ""