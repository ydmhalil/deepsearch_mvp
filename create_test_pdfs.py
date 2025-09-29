#!/usr/bin/env python3
"""
PDF Test Dokümanları Oluşturucu
"""

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import os


def create_test_pdf():
    """Test PDF'i oluştur"""
    
    pdf_path = "./test_docs/sirket_guvenlik_elkitabi.pdf"
    
    # PDF dokümanı oluştur
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    
    # Stil tanımlamaları
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=12,
        textColor='darkblue'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'], 
        fontSize=14,
        spaceAfter=10,
        textColor='darkgreen'
    )
    
    # PDF içeriği
    content = []
    
    # Başlık
    content.append(Paragraph("DeepSearch MVP - PDF Test Dokümanı", title_style))
    content.append(Spacer(1, 0.2*inch))
    
    content.append(Paragraph("Şirket Güvenlik El Kitabı", styles['Heading1']))
    content.append(Spacer(1, 0.2*inch))
    
    # Bölüm 1
    content.append(Paragraph("1. Acil Durum Prosedürleri", heading_style))
    
    content.append(Paragraph("<b>Yangın Alarm Prosedürü:</b>", styles['Normal']))
    yangın_steps = [
        "1. Yangın alarmı duyulduğunda derhal bölgeyi boşaltın",
        "2. En yakın yangın çıkışını kullanın", 
        "3. Asansör kullanmayın, merdivenleri tercih edin",
        "4. Toplanma noktasında bekleyin",
        "5. Güvenlik görevlisinin talimatlarını izleyin"
    ]
    
    for step in yangın_steps:
        content.append(Paragraph(step, styles['Normal']))
    
    content.append(Spacer(1, 0.1*inch))
    
    content.append(Paragraph("<b>Deprem Güvenlik Kuralları:</b>", styles['Normal']))
    deprem_rules = [
        "• Masa altına saklanın veya duvar kenarına çekilin",
        "• Cam ve ağır eşyalardan uzak durun", 
        "• Sarsıntı durduktan sonra dikkatlice tahliye edin"
    ]
    
    for rule in deprem_rules:
        content.append(Paragraph(rule, styles['Normal']))
    
    content.append(Spacer(1, 0.2*inch))
    
    # Bölüm 2
    content.append(Paragraph("2. Laboratuvar Güvenlik Prosedürleri", heading_style))
    
    content.append(Paragraph("<b>Kimyasal Güvenlik:</b>", styles['Normal']))
    kimya_rules = [
        "• Tüm kimyasalları etiketli kaplarda saklayın",
        "• Güvenlik gözlüğü ve eldiven kullanın",
        "• Havalandırma sistemi çalışır durumda olmalı",
        "• MSDS (Material Safety Data Sheet) bilgilerini bilin"
    ]
    
    for rule in kimya_rules:
        content.append(Paragraph(rule, styles['Normal']))
    
    content.append(Spacer(1, 0.1*inch))
    
    content.append(Paragraph("<b>Ekipman Güvenliği:</b>", styles['Normal']))
    ekipman_rules = [
        "• Düzenli kalibrasyonları yapın",
        "• Arızalı ekipmanları derhal raporlayın", 
        "• Kullanım öncesi güvenlik kontrolü yapın"
    ]
    
    for rule in ekipman_rules:
        content.append(Paragraph(rule, styles['Normal']))
    
    content.append(Spacer(1, 0.2*inch))
    
    # Bölüm 3
    content.append(Paragraph("3. Veri Güvenliği", heading_style))
    
    content.append(Paragraph("<b>Bilgi İşlem Güvenlik Kuralları:</b>", styles['Normal']))
    bilgi_rules = [
        "• Güçlü parolalar kullanın (en az 8 karakter, büyük/küçük harf, rakam)",
        "• İki faktörlü doğrulama aktif edin",
        "• Düzenli yedekleme yapın",
        "• Şüpheli e-postalar açmayın"
    ]
    
    for rule in bilgi_rules:
        content.append(Paragraph(rule, styles['Normal']))
    
    content.append(Spacer(1, 0.1*inch))
    
    content.append(Paragraph("<b>Fiziksel Güvenlik:</b>", styles['Normal']))
    fizik_rules = [
        "• Çalışma alanınızı kilitleyerek ayrılın",
        "• Misafir kartları daima görünür yerde taşıyın",
        "• Güvenlik kamerası alanlarını engellemeyedin"
    ]
    
    for rule in fizik_rules:
        content.append(Paragraph(rule, styles['Normal']))
    
    content.append(Spacer(1, 0.3*inch))
    
    # Footer
    content.append(Paragraph("---", styles['Normal']))
    content.append(Paragraph("<b>Son Güncelleme:</b> 29 Eylül 2025", styles['Normal']))
    content.append(Paragraph("<b>Doküman No:</b> SGB-2025-001", styles['Normal']))
    content.append(Paragraph("<b>Hazırlayan:</b> Güvenlik Departmanı", styles['Normal']))
    content.append(Spacer(1, 0.1*inch))
    content.append(Paragraph("<i>Bu doküman PDF test amaçlı oluşturulmuştur.</i>", styles['Normal']))
    
    # PDF'i oluştur
    doc.build(content)
    
    print(f"✅ Test PDF oluşturuldu: {pdf_path}")
    return pdf_path


def create_additional_test_files():
    """Ek test dosyaları oluştur"""
    
    # Excel benzeri test dosyası
    excel_content = """Sheet: Personel Listesi
Ad | Soyad | Departman | Pozisyon | Telefon
Ahmet | Yılmaz | IT | Yazılım Geliştirici | 555-0101  
Fatma | Kaya | İK | İnsan Kaynakları Uzmanı | 555-0102
Mehmet | Öz | Güvenlik | Güvenlik Amiri | 555-0103
Ayşe | Demir | Muhasebe | Mali Müşavir | 555-0104

Sheet: Departman Bütçeleri  
Departman | 2025 Bütçe | Harcanan | Kalan
IT | 500000 | 350000 | 150000
İK | 200000 | 180000 | 20000  
Güvenlik | 150000 | 120000 | 30000
Muhasebe | 100000 | 95000 | 5000"""
    
    with open('./test_docs/sirket_verileri.xlsx.txt', 'w', encoding='utf-8') as f:
        f.write(excel_content)
    
    print("✅ Excel benzeri test dosyası oluşturuldu: ./test_docs/sirket_verileri.xlsx.txt")


if __name__ == '__main__':
    print("📄 PDF Test Dosyaları Oluşturuluyor...")
    create_test_pdf()
    create_additional_test_files()
    print("🎉 Tüm test dosyaları hazır!")