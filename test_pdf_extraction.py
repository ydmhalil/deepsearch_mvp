#!/usr/bin/env python3
"""
PDF Test Script - PDF extraction'ı test et
"""

import sys
sys.path.append('.')

from utils import extract_text

def test_pdf_extraction():
    """PDF extraction'ı test et"""
    
    print("🔍 PDF EXTRACTION TESTİ")
    print("=" * 50)
    
    pdf_path = "./test_docs/sirket_guvenlik_elkitabi.pdf"
    
    try:
        print(f"📄 PDF dosyası: {pdf_path}")
        text = extract_text(pdf_path)
        
        if text:
            print(f"✅ PDF extraction başarılı!")
            print(f"📏 Çıkarılan metin uzunluğu: {len(text)} karakter")
            print(f"📏 Kelime sayısı: {len(text.split())} kelime")
            
            print(f"\n📝 İlk 500 karakter:")
            print("-" * 50)
            print(text[:500])
            print("-" * 50)
            
            # Anahtar kelime kontrolü
            keywords = ["güvenlik", "yangın", "deprem", "laboratuvar", "kimyasal", "prosedür"]
            found_keywords = [kw for kw in keywords if kw.lower() in text.lower()]
            
            print(f"\n🔍 Bulunan anahtar kelimeler: {', '.join(found_keywords)}")
            print(f"📊 Anahtar kelime başarı oranı: {len(found_keywords)}/{len(keywords)} ({len(found_keywords)/len(keywords)*100:.1f}%)")
            
            if len(found_keywords) >= len(keywords) * 0.7:
                print("✅ PDF extraction kalitesi: İYİ")
                return True
            else:
                print("⚠️  PDF extraction kalitesi: ORTA")
                return False
        else:
            print("❌ PDF'den metin çıkarılamadı!")
            return False
            
    except Exception as e:
        print(f"❌ PDF extraction hatası: {e}")
        return False

if __name__ == '__main__':
    test_pdf_extraction()