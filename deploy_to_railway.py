#!/usr/bin/env python3
"""
Railway deployment helper script for KF Searcher
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def check_railway_cli():
    """Check if Railway CLI is installed"""
    try:
        result = subprocess.run(['railway', '--version'], 
                              capture_output=True, text=True, check=True)
        logger.info(f"Railway CLI found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Railway CLI not found. Please install it first:")
        logger.error("npm install -g @railway/cli")
        return False

def check_environment():
    """Check environment variables"""
    logger.info("Checking environment variables...")
    
    required_vars = [
        'RAILWAY_TOKEN',
        'RAILWAY_PROJECT_ID', 
        'RAILWAY_SERVICE_ID',
        'DATABASE_URL',
        'TELEGRAM_BOT_TOKEN'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            logger.warning(f"Missing: {var}")
        else:
            logger.info(f"✓ {var} is set")
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

def deploy_to_railway():
    """Deploy to Railway"""
    try:
        logger.info("Starting Railway deployment...")
        
        # Login to Railway
        logger.info("Logging in to Railway...")
        subprocess.run(['railway', 'login'], check=True)
        
        # Link to project
        logger.info("Linking to Railway project...")
        subprocess.run(['railway', 'link'], check=True)
        
        # Deploy
        logger.info("Deploying to Railway...")
        subprocess.run(['railway', 'deploy'], check=True)
        
        logger.info("✅ Deployment completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Deployment failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during deployment: {e}")
        return False

def check_railway_status():
    """Check Railway service status"""
    try:
        logger.info("Checking Railway service status...")
        result = subprocess.run(['railway', 'status'], 
                              capture_output=True, text=True, check=True)
        logger.info("Railway service status:")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check status: {e}")
        return False

def show_railway_logs():
    """Show Railway service logs"""
    try:
        logger.info("Fetching Railway logs...")
        result = subprocess.run(['railway', 'logs'], 
                              capture_output=True, text=True, check=True)
        logger.info("Recent logs:")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to fetch logs: {e}")
        return False

def main():
    """Main deployment function"""
    logger.info("=== KF Searcher Railway Deployment Helper ===")
    
    # Check prerequisites
    if not check_railway_cli():
        sys.exit(1)
    
    if not check_environment():
        logger.error("Environment check failed. Please set required variables.")
        sys.exit(1)
    
    # Show available commands
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'deploy':
            deploy_to_railway()
        elif command == 'status':
            check_railway_status()
        elif command == 'logs':
            show_railway_logs()
        else:
            logger.error(f"Unknown command: {command}")
            logger.info("Available commands: deploy, status, logs")
    else:
        # Interactive mode
        logger.info("\nAvailable commands:")
        logger.info("1. deploy - Deploy to Railway")
        logger.info("2. status - Check service status")
        logger.info("3. logs - Show service logs")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            deploy_to_railway()
        elif choice == '2':
            check_railway_status()
        elif choice == '3':
            show_railway_logs()
        else:
            logger.error("Invalid choice")

if __name__ == '__main__':
    main()
