"""
File upload manager for DeepSearch
Handles file uploads, validation, and auto-indexing
"""

import os
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
from init_database import get_db_connection
import subprocess

# Import document insights for auto-analysis
try:
    from document_insights import insights_engine
    INSIGHTS_AVAILABLE = True
except ImportError:
    INSIGHTS_AVAILABLE = False
import json

class FileUploadManager:
    """Manages file uploads and processing"""
    
    def __init__(self, upload_folder='./data/uploads'):
        self.upload_folder = os.path.abspath(upload_folder)
        self.allowed_extensions = {
            'txt', 'pdf', 'docx', 'xlsx', 'pptx'
        }
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_folder, exist_ok=True)
        
    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def validate_file_content(self, filepath):
        """Validate file content using basic file signature checking"""
        try:
            # Read first few bytes to check file signatures
            with open(filepath, 'rb') as f:
                header = f.read(8)
            
            # File signatures for security validation
            file_signatures = {
                b'%PDF': 'pdf',
                b'PK\x03\x04': 'office',  # ZIP-based formats (DOCX, XLSX, PPTX)
                b'PK\x05\x06': 'office',  # Empty ZIP
                b'PK\x07\x08': 'office',  # Spanned ZIP
            }
            
            # Check for known signatures
            for signature, file_type in file_signatures.items():
                if header.startswith(signature):
                    return True, f"Dosya türü geçerli: {file_type}"
            
            # Check if it's a text file (should contain mostly printable characters)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read(1024)  # Read first 1KB
                # If we can read it as text, it's probably a text file
                return True, "Text dosyası geçerli"
            except UnicodeDecodeError:
                pass
            
            # If no signature matches and it's not text, it might be suspicious
            filename = os.path.basename(filepath)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            if ext in self.allowed_extensions:
                # Trust the extension for now, but log for monitoring
                print(f"Warning: File {filename} passed extension check but signature validation unclear")
                return True, f"Extension-based validation: {ext}"
            
            return False, "Dosya içeriği doğrulanamadı"
            
        except Exception as e:
            print(f"File validation error: {e}")
            # In case of error, allow file but log the issue
            return True, "Validation error - file allowed with warning"
    
    def get_file_hash(self, filepath):
        """Generate MD5 hash for file (to detect duplicates)"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def save_uploaded_file(self, file, user_id):
        """Save uploaded file and record in database"""
        try:
            if not file or file.filename == '':
                return {'success': False, 'message': 'Dosya seçilmedi'}
            
            if not self.allowed_file(file.filename):
                return {'success': False, 'message': f'Desteklenmeyen dosya türü. İzin verilen türler: {", ".join(self.allowed_extensions)}'}
            
            # Secure filename
            filename = secure_filename(file.filename)
            if not filename:
                return {'success': False, 'message': 'Geçersiz dosya adı'}
            
            # Add timestamp to avoid conflicts
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(self.upload_folder, filename)
            
            # Save file
            file.save(filepath)
            
            # Validate file content (security check)
            content_valid, content_message = self.validate_file_content(filepath)
            if not content_valid:
                os.remove(filepath)
                return {'success': False, 'message': content_message}
            
            # Check file size
            file_size = os.path.getsize(filepath)
            if file_size > self.max_file_size:
                os.remove(filepath)
                return {'success': False, 'message': f'Dosya boyutu çok büyük (max {self.max_file_size//1024//1024}MB)'}
            
            # Generate file hash
            file_hash = self.get_file_hash(filepath)
            
            # Check for duplicates
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT filename FROM documents WHERE file_hash = ?', (file_hash,))
            if cursor.fetchone():
                os.remove(filepath)
                conn.close()
                return {'success': False, 'message': 'Bu dosya daha önce yüklenmiş'}
            
            # Record in database
            cursor.execute('''
                INSERT INTO documents (filename, file_path, file_size, upload_date, uploaded_by, file_hash, is_indexed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                file.filename,  # Original filename
                filepath,       # Full path
                file_size,
                datetime.now(),
                user_id,
                file_hash,
                False  # Not indexed yet
            ))
            
            document_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Auto-analyze document content if insights engine available
            if INSIGHTS_AVAILABLE:
                try:
                    # Get file extension
                    file_ext = os.path.splitext(filename)[1].lower()
                    
                    # Extract text content for analysis
                    if file_ext == '.txt':
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                    else:
                        # For other file types, extract text using utils
                        from utils import extract_text
                        content = extract_text(filepath)
                    
                    # Perform document analysis
                    if content and len(content.strip()) > 50:  # Only analyze if substantial content
                        analysis = insights_engine.analyze_document_content(filepath, content)
                        insights_engine.save_analysis_to_db(analysis)
                        print(f"✨ Document analysis completed for: {filename}")
                        
                except Exception as e:
                    print(f"⚠️ Document analysis failed for {filename}: {str(e)}")
            
            return {
                'success': True, 
                'message': 'Dosya başarıyla yüklendi',
                'document_id': document_id,
                'filename': filename,
                'filepath': filepath,
                'file_size': file_size
            }
            
        except Exception as e:
            # Clean up file if database operation fails
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
            return {'success': False, 'message': f'Dosya yükleme hatası: {str(e)}'}
    
    def get_uploaded_files(self, user_id=None, include_all=False):
        """Get list of uploaded files"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if include_all:
                # Admin can see all files
                cursor.execute('''
                    SELECT d.*, u.username as uploader_name 
                    FROM documents d 
                    LEFT JOIN users u ON d.uploaded_by = u.id 
                    ORDER BY d.upload_date DESC
                ''')
            elif user_id:
                # User can see only their files
                cursor.execute('''
                    SELECT d.*, u.username as uploader_name 
                    FROM documents d 
                    LEFT JOIN users u ON d.uploaded_by = u.id 
                    WHERE d.uploaded_by = ? 
                    ORDER BY d.upload_date DESC
                ''', (user_id,))
            else:
                return []
            
            files = cursor.fetchall()
            conn.close()
            
            return [dict(file) for file in files]
            
        except Exception as e:
            print(f"Error getting uploaded files: {e}")
            return []
    
    def delete_file(self, document_id, user_id, is_admin=False):
        """Delete uploaded file"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get file info
            if is_admin:
                cursor.execute('SELECT file_path, filename FROM documents WHERE id = ?', (document_id,))
            else:
                cursor.execute('SELECT file_path, filename FROM documents WHERE id = ? AND uploaded_by = ?', 
                             (document_id, user_id))
            
            file_info = cursor.fetchone()
            if not file_info:
                conn.close()
                return {'success': False, 'message': 'Dosya bulunamadı veya silme yetkiniz yok'}
            
            filepath = file_info['file_path']
            
            # Delete from database
            cursor.execute('DELETE FROM documents WHERE id = ?', (document_id,))
            conn.commit()
            conn.close()
            
            # Delete physical file
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return {'success': True, 'message': 'Dosya başarıyla silindi'}
            
        except Exception as e:
            return {'success': False, 'message': f'Dosya silme hatası: {str(e)}'}
    
    def process_file_for_indexing(self, document_id):
        """Process uploaded file for indexing"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT file_path, filename FROM documents WHERE id = ?', (document_id,))
            file_info = cursor.fetchone()
            
            if not file_info:
                return {'success': False, 'message': 'Dosya bulunamadı'}
            
            filepath = file_info['file_path']
            
            # Create a temporary directory for this file's processing
            temp_dir = os.path.join(os.path.dirname(filepath), 'temp_processing')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Copy file to temp directory for processing
            import shutil
            temp_filepath = os.path.join(temp_dir, os.path.basename(filepath))
            shutil.copy2(filepath, temp_filepath)
            
            # Process file with ingest.py
            chunks_output = os.path.join('./data', f'chunks_{document_id}.jsonl')
            
            try:
                cmd = [
                    'python', 'ingest.py',
                    '--source', temp_dir,
                    '--output', chunks_output
                ]
                
                print(f"Running indexing command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
                
                if result.returncode == 0:
                    # Check if chunks were created
                    if os.path.exists(chunks_output) and os.path.getsize(chunks_output) > 0:
                        # Now create embeddings
                        index_output = os.path.join('./data', f'index_{document_id}.index')
                        meta_output = os.path.join('./data', f'meta_{document_id}.pkl')
                        
                        embed_cmd = [
                            'python', 'embed_index.py', 'build',
                            '--chunks', chunks_output,
                            '--index', index_output,
                            '--meta', meta_output
                        ]
                        
                        print(f"Running embedding command: {' '.join(embed_cmd)}")
                        embed_result = subprocess.run(embed_cmd, capture_output=True, text=True, cwd=os.getcwd())
                        
                        if embed_result.returncode == 0:
                            # Update database - mark as indexed
                            cursor.execute('''
                                UPDATE documents 
                                SET is_indexed = ?, indexed_date = ?, 
                                    chunks_file = ?, index_file = ?, meta_file = ?
                                WHERE id = ?
                            ''', (True, datetime.now(), chunks_output, index_output, meta_output, document_id))
                            conn.commit()
                            
                            # Clean up temp directory
                            shutil.rmtree(temp_dir, ignore_errors=True)
                            
                            conn.close()
                            return {'success': True, 'message': 'Dosya başarıyla indexlendi'}
                        else:
                            conn.close()
                            return {'success': False, 'message': f'Embedding hatası: {embed_result.stderr}'}
                    else:
                        conn.close()
                        return {'success': False, 'message': 'Chunk oluşturulamadı - desteklenmeyen dosya formatı olabilir'}
                else:
                    conn.close()
                    return {'success': False, 'message': f'Ingest hatası: {result.stderr}'}
                    
            finally:
                # Always clean up temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            return {'success': False, 'message': f'Indexleme hatası: {str(e)}'}
    
    def get_upload_stats(self):
        """Get upload statistics"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Total files
            cursor.execute('SELECT COUNT(*) as total FROM documents')
            total_files = cursor.fetchone()['total']
            
            # Indexed files
            cursor.execute('SELECT COUNT(*) as indexed FROM documents WHERE is_indexed = 1')
            indexed_files = cursor.fetchone()['indexed']
            
            # Total size
            cursor.execute('SELECT SUM(file_size) as total_size FROM documents')
            total_size = cursor.fetchone()['total_size'] or 0
            
            # Files by type
            cursor.execute('''
                SELECT 
                    CASE 
                        WHEN filename LIKE '%.pdf' THEN 'PDF'
                        WHEN filename LIKE '%.docx' THEN 'DOCX'
                        WHEN filename LIKE '%.xlsx' THEN 'XLSX'
                        WHEN filename LIKE '%.pptx' THEN 'PPTX'
                        WHEN filename LIKE '%.txt' THEN 'TXT'
                        ELSE 'OTHER'
                    END as file_type,
                    COUNT(*) as count
                FROM documents 
                GROUP BY file_type
            ''')
            files_by_type = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_files': total_files,
                'indexed_files': indexed_files,
                'pending_files': total_files - indexed_files,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'files_by_type': files_by_type
            }
            
        except Exception as e:
            print(f"Error getting upload stats: {e}")
            return {
                'total_files': 0,
                'indexed_files': 0,
                'pending_files': 0,
                'total_size_mb': 0,
                'files_by_type': {}
            }

# Global upload manager instance
upload_manager = FileUploadManager()