#!/usr/bin/env python3
"""
KF Searcher (KS1) v1.0 - Main Application Entry Point
Combines web interface and worker functionality
"""

import sys
import os
import logging
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kufar_searcher.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_web():
    """Run web interface"""
    try:
        from web_ui_plugin.app import create_app
        app = create_app()
        
        # Get port from environment (Railway requirement)
        port = int(os.environ.get('PORT', 5000))
        
        logger.info(f"Starting web interface on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        logger.error(f"Failed to start web interface: {e}")
        sys.exit(1)

def run_worker():
    """Run worker process"""
    try:
        from core import KufarSearcher
        from simple_telegram_worker import send_notifications
        from db import db
        import time
        
        logger.info("Starting worker process")
        
        # Initialize searcher
        searcher = KufarSearcher()
        
        # Main worker loop
        while True:
            try:
                logger.info("=== Starting search cycle ===")
                
                # Search for new items
                results = searcher.search_all_queries()
                logger.info(f"Search completed: {results}")
                
                # Send notifications if new items found
                if results.get('new_items', 0) > 0:
                    logger.info("Sending Telegram notifications...")
                    notification_results = send_notifications()
                    logger.info(f"Notifications sent: {notification_results}")
                
                # Wait before next cycle
                search_interval = int(os.environ.get('SEARCH_INTERVAL', 300))
                logger.info(f"Waiting {search_interval} seconds before next cycle...")
                time.sleep(search_interval)
                
            except KeyboardInterrupt:
                logger.info("Worker process interrupted")
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry
        
    except Exception as e:
        logger.error(f"Failed to start worker process: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python main.py [web|worker]")
        print("  web    - Run web interface")
        print("  worker - Run worker process")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'web':
        run_web()
    elif command == 'worker':
        run_worker()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: web, worker")
        sys.exit(1)

if __name__ == '__main__':
    main()
