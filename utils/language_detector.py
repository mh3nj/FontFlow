"""
FontFlow Studio - Language Detector
Simplified version that works with existing code
"""

from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from fontTools.ttLib import TTFont


@dataclass
class ScriptInfo:
    """Information about a script/language"""
    name: str
    code: str
    sample_chars: List[int]
    emoji: str
    sample_text: str


class LanguageDetector:
    """
    Detects which scripts a font supports.
    Simplified version for basic detection.
    """
    
    # Basic scripts to detect
    SCRIPTS = {
        'latin': ScriptInfo(
            name='Latin',
            code='latin',
            sample_chars=[0x0041, 0x0042, 0x0043],  # A, B, C
            emoji='🔤',
            sample_text='The Quick Brown Fox'
        ),
        'arabic': ScriptInfo(
            name='Arabic',
            code='arabic',
            sample_chars=[0x0627, 0x0628, 0x062C],  # ا, ب, ج
            emoji='🇸🇦',
            sample_text='السلام عليكم'
        ),
        'arabic_persian': ScriptInfo(
            name='Persian',
            code='arabic_persian',
            sample_chars=[0x06AF, 0x067E, 0x0686],  # گ, پ, چ
            emoji='🇮🇷',
            sample_text='درود بر جهان'
        ),
        'cyrillic': ScriptInfo(
            name='Cyrillic',
            code='cyrillic',
            sample_chars=[0x0410, 0x0411, 0x0412],  # А, Б, В
            emoji='🇷🇺',
            sample_text='Привет мир'
        ),
        'hebrew': ScriptInfo(
            name='Hebrew',
            code='hebrew',
            sample_chars=[0x05D0, 0x05D1, 0x05D2],  # א, ב, ג
            emoji='🇮🇱',
            sample_text='שלום עולם'
        ),
        'devanagari': ScriptInfo(
            name='Devanagari',
            code='devanagari',
            sample_chars=[0x0915, 0x0916, 0x0917],  # क, ख, ग
            emoji='🇮🇳',
            sample_text='नमस्ते दुनिया'
        ),
        'hangul': ScriptInfo(
            name='Korean',
            code='hangul',
            sample_chars=[0xAC00, 0xAC01, 0xAC02],  # 가, 각, 갂
            emoji='🇰🇷',
            sample_text='안녕하세요 세계'
        ),
        'cjk': ScriptInfo(
            name='Chinese',
            code='cjk',
            sample_chars=[0x4E00, 0x4E01, 0x4E02],  # 一, 丁, 丂
            emoji='🇨🇳',
            sample_text='你好世界'
        ),
        'emoji': ScriptInfo(
            name='Emoji',
            code='emoji',
            sample_chars=[0x1F600, 0x1F601, 0x1F602],  # 😀, 😁, 😂
            emoji='😊',
            sample_text='😀 😃 😄'
        ),
    }
    
    def __init__(self):
        self.font_path: Optional[Path] = None
    
    def analyze_font(self, font_path: Path) -> Dict[str, ScriptInfo]:
        """
        Analyze a font file and return which scripts it supports.
        
        Args:
            font_path: Path to font file
            
        Returns:
            Dictionary of script_code -> ScriptInfo for supported scripts
        """
        supported = {}
        
        try:
            font = TTFont(font_path)
            cmap = font.getBestCmap()
            
            if not cmap:
                font.close()
                return supported
            
            glyph_set = set(cmap.keys())
            
            for code, script_info in self.SCRIPTS.items():
                if self._script_supported(script_info, glyph_set):
                    supported[code] = script_info
            
            font.close()
            
        except Exception as e:
            print(f"Error analyzing {font_path.name}: {e}")
        
        return supported
    
    def _script_supported(self, script_info: ScriptInfo, glyph_set: Set[int]) -> bool:
        """Check if script is supported (at least 2 sample chars)"""
        found = 0
        for char_code in script_info.sample_chars:
            if char_code in glyph_set:
                found += 1
                if found >= 2:
                    return True
        return False
    
    def get_supported_summary(self, font_path: Path) -> str:
        """Get emoji summary of supported scripts"""
        scripts = self.analyze_font(font_path)
        if not scripts:
            return "🔤"
        return ' '.join([s.emoji for s in scripts.values()][:4])