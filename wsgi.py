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
    
    # Запускаем планировщик в фоновом потоке для production
    railway_env = os.getenv('RAILWAY_ENVIRONMENT')
    port_env = os.getenv('PORT')  # Railway всегда устанавливает PORT
    is_production = railway_env or port_env
    
    if is_production:
        logger.info(f"🔄 Starting background scheduler for production (Railway: {bool(railway_env)}, PORT: {port_env})...")
        import threading
        import time
        import schedule
        
        def background_scheduler():
            """Запускаем планировщик в фоновом потоке"""
            try:
                logger.info("📋 Setting up background scheduler...")
                
                # Настраиваем планировщик
                from kufar_notifications import setup_scheduler, search_and_notify
                setup_scheduler()
                
                # Запускаем первое сканирование через 30 секунд после старта
                logger.info("⏰ Waiting 30 seconds before first scan...")
                time.sleep(30)
                logger.info("🚀 Running initial background search...")
                search_and_notify()
                
                # Основной цикл планировщика
                logger.info("🔄 Starting scheduler loop...")
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # Проверяем каждую минуту
                    
            except Exception as e:
                logger.error(f"❌ Background scheduler error: {e}")
                import traceback
                traceback.print_exc()
        
        # Запускаем планировщик в daemon потоке
        scheduler_thread = threading.Thread(target=background_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("✅ Background scheduler thread started successfully")
    else:
        logger.info("🏠 Local development mode - no background scheduler")
    
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
