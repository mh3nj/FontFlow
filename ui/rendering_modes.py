"""
FontFlow Studio - Rendering Modes
Special rendering modes for font evaluation
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialog, QLineEdit
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from typing import Optional, List

from models.font_family import FontFamily, FontStyle
from ui.theme import COLORS, FONT_SIZES
from utils.persian_text import TextSampleProvider, PersianTextHandler
from utils.font_loader import FontLoader


class WeightStressTestMode(QWidget):
    """
    Weight Stress Test Mode
    
    Shows multiple weights simultaneously to test:
    - Scalability across sizes
    - Contrast stability
    - Text survivability at different weights
    """
    
    def __init__(self, font_loader: FontLoader, parent=None):
        super().__init__(parent)
        
        self.font_loader = font_loader
        self.current_family: Optional[FontFamily] = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the weight test layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(40)
        
        # Headline (Heavy weight)
        self.headline_label = QLabel("Breaking Headlines Daily")
        self.headline_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.headline_label.setWordWrap(True)
        layout.addWidget(self.headline_label)
        
        # Body paragraph (Regular weight)
        self.body_label = QLabel(
            "Professional typography requires attention to detail and an "
            "understanding of how type performs across various contexts. "
            "Great typefaces balance form and function, ensuring readability "
            "while maintaining visual interest throughout longer passages of text."
        )
        self.body_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.body_label.setWordWrap(True)
        layout.addWidget(self.body_label, stretch=2)
        
        # UI microcopy (Light/Medium weight)
        self.ui_label = QLabel("Button · Link · Metadata · 12:34 PM · Settings · Help")
        self.ui_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.ui_label)
        
        # Persian paragraph (if supported)
        self.persian_label = QLabel(
            PersianTextHandler.prepare_text(
                "طراحی تایپوگرافی حرفه‌ای نیازمند دقت و توجه به جزئیات است. "
                "فونت‌های خوب باید در تمام اندازه‌ها به خوبی کار کنند."
            )
        )
        self.persian_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.persian_label.setWordWrap(True)
        layout.addWidget(self.persian_label, stretch=1)
        
        layout.addStretch()
    
    def set_family(self, family: FontFamily, bg_color: tuple, text_color: tuple):
        """Update with new font family"""
        self.current_family = family
        
        # Set colors
        bg = QColor(*bg_color)
        text = QColor(*text_color)
        
        color_style = f"""
            color: rgb({text.red()}, {text.green()}, {text.blue()});
            background-color: rgb({bg.red()}, {bg.green()}, {bg.blue()});
            padding: 10px;
        """
        
        for label in [self.headline_label, self.body_label, self.ui_label, self.persian_label]:
            label.setStyleSheet(color_style)
        
        # Apply fonts
        self._apply_fonts()
    
    def _apply_fonts(self):
        """Apply different weights to different sections"""
        if not self.current_family:
            return
        
        # Get different weights
        heaviest = self.current_family.get_heaviest()
        regular = self.current_family.get_regular()
        lightest = self.current_family.get_lightest()
        
        # Headline: Heaviest weight, large size
        headline_font = self.font_loader.get_font_for_style(heaviest, FONT_SIZES['h1'])
        if headline_font:
            self.headline_label.setFont(headline_font)
        else:
            self.headline_label.setFont(
                self.font_loader.get_system_fallback(FONT_SIZES['h1'], heaviest.weight)
            )
        
        # Body: Regular weight, body size
        if regular:
            body_font = self.font_loader.get_font_for_style(regular, FONT_SIZES['body'])
            if body_font:
                self.body_label.setFont(body_font)
                self.persian_label.setFont(body_font)
            else:
                fallback = self.font_loader.get_system_fallback(FONT_SIZES['body'], regular.weight)
                self.body_label.setFont(fallback)
                self.persian_label.setFont(fallback)
        
        # UI: Lightest weight, small size
        if lightest:
            ui_font = self.font_loader.get_font_for_style(lightest, FONT_SIZES['small'])
            if ui_font:
                self.ui_label.setFont(ui_font)
            else:
                self.ui_label.setFont(
                    self.font_loader.get_system_fallback(FONT_SIZES['small'], lightest.weight)
                )


class LogoTestMode(QWidget):
    """
    Logo Test Mode with user-selectable logo text.
    """
    
    def __init__(self, font_loader: FontLoader, parent=None):
        super().__init__(parent)
        
        self.font_loader = font_loader
        self.current_family: Optional[FontFamily] = None
        
        # Custom logo text (can be changed by user)
        self.custom_logo_text = ""
        self.use_custom_logo = False
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize logo test layout"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(80, 80, 80, 80)
        
        # English logo text
        self.english_logo = QLabel("PARSEGAN")
        self.english_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.english_logo.setWordWrap(True)
        layout.addWidget(self.english_logo)
        
        layout.addSpacing(60)
        
        # Persian logo text
        persian_text = PersianTextHandler.prepare_text("پارسگان")
        self.persian_logo = QLabel(persian_text)
        self.persian_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.persian_logo.setWordWrap(True)
        layout.addWidget(self.persian_logo)
        
        layout.addSpacing(40)
        
        # Edit button
        edit_btn = QPushButton("✏️ Edit Logo Text")
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                border-color: {COLORS['accent_dim']};
            }}
        """)
        edit_btn.clicked.connect(self._show_logo_editor)
        layout.addWidget(edit_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def _show_logo_editor(self):
        """Show dialog to edit logo text"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Logo Text")
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_secondary']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
            }}
            QLineEdit {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
        """)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("English Logo Text:"))
        english_input = QLineEdit(self.english_logo.text())
        layout.addWidget(english_input)
        
        layout.addSpacing(20)
        
        layout.addWidget(QLabel("Persian Logo Text:"))
        persian_input = QLineEdit(self.persian_logo.text())
        layout.addWidget(persian_input)
        
        layout.addSpacing(20)
        
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: {COLORS['bg_primary']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
        """)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 8px 16px;
            }}
        """)
        
        def on_save():
            self.english_logo.setText(english_input.text())
            shaped_persian = PersianTextHandler.prepare_text(persian_input.text())
            self.persian_logo.setText(shaped_persian)
            self._apply_fonts()
            dialog.accept()
        
        save_btn.clicked.connect(on_save)
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def set_family(self, family: FontFamily, bg_color: tuple, text_color: tuple):
        """Update with new font family"""
        self.current_family = family
        
        # Set colors
        bg = QColor(*bg_color)
        text = QColor(*text_color)
        
        color_style = f"""
            color: rgb({text.red()}, {text.green()}, {text.blue()});
            background-color: rgb({bg.red()}, {bg.green()}, {bg.blue()});
        """
        
        self.english_logo.setStyleSheet(color_style)
        self.persian_logo.setStyleSheet(color_style)
        
        # Apply font
        self._apply_fonts()
    
    def _apply_fonts(self):
        """Apply heaviest weight for logo"""
        if not self.current_family:
            return
        
        heaviest = self.current_family.get_heaviest()
        logo_font = self.font_loader.get_font_for_style(heaviest, FONT_SIZES['huge'])
        
        if logo_font:
            self.english_logo.setFont(logo_font)
            self.persian_logo.setFont(logo_font)
        else:
            fallback = self.font_loader.get_system_fallback(FONT_SIZES['huge'], heaviest.weight)
            self.english_logo.setFont(fallback)
            self.persian_logo.setFont(fallback)


