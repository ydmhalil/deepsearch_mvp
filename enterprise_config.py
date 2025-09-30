"""
Enterprise Configuration for DeepSearch
Production-ready settings for large organizations
"""

import os
from datetime import timedelta

class EnterpriseConfig:
    """Enterprise-grade configuration settings"""
    
    # Database settings for large companies
    DATABASE_SETTINGS = {
        'connection_pool_size': 50,
        'max_overflow': 100,
        'pool_timeout': 30,
        'pool_recycle': 3600,
        'enable_query_cache': True,
        'query_cache_size': 1000,
        'enable_indexing': True,
        'auto_vacuum': 'incremental'
    }
    
    # Search performance settings
    SEARCH_SETTINGS = {
        'max_concurrent_searches': 100,
        'search_timeout': 30,
        'cache_search_results': True,
        'cache_ttl': 3600,  # 1 hour
        'max_results_per_search': 1000,
        'enable_search_analytics': True,
        'enable_search_suggestions': True,
        'suggestion_cache_size': 10000,
        'parallel_processing': True,
        'max_workers': 8
    }
    
    # Security settings for enterprise
    SECURITY_SETTINGS = {
        'enable_2fa': True,
        'password_min_length': 12,
        'password_complexity': True,
        'session_timeout': timedelta(hours=8),
        'max_login_attempts': 5,
        'lockout_duration': timedelta(minutes=30),
        'enable_audit_logging': True,
        'enable_rate_limiting': True,
        'rate_limit_per_minute': 100,
        'enable_ip_whitelisting': False,
        'allowed_ips': [],
        'enable_ssl_only': True,
        'csrf_protection': True
    }
    
    # File processing settings
    FILE_SETTINGS = {
        'max_file_size': 500 * 1024 * 1024,  # 500MB
        'allowed_extensions': ['.pdf', '.docx', '.xlsx', '.pptx', '.txt', '.csv'],
        'virus_scanning': True,
        'content_validation': True,
        'auto_indexing': True,
        'batch_processing': True,
        'max_batch_size': 100,
        'processing_threads': 4
    }
    
    # Performance optimization
    PERFORMANCE_SETTINGS = {
        'enable_caching': True,
        'cache_backend': 'redis',  # redis, memcached, or filesystem
        'cache_default_timeout': 3600,
        'enable_compression': True,
        'enable_minification': True,
        'static_file_caching': True,
        'database_optimization': True,
        'memory_monitoring': True,
        'auto_cleanup': True,
        'cleanup_interval': 24  # hours
    }
    
    # Multi-tenant support
    TENANT_SETTINGS = {
        'enable_multi_tenant': False,  # Set to True for multi-tenant deployment
        'tenant_isolation': 'database',  # 'database' or 'schema'
        'default_tenant': 'default',
        'tenant_specific_config': True,
        'tenant_analytics': True
    }
    
    # Monitoring and analytics
    MONITORING_SETTINGS = {
        'enable_performance_monitoring': True,
        'enable_error_tracking': True,
        'enable_user_analytics': True,
        'log_level': 'INFO',
        'log_rotation': True,
        'log_max_size': 100,  # MB
        'log_backup_count': 10,
        'health_check_interval': 60,  # seconds
        'alert_thresholds': {
            'memory_usage': 85,
            'cpu_usage': 80,
            'disk_usage': 90,
            'response_time': 5000  # ms
        }
    }
    
    # API settings for integrations
    API_SETTINGS = {
        'enable_rest_api': True,
        'enable_graphql': False,
        'api_rate_limiting': True,
        'api_authentication': 'bearer',
        'api_versioning': True,
        'current_api_version': 'v1',
        'enable_api_docs': True,
        'cors_enabled': True,
        'cors_origins': ['*']  # Restrict in production
    }

    @classmethod
    def get_config(cls, environment='production'):
        """Get configuration based on environment"""
        if environment == 'development':
            return cls._get_development_config()
        elif environment == 'testing':
            return cls._get_testing_config()
        else:
            return cls._get_production_config()
    
    @classmethod
    def _get_production_config(cls):
        """Production configuration with enterprise features"""
        return {
            'SECRET_KEY': os.environ.get('SECRET_KEY', 'change-this-in-production'),
            'DATABASE_URL': os.environ.get('DATABASE_URL'),
            'REDIS_URL': os.environ.get('REDIS_URL'),
            'DEBUG': False,
            'TESTING': False,
            'WTF_CSRF_ENABLED': True,
            'SSL_REDIRECT': True,
            **cls.DATABASE_SETTINGS,
            **cls.SEARCH_SETTINGS,
            **cls.SECURITY_SETTINGS,
            **cls.FILE_SETTINGS,
            **cls.PERFORMANCE_SETTINGS,
            **cls.MONITORING_SETTINGS,
            **cls.API_SETTINGS
        }
    
    @classmethod
    def _get_development_config(cls):
        """Development configuration"""
        config = cls._get_production_config()
        config.update({
            'DEBUG': True,
            'SSL_REDIRECT': False,
            'enable_audit_logging': False,
            'virus_scanning': False
        })
        return config
    
    @classmethod
    def _get_testing_config(cls):
        """Testing configuration"""
        config = cls._get_development_config()
        config.update({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'DATABASE_URL': 'sqlite:///:memory:'
        })
        return config

# Export enterprise settings
ENTERPRISE_CONFIG = EnterpriseConfig.get_config(
    os.environ.get('FLASK_ENV', 'production')
)