# Railway Environment Setup для KF Searcher

Пошаговая инструкция по настройке переменных окружения на Railway.

## 🚀 Начальная настройка

### 1. Создание проекта на Railway

1. Перейдите на [railway.app](https://railway.app)
2. Нажмите "New Project"
3. Выберите "Deploy from GitHub repo"
4. Подключите репозиторий KS1

### 2. Добавление PostgreSQL

1. В проекте нажмите "New Service"
2. Выберите "PostgreSQL"
3. Railway автоматически создаст `DATABASE_URL`

## 🔧 Обязательные переменные

### TELEGRAM_BOT_TOKEN
```
Описание: Токен бота от @BotFather
Обязательно: ДА
Пример: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

**Как получить:**
1. Напишите [@BotFather](https://t.me/botfather)
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте полученный токен

### TELEGRAM_CHAT_ID
```
Описание: ID чата для уведомлений
Обязательно: Рекомендуется
Пример: -1001234567890
```

**Как получить:**
1. Добавьте бота в супергруппу
2. Напишите [@userinfobot](https://t.me/userinfobot) в группе
3. Скопируйте Chat ID (с минусом для групп)

## 🛡️ Настройки прокси (рекомендуется)

### PROXY_ENABLED
```
Значение: true
Описание: Включает использование прокси
```

### PROXY_LIST
```
Описание: Список прокси через запятую
Пример: proxy1.com:8080,proxy2.com:3128,user:pass@proxy3.com:1080
```

**Форматы прокси:**
- `ip:port`
- `ip:port:username:password`
- `http://ip:port`
- `socks5://username:password@ip:port`

## 🔄 Auto-Redeploy настройки

### RAILWAY_TOKEN
```
Описание: API токен Railway для auto-redeploy
Получить: railway.app → Account Settings → Tokens
```

### RAILWAY_PROJECT_ID
```
Описание: ID проекта Railway
Получить: URL проекта или Railway CLI
```

### RAILWAY_SERVICE_ID
```
Описание: ID сервиса Railway
Получить: Settings → Service ID
```

## ⚙️ Дополнительные настройки

### Поисковые настройки
```env
SEARCH_INTERVAL=300                    # Интервал поиска (секунды)
MAX_ITEMS_PER_SEARCH=50               # Макс товаров за поиск
REQUEST_DELAY_MIN=1.0                 # Мин задержка между запросами
REQUEST_DELAY_MAX=3.0                 # Макс задержка между запросами
MAX_ERRORS_BEFORE_REDEPLOY=5          # Порог ошибок для redeploy
```

### Системные настройки
```env
LOG_LEVEL=INFO                        # Уровень логирования
SECRET_KEY=your-secret-key-here       # Ключ для Flask (генерируется автоматически)
DEBUG=false                           # Режим отладки (false для продакшена)
```

## 📋 Полный список переменных для Railway

Скопируйте и вставьте в Railway Variables:

```env
# Обязательные
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Рекомендуемые
TELEGRAM_CHAT_ID=your_chat_id_here
PROXY_ENABLED=true
PROXY_LIST=proxy1:port,proxy2:port

# Auto-redeploy (опционально)
RAILWAY_TOKEN=your_railway_token
RAILWAY_PROJECT_ID=your_project_id
RAILWAY_SERVICE_ID=your_service_id

# Настройки поиска (опционально)
SEARCH_INTERVAL=300
MAX_ITEMS_PER_SEARCH=50
REQUEST_DELAY_MIN=1.0
REQUEST_DELAY_MAX=3.0
MAX_ERRORS_BEFORE_REDEPLOY=5

# Системные (опционально)
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here
DEBUG=false
```

## 🔍 Получение Railway IDs

### Project ID
```bash
# Через Railway CLI
railway status

# Или из URL: https://railway.app/project/PROJECT_ID
```

### Service ID
```bash
# В Railway Dashboard
Project → Service → Settings → Service ID
```

### Railway Token
```bash
# В Railway Dashboard
Account Settings → Tokens → Create Token
```

## ✅ Проверка настроек

После настройки переменных:

1. **Деплой приложения** - Railway автоматически деплоит
2. **Проверка логов** - Railway → Deployments → View Logs
3. **Тест веб-интерфейса** - откройте URL приложения
4. **Тест Telegram** - через веб-интерфейс: Configuration → Test Telegram

## 🚨 Частые ошибки

### 1. Telegram уведомления не работают
```
Ошибка: TELEGRAM_BOT_TOKEN not configured
Решение: Добавьте токен бота в переменные Railway
```

### 2. Database connection failed
```
Ошибка: Нет подключения к БД
Решение: Убедитесь что PostgreSQL сервис добавлен в проект
```

### 3. Auto-redeploy не работает
```
Ошибка: Railway credentials not configured
Решение: Добавьте RAILWAY_TOKEN, PROJECT_ID, SERVICE_ID
```

### 4. Прокси не работают
```
Ошибка: Блокировки от Kufar.by
Решение: Проверьте формат PROXY_LIST, используйте качественные прокси
```

## 📞 Получение помощи

1. **Проверьте логи** в Railway Dashboard
2. **Используйте веб-интерфейс** для диагностики
3. **Создайте Issue** в репозитории с логами

## 🔗 Полезные ссылки

- [Railway Documentation](https://docs.railway.app)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [PostgreSQL на Railway](https://docs.railway.app/databases/postgresql)
- [Environment Variables](https://docs.railway.app/deploy/variables)

---

После настройки всех переменных ваш KF Searcher будет готов к работе! 🚀
