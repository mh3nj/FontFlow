"""
FontFlow Studio - Dark Theme
Spotify-inspired dark theme with neon green accents
"""

from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


# ═══════════════════════════════════════════════════════════════
# COLOR PALETTE
# ═══════════════════════════════════════════════════════════════

COLORS = {
    # Base colors
    'bg_primary': '#0a1628',      # Deep navy
    'bg_secondary': '#0d1b2a',    # Slightly lighter
    'bg_panel': '#1b263b',        # Panel background
    'bg_hover': '#253a5e',        # Hover state
    
    # Accents
    'accent_primary': '#00ff88',  # Neon green
    'accent_dim': '#00cc6a',      # Dimmed green
    'accent_danger': '#ff006e',   # Error/uncertain (magenta)
    'accent_warning': '#ffd93d',  # Warning (yellow)
    
    # Text
    'text_primary': '#e0e0e0',    # Soft white
    'text_secondary': '#8892b0',  # Muted gray
    'text_dim': '#495670',        # Very dim
    
    # UI elements
    'border': '#2d3e5f',
    'border_active': '#00ff88',
    'shadow': '#000000',
}


# ═══════════════════════════════════════════════════════════════
# TYPOGRAPHY
# ═══════════════════════════════════════════════════════════════

FONTS = {
    'family_ui': 'SF Pro Display, Segoe UI, -apple-system, sans-serif',
    'family_mono': 'JetBrains Mono, SF Mono, Consolas, monospace',
}

FONT_SIZES = {
    'huge': 72,      # Logo test
    'h1': 48,        # Weight test headline
    'h2': 32,        # Family name
    'h3': 24,        # Section headers
    'body': 18,      # Preview text
    'small': 14,     # UI labels
    'micro': 11,     # HUD info
}


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def hex_to_qcolor(hex_color: str) -> QColor:
    """Convert hex color string to QColor"""
    return QColor(hex_color)


def apply_dark_theme(app: QApplication):
    """
    Apply the dark theme to the entire application.
    This sets the base palette for all widgets.
    """
    palette = QPalette()
    
    # Window and base colors
    palette.setColor(QPalette.ColorRole.Window, hex_to_qcolor(COLORS['bg_primary']))
    palette.setColor(QPalette.ColorRole.WindowText, hex_to_qcolor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.Base, hex_to_qcolor(COLORS['bg_secondary']))
    palette.setColor(QPalette.ColorRole.AlternateBase, hex_to_qcolor(COLORS['bg_panel']))
    
    # Text colors
    palette.setColor(QPalette.ColorRole.Text, hex_to_qcolor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.PlaceholderText, hex_to_qcolor(COLORS['text_dim']))
    
    # Button colors
    palette.setColor(QPalette.ColorRole.Button, hex_to_qcolor(COLORS['bg_panel']))
    palette.setColor(QPalette.ColorRole.ButtonText, hex_to_qcolor(COLORS['text_primary']))
    
    # Highlight colors
    palette.setColor(QPalette.ColorRole.Highlight, hex_to_qcolor(COLORS['accent_primary']))
    palette.setColor(QPalette.ColorRole.HighlightedText, hex_to_qcolor(COLORS['bg_primary']))
    
    # Link colors
    palette.setColor(QPalette.ColorRole.Link, hex_to_qcolor(COLORS['accent_primary']))
    palette.setColor(QPalette.ColorRole.LinkVisited, hex_to_qcolor(COLORS['accent_dim']))
    
    app.setPalette(palette)
    
    # Set application-wide stylesheet for finer control
    app.setStyleSheet(get_stylesheet())


def get_stylesheet() -> str:
    """
    Get the application-wide stylesheet.
    This provides additional styling beyond the palette.
    """
    return f"""
    QMainWindow {{
        background-color: {COLORS['bg_primary']};
    }}
    
    QLabel {{
        color: {COLORS['text_primary']};
        background-color: transparent;
    }}
    
    QPushButton {{
        background-color: {COLORS['bg_panel']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        padding: 8px 16px;
        font-size: {FONT_SIZES['small']}px;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS['bg_hover']};
        border-color: {COLORS['accent_dim']};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS['bg_secondary']};
    }}
    
    QPushButton:disabled {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_dim']};
        border-color: {COLORS['border']};
    }}
    
    QScrollBar:vertical {{
        background-color: {COLORS['bg_secondary']};
        width: 12px;
        margin: 0px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {COLORS['border']};
        min-height: 30px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['accent_dim']};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QStatusBar {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_secondary']};
    }}
    
    QMenuBar {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
    }}
    
    QMenuBar::item:selected {{
        background-color: {COLORS['bg_hover']};
    }}
    
    QMenu {{
        background-color: {COLORS['bg_panel']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
    }}
    
    QMenu::item:selected {{
        background-color: {COLORS['bg_hover']};
    }}
    """


def get_font(size: str = 'body', mono: bool = False) -> QFont:
    """
    Get a QFont with the specified size.
    
    Args:
        size: Font size key from FONT_SIZES
        mono: If True, use monospace font
    """
    font = QFont()
    
    if mono:
        font.setFamily('Consolas')  # Cross-platform monospace
    else:
        font.setFamily('Segoe UI')  # Cross-platform sans-serif
    
    if size in FONT_SIZES:
        font.setPointSize(FONT_SIZES[size])
    else:
        font.setPointSize(FONT_SIZES['body'])
    
    return font
