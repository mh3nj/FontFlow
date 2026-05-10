#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Persian Text Test Script
Tests if Persian text reshaping is working correctly
"""

print("=" * 60)
print("Persian Text Rendering Test")
print("=" * 60)

# Test 1: Check if packages are installed
print("\n1. Checking required packages...")
try:
    import arabic_reshaper
    print("   ✓ arabic-reshaper installed")
except ImportError:
    print("   ✗ arabic-reshaper NOT installed")
    print("   Install with: pip install arabic-reshaper")
    exit(1)

try:
    from bidi.algorithm import get_display
    print("   ✓ python-bidi installed")
except ImportError:
    print("   ✗ python-bidi NOT installed")
    print("   Install with: pip install python-bidi")
    exit(1)

# Test 2: Test word reshaping
print("\n2. Testing Persian word reshaping...")
test_words = [
    "ایران",      # Iran (includes ی)
    "پارسگان",    # Parsegan (includes گ)
    "مؤسسه",      # Institution (includes ؤ)
    "فارسی",      # Farsi
    "تهران",      # Tehran
]

print("\n   Raw → Reshaped:")
for word in test_words:
    reshaped = arabic_reshaper.reshape(word)
    display = get_display(reshaped)
    print(f"   {word} → {display}")

# Test 3: Test full sentence
print("\n3. Testing full sentence...")
sentence = "طراحی گرافیک و تایپوگرافی فارسی در ایران"
print(f"   Raw: {sentence}")
reshaped = arabic_reshaper.reshape(sentence)
display = get_display(reshaped)
print(f"   Shaped: {display}")

# Test 4: Test Persian-specific letters
print("\n4. Testing Persian-specific letters (not in Arabic)...")
persian_letters = {
    'گ': 'Gāf (Persian G)',
    'پ': 'Pe (Persian P)',
    'چ': 'Che (Persian Ch)',
    'ژ': 'Zhe (Persian Zh)',
}

for letter, name in persian_letters.items():
    reshaped = arabic_reshaper.reshape(letter)
    display = get_display(reshaped)
    print(f"   {letter} ({name}) → {display}")

# Test 5: Check character connection
print("\n5. Testing letter connection...")
test_connection = "بسم"  # Should connect: ب + س + م = بسم
print(f"   Raw letters: ب س م")
reshaped = arabic_reshaper.reshape(test_connection)
display = get_display(reshaped)
print(f"   Connected: {display}")
print(f"   (Letters should be connected, not isolated)")

print("\n" + "=" * 60)
print("✓ All tests completed!")
print("=" * 60)
print("\nIf you see properly connected Persian text above,")
print("then Persian support is working correctly in FontFlow.")
print("\nExpected results:")
print("  - Words should be RIGHT-TO-LEFT")
print("  - Letters should be CONNECTED (not isolated)")
print("  - Persian letters (گ پ چ ژ) should display")
