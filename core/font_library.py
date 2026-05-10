"""
FontFlow Studio - Font Library Management
Scans directories and groups fonts into families
"""

from pathlib import Path
from typing import List, Optional, Callable
from collections import defaultdict
import re

from fontTools.ttLib import TTFont
from models.font_family import FontFamily, FontStyle
from utils.color_generator import ColorGenerator


class FontLibrary:
    """
    Manages font discovery, parsing, and family grouping.
    This is the core data structure that holds all font families.
    """
    
    # Font file extensions to scan
    FONT_EXTENSIONS = {'.ttf', '.otf', '.woff2', '.ttc'}
    
    def __init__(self, root_path: Optional[Path] = None):
        self.root_path = root_path
        self.families: List[FontFamily] = []
        self._family_map = {}  # family_name -> FontFamily (for quick lookup)
    
    def scan(self, progress_callback: Optional[Callable[[int, int], None]] = None) -> List[FontFamily]:
        """
        Scan the root directory for fonts and group them into families.
        
        Args:
            progress_callback: Optional callback (current, total) for progress updates
            
        Returns:
            List of FontFamily objects
        """
        if not self.root_path or not self.root_path.exists():
            print("Error: Invalid root path")
            return []
        
        print(f"Scanning fonts in: {self.root_path}")
        
        # Step 1: Find all font files
        font_files = self._find_font_files()
        total_files = len(font_files)
        print(f"Found {total_files} font files")
        
        if total_files == 0:
            return []
        
        # Step 2: Parse metadata from each font
        font_metadata = []
        for i, font_path in enumerate(font_files):
            if progress_callback:
                progress_callback(i + 1, total_files)
            
            try:
                metadata = self._parse_font_metadata(font_path)
                if metadata:
                    font_metadata.append(metadata)
            except Exception as e:
                print(f"Warning: Failed to parse {font_path.name}: {e}")
        
        print(f"Successfully parsed {len(font_metadata)} fonts")
        
        # Step 3: Group by family name
        families_dict = self._group_by_family(font_metadata)
        
        # Step 4: Create FontFamily objects
        self.families = []
        for family_name, styles in families_dict.items():
            # Generate stable colors
            colors = ColorGenerator.get_colors(family_name)
            
            # Detect Persian support
            has_persian = any(style.glyph_count > 500 for style in styles)  # Simplified check
            
            family = FontFamily(
                family_name=family_name,
                styles=styles,
                source_folder=styles[0].path.parent,
                bg_color=colors['bg'],
                text_color=colors['text'],
                has_persian=has_persian,
            )
            
            self.families.append(family)
            self._family_map[family_name] = family
        
        # Sort families alphabetically
        self.families.sort(key=lambda f: f.family_name.lower())
        
        print(f"Grouped into {len(self.families)} font families")
        return self.families
    
    def _find_font_files(self) -> List[Path]:
        """Find all font files recursively"""
        font_files = []
        for ext in self.FONT_EXTENSIONS:
            font_files.extend(self.root_path.rglob(f'*{ext}'))
        return font_files
    
    def _parse_font_metadata(self, font_path: Path) -> Optional[FontStyle]:
        """
        Parse metadata from a single font file.
        
        Returns:
            FontStyle object or None if parsing fails
        """
        try:
            font = TTFont(font_path)
            
            # Get name table
            name_table = font['name']
            
            # Extract family and style names
            family_name = self._get_name_entry(name_table, 1)  # Font Family
            style_name = self._get_name_entry(name_table, 2)   # Font Subfamily
            
            if not family_name:
                # Fallback: use folder name as family
                family_name = font_path.parent.name
            if not style_name:
                style_name = "Regular"
            
            # Get weight from OS/2 table
            weight = 400  # Default
            if 'OS/2' in font:
                weight = font['OS/2'].usWeightClass
            
            # Detect italic
            is_italic = 'italic' in style_name.lower() or 'oblique' in style_name.lower()
            
            # Check if variable font
            is_variable = 'fvar' in font
            
            # Count glyphs
            glyph_count = len(font.getGlyphOrder())
            
            # Generate fingerprint (simple hash for now)
            fingerprint = str(hash(font_path))
            
            font.close()
            
            # Create FontStyle with the actual family name stored
            style_obj = FontStyle(
                path=font_path,
                style_name=style_name,
                weight=weight,
                is_italic=is_italic,
                is_variable=is_variable,
                glyph_count=glyph_count,
                fingerprint=fingerprint,
            )
            
            # Store the family name on the style object for grouping
            style_obj._family_name = family_name
            
            return style_obj
            
        except Exception as e:
            print(f"Error parsing {font_path}: {e}")
            return None
    
    def _get_name_entry(self, name_table, name_id: int) -> Optional[str]:
        """Extract name entry from name table"""
        try:
            # Try to get English name (platform 3, encoding 1, language 0x409)
            name = name_table.getName(name_id, 3, 1, 0x409)
            if name:
                return str(name)
            
            # Fallback to any available name
            name = name_table.getName(name_id, 3, 1)
            if name:
                return str(name)
            
            # Last resort: first available
            for record in name_table.names:
                if record.nameID == name_id:
                    return str(record)
            
        except Exception:
            pass
        
        return None
    
    def _group_by_family(self, styles: List[FontStyle]) -> dict:
        """
        Group font styles by family name.
        Uses the actual family name from the font file's name table.
        """
        families = defaultdict(list)
        
        for style in styles:
            # Get the family name we stored during parsing
            family_key = getattr(style, '_family_name', style.path.parent.name)
            
            # Normalize it slightly (remove extra spaces, etc.)
            family_key = ' '.join(family_key.split())
            
            families[family_key].append(style)
        
        return dict(families)
    
    @staticmethod
    def _normalize_family_name(name: str) -> str:
        """
        Normalize family name for consistent grouping.
        Removes version numbers, hyphens, underscores, etc.
        """
        # Remove common suffixes
        name = re.sub(r'[-_]?(Regular|Bold|Italic|Light|Medium|Black).*$', '', name, flags=re.IGNORECASE)
        
        # Remove version numbers
        name = re.sub(r'[-_]?v?\d+(\.\d+)*$', '', name)
        
        # Clean up
        name = name.strip('-_ ')
        
        return name
    
    def get_family(self, family_name: str) -> Optional[FontFamily]:
        """Get a family by name"""
        return self._family_map.get(family_name)
    
    def __len__(self):
        return len(self.families)
    
    def __getitem__(self, index: int) -> FontFamily:
        return self.families[index]
