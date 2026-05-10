"""
FontFlow Studio - Text Samples
Provides preview text in English and Persian
"""


class TextSamples:
    """Repository of text samples for font preview"""
    
    # English samples
    ENGLISH_HEADLINE = "The Quick Brown Fox Jumps Over The Lazy Dog"
    
    ENGLISH_ALPHABET = (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ\n"
        "abcdefghijklmnopqrstuvwxyz\n"
        "0123456789 !@#$%^&*()"
    )
    
    ENGLISH_PARAGRAPH = (
        "Professional typography requires attention to detail and an understanding "
        "of how type performs across various contexts. Great typefaces balance form "
        "and function, ensuring readability while maintaining visual interest."
    )
    
    # Persian samples (includes Persian-specific letters: گ پ چ ژ)
    PERSIAN_HEADLINE = "طراحی تایپوگرافی ایران"
    
    PERSIAN_ALPHABET = (
        "ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی\n"
        "ءآأؤئا ة\n"
        "۰۱۲۳۴۵۶۷۸۹"
    )
    
    PERSIAN_PARAGRAPH = (
        "طراحی گرافیک و تایپوگرافی فارسی نیازمند دقت و توجه به جزئیات است. "
        "فونت‌های خوب باید حروف مانند گ، ژ، پ و چ را به‌خوبی نمایش دهند. "
        "ایران و کشورهای فارسی‌زبان از این حروف استفاده می‌کنند."
    )
    
    # Nastaliq-style stress test (complex shaping with Persian letters)
    PERSIAN_NASTALIQ_STRESS = "پیچیدگی‌های خطوط نستعلیق و شکسته در ایران"
    
    # UI microcopy (Persian)
    PERSIAN_UI_MICRO = "۱۲:۳۴ · فایل · ویرایش · ذخیره · گزینه‌ها · خروج"
    
    # Logo test (includes Persian-specific letters)
    LOGO_ENGLISH = "PARSEGAN"
    LOGO_PERSIAN = "پارسگان"  # Includes گ
    
    @staticmethod
    def get_default_english() -> str:
        """Get default English preview text (combined)"""
        return (
            f"{TextSamples.ENGLISH_HEADLINE}\n\n"
            f"{TextSamples.ENGLISH_ALPHABET}\n\n"
            f"{TextSamples.ENGLISH_PARAGRAPH}"
        )
    
    @staticmethod
    def get_default_persian() -> str:
        """Get default Persian preview text (combined)"""
        return (
            f"{TextSamples.PERSIAN_HEADLINE}\n\n"
            f"{TextSamples.PERSIAN_ALPHABET}\n\n"
            f"{TextSamples.PERSIAN_PARAGRAPH}"
        )
    
    @staticmethod
    def get_persian_stress_samples() -> list:
        """Get Persian shaping stress test samples"""
        return [
            TextSamples.PERSIAN_PARAGRAPH,
            TextSamples.PERSIAN_NASTALIQ_STRESS,
            TextSamples.PERSIAN_UI_MICRO,
        ]
