"""
Railway deployment configuration for KF Searcher
Based on VS5 Railway setup
"""

import os

# Railway environment detection
def is_railway_environment():
    """Check if running on Railway"""
    return os.getenv('RAILWAY_ENVIRONMENT') is not None

# Database configuration for Railway
def get_database_url():
    """Get database URL, prioritizing Railway PostgreSQL"""
    # Railway automatically provides DATABASE_URL for PostgreSQL
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Railway provides postgres:// but some libraries expect postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url
    
    # Fallback to SQLite for local development
    return 'sqlite:///kufar_searcher.db'

# Port configuration
def get_port():
    """Get port for web server"""
    return int(os.getenv('PORT', 5000))

# Environment-specific settings
RAILWAY_SETTINGS = {
    # Web server settings
    'PORT': get_port(),
    'HOST': '0.0.0.0',
    
    # Database
    'DATABASE_URL': get_database_url(),
    
    # Logging
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    'LOG_TO_STDOUT': True,
    
    # Worker settings
    'WORKER_TIMEOUT': int(os.getenv('WORKER_TIMEOUT', 30)),
    'WORKER_CONNECTIONS': int(os.getenv('WORKER_CONNECTIONS', 1000)),
    
    # Application settings
    'DEBUG': os.getenv('DEBUG', 'false').lower() == 'true',
    'SECRET_KEY': os.getenv('SECRET_KEY', 'kufar-searcher-production-key'),
    
    # Railway specific
    'RAILWAY_ENVIRONMENT': os.getenv('RAILWAY_ENVIRONMENT'),
    'RAILWAY_PROJECT_ID': os.getenv('RAILWAY_PROJECT_ID'),
    'RAILWAY_SERVICE_ID': os.getenv('RAILWAY_SERVICE_ID'),
}

# Environment variables setup guide
REQUIRED_ENV_VARS = {
    'TELEGRAM_BOT_TOKEN': 'Bot token from @BotFather (required for notifications)',
    'TELEGRAM_CHAT_ID': 'Default chat ID for notifications (optional)',
    'RAILWAY_TOKEN': 'Railway API token for auto-redeploy (optional)',
    'PROXY_LIST': 'Comma-separated list of proxies (optional)',
}

OPTIONAL_ENV_VARS = {
    'SEARCH_INTERVAL': 'Search interval in seconds (default: 300)',
    'MAX_ITEMS_PER_SEARCH': 'Max items per search (default: 50)',
    'MAX_ERRORS_BEFORE_REDEPLOY': 'Error threshold for redeploy (default: 5)',
    'REQUEST_DELAY_MIN': 'Min delay between requests (default: 1.0)',
    'REQUEST_DELAY_MAX': 'Max delay between requests (default: 3.0)',
    'LOG_LEVEL': 'Logging level (default: INFO)',
    'SECRET_KEY': 'Flask secret key (auto-generated if not set)',
}

def validate_environment():
    """Validate environment variables"""
    warnings = []
    errors = []
    
    # Check required variables
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        warnings.append('TELEGRAM_BOT_TOKEN not set - notifications will not work')
    
    # Check Railway configuration for auto-redeploy
    if is_railway_environment():
        if not os.getenv('RAILWAY_TOKEN'):
            warnings.append('RAILWAY_TOKEN not set - auto-redeploy will not work')
        
        if not os.getenv('RAILWAY_PROJECT_ID'):
            warnings.append('RAILWAY_PROJECT_ID not set - auto-redeploy will not work')
            
        if not os.getenv('RAILWAY_SERVICE_ID'):
            warnings.append('RAILWAY_SERVICE_ID not set - auto-redeploy will not work')
    
    # Check database
    if not get_database_url():
        errors.append('DATABASE_URL not available - database connection will fail')
    
    return {'errors': errors, 'warnings': warnings}

def print_environment_status():
    """Print environment status for debugging"""
    print("=== KF Searcher Environment Status ===")
    print(f"Railway Environment: {is_railway_environment()}")
    print(f"Database URL: {'Set' if get_database_url() else 'Not Set'}")
    print(f"Port: {get_port()}")
    print(f"Debug Mode: {RAILWAY_SETTINGS['DEBUG']}")
    
    validation = validate_environment()
    
    if validation['errors']:
        print("\n❌ ERRORS:")
        for error in validation['errors']:
            print(f"  - {error}")
    
    if validation['warnings']:
        print("\n⚠️  WARNINGS:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    if not validation['errors'] and not validation['warnings']:
        print("\n✅ All environment variables are properly configured!")
    
    print("=" * 40)

if __name__ == '__main__':
    print_environment_status()
