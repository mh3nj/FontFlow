"""
FontFlow Studio - Color Generator
Generates stable, deterministic colors for font families
"""

import hashlib
from typing import Tuple


class ColorGenerator:
    """
    Generates pleasant, high-contrast color pairs for font families.
    Colors are deterministic (same family name = same colors across sessions).
    """
    
    # Predefined palettes with good contrast
    BG_PALETTES = [
        (10, 22, 40),      # Deep navy
        (20, 15, 35),      # Deep purple
        (15, 30, 25),      # Deep teal
        (30, 20, 20),      # Deep burgundy
        (20, 25, 15),      # Deep olive
        (5, 20, 30),       # Deep ocean
        (25, 15, 30),      # Deep violet
        (15, 25, 30),      # Deep slate
    ]
    
    TEXT_PALETTES = [
        (224, 224, 224),   # Soft white
        (200, 220, 255),   # Soft blue-white
        (220, 255, 240),   # Soft green-white
        (255, 240, 220),   # Soft warm-white
        (240, 220, 255),   # Soft purple-white
        (255, 220, 220),   # Soft pink-white
    ]
    
    @staticmethod
    def get_colors(family_name: str) -> dict:
        """
        Generate stable background and text colors for a family.
        
        Args:
            family_name: The font family name
            
        Returns:
            Dictionary with 'bg' and 'text' RGB tuples
        """
        # Hash the family name to get deterministic values
        hash_bytes = hashlib.md5(family_name.encode('utf-8')).digest()
        
        # Use hash to select from palettes
        bg_index = hash_bytes[0] % len(ColorGenerator.BG_PALETTES)
        text_index = hash_bytes[1] % len(ColorGenerator.TEXT_PALETTES)
        
        return {
            'bg': ColorGenerator.BG_PALETTES[bg_index],
            'text': ColorGenerator.TEXT_PALETTES[text_index],
        }
    
    @staticmethod
    def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex string"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex string to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
