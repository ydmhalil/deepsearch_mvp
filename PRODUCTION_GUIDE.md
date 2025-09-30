# DeepSearch MVP - Production Deployment Guide

## Overview

DeepSearch MVP is a comprehensive offline document search and RAG (Retrieval-Augmented Generation) system designed for small-medium businesses (KOBİ). This production deployment guide covers installation, configuration, security, and maintenance.

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, Linux Ubuntu 18.04+, macOS 10.15+
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB free space minimum
- **CPU**: 2 cores minimum, 4 cores recommended

### Recommended Production Requirements
- **RAM**: 16GB+ for handling 100+ concurrent users
- **Storage**: 50GB+ SSD storage
- **CPU**: 8 cores for optimal performance
- **Network**: Stable internet for model downloads (initial setup)

## Quick Start Installation

### 1. Environment Setup

```powershell
# Windows PowerShell
git clone https://github.com/your-org/deepsearch-mvp.git
cd deepsearch-mvp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
# Linux/macOS
git clone https://github.com/your-org/deepsearch-mvp.git
cd deepsearch-mvp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Database Initialization

```powershell
python init_database.py
```

### 3. Document Processing

```powershell
# Process documents from a directory
python ingest.py --source .\documents --output .\data\chunks.jsonl

# Build search index
python embed_index.py build --chunks .\data\chunks.jsonl --index .\data\faiss.index --meta .\data\meta.pkl
```

### 4. Run Application

```powershell
# Development
python app.py

# Production (recommended)
pip install waitress
waitress-serve --host=0.0.0.0 --port=8080 app:app
```

## Production Configuration

### 1. Environment Variables

Create `.env` file in project root:

```env
# Security
SECRET_KEY=your-super-secret-production-key-change-this
FLASK_ENV=production
DEBUG=False

# Database
DATABASE_PATH=./config/production.db

# Performance
MAX_WORKERS=4
MEMORY_LIMIT_MB=2048
CACHE_SIZE=1000

# Security Settings
RATE_LIMIT_ENABLED=True
SESSION_TIMEOUT_HOURS=24
MAX_FILE_SIZE_MB=50

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/deepsearch.log
```

### 2. Production Settings

Update `app.py` for production:

```python
import os
from dotenv import load_dotenv

load_dotenv()

app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY'),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=int(os.environ.get('SESSION_TIMEOUT_HOURS', 24)))
)
```

## Security Configuration

### 1. SSL/TLS Setup

For production, always use HTTPS. Configure with nginx or use cloud services:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Firewall Configuration

```bash
# Ubuntu/Debian
sudo ufw allow 22/tcp
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp
sudo ufw enable

# Block direct access to application port
sudo ufw deny 8080
```

### 3. Security Headers

The application includes security middleware. Verify these headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

### 4. User Management

Create admin user:

```python
python -c "
from auth import user_manager
admin_user = user_manager.create_user('admin', 'your-secure-password', 'admin@company.com', 'admin')
print(f'Admin user created: {admin_user}')
"
```

## Database Management

### 1. Database Optimization

```python
# Run database optimization
python -c "
from database_optimizer import db_optimizer
db_optimizer.optimize_database()
print('Database optimization completed')
"
```

### 2. Backup Strategy

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR

# Backup database
cp ./config/users.db $BACKUP_DIR/users_$DATE.db

# Backup documents and indexes
tar -czf $BACKUP_DIR/data_$DATE.tar.gz ./data/

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### 3. Data Cleanup

```python
# Automated cleanup script
python -c "
from database_optimizer import db_optimizer
deleted_rows = db_optimizer.cleanup_old_data(days_to_keep=90)
print(f'Cleaned up {deleted_rows} old records')
"
```

## Performance Monitoring

### 1. System Health Monitoring

Access performance dashboard at: `/admin/performance`

Monitor these metrics:
- **Search Performance**: < 200ms average response time
- **Memory Usage**: < 80% system memory
- **Database Performance**: < 100ms query time
- **Cache Hit Rate**: > 60% for optimal performance

### 2. Performance Optimization

```python
# Run system optimization
python -c "
from resource_manager import optimize_system_performance
optimize_system_performance()
print('System optimization completed')
"
```

### 3. Automated Monitoring

Create monitoring script:

```python
#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime

