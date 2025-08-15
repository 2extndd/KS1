# KF Searcher

Система мониторинга Kufar.by с автоматическими уведомлениями в Telegram.

## 🚀 Быстрый старт на Railway

### 1. Установка Railway CLI
```bash
npm install -g @railway/cli
```

### 2. Логин в Railway
```bash
railway login
```

### 3. Связывание с проектом
```bash
railway link
```

### 4. Настройка переменных окружения
```bash
railway variables set TELEGRAM_BOT_TOKEN=your_bot_token
railway variables set TELEGRAM_CHAT_ID=your_chat_id
railway variables set DATABASE_URL=postgresql://...
```

### 5. Деплой
```bash
railway deploy
```

## 🔧 Переменные окружения

### Обязательные
- `TELEGRAM_BOT_TOKEN` - токен бота от @BotFather
- `TELEGRAM_CHAT_ID` - ID чата для уведомлений
- `DATABASE_URL` - URL PostgreSQL базы данных (автоматически на Railway)

### Опциональные
- `SEARCH_INTERVAL` - интервал поиска в секундах (по умолчанию: 300)
- `MAX_ITEMS_PER_SEARCH` - максимальное количество элементов на поиск (по умолчанию: 50)
- `LOG_LEVEL` - уровень логирования (по умолчанию: INFO)

## 📁 Структура проекта

```
KF Searcher/
├── kufar_notifications.py    # Главный файл приложения
├── db.py                     # Операции с базой данных
├── core.py                   # Основная логика поиска
├── simple_telegram_worker.py # Telegram бот
├── web_ui_plugin/           # Веб-интерфейс
├── Procfile                  # Конфигурация Railway
└── requirements.txt          # Python зависимости
```

## 🚦 Процессы Railway

### Web процесс
- **Команда**: `python kufar_notifications.py web`
- **Назначение**: Веб-интерфейс Flask
- **Порт**: Использует переменную `PORT`

### Worker процесс
- **Команда**: `python kufar_notifications.py worker`
- **Назначение**: Поиск и уведомления
- **Функции**: Автоматический поиск, уведомления, обработка ошибок

## 🧪 Тестирование

### Тест локальной базы данных
```bash
python3 test_db_connection.py
```

### Тест Railway PostgreSQL
```bash
python3 test_railway_postgres.py
```

### Тест веб-интерфейса
```bash
python3 kufar_notifications.py web
```

### Тест worker процесса
```bash
python3 kufar_notifications.py worker
```

## 📊 Мониторинг

### Health Check
```
GET /
```
Возвращает статус приложения и базовую статистику.

### Статистика
```
GET /stats
```
Возвращает детальную статистику приложения.

### Логи
```
GET /logs
```
Возвращает недавние логи приложения.

## 🔄 Авто-редиплой

Приложение автоматически перезапускается при критических ошибках:

- **Порог ошибок**: Настраивается через `MAX_ERRORS_BEFORE_REDEPLOY`
- **Коды ошибок**: 403, 404, 429, 500, 502, 503
- **Триггер**: Автоматически при достижении порога

## 🐛 Устранение неполадок

### Проблемы с базой данных
1. Проверьте `DATABASE_URL` в Railway
2. Убедитесь, что PostgreSQL сервис запущен
3. Запустите `python3 test_railway_postgres.py`

### Бот не работает
1. Проверьте `TELEGRAM_BOT_TOKEN`
2. Убедитесь, что у бота есть права
3. Проверьте логи Railway

### Логи не записываются
1. Проверьте переменные окружения Railway
2. Убедитесь, что таблицы созданы
3. Проверьте логи запуска приложения

### Проблемы с деплоем
1. Убедитесь, что Railway CLI установлен
2. Проверьте аутентификацию через `railway login`
3. Убедитесь в правильности связывания проекта

## 📝 Последние изменения

- ✅ Исправлены ошибки SQL синтаксиса для PostgreSQL
- ✅ Улучшена обработка ошибок и логирование
- ✅ Оптимизировано для Railway
- ✅ Исправлен Procfile и управление процессами
- ✅ Улучшена инициализация базы данных
- ✅ Добавлены инструменты тестирования

## 🆘 Поддержка

При возникновении проблем:

1. Запустите `python3 test_railway_postgres.py` для диагностики
2. Проверьте логи Railway через `railway logs`
3. Убедитесь, что переменные окружения настроены правильно
4. Протестируйте локально перед деплоем на Railway

## 📄 Лицензия

MIT License
