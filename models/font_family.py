"""
FontFlow Studio - Font Family Data Models
Represents font families and individual styles with language support
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import time


@dataclass
class FontStyle:
    """Individual font file within a family"""
    
    path: Path
    style_name: str              # e.g., "Bold Italic"
    weight: int                  # 100-900 (CSS weight scale)
    is_italic: bool
    is_variable: bool
    glyph_count: int
    fingerprint: str             # Hash of outline data for duplicate detection
    
    # Optional metadata
    width: Optional[str] = None  # "Normal", "Condensed", "Extended"
    
    def __str__(self):
        return f"{self.style_name} ({self.weight})"
    
    @property
    def weight_name(self) -> str:
        """Human-readable weight name"""
        weight_map = {
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
        return weight_map.get(self.weight, f"Weight {self.weight}")


@dataclass
class FontFamily:
    """Complete font family unit - the main entity we work with"""
    
    family_name: str
    styles: List[FontStyle]
    source_folder: Path
    
    # Visual identity (stable across sessions - generated from family name)
    bg_color: Tuple[int, int, int]      # RGB tuple
    text_color: Tuple[int, int, int]    # RGB tuple
    
    # Font capabilities (detected on load)
    has_persian: bool = False
    has_variable: bool = False
    weight_range: Tuple[int, int] = (400, 400)  # (min_weight, max_weight)
    
    # Language support (detected on demand)
    supported_scripts: List[str] = field(default_factory=list)
    language_summary: str = ""
    language_samples: Dict[str, str] = field(default_factory=dict)
    
    # UI state (ephemeral - resets each session)
    current_style_index: int = 0
    viewed_count: int = 0
    last_viewed: Optional[float] = None
    
    # Classification state
    classified: bool = False
    classification_stage: Optional[str] = None  # "A" or "B"
    
    def __post_init__(self):
        """Validate and compute derived properties"""
        if not self.styles:
            raise ValueError(f"Family '{self.family_name}' has no styles")
        
        # Sort styles by weight, then italic
        self.styles.sort(key=lambda s: (s.weight, s.is_italic))
        
        # Compute weight range
        weights = [s.weight for s in self.styles]
        self.weight_range = (min(weights), max(weights))
        
        # Check for variable fonts
        self.has_variable = any(s.is_variable for s in self.styles)
    
    @property
    def current_style(self) -> FontStyle:
        """Get the currently displayed style"""
        return self.styles[self.current_style_index]
    
    def next_style(self) -> FontStyle:
        """Cycle to next style and return it"""
        self.current_style_index = (self.current_style_index + 1) % len(self.styles)
        self.viewed_count += 1
        self.last_viewed = time.time()
        return self.current_style
    
    def prev_style(self) -> FontStyle:
        """Cycle to previous style and return it"""
        self.current_style_index = (self.current_style_index - 1) % len(self.styles)
        return self.current_style
    
    def get_style_by_weight(self, target_weight: int) -> Optional[FontStyle]:
        """Find the style closest to the target weight"""
        if not self.styles:
            return None
        
        return min(self.styles, key=lambda s: abs(s.weight - target_weight))
    
    def get_regular(self) -> Optional[FontStyle]:
        """Get the Regular weight (or closest to 400)"""
        return self.get_style_by_weight(400)
    
    def get_bold(self) -> Optional[FontStyle]:
        """Get the Bold weight (or closest to 700)"""
        return self.get_style_by_weight(700)
    
    def get_heaviest(self) -> FontStyle:
        """Get the heaviest weight in the family"""
        return max(self.styles, key=lambda s: s.weight)
    
    def get_lightest(self) -> FontStyle:
        """Get the lightest weight in the family"""
        return min(self.styles, key=lambda s: s.weight)
    
    @property
    def style_count(self) -> int:
        """Number of styles in this family"""
        return len(self.styles)
    
    @property
    def weight_range_name(self) -> str:
        """Human-readable weight range"""
        min_style = self.get_lightest()
        max_style = self.get_heaviest()
        
        if min_style.weight == max_style.weight:
            return min_style.weight_name
        
        return f"{min_style.weight_name} → {max_style.weight_name}"
    
    def detect_supported_languages(self, detector=None) -> List[str]:
        """
        Detect which scripts this font supports.
        Called on demand when viewing family.
        
        Args:
            detector: LanguageDetector instance (created if not provided)
            
        Returns:
            List of supported script codes
        """
        # Avoid re-detecting
        if self.supported_scripts:
            return self.supported_scripts
        
        try:
            from utils.language_detector import LanguageDetector
            
            if detector is None:
                detector = LanguageDetector()
            
            all_scripts = set()
            samples = {}
            
            # Check first few styles (don't need to check all)
            styles_to_check = min(3, len(self.styles))
            
            for i in range(styles_to_check):
                style = self.styles[i]
                try:
                    scripts = detector.analyze_font(style.path)
                    all_scripts.update(scripts.keys())
                    
                    # Collect sample texts
                    for code, script in scripts.items():
                        if code not in samples:
                            samples[code] = script.sample_text
                except Exception as e:
                    print(f"  Warning: Could not analyze {style.path.name}: {e}")
            
            self.supported_scripts = sorted(all_scripts)
            self.language_samples = samples
            
            # Create summary with emojis
            emoji_map = {
                'latin': '🔤',
                'latin_extended': '🌍',
                'cyrillic': '🇷🇺',
                'greek': '🇬🇷',
                'arabic': '🇸🇦',
                'arabic_persian': '🇮🇷',
                'hebrew': '🇮🇱',
                'devanagari': '🇮🇳',
                'bengali': '🇧🇩',
                'gurmukhi': '🇮🇳',
                'gujarati': '🇮🇳',
                'tamil': '🇮🇳',
                'telugu': '🇮🇳',
                'kannada': '🇮🇳',
                'malayalam': '🇮🇳',
                'sinhala': '🇱🇰',
                'thai': '🇹🇭',
                'lao': '🇱🇦',
                'tibetan': '🇹🇮',
                'georgian': '🇬🇪',
                'armenian': '🇦🇲',
                'hangul': '🇰🇷',
                'hiragana': '🇯🇵',
                'katakana': '🇯🇵',
                'cjk': '🇨🇳',
                'emoji': '😊',
            }
            
            summary_parts = []
            for script in self.supported_scripts[:4]:  # Show max 4
                summary_parts.append(emoji_map.get(script, '📝'))
            
            self.language_summary = ' '.join(summary_parts) if summary_parts else '🔤'
            
        except ImportError as e:
            print(f"Language detector not available: {e}")
            self.supported_scripts = ['latin']
            self.language_summary = '🔤'
        
        return self.supported_scripts
    
    def get_language_sample(self, max_samples: int = 3) -> str:
        """
        Get combined sample text from supported languages.
        
        Args:
            max_samples: Maximum number of language samples to show
            
        Returns:
            Combined sample text
        """
        if not self.language_samples:
            self.detect_supported_languages()
        
        if not self.language_samples:
            return "The Quick Brown Fox"
        
        # Prioritize certain scripts
        priority = ['latin', 'arabic', 'arabic_persian', 'cyrillic', 
                   'devanagari', 'hangul', 'cjk']
        
        samples = []
        for script in priority:
            if script in self.language_samples and len(samples) < max_samples:
                samples.append(self.language_samples[script])
        
        # Fill with any remaining
        if len(samples) < max_samples:
            for script, text in self.language_samples.items():
                if script not in priority and len(samples) < max_samples:
                    samples.append(text)
        
        return '\n\n'.join(samples)
    
    def __str__(self):
        return f"{self.family_name} ({self.style_count} styles)"
    
    def __repr__(self):
        return f"FontFamily('{self.family_name}', {self.style_count} styles, {self.weight_range_name})"


@dataclass
class DuplicatePair:
    """Represents a potential duplicate font pair"""
    
    family_a: FontFamily
    family_b: FontFamily
    confidence: float          # 0.0 - 1.0
    reasons: List[str]         # Human-readable explanation
    
    @property
    def is_likely_duplicate(self) -> bool:
        """High confidence duplicate"""
        return self.confidence >= 0.85
    
    def __str__(self):
        return f"{self.family_a.family_name} ≈ {self.family_b.family_name} ({self.confidence:.1%})"
