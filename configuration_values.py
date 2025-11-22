"""
Configuration values for KF Searcher (KS1)
Based on VS5 architecture, adapted for Kufar.by
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Kufar.by API Configuration
KF_BASE_URL = "https://www.kufar.by"
KF_API_BASE_URL = "https://www.kufar.by"
KF_SEARCH_ENDPOINT = "/listings"
KF_AD_ENDPOINT = "/item"

# Database Configuration
# На Railway используется PostgreSQL, локально - SQLite
if os.getenv('RAILWAY_ENVIRONMENT'):
    print("🚀 Railway environment detected")
    
    # На Railway ждем PostgreSQL URL из переменной окружения
    DATABASE_URL = os.getenv('DATABASE_URL')
    print(f"📍 DATABASE_URL from env: {'SET' if DATABASE_URL else 'NOT SET'}")
    
    if not DATABASE_URL:
        # Если нет DATABASE_URL, пытаемся собрать из отдельных переменных Railway
        db_host = os.getenv('PGHOST') or os.getenv('DATABASE_HOST')
        db_port = os.getenv('PGPORT') or os.getenv('DATABASE_PORT', '5432')
        db_name = os.getenv('PGDATABASE') or os.getenv('DATABASE_NAME')
        db_user = os.getenv('PGUSER') or os.getenv('DATABASE_USER')
        db_password = os.getenv('PGPASSWORD') or os.getenv('DATABASE_PASSWORD')
        
        print(f"📍 Individual DB vars: host={bool(db_host)}, port={bool(db_port)}, name={bool(db_name)}, user={bool(db_user)}, password={bool(db_password)}")
        
        if all([db_host, db_name, db_user, db_password]):
            DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            print(f"✅ Constructed DATABASE_URL from individual variables")
        else:
            print("❌ Missing PostgreSQL variables, checking for other DATABASE_URL patterns...")
            
            # Проверяем альтернативные переменные Railway
            for env_var in ['DATABASE_URL', 'POSTGRES_URL', 'POSTGRESQL_URL', 'DB_URL']:
                alt_url = os.getenv(env_var)
                if alt_url:
                    DATABASE_URL = alt_url
                    print(f"✅ Found DATABASE_URL in {env_var}")
                    break
            
            if not DATABASE_URL:
                print("🔍 Available environment variables with 'DB' or 'POSTGRES':")
                for key, value in os.environ.items():
                    if any(term in key.upper() for term in ['DB', 'POSTGRES', 'DATABASE']):
                        print(f"  {key}: {value[:50]}{'...' if len(value) > 50 else ''}")
                
                # Fallback на SQLite вместо краша
                print("⚠️ No PostgreSQL found, falling back to SQLite for now")
                DATABASE_URL = 'sqlite:///kufar_searcher.db'
    
    print(f"🔗 Final DATABASE_URL: {DATABASE_URL[:50]}{'...' if len(DATABASE_URL) > 50 else ''}")
else:
    # Локальная разработка - используем SQLite
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///kufar_searcher.db')

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_THREAD_ID = os.getenv('TELEGRAM_THREAD_ID')

# Proxy Configuration
PROXY_ENABLED = os.getenv('PROXY_ENABLED', 'false').lower() == 'true'
PROXY_LIST = os.getenv('PROXY_LIST', '').split(',') if os.getenv('PROXY_LIST') else []

# Railway Configuration
RAILWAY_TOKEN = os.getenv('RAILWAY_TOKEN')
RAILWAY_PROJECT_ID = os.getenv('RAILWAY_PROJECT_ID')
RAILWAY_SERVICE_ID = os.getenv('RAILWAY_SERVICE_ID')

# Auto-redeploy Configuration
MAX_ERRORS_BEFORE_REDEPLOY = int(os.getenv('MAX_ERRORS_BEFORE_REDEPLOY', '5'))
ERROR_CODES_FOR_REDEPLOY = [403, 404, 429, 500, 502, 503]

# Search Configuration
def get_search_interval():
    """Get search interval from database or environment"""
    try:
        from db import get_db
        
        # ПРИОРИТЕТ 1: Настройки из базы данных (веб-интерфейс) - ВСЕГДА ИМЕЕТ ПРИОРИТЕТ!
        db_value = get_db().get_setting('SEARCH_INTERVAL')
        if db_value and db_value.strip():
            result = int(db_value)
            env_value = os.getenv('SEARCH_INTERVAL', 'NOT SET')
            print(f"🔧 SEARCH_INTERVAL from database (WebUI): {db_value} -> {result} (env={env_value} IGNORED)")
            return result
        
        # ПРИОРИТЕТ 2: Переменные среды (только если НЕТ в БД)
        env_value = os.getenv('SEARCH_INTERVAL')
        if env_value and env_value.strip():
            result = int(env_value)
            print(f"🔧 SEARCH_INTERVAL from environment (no DB setting): {env_value} -> {result}")
            return result
        
        # ПРИОРИТЕТ 3: Дефолт
        print(f"🔧 SEARCH_INTERVAL default (no DB, no env): 300")
        return 300
        
    except Exception as e:
        # FALLBACK: Переменные среды или дефолт
        env_value = os.getenv('SEARCH_INTERVAL', '300')
        print(f"🔧 SEARCH_INTERVAL fallback due to error: {env_value} (error: {e})")
        return int(env_value)

def get_max_items_per_search():
    """Get max items per search from database or environment"""
    try:
        from db import get_db
        
        # ПРИОРИТЕТ 1: Настройки из базы данных (веб-интерфейс) - ВСЕГДА ИМЕЕТ ПРИОРИТЕТ!
        db_value = get_db().get_setting('MAX_ITEMS_PER_SEARCH')
        if db_value and db_value.strip():
            result = int(db_value)
            env_value = os.getenv('MAX_ITEMS_PER_SEARCH', 'NOT SET')
            print(f"🔧 MAX_ITEMS_PER_SEARCH from database (WebUI): {db_value} -> {result} (env={env_value} IGNORED)")
            return result
        
        # ПРИОРИТЕТ 2: Переменные среды (только если НЕТ в БД)
        env_value = os.getenv('MAX_ITEMS_PER_SEARCH')
        if env_value and env_value.strip():
            result = int(env_value)
            print(f"🔧 MAX_ITEMS_PER_SEARCH from environment (no DB setting): {env_value} -> {result}")
            return result
        
        # ПРИОРИТЕТ 3: Дефолт
        print(f"🔧 MAX_ITEMS_PER_SEARCH default (no DB, no env): 50")
        return 50
        
    except Exception as e:
        # FALLBACK: Переменные среды или дефолт
        env_value = os.getenv('MAX_ITEMS_PER_SEARCH', '50')
        print(f"🔧 MAX_ITEMS_PER_SEARCH fallback due to error: {env_value} (error: {e})")
        return int(env_value)

def get_telegram_bot_token():
    """Get telegram bot token from database or environment"""
    try:
        from db import get_db
        value = get_db().get_setting('TELEGRAM_BOT_TOKEN')
        return value if value else os.getenv('TELEGRAM_BOT_TOKEN')
    except:
        return os.getenv('TELEGRAM_BOT_TOKEN')

def get_telegram_chat_id():
    """Get telegram chat id from database or environment"""
    try:
        from db import get_db
        value = get_db().get_setting('TELEGRAM_CHAT_ID')
        return value if value else os.getenv('TELEGRAM_CHAT_ID')
    except:
        return os.getenv('TELEGRAM_CHAT_ID')

# Legacy compatibility - removed caching, now always reads from DB
# SEARCH_INTERVAL = get_search_interval()  # Don't cache - always call function
# MAX_ITEMS_PER_SEARCH = get_max_items_per_search()  # Don't cache - always call function

# Web UI Configuration
WEB_UI_PORT = int(os.getenv('PORT', '5000'))
WEB_UI_HOST = os.getenv('WEB_UI_HOST', '0.0.0.0')
SECRET_KEY = os.getenv('SECRET_KEY', 'kufar-searcher-secret-key-change-in-production')

# Regions mapping for Kufar.by
KF_REGIONS = {
    'minsk': 'Минск',
    'gomel': 'Гомель', 
    'brest': 'Брест',
    'vitebsk': 'Витебск',
    'grodno': 'Гродно',
    'mogilev': 'Могилев'
}

# Categories mapping for Kufar.by
KF_CATEGORIES = {
    'cars': 'Автомобили',
    'real_estate': 'Недвижимость',
    'electronics': 'Электроника',
    'clothes': 'Одежда и обувь',
    'home': 'Дом и сад',
    'services': 'Услуги'
}

# Request headers to mimic real browser
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'kufar_searcher.log')

# Rate limiting
REQUEST_DELAY_MIN = float(os.getenv('REQUEST_DELAY_MIN', '1.0'))
REQUEST_DELAY_MAX = float(os.getenv('REQUEST_DELAY_MAX', '3.0'))
