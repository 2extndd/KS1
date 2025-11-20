# 🤖 MercariSearcher Bot - Полная информация для AI агентов

## 📋 Обзор проекта

**MercariSearcher (MRS)** - автоматизированная система мониторинга товаров на японском маркетплейсе Mercari.jp с Telegram уведомлениями.

Проект адаптирован из KufarSearcher (https://github.com/2extndd/KS1) для японского рынка.

---

## 🏗️ Архитектура

### Railway Deployment (2 сервиса)

1. **Web Service** - Flask UI + Gunicorn
   - URL: https://web-production-fe38.up.railway.app/
   - Start: `gunicorn --bind 0.0.0.0:$PORT wsgi:application`
   - Переменная: `RAILWAY_SERVICE_NAME=web`

2. **Worker Service** - Scheduler + Search + Telegram
   - Start: `python mercari_notifications.py worker`
   - Переменная: `RAILWAY_SERVICE_NAME=worker`

### База данных
- **Production**: PostgreSQL (Railway)
- **Development**: SQLite (локально)
- Автоматическая миграция схемы

---

## 📂 Структура проекта

### Основные файлы

```
mercari_notifications.py  - Main worker с scheduler
core.py                    - MercariSearcher класс (поиск)
db.py                      - DatabaseManager (PostgreSQL/SQLite)
configuration_values.py    - Конфигурация с hot reload
simple_telegram_worker.py  - Telegram уведомления
pyMercariAPI/mercari.py    - Обертка вокруг mercapi
```

### Web UI

```
web_ui_plugin/
  app.py                   - Flask приложение
  templates/
    dashboard.html         - Главная страница
    items.html             - Список товаров (6 карточек в ряд, 4:5)
    logs.html              - Логи
    queries.html           - Управление searches
  static/
    js/app.js              - JavaScript
    css/style.css          - Стили
```

---

## 🗄️ База данных

### Таблицы

#### searches
```sql
- id, search_url, name, thread_id
- keyword, min_price, max_price, category_id
- brand, condition, size, color
- scan_interval (индивидуальный для каждого!)
- is_active, notify_on_price_drop
- last_scanned_at, total_scans, items_found
```

#### items
```sql
- id, mercari_id, search_id
- title, price, currency, brand, condition, size
- shipping_cost, item_url, image_url
- seller_name, seller_rating, location
- is_sent, sent_at, found_at
```

#### key_value_store
```sql
- key, value, updated_at
- Используется для hot reload конфигурации
- API counter (для web/worker visibility)
```

---

## 🔑 Ключевые особенности

### 1. Индивидуальные интервалы сканирования
Каждый search имеет свой `scan_interval` (в секундах).
Worker проверяет какие searches готовы к сканированию на основе `last_scanned_at + scan_interval`.

### 2. Hot Reload конфигурации
`configuration_values.py` обновляется каждые 10 секунд из БД.
Изменения применяются без перезапуска worker.

### 3. Multi-thread Telegram
Каждый search может иметь свой `thread_id` для отправки в разные топики супергруппы.

### 4. Event Loop Management
`pyMercariAPI/mercari.py` использует shared event loop для всех async вызовов.
Метод `_run_async()` обрабатывает running/closed loop states.

### 5. Web UI - 6 карточек в ряд, формат 4:5
Как в KS1 bot: `col-lg-2` (6 карточек), aspect-ratio 4:5 для фото.

---

## 📡 API Endpoints (Web UI)

### Основные
- `GET /` - Dashboard
- `GET /items` - Список товаров
- `GET /logs` - Логи
- `GET /queries` - Управление searches

### API
- `POST /api/force-scan` - Ручной запуск сканирования (background thread)
- `POST /api/clear-all-items` - Удалить все items + запустить scan
- `GET /api/recent-items` - Последние 30 items (для dashboard)
- `GET /api/stats` - Статистика (items, searches, API requests)

---

## 🤖 Telegram Notifications

### Формат сообщения (МИНИМАЛЬНЫЙ)

```
<b>Title</b>

💶: $XX.XX (¥YYYY)
📏 Size: XL (если есть)
🔍: search_keyword
```

**Что НЕ включается:**
- ❌ Condition
- ❌ Seller
- ❌ Category
- ❌ Brand

### Фото
- Получает full item details через API для высокого разрешения
- Проверяет: photos → thumbnail → thumbnails (в порядке качества)
- Fallback на thumbnail если full details недоступен

### Thread ID
- Глобальный: `config.TELEGRAM_THREAD_ID`
- Per-search: `search.thread_id` (приоритет)
- Используется: `item.get('search_thread_id') or self.thread_id`

---

## ⚙️ Конфигурация

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://...  # Railway PostgreSQL

# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
TELEGRAM_THREAD_ID=...  # Опционально, для топиков

# Railway
RAILWAY_SERVICE_NAME=web|worker  # КРИТИЧНО!
RAILWAY_ENVIRONMENT=production
PORT=5000  # Автоматически от Railway

# Search
SEARCH_INTERVAL=300  # Default 5 минут
MAX_ITEMS_PER_SEARCH=50

# Currency
USD_CONVERSION_RATE=0.0067  # JPY to USD
DISPLAY_CURRENCY=USD
```

### Hot Reload настройки
Хранятся в БД таблице `key_value_store`:
- `search_interval`
- `max_items_per_search`
- `usd_conversion_rate`
- `api_request_count`
- и другие...

---

## 🔍 Поиск на Mercari

### Библиотека: mercapi
```python
from mercapi import Mercapi

# Async библиотека, обернута в синхронный класс
api = Mercapi()
items = await api.search(keyword, limit=50)
```

### Параметры поиска
```python
{
    'keyword': 'Nike',
    'min_price': 1000,
    'max_price': 10000,
    'category_id': 'mens-clothing',
    'brand': 'Nike',
    'condition': 'new',
    'size': 'M',
    'color': 'black',
    'sort_order': 'created_desc'  # or 'price_asc', 'price_desc'
}
```

---

## 🚨 Критические моменты

### 1. Event Loop
**ПРОБЛЕМА:** `asyncio.run()` создает новый loop каждый раз → "Event loop is closed"

**РЕШЕНИЕ:** Shared event loop + ThreadPoolExecutor fallback
```python
def _run_async(self, coro):
    loop = self._get_or_create_loop()
    if loop.is_running():
        # Use ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return loop.run_until_complete(coro)
```

### 2. Railway Worker Deployment
**ПРОБЛЕМА:** Worker не обновляется автоматически при `railway up`

**РЕШЕНИЕ:** 
- Использовать `railway up --service worker`
- Или manual redeploy через Railway Dashboard
- Убедиться что `RAILWAY_SERVICE_NAME=worker` установлен

### 3. SQLite миграции
**ПРОБЛЕМА:** SQLite не поддерживает `ALTER TABLE ... IF NOT EXISTS`

**РЕШЕНИЕ:** Проверять тип БД и использовать `PRAGMA table_info()` для SQLite

### 4. Recent Items скорость
**ПРОБЛЕМА:** SQL WHERE filter был медленным

**РЕШЕНИЕ:** Просто `get_all_items(limit=30)` + фильтрация в Python (быстрее!)

### 5. Force Scan в Flask
**ПРОБЛЕМА:** Синхронный Flask + async mercapi → конфликт

**РЕШЕНИЕ:** Запуск scan в отдельном daemon thread

---

## 📊 Логирование

### Формат
```python
logger.info("[source] message")
db.add_log_entry('INFO', 'message', 'source', 'details')
```

### Источники (source)
- `[scanner]` - Процесс сканирования
- `[search]` - Выполнение поиска
- `[core]` - Core логика
- `[telegram]` - Telegram отправка
- `[config]` - Конфигурация
- `[api]` - Web UI API
- `[startup]` - Запуск worker

### Уровни
- `INFO` - Обычные события
- `WARNING` - Предупреждения
- `ERROR` - Ошибки

---

## 🧪 Тестирование

### Локально
```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Создать .env
cp .env.example .env
# Заполнить TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# 3. Запустить worker
python mercari_notifications.py worker

# 4. Запустить web (в другом терминале)
python mercari_notifications.py web
```

### Railway
```bash
# Проверить логи
railway logs --service worker
railway logs --service web

# Проверить переменные
railway variables --service worker

# Manual redeploy
railway up --service worker
railway up --service web
```

---

## 🐛 Частые проблемы

### Event Loop is Closed
**Симптом:** `RuntimeError: Event loop is closed`
**Причина:** Многократные вызовы `asyncio.run()` или closed loop
**Решение:** Использовать shared event loop (уже исправлено в коде)

### Worker не обновляется
**Симптом:** Изменения в коде не применяются после push
**Причина:** Railway worker не pull из GitHub автоматически
**Решение:** `railway up --service worker` или manual redeploy в Dashboard

### Telegram не отправляет
**Симптом:** `unsent_items > 0` но уведомлений нет
**Причина:** Worker на старом коде или `process_pending_notifications()` не вызывается
**Решение:** Проверить worker logs, убедиться что есть "Checking for pending notifications"

### Recent Items медленный
**Симптом:** Dashboard долго загружается
**Причина:** Сложный SQL query с WHERE filter
**Решение:** Использовать `get_all_items(limit=30)` (уже исправлено)

### Фото низкого качества
**Симптом:** Маленькие thumbnails в Telegram
**Причина:** mercapi возвращает только thumbnails в search results
**Решение:** Получать full item details для каждого item (уже исправлено)

---

## 🔄 Рекомендуемые улучшения (будущее)

### 1. Перевод JA→EN
См. `TRANSLATION_IDEAS.md`:
- DeepL API (лучшее качество, 500k chars/month free)
- MyMemory API (полностью бесплатный)
- Переключатель в Web UI

### 2. Мониторинг
- Health check endpoint для worker
- Статистика по каждому search
- Графики в dashboard

### 3. Фильтры в Web UI
- Фильтр по search
- Фильтр по price range
- Фильтр по дате

### 4. Auto-cleanup
- Удалять старые sent items (>30 дней)
- Cleanup старых логов (>7 дней)
- Сейчас есть метод, но не вызывается автоматически

---

## 📁 Важные файлы для изучения

### Для понимания логики:
1. `mercari_notifications.py` - Main entry point, scheduler
2. `core.py` - Search logic
3. `simple_telegram_worker.py` - Telegram formatting
4. `db.py` - Database operations

### Для понимания Web UI:
1. `web_ui_plugin/app.py` - Flask routes
2. `web_ui_plugin/templates/dashboard.html` - Main page
3. `web_ui_plugin/templates/items.html` - Items grid (6 cards, 4:5)

### Для понимания API:
1. `pyMercariAPI/mercari.py` - Mercapi wrapper
2. `pyMercariAPI/items.py` - Item data class

---

## 🎯 Ключевые принципы

### 1. Простота над сложностью
- Не усложнять там где можно упростить
- Recent Items: простой query лучше сложного SQL

### 2. Cross-process visibility
- API counter в БД (не shared_state)
- Логи в БД (видны web и worker)
- Hot reload из БД

### 3. Индивидуальные настройки
- Каждый search имеет свой scan_interval
- Каждый search может иметь свой thread_id

### 4. Graceful degradation
- Если фото нет - показать placeholder
- Если full item недоступен - использовать thumbnail
- Если timestamp parsing fails - include item anyway

### 5. Railway-first
- PostgreSQL primary, SQLite fallback
- Environment variables для всего
- start.sh определяет web/worker по RAILWAY_SERVICE_NAME

---

## 📞 Полезные ссылки

- **GitHub**: https://github.com/2extndd/MRS
- **Railway Project**: https://railway.app/project/f17da572-14c9-47b5-a9f1-1b6d5b6dea2d
- **Web UI**: https://web-production-fe38.up.railway.app/
- **KS1 (исходный проект)**: https://github.com/2extndd/KS1
- **mercapi library**: https://github.com/qwotix/mercapi

---

## 🔑 Секреты успеха

1. **Всегда проверяй RAILWAY_SERVICE_NAME** - без него worker/web не работают правильно
2. **railway up для worker** - не полагайся на auto-deploy
3. **Shared event loop** - для всех async операций
4. **Hot reload** - изменения конфигурации без перезапуска
5. **Background threads** - для Force Scan и Clear All Items
6. **6 карточек, 4:5** - как в KS1, красиво и компактно
7. **Минимальный Telegram формат** - только важное (title, price, size, query)

---

**Создано:** 2025-11-19  
**Версия:** 1.0  
**Автор:** AI Assistant  
**Для:** Будущих AI агентов и разработчиков
