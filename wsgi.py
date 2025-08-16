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
