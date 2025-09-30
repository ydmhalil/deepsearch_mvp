# DeepSearch MVP - Güvenlik Kılavuzu

## Güvenlik Genel Bakışı

DeepSearch MVP, kurumsal düzeyde güvenlik standartlarıyla tasarlanmış bir belge arama sistemidir. Bu kılavuz, sistemin güvenlik özelliklerini, en iyi uygulamaları ve güvenlik yönetimini kapsar.

## Güvenlik Mimarisi

### Çok Katmanlı Güvenlik

1. **Uygulama Katmanı Güvenliği**
   - Girdi doğrulama ve sanitizasyon
   - XSS ve CSRF koruması
   - SQL enjeksiyon koruması
   - Dosya yükleme güvenliği

2. **Kimlik Doğrulama ve Yetkilendirme**
   - Güvenli oturum yönetimi
   - Rol tabanlı erişim kontrolü
   - Brute force saldırı koruması
   - Oturum zaman aşımı

3. **Veri Güvenliği**
   - Veritabanı şifreleme
   - Dosya sistem güvenliği
   - Veri maskeleme
   - Güvenli yedekleme

4. **Ağ Güvenliği**
   - HTTPS/TLS şifreleme
   - Rate limiting
   - IP engelleme
   - Güvenlik başlıkları

## Güvenlik Özellik Detayları

### 1. Kimlik Doğrulama

#### Güvenli Şifre Politikası
- Minimum 8 karakter uzunluğu
- Büyük ve küçük harf kombinasyonu
- En az bir rakam ve özel karakter
- Yaygın şifrelerin engellemesi
- Şifre geçmişi kontrolü (son 5 şifre)

```python
# Şifre güvenlik kuralları
PASSWORD_REQUIREMENTS = {
    'min_length': 8,
    'require_uppercase': True,
    'require_lowercase': True,
    'require_numbers': True,
    'require_special_chars': True,
    'forbidden_patterns': ['123456', 'password', 'admin']
}
```

#### Oturum Güvenliği
- Güvenli session cookie'leri
- CSRF token koruması
- Otomatik oturum sonlandırma
- Eş zamanlı oturum kontrolü

### 2. Girdi Doğrulama ve Sanitizasyon

#### XSS Koruması
```python
import bleach

def sanitize_input(user_input, input_type='general'):
    if input_type == 'search_query':
        # Arama sorguları için özel temizleme
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-')
        return ''.join(c for c in user_input if c in allowed_chars)
    
    # Genel XSS koruması
    return bleach.clean(user_input, tags=[], attributes={}, strip=True)
```

#### SQL Enjeksiyon Koruması
- Parametrize edilmiş sorgular
- Girdi sanitizasyonu
- Veritabanı izin kontrolü
- Prepared statement kullanımı

#### Path Traversal Koruması
```python
def safe_path(path: str) -> str:
    base = os.path.abspath(os.path.join(os.getcwd()))
    target = os.path.abspath(path)
    if not target.startswith(base):
        raise ValueError('Invalid path - potential directory traversal')
    return target
```

### 3. Rate Limiting ve DDoS Koruması

#### Rate Limiting Kuralları
```python
RATE_LIMITS = {
    'login': {'count': 5, 'window': 300},      # 5 deneme / 5 dakika
    'search': {'count': 100, 'window': 60},    # 100 arama / dakika
    'upload': {'count': 10, 'window': 3600},   # 10 yükleme / saat
    'api': {'count': 1000, 'window': 3600}     # 1000 API çağrısı / saat
}
```

#### IP Engelleme
- Otomatik şüpheli IP algılama
- Coğrafi konum tabanlı engelleme
- Whitelist ve blacklist yönetimi
- Geçici ve kalıcı engelleme

### 4. Dosya Güvenliği

#### Güvenli Dosya Yükleme
```python
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.xlsx', '.txt'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def validate_file(file):
    # Dosya uzantısı kontrolü
    if not file.filename.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
        raise ValueError('Unsupported file type')
    
    # Dosya boyutu kontrolü
    if len(file.read()) > MAX_FILE_SIZE:
        raise ValueError('File too large')
    
    # MIME type kontrolü
    if not is_valid_mime_type(file):
        raise ValueError('Invalid file format')
```

