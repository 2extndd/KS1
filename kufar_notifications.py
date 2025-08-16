"""
Main application file for KF Searcher (KS1)
Based on VS5 vinted_notifications.py, adapted for Kufar.by
"""

import os
import sys
import logging
import time
import schedule
from datetime import datetime
from flask import Flask

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from configuration_values import (
    get_search_interval,
    LOG_LEVEL,
    LOG_FILE,
    WEB_UI_HOST,
    WEB_UI_PORT,
    SECRET_KEY
)
from core import searcher
from simple_telegram_worker import send_notifications
from railway_redeploy import redeployer
from db import db

# Create logger first
logger = logging.getLogger(__name__)

# Настройка белорусского часового пояса для логов
import pytz
from datetime import datetime

# Белорусский часовой пояс (UTC+3)
BELARUS_TZ = pytz.timezone('Europe/Minsk')

class BelarusFormatter(logging.Formatter):
    """Кастомный форматер для отображения времени в белорусском часовом поясе"""
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, BELARUS_TZ)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime('%Y-%m-%d %H:%M:%S %Z')

# Configure logging for Railway environment
if os.getenv('RAILWAY_ENVIRONMENT'):
    # Railway environment - log to stdout and database
    formatter = BelarusFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        handlers=[handler]
    )
    
    # Force database logging on Railway
    try:
        # Force PostgreSQL mode on Railway
        db.force_postgres_mode()
        logger.info(f"Database info: {db.get_database_info()}")
        
        # Try to add log entry, but don't fail if database not ready
        try:
            db.add_log_entry('INFO', 'Application started in Railway environment', 'System', 'Railway deployment successful')
            logger.info("Railway environment detected - database logging enabled")
        except Exception as log_error:
            logger.warning(f"Database not ready for logging: {log_error}")
    except Exception as e:
        logger.error(f"Failed to setup Railway database: {e}")
        logger.error(f"Database info: {db.get_database_info()}")
else:
    # Local environment - log to file and stdout
    formatter = BelarusFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        handlers=[file_handler, console_handler]
    )

# Flask app for web UI and health checks
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Global variables for tracking
app_start_time = datetime.now()  # Initialize immediately
total_api_requests = 0
total_items_found = 0
last_search_time = None

# Update start time when app actually starts
def update_start_time():
    global app_start_time
    app_start_time = datetime.now()
    logger.info(f"App start time updated to: {app_start_time}")

# Call this when the app starts running
update_start_time()

# Also update shared_state when app starts
try:
    import shared_state
    shared_state.set_app_start_time(app_start_time)
    logger.info(f"Updated shared_state app_start_time: {app_start_time}")
except Exception as e:
    logger.error(f"Failed to update shared_state: {e}")

def increment_api_requests():
    """Increment the API request counter"""
    global total_api_requests
    total_api_requests += 1
    # Also update shared_state
    try:
        import shared_state
        shared_state.increment_api_requests()
    except:
        pass

@app.route('/')
def health_check():
    """Health check endpoint"""
    try:
        # Get comprehensive system metrics
        metrics = get_system_metrics()
        
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500

@app.route('/stats')
def get_stats():
    """Get application statistics"""
    try:
        return get_system_metrics()
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {'error': str(e)}, 500

@app.route('/api/stats')
def api_stats():
    """API endpoint for stats (used by web UI)"""
    try:
        return get_system_metrics()
    except Exception as e:
        logger.error(f"Error getting API stats: {e}")
        return {'error': str(e)}, 500

