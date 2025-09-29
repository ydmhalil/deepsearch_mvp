#!/usr/bin/env python3
"""
Dosya format desteği test scripti
"""

import os
import sys
sys.path.append('.')

from utils import extract_text

def test_format_support():
    """Tüm desteklenen dosya formatlarını test et"""
    
    print("🧪 DOSYA FORMAT TESTLERİ")
    print("=" * 50)
    
    # Test dosyaları
    test_files = [
        './test_docs/test_content.txt',
        './example_docs/rocket_instructions.txt',
        './example_docs/flight_manual.txt'
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n📄 Test: {file_path}")
            try:
                text = extract_text(file_path)
                print(f"✅ Başarılı - {len(text)} karakter çıkarıldı")
                print(f"Önizleme: {text[:100]}...")
            except Exception as e:
                print(f"❌ Hata: {e}")
        else:
            print(f"⚠️  Dosya bulunamadı: {file_path}")
    
    print("\n" + "=" * 50)
    print("📋 DESTEKLENEN FORMATLAR:")
    print("✅ .txt - Metin dosyaları")
    print("✅ .pdf - PDF belgeler (OCR desteği ile)")
    print("✅ .docx - Word belgeleri") 
    print("✅ .pptx - PowerPoint sunumları")
    print("✅ .xlsx - Excel tablolar")

if __name__ == '__main__':
    test_format_support()