class PersianStressMode(QWidget):
    """
    Persian Shaping Stress Mode
    
    Cycles through demanding Persian text samples:
    - Normal Persian sentence
    - Dense Nastaliq-style phrase
    - Persian UI microcopy
    """
    
    def __init__(self, font_loader: FontLoader, parent=None):
        super().__init__(parent)
        
        self.font_loader = font_loader
        self.current_family: Optional[FontFamily] = None
        
        # Stress test samples (will cycle)
        self.samples = [
            PersianTextHandler.prepare_text("طراحی تایپوگرافی حرفه‌ای نیازمند دقت و توجه به جزئیات است."),
            PersianTextHandler.prepare_text("پیچیدگی‌های خطوط نستعلیق و شکسته"),
            PersianTextHandler.prepare_text("۱۲:۳۴ · فایل · ویرایش · ذخیره · خروج"),
        ]
        
        self.current_sample_index = 0
        
        self.init_ui()
        
        # Auto-cycle through samples
        self.cycle_timer = QTimer()
        self.cycle_timer.timeout.connect(self._next_sample)
        self.cycle_timer.start(2000)  # Change every 2 seconds
    
    def init_ui(self):
        """Initialize Persian stress layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Sample type label
        self.type_label = QLabel("Normal Sentence")
        self.type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.type_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: {FONT_SIZES['small']}px;")
        layout.addWidget(self.type_label)
        
        layout.addSpacing(40)
        
        # Persian text label
        self.persian_label = QLabel(self.samples[0])
        self.persian_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.persian_label.setWordWrap(True)
        layout.addWidget(self.persian_label, stretch=1)
    
    def set_family(self, family: FontFamily, bg_color: tuple, text_color: tuple):
        """Update with new font family"""
        self.current_family = family
        
        # Set colors
        bg = QColor(*bg_color)
        text = QColor(*text_color)
        
        color_style = f"""
            color: rgb({text.red()}, {text.green()}, {text.blue()});
            background-color: rgb({bg.red()}, {bg.green()}, {bg.blue()});
        """
        
        self.persian_label.setStyleSheet(color_style)
        
        # Apply font
        self._apply_fonts()
    
    def _apply_fonts(self):
        """Apply current family font"""
        if not self.current_family:
            return
        
        # Use regular weight for reading
        regular = self.current_family.get_regular()
        
        if regular:
            # Use larger size for stress test
            font = self.font_loader.get_font_for_style(regular, FONT_SIZES['h2'])
            if font:
                self.persian_label.setFont(font)
            else:
                self.persian_label.setFont(
                    self.font_loader.get_system_fallback(FONT_SIZES['h2'], regular.weight)
                )
    
    def _next_sample(self):
        """Cycle to next stress test sample"""
        self.current_sample_index = (self.current_sample_index + 1) % len(self.samples)
        
        # Update text
        self.persian_label.setText(self.samples[self.current_sample_index])
        
        # Update type label
        types = ["Normal Sentence", "Nastaliq Style", "UI Microcopy"]
        self.type_label.setText(types[self.current_sample_index])
    
    def stop_cycling(self):
        """Stop the auto-cycle timer"""
        self.cycle_timer.stop()
    
    def start_cycling(self):
        """Start the auto-cycle timer"""
        if not self.cycle_timer.isActive():
            self.cycle_timer.start(2000)
