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
    SEARCH_INTERVAL,
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

# Configure logging for Railway environment
if os.getenv('RAILWAY_ENVIRONMENT'):
    # Railway environment - log to stdout and database
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Force database logging on Railway
    try:
        # Force PostgreSQL mode on Railway
        db.force_postgres_mode()
        logger.info(f"Database info: {db.get_database_info()}")
        
        db.add_log_entry('INFO', 'Application started in Railway environment', 'System', 'Railway deployment successful')
        logger.info("Railway environment detected - database logging enabled")
    except Exception as e:
        logger.error(f"Failed to add initial log entry: {e}")
        logger.error(f"Database info: {db.get_database_info()}")
else:
    # Local environment - log to file and stdout
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger(__name__)

# Flask app for web UI and health checks
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Global variables for tracking
app_start_time = datetime.now()
total_api_requests = 0
total_items_found = 0
last_search_time = None

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
        uptime = current_time - app_start_time
        uptime_minutes = int(uptime.total_seconds() / 60)
        
        # Get database stats
        db_stats = db.get_items_stats()
        
        # Get proxy status
        proxy_status = get_proxy_status()
        
        # Get Railway redeploy status
        railway_status = get_railway_status()
        
        return {
            'uptime_minutes': uptime_minutes,
            'uptime_formatted': f"{uptime_minutes}m",
            'total_api_requests': total_api_requests,
            'total_items_found': total_items_found,
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
        working_proxies = proxy_manager.get_working_proxies()
        
        return {
            'status': 'active' if working_proxies else 'inactive',
            'working_proxies': len(working_proxies),
            'total_proxies': len(proxy_manager.proxies) if hasattr(proxy_manager, 'proxies') else 0,
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
            'last_deploy': app_start_time.isoformat(),
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
        
        # Update metrics
        total_api_requests += search_results.get('total_searches', 0)
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
    """Setup scheduled tasks"""
    try:
        # Schedule main search task
        interval_minutes = SEARCH_INTERVAL // 60
        schedule.every(interval_minutes).minutes.do(search_and_notify)
        
        # Schedule proxy refresh (every 2 hours)
        schedule.every(2).hours.do(refresh_proxies)
        
        # Schedule database cleanup (daily at 3 AM)
        schedule.every().day.at("03:00").do(cleanup_old_data)
        
        logger.info(f"Scheduler configured: search every {interval_minutes} minutes")
        
    except Exception as e:
        logger.error(f"Error setting up scheduler: {e}")
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
            if db.is_postgres:
                cursor.execute("""
                    DELETE FROM logs 
                    WHERE created_at < NOW() - INTERVAL %s
                """, ('7 days',))
                
                # Clean up old error tracking (keep last 3 days)
                cursor.execute("""
                    DELETE FROM error_tracking 
                    WHERE created_at < NOW() - INTERVAL %s
                """, ('3 days',))
            else:
                # SQLite version
                cursor.execute("""
                    DELETE FROM logs 
                    WHERE created_at < datetime('now', '-7 days')
                """)
                
                cursor.execute("""
                    DELETE FROM error_tracking 
                    WHERE created_at < datetime('now', '-3 days')
                """)
            
            # Clean up old items (keep last 30 days)
            cursor.execute("""
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
    logger.info("=== KF Searcher (KS1) Starting ===")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        try:
            db.init_database()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            # Try to continue anyway, database might be accessible later
            db.add_log_entry('ERROR', f'Database initialization failed: {e}', 'System')
        
        # Check configuration
        logger.info("Checking configuration...")
        from configuration_values import TELEGRAM_BOT_TOKEN
        
        if not TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured - notifications will not work")
        
        # Setup scheduler
        setup_scheduler()
        
        # Determine run mode
        if len(sys.argv) > 1 and sys.argv[1] == 'web':
            # Run web server only
            logger.info(f"Starting web server on {WEB_UI_HOST}:{WEB_UI_PORT}")
            
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
