"""
Production Server Configuration
WSGI server setup for enterprise deployment
"""

import logging
import sys
import os
from waitress import serve
from waitress.server import create_server
from paste.translogger import TransLogger

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from enterprise_config import ENTERPRISE_CONFIG

def configure_logging():
    """Configure enterprise-grade logging"""
    log_level = ENTERPRISE_CONFIG.get('log_level', 'INFO')
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.FileHandler('logs/deepsearch.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Rotate logs if they get too large
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        'logs/deepsearch.log',
        maxBytes=ENTERPRISE_CONFIG.get('log_max_size', 100) * 1024 * 1024,  # MB to bytes
        backupCount=ENTERPRISE_CONFIG.get('log_backup_count', 10)
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Configure app logger
    app.logger.handlers = []
    app.logger.addHandler(file_handler)
    app.logger.setLevel(getattr(logging, log_level))

def create_production_app():
    """Create production-ready Flask application"""
    # Apply enterprise configuration
    app.config.update(ENTERPRISE_CONFIG)
    
    # Configure security headers
    @app.after_request
    def set_security_headers(response):
        # Security headers for enterprise deployment
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://kit.fontawesome.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' https://kit.fontawesome.com https://ka-f.fontawesome.com;"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Performance headers
        if request.endpoint and request.endpoint.startswith('static'):
            response.headers['Cache-Control'] = 'public, max-age=31536000'
        else:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        return response
    
    # Health check endpoint for load balancers
    @app.route('/health')
    def health_check():
        """Health check endpoint for load balancers"""
        try:
            # Check database connectivity
            from init_database import get_db_connection
            with get_db_connection() as conn:
                conn.execute("SELECT 1").fetchone()
            
            # Check search engine
            from enterprise_search import get_enterprise_search_engine
            search_engine = get_enterprise_search_engine()
            
            # Check memory usage
            from resource_manager import get_system_health
            health = get_system_health()
            
            if health['memory_usage'] > 95:
                return {'status': 'unhealthy', 'reason': 'high_memory'}, 503
            
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'memory_usage': health['memory_usage'],
                'search_engine': 'operational'
            }
            
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}, 503
    
    # Metrics endpoint for monitoring
    @app.route('/metrics')
    def metrics():
        """Metrics endpoint for monitoring systems"""
        try:
            from enterprise_search import get_enterprise_search_engine
            from resource_manager import get_system_health
            
            search_engine = get_enterprise_search_engine()
            search_analytics = search_engine.get_search_analytics()
            system_health = get_system_health()
            
            return {
                'search_metrics': search_analytics,
                'system_metrics': system_health,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            app.logger.error(f"Metrics collection failed: {e}")
            return {'error': str(e)}, 500
    
    return app

def run_production_server():
    """Run production WSGI server"""
    # Configure logging
    configure_logging()
    
    # Create production app
    production_app = create_production_app()
    
    # Wrap with transaction logging
    logged_app = TransLogger(production_app, setup_console_handler=False)
    
    # Server configuration
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    threads = ENTERPRISE_CONFIG.get('max_workers', 8)
    
    print(f"🚀 Starting DeepSearch Production Server")
    print(f"📡 Host: {host}:{port}")
    print(f"🔧 Threads: {threads}")
    print(f"📊 Enterprise Mode: Enabled")
    print(f"🔒 Security Headers: Enabled")
    print(f"📝 Logging: Configured")
    print("=" * 50)
    
    try:
        # Use Waitress WSGI server for production
        serve(
            logged_app,
            host=host,
            port=port,
            threads=threads,
            cleanup_interval=30,
            channel_timeout=120,
            log_socket_errors=True,
            # Performance tuning
            send_bytes=65536,
            # Connection handling
            backlog=1024,
            recv_bytes=65536,
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server shutdown requested")
    except Exception as e:
        print(f"❌ Server error: {e}")
        logging.error(f"Production server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # Import required modules
    from datetime import datetime
    from flask import request
    
    run_production_server()