#!/usr/bin/env python3
"""
Chunking Performance Karşılaştırma Testi
"""

import os
import sys
import json
from time import time

sys.path.append('.')

from chunker import chunk_text as old_chunk_text
from chunker_smart import SmartChunker
from utils import extract_text

def compare_chunking_performance():
    """Eski vs Yeni chunking sistemini karşılaştır"""
    
    print("🧪 CHUNKING PERFORMANCE KARŞILAŞTIRMASI")
    print("=" * 60)
    
    # Test dosyaları
    test_files = [
        './example_docs/rocket_instructions.txt',
        './example_docs/flight_manual.txt', 
        './test_docs/test_content.txt'
    ]
    
    chunker = SmartChunker()
    
    old_total_time = 0
    new_total_time = 0
    old_total_chunks = 0
    new_total_chunks = 0
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"⚠️  Dosya bulunamadı: {file_path}")
            continue
            
        print(f"\n📄 Test Dosyası: {file_path}")
        text = extract_text(file_path)
        print(f"📏 Metin uzunluğu: {len(text)} karakter, {len(text.split())} kelime")
        
        # ESKİ CHUNKING TESTİ
        start_time = time()
        old_chunks = old_chunk_text(text)
        old_time = time() - start_time
        old_total_time += old_time
        old_total_chunks += len(old_chunks)
        
        # YENİ CHUNKING TESTİ  
        start_time = time()
        new_chunks = chunker.chunk_document(text, file_path)
        new_time = time() - start_time
        new_total_time += new_time
        new_total_chunks += len(new_chunks)
        
        # KARŞILAŞTIRMA
        print(f"⏱️  Eski chunking: {old_time*1000:.2f}ms - {len(old_chunks)} chunks")
        print(f"⚡ Yeni chunking: {new_time*1000:.2f}ms - {len(new_chunks)} chunks")
        
        if new_time > 0:
            speedup = old_time / new_time
            print(f"📈 Hız karşılaştırması: {speedup:.2f}x {'HIZLI' if speedup > 1 else 'YAVAS'}")
        
        # METADATA KARŞILAŞTIRMASI
        if old_chunks and new_chunks:
            old_meta_fields = len(old_chunks[0]['meta'].keys())
            new_meta_fields = len(new_chunks[0]['meta'].keys())
            print(f"🏷️  Metadata zenginliği: {old_meta_fields} → {new_meta_fields} fields (+{new_meta_fields-old_meta_fields})")
            
            print(f"📋 Yeni metadata alanları:")
            new_fields = set(new_chunks[0]['meta'].keys()) - set(old_chunks[0]['meta'].keys())
            for field in sorted(new_fields):
                print(f"   + {field}: {new_chunks[0]['meta'][field]}")
    
    print("\n" + "=" * 60)
    print("📊 GENEL PERFORMANS ÖZETİ")
    print(f"⏱️  Toplam eski chunking süresi: {old_total_time*1000:.2f}ms")
    print(f"⚡ Toplam yeni chunking süresi: {new_total_time*1000:.2f}ms") 
    
    if new_total_time > 0:
        overall_speedup = old_total_time / new_total_time
        print(f"📈 Genel hız iyileştirmesi: {overall_speedup:.2f}x")
    
    print(f"🔢 Chunk sayıları: {old_total_chunks} → {new_total_chunks}")
    
    print("\n✅ SMART CHUNKING ÖZELLİKLERİ:")
    print("   • Belge tipine göre adaptive strateji")
    print("   • Paragraf/cümle sınırlarına saygılı")
    print("   • Zengin metadata (dosya tipi, yapısal bilgi)")
    print("   • PowerPoint slide-bazlı chunking")
    print("   • Excel sheet-bazlı chunking")
    print("   • OCR içerik ayrımı")

if __name__ == '__main__':
    compare_chunking_performance()