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
    # На Railway ждем PostgreSQL URL из переменной окружения
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        # Если нет DATABASE_URL, пытаемся собрать из отдельных переменных Railway
        db_host = os.getenv('PGHOST') or os.getenv('DATABASE_HOST')
        db_port = os.getenv('PGPORT') or os.getenv('DATABASE_PORT', '5432')
        db_name = os.getenv('PGDATABASE') or os.getenv('DATABASE_NAME')
        db_user = os.getenv('PGUSER') or os.getenv('DATABASE_USER')
        db_password = os.getenv('PGPASSWORD') or os.getenv('DATABASE_PASSWORD')
        
        if all([db_host, db_name, db_user, db_password]):
            DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            raise ValueError("DATABASE_URL not found for Railway deployment. Please add PostgreSQL service to your Railway project.")
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
        value = get_db().get_setting('SEARCH_INTERVAL')
        return int(value) if value else int(os.getenv('SEARCH_INTERVAL', '300'))
    except:
        return int(os.getenv('SEARCH_INTERVAL', '300'))

def get_max_items_per_search():
    """Get max items per search from database or environment"""
    try:
        from db import get_db
        value = get_db().get_setting('MAX_ITEMS_PER_SEARCH')
        return int(value) if value else int(os.getenv('MAX_ITEMS_PER_SEARCH', '50'))
    except:
        return int(os.getenv('MAX_ITEMS_PER_SEARCH', '50'))

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

# Legacy compatibility
SEARCH_INTERVAL = get_search_interval()
MAX_ITEMS_PER_SEARCH = get_max_items_per_search()

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
