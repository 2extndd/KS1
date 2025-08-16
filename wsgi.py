#!/usr/bin/env python3
"""
WSGI entry point for KufarSearcher web application
"""

import os
import sys
import logging

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

try:
    # Import and create Flask app
    from web_ui_plugin.app import create_app
    
    logger.info("Creating Flask application...")
    application = create_app()
    logger.info("Flask application created successfully")
    
    # Запускаем планировщик в фоновом потоке для Railway
    if os.getenv('RAILWAY_ENVIRONMENT'):
        logger.info("🔄 Starting background scheduler for Railway...")
        import threading
        import time
        import schedule
        
        def background_scheduler():
            """Запускаем планировщик в фоновом потоке"""
            try:
                # Настраиваем планировщик
                from kufar_notifications import setup_scheduler, search_and_notify
                setup_scheduler()
                
                # Запускаем первое сканирование через 30 секунд после старта
                time.sleep(30)
                logger.info("🚀 Running initial background search...")
                search_and_notify()
                
                # Основной цикл планировщика
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # Проверяем каждую минуту
                    
            except Exception as e:
                logger.error(f"Background scheduler error: {e}")
        
        # Запускаем планировщик в daemon потоке
        scheduler_thread = threading.Thread(target=background_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("✅ Background scheduler started successfully")
    
    # Alias for gunicorn
    app = application
    
except Exception as e:
    logger.error(f"Failed to create Flask application: {e}")
    import traceback
    traceback.print_exc()
    raise

if __name__ == "__main__":
    # For development
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('WEB_UI_HOST', '0.0.0.0')
    
    logger.info(f"Starting development server on {host}:{port}")
    application.run(host=host, port=port, debug=False)
