# Production Deployment Quick Guide

## 🚀 DeepSearch MVP - Quick Production Deployment

### Prerequisites
- Windows 10/11 or Linux/macOS
- Python 3.8+ installed
- 8GB+ RAM recommended
- 10GB+ free disk space

### 1. Download & Setup
```powershell
# Clone or download the project
git clone https://github.com/your-org/deepsearch-mvp.git
cd deepsearch-mvp

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```powershell
# Install all requirements
pip install -r requirements.txt

# If you get errors, install one by one:
pip install Flask==2.3.2
pip install waitress==3.0.2
pip install sentence-transformers
pip install faiss-cpu==1.11.0
pip install pandas==2.2.2
pip install matplotlib
pip install seaborn
pip install reportlab
pip install bleach
pip install python-dotenv
pip install Flask-Session
```

### 3. Initialize System
```powershell
# Initialize database
python init_database.py

# Process example documents (optional)
python ingest.py --source .\example_docs --output .\data\chunks.jsonl

# Build search index
python embed_index.py build --chunks .\data\chunks.jsonl --index .\data\faiss.index --meta .\data\meta.pkl
```

### 4. Run System Check
```powershell
# Quick system check
python simple_check.py
```

### 5. Start the Application

#### Development Mode (for testing)
```powershell
python app.py
# Access: http://localhost:5000
```

#### Production Mode (recommended)
```powershell
# Method 1: Using waitress (recommended)
python -m waitress --host=0.0.0.0 --port=8080 app:app

# Method 2: Using gunicorn (Linux/macOS only)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

### 6. Access the System
- **URL**: http://localhost:8080 (production) or http://localhost:5000 (development)
- **Default Login**: 
  - Username: `admin`
  - Password: `admin`
- **Change Password**: Go to Settings after first login

### 7. Upload Documents
1. Login to the system
2. Click "Dosya Yükle" (Upload File)
3. Select PDF, DOCX, XLSX, or TXT files
4. Wait for processing to complete
5. Use the search feature

### 8. Security Configuration
```powershell
# Set production environment variables
$env:FLASK_ENV="production"
$env:SECRET_KEY="your-very-secure-secret-key-here"
$env:ADMIN_PASSWORD="your-admin-password"
```

### 9. Monitoring & Maintenance
- **Admin Dashboard**: http://localhost:8080/kobi/dashboard
- **Security Dashboard**: http://localhost:8080/security/dashboard
- **Performance Monitoring**: http://localhost:8080/admin/performance

### 10. Troubleshooting

#### Common Issues:
1. **Port already in use**: Change port number in commands
2. **Permission errors**: Run as administrator or adjust file permissions
3. **Memory issues**: Increase system memory or reduce concurrent users
4. **Encoding errors**: Set `$env:PYTHONIOENCODING="utf-8"`

#### Log Files:
- Application logs are displayed in the terminal
- Check the terminal output for errors and warnings

### 11. Production Hardening
1. Change default admin password immediately
2. Configure firewall to allow only necessary ports
3. Set up HTTPS with SSL certificates
4. Regular database backups
5. Monitor system resources

### 12. Backup & Recovery
```powershell
# Backup database
copy config\users.db config\users_backup.db

# Backup search index
copy data\*.* data_backup\

# Backup uploaded files
copy uploads\*.* uploads_backup\
```

### Support
- **Documentation**: See `PRODUCTION_GUIDE.md` for detailed deployment
- **User Manual**: See `USER_MANUAL.md` for usage instructions
- **API Documentation**: See `API_DOCUMENTATION.md` for API reference
- **Security Guide**: See `SECURITY_GUIDE.md` for security configuration

### System Requirements
- **Minimum**: 4GB RAM, 2 CPU cores, 10GB storage
- **Recommended**: 8GB+ RAM, 4+ CPU cores, 20GB+ SSD storage
- **Enterprise**: 16GB+ RAM, 8+ CPU cores, 50GB+ storage

---

**Status**: Production Ready ✅  
**Version**: 1.0.0  
**Last Updated**: January 15, 2024