def get_system_metrics():
    """Get comprehensive system metrics"""
    try:
        current_time = datetime.now()
        
        # Calculate uptime safely
        if app_start_time:
            uptime = current_time - app_start_time
            uptime_minutes = int(uptime.total_seconds() / 60)
        else:
            uptime_minutes = 0
        
        # Get database stats
        db_stats = db.get_items_stats()
        
        # Get proxy status
        proxy_status = get_proxy_status()
        
        # Get Railway redeploy status
        railway_status = get_railway_status()
        
        # Получаем актуальные метрики из metrics_storage
        try:
            import metrics_storage
            actual_api_requests = metrics_storage.metrics_storage.get_total_api_requests()
            actual_items_found = metrics_storage.metrics_storage.get_total_items_found()
            actual_app_start = metrics_storage.metrics_storage.get_app_start_time()
            
            # Пересчитываем uptime на основе актуального времени старта
            if actual_app_start:
                uptime = current_time - actual_app_start
                uptime_str = str(uptime).split('.')[0]  # Убираем микросекунды
                uptime_minutes = int(uptime.total_seconds() / 60)
            else:
                uptime_str = "0:00:00"
                uptime_minutes = 0
                
        except Exception as e:
            logger.warning(f"Could not get metrics from storage: {e}")
            actual_api_requests = total_api_requests
            actual_items_found = total_items_found
            uptime_str = f"{uptime_minutes}m"
        
        return {
            'uptime_minutes': uptime_minutes,
            'uptime_formatted': uptime_str,
            'total_api_requests': actual_api_requests,
            'total_items_found': actual_items_found,
            'last_search_time': last_search_time.isoformat() if last_search_time else None,
            'database': db_stats,
            'proxy_system': proxy_status,
            'railway_redeploy': railway_status,
            'timestamp': current_time.isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return {
            'error': str(e),
            'uptime_minutes': 0,
            'uptime_formatted': '0m'
        }

def get_proxy_status():
    """Get proxy system status"""
    try:
        # Check if proxy system is working
        from proxies import ProxyManager
        proxy_manager = ProxyManager()
        working_proxies = proxy_manager.working_proxies
        
        return {
            'status': 'active' if working_proxies else 'inactive',
            'working_proxies': len(working_proxies),
            'total_proxies': len(proxy_manager.proxy_list) if hasattr(proxy_manager, 'proxy_list') else 0,
            'last_check': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting proxy status: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'working_proxies': 0,
            'total_proxies': 0
        }

def get_railway_status():
    """Get Railway auto-redeploy system status"""
    try:
        # Check if redeployer is working
        if hasattr(redeployer, 'is_active'):
            status = 'active' if redeployer.is_active else 'inactive'
        else:
            status = 'unknown'
        
        return {
            'status': status,
            'auto_redeploy_enabled': os.getenv('RAILWAY_ENVIRONMENT') is not None,
            'last_deploy': app_start_time.isoformat() if app_start_time else datetime.now().isoformat(),
            'environment': os.getenv('RAILWAY_ENVIRONMENT', 'local')
        }
    except Exception as e:
        logger.error(f"Error getting Railway status: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'auto_redeploy_enabled': False
        }

def search_and_notify():
    """Main search and notification cycle"""
    global total_api_requests, total_items_found, last_search_time
    
    try:
        logger.info("=== Starting search and notification cycle ===")
        
        # 1. Search for new items
        logger.info("Step 1: Searching for new items...")
        search_results = searcher.search_all_queries()
        
        # Update metrics (API requests are counted in core.py, just update items and time)
        total_items_found += search_results.get('new_items', 0)
        last_search_time = datetime.now()
        
        logger.info(f"Search completed: {search_results}")
        
        # Log to database
        try:
            db.add_log_entry('INFO', f"Search cycle completed: {search_results.get('new_items', 0)} new items found", 'Searcher', str(search_results))
        except Exception as log_error:
            logger.error(f"Failed to log search results to database: {log_error}")
        
        # 2. Send notifications for new items
        if search_results.get('new_items', 0) > 0:
            logger.info("Step 2: Sending Telegram notifications...")
            notification_results = send_notifications()
            logger.info(f"Notifications sent: {notification_results}")
        else:
            logger.info("Step 2: No new items to notify about")
        
        # 3. Check for auto-redeploy if there were errors
        if search_results.get('failed_searches', 0) > 0:
            logger.info("Step 3: Checking if redeploy is needed...")
            redeploy_results = redeployer.check_and_redeploy_if_needed()
            logger.info(f"Redeploy check: {redeploy_results}")
            
            if redeploy_results['action'] == 'redeployed':
                logger.warning("Application will be redeployed, stopping current instance")
                return
        
        logger.info("=== Search and notification cycle completed ===")
        
    except Exception as e:
        logger.error(f"Error in search_and_notify cycle: {e}")
        
        # Log the error to database for redeploy tracking
        try:
            db.log_error(500, f"Search cycle error: {e}")
        except Exception as log_error:
            logger.error(f"Failed to log error to database: {log_error}")

def setup_scheduler():
    """Setup scheduled tasks - учитываем реальный Query Refresh Delay"""
    try:
        interval_seconds = get_search_interval()
        
        # ИСПРАВЛЕНО: планировщик учитывает реальный Query Refresh Delay
        if interval_seconds < 60:
            # Для коротких интервалов - проверяем каждые N секунд
            schedule.every(interval_seconds).seconds.do(search_and_notify)
            check_frequency = f"каждые {interval_seconds} секунд"
        else:
            # Для длинных интервалов - проверяем каждую минуту
            schedule.every(1).minutes.do(search_and_notify)
            check_frequency = "каждую минуту"
        
        logger.info(f"✅ Планировщик настроен:")
        logger.info(f"   • Query Refresh Delay: {interval_seconds} секунд")
        logger.info(f"   • Проверка готовности: {check_frequency}")
        logger.info(f"   • Каждый фильтр сканируется строго через {interval_seconds} секунд после последнего сканирования")
        
        # Предупреждение о высокой нагрузке
        if interval_seconds < 30:
            logger.warning(f"⚠️  ВНИМАНИЕ: Query Refresh Delay = {interval_seconds}с может создать высокую нагрузку на Kufar.by!")
            logger.warning(f"⚠️  Рекомендуется использовать интервал ≥ 60 секунд для стабильной работы")
            
            # Примерный расчет нагрузки
            try:
                searches = db.get_active_searches()
                if searches:
                    estimated_requests_per_hour = len(searches) * (3600 / interval_seconds)
                    logger.warning(f"⚠️  Примерная нагрузка: {estimated_requests_per_hour:.0f} запросов/час к Kufar.by")
            except:
                pass
        
        # Schedule proxy refresh (every 2 hours)
        schedule.every(2).hours.do(refresh_proxies)
        
        # Schedule database cleanup (daily at 3 AM)
        schedule.every().day.at("03:00").do(cleanup_old_data)
        
        logger.info(f"   • Обновление прокси: каждые 2 часа")
        logger.info(f"   • Очистка БД: ежедневно в 03:00")
        
    except Exception as e:
        logger.error(f"Ошибка настройки планировщика: {e}")
        raise

def refresh_proxies():
    """Refresh proxy list and validate"""
    try:
        logger.info("Refreshing proxy list...")
        from proxies import proxy_manager
        
        # Refresh failed proxies
        proxy_manager.refresh_failed_proxies()
        
        # Get stats
        stats = proxy_manager.get_proxy_stats()
        logger.info(f"Proxy refresh completed: {stats}")
        
    except Exception as e:
        logger.error(f"Error refreshing proxies: {e}")
        # Log to database if possible
        try:
            db.add_log_entry('ERROR', f'Proxy refresh error: {e}', 'System')
        except:
            pass

def cleanup_old_data():
    """Cleanup old data from database"""
    try:
        logger.info("Starting database cleanup...")
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clean up old logs (keep last 7 days)
            db.execute_query(cursor, """
                DELETE FROM logs 
                WHERE created_at < NOW() - INTERVAL %s
            """, ('7 days',))
            
            # Clean up old error tracking (keep last 3 days)
            db.execute_query(cursor, """
                DELETE FROM error_tracking 
                WHERE created_at < NOW() - INTERVAL %s
            """, ('3 days',))
            
            # Clean up old items (keep last 30 days)
            db.execute_query(cursor, """
                DELETE FROM items 
                WHERE created_at < NOW() - INTERVAL %s
                AND is_sent = TRUE
            """, ('30 days',))
            
            conn.commit()
            logger.info("Database cleanup completed")
            
    except Exception as e:
        logger.error(f"Error in database cleanup: {e}")

def run_scheduler():
    """Run the scheduler loop"""
    logger.info("Starting KF Searcher scheduler...")
    
    try:
        # Run initial search immediately
        logger.info("Running initial search...")
        search_and_notify()
        
        # Start scheduler loop
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        raise

def main():
    """Main application entry point"""
    global app_start_time
    app_start_time = datetime.now()
    
    logger.info("=== KF Searcher (KS1) Starting ===")
    
    try:
        # Initialize database with improved error handling
        logger.info("🔄 Initializing PostgreSQL database...")
        db_initialized = False
        
        try:
            # Force PostgreSQL mode for Railway
            if os.getenv('RAILWAY_ENVIRONMENT'):
                db.force_postgres_mode()
                logger.info("✅ PostgreSQL mode enabled for Railway")
            
            # Initialize database
            db.init_database()
            logger.info("✅ Database initialized successfully")
            db_initialized = True
            
            # Add log entry to database
            try:
                db.add_log_entry('INFO', 'Database initialized successfully', 'System', 'Database tables created')
            except Exception as log_error:
                logger.warning(f"⚠️  Could not add log entry: {log_error}")
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            logger.error(f"Database info: {db.get_database_info()}")
            
            # Don't fail completely - try to start anyway for Railway
            if os.getenv('RAILWAY_ENVIRONMENT'):
                logger.warning("⚠️  Starting without database - will retry later")
                try:
                    # Try simplified connection test
                    with db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT 1")
                        logger.info("✅ Database connection test successful")
                        db_initialized = True
                except Exception as conn_error:
                    logger.error(f"❌ Database connection test failed: {conn_error}")
            else:
                raise  # In local mode, fail completely
        
        if db_initialized:
            logger.info("✅ Database готова к работе")
        else:
            logger.warning("⚠️  Продолжаем без базы данных")
        
        # Check configuration
        logger.info("Checking configuration...")
        from configuration_values import get_telegram_bot_token
        
        telegram_bot_token = get_telegram_bot_token()
        if not telegram_bot_token:
            logger.warning("Telegram bot token not configured - notifications will not work")
            if db_initialized:
                try:
                    db.add_log_entry('WARNING', 'Telegram bot token not configured', 'System', 'Notifications will not work')
                except: pass
        else:
            if db_initialized:
                try:
                    db.add_log_entry('INFO', 'Telegram bot token configured', 'System', 'Notifications enabled')
                except: pass
        
        # Setup scheduler
        setup_scheduler()
        
        # Determine run mode
        if len(sys.argv) > 1 and sys.argv[1] == 'web':
            # Run web server only
            app_start_time = datetime.now()
            
            logger.info(f"Starting web server on {WEB_UI_HOST}:{WEB_UI_PORT}")
            if db_initialized:
                try:
                    db.add_log_entry('INFO', f'Starting web server on {WEB_UI_HOST}:{WEB_UI_PORT}', 'System', 'Web server mode')
                except: pass
            
            # Import and setup web UI
            from web_ui_plugin.app import create_app
            web_app = create_app()
            web_app.run(host=WEB_UI_HOST, port=WEB_UI_PORT, debug=False)
        elif len(sys.argv) > 1 and sys.argv[1] == 'worker':
            # Run worker mode (scheduler)
            logger.info("Starting worker mode (scheduler)")
            run_scheduler()
        else:
            # Run scheduler (default mode)
            run_scheduler()
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
