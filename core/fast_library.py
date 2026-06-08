"""
FontFlow Studio - Fast Font Library
Lazy loading - only parse fonts when needed
"""

from pathlib import Path
from typing import List, Optional, Dict, Callable
from dataclasses import dataclass, field
import json
from datetime import datetime

from models.font_family import FontFamily, FontStyle
from utils.color_generator import ColorGenerator


@dataclass
class FontFilePointer:
    """Lightweight reference to a font file (no parsing yet)"""
    path: Path
    size_bytes: int
    modified_time: float
    
    def __hash__(self):
        return hash(self.path)
    
    def __eq__(self, other):
        return self.path == other.path


@dataclass
class FamilyPointer:
    """Lightweight family reference (no styles loaded yet)"""
    name: str
    folder_path: Path
    file_ptrs: List[FontFilePointer]
    needs_parsing: bool = True
    parsed_family: Optional[FontFamily] = None
    
    def __hash__(self):
        return hash(self.name)


class FastFontLibrary:
    """
    Lazy-loading font library.
    - Initial scan: only directory listing (no font parsing)
    - Parse on demand: only when user views a family
    - Cache parsed families in memory
    - LRU eviction to control RAM
    """
    
    # Maximum families to keep parsed in memory
    MAX_CACHED_FAMILIES = 50
    
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
        self.families: List[FamilyPointer] = []
        self._parsed_cache: Dict[str, FontFamily] = {}  # name -> parsed family
        self._access_order: List[str] = []  # LRU tracking
        
        # Extensions to scan
        self.font_extensions = {'.ttf', '.otf', '.woff2', '.ttc'}
        
        # Track scanning progress
        self.scan_total = 0
        self.scan_current = 0
    
    def fast_scan(self, progress_callback: Optional[Callable[[int, int], None]] = None) -> List[FamilyPointer]:
        """
        Scan just file structure - NO font parsing!
        
        Args:
            progress_callback: Optional callback(current, total)
            
        Returns:
            List of FamilyPointer objects (lightweight)
        """
        if not self.root_path.exists():
            raise FileNotFoundError(f"Library path not found: {self.root_path}")
        
        print(f"Fast scanning: {self.root_path}")
        
        # Step 1: Find all font files
        font_files = self._find_font_files()
        self.scan_total = len(font_files)
        
        # Step 2: Group by folder (each folder is a potential family)
        folders: Dict[Path, List[FontFilePointer]] = {}
        
        for i, font_path in enumerate(font_files):
            if progress_callback:
                progress_callback(i + 1, self.scan_total)
            
            folder = font_path.parent
            if folder not in folders:
                folders[folder] = []
            
            # Store file pointer (no parsing!)
            file_ptr = FontFilePointer(
                path=font_path,
                size_bytes=font_path.stat().st_size,
                modified_time=font_path.stat().st_mtime
            )
            folders[folder].append(file_ptr)
        
        # Step 3: Create FamilyPointer objects
        self.families = []
        for folder, file_ptrs in folders.items():
            # Use folder name as family name (will be refined when parsed)
            family_name = folder.name
            
            # Check for .fontpalette or family hint file (optional)
            # Some folders might contain a .family.json with proper name
            hint_file = folder / ".family.json"
            if hint_file.exists():
                try:
                    with open(hint_file, 'r') as f:
                        hint = json.load(f)
                        family_name = hint.get('family_name', family_name)
                except:
                    pass
            
            family_ptr = FamilyPointer(
                name=family_name,
                folder_path=folder,
                file_ptrs=file_ptrs,
                needs_parsing=True
            )
            self.families.append(family_ptr)
        
        # Sort alphabetically
        self.families.sort(key=lambda f: f.name.lower())
        
        print(f"Found {len(self.families)} families (lazy mode - no fonts parsed)")
        return self.families
    
    def _find_font_files(self) -> List[Path]:
        """Find all font files recursively"""
        font_files = []
        for ext in self.font_extensions:
            font_files.extend(self.root_path.rglob(f'*{ext}'))
        return font_files
    
    def parse_family(self, family_ptr: FamilyPointer, 
                    progress_callback: Optional[Callable] = None) -> FontFamily:
        """
        Parse a single family on demand.
        Called when user actually views this family.
        
        Args:
            family_ptr: The family pointer to parse
            progress_callback: Optional callback(current, total, filename)
            
        Returns:
            Parsed FontFamily object
        """
        # Check cache first
        if family_ptr.name in self._parsed_cache:
            # Update access order for LRU
            self._update_lru(family_ptr.name)
            return self._parsed_cache[family_ptr.name]
        
        print(f"Parsing family on demand: {family_ptr.name}")
        
        # Parse all font files in this family
        from fontTools.ttLib import TTFont
        
        styles = []
        has_persian = False
        has_variable = False
        weights = []
        
        for i, file_ptr in enumerate(family_ptr.file_ptrs):
            if progress_callback:
                progress_callback(i + 1, len(family_ptr.file_ptrs), file_ptr.path.name)
            
            try:
                font = TTFont(file_ptr.path)
                
                # Extract metadata
                name_table = font['name']
                style_name = self._get_name_entry(name_table, 2) or "Regular"
                family_name_from_font = self._get_name_entry(name_table, 1) or family_ptr.name
                
                # Get weight
                weight = 400
                if 'OS/2' in font:
                    weight = font['OS/2'].usWeightClass
                
                # Check italic
                is_italic = 'italic' in style_name.lower() or 'oblique' in style_name.lower()
                
                # Check variable
                is_variable = 'fvar' in font
                if is_variable:
                    has_variable = True
                
                # Count glyphs
                glyph_count = len(font.getGlyphOrder())
                
                # Check Persian support (quick check)
                if not has_persian:
                    has_persian = self._check_persian_support(font)
                
                font.close()
                
                style = FontStyle(
                    path=file_ptr.path,
                    style_name=style_name,
                    weight=weight,
                    is_italic=is_italic,
                    is_variable=is_variable,
                    glyph_count=glyph_count,
                    fingerprint=str(hash(file_ptr.path))
                )
                styles.append(style)
                weights.append(weight)
                
            except Exception as e:
                print(f"Warning: Failed to parse {file_ptr.path.name}: {e}")
                continue
        
        if not styles:
            raise ValueError(f"No valid fonts found in {family_ptr.name}")
        
        # Generate stable colors
        colors = ColorGenerator.get_colors(family_ptr.name)
        
        # Create FontFamily
        family = FontFamily(
            family_name=family_ptr.name,
            styles=styles,
            source_folder=family_ptr.folder_path,
            bg_color=colors['bg'],
            text_color=colors['text'],
            has_persian=has_persian,
            has_variable=has_variable,
            weight_range=(min(weights), max(weights)) if weights else (400, 400)
        )
        
        # Cache it
        self._cache_family(family_ptr.name, family)
        
        # Mark as parsed
        family_ptr.needs_parsing = False
        family_ptr.parsed_family = family
        
        return family
    
    def _get_name_entry(self, name_table, name_id: int) -> Optional[str]:
        """Extract name entry from font name table"""
        try:
            name = name_table.getName(name_id, 3, 1, 0x409)
            if name:
                return str(name)
            for record in name_table.names:
                if record.nameID == name_id:
                    return str(record)
        except:
            pass
        return None
    
    def _check_persian_support(self, font) -> bool:
        """Quick check if font supports Persian/Arabic"""
        # Persian/Arabic Unicode range
        persian_range = range(0x0600, 0x06FF)
        
        cmap = font.getBestCmap()
        if not cmap:
            return False
        
        # Sample Persian characters
        persian_chars = [0x06AF, 0x067E, 0x0686, 0x0698, 0x0628, 0x062C, 0x062F]
        return any(c in cmap for c in persian_chars)
    
    def _cache_family(self, name: str, family: FontFamily):
        """Cache parsed family with LRU eviction"""
        self._parsed_cache[name] = family
        self._update_lru(name)
        
        # Evict if over limit
        while len(self._parsed_cache) > self.MAX_CACHED_FAMILIES:
            oldest = self._access_order.pop(0) if self._access_order else None
            if oldest and oldest in self._parsed_cache:
                del self._parsed_cache[oldest]
                print(f"Evicted from cache: {oldest}")
    
    def _update_lru(self, name: str):
        """Update LRU access order"""
        if name in self._access_order:
            self._access_order.remove(name)
        self._access_order.append(name)
    
    def get_family(self, index: int, parse: bool = True) -> Optional[FontFamily]:
        """
        Get family by index.
        
        Args:
            index: Index in families list
            parse: If True, parse on demand; if False, return pointer
            
        Returns:
            FontFamily if parse=True, otherwise FamilyPointer
        """
        if index < 0 or index >= len(self.families):
            return None
        
        family_ptr = self.families[index]
        
        if parse and family_ptr.needs_parsing:
            return self.parse_family(family_ptr)
        elif parse and family_ptr.parsed_family:
            return family_ptr.parsed_family
        elif parse:
            return self.parse_family(family_ptr)
        else:
            return family_ptr
    
    def get_family_by_name(self, name: str) -> Optional[FontFamily]:
        """Get parsed family by name"""
        return self._parsed_cache.get(name)
    
    def clear_cache(self):
        """Clear parsed font cache to free memory"""
        self._parsed_cache.clear()
        self._access_order.clear()
        for family_ptr in self.families:
            family_ptr.needs_parsing = True
            family_ptr.parsed_family = None
        print("Font cache cleared")
    
    def get_stats(self) -> dict:
        """Get library statistics"""
        return {
            'total_families': len(self.families),
            'cached_families': len(self._parsed_cache),
            'cache_limit': self.MAX_CACHED_FAMILIES,
            'total_font_files': sum(len(f.file_ptrs) for f in self.families),
            'lazy_mode': True
        }
    
    def __len__(self):
        return len(self.families)
    
    def __getitem__(self, index: int) -> FontFamily:
        """Allow indexing - auto-parse on demand"""
        result = self.get_family(index, parse=True)
        if result is None:
            raise IndexError(f"Family index {index} out of range")
        return result