#### Dosya İçerik Analizi
- Malware tarama
- Gizli makro kontrolü
- Dosya bütünlüğü kontrolü
- Virüs tarama entegrasyonu

### 5. Veri Şifreleme

#### Veritabanı Şifreleme
```python
# Hassas veri şifreleme
from cryptography.fernet import Fernet

class DataEncryption:
    def __init__(self, key):
        self.cipher = Fernet(key)
    
    def encrypt_sensitive_data(self, data):
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data):
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

#### Dosya Şifreleme
- AES-256 şifreleme
- Güvenli anahtar yönetimi
- Şifreli yedekleme
- Anahtar rotasyonu

## Güvenlik Monitoring

### 1. Güvenlik Olayları İzleme

#### Monitör Edilen Olaylar
```python
SECURITY_EVENTS = {
    'login_failed': 'medium',
    'login_success': 'low',
    'multiple_failed_logins': 'high',
    'sql_injection_attempt': 'high',
    'xss_attempt': 'high',
    'path_traversal_attempt': 'high',
    'rate_limit_exceeded': 'medium',
    'suspicious_file_upload': 'medium',
    'unauthorized_access_attempt': 'high',
    'data_export': 'medium'
}
```

#### Gerçek Zamanlı Alertler
- E-posta bildirimleri
- SMS uyarıları
- Dashboard uyarıları
- Log merkezi entegrasyonu

### 2. Güvenlik Dashboard

Yöneticiler `/security/dashboard` adresinden şunları izleyebilir:

- **Güvenlik Olayları**: Son güvenlik tehditleri
- **Başarısız Giriş Denemeleri**: Brute force saldırı tespiti
- **Rate Limiting**: Trafik analizı
- **Engellenen IP'ler**: Blacklist durumu
- **Sistem Sağlığı**: Güvenlik durum özeti

### 3. Audit Logging

#### Log Kategorileri
```python
AUDIT_CATEGORIES = {
    'authentication': ['login', 'logout', 'password_change'],
    'data_access': ['file_view', 'search', 'download'],
    'data_modification': ['upload', 'delete', 'update'],
    'administrative': ['user_creation', 'permission_change', 'system_config'],
    'security': ['failed_login', 'security_violation', 'suspicious_activity']
}
```

#### Log Retention
- Güvenlik logları: 2 yıl
- Erişim logları: 1 yıl  
- Sistem logları: 6 ay
- Debug logları: 1 ay

## Güvenlik Yapılandırması

### 1. Güvenlik Başlıkları

```python
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    'Referrer-Policy': 'strict-origin-when-cross-origin'
}
```

### 2. HTTPS Yapılandırması

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Sertifikaları
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # Güvenli SSL Yapılandırması
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

### 3. Firewall Kuralları

```bash
# UFW Firewall Kuralları (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Belirli IP'lerden erişim
sudo ufw allow from 192.168.1.0/24 to any port 22

