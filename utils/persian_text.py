"""
FontFlow Studio - Persian Text Handler
Proper bidirectional text and Arabic/Persian shaping
"""

try:
    import arabic_reshaper
    PERSIAN_SUPPORT = True
    print("✓ Persian text support loaded (arabic-reshaper)")
except ImportError as e:
    PERSIAN_SUPPORT = False
    print(f"⚠ Persian text support not available: {e}")
    print("  Install with: pip install arabic-reshaper")


class PersianTextHandler:
    """
    Handles proper rendering of Persian/Arabic text.
    
    Persian text requires:
    1. Reshaping: Connect letters properly (ا + ب + ج → ابج)
    2. RTL display: Handled by Qt's layout direction, not bidi.algorithm
    """
    
    @staticmethod
    def prepare_text(text: str) -> str:
        """
        Prepare Persian/Arabic text for display.
        
        IMPORTANT: We only reshape (connect letters), NOT reverse.
        Qt handles RTL display through setLayoutDirection(RightToLeft).
        
        Args:
            text: Raw Persian/Arabic text
            
        Returns:
            Reshaped text (letters connected, but NOT reversed)
        """
        if not PERSIAN_SUPPORT:
            # Fallback: just return as-is with warning
            print("⚠ Displaying Persian text without reshaping (install arabic-reshaper)")
            return text
        
        try:
            # ONLY reshape (connect letters)
            # Do NOT use bidi.algorithm.get_display() - it reverses everything!
            reshaped = arabic_reshaper.reshape(text)
            
            # Return reshaped text
            # Qt's RightToLeft layout will handle the display direction
            return reshaped
            
        except Exception as e:
            print(f"✗ Error shaping Persian text: {e}")
            return text
    
    @staticmethod
    def is_persian_text(text: str) -> bool:
        """
        Check if text contains Persian/Arabic characters.
        
        Args:
            text: Text to check
            
        Returns:
            True if text contains Persian/Arabic characters
        """
        # Arabic/Persian Unicode range: U+0600 to U+06FF
        persian_range = range(0x0600, 0x0700)
        
        return any(ord(char) in persian_range for char in text)
    
    @staticmethod
    def prepare_if_needed(text: str) -> str:
        """
        Prepare text only if it contains Persian/Arabic characters.
        
        Args:
            text: Text to prepare
            
        Returns:
            Prepared text (or original if no Persian characters)
        """
        if PersianTextHandler.is_persian_text(text):
            return PersianTextHandler.prepare_text(text)
        return text


class TextSampleProvider:
    """
    Provides text samples with proper Persian handling.
    Extends the basic TextSamples with shaping support.
    """
    
    @staticmethod
    def get_english_sample() -> str:
        """Get English sample text"""
        from utils.text_samples import TextSamples
        return TextSamples.get_default_english()
    
    @staticmethod
    def get_persian_sample() -> str:
        """Get Persian sample text with proper shaping"""
        from utils.text_samples import TextSamples
        raw_text = TextSamples.get_default_persian()
        
        if PERSIAN_SUPPORT:
            return PersianTextHandler.prepare_text(raw_text)
        else:
            return raw_text  # Return unshaped if libraries not available
    
    @staticmethod
    def get_persian_stress_samples() -> list:
        """Get Persian stress test samples with proper shaping"""
        from utils.text_samples import TextSamples
        raw_samples = TextSamples.get_persian_stress_samples()
        
        if PERSIAN_SUPPORT:
            return [PersianTextHandler.prepare_text(s) for s in raw_samples]
        else:
            return raw_samples
    
    @staticmethod
    def get_logo_samples() -> dict:
        """Get logo test samples with proper shaping"""
        from utils.text_samples import TextSamples
        
        persian_logo = TextSamples.LOGO_PERSIAN
        if PERSIAN_SUPPORT:
            persian_logo = PersianTextHandler.prepare_text(persian_logo)
        
        return {
            'english': TextSamples.LOGO_ENGLISH,
            'persian': persian_logo,
        }

