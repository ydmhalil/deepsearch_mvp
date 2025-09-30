"""
Security Hardening Module
Comprehensive security implementations for production environment
"""

import re
import html
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sqlite3
from flask import request, session, g
import bleach
from werkzeug.security import check_password_hash
import os

class SecurityManager:
    def __init__(self, db_path='config/users.db'):
        self.db_path = db_path
        
        # Security settings
        self.max_login_attempts = 5
        self.lockout_duration = 30  # minutes
        self.session_timeout = 60  # minutes
        self.password_history_count = 5
        
        # XSS Protection patterns
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
            r'<link[^>]*rel\s*=\s*["\']stylesheet["\'][^>]*>',
            r'<style[^>]*>.*?</style>',
            r'expression\s*\(',
            r'@import',
            r'vbscript:',
            r'data:text/html'
        ]
        
        # SQL Injection patterns
        self.sql_injection_patterns = [
            r"(?i)(union\s+select|select\s+.*\s+from|insert\s+into|update\s+.*\s+set|delete\s+from)",
            r"(?i)(drop\s+table|create\s+table|alter\s+table|truncate\s+table)",
            r"(?i)(exec\s*\(|execute\s*\(|sp_executesql)",
            r"(?i)(waitfor\s+delay|benchmark\s*\(|sleep\s*\()",
            r"[';\"]\s*;\s*[a-zA-Z]",
            r"--\s*[a-zA-Z]",
            r"/\*.*\*/",
            r"(?i)(information_schema|sys\.tables|mysql\.user)",
            r"(?i)(char\s*\(|ascii\s*\(|substring\s*\(|mid\s*\()",
            r"['\"]?\s*(or|and)\s+['\"]?1['\"]?\s*=['\"]?1"
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            r'\.\./+',
            r'\.\.\\+',
            r'%2e%2e[/\\]',
            r'%252e%252e[/\\]',
            r'\.%2e[/\\]',
            r'%2e\.[/\\]',
            r'%c0%af',
            r'%c1%9c'
        ]
        
        # File upload security
        self.allowed_file_types = {
            '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
            '.ppt', '.pptx', '.rtf', '.odt', '.ods', '.odp'
        }
        
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        
        # Rate limiting
        self.rate_limits = {
            'login': {'count': 5, 'window': 300},  # 5 attempts per 5 minutes
            'search': {'count': 100, 'window': 60},  # 100 searches per minute
            'upload': {'count': 10, 'window': 300},  # 10 uploads per 5 minutes
            'api': {'count': 1000, 'window': 3600}  # 1000 API calls per hour
        }
        
    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
        
    def initialize_security_tables(self):
        """Initialize security-related database tables"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Login attempts tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    username TEXT,
                    attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT FALSE,
                    user_agent TEXT
                )
            ''')
            
            # Security events log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    ip_address TEXT,
                    user_id INTEGER,
                    details TEXT,
                    severity TEXT DEFAULT 'medium',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Session management
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Rate limiting
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    request_count INTEGER DEFAULT 1,
                    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Password history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS password_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
            print("✅ Security tables initialized successfully!")
            
        except Exception as e:
            print(f"❌ Security tables initialization failed: {e}")
            conn.rollback()
        finally:
            conn.close()
            
    def validate_input(self, input_data: str, input_type: str = 'general') -> Dict[str, Any]:
        """
        Comprehensive input validation and sanitization
        """
        result = {
            'is_valid': True,
            'sanitized': input_data,
            'threats_detected': [],
            'severity': 'low'
        }
        
        if not input_data:
            return result
            
        original_input = input_data
        
        # XSS Detection and Prevention
        xss_detected = False
        for pattern in self.xss_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                xss_detected = True
                result['threats_detected'].append(f'XSS pattern detected: {pattern}')
                
        if xss_detected:
            result['severity'] = 'high'
            # Sanitize with bleach
            result['sanitized'] = bleach.clean(
                input_data,
                tags=['p', 'br', 'strong', 'em', 'u'],
                attributes={},
                strip=True
            )
            
        # SQL Injection Detection
        sql_injection_detected = False
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                sql_injection_detected = True
                result['threats_detected'].append(f'SQL injection pattern detected: {pattern}')
                
        if sql_injection_detected:
            result['is_valid'] = False
            result['severity'] = 'critical'
            
        # Path Traversal Detection
        path_traversal_detected = False
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                path_traversal_detected = True
                result['threats_detected'].append(f'Path traversal pattern detected: {pattern}')
                
        if path_traversal_detected:
            result['is_valid'] = False
            result['severity'] = 'high'
            
        # Additional sanitization based on input type
        if input_type == 'search_query':
            # Remove potentially dangerous characters for search
            result['sanitized'] = re.sub(r'[<>"\';\\]', '', result['sanitized'])
            
        elif input_type == 'filename':
            # Secure filename
            result['sanitized'] = re.sub(r'[^a-zA-Z0-9._-]', '_', result['sanitized'])
            
        elif input_type == 'html':
            # Allow only safe HTML tags
            result['sanitized'] = bleach.clean(
                result['sanitized'],
                tags=['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li'],
                attributes={},
                strip=True
            )
            
        # Log security events if threats detected
        if result['threats_detected']:
            self.log_security_event(
                'input_validation',
                details=f"Threats in {input_type}: {', '.join(result['threats_detected'])}",
                severity=result['severity']
            )
            
        return result
        
    def check_rate_limit(self, endpoint: str, ip_address: str = None) -> Dict[str, Any]:
        """
        Check and enforce rate limiting
        """
        if not ip_address:
            ip_address = request.remote_addr
            
        if endpoint not in self.rate_limits:
            return {'allowed': True, 'remaining': 999}
            
        limit_config = self.rate_limits[endpoint]
        max_requests = limit_config['count']
        window_seconds = limit_config['window']
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Clean old entries
            cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
            cursor.execute('''
                DELETE FROM rate_limits 
                WHERE ip_address = ? AND endpoint = ? AND window_start < ?
            ''', (ip_address, endpoint, cutoff_time))
            
            # Check current count
            cursor.execute('''
                SELECT SUM(request_count) as total_requests
                FROM rate_limits 
                WHERE ip_address = ? AND endpoint = ? AND window_start >= ?
            ''', (ip_address, endpoint, cutoff_time))
            
            result = cursor.fetchone()
            current_requests = result['total_requests'] if result['total_requests'] else 0
            
            if current_requests >= max_requests:
                conn.close()
                self.log_security_event(
                    'rate_limit_exceeded',
                    details=f"Rate limit exceeded for {endpoint}: {current_requests}/{max_requests}",
                    severity='medium'
                )
                return {
                    'allowed': False,
                    'remaining': 0,
                    'reset_time': window_seconds,
                    'message': f'Rate limit exceeded. Try again in {window_seconds} seconds.'
                }
                
            # Update or insert rate limit record
            cursor.execute('''
                INSERT OR REPLACE INTO rate_limits 
                (ip_address, endpoint, request_count, window_start)
                VALUES (?, ?, 
                    COALESCE((SELECT request_count FROM rate_limits 
                             WHERE ip_address = ? AND endpoint = ? AND window_start >= ?), 0) + 1,
                    CURRENT_TIMESTAMP)
            ''', (ip_address, endpoint, ip_address, endpoint, cutoff_time))
            
            conn.commit()
            conn.close()
            
            return {
                'allowed': True,
                'remaining': max_requests - current_requests - 1
            }
            
        except Exception as e:
            conn.close()
            print(f"Rate limit check error: {e}")
            return {'allowed': True, 'remaining': 999}  # Allow on error
            
    def validate_file_upload(self, file, filename: str) -> Dict[str, Any]:
        """
        Comprehensive file upload security validation
        """
        result = {
            'is_valid': True,
            'sanitized_filename': filename,
            'threats_detected': [],
            'file_info': {}
        }
        
        # Validate filename
        filename_validation = self.validate_input(filename, 'filename')
        result['sanitized_filename'] = filename_validation['sanitized']
        result['threats_detected'].extend(filename_validation['threats_detected'])
        
        # Check file extension
        file_ext = os.path.splitext(filename.lower())[1]
        if file_ext not in self.allowed_file_types:
            result['is_valid'] = False
            result['threats_detected'].append(f'Forbidden file type: {file_ext}')
            
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > self.max_file_size:
            result['is_valid'] = False
            result['threats_detected'].append(f'File too large: {file_size} bytes')
            
        result['file_info'] = {
            'size': file_size,
            'extension': file_ext,
            'original_filename': filename
        }
        
        # Basic file content validation
        try:
            # Read first 1KB to check for malicious content
            content_sample = file.read(1024)
            file.seek(0)  # Reset
            
            # Check for executable signatures
            executable_signatures = [
                b'MZ',  # Windows PE
                b'\x7fELF',  # Linux ELF
                b'\xfe\xed\xfa',  # Mach-O
                b'PK\x03\x04',  # ZIP (check more carefully)
            ]
            
            for sig in executable_signatures:
                if content_sample.startswith(sig):
                    if file_ext not in ['.zip', '.docx', '.xlsx', '.pptx']:  # These are ZIP-based
                        result['is_valid'] = False
                        result['threats_detected'].append('Potential executable file detected')
                        
        except Exception as e:
            result['threats_detected'].append(f'File content validation error: {e}')
            
        # Log security events
        if result['threats_detected']:
            self.log_security_event(
                'file_upload_validation',
                details=f"File upload threats: {', '.join(result['threats_detected'])}",
                severity='high' if not result['is_valid'] else 'medium'
            )
            
        return result
        
    def track_login_attempt(self, username: str, success: bool, ip_address: str = None) -> bool:
        """
        Track login attempts and enforce lockout policy
        Returns True if login should be allowed, False if account is locked
        """
        if not ip_address:
            ip_address = request.remote_addr
            
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Log this attempt
            cursor.execute('''
                INSERT INTO login_attempts (ip_address, username, success, user_agent)
                VALUES (?, ?, ?, ?)
            ''', (ip_address, username, success, request.headers.get('User-Agent', '')))
            
            if success:
                # Clear failed attempts on successful login
                cursor.execute('''
                    DELETE FROM login_attempts 
                    WHERE username = ? AND success = FALSE
                ''', (username,))
                conn.commit()
                conn.close()
                return True
                
            # Check failed attempts in lockout window
            lockout_start = datetime.now() - timedelta(minutes=self.lockout_duration)
            cursor.execute('''
                SELECT COUNT(*) as failed_count
                FROM login_attempts 
                WHERE username = ? AND success = FALSE AND attempt_time > ?
            ''', (username, lockout_start))
            
            failed_count = cursor.fetchone()['failed_count']
            
            if failed_count >= self.max_login_attempts:
                # Account is locked
                self.log_security_event(
                    'account_lockout',
                    details=f"Account locked due to {failed_count} failed attempts",
                    severity='high'
                )
                conn.commit()
                conn.close()
                return False
                
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            conn.close()
            print(f"Login attempt tracking error: {e}")
            return True  # Allow on error
            
    def create_secure_session(self, user_id: int) -> str:
        """
        Create a secure session with proper tracking
        """
        session_token = secrets.token_urlsafe(32)
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        expires_at = datetime.now() + timedelta(minutes=self.session_timeout)
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Invalidate old sessions for this user
            cursor.execute('''
                UPDATE user_sessions 
                SET is_active = FALSE 
                WHERE user_id = ? AND is_active = TRUE
            ''', (user_id,))
            
            # Create new session
            cursor.execute('''
                INSERT INTO user_sessions 
                (user_id, session_token, ip_address, user_agent, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, session_token, ip_address, user_agent, expires_at))
            
            conn.commit()
            conn.close()
            
            return session_token
            
        except Exception as e:
            conn.close()
            print(f"Session creation error: {e}")
            return None
            
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate session and update activity
        """
        if not session_token:
            return None
            
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT us.*, u.username, u.role
                FROM user_sessions us
                JOIN users u ON us.user_id = u.id
                WHERE us.session_token = ? 
                AND us.is_active = TRUE 
                AND us.expires_at > CURRENT_TIMESTAMP
            ''', (session_token,))
            
            session_data = cursor.fetchone()
            
            if not session_data:
                conn.close()
                return None
                
            # Update last activity
            cursor.execute('''
                UPDATE user_sessions 
                SET last_activity = CURRENT_TIMESTAMP 
                WHERE session_token = ?
            ''', (session_token,))
            
            conn.commit()
            conn.close()
            
            return dict(session_data)
            
        except Exception as e:
            conn.close()
            print(f"Session validation error: {e}")
            return None
            
    def log_security_event(self, event_type: str, details: str = '', severity: str = 'medium'):
        """
        Log security events for monitoring and analysis
        """
        ip_address = getattr(request, 'remote_addr', 'unknown')
        user_id = getattr(g, 'current_user_id', None)
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO security_events (event_type, ip_address, user_id, details, severity)
                VALUES (?, ?, ?, ?, ?)
            ''', (event_type, ip_address, user_id, details, severity))
            
            conn.commit()
            
            # Print security events in development
            print(f"🔒 Security Event [{severity.upper()}]: {event_type} - {details}")
            
        except Exception as e:
            print(f"Security event logging error: {e}")
        finally:
            conn.close()
            
    def get_security_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get security summary for monitoring dashboard
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            since_date = datetime.now() - timedelta(days=days)
            
            # Security events summary
            cursor.execute('''
                SELECT event_type, severity, COUNT(*) as count
                FROM security_events 
                WHERE timestamp > ?
                GROUP BY event_type, severity
                ORDER BY count DESC
            ''', (since_date,))
            
            events = cursor.fetchall()
            
            # Login attempts summary
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN success = TRUE THEN 1 ELSE 0 END) as successful_logins,
                    COUNT(DISTINCT ip_address) as unique_ips
                FROM login_attempts 
                WHERE attempt_time > ?
            ''', (since_date,))
            
            login_stats = cursor.fetchone()
            
            # Active sessions
            cursor.execute('''
                SELECT COUNT(*) as active_sessions
                FROM user_sessions 
                WHERE is_active = TRUE AND expires_at > CURRENT_TIMESTAMP
            ''')
            
            session_stats = cursor.fetchone()
            
            # Get events by severity
            cursor.execute('''
                SELECT * FROM security_events 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', (since_date,))
            
            all_events = [dict(row) for row in cursor.fetchall()]
            
            # Separate by severity
            high_severity_events = [e for e in all_events if e['severity'] == 'high']
            medium_severity_events = [e for e in all_events if e['severity'] == 'medium']
            low_severity_events = [e for e in all_events if e['severity'] == 'low']
            
            # Get blocked IPs
            cursor.execute('''
                SELECT ip_address, COUNT(*) as attempts
                FROM security_events 
                WHERE event_type LIKE '%blocked%' AND timestamp >= ?
                GROUP BY ip_address
                ORDER BY attempts DESC
                LIMIT 10
            ''', (since_date,))
            
            blocked_ips = [dict(row) for row in cursor.fetchall()]
            
            # Get top blocked IPs
            cursor.execute('''
                SELECT ip_address, COUNT(*) as attempts
                FROM security_events 
                WHERE event_type IN ('login_failed', 'rate_limit_exceeded') AND timestamp >= ?
                GROUP BY ip_address
                ORDER BY attempts DESC
                LIMIT 5
            ''', (since_date,))
            
            top_blocked_ips = [dict(row) for row in cursor.fetchall()]
            
            # Get failed login attempts count
            cursor.execute('''
                SELECT COUNT(*) as failed_attempts
                FROM security_events 
                WHERE event_type = 'login_failed' AND timestamp >= ?
            ''', (since_date,))
            
            failed_login_result = cursor.fetchone()
            failed_login_attempts = failed_login_result['failed_attempts'] if failed_login_result else 0
            
            # Get active rate limits count
            cursor.execute('''
                SELECT COUNT(DISTINCT ip_address) as active_limits
                FROM rate_limits 
                WHERE window_start >= ?
            ''', (since_date,))
            
            rate_limit_result = cursor.fetchone()
            active_rate_limits = rate_limit_result['active_limits'] if rate_limit_result else 0
            
            conn.close()
            
            return {
                'security_events': [dict(event) for event in events],
                'recent_events': all_events[:20],  # Last 20 events
                'high_severity_events': high_severity_events,
                'medium_severity_events': medium_severity_events,
                'low_severity_events': low_severity_events,
                'login_statistics': dict(login_stats),
                'active_sessions': session_stats['active_sessions'],
                'blocked_ips': blocked_ips,
                'top_blocked_ips': top_blocked_ips,
                'failed_login_attempts': failed_login_attempts,
                'active_rate_limits': active_rate_limits,
                'total_events': len(all_events),
                'summary_period_days': days,
                'timeline': self._generate_timeline_data(all_events, days)
            }
            
        except Exception as e:
            conn.close()
            print(f"Security summary error: {e}")
            return {}
    
    def _generate_timeline_data(self, events, days):
        """Generate timeline data for charts"""
        try:
            from datetime import datetime, timedelta
            
            # Create timeline buckets
            if days <= 1:
                # Hourly buckets for 24 hours
                buckets = []
                bucket_size = timedelta(hours=1)
                start_time = datetime.now() - timedelta(days=1)
                for i in range(24):
                    buckets.append(start_time + (i * bucket_size))
            elif days <= 7:
                # Daily buckets for 7 days
                buckets = []
                bucket_size = timedelta(days=1)
                start_time = datetime.now() - timedelta(days=days)
                for i in range(days):
                    buckets.append(start_time + (i * bucket_size))
            else:
                # Weekly buckets for longer periods
                buckets = []
                bucket_size = timedelta(days=7)
                start_time = datetime.now() - timedelta(days=days)
                weeks = days // 7 + 1
                for i in range(weeks):
                    buckets.append(start_time + (i * bucket_size))
            
            # Initialize data
            labels = []
            high_severity = [0] * len(buckets)
            medium_severity = [0] * len(buckets)
            low_severity = [0] * len(buckets)
            
            # Generate labels
            for bucket in buckets:
                if days <= 1:
                    labels.append(bucket.strftime('%H:00'))
                elif days <= 7:
                    labels.append(bucket.strftime('%d.%m'))
                else:
                    labels.append(bucket.strftime('%d.%m'))
            
            # Count events in buckets
            for event in events:
                if isinstance(event['timestamp'], str):
                    event_time = datetime.fromisoformat(event['timestamp'])
                else:
                    event_time = event['timestamp']
                
                # Find appropriate bucket
                for i, bucket in enumerate(buckets):
                    if i < len(buckets) - 1:
                        next_bucket = buckets[i + 1]
                        if bucket <= event_time < next_bucket:
                            if event['severity'] == 'high':
                                high_severity[i] += 1
                            elif event['severity'] == 'medium':
                                medium_severity[i] += 1
                            elif event['severity'] == 'low':
                                low_severity[i] += 1
                            break
                    else:
                        # Last bucket
                        if bucket <= event_time:
                            if event['severity'] == 'high':
                                high_severity[i] += 1
                            elif event['severity'] == 'medium':
                                medium_severity[i] += 1
                            elif event['severity'] == 'low':
                                low_severity[i] += 1
                            break
            
            return {
                'labels': labels,
                'high_severity': high_severity,
                'medium_severity': medium_severity,
                'low_severity': low_severity
            }
            
        except Exception as e:
            print(f"Timeline generation error: {e}")
            return {
                'labels': [],
                'high_severity': [],
                'medium_severity': [],
                'low_severity': []
            }

# Global security manager instance
security_manager = SecurityManager()