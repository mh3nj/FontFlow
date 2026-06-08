"""
FontFlow Studio - Search & Filter Panel
Find fonts quickly by name, category, language, and more
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QComboBox, QScrollArea, QFrame,
                              QPushButton, QCheckBox, QSlider, QListWidget,
                              QListWidgetItem, QGroupBox, QGridLayout, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QColor
from typing import List, Optional, Dict, Set
from pathlib import Path

from models.font_family import FontFamily
from ui.theme import COLORS, FONT_SIZES


class SearchResultItem(QWidget):
    """Individual search result item with hover effect"""
    
    item_clicked = pyqtSignal(int)  # Emits family index
    
    def __init__(self, family: FontFamily, index: int, parent=None):
        super().__init__(parent)
        self.family = family
        self.index = index
        
        self.setFixedHeight(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        
        # Color indicator
        color_indicator = QWidget()
        color_indicator.setFixedSize(8, 40)
        bg_color = QColor(*self.family.bg_color)
        color_indicator.setStyleSheet(f"""
            background-color: rgb({bg_color.red()}, {bg_color.green()}, {bg_color.blue()});
            border-radius: 4px;
        """)
        color_indicator.setToolTip("Family color code")
        layout.addWidget(color_indicator)
        
        # Family info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Name
        name_label = QLabel(self.family.family_name)
        name_label.setFont(QFont("Segoe UI", FONT_SIZES['small'], QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {COLORS['accent_primary']};")
        name_label.setToolTip("Click to jump to this font family")
        info_layout.addWidget(name_label)
        
        # Details
        details = f"{self.family.style_count} styles · {self.family.weight_range_name}"
        if self.family.has_variable:
            details += " · Variable"
        if self.family.has_persian:
            details += " · فارسی"
        
        details_label = QLabel(details)
        details_label.setFont(QFont("Consolas", FONT_SIZES['micro']))
        details_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        info_layout.addWidget(details_label)
        
        # Languages
        if self.family.supported_scripts:
            scripts = ', '.join(self.family.supported_scripts[:3])
            if len(self.family.supported_scripts) > 3:
                scripts += f" +{len(self.family.supported_scripts) - 3}"
            lang_label = QLabel(f"🌍 {scripts}")
            lang_label.setFont(QFont("Consolas", FONT_SIZES['micro']))
            lang_label.setStyleSheet(f"color: {COLORS['text_dim']};")
            lang_label.setToolTip(f"Supported scripts: {', '.join(self.family.supported_scripts)}")
            info_layout.addWidget(lang_label)
        
        layout.addLayout(info_layout, stretch=1)
        
        # Classification status
        status_layout = QVBoxLayout()
        status_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        if hasattr(self.family, 'classified') and self.family.classified:
            status = QLabel("✓ Classified")
            status.setStyleSheet(f"color: {COLORS['accent_primary']}; font-size: 10px;")
            status.setToolTip("This font has been classified")
        else:
            status = QLabel("○ Unclassified")
            status.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px;")
            status.setToolTip("This font has not been classified yet")
        status_layout.addWidget(status)
        
        # Style count badge
        style_badge = QLabel(f"{self.family.style_count}")
        style_badge.setFont(QFont("Consolas", 9))
        style_badge.setStyleSheet(f"""
            background-color: {COLORS['bg_panel']};
            color: {COLORS['accent_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            padding: 2px 6px;
            font-size: 10px;
        """)
        style_badge.setToolTip("Number of font styles in this family")
        status_layout.addWidget(style_badge)
        
        layout.addLayout(status_layout)
        
        # Hover effect
        self.setStyleSheet(f"""
            SearchResultItem {{
                background-color: {COLORS['bg_secondary']};
                border-bottom: 1px solid {COLORS['border']};
            }}
            SearchResultItem:hover {{
                background-color: {COLORS['bg_hover']};
            }}
        """)
    
    def mousePressEvent(self, event):
        self.item_clicked.emit(self.index)


class SearchPanel(QWidget):
    """
    Search and filter panel for finding fonts.
    Can be toggled with Ctrl+F keyboard shortcut.
    """
    
    family_selected = pyqtSignal(int)  # Emits family index to jump to
    
    def __init__(self, families: List[FontFamily], parent=None):
        super().__init__(parent)
        
        self.all_families = families
        self.filtered_families = []
        self.is_loading = False
        
        self.setMinimumWidth(380)
        self.setMaximumWidth(450)
        
        self.setStyleSheet(f"""
            SearchPanel {{
                background-color: {COLORS['bg_primary']};
                border-left: 2px solid {COLORS['accent_primary']};
            }}
        """)
        
        self.init_ui()
        self.setup_completion()
    
    def init_ui(self):
        """Initialize the search panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header with close button
        header_layout = QHBoxLayout()
        
        header = QLabel("🔍 Search Fonts")
        header.setFont(QFont("Segoe UI", FONT_SIZES['h3'], QFont.Weight.Bold))
        header.setStyleSheet(f"color: {COLORS['accent_primary']};")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 14px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_danger']};
                color: white;
                border-color: {COLORS['accent_danger']};
            }}
        """)
        close_btn.setToolTip("Close search panel (Esc)")
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Search input
        search_label = QLabel("🔎 Search by name:")
        search_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: bold;")
        layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type font name... (e.g., 'Montserrat')")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['accent_primary']};
                border-width: 2px;
            }}
        """)
        self.search_input.setToolTip("Start typing to filter fonts in real-time")
        self.search_input.textChanged.connect(self.on_search_changed)
        layout.addWidget(self.search_input)
        
        # Search stats
        self.stats_label = QLabel("")
        self.stats_label.setFont(QFont("Consolas", FONT_SIZES['micro']))
        self.stats_label.setStyleSheet(f"color: {COLORS['text_dim']};")
        layout.addWidget(self.stats_label)
        
        # Category filter
        category_group = QGroupBox("📁 Category Status")
        category_group.setStyleSheet(self._group_style())
        category_layout = QVBoxLayout(category_group)
        
        self.category_filter = QComboBox()
        self.category_filter.addItems([
            "All Categories",
            "✓ Classified Only",
            "○ Unclassified Only",
            "⚠ Uncertain Only"
        ])
        self.category_filter.setStyleSheet(self._combo_style())
        self.category_filter.setToolTip("Filter fonts by classification status")
        self.category_filter.currentTextChanged.connect(self.on_filter_changed)
        category_layout.addWidget(self.category_filter)
        
        layout.addWidget(category_group)
        
        # Language filter
        lang_group = QGroupBox("🌍 Language Support")
        lang_group.setStyleSheet(self._group_style())
        lang_layout = QVBoxLayout(lang_group)
        
        self.lang_filter = QComboBox()
        self.lang_filter.addItems([
            "All Languages", "🇬🇧 Latin", "🇮🇷 Persian/Arabic", 
            "🇷🇺 Cyrillic", "🇬🇷 Greek", "🇮🇱 Hebrew",
            "🇮🇳 Devanagari", "🇰🇷 Korean", "🇨🇳 Chinese", "🇯🇵 Japanese"
        ])
        self.lang_filter.setStyleSheet(self._combo_style())
        self.lang_filter.setToolTip("Filter fonts by which writing systems they support")
        self.lang_filter.currentTextChanged.connect(self.on_filter_changed)
        lang_layout.addWidget(self.lang_filter)
        
        layout.addWidget(lang_group)
        
        # Weight range filter
        weight_group = QGroupBox("⚖️ Minimum Weight")
        weight_group.setStyleSheet(self._group_style())
        weight_layout = QVBoxLayout(weight_group)
        
        weight_label = QLabel("Show fonts with weight ≥")
        weight_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px;")
        weight_layout.addWidget(weight_label)
        
        self.weight_slider = QSlider(Qt.Orientation.Horizontal)
        self.weight_slider.setMinimum(100)
        self.weight_slider.setMaximum(900)
        self.weight_slider.setValue(100)
        self.weight_slider.setTickInterval(100)
        self.weight_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.weight_slider.setStyleSheet(self._slider_style())
        self.weight_slider.setToolTip("Minimum font weight (Thin=100, Regular=400, Bold=700, Black=900)")
        self.weight_slider.valueChanged.connect(self.on_filter_changed)
        weight_layout.addWidget(self.weight_slider)
        
        # Weight value display
        self.weight_value = QLabel("100 (Thin)")
        self.weight_value.setStyleSheet(f"color: {COLORS['accent_primary']}; font-size: 11px; text-align: center;")
        self.weight_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.weight_slider.valueChanged.connect(lambda v: self.weight_value.setText(self._get_weight_name(v)))
        weight_layout.addWidget(self.weight_value)
        
        layout.addWidget(weight_group)
        
        # Reset filters button
        reset_btn = QPushButton("⟳ Reset All Filters")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                border-color: {COLORS['accent_dim']};
            }}
        """)
        reset_btn.setToolTip("Reset all search filters to default values")
        reset_btn.clicked.connect(self.reset_filters)
        layout.addWidget(reset_btn)
        
        # Results header
        results_header = QHBoxLayout()
        self.results_label = QLabel("0 results")
        self.results_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: bold;")
        results_header.addWidget(self.results_label)
        results_header.addStretch()
        
        # Clear search button
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_dim']};
                border: none;
                font-size: 11px;
                text-decoration: underline;
            }}
            QPushButton:hover {{
                color: {COLORS['accent_primary']};
            }}
        """)
        clear_btn.setToolTip("Clear search text")
        clear_btn.clicked.connect(lambda: self.search_input.clear())
        results_header.addWidget(clear_btn)
        
        layout.addLayout(results_header)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 0px;
            }}
            QListWidget::item:selected {{
                background-color: transparent;
            }}
        """)
        self.results_list.setToolTip("Click any result to jump to that font")
        self.results_list.itemClicked.connect(self.on_result_clicked)
        layout.addWidget(self.results_list)
        
        # Keyboard hint
        hint_label = QLabel("💡 Tip: Press Esc to close | Click result to jump")
        hint_label.setFont(QFont("Segoe UI", FONT_SIZES['micro']))
        hint_label.setStyleSheet(f"color: {COLORS['text_dim']};")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)
    
    def _group_style(self) -> str:
        """Style for group boxes"""
        return f"""
            QGroupBox {{
                color: {COLORS['accent_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
            }}
        """
    
    def _combo_style(self) -> str:
        """Style for combo boxes"""
        return f"""
            QComboBox {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 8px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {COLORS['text_secondary']};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['bg_hover']};
                border: 1px solid {COLORS['border']};
            }}
        """
    
    def _slider_style(self) -> str:
        """Style for slider"""
        return f"""
            QSlider::groove:horizontal {{
                height: 4px;
                background: {COLORS['border']};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['accent_primary']};
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {COLORS['accent_dim']};
                transform: scale(1.1);
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['accent_primary']};
                border-radius: 2px;
            }}
        """
    
    def _get_weight_name(self, weight: int) -> str:
        """Get human-readable weight name"""
        names = {
            100: "Thin",
            200: "ExtraLight",
            300: "Light",
            400: "Regular",
            500: "Medium",
            600: "SemiBold",
            700: "Bold",
            800: "ExtraBold",
            900: "Black",
        }
        return f"{weight} ({names.get(weight, '')})"
    
    def setup_completion(self):
        """Setup auto-completion for search"""
        self.all_names = [f.family_name for f in self.all_families]
        self.completion_timer = QTimer()
        self.completion_timer.setSingleShot(True)
        self.completion_timer.timeout.connect(self.update_results)
    
    def on_search_changed(self, text: str):
        """Handle search text change with debounce"""
        self._show_loading()
        self.completion_timer.start(300)
    
    def on_filter_changed(self):
        """Handle filter changes"""
        self.update_results()
    
    def reset_filters(self):
        """Reset all filters to default values"""
        self.search_input.clear()
        self.category_filter.setCurrentIndex(0)
        self.lang_filter.setCurrentIndex(0)
        self.weight_slider.setValue(100)
        self.update_results()
        self.stats_label.setText("Filters reset")
    
    def _show_loading(self):
        """Show loading indicator while searching"""
        self.results_list.clear()
        
        loading_item = QListWidgetItem()
        loading_item.setSizeHint(QSize(280, 60))
        self.results_list.addItem(loading_item)
        
        loading_widget = QWidget()
        loading_layout = QHBoxLayout(loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        loading_text = QLabel("🔍 Searching...")
        loading_text.setStyleSheet(f"color: {COLORS['accent_primary']};")
        loading_layout.addWidget(loading_text)
        
        self.results_list.setItemWidget(loading_item, loading_widget)
        self.is_loading = True
    
    def update_results(self):
        """Update search results based on current filters"""
        search_text = self.search_input.text().lower().strip()
        category_filter = self.category_filter.currentText()
        lang_filter = self.lang_filter.currentText()
        min_weight = self.weight_slider.value()
        
        self.filtered_families = []
        
        for i, family in enumerate(self.all_families):
            # Name search
            if search_text and search_text not in family.family_name.lower():
                continue
            
            # Category filter
            if category_filter == "✓ Classified Only":
                if not (hasattr(family, 'classified') and family.classified):
                    continue
            elif category_filter == "○ Unclassified Only":
                if hasattr(family, 'classified') and family.classified:
                    continue
            elif category_filter == "⚠ Uncertain Only":
                if not (hasattr(family, 'classified_uncertain') and family.classified_uncertain):
                    continue
            
            # Language filter
            if lang_filter != "All Languages":
                family.detect_supported_languages()
                
                lang_map = {
                    "🇬🇧 Latin": 'latin',
                    "🇮🇷 Persian/Arabic": ('arabic', 'arabic_persian'),
                    "🇷🇺 Cyrillic": 'cyrillic',
                    "🇬🇷 Greek": 'greek',
                    "🇮🇱 Hebrew": 'hebrew',
                    "🇮🇳 Devanagari": 'devanagari',
                    "🇰🇷 Korean": 'hangul',
                    "🇨🇳 Chinese": 'cjk',
                    "🇯🇵 Japanese": ('hiragana', 'katakana'),
                }
                
                target = lang_map.get(lang_filter)
                if target:
                    if isinstance(target, tuple):
                        if not any(t in family.supported_scripts for t in target):
                            continue
                    elif target not in family.supported_scripts:
                        continue
            
            # Weight filter
            if family.weight_range[1] < min_weight:
                continue
            
            self.filtered_families.append((i, family))
        
        # Update results display
        self.results_list.clear()
        self.is_loading = False
        
        # Update stats
        total = len(self.all_families)
        filtered = len(self.filtered_families)
        self.stats_label.setText(f"📊 {filtered} of {total} families")
        
        # Show results or empty state
        if not self.filtered_families:
            self._show_empty_state()
        else:
            for index, family in self.filtered_families:
                item = QListWidgetItem()
                item.setSizeHint(QSize(350, 80))
                self.results_list.addItem(item)
                
                result_widget = SearchResultItem(family, index)
                result_widget.item_clicked.connect(self.on_family_selected)
                self.results_list.setItemWidget(item, result_widget)
        
        self.results_label.setText(f"{len(self.filtered_families)} results")
    
    def _show_empty_state(self):
        """Show empty state message when no results"""
        empty_item = QListWidgetItem()
        empty_item.setSizeHint(QSize(350, 150))
        self.results_list.addItem(empty_item)
        
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setContentsMargins(20, 20, 20, 20)
        
        # Icon
        empty_icon = QLabel("🔍")
        empty_icon.setFont(QFont("Segoe UI", 48))
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_icon.setStyleSheet(f"color: {COLORS['text_dim']};")
        empty_layout.addWidget(empty_icon)
        
        # Title
        empty_text = QLabel("No fonts found")
        empty_text.setFont(QFont("Segoe UI", FONT_SIZES['small'], QFont.Weight.Bold))
        empty_text.setStyleSheet(f"color: {COLORS['text_secondary']};")
        empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_text)
        
        # Hint
        empty_hint = QLabel("Try adjusting your search or filters")
        empty_hint.setFont(QFont("Segoe UI", FONT_SIZES['micro']))
        empty_hint.setStyleSheet(f"color: {COLORS['text_dim']};")
        empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_hint)
        
        self.results_list.setItemWidget(empty_item, empty_widget)
    
    def on_family_selected(self, index: int):
        """Handle family selection from results"""
        self.family_selected.emit(index)
        self.hide()
    
    def on_result_clicked(self, item):
        """Handle click on list item"""
        widget = self.results_list.itemWidget(item)
        if widget and hasattr(widget, 'index'):
            self.family_selected.emit(widget.index)
            self.hide()
    
    def show_search(self):
        """Show the search panel and focus search input"""
        self.show()
        self.search_input.setFocus()
        self.search_input.selectAll()
        self.update_results()
    
    def keyPressEvent(self, event):
        """Handle escape key to close"""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)