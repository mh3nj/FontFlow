"""
FontFlow Studio - Comparison Panel
Side-by-side comparison of fonts from a selected folder
"""

from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QScrollArea, QGridLayout, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import Optional, List

from models.font_family import FontFamily
from ui.theme import COLORS, FONT_SIZES
from utils.font_loader import FontLoader
from utils.text_samples import TextSamples


class ComparisonFontCard(QWidget):
    """
    Individual font card for comparison view.
    Shows a preview of one font family.
    """
    
    def __init__(self, family: FontFamily, font_loader: FontLoader, parent=None):
        super().__init__(parent)
        
        self.family = family
        self.font_loader = font_loader
        
        self.setFixedSize(280, 200)
        self.init_ui()
    
    def init_ui(self):
        """Initialize card UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Set card background
        bg = QColor(*self.family.bg_color)
        text = QColor(*self.family.text_color)
        
        self.setStyleSheet(f"""
            ComparisonFontCard {{
                background-color: rgb({bg.red()}, {bg.green()}, {bg.blue()});
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
            }}
            ComparisonFontCard:hover {{
                border-color: {COLORS['accent_primary']};
            }}
        """)
        
        # Family name
        name_label = QLabel(self.family.family_name)
        name_label.setFont(QFont("Segoe UI", FONT_SIZES['micro'], QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {COLORS['accent_primary']}; border: none;")
        name_label.setWordWrap(True)
        name_label.setMaximumHeight(40)
        layout.addWidget(name_label)
        
        # Preview text
        self.preview_label = QLabel("The Quick Brown Fox")
        self.preview_label.setStyleSheet(f"""
            color: rgb({text.red()}, {text.green()}, {text.blue()});
            border: none;
        """)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label, stretch=1)
        
        # Style info
        info_label = QLabel(f"{self.family.style_count} styles · {self.family.weight_range_name}")
        info_label.setFont(QFont("Consolas", FONT_SIZES['micro'] - 2))
        info_label.setStyleSheet(f"color: rgb({text.red()}, {text.green()}, {text.blue()}); border: none; opacity: 0.7;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        # Apply font
        self._apply_font()
    
    def _apply_font(self):
        """Load and apply the font"""
        # Use regular or closest to regular
        style = self.family.get_regular()
        if not style:
            style = self.family.styles[0]
        
        font = self.font_loader.get_font_for_style(style, FONT_SIZES['body'])
        
        if font:
            self.preview_label.setFont(font)
        else:
            self.preview_label.setFont(
                self.font_loader.get_system_fallback(FONT_SIZES['body'], style.weight)
            )


class ComparisonPanel(QWidget):
    """
    Right panel showing multiple fonts for comparison.
    Allows selecting a folder and viewing all fonts from it side-by-side.
    """
    
    folder_selected = pyqtSignal(Path)  # Emitted when a folder is selected
    
    def __init__(self, font_loader: FontLoader, parent=None):
        super().__init__(parent)
        
        self.font_loader = font_loader
        self.comparison_families: List[FontFamily] = []
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize comparison panel UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Scroll area for font cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLORS['bg_primary']};
            }}
        """)
        
        # Container for cards
        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(16)
        self.cards_layout.setContentsMargins(16, 16, 16, 16)
        
        scroll.setWidget(self.cards_container)
        main_layout.addWidget(scroll)
    
    def _create_header(self) -> QWidget:
        """Create header with title and folder selector"""
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_secondary']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 16, 0)
        
        # Title
        title = QLabel("COMPARISON MODE")
        title.setFont(QFont("Segoe UI", FONT_SIZES['small'], QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['accent_primary']}; border: none;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Folder info label
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setFont(QFont("Consolas", FONT_SIZES['micro']))
        self.folder_label.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
        layout.addWidget(self.folder_label)
        
        # Select folder button
        select_btn = QPushButton("Select Folder")
        select_btn.setFont(QFont("Segoe UI", FONT_SIZES['micro']))
        select_btn.clicked.connect(self._select_folder)
        layout.addWidget(select_btn)
        
        return header
    
    def _select_folder(self):
        """Open folder selection dialog"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Compare",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.load_folder(Path(folder))
    
    def load_folder(self, folder_path: Path):
        """
        Load fonts from a folder for comparison.
        
        Args:
            folder_path: Path to folder containing fonts
        """
        from core.font_library import FontLibrary
        
        # Clear existing cards
        self._clear_cards()
        
        # Update label
        self.folder_label.setText(folder_path.name)
        
        # Scan folder
        print(f"Loading comparison folder: {folder_path}")
        library = FontLibrary(folder_path)
        self.comparison_families = library.scan()
        
        print(f"Found {len(self.comparison_families)} families for comparison")
        
        # Create cards
        self._create_cards()
        
        # Emit signal
        self.folder_selected.emit(folder_path)
    
    def _clear_cards(self):
        """Clear all font cards"""
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _create_cards(self):
        """Create font cards in grid layout"""
        columns = 2  # 2 cards per row
        
        for i, family in enumerate(self.comparison_families):
            card = ComparisonFontCard(family, self.font_loader)
            
            row = i // columns
            col = i % columns
            
            self.cards_layout.addWidget(card, row, col)
    
    def set_families(self, families: List[FontFamily]):
        """
        Set families directly (instead of loading from folder).
        
        Args:
            families: List of FontFamily objects to compare
        """
        self._clear_cards()
        self.comparison_families = families
        self.folder_label.setText(f"{len(families)} families")
        self._create_cards()
