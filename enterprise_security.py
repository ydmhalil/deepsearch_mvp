"""
Enterprise Security and Multi-tenant Support
Advanced security features for large organizations
"""

import hashlib
import secrets
import time
import jwt
import pyotp
import qrcode
import io
import base64
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from functools import wraps
from flask import request, session, jsonify, current_app
import logging
import threading
from collections import defaultdict, deque
import ipaddress
import re

@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: str
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    severity: str  # low, medium, high, critical
    details: Dict[str, Any]
    tenant_id: Optional[str] = None

@dataclass
class UserSession:
    """Enhanced user session data"""
    session_id: str
    user_id: str
    tenant_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    is_2fa_verified: bool
    device_fingerprint: str
    security_level: str

class EnterpriseSecurity:
    """Enterprise-grade security manager"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.rate_limits = defaultdict(lambda: deque(maxlen=100))
        self.rate_limit_lock = threading.RLock()
        
        # Login attempt tracking
        self.login_attempts = defaultdict(list)
        self.locked_accounts = {}
        self.locked_ips = {}
        
        # Session management
        self.active_sessions = {}
        self.session_lock = threading.RLock()
        
        # Security events
        self.security_events = deque(maxlen=10000)
        self.events_lock = threading.RLock()
        
        # IP whitelisting
        self.whitelist_enabled = config.get('enable_ip_whitelisting', False)
        self.allowed_ips = self._parse_ip_whitelist(config.get('allowed_ips', []))
        
        # 2FA settings
        self.enable_2fa = config.get('enable_2fa', True)
        self.totp_issuer = config.get('totp_issuer', 'DeepSearch Enterprise')
        
        # JWT settings
        self.jwt_secret = config.get('jwt_secret', secrets.token_urlsafe(32))
        self.jwt_algorithm = 'HS256'
        self.jwt_expiration = config.get('jwt_expiration', 3600)  # 1 hour
        
        # Password complexity
        self.password_min_length = config.get('password_min_length', 12)
        self.password_complexity = config.get('password_complexity', True)
        
        # Start security monitoring
        self._start_security_monitoring()
    
    def _parse_ip_whitelist(self, ip_list: List[str]) -> List[ipaddress.IPv4Network]:
        """Parse IP whitelist configuration"""
        parsed_ips = []
        for ip_str in ip_list:
            try:
                if '/' in ip_str:
                    parsed_ips.append(ipaddress.IPv4Network(ip_str))
                else:
                    parsed_ips.append(ipaddress.IPv4Network(f"{ip_str}/32"))
            except Exception as e:
                self.logger.error(f"Invalid IP in whitelist: {ip_str} - {e}")
        return parsed_ips
    
    def _start_security_monitoring(self):
        """Start background security monitoring"""
        def security_worker():
            while True:
                try:
                    time.sleep(60)  # Check every minute
                    self._cleanup_expired_sessions()
                    self._cleanup_old_events()
                    self._analyze_security_patterns()
                except Exception as e:
                    self.logger.error(f"Security monitoring error: {e}")
        
        thread = threading.Thread(target=security_worker, daemon=True)
        thread.start()
    
    def validate_ip_access(self, ip_address: str) -> bool:
        """Validate IP access against whitelist"""
        if not self.whitelist_enabled:
            return True
        
        try:
            client_ip = ipaddress.IPv4Address(ip_address)
            for allowed_network in self.allowed_ips:
                if client_ip in allowed_network:
                    return True
            return False
        except Exception as e:
            self.logger.error(f"IP validation error: {e}")
            return False
    
    def check_rate_limit(self, identifier: str, limit: int = None, window: int = 60) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limiting for requests"""
        limit = limit or self.config.get('rate_limit_per_minute', 100)
        current_time = time.time()
        
        with self.rate_limit_lock:
            # Clean old entries
            requests = self.rate_limits[identifier]
            while requests and requests[0] < current_time - window:
                requests.popleft()
            
            # Check if limit exceeded
            if len(requests) >= limit:
                return False, {
                    'allowed': False,
                    'limit': limit,
                    'remaining': 0,
                    'reset_time': int(requests[0] + window)
                }
            
            # Add current request
            requests.append(current_time)
            
            return True, {
                'allowed': True,
                'limit': limit,
                'remaining': limit - len(requests),
                'reset_time': int(current_time + window)
            }
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength according to enterprise policies"""
        result = {
            'is_valid': True,
            'score': 0,
            'feedback': []
        }
        
        # Check minimum length
        if len(password) < self.password_min_length:
            result['is_valid'] = False
            result['feedback'].append(f"Password must be at least {self.password_min_length} characters long")
        else:
            result['score'] += 20
        
        if not self.password_complexity:
            return result
        
        # Check complexity requirements
        checks = [
            (r'[a-z]', "lowercase letter"),
            (r'[A-Z]', "uppercase letter"),
            (r'[0-9]', "number"),
            (r'[!@#$%^&*(),.?\":{}|<>]', "special character")
        ]
        
        for pattern, description in checks:
            if re.search(pattern, password):
                result['score'] += 20
            else:
                result['is_valid'] = False
                result['feedback'].append(f"Password must contain at least one {description}")
        
        # Check for common patterns
        if password.lower() in ['password', '123456', 'admin', 'user']:
            result['is_valid'] = False
            result['feedback'].append("Password is too common")
            result['score'] -= 50
        
        # Check for repeated characters
        if len(set(password)) < len(password) * 0.6:
            result['feedback'].append("Password has too many repeated characters")
            result['score'] -= 10
        
        result['score'] = max(0, min(100, result['score']))
        
        return result
    
    def generate_2fa_secret(self, user_email: str) -> Tuple[str, str]:
        """Generate 2FA secret and QR code"""
        secret = pyotp.random_base32()
        
        # Create TOTP URL
        totp_url = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=self.totp_issuer
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        qr_code_data = base64.b64encode(img_io.getvalue()).decode()
        
        return secret, qr_code_data
    
    def verify_2fa_token(self, secret: str, token: str) -> bool:
        """Verify 2FA token"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)
        except Exception as e:
            self.logger.error(f"2FA verification error: {e}")
            return False
    
    def create_secure_session(self, user_id: str, tenant_id: str, 
                            ip_address: str, user_agent: str) -> UserSession:
        """Create a secure user session"""
        session_id = secrets.token_urlsafe(32)
        device_fingerprint = self._generate_device_fingerprint(ip_address, user_agent)
        
        session_data = UserSession(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            is_2fa_verified=False,
            device_fingerprint=device_fingerprint,
            security_level='basic'
        )
        
        with self.session_lock:
            self.active_sessions[session_id] = session_data
        
        # Log session creation
        self._log_security_event(
            'session_created',
            user_id,
            ip_address,
            user_agent,
            'low',
            {'session_id': session_id, 'tenant_id': tenant_id},
            tenant_id
        )
        
        return session_data
    
    def validate_session(self, session_id: str, ip_address: str, 
                        user_agent: str) -> Optional[UserSession]:
        """Validate user session"""
        with self.session_lock:
            if session_id not in self.active_sessions:
                return None
            
            session_data = self.active_sessions[session_id]
            
            # Check session expiration
            session_timeout = self.config.get('session_timeout', timedelta(hours=8))
            if datetime.now() - session_data.last_activity > session_timeout:
                del self.active_sessions[session_id]
                self._log_security_event(
                    'session_expired',
                    session_data.user_id,
                    ip_address,
                    user_agent,
                    'low',
                    {'session_id': session_id}
                )
                return None
            
            # Check IP consistency (optional)
            if self.config.get('strict_ip_checking', False):
                if session_data.ip_address != ip_address:
                    self._log_security_event(
                        'session_ip_mismatch',
                        session_data.user_id,
                        ip_address,
                        user_agent,
                        'high',
                        {
                            'session_id': session_id,
                            'original_ip': session_data.ip_address,
                            'current_ip': ip_address
                        }
                    )
                    return None
            
            # Update last activity
            session_data.last_activity = datetime.now()
            
            return session_data
    
    def invalidate_session(self, session_id: str):
        """Invalidate a user session"""
        with self.session_lock:
            if session_id in self.active_sessions:
                session_data = self.active_sessions[session_id]
                del self.active_sessions[session_id]
                
                self._log_security_event(
                    'session_invalidated',
                    session_data.user_id,
                    session_data.ip_address,
                    session_data.user_agent,
                    'low',
                    {'session_id': session_id}
                )
    
    def _generate_device_fingerprint(self, ip_address: str, user_agent: str) -> str:
        """Generate device fingerprint"""
        fingerprint_data = f"{ip_address}:{user_agent}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    def track_login_attempt(self, identifier: str, success: bool, 
                          ip_address: str, user_agent: str) -> Dict[str, Any]:
        """Track login attempts for account security"""
        current_time = datetime.now()
        max_attempts = self.config.get('max_login_attempts', 5)
        lockout_duration = self.config.get('lockout_duration', timedelta(minutes=30))
        
        # Clean old attempts
        cutoff_time = current_time - timedelta(hours=1)
        self.login_attempts[identifier] = [
            attempt for attempt in self.login_attempts[identifier]
            if attempt['timestamp'] > cutoff_time
        ]
        
        # Add current attempt
        self.login_attempts[identifier].append({
            'success': success,
            'timestamp': current_time,
            'ip_address': ip_address,
            'user_agent': user_agent
        })
        
        # Check for account lockout
        recent_failures = [
            attempt for attempt in self.login_attempts[identifier]
            if not attempt['success'] and 
               current_time - attempt['timestamp'] < timedelta(minutes=15)
        ]
        
        if len(recent_failures) >= max_attempts:
            self.locked_accounts[identifier] = current_time + lockout_duration
            
            self._log_security_event(
                'account_locked',
                identifier,
                ip_address,
                user_agent,
                'high',
                {
                    'failed_attempts': len(recent_failures),
                    'lockout_until': (current_time + lockout_duration).isoformat()
                }
            )
            
            return {
                'is_locked': True,
                'lockout_until': current_time + lockout_duration,
                'attempts_remaining': 0
            }
        
        return {
            'is_locked': False,
            'attempts_remaining': max_attempts - len(recent_failures),
            'lockout_until': None
        }
    
    def is_account_locked(self, identifier: str) -> bool:
        """Check if account is currently locked"""
        if identifier in self.locked_accounts:
            if datetime.now() > self.locked_accounts[identifier]:
                # Lock expired
                del self.locked_accounts[identifier]
                return False
            return True
        return False
    
    def _log_security_event(self, event_type: str, user_id: str, 
                          ip_address: str, user_agent: str, severity: str,
                          details: Dict[str, Any], tenant_id: str = None):
        """Log security event"""
        event = SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(),
            severity=severity,
            details=details,
            tenant_id=tenant_id
        )
        
        with self.events_lock:
            self.security_events.append(event)
        
        # Log to file for persistent storage
        self.logger.warning(f"Security Event [{severity.upper()}]: {event_type} - User: {user_id}, IP: {ip_address}")
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        session_timeout = self.config.get('session_timeout', timedelta(hours=8))
        current_time = datetime.now()
        expired_sessions = []
        
        with self.session_lock:
            for session_id, session_data in list(self.active_sessions.items()):
                if current_time - session_data.last_activity > session_timeout:
                    expired_sessions.append(session_id)
                    del self.active_sessions[session_id]
        
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def _cleanup_old_events(self):
        """Clean up old security events"""
        cutoff_time = datetime.now() - timedelta(days=30)
        
        with self.events_lock:
            # Keep only events from last 30 days
            self.security_events = deque(
                [event for event in self.security_events if event.timestamp > cutoff_time],
                maxlen=10000
            )
    
    def _analyze_security_patterns(self):
        """Analyze security events for patterns"""
        try:
            # Analyze recent events for suspicious patterns
            recent_events = [
                event for event in self.security_events
                if datetime.now() - event.timestamp < timedelta(hours=1)
            ]
            
            # Check for suspicious IP activity
            ip_activity = defaultdict(list)
            for event in recent_events:
                ip_activity[event.ip_address].append(event)
            
            for ip, events in ip_activity.items():
                if len(events) > 50:  # High activity threshold
                    # Check if it's legitimate or suspicious
                    failed_logins = sum(1 for e in events if e.event_type == 'login_failed')
                    if failed_logins > 10:
                        self._log_security_event(
                            'suspicious_ip_activity',
                            'system',
                            ip,
                            'automated_detection',
                            'high',
                            {
                                'total_events': len(events),
                                'failed_logins': failed_logins,
                                'analysis_window': '1_hour'
                            }
                        )
            
        except Exception as e:
            self.logger.error(f"Security pattern analysis error: {e}")
    
    def generate_jwt_token(self, user_id: str, tenant_id: str, 
                          additional_claims: Dict[str, Any] = None) -> str:
        """Generate JWT token for API access"""
        payload = {
            'user_id': user_id,
            'tenant_id': tenant_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=self.jwt_expiration),
            'iss': 'deepsearch-enterprise'
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            self.logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Invalid JWT token: {e}")
            return None
    
    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get security dashboard data"""
        recent_time = datetime.now() - timedelta(hours=24)
        
        with self.events_lock:
            recent_events = [
                event for event in self.security_events
                if event.timestamp > recent_time
            ]
        
        # Categorize events
        event_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for event in recent_events:
            event_counts[event.event_type] += 1
            severity_counts[event.severity] += 1
        
        # Active sessions
        with self.session_lock:
            active_session_count = len(self.active_sessions)
            
            # Session by tenant
            tenant_sessions = defaultdict(int)
            for session in self.active_sessions.values():
                tenant_sessions[session.tenant_id] += 1
        
        return {
            'recent_events': {
                'total': len(recent_events),
                'by_type': dict(event_counts),
                'by_severity': dict(severity_counts)
            },
            'active_sessions': {
                'total': active_session_count,
                'by_tenant': dict(tenant_sessions)
            },
            'account_security': {
                'locked_accounts': len(self.locked_accounts),
                'rate_limited_ips': len(self.rate_limits)
            },
            'system_status': {
                'ip_whitelist_enabled': self.whitelist_enabled,
                '2fa_enabled': self.enable_2fa,
                'jwt_auth_enabled': True
            }
        }

class MultiTenantManager:
    """Multi-tenant support for enterprise deployments"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.enabled = config.get('enable_multi_tenant', False)
        self.isolation_type = config.get('tenant_isolation', 'database')
        self.default_tenant = config.get('default_tenant', 'default')
        
        # Tenant configurations
        self.tenant_configs = {}
        self.tenant_lock = threading.RLock()
        
        if self.enabled:
            self._initialize_multi_tenant()
    
    def _initialize_multi_tenant(self):
        """Initialize multi-tenant support"""
        # Load tenant configurations
        # In a real implementation, this would load from a configuration database
        self.tenant_configs[self.default_tenant] = {
            'name': 'Default Organization',
            'database_path': './config/tenants/default/users.db',
            'storage_path': './data/tenants/default/',
            'max_users': 1000,
            'max_storage_gb': 100,
            'features': ['search', 'upload', 'analytics'],
            'created_at': datetime.now()
        }
        
        self.logger.info("Multi-tenant support initialized")
    
    def get_tenant_config(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant configuration"""
        with self.tenant_lock:
            return self.tenant_configs.get(tenant_id)
    
    def create_tenant(self, tenant_id: str, config: Dict[str, Any]) -> bool:
        """Create a new tenant"""
        if not self.enabled:
            return False
        
        try:
            with self.tenant_lock:
                if tenant_id in self.tenant_configs:
                    return False
                
                # Create tenant configuration
                tenant_config = {
                    'name': config.get('name', f'Organization {tenant_id}'),
                    'database_path': f'./config/tenants/{tenant_id}/users.db',
                    'storage_path': f'./data/tenants/{tenant_id}/',
                    'max_users': config.get('max_users', 100),
                    'max_storage_gb': config.get('max_storage_gb', 10),
                    'features': config.get('features', ['search', 'upload']),
                    'created_at': datetime.now()
                }
                
                # Create tenant directories
                import os
                os.makedirs(os.path.dirname(tenant_config['database_path']), exist_ok=True)
                os.makedirs(tenant_config['storage_path'], exist_ok=True)
                
                self.tenant_configs[tenant_id] = tenant_config
                
                self.logger.info(f"Created tenant: {tenant_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to create tenant {tenant_id}: {e}")
            return False
    
    def get_tenant_database_path(self, tenant_id: str) -> str:
        """Get tenant-specific database path"""
        if not self.enabled:
            return './config/users.db'
        
        tenant_config = self.get_tenant_config(tenant_id)
        if tenant_config:
            return tenant_config['database_path']
        
        return self.tenant_configs[self.default_tenant]['database_path']
    
    def get_tenant_storage_path(self, tenant_id: str) -> str:
        """Get tenant-specific storage path"""
        if not self.enabled:
            return './data/'
        
        tenant_config = self.get_tenant_config(tenant_id)
        if tenant_config:
            return tenant_config['storage_path']
        
        return self.tenant_configs[self.default_tenant]['storage_path']

# Security decorators
def require_2fa(f):
    """Decorator to require 2FA verification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user has 2FA enabled and verified
        user = get_current_user()
        if user and user.get('2fa_enabled'):
            session_id = session.get('session_id')
            if session_id:
                enterprise_security = get_enterprise_security()
                session_data = enterprise_security.validate_session(
                    session_id, 
                    request.remote_addr, 
                    request.user_agent.string
                )
                if not session_data or not session_data.is_2fa_verified:
                    return jsonify({'error': '2FA verification required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(limit: int = 100, window: int = 60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            enterprise_security = get_enterprise_security()
            
            # Use IP + user ID as identifier
            identifier = f"{request.remote_addr}:{session.get('user_id', 'anonymous')}"
            
            allowed, rate_info = enterprise_security.check_rate_limit(identifier, limit, window)
            
            if not allowed:
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': rate_info['reset_time']
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(rate_info['reset_time'])
                return response
            
            # Add rate limit headers
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(rate_info['reset_time'])
            
            return response
        return decorated_function
    return decorator

# Global instances
enterprise_security = None
multi_tenant_manager = None

def get_enterprise_security(config: Dict[str, Any] = None) -> EnterpriseSecurity:
    """Get global enterprise security instance"""
    global enterprise_security
    
    if enterprise_security is None:
        from enterprise_config import ENTERPRISE_CONFIG
        config = config or ENTERPRISE_CONFIG
        enterprise_security = EnterpriseSecurity(config)
    
    return enterprise_security

def get_multi_tenant_manager(config: Dict[str, Any] = None) -> MultiTenantManager:
    """Get global multi-tenant manager instance"""
    global multi_tenant_manager
    
    if multi_tenant_manager is None:
        from enterprise_config import ENTERPRISE_CONFIG
        config = config or ENTERPRISE_CONFIG
        multi_tenant_manager = MultiTenantManager(config)
    
    return multi_tenant_manager

# Import required modules for decorators
from auth import get_current_user