def health_check():
    try:
        # Check application health
        response = requests.get('http://localhost:8080/health', timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Application healthy at {datetime.now()}")
            return True
        else:
            print(f"❌ Application unhealthy: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == '__main__':
    while True:
        health_check()
        time.sleep(300)  # Check every 5 minutes
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```python
   # Clear caches
   python -c "
   from faiss_optimizer import faiss_optimizer
   faiss_optimizer.clear_cache()
   print('Caches cleared')
   "
   ```

2. **Slow Search Performance**
   ```python
   # Rebuild index with optimization
   python embed_index.py build --chunks ./data/chunks.jsonl --index ./data/faiss.index --meta ./data/meta.pkl
   ```

3. **Database Lock Issues**
   ```python
   # Check database connections
   python -c "
   from database_optimizer import db_optimizer
   stats = db_optimizer.get_performance_stats()
   print(f'Connection pool size: {stats[\"connection_pool_size\"]}')
   "
   ```

### Log Analysis

Check application logs:

```bash
# View recent logs
tail -f ./logs/deepsearch.log

# Search for errors
grep "ERROR" ./logs/deepsearch.log | tail -20

# Monitor performance issues
grep "Slow query" ./logs/deepsearch.log
```

## Maintenance Schedule

### Daily
- [ ] Check system health dashboard
- [ ] Review security events
- [ ] Monitor disk space
- [ ] Backup database

### Weekly
- [ ] Run database optimization
- [ ] Clear old logs (>30 days)
- [ ] Update system packages
- [ ] Review performance metrics

### Monthly
- [ ] Full system backup
- [ ] Security assessment
- [ ] Performance benchmarking
- [ ] Update documentation

## Scaling Guidelines

### Horizontal Scaling

For handling more users, deploy multiple instances:

```yaml
# docker-compose.yml
version: '3.8'
services:
  deepsearch-1:
    build: .
    ports:
      - "8081:8080"
    volumes:
      - ./data:/app/data
      
  deepsearch-2:
    build: .
    ports:
      - "8082:8080"
    volumes:
      - ./data:/app/data
      
  nginx:
    image: nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### Vertical Scaling

For better performance on single instance:

1. **Increase memory allocation**:
   ```env
   MEMORY_LIMIT_MB=4096
   CACHE_SIZE=2000
   ```

2. **Optimize database**:
   ```env
   DB_POOL_SIZE=20
   DB_TIMEOUT=30
   ```

3. **Tune FAISS parameters**:
   ```env
   FAISS_CACHE_SIZE=1500
   SEARCH_BATCH_SIZE=100
   ```

## Security Best Practices

### 1. Regular Security Updates

```bash
# Update dependencies
pip list --outdated
pip install -r requirements.txt --upgrade

# Security audit
pip-audit
```

### 2. Access Control

- Use strong passwords (minimum 12 characters)
- Enable two-factor authentication (if implemented)
- Regular access review
- Principle of least privilege

### 3. Monitoring

- Enable security logging
- Monitor failed login attempts
- Review access patterns
- Set up alerting for suspicious activity

### 4. Data Protection

- Encrypt sensitive data at rest
- Secure backup storage
- Regular security testing
- Document classification

## API Documentation

### Authentication Endpoints

```http
POST /login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "secure_password"
}
```

### Search API

```http
POST /search
Content-Type: application/json
Authorization: Bearer <session_token>

{
  "query": "search terms",
  "filters": {
    "file_types": ["pdf", "docx"],
    "date_from": "2024-01-01",
    "date_to": "2024-12-31"
  },
  "top_k": 10
}
```

### Document Upload

```http
POST /upload
Content-Type: multipart/form-data
Authorization: Bearer <session_token>

Form data:
- file: document file
- auto_index: true/false
```

## Support and Contact

For production support:

- **Email**: support@deepsearch.com
- **Documentation**: https://docs.deepsearch.com
- **Issue Tracker**: https://github.com/your-org/deepsearch-mvp/issues
- **Emergency Contact**: +1-XXX-XXX-XXXX

## License and Compliance

This software is licensed under [MIT License](LICENSE). For enterprise licensing and compliance requirements, contact our sales team.

### Data Privacy

- GDPR compliant data handling
- Data retention policies
- User data export/deletion
- Privacy by design principles

---

**Version**: 1.0.0  
**Last Updated**: $(date)  
**Deployment Guide Version**: 1.0