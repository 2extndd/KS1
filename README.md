# KF Searcher (KS1) v1.0 - Stable Release

🚀 **Professional Kufar.by monitoring system with Telegram notifications and web interface**

A powerful, production-ready search and notification system for Kufar.by marketplace. Built with Python, Flask, and Telegram Bot API. Features smart item monitoring, thread-based notifications, size extraction, and a responsive web dashboard.

## ✨ Features

### 🔍 Smart Search & Monitoring
- **Real-time monitoring** of multiple search queries
- **Automatic item detection** with duplicate prevention
- **Size extraction** from item descriptions (48 (M), XL, Large, etc.)
- **Price formatting** with size display (75 BYN - 48 (M))
- **Location tracking** and filtering

### 📱 Telegram Integration
- **Inline buttons** for direct item access
- **Thread-based routing** to specific topics
- **Rich media support** (images + text in single message)
- **Smart notifications** only for new items
- **Customizable message format**

### 🌐 Web Dashboard
- **Real-time metrics** (API requests, uptime, items count)
- **Smart auto-refresh** (no page jumping, preserves scroll position)
- **Responsive design** (5 items per row, optimized layout)
- **Search management** (add/edit/remove queries)
- **Item browsing** with filters and pagination
- **Configuration panel** for system settings

### 🗄️ Database & Storage
- **PostgreSQL support** for production deployment
- **SQLite fallback** for development
- **Efficient indexing** for fast queries
- **Logging system** with Belarus timezone
- **Metrics tracking** (API calls, uptime, performance)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL (for production) or SQLite (for development)
- Telegram Bot Token

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/KufarSearcher.git
cd KufarSearcher
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
```bash
cp env.example .env
# Edit .env with your settings
```

### 4. Run Application
```bash
# Web Interface
python main.py web

# Worker Process (in separate terminal)
python main.py worker
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
DATABASE_URL=postgresql://user:pass@host:port/db

# Optional
SEARCH_INTERVAL=300          # Search interval in seconds
MAX_ITEMS_PER_SEARCH=50      # Max items per search query
LOG_LEVEL=INFO               # Logging level
```

### Telegram Bot Setup
1. Create bot via [@BotFather](https://t.me/botfather)
2. Get bot token
3. Add bot to your chat/channel
4. Get chat ID
5. Configure thread IDs for topic-based routing

## 📁 Project Structure

```
KF Searcher/
├── main.py                      # 🚀 Main application entry point
├── core.py                      # 🔍 Core search logic
├── db.py                        # 🗄️ Database operations
├── simple_telegram_worker.py    # 📱 Telegram bot worker
├── metrics_storage.py           # 📊 Metrics and statistics
├── shared_state.py              # 🔄 Shared application state
├── configuration_values.py      # ⚙️ Configuration constants
├── web_ui_plugin/              # 🌐 Flask web interface
│   ├── app.py                  # Flask application
│   ├── templates/              # HTML templates
│   └── static/                 # CSS, JS, images
├── pyKufarVN/                  # 🔌 Kufar API client
├── Procfile                    # 🚂 Railway deployment config
├── requirements.txt             # 📦 Python dependencies
└── README.md                   # 📚 This documentation
```

## 🚂 Railway Deployment

### 1. Install Railway CLI
```bash
npm install -g @railway/cli
```

### 2. Login & Link Project
```bash
railway login
railway link
```

### 3. Set Environment Variables
```bash
railway variables set TELEGRAM_BOT_TOKEN=your_token
railway variables set TELEGRAM_CHAT_ID=your_chat_id
railway variables set DATABASE_URL=postgresql://...
```

### 4. Deploy
```bash
railway deploy
```

## 🎯 Usage

### Adding Search Queries
1. Access web dashboard at `/queries`
2. Click "Add New Query"
3. Enter search terms, chat ID, and thread ID
4. Save and activate

### Managing Items
- **View all items**: `/items` page
- **Filter by search**: Use search name filter
- **Clear items**: Use "Clear All Items" button
- **Force scan**: Trigger immediate search

### Telegram Notifications
- **Automatic**: New items trigger notifications
- **Thread routing**: Items sent to specific topics
- **Rich format**: Title, price, size, location
- **Direct access**: Inline "Open Kufar" button

## 🔍 API Endpoints

### Web Interface
- `GET /` - Dashboard
- `GET /queries` - Search queries management
- `GET /items` - Items browsing
- `GET /config` - Configuration panel
- `GET /logs` - System logs

### API Endpoints
- `GET /api/stats` - Application statistics
- `GET /api/recent-items` - Recent items data
- `POST /api/queries` - Add/edit queries
- `DELETE /api/queries/<id>` - Remove queries

## 🧪 Testing

### Local Development
```bash
# Test database connection
python3 -c "from db import db; print('DB OK')"

# Test web interface
python3 main.py web

# Test worker process
python3 main.py worker
```

### Production Testing
```bash
# Health check
curl https://your-app.railway.app/

# API stats
curl https://your-app.railway.app/api/stats
```

## 📊 Monitoring & Logs

### Metrics Tracked
- **API Requests**: Total calls to Kufar
- **Items Found**: Total items discovered
- **Uptime**: Application running time
- **Search Queries**: Active monitoring count
- **Last Found Item**: Most recent discovery

### Logging
- **Timezone**: Belarus (UTC+3)
- **Levels**: INFO, WARNING, ERROR
- **Storage**: Database + file logging
- **Rotation**: Automatic log management

## 🚨 Troubleshooting

### Common Issues
1. **Telegram bot not responding**: Check token and chat ID
2. **Items not found**: Verify search queries and API access
3. **Database errors**: Check connection string and permissions
4. **Web interface issues**: Verify Flask app configuration

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 main.py web
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🆕 Changelog

### v1.0.0 - Stable Release
- ✅ **Smart partial refresh** - No more page jumping
- ✅ **Inline Telegram buttons** - Direct item access
- ✅ **Thread-based routing** - Topic-specific notifications
- ✅ **Size extraction** - Automatic size detection
- ✅ **Clean project structure** - Removed unnecessary files
- ✅ **Unified entry point** - Single main.py file
- ✅ **Production ready** - Railway deployment support

### Previous Versions
- v0.9.x - Development and testing
- v0.8.x - Core functionality
- v0.7.x - Initial Telegram integration

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/KufarSearcher/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/KufarSearcher/discussions)
- **Documentation**: This README and inline code comments

---

**Built with ❤️ for the Kufar.by community**

*Last updated: August 2025*
