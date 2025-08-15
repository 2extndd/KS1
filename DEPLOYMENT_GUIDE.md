# KF Searcher Deployment Guide

## Critical Issues Fixed

### 1. SQL Syntax Error
- **Problem**: PostgreSQL syntax errors with `%` placeholders and `INTERVAL` syntax
- **Solution**: Added proper database type detection and SQL syntax handling for both PostgreSQL and SQLite
- **Files Modified**: `db.py`, `web_ui_plugin/app.py`

### 2. Bot Not Working
- **Problem**: Database initialization failures preventing bot startup
- **Solution**: Fixed database connection handling and added proper error handling
- **Files Modified**: `kufar_notifications.py`, `db.py`

### 3. Logs Not Writing
- **Problem**: Logging configuration not optimized for Railway environment
- **Solution**: Added Railway-specific logging configuration and database logging
- **Files Modified**: `kufar_notifications.py`

### 4. Railway Deployment Issues
- **Problem**: Procfile and application structure issues
- **Solution**: Fixed Procfile, added worker mode, and improved application startup
- **Files Modified**: `Procfile`, `kufar_notifications.py`

## Quick Fix Commands

### 1. Test Database Connection
```bash
python test_db_connection.py
```

### 2. Deploy to Railway
```bash
python deploy_to_railway.py deploy
```

### 3. Check Railway Status
```bash
python deploy_to_railway.py status
```

### 4. View Railway Logs
```bash
python deploy_to_railway.py logs
```

## Environment Variables Required

```bash
# Railway Configuration
RAILWAY_TOKEN=your_railway_token
RAILWAY_PROJECT_ID=your_project_id
RAILWAY_SERVICE_ID=your_service_id

# Database
DATABASE_URL=postgresql://username:password@host:port/database

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Optional
SEARCH_INTERVAL=300
MAX_ITEMS_PER_SEARCH=50
LOG_LEVEL=INFO
```

## Deployment Steps

### 1. Local Testing
```bash
# Test database connection
python test_db_connection.py

# Test web interface
python kufar_notifications.py web

# Test worker
python kufar_notifications.py worker
```

### 2. Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to project
railway link

# Deploy
railway deploy
```

### 3. Verify Deployment
```bash
# Check service status
railway status

# View logs
railway logs

# Open web interface
railway open
```

## Application Structure

```
KF Searcher/
├── kufar_notifications.py    # Main application entry point
├── db.py                     # Database operations
├── core.py                   # Core search logic
├── simple_telegram_worker.py # Telegram bot worker
├── web_ui_plugin/           # Web interface
├── Procfile                  # Railway process definitions
└── requirements.txt          # Python dependencies
```

## Process Types

### Web Process
- **Command**: `python kufar_notifications.py web`
- **Purpose**: Runs the Flask web interface
- **Port**: Uses `PORT` environment variable

### Worker Process
- **Command**: `python kufar_notifications.py worker`
- **Purpose**: Runs the search scheduler and bot
- **Features**: Automatic search, notifications, error handling

## Troubleshooting

### Database Connection Issues
1. Check `DATABASE_URL` environment variable
2. Verify PostgreSQL service is running
3. Test connection with `test_db_connection.py`

### Bot Not Working
1. Check `TELEGRAM_BOT_TOKEN` is set
2. Verify bot has proper permissions
3. Check Railway logs for errors

### Logs Not Appearing
1. Check Railway environment variables
2. Verify database tables are created
3. Check application startup logs

### Railway Deployment Fails
1. Verify Railway CLI is installed
2. Check authentication with `railway login`
3. Verify project linking with `railway link`

## Monitoring

### Health Check Endpoint
```
GET /
```
Returns application health status and basic statistics.

### Statistics Endpoint
```
GET /stats
```
Returns detailed application statistics.

### Logs Endpoint
```
GET /logs
```
Returns recent application logs.

## Auto-Redeploy

The application includes automatic redeploy functionality when critical errors occur:

- **Error Threshold**: Configurable via `MAX_ERRORS_BEFORE_REDEPLOY`
- **Error Codes**: 403, 404, 429, 500, 502, 503
- **Trigger**: Automatic when threshold is reached

## Support

If you encounter issues:

1. Run `python test_db_connection.py` to identify problems
2. Check Railway logs with `railway logs`
3. Verify environment variables are set correctly
4. Test locally before deploying to Railway

## Recent Changes

- Fixed PostgreSQL/SQLite compatibility issues
- Improved error handling and logging
- Added Railway-specific optimizations
- Fixed Procfile and process management
- Enhanced database initialization
- Added comprehensive testing tools