# Uygulama portunu gizle
sudo ufw deny 8080
```

## Veri Koruma ve Gizlilik

### 1. GDPR Uyumluluğu

#### Veri İşleme İlkeleri
- **Amaç Sınırlaması**: Sadece belirtilen amaçlar için veri işleme
- **Veri Minimizasyonu**: Gerekli minimum veri toplama
- **Doğruluk**: Güncel ve doğru veri tutma
- **Saklama Süresi**: Belirli süre sonra veri silme
- **Bütünlük ve Gizlilik**: Güvenli veri işleme

#### Kullanıcı Hakları
- **Erişim Hakkı**: Kişisel verilere erişim
- **Düzeltme Hakkı**: Yanlış verileri düzeltme
- **Silme Hakkı**: Verilerin silinmesini isteme
- **Taşınabilirlik**: Verileri başka sisteme taşıma
- **İtiraz Hakkı**: Veri işlemeye karşı çıkma

### 2. Veri Sınıflandırması

```python
DATA_CLASSIFICATION = {
    'public': {
        'description': 'Genel erişilebilir bilgiler',
        'examples': ['kullanıcı adı', 'genel belgeler'],
        'protection_level': 'düşük'
    },
    'internal': {
        'description': 'Kurum içi bilgiler',
        'examples': ['departman belgeleri', 'iç prosedürler'],
        'protection_level': 'orta'
    },
    'confidential': {
        'description': 'Gizli bilgiler',
        'examples': ['finansal raporlar', 'stratejik planlar'],
        'protection_level': 'yüksek'
    },
    'restricted': {
        'description': 'Kısıtlı erişim bilgileri',
        'examples': ['kişisel veriler', 'ticari sırlar'],
        'protection_level': 'en yüksek'
    }
}
```

### 3. Veri Maskeleme

```python
def mask_sensitive_data(data, data_type):
    if data_type == 'email':
        name, domain = data.split('@')
        return f"{name[:2]}***@{domain}"
    elif data_type == 'phone':
        return f"***-***-{data[-4:]}"
    elif data_type == 'name':
        return f"{data[0]}***"
    return "***"
```

## Güvenlik Testleri

### 1. Penetrasyon Testleri

#### Otomatik Güvenlik Testleri
```python
# Test senaryoları
SECURITY_TESTS = [
    'sql_injection_tests',
    'xss_vulnerability_tests',
    'csrf_protection_tests',
    'authentication_bypass_tests',
    'file_upload_security_tests',
    'session_security_tests',
    'input_validation_tests'
]

def run_security_tests():
    for test in SECURITY_TESTS:
        result = execute_test(test)
        log_test_result(test, result)
```

#### Güvenlik Taraması
- OWASP ZAP entegrasyonu
- Sqlmap taraması
- Nikto web scanner
- Nessus vulnerability scanner

### 2. Güvenlik Metrikleri

```python
SECURITY_METRICS = {
    'blocked_attacks_per_day': 0,
    'failed_login_attempts': 0,
    'successful_logins': 0,
    'file_uploads_blocked': 0,
    'rate_limit_violations': 0,
    'security_incidents': 0,
    'patch_compliance_rate': 100,
    'vulnerability_count': 0
}
```

## Olay Müdahale Prosedürleri

### 1. Güvenlik Olayı Sınıflandırması

#### Kritiklik Seviyeleri
- **Kritik**: Sistem güvenliğini ciddi tehdit eden olaylar
- **Yüksek**: Veri kaybı riski olan olaylar
- **Orta**: Hizmet kalitesini etkileyen olaylar
- **Düşük**: İzleme gerektiren normal dışı olaylar

#### Müdahale Süreleri
- Kritik: 15 dakika
- Yüksek: 1 saat
- Orta: 4 saat
- Düşük: 24 saat

### 2. Olay Müdahale Adımları

1. **Tespit ve Bildirme**
   - Otomatik alert sistemleri
   - Kullanıcı bildirimleri
   - Sistem monitoring

2. **İlk Değerlendirme**
   - Olay türü belirleme
   - Kritiklik seviyesi atama
   - Ekip bilgilendirme

3. **Kapsama ve Analiz**
   - Etkilenen sistemler
   - Veri kaybı analizi
   - Saldırı vektörü tespiti

4. **Müdahale ve İyileştirme**
   - Güvenlik açığını kapatma
   - Sistem güvenliğini sağlama
   - Veri kurtarma

5. **İyileşme ve Raporlama**
   - Sistem normalleştirme
   - Olay raporu hazırlama
   - Gelecek önlemler

## Güvenlik Eğitimi

### 1. Kullanıcı Eğitimi

#### Eğitim Konuları
- Güvenli şifre oluşturma
- Phishing saldırı tanıma
- Sosyal mühendislik farkındalığı
- Güvenli dosya paylaşımı
- Veri gizlilik ilkeleri

#### Eğitim Yöntemleri
- Online eğitim modülleri
- Simülasyon testleri
- Bilgilendirme e-postaları
- Güvenlik farkındalık kampanyaları

### 2. Yönetici Eğitimi

- Güvenlik politika yönetimi
- Olay müdahale prosedürleri
- Risk değerlendirmesi
- Mevzuat uyumluluğu
- Güvenlik teknolojileri

## Mevzuat Uyumluluğu

### 1. Ulusal Mevzuat

#### 6698 Sayılı KVKK
- Kişisel veri işleme ilkeleri
- Aydınlatma yükümlülüğü
- Veri güvenliği önlemleri
- İhlal bildirimi

#### 5651 Sayılı Kanun
- Log kayıt tutma
- Veri saklama süreleri
- Yetkili makam talepleri

### 2. Uluslararası Standartlar

#### ISO 27001
- Bilgi güvenliği yönetim sistemi
- Risk yönetimi
- Sürekli iyileştirme
- İç denetim

#### GDPR
- Avrupa veri koruma mevzuatı
- Veri işleme şartları
- Kullanıcı hakları
- Ceza prosedürleri

## Yedekleme ve Kurtarma

### 1. Güvenli Yedekleme

```bash
#!/bin/bash
# Güvenli yedekleme scripti

