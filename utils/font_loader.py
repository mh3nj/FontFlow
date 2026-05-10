"""
FontFlow Studio - Font Loader
Loads actual font files and manages font database
"""

from pathlib import Path
from typing import Optional, Dict
from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtCore import QObject, pyqtSignal

from models.font_family import FontStyle


class FontLoader(QObject):
    """
    Manages loading actual font files into Qt's font database.
    Handles caching, fallbacks, and error recovery.
    """
    
    # Signal emitted when a font fails to load
    font_load_failed = pyqtSignal(str, str)  # path, error_message
    
    def __init__(self):
        super().__init__()
        
        # Cache: font_path → font_id
        self._loaded_fonts: Dict[str, int] = {}
        
        # Cache: font_path → QFont object
        self._font_cache: Dict[str, QFont] = {}
        
        # Track failed fonts to avoid repeated attempts
        self._failed_fonts: set = set()
    
    def load_font(self, style: FontStyle) -> Optional[QFont]:
        """
        Load a font file and return a QFont object.
        
        Args:
            style: FontStyle to load
            
        Returns:
            QFont object or None if loading failed
        """
        font_path = str(style.path)
        
        # Check if already in cache
        if font_path in self._font_cache:
            return self._font_cache[font_path]
        
        # Check if previously failed
        if font_path in self._failed_fonts:
            return None
        
        # Check if file exists
        if not style.path.exists():
            print(f"Font file not found: {font_path}")
            self._failed_fonts.add(font_path)
            self.font_load_failed.emit(font_path, "File not found")
            return None
        
        try:
            # Load font into database (use class method, not instance)
            if font_path not in self._loaded_fonts:
                font_id = QFontDatabase.addApplicationFont(font_path)
                
                if font_id == -1:
                    raise Exception("Failed to load font into database")
                
                self._loaded_fonts[font_path] = font_id
                print(f"✓ Loaded font: {style.path.name}")
            
            # Get font families from this font file
            font_id = self._loaded_fonts[font_path]
            families = QFontDatabase.applicationFontFamilies(font_id)
            
            if not families:
                raise Exception("No font families found in file")
            
            # Create QFont object
            family_name = families[0]  # Use first family
            font = QFont(family_name)
            
            # Apply style properties
            font.setWeight(self._map_weight_to_qt(style.weight))
            font.setItalic(style.is_italic)
            
            # Cache and return
            self._font_cache[font_path] = font
            return font
            
        except Exception as e:
            print(f"✗ Error loading font {style.path.name}: {e}")
            self._failed_fonts.add(font_path)
            self.font_load_failed.emit(font_path, str(e))
            return None
    
    def _map_weight_to_qt(self, css_weight: int) -> QFont.Weight:
        """
        Map CSS weight (100-900) to Qt weight enum.
        
        Qt6 uses QFont.Weight enum with these values:
        - Thin = 100
        - ExtraLight = 200
        - Light = 300
        - Normal = 400
        - Medium = 500
        - DemiBold = 600
        - Bold = 700
        - ExtraBold = 800
        - Black = 900
        """
        weight_map = {
            100: QFont.Weight.Thin,
            200: QFont.Weight.ExtraLight,
            300: QFont.Weight.Light,
            400: QFont.Weight.Normal,
            500: QFont.Weight.Medium,
            600: QFont.Weight.DemiBold,
            700: QFont.Weight.Bold,
            800: QFont.Weight.ExtraBold,
            900: QFont.Weight.Black,
        }
        
        # Find closest weight
        if css_weight in weight_map:
            return weight_map[css_weight]
        
        # Find nearest
        closest = min(weight_map.keys(), key=lambda w: abs(w - css_weight))
        return weight_map[closest]
    
    def get_font_for_style(self, style: FontStyle, size: int = 18) -> Optional[QFont]:
        """
        Get a QFont object for a style with specific size.
        
        Args:
            style: FontStyle to load
            size: Font size in points
            
        Returns:
            QFont object or None if loading failed
        """
        base_font = self.load_font(style)
        
        if base_font is None:
            return None
        
        # Create a copy with the specified size
        font = QFont(base_font)
        font.setPointSize(size)
        
        return font
    
    def get_system_fallback(self, size: int = 18, weight: int = 400, italic: bool = False) -> QFont:
        """
        Get a system fallback font when loading fails.
        
        Args:
            size: Font size in points
            weight: CSS weight (100-900)
            italic: Whether font should be italic
            
        Returns:
            QFont object using system font
        """
        font = QFont("Segoe UI", size)  # Cross-platform default
        font.setWeight(self._map_weight_to_qt(weight))
        font.setItalic(italic)
        return font
    
    def clear_cache(self):
        """Clear the font cache (useful for memory management)"""
        self._font_cache.clear()
        print("Font cache cleared")
    
    def unload_font(self, style: FontStyle):
        """Unload a specific font from cache"""
        font_path = str(style.path)
        
        if font_path in self._font_cache:
            del self._font_cache[font_path]
        
        if font_path in self._loaded_fonts:
            font_id = self._loaded_fonts[font_path]
            QFontDatabase.removeApplicationFont(font_id)
            del self._loaded_fonts[font_path]
    
    def get_loaded_count(self) -> int:
        """Get number of fonts currently loaded"""
        return len(self._loaded_fonts)
    
    def get_failed_count(self) -> int:
        """Get number of fonts that failed to load"""
        return len(self._failed_fonts)
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        return {
            'loaded': len(self._loaded_fonts),
            'cached': len(self._font_cache),
            'failed': len(self._failed_fonts),
        }
