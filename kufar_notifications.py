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
    # Railway environment - log to stdout only
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Also log to database
    db.add_log_entry('INFO', 'Application started in Railway environment', 'System')
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

@app.route('/')
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_stats = db.get_items_stats()
        
        # Check searcher status
        searcher_status = searcher.get_searcher_status()
        
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': db_stats,
            'searcher': searcher_status
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
        return {
            'database': db.get_items_stats(),
            'searcher': searcher.get_searcher_status(),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {'error': str(e)}, 500

def search_and_notify():
    """Main search and notification cycle"""
    try:
        logger.info("=== Starting search and notification cycle ===")
        
        # 1. Search for new items
        logger.info("Step 1: Searching for new items...")
        search_results = searcher.search_all_queries()
        logger.info(f"Search completed: {search_results}")
        
        # 2. Send notifications for new items
        if search_results['new_items'] > 0:
            logger.info("Step 2: Sending Telegram notifications...")
            notification_results = send_notifications()
            logger.info(f"Notifications sent: {notification_results}")
        else:
            logger.info("Step 2: No new items to notify about")
        
        # 3. Check for auto-redeploy if there were errors
        if search_results['failed_searches'] > 0:
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
        db.log_error(500, f"Search cycle error: {e}")

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
            cursor.execute("""
                DELETE FROM logs 
                WHERE created_at < NOW() - INTERVAL %s
            """, ('7 days',))
            
            # Clean up old error tracking (keep last 3 days)
            cursor.execute("""
                DELETE FROM error_tracking 
                WHERE created_at < NOW() - INTERVAL %s
            """, ('3 days',))
            
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