BACKUP_DIR="/secure/backups"
DATE=$(date +%Y%m%d_%H%M%S)
ENCRYPTION_KEY="/secure/keys/backup.key"

# Veritabanı yedeği
pg_dump deepsearch_db | gpg --cipher-algo AES256 --compress-algo 1 \
    --symmetric --output "$BACKUP_DIR/db_backup_$DATE.sql.gpg"

# Dosya yedeği
tar czf - /data/documents | gpg --cipher-algo AES256 --compress-algo 1 \
    --symmetric --output "$BACKUP_DIR/files_backup_$DATE.tar.gz.gpg"

# Eski yedekleri temizle (30 gün)
find "$BACKUP_DIR" -name "*.gpg" -mtime +30 -delete
```

### 2. Kurtarma Prosedürleri

#### RTO/RPO Hedefleri
- **RTO** (Recovery Time Objective): 4 saat
- **RPO** (Recovery Point Objective): 1 saat

#### Kurtarma Adımları
1. Yedek doğrulama
2. Sistem hazırlama
3. Veri geri yükleme
4. Sistem testi
5. Kullanıcı erişimi

## Güvenlik Kontrol Listesi

### Günlük Kontroller
- [ ] Güvenlik alert'lerini gözden geçir
- [ ] Başarısız login denemelerini kontrol et
- [ ] Rate limiting istatistiklerini incele
- [ ] Yeni dosya yüklemelerini gözden geçir
- [ ] Sistem kaynak kullanımını kontrol et

### Haftalık Kontroller
- [ ] Güvenlik log'larını analiz et
- [ ] Blacklist IP'leri gözden geçir
- [ ] Yedekleme durumunu kontrol et
- [ ] Güvenlik açığı taramalarını çalıştır
- [ ] Kullanıcı erişim haklarını gözden geçir

### Aylık Kontroller
- [ ] Güvenlik politikalarını güncelle
- [ ] Penetrasyon testleri yap
- [ ] Güvenlik eğitimlerini planla
- [ ] Olay müdahale prosedürlerini test et
- [ ] Mevzuat uyumluluğunu değerlendir

## İletişim Bilgileri

### Güvenlik Ekibi
- **Güvenlik Müdürü**: security@deepsearch.com
- **SOC Ekibi**: soc@deepsearch.com
- **Acil Durum**: +90 XXX XXX XX XX

### Olay Bildirimi
- **E-posta**: incident@deepsearch.com
- **Hotline**: +90 XXX XXX XX XX
- **Portal**: https://security.deepsearch.com/incident

---

**Güvenlik Kılavuzu Sürümü**: 1.0  
**Son Güncelleme**: 15 Ocak 2024  
**Onaylayan**: Güvenlik Müdürü  
**Geçerlilik**: 1 yıl